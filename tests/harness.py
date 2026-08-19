from __future__ import annotations
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"
STUB = pathlib.Path(__file__).resolve().parent / "stub_team.py"


class HookCase(unittest.TestCase):
    """Runs a hook in a scratch dir with the stub `team` beside it.

    The stub sits NEXT TO the hook because Python resolves imports from the
    script's own directory before PYTHONPATH — a stub placed only on PYTHONPATH
    is silently shadowed by the real team.py."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def scratch(self, hook: str) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(dir=self._tmp))
        shutil.copy(HOOKS / hook, d / hook)
        shutil.copy(STUB, d / "team.py")
        return d

    def run_hook(self, hook: str, env: dict, cwd: pathlib.Path | None = None):
        d = self.scratch(hook)
        calls = d / "calls.jsonl"
        out = d / "github_output.txt"
        out.write_text("")
        full = {
            **os.environ,
            "HOOKS_DIR": str(HOOKS),
            "CALLS_FILE": str(calls),
            "GITHUB_OUTPUT": str(out),
            "REPO": env.pop("REPO", "o/r"),
            **{k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v)) for k, v in env.items()},
        }
        result = subprocess.run(
            ["python3", str(d / hook)],
            capture_output=True, text=True, env=full, cwd=cwd or d,
        )
        result.calls = [json.loads(l) for l in calls.read_text().splitlines()] if calls.exists() else []
        result.outputs = dict(
            line.split("=", 1) for line in out.read_text().splitlines() if "=" in line
        )
        return result

    def calls_matching(self, result, *needles):
        return [c for c in result.calls if all(n in " ".join(map(str, c["args"])) for n in needles)]


class GitFixture:
    """A bare origin plus a working clone, with a default branch named mainline."""

    def __init__(self, tmp: str):
        self.dir = pathlib.Path(tempfile.mkdtemp(dir=tmp))
        self.origin = self.dir / "origin.git"
        self.wc = self.dir / "wc"
        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.wc)],
                       check=True, capture_output=True)
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        (self.wc / "a.txt").write_text("a\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "c1")
        self.git("branch", "-M", "mainline")
        self.git("push", "-q", "origin", "mainline")
        self.git("remote", "set-head", "origin", "mainline")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.wc, check=check,
                              capture_output=True, text=True)

    def origin_git(self, *args):
        return subprocess.run(["git", *args], cwd=self.origin,
                              capture_output=True, text=True)

    def push_branch(self, name: str, at: str = "mainline"):
        self.git("push", "-q", "origin", f"{at}:{name}")

    def commit(self, filename: str, message: str):
        (self.wc / filename).write_text(message + "\n")
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def checkout_new(self, name: str, at: str | None = None):
        args = ["checkout", "-q", "-b", name] + ([at] if at else [])
        self.git(*args)

    def origin_branches(self):
        r = self.origin_git("for-each-ref", "--format=%(refname:short)")
        return r.stdout.split()

    def ahead_of_mainline(self, ref: str) -> int:
        self.git("fetch", "-q", "origin")
        r = self.git("rev-list", "--count", f"origin/mainline..origin/{ref}", check=False)
        return int(r.stdout.strip() or -1)
