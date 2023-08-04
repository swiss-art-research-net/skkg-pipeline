"""
Script to prepare data for mapping.
This script will take the XML files from the input folder and copy them to the output folder.
The script will only copy files that have been updated since the last mapping.

Usage:
    python prepareDataForMapping.py --module <module> --inputFolder <inputFolder> --outputFolder <outputFolder> [--limit <limit>] [--offset <offset>]

Arguments:
    --module: Name of the module to process the data form
    --inputFolder: Folder where the XML files are stored.
    --outputFolder: Folder to put the XML files that should be mapped.
    --limit: Limit the number of items to process.
    --offset: Offset the items to process.
"""

import argparse
from datetime import datetime
from os import listdir
from os.path import join, isfile

from lib.Metadata import ItemMetadata

def prepareDataForMapping(*, module, inputFolder, outputFolder, limit=None, offset=None):
    metadata = ItemMetadata(inputFolder)
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.xml')]
    filesToMap = []
    
    if limit is None:
        limit = len(files)
    else:
        limit = int(limit)
    if offset is None:
        offset = 0
    else:
        offset = int(offset)

    for file in files[offset:offset+limit]:
        if shouldBeMapped(file=file, metadata=metadata):
            filesToMap.append(file)
            prepareFileForMapping(file=file, inputFolder=inputFolder, outputFolder=outputFolder)
    if len(filesToMap) < limit:
        print(f"Prepared {len(filesToMap)} files for mapping. {limit - len(filesToMap)} files do not need to be mapped.")
    else:
        print(f"Prepared {len(filesToMap)} files for mapping")

def prepareFileForMapping(*, file, inputFolder, outputFolder):
    # TODO: This function currently only copies the file from the input folder to the output folder,
    # removing the XML namespace for compatibility with the X3ML mapping.
    # Later on this function will also take care of preprocessing the data for mapping.
    with open(join(inputFolder, file), 'r') as f:
        with open(join(outputFolder, file), 'w') as g:
            contents = f.read()
            contents = contents.replace('xmlns="http://www.zetcom.com/ria/ws/module"', '')
            g.write(contents)

def shouldBeMapped(*, file, metadata):
    lastMapped = metadata.getLastMappedDateForFile(file)
    if lastMapped is None:
        return True
    lastUpdated = metadata.getLastUpdatedDateForFile(file)
    # Check if lastUpdated is later than lastMapped
    if lastUpdated is not None and datetime.strptime(lastUpdated, '%Y-%m-%d %H:%M:%S.%f') > datetime.strptime(lastMapped, '%Y-%m-%d %H:%M:%S.%f'):
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description = 'Prepare data for mapping')
    parser.add_argument('--module', required= True, help='Name of the module to process the data form')
    parser.add_argument('--inputFolder', required= True, help='Folder where the XML files are stored.')
    parser.add_argument('--outputFolder', required= True, help='Folder to put the XML files that should be mapped.')
    parser.add_argument('--limit', required= False, help='Limit the number of items to process.')
    parser.add_argument('--offset', required= False, help='Offset the items to process.')
    args = parser.parse_args()

    prepareDataForMapping(module=args.module, inputFolder=args.inputFolder, outputFolder=args.outputFolder, limit=args.limit, offset=args.offset)
