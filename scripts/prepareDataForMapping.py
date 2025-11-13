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
    --ids: List of ids to process. If this argument is given, the script will ignore the limit and offset arguments.
"""

import argparse
from lib.Preprocessor import getPreprocessor
import lib.SkkgPreprocessors # To ensure SKKG Preprocessors are registered
from datetime import datetime
from os import listdir
from os.path import join, isfile

from lib.Metadata import ItemMetadata

def prepareDataForMapping(*, module, inputFolder, outputFolder, filenamePrefix='item-', limit=None, offset=None, ids=None):
    metadata = ItemMetadata(inputFolder)
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.xml')]
    filesToMap = []
    
    if ids is not None:
        # Filenames are of the shape {module}-{filenamePrefix}{id}.xml
        # Hence we extract the id from the filename by removing the module and the filenamePrefix
        files = [f for f in files if f.split(f'{module.lower()}-{filenamePrefix}')[1].replace('.xml', '') in ids]
    if limit is None or ids is not None:
        limit = len(files)
    else:
        limit = int(limit)
    if offset is None or ids is not None:
        offset = 0
    else:
        offset = int(offset)

    preprocessor = getPreprocessor(module)

    for file in files[offset:offset+limit]:
        if ids is not None or shouldBeMapped(file=file, metadata=metadata):
            filesToMap.append(file)
            prepareFileForMapping(file=file, inputFolder=inputFolder, outputFolder=outputFolder, preprocessor=preprocessor)
    if len(filesToMap) < limit:
        print(f"Prepared {len(filesToMap)} {module} items for mapping. {limit - len(filesToMap)} items do not need to be mapped.")
    else:
        print(f"Prepared {len(filesToMap)} {module} items for mapping")

def prepareFileForMapping(*, file, inputFolder, outputFolder, preprocessor):
    with open(join(inputFolder, file), 'r') as f:
        with open(join(outputFolder, file), 'w') as g:
            contents = f.read()
            contents = preprocessor.preprocess(contents)
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

    parser = argparse.ArgumentParser(description='Prepare data for mapping', allow_abbrev=False)
    parser.add_argument('--module', required=True, help='Name of the module to process the data form')
    parser.add_argument('--inputFolder', required=True, help='Folder where the XML files are stored.')
    parser.add_argument('--outputFolder', required=True, help='Folder to put the XML files that should be mapped.')
    parser.add_argument('--limit', required=False, help='Limit the number of items to process.')
    parser.add_argument('--offset', required=False, help='Offset the items to process.')
    parser.add_argument('--ids', required=False, help='List of ids to process. If this argument is given, the script will ignore the limit and offset arguments.')
    parser.add_argument('--filenamePrefix', required=False, help='Prefix to use for the filenames of the XML files. Required when using ids argument. Defaults to "item-"')
    args, _ = parser.parse_known_args()

    if args.ids is not None:
        args.ids = args.ids.split(',')

    if args.filenamePrefix is None:
        args.filenamePrefix = 'item-'

    prepareDataForMapping(module=args.module, inputFolder=args.inputFolder, outputFolder=args.outputFolder, limit=args.limit, offset=args.offset, ids=args.ids, filenamePrefix=args.filenamePrefix)
