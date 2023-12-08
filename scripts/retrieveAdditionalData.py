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

def runDataRetrieval(*, endpoint, sources, predicates, outputFolder, outputFilePrefix='', ingest=False, ingestNamespace=None):
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
    sourceRetrievalFunctions = {
        "aat": retrieveAatData,
        "gnd": retrieveGndData,
        "loc": retrieveLocData
    }

    for source in sources:
        query = getSourceQuery(source, predicates)
        sparql.setQuery(query)
        results = sparqlResultToDict(sparql.query().convert())
        outputFileName = path.join(outputFolder, "%s%s.ttl" % (outputFilePrefix, source))
        identifiers = [r["identifier"] for r in results]

        if source in sourceRetrievalFunctions:
            logs[source] = sourceRetrievalFunctions[source](identifiers, outputFileName)
        else:
            logs[source] = {
                "status": "error",
                "message": "Source %s is not supported" % source
            }

    printLogs(logs)

    if ingest:
        ingestRetrievedData(endpoint, sources, outputFolder, outputFilePrefix, ingestNamespace)

def getSourceQuery(source, predicates):
    predicatesForQuery = '|'.join(["<%s>" % d for d in predicates])
    template = Template("""SELECT DISTINCT ?identifier WHERE { 
                        ?s $predicates ?identifier . 
                        FILTER(STRSTARTS(STR(?identifier), '$namespace')) 
    }""")
    query = template.substitute(predicates=predicatesForQuery, namespace=SOURCE_NAMESPACES[source])
    return query

def queryIdentifiersInFile(sourceFile, queryPart):
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

def ingestRetrievedData(endpoint, sources, inputFolder, filePrefix, ingestNamespace=None):
    sparql = SPARQLWrapper(endpoint)
    for source in sources:
        filename = path.join(inputFolder, "%s%s.ttl" % (filePrefix, source))
        if path.isfile(filename):
            if ingestNamespace is not None:
                namedGraph = "%s%s" % (ingestNamespace, source)
            with open(filename, 'rb') as f:
                data = f.read()
                headers = {'Content-Type': 'text/turtle'}
                if namedGraph:
                    # Drop the named graph if it already exists
                    sparql.setQuery("DROP GRAPH <%s>" % namedGraph)
                    sparql.method = 'POST'
                    result = sparql.query()
                if ingestNamespace is not None:
                    sourceEndpoint = endpoint + "?context-uri=%s" % namedGraph
                else:
                    sourceEndpoint = endpoint
                try:
                    r = requests.post(sourceEndpoint, data=data, headers=headers)
                    if r.status_code == 200:
                        print("Successfully ingested %s" % filename)
                    else:
                        print("Could not ingest %s because of an error" % filename)
                        print(r.text)
                except:
                    print("Could not ingest %s because of an error" % filename)


        else:
            print("Could not ingest %s because the file does not exist" % filename)

def retrieveAatData(identifiers, outputFile):
    """
    Retrieves the data for the given identifiers and writes it to a file named aat.ttl in the target folder.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the Getty AAT.
    :param identifiers: The list of identifiers to retrieve.
    :param targetFolder: The folder where the data is stored.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    existingIdentifiers = queryIdentifiersInFile(outputFile, "?identifier a gvp:Concept .")
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

def retrieveGndData(identifiers, outputFile):
    """
    Retrieves the data for the given identifiers and writes it to an output file.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the LOBID API.
    :param identifiers: The list of identifiers to retrieve.
    :param outputFile: The output file to write the data to.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    existingIdentifiers = queryIdentifiersInFile(outputFile, "?identifier a gndo:AuthorityResource .")
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

def retrieveLocData(identifiers, outputFile):
    """
    Retrieves the data for the given identifiers and writes it to a file named loc.ttl in the target folder.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the Library of Congress API.
    :param identifiers: The list of identifiers to retrieve.
    :param targetFolder: The folder where the data is stored.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    existingIdentifiers = queryIdentifiersInFile(outputFile, "?identifier a <http://www.loc.gov/mads/rdf/v1#Authority> .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(outputFile, 'a') as f:
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.nt" % identifier
            try:
                firstRequest = requests.get(url)
                # Follow redirect
                if firstRequest.status_code == 200:
                    f.write(firstRequest.text + "\n")
                elif firstRequest.status_code == 301:
                    url = firstRequest.headers['location']
                    secondRequest = requests.get(url)
                    f.write(secondRequest.text + "\n")
            except:
                print("Could not retrieve", url)

        f.close()
    return {
        "status": "success",
        "message": "Retrieved %d additional LOC identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def printLogs(logs):
    """
    Print the logs for the data retrieval
    :param logs: A dictionary with the status and a message for each source, contains keys 'status' and 'message'
    """
    # Print a summary stating how many sources were retrieved successfully
    successCount = len([source for source in logs if logs[source]["status"] == "success"])
    print("Successfully retrieved data for %d sources" % successCount)
    # If there have been errors, print how many sources produced errors
    if successCount < len(logs):
        errorCount = len([source for source in logs if logs[source]["status"] == "error"])
        print("Could not retrieve data for %d sources" % errorCount)
    for source in logs:
        # Depending on the status (success or error), print the message in green or red
        if logs[source]["status"] == "success":
            print("\033[92m%s\033[0m: %s" % (source, logs[source]["message"]))
        else:
            print("\033[91m%s\033[0m: %s" % (source, logs[source]["message"]))

def sparqlResultToDict(results):
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
    parser.add_argument('--sources', type=str, default='aat,gnd,loc', help='Sources to retrieve additional data from. Supported sources: aat, gnd, loc, wikidata, loc. Provide as comma separated list.')
    parser.add_argument('--predicates', type=str, default='http://www.w3.org/2002/07/owl#sameAs', help='Predicates to use for retrieving external data. Provide as comma separated list.')
    parser.add_argument('--outputFolder', type=str, help='Folder to store the retrieved data', required=True)
    parser.add_argument('--outputFilePrefix', type=str, default='', help='Optional prefix for the output files')
    parser.add_argument('--ingest', type=bool, default=False, help='Ingest the retrieved data into the Triple Store')
    parser.add_argument('--ingestNamespace', type=str, help='Namespace for named graphs where sources will be ingested to. The source name will be appended to the namespace.')
    args = parser.parse_args()

    if args.predicates is not None:
        args.predicates = [s.strip() for s in args.predicates.split(",")]

    if args.sources is not None:
        args.sources = [s.strip() for s in args.sources.split(",")]

    runDataRetrieval(endpoint=args.endpoint, sources=args.sources, predicates=args.predicates, outputFolder=args.outputFolder, outputFilePrefix=args.outputFilePrefix, ingest=args.ingest, ingestNamespace=args.ingestNamespace)
