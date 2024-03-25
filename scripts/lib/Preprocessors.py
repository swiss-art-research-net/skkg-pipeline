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

class Preprocessor(ABC):
    @abstractmethod
    def preprocess(self, content: str) -> str:
        pass

class BasePreprocessor(Preprocessor):
    def preprocess(self, content: str) -> str:
        return content.replace('xmlns="http://www.zetcom.com/ria/ws/module"', '')
    
class LiteraturePreprocessor(BasePreprocessor):
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        # Add literature-specific preprocessing steps here
        return content

class ObjectPreprocessor(BasePreprocessor):
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        # Add object-specific preprocessing steps here
        return content
    
class Preprocessors:
    @staticmethod
    def getPreprocessor(module: str) -> Preprocessor:
        if module == 'literature':
            return LiteraturePreprocessor()
        elif module == 'object':
            return ObjectPreprocessor()
        else:
            return BasePreprocessor()