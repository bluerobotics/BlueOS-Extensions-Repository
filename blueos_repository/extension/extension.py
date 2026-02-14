import asyncio
import uuid
from typing import Dict, List, Optional

import aiohttp
import json5
from docker.hub import DockerHub
from docker.image_ref import DockerImageRef
from docker.models.blob import Blob
from docker.models.manifest import ImageManifest, ManifestFetch, ManifestPlatform
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
from extension.utils.markdown_img_encoder import MarkdownImageEncoder
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

        # Parse docker image reference to determine registry
        self.image_ref: DockerImageRef = DockerImageRef.parse(metadata.docker)

        # Docker Registry V2 API (works for any OCI-compliant registry)
        self.registry: DockerRegistry = DockerRegistry(
            self.image_ref.repository,
            registry_url=self.image_ref.registry_url,
            auth_url=self.image_ref.auth_url,
            auth_service=self.image_ref.auth_service,
        )

        # Docker Hub has a proprietary REST API that provides richer tag
        # metadata (ordering, pull counts, per-image details).  For other
        # registries we fall back to the standard V2 tag list on self.registry.
        self.docker_hub: Optional[DockerHub] = (
            DockerHub(self.image_ref.repository) if self.image_ref.is_dockerhub else None
        )

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

    @staticmethod
    async def process_readme_md(readme: str, resources_url: str) -> str:
        encoder = MarkdownImageEncoder(readme, resources_url)
        return str(await encoder.get_processed_markdown())

    @staticmethod
    def __extract_images_from_tag(tag: Tag) -> List[Image]:
        active_images = [
            image
            for image in tag.images
            if (image.status == "active" and image.architecture != "unknown" and image.os != "unknown")
        ]

        return [
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

    @staticmethod
    def __extract_images_from_manifest(manifest_fetch: ManifestFetch, blob: Blob) -> List[Image]:
        """
        Derive per-platform image information directly from a registry manifest.

        This is the registry-agnostic path used when the Docker Hub tag API is
        not available (e.g. GHCR, Quay, or any other OCI registry).

        Args:
            manifest_fetch: The fetched manifest (may be a single image or a manifest list / OCI index).
            blob: The blob config for the embedded (ARM) image — used for
                  platform info when the manifest is a single image.

        Returns:
            List of Image objects.
        """

        if isinstance(manifest_fetch.manifest, ImageManifest):
            return [
                Image(
                    digest=manifest_fetch.manifest.config.digest,
                    expanded_size=sum(layer.size for layer in manifest_fetch.manifest.layers),
                    platform=Platform(
                        architecture=blob.architecture or "unknown",
                        variant=None,
                        os=blob.os or "unknown",
                    ),
                )
            ]

        # ManifestList / OCI Index — entry.size is the manifest document
        # size, NOT the image layer size, so we report 0 (unknown) instead.
        return [
            Image(
                digest=entry.digest,
                expanded_size=0,
                platform=Platform(
                    architecture=entry.platform.architecture,
                    variant=entry.platform.variant if entry.platform.variant else None,
                    os=entry.platform.os if entry.platform.os else None,
                ),
            )
            for entry in manifest_fetch.manifest.manifests
        ]

    def __is_compatible(self, platform: ManifestPlatform) -> bool:
        """
        Checks if the platform is compatible with embedded devices BlueOS targets.

        Args:
            platform (ManifestPlatform): Platform to check.

        Returns:
            bool: True if compatible, False otherwise.
        """

        return bool(platform.os == "linux" and "arm" in platform.architecture)

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
        if isinstance(fetch.manifest, ImageManifest):
            return str(fetch.manifest.config.digest)

        # Manifest list
        valid_manifests = [entry for entry in fetch.manifest.manifests if self.__is_compatible(entry.platform)]
        if len(valid_manifests) != 1:
            Logger.warning(
                self.identifier,
                f"Expected one valid manifest for target embedded arch but found: {len(valid_manifests)}",
            )

        # Needs to refetch because it was a manifest list
        manifest_fetch = await self.registry.get_manifest(valid_manifests[0].digest)

        if isinstance(manifest_fetch.manifest, ImageManifest):
            return str(manifest_fetch.manifest.config.digest)

        raise RuntimeError(f"Expected to have a valid image manifest but got a manifest list: {manifest_fetch}")

    async def __create_version(  # pylint: disable=too-many-locals
        self,
        tag_name: str,
        blob: Blob,
        manifest: ManifestFetch,
        hub_tag: Optional[Tag] = None,
    ) -> ExtensionVersion:
        """
        Build an :class:`ExtensionVersion` from the blob labels, manifest, and
        (optionally) Docker Hub tag metadata.

        Args:
            tag_name: The semver tag string (e.g. ``"1.2.3"``).
            blob: The config blob for the embedded ARM image.
            manifest: The top-level manifest fetch for this tag.
            hub_tag: If available, the Docker Hub ``Tag`` object that provides
                     rich per-image metadata (sizes, architecture, status).
        """

        labels = blob.config.Labels

        authors = labels.get("authors", "[]")
        links = json5.loads(labels.get("links", "{}"))
        filter_tags = json5.loads(labels.get("tags", "[]"))

        docs_raw = links.pop("docs", links.pop("documentation", labels.get("docs", None)))
        company_raw = labels.get("company", None)
        permissions_raw = labels.get("permissions", None)

        readme = labels.get("readme", None)
        if readme is not None:
            url = readme.replace(r"{tag}", tag_name)
            try:
                readme = await Extension.fetch_readme(url)
                try:
                    url = url.rsplit("/", 1)[0]
                    readme = await Extension.process_readme_md(readme, url)
                except Exception as error:  # pylint: disable=broad-except
                    Logger.warning(self.identifier, str(error))
            except Exception as error:  # pylint: disable=broad-except
                Logger.warning(self.identifier, str(error))
                readme = "No README available"

        # Prefer Docker Hub's rich per-image data when available; otherwise
        # derive the image list from the manifest (works for any registry).
        images: List[Image] = []
        if hub_tag:
            images = self.__extract_images_from_tag(hub_tag)
        if not images:
            images = self.__extract_images_from_manifest(manifest, blob)
        if not images:
            Logger.error(
                self.identifier,
                f"Could not find images associated with tag {tag_name} for extension {self.identifier}",
            )

        tag_identifier = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.identifier}.{tag_name}"))
        return ExtensionVersion(
            identifier=tag_identifier,
            tag=tag_name,
            type=ExtensionType(labels.get("type", ExtensionType.OTHER.value)),
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
            images=images,
        )

    async def __process_tag(self, tag_name: str, hub_tag: Optional[Tag] = None) -> None:
        """
        Fetch the manifest and blob for *tag_name*, build an
        :class:`ExtensionVersion`, and store it in ``self.versions``.

        Args:
            tag_name: The tag string to process.
            hub_tag: Optional Docker Hub ``Tag`` object for richer metadata.
        """

        try:
            if not valid_semver(tag_name):
                raise ValueError(f"Invalid version naming: {tag_name}")

            manifest = await self.registry.get_manifest(tag_name)

            # Extract the digest of the embedded image and blob from it
            embedded_digest = await self.__extract_valid_embedded_digest(manifest)
            blob = await self.registry.get_manifest_blob(embedded_digest)

            self.versions[tag_name] = await self.__create_version(tag_name, blob, manifest, hub_tag)

            Logger.info(self.identifier, f"Generated version entry {tag_name} for extension {self.identifier}")
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

    async def inflate(self, tag: Optional[Tag] = None) -> None:
        """
        Inflate extension data, this will fetch all the necessary data from docker hub, registry, etc.
        And store it in the object to allow manifest formation after.

        Args:
            tag (Optional[Tag]): Tag to inflate, if not provided all tags will be inflated.

        Returns:
            None
        """

        if tag:
            return await self.__process_tag(tag.name, hub_tag=tag)

        try:
            if self.docker_hub:
                # Docker Hub: use its proprietary API for ordered results,
                # rich per-image metadata, and download stats.
                hub_tags = await self.docker_hub.get_tags()
                self.repo_info = await self.docker_hub.repo_info()

                await asyncio.gather(*(self.__process_tag(t.name, hub_tag=t) for t in hub_tags.results))
            else:
                # Any other OCI registry: use the standard V2 tag list.
                tag_names = await self.registry.list_tags()

                await asyncio.gather(*(self.__process_tag(name) for name in tag_names))
        except Exception as error:  # pylint: disable=broad-except
            Logger.error(self.identifier, f"Unable to fetch tags for {self.identifier}, error: {error}")
