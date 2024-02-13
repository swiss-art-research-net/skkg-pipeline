
import argparse
from lxml import etree
from pyexistdb import db

def updateMappingFromDB(*, id, outputFile, url="http://3m:8081/exist", user="admin", password="admin"):
    # Create a connection to eXist-db
    existdb = db.ExistDB(url, user, password)

    # Define your XQuery expression
    xquery = f"""
    xquery version "3.0";

    doc("/db/DMSCOLLECTION/3M/Mapping/1/Mapping{id}.xml")
    """

    # Execute the XQuery
    response = existdb.query(xquery)

    root = response.results[0]

    # We want to retain only the namespaces and mappings
    namespaces = root.find("namespaces")
    mappings = root.find("mappings")

    # Create a new root element
    newRoot = etree.Element("x3ml")

    # Add the attributes from the original root to the new root
    for key, value in root.attrib.items():
        newRoot.set(key, value)

    # Add the namespaces and mappings to the new root
    newRoot.append(namespaces)
    newRoot.append(mappings)

    # Write the new root to a file
    with open(outputFile, "wb") as f:
        f.write(etree.tostring(newRoot, pretty_print=True))

    print(f"Mapping {id} has been written to {outputFile}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description = 'Retrieve a mapping from eXist-db and write it to a file')
    parser.add_argument('--id', required=True, help='ID of the mapping to retrieve')
    parser.add_argument('--outputFile', required=True, help='File to write the mapping to')
    parser.add_argument('--url', default="http://3m:8081/exist", help='URL of the eXist-db instance')
    parser.add_argument('--user', default="admin", help='Username to connect to eXist-db')
    parser.add_argument('--password', default="admin", help='Password to connect to eXist-db')
    args = parser.parse_args()

    updateMappingFromDB(id=args.id, outputFile=args.outputFile, url=args.url, user=args.user, password=args.password)
