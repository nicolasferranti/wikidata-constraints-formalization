import requests, json, os, argparse
from enum import Enum
from abc import ABC, abstractmethod
from constraints import *

query_results = "./query results"


def read_json(dir, fname):
    with open(f"{dir}/{fname}.json", "r") as property_file:
        return json.load(property_file)


def dump_json(dir, fname, data):
    if not os.path.exists(dir):
        os.mkdir(dir)

    with open(f"{dir}/{fname}.json", "w") as outfile:
        json.dump(data, outfile, indent=2)


def write_file(dir, fname, data):
    if not os.path.exists(dir):
        os.mkdir(dir)

    with open(f"{dir}/{fname}.ttl", "w") as outfile:
        outfile.write(data)


class EnumPropertyConstraints(Enum):
    ItemRequiresStatementConstraint = "Q21503247"
    TypeConstraint = "Q21503250"


class WdDataExtractor(ABC):  # Abstract class for querying wikidata
    @abstractmethod
    def extractPropertyConstraints(self, pid):
        pass


class WdToShaclController(WdDataExtractor):
    def __init__(self, pid):
        self.pid = pid

        self.extractPropertyConstraints(self.pid)

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
"""

        url = "https://query.wikidata.org/sparql"
        response = requests.get(url, params={"format": "json", "query": SPARQL_query})
        data = response.json()
        dump_json(query_results, pid, data)

        property_constraints = {}
        property_json = read_json(query_results, pid)

        for json_item in property_json["results"]["bindings"]:
            constraint_url = json_item.get("constraint_type").get("value")
            constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
            for enum_item in EnumPropertyConstraints:
                if constraint == enum_item.value:
                    match constraint:
                        case "Q21503250":
                            # Item of property constraint
                            if (
                                json_item.get("constraint_type").get("value")[
                                    json_item.get("constraint_type")
                                    .get("value")
                                    .rfind("/Q")
                                    + 1 :
                                ]
                            ) == "Q21503250" and json_item.get("pq_qualifiers").get(
                                "value"
                            ) == "http://www.wikidata.org/prop/qualifier/P2308":
                                value_list = (
                                    json_item.get("object_val").get("value").split(", ")
                                )
                                property_constraints["Q21503250"] = value_list
                            # Check mandatory constraint
                            if (
                                json_item.get("constraint_type").get("value")[
                                    json_item.get("constraint_type")
                                    .get("value")
                                    .rfind("/Q")
                                    + 1 :
                                ]
                            ) == "Q21503250" and json_item.get("pq_qualifiers").get(
                                "value"
                            ) == "http://www.wikidata.org/prop/qualifier/P2316":
                                if (
                                    json_item.get("object_val").get("value")
                                    == "http://www.wikidata.org/entity/Q21502408"
                                ):
                                    mandatory = 1
                            else:
                                mandatory = 0

        for item in property_constraints:
            match item:
                case "Q21503250":
                    type_constraint = TypeConstraint()
                    type_constraint.property = pid
                    type_constraint.value_list = property_constraints["Q21503250"]
                    type_constraint.mandatory = mandatory
                    string_shacl = type_constraint.toShacl()
                    write_file("./type constraint", pid, string_shacl)
                case "Q21503247":
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--property",
        type=str,
        help="WD property to generate SHACL property shapes for",
    )
    # parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    args = parser.parse_args()
    if args.property:
        string_pid = args.property
    else:
        string_pid = input(
            "For which property would you like to generate a SHACL property shape?\n> "
        )

    wd_prop = WdToShaclController(string_pid)
