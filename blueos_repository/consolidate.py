#!/usr/bin/env python3
import asyncio
import dataclasses
from typing import Dict, AsyncIterable
from pathlib import Path
# Extensions
from extension.extension import Extension
from extension.models import ExtensionMetadata, ExtensionVersion
# Extra
import json
import json5
from utils import EnhancedJSONEncoder


# This is the name manifest file that will be generated
MANIFEST_FILE = "manifest.json"

# This is the root URL for the public repository
REPO_ROOT_URL = "https://raw.githubusercontent.com/bluerobotics/BlueOS-Extensions-Repository/master/repos"


@dataclasses.dataclass
class RepositoryEntry(ExtensionMetadata):
    """
    Represents a repository entry in the manifest output

    Attributes:
        versions (Dict[str, Version]): Available extension versions.
    """

    versions: Dict[str, ExtensionVersion] = dataclasses.field(default_factory=dict)


class Consolidator:
    """
    This class is used to consolidate the BlueOS extensions repository generating
    a manifest file with all the extensions available and their versions.
    """

    @staticmethod
    def repo_folder() -> Path:
        return Path(__file__).parent.parent.joinpath("repos")


    async def fetch_extensions_metadata(self) ->  AsyncIterable[ExtensionMetadata]:
        """
        Fetch the metadata for all the extensions in the repository.

        Returns:
            List[ExtensionMetadata]: List of all the extensions metadata.
        """

        repos = self.repo_folder()

        for repo in repos.glob("**/metadata.json"):
            with open(repo, "r", encoding="utf-8") as metadata_file:
                company, extension_name = repo.as_posix().split("/")[-3:-1]
                identifier = ".".join([company, extension_name])

                try:
                    data = json5.load(metadata_file)
                except Exception as error:
                    print(f" INVALID-EXTENSION - Skipping {repo}, unable to parse metadata file, exception: {error}")
                    continue

                company_logo = (repo / "../../company_logo.png").resolve().relative_to(repos.resolve())
                extension_logo_file = (repo / "../extension_logo.png").resolve()

                if extension_logo_file.exists():
                    extension_logo = extension_logo_file.resolve().relative_to(repos.resolve())
                else:
                    extension_logo = company_logo

                try:
                    remote_extension_logo = f"{REPO_ROOT_URL}/{extension_logo}" if extension_logo else None
                    remote_company_logo = f"{REPO_ROOT_URL}/{company_logo}" if company_logo else None

                    metadata = ExtensionMetadata(
                        identifier=identifier,
                        name=data["name"],
                        docker=data["docker"],
                        description=data["description"],
                        website=data["website"],
                        extension_logo=remote_extension_logo,
                        company_logo=remote_company_logo,
                    )

                    yield metadata
                except Exception as error:
                    print(f"INVALID-EXTENSION - Skipping {repo}, invalid metadata file, exception: {error}")
                    continue


    async def run(self) -> None:
        extensions = [Extension(metadata) async for metadata in self.fetch_extensions_metadata()]

        await asyncio.gather(*(ext.inflate() for ext in extensions))

        consolidated_data = [
            RepositoryEntry(
                **dataclasses.asdict(ext.metadata),
                versions=ext.versions
            )
            for ext in extensions if ext.versions
        ]

        with open(MANIFEST_FILE, "w", encoding="utf-8") as manifest_file:
            manifest_file.write(json.dumps(consolidated_data, indent=4, cls=EnhancedJSONEncoder))


consolidator = Consolidator()
asyncio.run(consolidator.run())
