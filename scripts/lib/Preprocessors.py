"""
We implement an Interface Preprocessor using the ABC module
This interface will have the method preprocess that will take as an input the
content of an XML file as a string and return the preprocessed content as a string.
We will implement individual subclasses for each module item that will preprocess the data.
There are preprocessing steps that are common to all modules, such as removing the XML namespace.
These steps will be implemented in the base class, and the individual subclasses will implement
the module-specific preprocessing steps. Not all modules will need module-specific preprocessing steps.

The Preprocessor class will have a static method getPreprocessor that will return the appropriate
Preprocessor subclass based on the module name.

Usage:
    preprocessor = Preprocessors.getPreprocessor('item')
    preprocessedContent = preprocessor.preprocess(content)

"""

from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

class Preprocessor(ABC):
    @abstractmethod
    def preprocess(self, content: str) -> str:
        pass

class BasePreprocessor(Preprocessor):
    def preprocess(self, content: str) -> str:
        return content.replace('xmlns="http://www.zetcom.com/ria/ws/module"', '')
    
    def dumpXML(self, root: ET.Element) -> str:
        return ET.tostring(root, encoding='unicode')

    def parseXML(self, content: str) -> ET.Element:
        return ET.fromstring(content)
    
    def processDateFields(self, root: ET.Element, dateFields: list) -> ET.Element:
        for dateField in dateFields:
            datafield = root.find(f".//dataField[@name='{dateField}']")
            if datafield is not None:
                value = datafield.find('value').text
                print(f"Found  {dateField}: {value}")
        return root
    
class LiteraturePreprocessor(BasePreprocessor):
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        root = super().parseXML(content)
        dateFields = ['LitYearTxt']
        root = super().processDateFields(root, dateFields)
        return super().dumpXML(root)
    
class ObjectPreprocessor(BasePreprocessor):
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        return content
    
class Preprocessors:
    @staticmethod
    def getPreprocessor(module: str) -> Preprocessor:
        if module == 'Literature':
            return LiteraturePreprocessor()
        elif module == 'Object':
            return ObjectPreprocessor()
        else:
            return BasePreprocessor()