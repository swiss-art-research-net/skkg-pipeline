import json
from datetime import datetime
from os.path import join, exists, isfile
from lxml import etree

class ItemMetadata:
    METADATA_FILENAME = 'metadata.json'

    directory = None
    metadataFile = None

    def __init__(self, directory):
        self.directory = directory
        self.metadataFile = join(directory, self.METADATA_FILENAME)
        self.metadata = self.loadMetadata()

    def getLastUpdatedDate(self):
        if self.metadata['lastUpdated']:
            return self.metadata['lastUpdated']
        else:
            # Get the last updated date from the existing files
            lastUpdated  = self.getLastUpdatedFromItemFiles(self.directory)
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

    def setLastUpdated(self, lastUpdated: datetime):
        self.metadata['lastUpdated'] = lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.writeMetadata()

    def writeMetadata(self):
        with open(self.metadataFile, 'w') as f:
            json.dump(self.metadata, f)