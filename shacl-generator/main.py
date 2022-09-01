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
    Q21503247 = "item-requires-statement constraint"
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
        dump_json(query_results, pid, data)

        property_constraints = []
        property_json = read_json(query_results, pid)

        print(
            f"Property {pid} has the following property constraints:"
        ) if args.verbose else None
        for item in property_json["results"]["bindings"]:
            constraint_url = item.get("constraint_type").get("value")
            constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
            for item in EnumPropertyConstraints:
                if constraint == item.name and constraint not in property_constraints:
                    property_constraints.append(constraint)
                    print(f"◆ {item.value}") if args.verbose else None

        for item in property_constraints:
            match item:
                case "Q21503250":
                    # import importlib
                    # module = importlib.import_module(module_name)
                    # class_ = getattr(module, class_name)
                    # instance = class_()

                    print(
                        "Generating SHACL property shape for the Type Constraint"
                    ) if args.verbose else None
                    type_constraint = TypeConstraint()
                    type_constraint.property = pid
                    string_shacl = type_constraint.toShacl(property_json)
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
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    args = parser.parse_args()
    if args.property:
        string_pid = args.property
    else:
        string_pid = input(
            "For which property would you like to generate a SHACL property shape?\n> "
        )

    wd_prop = WdToShaclController(string_pid)
