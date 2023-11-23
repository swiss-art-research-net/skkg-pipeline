"""
Validate a directory of Turtle files using a SHACL Shape Graph. 
Optionally ingest the validation results into a Triplestore if the validation fails.

Usage:
python validateTurtleWithShacl.py --directory <directory> --shapesGraph <shapesGraph> --ontologyFile <ontologyFile> --endpoint <endpoint> --namedGraph <namedGraph>

Arguments:
--directory: Directory containing the Turtle files to validate
--shapesGraph: Path to the SHACL Shape Graph to use for validation
--ontologyFile: Path to an ontology file to use for validation
--endpoint: URL of the SPARQL endpoint to ingest the validation results into (optional)
--namedGraph: URI of the named graph to ingest the validation results into (optional)
"""


import argparse
import requests
import glob
from pyshacl import validate
from os.path import join, isfile
from rdflib import Graph
from tqdm import tqdm

def validateTurtleWithShacl(*, directory, shapesGraph, ontologyFiles=False, endpoint=False, namedGraph=''):
    # Read SHACL shape graph into graph
    shaclGraph = Graph()
    shaclGraph.parse(shapesGraph, format='turtle')

    # Read ontology files into graph
    ontologyGraph = Graph()
    if ontologyFiles:
        for file in ontologyFiles:
            # Check extension of file
            if file.endswith('.ttl'):
                ontologyGraph.parse(file, format='turtle')
            elif file.endswith('.rdfs'):
                ontologyGraph.parse(file, format='xml')

    validationSuccessful = True
    ttlOutput = ''
    
    print("Validating...")
    for file in tqdm(glob.iglob(directory + '/*.ttl')):
        # Read RDF file into graph
        dataGraph = Graph()
        dataGraph.parse(join(directory, file), format='turtle')
        # Validate
        r = validate(dataGraph,
                shacl_graph=shaclGraph,
                 shacl_graph_format='turtle',
                 do_owl_imports=True,
                 ont_graph=ontologyGraph,
                 inference='rdfs',
                 abort_on_first=True,
                 serialize_report_graph=False,
                 allow_warnings=False,
                 debug=False
        )
        conforms, results_graph, results_text = r
    
        if not conforms:
            validationSuccessful = False
            if endpoint:
                ttlOutput += results_graph.serialize(format='turtle')
    
    if validationSuccessful:
        print("Validation successful!")
    else:
        print("Validation failed!")
        if endpoint:
            print("Ingesting validation results into endpoint...")
            ttlOutput = results_graph.serialize(format='turtle')
            if namedGraph:
                url = endpoint + "?context-uri=" + namedGraph
            else:
                url = endpoint
            r = requests.post(url, data=ttlOutput, headers={'Content-Type': 'application/x-turtle'})
            if r.status_code == 200:
                print("Ingestion successful!")
            else:
                print("Ingestion failed!")
                print(r.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Validate a directory of Turtle files using a SHACL Shape Graph. Optionally ingest the validation results into a Triplestore.')
    parser.add_argument('--directory', required=True, help='Directory containing the Turtle files to validate')
    parser.add_argument('--shapesGraph', required=True, help='Path to the SHACL Shape Graph to use for validation')
    parser.add_argument('--namedGraph', required=False, help='URI of the named graph to ingest the validation results into')
    parser.add_argument('--ontologyFile', required=False, action='append', help='Path to an ontology file to use for validation')
    parser.add_argument('--endpoint', required=False, help='URL of the SPARQL endpoint to ingest the validation results into')

    args = parser.parse_args()

    validateTurtleWithShacl(directory=args.directory, shapesGraph=args.shapesGraph, ontologyFiles=args.ontologyFile, endpoint=args.endpoint, namedGraph=args.namedGraph)
