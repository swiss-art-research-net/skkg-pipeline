import argparse
import json
from datetime import datetime
from lxml import etree
from os import listdir, remove as removeFile
from os.path import join, exists, isfile
from tqdm import tqdm

from lib.MuseumPlusConnector import MPWrapper


class ItemMetadata:
    METADATA_FILENAME = 'metadata.json'

    directory = None

    def __init__(self, directory):
        self.directory = directory

    def getLastUpdatedDate(self):
        # Look for metadata file in the output folder
        metadataFilename = join(self.directory, self.METADATA_FILENAME)
        if exists(metadataFilename):
            # Read the metadata file
            with open(metadataFilename, 'r') as f:
                metadata = json.load(f)
            # Get last updated date from metadata
            lastUpdated = metadata['lastUpdated']
        else:
            # Get the last updated date from the existing files
            lastUpdated  = self.getLastUpdatedFromItemFiles(self.directory)
            if lastUpdated:
                # Save the last updated date in a metadata file
                with open(metadataFilename, 'w') as f:
                    json.dump({'lastUpdated': lastUpdated}, f)
        return lastUpdated
    
    def getLastUpdatedFromItemFiles(self):
        # Read all XML files in the input folder
        files = [f for f in listdir(self.directory) if isfile(join(self.directory, f)) and f.endswith('.xml')]
        
        # If no files exist yet, return None
        if len(files) == 0:
            return None

        # Set lastUpdated to a Date object with the lowest possible value
        lastUpdated = datetime.min

        for file in tqdm(files):
            tree = etree.parse(join(self.directory, file))
            lastUpdatedString= tree.find('.//{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]/{http://www.zetcom.com/ria/ws/module}value').text
            lastUpdatedItem = datetime.strptime(lastUpdatedString, '%Y-%m-%d %H:%M:%S.%f')
            if lastUpdatedItem > lastUpdated:
                lastUpdated = lastUpdatedItem
        return lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

    def setLastUpdated(self, lastUpdated):
        metadataFilename = join(self.directory, self.METADATA_FILENAME)
        with open(metadataFilename, 'w') as f:
            json.dump({'lastUpdated': lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f')}, f)


def downloadItems(*, host, username, password, module, outputFolder, tempFolder, filenamePrefix = 'item-', limit = None, offset = None):          
    client = MPWrapper(url=host, username=username, password=password)
    metadata = ItemMetadata(outputFolder)

    # Log the downloaded files
    log = {
        'downloaded': [],
        'existing': [],
        'omitted': []
    }

    lastUpdated = metadata.getLastUpdatedDate();

    # Store the current datetime
    downloadStarted = datetime.now()
    
    # Get the number of items
    numItems = client.getNumberOfItems(module=module, lastUpdated=lastUpdated)
    if numItems > 0:
        if lastUpdated is not None:
            print(f"Retrieving {numItems} items for module {module} (updated after {datetime.strptime(lastUpdated, '%Y-%m-%dT%H:%M:%S.%f').strftime('%d.%m.%Y %H:%M:%S')})")
        else:
            print(f"Retrieving all {numItems} items for module {module}")
    else:
        print(f"No new items found for module {module}")
        metadata.setLastUpdated(downloadStarted)
        return

    if not limit:
        limit = numItems
    if not offset:
        offset = 0

    for i in tqdm(range(offset, offset+limit)):
        filename = join(tempFolder, filenamePrefix + str(i).zfill(6) + ".xml")
        # Check if the file already exists
        if not exists(filename):
            try:
                item = client.getItemByOffset(i, module=module, lastUpdated=lastUpdated)
            except:
                log['omitted'].append(filename)
                continue
            with open(filename, 'wb') as f:
                f.write(etree.tostring(item, pretty_print=True))
                log['downloaded'].append(filename)
        else:
            log['existing'].append(filename)

    renameItemsBasedOnIds(inputFolder=tempFolder, outputFolder=outputFolder, filenamePrefix=filenamePrefix)

    metadata.setLastUpdated(downloadStarted)

    print(f"Downloaded {len(log['downloaded'])} items.")
    print(f"Skipped {len(log['existing'])} items that already existed.")
    if len(log['omitted']) > 0:
        print(f"Omitted {len(log['omitted'])} items that could not be downloaded.")
        # List omitted files
        print("Omitted files:")
        for file in log['omitted']:
            print(file)

def renameItemsBasedOnIds(*, inputFolder, outputFolder, filenamePrefix):
    # Read all XML files in the input folder
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.xml')]
    for file in tqdm(files):
        # Retrieve the id and uuid attributes from the moduleItem element
        tree = etree.parse(join(inputFolder, file))
        id = tree.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('id')
        #uuid = tree.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('uuid')
        # Rename the file
        newFilename = join(outputFolder, filenamePrefix + id.zfill(6) + ".xml")
        with open(newFilename, 'wb') as f:
            f.write(etree.tostring(tree, pretty_print=True))
        # Remove the old file
        if exists(join(inputFolder, file)):
            removeFile(join(inputFolder, file))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Download all Object Items from MuseumPlus and save them to individual XML files')
    parser.add_argument('--url', required= True, help='URL of the MuseumPlus instance')
    parser.add_argument('--module', required= True, help='Name of the module to download items from')
    parser.add_argument('--username', required= True, help='Username to use for authentication')
    parser.add_argument('--password', required= True, help='Password to use for authentication')
    parser.add_argument('--outputFolder', required= True, help='Folder to save the XML files to')
    parser.add_argument('--tempFolder', required= True, help='Folder to temporarily save the XML during download')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    parser.add_argument('--limit', required= False, help='Limit the number of items to download')
    parser.add_argument('--offset', required= False, help='Offset to start downloading items from')
    args = parser.parse_args()

    if args.limit:
        args.limit = int(args.limit)

    if args.offset:
        args.offset = int(args.offset)

    downloadItems(host=args.url, module=args.module, username=args.username, password=args.password, outputFolder=args.outputFolder, tempFolder=args.tempFolder, filenamePrefix=args.filenamePrefix or 'item-', limit=args.limit, offset=args.offset)
