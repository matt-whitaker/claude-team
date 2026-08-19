import unittest
from harness import GitFixture, HookCase


class CaptureFailure(HookCase):
    def capture(self, fx, **extra):
        env = {"ISSUE": "1094", "GITHUB_RUN_ID": "99", "GITHUB_RUN_ATTEMPT": "1",
               "MODEL_FAILED": "true", "GH_TOKEN": "t", "STUB_ISSUES": {}}
        env.update(extra)
        return self.run_hook("capture-failure.py", env, cwd=fx.wc)

    def test_a_run_that_produced_nothing_creates_no_branch(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1094-run")
        r = self.capture(fx)
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("failure/1094-99-1", fx.origin_branches())
        self.assertIn("nothing to recover", " ".join(
            c["args"][1] for c in r.calls if c["kind"] == "append_comment"))

    def test_real_work_is_captured_to_a_failure_ref(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1094-run")
        fx.commit("w.txt", "unlanded work")
        r = self.capture(fx)
        self.assertEqual(r.returncode, 0)
        self.assertIn("failure/1094-99-1", fx.origin_branches())
        self.assertIn("captured to failure/1094-99-1", r.stdout)

    def test_uncommitted_work_is_committed_then_captured(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1094-run")
        (fx.wc / "dirty.txt").write_text("uncommitted\n")
        r = self.capture(fx)
        self.assertIn("failure/1094-99-1", fx.origin_branches())
        self.assertIn("committed the uncommitted remainder", r.stdout)

    def test_it_never_fails_the_run(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1094-run")
        fx.commit("w.txt", "work")
        r = self.capture(fx, STUB_GH_FAIL=["comments"])
        self.assertEqual(r.returncode, 0)

    def test_divergence_note_the_zero_ahead_guard_needs_origin_head(self):
        fx = GitFixture(self._tmp)
        fx.checkout_new("1094-run")
        fx.git("remote", "set-head", "origin", "-d")
        r = self.capture(fx)
        self.assertEqual(r.returncode, 0)
        self.assertIn("failure/1094-99-1", fx.origin_branches())


if __name__ == "__main__":
    unittest.main()
