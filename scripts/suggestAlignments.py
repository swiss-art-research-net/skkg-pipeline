"""
Script to suggest alignments to entities that have a given type using reconciliation service

Usage:
    python suggestAlignments.py --input_file <input_file> --base_type <base_type> --limit <limit> --output_file <output_file> [--api_uri <api_uri> --minimum_score <minimum_score>  --reconciliation_type <reconciliation_type>]

Arguments:
    --input_file: TTL input file
    --base_type: type for entities to retrieve from input TTL
    --reconciliation_type: type for entities to retrieve from reconciliation service
    --limit: Limit for number of results that are returned by reconciliation service
    --output_file: TTL output file
    --api_uri: URL of reconciliation API. Defaults to https://lobid.org/gnd/reconcile/. 
    --minimum_score: Minimum score to consider for results. Defaults to 0.
    
"""

from rdflib import Graph
import argparse
import pandas as pd
import requests
from itertools import islice
from string import Template
import uuid
from tqdm import tqdm
import time

NAMESPACES = """
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

NAMESPACES4TTL_HARDCODED = """
@prefix classification: <https://data.skkg.ch/classification/> .
@prefix crm:   <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix crmdig: <http://www.ics.forth.gr/isl/CRMdig/> .
@prefix gnd: <http://d-nb.info/gnd/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

ONE_CLASSIFICATION = Template("""
classification:$class_id a crm:E13_Attribute_Assignment ;
crm:P140_assigned_attribute_to <$base_uri> ;
crm:P141_assigned gnd:$aligned_id ;
crm:P177_assigned_property_of_type $same_as skos:$match_type ;
rdf:value "$score"^^xsd:float .

gnd:$aligned_id a crm:E55_Type ;
    rdfs:label "$aligned_label" .
""")

MINIMUM_SCORE_NULL = 0
LOBID_API_URL ='https://lobid.org/gnd/reconcile/'
AUTHORITY_RESOURCE = 'AuthorityResource'

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

def parse_reconciliation_response(q_response, q_number, q2entities_dict, min_score=0):
    """
    function to parse the one element in the response from the reconciliation endpoint and format it into a ttl classification
    Args:
    q_response - one element from the reconciliation query response
    q_number - query number in format "qn" where n is the number of the query
    q2entities_dict - a dictionary such that keys are the query numbers and values are dictionaries containing 'uri' which
    correspond to uris of elements of interest and 'label' which contain the labels used for reconciliation
    min_score - minimum score to consider for results
    """
    ret = ''
    for result in q_response:
        if float(result['score']) >= min_score:
            ret = ret + ONE_CLASSIFICATION.substitute(class_id=str(uuid.uuid4()),
                                            base_uri=q2entities_dict[q_number]['uri'],
                                            aligned_id=result['id'],
                                            match_type='exactMatch' if result['match'] else 'closeMatch',
                                            score=result['score'],
                                            aligned_label=result['name'],
                                            same_as = 'crmdig:L54_is_same-as,' if result['match'] else '')
    return ret

def parse_all_responses(reconciliation_whole_response, q2entities_dict, min_score=0):
    """
    function to parse the whole reconciliation query response into a ttl string
    Args:
    reconciliation_whole_response - the whole response from the reconciliation endpoint
    q2entities_dict - a dictionary such that keys are the query numbers and values are dictionaries containing 'uri' which
    correspond to uris of elements of interest and 'label' which contain the labels used for reconciliation
    min_score - minimum score to consider for results
    Returns:
    string with ttl formatted classifications
    """
    return ''.join([  parse_reconciliation_response(q_response = values['result'], q_number = key, q2entities_dict = q2entities_dict, min_score=min_score) for (key, values) in reconciliation_whole_response.items() ])

def main(input_file, base_type, reconciliation_type, limit, output_file, api_uri, minimum_score=0, namespaces4ttl=NAMESPACES4TTL_HARDCODED):
    #parse input file
    g = Graph()
    g.parse(input_file)
    
    #retrieve needed entities and labels from input file
    base_query = """
    SELECT * WHERE {{
    ?entity a <{0}> .
    ?entity rdfs:label ?label .
    }}
    """.format(base_type)
    base_res = g.query(NAMESPACES + base_query)
    base_res_dict = {}
    i = 1
    for row in base_res:
        base_res_dict.update({'q'+str(i): {'uri': str(row.entity), 'label': str(row.label)}})
        i = i + 1
    
    #prepare reconciliation queries
    queries = {key : {"query": values['label'], "limit": limit, "type": reconciliation_type } for (key, values) in base_res_dict.items()}
    
    #make requests and put in dictionary
    response_dict = {}
    print('Reconciliation queries in progress...')
    pbar = tqdm(total = len(queries))
    for chunk in chunks(queries):
        response = requests.get(api_uri, params={'queries': str(chunk).replace('\'', '"') })
        response_dict.update(response.json())
        pbar.update(len(chunk))
    pbar.close()
    
    #format response into ttl
    ttl = parse_all_responses(reconciliation_whole_response = response_dict, q2entities_dict = base_res_dict, min_score=minimum_score)
    
    #save ttl
    with open(output_file, 'w') as f:
        f.write(namespaces4ttl + ttl)
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    parser = argparse.ArgumentParser(description = 'Produce alignments to SKKG entities using reconciliation service')
    parser.add_argument('--input_file', required= True, help='TTL input file with SKKG entities')
    parser.add_argument('--base_type', required= True, help='Base type of entities to retrieve')
    parser.add_argument('--limit', required= True, help='Limit of results when querying reconciliation service')
    parser.add_argument('--output_file', required= True, help='TTL output file')
    parser.add_argument('--reconciliation_type', required= False, help='GND type of entities to retrieve')
    parser.add_argument('--api_uri', required= False, help='URL of reconciliation API. Defaults to https://lobid.org/gnd/reconcile/.')
    parser.add_argument('--minimum_score', required= False, help='Minimum score to consider for results. Defaults to 0.')
    
    args = parser.parse_args()
    
    if args.reconciliation_type is None:
        reconciliation_type = AUTHORITY_RESOURCE
    else:
        reconciliation_type = args.reconciliation_type
        
    if args.api_uri is None:
        api_uri = LOBID_API_URL
    else:
        api_uri = args.api_uri

    if args.minimum_score is None:
        minimum_score = MINIMUM_SCORE_NULL
    else:
        minimum_score = float(args.minimum_score)
        
    main(input_file = args.input_file, base_type= args.base_type, reconciliation_type = reconciliation_type, limit = args.limit, output_file = args.output_file, api_uri = api_uri, minimum_score=minimum_score, namespaces4ttl=NAMESPACES4TTL_HARDCODED)