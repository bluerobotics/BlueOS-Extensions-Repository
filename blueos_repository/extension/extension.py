import asyncio
import uuid
from typing import Dict, List, Optional

import aiohttp
import json5
from docker.hub import DockerHub
from docker.models.blob import Blob
from docker.models.manifest import ManifestFetch, ManifestPlatform
from docker.models.repo import RepoInfo
from docker.models.tag import Tag
from docker.registry import DockerRegistry
from extension.models import (
    ExtensionMetadata,
    ExtensionType,
    ExtensionVersion,
    Image,
    Platform,
)
from logger import Logger
from utils import valid_semver


class Extension:
    """
    Represents an BlueOS extension.

    Attributes:
        metadata (ExtensionMetadata): Metadata associated with the extension.
    """

    def __init__(self, metadata: ExtensionMetadata) -> None:
        """
        Constructor for the Extension class.

        Args:
            metadata (ExtensionMetadata): Metadata associated with the extension.

        Returns:
            None
        """

        self.identifier = metadata.identifier
        self.metadata = metadata
        self.repo_info: Optional[RepoInfo] = None

        # Versions
        self.versions: Dict[str, ExtensionVersion] = {}

        # Docker API
        self.hub: DockerHub = DockerHub(metadata.docker)
        self.registry: DockerRegistry = DockerRegistry(metadata.docker)

    @property
    def sorted_versions(self) -> Dict[str, ExtensionVersion]:
        """
        Returns the versions reverse sorted by semver.

        Returns:
            Dict[str, ExtensionVersion]: Sorted versions.
        """

        return dict(sorted(self.versions.items(), key=lambda item: valid_semver(item[0]), reverse=True))  # type: ignore

    @staticmethod
    async def fetch_readme(url: str) -> str:
        if not url.startswith("http"):
            raise Exception(f"Invalid readme url: {url}, must start with http or https.")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Could not get readme {url}: status: {resp.status}: {await resp.text()}")
                if resp.content_type != "text/plain":
                    raise Exception(f"Could not get readme, expected type to be text/plain but got {resp.content_type}")
                return await resp.text()

    def __extract_images_from_tag(self, tag: Tag) -> List[Image]:
        active_images = [
            image
            for image in tag.images
            if (image.status == "active" and image.architecture != "unknown" and image.os != "unknown")
        ]

        images = [
            Image(
                digest=image.digest if image.digest else None,
                expanded_size=image.size,
                platform=Platform(
                    architecture=image.architecture,
                    variant=image.variant if image.variant else None,
                    os=image.os if image.os else None,
                ),
            )
            for image in active_images
        ]
        return images

    def __is_compatible(self, platform: ManifestPlatform) -> bool:
        """
        Checks if the platform is compatible with embedded devices BlueOS targets.

        Args:
            platform (ManifestPlatform): Platform to check.

        Returns:
            bool: True if compatible, False otherwise.
        """

        return bool(platform.os == "linux" and platform.architecture == "arm")

    async def __extract_valid_embedded_digest(self, fetch: ManifestFetch) -> str:
        """
        Tries to find a valid embedded image digest in the extension manifest.
        As this image should be able to run on the vehicle raspberry pi, it should be
        a valid arm image with target os as linux.

        Args:
            fetch (ManifestFetch): The manifest to extract the digest from.

        Returns:
            str: The digest of the embedded image.

        Raises:
            RuntimeError: If the manifest does not contain a valid embedded image.
        """

        # Regular images/ OCI images
        if fetch.is_image_manifest:
            return str(fetch.manifest.config.digest)

        # Manifest list
        valid_manifests = [entry for entry in fetch.manifest.manifests if self.__is_compatible(entry.platform)]
        if len(valid_manifests) != 1:
            raise RuntimeError(
                f"Expected one valid manifest for target embedded arch but found: {len(valid_manifests)}"
            )

        # Needs to refetch because it was a manifest list
        manifest_fetch = await self.registry.get_manifest(valid_manifests[0].digest)

        if manifest_fetch.is_image_manifest:
            return str(manifest_fetch.manifest.config.digest)

        raise RuntimeError(f"Expected to have a valid image manifest but got a manifest list: {manifest_fetch}")

    async def __create_version_from_tag_blob(self, version_tag: Tag, blob: Blob) -> ExtensionVersion:
        labels = blob.config.Labels

        authors = labels.get("authors", "[]")
        links = json5.loads(labels.get("links", "{}"))
        filter_tags = json5.loads(labels.get("tags", "[]"))

        docs_raw = links.pop("docs", links.pop("documentation", labels.get("docs", None)))
        company_raw = labels.get("company", None)
        permissions_raw = labels.get("permissions", None)

        readme = labels.get("readme", None)
        if readme is not None:
            readme = readme.replace(r"{tag}", version_tag.name)
            try:
                readme = await Extension.fetch_readme(readme)
            except Exception as error:  # pylint: disable=broad-except
                Logger.warning(self.identifier, str(error))
                readme = str(error)

        images = self.__extract_images_from_tag(version_tag)
        if not images:
            Logger.error(
                self.identifier,
                f"Could not find images associated with tag {version_tag.name} for extension {self.identifier}",
            )

        tag_identifier = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.identifier}.{version_tag.name}"))
        return ExtensionVersion(
            identifier=tag_identifier,
            tag=version_tag.name,
            type=labels.get("type", ExtensionType.OTHER),
            website=links.pop("website", labels.get("website", None)),
            readme=readme,
            support=links.pop("support", labels.get("support", None)),
            requirements=labels.get("requirements", None),
            extra_links=links,
            authors=json5.loads(authors),
            filter_tags=ExtensionVersion.validate_filter_tags(filter_tags),
            docs=json5.loads(docs_raw) if docs_raw else None,
            company=json5.loads(company_raw) if company_raw else None,
            permissions=json5.loads(permissions_raw) if permissions_raw else None,
            images=self.__extract_images_from_tag(version_tag),
        )

    async def __process_tag_version(self, tag: Tag) -> None:
        """
        Process a tag and create a version object for it and store it in the versions
        dictionary property.

        Args:
            tag (Tag): Tag to process.
        """

        tag_name = tag.name
        try:
            if not valid_semver(tag_name):
                raise ValueError(f"Invalid version naming: {tag_name}")

            manifest = await self.registry.get_manifest(tag_name)

            # Extract the digest of the embedded image and blob from it
            embedded_digest = await self.__extract_valid_embedded_digest(manifest)
            blob = await self.registry.get_manifest_blob(embedded_digest)

            self.versions[tag_name] = await self.__create_version_from_tag_blob(tag, blob)
        except ValueError as error:
            Logger.error(
                self.identifier, f"Invalid tag name {tag_name} for extension {self.identifier}, error: {error}"
            )
        except KeyError as error:
            Logger.error(
                self.identifier,
                f"Failed to generate version {tag_name} for extension {self.identifier}, error in key: {error}",
            )
        except Exception as error:  # pylint: disable=broad-except
            Logger.error(
                self.identifier,
                f"Failed to generate version {tag_name} for extension {self.identifier}, error: {error}",
            )

    async def inflate(self) -> None:
        """
        Inflate extension data, this will fetch all the necessary data from docker hub, registry, etc.
        And store it in the object to allow manifest formation after.

        Returns:
            None
        """

        try:
            tags = await self.hub.get_tags()
            self.repo_info = await self.hub.repo_info()
        except Exception as error:  # pylint: disable=broad-except
            Logger.error(self.identifier, f"Unable to fetch tags for {self.identifier}, error: {error}")
            return

        # We may want to split and process first 5 tags prior to make sure we dont reach limit and always have the
        # latest ones processed.
        await asyncio.gather(*(self.__process_tag_version(tag) for tag in tags.results))
