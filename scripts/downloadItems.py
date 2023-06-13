import argparse
import sys
from lxml import etree
from os.path import join
from dotenv import dotenv_values
from tqdm import tqdm

from lib.MuseumPlusConnector import MPWrapper

def downloadItems(*, outputFolder, dotenvFile = '.env', filenamePrefix = 'item-'):
    config = dotenv_values(dotenvFile)
    host = config['MUSEUMPLUS_URL']
    username = config['MUSEUMPLUS_USERNAME']
    password = config['MUSEUMPLUS_PASSWORD']
            
    client = MPWrapper(url=host, username=username, password=password)

    numObjects = client.getNumberOfObjects()
    for i in tqdm(range(numObjects)):
        item = client.getObjectByOffset(i)
        id = item.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('id')
        filename = join(outputFolder, filenamePrefix + id + ".xml")
        with open(filename, 'wb') as f:
            f.write(etree.tostring(item, pretty_print=True))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Download all Object Items from MuseumPlus and save them to individual XML files')
    parser.add_argument('--dotenv', required= False, help='Location of a .env file containing the credentials for the MuseumPlus API. Defaults to ".env"')
    parser.add_argument('--outputFolder', required= True, help='Folder to save the XML files to')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    
    args = parser.parse_args()

    downloadItems(outputFolder=args.outputFolder, dotenvFile=args.dotenv, filenamePrefix=args.filenamePrefix or 'item-')
