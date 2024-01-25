"""

"""

import argparse
from os.path import join, isfile
from tqdm import tqdm

def retrieveIiifData(*, input, outputFolder):
    print("ok")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Retrieve and prepare data related to the IIIF images')
    parser.add_argument('--input', required=True, help='CSV file with the metadata for the IIIF images')
    parser.add_argument('--outputFolder', required=True, help='Folder where the output data should be stored')
    args = parser.parse_args()

    retrieveIiifData(input=args.input, outputFolder=args.outputFolder)
