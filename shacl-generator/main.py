import requests, json, os, argparse
from enum import Enum
from abc import ABC, abstractmethod
from constraints import *
from wikidataDataExtractor import WikidataOnlineEndpointExtractor
from pprint import pprint
import time

query_results = "./query results"


def read_json(dir, fname):
    with open(f"{dir}/{fname}.json", "r") as property_file:
        return json.load(property_file)


def dump_json(dir, fname, data):
    if not os.path.exists(dir):
        os.mkdir(dir)

    with open(f"{dir}/{fname}.json", "w") as outfile:
        json.dump(data, outfile, indent=2)


def write_file(dir, fname, data):
    if not os.path.exists(dir):
        os.mkdir(dir)

    nanotime = str(time.time_ns())

    with open(f"{dir}/{fname}_{nanotime}.ttl", "w") as outfile:
        outfile.write(data)


class EnumPropertyConstraints(Enum):
    FormatConstraint = "Q21502404"
    # ItemRequiresStatementConstraint = "Q21503247"
    TypeConstraint = "Q21503250"


class WdToShaclController():
    def __init__(self, save_file):

        self.save_to_file = save_file
        self.wikidataDataExtractor = WikidataOnlineEndpointExtractor()

    def getDictQualifierValue(self, constraint_detail):
        dict = {"pq_qualifiers": constraint_detail["pq_qualifiers"]["value"],
                "object_val": constraint_detail["object_val"]["value"].split("|#@$|")}
        return dict

    def parseQueryDataToDict(self, query_data):
        data = query_data["results"]["bindings"]

        dict_return = {}
        temp_dict = {}
        qualifiers = []
        statement_control = None

        for constraint_detail in data:
            statement_id = constraint_detail["statement"]["value"]
            statement_id = statement_id[statement_id.rfind("/P") + 1:]
            if (statement_control is None) | (statement_id != statement_control):

                if len(temp_dict) != 0:
                    temp_dict["qualifiers"] = qualifiers
                    dict_return[statement_control] = temp_dict
                    temp_dict = {}
                    qualifiers = []

                temp_dict["constraint_type"] = constraint_detail["constraint_type"]["value"]
                statement_control = statement_id

            qualifiers.append(self.getDictQualifierValue(constraint_detail))

        if statement_control is not None:
            temp_dict["qualifiers"] = qualifiers
            dict_return[statement_control] = temp_dict

        return dict_return

    def get_class(self, kls):
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m

    def prefixes_2_ttl(self, prefixes: list):
        output = ""
        for prefix in prefixes:
            output += "@prefix " + prefix.value.getPrefix() + ": <" + prefix.value.getNamespace() + ">. \n"
        return output

    def run(self, pid):

        query_data = self.wikidataDataExtractor.extractPropertyConstraints(pid)
        property_json = self.parseQueryDataToDict(query_data)

        shacl_constraints = []
        prefixes = []

        # the same constraint type can be used more than once, so we count to differentiate

        for json_item in property_json.values():
            constraint_url = json_item.get("constraint_type")
            constraint = json_item.get("constraint_type")[constraint_url.rfind("/Q") + 1:]

            if constraint in EnumPropertyConstraints._value2member_map_:
                constraint_class_name = EnumPropertyConstraints(constraint).name
                constraint_class_name = "constraints." + constraint_class_name
                clss = self.get_class(constraint_class_name)
                obj = clss()
                shacl_constraints.append(obj.toShacl(pid=pid, qualifiers=json_item.get("qualifiers")))
                prefixes = list(set(prefixes + obj.getRequiredPrefixes()))

            """
            try:
                constraint_func = constraints_delegate[constraint]
                shacl_constraints[shacl_index] = constraint_func.toShacl(pid=pid, qualifiers=json_item.get("qualifiers"))
            except KeyError:
                pass
            """

            """
            match constraint:
                case EnumPropertyConstraints.FormatConstraint.value:
                    format_constraint = FormatConstraint()
                    shacl_constraints[shacl_index] = format_constraint.toShacl(pid=pid, qualifiers=json_item.get("qualifiers"))
                case EnumPropertyConstraints.TypeConstraint.value:
                    type_constraint = TypeConstraint()
                    shacl_constraints[shacl_index] = type_constraint.toShacl(pid=pid, qualifiers=json_item.get("qualifiers"))

            count_diff_constraint += 1
            """

        output = ""
        for const in shacl_constraints:
            output += const

        ttl_prefixes = self.prefixes_2_ttl(prefixes)
        output = ttl_prefixes + output

        if self.save_to_file:
            write_file("./shacl constraints", pid, output)
        else:
            print(output, end="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-pid",
        "--property_id",
        type=str,
        help="WD property ID to generate SHACL property shapes for"
    )

    parser.add_argument(
        "-s",
        "--save",
        type=bool,
        help="flag that indicates whether the output should be saved or not. If not save, then it is printed to std out"
    )

    # parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    args = parser.parse_args()
    if args.property_id is None:
        args.property_id = input(
            "For which property would you like to generate a SHACL property shape?\n> "
        )

    if args.save is None:
        args.save = input(
            "Type True to save the output into a file or False to print the output\n> "
        )
        args.save = (args.save == "True")

    controller = WdToShaclController(save_file=args.save)
    # test: P6 and P578 (no property constraint)
    controller.run(args.property_id)
