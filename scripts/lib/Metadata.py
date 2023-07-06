import json
from os.path import join, exists, isfile
from lxml import etree

class ItemMetadata:
    METADATA_FILENAME = 'metadata.json'

    directory = None
    metadataFile = None

    def __init__(self, directory):
        self.directory = directory
        self.metadataFile = join(directory, self.METADATA_FILENAME)

    def getLastUpdatedDate(self):
        # Look for metadata file in the output folder
        if exists(self.metadataFile):
            # Read the metadata file
            with open(self.metadataFile, 'r') as f:
                metadata = json.load(f)
            # Get last updated date from metadata
            lastUpdated = metadata['lastUpdated']
        else:
            # Get the last updated date from the existing files
            lastUpdated  = self.getLastUpdatedFromItemFiles(self.directory)
            if lastUpdated:
                # Save the last updated date in a metadata file
                with open(self.metadataFile, 'w') as f:
                    json.dump({'lastUpdated': lastUpdated}, f)
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

    def setLastUpdated(self, lastUpdated):
        self.metadataFile = join(self.directory, self.METADATA_FILENAME)
        with open(self.metadataFile, 'w') as f:
            json.dump({'lastUpdated': lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f')}, f)
