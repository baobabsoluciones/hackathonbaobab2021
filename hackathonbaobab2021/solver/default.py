from ..core import Experiment, Solution
from pytups import TupList
from cornflow_client.constants import (
    STATUS_UNDEFINED,
    SOLUTION_STATUS_FEASIBLE,
)
from itertools import permutations


class Default(Experiment):
    def solve(self, options: dict) -> dict:
        teams = self.instance.get_teams().keys_tl()
        size = len(teams)
        slots = self.instance.get_slots().keys_tl()
        matches_per_slot = size // 2

        def find_match(remaining: set, already_scheduled: set):
            for home, away in remaining:
                if home not in already_scheduled and away not in already_scheduled:
                    already_scheduled.add(home)
                    already_scheduled.add(away)
                    el = (home, away)
                    remaining.remove(el)
                    return el

        remaining = set(permutations(teams, 2))

        solution = TupList()
        for pos_slot, slot in enumerate(slots):
            already_scheduled = set()
            for pos_match in range(matches_per_slot):
                match = find_match(remaining, already_scheduled)
                solution.append(dict(home=match[0], away=match[1], slot=slot))

        self.solution = Solution(dict(assignment=solution))
        return dict(status=STATUS_UNDEFINED, status_sol=SOLUTION_STATUS_FEASIBLE)
