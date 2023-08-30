from typing import Any, Dict, List, Optional

import aiohttp_retry


class Registry:
    """
    Interfaces with DockerHub registry using registry API
    https://docs.docker.com/registry/spec/api/
    """

    index_url = "https://registry-1.docker.io/"
    docker_url: str = "https://hub.docker.com/"
    token: Optional[str] = None

    retry_options = aiohttp_retry.ExponentialRetry(attempts=5)

    async def _get_token(self, repo: str) -> str:
        """[summary]
        Gets a token for dockerhub.com
        Args:
            auth_url: authentication url, default to https://auth.docker.io
            image_name: image name, for example "bluerobotics/core"

        Raises:
            Exception: Raised if unable to get the token

        Returns:
            The token
        """
        payload = {
            "service": "registry.docker.io",
            "scope": f"repository:{repo}:pull",
        }

        auth_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"
        async with aiohttp_retry.RetryClient(retry_options=self.retry_options) as session:
            async with session.get(auth_url + "/token", params=payload) as resp:
                if resp.status != 200:
                    print(f"Error status {resp.status}")
                    raise Exception("Could not get auth token")
                return str((await resp.json(content_type=None))["token"])

    async def fetch_remote_tags(self, repository: str) -> List[str]:
        """Fetches the tags available for an image in DockerHub"""
        print(f"fetching tags in {repository}")
        self.token = await self._get_token(repository)
        async with aiohttp_retry.RetryClient(retry_options=self.retry_options) as session:
            async with session.get(
                f"{self.docker_url}/v2/repositories/{repository}/tags/?page_size=25&page=1&ordering=last_updated"
            ) as resp:
                if resp.status != 200:
                    print(f"Error status {resp.status}")
                    raise Exception("Failed getting tags from DockerHub!")
                data = await resp.json(content_type=None)
                tags = data["results"]

                valid_images = [tag["name"] for tag in tags]
                print(valid_images)
                return valid_images

    def is_compatible(self, entry: Any) -> bool:
        if entry["os"] != "linux":
            return False
        return bool(entry["architecture"] == "arm")

    async def extract_digest(self, data: Any, repo: str) -> str:
        # regular images/ OCI images
        if "config" in data:
            return str(data["config"]["digest"])
        # OCI index. we need to filter for the right arch
        manifests = data["manifests"]
        filtered_manifests = [entry for entry in manifests if self.is_compatible(entry["platform"])]
        if len(filtered_manifests) != 1:
            raise RuntimeError(f"unexpected number of manifests found for current arch: {len(filtered_manifests)}")
        digest = filtered_manifests[0]["digest"]
        return await self.fetch_digest(digest, repo)

    async def fetch_digest(self, digest: str, repository: str) -> str:
        header = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.oci.image.index.v1+json",
        }
        async with aiohttp_retry.RetryClient(retry_options=self.retry_options) as session:
            url = f"{self.index_url}/v2/{repository}/manifests/{digest}"
            async with session.get(url, headers=header) as resp:
                if resp.status != 200:
                    print(f"Error status {resp.status}")
                    print(await resp.text())
                    raise Exception(f"Failed getting sha from DockerHub at {url} : {resp.status} : {await resp.text()}")
                data = await resp.json(content_type=None)
                return str(data["config"]["digest"])

    async def fetch_labels(self, repo: str) -> Dict[str, Any]:
        """Fetches the digest sha from a tag. This returns the image id displayed by 'docker image ls'"""
        header = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.oci.image.index.v1+json",
        }
        repository, tag = repo.split(":")
        print(f"fetching labels for {repository}:{tag}")
        async with aiohttp_retry.RetryClient(retry_options=self.retry_options) as session:
            url = f"{self.index_url}/v2/{repository}/manifests/{tag}"
            async with session.get(url, headers=header) as resp:
                if resp.status != 200:
                    print(f"Error status {resp.status}")
                    raise Exception(f"Failed getting sha from DockerHub at {url} : {resp.status} : {await resp.text()}")
                data = await resp.json(content_type=None)
                digest = await self.extract_digest(data, repository)
                blob_url = f"{self.index_url}/v2/{repository}/blobs/{digest}"

                async with session.get(blob_url, headers=header) as resp:
                    if resp.status != 200:
                        print(f"Error status {resp.status}")
                        print(resp.text)
                        raise Exception("Failed getting blob from DockerHub!")
                    data = await resp.json(content_type=None)
                    try:
                        return data["config"]["Labels"]  # type: ignore
                    except KeyError:
                        return {}
