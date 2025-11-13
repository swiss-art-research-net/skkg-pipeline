import xml.etree.ElementTree as ET

from .Preprocessor import BasePreprocessor, registerPreprocessor

@registerPreprocessor('Literature')
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
    
@registerPreprocessor('Object')
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

@registerPreprocessor('Ownership') 
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

@registerPreprocessor('Person')
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

        The known IDs are mapped to the following types and AAT terms:

        ID, Label, Type, AAT Term

        258982, ab Namensänderung, name change
        258981, bis Namensänderung, name change
        255974, ab Ortswechsel, location change, 300393179
        258983, bis Ortswechsel, location change 300393179
        194028, aktiv ab, active, 300393177
        184965, aktiv bis, active, 300393177
        190028, aktiv um, active, 300393177
        184964, aktiv von, active, 300393177

        The preprocessed dates will get an additional node in the repeatableGroupItem
        with the prefixed name 'dateType' and the following attributes:
        - type: 'nameChange', 'locationChange', 'active', 'other'
        - label: human readable label
        - aat: AAT term ID (if available)
        
        """
        knownDateTypes = {
            '258982': {'type': 'nameChange', 'label': 'name change'},
            '258981': {'type': 'nameChange', 'label': 'name change'},
            '255974': {'type': 'locationChange', 'label': 'location change', 'aat': '300393179', 'aatLabel': 'change of residence'},
            '258983': {'type': 'locationChange', 'label': 'location change', 'aat': '300393179', 'aatLabel': 'change of residence'},
            '194028': {'type': 'active', 'label': 'active', 'aat': '300393177', 'aatLabel': 'professional activity'},
            '184965': {'type': 'active', 'label': 'active', 'aat': '300393177', 'aatLabel': 'professional activity'},
            '190028': {'type': 'active', 'label': 'active', 'aat': '300393177', 'aatLabel': 'professional activity'},
            '184964': {'type': 'active', 'label': 'active', 'aat': '300393177', 'aatLabel': 'professional activity'},
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
                                subElem = ET.SubElement(dateTypeField, key)
                                subElem.text = value

        return root