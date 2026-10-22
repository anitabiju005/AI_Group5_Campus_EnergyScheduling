
# Campus Energy Scheduling AI Prototype

**Group:** 5  
**Roll numbers:** 25–30  
TEAM MEMBERS:
ANGEL MARY ANTONY 	(CCE23CS025)
ANGEL ROSE PY 		(CCE23CS026)
ANITA BIJU 			(CCE23CS027)
ANNA GRACE RAJU 		(CCE23CS028)
ANNA SHAJI 			(CCE23CS029)
ANNA TOM 			(CCE23CS30)
**Topic:** Campus Energy Scheduling  
**SDGs:** SDG 7 – Affordable and Clean Energy; SDG 12 – Responsible Consumption and Production; SDG 13 – Climate Action

## Overview

This project schedules campus activities into rooms and time slots while
respecting capacity, equipment, fixed-time and room-availability constraints.
It uses simulated energy costs to compare scheduling choices.

## AI concepts

- CO1: Intelligent agent and PEAS description
- CO2: Uniform Cost Search (UCS) and A* search
- CO3: CSP using backtracking, MRV and forward checking
- CO4: Logic-based facts, rules, queries and inference traces

## Requirements

- Python 3.10 or newer
- No third-party Python packages required

## Run the program

Open a terminal in the project root.

### Interactive input

```bash
python -m src.main
```

Choose `1` to enter rooms, activities, slots and unavailable room/time pairs.

### Use the sample JSON

```bash
python -m src.main --file data/sample_campus.json
```

### Run tests

```bash
python -m unittest discover -s tests -v
```

## Input rules

- Room and activity names must be unique.
- Equipment names must match between rooms and activities.
- Fixed time slots must be listed among the available slots.
- Two activities cannot occupy the same room at the same time.
- Each activity must fit the room capacity and equipment requirements.
- Energy costs are illustrative relative units, not measured electricity use.

## Output

The program prints the PEAS description, UCS and A* schedules, their costs
and expanded-node counts, the CSP result, backtracking trace, and logic
query results.

## Limitations

This is a small educational prototype. It does not read real campus smart
meters, predict actual electricity consumption, or automatically control
building equipment. Its environmental benefit is represented through
simulated scheduling costs.
