#!/bin/bash
source .env
REPO_DATA=swiss-art-research-net/skkg-data

download () {
  repo=$1
  remotepath=$2
  localpath=$3

  echo -n "Downloading $remotepath: "
  python3 scripts/getFileContentsFromGit.py $GITHUB_USERNAME $GITHUB_PERSONAL_ACCESS_TOKEN $repo $remotepath $localpath
}