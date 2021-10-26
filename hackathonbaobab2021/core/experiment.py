import os
from .instance import Instance
from .solution import Solution
from . import tools as di
from zipfile import ZipFile
from typing import List
from cornflow_client import ExperimentCore
import xml.etree.ElementTree as ET
from .tools import indent
from pytups import SuperDict, TupList

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
        for each team, for each timeslot: H or A
        """
        assignment = self.solution.get_assignment()
        result = SuperDict()
        for key, name in abbrv.items():
            _v = assignment.take([name, "slot"]).to_dict(None).vapply(lambda v: key)
            result.update(_v)
        return result.to_dictdict()

    def check_CA1(self):
        constraints = self.instance.get_constraint("CA1")
        team_slot = self.team_slot()
        # make one single comparison
        _max_violations = {
            (c["_id"], team, slot): (team_slot.get_m(team, slot) == c["mode"])
            - int(c["max"])
            for c in constraints.values()
            for team in c["teams"]
            for slot in c["slots"]
        }
        _min_violations = {
            (c["_id"], team, slot): (team_slot.get_m(team, slot) == c["mode"])
            - int(c["min"])
            for c in constraints.values()
            for team in c["teams"]
            for slot in c["slots"]
        }
        result = SuperDict(_max_violations).vfilter(lambda v: v > 0)
        _min = SuperDict(_min_violations).vfilter(lambda v: v < 0)
        result.update(_min)
        return result

    def check_CA3(self):

        pass

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
