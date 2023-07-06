import argparse
from datetime import datetime
from os import listdir
from os.path import join, exists, isfile
from tqdm import tqdm
from lxml import etree

from lib.Metadata import ItemMetadata

def updateMetadata(*, folder):
    metadata = ItemMetadata(folder)

    files = [f for f in listdir(folder) if isfile(join(folder, f)) and f.endswith('.xml')]
    for file in tqdm(files):
        tree = etree.parse(join(folder, file))
        lastModified= tree.find('.//{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]/{http://www.zetcom.com/ria/ws/module}value').text
        metadata.setLastUpdatedForFile(file, lastModified, write=False)
    metadata.writeMetadata()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Update the metadata file for a given folder')
    parser.add_argument('--folder', required= True, help='Folder to save the XML files to')
    args = parser.parse_args()

    updateMetadata(folder=args.folder)
