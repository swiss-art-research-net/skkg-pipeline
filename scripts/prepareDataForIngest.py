"""
Script to prepare data for ingest.
This script will copy the TTL files that have not been ingested after the last mapping into a new folder.
The script also takes the folder of the XML files as input to retrieve the metadata.

"""

import argparse
from datetime import datetime
from os import listdir
from os.path import join, isfile

from lib.Metadata import ItemMetadata

def prepareDataForIngest(*, inputFolder, outputFolder, xmlFolder):
    metadata = ItemMetadata(xmlFolder)
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.ttl')]
    filesToIngest = []

    for file in files:
        if shouldBeIngested(file=file, metadata=metadata):
            filesToIngest.append(file)
            prepareFileForIngest(file=file, inputFolder=inputFolder, outputFolder=outputFolder)
    if len(filesToIngest) < len(files):
        print(f"Prepared {len(filesToIngest)} files for ingest. {len(files) - len(filesToIngest)} files do not need to be ingested.")
    else:
        print(f"Prepared {len(filesToIngest)} files for ingest")

def prepareFileForIngest(*, file, inputFolder, outputFolder):
    with open(join(inputFolder, file), 'r') as f:
        with open(join(outputFolder, file), 'w') as g:
            contents = f.read()
            g.write(contents)

def shouldBeIngested(*, file, metadata):
    fileKey = file.replace('.ttl', '.xml')
    lastIngested = metadata.getLastIngestedDateForFile(fileKey)
    if lastIngested is None:
        return True
    lastMapped = metadata.getLastMappedDateForFile(fileKey)
    # Check if the file has been mapped after the last ingest
    if lastMapped is not None and datetime.strptime(lastMapped, '%Y-%m-%d %H:%M:%S.%f') > datetime.strptime(lastIngested, '%Y-%m-%d %H:%M:%S.%f'):
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description = 'Prepare data for mapping')
    parser.add_argument('--inputFolder', required= True, help='Folder where the TTL files are stored.')
    parser.add_argument('--outputFolder', required= True, help='Folder to put the TTL files that should be ingested.')
    parser.add_argument('--xmlFolder', required= True, help='Folder where the XML files are stored.')
    args = parser.parse_args()

    prepareDataForIngest(inputFolder=args.inputFolder, outputFolder=args.outputFolder, xmlFolder=args.xmlFolder)
