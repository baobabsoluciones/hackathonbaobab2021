# hackathon baobab 2021

## The problem

The following is a very succinct summary from the document found in `hackathonbaobab2021/data/OrganizationITC2021_V7.pdf`, which explains in detail everything about the problem, data format, etc.

We want to plan one on one matches between sports team that belong to a single league (we assume there's only one league). We call the complete set of matches a tournament. This tournament follows a double round-robin. This implies that every team plays against every other team two times: once in their home stadium, the other in the adversary's. As a result we have `(N - 1) x 2` matches per team, where `N` is the total number of teams. 

The planning horizon is divided in slots. Since we assume that each team plays exactly once per slot (i.e., this is a "time-constrained timetable"), we have `(N-1)x2` slots. We also assume an even number of teams.

There are several types of constraints that we briefly present here. For more details and examples, please refer to the original document cited above.

There are both soft and hard constraints. Soft ones are indicated with SOFT tag and include a PENALTY for each unit of violation. The unit of violation depends on the constraint. Hard are tagged as HARD and must be complied in order to have a valid solution.

### Objective function

We want to minimize the sum of soft constraints violations.

### Structure

If the timetable instance is "phased", then the first half of slots in the tournament is a complete round-robin and the second half is another complete round-robin. That is, Each pair of teams only sees each other once in each half, with their home-away status inverted between halfs.

### Capacity

> CA1 <CA1 teams="0" max="0" mode="H" slots="0" type="HARD"/>
Each team from teams plays at most max home games ( mode = "H") or away games
( mode = "A") during time slots in slots . Team 0 cannot play at home on time slot 0.
Each team in teams triggers a deviation equal to the number of home games ( mode = "H")
or away games ( mode = "A") in slots more than max .

> CA2 <CA2 teams1="0" min="0" max="1" mode1="HA" mode2="GLOBAL" teams2="1;2"
slots ="0;1;2" type="SOFT"/>
Each team in teams1 plays at most max home games ( mode1 = "H"), away games ( mode1 =
"A"), or games ( mode1 = "HA") against teams ( mode2 = "GLOBAL"; the only mode we
consider) in teams2 during time slots in slots . Team 0 plays at most one game against
4teams 1 and 2 during the first three time slots.
Each team in teams1 triggers a deviation equal to the number of home games ( mode1 =
"H"), away games ( mode1 = "A"), or games ( mode1 = "HA") against teams in teams2
during time slots in slots more than max .


> CA3 <CA3 teams1="0" max="2" mode1="HA" teams2="1;2;3" intp="3" mode2=
"SLOTS" type="SOFT"/>
Each team in teams1 plays at most max home games ( mode1 = "H"), away games ( mode1 =
"A"), or games ( mode1 = "HA") against teams in teams2 in each sequence of intp time
slots ( mode2 = "SLOTS"; the only mode we consider). Team 0 plays at most two consecu-
tive games against teams 1, 2, and 3.
Each team in teams1 triggers a deviation equal to the sum of the number of home games
( mode1 = "H"), away games ( mode1 = "A"), or games ( mode1 = "HA") against teams in
teams2 more than max for each sequence of intp time slots.

> CA4 <CA4 teams1="0;1" max="3" mode1="H" teams2="2,3" mode2="GLOBAL"
slots ="0;1" type="HARD"/>
Teams in teams1 play at most max home games ( mode1 = "H"), away games ( mode1 =
"A"), or games ( mode1 = "HA") against teams in teams2 during time slots in slots
( mode2 = "GLOBAL") or during each time slot in slots ( mode2 = "EVERY"). Teams
0 and 1 together play at most three home games against teams 2 and 3 during the first two
time slots.
The set slots ( mode2 = "GLOBAL") or each time slot in slots ( mode2 = "EVERY") trig-
gers a deviation equal to the number of games (i, j) ( mode1 = "H"), ( j, i) ( mode1 = "A"), or
(i, j) and ( j, i) ( mode1 = "HA") with i a team from teams1 and j a team from teams2 more
than max .

### Game

> GA1 <GA1 min="0" max="0" meetings="0,1;1,2;" slots="3" type="HARD"/>
At least min and at most max games from G = {(i 1 , j 1 ), (i 2 , j 2 ), . . . } take place during time
slots in slots . Game (0, 1) and (1, 2) cannot take place during time slot 3.
The set slots triggers a deviation equal to the number of games in meetings less than min
or more than max.
 
### Break constraints

> BR1 <BR1 teams="0" intp="0" mode2="HA" slots="1" type="HARD"/>
Each team in teams has at most intp home breaks ( mode2 = "H"), away breaks ( mode2 =
"A"), or breaks ( mode2 = "HA") during time slots in slots . Team 0 cannot have a break
on time slot 1.
Each team in teams triggers a deviation equal to the difference in the sum of home breaks,
away breaks, or breaks during time slots in slots more than max .

> BR2 <BR2 homeMode="HA" teams="0;1" mode2="LEQ" intp="2" slots="0;1;2;3" type="HARD
"/>
The sum over all breaks ( homeMode = "HA", the only mode we consider) in teams is no
more than ( mode2 = "LEQ", the only mode we consider) intp during time slots in slots .
Team 0 and 1 together do not have more than two breaks during the first four time slots.
The set teams triggers a deviation equal to the number of breaks in the set slots more than
intp .

### Fairness

> FA2 <FA2 teams="0;1;2" mode="H" intp="1" slots="0;1;2;3" type="HARD"/>
Each pair of teams in teams has a difference in played home games ( mode = "H", the only
mode we consider) that is not larger than intp after each time slot in slots . The difference
in home games played between the first three teams is not larger than 1 during the first four
time slots.
Each pair of teams in teams triggers a deviation equal to the largest difference in played
home games more than intp over all time slots in slots .

### Separation

> SE1 <SE1 teams="0;1" min="5" mode1="SLOTS" type="HARD"/>
Each pair of teams in teams has at least min time slots ( mode1 = "SLOTS", the only mode
we consider) between two consecutive mutual games. There are at least 5 time slots between
the mutual games of team 0 and 1.
Each pair of teams in teams triggers a deviation equal to the sum of the number of time
slots less than min or more than max for all consecutive mutual games.

## The instances

The instances for the problem are found here:

https://www.sportscheduling.ugent.be/ITC2021/instances.php

On the `data` directory of this repository we have copied a couple instances.

## The format

The original format for input and output is the RobinX XML format, explained [here](https://www.sportscheduling.ugent.be/RobinX/threeField.php). 
This format is used for most sports scheduling problems, which includes the ones in this repository.

To understand the format of the input data file, you can check how we parse it in python in the function `Instance.from_xml(path)` in the file`hackathonbaobab2021/core/instance.py`

We provide full I/O integration with the RobinX XML format for the Instance and Solution.

## The json-schema format

We have prepared our own json-schema format for the present hackathon to make it compatible with [cornflow](https://baobabsoluciones.github.io/cornflow-server/). The json-schema format is less ambitious than the XML and has only been tested with instances used in this variant of the sports scheduling problem.

As always, these schemas are found in the `hackathonbaobab2021/schemas` folder.

## The checkers

There is a [web checker in the site of the original challenge](https://www.sportscheduling.ugent.be/ITC2021/validator.php) where you can paste your solution and see the validations.

Alternatively, the organizers have kindly [shared the code of the checker in github](https://github.com/Robin-X/RobinX/) so it can be run locally (it has been tested in Linux exclusively).

Finally, we provide through the `Experiment.check_solution` method, the same validations as the original ones.

In case you find differences between validations, let us know. 

## Requisites and download

python>=3.6 and git are needed. All command line actions assume a Windows machine.

```bash
git clone git@github.com:baobabsoluciones/hackathonbaobab2021.git
```

## Installation

To install from source:

```
cd hackathonbaobab2021
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```

## How to add a new solver

These are the steps to add a solver and make it compatible with the command line and the python functions:

1. Add a file inside the `hackathonbaobab2021/solver` directory with a subclass of `hackathonbaobab2021.core.experiment.Experiment` that implements, at least, the `solve()` method *with the same argument and argument names*.
1. Your `solve` method needs to return a dictionary with the following format `dict(status=INTEGER, status_sol=INTEGER)`. The codes for the status and solution status are taken from `cornflow_client.constants`.
1. Your `solve` method also needs to store the best solution found in `self.solution`. It needs to be an instance of the `Solution` object.
1. Edit the `hackathonbaobab2021/solver/__init__.py` to import your solver and edit the `hackathonbaobab2021.SportsScheduling.solvers` property by giving your solver a name.
1. If the `requirements.txt` file is missing some package you need for your solver, add it to the list under `solvers`. Also edit the `setup.py` and add the dependency on `solvers` within the `extras_require` dictionary.

**Additional considerations**:

1. One way to see if the solver is correctly integrated is to test solving with it via the command line (see below).
2. Everything that your solver needs should be inside the `hackathonbaobab2021/solver` directory (you can put more than one file). Do not edit the files outside the `solver` directories with code from your solver!

## How to run tests

These tests are run also in github and test the smallest example with a `timelimit` of 2 s (check the `options` dictionary).
```
python -m unittest hackathonbaobab2021/tests/tests.py 
 ```

## Command line

The command line app has three main ways to use it.

### To execute instances

To get all possible commands just run:

    python hackathonbaobab2021/main.py solve-scenarios --help

## Using python API

We use the following helper objects:

1. `Instance` to represent input data.
2. `Solution` to represent a solution.
3. `Experiment` to represent input data+solution.
4. `Algorithm(Experiment)` to represent a resolution approach.

An example of the last one (4) is found in `hackathonbaobab2021/solver/default.py`. It produces a solution that matches the schema, but not much more.

There are helper functions to read and write an instance and a solution to/from a file.

A small example of how to use the existing code is available in `hackathonbaobab2021/execution/test_script.py`.
Below an example:

```python
from hackathonbaobab2021 import SportsScheduling

# get xml file
path = "hackathonbaobab2021/data/TestInstanceDemo.xml"
# create the app
app = SportsScheduling()
# initialize an instance object
instance = app.instance.from_xml(path)
# get the default solver (in solver/default.py)
solver = app.get_solver("default")
# initialize the solver with the instance
exp = solver(instance=instance)
# solve the instance using the solver with a timeLimit of 2 seconds
exp.solve({'timeLimit': 2})
# The next functions do not depend on the solver and should not be overwritten:
# print the possible errors on the solution obtained from the solver
print(exp.check_solution())
# print the objective function of the solution
print(exp.get_objective())
```






