import os
from .instance import Instance
from .solution import Solution
from . import tools as di
from zipfile import ZipFile
from typing import List, Union
from cornflow_client import ExperimentCore
import xml.etree.ElementTree as ET
from .tools import indent
from pytups import SuperDict, TupList

from itertools import combinations

abbrv = SuperDict(H="home", A="away")


class Experiment(ExperimentCore):
    def __init__(self, instance: Instance, solution: Solution = None):
        super().__init__(instance, solution)
        if solution is None:
            solution = Solution(SuperDict(assignment=TupList()))
        self.solution = solution
        return

    @property
    def instance(self) -> Instance:
        return self._instance

    @property
    def solution(self) -> Solution:
        return super().solution

    @solution.setter
    def solution(self, value):
        self._solution = value

    @classmethod
    def from_json(
        cls, path: str, inst_file: str = "input.json", sol_file: str = "output.json"
    ) -> "Experiment":
        instance = Instance.from_json(os.path.join(path, inst_file))
        if os.path.exists(os.path.join(path, sol_file)):
            solution = Solution.from_json(os.path.join(path, sol_file))
        else:
            solution = None
        return cls(instance, solution)

    @classmethod
    def from_zipped_json(
        cls,
        zipobj: ZipFile,
        path: str,
        inst_file: str = "input.json",
        sol_file: str = "output.json",
    ) -> "Experiment":
        instance = di.load_data_zip(zipobj, os.path.join(path, inst_file))
        instance = Instance.from_dict(instance)
        try:
            solution = di.load_data_zip(zipobj, os.path.join(path, sol_file))
            solution = Solution.from_dict(solution)
        except:
            solution = None
        return cls(instance, solution)

    def solve(self, options: dict):
        raise NotImplementedError("complete this!")

    def check_solution(self, list_tests: List[str] = None, **params) -> SuperDict:
        # simple checks:
        # each team plays twice
        return SuperDict(
            num_away=self.check_num_away(),
            num_home=self.check_num_home(),
            one_match_slot=self.check_one_match_per_slot(),
            CA1=self.check_CA1(),
            CA2=self.check_CA2(),
            CA3=self.check_CA3(),
            CA4_slots=self.check_CA4_slots(),
            CA4_global=self.check_CA4_global(),
            GA1=self.check_GA1(),
            SE1=self.check_SE1(),
            BR1=self.check_BR1(),
            BR2=self.check_BR2(),
            FA2=self.check_FA2(),
        )

    def check_num_away(self):
        assignment = self.solution.get_assignment()
        teams = self.instance.get_teams("id").vapply(lambda v: 0)
        num_matches = len(teams) - 1
        return (
            assignment.to_dict(result_col=["slot"], indices=["away"])
            .to_lendict()
            .fill_with_default(teams)
            .vfilter(lambda v: v != num_matches)
        )

    def check_one_match_per_slot(self):
        """
        returns the (slot, team) combinations where the team plays more than once
        """
        assignment = self.solution.get_assignment()
        home = assignment.to_dict(result_col=["home"], indices=["slot"])
        away = assignment.to_dict(result_col=["away"], indices=["slot"])
        return (
            (home + away)
            .to_tuplist()
            .to_dict(result_col=[0, 1], indices=[0, 1])
            .vfilter(lambda v: len(v) > 1)
            .vapply(lambda v: 1)
        )

    def team_slot(self):
        """
        for each team, for each slot: H or A
        """
        assignment = self.solution.get_assignment()
        result = SuperDict()
        for key, name in abbrv.items():
            _v = assignment.take([name, "slot"]).to_dict(None).vapply(lambda v: key)
            result.update(_v)
        return result.to_dictdict()

    def get_match_slot(self):
        """
        for each match, the slot when it happened
        """
        assignment = self.solution.get_assignment()
        return assignment.to_dict(
            result_col=["slot"], indices=["home", "away"], is_list=False
        )

    def get_pair_slots(self):
        """
        for each pair (a, b) | (a < b), the ordered slots they play.
        """
        match_slot = self.get_match_slot().vapply(TupList)
        return (
            match_slot.kfilter(lambda k: k[0] < k[1])
            .kvapply(lambda k, v: v + match_slot[k[1], k[0]])
            .vapply(sorted)
        )

    def get_acc(self, check="H"):
        """
        for each (team, slot): accumulate H (or A if not home).
        """
        slots = self.instance.slots
        team_slot = self.team_slot()
        teams = self.instance.get_teams()
        acc = SuperDict()
        for team in teams:
            _acc = 0
            for slot in slots:
                _acc += team_slot.get_m(team, slot) == check
                acc[team, slot] = _acc
        return acc

    def check_FA2(self):
        acc_homes = self.get_acc(check="H")
        constraints = self.instance.get_constraint("FA2")
        err = SuperDict()
        for k, c in constraints.items():
            pairs = TupList(combinations(c["teams"], 2)).vapply(get_sym)
            err[k] = (
                pairs.to_dict(None)
                .vapply(
                    lambda v: max(
                        abs(acc_homes[v[0], slot] - acc_homes[v[1], slot])
                        for slot in c["slots"]
                    )
                )
                .vfilter(lambda v: v - c["intp"])
            )
        return err.to_dictdict().to_dictup()

    def check_CA1(self):
        """
        "for each (c, team, slot) => violation"
        """
        constraints = self.instance.get_constraint("CA1")
        team_slot = self.team_slot()
        # make one single comparison
        value = {
            (k, team, slot): team_slot.get_m(team, slot) == c["mode"]
            for k, c in constraints.items()
            for team in c["teams"]
            for slot in c["slots"]
        }
        return compare(SuperDict(value), constraints, side=None)

    def check_CA2(self):
        matches = self.solution.get_assignment().take(["home", "away", "slot"]).to_set()
        constraints = self.instance.get_constraint("CA2")
        # we index by constraint and team1
        # we apply the mode to expand or move the home away
        # we intersect with the solution and get the number of finds
        value = (
            constraints.vapply(get_matches_slots_constraint)
            .to_tuplist()
            .to_dict(result_col=[1, 2, 3], indices=[0, 1])
            .kvapply(lambda k, v: apply_mode(v, mode=constraints[k[0]]["mode2"]))
            .vapply(lambda v: v.intersect(matches).len())
        )
        return compare(value, constraints, side=None)

    def check_CA3(self):
        "for each (c, team) => violation"
        matches = self.solution.get_assignment().take(["home", "away", "slot"]).to_set()
        constraints = self.instance.get_constraint("CA3")
        all_slots = self.instance.slots
        value = SuperDict()
        for k, c in constraints.items():
            # for each slot, we want c["intp"] consecutive slots:
            slot_slots = TupList(
                (start, slot)
                for pos, start in enumerate(all_slots[: -c["intp"] + 1])
                for slot in all_slots[pos : pos + c["intp"]]
            ).to_dict(result_col=1)
            # for each team and slot, we get all matches and slots to check
            check = {
                (team, start): [
                    (team, rival, slot) for rival in c["teams2"] for slot in slots
                ]
                for team in c["teams1"]
                for start, slots in slot_slots.items()
            }
            # we order the matches and compare it with the solution, only store violations
            value[k] = (
                SuperDict(check)
                .vapply(TupList)
                .vapply(apply_mode, mode=c["mode1"])
                .vapply(lambda v: v.intersect(matches).len())
                .vfilter(lambda v: v > c["max"])
            )
        return value.to_dictup()

    def check_CA4_global(self):
        """
        for each (constraint, ) => violation
        """
        matches = self.solution.get_assignment().take(["home", "away", "slot"]).to_set()
        constraints = self.instance.get_constraint("CA4").vfilter(
            lambda c: c["mode2"] == "GLOBAL"
        )
        _func = (
            lambda v: get_matches_slots_constraint(v)
            .vapply(apply_mode, mode=v["mode2"])
            .to_set()
        )
        value = {(k,): len(_func(c) & matches) for k, c in constraints.items()}
        return compare(SuperDict(value), constraints, "max")

    def check_CA4_slots(self):
        """
        for each (constraint, slot) => violation
        """
        matches = self.solution.get_assignment().take(["home", "away", "slot"]).to_set()
        constraints = self.instance.get_constraint("CA4").vfilter(
            lambda c: c["mode2"] == "EVERY"
        )
        _func = (
            lambda v: get_matches_slots_constraint(v)
            .vapply(apply_mode, mode=v["mode2"])
            .to_set()
        )
        value = {k: TupList(_func(c) & matches) for k, c in constraints.items()}
        value = (
            SuperDict(value)
            .vapply(lambda v: v.to_dict(result_col=[0, 1]).to_lendict())
            .to_dictup()
        )
        return compare(value, constraints, "max")

    def check_GA1(self):
        constraints = self.instance.get_constraint("GA1")
        match_slot = self.get_match_slot()
        value = {
            (k, match, slot): match_slot.get(match) == slot
            for k, c in constraints.items()
            for match in c["meetings"]
            for slot in c["slots"]
        }
        return compare(SuperDict(value), constraints, side=None)

    def check_SE1(self):
        constraints = self.instance.get_constraint("SE1")
        value = SuperDict()
        _dist = self.instance.slots.dist
        for k, c in constraints.items():
            pairs = TupList(combinations(c["teams"], 2)).vapply(get_sym)
            value[k] = self.get_pair_slots().filter(pairs).vapply(lambda v: _dist(*v))
        return compare(value.to_dictdict().to_dictup(), constraints, side="min")

    def check_BR1(self):
        breaks = self.count_breaks().to_tuplist().to_set()
        constraints = self.instance.get_constraint("BR1")
        value = SuperDict()
        for k, c in constraints.items():
            if c["mode2"] in ["A", "H"]:
                # we pass the team to away position
                modes = [c["mode2"]]
            else:
                # c["mode1"] == "HA"
                modes = ["H", "A"]
            check = TupList(
                (team, slot, mode)
                for team in c["teams"]
                for slot in c["slots"]
                for mode in modes
            ).to_set()
            value[k,] = (
                len((check & breaks)) - c["intp"]
            )
        return SuperDict(value).vfilter(lambda v: v > 0)

    def check_BR2(self):
        breaks = self.count_breaks()
        constraints = self.instance.get_constraint("BR2")
        value = {
            k: breaks.kfilter(lambda v: v[0] in c["teams"] and v[1] in c["slots"]).len()
            - c["intp"]
            for k, c in constraints.items()
        }
        return SuperDict(value).vfilter(lambda v: v > 0)

    def count_breaks(self):
        """
        (team, slot) when the team starts a break
        """
        prev = self.instance.slots.prev
        first = self.instance.slots[0]
        t_prev = lambda k: (k[0], prev(k[1]))
        team_slot = self.team_slot().to_dictup()
        return team_slot.kfilter(lambda k: k[1] != first).kvfilter(
            lambda k, v: v != team_slot.get(t_prev(k))
        )

    def check_num_home(self):
        assignment = self.solution.get_assignment()
        teams = self.instance.get_teams("id").vapply(lambda v: 0)
        num_matches = len(teams) - 1
        return (
            assignment.to_dict(result_col=["slot"], indices=["home"])
            .to_lendict()
            .fill_with_default(teams)
            .vfilter(lambda v: v != num_matches)
        )

    def get_objective(self, **params) -> float:
        return 0

    def get_infeasibility(self) -> float:
        return 0

    def graph(self):
        pass

    def to_xml(self, path, instance_name="Test Instance Demo"):
        root = ET.Element("Solution")
        metadata = self._build_metadata(instance_name)
        games = self._build_games()
        root.append(metadata)
        root.append(games)
        tree = ET.ElementTree(element=root)
        # this gives the
        indent(root)
        tree.write(
            path, xml_declaration=True, encoding="utf-8", short_empty_elements=False
        )

    def _build_metadata(self, instance_name):
        metadata = ET.Element("MetaData")
        solution = ET.Element("SolutionName")
        solution.text = "Sol" + instance_name
        instance = ET.Element("InstanceName")
        instance.text = instance_name
        objective = ET.Element("ObjectiveValue")
        objective_contents = dict(
            infeasibility=str(self.get_infeasibility()),
            objective=str(self.get_objective()),
        )
        for v in objective_contents.items():
            objective.set(*v)
        for el in [instance, solution, objective]:
            metadata.append(el)
        return metadata

    def _build_games(self):
        games = ET.Element("Games")

        def to_et(value):
            el = ET.Element("ScheduledMatch")
            for v in value.items():
                el.set(*v)
            return el

        assignment = self.solution.get_assignment().vapply(to_et)
        for el in assignment:
            games.append(el)
        return games


def compare(_dict: SuperDict, constraints, side: Union[str, None] = "min"):
    if side is None:
        # we overload the function to calculate both sides
        _max = compare(_dict, constraints, side="max")
        _min = compare(_dict, constraints, side="min")
        return _max._update(_min)
    if side == "min":
        _func = lambda v: v < 0
    else:  #  max
        _func = lambda v: v > 0
    return (
        SuperDict(_dict)
        .kvapply(lambda k, v: v - constraints[k[0]][side])
        .vfilter(_func)
    )


def get_sym(pair):
    if pair[0] > pair[1]:
        return pair[1], pair[0]
    else:
        return pair


def apply_mode(tup_list, mode):
    if mode == "A":
        # we pass the team to away position
        return tup_list.vapply(lambda v: (v[1], v[0], v[2]))
    elif mode == "HA":
        # we duplicate the rows to check both positions
        return tup_list + tup_list.vapply(lambda v: (v[1], v[0], v[2]))
    # mode = H
    return tup_list


def get_matches_slots_constraint(constraint):
    """
    Returns the values that we look to count in a solution, based on the
        information on the constraint

    """
    check = TupList(
        (team, rival, slot)
        for team in constraint["teams1"]
        for rival in constraint["teams2"]
        for slot in constraint["slots"]
    )
    return check
