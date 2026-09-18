"""Durable reporting records; only the loop harness writes agent outputs.

Design section 2-2 keeps input projections (planner_context_payload,
whiteboard_for_planner, etc.) separate: they must not import this module.
mode records the recording method, not observed generation: live is appended by
harness before evaluation; ingested imports output produced elsewhere. ts is the
recording time. input_sha256 is the canonical SHA-256 of saved JSON declared by
the caller as actual input, not proof of delivery. prompt_sha256 is the SHA-256
of the specified file bytes. mechanism_hypotheses records LLM (critic)
attribution, not empirical proof of a mechanism.
This module depends on neither the harness, renderer, nor WAL recording layer.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import stat


class AgentOutputError(ValueError):
    """An agent output violates the envelope or durable append contract."""


STAGES: tuple[str, ...] = (
    "planner_proposed", "coder_proposed", "critic_attributed",
)
AGENT_OUTPUTS_FILENAME = "agent_outputs.jsonl"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_WAL_REF = re.compile(r"wal:[0-9a-f]{64}")


def extract_critic_sections(raw: str) -> dict:
    """Select exact, unique level-two sections outside Markdown fences.

    Bodies end at the next unfenced ``## `` line and are stripped at both ends.
    Preserve interior bytes, including CRLF and fenced examples.
    """
    headings = []
    offset = 0
    fence = None
    for line in re.findall(r"[^\n]*\n|[^\n]+$", raw):
        text = line.rstrip("\r\n")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", text)
        if fence is not None:
            if (marker and marker[1][0] == fence[0]
                    and len(marker[1]) >= len(fence) and not marker[2].strip()):
                fence = None
        elif marker and (marker[1][0] != "`" or "`" not in marker[2]):
            fence = marker[1]
        elif text.startswith("## "):
            headings.append((offset, offset + len(line), text))
        offset += len(line)
    sections = {}
    for name in ("attribution", "recommend", "avoid", "uncertainty"):
        matches = [i for i, (_, _, text) in enumerate(headings)
                   if re.fullmatch(r"## " + name + r"\s*", text)]
        if len(matches) != 1:
            raise AgentOutputError(f"critic heading ## {name} must occur exactly once")
        index = matches[0]
        end = headings[index + 1][0] if index + 1 < len(headings) else len(raw)
        sections[name] = raw[headings[index][1]:end].strip()
    return sections


def canonical_bytes(obj) -> bytes:
    try:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise AgentOutputError("invalid canonical JSON: %s" % exc) from exc


def canonical_sha256(obj) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def _digest(value, name):
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise AgentOutputError(name + " must be lowercase SHA-256 hex")


def validate_envelope(env) -> None:
    if not isinstance(env, dict) or set(env) != {
            "ts", "stage", "variant", "env_tag", "payload"}:
        raise AgentOutputError("envelope must have exact 5 keys")
    if type(env["ts"]) is not float or not math.isfinite(env["ts"]):
        raise AgentOutputError("ts must be a finite float")
    if env["stage"] not in STAGES:
        raise AgentOutputError("unknown stage")
    critic = env["stage"] == "critic_attributed"
    variant = env["variant"]
    if variant is not None and not isinstance(variant, str):
        raise AgentOutputError("variant must be str or None")
    if critic and (not isinstance(variant, str) or not variant):
        raise AgentOutputError("critic variant must be a nonempty str")
    if not isinstance(env["env_tag"], str) or not env["env_tag"]:
        raise AgentOutputError("env_tag must be a nonempty str")
    payload = env["payload"]
    required = {"output", "input_sha256", "provenance", "refs"}
    if not isinstance(payload, dict) or not required <= set(payload):
        raise AgentOutputError("payload missing required keys")
    if not isinstance(payload["output"], dict):
        raise AgentOutputError("output must be a dict")
    _digest(payload["input_sha256"], "input_sha256")
    refs = payload["refs"]
    if not isinstance(refs, list) or any(
            not isinstance(ref, str) or _WAL_REF.fullmatch(ref) is None
            for ref in refs):
        raise AgentOutputError("refs must be a list of wal: SHA-256 references")
    provenance = payload["provenance"]
    required = {"mode", "source_path", "source_sha256", "input_path",
                "input_file_sha256"}
    optional = {"prompt_path", "prompt_sha256"}
    if (not isinstance(provenance, dict)
            or not required <= set(provenance)
            or set(provenance) - (required | optional)):
        raise AgentOutputError("provenance has missing or unknown keys")
    if provenance["mode"] not in ("live", "ingested"):
        raise AgentOutputError("provenance mode must be live or ingested")
    for key in ("source_path", "input_path", "prompt_path"):
        if key in provenance and not isinstance(provenance[key], str):
            raise AgentOutputError("provenance " + key + " must be str")
    for key in ("source_sha256", "input_file_sha256", "prompt_sha256"):
        if key in provenance:
            _digest(provenance[key], key)
    if critic:
        _digest(payload.get("digest_sha256"), "digest_sha256")
        output = payload["output"]
        if (set(output) != {"raw_markdown", "attribution", "recommend", "avoid",
                           "uncertainty"}
                or any(not isinstance(v, str) for v in output.values())):
            raise AgentOutputError("critic output must have exact 5 string keys")
    elif "digest_sha256" in payload:
        raise AgentOutputError("digest_sha256 is only allowed for critic")
    canonical_bytes(env)


def semantic_key(env) -> str:
    payload = env["payload"]
    return (env["stage"] + ":" + payload["input_sha256"] + ":"
            + canonical_sha256(payload["output"]))


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AgentOutputError("duplicate key: %r" % key)
        result[key] = value
    return result


def _check_duplicate(env, canonical_seen, semantic_seen):
    encoded = canonical_bytes(env)
    if encoded in canonical_seen:
        raise AgentOutputError("duplicate canonical envelope")
    key = semantic_key(env)
    if key in semantic_seen:
        raise AgentOutputError("duplicate semantic_key")
    canonical_seen.add(encoded)
    semantic_seen.add(key)


def _read_bytes(raw):
    records = []
    canonical_seen, semantic_seen = set(), set()
    frames = raw.split(b"\n")
    for number, frame in enumerate(frames[:-1], 1):
        try:
            if not frame.strip():
                raise AgentOutputError("blank line")
            env = json.loads(frame.decode("utf-8"),
                             object_pairs_hook=_reject_duplicate_keys)
            validate_envelope(env)
            _check_duplicate(env, canonical_seen, semantic_seen)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise AgentOutputError("line %d: %s" % (number, exc)) from exc
        records.append(env)
    if frames[-1]:
        raise AgentOutputError("line %d: not newline-terminated" % len(frames))
    return records


def _absolute_path(path):
    path = os.fspath(path)
    if not os.path.isabs(path):
        raise AgentOutputError("path must be absolute")
    return path


def _check_regular(path):
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise AgentOutputError("path must be a regular file (no symlink)")


def _read_fd(fd):
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        raise AgentOutputError("path must be a regular file")
    chunks = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            return _read_bytes(b"".join(chunks))
        chunks.append(chunk)


def read_agent_outputs(path) -> list[dict]:
    path = _absolute_path(path)
    _check_regular(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        return _read_fd(fd)
    finally:
        os.close(fd)


def append_agent_output(path, env) -> str:
    validate_envelope(env)
    path = _absolute_path(path)
    encoded = canonical_bytes(env)
    # A directory lock also covers initial creation: no extra persistent lock
    # file, and opening/creating the append target happens inside LOCK_EX.
    dfd = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(dfd, fcntl.LOCK_EX)
        try:
            try:
                _check_regular(path)
            except FileNotFoundError:
                pass
            fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT
                         | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            try:
                existing = _read_fd(fd)
                try:
                    _check_duplicate(env, {canonical_bytes(e) for e in existing},
                                     {semantic_key(e) for e in existing})
                except AgentOutputError as exc:
                    raise AgentOutputError(
                        "line %d: %s" % (len(existing) + 1, exc)) from exc
                frame = encoded + b"\n"
                written = os.write(fd, frame)
                if written != len(frame):
                    raise AgentOutputError("short write: %d of %d bytes"
                                           % (written, len(frame)))
                os.fsync(fd)
                os.fsync(dfd)
            finally:
                os.close(fd)
        finally:
            fcntl.flock(dfd, fcntl.LOCK_UN)
    finally:
        os.close(dfd)
    return hashlib.sha256(encoded).hexdigest()


def envelope_ref(env) -> str:
    return "ao:" + canonical_sha256(env)
