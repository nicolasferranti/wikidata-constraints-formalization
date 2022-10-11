from abc import ABC, abstractmethod
from utils import *
import os

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
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            match qid:
                ## P2309 RELATION
                case EnumQualifiersID.relation_qualifier.value:

                    match qualifier.get("object_val")[0]:  ## Testing instance of, subclass of, or instance or subclass of
                        # case "https://www.wikidata.org/wiki/Q21503252": # instance of
                        # relation_path = "[sh:zeroOrOnePath wdt:P31] [sh:zeroOrMorePath wdt:P279]"
                        case "https://www.wikidata.org/wiki/Q21514624":  # subclass of
                            relation_path = "[sh:zeroOrMorePath wdt:P279]"
                        # case "https://www.wikidata.org/wiki/Q30208840": # instance or subclass of
                        # relation_path = "[sh:zeroOrOnePath wdt:P31] [sh:zeroOrMorePath wdt:P279]"
                ## P2308 CLASS LIST
                case EnumQualifiersID.class_qualifier.value:
                    expected_classes = qualifier.get("object_val")
                ## P2316 CONSTRAINT STATUS
                case EnumQualifiersID.constraint_status_qualifier.value:
                    if qualifier.get("object_val")[0] == "https://www.wikidata.org/wiki/Q21502408":
                        mandatory = True

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

        if mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl

    def getRequiredPrefixes(self):
        return [EnumPrefixes.example_prefix, EnumPrefixes.wdt_prefix, EnumPrefixes.wd_prefix, EnumPrefixes.sh_prefix]


class FormatConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """
            :$WD_PROPERTY$_FormatConstraintShape 
                a sh:NodeShape ;
                sh:targetSubjectsOf wdt:$WD_PROPERTY$;
                sh:property [
                    sh:path wdt:$WD_PROPERTY$ ;
                    sh:pattern  "$REGULAR_EXPRESSION$";
                    sh:description "the value for this property has to correspond to a given pattern"; 
                ] ;
                $MANDATORY$
        """

    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )

        regular_expression = ""
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            match qid:
                ## P1793 FORMAT AS A REGULAR EXPRESSION
                case EnumQualifiersID.format_as_a_regular_expression_qualifier.value:
                    regular_expression = qualifier.get("object_val")[0]
                ## P2316 CONSTRAINT STATUS
                case EnumQualifiersID.constraint_status_qualifier.value:
                    if qualifier.get("object_val")[0] == "https://www.wikidata.org/wiki/Q21502408":
                        mandatory = True

        if regular_expression == "":
            raise Exception("Format constraint has no regular expression. PID:" + str(pid))

        self.constraint_shacl = self.constraint_shacl.replace(
            "$REGULAR_EXPRESSION$", regular_expression
        )
        if mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl

    def getRequiredPrefixes(self):
        return [EnumPrefixes.example_prefix, EnumPrefixes.wdt_prefix, EnumPrefixes.sh_prefix]