"""
Downloads the metadata for the IIIF stored as CSV file and converts it to XML

Usage:
    python retrieveIiifData.py --input <input> --outputFolder <outputFolder> --filename <filename>

Arguments:
    --input: URL to a CSV file with the metadata for the IIIF images
    --outputFolder: Folder where the output data should be stored
    --filename: Name of the output files (default: iiif)
"""

import argparse
import csv
import urllib.request
from os.path import getsize, join
from lxml import etree
import sys

def retrieveIiifData(*, input, outputFolder, filename='iiif'):
    # Check if local file size is same as remote file size
    remoteFileSize = urllib.request.urlopen(input).info()['Content-Length']
    localFileSize = getsize(join(outputFolder, f'{filename}.csv'))
    
    inputFileUpdated = False

    if str(remoteFileSize) == str(localFileSize):
        print('Remote file has not changed, no need to download it again')
    else:
        print('Downloading report file')
        urllib.request.urlretrieve(input, join(outputFolder, f'{filename}.csv'))
        inputFileUpdated = True

    # If the input file has changed or the output file does not exist, convert the CSV to XML
    if inputFileUpdated or not join(outputFolder, f'{filename}.xml'):
        print('Converting CSV to XML')
        convertCsvToXml(inputFile=join(outputFolder, f'{filename}.csv'), outputFile=join(outputFolder, f'{filename}.xml'))
    else:
        print('Output file already exists, no need to convert CSV to XML')

def convertCsvToXml(*, inputFile, outputFile):
    with open(inputFile, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = next(reader)
        root = etree.Element('collection')
        for row in reader:
            item = etree.SubElement(root, 'item')
            for index, column in enumerate(row):
                if column:
                    etree.SubElement(item, header[index]).text = column
    with open(outputfile, 'wb') as xmlfile:
        xmlfile.write(etree.tostring(root, pretty_print=True))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Retrieve and prepare data related to the IIIF images')
    parser.add_argument('--input', required=True, help='CSV file with the metadata for the IIIF images')
    parser.add_argument('--outputFolder', required=True, help='Folder where the output data should be stored')
    parser.add_argument('--filename', default='iiif', help='Name of the output files')
    args = parser.parse_args()

    if args.filename is None:
        args.filename = 'iiif'

    retrieveIiifData(input=args.input, outputFolder=args.outputFolder, filename=args.filename)
