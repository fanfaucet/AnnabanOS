import unittest

from fastapi.testclient import TestClient

from annaban_maritime.alignment.evaluator import evaluate_route
from annaban_maritime.api.main import app
from annaban_maritime.core.eta import estimate_eta
from annaban_maritime.core.routing import choose_best_route, score_route
from annaban_maritime.core.state import MaritimeState
from annaban_maritime.core.vessel import Vessel
from annaban_maritime.utils.geo import bearing, haversine


class MaritimeCoreTests(unittest.TestCase):
    def test_haversine_and_bearing_are_operational(self):
        distance = haversine(0, 0, 0, 1)
        self.assertAlmostEqual(distance, 111.19, places=1)
        self.assertAlmostEqual(bearing(0, 0, 0, 1), 90.0, places=1)

    def test_eta_estimate_includes_uncertainty_window(self):
        vessel = Vessel("imo-123", 0, 0, 10, 0.8, "medical")
        eta = estimate_eta(vessel, {"lat": 0, "lon": 1})
        self.assertGreater(eta["eta_hours"], 0)
        self.assertLess(eta["eta_lower"], eta["eta_hours"])
        self.assertGreater(eta["eta_upper"], eta["eta_hours"])

    def test_route_scoring_selects_shorter_lower_risk_route(self):
        state = MaritimeState(weather_risk=0.1, congestion=0.2, ecological_zone=0.0, priority=0.4)
        safer_score = score_route(100, state)
        worse_score = score_route(200, state)
        self.assertGreater(safer_score, worse_score)

        best = choose_best_route(
            [
                {"route_id": "long", "distance": 200},
                {"route_id": "short", "distance": 100},
            ],
            state,
        )
        self.assertEqual(best["route_id"], "short")
        self.assertIn("score", best)

    def test_alignment_rejects_excessive_risk_and_ecological_crossing(self):
        result = evaluate_route(
            {"ecological_zone_crossing": 0.9, "risk_score": 0.95},
            MaritimeState(weather_risk=0.2, congestion=0.1, ecological_zone=0.0, priority=0.0),
        )
        self.assertFalse(result["approved"])
        self.assertEqual(result["violations"], ["eco_violation", "safety_risk"])

    def test_fastapi_maritime_endpoints(self):
        client = TestClient(app)
        eta_response = client.post(
            "/maritime/eta",
            json={
                "vessel": {
                    "vessel_id": "imo-123",
                    "lat": 0,
                    "lon": 0,
                    "speed_knots": 10,
                    "fuel_level": 0.8,
                    "cargo_type": "medical",
                },
                "destination": {"lat": 0, "lon": 1},
            },
        )
        self.assertEqual(eta_response.status_code, 200)
        self.assertIn("eta_hours", eta_response.json())

        route_response = client.post(
            "/maritime/route_check",
            json={
                "route": {"ecological_zone_crossing": 0.2, "risk_score": 0.2},
                "state": {
                    "weather_risk": 0.2,
                    "congestion": 0.1,
                    "ecological_zone": 0.2,
                    "priority": 0.3,
                },
            },
        )
        self.assertEqual(route_response.status_code, 200)
        self.assertTrue(route_response.json()["approved"])


if __name__ == "__main__":
    unittest.main()
