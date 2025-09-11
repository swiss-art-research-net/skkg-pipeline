"""
Downloads the metadata for the IIIF stored as CSV file and converts it to XML

Usage:
    python retrieveIiifData.py --input <input> --outputFolder <outputFolder> --filename <filename>

Arguments:
    --input: URL to a CSV file with the metadata for the IIIF images
    --outputFolder: Folder where the output data should be stored
    --filename: Name of the output files (default: iiif)
    --itemsPerFile: Number of items per XML file (default: 1000)
"""

import argparse
import csv
import urllib.request
from os import listdir, remove as removeFile
from os.path import exists, getsize, join
from lxml import etree

def retrieveIiifData(*, input, outputFolder, filename='iiif', itemsPerFile=1000):
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
    if inputFileNeedsUpdate or not any(fname.startswith(f"{filename}_") and fname.endswith(".xml") for fname in listdir(outputFolder)):
        print('Converting CSV to XML')
        # Delete all existing XML files
        for file in listdir(outputFolder):
            if file.endswith(".xml"):
                removeFile(join(outputFolder, file))
        convertCsvToXml(
            inputFile=join(outputFolder, f'{filename}.csv'), 
            outputFolder=outputFolder, 
            filename=filename, 
            itemsPerFile=itemsPerFile
        )
    else:
        print('Output files already exist, no need to convert CSV to XML')

def convertCsvToXml(*, inputFile, outputFolder, filename, itemsPerFile):
    # Read CSV file
    inputData = []
    with open(inputFile, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            inputData.append(row)

    # Calculate the padding width based on the total items
    totalItems = len(inputData)
    padding_width = len(str(totalItems))  # Ensures we have enough padding for all ranges

    # Variables to track summary
    filesCreated = []
    totalBatches = (totalItems + itemsPerFile - 1) // itemsPerFile  # Total batches

    # Split data into batches and write XML files
    for batchNumber, startIndex in enumerate(range(0, totalItems, itemsPerFile), start=1):
        batch_data = inputData[startIndex:startIndex + itemsPerFile]
        root = etree.Element('collection')
        for row in batch_data:
            # If the page number is empty, set it to 1
            if row['page_number'] == '':
                row['page_number'] = '1'
            item = etree.SubElement(root, 'item')
            for key, value in row.items():
                if value:
                    etree.SubElement(item, key).text = value

        # Generate the output filename with zero-padded numbers
        startNumber = str(startIndex + 1).zfill(padding_width)
        endNumber = str(startIndex + len(batch_data)).zfill(padding_width)
        outputFile = join(outputFolder, f'{filename}_{batchNumber:05d}_{startNumber}-{endNumber}.xml')
        
        with open(outputFile, 'wb') as xmlfile:
            xmlfile.write(etree.tostring(root, pretty_print=True))
        
        # Record file creation
        filesCreated.append(f"{batchNumber:05d}: {startNumber}-{endNumber}")

    # Print summary
    print("\nIIIF input files successfully completed!")
    print(f"Total files created: {len(filesCreated)}")
    print(f"Total items processed: {totalItems}")
    print(f"Items per file: {itemsPerFile}")
    print(f"Number of batches: {totalBatches}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Retrieve and prepare data related to the IIIF images')
    parser.add_argument('--input', required=True, help='CSV file with the metadata for the IIIF images')
    parser.add_argument('--outputFolder', required=True, help='Folder where the output data should be stored')
    parser.add_argument('--filename', default='iiif', help='Name of the output files')
    parser.add_argument('--itemsPerFile', type=int, default=100, help='Number of items per XML file (default: 100)')
    args = parser.parse_args()

    retrieveIiifData(input=args.input, outputFolder=args.outputFolder, filename=args.filename, itemsPerFile=args.itemsPerFile)
