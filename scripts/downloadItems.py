import argparse
import csv
import sys
from lxml import etree
from os.path import join, exists
from tqdm import tqdm

from lib.MuseumPlusConnector import MPWrapper

def downloadItems(*, host, username, password, outputFolder, uuidMapCsv, filenamePrefix = 'item-', limit = None, offset = None):          
    client = MPWrapper(url=host, username=username, password=password)

    # Log the downloaded files
    log = {
        'downloaded': [],
        'existing': []
    }

    uuidMap = getUuidMap(uuidMapCsv);
    
    # Get the number of objects
    numObjects = client.getNumberOfObjects()

    if not limit:
        limit = numObjects
    if not offset:
        offset = 0

    for i in tqdm(range(offset, offset+limit)):
        filename = join(outputFolder, filenamePrefix + str(i) + ".xml")
        # Check if the file already exists
        if not exists(filename):
            item = client.getObjectByOffset(i)
            uuid = item.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('uuid')
            with open(filename, 'wb') as f:
                f.write(etree.tostring(item, pretty_print=True))
                uuidMap[i] = uuid
                log['downloaded'].append(filename)
        else:
            log['existing'].append(filename)
    
    writeUuidMap(uuidMap, uuidMapCsv)

    print(f"Downloaded {len(log['downloaded'])} items.")
    print(f"Skipped {len(log['existing'])} items that already existed.")

def getUuidMap(filename):
    uuidMap = {}
    if exists(filename):
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            uuidMap = {rows[0]:rows[1] for rows in reader}
    return uuidMap

def writeUuidMap(uuidMap, filename):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for key, value in uuidMap.items():
            writer.writerow([key, value])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Download all Object Items from MuseumPlus and save them to individual XML files')
    parser.add_argument('--url', required= True, help='URL of the MuseumPlus instance')
    parser.add_argument('--username', required= True, help='Username to use for authentication')
    parser.add_argument('--password', required= True, help='Password to use for authentication')
    parser.add_argument('--outputFolder', required= True, help='Folder to save the XML files to')
    parser.add_argument('--uuidMap', required= True, help='Path to a CSV file used to store corresponding indices and UUIDs')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    parser.add_argument('--limit', required= False, help='Limit the number of items to download')
    parser.add_argument('--offset', required= False, help='Offset to start downloading items from')
    args = parser.parse_args()

    if args.limit:
        args.limit = int(args.limit)

    if args.offset:
        args.offset = int(args.offset)

    downloadItems(host=args.url, username=args.username, password=args.password, uuidMapCsv=args.uuidMap, outputFolder=args.outputFolder, filenamePrefix=args.filenamePrefix or 'item-', limit=args.limit, offset=args.offset)
