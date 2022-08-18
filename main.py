import requests, json, os


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

    resultsPath = "./results"
    if not os.path.exists(resultsPath):
        os.mkdir(resultsPath)

    with open(f"{resultsPath}/{wdProperty}.json", "w") as outfile:
        json.dump(data, outfile)

### Global Variables
resultsPath = "./results"

# wdProperty = input('For which property would you like to generate a SHACL property shape?')
wdProperty = "P1559"
wdQuery(wdProperty)
