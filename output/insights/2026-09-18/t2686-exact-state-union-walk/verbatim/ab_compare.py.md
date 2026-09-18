"""[T-2686] 旧/新 check_branch_landed の同一入力比較 driver (repo 外、production CLI/定数は触らない)。

usage: ab_compare.py REPO TARGET_OID OLD_MODULE NEW_MODULE OUT_DIR [--rounds N] [--timeout S]
旧/新/旧/新 の順に assess() を呼び、各走で main OID を前後照合し、raw payload・wall・process 数を保存、
timing 系 field (elapsed_seconds の全出現, top-level timing) を除いた canonical JSON を byte 比較する。
"""
import argparse, hashlib, importlib.util, json, os, platform, socket, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main_oid(repo: Path) -> str:
    return subprocess.run(["git", "rev-parse", "main"], cwd=repo, stdout=subprocess.PIPE,
                          check=True, text=True).stdout.strip()


def strip_timing(value):
    if isinstance(value, dict):
        return {k: strip_timing(v) for k, v in value.items() if k != "elapsed_seconds"}
    if isinstance(value, list):
        return [strip_timing(v) for v in value]
    return value


def canonical(payload) -> bytes:
    return json.dumps(strip_timing({k: v for k, v in payload.items() if k != "timing"}), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normally_completed(payload):
    phases = payload.get("phase_outcomes", {})
    required = ("preflight", "closure", "proof", "history_scan", "observations", "ref_snapshot")
    if any(phases.get(phase) not in {"matched", "not-matched", "not-applicable"} for phase in required):
        return False

    def complete(value):
        if isinstance(value, dict):
            if value.get("outcome") in {"error", "truncated"} or value.get("truncated") is True:
                return False
            # The unused any-path observation is explicitly not-run / not-needed.
            if value.get("outcome") == "not-run" and value.get("reason") != "not-needed":
                return False
            return all(complete(v) for v in value.values())
        if isinstance(value, list):
            return all(complete(v) for v in value)
        return True

    return complete(payload)


def observe_host():
    ps = subprocess.run(["ps", "-eo", "pid,ppid,user,stat,pcpu,pmem,etimes,comm"],
                        capture_output=True, text=True, timeout=10)
    return {"time_utc": datetime.now(timezone.utc).isoformat(), "loadavg": os.getloadavg(),
            "ps_rc": ps.returncode, "processes": ps.stdout, "ps_stderr": ps.stderr}


def run_once(mod, repo: Path, target: str, timeout: float):
    start = observe_host()
    before = main_oid(repo)
    t = time.monotonic()
    payload = mod.assess(repo, target, timeout_seconds=timeout)
    wall = time.monotonic() - t
    after = main_oid(repo)
    return payload, wall, before, after, start, observe_host()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", type=Path); ap.add_argument("target", choices=["559bcbc29cfa27412f103b608e8ac708dcfae6b9"]); ap.add_argument("old_module", type=Path)
    ap.add_argument("new_module", type=Path); ap.add_argument("out_dir", type=Path)
    ap.add_argument("--rounds", type=int, choices=[2], default=2); ap.add_argument("--timeout", type=float, choices=[900.0], default=900.0)
    a = ap.parse_args()
    a.repo = a.repo.resolve()
    sys.path.insert(0, str(a.repo))
    a.out_dir.mkdir(parents=True, exist_ok=True)
    old = load(a.old_module, "cbl_old"); new = load(a.new_module, "cbl_new")
    meta = {
        "repo": str(a.repo), "target": a.target, "timeout": a.timeout,
        "old_module": str(a.old_module), "old_sha256": hashlib.sha256(a.old_module.read_bytes()).hexdigest(),
        "new_module": str(a.new_module), "new_sha256": hashlib.sha256(a.new_module.read_bytes()).hexdigest(),
        "python_version": sys.version, "python_executable": sys.executable,
        "git_version": subprocess.run(["git", "--version"], cwd=a.repo, check=True,
                                      capture_output=True, text=True).stdout.strip(),
        "hostname": socket.gethostname(), "platform": platform.platform(), "pid": os.getpid(),
        "started": observe_host(),
        "load_observation_limit": "Endpoint ps/loadavg snapshots only; visibility may be restricted, "
                                  "transient co-load and I/O interference are not excluded; "
                                  "wall times do not establish exclusive use or general speedup.",
        "runs": [],
    }
    canon = {}
    for r in range(a.rounds):
        for label, mod in (("old", old), ("new", new)):
            payload, wall, before, after, start, end = run_once(mod, a.repo, a.target, a.timeout)
            name = f"{label}-{r + 1}"
            (a.out_dir / f"{name}.json").write_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            c = canonical(payload)
            (a.out_dir / f"{name}.canonical.json").write_bytes(c)
            canon[name] = c
            run = {
                "name": name, "wall_seconds": round(wall, 3), "main_before": before, "main_after": after,
                "main_stable": before == after, "verdict": payload["decision"],
                "normally_completed": normally_completed(payload),
                "git_child_processes": payload["timing"].get("git_child_processes"),
                "history_candidate_walks": payload["timing"].get("history_candidate_walks"),
                "history_candidate_walk_seconds": payload["timing"].get("history_candidate_walk_seconds"),
                "canonical_sha256": hashlib.sha256(c).hexdigest(),
                "started": start, "finished": end,
            }
            meta["runs"].append(run)
            (a.out_dir / "summary.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            print(json.dumps(run, ensure_ascii=False), flush=True)
    mains = {r["main_before"] for r in meta["runs"]} | {r["main_after"] for r in meta["runs"]}
    meta["main_oids_seen"] = sorted(mains)
    meta["all_runs_same_main"] = len(mains) == 1
    meta["canonical_all_identical"] = len(set(canon.values())) == 1
    meta["finished"] = observe_host()
    meta["git_process_comparisons"] = [
        {"round": i // 2 + 1, "old": meta["runs"][i]["git_child_processes"],
         "new": meta["runs"][i + 1]["git_child_processes"],
         "old_gt_new": meta["runs"][i]["git_child_processes"] > meta["runs"][i + 1]["git_child_processes"]}
        for i in (0, 2)]
    meta["all_old_gt_new"] = all(pair["old_gt_new"] for pair in meta["git_process_comparisons"])
    meta["all_runs_normally_completed"] = all(r["normally_completed"] for r in meta["runs"])
    (a.out_dir / "summary.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"all_runs_same_main": meta["all_runs_same_main"],
                      "canonical_all_identical": meta["canonical_all_identical"]}, ensure_ascii=False))
    return 0 if meta["all_runs_normally_completed"] and meta["canonical_all_identical"] and meta["all_runs_same_main"] and meta["all_old_gt_new"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
