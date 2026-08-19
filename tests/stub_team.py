"""The scripted `team` module hooks import under test.

Pure text helpers are IMPORTED FROM THE REAL team.py so they cannot drift;
everything that talks to GitHub is env-scripted and records to CALLS_FILE."""
import importlib.util
import json
import os
import subprocess
import sys

_spec = importlib.util.spec_from_file_location(
    "_real_team", os.path.join(os.environ["HOOKS_DIR"], "team.py"))
_real = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_real)

REPO = os.environ.get("REPO", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")

branch_line = _real.branch_line
role_stamp = _real.role_stamp
story_from_branch = _real.story_from_branch
titled_epic = _real.titled_epic
titled_spike = _real.titled_spike
titled_bug = _real.titled_bug
scrub = _real.scrub


def _record(kind, args):
    with open(os.environ["CALLS_FILE"], "a") as fh:
        fh.write(json.dumps({"kind": kind, "args": [str(a) for a in args]}) + "\n")


def _issues():
    return json.loads(os.environ.get("STUB_ISSUES", "{}"))


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def warn(message):
    print(f"::warning::{message}")


def issue(number, *fields):
    data = _issues().get(str(number), {})
    if "labels" in fields or not fields:
        data.setdefault("labels", [])
        data["labels"] = [{"name": n} if isinstance(n, str) else n for n in data["labels"]]
    return data


def issue_body(number):
    return _issues().get(str(number), {}).get("body", "")


def issue_state(number):
    return _issues().get(str(number), {}).get("state", "OPEN")


def sub_issues(number):
    return _issues().get(str(number), {}).get("kids", [])


def parent(number):
    return _issues().get(str(number), {}).get("parent")


def kind(number, data=None, body=None):
    return _issues().get(str(number), {}).get("kind", "story")


def is_epic(number):
    return kind(number) == "epic"


def gh(*args, check=False):
    _record("gh", args)
    joined = " ".join(map(str, args))
    for needle in json.loads(os.environ.get("STUB_GH_FAIL", "[]")):
        if needle in joined:
            return None
    return ""


def gh_json(*args, check=False):
    _record("gh_json", args)
    joined = " ".join(map(str, args))
    if "defaultBranchRef" in joined:
        return {"defaultBranchRef": {"name": os.environ.get("STUB_DEFAULT", "mainline")}}
    if "git/ref/heads/" in joined:
        if os.environ.get("STUB_HEAD_SHA"):
            return {"object": {"sha": os.environ["STUB_HEAD_SHA"]}}
        return None
    if "issues?state=all" in joined:
        return json.loads(os.environ.get("STUB_LISTING", "[]"))
    if "/comments" in joined:
        return []
    if "pr" == str(args[0]) and "list" in joined:
        return json.loads(os.environ.get("STUB_PRS", "[]"))
    if "compare" in joined:
        return {"ahead_by": int(os.environ.get("STUB_AHEAD", "0"))}
    tail = str(args[-1]).rsplit("/", 1)[-1]
    if tail.isdigit():
        rec = _issues().get(tail, {})
        return {"id": int(tail) * 10, "pull_request": rec.get("pull_request")}
    return None


def authenticate_git():
    _record("auth", [])
    return True


def mark_complete(number):
    _record("mark_complete", [number])


def upsert_comment(number, marker, body):
    _record("upsert_comment", [number, body])
    return True


def append_to_comment(number, marker, section, header):
    _record("append_comment", [number, section])
    return True


def run_link():
    return ""


def run_footer():
    return ""
