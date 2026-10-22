
import heapq
import itertools

from src.agent import get_legal_options


def conflicts(option, assigned_options):
    """Check whether a room and time slot are already occupied."""
    room, slot, _ = option

    return any(
        other is not None
        and other[0] == room
        and other[1] == slot
        for other in assigned_options
    )


def run_search(problem, algorithm="astar", debug=True):
    """
    Schedule activities using Uniform Cost Search or A*.

    Each legal option must have the format:
        (room_name, time_slot, energy_cost)

    The problem must contain:
        problem["activities"]
    """

    algorithm = algorithm.lower()

    if algorithm not in {"ucs", "astar"}:
        raise ValueError("Algorithm must be 'ucs' or 'astar'.")

    activities = problem.get("activities", [])

    if not activities:
        return {
            "algorithm": algorithm.upper(),
            "success": False,
            "message": "No activities were provided.",
            "schedule": [],
            "total_cost": 0,
            "expanded": 0
        }

    # Generate legal room/time options for each activity.
    options = []

    for activity in activities:
        try:
            choices = get_legal_options(problem, activity)
        except (KeyError, TypeError, ValueError) as exc:
            return {
                "algorithm": algorithm.upper(),
                "success": False,
                "message": (
                    f"Could not generate options for "
                    f"{activity.get('name', 'Unknown activity')}: {exc}"
                ),
                "schedule": [],
                "expanded": 0
            }

        choices = list(choices or [])
        options.append(choices)

        if debug:
            print(f"\nActivity: {activity.get('name', 'Unknown')}")
            print(f"Legal options: {len(choices)}")
            for choice in choices:
                print(f"  {choice}")

    # Stop early if any activity has no legal options.
    for activity, choices in zip(activities, options):
        if not choices:
            return {
                "algorithm": algorithm.upper(),
                "success": False,
                "message": (
                    f"No legal room/time option for "
                    f"{activity['name']}. Check room capacity, "
                    "equipment, time slots and availability."
                ),
                "schedule": [],
                "expanded": 0
            }

    # Lower-bound estimate of the remaining energy cost.
    def heuristic(state):
        return sum(
            min(choice[2] for choice in options[i])
            for i, index in enumerate(state)
            if index == -1
        )

    # -1 means that the activity has not been scheduled.
    initial = tuple(-1 for _ in activities)
    counter = itertools.count()

    initial_priority = (
        heuristic(initial) if algorithm == "astar" else 0
    )

    frontier = [
        (initial_priority, 0, next(counter), initial)
    ]

    best_cost = {initial: 0}
    expanded = 0

    while frontier:
        _, cost_so_far, _, state = heapq.heappop(frontier)

        # Ignore outdated entries in the priority queue.
        if cost_so_far != best_cost.get(state):
            continue

        expanded += 1

        # A complete schedule has been found.
        if all(index != -1 for index in state):
            schedule = []

            for i, option_index in enumerate(state):
                room, slot, cost = options[i][option_index]

                schedule.append({
                    "activity": activities[i]["name"],
                    "room": room,
                    "slot": slot,
                    "energy_cost": cost
                })

            return {
                "algorithm": algorithm.upper(),
                "success": True,
                "message": "A complete schedule was found.",
                "schedule": schedule,
                "total_cost": cost_so_far,
                "expanded": expanded
            }

        # Select the first unscheduled activity.
        activity_index = state.index(-1)

        chosen_so_far = [
            None if index == -1 else options[i][index]
            for i, index in enumerate(state)
        ]

        # Try each legal room/time option.
        for option_index, option in enumerate(options[activity_index]):

            if conflicts(option, chosen_so_far):
                continue

            new_state = list(state)
            new_state[activity_index] = option_index
            new_state = tuple(new_state)

            new_cost = cost_so_far + option[2]

            # Keep only a lower-cost path to each state.
            if new_cost >= best_cost.get(
                new_state, float("inf")
            ):
                continue

            best_cost[new_state] = new_cost

            priority = new_cost

            if algorithm == "astar":
                priority += heuristic(new_state)

            heapq.heappush(
                frontier,
                (
                    priority,
                    new_cost,
                    next(counter),
                    new_state
                )
            )

    return {
        "algorithm": algorithm.upper(),
        "success": False,
        "message": (
            "No complete legal schedule exists. "
            "The available options conflict with each other."
        ),
        "schedule": [],
        "expanded": expanded
    }
