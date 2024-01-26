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
from os.path import exists, getsize, join
from lxml import etree

def retrieveIiifData(*, input, outputFolder, filename='iiif'):
    inputFileNeedsUpdate = True

    if exists(join(outputFolder, f'{filename}.csv')):
        remoteFileSize = urllib.request.urlopen(input).info()['Content-Length']
        localFileSize = getsize(join(outputFolder, f'{filename}.csv'))    
        if str(remoteFileSize) == str(localFileSize):
            print('Remote file has not changed, no need to download it again')
            inputFileNeedsUpdate = False
    
    if inputFileNeedsUpdate:
        print('Downloading report file')
        urllib.request.urlretrieve(input, join(outputFolder, f'{filename}.csv'))

    # If the input file has changed or the output file does not exist, convert the CSV to XML
    if inputFileNeedsUpdate or not join(outputFolder, f'{filename}.xml'):
        print('Converting CSV to XML')
        convertCsvToXml(inputFile=join(outputFolder, f'{filename}.csv'), outputFile=join(outputFolder, f'{filename}.xml'))
    else:
        print('Output file already exists, no need to convert CSV to XML')

def convertCsvToXml(*, inputFile, outputFile):
    # read csv file
    inputData = []
    with open(inputFile, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            inputData.append(row)
    
    # write xml file
    root = etree.Element('collection')
    for row in inputData:
        # If the page number is empty, set it to 1
        if row['page_number'] == '':
            row['page_number'] = '1'
        item = etree.SubElement(root, 'item')
        for key, value in row.items():
            if value:
                etree.SubElement(item, key).text = value

    with open(outputFile, 'wb') as xmlfile:
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
