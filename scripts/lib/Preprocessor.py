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
from typing import Dict, Type
import xml.etree.ElementTree as ET

_PREPROCESSOR_REGISTRY: Dict[str, Type['Preprocessor']] = {}

def getPreprocessor(module: str) -> 'Preprocessor':
    """
    Returns the appropriate preprocessor based on the module name.
    """
    preprocessorClass = _PREPROCESSOR_REGISTRY.get(module)
    if preprocessorClass is not None:
        return preprocessorClass()
    else:
        return BasePreprocessor()

def registerPreprocessor(module: str):
    """
    Decorator to register a preprocessor class for a specific module.
    """
    def decorator(cls: Type['Preprocessor']):
        _PREPROCESSOR_REGISTRY[module] = cls
        return cls
    return decorator

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
    
    def processYearFields(self, root: ET.Element, yearFieldSelectors: list) -> ET.Element:
        """
        This function takes an XML root element and a list of field selectors that contain years.
        If necessary, it converts the year fields into a xsd:gYear compliant format. e.g. at least
        4 digits and optionally prefixed with a '-' sign for BCE years.
        """
        for yearFieldSelector in yearFieldSelectors:
            datafields = root.findall(yearFieldSelector)
            for datafield in datafields:
                value = datafield.find('value').text
                if value is not None:
                    if int(value):
                        if int(value) < 0:
                            processedValue = f'-{abs(int(value)):05}'
                        else:
                            processedValue = f'{int(value):04}'
                        datafield.set(f'{self.PREFIX}type', 'gYear')
                        datafield.set(f'{self.PREFIX}year', processedValue)
        return root