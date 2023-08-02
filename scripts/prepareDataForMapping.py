
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

    print(f"Prepared {len(filesToMap)} files for mapping")

def prepareFileForMapping(*, file, inputFolder, outputFolder):
    # Copy file from inputFolder to outputFolder
    with open(join(inputFolder, file), 'r') as f:
        with open(join(outputFolder, file), 'w') as g:
            g.write(f.read())

def shouldBeMapped(*, file, metadata):
    lastMapped = metadata.getLastMappedDateForFile(file)
    if lastMapped is None:
        print(f"No date for {file}. File should be mapped")
        return True
    lastUpdated = metadata.getLastUpdatedDateForFile(file)
    # Check if lastUpdated is later than lastMapped
    if lastUpdated is not None and datetime.strptime(lastUpdated, '%Y-%m-%d %H:%M:%S.%f') > datetime.strptime(lastMapped, '%Y-%m-%d %H:%M:%S.%f'):
        print(f"File {file} was updated since last map. File should be mapped")
        return True
    print(f"File {file} does not need to be mapped")
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
