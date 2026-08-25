"""The shipped consumer artifacts: the guard blocks what it claims, and only that.

`templates/settings/` is installed into a consumer's `.claude/` — it is law executed by the
harness on every Bash call, in every session, in that repo. A guard that blocks too little is a
prompt instruction wearing enforcement's clothes; one that blocks too much starves the driver.
Both directions are asserted, with the near-miss cases (a branch *named* like a default branch)
that a substring match would get wrong.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUARD = ROOT / "templates/settings/hooks/guard-push.py"
SETTINGS = ROOT / "templates/settings/settings.json"
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))


def run_guard(command: str):
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    return subprocess.run([sys.executable, str(GUARD)], input=json.dumps(event),
                          capture_output=True, text=True)


class GuardPush(unittest.TestCase):
    def assert_blocked(self, command, why=""):
        r = run_guard(command)
        self.assertEqual(r.returncode, 2, f"{command!r} must be blocked {why}: {r.stderr}")
        self.assertIn("guard-push:", r.stderr)

    def assert_allowed(self, command, why=""):
        r = run_guard(command)
        self.assertEqual(r.returncode, 0, f"{command!r} must be allowed {why}: {r.stderr}")

    def test_default_branch_pushes_are_blocked(self):
        self.assert_blocked("git push origin mainline")
        self.assert_blocked("git push origin main")
        self.assert_blocked("git push -u origin master")
        self.assert_blocked("git push origin HEAD:mainline", "a refspec's target is the push")
        self.assert_blocked("git push origin feature:refs/heads/main")

    def test_force_push_is_blocked_anywhere(self):
        self.assert_blocked("git push --force origin feature-x")
        self.assert_blocked("git push -f origin feature-x")
        self.assert_blocked("git push --force-with-lease origin feature-x")

    def test_merging_is_blocked(self):
        self.assert_blocked("gh pr merge 42 --squash")

    def test_ordinary_work_is_untouched(self):
        self.assert_allowed("git push origin the-heartbeat")
        self.assert_allowed("git push -u origin 84-brief-screen")
        self.assert_allowed("git push origin 42-mainline-fix",
                            "a branch NAMED like a default must not trip a token match")
        self.assert_allowed("git fetch origin mainline", "fetching the default is reading")
        self.assert_allowed("gh pr view 42")
        self.assert_allowed("ls -la")

    def test_compound_commands_are_examined_per_segment(self):
        self.assert_blocked("git add -A && git commit -m x && git push origin mainline")

    def test_malformed_input_never_blocks(self):
        r = subprocess.run([sys.executable, str(GUARD)], input="not json",
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                         "the guard must fail open on its own parse errors — a guard that "
                         "blocks on malformed input blocks everything when the harness "
                         "changes its event shape")


class ShippedArtifacts(unittest.TestCase):
    def test_settings_fragment_is_valid_and_wires_the_shipped_guard(self):
        d = json.loads(SETTINGS.read_text(encoding="utf-8"))
        commands = [h["command"]
                    for m in d["hooks"]["PreToolUse"] for h in m["hooks"]]
        self.assertTrue(any("guard-push.py" in c for c in commands),
                        "the fragment must wire the guard this directory ships")
        for c in commands:
            name = c.split("/")[-1].strip('"')
            self.assertTrue((GUARD.parent / name).exists(),
                            f"fragment references {name}, which templates/settings/hooks does "
                            "not ship — a wired-but-absent hook fails every Bash call")

    def test_guard_compiles_alone(self):
        r = subprocess.run([sys.executable, "-m", "py_compile", str(GUARD)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_every_skill_carries_name_and_description(self):
        self.assertTrue(SKILLS, "skills/ ships at least one skill")
        for p in SKILLS:
            head = p.read_text(encoding="utf-8").split("---")[1]
            self.assertRegex(head, r"(?m)^name: \S+", p.name)
            self.assertRegex(head, r"(?m)^description: \S+", p.name)
