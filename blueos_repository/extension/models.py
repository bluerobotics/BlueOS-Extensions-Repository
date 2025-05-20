import dataclasses
from enum import StrEnum
from typing import Any, Dict, List, Optional


class ExtensionType(StrEnum):
    """
    Represents the type of an extension.

    Attributes:
        DEVICE_INTEGRATION (str): Device integration extension.
        EXAMPLE (str): Example extension.
        THEME (str): Theme extension.
        OTHER (str): Other extension.
        TOOL (str): Tool extension.
    """

    DEVICE_INTEGRATION = "device-integration"
    EXAMPLE = "example"
    THEME = "theme"
    OTHER = "other"
    TOOL = "tool"


@dataclasses.dataclass
class Author:
    """
    Represents an author of an extension.

    Attributes:
        name (str): Name of the author.
        email (str): Email of the author.
    """

    name: str
    email: str


@dataclasses.dataclass
class Platform:
    """
    Represents a platform supported by the extension.

    Attributes:
        architecture (str): Architecture of the platform.
        variant (Optional[str]): Variant of the platform.
        os (Optional[str]): Operating system of the platform.
    """

    architecture: str
    variant: Optional[str] = None
    os: Optional[str] = None


@dataclasses.dataclass
class Image:
    """
    Represents description of an image available for a given extension version.

    Attributes:
        digest (Optional[str]): Digest of the image.
        size (int): Uncompressed size of the image.
        platform (Platform): Platform of the image.
    """

    expanded_size: int
    platform: Platform
    digest: Optional[str] = None


@dataclasses.dataclass
class Company:
    """
    Represents a company associated with an extension.

    Attributes:
        name (str): Name of the company.
        about (Optional[str]): Description of the company.
        email (Optional[str]): Email of the company.
    """

    name: str
    about: Optional[str] = None
    email: Optional[str] = None


@dataclasses.dataclass
class ExtensionVersion:  # pylint: disable=too-many-instance-attributes
    """
    Represents a version of an extension.

    Attributes:
        identifier (str): Unique identifier of this tag version, in extension repository is the 256 sha digest from the
            first compatible image, in BlueOS cloud is a uuid v4.
        tag (Optional[str]): Tag of the version.
        type (ExtensionType): Type of the extension.
        website (str): URL to the extension's website.
        docs (Optional[str]): URL to the extension's documentation.
        readme (Optional[str]): URL to the extension's readme.
        support (Optional[str]): URL to the extension's support.
        requirements (Optional[str]): Requirements of the extension.
        authors (List[Author]): Authors of the extension.
        company (Optional[Company]): Company associated with the extension.
        permissions (Optional[Dict[str, Any]]): Permissions of the extension.
        filter_tags (List[str]): Tags used to filter the extension.
        extra_links (Dict[str, str]): Extra links associated with the extension.
        images (List[Image]): Images available for the extension.
    """

    identifier: str  # TODO - In future try to unify with identifiers coming from cloud
    type: ExtensionType
    website: str
    images: List[Image]
    authors: List[Author]
    filter_tags: List[str]
    extra_links: Dict[str, str]
    tag: Optional[str] = None
    docs: Optional[str] = None
    readme: Optional[str] = None
    support: Optional[str] = None
    requirements: Optional[str] = None
    company: Optional[Company] = None
    permissions: Optional[Dict[str, Any]] = None

    @staticmethod
    def validate_filter_tags(tags: List[str]) -> List[str]:
        """Returns a list of up to 10 lower-case alpha-numeric tags (dashes allowed)."""
        return [tag.lower() for tag in tags if tag.replace("-", "").isalnum()][:10]


@dataclasses.dataclass
class ExtensionMetadata:
    """
    Represents metadata associated with some extension.

    Attributes:
        identifier (str): Identifier of the extension.
        name (str): Name of the extension.
        website (str): URL to the extension's website.
        docker (str): Docker repository name.
        description (str): Description of the extension.
        extension_logo (Optional[str]): URL to the extension's logo.
        company_logo (Optional[str]): URL to the company's logo.
    """

    identifier: str
    name: str
    website: str
    docker: str
    description: str
    extension_logo: Optional[str] = None
    company_logo: Optional[str] = None
