from ..core import Experiment, Solution
from pytups import TupList
from cornflow_client.constants import (
    STATUS_UNDEFINED,
    SOLUTION_STATUS_FEASIBLE,
)


class Default(Experiment):
    def solve(self, options: dict) -> dict:
        teams = self.instance.get_teams().keys_tl()
        size = len(teams)
        slots = range((size - 1) * 2)

        # each team plays with the next team in the list.
        def get_rival_pos(team_pos, day):
            return (team_pos + day + 1) % size

        solution = TupList()
        for day in slots:
            for pos, team in enumerate(teams):
                rival_pos = get_rival_pos(pos, day)
                solution.append(dict(home=team, away=teams[rival_pos], slot=day))

        self.solution = Solution(dict(assignment=solution))
        return dict(status=STATUS_UNDEFINED, status_sol=SOLUTION_STATUS_FEASIBLE)
