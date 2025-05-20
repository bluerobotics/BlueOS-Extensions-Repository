from typing import Any, Optional

import aiohttp_retry
from dataclass_wizard import fromdict
from docker.auth import DockerAuthAPI
from docker.models.auth import AuthToken
from docker.models.blob import Blob
from docker.models.limit import RateLimit
from docker.models.manifest import ImageManifest, ManifestFetch, ManifestList


class DockerRegistry:
    """
    This class is used to interact with the Docker Registry API.

    More details in https://distribution.github.io/distribution/spec/api/
    """

    __api_base_url: str = "https://registry-1.docker.io"
    __api_version: str = "v2"
    __api_url: str = f"{__api_base_url}/{__api_version}"

    __token: Optional[AuthToken] = None

    @staticmethod
    def from_preview() -> "DockerRegistry":
        """
        Create a DockerRegistry object using the rate limit preview repository as base.

        Returns:
            A DockerRegistry object using the preview repository API.
        """

        return DockerRegistry("ratelimitpreview/test")

    def __init__(self, repository: str, max_retries: int = 5) -> None:
        """
        Constructor for the DockerHubAPI class.

        Args:
            repository: Repository that this registry class will operate on
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to 5.

        Returns:
            None
        """
        self.repository = repository
        self.__retry_options = aiohttp_retry.ExponentialRetry(attempts=max_retries)

    async def __check_token(self) -> None:
        """
        Checks if the token is set and not expired, otherwise renew it.
        """

        if not self.__token or self.__token.is_expired:
            auth = DockerAuthAPI()
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
        Make a GET request to the Docker Hub API.

        Args:
            route: The route to be used in the request.
            params: The parameters to be used in the request.
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to None.

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
            "Accept": "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.oci.image.index.v1+json",
        }

        manifest = await self.get(route, headers=header)

        if "config" in manifest:
            return ManifestFetch(manifest=fromdict(ImageManifest, manifest))

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
            "Accept": "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.oci.image.index.v1+json",
        }

        blob = await self.get(route, headers=header)

        return fromdict(Blob, blob)

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
