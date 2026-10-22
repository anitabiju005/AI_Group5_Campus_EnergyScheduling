
import argparse
import json

from src.agent import load_problem, validate_problem, run_agent
from src.knowledge_base import (
    check_schedule,
    query_capacity,
    query_availability
)


def ask_int(prompt, minimum=0):
    while True:
        try:
            value = int(input(prompt))
            if value >= minimum:
                return value
            print(f"Enter a number greater than or equal to {minimum}.")
        except ValueError:
            print("Enter a valid whole number.")


def ask_list(prompt):
    value = input(prompt).strip()
    return [item.strip() for item in value.split(",") if item.strip()]


def interactive_problem():
    print("\n=== Campus Energy Scheduling: Enter Your Scenario ===")

    rooms = []
    room_count = ask_int("Number of rooms: ", 1)

    for i in range(room_count):
        print(f"\nRoom {i + 1}")
        name = input("Room name: ").strip()
        capacity = ask_int("Maximum student capacity: ", 0)
        equipment = ask_list(
            "Equipment (comma-separated, or press Enter for none): "
        )
        energy = ask_int("Energy cost per use (relative units): ", 0)

        rooms.append({
            "name": name,
            "capacity": capacity,
            "equipment": equipment,
            "energy_cost": energy
        })

    activities = []
    activity_count = ask_int("\nNumber of activities: ", 1)

    for i in range(activity_count):
        print(f"\nActivity {i + 1}")
        name = input("Activity name: ").strip()
        students = ask_int("Number of students: ", 0)
        equipment = ask_list(
            "Required equipment (comma-separated, or Enter for none): "
        )
        fixed = input(
            "Fixed time slot (press Enter if flexible): "
        ).strip()

        activity = {
            "name": name,
            "students": students,
            "equipment": equipment
        }
        if fixed:
            activity["fixed_slot"] = fixed

        activities.append(activity)

    slots = ask_list(
        "\nTime slots (comma-separated, e.g. 09:00,11:00,14:00): "
    )

    unavailable = []
    count = ask_int("Number of unavailable room/time pairs: ", 0)

    for i in range(count):
        print(f"Unavailable pair {i + 1}")
        room = input("Room name (must match exactly): ").strip()
        slot = input("Time slot (must match exactly): ").strip()
        unavailable.append({"room": room, "slot": slot})

    problem = {
        "rooms": rooms,
        "activities": activities,
        "slots": slots,
        "unavailable": unavailable,
        "energy_costs": {}
    }
    validate_problem(problem)
    return problem


def print_schedule(result):
    if not result.get("success"):
        print("No schedule:", result.get("message", "Unsuccessful"))
        return

    print(f"\nAlgorithm: {result.get('algorithm', 'CSP')}")
    print(f"Total energy cost: {result.get('total_cost', 0)}")
    print(f"Search nodes expanded: {result.get('expanded', 'N/A')}")
    print("-" * 72)
    print(f"{'Activity':25} {'Room':20} {'Time':10} {'Cost':>8}")
    print("-" * 72)

    schedule = result.get("schedule", result.get("assignments", []))
    for item in schedule:
        print(
            f"{item['activity'][:25]:25} "
            f"{item['room'][:20]:20} "
            f"{item['slot']:10} "
            f"{item['energy_cost']:>8}"
        )
    print("-" * 72)


def run_demo(problem):
    print("\n=== PEAS: Intelligent Agent Description ===")
    result = run_agent(problem)

    for key, value in result["agent"].items():
        print(f"{key}: {value}")

    print("\n=== CO2: Search Comparison ===")
    ucs = run_agent_search(problem, "ucs")
    astar = run_agent_search(problem, "astar")
    print_schedule(ucs)
    print_schedule(astar)

    if ucs.get("success") and astar.get("success"):
        print("\nSearch comparison:")
        print(f"UCS cost: {ucs['total_cost']}")
        print(f"A* cost:  {astar['total_cost']}")
        print(f"UCS expanded nodes: {ucs['expanded']}")
        print(f"A* expanded nodes:  {astar['expanded']}")

    print("\n=== CO3: CSP with Backtracking and Forward Checking ===")
    csp = result["csp"]
    print_schedule(csp)
    print(f"Backtracks: {csp.get('backtracks', 0)}")

    for line in csp.get("trace", []):
        print("  ", line)

    schedule = (
        astar.get("schedule", [])
        if astar.get("success")
        else csp.get("assignments", [])
    )

    print("\n=== CO4: Knowledge Base and Inference ===")
    validation = check_schedule(problem, schedule)
    print("\nQuery 1: Is the generated schedule valid?")
    print("Answer:", validation["valid"])
    for fact in validation["facts"]:
        print("  FACT:", fact)
    for error in validation["errors"]:
        print("  ERROR:", error)

    first_activity = problem["activities"][0]
    first_room = problem["rooms"][0]

    print(
        f"\nQuery 2: Can {first_activity['name']} fit in "
        f"{first_room['name']}?"
    )
    query1 = query_capacity(
        problem, first_activity["name"], first_room["name"]
    )
    print("Answer:", query1["answer"])
    for line in query1["trace"]:
        print("  ", line)

    print(
        f"\nAdditional query: Is {first_room['name']} available "
        f"at {problem['slots'][0]}?"
    )
    query2 = query_availability(
        problem, first_room["name"], problem["slots"][0]
    )
    print("Answer:", query2["answer"])
    for line in query2["trace"]:
        print("  ", line)

    output = {
        "ucs": ucs,
        "astar": astar,
        "csp": csp,
        "validation": validation
    }
    with open("results/latest_results.json", "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print("\nResults saved to results/latest_results.json")


def run_agent_search(problem, algorithm):
    from src.search import run_search
    return run_search(problem, algorithm)


def main():
    parser = argparse.ArgumentParser(
        description="Campus Energy Scheduling AI Prototype"
    )
    parser.add_argument(
        "--file",
        help="Path to a campus JSON input file."
    )
    args = parser.parse_args()

    try:
        if args.file:
            problem = load_problem(args.file)
        else:
            mode = input(
                "Choose input mode: 1 = enter data, 2 = sample JSON: "
            ).strip()

            if mode == "2":
                problem = load_problem("data/sample_campus.json")
            else:
                problem = interactive_problem()

        run_demo(problem)

    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        print(f"\nInput error: {error}")


if __name__ == "__main__":
    main()
