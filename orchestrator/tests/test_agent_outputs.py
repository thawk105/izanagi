"""Agent output contract using temporary files and a plain runner."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import agent_outputs as ao
from orchestrator.campaign.layout import CampaignLayout


def _env(stage="planner_proposed"):
    payload = {
        "output": {"text": "機序", "nested": {"b": 2, "a": 1}},
        "input_sha256": "1" * 64,
        "provenance": {"mode": "ingested", "source_path": "source.json",
                       "source_sha256": "2" * 64, "input_path": "input.json",
                       "input_file_sha256": "3" * 64},
        "refs": ["wal:" + "4" * 64],
    }
    if stage == "critic_attributed":
        payload["digest_sha256"] = "5" * 64
        payload["output"] = dict.fromkeys(
            ("raw_markdown", "attribution", "recommend", "avoid", "uncertainty"),
            "機序の記録")
    return {"ts": 1.0, "stage": stage,
            "variant": "variant" if stage == "critic_attributed" else None,
            "env_tag": "fixture", "payload": payload}


def _reject(tmp_path, env, reason):
    path = tmp_path / "ao.jsonl"
    path.write_bytes(json.dumps(env, ensure_ascii=False).encode() + b"\n")
    with pytest.raises(ao.AgentOutputError, match="line 1:.*" + reason):
        ao.read_agent_outputs(path)
    before = path.read_bytes()
    with pytest.raises(ao.AgentOutputError, match=reason):
        ao.append_agent_output(path, env)
    assert path.read_bytes() == before


def test_roundtrip_three_stages(tmp_path):
    path = tmp_path / ao.AGENT_OUTPUTS_FILENAME
    records = [_env(stage) for stage in ao.STAGES]
    for env in records:
        digest = ao.append_agent_output(path, env)
        assert digest == hashlib.sha256(ao.canonical_bytes(env)).hexdigest()
        assert ao.envelope_ref(env) == "ao:" + digest
    assert ao.read_agent_outputs(str(path)) == records
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_unknown_stage(tmp_path):
    env = _env()
    env["stage"] = "unregistered"
    _reject(tmp_path, env, "unknown stage")


def test_envelope_exact_keys(tmp_path):
    for operation in ("missing", "extra"):
        env = _env()
        if operation == "missing":
            del env["ts"]
        else:
            env["extra"] = 1
        _reject(tmp_path, env, "exact 5 keys")


def test_timestamp(tmp_path):
    for value in (True, float("inf"), float("nan"), 1, None):
        env = _env()
        env["ts"] = value
        _reject(tmp_path, env, "finite float")


def test_critic_variant(tmp_path):
    for value in (None, ""):
        env = _env("critic_attributed")
        env["variant"] = value
        _reject(tmp_path, env, "critic variant")


def test_critic_digest_required(tmp_path):
    env = _env("critic_attributed")
    del env["payload"]["digest_sha256"]
    _reject(tmp_path, env, "digest_sha256")


def test_planner_digest_forbidden(tmp_path):
    for stage in ao.STAGES[:2]:
        env = _env(stage)
        env["payload"]["digest_sha256"] = "5" * 64
        _reject(tmp_path, env, "only allowed for critic")


def test_critic_output_exact_keys(tmp_path):
    for change in ("missing", "extra", "type"):
        env = _env("critic_attributed")
        output = env["payload"]["output"]
        if change == "missing":
            del output["avoid"]
        elif change == "extra":
            output["extra"] = "text"
        else:
            output["avoid"] = None
        _reject(tmp_path, env, "critic output")


def test_refs(tmp_path):
    for refs in (["ao:" + "4" * 64], ["wal:" + "A" * 64], [1], "wal:bad"):
        env = _env()
        env["payload"]["refs"] = refs
        _reject(tmp_path, env, "refs")


def test_provenance_unknown_key(tmp_path):
    env = _env()
    env["payload"]["provenance"]["unknown"] = "text"
    _reject(tmp_path, env, "provenance.*unknown keys")


def test_provenance_mode(tmp_path):
    env = _env()
    env["payload"]["provenance"]["mode"] = "inferred"
    _reject(tmp_path, env, "provenance mode")


def test_payload_and_provenance_types(tmp_path):
    for key in ("output", "input_sha256", "provenance", "refs"):
        env = _env()
        del env["payload"][key]
        _reject(tmp_path, env, "payload missing")
    for key, value in (("output", []), ("input_sha256", "A" * 64),
                       ("provenance", [])):
        env = _env()
        env["payload"][key] = value
        _reject(tmp_path, env, key)
    for key in _env()["payload"]["provenance"]:
        env = _env()
        del env["payload"]["provenance"][key]
        _reject(tmp_path, env, "provenance")
    for key in ("source_path", "input_path", "prompt_path",
                "source_sha256", "input_file_sha256", "prompt_sha256"):
        env = _env()
        env["payload"]["provenance"][key] = 7
        _reject(tmp_path, env, key)


def test_optional_prompt_and_live(tmp_path):
    env = _env()
    env["payload"]["provenance"].update(
        mode="live", prompt_path="prompt.txt", prompt_sha256="6" * 64)
    env["payload"]["extension"] = {"preserved": True}
    env["variant"] = ""
    path = tmp_path / "ao.jsonl"
    ao.append_agent_output(path, env)
    assert ao.read_agent_outputs(path) == [env]


def test_env_tag_and_variant_types(tmp_path):
    for key, values in (("env_tag", ("", None, 1)), ("variant", (True, 1, []))):
        for value in values:
            env = _env()
            env[key] = value
            _reject(tmp_path, env, key)


def test_unterminated_last_frame(tmp_path):
    path = tmp_path / "ao.jsonl"
    valid = ao.canonical_bytes(_env())
    path.write_bytes(valid + b"\n" + valid)
    with pytest.raises(ao.AgentOutputError, match="line 2:.*newline-terminated"):
        ao.read_agent_outputs(path)


def test_blank_line(tmp_path):
    for blank in (b"", b" \t\r"):
        path = tmp_path / "ao.jsonl"
        path.write_bytes(ao.canonical_bytes(_env()) + b"\n" + blank + b"\n")
        with pytest.raises(ao.AgentOutputError, match="line 2:.*blank"):
            ao.read_agent_outputs(path)


def test_duplicate_json_key(tmp_path):
    path = tmp_path / "ao.jsonl"
    raw = ao.canonical_bytes(_env()).replace(b'"a":1', b'"a":1,"a":2')
    path.write_bytes(raw + b"\n")
    with pytest.raises(ao.AgentOutputError, match="line 1:.*duplicate key"):
        ao.read_agent_outputs(path)


def test_invalid_encoding_and_json(tmp_path):
    path = tmp_path / "ao.jsonl"
    for raw in (b"\xff\n", b"not json\n", b"[]\n"):
        path.write_bytes(raw)
        with pytest.raises(ao.AgentOutputError, match="line 1:"):
            ao.read_agent_outputs(path)


def test_complete_duplicate_append(tmp_path):
    path = tmp_path / "ao.jsonl"
    env = _env()
    ao.append_agent_output(path, env)
    before = path.read_bytes()
    with pytest.raises(ao.AgentOutputError, match="line 2:.*duplicate canonical"):
        ao.append_agent_output(path, env)
    assert path.read_bytes() == before


def test_semantic_duplicate_append(tmp_path):
    path = tmp_path / "ao.jsonl"
    env = _env()
    ao.append_agent_output(path, env)
    before = path.read_bytes()
    changed = copy.deepcopy(env)
    changed["ts"] += 1.0
    assert ao.canonical_sha256(changed) != ao.canonical_sha256(env)
    assert ao.semantic_key(changed) == ao.semantic_key(env)
    with pytest.raises(ao.AgentOutputError, match="line 2:.*duplicate semantic_key"):
        ao.append_agent_output(path, changed)
    assert path.read_bytes() == before


def test_reader_duplicates(tmp_path):
    path = tmp_path / "ao.jsonl"
    first = _env()
    for timestamp, reason in ((1.0, "canonical"), (2.0, "semantic_key")):
        second = _env()
        second["ts"] = timestamp
        path.write_bytes(ao.canonical_bytes(first) + b"\n"
                         + json.dumps(second).encode() + b"\n")
        with pytest.raises(ao.AgentOutputError, match="line 2:.*duplicate " + reason):
            ao.read_agent_outputs(path)


def test_corrupt_existing_append_unchanged(tmp_path):
    path = tmp_path / "ao.jsonl"
    for raw in (b"partial", b"bad\n", b"\n", b"\xff\n",
                ao.canonical_bytes(_env()) + b"\n\n"):
        path.write_bytes(raw)
        with pytest.raises(ao.AgentOutputError, match="line [12]:"):
            ao.append_agent_output(path, _env("coder_proposed"))
        assert path.read_bytes() == raw


def test_symlink_rejected(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"")
    path = tmp_path / "ao.jsonl"
    path.symlink_to(target)
    for exists in (True, False):
        if not exists:
            target.unlink()
        with pytest.raises(ao.AgentOutputError, match="regular file.*symlink"):
            ao.read_agent_outputs(path)
        with pytest.raises(ao.AgentOutputError, match="regular file.*symlink"):
            ao.append_agent_output(path, _env())
        assert target.exists() == exists


def test_nonregular_path_rejected(tmp_path):
    for path in (tmp_path / "dir", tmp_path / "fifo"):
        if path.name == "dir":
            path.mkdir()
        else:
            os.mkfifo(path)
        with pytest.raises(ao.AgentOutputError, match="regular file"):
            ao.read_agent_outputs(path)
        with pytest.raises(ao.AgentOutputError, match="regular file"):
            ao.append_agent_output(path, _env())


def test_missing_empty_and_parent(tmp_path):
    path = tmp_path / "absent"
    with pytest.raises(FileNotFoundError):
        ao.read_agent_outputs(path)
    with pytest.raises(FileNotFoundError):
        ao.append_agent_output(path / "ao.jsonl", _env())
    assert not path.exists()
    path.write_bytes(b"")
    assert ao.read_agent_outputs(path) == []


def test_short_write(tmp_path):
    path = tmp_path / "ao.jsonl"
    real_write = os.write
    calls = []

    def short_write(fd, data):
        calls.append(data)
        return real_write(fd, data[:7])

    with patch.object(ao.os, "write", short_write):
        with pytest.raises(ao.AgentOutputError, match="short write"):
            ao.append_agent_output(path, _env())
    assert len(calls) == 1
    assert path.read_bytes() == calls[0][:7]
    with pytest.raises(ao.AgentOutputError, match="newline-terminated"):
        ao.append_agent_output(path, _env())


def test_fsync_file_and_directory(tmp_path):
    real_fsync = os.fsync
    calls = []

    def fsync(fd):
        calls.append("dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
        return real_fsync(fd)

    with patch.object(ao.os, "fsync", fsync):
        ao.append_agent_output(tmp_path / "ao.jsonl", _env())
    assert calls == ["file", "dir"]


def test_fsync_failure_propagates(tmp_path):
    for fail_directory in (False, True):
        real_fsync = os.fsync

        def fsync(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode) == fail_directory:
                raise OSError("injected fsync failure")
            return real_fsync(fd)

        path = tmp_path / str(fail_directory)
        with patch.object(ao.os, "fsync", fsync):
            with pytest.raises(OSError, match="injected fsync failure"):
                ao.append_agent_output(path, _env())
        assert ao.read_agent_outputs(path) == [_env()]


def test_flock_covers_open_validation_and_write(tmp_path):
    path = tmp_path / "ao.jsonl"
    ao.append_agent_output(path, _env())
    events = []
    real_flock, real_open = ao.fcntl.flock, os.open
    real_read, real_write = ao._read_bytes, os.write
    locked = False

    def flock(fd, operation):
        nonlocal locked
        result = real_flock(fd, operation)
        locked = operation == ao.fcntl.LOCK_EX
        events.append("lock" if locked else "unlock")
        return result

    def open_file(name, flags, *args):
        if os.fspath(name) == str(path):
            assert locked
            events.append("open")
        return real_open(name, flags, *args)

    def read(raw):
        assert locked
        events.append("validate")
        return real_read(raw)

    def write(fd, data):
        assert locked and events[-1] == "validate"
        events.append("write")
        return real_write(fd, data)

    with patch.object(ao.fcntl, "flock", flock), \
            patch.object(ao.os, "open", open_file), \
            patch.object(ao, "_read_bytes", read), \
            patch.object(ao.os, "write", write):
        ao.append_agent_output(path, _env("coder_proposed"))
    assert events == ["lock", "open", "validate", "write", "unlock"]


def test_canonical_bytes():
    expected = '{"a":"機序","z":[1,true,null]}'.encode("utf-8")
    assert ao.canonical_bytes({"z": [1, True, None], "a": "機序"}) == expected
    assert ao.canonical_bytes({"a": "機序", "z": [1, True, None]}) == expected
    assert ao.canonical_sha256({"a": "機序", "z": [1, True, None]}) == hashlib.sha256(expected).hexdigest()
    for value in (float("inf"), float("-inf"), float("nan"), object(), {1, 2}):
        with pytest.raises(ao.AgentOutputError, match="canonical JSON"):
            ao.canonical_bytes({"nested": [value]})


def test_layout(tmp_path):
    layout = CampaignLayout(root=str(tmp_path))
    path = Path(layout.agent_outputs_file)
    assert path == tmp_path / "runs" / "agent_outputs.jsonl"
    assert path.parent == Path(layout.runs_dir)


def _run():
    from skiputil import Skip
    passed = failed = skipped = 0
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        try:
            with tempfile.TemporaryDirectory() as directory:
                kwargs = {name: Path(directory) for name in inspect.signature(fn).parameters}
                fn(**kwargs)
            print("PASS " + fn.__name__)
            passed += 1
        except Skip as exc:
            print("SKIP %s: %s" % (fn.__name__, exc))
            skipped += 1
        except AssertionError as exc:
            print("FAIL %s: %s" % (fn.__name__, exc))
            failed += 1
        except Exception as exc:
            print("ERROR %s: %s: %s" % (fn.__name__, type(exc).__name__, exc))
            failed += 1
    print("%d passed, %d failed, %d skipped" % (passed, failed, skipped))
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(_run())
