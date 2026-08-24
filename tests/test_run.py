"""The dispatcher is only trustworthy if its verb set cannot drift from the directory.

`run.py` derives verbs from `hooks/*.py` at call time, so the thing to assert is the derivation
itself — every hook is a verb, the two non-verbs are excluded — plus the two behaviours a caller
leans on: an unknown verb fails naming the known set (E8: failing loudly is not failing
usefully), and a verb executes its script with the caller's env and returns the script's own
exit code.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"


def run(args, cwd=HOOKS, env=None):
    return subprocess.run(
        [sys.executable, str(HOOKS / "run.py"), *args],
        capture_output=True, text=True, cwd=cwd, env=env,
    )


class Dispatcher(unittest.TestCase):
    def test_every_hook_is_a_verb_and_the_non_verbs_are_not(self):
        listed = run(["--list"])
        self.assertEqual(listed.returncode, 0, listed.stderr)
        names = {line.split()[0] for line in listed.stdout.splitlines() if line.strip()}
        on_disk = {p.stem for p in HOOKS.glob("*.py")} - {"run", "team"}
        self.assertEqual(names, on_disk,
                         "the verb list must be exactly the hooks directory minus the library "
                         "and the dispatcher — a roster that drifts is the defect this derives "
                         "its way around")
        self.assertNotIn("team", names)
        self.assertNotIn("run", names)

    def test_an_unknown_verb_fails_naming_the_known_set(self):
        r = run(["no-such-verb"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown verb: no-such-verb", r.stderr)
        self.assertIn("delegate", r.stderr,
                      "the failure must name the known verbs, or the caller needs a second "
                      "command to learn what was available")

    def test_a_verb_runs_its_script_with_env_and_returns_its_exit_code(self):
        # A scratch copy with one fake verb, so the test exercises dispatch itself
        # rather than any real hook's behaviour.
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        shutil.copy(HOOKS / "run.py", tmp / "run.py")
        (tmp / "probe.py").write_text(
            '"""A probe verb."""\n'
            "import os, sys\n"
            "print(os.environ.get('PROBE_INPUT', 'missing'))\n"
            "sys.exit(7)\n",
            encoding="utf-8",
        )
        env = dict(os.environ, PROBE_INPUT="carried")
        r = subprocess.run(
            [sys.executable, str(tmp / "run.py"), "probe"],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 7, "the hook's own exit code must pass through")
        self.assertIn("carried", r.stdout, "the caller's env must reach the hook")
