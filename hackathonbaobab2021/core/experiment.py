import pytups as pt
import os
from .instance import Instance
from .solution import Solution
from . import tools as di
from zipfile import ZipFile
from typing import List
from cornflow_client import ExperimentCore


class Experiment(ExperimentCore):
    def __init__(self, instance: Instance, solution: Solution = None):
        super().__init__(instance, solution)
        if solution is None:
            solution = Solution(pt.SuperDict(assignment=pt.TupList()))
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

    def check_solution(self, list_tests: List[str] = None, **params) -> pt.SuperDict:
        # simple checks:
        # each team plays twice
        return pt.SuperDict(
            num_away=self.check_num_away(), num_home=self.check_num_home()
        )

    def check_num_away(self):
        assignment = self.solution.get_assignment()
        teams = self.instance.get_teams("id").vapply(lambda v: 0)
        num_matches = (len(teams) - 1) * 2
        return (
            teams
            + assignment.to_dict(result_col=["slot"], indices=["away"]).to_lendict()
        ).vfilter(lambda v: v != num_matches)

    def check_num_home(self):
        assignment = self.solution.get_assignment()
        teams = self.instance.get_teams("id").vapply(lambda v: 0)
        num_matches = (len(teams) - 1) * 2
        return (
            teams
            + assignment.to_dict(result_col=["slot"], indices=["home"]).to_lendict()
        ).vfilter(lambda v: v != num_matches)

    def get_objective(self, **params) -> int:
        return 0

    def graph(self):
        pass
