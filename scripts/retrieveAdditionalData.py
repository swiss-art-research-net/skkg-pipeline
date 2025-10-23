import argparse
import re
import requests
from os import path
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON
from string import Template
from time import sleep
from tqdm import tqdm
from urllib import request

PREFIXES = """
    PREFIX gvp:  <http://vocab.getty.edu/ontology#>
    PREFIX gndo:  <https://d-nb.info/standards/elementset/gnd#>
    PREFIX lt: <http://terminology.lido-schema.org/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    """

SOURCE_NAMESPACES  = {
    "aat": "http://vocab.getty.edu/",
    "gnd": "https://d-nb.info/gnd/",
    "loc": "http://id.loc.gov/vocabulary/relators/",
    "lt": "http://terminology.lido-schema.org/",
    "wd": "http://www.wikidata.org/entity/"
}

def runDataRetrieval(*, endpoint, sources, predicates, outputFolder, outputFilePrefix='', ingest=False, ingestNamespace=None, ingestUpdate=False, options=None):
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
        "loc": retrieveLocData,
        "lt": retrieveLtData,
        "wd": retrieveWdData
    }

    for source in sources:
        query = getSourceQuery(source, predicates, ingestNamespace)
        sparql.setQuery(query)
        results = sparqlResultToDict(sparql.query().convert())
        outputFileName = path.join(outputFolder, "%s%s.ttl" % (outputFilePrefix, source))
        identifiers = [r["identifier"] for r in results]
        # If no identifiers are found, skip the source
        if len(identifiers) == 0:
            logs[source] = {
                "status": "info",
                "numRetrieved": 0,
                "message": "No identifiers found for source %s" % source
            }
        elif source in sourceRetrievalFunctions:
            logs[source] = sourceRetrievalFunctions[source](identifiers, outputFileName, **(options.get(source, {}) if options else {}))
        else:
            logs[source] = {
                "status": "error",
                "message": "Source %s is not supported" % source
            }

    printLogs(logs)

    if ingest:
        if ingestUpdate:
            # Remove sources for which no new data has been retrieved
            ingestSources = [source for source in sources if logs[source]["numRetrieved"] > 0]
            print("Ingesting data for %d sources" % len(ingestSources))
        else:
            # Ingest all sources
            ingestSources = sources
        ingestRetrievedData(endpoint, ingestSources, outputFolder, outputFilePrefix, ingestNamespace)

def getSourceQuery(source, predicates, ingestNamespace=None):
    predicatesForQuery = '|'.join(["<%s>" % d for d in predicates])
    if ingestNamespace is not None:
        # If an ingest namespace is provided, query for identifiers that are not in the named graph 
        # to avoid accidental recursive retrieval of the entire external dataset.
        namedGraph = "%s%s" % (ingestNamespace, source)
        template = Template("""SELECT DISTINCT ?identifier WHERE {
            GRAPH ?g {
                ?s $predicates ?identifier .
            }
            FILTER(STRSTARTS(STR(?identifier), '$namespace'))
            FILTER(?g != <$namedGraph>)
        }""")
        query = template.substitute(predicates=predicatesForQuery, namespace=SOURCE_NAMESPACES[source], namedGraph=namedGraph)
    else:
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
                        print("Successfully ingested %s" % source)
                    else:
                        print("Could not ingest %s because of an error" % source)
                        print(r.text)
                except:
                    print("Could not ingest %s because of an error" % source)
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
        print("Retrieving %d AAT identifiers" % len(identifiersToRetrieve))
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
        "numRetrieved": len(identifiersToRetrieve),
        "message": "Retrieved %d additional AAT identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def retrieveGndData(identifiers, outputFile, *, predicates=None, depth=0, maxDepth=2):
    """
    Retrieves the data for the given identifiers and writes it to an output file.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the LOBID API.
    :param identifiers: The list of identifiers to retrieve.
    :param outputFile: The output file to write the data to.
    :param predicates: The predicates to use for retrieving additional identifiers recursively.
    :param depth: The current recursion depth.
    :param maxDepth: The maximum recursion depth.
    :return: A dictionary with the status and a message.
    """

    DEFAULT_GND_PREDICATES = [
        "gndo:placeOfActivity",
        "gndo:placeOfBirth",
        "gndo:placeOfDeath"
    ]

    # Read the output file and query for existing URIs
    existingIdentifiers = queryIdentifiersInFile(outputFile, "?identifier a gndo:AuthorityResource .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(outputFile, 'a') as outputFileHandle:
        print("Retrieving %d GND identifiers" % len(identifiersToRetrieve))
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.ttl" % identifier.replace("https://d-nb.info/gnd/","https://lobid.org/gnd/")
            try:
                with request.urlopen(url) as r:
                    content = r.read().decode()
                outputFileHandle.write(content + "\n")
                outputFileHandle.flush()
            except:
                print("Could not retrieve", url)
    status = {
        "status": "success",
        "numRetrieved": len(identifiersToRetrieve),
        "message": "Retrieved %d additional GND identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }
    depth += 1
    if depth < maxDepth:
        # Recursively retrieve data for any new identifiers found in the retrieved data
        if predicates is None:
            predicates = DEFAULT_GND_PREDICATES
        newIdentifiers = queryIdentifiersInFile(outputFile, "?entity ?predicate ?identifier . VALUES (?predicate) { %s }" % ' '.join(f"({p})" for p in predicates))
        identifiersToRetrieve = [d for d in newIdentifiers if d not in existingIdentifiers]
        if len(identifiersToRetrieve) > 0:
            print("Recursively retrieving data for %d new GND identifiers at depth %d" % (len(identifiersToRetrieve), depth))
            newStatus = retrieveGndData(identifiersToRetrieve, outputFile, depth=depth, maxDepth=maxDepth)
            if newStatus["status"] == "success":
                status["numRetrieved"] += newStatus["numRetrieved"]
                status["message"] = "Retrieved %d additional GND identifiers (%d present in total)" % (status["numRetrieved"], len(identifiers))
            else:
                status = newStatus
    return status            
    
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
        print("Retrieving %d LOC identifiers" % len(identifiersToRetrieve))
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
        "numRetrieved": len(identifiersToRetrieve),
        "message": "Retrieved %d additional LOC identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def retrieveLtData(identifiers, outputFile):
    """
    Retrieves the data for the given identifiers and writes it to an output file.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the LIDO API.
    :param identifiers: The list of identifiers to retrieve.
    :param outputFile: The output file to write the data to.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    existingIdentifiers = queryIdentifiersInFile(outputFile, "?identifier a skos:Concept .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(outputFile, 'a') as outputFile:
        print("Retrieving %d LIDO Terminology identifiers" % len(identifiersToRetrieve))
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.ttl" % identifier
            try:
                with request.urlopen(url) as r:
                    content = r.read().decode()
                outputFile.write(content + "\n")
                outputFile.flush()
            except:
                print("Could not retrieve", url)
    return {
        "status": "success",
        "numRetrieved": len(identifiersToRetrieve),
        "message": "Retrieved %d additional LIDO Terminology identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def retrieveWdData(identifiers, outputFile, *, constructQuery=None):
    """
    Retrieves the data for the given identifiers and writes it to a file named wd.ttl in the specified output file.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the Wikidata SPARQL Endpoint.
    :param identifiers: The list of identifiers to retrieve.
    :param outputFile: The file path where the data is written.
    :param constructQuery: Optional custom CONSTRUCT query to use for data retrieval. VALUES clause for ?entity will be added automatically.
    :return: A dictionary with the status and a message.
    """

    DEFAULT_WD_CONSTRUCT_QUERY = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        CONSTRUCT {
        ?entity rdfs:label ?label ;
                wdt:P625 ?coordinates ;
                wdt:P18 ?image .
        }
        WHERE {
            { ?entity rdfs:label ?label . FILTER(LANG(?label) = "de") }
            UNION { ?entity wdt:P625 ?coordinates . }
            UNION { ?entity wdt:P18 ?image . }
        }
    """

    def chunker(seq, size):
        """
        Function to loop through list in chunks
        Yields successive chunks from seq.
        :param seq: The list to loop through.
        :param size: The size of the chunks.
        """
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    # Read the output file and query for existing URIs
    # targetFile = path.join(targetFolder, 'wd.ttl')
    existingIdentifiers = queryIdentifiersInFile(outputFile, "?identifier wdt:P31 ?type .")

    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]

    # Retrieve relevant data from Wikidata and append to ttl file
    wdEndpoint = "https://query.wikidata.org/sparql"
    batchSizeForRetrieval = 20
    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    sparql = SPARQLWrapper(wdEndpoint, agent=agent)    
    # with open(targetFile, 'a') as outputFile:
    with open(outputFile, 'a') as outputFile:
        if constructQuery is None:
            constructQuery = DEFAULT_WD_CONSTRUCT_QUERY
        print("Retrieving %d Wikidata identifiers in %d chunks" % (len(identifiersToRetrieve), (len(identifiersToRetrieve) + batchSizeForRetrieval - 1) // batchSizeForRetrieval))
        for batch in tqdm(chunker(identifiersToRetrieve, batchSizeForRetrieval)):
            valuesClause = """
            VALUES (?entity) {
                %s
            }""" % ( "(<" + ">)\n(<".join(batch) + ">)" )
            query = re.sub(r'\}\s*$', valuesClause + "\n}", constructQuery, flags=re.DOTALL)
            sparql.setQuery(query)
            try:
                results = sparql.query().convert()
            except request.HTTPError as exception:
                print(exception)
            sleep(3)
            outputFile.write(results.serialize(format='turtle'))
    return {
        "status": "success",
        "numRetrieved": len(identifiersToRetrieve),
        "message": "Retrieved %d additional Wikidata identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
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
    parser.add_argument('--ingestUpdate', type=bool, default=False, help='Ingest the data only if new data has been retrieved')
    parser.add_argument('--wdConstructQuery', type=str, help='Optional custom CONSTRUCT query to use for Wikidata data retrieval. VALUES bound for ?entity will be added automatically.')
    parser.add_argument('--gndPredicates', type=str, help='Optional predicates to use for recursively retrieving additional GND identifiers. Provide as comma separated list of full URIs or gndo: predicates.')
    args = parser.parse_args()

    if args.predicates is not None:
        args.predicates = [s.strip() for s in args.predicates.split(",")]

    if args.sources is not None:
        args.sources = [s.strip() for s in args.sources.split(",")]

    options = {}
    if args.wdConstructQuery is not None:
        options['wd'] = {
            'constructQuery': args.wdConstructQuery
        }
    if args.gndPredicates is not None:
        gndPredicates = []
        for s in args.gndPredicates.split(","):
            s = s.strip()
            if s.startswith("http://") or s.startswith("https://"):
                gndPredicates.append(f"<{s}>")
            elif s.startswith("gndo:") and " " not in s:
                gndPredicates.append(s)
            else:
                raise ValueError(f"Invalid predicate format: {s}. Must be a full URI or start with 'gndo:'.")
        options['gnd'] = {
            'predicates': gndPredicates
        }

    runDataRetrieval(endpoint=args.endpoint, sources=args.sources, predicates=args.predicates, outputFolder=args.outputFolder, outputFilePrefix=args.outputFilePrefix, ingest=args.ingest, ingestNamespace=args.ingestNamespace, ingestUpdate=args.ingestUpdate, options=options)
