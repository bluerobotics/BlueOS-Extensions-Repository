# BlueOS-Extensions-Repository

This is a repository for metadata of BlueOS Extensions.

- [Documentation](https://blueos.cloud/docs/latest/development/extensions/)
- [Available Extensions](https://docs.bluerobotics.com/BlueOS-Extensions-Repository)
- [Community Extensions, Tools, and Examples](https://github.com/BlueOS-Community/)

---

For publishing a new extension, open a pull request to this repository with the following structure:

## Data in this repository

1. Extension registration metadata: `/repos/yourcompany/yourextension/metadata.json`
    ```json
    {
        "name": "The Name of Your Extension",
        "website": "https://your.extension.website.com/",
        "docker": "your-dockerhub-user/your-extension-docker",
        "description": "A brief description of your extension. This will be shown in the store card."
    }
    ```
1. Your Extension logo: `/repos/yourcompany/yourextension/extension_logo.png`
1. Your company logo: `/repos/yourcompany/company_logo.png`
    - You only need to add this the first time you add an Extension

## Data in DockerHub

Additionally, we have versioned data. This data should be in each of your DockerHub tags, and use the following format:

```Dockerfile
LABEL version="1.0.0"
LABEL permissions='{\
  "ExposedPorts": {\
    "80/tcp": {}\          // we have a server at port 80
  },\
  "HostConfig": {\
    "PortBindings": {\
      "80/tcp": [\         // our server at port 80 is automatically bound to a free port in the host
        {\
          "HostPort": ""\
        }\
      ]\
    }\
  }\
}'
LABEL authors='[\
    {\
        "name": "John Doe",\
        "email": "doe@john.com"\
    }\
]'
LABEL company='{\
  "about": "brief description",\
  "name": "Company/Person Name",\
  "email": "email@company.com"\
}'
LABEL readme="https://raw.githubusercontent.com/username/repo/{tag}/README.md"
LABEL links='{\
  "website": "https://...",\
  "support": "mailto:support@company.com",\
  "documentation": "https://docs.company.com/cool-extension/",\
}'
LABEL type="example"
LABEL tags='[\
  "positioning",\
  "navigation"\
]'
```

 - `version` is the name of the current tag, which we expect to be a valid [semver](https://semver.org/).
 - `permissions`is a json file that follows the [Docker API payload for creating containers](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerCreate).
 - `authors` is a json list of authors of your extension
 - `company` is a json with information about the maintainer responsible for providing new versions
 - `readme` is a URL to a markdown-based README file for the extension
 - `links` is a collection of additional useful/relevant links
 - `type` is a primary categorisation of the extension, and should be one of:
    - "device-integration"
    - "example"
    - "tool"
    - "other"
- `tags` is a collection of relevant tags for filtering, which should be lowercase alpha-numeric with dashes
    - limit of 10 per extension

Some additional information and examples are available in the 
[metadata documentation](https://docs.bluerobotics.com/ardusub-zola/software/onboard/BlueOS-latest/extensions#metadata-dockerfile).

 ## How this repo works

Every time this repo changes, a Github Action runs and goes through all the `.json` files in here. For each of them, it reaches out to DockerHub and fetches all the available tags, extracting the metadata in LABELS and crafting a complete `manifest.json`, which is stored in this repo's `gh-pages` branch.

There is also a [website](https://docs.bluerobotics.com/BlueOS-Extensions-Repository) that gets generated, to show which extensions are currently available in the store.

## Testing the website locally

```bash
# clone and enter the repo
git clone ...
cd BlueOS-Extensions-Repository
# install yarn if necessary (`brew install yarn` on mac)
sudo apt install -y yarn
# install Python dependencies
python -m pip install --upgrade poetry
python -m poetry install
# generate the manifest (takes some time)
python -m poetry run blueos_repository/consolidate.py
# make the manifest accessible to the local website
mv manifest.json website/public/
# install website dependencies
cd website
yarn install --frozen-lockfile
# generate and serve the website locally, in development mode
yarn dev
... # go to http://localhost:3000/ in your browser (may need to refresh if it's not working)
```
