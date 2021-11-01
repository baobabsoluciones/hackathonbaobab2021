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
        self.data["assignment"] = TupList(data["assignment"])

    @property
    def data(self) -> SuperDict:
        return self._data

    @data.setter
    def data(self, value: SuperDict):
        self._data = value

    def get_assignment(self) -> TupList:
        return self.data["assignment"]

    def get_home_away_slot(self):
        return self.get_assignment().take(["home", "away", "slot"])

    def get_match_slot(self):
        """
        for each match, the slot when it happened
        """
        assignment = self.get_assignment()
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
