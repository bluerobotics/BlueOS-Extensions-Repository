import base64
import os
from typing import Optional

import aiohttp_retry
from docker.models.auth import AuthToken


class DockerAuthAPI:  # pylint: disable=too-few-public-methods
    """
    This class is used to interact with a Docker-compatible token authentication API.

    Supports Docker Hub (auth.docker.io), GHCR (ghcr.io), and other OCI-compliant
    registries that follow the Docker token authentication specification.

    More details in https://distribution.github.io/distribution/spec/auth/token/
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_url: str = "https://auth.docker.io",
        service: str = "registry.docker.io",
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_retries: int = 5,
    ) -> None:
        """
        Constructor for the DockerAuthAPI class.

        Args:
            auth_url: Base URL for the token endpoint (e.g. "https://auth.docker.io" or "https://ghcr.io").
            service: The ``service`` query parameter sent to the token endpoint.
            username: The username to be used in the authentication (optional).
            password: The password to be used in the authentication (optional).
            max_retries: The maximum number of retries to be used in case of request failure. Defaults to 5.

        Returns:
            None
        """

        self.__api_url: str = auth_url
        self.__service: str = service
        self.__auth_header: Optional[str] = None

        if username and password:
            self.__auth_header = f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
        elif service == "registry.docker.io":
            # Docker Hub credentials from environment
            if "DOCKER_USERNAME" in os.environ and "DOCKER_PASSWORD" in os.environ:
                env_user = os.environ["DOCKER_USERNAME"]
                env_pass = os.environ["DOCKER_PASSWORD"]
                self.__auth_header = f"Basic {base64.b64encode(f'{env_user}:{env_pass}'.encode()).decode()}"
        elif service == "ghcr.io":
            # GitHub Container Registry – use a GitHub token when available
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if token:
                self.__auth_header = f"Basic {base64.b64encode(f'token:{token}'.encode()).decode()}"

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
            "service": self.__service,
            "scope": f"repository:{repo}:pull",
        }

        headers = {"Authorization": self.__auth_header} if self.__auth_header else {}

        auth_url = f"{self.__api_url}/token"
        async with aiohttp_retry.RetryClient(retry_options=self.__retry_options) as session:
            async with session.get(auth_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    error_msg = f"Error on Docker Auth API ({self.__api_url}) with status {resp.status}"
                    print(error_msg)
                    raise Exception(error_msg)

                return AuthToken(**(await resp.json()))
