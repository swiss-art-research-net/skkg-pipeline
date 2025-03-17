"""
Items that have been deleted or unpublished in MuseumPlus should be deleted from the local cache .
This script checks if any items have been unpblished in MuseumPlus and, if so, removes the local copy.

Usage:
    python processUnpublishedItems.py --url <url> --module <module> --username <username> --password <password> --inputFolder <inputFolder> [--filenamePrefix <filenamePrefix>]

Arguments:
    --url: URL of the MuseumPlus instance
    --module: Name of the module to check for unpublished items
    --username: Username to use for authentication
    --password: Password to use for authentication
    --inputFolder: Folder where the XML files are stored
    --filenamePrefix: Prefix to use for the filenames of the XML files. Defaults to "item-"
"""

import argparse
import requests
import time
from lxml import etree
from os import remove as removeFile
from os.path import exists, join
from tqdm import tqdm

from lib.Metadata import ItemMetadata
from lib.MuseumPlusConnector import MPWrapper
from lib.Utils import createXMLCopy

from config.moduleQueryAdditions import moduleQueryAdditions

def synchroniseItems(*, host, username, password, module, inputFolder, turtleFolder, namedGraphBase, sparqlEndpoint, filenamePrefix = 'item-'):
    client = MPWrapper(url=host, username=username, password=password)
    queryAddition = moduleQueryAdditions.get(module, None)
    queryAddition = etree.fromstring(queryAddition) if queryAddition else None
    metadata = ItemMetadata(inputFolder)
    files = metadata.listFiles()
    identifiersToRemove = []
    for file in tqdm(files):
        identifier = str(file.replace(filenamePrefix, '').replace('.xml', ''))
        retries = 3
        while retries > 0:
            try:
                if not client.existsItem(module=module, uuid=identifier, queryAddition=createXMLCopy(queryAddition)):
                    identifiersToRemove.append(identifier)
                break
            except Exception as e:
                print(f"Error checking item {identifier}: {e}. Retrying in 5 seconds...")
            retries -= 1
            if retries == 0:
                raise RuntimeError(f"Failed to check item {identifier} after several attempts.")
            else:
                time.sleep(5)
    for identifier in identifiersToRemove:
        print(f"Item {identifier} in module {module} has been deleted or unpublished in MuseumPlus. Deleting local copy.")
        filenameXML = f"{filenamePrefix}{identifier}.xml"
        filepathXML = join(inputFolder, filenameXML)
        if exists(filepathXML):
            removeFile(filepathXML)
        else:
            print(f"File {filenameXML} does not exist in the input folder.")
        filenameTTL = f"{filenamePrefix}{identifier}.ttl"
        filepathTTL = join(turtleFolder, filenameTTL)
        if exists(filepathTTL):
            removeFile(filepathTTL)
        metadata.removeFile(filenameXML)
        removeFromTripleStore(identifier, namedGraphBase=namedGraphBase, filenamePrefix=filenamePrefix, endpoint=sparqlEndpoint)
    if len(identifiersToRemove) > 0:
        print(f"Removed {len(identifiersToRemove)} items from the local copy and triple store.")
    else:
        print("No items have been unpublished in MuseumPlus.")

def removeFromTripleStore(identifier, *, namedGraphBase, filenamePrefix, endpoint):
    namedgraph = f"{namedGraphBase}{filenamePrefix}{identifier}"
    data = {'update': f'DROP GRAPH <{namedgraph}>'}
    response = requests.post(endpoint, data=data)
    if response.status_code != 200:
        print(f"Error while deleting item {identifier} from the triple store.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description = 'Delete all local items that have been unpublished or deleted in MuseumPlus')
    parser.add_argument('--url', required= True, help='URL of the MuseumPlus instance')
    parser.add_argument('--module', required= True, help='Name of the module to synchronise')
    parser.add_argument('--username', required= True, help='Username to use for authentication')
    parser.add_argument('--password', required= True, help='Password to use for authentication')
    parser.add_argument('--inputFolder', required= True, help='Local folder where the XML files are stored')
    parser.add_argument('--turtleFolder', required= False, help='Local folder where the Turtle files are stored.')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    parser.add_argument('--namedGraphBase', required= True, help='Base URI of the named graphs of the items in the triple store')
    parser.add_argument('--sparqlEndpoint', required= True, help='URL of the SPARQL endpoint of the triple store')
    args = parser.parse_args()

    synchroniseItems(host=args.url, module=args.module, username=args.username, password=args.password, inputFolder=args.inputFolder, turtleFolder=args.turtleFolder, namedGraphBase=args.namedGraphBase, sparqlEndpoint=args.sparqlEndpoint, filenamePrefix=args.filenamePrefix or 'item-')
