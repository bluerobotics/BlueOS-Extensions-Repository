import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class ManifestPlatform:
    """
    Describes the platform which the image in the manifest runs on.

    Attributes:
        architecture (str): The architecture field specifies the CPU architecture, for example amd64 or ppc64le
        os (str): Operating system, for example linux or windows.
        variant (Optional[str]): Variant of the CPU, for example v6 for ARM CPU.
        features (Optional[List[str]]): The optional features field specifies an array of strings, each listing a required CPU feature (for example sse4 or aes).
    """

    architecture: str
    os: str
    variant: Optional[str] = None
    features: Optional[List[str]] = None


@dataclasses.dataclass
class Manifest:
    """
    Represents a single image manifest within a manifest list.

    Attributes:
        mediaType (str): The MIME type of the referenced object.
        size (int): The size in bytes of the object.
        digest (str): Digest of the content as defined by the Registry V2 HTTP API Specification.
        platform (Platform): The platform object describes the platform which the image in the manifest runs on
    """

    mediaType: str  # pylint: disable=invalid-name
    size: int
    digest: str
    platform: ManifestPlatform


@dataclasses.dataclass
class ManifestList:
    """
    The manifest list is the “fat manifest” which points to specific image manifests
    for one or more platforms. Its use is optional, and relatively few images will use
    one of these manifests. A client will distinguish a manifest list from an image
    manifest based on the Content-Type returned in the HTTP response.

    Attributes:
        schemaVersion (int): This field specifies the image manifest schema version as an integer. This schema uses the version 2.
        mediaType (str): The MIME type of the manifest list. This should be set to application/vnd.docker.distribution.manifest.list.v2+json.
        manifests (List[Manifest]): The manifests field contains a list of manifests for specific platforms.
    """

    schemaVersion: int  # pylint: disable=invalid-name
    mediaType: str  # pylint: disable=invalid-name
    manifests: List[Manifest]


@dataclasses.dataclass
class ConfigReference:
    """
    References a configuration object for a container, by digest. The configuration is a JSON blob used by the runtime.

    Attributes:
        mediaType (str): MIME type of the referenced object.
        size (int): Size in bytes of the object.
        digest (str): Digest of the content, as defined by the Registry V2 HTTP API Specification.
    """

    mediaType: str  # pylint: disable=invalid-name
    size: int
    digest: str


@dataclasses.dataclass
class ManifestLayer:
    """
    Represents a single layer within the image manifest, specifying the content and its source.

    Attributes:
        mediaType (str): MIME type of the referenced object. Expected to be application/vnd.docker.image.rootfs.diff.tar.gzip or application/vnd.docker.image.rootfs.foreign.diff.tar.gzip.
        size (int): Size in bytes of the object.
        digest (str): Digest of the content, as defined by the Registry V2 HTTP API Specification.
        urls (Optional[List[str]]): List of URLs from which the content may be fetched. Optional field.
    """

    mediaType: str  # pylint: disable=invalid-name
    size: int
    digest: str
    urls: Optional[List[str]] = None


@dataclasses.dataclass
class ImageManifest:
    """
    Provides a configuration and a set of layers for a container image, replacing the schema-1 manifest.

    Attributes:
        schemaVersion (int): The image manifest schema version as an integer, version 2 is expected.
        mediaType (str): MIME type of the manifest, expected to be application/vnd.docker.distribution.manifest.v2+json.
        config (ConfigObject): The configuration object for a container by digest.
        layers (List[Layer]): Ordered list of layers starting from the base image.
    """

    schemaVersion: int  # pylint: disable=invalid-name
    mediaType: str  # pylint: disable=invalid-name
    config: ConfigReference
    layers: List[ManifestLayer]


@dataclasses.dataclass
class ManifestFetch:
    """
    Represents a manifest fetch response.

    Attributes:
        manifest (Manifest | ManifestList | ImageManifest): The manifest object.
    """

    manifest: ManifestList | ImageManifest
