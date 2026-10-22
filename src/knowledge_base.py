
def check_schedule(problem, schedule):
    rooms = {room["name"]: room for room in problem["rooms"]}
    activities = {
        activity["name"]: activity
        for activity in problem["activities"]
    }

    facts = []
    errors = []
    occupied = set()

    for item in schedule:
        activity_name = item["activity"]
        room_name = item["room"]
        slot = item["slot"]

        activity = activities[activity_name]
        room = rooms[room_name]

        facts.append(
            f"students({activity_name}, {activity['students']})"
        )
        facts.append(
            f"capacity({room_name}, {room['capacity']})"
        )

        # Rule 1: activity students must fit in the room.
        if activity["students"] <= room["capacity"]:
            facts.append(
                f"capacity_ok({activity_name}, {room_name})"
            )
        else:
            errors.append(
                f"{activity_name} exceeds {room_name}'s capacity."
            )

        # Rule 2: required equipment must be present.
        missing = set(activity.get("equipment", [])) - set(
            room.get("equipment", [])
        )
        if missing:
            errors.append(
                f"{room_name} lacks equipment for {activity_name}: "
                + ", ".join(sorted(missing))
            )
        else:
            facts.append(f"equipment_ok({activity_name}, {room_name})")

        # Rule 3: room and slot must not be blocked.
        if any(
            blocked["room"] == room_name and blocked["slot"] == slot
            for blocked in problem.get("unavailable", [])
        ):
            errors.append(f"{room_name} is unavailable at {slot}.")
        else:
            facts.append(f"available({room_name}, {slot})")

        key = (room_name, slot)
        if key in occupied:
            errors.append(
                f"Room conflict: {room_name} is assigned more than once "
                f"at {slot}."
            )
        occupied.add(key)

        if activity.get("fixed_slot") and activity["fixed_slot"] != slot:
            errors.append(
                f"{activity_name} must be scheduled at "
                f"{activity['fixed_slot']}."
            )

    return {
        "valid": not errors,
        "facts": facts,
        "errors": errors
    }


def query_capacity(problem, activity_name, room_name):
    activities = {
        a["name"]: a for a in problem["activities"]
    }
    rooms = {r["name"]: r for r in problem["rooms"]}

    if activity_name not in activities or room_name not in rooms:
        return {
            "answer": False,
            "trace": ["Query failed: unknown activity or room."]
        }

    students = activities[activity_name]["students"]
    capacity = rooms[room_name]["capacity"]

    trace = [
        f"Fact: students({activity_name}, {students})",
        f"Fact: capacity({room_name}, {capacity})",
        "Rule: capacity_ok(A, R) if students(A, N), "
        "capacity(R, C), and N <= C.",
        f"Inference: {students} <= {capacity} is "
        f"{students <= capacity}."
    ]

    return {
        "answer": students <= capacity,
        "trace": trace
    }


def query_availability(problem, room_name, slot):
    room_exists = any(
        room["name"] == room_name for room in problem["rooms"]
    )
    slot_exists = slot in problem["slots"]

    blocked = any(
        item["room"] == room_name and item["slot"] == slot
        for item in problem.get("unavailable", [])
    )

    available = room_exists and slot_exists and not blocked

    return {
        "answer": available,
        "trace": [
            f"Fact: room_exists({room_name}) = {room_exists}",
            f"Fact: slot_exists({slot}) = {slot_exists}",
            f"Fact: blocked({room_name}, {slot}) = {blocked}",
            "Rule: available(R, T) if room_exists(R), slot_exists(T), "
            "and not blocked(R, T).",
            f"Inference: available = {available}."
        ]
    }
