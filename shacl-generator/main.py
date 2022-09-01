import requests, json, os, argparse
from enum import Enum
from abc import ABC, abstractmethod
from constraints import *

query_results = "./query results"


class EnumPropertyConstraints(Enum):
    Q52004125 = "allowed entity types constraint"
    Q21510851 = "allowed qualifiers constraint"
    Q21503247 = "item-requires-statement constraint"
    Q53869507 = "property scope constraint"
    Q21503250 = "type constraint"


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

        if not os.path.exists(query_results):
            os.mkdir(query_results)

        with open(f"{query_results}/{pid}.json", "w") as outfile:
            json.dump(data, outfile, indent=2)

        property_constraints = []
        with open(f"{query_results}/{pid}.json", "r") as property_file:
            property_json = json.load(property_file)

        if args.verbose:
            print(f"Property {pid} has the following property constraints:")
            for item in property_json["results"]["bindings"]:
                constraint_url = item.get("constraint_type").get("value")
                constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
                for item in EnumPropertyConstraints:
                    if (
                        constraint == item.name
                        and constraint not in property_constraints
                    ):
                        property_constraints.append(constraint)
                        print(f"◆ {item.value}")
        else:
            for item in property_json["results"]["bindings"]:
                constraint_url = item.get("constraint_type").get("value")
                constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
                for enum_item in EnumPropertyConstraints:
                    if (
                        constraint == enum_item.name
                        and constraint not in property_constraints
                    ):
                        property_constraints.append(constraint)

        for item in property_constraints:
            for enum_item in EnumPropertyConstraints:
                if item == enum_item.name:
                    match item:
                        case "Q21503250":
                            print(
                                "Generating SHACL property shape for the Type Constraint"
                            ) if args.verbose else None
                            type_constraint = TypeConstraint()
                            type_constraint.property = pid
                            type_constraint.toShacl(property_json)
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
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    args = parser.parse_args()
    if args.property:
        string_pid = args.property
    else:
        string_pid = input(
            "For which property would you like to generate a SHACL property shape?\n> "
        )

    wd_prop = WdToShaclController(string_pid)
