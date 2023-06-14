import argparse
import sys
from lxml import etree
from os.path import join
from tqdm import tqdm

from lib.MuseumPlusConnector import MPWrapper

def downloadItems(*, host, username, password, outputFolder, filenamePrefix = 'item-', limit = None, offset = None):          
    client = MPWrapper(url=host, username=username, password=password)

    # Get the number of objects
    numObjects = client.getNumberOfObjects()

    if not limit:
        limit = numObjects
    if not offset:
        offset = 0

    for i in tqdm(range(offset, offset+limit)):
        print(i)
        # item = client.getObjectByOffset(i)
        # id = item.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('id')
        # filename = join(outputFolder, filenamePrefix + id + ".xml")
        # with open(filename, 'wb') as f:
        #     f.write(etree.tostring(item, pretty_print=True))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Download all Object Items from MuseumPlus and save them to individual XML files')
    parser.add_argument('--url', required= True, help='URL of the MuseumPlus instance')
    parser.add_argument('--username', required= True, help='Username to use for authentication')
    parser.add_argument('--password', required= True, help='Password to use for authentication')
    parser.add_argument('--outputFolder', required= True, help='Folder to save the XML files to')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    parser.add_argument('--limit', required= False, help='Limit the number of items to download')
    parser.add_argument('--offset', required= False, help='Offset to start downloading items from')
    args = parser.parse_args()

    if args.limit:
        args.limit = int(args.limit)

    if args.offset:
        args.offset = int(args.offset)

    downloadItems(host=args.url, username=args.username, password=args.password, outputFolder=args.outputFolder, filenamePrefix=args.filenamePrefix or 'item-', limit=args.limit, offset=args.offset)
