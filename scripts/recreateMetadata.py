"""
Script to recreate the metadata file for a given folder.

Usage:
    python recreateMetadata.py --folder <folder>

Arguments:
    --folder: Folder where the XML files are stored
"""

import argparse
from datetime import datetime
from lxml import etree
from os import listdir
from os.path import join, isfile
from tqdm import tqdm

from lib.Metadata import ItemMetadata

def updateMetadata(*, folder):
    metadata = ItemMetadata(folder)

    files = [f for f in listdir(folder) if isfile(join(folder, f)) and f.endswith('.xml')]
    for file in tqdm(files):
        tree = etree.parse(join(folder, file))
        lastModified = tree.find('.//{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]/{http://www.zetcom.com/ria/ws/module}value').text
        metadata.setLastUpdatedForFile(file, lastModified, write=False)
    metadata.writeMetadata()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Update the metadata file for a given folder')
    parser.add_argument('--folder', required=True, help='Folder where the XML files are found')
    args = parser.parse_args()

    updateMetadata(folder=args.folder)
