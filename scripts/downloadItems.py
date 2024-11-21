"""
Script to download all items from a module in MuseumPlus and save them to individual XML files.
The script will only download items that have been updated since the last download.
Downloaded files are stored in a temporary folder and renamed based on the UUID after the download is complete. 
This ensures that the script can be interrupted and restarted without having to download all items again.

Usage:
    python downloadItems.py --url <url> --module <module> --username <username> --password <password> --outputFolder <outputFolder> --tempFolder <tempFolder> [--filenamePrefix <filenamePrefix>] [--limit <limit>] [--offset <offset>]

Arguments:
    --url: URL of the MuseumPlus instance
    --module: Name of the module to download items from
    --username: Username to use for authentication
    --password: Password to use for authentication
    --outputFolder: Folder to save the XML files to
    --tempFolder: Folder to temporarily save the XML during download
    --filenamePrefix: Prefix to use for the filenames of the XML files. Defaults to "item-"
    --limit: Limit the number of items to download
    --offset: Offset to start downloading items from
"""


import argparse
import pytz
from datetime import datetime
from lxml import etree
from os import listdir, remove as removeFile
from os.path import join, exists, isfile
from tqdm import tqdm

from lib.Metadata import ItemMetadata
from lib.MuseumPlusConnector import MPWrapper
from lib.Utils import createXMLCopy

from config.moduleQueryAdditions import moduleQueryAdditions

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
    downloadStarted_utc = datetime.now(pytz.utc)
    zurich_timezone = pytz.timezone('Europe/Zurich')
    downloadStarted = downloadStarted_utc.astimezone(zurich_timezone)
    
    queryAddition = moduleQueryAdditions.get(module, None)
    queryAddition = etree.fromstring(queryAddition) if queryAddition else None

    # Get the number of items
    numItems = client.getNumberOfItems(module=module, lastUpdated=lastUpdated, queryAddition=createXMLCopy(queryAddition))
    print(f"Found {numItems} items for module {module}")
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
    else:
        limit = min(limit, numItems)
    if not offset:
        offset = 0

    for i in tqdm(range(offset, offset+limit)):
        filename = join(tempFolder, filenamePrefix + str(i).zfill(6) + ".xml")
        # Check if the file already exists
        if not exists(filename):
            try:
                item = client.getItemByOffset(i, module=module, lastUpdated=lastUpdated, queryAddition=createXMLCopy(queryAddition))
            except:
                log['omitted'].append(filename)
                continue
            with open(filename, 'wb') as f:
                f.write(etree.tostring(item, pretty_print=True))
                log['downloaded'].append(filename)
        else:
            log['existing'].append(filename)

    storeAndRenameItems(inputFolder=tempFolder, outputFolder=outputFolder, filenamePrefix=filenamePrefix, metadata=metadata)

    metadata.setLastUpdated(downloadStarted)

    print(f"Downloaded {len(log['downloaded'])} items.")
    print(f"Skipped {len(log['existing'])} items that already existed.")
    if len(log['omitted']) > 0:
        print(f"Omitted {len(log['omitted'])} items that could not be downloaded.")
        # List omitted files
        print("Omitted files:")
        for file in log['omitted']:
            print(file)

def storeAndRenameItems(*, inputFolder, outputFolder, filenamePrefix, metadata):
    # Read all XML files in the input folder
    files = [f for f in listdir(inputFolder) if isfile(join(inputFolder, f)) and f.endswith('.xml')]
    for file in tqdm(files):

        # Retrieve the uuid and last modified attributes from the moduleItem element
        tree = etree.parse(join(inputFolder, file))
        try:
            uuid = tree.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('uuid')
        except:
            print(f"Could not find uuid for file {file}")
            import sys
            sys.exit(1)
        lastModified= tree.find('.//{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]/{http://www.zetcom.com/ria/ws/module}value').text

        # Rename the file
        filename = filenamePrefix + uuid + ".xml"
        newFile = join(outputFolder, filename)
        with open(newFile, 'wb') as f:
            f.write(etree.tostring(tree, pretty_print=True))
        # Remove the old file
        if exists(join(inputFolder, file)):
            removeFile(join(inputFolder, file))
            # Update last modified for file
            metadata.setLastUpdatedForFile(filename, lastModified, write=False)
    metadata.writeMetadata()
        
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
    args, _ = parser.parse_known_args()

    if args.limit:
        args.limit = int(args.limit)

    if args.offset:
        args.offset = int(args.offset)

    downloadItems(host=args.url, module=args.module, username=args.username, password=args.password, outputFolder=args.outputFolder, tempFolder=args.tempFolder, filenamePrefix=args.filenamePrefix or 'item-', limit=args.limit, offset=args.offset)
