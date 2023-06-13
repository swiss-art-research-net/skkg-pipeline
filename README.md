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

To limit the pipeline to a subset of records use the `--limit` parameter.

```sh
docker compose exec jobs task -- --limit 20
```

To list available tasks, run:

```sh
docker compose exec jobs task --list
```

This will output a list of tasks:
```
task: Available tasks for this project:
* default:                     Runs the entire pipeline
* download-source-items:       Download the item records from MuseumPlus
```

To run a specific task type `task` followed by the task name, e.g.:

```sh
docker compose exec jobs task example-task
```

If the task is already up to date, it will not run. To force a task to run, type the command followed by `--force`

```sh
docker compose exec jobs task example-task --force
```

To add additional arguments to the task itself, enter the arguments after a `--` sign, e.g.:

```sh
docker compose exec jobs task example-task -- --limit 100
```
