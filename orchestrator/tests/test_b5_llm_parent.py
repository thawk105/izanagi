"""429 and abnormal termination behavior of the login parent."""
import json
from pathlib import Path

from tools.pegasus.b5_llm_parent import Parent, classify_exit


def _config(tmp_path):
    for name, content in (("header", "request {a} {request_path}\n"),
                          ("resume", "resume {a} {request_path}\n"),
                          ("template", "# template\n## 2. fixed\ntext\n")):
        (tmp_path / name).write_text(content)
    return {"effect_checkout": str(tmp_path), "settings": "settings.json", "model": "claude-opus-5",
            "header": str(tmp_path / "header"), "resume": str(tmp_path / "resume"),
            "template": str(tmp_path / "template"), "manifest": "manifest.json"}


def test_429_three_times_keeps_same_a_session_and_failure_budget(tmp_path, monkeypatch):
    from tools.pegasus.b5_llm_parent import FORBIDDEN
    for key in FORBIDDEN:
        monkeypatch.delenv(key, raising=False)
    replies = [{"is_error": True, "api_error_status": 429}] * 3 + [{"is_error": False}] * 2
    calls = []
    class Child:
        def __init__(self, number): self.pid = 1000 + number
        def poll(self): return 0
    def spawn(argv, **kw):
        calls.append(argv)
        kw["stdout"].write(json.dumps(replies[len(calls) - 1]).encode())
        return Child(len(calls))
    now = [0.]
    parent = Parent(_config(tmp_path), tmp_path / "state", spawn=spawn,
                    alive=lambda _pid: False, now=lambda: now[0])
    item = {"session_id": "fixed-session", "job_id": "job"}
    request = tmp_path / "request-2.json"
    request.write_text("{}")
    handshake = tmp_path / "handshake"
    for k in range(3):
        assert parent.tick(item, 2, request, handshake) == "running"
        assert parent.tick(item, 2, request, handshake) == "outage"
        assert json.loads((handshake / "outage-2.json").read_text())["a"] == 2
        assert json.loads((tmp_path / "state/state.json").read_text())["failures"] == 0
        now[0] += 899
        assert parent.tick(item, 2, request, handshake) == "outage"
        assert len(calls) == k + 1
        now[0] += 2
    assert parent.tick(item, 2, request, handshake) == "running"
    assert parent.tick(item, 2, request, handshake) == "success"
    assert len(calls) == 4
    assert calls[0][calls[0].index("--session-id") + 1] == "fixed-session"
    assert all("--resume" in argv and argv[argv.index("--resume") + 1] == "fixed-session"
               for argv in calls[1:])
    next_request = tmp_path / "request-3.json"
    next_request.write_text("{}")
    assert parent.tick(item, 3, next_request, handshake) == "running"
    assert "--resume" in calls[-1] and len(calls) == 5


def test_429_requires_structured_status_and_valid_json(tmp_path):
    out = tmp_path / "out.json"
    out.write_text(json.dumps({"is_error": False, "api_error_status": 429,
                               "result": "rate limit 429"}))
    assert classify_exit(out, 0) == "success"
    out.write_text(json.dumps({"is_error": True, "result": "429 weekly limit"}))
    assert classify_exit(out, 1) == "failure"
    out.write_text("{bad json 429")
    assert classify_exit(out, 1) == "failure"
    out.write_text(json.dumps({"is_error": True, "api_error_status": 429}))
    assert classify_exit(out, 1) == "outage"


def test_forbidden_environment_stops_before_parent_spawn(tmp_path, monkeypatch):
    from tools.pegasus.b5_llm_parent import FORBIDDEN
    monkeypatch.setenv(FORBIDDEN[2], "present")
    parent = Parent(_config(tmp_path), tmp_path / "state", spawn=lambda *_a, **_k:
                    (_ for _ in ()).throw(AssertionError("spawned")))
    request = tmp_path / "request-1.json"
    request.write_text("{}")
    try:
        parent.tick({"session_id": "fixed-session"}, 1, request, tmp_path / "handshake")
    except RuntimeError as exc:
        assert str(exc) == "forbidden parent environment"
    else:
        raise AssertionError("forbidden environment was accepted")
