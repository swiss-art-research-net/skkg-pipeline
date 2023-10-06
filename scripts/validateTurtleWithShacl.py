import argparse
from pyshacl import validate
from os import listdir
from os.path import join, isfile
from rdflib import Graph

import sys

def validateTurtleWithShacl(*, directory, shapesGraph, ontologyFiles=False, endpoint=False):
    inputFiles = [f for f in listdir(directory) if isfile(join(directory, f)) and f.endswith('.ttl')]
    
    # Read RDF files into graph
    print("Reading RDF files into graph...")
    dataGraph = Graph()
    for file in inputFiles:
        dataGraph.parse(join(directory, file), format='turtle')

    # Read SHACL shape graph into graph
    print("Reading SHACL shape graph into graph...")
    shaclGraph = Graph()
    shaclGraph.parse(shapesGraph, format='turtle')

    # Read ontology files into graph
    print("Reading ontology files into graph...")
    ontologyGraph = Graph()
    if ontologyFiles:
        for file in ontologyFiles:
            # Check extension of file
            if file.endswith('.ttl'):
                ontologyGraph.parse(file, format='turtle')
            elif file.endswith('.rdfs'):
                ontologyGraph.parse(file, format='xml')

    # Validate
    print("Validating...")
    r = validate(dataGraph,
                 shacl_graph=shaclGraph,
                 ont_graph=ontologyGraph,
                 inference='rdfs',
                 abort_on_first=False,
                 meta_shacl=False,
                 advanced=True,
                 js=False,
                 debug=False,
                 serialize_report_graph=False,
                 use_iron=True,
                 allow_warnings=False,
                 )
    conforms, results_graph, results_text = r
    
    if conforms:
        print("Validation successful!")
    else:
        print("Validation failed!")

    print(results_text)
    if endpoint:
        print("Ingesting validation results into endpoint...")
        ttlOutput = results_graph.serialize(destination='results.ttl', format='turtle')
        print(ttlOutput)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Validate a directory of Turtle files using a SHACL Shape Graph. Optionally ingest the validation results into a Triplestore.')
    parser.add_argument('--directory', required=True, help='Directory containing the Turtle files to validate')
    parser.add_argument('--shapesGraph', required=True, help='Path to the SHACL Shape Graph to use for validation')
    parser.add_argument('--ontologyFile', required=False, action='append', help='Path to an ontology file to use for validation')
    parser.add_argument('--endpoint', required=False, help='URL of the SPARQL endpoint to ingest the validation results into')

    args = parser.parse_args()

    validateTurtleWithShacl(directory=args.directory, shapesGraph=args.shapesGraph, ontologyFiles=args.ontologyFile, endpoint=args.endpoint)
