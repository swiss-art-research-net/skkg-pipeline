import argparse
import requests
from os import path
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON
from string import Template
from tqdm import tqdm
from urllib import request

PREFIXES = """
    PREFIX gvp:  <http://vocab.getty.edu/ontology#>
    PREFIX gndo:  <https://d-nb.info/standards/elementset/gnd#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    """

SOURCE_NAMESPACES  = {
    "aat": "http://vocab.getty.edu/",
    "gnd": "https://d-nb.info/gnd/",
    "loc": "http://id.loc.gov/vocabulary/relators/",
    "wd": "http://www.wikidata.org/entity/"
}

def retrieveAdditionalData(*, endpoint, sources, predicates, outputFolder, outputFilePrefix=''):
    """Retrieve additional data for URIs in the Triple Store from respective sources

    Args:
        endpoint (str): SPARQL Endpoint to query for URIs
        sources (list): Sources to retrieve additional data from. Supported sources: aat, gnd, loc, wikidata, loc
        sameAsPredicate (str): Predicate to use for sameAs links
        outputFolder (str): Folder to store the retrieved data
        outputFilePrefix (str): Optional prefix for the output files
    """
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    logs = {}
    for source in sources:
        query = _getSourceQuery(source, predicates)
        sparql.setQuery(query)
        results = _sparqlResultToDict(sparql.query().convert())
        outputFileName = path.join(outputFolder, "%s%s.ttl" % (outputFilePrefix, source))
        identifiers = [r["identifier"] for r in results]

        if source == "aat":
            logs[source] = _retrieveAatData(identifiers, outputFileName)
        elif source == "gnd":
            logs[source] = _retrieveGndData(identifiers, outputFileName)
    print(logs)
        


def _getSourceQuery(source, predicates):
    predicatesForQuery = '|'.join(["<%s>" % d for d in predicates])
    template = Template("""SELECT DISTINCT ?identifier WHERE { 
                        ?s $predicates ?identifier . 
                        FILTER(STRSTARTS(STR(?identifier), '$namespace')) 
    }""")
    query = template.substitute(predicates=predicatesForQuery, namespace=SOURCE_NAMESPACES[source])
    print(query)
    return query

def _queryIdentifiersInFile(sourceFile, queryPart):
    """
    Queries the given file for identifiers and returns a list of the identifiers found.
    Expects a part of a SPARQL select query that is used in the WHERE clause that returns the identifier as ?identifier.
    
    :param sourceFile: The Turtle file to query.
    :param queryPart: A part of a SPARQL select query that is used in the WHERE clause that returns the identifier as ?identifier.
    :return: A list of the identifiers found.
    """
    identifiers = []
    if path.isfile(sourceFile):
        data = Graph()
        data.parse(sourceFile, format='turtle')
        queryResults = data.query(PREFIXES + "\nSELECT DISTINCT ?identifier WHERE {" + queryPart + "}")
        for row in queryResults:
            identifiers.append(str(row[0]))
    return identifiers

def _retrieveAatData(identifiers, outputFile):
    """
    Retrieves the data for the given identifiers and writes it to a file named aat.ttl in the target folder.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the Getty AAT.
    :param identifiers: The list of identifiers to retrieve.
    :param targetFolder: The folder where the data is stored.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    existingIdentifiers = _queryIdentifiersInFile(outputFile, "?identifier a gvp:Concept .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(outputFile, 'a') as outputFile:
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.ttl" % identifier
            try:
                firstRequest = requests.get(url)
                # Follow redirect
                if firstRequest.status_code == 200:
                    outputFile.write(firstRequest.text + "\n")
                elif firstRequest.status_code == 301:
                    url = firstRequest.headers['location']
                    secondRequest = requests.get(url)
                    outputFile.write(secondRequest.text + "\n")
            except:
                print("Could not retrieve", url)

        outputFile.close()
    return {
        "status": "success",
        "message": "Retrieved %d additional AAT identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def _retrieveGndData(identifiers, outputFile):
    """
    Retrieves the data for the given identifiers and writes it to an output file.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the LOBID API.
    :param identifiers: The list of identifiers to retrieve.
    :param outputFile: The output file to write the data to.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    existingIdentifiers = _queryIdentifiersInFile(outputFile, "?identifier a gndo:AuthorityResource .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(outputFile, 'a') as outputFile:
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.ttl" % identifier.replace("https://d-nb.info/gnd/","https://lobid.org/gnd/")
            try:
                with request.urlopen(url) as r:
                    content = r.read().decode()
                outputFile.write(content + "\n")
                outputFile.flush()
            except:
                print("Could not retrieve", url)
    return {
        "status": "success",
        "message": "Retrieved %d additional GND identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def _sparqlResultToDict(results):
    """
    Convert a SPARQL query result to a list of dictionaries
    :param results: The SPARQL query result returned from SPARQLWrapper
    """
    rows = []
    for result in results["results"]["bindings"]:
        row = {}
        for key in list(result.keys()):
            row[key] = result[key]["value"]
        rows.append(row)
    return rows



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Retrieve additional data for URIs in the Triple Store from respective sources')
    parser.add_argument('--endpoint', type=str, default='http://blazegraph:8080/blazegraph/sparql', help='SPARQL Endpoint to query for URIs')
    parser.add_argument('--sources', type=str, default='aat,gnd', help='Sources to retrieve additional data from. Supported sources: aat, gnd, loc, wikidata, loc. Provide as comma separated list.')
    parser.add_argument('--predicates', type=str, default='http://www.w3.org/2002/07/owl#sameAs', help='Predicates to use for retrieving external data. Provide as comma separated list.')
    parser.add_argument('--outputFolder', type=str, help='Folder to store the retrieved data', required=True)
    parser.add_argument('--outputFilePrefix', type=str, default='', help='Optional prefix for the output files')
    args = parser.parse_args()

    if args.predicates is not None:
        args.predicates = [s.strip() for s in args.predicates.split(",")]

    if args.sources is not None:
        args.sources = [s.strip() for s in args.sources.split(",")]

    retrieveAdditionalData(endpoint=args.endpoint, sources=args.sources, predicates=args.predicates, outputFolder=args.outputFolder, outputFilePrefix=args.outputFilePrefix)
