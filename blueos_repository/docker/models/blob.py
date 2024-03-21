import dataclasses
from typing import Optional, List, Dict


@dataclasses.dataclass
class BlobConfig:
    """
    Represents a blob configuration in the Docker Registry.

    Attributes:
        Env (List[str]): Environment variables of the blob.
        Entrypoint (List[str]): Entrypoint of the blob.
        Labels (Dict[str, str]): Labels of the blob.
        OnBuild (Optional[str]): OnBuild of the blob.
    """

    Env: List[str]
    Entrypoint: List[str]
    Labels: Dict[str, str]
    OnBuild: Optional[str] = None


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
    os: Optional[str] = None
