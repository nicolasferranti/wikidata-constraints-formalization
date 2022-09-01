from abc import ABC, abstractmethod
import os


class ConstraintType(ABC):  # Abstract class for all constraints
    @abstractmethod
    def toShacl(self):
        pass


class TypeConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """@prefix :        <http://example.org/>
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

    def toShacl(self, property_json):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", self.property
        )
        for json_item in property_json["results"]["bindings"]:
            if (
                json_item.get("constraint_type").get("value")[
                    json_item.get("constraint_type").get("value").rfind("/Q") + 1 :
                ]
            ) == "Q21503250" and json_item.get("pq_qualifiers").get(
                "value"
            ) == "http://www.wikidata.org/prop/qualifier/P2308":
                value_list = (
                    json_item.get("object_val").get("value").split(", ")
                )  # Item of Property Constraint
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
                    self.constraint_shacl = self.constraint_shacl.replace(
                        "$PROPERTY_SHACL$\n",
                        property_shacl,
                    )
                self.constraint_shacl = self.constraint_shacl.replace(
                    "$PROPERTY_SHACL$", ""
                )

        return self.constraint_shacl
