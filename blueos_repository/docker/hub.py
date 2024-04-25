from typing import Any, Optional

import aiohttp_retry
from dataclass_wizard import fromdict
from docker.models.tag import TagList


class DockerHub:
    """
    This class is used to interact with the Docker Hub API.

    More details in https://docs.docker.com/docker-hub/api/latest/
    """

    __api_base_url: str = "https://hub.docker.com"
    __api_version: str = "v2"
    __api_url: str = f"{__api_base_url}/{__api_version}"

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

    async def get(self, route: str, max_retries: Optional[int] = None, **kwargs: Any) -> Any:
        """
        Make a GET request to the Docker Hub API.

        Args:
            route: The route to be used in the request.
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to None.
            **kwargs: The keyword arguments to be used in the request like params, headers, etc.

        Returns:
            The response from the request parsed as json.

        Raises:
            Exception: The pretty error message in case of error status.
        """

        retry = self.__retry_options if not max_retries else aiohttp_retry.ExponentialRetry(attempts=max_retries)

        async with aiohttp_retry.RetryClient(retry_options=retry) as session:
            async with session.get(f"{self.__api_url}/{route}", **kwargs) as resp:
                if resp.status >= 400:
                    error_msg = f"Error on GET Docker HUB API with status {resp.status} on call to {resp.url}"
                    print(error_msg)
                    raise Exception(error_msg)

                return await resp.json(content_type=None)

    async def get_tags(self) -> TagList:
        """
        Get all tags for a given repository

        Args:
            repo: The repository name, for example "bluerobotics/core"

        Returns:
            A list of tags
        """

        route = f"/repositories/{self.repository}/tags"
        params = {
            "page_size": 25,
            "page": 1,
            "ordering": "last_updated",
        }

        return fromdict(TagList, await self.get(route, params=params))
