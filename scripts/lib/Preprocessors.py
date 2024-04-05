"""
This file contains the Preprocessor classes for the different modules. It contains a function
that returns the appropriate preprocessor based on the module name.

The preprocess function in each preprocessor class takes the content of an input file as a string
and returns the preprocessed content as a string.

The preprocess function in the BasePreprocessor class contains the common preprocessing steps
that are shared across all modules. If no specific preprocessor is found for a module, the
BasePreprocessor is returned.

Usage:
    preprocessor = Preprocessors.getPreprocessor('Literature')
    preprocessedContent = preprocessor.preprocess(content)

"""

from abc import ABC, abstractmethod
from sariDateParser.dateParser import parse
from lib.DateUtils import convertEDTFdate
import xml.etree.ElementTree as ET

class Preprocessor(ABC):
    @abstractmethod
    def preprocess(self, content: str) -> str:
        pass

class BasePreprocessor(Preprocessor):

    PREFIX = '_preprocessed_'

    def preprocess(self, content: str) -> str:
        """
        Common preprocessing steps that are shared across all modules.
        """
        return content.replace('xmlns="http://www.zetcom.com/ria/ws/module"', '')
    
    def dumpXML(self, root: ET.Element) -> str:
        """
        Return the XML content as a string.
        """
        return ET.tostring(root, encoding='unicode')

    def parseXML(self, content: str) -> ET.Element:
        """
        Parse the XML content and return the root element.
        """
        return ET.fromstring(content)
    
    def processDateFields(self, root: ET.Element, dateFieldSelectors: list) -> ET.Element:
        """
        This function takes an XML root element and a list of field selectors that contain dates.
        It parses the date values and adds the lower and upper date values to the XML element.
        """
        for dateFieldSelector in dateFieldSelectors:
            datafields = root.findall(dateFieldSelector)
            for datafield in datafields:
                value = datafield.find('value').text
                parsedDate = parse(value)
                if parsedDate is not None:
                    daterange = convertEDTFdate(parsedDate)
                    datafield.set(f'{self.PREFIX}type', 'daterange')
                    datafield.set(f'{self.PREFIX}dateLower', daterange['lower'])
                    datafield.set(f'{self.PREFIX}dateUpper', daterange['upper'])
        return root
class LiteraturePreprocessor(BasePreprocessor):
    """
    Preprocessor for the Literature module.
    """
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        root = super().parseXML(content)
        dateFieldSelectors = [".//dataField[@name='LitYearTxt']"]
        root = super().processDateFields(root, dateFieldSelectors)
        return super().dumpXML(root)
    
class ObjectPreprocessor(BasePreprocessor):
    """
    Preprocessor for the Object module.
    """
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        return content
    
class Preprocessors:
    @staticmethod
    def getPreprocessor(module: str) -> Preprocessor:
        """
        Returns the appropriate preprocessor based on the module name.
        """
        if module == 'Literature':
            return LiteraturePreprocessor()
        elif module == 'Object':
            return ObjectPreprocessor()
        else:
            return BasePreprocessor()