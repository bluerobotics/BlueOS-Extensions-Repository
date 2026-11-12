import dataclasses


@dataclasses.dataclass
class DockerImageRef:
    """
    Parsed Docker image reference.

    Handles both Docker Hub short references (e.g. "bluerobotics/blueos-doris")
    and fully-qualified references with a registry hostname
    (e.g. "ghcr.io/bluerobotics/blueos-doris").
    """

    registry: str
    repository: str

    @staticmethod
    def parse(docker: str) -> "DockerImageRef":
        """
        Parse a Docker image reference string into registry and repository components.

        Args:
            docker: The docker image reference, e.g.:
                - "bluerobotics/cockpit"                  → docker.io / bluerobotics/cockpit
                - "ghcr.io/bluerobotics/blueos-doris"     → ghcr.io / bluerobotics/blueos-doris
                - "docker.io/bluerobotics/cockpit"        → docker.io / bluerobotics/cockpit
                - "registry.example.com/org/repo"         → registry.example.com / org/repo

        Returns:
            A DockerImageRef with the extracted registry and repository.
        """

        # Strip any tag or digest suffix so we only deal with the image name
        name = docker.split("@")[0].split(":")[0]
        parts = name.split("/")

        # If the first part looks like a hostname (contains a dot or a colon,
        # or is "localhost"), treat it as the registry.
        if len(parts) >= 3 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
            registry = parts[0]
            repository = "/".join(parts[1:])
        else:
            registry = "docker.io"
            repository = name

        return DockerImageRef(registry=registry, repository=repository)

    @property
    def is_dockerhub(self) -> bool:
        return self.registry in ("docker.io", "registry-1.docker.io", "index.docker.io")

    @property
    def is_ghcr(self) -> bool:
        return self.registry == "ghcr.io"

    @property
    def registry_url(self) -> str:
        """Base URL for the Docker Registry V2 API."""
        if self.is_dockerhub:
            return "https://registry-1.docker.io"
        return f"https://{self.registry}"

    @property
    def auth_url(self) -> str:
        """Base URL for the token authentication endpoint."""
        if self.is_dockerhub:
            return "https://auth.docker.io"
        # GHCR (and most OCI registries) serve the token endpoint on the
        # same host as the registry itself.
        return f"https://{self.registry}"

    @property
    def auth_service(self) -> str:
        """The ``service`` parameter sent to the token endpoint."""
        if self.is_dockerhub:
            return "registry.docker.io"
        return self.registry
