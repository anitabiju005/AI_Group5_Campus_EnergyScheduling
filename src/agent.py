
import json
from pathlib import Path


def normalize_equipment(value):
    """Convert equipment input into a normalized set of names."""

    if value is None:
        return set()

    if isinstance(value, str):
        if value.strip().lower() in {
            "", "none", "no equipment", "leave blank", "n/a"
        }:
            return set()

        items = value.split(",")

    elif isinstance(value, (list, tuple, set)):
        items = list(value)

    else:
        return set()

    return {
        str(item).strip().lower()
        for item in items
        if str(item).strip()
        and str(item).strip().lower() not in {
            "none", "no equipment", "leave blank", "n/a"
        }
    }


def get_student_count(data):
    """Support both students and participants field names."""

    return int(data.get("students", data.get("participants", 0)) or 0)


def get_fixed_slot(activity):
    """Support common fixed-time field names."""

    return (
        activity.get("fixed_slot")
        or activity.get("fixed_time")
        or activity.get("time")
        or None
    )


def load_problem(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        problem = json.load(file)

    validate_problem(problem)
    return problem


def validate_problem(problem):
    required = {"rooms", "activities", "slots"}
    missing = required - problem.keys()

    if missing:
        raise ValueError(
            f"Missing fields: {', '.join(sorted(missing))}"
        )

    if not problem["rooms"]:
        raise ValueError("At least one room is required.")

    if not problem["activities"]:
        raise ValueError("At least one activity is required.")

    if not problem["slots"]:
        raise ValueError("At least one time slot is required.")

    room_names = [room["name"] for room in problem["rooms"]]
    activity_names = [
        activity["name"] for activity in problem["activities"]
    ]

    if len(room_names) != len(set(room_names)):
        raise ValueError("Room names must be unique.")

    if len(activity_names) != len(set(activity_names)):
        raise ValueError("Activity names must be unique.")

    room_set = set(room_names)
    slot_set = set(problem["slots"])

    for room in problem["rooms"]:
        if float(room.get("capacity", 0)) < 0:
            raise ValueError("Room capacity cannot be negative.")

        cost = float(room.get("energy_cost", 1))
        if cost < 0:
            raise ValueError("Energy costs must be non-negative.")

    for activity in problem["activities"]:
        if get_student_count(activity) < 0:
            raise ValueError("Student count cannot be negative.")

        fixed_slot = get_fixed_slot(activity)

        if fixed_slot and fixed_slot not in slot_set:
            raise ValueError(
                f"Unknown fixed slot '{fixed_slot}' for "
                f"{activity['name']}."
            )

    for item in problem.get("unavailable", []):
        if item["room"] not in room_set:
            raise ValueError(
                f"Unknown unavailable room: {item['room']}"
            )

        if item["slot"] not in slot_set:
            raise ValueError(
                f"Unknown unavailable slot: {item['slot']}"
            )

    for key, cost in problem.get("energy_costs", {}).items():
        if float(cost) < 0:
            raise ValueError(
                f"Energy cost for '{key}' cannot be negative."
            )


def get_legal_options(problem, activity):
    """
    Return legal (room, slot, cost) options for one activity.

    Supports:
    - students or participants
    - list or comma-separated equipment
    - blank / 'Leave blank' equipment
    - fixed_slot, fixed_time or time
    - unavailable room/time combinations
    """

    unavailable = {
        (item["room"], item["slot"])
        for item in problem.get("unavailable", [])
    }

    required_equipment = normalize_equipment(
        activity.get("equipment", [])
    )

    student_count = get_student_count(activity)
    fixed_slot = get_fixed_slot(activity)

    options = []

    for room in problem["rooms"]:

        # Check room capacity.
        capacity = int(room.get("capacity", 0))

        if capacity < student_count:
            continue

        # Check equipment compatibility.
        available_equipment = normalize_equipment(
            room.get("equipment", [])
        )

        if not required_equipment.issubset(available_equipment):
            continue

        # Check all permitted time slots.
        for slot in problem["slots"]:

            if fixed_slot and slot != fixed_slot:
                continue

            if (room["name"], slot) in unavailable:
                continue

            key = f"{activity['name']}|{room['name']}|{slot}"

            cost = float(
                problem.get("energy_costs", {}).get(
                    key,
                    room.get("energy_cost", 1)
                )
            )

            if cost < 0:
                raise ValueError(
                    "Energy costs must be non-negative."
                )

            options.append((room["name"], slot, cost))

    return options


def describe_agent():
    return {
        "Performance measure": (
            "Schedule every activity legally while minimizing energy cost."
        ),
        "Environment": (
            "Campus rooms, activities, equipment, time slots and "
            "room availability."
        ),
        "Actuators": (
            "Assign an activity to a room and a time slot."
        ),
        "Sensors": (
            "Read room capacity, equipment, participant count, fixed "
            "slots, unavailable combinations and energy costs."
        ),
        "Agent type": (
            "Goal-based, cost-aware scheduling agent."
        )
    }


def run_agent(problem, algorithm="astar"):
    from src.search import run_search
    from src.csp import solve_csp

    search_result = run_search(problem, algorithm)
    csp_result = solve_csp(problem)

    return {
        "agent": describe_agent(),
        "search": search_result,
        "csp": csp_result
    }
