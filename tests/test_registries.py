"""
Integration tests for Docker Hub and GHCR registry support.

These tests hit real registry APIs (no mocking) using two public repositories:
  - Docker Hub:  bluerobotics/cockpit
  - GHCR:        ghcr.io/bluerobotics/blueos-doris
"""

# pylint: disable=redefined-outer-name

import pytest
from docker.auth import DockerAuthAPI
from docker.image_ref import DockerImageRef
from docker.models.manifest import ImageManifest, ManifestList
from docker.registry import DockerRegistry
from extension.extension import Extension
from extension.models import ExtensionMetadata

DOCKERHUB_IMAGE = "bluerobotics/cockpit"
GHCR_IMAGE = "ghcr.io/bluerobotics/blueos-doris"


@pytest.fixture
def dockerhub_ref() -> DockerImageRef:
    return DockerImageRef.parse(DOCKERHUB_IMAGE)


@pytest.fixture
def ghcr_ref() -> DockerImageRef:
    return DockerImageRef.parse(GHCR_IMAGE)


@pytest.fixture
def dockerhub_registry(dockerhub_ref: DockerImageRef) -> DockerRegistry:
    return DockerRegistry(
        dockerhub_ref.repository,
        registry_url=dockerhub_ref.registry_url,
        auth_url=dockerhub_ref.auth_url,
        auth_service=dockerhub_ref.auth_service,
    )


@pytest.fixture
def ghcr_registry(ghcr_ref: DockerImageRef) -> DockerRegistry:
    return DockerRegistry(
        ghcr_ref.repository,
        registry_url=ghcr_ref.registry_url,
        auth_url=ghcr_ref.auth_url,
        auth_service=ghcr_ref.auth_service,
    )


class TestDockerImageRef:
    def test_parse_dockerhub_short(self) -> None:
        ref = DockerImageRef.parse("bluerobotics/cockpit")
        assert ref.registry == "docker.io"
        assert ref.repository == "bluerobotics/cockpit"
        assert ref.is_dockerhub is True
        assert ref.is_ghcr is False

    def test_parse_dockerhub_explicit(self) -> None:
        ref = DockerImageRef.parse("docker.io/bluerobotics/cockpit")
        assert ref.registry == "docker.io"
        assert ref.repository == "bluerobotics/cockpit"
        assert ref.is_dockerhub is True

    def test_parse_ghcr(self) -> None:
        ref = DockerImageRef.parse("ghcr.io/bluerobotics/blueos-doris")
        assert ref.registry == "ghcr.io"
        assert ref.repository == "bluerobotics/blueos-doris"
        assert ref.is_ghcr is True
        assert ref.is_dockerhub is False

    def test_parse_strips_tag(self) -> None:
        ref = DockerImageRef.parse("ghcr.io/bluerobotics/blueos-doris:0.0.1")
        assert ref.repository == "bluerobotics/blueos-doris"

    def test_parse_strips_digest(self) -> None:
        ref = DockerImageRef.parse("ghcr.io/org/repo@sha256:abcdef1234567890")
        assert ref.repository == "org/repo"

    def test_registry_url_dockerhub(self, dockerhub_ref: DockerImageRef) -> None:
        assert dockerhub_ref.registry_url == "https://registry-1.docker.io"

    def test_registry_url_ghcr(self, ghcr_ref: DockerImageRef) -> None:
        assert ghcr_ref.registry_url == "https://ghcr.io"

    def test_auth_url_dockerhub(self, dockerhub_ref: DockerImageRef) -> None:
        assert dockerhub_ref.auth_url == "https://auth.docker.io"

    def test_auth_url_ghcr(self, ghcr_ref: DockerImageRef) -> None:
        assert ghcr_ref.auth_url == "https://ghcr.io"

    def test_auth_service_dockerhub(self, dockerhub_ref: DockerImageRef) -> None:
        assert dockerhub_ref.auth_service == "registry.docker.io"

    def test_auth_service_ghcr(self, ghcr_ref: DockerImageRef) -> None:
        assert ghcr_ref.auth_service == "ghcr.io"


class TestDockerAuth:
    async def test_dockerhub_token(self, dockerhub_ref: DockerImageRef) -> None:
        auth = DockerAuthAPI(auth_url=dockerhub_ref.auth_url, service=dockerhub_ref.auth_service)
        token = await auth.get_token(dockerhub_ref.repository)
        assert token.token is not None
        assert len(token.token) > 0
        assert token.is_expired is False

    async def test_ghcr_token(self, ghcr_ref: DockerImageRef) -> None:
        auth = DockerAuthAPI(auth_url=ghcr_ref.auth_url, service=ghcr_ref.auth_service)
        token = await auth.get_token(ghcr_ref.repository)
        assert token.token is not None
        assert len(token.token) > 0
        assert token.is_expired is False


class TestDockerRegistryTagList:
    async def test_dockerhub_list_tags(self, dockerhub_registry: DockerRegistry) -> None:
        tags = await dockerhub_registry.list_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0
        # cockpit has semver tags
        assert any("." in tag for tag in tags)

    async def test_ghcr_list_tags(self, ghcr_registry: DockerRegistry) -> None:
        tags = await ghcr_registry.list_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert any("." in tag for tag in tags)


class TestDockerRegistryManifest:
    async def test_dockerhub_get_manifest(self, dockerhub_registry: DockerRegistry) -> None:
        tags = await dockerhub_registry.list_tags()
        # Pick a semver-looking tag
        semver_tags = [t for t in tags if "." in t and t[0].isdigit()]
        assert len(semver_tags) > 0, "Expected at least one semver tag for cockpit"

        fetch = await dockerhub_registry.get_manifest(semver_tags[0])
        manifest = fetch.manifest

        # Could be a single image or a manifest list
        assert isinstance(manifest, (ImageManifest, ManifestList))

        if isinstance(manifest, ManifestList):
            assert len(manifest.manifests) > 0
            # All entries must have platform (attestation entries filtered)
            for entry in manifest.manifests:
                assert entry.platform is not None
                assert entry.platform.architecture
                assert entry.platform.os

    async def test_ghcr_get_manifest(self, ghcr_registry: DockerRegistry) -> None:
        tags = await ghcr_registry.list_tags()
        semver_tags = [t for t in tags if "." in t and t[0].isdigit()]
        assert len(semver_tags) > 0, "Expected at least one semver tag for blueos-doris"

        fetch = await ghcr_registry.get_manifest(semver_tags[0])
        manifest = fetch.manifest

        assert isinstance(manifest, (ImageManifest, ManifestList))

        if isinstance(manifest, ManifestList):
            assert len(manifest.manifests) > 0
            # Attestation manifests must have been filtered — all entries have platform
            for entry in manifest.manifests:
                assert entry.platform is not None
                assert entry.platform.architecture
                assert entry.platform.os


class TestDockerRegistryBlob:
    async def test_dockerhub_get_blob(self, dockerhub_registry: DockerRegistry) -> None:
        tags = await dockerhub_registry.list_tags()
        semver_tags = [t for t in tags if "." in t and t[0].isdigit()]
        fetch = await dockerhub_registry.get_manifest(semver_tags[0])

        # Resolve to a single-image manifest to get config digest
        if isinstance(fetch.manifest, ManifestList):
            entry = fetch.manifest.manifests[0]
            fetch = await dockerhub_registry.get_manifest(entry.digest)

        assert isinstance(fetch.manifest, ImageManifest)
        blob = await dockerhub_registry.get_manifest_blob(fetch.manifest.config.digest)

        assert blob.config is not None
        assert isinstance(blob.config.Labels, dict)
        assert blob.architecture is not None

    async def test_ghcr_get_blob(self, ghcr_registry: DockerRegistry) -> None:
        tags = await ghcr_registry.list_tags()
        semver_tags = [t for t in tags if "." in t and t[0].isdigit()]
        fetch = await ghcr_registry.get_manifest(semver_tags[0])

        if isinstance(fetch.manifest, ManifestList):
            entry = fetch.manifest.manifests[0]
            fetch = await ghcr_registry.get_manifest(entry.digest)

        assert isinstance(fetch.manifest, ImageManifest)
        blob = await ghcr_registry.get_manifest_blob(fetch.manifest.config.digest)

        assert blob.config is not None
        assert isinstance(blob.config.Labels, dict)
        assert blob.architecture is not None


class TestExtensionInflate:
    @staticmethod
    def _make_metadata(docker: str, identifier: str) -> ExtensionMetadata:
        return ExtensionMetadata(
            identifier=identifier,
            name=identifier,
            website="https://example.com",
            docker=docker,
            description="Test extension",
        )

    async def test_dockerhub_extension_inflate(self) -> None:
        metadata = self._make_metadata(DOCKERHUB_IMAGE, "test.cockpit")
        ext = Extension(metadata)

        assert ext.docker_hub is not None
        assert ext.image_ref.is_dockerhub is True

        await ext.inflate()

        assert len(ext.versions) > 0, "Expected at least one valid version from Docker Hub"

        for tag_name, version in ext.versions.items():
            assert "." in tag_name  # semver
            assert len(version.images) > 0
            for image in version.images:
                assert image.platform is not None
                assert image.platform.architecture

    async def test_ghcr_extension_inflate(self) -> None:
        metadata = self._make_metadata(GHCR_IMAGE, "test.doris")
        ext = Extension(metadata)

        assert ext.docker_hub is None
        assert ext.image_ref.is_ghcr is True

        await ext.inflate()

        assert len(ext.versions) > 0, "Expected at least one valid version from GHCR"

        for tag_name, version in ext.versions.items():
            assert "." in tag_name  # semver
            assert len(version.images) > 0
            for image in version.images:
                assert image.platform is not None
                assert image.platform.architecture
