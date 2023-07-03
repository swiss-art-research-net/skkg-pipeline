import argparse
from datetime import datetime
from lxml import etree
from os import listdir, remove as removeFile
from os.path import join, exists, isfile
from tqdm import tqdm

from lib.MuseumPlusConnector import MPWrapper

def downloadItems(*, host, username, password, outputFolder, tempFolder, filenamePrefix = 'item-', limit = None, offset = None):          
    client = MPWrapper(url=host, username=username, password=password)

    # Log the downloaded files
    log = {
        'downloaded': [],
        'existing': []
    }

    # Get the last updated date from the existing files
    lastUpdated  = getLastUpdatedFromItemFiles(outputFolder)
    print(f"Last updated date of existing files: {lastUpdated}")
    
    # Get the number of objects
    numObjects = client.getNumberOfObjects(lastUpdated=lastUpdated)

    if not limit:
        limit = numObjects
    if not offset:
        offset = 0

    for i in tqdm(range(offset, offset+limit)):
        filename = join(tempFolder, filenamePrefix + str(i).zfill(6) + ".xml")
        # Check if the file already exists
        if not exists(filename):
            item = client.getObjectByOffset(i, lastUpdated=lastUpdated)
            with open(filename, 'wb') as f:
                f.write(etree.tostring(item, pretty_print=True))
                log['downloaded'].append(filename)
        else:
            log['existing'].append(filename)

    renameItemsBasedOnIds(inputFolder=tempFolder, outputFolder=outputFolder, filenamePrefix=filenamePrefix)
    print(f"Downloaded {len(log['downloaded'])} items.")
    print(f"Skipped {len(log['existing'])} items that already existed.")

def getLastUpdatedFromItemFiles(inputFolder):
    # Read all XML files in the input folder
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.xml')]
    
    # Set lastUpdated to a Date object with the lowest possible value
    lastUpdated = datetime.min

    for file in tqdm(files):
        tree = etree.parse(join(inputFolder, file))
        lastUpdatedString= tree.find('.//{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]/{http://www.zetcom.com/ria/ws/module}value').text
        lastUpdatedItem = datetime.strptime(lastUpdatedString, '%Y-%m-%d %H:%M:%S.%f')
        if lastUpdatedItem > lastUpdated:
            lastUpdated = lastUpdatedItem
    return lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

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

    downloadItems(host=args.url, username=args.username, password=args.password, outputFolder=args.outputFolder, tempFolder=args.tempFolder, filenamePrefix=args.filenamePrefix or 'item-', limit=args.limit, offset=args.offset)
