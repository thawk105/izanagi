#!/usr/bin/env python3
"""T503 restore-durability probe; every writable artifact is below --root."""
from __future__ import annotations
import argparse, base64, hashlib, json, os, re, signal, socket, time
from pathlib import Path
SCHEMA = "t503-restore-durability-probe/v2"; TARGETS = ("targets/t0.bin", "targets/t1.bin")
DEFAULT_SIZE = 1024 * 1024; REQUIRED_LEGS = ("L-A", "L-C"); SCHEDULER_PROXY = "allocation 終了の proxy であり物理ノード死ではない"
DOES_NOT_PROVE = {"L-A": "物理ノード死、client eviction、OST/MDT failover、電源断後の fsync 永続性、fresh-client recovery、複数 file 原子性、任意 crash 点、非協調 consumer、本番機構の完全性を証明しない", "L-C": "原子的置換の耐久性、crash recovery、物理ノード死を証明しない", "L-B": "物理ノード死は未実施であり、walltime proxy から推論しない", "L-B2": SCHEDULER_PROXY}
class EvidenceError(RuntimeError): pass
def classify(current_sha256, original_sha256, mutated_sha256) -> str:
    if original_sha256 == mutated_sha256: raise ValueError("original と mutated の hash は異ならなければならない")
    if current_sha256 == original_sha256: return "ORIGINAL"
    return "MUTATED" if current_sha256 == mutated_sha256 else "OTHER"
def repair_decision(classifications) -> str:
    values = list(classifications)
    return "RESTORED" if len(values) == len(TARGETS) and all(value in {"ORIGINAL", "MUTATED"} for value in values) else "QUARANTINE"
def require_cross_client(writer_identity, observer_identity, allow_same_host=False) -> None:
    if allow_same_host: return
    writer_boot, observer_boot = writer_identity.get("boot_id"), observer_identity.get("boot_id")
    if writer_identity.get("host") == observer_identity.get("host") or writer_boot is None or observer_boot is None or writer_boot == observer_boot:
        raise EvidenceError("writer と observer は別 host・別 boot_id でなければならない")
def aggregate_verdict(legs) -> str:
    return "GO" if all(legs.get(name) == "PASS" for name in REQUIRED_LEGS) else "NO-GO"
def record_event(recorder, name: str) -> None:
    if recorder is not None: recorder(name)
def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _json_sha(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
def _probe_sha256() -> str: return _sha(Path(__file__).read_bytes())
def _proc(path: str, start=False):
    try:
        text = Path(path).read_text().strip()
        return text.rsplit(")", 1)[1].split()[19] if start else text
    except (OSError, IndexError):
        return None
def _identity(writer=False):
    value = {"host": socket.gethostname(), "boot_id": _proc("/proc/sys/kernel/random/boot_id"), "pid": os.getpid()}
    if writer: value["start_token"] = _proc("/proc/self/stat", True)
    return value
def _sync(path: Path, recorder=None, event=None, directory=False) -> None:
    flags = os.O_RDONLY | (getattr(os, "O_DIRECTORY", 0) if directory else 0)
    fd = os.open(path, flags)
    try: os.fsync(fd)
    finally: os.close(fd)
    if event: record_event(recorder, event)
def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    _sync(path.parent, directory=True)
def _write_json(path: Path, value: dict) -> None:
    _write_new(path, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
def _append(path: Path, value: dict, recorder, event: str) -> None:
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with path.open("ab") as stream:
        stream.write(data); stream.flush()
    record_event(recorder, event)
def _check_components(path: Path) -> None:
    for component in (path, *path.parents):
        if component.is_symlink(): raise EvidenceError(f"symlink component: {component}")
def _ensure_root(path) -> tuple[Path, dict]:
    root = Path(path)
    if not root.is_absolute(): raise EvidenceError("--root は絶対 path でなければならない")
    _check_components(root)
    missing, cursor = [], root
    while not cursor.exists():
        missing.append(cursor); cursor = cursor.parent
    if not cursor.is_dir(): raise EvidenceError("--root の既存祖先が directory でない")
    created, parents = [], []
    for directory in reversed(missing):
        directory.mkdir(mode=0o700); _sync(directory.parent, directory=True)
        created.append(str(directory)); parents.append(str(directory.parent))
    _check_components(root)
    return root.resolve(), {"created_directories": created, "fsynced_parents": parents, "existing_ancestor": str(cursor.resolve())}
def _root(path, create=False) -> Path:
    if create: return _ensure_root(path)[0]
    root = Path(path)
    if not root.is_absolute() or not root.is_dir(): raise EvidenceError("--root は存在する絶対 directory でなければならない")
    _check_components(root)
    return root.resolve()
def _artifact(root: Path, value, name: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.name != name or path.parent.resolve() != root: raise EvidenceError(f"{name} は --root 直下でなければならない")
    if path.is_symlink(): raise EvidenceError(f"symlink artifact: {name}")
    return path
def _target(root: Path, rel: str) -> Path:
    if rel not in TARGETS: raise EvidenceError(f"unexpected target: {rel}")
    path = root / rel
    if path.is_symlink() or path.parent.resolve() != path.parent: raise EvidenceError(f"symlink target: {rel}")
    return path
def _records(path: Path) -> list[dict]:
    data = path.read_bytes()
    if not data or not data.endswith(b"\n"): raise EvidenceError("journal has an unterminated tail")
    try:
        records = [json.loads(line) for line in data.splitlines()]
    except json.JSONDecodeError as exc:
        raise EvidenceError("journal JSON is invalid") from exc
    _validate_records(records)
    return records
def _valid_identity(value, writer=False) -> bool:
    keys = {"host", "boot_id", "pid"} | ({"start_token"} if writer else set())
    return isinstance(value, dict) and set(value) == keys and isinstance(value["host"], str) and value["host"] and (value["boot_id"] is None or isinstance(value["boot_id"], str)) and isinstance(value["pid"], int) and (not writer or isinstance(value["start_token"], str))
def _armed(record: dict):
    try:
        ancestry = record["ancestor_fsync"]
        if set(record) != {"record", "seq", "schema", "writer", "targets", "ancestor_fsync"} or record["record"] != "armed" or record["seq"] != 0 or record["schema"] != SCHEMA or not _valid_identity(record["writer"], True) or [item["rel"] for item in record["targets"]] != list(TARGETS) or not isinstance(ancestry, dict) or set(ancestry) != {"created_directories", "fsynced_parents", "existing_ancestor"} or not all(isinstance(x, str) for x in ancestry["created_directories"] + ancestry["fsynced_parents"]) or not isinstance(ancestry["existing_ancestor"], str):
            return None
        for item in record["targets"]:
            if set(item) != {"rel", "original_sha256", "original_b64", "mutated_sha256", "mutated_b64", "temp_name"}: return None
            old = base64.b64decode(item["original_b64"], validate=True)
            new = base64.b64decode(item["mutated_b64"], validate=True)
            if _sha(old) != item["original_sha256"] or _sha(new) != item["mutated_sha256"] or item["original_sha256"] == item["mutated_sha256"] or Path(item["temp_name"]).name != item["temp_name"]: return None
    except (KeyError, TypeError, ValueError):
        return None
    return record
def _validate_records(records: list[dict]) -> None:
    if not records or any(not isinstance(value, dict) for value in records): raise EvidenceError("journal records must be non-empty objects")
    if [value.get("seq") for value in records] != list(range(len(records))): raise EvidenceError("journal seq is not contiguous from zero")
    states = tuple(value.get("record") for value in records)
    allowed = {("armed",), ("armed", "mutated"), ("armed", "recovering"), ("armed", "mutated", "recovering"), ("armed", "recovering", "clean"), ("armed", "mutated", "recovering", "clean")}
    if states not in allowed or _armed(records[0]) is None: raise EvidenceError("journal transition or armed record is invalid")
    for value in records[1:]:
        state = value["record"]
        if state in {"mutated", "clean"} and set(value) != {"record", "seq"}: raise EvidenceError(f"invalid {state} record")
        if state == "recovering":
            if set(value) != {"record", "seq", "crash_evidence", "observer", "epoch"} or value["crash_evidence"] not in {"controlled-sigkill-receipt", "scheduler-accounting"} or not _valid_identity(value["observer"]) or not isinstance(value["epoch"], int): raise EvidenceError("invalid recovering record")
def _writer_info(root: Path, armed: dict | None = None) -> dict:
    value = json.loads((root / "writer-info").read_text())
    keys = {"pbs_jobid", "hostname", "boot_id", "pid", "start_token", "probe_sha256", "pbs_sha256", "epoch"}
    if not isinstance(value, dict) or set(value) != keys or not isinstance(value["pbs_jobid"], str) or not value["pbs_jobid"] or not isinstance(value["pid"], int) or not all(isinstance(value[name], str) and value[name] for name in ("hostname", "boot_id", "start_token", "probe_sha256", "pbs_sha256")) or not all(re.fullmatch(r"[0-9a-f]{64}", value[name]) for name in ("probe_sha256", "pbs_sha256")) or not isinstance(value["epoch"], int) or value["probe_sha256"] != _probe_sha256():
        raise EvidenceError("writer-info or probe source binding is invalid")
    if armed is not None and armed["writer"] != {"host": value["hostname"], "boot_id": value["boot_id"], "pid": value["pid"], "start_token": value["start_token"]}:
        raise EvidenceError("writer-info does not match armed writer")
    return value
def _ready(root: Path, writer: dict, armed: dict) -> dict:
    value = json.loads((root / "ready").read_text())
    if not isinstance(value, dict) or value.get("record") != "ready" or value.get("writer") != armed["writer"] or value.get("probe_sha256") != _probe_sha256() or value.get("epoch") != writer["epoch"] or value.get("ancestor_fsync") != armed["ancestor_fsync"]:
        raise EvidenceError("ready receipt is invalid")
    return value
def _mount_info(root: Path) -> dict:
    matches = []
    for line in Path("/proc/mounts").read_text().splitlines():
        fields = line.split()
        if len(fields) < 3: continue
        mount = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), fields[1])
        point = Path(mount)
        try:
            root.relative_to(point)
        except ValueError: continue
        matches.append((len(str(point)), point, fields[2]))
    if not matches: raise EvidenceError("root mount could not be resolved")
    _, point, fstype = max(matches)
    return {"st_dev": os.stat(root).st_dev, "mount_point": str(point), "fstype": fstype}
def _context(root: Path) -> tuple[list[dict], dict, dict, dict]:
    records = _records(root / "journal/attempt.jsonl"); armed = records[0]
    writer = _writer_info(root, armed); ready = _ready(root, writer, armed)
    return records, armed, writer, ready
def _states(root: Path, armed: dict) -> list[dict]:
    result = []
    for item in armed["targets"]:
        data = _target(root, item["rel"]).read_bytes(); mutated = base64.b64decode(item["mutated_b64"])
        result.append({"rel": item["rel"], "sha256": _sha(data), "size": len(data),
                       "classification": classify(_sha(data), item["original_sha256"], item["mutated_sha256"]),
                       "partial_prefix": len(data) == len(mutated) // 2 and data == mutated[:len(mutated) // 2]})
    return result
def run_writer(root, mode, recorder=None, size=DEFAULT_SIZE, block=False, pbs_jobid="unit-test", pbs_sha256="0" * 64):
    if mode not in {"atomic", "inplace-partial"} or size <= 1: raise ValueError("invalid writer mode or size")
    root, ancestry = _ensure_root(root)
    if (root / "root-durability.json").is_file(): ancestry = json.loads((root / "root-durability.json").read_text())
    if (root / "go-kill").exists() or (root / "go-kill").is_symlink(): raise EvidenceError("stale go-kill exists before writer startup")
    targets_dir, journal_dir = root / "targets", root / "journal"
    targets_dir.mkdir(mode=0o700); journal_dir.mkdir(mode=0o700)
    identity, epoch = _identity(True), int(time.time())
    info = {"pbs_jobid": pbs_jobid, "hostname": identity["host"], "boot_id": identity["boot_id"], "pid": identity["pid"], "start_token": identity["start_token"], "probe_sha256": _probe_sha256(), "pbs_sha256": pbs_sha256, "epoch": epoch}
    _write_json(root / "writer-info", info)
    entries = []
    for index, rel in enumerate(TARGETS):
        old, new = bytes([0x41 + index]) * size, bytes([0x61 + index]) * size
        target = _target(root, rel); _write_new(target, old)
        entries.append({"rel": rel, "original_sha256": _sha(old), "original_b64": base64.b64encode(old).decode(), "mutated_sha256": _sha(new), "mutated_b64": base64.b64encode(new).decode(), "temp_name": f".{target.name}.t503-new"})
    _sync(targets_dir, directory=True); _sync(journal_dir, directory=True); _sync(root, directory=True)
    record_event(recorder, "setup_targets")
    journal = journal_dir / "attempt.jsonl"
    armed = {"record": "armed", "seq": 0, "schema": SCHEMA, "writer": identity, "targets": entries, "ancestor_fsync": ancestry}
    with journal.open("xb") as stream:
        stream.write((json.dumps(armed, sort_keys=True, separators=(",", ":")) + "\n").encode()); stream.flush()
    record_event(recorder, "armed_write")
    _sync(journal, recorder, "armed_fsync")
    _write_new(journal_dir / "active", b"attempt.jsonl\n"); record_event(recorder, "active_publish")
    _sync(journal_dir, recorder, "active_dir_fsync", True)
    for item in entries:
        target, new = _target(root, item["rel"]), base64.b64decode(item["mutated_b64"])
        if mode == "inplace-partial":
            with target.open("wb") as stream:
                stream.write(new[:len(new) // 2]); stream.flush()
            _sync(target, recorder, "target_inplace_fsync")
            continue
        temp = target.parent / item["temp_name"]
        with temp.open("xb") as stream:
            stream.write(new); stream.flush(); record_event(recorder, "target_temp_write")
            os.fsync(stream.fileno()); record_event(recorder, "target_temp_fsync")
        os.replace(temp, target); record_event(recorder, "target_replace")
        _sync(target.parent, recorder, "target_dir_fsync", True)
    if mode == "atomic" and any(_sha(_target(root, x["rel"]).read_bytes()) != x["mutated_sha256"] for x in entries):
        raise EvidenceError("mutated bytes verification failed")
    _append(journal, {"record": "mutated", "seq": 1}, recorder, "mutated_append")
    _sync(journal, recorder, "mutated_fsync")
    ready = {"record": "ready", "writer": identity, "epoch": epoch, "probe_sha256": _probe_sha256(), "ancestor_fsync": ancestry}
    _write_json(root / "ready", ready); record_event(recorder, "ready_publish")
    if block:
        while True: signal.pause()
    return armed
def run_inspect(root, allow_same_host=False, expect_partial_prefix=False, require_fstype=None):
    root, observer = _root(root), _identity()
    result = {"inspector": observer, "armed_visible": False, "ready_visible": False, "mutated_visible": False, "source_bound": False, "cross_client": False, "classifications": [], "all_complete_bytes": False, "all_partial_prefix": False, "expected_partial_prefix": expect_partial_prefix, "mount": None, "acceptance_conditions": [], "does_not_prove": DOES_NOT_PROVE["L-C" if expect_partial_prefix else "L-A"]}
    try:
        records, armed, writer, _ = _context(root)
        result.update(armed_visible=True, ready_visible=True, mutated_visible=records[-1]["record"] == "mutated", source_bound=True, mount=_mount_info(root))
        if not result["mutated_visible"]: raise EvidenceError("inspect requires a mutated record")
        require_cross_client(armed["writer"], observer, allow_same_host)
        result["cross_client"] = armed["writer"]["host"] != observer["host"] and armed["writer"]["boot_id"] != observer["boot_id"]
        if require_fstype is not None and result["mount"]["fstype"] != require_fstype: raise EvidenceError("unexpected filesystem type")
        result["classifications"] = _states(root, armed)
        result["all_complete_bytes"] = all(x["classification"] in {"ORIGINAL", "MUTATED"} for x in result["classifications"])
        result["all_partial_prefix"] = all(x["partial_prefix"] for x in result["classifications"])
        accepted = result["all_partial_prefix"] if expect_partial_prefix else result["all_complete_bytes"]
        result["acceptance_conditions"] = ["ready receipt", "mutated record", "source hash binding", "different host and boot_id", "mount recorded", "exact half mutated prefix" if expect_partial_prefix else "complete original-or-mutated bytes"]
        if not accepted: raise EvidenceError("target bytes do not satisfy inspect acceptance")
        return result, 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, EvidenceError) as exc:
        result["error"] = str(exc); return result, 3
def _inspect_receipt(root: Path, result: dict, pbs_jobid: str, output: Path) -> dict:
    return {"record": "inspect-receipt", "host": result["inspector"]["host"], "boot_id": result["inspector"]["boot_id"], "epoch": int(time.time()), "pbs_jobid": pbs_jobid, "probe_sha256": _probe_sha256(), "inspect_output": output.name, "classifications_sha256": _json_sha(result["classifications"])}
def _validated_inspect_receipt(root: Path) -> tuple[dict, dict]:
    receipt = json.loads((root / "inspect-receipt").read_text())
    keys = {"record", "host", "boot_id", "epoch", "pbs_jobid", "probe_sha256", "inspect_output", "classifications_sha256"}
    if not isinstance(receipt, dict) or set(receipt) != keys or receipt["record"] != "inspect-receipt" or not all(isinstance(receipt[name], str) and receipt[name] for name in ("host", "boot_id", "pbs_jobid", "probe_sha256", "inspect_output", "classifications_sha256")) or not isinstance(receipt["epoch"], int) or receipt["probe_sha256"] != _probe_sha256() or Path(receipt["inspect_output"]).name != receipt["inspect_output"]:
        raise EvidenceError("inspect receipt is invalid")
    result = json.loads((root / receipt["inspect_output"]).read_text())
    if result.get("rc") != 0 or result.get("inspector", {}).get("host") != receipt["host"] or result.get("inspector", {}).get("boot_id") != receipt["boot_id"] or _json_sha(result.get("classifications")) != receipt["classifications_sha256"]:
        raise EvidenceError("inspect receipt does not bind inspect result")
    return receipt, result
def run_request_kill(root, pbs_jobid: str):
    root, observer = _root(root), _identity()
    receipt, _ = _validated_inspect_receipt(root)
    if receipt["host"] != observer["host"] or receipt["boot_id"] != observer["boot_id"] or receipt["pbs_jobid"] != pbs_jobid:
        raise EvidenceError("go-kill requester does not match inspector")
    value = {"record": "go-kill", "host": observer["host"], "boot_id": observer["boot_id"], "epoch": int(time.time()), "pbs_jobid": pbs_jobid, "probe_sha256": _probe_sha256()}
    _write_json(root / "go-kill", value)
def run_record_crash(root, pid: int, wait_status: int):
    root = _root(root); writer = _writer_info(root)
    request = json.loads((root / "go-kill").read_text())
    if pid != writer["pid"] or wait_status != 137 or request.get("record") != "go-kill" or request.get("probe_sha256") != _probe_sha256():
        raise EvidenceError("controlled SIGKILL evidence is invalid")
    value = {"record": "crash-receipt", "pid": pid, "host": writer["hostname"], "boot_id": writer["boot_id"], "start_token": writer["start_token"], "signal": 9, "wait_status": wait_status, "alive_after": "no"}
    _write_json(root / "crash-receipt", value)
def _crash_evidence(root: Path, kind: str, writer: dict, inspect_receipt: dict) -> tuple[str, str]:
    if kind == "receipt":
        request = json.loads((root / "go-kill").read_text())
        crash = json.loads((root / "crash-receipt").read_text())
        expected = {"record": "crash-receipt", "pid": writer["pid"], "host": writer["hostname"],
                    "boot_id": writer["boot_id"], "start_token": writer["start_token"],
                    "signal": 9, "wait_status": 137, "alive_after": "no"}
        if (crash != expected or request.get("record") != "go-kill"
                or request.get("host") != inspect_receipt["host"]
                or request.get("boot_id") != inspect_receipt["boot_id"]
                or request.get("pbs_jobid") != inspect_receipt["pbs_jobid"]
                or request.get("probe_sha256") != _probe_sha256()):
            raise EvidenceError("receipt crash chain is invalid")
        return "controlled-sigkill-receipt", DOES_NOT_PROVE["L-A"]
    if (root / "go-kill").exists() or (root / "go-kill").is_symlink():
        raise EvidenceError("scheduler leg must not contain go-kill")
    text = (root / "scheduler-terminal.txt").read_text()
    lines = text.splitlines()
    request_id = re.sub(r"^\d+:", "", writer["pbs_jobid"], count=1)
    request_ids = []
    for line in lines:
        match = re.fullmatch(r"\s*Request ID:\s*(\S+)\s*", line)
        if match:
            request_ids.append(match.group(1))
    if (not request_id or request_id not in request_ids
            or not any("signal SIGKILL" in line
                       and "Exceeded per-req elapse time limit" in line
                       for line in lines)):
        raise EvidenceError("scheduler terminal accounting is invalid")
    return "scheduler-accounting", SCHEDULER_PROXY
def run_repair(root, crash_evidence, allow_same_host=False, recorder=None, require_fstype=None):
    root, observer = _root(root), _identity()
    result = {"result": "QUARANTINE", "classifications": [], "mount": None,
              "crash_evidence": None, "does_not_prove": DOES_NOT_PROVE["L-A"], "acceptance_conditions": []}
    try:
        records, armed, writer, _ = _context(root)
        if records[-1]["record"] != "mutated":
            raise EvidenceError("repair requires mutated as the current state")
        active = root / "journal/active"
        if active.is_symlink() or not active.is_file() or active.read_bytes() != b"attempt.jsonl\n":
            raise EvidenceError("active locator is invalid")
        require_cross_client(armed["writer"], observer, allow_same_host)
        result["mount"] = _mount_info(root)
        if require_fstype is not None and result["mount"]["fstype"] != require_fstype:
            raise EvidenceError("unexpected filesystem type")
        inspect_receipt, _ = _validated_inspect_receipt(root)
        if (inspect_receipt["host"] != observer["host"] or inspect_receipt["boot_id"] != observer["boot_id"]):
            raise EvidenceError("repairer is not the inspecting client")
        evidence, limitation = _crash_evidence(root, crash_evidence, writer, inspect_receipt)
        result.update(crash_evidence=evidence, does_not_prove=limitation)
        states = _states(root, armed); result["classifications"] = states
        result["acceptance_conditions"] = ["valid journal and active locator", "valid inspect receipt",
                                            "source hash binding", "different host and boot_id",
                                            "required crash evidence", "all-target preflight"]
        if repair_decision(item["classification"] for item in states) != "RESTORED":
            return result, 4
        seq = len(records)
        recovering = {"record": "recovering", "seq": seq, "crash_evidence": evidence,
                      "observer": observer, "epoch": int(time.time())}
        _append(root / "journal/attempt.jsonl", recovering, recorder, "recovering_append")
        _sync(root / "journal/attempt.jsonl", recorder, "recovering_fsync")
        for state, item in zip(states, armed["targets"]):
            target = _target(root, item["rel"])
            if _sha(target.read_bytes()) != state["sha256"]:
                raise EvidenceError("target changed after preflight")
            temp = target.parent / (item["temp_name"] + ".restore")
            with temp.open("xb") as stream:
                stream.write(base64.b64decode(item["original_b64"])); stream.flush()
                os.fsync(stream.fileno()); record_event(recorder, "restore_temp_fsync")
            os.replace(temp, target); record_event(recorder, "restore_replace")
            _sync(target.parent, recorder, "restore_dir_fsync", True)
        if any(_sha(_target(root, x["rel"]).read_bytes()) != x["original_sha256"] for x in armed["targets"]):
            raise EvidenceError("restore verification failed")
        record_event(recorder, "restore_verify")
        _append(root / "journal/attempt.jsonl", {"record": "clean", "seq": seq + 1}, recorder, "clean_append")
        _sync(root / "journal/attempt.jsonl", recorder, "clean_fsync")
        active.unlink(); _sync(root / "journal", recorder, "active_dir_fsync", True)
        result["result"] = "RESTORED"
        return result, 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, EvidenceError) as exc:
        result["error"] = str(exc)
        return result, 4
def run_verify(root):
    root = _root(root)
    try:
        records, armed, _, _ = _context(root)
        original = all(_sha(_target(root, x["rel"]).read_bytes()) == x["original_sha256"] for x in armed["targets"])
        clean = records[-1]["record"] == "clean"
    except (OSError, ValueError, KeyError, json.JSONDecodeError, EvidenceError):
        original = clean = False
    passed = bool(original and clean)
    return {"result": "PASS" if passed else "FAIL", "targets_original": bool(original),
            "clean_terminal": clean, "does_not_prove": DOES_NOT_PROVE["L-A"]}, 0 if passed else 5
def _load_result(root: Path, name: str) -> dict:
    value = json.loads((root / name).read_text())
    if not isinstance(value, dict) or not isinstance(value.get("rc"), int):
        raise EvidenceError(f"invalid {name}")
    return value
def _derive_leg(name: str, root: Path) -> tuple[str, list[str]]:
    try:
        root = _root(root); records, armed, writer, _ = _context(root)
        receipt, inspect = _validated_inspect_receipt(root)
        repair, verify = _load_result(root, "repair.json"), _load_result(root, "verify.json")
        require_cross_client(armed["writer"], {"host": receipt["host"], "boot_id": receipt["boot_id"]})
        if inspect.get("mount", {}).get("fstype") != "lustre" or repair.get("mount", {}).get("fstype") != "lustre": raise EvidenceError("leg evidence is not from Lustre")
        reasons = ["inspect receipt and source binding", "cross-client identity", "journal state machine"]
        if name == "L-A":
            _crash_evidence(root, "receipt", writer, receipt)
            complete = len(inspect.get("classifications", [])) == len(TARGETS) and all(x.get("classification") in {"ORIGINAL", "MUTATED"} for x in inspect["classifications"])
            passed = (complete and not inspect.get("expected_partial_prefix") and records[-1]["record"] == "clean"
                      and repair.get("rc") == 0 and repair.get("result") == "RESTORED"
                      and repair.get("crash_evidence") == "controlled-sigkill-receipt"
                      and verify.get("rc") == 0 and verify.get("result") == "PASS" and run_verify(root)[1] == 0)
            reasons += ["complete bytes before kill", "controlled SIGKILL receipt", "restore and reopen verify"]
        elif name == "L-C":
            _crash_evidence(root, "receipt", writer, receipt)
            exact = len(inspect.get("classifications", [])) == len(TARGETS) and all(x.get("partial_prefix") is True and x.get("classification") == "OTHER" for x in inspect["classifications"])
            passed = (exact and inspect.get("expected_partial_prefix") is True and records[-1]["record"] == "mutated" and all(x["partial_prefix"] for x in _states(root, armed))
                      and repair.get("rc") == 4 and repair.get("result") == "QUARANTINE"
                      and repair.get("crash_evidence") == "controlled-sigkill-receipt"
                      and verify.get("rc") == 5 and verify.get("result") == "FAIL")
            reasons += ["exact half mutated prefix", "repair quarantines without writing", "verify remains non-clean"]
        else:
            _crash_evidence(root, "scheduler", writer, receipt)
            complete = len(inspect.get("classifications", [])) == len(TARGETS) and all(x.get("classification") in {"ORIGINAL", "MUTATED"} for x in inspect["classifications"])
            passed = (complete and records[-1]["record"] == "clean" and repair.get("rc") == 0
                      and repair.get("result") == "RESTORED" and repair.get("crash_evidence") == "scheduler-accounting"
                      and verify.get("rc") == 0 and verify.get("result") == "PASS" and run_verify(root)[1] == 0)
            reasons += ["complete bytes", "scheduler terminal accounting", "restore and reopen verify"]
        return ("PASS" if passed else "FAIL"), reasons
    except (OSError, ValueError, KeyError, json.JSONDecodeError, EvidenceError) as exc:
        return "FAIL", [f"invalid or missing evidence: {exc}"]
def run_verdict(leg_roots: dict[str, Path]) -> tuple[dict, int]:
    legs = {"L-B": {"result": "UNKNOWN", "acceptance_conditions": ["admin-approved physical node death"],
                     "does_not_prove": DOES_NOT_PROVE["L-B"]}}
    for name in ("L-A", "L-C", "L-B2"):
        if name in leg_roots:
            result, conditions = _derive_leg(name, leg_roots[name])
        else:
            result, conditions = "UNKNOWN", ["leg root was not supplied"]
        legs[name] = {"result": result, "acceptance_conditions": conditions,
                      "does_not_prove": DOES_NOT_PROVE[name]}
    flat = {name: value["result"] for name, value in legs.items()}
    verdict = aggregate_verdict(flat)
    return {"verdict": verdict, "legs": legs, "required": list(REQUIRED_LEGS)}, 0 if verdict == "GO" else 8
def _parser():
    parser = argparse.ArgumentParser(); commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-root"); prepare.add_argument("--root", required=True); prepare.add_argument("--output", required=True)
    write = commands.add_parser("write"); write.add_argument("--root", required=True)
    write.add_argument("--mode", choices=("atomic", "inplace-partial"), required=True)
    write.add_argument("--pbs-jobid", required=True); write.add_argument("--pbs-sha256", required=True)
    write.add_argument("--block", action="store_true")
    inspect = commands.add_parser("inspect"); inspect.add_argument("--root", required=True)
    inspect.add_argument("--output", required=True); inspect.add_argument("--receipt", required=True)
    inspect.add_argument("--pbs-jobid", required=True); inspect.add_argument("--expect-partial-prefix", action="store_true")
    inspect.add_argument("--require-fstype")
    request = commands.add_parser("request-kill"); request.add_argument("--root", required=True); request.add_argument("--pbs-jobid", required=True)
    crash = commands.add_parser("record-crash"); crash.add_argument("--root", required=True)
    crash.add_argument("--pid", type=int, required=True); crash.add_argument("--wait-status", type=int, required=True)
    repair = commands.add_parser("repair"); repair.add_argument("--root", required=True); repair.add_argument("--output", required=True)
    repair.add_argument("--crash-evidence", choices=("receipt", "scheduler"), required=True); repair.add_argument("--require-fstype")
    verify = commands.add_parser("verify"); verify.add_argument("--root", required=True); verify.add_argument("--output", required=True)
    verdict = commands.add_parser("verdict"); verdict.add_argument("--root", required=True); verdict.add_argument("--output", required=True)
    verdict.add_argument("--leg-root", action="append", required=True)
    return parser
def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "prepare-root":
        root, ancestry = _ensure_root(args.root); output = _artifact(root, args.output, "root-durability.json")
        _write_json(output, ancestry); return 0
    if args.command == "write":
        run_writer(args.root, args.mode, block=args.block, pbs_jobid=args.pbs_jobid, pbs_sha256=args.pbs_sha256); return 0
    root = _root(args.root)
    if args.command == "inspect":
        output, receipt_path = _artifact(root, args.output, "inspect.json"), _artifact(root, args.receipt, "inspect-receipt")
        result, rc = run_inspect(root, expect_partial_prefix=args.expect_partial_prefix, require_fstype=args.require_fstype)
        result["rc"] = rc; _write_json(output, result)
        if rc == 0:
            _write_json(receipt_path, _inspect_receipt(root, result, args.pbs_jobid, output))
        return rc
    if args.command == "request-kill":
        run_request_kill(root, args.pbs_jobid); return 0
    if args.command == "record-crash":
        run_record_crash(root, args.pid, args.wait_status); return 0
    if args.command == "repair":
        output = _artifact(root, args.output, "repair.json")
        result, rc = run_repair(root, args.crash_evidence, require_fstype=args.require_fstype)
    elif args.command == "verify":
        output = _artifact(root, args.output, "verify.json"); result, rc = run_verify(root)
    else:
        output = _artifact(root, args.output, "verdict.json"); roots = {}
        for item in args.leg_root:
            name, separator, value = item.partition("=")
            if not separator or name not in {"L-A", "L-C", "L-B2"} or name in roots or not Path(value).is_absolute():
                _parser().error("--leg-root は一意な L-A|L-C|L-B2=/absolute/path")
            roots[name] = Path(value)
        if any(name not in roots for name in REQUIRED_LEGS):
            _parser().error("L-A と L-C の --leg-root は必須")
        result, rc = run_verdict(roots)
    result["rc"] = rc; _write_json(output, result)
    return rc
if __name__ == "__main__":
    raise SystemExit(main())
