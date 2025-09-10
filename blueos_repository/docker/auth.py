import base64
import os
from typing import Optional

import aiohttp_retry
from docker.models.auth import AuthToken


class DockerAuthAPI:  # pylint: disable=too-few-public-methods
    """
    This class is used to interact with the Docker Auth API.

    More details in https://distribution.github.io/distribution/spec/auth/token/
    """

    __api_url: str = "https://auth.docker.io"

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, max_retries: int = 5) -> None:
        """
        Constructor for the DockerAuthAPI class.

        Args:
            username: The username to be used in the authentication (optional)
            password: The password to be used in the authentication (optional)
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to 5.

        Returns:
            None
        """

        self.__auth_header: Optional[str] = None

        if username and password:
            self.__auth_header = f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
        elif "DOCKER_USERNAME" in os.environ and "DOCKER_PASSWORD" in os.environ:
            username = os.environ["DOCKER_USERNAME"]
            password = os.environ["DOCKER_PASSWORD"]
            self.__auth_header = f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"

        self.__retry_options = aiohttp_retry.ExponentialRetry(attempts=max_retries)

    async def get_token(self, repo: str) -> AuthToken:
        """
        Gets a token to be used in docker registry requests.

        Args:
            repo: The repository name, for example "bluerobotics/core"

        Returns:
            The token
        """

        params = {
            "service": "registry.docker.io",
            "scope": f"repository:{repo}:pull",
        }

        headers = {"Authorization": self.__auth_header} if self.__auth_header else {}

        auth_url = f"{self.__api_url}/token?service=registry.docker.io&scope=repository:{repo}:pull"
        async with aiohttp_retry.RetryClient(retry_options=self.__retry_options) as session:
            async with session.get(auth_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    error_msg = f"Error on Docker Auth API with status {resp.status}"
                    print(error_msg)
                    raise Exception(error_msg)

                return AuthToken(**(await resp.json()))
