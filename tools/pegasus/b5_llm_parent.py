"""Durable login-side Claude parent for one B-5 v2 series."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

FORBIDDEN = ('CLAUDE_CODE_SUBAGENT_MODEL', 'CLAUDE_CODE_EFFORT_LEVEL',
             'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN',
             'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX')
FIELDS = ('job_id', 'workload', 'series', 'block', 'ledger_root', 'materials_root', 'session_id')


def read_config(path: Path) -> dict:
    config = json.loads(Path(path).read_text())
    for key in ("effect_checkout", "settings", "model", "template", "header", "resume", "manifest"):
        if not isinstance(config.get(key), str):
            raise ValueError(f"{key} must be a string")
    series = config.get("series")
    if not isinstance(series, list):
        raise ValueError("series must be a list")
    seen = set()
    for item in series:
        if not isinstance(item, dict) or any(key not in item for key in FIELDS):
            raise ValueError("series item missing field")
        job_id = item["job_id"]
        if not isinstance(job_id, str) or re.fullmatch(r"[A-Za-z0-9_-]+", job_id) is None:
            raise ValueError("invalid job_id")
        if job_id in seen:
            raise ValueError(f"duplicate job_id: {job_id}")
        seen.add(job_id)
    return config


def classify_exit(path: Path, rc: int) -> str:
    try:
        document = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return "failure"
    if document.get("is_error") is True and document.get("api_error_status") == 429:
        return "outage"
    if rc == 0 and document.get("is_error") is False:
        return "success"
    return "failure"


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


def _alive(pid: int) -> bool:
    try:
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        status = Path(f"/proc/{pid}/stat").read_text().split()[2]
        return status != "Z" and "claude" in cmd and (" -p " in f" {cmd} " or " --print " in f" {cmd} ")
    except (OSError, IndexError):
        return False


class Parent:
    def __init__(self, config: dict, state_dir: Path, *, spawn=subprocess.Popen,
                 alive=_alive, now=time.time):
        self.config = config
        self.root = Path(state_dir)
        self.spawn = spawn
        self.alive = alive
        self.now = now
        self.children = {}
        for key in ("effect_checkout", "settings", "model", "template", "header", "resume", "manifest"):
            if not isinstance(config.get(key), str):
                raise ValueError(f"invalid parent config: {key}")

    def _prompt(self, item: dict, a: int, request: Path, first: bool) -> str:
        values = {**item, "a": a, "request_path": str(request),
                  "manifest": self.config["manifest"],
                  "effect_checkout": self.config["effect_checkout"],
                  "transcript_dir": str(Path.home() / ".claude/projects" /
                                        self.config["effect_checkout"].replace("/", "-").replace(".", "-") /
                                        item["session_id"] / "subagents")}
        prompt = Path(self.config["header"] if first else self.config["resume"]).read_text().format_map(values)
        if first:
            template = Path(self.config["template"]).read_text()
            match = re.search(r"^## 2\..*$", template, re.M)
            if not match:
                raise ValueError("template has no section 2")
            prompt += template[match.start():]
        return prompt

    def stop(self, a: int) -> None:
        state_path = self.root / "state.json"
        if not state_path.exists():
            return
        running = json.loads(state_path.read_text()).get("running")
        if running and running["a"] == a and self.alive(running["pid"]):
            try:
                os.killpg(running["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass

    def tick(self, item: dict, a: int, request: Path, handshake: Path) -> str:
        """One nonblocking poll. Returns running, outage, success, or exhausted."""
        self.root.mkdir(parents=True, exist_ok=True)
        state_path = self.root / "state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {
            "launched": 0, "failures": 0, "running": None, "next_retry": 0.0, "a": a}
        if state["a"] != a:
            if state["running"] is not None:
                raise RuntimeError("previous original proposal is still running")
            state.update(a=a, failures=0, next_retry=0.0)
            _save(state_path, state)
        if state.get("success_a") == a and state["running"] is None:
            return "success"
        if state["running"] is not None:
            run = state["running"]
            child = self.children.get(run["attempt"])
            rc = child.poll() if child else None
            if rc is None and self.alive(run["pid"]):
                return "running"
            if rc is None:
                rc = 255
            attempt = self.root / f"a-{a}-attempt-{run['attempt']}"
            (attempt / "rc").write_text(str(rc) + "\n")
            (attempt / "finished").write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n")
            state["running"] = None
            status = classify_exit(attempt / "out.json", rc)
            if status == "outage":
                handshake.mkdir(exist_ok=True)
                document = json.loads((attempt / "out.json").read_text())
                reset = re.search(r"\bresets\s+(.+)", str(document.get("result", "")))
                _save(handshake / f"outage-{a}.json", {"a": a, "attempt": run["attempt"],
                                                     "api_error_status": 429,
                                                     "reported_reset": reset.group(1) if reset else None})
                state["next_retry"] = self.now() + 20
            elif status == "failure":
                state["failures"] += 1
            _save(state_path, state)
            if status == "success":
                state["success_a"] = a
                _save(state_path, state)
                return "success"
            if state["failures"] > 2:
                return "exhausted"
            return "outage" if status == "outage" else "running"
        if state["failures"] > 2:
            return "exhausted"
        if self.now() < state["next_retry"]:
            return "outage"
        if any(key in os.environ for key in FORBIDDEN):
            raise RuntimeError("forbidden parent environment")
        attempt_no = state["launched"] + 1
        attempt = self.root / f"a-{a}-attempt-{attempt_no}"
        attempt.mkdir(parents=True, exist_ok=False)
        first = state["launched"] == 0
        (attempt / "prompt.md").write_text(self._prompt(item, a, request, first))
        state["launched"] = attempt_no
        _save(state_path, state)
        argv = ["claude", "-p", "--model", self.config["model"], "--settings", self.config["settings"],
                "--session-id" if first else "--resume", item["session_id"],
                "--allowedTools", "Bash(python3 tools/b5_llm_round.py *)", "Bash(ls *)", "Bash(test *)",
                "Read", "Write", "Agent", "--output-format", "json"]
        with (attempt / "prompt.md").open("rb") as inp, (attempt / "out.json").open("wb") as out, (attempt / "err.log").open("wb") as err:
            child = self.spawn(argv, cwd=self.config["effect_checkout"], stdin=inp,
                               stdout=out, stderr=err, start_new_session=True)
        self.children[attempt_no] = child
        (attempt / "pid").write_text(str(child.pid) + "\n")
        state["running"] = {"pid": child.pid, "attempt": attempt_no, "a": a}
        _save(state_path, state)
        return "running"
