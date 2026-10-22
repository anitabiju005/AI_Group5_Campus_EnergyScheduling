
import unittest

from src.agent import load_problem
from src.search import run_search
from src.csp import solve_csp
from src.knowledge_base import check_schedule, query_capacity


class CampusSchedulingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = load_problem("data/sample_campus.json")

    def test_ucs_finds_schedule(self):
        result = run_search(self.problem, "ucs")
        self.assertTrue(result["success"])

    def test_astar_finds_schedule(self):
        result = run_search(self.problem, "astar")
        self.assertTrue(result["success"])

    def test_search_costs_match(self):
        ucs = run_search(self.problem, "ucs")
        astar = run_search(self.problem, "astar")

        self.assertTrue(ucs["success"])
        self.assertTrue(astar["success"])
        self.assertEqual(ucs["total_cost"], astar["total_cost"])

    def test_csp_finds_valid_schedule(self):
        result = solve_csp(self.problem)
        self.assertTrue(result["success"])

        checked = check_schedule(
            self.problem, result["assignments"]
        )
        self.assertTrue(checked["valid"])

    def test_capacity_query(self):
        result = query_capacity(
            self.problem, "AI Lecture", "Room A"
        )
        self.assertTrue(result["answer"])

    def test_same_room_cannot_be_used_twice_at_same_time(self):
        schedule = [
            {
                "activity": "AI Lecture",
                "room": "Room A",
                "slot": "09:00",
                "energy_cost": 5
            },
            {
                "activity": "Project Discussion",
                "room": "Room A",
                "slot": "09:00",
                "energy_cost": 8
            }
        ]
        checked = check_schedule(self.problem, schedule)
        self.assertFalse(checked["valid"])


if __name__ == "__main__":
    unittest.main()
