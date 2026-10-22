
import streamlit as st
import pandas as pd

from src.agent import validate_problem, describe_agent
from src.search import run_search
from src.csp import solve_csp
from src.knowledge_base import (
    check_schedule,
    query_capacity,
    query_availability,
)

st.set_page_config(
    page_title="Campus Energy Scheduling",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Campus Energy Scheduling")
st.caption(
    "AI-powered scheduling using UCS, A*, CSP and logic-based inference"
)

st.markdown(
    "Enter your campus details below and click **Generate Schedule**. "
    "The system will calculate a schedule using the data you provide."
)


def clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def equipment_list(value):
    text = clean_text(value)
    return [x.strip() for x in text.split(",") if x.strip()]


def parse_unavailable(text):
    pairs = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        parts = [part.strip() for part in line.split(",", 1)]
        if len(parts) != 2 or not all(parts):
            raise ValueError(
                f"Unavailable entry on line {line_number} must be "
                "'Room name,Time slot'."
            )

        pairs.append({"room": parts[0], "slot": parts[1]})

    return pairs


def build_problem(room_df, activity_df, slots_text, unavailable_text):
    rooms = []

    for _, row in room_df.iterrows():
        name = clean_text(row["Room"])
        if not name:
            continue

        rooms.append({
            "name": name,
            "capacity": int(row["Capacity"]),
            "equipment": equipment_list(row["Equipment"]),
            "energy_cost": float(row["Energy cost"]),
        })

    activities = []

    for _, row in activity_df.iterrows():
        name = clean_text(row["Activity"])
        if not name:
            continue

        activity = {
            "name": name,
            "students": int(row["Students"]),
            "equipment": equipment_list(row["Required equipment"]),
        }

        fixed_slot = clean_text(row["Fixed slot"])
        if fixed_slot:
            activity["fixed_slot"] = fixed_slot

        activities.append(activity)

    slots = [
        slot.strip()
        for slot in slots_text.split(",")
        if slot.strip()
    ]

    problem = {
        "rooms": rooms,
        "activities": activities,
        "slots": slots,
        "unavailable": parse_unavailable(unavailable_text),
        "energy_costs": {},
    }

    validate_problem(problem)

    for room in rooms:
        if room["energy_cost"] < 0:
            raise ValueError("Energy costs cannot be negative.")

    return problem


def show_schedule(result):
    if not result.get("success"):
        st.error(result.get("message", "No valid schedule found."))
        st.write("Search nodes expanded:", result.get("expanded", "N/A"))
        return

    schedule = result.get("schedule", result.get("assignments", []))

    st.success("A complete schedule was found.")
    c1, c2 = st.columns(2)

    c1.metric("Total energy cost", result.get("total_cost", 0))
    c2.metric("Activities scheduled", len(schedule))

    st.dataframe(
        pd.DataFrame(schedule),
        width="stretch",
        hide_index=True,
    )

    if "expanded" in result:
        st.caption(f"Search nodes expanded: {result['expanded']}")

    if "backtracks" in result:
        st.caption(f"CSP backtracks: {result['backtracks']}")


# -------------------- INPUT FORM --------------------

st.header("1. Enter Campus Details")

with st.form("campus_input_form"):
    st.subheader("Rooms")

    st.caption(
        "Enter one room per row. Equipment should be comma-separated, "
        "for example: projector,computers."
    )

    room_df = st.data_editor(
        pd.DataFrame([
            {
                "Room": "Room A",
                "Capacity": 30,
                "Equipment": "projector",
                "Energy cost": 8.0,
            },
            {
                "Room": "Computer Lab",
                "Capacity": 20,
                "Equipment": "computers,projector",
                "Energy cost": 12.0,
            },
            {
                "Room": "Room B",
                "Capacity": 40,
                "Equipment": "projector",
                "Energy cost": 6.0,
            },
        ]),
        num_rows="dynamic",
        width="stretch",
        key="rooms_editor",
        column_config={
            "Room": st.column_config.TextColumn(required=True),
            "Capacity": st.column_config.NumberColumn(
                min_value=0, step=1, required=True
            ),
            "Equipment": st.column_config.TextColumn(),
            "Energy cost": st.column_config.NumberColumn(
                min_value=0.0, step=1.0, required=True
            ),
        },
    )

    st.subheader("Activities")

    activity_df = st.data_editor(
        pd.DataFrame([
            {
                "Activity": "AI Lecture",
                "Students": 25,
                "Required equipment": "projector",
                "Fixed slot": "",
            },
            {
                "Activity": "Programming Lab",
                "Students": 18,
                "Required equipment": "computers",
                "Fixed slot": "11:00",
            },
            {
                "Activity": "Project Discussion",
                "Students": 15,
                "Required equipment": "",
                "Fixed slot": "",
            },
        ]),
        num_rows="dynamic",
        width="stretch",
        key="activities_editor",
        column_config={
            "Activity": st.column_config.TextColumn(required=True),
            "Students": st.column_config.NumberColumn(
                min_value=0, step=1, required=True
            ),
            "Required equipment": st.column_config.TextColumn(),
            "Fixed slot": st.column_config.TextColumn(
                help="Leave blank if the activity is flexible."
            ),
        },
    )

    st.subheader("Time Slots and Availability")

    slots_text = st.text_input(
        "Available time slots",
        value="09:00, 11:00, 14:00",
        help="Separate time slots with commas.",
    )

    unavailable_text = st.text_area(
        "Unavailable room/time combinations",
        value="Room A,11:00",
        help=(
            "Enter one blocked combination per line, in the format "
            "'Room name,Time slot'. Leave empty if none."
        ),
        height=90,
    )

    submitted = st.form_submit_button(
        "⚡ Generate Schedule",
        type="primary",
        width="stretch",
    )


# -------------------- PROCESS INPUT --------------------

if submitted:
    try:
        problem = build_problem(
            room_df,
            activity_df,
            slots_text,
            unavailable_text,
        )

        st.session_state["campus_problem"] = problem

    except (ValueError, TypeError, KeyError) as error:
        st.session_state.pop("campus_problem", None)
        st.error(f"Please check your input: {error}")


# -------------------- RESULTS --------------------

if "campus_problem" in st.session_state:
    problem = st.session_state["campus_problem"]

    st.divider()
    st.header("2. Scheduling Results")

    with st.spinner("Running search algorithms and CSP..."):
        ucs_result = run_search(problem, "ucs")
        astar_result = run_search(problem, "astar")
        csp_result = solve_csp(problem)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Best Schedule",
        "UCS vs A*",
        "CSP Solver",
        "Logic & PEAS",
    ])

    with tab1:
        st.subheader("A* Schedule")
        show_schedule(astar_result)

        if not astar_result.get("success"):
            st.info("Showing the CSP result as an alternative.")
            show_schedule(csp_result)

        chosen_schedule = (
            astar_result.get("schedule", [])
            if astar_result.get("success")
            else csp_result.get("assignments", [])
        )

        if chosen_schedule:
            validation = check_schedule(problem, chosen_schedule)

            st.subheader("Schedule Validation")
            if validation["valid"]:
                st.success("All checked constraints are satisfied.")
            else:
                st.error("The schedule has constraint violations.")
                for error in validation["errors"]:
                    st.write(f"- {error}")

            with st.expander("View validation facts"):
                for fact in validation["facts"]:
                    st.write(fact)

    with tab2:
        st.subheader("Uniform Cost Search vs A*")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Uniform Cost Search (UCS)**")
            show_schedule(ucs_result)

        with col2:
            st.markdown("**A* Search**")
            show_schedule(astar_result)

        if ucs_result.get("success") and astar_result.get("success"):
            st.subheader("Comparison")
            comparison = pd.DataFrame([
                {
                    "Algorithm": "UCS",
                    "Total cost": ucs_result["total_cost"],
                    "Nodes expanded": ucs_result["expanded"],
                },
                {
                    "Algorithm": "A*",
                    "Total cost": astar_result["total_cost"],
                    "Nodes expanded": astar_result["expanded"],
                },
            ])
            st.dataframe(
                comparison, width="stretch", hide_index=True
            )

            st.caption(
                "Both algorithms should find the same minimum cost. "
                "The number of expanded nodes can differ."
            )

    with tab3:
        st.subheader("Constraint Satisfaction Problem")
        st.write(
            "The CSP solver uses backtracking, minimum remaining values "
            "(MRV), and forward checking."
        )
        show_schedule(csp_result)

        with st.expander("View backtracking trace"):
            for step in csp_result.get("trace", []):
                st.write(step)

    with tab4:
        st.subheader("CO1: Intelligent Agent (PEAS)")

        for key, value in describe_agent().items():
            st.markdown(f"**{key}:** {value}")

        st.divider()
        st.subheader("CO4: Logic-Based Knowledge Base")

        activity_names = [
            a["name"] for a in problem["activities"]
        ]
        room_names = [r["name"] for r in problem["rooms"]]

        left, right = st.columns(2)

        with left:
            st.markdown("**Query 1: Room capacity**")
            selected_activity = st.selectbox(
                "Select activity",
                activity_names,
                key="logic_activity",
            )
            selected_room = st.selectbox(
                "Select room",
                room_names,
                key="logic_room",
            )

            if st.button("Check capacity"):
                answer = query_capacity(
                    problem, selected_activity, selected_room
                )

                if answer["answer"]:
                    st.success("The room has sufficient capacity.")
                else:
                    st.warning(
                        "The room cannot accommodate this activity, "
                        "or the selected names are invalid."
                    )

                for line in answer["trace"]:
                    st.write(line)

        with right:
            st.markdown("**Query 2: Room availability**")
            availability_room = st.selectbox(
                "Select room",
                room_names,
                key="availability_room",
            )
            availability_slot = st.selectbox(
                "Select time slot",
                problem["slots"],
                key="availability_slot",
            )

            if st.button("Check availability"):
                answer = query_availability(
                    problem, availability_room, availability_slot
                )

                if answer["answer"]:
                    st.success("The room is available.")
                else:
                    st.warning("The room/time combination is unavailable.")

                for line in answer["trace"]:
                    st.write(line)

    st.divider()
    st.caption(
        "Energy values are simulated relative units. This prototype "
        "demonstrates AI scheduling; it does not measure actual "
        "electricity consumption."
    )
else:
    st.info(
        "Edit the room and activity tables above, then click "
        "**Generate Schedule** to see your results."
    )
