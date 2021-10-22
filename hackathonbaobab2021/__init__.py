import os
from typing import Dict, List
from cornflow_client import ApplicationCore, get_empty_schema
from .core import Instance, Experiment, Solution, Batch, ZipBatch
from .solver import Default


class SportsScheduling(ApplicationCore):
    name = "sports_scheduling"
    instance = Instance
    solution = Solution
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
    def test_cases(self) -> List[Dict]:
        path = os.path.join(os.path.dirname(__file__), "data/TestInstanceDemo.xml")
        return [Instance.from_xml(path).to_dict()]
