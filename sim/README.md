# AGV Simulator :tractor:
---

## Updates:
06/06/2022: 
- A new general algorithm is developed, collision is still expected.

21/03/2022: 
- Created `showMap.py` for anyone who wants to observe the map
- Change the prat of hardcoded, now should be working without hard coded parts 

15/03/2022: 
- queueing system in pickup/dropoff point is available!

09/03/2022: 
- Queueing System is available in dropoff point

03/03/2022: 
- A mess now
- Required to fix the AGV stopping before departure / approach when there is AGV nearby.

25/02/2022 (2):
- bug fixed 
- `fixedPickUpPoint`, `fixedDropOffPoint` and `idlePoint` can be auto-generated
- for replay, AGVs are now present the status in terms of color
- TOFIX: 
    - both AGVs are having the same drop-off point -> need prioritize
    - save points into json
    - load fix points from json
    - re-check idle points

25/02/2022 (1): 
- bug fixed
- code optimization
- remove unused variables

24/02/2022 (2):
- Code tidied 
- idlePoint changed to `config.ini` 
- fixed minor bug of `self.path` in `agv.py`
- added and changed some logics to methods for eaier read

24/02/2022 (1): 
- [FINALLY DONE] crash avoidance system.not the most efficient way, future improvements are needed.
- script untidied 
- note: the version on this day does not include from TRANSIT to TASKRECEIVED 
- next step: tidy the script

22/02/2022: 
- Still working on the algorithm... almost there

17/02/2022: 
- Still writing the crash avoidance algorithm since 26/01
- Added insturctions

10/02/2022: 
- Happy Lunar New Year!
- created direction matrix for checking direction conflicts (face to face)
- still making collison advisory system

26/01/2022: 
- refined variables
- add pick-up and drop-off point

12/01/2022:
- Added crashed site in `replay.py`
- Crash information is stored in `fms.py`
- When AGV is crashed, it will change status and stopped working
- replay speed variable

11/01/2022: 
- Refined `replay.py`
- `dev.py` can fully test with any given agv numbers (Added `mapper.generateRandomPoints()`)
- Added collision detection system
- collision is logged into .json

10/01/2022: 
- .ini config implemented, every setting is in-sync among different scripts
- Added memory_profiler for memory monitoring
- Fixed ratio problem in `replay.py`, an okay-to-show simple UI

07/01/2022: 
- Complete FMS infrastructure
- All modules (Scheduler, dispatcher and router) are customizable 
- AGV equips a state of path request from FMS (self.pathRequest)
- AGV path is now sent from FMS

03/01/2022: 
- Added `TaskGenerator`

23/12/2021: 
- Updated json record system
- Updated json replay system
- Built braking system
- Built remaining distance 

17/12/2021:
- Updated replay module.

17/12/2021:
- Added `README.md`

---
## Instructions (*OUTDATED)
### A. Simulation setup
1. Clone the repo via 
    a. https `git clone https://hkflair_admin@bitbucket.org/flairhk/p2-3-agv-fms.git` 
    b. ssh `git clone git@bitbucket.org:flairhk/p2-3-agv-fms.git`
<br/>
2. You can configure the simulator environment in `config.ini`
    The followings are the desciptions in `config.ini`:

| Parameters            | Description | Variable type  | Unit |default value |
| -------------         |---------------------------------  |:-----:   |:-----:|:-----:|
| **AGV**               |
| `numberOfAGV`         | Number of AGV                         | `int`   | devices | 6 |
| `agvSPD`              | Maximum speed of AGV                  | `float` | m/s     | 1.5 |
| `agvACL`              | Constant aceleration of AGV           | `float` | m/s^2^  | 1.5 |
| `agvSize`             | Physical size of an AGV as a 2D square| `float` | m       |0.24 |
| **MAP**               |
| `length`              | Number of nodes in terms of length    | `int`   | nodes   | 10 |
| `width`               | Number of nodes in terms of width     | `int`   | nodes   | 10 |
| `gridSize`            | Length between nodes                  | `float` | m       | 0.25 |
| **REPLAY**            |
| `filename`            | json filename                         | `string`| -       | position.json |
| `playbackSpeed`       | Animation playback speed              | `int`   | -       | 2 |
| **TASK**              |
| `fixedPickUpPoint`    | Specific nodes for pick-up            | `list`  | -       | [90,91,92,93,94,95,96,97,98,99]^1^|
| `fixedDropOffPoint`   | Specific nodes for drop-off           | `list`  | -       | [3,4,5,6]^2^|

    ^1^: the whole upper nodes of a 10 x 10 grid
    ^2^: the middle 4 nodes of a 10 x 10 grid
<br/>
3. Run `dev.py`
    All the logs will be shown during the simulation, you must let the simulation run completely to have a complete json log. Otherwise, the json will be incomplete.
    <br/>If you want to configure dispatch, scheduler or router algorithm, you can edit in `dispatcher.py`, `scheduler.py` and `router.py` respectively.
### B. Playback

After running the simulation, you can run `replay.py` to replay the simulation. 
Follow insturctions in prompt.

---
## Endless To-do-list:
- [x] Task generator 
- [ ] FMS   
    - [X] Router (path planning)
    - [X] Dispatcher
    - [X] Scheduler 
        - [ ] Priority System
    - [X] Crash system
    - [X] Traffic Control (Centralized traffic control) (remarks: very hard)
- [ ] AGV  
    - [x] 1. Brake (retard sytem)
    - [x] 2a. Traffic radar (TA) (Decentralized traffic control) (not prioritized )
    - [x] 2b. Auto reroute based on traffic condition (not prioritized )
    - [ ] turning system
- [x] large-scale agv implementation (>100)
- [x] config implmentation(.ini)
- [x] Task list generator
- [X] Replay module scaling
- [ ] Statistics
- [ ] Full UI (replay + statistics)
- [x] logging system


#### Known Problems:
- many