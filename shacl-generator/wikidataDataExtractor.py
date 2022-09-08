import requests, json, os, argparse
from enum import Enum
from abc import ABC, abstractmethod
from constraints import *

query_results = "./query results"


def read_json(dir, fname):
    with open(f"{dir}/{fname}.json", "r") as property_file:
        return json.load(property_file)


# Abstract class for querying wikidata
class WdDataExtractor(ABC):
    @abstractmethod
    def extractPropertyConstraints(self, pid):
        pass


# Specification of WdDataExtractor, ONLINE extractor
class WikidataOnlineEndpointExtractor(WdDataExtractor):

    def __init__(self):

        self.url = "https://query.wikidata.org/sparql"
        pass

    def extractPropertyConstraints(self, pid):
        SPARQL_query = f"""
                    SELECT DISTINCT
                        ?statement ?constraint_type ?pq_qualifiers
                        (GROUP_CONCAT(DISTINCT ?val; SEPARATOR=", ") AS ?object_val)
                    {{
                        wd:{pid} p:P2302 ?statement .
                        # [] p:P2302 ?statement . # TIMEOUT
                        ?statement ps:P2302 ?constraint_type .
                        ?statement ?pq_qualifiers [] .
                        [] wikibase:qualifier ?pq_qualifiers .
                        OPTIONAL {{?statement ?pq_qualifiers ?val}}
                    }}  GROUP BY ?constraint_type ?pq_qualifiers ?statement
                    ORDER BY ASC(?statement)
                """

        response = requests.get(self.url, params={"format": "json", "query": SPARQL_query})

        return response.json()