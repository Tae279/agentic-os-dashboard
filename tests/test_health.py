"""Run: .venv/bin/python -m unittest tests.test_health -v"""
import unittest

import health

H = 3600


class EvaluateLogin(unittest.TestCase):
    def test_fresh_probe_passes(self):
        st = {"probe": {"ts": 1000, "ok": True}}
        self.assertEqual(health.evaluate_login(st, {"loggedIn": True}, now=1000 + H)["status"], "pass")

    def test_logged_out_fails_even_with_good_probe(self):
        st = {"probe": {"ts": 1000, "ok": True}}
        self.assertEqual(health.evaluate_login(st, {"loggedIn": False}, now=1000 + H)["status"], "fail")

    def test_loggedin_true_but_run_auth_error_fails(self):  # the 2026-09-03 case
        st = {"probe": {"ts": 1000, "ok": True}, "run_auth_error": {"ts": 2000, "detail": "OAuth session expired"}}
        self.assertEqual(health.evaluate_login(st, {"loggedIn": True}, now=3000)["status"], "fail")

    def test_probe_auth_failure_fails(self):
        st = {"probe": {"ts": 1000, "ok": False, "auth_error": True, "detail": "x"}}
        self.assertEqual(health.evaluate_login(st, None, now=1500)["status"], "fail")

    def test_probe_network_failure_only_warns(self):
        st = {"probe": {"ts": 1000, "ok": False, "auth_error": False, "detail": "timeout"}}
        self.assertEqual(health.evaluate_login(st, None, now=1500)["status"], "warn")

    def test_stale_or_missing_probe_warns(self):
        self.assertEqual(health.evaluate_login({}, None, now=5000)["status"], "warn")
        st = {"probe": {"ts": 1000, "ok": True}}
        self.assertEqual(health.evaluate_login(st, None, now=1000 + 27 * H)["status"], "warn")

    def test_auth_error_regex(self):
        for t in ("Failed to authenticate: OAuth session expired", "Please run /login", "API Error: 401"):
            self.assertTrue(health.AUTH_ERROR_RE.search(t), t)
        self.assertFalse(health.AUTH_ERROR_RE.search("ECONNRESET network down"))


class Alerts(unittest.TestCase):
    def chk(self, status):
        return [{"id": "web", "label": "หน้าเว็บ", "status": status, "detail": "ไม่ตอบ", "fix": "เปิดใหม่"}]

    def test_alert_once_then_quiet_then_remind_then_recover(self):
        st = {}
        self.assertEqual(len(health.plan_alerts(st, self.chk("fail"), now=0)), 1)
        self.assertEqual(health.plan_alerts(st, self.chk("fail"), now=H), [])           # no spam
        self.assertEqual(len(health.plan_alerts(st, self.chk("fail"), now=7 * H)), 1)   # reminder after 6h
        rec = health.plan_alerts(st, self.chk("pass"), now=8 * H)
        self.assertEqual(len(rec), 1)
        self.assertIn("กลับมาปกติ", rec[0])
        self.assertEqual(st["alerts"], {})

    def test_hold_suppresses_alert_right_after_restart(self):
        self.assertEqual(health.plan_alerts({}, self.chk("fail"), now=0, hold={"web"}), [])


class Heal(unittest.TestCase):
    def test_budget_caps_at_three_per_hour(self):
        st = {"heal_log": [{"ts": 100, "target": "api"}, {"ts": 200, "target": "api"}, {"ts": 300, "target": "api"}]}
        self.assertFalse(health._heal_allowed(st, "api", 400))
        self.assertTrue(health._heal_allowed(st, "web", 400))
        self.assertTrue(health._heal_allowed(st, "api", 100 + H + 1))


class Overall(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(health.overall([{"status": "pass"}, {"status": "warn"}]), "warn")
        self.assertEqual(health.overall([{"status": "warn"}, {"status": "fail"}]), "fail")
        self.assertEqual(health.overall([{"status": "pass"}, {"status": "skip"}]), "pass")


class NotifyOffSwitch(unittest.TestCase):
    def test_flag_file_blocks_line_push(self):
        import tempfile
        from pathlib import Path
        from unittest import mock

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "notify-off").touch()
            with mock.patch.object(health, "CACHE_DIR", Path(d)), \
                 mock.patch.object(health.urllib.request, "urlopen") as net:
                self.assertFalse(health._line_push("x"))
                net.assert_not_called()


if __name__ == "__main__":
    unittest.main()
