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
    $MANDATORY$"""

    def toShacl(self):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", self.property
        )
        for value in self.value_list:
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
        self.constraint_shacl = self.constraint_shacl.replace("$PROPERTY_SHACL$", "")
        if self.mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl
