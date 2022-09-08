from abc import ABC, abstractmethod
from enum import Enum
import os

class EnumQualifiersID(Enum):
    relation_qualifier = "P2309"
    class_qualifier = "P2308"

class ConstraintType(ABC):  # Abstract class for all constraints
    @abstractmethod
    def toShacl(self):
        pass

    @abstractmethod
    def getRequiredPrefixes(self):
        pass


class TypeConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """
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
                $MANDATORY$
        """

    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )

        relation_path = "[sh:zeroOrOnePath wdt:P31] [sh:zeroOrMorePath wdt:P279]"
        expected_classes = []
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            match qid:
                ## P2309 RELATION
                case EnumQualifiersID.relation_qualifier.value:

                    match qualifier.get("object_val")[0]: ## Testing instance of, subclass of, or instance or subclass of
                        #case "https://www.wikidata.org/wiki/Q21503252": # instance of
                            #relation_path = "[sh:zeroOrOnePath wdt:P31] [sh:zeroOrMorePath wdt:P279]"
                        case "https://www.wikidata.org/wiki/Q21514624": # subclass of
                            relation_path = "[sh:zeroOrMorePath wdt:P279]"
                        #case "https://www.wikidata.org/wiki/Q30208840": # instance or subclass of
                            #relation_path = "[sh:zeroOrOnePath wdt:P31] [sh:zeroOrMorePath wdt:P279]"
                ## P2308 CLASS LIST
                case EnumQualifiersID.class_qualifier.value:
                    expected_classes = qualifier.get("object_val")

        for value in expected_classes:
            property_shacl = """
                [ sh:property [
                        sh:path ($PROPERTY_PATH$) ;
                        sh:minCount 1 ;
                        sh:hasValue wd:$PROPERTY$ ;
                    ]
                ]
                $PROPERTY_SHACL$
            """.replace("$PROPERTY_PATH$", relation_path)
            property_shacl = property_shacl.replace(
                "$PROPERTY$", value[value.rfind("/Q") + 1:]
            )
            self.constraint_shacl = self.constraint_shacl.replace(
                "$PROPERTY_SHACL$\n",
                property_shacl,
            )
        self.constraint_shacl = self.constraint_shacl.replace("$PROPERTY_SHACL$", "")

        ## TODO
        if self.mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl
    def getRequiredPrefixes(self):
        pass