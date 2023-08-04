"""
Update the metadata value for a given key for all the files in a given folder.
The folder that is used to retrieve the list of the file can be different from 
the folder that is used to store the metadata file.

Usage:
    python updateMetadataValueForFiles.py --metadataFolder <metadataFolder> --inputFolder <inputFolder> --key <key> --value <value>

Arguments:
    --metadataFolder: The folder where the metadata file is stored
    --inputFolder: The folder where the XML files are stored whose metadata should be updated
    --key: The key to update
    --value: The value to set for the given key
"""


import argparse

from lib.Metadata import ItemMetadata
from os import listdir
from os.path import isfile, join

def setMetadata(metadataFolder, inputFolder, key, value):
    metadata = ItemMetadata(metadataFolder)
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.xml')]
    print('Updating metadata for {} files'.format(len(files)))
    for file in files:
        metadata.setKeyValueForFile(file, key, value, write=False)
    metadata.writeMetadata()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Update the mapping metadata based on the TTL files in a given folder')
    parser.add_argument('--metadataFolder', required= True, help='Path to the metadata file')
    parser.add_argument('--inputFolder', required= True, help='Folder read the XML files from')
    parser.add_argument('--key', required= True, help='Metadata key to update')
    parser.add_argument('--value', required= True, help='Metadata value to update')

    args = parser.parse_args()

    setMetadata(args.metadataFolder, args.inputFolder, args.key, args.value)