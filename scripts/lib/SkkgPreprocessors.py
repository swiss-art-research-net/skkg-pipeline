import xml.etree.ElementTree as ET
import logging

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
        root = self.addSortingForReferencedObjects(root)
        return super().dumpXML(root)
    

    def _extract_number(self, value):
        """
        Convert strings like "28a" -> 28, "  1600 " -> 1600.
        Returns None if no leading digits exist.
        """
        import re
        if not value:
            return None
        m = re.match(r"\s*(\d+)", value)
        return int(m.group(1)) if m else None

    def addSortingForReferencedObjects(self, root: ET.Element) -> ET.Element:
        """
        This function adds sorting information for referenced objects in the Literature module.
        """
        moduleItems = root.findall(".//moduleItem")
        for moduleItem in moduleItems:
            referencedObjects = moduleItem.findall("./moduleReference[@name='LitObjectRef']/moduleReferenceItem")
            sortKeys = {}

            for obj in referencedObjects:
                objId = obj.attrib.get("uuid")

                # Invnr from formattedValue, e.g. "Objekt in Literatur: 1600, ..."
                invNr = None
                label = obj.find("./formattedValue")
                if label is not None and label.text:
                    labelText = label.text
                    if labelText.startswith("Objekt in Literatur: "):
                        invNr_raw = labelText.replace("Objekt in Literatur: ", "").split(",")[0].strip()
                        invNr = self._extract_number(invNr_raw) 

                # Catalogue number
                catNumberField = obj.find("./dataField[@name='CatalogueNoTxt']/value")
                catNumber_raw = catNumberField.text.strip() if (catNumberField is not None and catNumberField.text) else None
                catNumber = self._extract_number(catNumber_raw)

                # Page number (if it’s numeric-like, treat it numeric; otherwise None)
                pageField = obj.find("./dataField[@name='PageRefTxt']/value")
                page_raw = pageField.text.strip() if (pageField is not None and pageField.text) else None
                pageNumber = self._extract_number(page_raw)

                # Figure page number (you had FigRefTxt twice; keep FigRefTxt here)
                figPageField = obj.find("./dataField[@name='FigRefTxt']/value")
                fig_raw = figPageField.text.strip() if (figPageField is not None and figPageField.text) else None
                figPageNumber = self._extract_number(fig_raw)

                sortKeys[objId] = {
                    "invNr": invNr,
                    "catNumber": catNumber,
                    "pageNumber": pageNumber,
                    "figPageNumber": figPageNumber,
                }
            # Sort by catNumber, then figPageNumber, then pageNumber, then invNr
            sortKeysList = [
                (objId, keys["catNumber"] if keys["catNumber"] is not None else float('inf'),
                 keys["figPageNumber"] if keys["figPageNumber"] is not None else float('inf'),
                 keys["pageNumber"] if keys["pageNumber"] is not None else float('inf'),
                 keys["invNr"] if keys["invNr"] is not None else float('inf'))
                for objId, keys in sortKeys.items()
            ]
            sortedKeys = sorted(sortKeysList, key=lambda x: (x[1], x[2], x[3], x[4]), reverse=False)
            for index, (objId, _, _, _, _) in enumerate(sortedKeys):
                obj = next((o for o in referencedObjects if o.attrib.get("uuid") == objId), None)
                if obj is not None:
                    sortField = ET.SubElement(obj, 'dataField')
                    sortField.set('dataType', 'Long')
                    sortField.set('name', 'SortLnu')
                    valueElem = ET.SubElement(sortField, 'value')
                    valueElem.text = str(index + 1)
                    formattedValueElem = ET.SubElement(sortField, 'formattedValue')
                    formattedValueElem.set('language', 'de')
                    formattedValueElem.text = str(index + 1)
        return root
        
    
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
        and the type of acquisition, which is specified in the OwsAcquisitionTypeVoc vocabulary reference field,
        we add a tag to the XML element that indicates the type of CIDOC-CRM Activity that best matches the transaction
        in reference to the Linked.Art provenance types (https://linked.art/model/provenance).

        The mappings are as follows:
        |Art Besitz          |OwsOwnerType|Erwerbsart           |OwsAcquisitionType|Mapping                |
        |--------------------|------------|---------------------|-----------------|-----------------------|
        |<leer>              |            |<leer>               |                 |E7 Activity            |
        |<leer>              |            |Erwerbsart unbekannt |231997           |E7 Activity            |
        |<leer>              |            |erworben auf Auktion |231993           |E8 Acquisition         |
        |<leer>              |            |geerbt               |231994           |E8 Acquisition         |
        |Auslagerung         |234014      |                     |                 |E10 Transfer of Custody|
        |Besitz              |233966      |<leer>               |                 |E10 Transfer of Custody|
        |Besitz              |233966      |erhalten als Leihgabe|231996           |E10 Transfer of Custody|
        |Eigentum            |233967      |<leer>               |                 |E8 Acquisition         |
        |Eigentum            |233967      |erhalten im Tausch   |265972           |E8 Acquisition         |
        |Eigentum            |233967      |Erwerbsart unbekannt |231997           |E8 Acquisition         |
        |Eigentum            |233967      |erworben als Kauf    |231995           |E8 Acquisition         |
        |Eigentum            |233967      |erworben auf Auktion |231993           |E8 Acquisition         |
        |Eigentum            |233967      |geerbt               |231994           |E8 Acquisition         |
        |Einlagerung         |233965      |                     |                 |E10 Transfer of Custody|
        |Kommissionsware     |231984      |<leer>               |                 |E10 Transfer of Custody|
        |Leihgabe            |233964      |                     |                 |E10 Transfer of Custody|
        |Öffentliche Sammlung|231985      |                     |                 |E10 Transfer of Custody
        |Privatbesitz        |231986      |<leer>               |                 |E8 Acquisition         |
        |Private Sammlung    |231987      |Erwerbsart unbekannt |231997           |E8 Acquisition         |

        """
        logger = logging.getLogger(__name__)
        # Mappings
        mappings = {
            None: {
                None: {'type': 'E7_Activity', 'label': 'activity'},
                'default': {'type': 'E7_Activity', 'label': 'activity'},
                '231997': {'type': 'E7_Activity', 'label': 'activity'},
                '231993': {'type': 'E8_Acquisition', 'label': 'acquisition'},
                '231994': {'type': 'E8_Acquisition', 'label': 'acquisition'}
            },
            '234014': {
                'default': {'type': 'E10_Transfer_of_Custody', 'label': 'transfer of custody'},
            },
            '233966': {
                'default': {'type': 'E10_Transfer_of_Custody', 'label': 'transfer of custody'}
            },
            '233967': {
                'default': {'type': 'E8_Acquisition', 'label': 'acquisition'}
            },
            '233965': {
                'default': {'type': 'E10_Transfer_of_Custody', 'label': 'transfer of custody'}
            },
            '231984': {
                'default': {'type': 'E10_Transfer_of_Custody', 'label': 'transfer of custody'}
            },
            '233964': {
                'default': {'type': 'E10_Transfer_of_Custody', 'label': 'transfer of custody'}
            },
            '231985': {
                'default': {'type': 'E10_Transfer_of_Custody', 'label': 'transfer of custody'}
            },
            '231986': {
                'default': {'type': 'E8_Acquisition', 'label': 'acquisition'}
            },
            '231987': {
                'default': {'type': 'E8_Acquisition', 'label': 'acquisition'}
            }
        }
        # Retrieve all vocabulary reference fields
        moduleItems = root.findall(".//moduleItem")
        for moduleItem in moduleItems:
            typeField = moduleItem.find(".//vocabularyReference[@name='OwsOwnerTypeVoc']/vocabularyReferenceItem")
            acquisitionField = moduleItem.find(".//vocabularyReference[@name='OwsAcquisitionTypeVoc']/vocabularyReferenceItem")
            if typeField is None:
                typeId = None
            else:
                typeId = typeField.attrib.get('id')
            if acquisitionField is None:
                acquisitionId = None
            else:
                acquisitionId = acquisitionField.attrib.get('id')
            typeMappings = mappings.get(typeId)
            if typeMappings:
                crmType = typeMappings.get(acquisitionId)
                if not crmType:
                    crmType = typeMappings.get('default')
                if crmType is not None:
                    transaction_elem = ET.SubElement(moduleItem, f'{self.PREFIX}transaction')
                    transaction_elem.set('type', crmType['type'])
                    transaction_elem.set('label', crmType['label'])
                else:
                    logger.error(f'No mapping found for typeId {typeId} and acquisitionId {acquisitionId}')
            else:
                logger.error(f'No mapping found for typeId {typeId}.')

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