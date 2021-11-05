from pytups import TupList, OrderSet
import os
from cornflow_client import InstanceCore
from cornflow_client.core.tools import load_json
from pytups import SuperDict
import xml.etree.ElementTree as ET
from .tools import copy_dict
from .constants import C_CLUSTER, C_CAT, C_TUPLES, _CAT, _ID, INT_PROPS


class Instance(InstanceCore):
    def __init__(self, data: SuperDict):
        super().__init__(data)
        self.slots = OrderSet(data["slots"].keys_tl().sorted())

    schema = load_json(
        os.path.join(os.path.dirname(__file__), "../schemas/instance.json")
    )

    @property
    def data(self) -> SuperDict:
        return self._data

    @data.setter
    def data(self, value: SuperDict):
        self._data = value

    def get_constraint(self, tag, c_type=None) -> SuperDict:
        if c_type is None:
            return self.data[tag]
        return self.data[tag].vfilter(lambda v: v["type"] == c_type)

    def get_penalty(self, tag, id) -> float:
        return self.data.get_m(tag, id, "penalty")

    def get_teams(self, property=None) -> SuperDict:
        if property is None:
            return self.data["teams"]
        return self.data["teams"].get_property(property)

    def get_slots(self) -> SuperDict:
        return self.data["slots"]

    def to_dict(self) -> dict:
        # we will keep as close format to the original XML
        masters = ["teams", "slots", "leagues"] + C_CAT.keys_tl()
        data = {table: self.data[table].values_tl() for table in masters}

        # for each constraint, we go back to the flat XML notation
        data = copy_dict(data)
        for c in C_CAT.keys():
            for constraint in data[c]:
                flatten_constraint(constraint)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Instance":
        data_p = SuperDict()
        for table in ["teams", "slots", "leagues"]:
            data_p[table] = {el["id"]: el for el in data[table]}
        for table in C_CAT.keys():
            data_p[table] = {el[_ID]: el for el in data[table]}

        data_p = copy_dict(data_p)
        for c in C_CAT.keys():
            for constraint in data_p[c].values():
                unflatten_constraint(constraint)

        return cls(SuperDict.from_dict(data_p))

    @classmethod
    def from_xml(cls, path) -> "Instance":

        # by default, all properties that start with _ are created by us.

        # follows a special case of the RobinX XML format.
        tree = ET.parse(path)
        root = tree.getroot()
        resources = root.find("Resources")
        as_dict_list = lambda l: TupList(l).vapply(lambda v: v.attrib)

        data_p = SuperDict(teams="Teams", slots="Slots", leagues="Leagues").vapply(
            lambda v: as_dict_list(resources.find(v))
        )
        # we want to index the list of dictionaries by their own id
        for k, v in data_p.items():
            data_p[k] = SuperDict({vv["id"]: vv for vv in v})

        constraints = root.find("Constraints")

        # we want to store the category of the constraint.
        # we create the _cat field

        def read_constraint(c):
            _dict = dict(c.attrib)
            _dict[_CAT] = c.tag
            return _dict

        # we read all constraints data
        read_constraints = lambda l: TupList(l).vapply(read_constraint)

        # we create the _id field to represent the enumeration of constraints in each category
        def _treat(constraint_arr):
            _dict = {pos: {**{_ID: pos}, **el} for pos, el in enumerate(constraint_arr)}
            for v in _dict.values():
                unflatten_constraint(v)

            return SuperDict(_dict)

        constraints_per_cluster = C_CLUSTER.vapply(
            lambda c: constraints.find(c)
        ).vapply(read_constraints)
        # we will group by constraint type, not the 5 large groups.
        constraints_per_type = C_CAT.vapply(lambda v: [])
        for constraint_cluster in constraints_per_cluster.values():
            for constraint in constraint_cluster:
                constraints_per_type[constraint[_CAT]].append(constraint)

        data_p.update(constraints_per_type.vapply(_treat))

        return cls(data_p)


def flatten_constraint(constraint):
    for key in C_CAT[constraint[_CAT]]:
        _list = TupList(constraint[key])
        # we flatten the tuples
        if C_TUPLES.get_m(constraint[_CAT], key):
            _list = _list.vapply(lambda v: ",".join(v))
        # we flatten the lists
        _list = ";".join(_list)
        constraint[key] = _list
    for el in INT_PROPS:
        try:
            constraint[el] = str(constraint[el])
        except:
            continue


def unflatten_constraint(constraint):
    for key in C_CAT[constraint[_CAT]]:
        _list = TupList(constraint[key].split(";"))
        _list = _list.vfilter(lambda v: v)
        if len(_list) and C_TUPLES.get_m(constraint[_CAT], key):
            _list = _list.vapply(lambda v: tuple(v.split(",")))
        constraint[key] = _list
    for el in INT_PROPS:
        try:
            constraint[el] = int(constraint[el])
        except:
            continue
