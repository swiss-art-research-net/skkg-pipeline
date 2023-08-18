# SKKG Pipeline

## About

This contains the pipeline for the Sammlung Digital project by the [Stiftung für Kunst und Kultur (SKKG)](https://www.skkg.ch/)

## How to use

Prerequisites: [Docker](http://docker.io) including Docker Compose

Copy and (if required) edit the .env.example
```
cp .env.example .env
```

Run the project with
```
docker compose up -d
```

## Initialisation

To include the [SKKG App](https://github.com/swiss-art-research-net/skkg-app) when cloning, clone with:
```
git clone --recurse-submodules git@github.com:swiss-art-research-net/skkg-pipeline.git
```

To download the source data create a [GitHub personal access token](https://github.com/settings/tokens) and add it to the `.env` file, along with your username.

Download the source files by runnning
```sh
bash downloadSources.sh
```

### Tasks

The pipeline can be controlled by the Task runner. To run the entire pipeline, run

```sh
docker compose exec jobs task
```

To list available tasks, run:

```sh
docker compose exec jobs task --list
```

This will output a list of tasks:
```
task: Available tasks for this project:
* default:                                 Runs the entire pipeline
* download-address-items:                  Download the address item records from MuseumPlus
* download-literature-items:               Download the literature item records from MuseumPlus
* download-object-items:                   Download the object item records from MuseumPlus
* download-person-items:                   Download the person item records from MuseumPlus
* download-source-items:                   Downloads all item records from MuseumPlus
* generate-example-record-object:          Generates an example record for developing the mapping in the X3ML editor
* generate-example-record-person:          Generates an example record for developing the mapping in the X3ML editor
* ingest-items:                            Ingest items for all modules
* ingest-object-items:                     Ingests the object items into the triplestore
* ingest-ontologies:                       Ingests the ontologies into individual named Graphs
* ingest-person-items:                     Ingests the person items into the triplestore
* perform-mapping-for-object-items:        Performs the mapping for the object items
* perform-mapping-for-person-items:        Performs the mapping for the person items
* prepare-and-perform-mapping:             Prepares and performs the mapping for all modules
* prepare-mapping-for-address-items:       Prepares the mapping for the object items
* prepare-mapping-for-object-items:        Prepares the mapping for the object items
* prepare-mapping-for-person-items:        Prepares the mapping for the person items
* recreate-folder-metadata:                Recreate the metadata for a specific folder. The folder name should be passed as an argument.
* remove-deleted-address-items:            Removes address item records that have been deleted from MuseumPlus
* remove-deleted-literature-items:         Removes literature item records that have been deleted from MuseumPlus
* remove-deleted-object-items:             Removes object item records that have been deleted from MuseumPlus
* remove-deleted-person-items:             Removes person item records that have been deleted from MuseumPlus
* remove-deleted-source-items:             Removes item records that have been deleted from MuseumPlus
* reset-last-mapped-metadata:              Resets the last mapped metadata for a specific module. The module name should be passed as an argument.
```

To run a specific task type `task` followed by the task name, e.g.:

```sh
docker compose exec jobs task download-object-items
```

If the task is already up to date, it will not run. To force a task to run, type the command followed by `--force`

```sh
docker compose exec jobs task download-object-items --force
```

To add additional arguments to the task itself, enter the arguments after a `--` sign, e.g.:

```sh
docker compose exec jobs task download-object-items -- --limit 100
```
