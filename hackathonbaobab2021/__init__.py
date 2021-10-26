import os
from typing import Dict, List, Type
from cornflow_client import ApplicationCore, get_empty_schema
from cornflow_client.core.tools import load_json
from .core import Instance, Experiment, Solution, Batch, ZipBatch
from .solver import Default


class SportsScheduling(ApplicationCore):
    name = "sports_scheduling"
    solvers = dict(default=Default)
    schema = get_empty_schema(
        properties=dict(
            timeLimit=dict(type="number"),
            msg=dict(type="boolean"),
            fixSolution=dict(type="boolean"),
            warmStart=dict(type="boolean"),
            gapAbs=dict(type="number"),
            gapRel=dict(type="number"),
            threads=dict(type="integer"),
        ),
        solvers=list(solvers.keys()),
    )

    @property
    def instance(self) -> Type[Instance]:
        return Instance

    @property
    def solution(self) -> Type[Solution]:
        return Solution

    def get_solver(self, name="default") -> Type[Experiment]:
        return super().get_solver(name)

    @property
    def test_cases(self) -> List[Dict]:
        path = os.path.join(os.path.dirname(__file__), "data/TestInstanceDemo.xml")
        _json = os.path.join(os.path.dirname(__file__), "data/example_instance.json")
        _json_sol = os.path.join(
            os.path.dirname(__file__), "data/example_solution.json"
        )
        return [
            Instance.from_xml(path).to_dict(),
            (load_json(_json), load_json(_json_sol)),
        ]
