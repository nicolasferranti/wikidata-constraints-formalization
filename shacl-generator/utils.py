from enum import Enum

class EnumQualifiersID(Enum):
    relation_qualifier = "P2309"
    class_qualifier = "P2308"
    constraint_status_qualifier = "P2316"
    format_as_a_regular_expression_qualifier = "P1793"


class ShapePrefix:
    __prefix: str
    __namespace: str

    def __init__(self, prefix: str, namespace: str):
        self.__prefix = prefix
        self.__namespace = namespace

    def getPrefix(self):
        return self.__prefix

    def getNamespace(self):
        return self.__namespace


class EnumPrefixes(Enum):
    example_prefix = ShapePrefix("", "http://example.org/")
    wdt_prefix = ShapePrefix("wdt", "http://www.wikidata.org/prop/direct/")
    wd_prefix = ShapePrefix("wd", "http://www.wikidata.org/entity/")
    sh_prefix = ShapePrefix("sh", "http://www.w3.org/ns/shacl#")
