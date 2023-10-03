"""
Script to suggest alignments to SKKG entities using reconciliation service

Usage:
    python suggestAlignments.py --input_file <input_file> --type <type> --limit <limit> --output_file <output_file> [--api_uri <api_uri> --minimum_score <minimum_score> --aligned_prefix <aligned_prefix> --ttl_namespaces <ttl_namespaces>]

Arguments:
    --input_file: TTL input file
    --type: SKKG type for entities to retrieve
    --limit: Limit for number of results that are returned by reconciliation service
    --output_file: TTL output file
    --api_uri: URL of reconciliation API. Defaults to https://lobid.org/gnd/reconcile/. 
    --minimum_score: Minimum score to consider for results. Defaults to 0.
    --aligned_prefix : Prefix abbreviation to use. Defaults to "gnd".
    --ttl_namespaces : Text file containing namespaces for TTL files. Defaults to the most common ones (crm, crmdig, gnd, rdf, rdfs, skos, xsd).
    
"""

from rdflib import Graph
import argparse
import pandas as pd
import requests
from itertools import islice
from string import Template
import uuid

namespaces = """
PREFIX loc: <http://id.loc.gov/vocabulary/relators/> 
PREFIX skkg:  <https://ontology.skkg.ch/> 
PREFIX mods:  <http://www.loc.gov/mods/v3> 
PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#> 
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#> 
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX crmdig: <http://www.ics.forth.gr/isl/CRMdig/> 
PREFIX wd:    <http://www.wikidata.org/entity/> 
PREFIX rso:   <http://www.researchspace.org/ontology/>
PREFIX aat:   <http://vocab.getty.edu/aat/>
PREFIX oai:   <http://www.openarchives.org/OAI/2.0/>
PREFIX xml:   <http://www.w3.org/XML/1998/namespace>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX sikart: <https://recherche.sik-isea.ch/>
PREFIX gnd:   <https://d-nb.info/gnd/>
PREFIX crm:   <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX mets:  <http://www.loc.gov/METS/>
PREFIX resource: <https://data.skkg.ch/>
PREFIX viaf:  <https://viaf.org/viaf/>
PREFIX ulan:  <http://vocab.getty.edu/page/ulan/>
PREFIX la:    <https://linked.art/ns/terms/>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wikidata: <https://www.wikidata.org/wiki/>
PREFIX dc:    <http://purl.org/dc/elements/1.1/>
PREFIX frbroo: <http://iflastandards.info/ns/fr/frbr/frbroo/>
"""

namespaces4ttl_hardcoded = """
@prefix classification: <https://data.skkg.ch/classification/> .
@prefix crm:   <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix crmdig: <http://www.ics.forth.gr/isl/CRMdig/> .
@prefix gnd: <http://d-nb.info/gnd/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

one_classification = Template("""
classification:$class_id a crm:E13_Attribute_Assignment ;
crm:P140_assigned_attribute_to $skkg_uri ;
crm:P141_assigned $aligned_prefix:$aligned_id ;
crm:P177_assigned_property_of_type crmdig:L54_is_same-as, skos:$match_type ;
rdf:value "$score"^^xsd:float .

$aligned_prefix:$aligned_id a crm:E55_Type ;
    rdfs:label "$aligned_label" .
""")

def chunks(data, SIZE=10):
    """
    function to chunk a dictionary into multiple parts of a given size
    Args:
    data - dictionary
    SIZE - size of each chunk
    Returns:
    Iterator on the chunked dictionary
    """
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

def parse_reconciliation_response(q_response, q_number, skkg_dict, aligned_prefix='gnd', min_score=0):
    """
    function to parse the one element in the response from the reconciliation endpoint and format it into a ttl classification
    Args:
    q_response - one element from the reconciliation query response
    q_number - query number in format "qn" where n is the number of the query
    skkg_dict - a dictionary such that keys are the query numbers and values are dictionaries containing 'uri' which
    correspond to SKKG uris of elements of interest and 'label' which contain the labels used for reconciliation
    min_score - minimum score to consider for results
    """
    ret = ''
    for result in q_response:
        if float(result['score']) >= min_score:
            ret = ret + one_classification.substitute(class_id=str(uuid.uuid4()),
                                            skkg_uri=skkg_dict[q_number]['uri'],
                                            aligned_id=result['id'],
                                            match_type='exactMatch' if result['match'] else 'closeMatch',
                                            score=result['score'],
                                            aligned_label=result['name'],
                                            aligned_prefix=aligned_prefix)
    return ret

def parse_all_responses(reconciliation_whole_response, skkg_dict, aligned_prefix='gnd', min_score=0):
    """
    function to parse the whole reconciliation query response into a ttl string
    Args:
    reconciliation_whole_response - the whole response from the reconciliation endpoint
    skkg_dict - a dictionary such that keys are the query numbers and values are dictionaries containing 'uri' which
    min_score - minimum score to consider for results
    Returns:
    string with ttl formatted classifications
    """
    return ''.join([  parse_reconciliation_response(values['result'], key, skkg_dict, aligned_prefix=aligned_prefix, min_score=min_score) for (key, values) in reconciliation_whole_response.items() ])


def main(input_file, type_, limit, output_file, api_uri, aligned_prefix='gnd', minimum_score=0, namespaces4ttl=namespaces4ttl_hardcoded):
    #parse input file
    g = Graph()
    g.parse(input_file)
    
    #retrieve needed entities and labels from input file
    skkg_query = """
    SELECT * WHERE {
    ?entity a skkg:Type .
    ?entity rdfs:label ?label .
    }
    """
    skkg_res = g.query(namespaces + skkg_query)
    skkg_res_dict = {}
    i = 1
    for row in skkg_res:
        skkg_res_dict.update({'q'+str(i): {'uri': str(row.entity), 'label': str(row.label)}})
        i = i + 1
    
    #prepare reconciliation queries
    queries = {key : {"query": values['label'], "limit": limit, "type": type_ } for (key, values) in skkg_res_dict.items()}
    
    #make requests and put in dictionary
    response_dict = {}
    for chunk in chunks(queries):
        response = requests.get(api_uri, params={'queries': str(chunk).replace('\'', '"') })
        response_dict.update(response.json())
    
    #format response into ttl
    ttl = parse_all_responses(response_dict, skkg_res_dict, aligned_prefix=aligned_prefix, min_score=minimum_score)
    
    #save ttl
    with open(output_file, 'w') as f:
        f.write(namespaces4ttl + ttl)
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Produce alignments to SKKG entities using reconciliation service')
    parser.add_argument('--input_file', required= True, help='TTL input file with SKKG entities')
    parser.add_argument('--type', required= True, help='SKKG type of entities to reteive')
    parser.add_argument('--limit', required= True, help='Limit of results when querying reconciliation service')
    parser.add_argument('--output_file', required= True, help='TTL output file')
    parser.add_argument('--api_uri', required= False, help='URL of reconciliation API. Defaults to https://lobid.org/gnd/reconcile/.')
    parser.add_argument('--minimum_score', required= False, help='Minimum score to consider for results. Defaults to 0.')
    parser.add_argument('--aligned_prefix', required= False, help='Prefix abbreviation to use. Defaults to "gnd".')
    parser.add_argument('--ttl_namespaces', required= False, help='Text file containing namespaces for TTL files. Defaults to the most common ones (crm, crmdig, gnd, rdf, rdfs, skos, xsd)')
    
    args = parser.parse_args()
    
    if args.ttl_namespaces is None:
        namespaces4ttl = namespaces4ttl_hardcoded
    else:
        with open(args.ttl_namespaces, 'r') as f:
            namespaces4ttl = f.read()
    
    if args.aligned_prefix is None:
        aligned_prefix = 'gnd'
    else:
        aligned_prefix = args.aligned_prefix
        
    if args.api_uri is None:
        api_uri = 'https://lobid.org/gnd/reconcile/'
    else:
        api_uri = args.api_uri

    if args.minimum_score is None:
        minimum_score = 0
    else:
        minimum_score = float(args.minimum_score)

    main(args.input_file, args.type, args.limit, args.output_file, api_uri, aligned_prefix=aligned_prefix, minimum_score=minimum_score, namespaces4ttl=namespaces4ttl)