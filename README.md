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
* create-blazegraph-backup:                                          Creates a compressed Blazegraph backup
* create-data-dump:                                                  Creates a TTL dump of the data generated by the pipeline
* default:                                                           Runs the entire pipeline
* download-items-for-module:                                         Downloads the item records for a specific module from MuseumPlus. Pass the module name as command line argument
* download-source-items:                                             Downloads all item records from MuseumPlus
* download-source-vocabularies:                                      Downloads all vocabularies from MuseumPlus
* execute-query-from-file:                                           Execute a query against the main Blazegraph instance. Pass the path to the file as command line argument
* first-run:                                                         Task to run when the pipeline is run for the first time
* generate-example-record-address:                                   Generates an example Address record for developing the mapping in the X3ML editor
* generate-example-record-exhibition:                                Generates an example Exhibition record for developing the mapping in the X3ML editor
* generate-example-record-literature:                                Generates an example Literature record for developing the mapping in the X3ML editor
* generate-example-record-multimedia:                                Generates an example Multimedia record for developing the mapping in the X3ML editor
* generate-example-record-object:                                    Generates an example Object record for developing the mapping in the X3ML editor
* generate-example-record-person:                                    Generates an example Person record for developing the mapping in the X3ML editor
* generate-example-record-registrar:                                 Generates an example Registrar record for developing the mapping in the X3ML editor
* generate-field-definitions:                                        Generates the field definitions for the platform based on the fieldDefinitions.yml file
* generate-mapping-file-from-3m:                                     Generates a mapping file from data stored in the 3M Editor.
* ingest-classifications:                                            Ingest classifications into the triplestore
* ingest-iiif:                                                       Ingest IIIF data into the triplestore
* ingest-items:                                                      Ingest items for all modules. Add --debug true To see the response from the triplestore
* ingest-module-items:                                               Ingests the items for a specific module. The module name should be passed as an argument or via the MODULE variable.
* ingest-ontologies:                                                 Ingests the ontologies into individual named Graphs
* ingest-platform-data:                                              Ingests the data used for the operation of the platform
* perform-mapping-for-module-items:                                  Performs the mapping for a specific module. The module name should be passed as an argument or via the MODULE variable.
* perform-mapping-for-vocabularies:                                  Performs the mapping for the vocabularies
* prepare-and-perform-mapping-for-iiif:                              Performs the mapping for the IIIF data
* prepare-and-perform-mapping-for-items:                             Prepares and performs the mapping for all modules
* prepare-mapping-for-module-items:                                  Prepares the mapping for a specific module. The module name should be passed as an argument or via the MODULE variable.
* push-latest-data-dump:                                             Upload latest data dump to S3 endpoint for data sharing
* recreate-folder-metadata:                                          Recreate the metadata for a specific module. The module name should be passed as an argument or via the MODULE variable.
* remove-items-without-equivalent-ttl-from-triplestore:              Removes all item records from the triplestore that do not have an equivalent TTL file
* remove-module-items-from-triplestore:                              Removes all item records for a specific module from the triplestore. The module name should be passed as an argument or via the MODULE variable.
* remove-module-items-without-equivalent-ttl-from-triplestore:       Removes all item records for a specific module from the triplestore that do not have an equivalent TTL file. The module name should be passed as an argument or via the MODULE variable.
* remove-unpublished-items:                                          Removes all item records that have been unpublished from MuseumPlus
* remove-unpublished-module-items:                                   Removes item records that have been unpublished from MuseumPlus for a specific module. The module name should be passed as an argument or via the MODULE variable.
* reset:                                                             Delete all artefacts produced by the pipeline.
* reset-iiif:                                                        Delete all artefacts produced by the pipeline for the iiif data.
* reset-last-ingested-metadata:                                      Resets the last ingested metadata for a specific module. The module name should be passed as an argument or via the MODULE variable.
* reset-last-mapped-metadata:                                        Resets the last mapped metadata for a specific module. The module name should be passed as an argument or via the MODULE variable.
* reset-module:                                                      Delete all artefacts produced by the pipeline for a given module. The module name should be passed as an argument or via the MODULE variable.
* reset-vocabularies:                                                Delete all artefacts produced by the pipeline for the vocabularies.
* retrieve-and-ingest-additional-data:                               Retrieve and ingest additional data for external URIs in the Triple Store
* retrieve-iiif-data:                                                Downloads and prepares data related to the IIIF images
* run-pipeline-cycles:                                               Runs the entire pipeline as well as certain tasks according to a specific interval. When this task is executed, each step of the pipeline will be run if the interval has passed since the last execution of the task. The interval is defined in the vars section of each task.
* suggest-alignments-for-vocabularies:                               Suggest alignments for all vocabularies with GND data
* update-iiif:                                                       Downloads, maps, and ingests the IIIF data
* update-vocabularies:                                               Downloads, maps, and ingests the vocabularies
* validate-turtle-file:                                              Validate a Turtle file using SHACL. Pass the file to validate through command line argument
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
| `reset-last-ingested-metadata` | Resets the last ingested metadata for a specific module. The module name should be passed as an argument. | `docker compose exec jobs task reset-last-ingested-metadata -- {module}` where `{module}` is the name of the module (e.g. `object`, `person`, `address`)
| `reset-last-mapped-metadata` | Resets the last mapped metadata for a specific module. The module name should be passed as an argument. | `docker compose exec jobs task reset-last-mapped-metadata -- {module}` where `{module}` is the name of the module
| `reset-module -- {module}` | Deletes all artefacts generated by the pipeline for a given module, leaving the source data intact.
| `remove-module-items-from-triplestore -- {module}` | Removes all item records for a specific module from the triplestore. The module name should be passed as an argument. Useful when the query for retreiving module item has been changed and items that are no longer returned should be removed. | `docker compose exec jobs task remove-module-items-from-triplestore -- {module}` where `{module}` is the name of the module
| `update-vocabularies` | Downloads, maps, and ingests the vocabularies | `docker compose exec jobs task update-vocabularies` |
| `recreate-folder-metadata` | If the folder metadata is lost or gets corrupted, it can be recreated using this tasks | `docker compose exec jobs task recreate-folder-metadata -- {module}` where `{module}` is the name of the folder to recreate the metadata for, e.g. `object`, `person` or `address`
| `un-pipeline-cycles` | Runs the pipeline as well as certain tasks, such as updating the vocabularies, according to a specific interval. When this task is executed, each step of the pipeline will be run if the interval has passed since the last execution of the task. The interval is defined in the vars section of each commend. | `docker compose exec jobs task run-pipeline-cycles`
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
- **secrets** Contains secrets, e.g. the aws access credentials for uploading the data to S3
- **services** Contains relevant files for the Docker-based services used in the Pipeline
