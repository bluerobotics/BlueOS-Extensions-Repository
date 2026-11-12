#!/usr/bin/env python3
import sys
from pathlib import Path

import json5
from extension.models import ExtensionMetadata

REPOS_FOLDER = Path(__file__).parent.parent.joinpath("repos")


def main() -> None:
    errors = []
    for path in sorted(REPOS_FOLDER.glob("**/metadata.json")):
        try:
            data = json5.loads(path.read_text(encoding="utf-8"))
            ExtensionMetadata(
                identifier=path.parent.relative_to(REPOS_FOLDER).as_posix(),
                name=data["name"],
                website=data["website"],
                docker=data["docker"],
                description=data["description"],
            )
        except Exception as exception:  # pylint: disable=broad-except
            errors.append(f"{path.relative_to(REPOS_FOLDER)}: {exception!r}")

    if errors:
        sys.exit("Invalid metadata:\n" + "\n".join(errors))


if __name__ == "__main__":
    main()
