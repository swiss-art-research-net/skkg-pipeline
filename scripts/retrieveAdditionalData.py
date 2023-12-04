import argparse
from os import path
from SPARQLWrapper import SPARQLWrapper, JSON
from string import Template
from tqdm import tqdm
from urllib import request

SOURCE_NAMESPACES  = {
    "aat": "http://vocab.getty.edu/",
    "gnd": "https://d-nb.info/gnd/",
    "loc": "http://id.loc.gov/vocabulary/relators/",
    "wd": "http://www.wikidata.org/entity/"
}

def retrieveAdditionalData(*, endpoint, sources, sameAsPredicate, outputFolder, outputFilePrefix=''):
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
    for source in sources:
        query = _getSourceQuery(source, sameAsPredicate)
        sparql.setQuery(query)
        results = _sparqlResultToDict(sparql.query().convert())
        outputFileName = path.join(outputFolder, "%s%s.ttl" % (outputFilePrefix, source))
        print(outputFileName)
        if source == "gnd":
            identifiers = [r["identifier"] for r in results]
            _retrieveGndData(identifiers, outputFileName)
        
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


def _getSourceQuery(source, sameAsPredicate):
    template = Template("""SELECT DISTINCT ?identifier WHERE { 
                        ?s <$sameAsPredicate> ?identifier . 
                        FILTER(STRSTARTS(STR(?identifier), '$namespace')) 
    }""")
    query = template.substitute(sameAsPredicate=sameAsPredicate, namespace=SOURCE_NAMESPACES[source])
    return query



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Retrieve additional data for URIs in the Triple Store from respective sources')
    parser.add_argument('--endpoint', type=str, default='http://blazegraph:8080/blazegraph/sparql', help='SPARQL Endpoint to query for URIs')
    parser.add_argument('--sources', nargs='+', default=['gnd'], help='Sources to retrieve additional data from. Supported sources: aat, gnd, loc, wikidata, loc')
    parser.add_argument('--sameAsPredicate', type=str, default='http://www.w3.org/2002/07/owl#sameAs', help='Predicate to use for sameAs links')
    parser.add_argument('--outputFolder', type=str, help='Folder to store the retrieved data', required=True)
    parser.add_argument('--outputFilePrefix', type=str, default='', help='Optional prefix for the output files')
    args = parser.parse_args()

    retrieveAdditionalData(endpoint=args.endpoint, sources=args.sources, sameAsPredicate=args.sameAsPredicate, outputFolder=args.outputFolder, outputFilePrefix=args.outputFilePrefix)
