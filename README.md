# SKKG Pipeline

## About

The repository contains the pipeline for the Sammlung Digital project by the [Stiftung für Kunst und Kultur (SKKG)](https://www.skkg.ch/).

This code is published primarily for the sake of transparency and to share our work with the community. Please note that this pipeline was developed for SKKG and their use case, and may not be directly applicable to other projects. While we encourage reusing all or parts of this code we also want to emphasise that this project is a work in progress and may contain bugs or incomplete features. 

Please note that we cannot be responsible for any issues or damages resulting from the use of this code, and that it comes with no warranties or guarantees of suitability for any specific purpose. In using this code, you agree to do so at your own risk and responsibility.

## Table of contents

- [How to use](#how-to-use)
- [Initialisation](#initialisation)
  - [Running the pipeline](#running-the-pipeline)
- [Tasks](#tasks)
    - [Useful tasks](#useful-tasks)
- [Folder structure](#folder-structure)
## How to use

Prerequisites: [Docker](http://docker.io) including Docker Compose

Copy and (if required) edit the `.env.example`
```sh
cp .env.example .env
```

If using the S3 storage, copy and edit the `credentials.example` file in `secrets/aws`

```sh
cp secrets/aws/credentials.example secrets/aws/credentials
```

Run the project with
```sh
docker compose up -d
```

## Initialisation

To include the [SKKG App](https://github.com/swiss-art-research-net/skkg-app) when cloning, clone with:
```sh
git clone --recurse-submodules git@github.com:swiss-art-research-net/skkg-pipeline.git
```

To download the source data create a [GitHub personal access token](https://github.com/settings/tokens) and add it to the `.env` file, along with your username.

Download the source files by runnning
```sh
bash downloadSources.sh
```

### Running the pipeline

The pipeline can be controlled by the Task runner. When running the pipeline for the first time, run
```sh
docker compose exec jobs task first-run
```

To subsequently run the entire pipeline, run

```sh
docker compose exec jobs task
```

## Tasks

The pipeline is can be controlled by the [Task](https://taskfile.dev/#/) runner. The tasks are defined in the `Taskfile.yml` file.

To list available tasks, run:

```sh
docker compose exec jobs task --list
```

This will output a list of tasks:
```
task: Available tasks for this project:
* create-blazegraph-backup:                   Creates a compressed Blazegraph backup
* default:                                    Runs the entire pipeline
* download-address-items:                     Download the address item records from MuseumPlus
* download-literature-items:                  Download the literature item records from MuseumPlus
* download-multimedia-items:                  Download the multimedia item records from MuseumPlus
* download-object-items:                      Download the object item records from MuseumPlus
* download-person-items:                      Download the person item records from MuseumPlus
* download-source-items:                      Downloads all item records from MuseumPlus
* download-source-vocabularies:               Downloads all vocabularies from MuseumPlus
* execute-query-from-file:                    Execute a query against the main Blazegraph instance. Pass the path to the file as command line argument
* first-run:                                  Task to run when the pipeline is run for the first time
* generate-example-record-multimedia:         Generates an example record for developing the mapping in the X3ML editor
* generate-example-record-object:             Generates an example record for developing the mapping in the X3ML editor
* generate-example-record-person:             Generates an example record for developing the mapping in the X3ML editor
* generate-field-definitions:                 Generates the field definitions for the platform based on the fieldDefinitions.yml file
* ingest-classifications:                     Ingest classifications into the triplestore
* ingest-items:                               Ingest items for all modules. Add --debug true To see the response from the triplestore
* ingest-multimedia-items:                    Ingests the multimedia items into the triplestore
* ingest-object-items:                        Ingests the object items into the triplestore
* ingest-ontologies:                          Ingests the ontologies into individual named Graphs
* ingest-person-items:                        Ingests the person items into the triplestore
* ingest-platform-data:                       Ingests the data used for the operation of the platform
* perform-mapping-for-multimedia-items:       Performs the mapping for the multimedia items
* perform-mapping-for-object-items:           Performs the mapping for the object items
* perform-mapping-for-person-items:           Performs the mapping for the person items
* perform-mapping-for-vocabularies:           Performs the mapping for the vocabularies
* prepare-and-perform-mapping:                Prepares and performs the mapping for all modules
* prepare-mapping-for-address-items:          Prepares the mapping for the object items
* prepare-mapping-for-multimedia-items:       Prepares the mapping for the multimedia items
* prepare-mapping-for-object-items:           Prepares the mapping for the object items
* prepare-mapping-for-person-items:           Prepares the mapping for the person items
* recreate-folder-metadata:                   Recreate the metadata for a specific module. The module name should be passed as an argument or via the MODULE variable.
* remove-deleted-address-items:               Removes address item records that have been deleted from MuseumPlus
* remove-deleted-literature-items:            Removes literature item records that have been deleted from MuseumPlus
* remove-deleted-multimedia-items:            Removes multimedia item records that have been deleted from MuseumPlus
* remove-deleted-object-items:                Removes object item records that have been deleted from MuseumPlus
* remove-deleted-person-items:                Removes person item records that have been deleted from MuseumPlus
* remove-deleted-source-items:                Removes item records that have been deleted from MuseumPlus
* reset:                                      Delete all artefacts produced by the pipeline.
* reset-last-ingested-metadata:               Resets the last ingested metadata for a specific module. The module name should be passed as an argument.
* reset-last-mapped-metadata:                 Resets the last mapped metadata for a specific module. The module name should be passed as an argument.
* reset-module:                               Delete all artefacts produced by the pipeline for a given module. The module name should be passed as an argument or via the MODULE variable.
* reset-vocabularies:                         Delete all artefacts produced by the pipeline for the vocabularies.
* retrieve-and-ingest-additional-data:        Retrieve and ingest additional data for external URIs in the Triple Store
* suggest-alignments-for-vocabularies:        Suggest alignments for all vocabularies with GND data
* update-vocabularies:                        Downloads, maps, and ingests the vocabularies
* validate-turtle-file:                       Validate a Turtle file using SHACL. Pass the file to validate through command line argument
```

To run a specific task type `task` followed by the task name, e.g.:

```sh
docker compose exec jobs task ingest-items
```

If the task is already up to date, it will not run. To force a task to run, type the command followed by `--force`

```sh
docker compose exec jobs task ingest-items --force
```

To add additional arguments to the task itself, enter the arguments after a `--` sign, e.g.:

```sh
docker compose exec jobs task reset-last-mapped-metadata -- object
```

###  Useful tasks

| Name | Description | Usage
--- | --- | ---
| `reset-last-ingested-metadata` | Resets the last ingested metadata for a specific module. The module name should be passed as an argument. | `docker compose exec jobs task reset-last-ingested-metadata -- {module}` where `{module}` can be `object`, `person` or `address`
| `reset-last-mapped-metadata` | Resets the last mapped metadata for a specific module. The module name should be passed as an argument. | `docker compose exec jobs task reset-last-mapped-metadata -- {module}` where `{module}` can be `object`, `person` or `address`
| `update-vocabularies` | Downloads, maps, and ingests the vocabularies | `docker compose exec jobs task update-vocabularies` |
| `recreate-folder-metadata` | If the folder metadata is lost or gets corrupted, it can be recreated using this tasks | `docker compose exec jobs task recreate-folder-metadata -- {module}` where `{module}` is the name of the folder to recreate the metadata for, e.g. `object`, `person` or `address`
| `generate-field-definitions` | Generates the field definitions for the platform based on the fieldDefinitions.yml file | `docker compose exec jobs task generate-field-definitions`

## Folder structure

The pipeline stores everything as individual files (instead of relying on a database). The folder structure is as follows:

- **data**
  - **platform** Contains data that is used for the operation of the platform
  - **source** Contains the source files obtained from MuseumPlus
    - ***{module}*** Contains the module items as XML files. There is an individual folder per module.
    - **vocabularies** Contains the vocabulary nodes
  - **temp** Folder to store temporary data
    - **download** Temporary data used during the download process
      - **temp_*{module}*** Temporary data used during the download process. There is an individual folder per module so a download can be resumed if it fails.
    - **ingest**
      - ***{module}*** Files that need to be ingested into Blazegraph will be temporarily stored here. There is an individual folder per module.
  - **ttl** Contains RDF data. This can include mapped source data as well as additional data.
    - **main** Contains the main RDF data
      - ***{module}*** Contains the RDF data for each module as Turtle files. There is an individual folder per module.
      - **vocabularies** Contains the RDF data for the vocabularies as Turtle files.
    - **additional** Contains additional RDF data, such as data retrieved from external soures
- **logs** Contains log files
- **mapping** Contains mapping specifications as well as other relevant data for mapping
  - **input** Mapping input data will be (temporarily) stored here
    - ***{module}*** Temporary storage for the mapping input data for each module. There is an individual folder per 
    module.
  - **output** Mapping output data will be (temporarily) stored here
    - ***{module}*** Temporary storage for the mapping output data for each module. There is an individual folder per module. Sucessfully mapped data will be moved to *data/ttl/main/{module}*
  - **schemas** Contains RDFS schemas for the ontologies used in the mapping
- **scripts** Contains scripts, mostly in Python or bash, used for more complex tasks in the pipeline. This folder also contains the Task definitions.
- **services** Contains relevant files for the Docker-based services used in the Pipeline
