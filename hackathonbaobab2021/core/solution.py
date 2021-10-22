import os
from cornflow_client import SolutionCore
from cornflow_client.core.tools import load_json
from pytups import SuperDict, TupList


class Solution(SolutionCore):
    schema = load_json(
        os.path.join(os.path.dirname(__file__), "../schemas/solution.json")
    )

    def __init__(self, data: dict) -> None:
        super().__init__(data)
        data["assignment"] = TupList(data["assignment"])

    @property
    def data(self) -> SuperDict:
        return self._data

    @data.setter
    def data(self, value: SuperDict):
        self._data = value

    def get_assignment(self):
        return self.data["assignment"]
