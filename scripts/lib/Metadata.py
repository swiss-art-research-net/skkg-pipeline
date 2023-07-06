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
        """
        Initialize the class
        
        args:
            directory (str): The directory where the items are stored
        """
        self.directory = directory
        self.metadataFile = join(directory, self.METADATA_FILENAME)
        self.metadata = self.loadMetadata()

    def getLastUpdatedDate(self):
        """
        Get the last updated date from the metadata file.
        The last updated date is stored in the key 'lastUpdated' in the metadata file.
        """
        if 'lastUpdated' in self.metadata and self.metadata['lastUpdated'] is not None:
            return self.metadata['lastUpdated']
        else:
            # Get the last updated date from the existing files
            lastUpdated  = self.getLastUpdatedFromItemFiles()
            if lastUpdated:
                self.setLastUpdated(lastUpdated)
                return lastUpdated
    
    def getLastUpdatedFromItemFiles(self):
        """
        Determines the last updated date by reading the __lastModified field from
        all XML files in the input folder and returning the highest value.
        """
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
        """
        Reads the metadata file and returns the contents as a dictionary.
        """
        if exists(self.metadataFile):
            with open(self.metadataFile, 'r') as f:
                return json.load(f)
        else:
            return {}

    def setLastUpdated(self, lastUpdated):
        """
        Set the last updated date for the module.
        Adds the key 'lastUpdated' to the metadata if it does not exist yet and
        sets the value to the given lastUpdated date.

        args:
            lastUpdated (str or datetime): The last updated date to set
        """
        if isinstance(lastUpdated, str):
            self.metadata['lastUpdated'] = lastUpdated
        elif isinstance(lastUpdated, datetime):
            self.metadata['lastUpdated'] = lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.writeMetadata()

    def setLastUpdatedForFile(self, filename, lastUpdated):
        """
        Set the last updated date for a specific file.
        Adds the key 'files' to the metadata if it does not exist yet.
        Adds the key 'filename' to the 'files' key if it does not exist yet.

        args:
            filename (str): The filename of the file to set the last updated date for
            lastUpdated (str or datetime): The last updated date to set   
        """
        if not 'files' in self.metadata:
            self.metadata['files'] = {}
        if not filename in self.metadata['files']:
            self.metadata['files'][filename] = {}
        if isinstance(lastUpdated, str):
            self.metadata['files'][filename]['lastUpdated'] = lastUpdated
        elif isinstance(lastUpdated, datetime):
            self.metadata['files'][filename] = lastUpdated.strftime('%Y-%m-%dT%H:%M:%S.%f')

    def writeMetadata(self):
        """
        Writes the metadata to the metadata file.
        """
        with open(self.metadataFile, 'w') as f:
            json.dump(self.metadata, f)