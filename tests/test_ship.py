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

    def test_quoting_a_token_does_not_bypass_any_protection(self):
        """bash strips quotes before git ever sees the argument, so a quoted token executes
        identically — a tokenizer that is not shell-aware sees a different word and stands down.
        Every protection is asserted against both quote styles, in every position it matches on."""
        for q in ('"', "'"):
            self.assert_blocked(f"git push origin {q}mainline{q}", "the target was merely quoted")
            self.assert_blocked(f"git {q}push{q} origin mainline", "the verb was merely quoted")
            self.assert_blocked(f"git push origin HEAD:{q}mainline{q}", "the refspec target")
            self.assert_blocked(f"git push {q}--force{q} origin feature-x", "the flag")
            self.assert_blocked(f"gh pr {q}merge{q} 42", "the subcommand")
            self.assert_blocked(f"{q}gh{q} pr merge 42", "the program name")
            self.assert_blocked(f"{q}git{q} push origin mainline", "the program name")

    def test_the_command_is_found_past_prefixes_and_global_flags(self):
        """`git -C x push` and `gh -R o/r pr merge` are ordinary invocations, and a check that
        reads only the first two tokens or demands strict adjacency misses both."""
        self.assert_blocked("git -C /some/repo push origin mainline")
        self.assert_blocked("git -c user.name=x push --force origin feature-x")
        self.assert_blocked("gh -R matt-whitaker/claude-team pr merge 42")
        self.assert_blocked("env FOO=1 git push origin mainline")

    def test_the_trigger_words_do_not_fire_from_inside_an_argument(self):
        """The mirror-image failure: co-presence anywhere in the line is not an invocation. A
        report *about* the guard must be fileable, and describing a command is not running one."""
        self.assert_allowed(
            'gh issue create --title "guard bug" '
            '--body "reproduce with: gh pr merge 42, and git push origin mainline"',
            "an issue body quoting the commands it describes is not those commands")
        self.assert_allowed('git commit -m "explain why gh pr merge is blocked"')
        self.assert_allowed('echo "git push origin mainline"')
        self.assert_allowed("gh pr list --search 'merge'")

    def test_unbalanced_quotes_never_relax_a_check(self):
        """An unparseable line is not a licence. bash would reject it too, but the guard must
        not answer a tokenizer failure by standing down."""
        self.assert_blocked('git push origin "mainline', "an unclosed quote is not an escape")

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

    def test_guard_runs_alone(self):
        """Compiling is not running. `py_compile` accepts an annotation the interpreter then
        raises on (`int | None` before 3.10), and a guard that dies on import exits non-2 —
        which the harness reads as permission. The check has to execute it."""
        r = subprocess.run([sys.executable, str(GUARD)], input='{"tool_input":{"command":"ls"}}',
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "", "a clean run says nothing")

    def test_every_handoff_channel_has_a_named_reader_in_the_driver(self):
        """E4: every required output has a named reader. Two of the four channels reach an
        automated one; the other two reach nobody unless the driving session carries them, so
        the skill's routing table is where their reader is named. A channel added to the schema
        and not to that table is a channel with no reader at all — which is how the two that
        already existed went seventeen entries without being read."""
        schema = json.loads((ROOT / "schemas/handoff.json").read_text(encoding="utf-8"))
        channels = set(schema["properties"]) - {"commitMessage"}
        skill = (ROOT / "skills/take-on-story/SKILL.md").read_text(encoding="utf-8")
        section = skill.split("### Harvesting a handoff", 1)
        self.assertEqual(len(section), 2, "take-on-story must carry a harvest section")
        # The ROWS, not the prose around them: a channel discussed in a paragraph but absent
        # from the table has no stated action, and matching loosely lets that pass.
        rows = [ln for ln in section[1].splitlines()
                if ln.startswith("|") and "what you do with it" not in ln
                and set(ln) - set("|- ")]
        self.assertTrue(rows, "the harvest section must carry a routing table")
        routed = {c for c in channels if any(f"`{c}`" in r for r in rows)}
        self.assertEqual(routed, channels,
                         f"handoff channels with no row in the driver's routing table: "
                         f"{sorted(channels - routed)} — each is forced out of every author "
                         "and would reach no reader at all")

    def test_every_skill_carries_name_and_description(self):
        self.assertTrue(SKILLS, "skills/ ships at least one skill")
        for p in SKILLS:
            head = p.read_text(encoding="utf-8").split("---")[1]
            self.assertRegex(head, r"(?m)^name: \S+", p.name)
            self.assertRegex(head, r"(?m)^description: \S+", p.name)
