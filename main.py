import requests, json, os
from enum import Enum

### Global Variables
query_results = "./query results"

constraint_shacl = {
    "Q21503250": """
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
  """,
    "Q21503247": """
@prefix :        <http://example.org/>
@prefix wdt:     <http://www.wikidata.org/prop/direct/>
@prefix wd:      <http://www.wikidata.org/entity/>
@prefix sh:      <http://www.w3.org/ns/shacl#>

:$WD_PROPERTY$_ItemRequiresStatementShape 
	a sh:NodeShape ;
	sh:targetSubjectsOf wdt:$WD_PROPERTY$ ;
	sh:property [
    	sh:path wdt:$PROP_CONSTRAINT$ ;
        sh:minCount 1;
        sh:in (wd:$ITEM_OF_PROP_CONSTRAINT$) ;
  	] .
  """,
}


class PropertyConstraints(Enum):
    Q52004125 = "allowed-entity-types constraint"
    Q21510851 = "allowed qualifiers constraint"
    Q21503247 = "item-requires-statement constraint"
    Q53869507 = "property scope constraint"
    Q21503250 = "type constraint"


def wdQuery(wdProperty):
    SPARQL_query = f"""
    SELECT DISTINCT
        ?statement ?constraint_type ?pq_qualifiers
        (GROUP_CONCAT(DISTINCT ?val; SEPARATOR=", ") AS ?object_val)
    {{
        wd:{wdProperty} p:P2302 ?statement .
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

    with open(f"{query_results}/{wdProperty}.json", "w") as outfile:
        json.dump(data, outfile, indent=2)


def wdPropertyConstraints(wdProperty):
    property_constraints = []
    with open(f"{query_results}/{wdProperty}.json", "r") as property_file:
        property_json = json.load(property_file)
        property_file.close()
        print(f"Property {wdProperty} has the following property constraints:")
        for item in property_json["results"]["bindings"]:
            constraint_url = item.get("constraint_type").get("value")
            constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
            for item in PropertyConstraints:
                if constraint == item.name and constraint not in property_constraints:
                    property_constraints.append(constraint)
                    print(f"◆ {item.value}")
    shacl_generate(wdProperty, property_json, property_constraints)


def shacl_generate(wdProperty, property_json, property_constraints):
    for item in property_constraints:
        if item in constraint_shacl:
            match item:
                case "Q21503250":
                    results_path = "./type constraint"
                    constraint_shape = constraint_shacl[item]
                    constraint_shape = constraint_shape.replace(
                        "$WD_PROPERTY$", wdProperty
                    )
                    for json_item in property_json["results"]["bindings"]:
                        if (
                            json_item.get("constraint_type").get("value")[
                                json_item.get("constraint_type")
                                .get("value")
                                .rfind("/Q")
                                + 1 :
                            ]
                            == item
                            and json_item.get("pq_qualifiers").get("value")
                            != "http://www.wikidata.org/prop/qualifier/P2309"
                        ):
                            value_list = (
                                json_item.get("object_val").get("value").split(", ")
                            )
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
                                constraint_shape = constraint_shape.replace(
                                    "$PROPERTY_SHACL$", property_shacl
                                )
                            constraint_shape = constraint_shape.replace(
                                "$PROPERTY_SHACL$", ""
                            )

                    if not os.path.exists(results_path):
                        os.mkdir(results_path)

                    with open(f"{results_path}/{wdProperty}.ttl", "w") as outfile:
                        outfile.write(constraint_shape)
                        outfile.close()
                case "Q21503247":
                    pass
                    # for json_item in property_json["results"]["bindings"]:
                    #     if (
                    #         json_item.get("constraint_type").get("value")[
                    #             json_item.get("constraint_type")
                    #             .get("value")
                    #             .rfind("/Q")
                    #             + 1 :
                    #         ]
                    #         == item
                    #         and json_item.get("pq_qualifiers").get("value")
                    #         == "http://www.wikidata.org/prop/qualifier/P2305"
                    #     ):
                    #         value_list = (
                    #             json_item.get("object_val").get("value").split(", ")
                    #         )
                    #         print(value_list)
                    # # results_path = "./item-requires-statement constraint"

                    # # if not os.path.exists(results_path):
                    # #     os.mkdir(results_path)

                    # # with open(f"{results_path}/{wdProperty}.ttl", "w") as outfile:
                    # #     outfile.write(constraint_shape)
                    # #     outfile.close()


# wdProperty = input(
#     "For which property would you like to generate a SHACL property shape?\n> "
# )
wdProperty = "P1469"
wdQuery(wdProperty)
wdPropertyConstraints(wdProperty)
