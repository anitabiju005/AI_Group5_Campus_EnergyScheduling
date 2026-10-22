
from src.agent import get_legal_options


def solve_csp(problem, debug=True):
    """
    Solve the campus scheduling problem using CSP.

    Features:
    - MRV: Select the unassigned activity with the fewest options.
    - Forward checking: Remove room/time conflicts from remaining domains.
    - Backtracking: Undo assignments when a conflict prevents completion.
    - Trace: Record assignments, failures and backtracking.
    """

    activities = problem.get("activities", [])

    if not activities:
        return {
            "success": False,
            "message": "No activities were provided.",
            "assignments": [],
            "total_cost": 0,
            "backtracks": 0,
            "trace": []
        }

    # Generate legal domains for every activity.
    domains = {}

    for activity in activities:
        name = activity.get("name", "Unknown activity")

        try:
            options = get_legal_options(problem, activity)
        except (KeyError, TypeError, ValueError) as exc:
            return {
                "success": False,
                "message": f"Could not generate options for {name}: {exc}",
                "assignments": [],
                "total_cost": 0,
                "backtracks": 0,
                "trace": []
            }

        domains[name] = list(options or [])

        if debug:
            print(f"\nActivity: {name}")
            print(f"Legal options: {len(domains[name])}")
            for option in domains[name]:
                print(f"  {option}")

    # Detect empty domains before beginning the search.
    empty = [
        name for name, domain in domains.items()
        if not domain
    ]

    if empty:
        return {
            "success": False,
            "message": "No legal options for: " + ", ".join(empty),
            "assignments": [],
            "total_cost": 0,
            "backtracks": 0,
            "trace": []
        }

    assignment = {}
    backtracks = 0
    expanded = 0
    trace = []

    def search(current_domains):
        nonlocal backtracks, expanded

        expanded += 1

        # All activities have been assigned.
        if len(assignment) == len(activities):
            return True

        # Minimum Remaining Values (MRV).
        unassigned = [
            activity["name"]
            for activity in activities
            if activity["name"] not in assignment
        ]

        variable = min(
            unassigned,
            key=lambda name: len(current_domains[name])
        )

        if debug:
            print(
                f"\nSelecting: {variable} "
                f"({len(current_domains[variable])} options)"
            )

        for option in current_domains[variable]:
            room, slot, cost = option

            # Reject a room/time combination already assigned.
            conflict = any(
                assigned_room == room and assigned_slot == slot
                for assigned_room, assigned_slot, _ in assignment.values()
            )

            if conflict:
                trace.append(
                    f"Conflict: {variable} cannot use "
                    f"{room} at {slot}"
                )
                continue

            assignment[variable] = option
            trace.append(
                f"Assign {variable} -> {room} at {slot}"
            )

            if debug:
                print(f"Assign {variable} -> {room} at {slot}")

            # Copy domains so failed branches can be safely undone.
            reduced = {
                name: list(domain)
                for name, domain in current_domains.items()
            }

            failed = False

            # Forward checking: remove the selected room/time
            # from every remaining activity's domain.
            for other in unassigned:
                if other == variable:
                    continue

                reduced[other] = [
                    candidate
                    for candidate in reduced[other]
                    if not (
                        candidate[0] == room
                        and candidate[1] == slot
                    )
                ]

                if not reduced[other]:
                    failed = True
                    trace.append(
                        f"Forward checking failed for {other}"
                    )

                    if debug:
                        print(
                            f"Forward checking failed for {other}"
                        )

                    break

            if not failed and search(reduced):
                return True

            # Undo the assignment when this branch fails.
            del assignment[variable]
            backtracks += 1

            trace.append(f"Backtrack from {variable}")

            if debug:
                print(f"Backtrack from {variable}")

        return False

    success = search(domains)

    # Return assignments in the original activity order.
    assignments = [
        {
            "activity": activity["name"],
            "room": assignment[activity["name"]][0],
            "slot": assignment[activity["name"]][1],
            "energy_cost": assignment[activity["name"]][2]
        }
        for activity in activities
        if activity["name"] in assignment
    ]

    total_cost = sum(
        item["energy_cost"] for item in assignments
    )

    if debug:
        print("\n--- CSP Result ---")
        print(f"Success: {success}")
        print(f"Expanded nodes: {expanded}")
        print(f"Backtracks: {backtracks}")
        print(f"Total energy cost: {total_cost}")

    return {
        "success": success,
        "assignments": assignments,
        "total_cost": total_cost,
        "expanded": expanded,
        "backtracks": backtracks,
        "trace": trace,
        "message": (
            "A complete schedule was found."
            if success
            else "No complete legal schedule exists."
        )
    }
