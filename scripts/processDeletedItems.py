"""
Items that have been deleted in MuseumPlus should be deleted from the local cache as well.
This script checks if any items have been deleted in MuseumPlus and, if so, removes the local copy.

Usage:
    python processDeletedItems.py --url <url> --module <module> --username <username> --password <password> --inputFolder <inputFolder> [--filenamePrefix <filenamePrefix>]

Arguments:
    --url: URL of the MuseumPlus instance
    --module: Name of the module to check for deleted items
    --username: Username to use for authentication
    --password: Password to use for authentication
    --inputFolder: Folder where the XML files are stored
    --filenamePrefix: Prefix to use for the filenames of the XML files. Defaults to "item-"
"""

import argparse
import requests
from os import remove as removeFile
from os.path import join
from tqdm import tqdm

from lib.Metadata import ItemMetadata
from lib.MuseumPlusConnector import MPWrapper

def synchroniseItems(*, host, username, password, module, inputFolder, namedGraphBase, sparqlEndpoint, filenamePrefix = 'item-'):
    client = MPWrapper(url=host, username=username, password=password)
    metadata = ItemMetadata(inputFolder)
    files = metadata.listFiles()
    identifiersToRemove = []
    for file in tqdm(files):
        identifier = str(file.replace(filenamePrefix, '').replace('.xml', ''))
        if not client.existsItem(module=module, uuid=identifier):
            identifiersToRemove.append(identifier)
    
    for identifier in identifiersToRemove:
        filename = f"{filenamePrefix}{identifier}.xml"
        filepath = join(inputFolder, filename)
        print(f"Item {identifier} in module {module} has been deleted in MuseumPlus. Deleting local copy.")
        removeFile(filepath)
        metadata.removeFile(filename)
        removeFromTripleStore(identifier, namedGraphBase=namedGraphBase, filenamePrefix=filenamePrefix, endpoint=sparqlEndpoint)
    if len(identifiersToRemove) > 0:
        print(f"Removed {len(identifiersToRemove)} items from the local copy and triple store.")
    else:
        print("No items have been deleted in MuseumPlus.")

def removeFromTripleStore(identifier, *, namedGraphBase, filenamePrefix, endpoint):
    namedgraph = f"{namedGraphBase}{filenamePrefix}{identifier}"
    data = {'update': f'DROP GRAPH <{namedgraph}>'}
    response = requests.post(endpoint, data=data)
    if response.status_code != 200:
        print(f"Error while deleting item {identifier} from the triple store.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description = 'Delete all local items that have been deleted in MuseumPlus')
    parser.add_argument('--url', required= True, help='URL of the MuseumPlus instance')
    parser.add_argument('--module', required= True, help='Name of the module to synchronise')
    parser.add_argument('--username', required= True, help='Username to use for authentication')
    parser.add_argument('--password', required= True, help='Password to use for authentication')
    parser.add_argument('--inputFolder', required= True, help='Local folder where the XML files are stored')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    parser.add_argument('--namedGraphBase', required= True, help='Base URI of the named graphs of the items in the triple store')
    parser.add_argument('--sparqlEndpoint', required= True, help='URL of the SPARQL endpoint of the triple store')
    args = parser.parse_args()

    synchroniseItems(host=args.url, module=args.module, username=args.username, password=args.password, inputFolder=args.inputFolder, namedGraphBase=args.namedGraphBase, sparqlEndpoint=args.sparqlEndpoint, filenamePrefix=args.filenamePrefix or 'item-')
