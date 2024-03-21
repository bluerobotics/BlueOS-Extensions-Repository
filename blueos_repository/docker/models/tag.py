import dataclasses
from typing import Optional, List


@dataclasses.dataclass
class Layer:
    """
    Represents a layer within a Docker image.

    Attributes:
        digest (Optional[str]): The SHA256 digest of the layer, or None if not available.
        size (int): The size of the layer in bytes.
        instruction (str): The Dockerfile instruction that created this layer.
    """
    digest: Optional[str]
    size: int
    instruction: str


@dataclasses.dataclass
class Image:
    """
    Describes a Docker image and its characteristics.

    Attributes:
        architecture (str): CPU architecture of the image.
        features (str): Specific CPU features of the image.
        variant (str): The variant of the CPU architecture.
        digest (Optional[str]): The SHA256 digest of the image, or None if not available.
        layers (Optional[List[Layer]]): The list of layers that compose the image.
        os (str): The operating system on which the image is based.
        os_features (str): Features or characteristics of the image's operating system.
        os_version (Optional[str]): The version of the operating system.
        size (int): The total size of the image in bytes.
        status (str): The current status of the image.
        last_pulled (Optional[str]): The timestamp of the last time the image was pulled.
        last_pushed (Optional[str]): The timestamp of the last time the image was pushed.
    """
    architecture: str
    features: str
    variant: str
    digest: Optional[str]
    layers: Optional[List[Layer]]
    os: str
    os_features: str
    os_version: Optional[str]
    size: int
    status: str
    last_pulled: Optional[str]
    last_pushed: Optional[str]


@dataclasses.dataclass
class Tag:
    """
    Represents a tag assigned to a set Docker image in a repository.

    Attributes:
        id (int): The unique identifier for the tag.
        images (List[Image]): The list of images associated with this tag.
        creator (int): The user ID of the tag's creator.
        last_updated (Optional[str]): The timestamp of the last update to the tag.
        last_updater (int): The user ID of the last person to update the tag.
        last_updater_username (str): The username of the last person to update the tag.
        name (str): The name of the tag.
        repository (int): The repository ID where the tag is located.
        full_size (int): Compressed size (sum of all layers) of the tagged image.
        v2 (str): Repository API version.
        status (str): The current status of the tag can be "active" "inactive".
        tag_last_pulled (Optional[str]): The timestamp of the last time the tag was pulled.
        tag_last_pushed (Optional[str]): The timestamp of the last time the tag was pushed.
    """
    id: int
    images: List[Image]
    creator: int
    last_updated: Optional[str]
    last_updater: int
    last_updater_username: str
    name: str
    repository: int
    full_size: int
    v2: str
    status: str
    tag_last_pulled: Optional[str]
    tag_last_pushed: Optional[str]


    def __post_init__(self):
        """
        Post-initialization processing to enforce constraints
        """
        valid_statuses = {'active', 'inactive'}
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}, not {self.status}.")


@dataclasses.dataclass
class TagList:
    """
    Represents the result of fetching a list of tags from a Docker registry.

    Attributes:
        count (int): The total number of tags available.
        next (Optional[str]): The URL to the next page of tags, or None if this is the last page.
        previous (Optional[str]): The URL to the previous page of tags, or None if this is the first page.
        results (List[Tag]): The list of tags fetched.
    """
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Tag]
