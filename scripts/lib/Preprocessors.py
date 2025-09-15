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
        root = super().parseXML(content)
        # Process year fields
        yearFieldSelectors = [".//dataField[@dataType='Long'][@name='DateFromLnu']", ".//dataField[@dataType='Long'][@name='DateToLnu']"]
        root = super().processYearFields(root, yearFieldSelectors)
        # Mark latest Object Documentation Status assignment
        root = self.markLatestObjectDocumentationStatusAssignment(root)
        return super().dumpXML(root)
    
    def markLatestObjectDocumentationStatusAssignment(self, root: ET.Element) -> ET.Element:
        """
        This function marks the latest Object Documentation Status assignments with a flag.
        """
        moduleItems = root.findall(".//moduleItem")
        for moduleItem in moduleItems:
            objDocumentationStatusGroups = moduleItem.findall("repeatableGroup[@name='ObjDocumentationStatusGrp']")
            for objDocumentationStatus in objDocumentationStatusGroups:
                statusItems = objDocumentationStatus.findall('repeatableGroupItem')
                latestDate = ''
                latestItems = []
                for item in statusItems:
                    dateField = item.find("dataField[@name='DateDat']")
                    if dateField is not None:
                        date = dateField.find('value').text
                        if date > latestDate:
                            latestDate = date
                            latestItems = [item]
                        elif date == latestDate:
                            latestItems.append(item)
                for latestItem in latestItems:
                    latestItem.set(f'{self.PREFIX}latest', 'true')
        return root
    
class OwnershipPreprocessor(BasePreprocessor):
    """
    Preprocessor for the Ownership module.
    """
    def addTransactionTypeData(self, root: ET.Element) -> ET.Element:
        """
        Depending on the transaction type, which is specified in the OwsOwnerTypeVoc vocabulary reference field,
        we add a tag to the XML element that indicates the type of CIDOC-CRM Activity that best matches the transaction
        in reference to the Linked.Art provenance types (https://linked.art/model/provenance).
        """
        # Mappings
        mappings = {
            '234014': {'type': 'crm:E9_Move', 'label': 'move'},
            '233966': {'type': 'crm:E10_Transfer_of_Custody', 'label': 'transfer of custody'},
            '233967': {'type': 'crm:E8_Acquisition', 'label': 'acquisition'},
            '233965': {'type': 'crm:E9_Move', 'label': 'move'},
            '231984': {'type': 'crm:E10_Transfer_of_Custody', 'label': 'transfer of custody'},
            '233964': {'type': 'crm:E10_Transfer_of_Custody', 'label': 'transfer of custody'},
            '231986': {'type': 'crm:E10_Transfer_of_Custody', 'label': 'transfer of custody'},
            '231987': {'type': 'crm:E8_Acquisition', 'label': 'acquisition'},
            '231985': {'type': 'crm:E8_Acquisition', 'label': 'acquisition'}
        }
        # Retrieve all vocabulary reference fields
        moduleItems = root.findall(".//moduleItem")
        for moduleItem in moduleItems:
            typeField = moduleItem.find(".//vocabularyReference[@name='OwsOwnerTypeVoc']/vocabularyReferenceItem")
            if typeField is not None and 'id' in typeField.attrib:
                typeId = typeField.attrib['id']
                crmType = mappings.get(typeId)
                if crmType:
                    transaction_elem = ET.SubElement(moduleItem, f'{self.PREFIX}transaction')
                    transaction_elem.set('type', crmType['type'])
                    transaction_elem.set('label', crmType['label'])
        return root
    
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        root = super().parseXML(content)
        # Process date fields
        dateFieldSelectors = [".//repeatableGroup[@name='OwsDateGrp']/repeatableGroupItem/dataField[@name='DateFromTxt']",
                             ".//repeatableGroup[@name='OwsDateGrp']/repeatableGroupItem/dataField[@name='DateToTxt']",]
        root = super().processDateFields(root, dateFieldSelectors)
        # Add transaction type data
        root = self.addTransactionTypeData(root)
        return super().dumpXML(root)
    
class PersonPreprocessor(BasePreprocessor):
    """
    Preprocessor for the Person module.
    """
    def preprocess(self, content: str) -> str:
        content = super().preprocess(content)
        root = super().parseXML(content)
        root = self.processPersonDates(root)
        return super().dumpXML(root)
    
    def processPersonDates(self, root: ET.Element) -> ET.Element:
        """
        This function processes the additional dates in the Person item, i.e.
        those that are not Birth/Death or Formation/Dissolution.

        There is a repeatable group called PerDateGrp that contains the additional dates.
        Birth/Death and Formation/Dissolution are given the vocabularyReference
        of instance PerDateTypeVgr with the IDs 143906, 143911, 141086 and 141087. All other
        dates are considered additional dates and are processed here.

        We use a map of known vocabulary reference IDs to determine the type of date. Unknown
        IDs are treated as 'other'.

        The known IDs are mapped to the following types, date predicates, and AAT terms:

        ID, Label, Type, Date Predicate, AAT Term

        258982, ab Namensänderung, name change, crm:P82a_begin_of_the_begin
        258981, bis Namensänderung, name change, crm:P82b_end_of_the_end
        255974, ab Ortswechsel, location change, crm:P82a_begin_of_the_begin, 300393179
        258983, bis Ortswechsel, location change, crm:P82b_end_of_the_end, 300393179
        194028, aktiv ab, active, crm:P82a_begin_of_the_begin, 300393177
        184965, aktiv bis, active, crm:P82b_end_of_the_end, 300393177
        190028, aktiv um, active, crm:P82_at_some_time_within, 300393177
        184964, aktiv von, active, crm:P82a_begin_of_the_begin, 300393177

        The preprocessed dates will get an additional node in the repeatableGroupItem
        with the prefixed name 'dateType' and the following attributes:
        - type: 'nameChange', 'locationChange', 'active', 'other'
        - predicate: the corresponding CIDOC-CRM date predicate
        """
        knownDateTypes = {
            '258982': {'type': 'nameChange', 'label': 'name change', 'predicate': 'crm:P82a_begin_of_the_begin'},
            '258981': {'type': 'nameChange', 'label': 'name change', 'predicate': 'crm:P82b_end_of_the_end'},
            '255974': {'type': 'locationChange', 'label': 'location change', 'predicate': 'crm:P82a_begin_of_the_begin', 'aat': '300393179'},
            '258983': {'type': 'locationChange', 'label': 'location change', 'predicate': 'crm:P82b_end_of_the_end', 'aat': '300393179'},
            '194028': {'type': 'active', 'label': 'active', 'predicate': 'crm:P82a_begin_of_the_begin', 'aat': '300393177'},
            '184965': {'type': 'active', 'label': 'active', 'predicate': 'crm:P82b_end_of_the_end', 'aat': '300393177'},
            '190028': {'type': 'active', 'label': 'active', 'predicate': 'crm:P82_at_some_time_within', 'aat': '300393177'},
            '184964': {'type': 'active', 'label': 'active', 'predicate': 'crm:P82a_begin_of_the_begin', 'aat': '300393177'},
        }
        moduleItems = root.findall(".//moduleItem")
        for moduleItem in moduleItems:
            perDateGroups = moduleItem.findall("repeatableGroup[@name='PerDateGrp']")
            for perDateGroup in perDateGroups:
                dateItems = perDateGroup.findall('repeatableGroupItem')
                for item in dateItems:
                    typeField = item.find(".//vocabularyReference[@instanceName='PerDateTypeVgr']/vocabularyReferenceItem")
                    if typeField is not None and 'id' in typeField.attrib:
                        typeId = typeField.attrib['id']
                        if typeId not in ['143906', '143911', '141086', '141087']:
                            dateType = knownDateTypes.get(typeId, {'type': 'other', 'predicate': 'crm:P82_at_some_time_within'})
                            dateTypeField = ET.SubElement(item, f'{self.PREFIX}dateType')
                            for key, value in dateType.items():
                                dateTypeField.set(key, value)

        return root
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
        elif module == 'Ownership':
            return OwnershipPreprocessor()
        elif module == 'Person':
            return PersonPreprocessor()
        else:
            return BasePreprocessor()