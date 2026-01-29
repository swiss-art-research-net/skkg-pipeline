"""
Download a single item from a module in MuseumPlus by UUID and save it as an XML file.

This mirrors the behavior of downloadItems.py:
- Writes to temp folder first (safe to interrupt/retry)
- Renames final file to <filenamePrefix><uuid>.xml in output folder
- Updates per-file lastModified in metadata.json
- Optionally overwrites existing file with --force

Usage:
    python downloadItemByUuid.py --url <url> --module <module> --uuid <uuid> --username <username> --password <password> --outputFolder <outputFolder> --tempFolder <tempFolder> [--filenamePrefix item-] [--force]
"""

import argparse
from os.path import join, exists
from os import remove as removeFile
from lxml import etree

from lib.Metadata import ItemMetadata
from lib.MuseumPlusConnector import MPWrapper
from lib.Utils import createXMLCopy

from config.moduleQueryAdditions import moduleQueryAdditions


def _extract_uuid_and_last_modified(tree: etree._ElementTree):
    uuid = tree.find('.//{http://www.zetcom.com/ria/ws/module}moduleItem').get('uuid')
    lastModified = tree.find(
        './/{http://www.zetcom.com/ria/ws/module}systemField[@name="__lastModified"]'
        '/{http://www.zetcom.com/ria/ws/module}value'
    ).text
    return uuid, lastModified


def downloadItemByUuid(*, host, username, password, module, uuid, outputFolder, tempFolder, filenamePrefix="item-", force=False):
    client = MPWrapper(url=host, username=username, password=password)
    queryAddition = moduleQueryAdditions.get(module, None)
    queryAddition = etree.fromstring(queryAddition) if queryAddition else None
    metadata = ItemMetadata(outputFolder)

    outFilename = f"{filenamePrefix}{uuid}.xml"
    outPath = join(outputFolder, outFilename)

    if exists(outPath) and not force:
        print(f"File already exists, skipping (use --force to overwrite): {outPath}")
        return

    tempFilename = f"{filenamePrefix}{uuid}.xml.part"
    tempPath = join(tempFolder, tempFilename)

    existsItem = client.existsItem(module=module, uuid=uuid, queryAddition=createXMLCopy(queryAddition))
    if not existsItem:
        print(f"Item with uuid={uuid} does not exist in module={module}")
        return
    item = client.getItemByUuid(module=module, uuid=uuid, queryAddition=createXMLCopy(queryAddition))
    with open(tempPath, "wb") as f:
        f.write(etree.tostring(item, pretty_print=True))
    tree = etree.parse(tempPath)

    # Validate / extract fields and store final
    try:
        extracted_uuid, lastModified = _extract_uuid_and_last_modified(tree)
    except Exception as e:
        print(f"Downloaded XML did not contain expected moduleItem/lastModified fields for uuid={uuid}")
        raise

    if extracted_uuid != uuid:
        print(f"Warning: requested uuid={uuid} but response uuid={extracted_uuid}. Saving with response uuid.")
        outFilename = f"{filenamePrefix}{extracted_uuid}.xml"
        outPath = join(outputFolder, outFilename)

    with open(outPath, "wb") as f:
        f.write(etree.tostring(tree, pretty_print=True))

    # Cleanup temp
    if exists(tempPath):
        removeFile(tempPath)

    # Update metadata for this file
    metadata.setLastUpdatedForFile(outFilename, lastModified, write=False)
    metadata.writeMetadata()

    print(f"Saved: {outPath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download one MuseumPlus item by UUID")
    parser.add_argument("--url", required=True, help="URL of the MuseumPlus instance")
    parser.add_argument("--module", required=True, help="Name of the module")
    parser.add_argument("--uuid", required=True, help="UUID of the item to download")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--outputFolder", required=True, help="Folder to save the XML")
    parser.add_argument("--tempFolder", required=True, help="Folder to store temp downloads")
    parser.add_argument("--filenamePrefix", required=False, default="item-", help='Filename prefix (default: "item-")')
    parser.add_argument("--force", action="store_true", help="Overwrite output and re-download even if it exists")

    args = parser.parse_args()

    downloadItemByUuid(
        host=args.url,
        module=args.module,
        uuid=args.uuid,
        username=args.username,
        password=args.password,
        outputFolder=args.outputFolder,
        tempFolder=args.tempFolder,
        filenamePrefix=args.filenamePrefix or "item-",
        force=args.force,
    )