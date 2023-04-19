#!/usr/bin/env python3
import asyncio
import dataclasses
import json
from pathlib import Path
from typing import Any, AsyncIterable, Dict, List, Optional, Union

import aiohttp
import semver
from registry import Registry

REPO_ROOT = "https://raw.githubusercontent.com/bluerobotics/BlueOS-Extensions-Repository/master/"


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


@dataclasses.dataclass
class Author:
    name: str
    email: str

    @staticmethod
    def from_json(json_dict: Dict[str, str]) -> "Author":
        return Author(name=json_dict["name"], email=json_dict["email"])


@dataclasses.dataclass
class Company:
    name: str
    about: Optional[str]
    email: Optional[str]

    @staticmethod
    def from_json(json_dict: Dict[str, str]) -> "Company":
        return Company(name=json_dict["name"], email=json_dict.get("email", None), about=json_dict.get("about", None))


# pylint: disable=too-many-instance-attributes
@dataclasses.dataclass
class Version:
    permissions: Optional[Dict[str, Any]]
    requirements: Optional[str]
    tag: Optional[str]
    website: str
    authors: List[Author]
    docs: Optional[str]
    readme: Optional[str]
    company: Optional[Company]
    support: Optional[str]


@dataclasses.dataclass
class RepositoryEntry:
    identifier: str
    name: str
    description: str
    docker: str
    website: str
    versions: Dict[str, Version]
    extension_logo: Optional[str]
    company_logo: Optional[str]


class Consolidator:
    registry = Registry()
    consolidated_data: List[RepositoryEntry] = []

    @staticmethod
    def repo_folder() -> Path:
        return Path(__file__).parent.parent

    @staticmethod
    async def fetch_readme(url: str) -> str:
        if not url.startswith("http"):
            print(f"Invalid Readme url: {url}")
            return "Readme not provided."
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"Error status {resp.status}")
                    raise Exception(f"Could not get readme {url}: status: {resp.status}")
                if resp.content_type != "text/plain":
                    raise Exception(f"bad response type for readme: {resp.content_type}, expected text/plain")
                return await resp.text()

    async def all_repositories(self) -> AsyncIterable[RepositoryEntry]:
        repos = self.repo_folder()
        for repo in repos.glob("repos/**/metadata.json"):
            with open(repo, "r", encoding="utf-8") as individual_file:
                company, extension_name = repo.as_posix().split("/")[-3:-1]
                identifier = ".".join([company, extension_name])
                try:
                    data = json.load(individual_file)
                except Exception as exc:
                    raise Exception(f"Unable to parse file {repo}") from exc
                company_logo = (repo / "../../company_logo.png").resolve().relative_to(repos.resolve())
                extension_logo_file = (repo / "../extension_logo.png").resolve()
                if extension_logo_file.exists():
                    extension_logo = extension_logo_file.resolve().relative_to(repos.resolve())
                else:
                    extension_logo = company_logo
                try:
                    new_repo = RepositoryEntry(
                        identifier=identifier,
                        name=data["name"],
                        docker=data["docker"],
                        description=data["description"],
                        website=data["website"],
                        extension_logo=f"{REPO_ROOT}/{extension_logo}" if extension_logo else None,
                        versions={},
                        company_logo=f"{REPO_ROOT}/{company_logo}" if company_logo else None,
                    )
                    yield new_repo
                except Exception as error:
                    raise Exception(f"unable to read file {repo}: {error}") from error

    @staticmethod
    def is_valid_semver(string: str) -> bool:
        # We want to allow versions to be prefixed with a 'v'.
        # This is up for discussion
        if string.startswith("v"):
            string = string[1:]
        try:
            semver.VersionInfo.parse(string)
            return True
        except ValueError:
            return False

    async def run(self) -> None:
        async for repository in self.all_repositories():
            for tag in await self.registry.fetch_remote_tags(repository.docker):
                try:
                    if not self.is_valid_semver(tag):
                        print(f"{tag} is not valid SemVer, ignoring it...")
                        continue
                    raw_labels = await self.registry.fetch_labels(f"{repository.docker}:{tag}")
                    permissions = raw_labels.get("permissions", None)
                    website = raw_labels.get("website", None)
                    authors = raw_labels.get("authors", None)
                    docs = raw_labels.get("docs", None)
                    readme = raw_labels.get("readme", None)
                    if readme is not None:
                        readme = readme.replace(r"{tag}", tag)
                    company_raw = raw_labels.get("company", None)
                    company = Company.from_json(json.loads(company_raw)) if company_raw is not None else None
                    support = raw_labels.get("support", None)

                    new_version = Version(
                        permissions=json.loads(permissions) if permissions else None,
                        website=website,
                        authors=json.loads(authors) if authors else [],
                        docs=json.loads(docs) if docs else None,
                        readme=await self.fetch_readme(readme) if readme is not None else None,
                        company=company,
                        support=support,
                        requirements=raw_labels.get("requirements", None),
                        tag=tag,
                    )
                    repository.versions[tag] = new_version
                except KeyError as error:
                    raise Exception(f"unable to parse repository {repository}: {error}") from error
            self.consolidated_data.append(repository)

        with open("manifest.json", "w", encoding="utf-8") as manifest_file:
            manifest_file.write(json.dumps(self.consolidated_data, indent=4, cls=EnhancedJSONEncoder))


consolidator = Consolidator()
asyncio.run(consolidator.run())
