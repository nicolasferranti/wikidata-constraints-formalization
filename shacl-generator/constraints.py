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

class SingleValueConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """
:$WD_PROPERTY$_SingleValueConstraintShape 
    a sh:NodeShape ;
    sh:targetSubjectsOf wdt:$WD_PROPERTY$;
    sh:property [
		sh:path wdt:$WD_PROPERTY$ ;
	    sh:maxCount 1 ;
	    sh:description "Specifies that a property generally only has a single value."; 
    ] ;
    $MANDATORY$
"""

    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]  # without P
            match qid:
                ## P2316 CONSTRAINT STATUS
                case EnumQualifiersID.constraint_status_qualifier.value:
                    constraint_status_link = qualifier.get("object_val")[0]  # !!??
                    if constraint_status_link == "http://www.wikidata.org/entity/Q21502408":
                        mandatory = True

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

class ItemRequiresStatementConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """
:$WD_PROPERTY$_ItemRequiresStatementShape
    a sh:NodeShape ;
    sh:targetSubjectsOf wdt:$WD_PROPERTY$ ;
    sh:property [
       sh:path wdt:$PROPERTY$ ;
       sh:minCount 1;
       sh:in ($item_of$) ;
       sh:description "items using this property should have a certain other statement"; 
    ] ;
    $MANDATORY$
"""

    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )

        prop = ""
        item_of = ""
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            constraint_status_link = ""
            match qid:
                ## P2306 property
                case EnumQualifiersID.property_qualifier.value:  # !!
                    prop = qualifier.get("object_val")[0]
                    prop = prop[prop.rfind("/P") + 1:]
                ## P2305 item of property constraint
                case EnumQualifiersID.item_of_property_constraint_qualifier.value:  # !!
                    for new_expression in qualifier.get("object_val"):
                        new_expression = new_expression[new_expression.rfind("/Q") + 1:]
                        new_expression = "wd:" + new_expression + " "
                        item_of += new_expression
                ## P2316 constraint status
                case EnumQualifiersID.constraint_status_qualifier.value:
                    constraint_status_link = qualifier.get("object_val")[0]  # !!??
                    if constraint_status_link == "http://www.wikidata.org/entity/Q21502408":
                        mandatory = True

        self.constraint_shacl = self.constraint_shacl.replace(
            "$PROPERTY$", prop
        )
        if item_of:
            item_of = item_of[:-1]
            self.constraint_shacl = self.constraint_shacl.replace(
                "$item_of$", item_of
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "       sh:in ($item_of$) ;\n", ""
            )

        if mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        elif not mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl

    def getRequiredPrefixes(self):
        return [EnumPrefixes.example_prefix, EnumPrefixes.wdt_prefix, EnumPrefixes.wd_prefix, EnumPrefixes.sh_prefix]


class OneOfConstraint(ConstraintType): # why P279??
    def __init__(self):
        self.constraint_shacl = """
:$WD_PROPERTY$_OneOfShape
    a sh:NodeShape ;
    sh:targetSubjectsOf wdt:$WD_PROPERTY$;
    sh:property[
        sh:path ( wdt:$WD_PROPERTY$ [ sh:zeroOrMorePath wdt:P279 ] ) ;
        sh:in ($item_of$) ;
        sh:description "specifies that only certain values are allowed for a property."; 
    ] ;
    $MANDATORY$
"""

    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )

        item_of = ""
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            constraint_status_link = ""
            match qid:
                ## P2305 item of property constraint
                case EnumQualifiersID.item_of_property_constraint_qualifier.value:  # !!
                    for new_expression in qualifier.get("object_val"):
                        position = new_expression.rfind("/Q")
                        if position > -1:
                            new_expression = new_expression[position + 1:]
                            new_expression = "wd:" + new_expression + " "
                            item_of += new_expression
                ## P2316 constraint status
                case EnumQualifiersID.constraint_status_qualifier.value:
                    constraint_status_link = qualifier.get("object_val")[0]  # !!??
                    if constraint_status_link == "http://www.wikidata.org/entity/Q21502408":
                        mandatory = True

        if item_of:
            item_of = item_of[:-1]
            self.constraint_shacl = self.constraint_shacl.replace(
                "$item_of$", item_of
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "       sh:in ($item_of$) ;\n", ""
            )

        if mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        elif not mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl

    def getRequiredPrefixes(self):
        return [EnumPrefixes.example_prefix, EnumPrefixes.wdt_prefix, EnumPrefixes.wd_prefix, EnumPrefixes.sh_prefix,
                EnumPrefixes.p_prefix, EnumPrefixes.pq_prefix, EnumPrefixes.sh_prefix]

class RequiredQualifiersConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """
:$WD_PROPERTY$_RequiredQualifiersShape 
    a sh:NodeShape ;
    sh:targetObjectsOf p:$WD_PROPERTY$ ;
    sh:property[
        sh:path pq:$PROPERTY$ ;
        sh:minCount 1 ;
        sh:description "Specifies that some qualifier is required for this property."; 
    ] ;
    $MANDATORY$
"""

    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )

        prop = ""
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            constraint_status_link = ""
            match qid:
                ## P2306 property_qualifier
                case EnumQualifiersID.property_qualifier.value:
                    prop = qualifier.get("object_val")[0]
                    prop = prop[prop.rfind("/P") + 1:]
                ## P2316 constraint status
                case EnumQualifiersID.constraint_status_qualifier.value:
                    constraint_status_link = qualifier.get("object_val")[0]
                    if constraint_status_link == "http://www.wikidata.org/entity/Q21502408":
                        mandatory = True

        self.constraint_shacl = self.constraint_shacl.replace(
            "$PROPERTY$", prop
        )

        if mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        elif not mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl

    def getRequiredPrefixes(self):
        return [EnumPrefixes.example_prefix, EnumPrefixes.wdt_prefix, EnumPrefixes.wd_prefix, EnumPrefixes.sh_prefix,
                EnumPrefixes.p_prefix, EnumPrefixes.pq_prefix, EnumPrefixes.sh_prefix]

class ValueRequiresStatementConstraint(ConstraintType):
    def __init__(self):
        self.constraint_shacl = """
:$WD_PROPERTY$_ValueRequiresStatementShape
    a sh:NodeShape ;
    sh:targetSubjectsOf wdt:$WD_PROPERTY$ ;
    sh:description "Specifies that values for this property (enitity of the property) should have a certain other statement."; 
    sh:or (
        [ sh:in ($EXCEPTIONS$) ]
        [
            sh:property [
                sh:path (wdt:$WD_PROPERTY$ wdt:$PROPERTY$) ;
                sh:minCount 1 ;
                sh:in ($item_of$) ;
            ]
        ]
    ) ;
    $MANDATORY$
"""
    def toShacl(self, pid, qualifiers):
        self.constraint_shacl = self.constraint_shacl.replace(
            "$WD_PROPERTY$", pid
        )

        exceptions = ""
        prop = ""
        item_of = ""
        mandatory = False
        for qualifier in qualifiers:
            qid = qualifier.get("pq_qualifiers")
            qid = qid[qid.rfind("/P") + 1:]
            constraint_status_link = ""
            match qid:
                ## P2306 property
                case EnumQualifiersID.property_qualifier.value:  # !!
                    prop = qualifier.get("object_val")[0]
                    prop = prop[prop.rfind("/P") + 1:]
                ## P2305 item of property constraint
                case EnumQualifiersID.item_of_property_constraint_qualifier.value:  # !!
                    for new_expression in qualifier.get("object_val"):
                        new_expression = new_expression[new_expression.rfind("/Q") + 1:]
                        new_expression = "wd:" + new_expression + " "
                        item_of += new_expression
                ## P2303 exception to constraint
                case EnumQualifiersID.exception_to_constraint_qualifier.value:
                    for exception in qualifier.get("object_val"):
                        exception = exception[exception.rfind("/Q") + 1:]
                        exception = "wd:" + exception + " "
                        exceptions += exception
                ## P2316 constraint status
                case EnumQualifiersID.constraint_status_qualifier.value:
                    constraint_status_link = qualifier.get("object_val")[0]  # !!??
                    if constraint_status_link == "http://www.wikidata.org/entity/Q21502408":
                        mandatory = True

        # property
        self.constraint_shacl = self.constraint_shacl.replace(
            "$PROPERTY$", prop
        )
        # item of property
        if item_of:
            item_of = item_of[:-1]
            self.constraint_shacl = self.constraint_shacl.replace(
                "$item_of$", item_of
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "                sh:in ($item_of$) ;\n", ""
            )

        # Exceptions
        if exceptions:
            exceptions = exceptions[:-1]
            self.constraint_shacl = self.constraint_shacl.replace(
                "$EXCEPTIONS$", exceptions
            )
        else:
            self.constraint_shacl = self.constraint_shacl.replace(
                "        [ sh:in ($EXCEPTIONS$) ]\n", ""
            )

        # Mandatory
        if mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Violation ."
            )
        elif not mandatory:
            self.constraint_shacl = self.constraint_shacl.replace(
                "$MANDATORY$", "sh:severity sh:Warning ."
            )

        return self.constraint_shacl

    def getRequiredPrefixes(self):
        return [EnumPrefixes.example_prefix, EnumPrefixes.wdt_prefix, EnumPrefixes.wd_prefix, EnumPrefixes.p_prefix,
                EnumPrefixes.pq_prefix, EnumPrefixes.sh_prefix]