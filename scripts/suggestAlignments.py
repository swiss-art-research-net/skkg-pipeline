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
import os
import datetime

ESCAPE_DICT = {'"':  r'\"'}

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
    crm:P33_used_specific_technique <$technique_uri> ;
    crm:P140_assigned_attribute_to <$base_uri> ;
    crm:P141_assigned gnd:$aligned_id ;
    crm:P177_assigned_property_of_type $same_as skos:$match_type ;
    rdf:value "$score"^^xsd:float .

gnd:$aligned_id a crm:E55_Type ;
    rdfs:label "$aligned_label" .
""")


GENERAL_CLASSIFICATION_STATEMENT = Template("""
classification:$class_id a crm:E13_Attribute_Assignment ;
    crm:P16_used_specific_object $all_uris ;
    crm:P33_used_specific_technique <$technique_uri> ;
    crm:P4_has_time_span <https://data.skkg.ch/classification/$class_id/date> ;
    rdf:value "$minimum_score"^^xsd:float ;
    rdfs:label "Alignment Suggestions" .
    
    $matched_uris_statement

<https://data.skkg.ch/classification/$class_id/date> a crm:E52_Time-Span ;
    crm:P82_at_some_time_within "$current_time"^^xsd:dateTime .
""")

ESCAPE_TRANSLATION_TABLE = str.maketrans({"\"": r"\"",})


MINIMUM_SCORE_NULL = 0
LOBID_API_URL ='https://lobid.org/gnd/reconcile/'
AUTHORITY_RESOURCE = 'AuthorityResource'
MATCHED_INPUT_URIS = []
ALL_INPUT_URIS = []
TECHNIQUE_URI = 'https://github.com/swiss-art-research-net/skkg-pipeline/blob/45-create-python-script-to-suggest-alignments/scripts/suggestAlignments.py'

def query_ttl(input_file, query):
    #parse input file
    g = Graph()
    g.parse(input_file)
    #retrieve needed entities and labels from input file
    res = g.query(NAMESPACES + query)
    return res

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
    matched_gnd_nb = 0
    for result in q_response:
        if float(result['score']) >= min_score:
            matched_gnd_nb = matched_gnd_nb + 1
            #get SHA1 UUID bases on base uri first and then use resulting UUID to get SHA1 UUID based on ID of aligned entity
            base_uri_uuid = uuid.uuid5(uuid.NAMESPACE_URL, q2entities_dict[q_number]['uri'])
            class_id = uuid.uuid5(base_uri_uuid, result['id'])
            ret = ret + ONE_CLASSIFICATION.substitute(class_id=str(class_id),
                                            base_uri=q2entities_dict[q_number]['uri'],
                                            aligned_id=result['id'],
                                            technique_uri = TECHNIQUE_URI,
                                            match_type='exactMatch' if result['match'] else 'closeMatch',
                                            score=result['score'],
                                            aligned_label=result['name'].translate(str.maketrans(ESCAPE_DICT)),
                                            same_as = 'crmdig:L54_is_same-as,' if result['match'] else '')
    if matched_gnd_nb > 0:
        MATCHED_INPUT_URIS.append(q2entities_dict[q_number]['uri'])#append input URI
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
    
    #retrieve needed entities and labels from input file
    base_query = """
    SELECT * WHERE {{
    ?entity a <{0}> .
    ?entity rdfs:label ?label .
    }}
    """.format(base_type)
    base_res = query_ttl(input_file, base_query)
    
    if list(base_res) == []:
        print('There are no entitites of type {0} in input file.'.format(base_type))
        return
    #get entities that are already classified
    if os.path.isfile(output_file):
        
        existing_classifications_query_1 = """
        SELECT DISTINCT ?base_uri WHERE {
            ?classification a crm:E13_Attribute_Assignment ;
            crm:P140_assigned_attribute_to ?base_uri ;
            crm:P141_assigned ?gnd ;
            crm:P177_assigned_property_of_type ?sameness ;
            rdf:value ?score .

            ?gnd a crm:E55_Type ;
            rdfs:label ?label .
        }
        """
        existing_classifications_query_2 = """
        SELECT DISTINCT ?base_uri WHERE {
            ?classification a crm:E13_Attribute_Assignment ;
            crm:P16_used_specific_object ?base_uri .
        }
        """
        existing_classifications_res_1 = query_ttl(output_file, existing_classifications_query_1)
        existing_classifications_res_2 = query_ttl(output_file, existing_classifications_query_2)
        existing_entities_list = []
        for row in existing_classifications_res_1:
            existing_entities_list.append(str(row.base_uri))
        for row in existing_classifications_res_2:
            existing_entities_list.append(str(row.base_uri))

        base_res_dict = {}
        i = 1
        for row in base_res:
            if not str(row.entity) in existing_entities_list:
                ALL_INPUT_URIS.append(str(row.entity))
                base_res_dict.update({'q'+str(i): {'uri': str(row.entity), 'label': str(row.label)}})
                i = i + 1
    else:
        base_res_dict = {}
        i = 1
        for row in base_res:
            ALL_INPUT_URIS.append(str(row.entity))
            base_res_dict.update({'q'+str(i): {'uri': str(row.entity), 'label': str(row.label)}})
            i = i + 1

    if base_res_dict == {}:
        print('All entities are present in output file! To query for non classified input entities, please remove the general classification statement. To query for all input entities, please specify another output file.')
        return
    
    #prepare reconciliation queries    
    queries = {key : {"query": values['label'].translate(ESCAPE_TRANSLATION_TABLE), "limit": limit, "type": reconciliation_type } for (key, values) in base_res_dict.items()}
    
    #make requests and put in dictionary
    response_dict = {}
    print('Reconciliation queries in progress...')
    current_date_time = datetime.datetime.now()
    pbar = tqdm(total = len(queries))
    for chunk in chunks(queries):
        response = requests.get(api_uri, params={'queries': json.dumps(chunk) })
        response_dict.update(response.json())
        pbar.update(len(chunk))
    pbar.close()
    
    #format response into ttl
    ttl = parse_all_responses(reconciliation_whole_response = response_dict, q2entities_dict = base_res_dict, min_score=minimum_score)
    
    #save ttl
    if os.path.isfile(output_file):
        with open(output_file, 'a') as f:
            f.write(ttl)        
    else:
        with open(output_file, 'w') as f:
            f.write(namespaces4ttl + ttl)
    
    with open(output_file, 'a') as f:
        general_classification_base_uri_uuid = uuid.uuid5(uuid.NAMESPACE_URL, TECHNIQUE_URI)
        general_classification_uuid = uuid.uuid5(general_classification_base_uri_uuid, current_date_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if len(MATCHED_INPUT_URIS) > 0:
            matched_uris_statement = 'classification:{0} crm:P140_assigned_attribute_to {1} .'.format(general_classification_uuid, ', '.join(['<' + internal_entity + '>' for internal_entity in MATCHED_INPUT_URIS]))
        else:
            matched_uris_statement = ''
        all_uris = ', '.join(['<' + internal_entity + '>' for internal_entity in ALL_INPUT_URIS])
        concluding_classification = GENERAL_CLASSIFICATION_STATEMENT.substitute(
                                                            all_uris = all_uris,
                                                            class_id = general_classification_uuid,
                                                            current_time = current_date_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                            technique_uri = TECHNIQUE_URI,
                                                            minimum_score = minimum_score,
                                                            matched_uris_statement = matched_uris_statement)
        f.write(concluding_classification)

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