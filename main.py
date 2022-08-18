import requests, json, os
from enum import Enum


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

    if not os.path.exists(resultsPath):
        os.mkdir(resultsPath)

    with open(f"{resultsPath}/{wdProperty}.json", "w") as outfile:
        json.dump(data, outfile, indent=2)


def wdPropertyConstraints(wdProperty):
    property_constraints = []
    with open(f"{resultsPath}/{wdProperty}.json", "r") as property_file:
        property_json = json.load(property_file)
        print(f"Property {wdProperty} has the following property constraints:")
        for item in property_json["results"]["bindings"]:
            constraint_url = item.get("constraint_type").get("value")
            constraint = constraint_url[constraint_url.rfind("/Q") + 1 :]
            for item in PropertyConstraints:
                if constraint == item.name and constraint not in property_constraints:
                    property_constraints.append(constraint)
                    print(f"◆ {item.value}")


### Global Variables
resultsPath = "./results"

# wdProperty = input(
#     "For which property would you like to generate a SHACL property shape?\n> "
# )
wdProperty = "P1559"
wdQuery(wdProperty)
wdPropertyConstraints(wdProperty)
