import json
from datetime import datetime
from os import listdir
from os.path import join, exists, isfile
from lxml import etree

class ItemMetadata:
    """
    Class for storing and retrieving metadata about the downloaded items

    Usage:
    >>> # Create a new instance of the class based on the folder where the items are stored
    >>> metadata = ItemMetadata(folder)
    >>> # Get the last updated date
    >>> lastUpdated = metadata.getLastUpdatedDate()
    >>> # Set the last updated date
    >>> metadata.setLastUpdated(datetime.now())
    """
    METADATA_FILENAME = 'metadata.json'

    directory = None
    metadataFile = None

    def __init__(self, directory):
        self.directory = directory
        self.metadataFile = join(directory, self.METADATA_FILENAME)
        self.metadata = self.loadMetadata()

    def getLastUpdatedDate(self):
        if 'lastUpdated' in self.metadata and self.metadata['lastUpdated'] is not None:
            return self.metadata['lastUpdated']
        else:
            # Get the last updated date from the existing files
            lastUpdated  = self.getLastUpdatedFromItemFiles()
            if lastUpdated:
                self.setLastUpdated(lastUpdated)
                return lastUpdated
    
    def getLastUpdatedFromItemFiles(self):
        # Read all XML files in the input folder
        files = [f for f in listdir(self.directory) if isfile(join(self.directory, f)) and f.endswith('.xml')]
        
        # If no files exist yet, return None
        if len(files) == 0:
            return None

        # Set lastUpdated to a Date object with the lowest possible value
        lastUpdated = datetime.min

        for file in files:
            tree = etree.parse(join(self.directory, file))
            lastUpdatedString= tree.find('.//{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]/{http://www.zetcom.com/ria/ws/module}value').text
            lastUpdatedItem = datetime.strptime(lastUpdatedString, '%Y-%m-%d %H:%M:%S.%f')
            if lastUpdatedItem > lastUpdated:
                lastUpdated = lastUpdatedItem
        return lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

    def loadMetadata(self):
        if exists(self.metadataFile):
            with open(self.metadataFile, 'r') as f:
                return json.load(f)
        else:
            return {}

    def setLastUpdated(self, lastUpdated):
        if isinstance(lastUpdated, str):
            self.metadata['lastUpdated'] = lastUpdated
        elif isinstance(lastUpdated, datetime):
            self.metadata['lastUpdated'] = lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.writeMetadata()

    def writeMetadata(self):
        with open(self.metadataFile, 'w') as f:
            json.dump(self.metadata, f)