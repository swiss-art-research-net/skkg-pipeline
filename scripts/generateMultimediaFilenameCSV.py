import argparse
from csv import DictWriter
from lxml import etree
from os import makedirs, listdir
from os.path import dirname, isfile, join
from tqdm import tqdm

NAMESPACES = {
    'ns': 'http://www.zetcom.com/ria/ws/module'
}

def generateMultimediaFilenameCSV(*, multimediaFolder: str, objectsFolder: str, outputFile: str):
    try:
        multimediaFiles = [f for f in listdir(multimediaFolder) if isfile(join(multimediaFolder, f)) and f.endswith('.xml')]
    except Exception as e:
        print(f"Error accessing {multimediaFolder}: {e}")
        return

    try:
        objectFiles = [f for f in listdir(objectsFolder) if isfile(join(objectsFolder, f)) and f.endswith('.xml')]
    except Exception as e:
        print(f"Error accessing {objectsFolder}: {e}")
        return
    
    multimediaItems = {}

    for file in tqdm(multimediaFiles):
        tree = etree.parse(join(multimediaFolder, file))
        try:
            uuid = tree.find('.//ns:moduleItem', namespaces=NAMESPACES).get('uuid')
        except Exception as e:
            print(etree.tostring(tree))
            print(f"Error retrieving uuid from {file}: {e}")
            import sys
            sys.exit(1)

        if not uuid in multimediaItems:
            multimediaItems[uuid] = {}
        # Get the filename
        filenameElement = tree.find('.//ns:dataField[@name="MulOriginalFileTxt"]/ns:value', namespaces=NAMESPACES)
        if filenameElement is not None:
            multimediaItems[uuid]['filename'] = filenameElement.text
        # Retrieve module ID
        multimediaItems[uuid]['moduleId'] = tree.find('.//ns:moduleItem', namespaces=NAMESPACES).get('id')
        # Retrieve usage
        multimediaItems[uuid]['usage'] = tree.find('.//ns:moduleItem/ns:vocabularyReference[@instanceName="MulUsageVgr"]/ns:vocabularyReferenceItem/ns:formattedValue', namespaces=NAMESPACES).text
        # Retrieve category
        categoryElement = tree.find('.//ns:moduleItem/ns:vocabularyReference[@instanceName="MulCategoryVgr"]/ns:vocabularyReferenceItem/ns:formattedValue', namespaces=NAMESPACES)
        if categoryElement is not None:
            multimediaItems[uuid]['category'] = categoryElement.text
    
    for file in tqdm(objectFiles):
        tree = etree.parse(join(objectsFolder, file))
        objectElement = tree.find('.//ns:moduleItem', namespaces=NAMESPACES)
        if objectElement is None:
            continue 
        # Retrieve object uuid
        objectUuid = objectElement.get('uuid')
        # Retrieve object id
        objectId = objectElement.get('id')
        # Retrieve inventory number
        try:
            objectInvNr = tree.find('.//ns:repeatableGroup[@name="ObjObjectNumberGrp"]/ns:repeatableGroupItem/ns:virtualField[@name="NumberVrt"]/ns:value', namespaces=NAMESPACES).text.strip()
        except:
            objectInvNr = ''
        # Retrieve linked multimedia items
        moduleReferenceItems = tree.findall('.//ns:moduleReference[@name="ObjMultimediaRef"]/ns:moduleReferenceItem', namespaces=NAMESPACES)
        for moduleReferenceItem in moduleReferenceItems:
            # Get uuid of multimedia item
            uuid = moduleReferenceItem.get('uuid')
            # Get id of multimedia item
            multimediaModuleId = moduleReferenceItem.get('id')
            # Update entry only if it exists already
            if not uuid in multimediaItems:
                continue
            # Add object IDs
            if not 'objectIds' in multimediaItems[uuid]:
                multimediaItems[uuid]['objectIds'] = []
            multimediaItems[uuid]['objectIds'].append(objectId)
            # Add object uuids
            if not 'objectUuids' in multimediaItems[uuid]:
                multimediaItems[uuid]['objectUuids'] = []
            multimediaItems[uuid]['objectUuids'].append(objectUuid)
            # Add inventory numbers
            if not 'objectInvNrs' in multimediaItems[uuid]:
                multimediaItems[uuid]['objectInvNrs'] = []
            multimediaItems[uuid]['objectInvNrs'].append(objectInvNr)
            # If filename is not present, retrieve from formatted value
            if not 'filename' in multimediaItems[uuid]:
                # Get filename from object
                filenameElement = moduleReferenceItem.find('./ns:formattedValue', namespaces=NAMESPACES)
                if filenameElement is not None:
                    if len(filenameElement.text.split(', ')) > 1:
                        multimediaItems[uuid]['filename'] = filenameElement.text.split(', ')[1]
        
    # Sort uuids for output
    uuids = sorted(multimediaItems.keys())

    # Ensure output directory exists
    makedirs(dirname(outputFile), exist_ok=True)
    
    # Write output to CSV
    with open(outputFile, 'w') as f:
        writer = DictWriter(f, fieldnames=('uuid' ,'filename','multimediaId','objectUuids','objectIds','objectInvNrs', 'category', 'usage'))
        writer.writeheader()
        for uuid in uuids:
            item = multimediaItems[uuid]
            if 'usage' in item and 'Intern' not in item['usage']:
                row = {
                    'uuid': uuid,
                    'filename': item['filename'] if 'filename' in item else '',
                    'multimediaId': item['moduleId'] if 'moduleId' in item else '',
                    'objectUuids': ';'.join(item['objectUuids']) if 'objectUuids' in item else '',
                    'objectIds': ';'.join(item['objectIds']) if 'objectIds' in item else '',
                    'objectInvNrs': ';'.join(item['objectInvNrs']) if 'objectInvNrs' in item else '',
                    'category': item['category'] if 'category' in item else '',
                    'usage': item['usage'],
                }
                writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Generate a CSV file with correspondences between multimedia item uuids and their filenames, along with linked objects.')
    parser.add_argument('--multimediaFolder', type=str, default='/data/source/multimedia', help='Folder containing multimedia XML files')
    parser.add_argument('--objectsFolder', type=str, default='/data/source/object', help='Folder containing object XML files')
    parser.add_argument('--outputFile', type=str, default='/data/csv/multimediaCorrespondences.csv', help='Output file')
    args = parser.parse_args()

    generateMultimediaFilenameCSV(multimediaFolder=args.multimediaFolder, objectsFolder=args.objectsFolder, outputFile=args.outputFile)