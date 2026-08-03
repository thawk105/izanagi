# -*- coding: utf-8 -*-
"""S-1 検証相の long extime を実測で確定する校正 driver。

候補 ``(3, 6, 10)`` を昇順に各 1 回だけ trace run + verifier 実走し、verifier
wall time が 600 秒以下だった最大 extime を採る。超過後の候補は測らず、extime=3
から超過した場合は下限へ丸めず失敗する (phase3-main-experiment.md「2026-07-15
着手時確定 — S-1 サンプル設計 4 点」層 1 (iv 付属)、規律 2/4)。

校正対象は read-heavy (rr95) の系側 gate ``g_rl``。stock で校正すると、D50 で既知の
gate-on throughput 増 (+61〜99%) により本番 trace の transaction 数を過小評価して
extime を過大選択しうるため、絶対 throughput が最大と見込む最重条件を保守側に選ぶ。後続の
他 workload/構成で個別 verify が 600 秒を超える見込みが出た場合は extime を下げ、
事前登録済みの ``N_verify`` は削らない、という安全弁は同節の規定どおり維持する。

``g_rl`` は s8a_trigger_sweep の既存経路と同じく subset 名・述語・genome を生成し、
template patch → diff quarantine → buildcache の順に trace-enabled build を作る。
起動時には known_axes_freeze を verify_document で検証してから、構築した flags/述語と
read-heavy.system_gate の完全一致を要求する。

実走は単一テナントを証明できるホストでだけ行う。この sandbox では main を実行しない。

  python3 orchestrator/campaign/s1_verify_extime_calibration.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import (axis_trigger_gating, buildcache, p3_s4_loop, pin,  # noqa: E402
                      s1_known_axes_freeze, s8a_trigger_sweep, source_digest)
from campaign.build_admission import (GeneratorId, attest_generator_output,  # noqa: E402
                                      build_run_context, derive_build_admission)
from campaign.layout import repo_output_root                              # noqa: E402
from campaign.p2_2 import (CLK, NUMA, RECORDS, THREADS,                  # noqa: E402
                           _assert_single_tenant)
from campaign.patchharness import applied, assert_pinned_clean           # noqa: E402


ENV_TAG = "linux-baremetal"
PIN = pin.CURRENT_PIN
CONFIG_NAME = "s1-verify-extime"
WORKLOAD_NAME = "read-heavy"
GATE_NAME = "g_rl"
EXTIME_CANDIDATES = (3, 6, 10)
GATE2_VERIFIER_WALL_S = 600.0
MIN_FREE_DISK_GB = 20.0
TRACE_RUN_TIMEOUT_S = 120.0
# 600 秒は採否閾値であって verifier の強制終了時刻ではない。超過候補も完走結果の
# serializable verdict を確認してから棄却する必要があるため、liveness 用 hard timeout
# だけを別に置く。timeout は候補不通過への丸めでなく校正全体の失敗になる。
VERIFIER_HARD_TIMEOUT_S = 1200.0

CALIBRATION_FLAGS = {
    "ycsb_tuple_num": str(RECORDS),
    **s8a_trigger_sweep.WORKLOADS[WORKLOAD_NAME],
    "ycsb_max_ope": "10",
    "thread_num": str(THREADS),
}

DECISION_RULE = (
    "extime 3,6,10 を昇順に各 1 回実測し、verifier walltime <= 600s の最大値を採る。"
    "walltime > 600s で残候補を打ち切り、extime=3 も超過なら候補なしとして失敗する。"
    "verdict != serializable または certified != true は校正全体を失敗させる。"
)


class CalibrationError(RuntimeError):
    """校正入力・実走結果を安全に採用できないときの fail-closed 例外。"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _finite_number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalibrationError(f"{label} が数値でない: {value!r}")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise CalibrationError(f"{label} が有限な非負値でない: {value!r}")
    return number


def choose_extime(results: Sequence[Mapping], limit_s: float) -> int:
    """実測済みの候補 prefix から通過した最大 extime を選ぶ純関数。

    ``results`` は EXTIME_CANDIDATES の昇順 prefix でなければならない。超過候補より
    後の結果を受け入れないことで、停止規則を consumer 側でも機械検査する。
    """
    limit = _finite_number(limit_s, "limit_s")
    if limit <= 0:
        raise CalibrationError(f"limit_s は正でなければならない: {limit_s!r}")
    if not results:
        raise CalibrationError("候補結果が空 — extime を選べない")
    if len(results) > len(EXTIME_CANDIDATES):
        raise CalibrationError("候補結果数が事前登録済み候補数を超えている")

    chosen: Optional[int] = None
    exceeded = False
    for index, result in enumerate(results):
        if not isinstance(result, Mapping):
            raise CalibrationError(f"候補結果が object でない: index={index}")
        expected = EXTIME_CANDIDATES[index]
        extime = result.get("extime")
        if isinstance(extime, bool) or extime != expected:
            raise CalibrationError(
                f"候補順が不正: index={index} expected={expected} actual={extime!r}")
        if exceeded:
            raise CalibrationError("600s 超過候補より後の候補が実測されている")
        wall = _finite_number(result.get("verifier_walltime_s"),
                              f"extime={extime} verifier_walltime_s")
        if wall <= limit:
            chosen = int(extime)
        else:
            exceeded = True

    if chosen is None:
        raise CalibrationError(
            f"extime={EXTIME_CANDIDATES[0]} も verifier walltime > {limit:g}s — "
            "下限へ丸めず候補なしとして失敗")
    return chosen


def _validate_candidate(result: Mapping, expected_extime: int) -> None:
    required = {
        "extime", "run_walltime_s", "trace_files", "trace_bytes", "trace_lines",
        "verifier_walltime_s", "maxrss_gb", "txns", "edges", "verdict", "certified",
    }
    if not isinstance(result, Mapping) or set(result) != required:
        actual = set(result) if isinstance(result, Mapping) else set()
        raise CalibrationError(
            f"候補結果 schema が不一致: missing={sorted(required - actual)} "
            f"extra={sorted(actual - required)}")
    if result["extime"] != expected_extime or isinstance(result["extime"], bool):
        raise CalibrationError(
            f"実測候補 extime が要求値と不一致: expected={expected_extime} "
            f"actual={result['extime']!r}")
    for key in ("run_walltime_s", "verifier_walltime_s", "maxrss_gb"):
        _finite_number(result[key], f"extime={expected_extime} {key}")
    for key in ("trace_files", "trace_bytes", "trace_lines", "txns", "edges"):
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise CalibrationError(
                f"extime={expected_extime} {key} が非負整数でない: {value!r}")
    if result["verdict"] != "serializable" or result["certified"] is not True:
        raise CalibrationError(
            f"extime={expected_extime} verifier anomaly: "
            f"verdict={result['verdict']!r} certified={result['certified']!r} — "
            "校正値を選ばず全体を失敗")


def calibrate_candidates(
        measure_once: Callable[[int], Mapping],
        candidates: Sequence[int] = EXTIME_CANDIDATES,
        limit_s: float = GATE2_VERIFIER_WALL_S) -> tuple[List[Dict], int]:
    """callable 注入可能な候補ループ。超過後の callable は呼ばない。"""
    if tuple(candidates) != EXTIME_CANDIDATES:
        raise CalibrationError(
            f"候補列は事前登録済み {EXTIME_CANDIDATES} でなければならない: {candidates!r}")
    limit = _finite_number(limit_s, "limit_s")
    if limit <= 0:
        raise CalibrationError("limit_s は正でなければならない")

    results: List[Dict] = []
    for extime in candidates:
        result = dict(measure_once(extime))
        _validate_candidate(result, extime)
        results.append(result)
        if float(result["verifier_walltime_s"]) > limit:
            break
    return results, choose_extime(results, limit)


def _constructed_target() -> Dict:
    """s8a の subset→述語→genome 経路で read-heavy の g_rl を構築する。"""
    reasons = ("readvali-locked",)
    name = s8a_trigger_sweep.subset_name(reasons)
    predicate = s8a_trigger_sweep.predicate_for(reasons)
    genome = s8a_trigger_sweep._genome(1)
    return {"name": name, "flags": dict(genome.flags),
            "gate_predicate": predicate, "genome": genome}


def validated_target(
        freeze_doc: Mapping, *,
        verify_fn: Optional[Callable[[Mapping], None]] = None,
        target_builder: Optional[Callable[[], Mapping]] = None) -> Dict:
    """freeze を検証後、構築対象との完全一致を検査する (テストでは callable 注入)。"""
    verifier = verify_fn or s1_known_axes_freeze.verify_document
    builder = target_builder or _constructed_target
    verifier(freeze_doc)
    try:
        frozen = freeze_doc["entries"][WORKLOAD_NAME]["system_gate"]
    except (KeyError, TypeError) as e:
        raise CalibrationError("freeze に entries.read-heavy.system_gate がない") from e
    target = dict(builder())
    for key in ("name", "flags", "gate_predicate", "genome"):
        if key not in target:
            raise CalibrationError(f"構築対象に {key} がない")
    if target["name"] != GATE_NAME:
        raise CalibrationError(
            f"構築 subset 名が {GATE_NAME} と不一致: {target['name']!r}")
    if (frozen.get("name") != target["name"]
            or frozen.get("flags") != target["flags"]
            or frozen.get("gate_predicate") != target["gate_predicate"]):
        raise CalibrationError(
            "構築した g_rl の flags/gate_predicate が known_axes_freeze の "
            "read-heavy.system_gate と不一致")
    return target


def _load_validated_target(path: Path = s1_known_axes_freeze.FREEZE_PATH) -> Dict:
    try:
        with path.open(encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise CalibrationError(f"freeze JSON を読めない: {path}: {e}") from e
    target = validated_target(doc)  # entries を使う前に verify_document を必ず通す。
    target["freeze_doc"] = doc
    return target


def _assert_free_disk(path: str) -> float:
    free_gb = shutil.disk_usage(path).free / 2**30
    if free_gb < MIN_FREE_DISK_GB:
        raise CalibrationError(
            f"空きディスク {free_gb:.1f}GB < {MIN_FREE_DISK_GB}GB ({path}) — "
            "最大候補 extime=10 の trace を安全に置けない")
    return free_gb


def _run_once(binary: str, flags: Mapping[str, str], extime: int) -> Dict:
    """trace-enabled binary を 1 回だけ実走し、trace 統計と一時 dir を返す。"""
    trace_dir = tempfile.mkdtemp(prefix=f"izanagi_s1_extime{extime}_trace_")
    os.makedirs(os.path.join(trace_dir, "log"), exist_ok=True)
    args = list(NUMA) + [binary] + [f"-{key}={value}" for key, value in flags.items()] \
        + [f"-extime={extime}", f"-clocks_per_us={CLK}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=trace_dir)
    started = time.monotonic()
    try:
        proc = subprocess.run(args, env=env, capture_output=True, text=True,
                              timeout=TRACE_RUN_TIMEOUT_S, cwd=trace_dir)
        wall = time.monotonic() - started
        if proc.returncode != 0:
            raise CalibrationError(
                f"trace run rc={proc.returncode} extime={extime}: "
                f"{proc.stderr.strip()[-400:]}")
        files = sorted(
            entry.path for entry in os.scandir(trace_dir)
            if entry.is_file() and entry.name.startswith("trace_")
            and entry.name.endswith(".log"))
        if not files:
            raise CalibrationError(f"extime={extime} の trace file が 1 件もない")
        lines = 0
        for file_path in files:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                lines += sum(1 for _ in f)
        return {
            "run_walltime_s": wall,
            "trace_files": len(files),
            "trace_bytes": sum(os.path.getsize(file_path) for file_path in files),
            "trace_lines": lines,
            "_trace_dir": trace_dir,
        }
    except Exception:
        shutil.rmtree(trace_dir, ignore_errors=True)
        raise


def _verifier_run(trace_dir: str) -> Dict:
    """verifier を /usr/bin/time -v 配下の別プロセスで実走する。"""
    cmd = ["/usr/bin/time", "-v", sys.executable, "-m", "verifier",
           trace_dir, "--json", "--quiet"]
    started = time.monotonic()
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=VERIFIER_HARD_TIMEOUT_S,
        cwd=str(_repo_root() / "orchestrator"))
    wall = time.monotonic() - started
    match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", proc.stderr)
    if match is None:
        raise CalibrationError(
            f"verifier maxrss を /usr/bin/time 出力から読めない (rc={proc.returncode}): "
            f"{proc.stderr[-300:]}")
    try:
        payload = json.loads(proc.stdout)
        rows = payload["results"]
        if not isinstance(rows, list) or len(rows) != 1:
            raise CalibrationError(f"verifier results が 1 件でない: {len(rows)!r}")
        result = rows[0]
        stats = result["stats"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise CalibrationError(
            f"verifier 出力を解釈できない (rc={proc.returncode}): "
            f"{proc.stdout[:300]} / {proc.stderr[-300:]}") from e
    return {
        "verifier_walltime_s": wall,
        "maxrss_gb": int(match.group(1)) / 2**20,
        "txns": stats.get("txns"),
        "edges": stats.get("edges"),
        "verdict": result.get("verdict"),
        "certified": result.get("certified"),
    }


def _measure_candidate(binary: str, extime: int) -> Dict:
    """1 候補を admission → trace run → verifier → trace 削除の順で測る。"""
    _assert_single_tenant()  # trace run の直前に毎候補検査する (規律 4)。
    run = _run_once(binary, CALIBRATION_FLAGS, extime)
    trace_dir = run.pop("_trace_dir")
    try:
        verifier = _verifier_run(trace_dir)
        return {"extime": extime, **run, **verifier}
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


def _build_target(target: Mapping) -> Dict:
    root = _repo_root()
    sub = root / "external" / "ccbench"
    patch_path = root / "patches" / axis_trigger_gating.TEMPLATE_PATCH
    genome = target["genome"]
    with applied(str(patch_path), PIN, str(sub)):
        quarantine, _base, _edited, _diff = p3_s4_loop.quarantine(
            str(sub), target["gate_predicate"],
            marker_id=axis_trigger_gating.MARKER_ID,
            source_rel=axis_trigger_gating.SOURCE_REL, write=True)
        if not quarantine.passed:
            raise CalibrationError(
                f"g_rl の diff quarantine が reject: {quarantine.reason}")
        build_context = build_run_context(generator_id=GeneratorId.S1_EXTIME_CALIBRATION)
        evidence = source_digest.resolve_evidence(genome, PIN, ccbench_dir=str(sub))
        src_token = evidence.src_token
        capability = attest_generator_output(
            build_context, evidence,
            generator_input_sha256=hashlib.sha256(
                json.dumps(target, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
        )
        built = buildcache.build(genome, PIN, trace=True, ccbench_dir=str(sub),
                                 src_token=src_token,
                                 admission=derive_build_admission(
                                     build_context, evidence,
                                     generator_receipt=capability),
                                 build_context=build_context,
                                 source_evidence=evidence)
    return {
        "binary": built.binary,
        "src_token": src_token,
        "bin_hash": built.bin_hash,
        "cached": built.cached,
        "configure_cmd": built.configure_cmd,
        "build_cmd": built.build_cmd,
        "template_patch": axis_trigger_gating.TEMPLATE_PATCH,
    }


def _write_md(path: Path, result: Mapping) -> None:
    lines = [
        "# S-1 検証相 extime 校正結果", "",
        f"- env: {result['env_tag']} / ccbench pin: `{result['ccbench_commit']}`",
        f"- 構成: {WORKLOAD_NAME} (rr95) × `{GATE_NAME}` / genome: `{result['genome']}`",
        f"- 採用 extime: **{result['chosen_extime']}s** / 上限: {result['limit_s']}s", "",
        "## 保守側の校正対象", "",
        "D50 では系側 gate が stock より +61〜99% 高 throughput であり、trace transaction 数も "
        "増えるため、stock 校正は extime を過大選択しうる。絶対 throughput 最大と見込む "
        "read-heavy (rr95) × g_rl を最重条件として校正した。", "",
        "他 workload/構成で個別 verify が 600s を超える見込みが出た場合は extime を下げる。"
        "事前登録済みの N_verify は削らない (phase3-main-experiment.md 層 1 (iv 付属) の安全弁)。",
        "", "## 候補", "",
        "| extime | trace run | trace | verifier | maxrss | txns | edges | verdict |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for candidate in result["candidates"]:
        lines.append(
            f"| {candidate['extime']}s | {candidate['run_walltime_s']:.2f}s | "
            f"{candidate['trace_files']} files / {candidate['trace_bytes'] / 2**30:.2f}GiB / "
            f"{candidate['trace_lines']} lines | {candidate['verifier_walltime_s']:.2f}s | "
            f"{candidate['maxrss_gb']:.2f}GiB | {candidate['txns']} | "
            f"{candidate['edges']} | {candidate['verdict']} |")
    lines += ["", "## 選定規則", "", result["decision_rule"], "",
              "詳細な構成 provenance と全候補の生値は同名 JSON に記録した。", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = _repo_root()
    sub = root / "external" / "ccbench"
    _assert_single_tenant()
    free_gb = _assert_free_disk(tempfile.gettempdir())
    assert_pinned_clean(str(sub), PIN)
    target = _load_validated_target()
    built = _build_target(target)

    candidates, chosen = calibrate_candidates(
        lambda extime: _measure_candidate(built["binary"], extime))
    freeze_gate = target["freeze_doc"]["entries"][WORKLOAD_NAME]["system_gate"]
    result = {
        "config_name": CONFIG_NAME,
        "env_tag": ENV_TAG,
        "ccbench_commit": PIN,
        "genome": target["genome"].canonical(),
        "configuration_provenance": {
            "workload": WORKLOAD_NAME,
            "workload_flags": CALIBRATION_FLAGS,
            "subset_name": target["name"],
            "gate_predicate": target["gate_predicate"],
            "freeze_path": s1_known_axes_freeze.FREEZE_REL,
            "freeze_frozen_at_head": target["freeze_doc"]["frozen_at_head"],
            "freeze_system_gate": freeze_gate,
            "template_patch": built["template_patch"],
            "src_token": built["src_token"],
            "binary_hash": built["bin_hash"],
            "build_cached": built["cached"],
            "configure_cmd": built["configure_cmd"],
            "build_cmd": built["build_cmd"],
            "free_disk_gb_at_start": round(free_gb, 1),
        },
        "candidates": candidates,
        "chosen_extime": chosen,
        "limit_s": int(GATE2_VERIFIER_WALL_S),
        "decision_rule": DECISION_RULE,
    }
    out_dir = Path(repo_output_root()) / "env" / ENV_TAG / "calibration"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / "s1_verify_extime"
    with (base.with_suffix(".json")).open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    _write_md(base.with_suffix(".md"), result)
    print(f"結果: {base}.json / .md")
    print(f"chosen_extime={chosen}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (CalibrationError, s1_known_axes_freeze.FreezeError,
            subprocess.SubprocessError) as error:
        print(f"fails-closed: {error}", file=sys.stderr)
        sys.exit(1)
