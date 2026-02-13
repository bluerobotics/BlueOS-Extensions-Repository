from typing import Any, List, Optional

import aiohttp_retry
from dataclass_wizard import fromdict
from docker.auth import DockerAuthAPI
from docker.models.auth import AuthToken
from docker.models.blob import Blob
from docker.models.limit import RateLimit
from docker.models.manifest import ImageManifest, ManifestFetch, ManifestList


class DockerRegistry:  # pylint: disable=too-many-instance-attributes
    """
    This class is used to interact with a Docker-compatible Registry V2 API.

    Supports Docker Hub (registry-1.docker.io), GHCR (ghcr.io), and other
    OCI-compliant registries.

    More details in https://distribution.github.io/distribution/spec/api/
    """

    # Media types accepted when fetching manifests.  We request every format
    # the codebase can handle so the registry returns the best match.
    __manifest_accept: str = ",".join(
        [
            "application/vnd.docker.distribution.manifest.v2+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.oci.image.index.v1+json",
        ]
    )

    @staticmethod
    def from_preview() -> "DockerRegistry":
        """
        Create a DockerRegistry object using the rate limit preview repository as base.

        Returns:
            A DockerRegistry object using the preview repository API.
        """

        return DockerRegistry("ratelimitpreview/test")

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        repository: str,
        registry_url: str = "https://registry-1.docker.io",
        auth_url: str = "https://auth.docker.io",
        auth_service: str = "registry.docker.io",
        max_retries: int = 5,
    ) -> None:
        """
        Constructor for the DockerRegistry class.

        Args:
            repository: Repository that this registry class will operate on.
            registry_url: Base URL for the registry (e.g. "https://registry-1.docker.io" or "https://ghcr.io").
            auth_url: Base URL for the token authentication endpoint.
            auth_service: The ``service`` parameter used for token requests.
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to 5.

        Returns:
            None
        """

        self.repository = repository
        self.__api_base_url: str = registry_url
        self.__auth_url: str = auth_url
        self.__auth_service: str = auth_service
        self.__api_version: str = "v2"
        self.__api_url: str = f"{self.__api_base_url}/{self.__api_version}"
        self.__token: Optional[AuthToken] = None
        self.__retry_options = aiohttp_retry.ExponentialRetry(attempts=max_retries)

    async def __check_token(self) -> None:
        """
        Checks if the token is set and not expired, otherwise renew it.
        """

        if not self.__token or self.__token.is_expired:
            auth = DockerAuthAPI(auth_url=self.__auth_url, service=self.__auth_service)
            self.__token = await auth.get_token(self.repository)

    async def __raise_pretty(self, resp: Any) -> None:
        """
        Throws a pretty error message in case of a error status conforming with
        errors in the Docker Registry API.

        Args:
            resp: The response from the request.

        Raises:
            Exception: The pretty error message.
        """

        errors = (await resp.json()).get("errors", [])
        error = errors[0] if errors else {}

        error_code = error.get("code", "Unknown Code")
        error_message = error.get("message", "Unknown Message")

        error_msg = f"Error on Docker Registry API with status {resp.status} on call to {resp.url}: {error_code} - {error_message}"

        print(error_msg)
        raise Exception(error_msg)

    async def get(self, route: str, max_retries: Optional[int] = None, **kwargs: Any) -> Any:
        """
        Make a GET request to the Docker Registry V2 API.

        Args:
            route: The route to be used in the request.
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to None.
            **kwargs: Additional keyword arguments passed to the HTTP client (e.g. headers, params).

        Returns:
            The response from the request parsed as json.

        Raises:
            Exception: The pretty error message in case of error status.
        """

        retry = self.__retry_options if not max_retries else aiohttp_retry.ExponentialRetry(attempts=max_retries)

        async with aiohttp_retry.RetryClient(retry_options=retry) as session:
            async with session.get(f"{self.__api_url}/{route}", **kwargs) as resp:
                # In case of an error status, tries to make a better error message
                if resp.status >= 400:
                    await self.__raise_pretty(resp)

                return await resp.json(content_type=None)

    async def get_manifest(self, tag_or_digest: str) -> ManifestFetch:
        """
        Get the manifest for a given tag

        Args:
            tag_or_digest: Can be a tag name or a specific digest related to a ManifestList

        Returns:
            The manifest
        """

        await self.__check_token()

        route = f"{self.repository}/manifests/{tag_or_digest}"
        header = {
            "Authorization": f"Bearer {self.__token.token if self.__token else ''}",
            "Accept": self.__manifest_accept,
        }

        manifest = await self.get(route, headers=header)

        if "config" in manifest:
            return ManifestFetch(manifest=fromdict(ImageManifest, manifest))

        # OCI indexes (e.g. from GHCR) may contain non-image entries such as
        # attestation manifests that lack a "platform" field.  Filter them out
        # so the typed Manifest dataclass can require platform unconditionally.
        if "manifests" in manifest:
            manifest["manifests"] = [m for m in manifest["manifests"] if "platform" in m]

        return ManifestFetch(manifest=fromdict(ManifestList, manifest))

    async def get_manifest_blob(self, digest: str) -> Blob:
        """
        Get the blob config object for a given manifest digest

        Args:
            digest: The digest of the manifest

        Returns:
            The blob config object
        """

        await self.__check_token()

        route = f"{self.repository}/blobs/{digest}"
        header = {
            "Authorization": f"Bearer {self.__token.token if self.__token else ''}",
            "Accept": "application/vnd.oci.image.config.v1+json,application/json",
        }

        blob = await self.get(route, headers=header)

        return fromdict(Blob, blob)

    async def list_tags(self) -> List[str]:
        """
        List all tags for the repository using the standard V2 tag listing API.

        This is the registry-agnostic way to discover tags; it works on any
        OCI-compliant registry (Docker Hub, GHCR, Quay, etc.).

        Returns:
            A list of tag name strings.
        """

        await self.__check_token()

        route = f"{self.repository}/tags/list"
        header = {"Authorization": f"Bearer {self.__token.token if self.__token else ''}"}

        data = await self.get(route, headers=header)
        return list(data.get("tags", []) or [])

    async def get_rate_limit(self) -> RateLimit:

        await self.__check_token()

        route = f"{self.repository}/manifests/latest"

        header = {"Authorization": f"Bearer {self.__token.token if self.__token else ''}"}

        async with aiohttp_retry.RetryClient(retry_options=self.__retry_options) as session:
            async with session.head(f"{self.__api_url}/{route}", headers=header) as resp:
                # In case of an error status, tries to make a better error message
                if resp.status >= 400:
                    raise Exception(f"Error on Docker Registry API with status {resp.status} on call to {resp.url}")

                limit = int(resp.headers.get("ratelimit-limit", "0;0").split(";")[0])
                interval = int(resp.headers.get("ratelimit-limit", "0;w=0").split(";")[1].replace("w=", ""))
                remaining = int(resp.headers.get("ratelimit-remaining", "0;0").split(";")[0])

                return RateLimit(
                    limit=limit,
                    remaining=remaining,
                    interval_seconds=interval,
                    source_ip=resp.headers.get("docker-ratelimit-source", "unknown"),
                )
