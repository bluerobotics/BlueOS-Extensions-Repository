import dataclasses
from typing import Dict, List, Optional


@dataclasses.dataclass
class BlobConfig:
    """
    Represents a blob configuration in the Docker Registry.

    Attributes:
        Env (List[str]): Environment variables of the blob.
        Labels (Dict[str, str]): Labels of the blob.
    """

    Env: List[str]  # pylint: disable=invalid-name
    Labels: Dict[str, str]  # pylint: disable=invalid-name


@dataclasses.dataclass
class Blob:
    """
    Represents a blob in the Docker Registry. Currently not complete, only
    including what we need

    Attributes:
        config (BlobConfig): Configuration of the blob.
        architecture (str): Architecture of the blob.
        os (str): OS of the blob.
    """

    config: BlobConfig
    architecture: Optional[str] = None
    os: Optional[str] = None  # pylint: disable=invalid-name
