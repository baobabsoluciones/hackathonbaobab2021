from pytups import SuperDict

HOME = "H"
AWAY = "A"
SOFT = "SOFT"
HARD = "HARD"
GLOBAL = "GLOBAL"
EVERY = "EVERY"
status = SuperDict({HOME: "home", AWAY: "away"})

C_CLUSTER = SuperDict(
    separation="SeparationConstraints",
    capacity="CapacityConstraints",
    breaks="BreakConstraints",
    fairness="FairnessConstraints",
    game="GameConstraints",
)

C_CAT = SuperDict(
    CA1=["slots", "teams"],
    CA2=["slots", "teams1", "teams2"],
    CA3=["teams1", "teams2"],
    CA4=["teams1", "teams2", "slots"],
    GA1=["meetings", "slots"],
    BR1=["teams", "slots"],
    BR2=["slots", "teams"],
    SE1=["teams"],
    FA2=["teams", "slots"],
)
C_TUPLES = SuperDict(GA1=SuperDict(meetings=True))

_ID = "_id"
_CAT = "_cat"

INT_PROPS = ["min", "max", "intp", "penalty"]
