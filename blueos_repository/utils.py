import dataclasses
import json
from typing import Any, Dict, Optional, Union

import semver


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    Custom json encoder for dataclasses,
    see https://docs.python.org/3/library/json.html#json.JSONEncoder.default
    Returns a serializable type
    """

    def default(self, o: Any) -> Union[Any, Dict[str, Any]]:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def valid_semver(string: str) -> Optional[semver.VersionInfo]:
    """
    Check if a string is a valid SemVer version.

    Args:
        string (str): The string to check.

    Returns:
        Optional[semver.VersionInfo]: The version if it's valid, otherwise None.
    """

    # We want to allow versions to be prefixed with a 'v'.
    # This is up for discussion
    if string.startswith("v"):
        string = string[1:]
    try:
        return semver.VersionInfo.parse(string)
    except ValueError:
        return None
