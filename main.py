import requests, json, os, argparse
from enum import Enum
from abc import ABC, abstractmethod

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


class ConstraintType(ABC):  # Abstract class for all constraints
    @abstractmethod
    def toShacl(self):
        pass


class WdToShaclController:
    def __init__(self, pid):
        self.pid = pid
        self.query = self.WdQuery()

    class WdQuery(WdDataExtractor):
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
            response = requests.get(
                url, params={"format": "json", "query": SPARQL_query}
            )
            data = response.json()

            if not os.path.exists(query_results):
                os.mkdir(query_results)

            with open(f"{query_results}/{pid}.json", "w") as outfile:
                json.dump(data, outfile, indent=2)


class WD_Prop:
    # def __init__(self, pid):
    #     self.pid = pid

    #     self.wd_data_extractor(self.pid)

    # def wd_data_extractor(self, pid):
    #     SPARQL_query = f"""
    #     SELECT DISTINCT
    #         ?statement ?constraint_type ?pq_qualifiers
    #         (GROUP_CONCAT(DISTINCT ?val; SEPARATOR=", ") AS ?object_val)
    #     {{
    #         wd:{pid} p:P2302 ?statement .
    #         # [] p:P2302 ?statement . # TIMEOUT
    #         ?statement ps:P2302 ?constraint_type .
    #         ?statement ?pq_qualifiers [] .
    #         [] wikibase:qualifier ?pq_qualifiers .

    #         OPTIONAL {{?statement ?pq_qualifiers ?val}}
    #     }}  GROUP BY ?constraint_type ?pq_qualifiers ?statement
    #     """

    #     url = "https://query.wikidata.org/sparql"
    #     response = requests.get(url, params={"format": "json", "query": SPARQL_query})
    #     data = response.json()

    #     if not os.path.exists(query_results):
    #         os.mkdir(query_results)

    #     with open(f"{query_results}/{pid}.json", "w") as outfile:
    #         json.dump(data, outfile, indent=2)

    #     self.extract_property_constraints(self.pid)

    # def extract_property_constraints(self, pid):
    #     self.property_constraints = []
    #     with open(f"{query_results}/{pid}.json", "r") as property_file:
    #         property_json = json.load(property_file)
    #         property_file.close()
    #         print(f"Property {pid} has the following property constraints:")
    #         for item in property_json["results"]["bindings"]:
    #             constraint_url = item.get("constraint_type").get("value")
    #             constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
    #             for item in EnumPropertyConstraints:
    #                 if (
    #                     constraint == item.name
    #                     and constraint not in self.property_constraints
    #                 ):
    #                     self.property_constraints.append(constraint)
    #                     print(f"◆ {item.value}")
    #     self.shacl_generate(self.pid, property_json, self.property_constraints)

    def shacl_generate(self, pid, property_json, property_constraints):
        for item in property_constraints:
            for enum_item in EnumPropertyConstraints:
                if item == enum_item.name:
                    match item:
                        case "Q21503250":
                            PropertyConstraints.type_constraint(
                                self, pid, property_json, item
                            )
                        case "Q21503247":
                            pass


class PropertyConstraints:
    def type_constraint(object, pid, property_json, constraint):
        results_path = "./type constraint"
        constraint_shacl = """
@prefix :        <http://example.org/>
@prefix wdt:     <http://www.wikidata.org/prop/direct/>
@prefix wd:      <http://www.wikidata.org/entity/>
@prefix sh:      <http://www.w3.org/ns/shacl#>

:$WD_PROPERTY$_TypeConstraintShape 
    a sh:NodeShape ;
    sh:targetSubjectsOf wdt:$WD_PROPERTY$;
    sh:or (
        $PROPERTY_SHACL$
    ) ;
    sh:severity sh:Violation .
"""
        constraint_shacl = constraint_shacl.replace("$WD_PROPERTY$", pid)
        for json_item in property_json["results"]["bindings"]:
            if (
                json_item.get("constraint_type").get("value")[
                    json_item.get("constraint_type").get("value").rfind("/Q") + 1 :
                ]
                == constraint
                and json_item.get("pq_qualifiers").get("value")
                != "http://www.wikidata.org/prop/qualifier/P2309"
            ):
                value_list = json_item.get("object_val").get("value").split(", ")
                for value in value_list:
                    property_shacl = """
        [ sh:property [
                sh:path ([sh:zeroOrOnePath wdt:P31] [sh:zeroOrMorePath wdt:P279]) ;
                sh:minCount 1 ;
                sh:hasValue wd:$PROPERTY$ ;
            ]
        ]
        $PROPERTY_SHACL$
"""
                    property_shacl = property_shacl.replace(
                        "$PROPERTY$", value[value.rfind("/Q") + 1 :]
                    )
                    constraint_shacl = constraint_shacl.replace(
                        "$PROPERTY_SHACL$\n", property_shacl
                    )
                constraint_shacl = constraint_shacl.replace("$PROPERTY_SHACL$", "")

        if not os.path.exists(results_path):
            os.mkdir(results_path)

        with open(f"{results_path}/{pid}.ttl", "w") as outfile:
            outfile.write(constraint_shacl)
            outfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--property",
        type=str,
        help="WD property to generate SHACL property shapes for",
    )
    args = parser.parse_args()
    if args.property:
        value = args.property
    else:
        value = input(
            "For which property would you like to generate a SHACL property shape?\n> "
        )

    wd_prop = WdToShaclController(value)
    wd_prop.query.extractPropertyConstraints(value)
