"""
Script to download a vocabulary from a MuseumPlus and save them to individual XML files.

Usage:
    python downloadVocabularies.py --url <url> --vocabulary <vocabulary> --username <username> --password <password> --outputFolder <outputFolder> [--filenamePrefix <filenamePrefix>]

Arguments:
    --url: URL of the MuseumPlus instance
    --vocabulary: Name of the vocabulary to download
    --username: Username to use for authentication
    --password: Password to use for authentication
    --outputFolder: Folder to save the XML files to
    --filenamePrefix: Prefix to use for the filenames of the XML files. Defaults to "item-"
"""

import argparse
from lxml import etree
from os.path import join

from lib.MuseumPlusConnector import MPWrapper

def downloadVocabulary(*, host, username, password, vocabulary, outputFolder, filenamePrefix = 'vocab-'):          
    client = MPWrapper(url=host, username=username, password=password)

    filename = join(outputFolder, filenamePrefix + vocabulary + ".xml")
    vocabularyNodes = client.getVocabularyNodes(vocabulary)
    with open(filename, 'wb') as f:
        f.write(etree.tostring(vocabularyNodes, pretty_print=True))
    
    print(f"Downloaded vocabulary {vocabulary}.")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Download all Object Items from MuseumPlus and save them to individual XML files')
    parser.add_argument('--url', required= True, help='URL of the MuseumPlus instance')
    parser.add_argument('--vocabulary', required= True, help='Name of the vocabulary to download')
    parser.add_argument('--username', required= True, help='Username to use for authentication')
    parser.add_argument('--password', required= True, help='Password to use for authentication')
    parser.add_argument('--outputFolder', required= True, help='Folder to save the XML files to')
    parser.add_argument('--filenamePrefix', required= False, help='Prefix to use for the filenames of the XML files. Defaults to "item-"')
    args = parser.parse_args()

    downloadVocabulary(host=args.url, vocabulary=args.vocabulary, username=args.username, password=args.password, outputFolder=args.outputFolder, filenamePrefix=args.filenamePrefix or 'vocab-')
