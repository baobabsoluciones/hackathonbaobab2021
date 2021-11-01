import os
from .instance import Instance
from .solution import Solution
from . import tools as di
from zipfile import ZipFile
from typing import List, Union, Any
from cornflow_client import ExperimentCore
import xml.etree.ElementTree as ET
from .tools import indent
from pytups import SuperDict, TupList
from functools import partial

from itertools import combinations

HOME = "H"
AWAY = "A"
SOFT = "SOFT"
HARD = "HARD"
GLOBAL = "GLOBAL"
EVERY = "EVERY"
status = SuperDict({HOME: "home", AWAY: "away"})


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

    def check_solution(
        self, list_tests: List[str] = None, c_type=HARD, **params
    ) -> SuperDict:
        # simple checks:
        # each team plays twice
        official_checks = SuperDict(
            CA1=self.check_CA1,
            CA2=self.check_CA2,
            CA3=self.check_CA3,
            CA4_slots=partial(self.check_CA4, level=EVERY),
            CA4_global=partial(self.check_CA4, level=GLOBAL),
            GA1=self.check_GA1,
            SE1=self.check_SE1,
            BR1=self.check_BR1,
            BR2=self.check_BR2,
            FA2=self.check_FA2,
        )
        if list_tests is not None:
            official_checks = official_checks.filter(indices=list_tests)
        checks = official_checks.vapply(lambda v: v(c_type=c_type, **params))
        own_checks = dict()
        if c_type == HARD:
            own_checks = SuperDict(
                num_away=self.check_num_matches("away"),
                num_home=self.check_num_matches("home"),
                one_match_slot=self.check_one_match_per_slot(),
            )
        return checks._update(own_checks).vfilter(lambda v: len(v))

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
        for key, name in status.items():
            _v = assignment.take([name, "slot"]).to_dict(None).vapply(lambda v: key)
            result.update(_v)
        return result.to_dictdict()

    def get_acc(self, check=HOME):
        """
        (team, slot): accumulate check (H=home, A=away).
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

    def check_FA2(self, **kwargs):
        """
        team and team2 in T
        (c, team, team2): max(difference in accumulated homes in slots in S) <= intp
        """
        acc_homes = self.get_acc(check=HOME)
        constraints = self.instance.get_constraint("FA2", **kwargs)
        err = SuperDict()
        for k, c in constraints.items():

            def max_diff_acc_homes(team1, team2):
                return max(
                    abs(acc_homes[team1, slot] - acc_homes[team2, slot])
                    for slot in c["slots"]
                )

            # we get all combinations, and re-arrange so team1 < team2.
            # then we calculate the max diff among all slots
            # then compare with maximum
            # then we filter those that surpass
            err[k] = (
                TupList(combinations(c["teams"], 2))
                .vapply(get_sym)
                .to_dict(None)
                .vapply(lambda v: max_diff_acc_homes(*v) - c["intp"])
                .vfilter(lambda v: v > 0)
            )
        return err.vfilter(lambda v: len(v)).to_dictup()

    def check_CA1(self, **kwargs):
        """
        team in T, slot in S
        (c, team, slot): min <= sum(matches in mode M) <= max
        """
        constraints = self.instance.get_constraint("CA1", **kwargs)
        team_slot = self.team_slot()
        # make one single comparison
        value = {
            (k, team, slot): team_slot.get_m(team, slot) == c["mode"]
            for k, c in constraints.items()
            for team in c["teams"]
            for slot in c["slots"]
        }
        return compare(SuperDict(value), constraints, side=None)

    def check_CA2(self, **kwargs):
        """
        (c, team) : min <= sum(matches by teams T and R rivals in mode M during slots S) <= max
        """
        matches = self.solution.get_home_away_slot().to_set()
        constraints = self.instance.get_constraint("CA2", **kwargs)
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

    def check_CA3(self, **kwargs):
        """
        for each (c, team, slot) => sum(matches with R rivals in next S slots in mode M) <= max
        """
        matches = self.solution.get_home_away_slot().to_set()
        constraints = self.instance.get_constraint("CA3", **kwargs)
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
        return value.to_dictdict().to_dictup()

    def check_CA4(self, level=GLOBAL, **kwargs):
        """
        if level == GLOBAL:
            (c, ) => sum(matches by all teams in T with R rivals in S slots in mode M) <= max
        if level == EVERY:
            (c, slot) : sum(matches by all teams in T with R rivals in mode M) <= max
        """
        matches = self.solution.get_home_away_slot().to_set()
        constraints = self.instance.get_constraint("CA4", **kwargs).vfilter(
            lambda c: c["mode2"] == level
        )

        def _func(constraint):
            tuplist = get_matches_slots_constraint(constraint)
            return apply_mode(tuplist, mode=constraint["mode2"]).to_set()

        if level == GLOBAL:
            value = {(k,): len(_func(c) & matches) for k, c in constraints.items()}
        else:
            # level == EVERY
            value = {k: TupList(_func(c) & matches) for k, c in constraints.items()}
            value = (
                SuperDict(value)
                .vapply(lambda v: v.to_dict(result_col=[0, 1]).to_lendict())
                .to_dictup()
            )
        return compare(SuperDict(value), constraints, "max")

    def check_GA1(self, **kwargs):
        """
        (c, ): min <= sum(matches in M in mode M) <= max
        """
        constraints = self.instance.get_constraint("GA1", **kwargs)
        tup_list = self.solution.get_home_away_slot()
        value = {
            (k,): (*match, slot)
            for k, c in constraints.items()
            for match in c["meetings"]
            for slot in c["slots"]
        }
        value = SuperDict(value).vapply(lambda v: tup_list.intersect(value).len())
        return compare(value, constraints, side=None)

    def check_SE1(self, **kwargs):
        """
        (c, ):
        """
        constraints = self.instance.get_constraint("SE1", **kwargs)
        value = SuperDict()
        _dist = self.instance.slots.dist
        for k, c in constraints.items():
            pairs = TupList(combinations(c["teams"], 2)).vapply(get_sym)
            value[k] = (
                self.solution.get_pair_slots().filter(pairs).vapply(lambda v: _dist(*v))
            )
        return compare(value.to_dictdict().to_dictup(), constraints, side="min")

    def check_BR1(self, **kwargs):
        """
        (c, team) : sum(breaks of team in slots in S, modes in M) <= intp
        """
        # raise NotImplementedError("we need to index by team")
        breaks_per_team = (
            self.count_breaks().to_tuplist().to_dict(result_col=[1, 2]).vapply(set)
        )
        constraints = self.instance.get_constraint("BR1", **kwargs)
        value = SuperDict()
        for k, c in constraints.items():
            if c["mode2"] in [AWAY, HOME]:
                modes = [c["mode2"]]
            else:  #  c["mode1"] == "HA"
                modes = [HOME, AWAY]
            check = TupList(
                (slot, mode) for slot in c["slots"] for mode in modes
            ).to_set()
            value[k] = {
                team: len((check & breaks_per_team[team])) - c["intp"]
                for team in c["teams"]
            }
        value = value.to_dictup()
        return value.vfilter(lambda v: v > 0)

    def check_BR2(self, **kwargs):
        """
        (c, ): sum(breaks of teams T in slots S) <= intp
        """
        breaks = self.count_breaks()
        constraints = self.instance.get_constraint("BR2", **kwargs)
        value = {
            k: breaks.kfilter(lambda v: v[0] in c["teams"] and v[1] in c["slots"]).len()
            - c["intp"]
            for k, c in constraints.items()
        }
        return SuperDict(value).vfilter(lambda v: v > 0)

    def count_breaks(self):
        """
        (team, slot): H / A when the team ends a break (H= ends in home, A= ends in away)
        """
        prev = self.instance.slots.prev
        first = self.instance.slots[0]
        t_prev = lambda k: (k[0], prev(k[1]))
        team_slot = self.team_slot().to_dictup()
        return team_slot.kfilter(lambda k: k[1] != first).kvfilter(
            lambda k, v: v != team_slot.get(t_prev(k))
        )

    def check_num_matches(self, mode="home"):
        """
        returns {team: # matches in mode} if different from correct value
        """
        assignment = self.solution.get_assignment()
        teams = self.instance.get_teams("id").vapply(lambda v: 0)
        num_matches = len(teams) - 1
        return (
            assignment.to_dict(result_col=["slot"], indices=[mode])
            .to_lendict()
            .fill_with_default(teams)
            .vfilter(lambda v: v != num_matches)
        )

    def get_objective(self, **params) -> float:
        # for each check, the violation value
        checks = self.check_solution(c_type=SOFT).to_dictdict().to_dictup()
        # CA4 has CA4_global and CA4_slot so we need to get the name by looking for _
        get_name = lambda name: name.split("_")[0]
        # the first key is the constraint tag, the second is the constraint id.
        get_penaly = lambda k: self.instance.get_penalty(get_name(k[0]), k[1])
        # we get the absolute deviation, then
        # we multiply the violation with the penalty, then sum the results
        return sum(checks.kvapply(lambda k, v: abs(v) * get_penaly(k)).values())

    def to_xml(self, path, instance_name="Test Instance Demo"):
        root = ET.Element("Solution")
        metadata = self._xml_build_metadata(instance_name)
        games = self._xml_build_games()
        root.append(metadata)
        root.append(games)
        tree = ET.ElementTree(element=root)
        # this following function gives the indentation and spacing:
        indent(root)
        tree.write(
            path, xml_declaration=True, encoding="utf-8", short_empty_elements=False
        )

    def _xml_build_metadata(self, instance_name):
        metadata = ET.Element("MetaData")
        solution = ET.Element("SolutionName")
        solution.text = "Sol" + instance_name
        instance = ET.Element("InstanceName")
        instance.text = instance_name
        objective = ET.Element("ObjectiveValue")
        objective_contents = dict(
            infeasibility=str(sum(self.check_solution().to_lendict().values())),
            objective=str(self.get_objective()),
        )
        for v in objective_contents.items():
            objective.set(*v)
        for el in [instance, solution, objective]:
            metadata.append(el)
        return metadata

    def _xml_build_games(self):
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


def compare(_dict: SuperDict[Any, int], constraints, side: Union[str, None] = "min"):
    """
    _dict has the structure: {(c, *): int}
    constraints is a dictionary: {c: dict(min=int, max=int)}

    this function compares the value of the dictionary against the min and / or max
    levels of the constraint.
    And returns a negative number if it goes under the min
     and a positive number when it goes over the max.
    """
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
    """
    reformats a tuple of (team, rival) so that the first element is smaller than the other
    (by convention, this is how we represent a match without home-away status).
    """
    if pair[0] > pair[1]:
        return pair[1], pair[0]
    else:
        return pair


def apply_mode(tup_list, mode):
    """
    Assumes a tup_list with the structure (team, rival, slot)
    re-arranges the tuples in the tup_list so the home team depending on what we want to check
    If we want to check for when team is playing in

    * home: we leave it as is.
    * away: we switch team and rival
    * both: we return both tup_lists joined

    """
    if mode == HOME:
        return tup_list
    reversed = tup_list.vapply(lambda v: (v[1], v[0], v[2]))
    if mode == AWAY:
        # we pass the team to away position
        return reversed
    # mode == "HA"
    # we duplicate the rows to check both positions
    return tup_list + reversed


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
