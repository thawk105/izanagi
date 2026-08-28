from __future__ import annotations

import contextlib
import hashlib
import inspect
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import backoff_requested_us as M
from orchestrator.campaign.build_admission import (
    GeneratorId,
    resolve_current_build_admission_policy,
    resolve_immediate_predecessor_build_admission_policy,
)
from tools.pegasus import dispatch_compute as DISPATCH


def _diagnostic_line(**overrides: int) -> str:
    values = {
        "call_count": 11,
        "requested_us_sum": sum(M.D1106_STATES),
        **{f"state_{state}_call_count": 1 for state in M.D1106_STATES},
        "unknown_state_call_count": 0,
        "counter_overflowed": 0,
        **overrides,
    }
    return M.PREFIX + " " + " ".join(f"{key}={values[key]}" for key in M.FIELD_NAMES)


def _copy_patch_surface(destination: Path) -> None:
    source = _ROOT / "external" / "ccbench"
    shutil.copytree(source / "include", destination / "include")
    (destination / "cmake").mkdir()
    shutil.copy2(source / "cmake" / "Options.cmake", destination / "cmake" / "Options.cmake")
    (destination / "cc" / "silo").mkdir(parents=True)
    for name in ("transaction.cc", "ycsb_silo.cc"):
        shutil.copy2(source / "cc" / "silo" / name, destination / "cc" / "silo" / name)


def _apply(tree: Path, patch: Path) -> None:
    completed = subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "--fuzz=0", "-i", str(patch)],
        cwd=tree,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _compile(tree: Path, source: str, output: Path, *extra: str) -> None:
    unit = output.with_suffix(".cc")
    unit.write_text(source, encoding="utf-8")
    completed = subprocess.run(
        [
            "g++", "-std=c++17", "-O2", "-pthread", "-I", str(tree / "include"),
            *extra, str(unit), "-o", str(output),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def _preprocess_without_includes(
        path: Path, output: Path, requested_us_default: str,
) -> bytes:
    unit = output.with_suffix(".cc")
    unit.write_text(
        "".join(
            line for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
            if not line.lstrip().startswith("#include")
        ),
        encoding="utf-8",
    )
    return subprocess.run(
        [
            "g++", "-std=c++17", "-E", "-P", "-x", "c++",
            "-DADD_ANALYSIS=0", "-DBACK_OFF=1", "-DBACKOFF_FIXED=-1",
            "-DBACKOFF_NOINLINE=0",
            f"-DBACKOFF_REQUESTED_US={requested_us_default}",
            str(unit),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _counter_block(transaction: str) -> str:
    begin_marker = "// IZANAGI_BACKOFF_REQUESTED_US_COUNTER_BEGIN"
    end_marker = "// IZANAGI_BACKOFF_REQUESTED_US_COUNTER_END"
    assert transaction.count(begin_marker) == 1
    assert transaction.count(end_marker) == 1
    begin = transaction.index("\n", transaction.index(begin_marker)) + 1
    end = transaction.index(end_marker)
    return transaction[begin:end]


def _raw_counter_values(stdout: str) -> dict[str, int]:
    lines = [line for line in stdout.splitlines() if line.startswith(M.PREFIX)]
    assert len(lines) == 1
    values = {}
    for token in lines[0].split()[1:]:
        key, raw = token.split("=", 1)
        assert key not in values
        values[key] = int(raw)
    assert set(values) == set(M.FIELD_NAMES)
    return values


def test_fixed_then_diagnostic_uses_production_git_apply_and_reverts_clean(
    tmp_path,
):
    tree = tmp_path / "production-apply"
    _copy_patch_surface(tree)
    subprocess.run(["git", "init", "--quiet", str(tree)], check=True)
    subprocess.run(
        ["git", "-C", str(tree), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tree), "config", "user.name", "Fixture"],
        check=True,
    )
    subprocess.run(["git", "-C", str(tree), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tree), "commit", "--quiet", "-m", "base"],
        check=True,
    )

    fixed = _ROOT / "patches" / "silo-backoff-fixed.patch"
    diagnostic = _ROOT / M.PATCH_REL
    fixed_files = M.patchharness.patch_files(str(fixed), str(tree))
    M.patchharness.apply_patch(str(fixed), str(tree))
    diagnostic_files = M.patchharness.patch_files(str(diagnostic), str(tree))
    expected = {
        "cmake/Options.cmake",
        "include/backoff.hh",
        "cc/silo/transaction.cc",
    }
    assert set(diagnostic_files) == expected
    M.patchharness.apply_patch(str(diagnostic), str(tree))
    assert "BACKOFF_REQUESTED_US" in (
        tree / "cc" / "silo" / "transaction.cc"
    ).read_text(encoding="utf-8")
    assert set(subprocess.check_output(
        ["git", "-C", str(tree), "diff", "--name-only"], text=True,
    ).splitlines()) == expected

    touched = sorted(set(fixed_files) | set(diagnostic_files))
    assert set(touched) == expected
    M.patchharness.revert_worktree(str(tree), touched)
    assert subprocess.check_output(
        ["git", "-C", str(tree), "status", "--porcelain"], text=True,
    ) == ""


def test_mu01_patch_layers_after_fixed_and_default_is_preprocess_and_object_inert(tmp_path):
    baseline = tmp_path / "baseline"
    diagnostic = tmp_path / "diagnostic"
    _copy_patch_surface(baseline)
    _copy_patch_surface(diagnostic)
    fixed = _ROOT / "patches" / "silo-backoff-fixed.patch"
    requested = _ROOT / M.PATCH_REL
    _apply(baseline, fixed)
    _apply(diagnostic, fixed)
    _apply(diagnostic, requested)
    requested_us_default = M.source_digest.parse_options_defaults(
        (diagnostic / "cmake" / "Options.cmake").read_text(encoding="utf-8")
    ).get("BACKOFF_REQUESTED_US")
    assert requested_us_default == "0"

    wrapper = (
        "#define ADD_ANALYSIS 0\n"
        "#define BACKOFF_FIXED -1\n"
        "#define BACKOFF_NOINLINE 0\n"
        f"#define BACKOFF_REQUESTED_US {requested_us_default}\n"
        "#include \"backoff.hh\"\n"
        "void invoke_backoff(std::size_t clocks) { Backoff::backoff(clocks); }\n"
    )
    preprocessed = []
    objects = []
    for index, tree in enumerate((baseline, diagnostic)):
        unit = tmp_path / "inert.cc"
        unit.write_text(wrapper, encoding="utf-8")
        prefix_map = f"-fmacro-prefix-map={tree}=/ccbench"
        pre = subprocess.run(
            [
                "g++", "-std=c++17", "-E", "-P", prefix_map,
                "-I", str(tree / "include"), str(unit),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        obj = tmp_path / f"inert-{index}.o"
        completed = subprocess.run(
            [
                "g++", "-std=c++17", "-O2", "-pthread", "-c",
                prefix_map, "-I", str(tree / "include"), str(unit),
                "-o", str(obj),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
        preprocessed.append(pre)
        objects.append(obj.read_bytes())
    assert preprocessed[0] == preprocessed[1]
    assert objects[0] == objects[1]
    for index, relative in enumerate((
        "include/backoff.hh",
        "cc/silo/transaction.cc",
    )):
        assert _preprocess_without_includes(
            baseline / relative, tmp_path / f"baseline-surface-{index}",
            requested_us_default,
        ) == _preprocess_without_includes(
            diagnostic / relative, tmp_path / f"diagnostic-surface-{index}",
            requested_us_default,
        )


def test_mu02_tls_registry_exit_aggregation_unknown_overflow_and_silo_callsite(
    tmp_path,
):
    tree = tmp_path / "surface"
    _copy_patch_surface(tree)
    _apply(tree, _ROOT / "patches" / "silo-backoff-fixed.patch")
    _apply(tree, _ROOT / M.PATCH_REL)
    transaction = (tree / "cc" / "silo" / "transaction.cc").read_text(
        encoding="utf-8",
    )
    counter_block = _counter_block(transaction)
    harness = r'''
#include <atomic>
#include <cmath>
#include <cstdint>
#include <stdio.h>
#include <limits>
#include <thread>
#include <vector>
#include <x86intrin.h>
''' + counter_block + r'''
int main(int argc, char**) {
  if (argc == 1) {
    std::thread first([] {
      auto& counter = izanagi_backoff_requested_us_worker_counter();
      counter.record(0.0);
      counter.record(100.0);
    });
    std::thread second([] {
      auto& counter = izanagi_backoff_requested_us_worker_counter();
      counter.record(1000.0);
      counter.record(std::numeric_limits<double>::quiet_NaN());
    });
    first.join();
    second.join();
  } else {
    std::thread first([] {
      auto& counter = izanagi_backoff_requested_us_worker_counter();
      counter.call_count_ = ~std::uint64_t{0};
      counter.requested_us_sum_ = ~std::uint64_t{0};
      counter.record(100.0);
    });
    std::thread second([] {
      izanagi_backoff_requested_us_worker_counter().record(0.0);
    });
    first.join();
    second.join();
  }
  return 0;
}
'''
    binary = tmp_path / "counter-harness"
    _compile(tree, harness, binary)
    normal = subprocess.run(
        [str(binary)], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    assert normal.returncode == 0, normal.stderr
    normal_values = _raw_counter_values(normal.stdout)
    assert normal_values["call_count"] == 4
    assert normal_values["requested_us_sum"] == 1100
    assert normal_values["state_0_call_count"] == 1
    assert normal_values["state_100_call_count"] == 1
    assert normal_values["state_1000_call_count"] == 1
    assert normal_values["unknown_state_call_count"] == 1
    assert normal_values["counter_overflowed"] == 0

    overflow = subprocess.run(
        [str(binary), "overflow"], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    assert overflow.returncode == 0, overflow.stderr
    overflow_values = _raw_counter_values(overflow.stdout)
    assert overflow_values["call_count"] == M.UINT64_MAX
    assert overflow_values["requested_us_sum"] == M.UINT64_MAX
    assert overflow_values["state_0_call_count"] == 1
    assert overflow_values["state_100_call_count"] == 1
    assert overflow_values["unknown_state_call_count"] == 0
    assert overflow_values["counter_overflowed"] == 1

    backoff_harness = r'''
#define ADD_ANALYSIS 0
#define BACKOFF_FIXED -1
#define BACKOFF_NOINLINE 0
#define BACKOFF_REQUESTED_US 1
#define GLOBAL_VALUE_DEFINE
#include "backoff.hh"
int main() {
  return Backoff::backoff(1) == 0.0 ? 0 : 1;
}
'''
    backoff_binary = tmp_path / "backoff-counter-harness"
    _compile(tree, backoff_harness, backoff_binary)
    assert subprocess.run([str(backoff_binary)], check=False).returncode == 0
    assert "Backoff::backoff(FLAGS_clocks_per_us)" in transaction
    assert "izanagi_backoff_requested_us_worker_counter().record" in transaction
    assert "thread_local IzanagiBackoffRequestedUsCounter* const" in counter_block
    assert "new IzanagiBackoffRequestedUsCounter" in counter_block
    assert "std::mutex" not in counter_block
    assert counter_block.count("test_and_set") == 1
    record_body = counter_block.split("void record", 1)[1].split("void merge", 1)[0]
    assert "registration_lock_" not in record_body
    assert "workers_" not in record_body
    assert "test_and_set" not in record_body
    assert "~IzanagiBackoffRequestedUsRegistry" in counter_block
    assert counter_block.count(M.PREFIX) == 1


def test_raw_stdout_parser_ignores_normal_metrics_and_returns_only_fifteen_fields():
    stdout = "throughput[tps]: 999999\nabort_rate: 0.9\n" + _diagnostic_line() + "\n"
    values = M.parse_diagnostic_stdout(stdout)
    assert set(values) == set(M.FIELD_NAMES)
    assert len(values) == 15
    assert values["counter_overflowed"] is False
    assert not any(key in values for key in ("throughput[tps]", "abort_rate", "latency[ns]"))


@pytest.mark.parametrize(
    "stdout, message",
    [
        ("", "prefix line count"),
        (_diagnostic_line() + "\n" + _diagnostic_line(), "prefix line count"),
        (_diagnostic_line() + " call_count=11", "duplicate diagnostic field"),
        (_diagnostic_line().replace(" call_count=11", "", 1), "field set mismatch"),
        (_diagnostic_line() + " tps=1", "field set mismatch"),
        (_diagnostic_line(unknown_state_call_count=1, call_count=12), "unknown"),
        (_diagnostic_line(counter_overflowed=1), "overflow"),
        (_diagnostic_line(call_count=10), "call/bucket"),
        (_diagnostic_line(requested_us_sum=5499), "weighted-sum"),
        (_diagnostic_line(**{
            "call_count": 0,
            "requested_us_sum": 0,
            **{f"state_{state}_call_count": 0 for state in M.D1106_STATES},
        }), "call/bucket"),
    ],
)
def test_raw_stdout_parser_fails_closed(stdout, message):
    with pytest.raises(RuntimeError, match=message):
        M.parse_diagnostic_stdout(stdout)


def test_all_fifteen_fields_are_bounded_to_uint64():
    M._require_uint64_fields({field: M.UINT64_MAX for field in M.FIELD_NAMES})
    for field in M.FIELD_NAMES:
        with pytest.raises(RuntimeError, match="outside uint64"):
            M.parse_diagnostic_stdout(_diagnostic_line(**{field: 1 << 64}))


def test_reference_binary_is_bound_to_attempt_build_receipt_and_sha(tmp_path):
    build_dir = tmp_path / "cache" / "identity" / "perf"
    binary = build_dir / "cc" / "silo" / "ycsb_silo.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"attempt-bound perf binary\n")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    payload = {
        "perf_bin": digest[:16],
        "perf_bin_sha256": digest,
        "perf_configure_cmd": ["cmake", "-S", "/ccbench", "-B", str(build_dir)],
        "perf_build_cmd": ["cmake", "--build", str(build_dir), "-j", "48"],
    }
    live = M._require_reference_binary_binding(payload, str(binary))
    assert live["binding_method"] == "live-binary-sha256"
    assert live["live_binary_rehashed"] is True

    binary.write_bytes(b"different binary\n")
    with pytest.raises(RuntimeError, match="SHA differs"):
        M._require_reference_binary_binding(payload, str(binary))
    binary.unlink()
    frozen = M._require_reference_binary_binding(payload, str(binary))
    assert frozen["binding_method"] == "attempt-build-cache-receipt"
    assert frozen["live_binary_rehashed"] is False
    with pytest.raises(RuntimeError, match="differs from perf build receipt"):
        M._require_reference_binary_binding(payload, str(tmp_path / "other/ycsb_silo.exe"))


def test_completion_hash_and_wal_decode_share_one_byte_snapshot(tmp_path):
    root = tmp_path / "reference"
    root.mkdir()
    wal_path = root / "wal.jsonl"
    record = {
        "variant": "variant-a",
        "stage": "build_start",
        "env_tag": "pegasus",
        "ts": 1,
        "payload": {"build_attempt_id": "attempt-a"},
    }
    wal_a = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    wal_path.write_bytes(wal_a)
    runtime_path = root / "runtime.manifest.json"
    runtime_a = b'{"runtime_contract":{"threads":48}}\n'
    runtime_path.write_bytes(runtime_a)
    completion = {"artifacts": {
        "runtime.manifest.json": hashlib.sha256(runtime_a).hexdigest(),
        "wal.jsonl": hashlib.sha256(wal_a).hexdigest(),
    }}
    hashes, snapshots = M._snapshot_completion_artifacts(root, completion)
    wal_path.write_bytes(b'{"replacement":true}\n')
    runtime_path.write_bytes(b'{"runtime_contract":{"threads":1}}\n')
    raw_records, records = M._load_wal_snapshot(snapshots["wal.jsonl"])
    runtime = M._decode_json_object(
        snapshots["runtime.manifest.json"], "runtime fixture",
    )
    assert hashes == completion["artifacts"]
    assert raw_records[0]["variant"] == "variant-a"
    assert records[0].payload["build_attempt_id"] == "attempt-a"
    assert runtime["runtime_contract"]["threads"] == 48


def test_mu03_completion_artifact_tamper_is_rejected_without_volatile_hash_fixture(tmp_path):
    root = tmp_path / "reference"
    root.mkdir()
    artifact = root / "artifact.json"
    artifact.write_bytes(b"{}\n")
    completion = {
        "artifacts": {
            "artifact.json": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        },
    }
    assert M._verify_completion_artifacts(root, completion) == completion["artifacts"]
    artifact.write_bytes(b'{"tampered":true}\n')
    with pytest.raises(RuntimeError, match="SHA mismatch"):
        M._verify_completion_artifacts(root, completion)


def test_mu04_reference_and_diagnostic_roots_are_separate_and_create_only(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    before = reference.stat()
    diagnostic = tmp_path / "diagnostic"
    resolved_reference, resolved_diagnostic = M._assert_output_boundary(
        str(reference), str(diagnostic),
    )
    assert resolved_reference == reference.resolve()
    assert resolved_diagnostic == diagnostic.resolve()
    assert reference.stat().st_mtime_ns == before.st_mtime_ns
    with pytest.raises(RuntimeError, match="inside the reference"):
        M._assert_output_boundary(str(reference), str(reference / "diagnostic"))
    diagnostic.mkdir()
    with pytest.raises(FileExistsError):
        M._assert_output_boundary(str(reference), str(diagnostic))

    create_only = tmp_path / "one.json"
    M._write_create_only(create_only, {"value": 1})
    with pytest.raises(FileExistsError):
        M._write_create_only(create_only, {"value": 2})
    assert json.loads(create_only.read_text(encoding="utf-8")) == {"value": 1}


def test_diagnostic_parent_symlink_swap_cannot_write_reference(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    parent = tmp_path / "diagnostic-parent"
    parent.mkdir()
    moved_parent = tmp_path / "diagnostic-parent-original"
    boundary = M._open_output_boundary(str(reference), str(parent / "diagnostic"))
    parent.rename(moved_parent)
    parent.symlink_to(reference, target_is_directory=True)
    try:
        with pytest.raises(RuntimeError, match="parent changed"):
            boundary.publish({"rep": 0}, {"status": "complete"})
    finally:
        boundary.close()
    assert list(reference.iterdir()) == []
    assert not (moved_parent / "diagnostic").exists()


def test_dirfd_diagnostic_publish_is_create_only(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    parent = tmp_path / "diagnostic-parent"
    parent.mkdir()
    target = parent / "diagnostic"
    boundary = M._open_output_boundary(str(reference), str(target))
    try:
        boundary.publish({"rep": 0}, {"status": "complete"})
    finally:
        boundary.close()
    assert json.loads((target / "rep-000.json").read_text(encoding="utf-8")) == {"rep": 0}
    assert json.loads((target / "manifest.json").read_text(encoding="utf-8")) == {
        "status": "complete",
    }
    with pytest.raises(FileExistsError):
        M._open_output_boundary(str(reference), str(target))


def test_fixed_only_source_must_match_certified_reference_except_checkout_root():
    genome_sha256 = hashlib.sha256(b"silo|BACK_OFF=1").hexdigest()
    fixed = M.source_digest.SourceEvidence(
        schema_version=M.source_digest.SOURCE_EVIDENCE_SCHEMA,
        source_root="/tmp/current-fixed-source",
        ccbench_commit="511c953",
        genome_sha256=genome_sha256,
        src_token="a" * 64,
        source_bytes_sha256="b" * 64,
        tracked_clean=False,
        tracked_diff_sha256="c" * 64,
        tracked_paths=("cmake/Options.cmake", "include/backoff.hh"),
    )
    reference = fixed.as_receipt()
    reference["source_root"] = "/scr/frozen-reference-source"
    M._require_fixed_source_match(reference, fixed)
    reference["source_bytes_sha256"] = "d" * 64
    with pytest.raises(RuntimeError, match="differs"):
        M._require_fixed_source_match(reference, fixed)


def test_mu05_unknown_and_overflow_cannot_enter_value_schema():
    for mutation in (
        {"unknown_state_call_count": 1, "call_count": 12},
        {"counter_overflowed": 1},
    ):
        with pytest.raises(RuntimeError):
            M.parse_diagnostic_stdout(_diagnostic_line(**mutation))


def test_mu06_usage_scope_is_exactly_four_false_and_counter_mutation_cannot_change_it():
    expected = {key: False for key in M.USAGE_ELIGIBILITY_KEYS}
    assert M.usage_eligibility() == expected
    M.validate_usage_eligibility(expected)
    for key in M.USAGE_ELIGIBILITY_KEYS:
        mutated = dict(expected)
        mutated[key] = True
        with pytest.raises(RuntimeError, match="ineligible"):
            M.validate_usage_eligibility(mutated)
        missing = dict(expected)
        missing.pop(key)
        with pytest.raises(RuntimeError, match="key set"):
            M.validate_usage_eligibility(missing)
    counter_sets = [
        M.parse_diagnostic_stdout(_diagnostic_line()),
        M.parse_diagnostic_stdout(_diagnostic_line(
            call_count=22,
            requested_us_sum=11000,
            **{f"state_{state}_call_count": 2 for state in M.D1106_STATES},
        )),
    ]
    assert all(M.usage_eligibility() == expected for _counters in counter_sets)


def test_mu07_requested_and_admitted_intersections_keep_f718_1000_separate():
    committed = tuple(genome.canonical() for genome in M.genomes(M.WORKLOAD))
    projection = M._grid_projection(committed)
    assert projection["expected_d1106_grid"] == list(M.EXPECTED_FIXED_GRID)
    assert projection["observed_fixed_grid"] == list(M.EXPECTED_FIXED_GRID)
    requested = projection["requested_grid_intersection"]
    admitted = projection["admitted_realized_intersection"]
    assert requested == list(M.D1106_STATES)
    assert admitted == list(M.D1106_STATES[:-1])
    assert 1000 in requested and 1000 not in admitted
    without_1000 = tuple(
        canonical for canonical in committed if "BACKOFF_FIXED=1000" not in canonical
    )
    with pytest.raises(RuntimeError, match="fixed grid"):
        M._grid_projection(without_1000)


def test_historical_reference_policy_is_only_the_immediate_t1941_predecessor():
    current = resolve_current_build_admission_policy().as_preimage()
    predecessor = resolve_immediate_predecessor_build_admission_policy(
        added_generator_id=GeneratorId.BACKOFF_REQUESTED_US,
    ).as_preimage()
    expected_registry = list(current["generator_registry"])
    expected_registry.remove(GeneratorId.BACKOFF_REQUESTED_US.value)
    assert predecessor == {**current, "generator_registry": expected_registry}


def test_driver_is_balanced_one_rep_raw_only_and_uses_diagnostic_admission():
    source = inspect.getsource(M)
    measure = inspect.getsource(M.measure)
    run_rep = inspect.getsource(M._run_rep)
    assert M.WORKLOAD == "balanced"
    assert M.REPS == 1
    assert M.DIAGNOSTIC_USE_CLASS != "official"
    assert "GeneratorId.BACKOFF_REQUESTED_US" in measure
    assert "attest_generator_output(" in measure
    assert "declared_use_class=DIAGNOSTIC_USE_CLASS" in measure
    assert "patchharness.applied(" not in measure
    checkout = measure.index("patchharness.checkout(")
    fixed_apply = measure.index("patchharness.apply_patch(str(fixed_patch)")
    diagnostic_apply = measure.index(
        "patchharness.apply_patch(str(diagnostic_patch)"
    )
    revert = measure.index("patchharness.revert_worktree(")
    assert checkout < fixed_apply < diagnostic_apply < revert
    assert "finally:" in measure[diagnostic_apply:revert]
    assert "ccbench_dir=isolated_ccbench" in measure
    assert "subprocess.run(" in run_rep
    assert source.count("subprocess.run(") == 1
    assert "--build" not in source
    assert "run_once" not in source
    assert "throughput_tps" not in source
    assert "abort_rate" not in source
    assert "latency_ns" not in source
    assert GeneratorId.BACKOFF_REQUESTED_US.value == "backoff-requested-us"


def test_measure_uses_real_isolated_checkout_for_fixed_then_diagnostic(
    tmp_path, monkeypatch,
):
    base = tmp_path / "ccbench"
    base.mkdir()
    layer = base / "layer.txt"
    layer.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", str(base)], check=True)
    subprocess.run(
        ["git", "-C", str(base), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(base), "config", "user.name", "Fixture"],
        check=True,
    )
    subprocess.run(["git", "-C", str(base), "add", "layer.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(base), "commit", "--quiet", "-m", "base"],
        check=True,
    )
    head = subprocess.check_output(
        ["git", "-C", str(base), "rev-parse", "HEAD"], text=True,
    ).strip()

    driver_root = tmp_path / "driver"
    patches = driver_root / "patches"
    patches.mkdir(parents=True)
    fixed_patch = patches / "fixed.patch"
    fixed_patch.write_text(
        "diff --git a/layer.txt b/layer.txt\n"
        "--- a/layer.txt\n"
        "+++ b/layer.txt\n"
        "@@ -1 +1 @@\n"
        "-base\n"
        "+fixed\n"
        "diff --git a/fixed-only.txt b/fixed-only.txt\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/fixed-only.txt\n"
        "@@ -0,0 +1 @@\n"
        "+fixed-only\n",
        encoding="utf-8",
    )
    diagnostic_patch = patches / "diagnostic.patch"
    diagnostic_patch.write_text(
        "diff --git a/layer.txt b/layer.txt\n"
        "--- a/layer.txt\n"
        "+++ b/layer.txt\n"
        "@@ -1 +1 @@\n"
        "-fixed\n"
        "+diagnostic\n"
        "diff --git a/diagnostic-only.txt b/diagnostic-only.txt\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/diagnostic-only.txt\n"
        "@@ -0,0 +1 @@\n"
        "+diagnostic-only\n",
        encoding="utf-8",
    )

    before_bytes = layer.read_bytes()
    before_status = subprocess.check_output(
        ["git", "-C", str(base), "status", "--porcelain"], text=True,
    )
    events = []
    captured = {}
    real_checkout = M.patchharness.checkout
    real_patch_files = M.patchharness.patch_files
    real_apply_patch = M.patchharness.apply_patch
    real_revert_worktree = M.patchharness.revert_worktree

    @contextlib.contextmanager
    def observed_checkout(pin_commit, base_dir=""):
        events.append("checkout")
        with real_checkout(pin_commit, base_dir=base_dir) as isolated:
            captured["isolated"] = isolated
            yield isolated
        events.append("checkout-exit")

    def observed_patch_files(path, isolated):
        files = real_patch_files(path, isolated)
        events.append(f"files-{Path(path).stem}")
        return files

    def observed_apply_patch(path, isolated):
        real_apply_patch(path, isolated)
        state = (Path(isolated) / "layer.txt").read_text(encoding="utf-8").strip()
        events.append(f"apply-{state}")

    def observed_revert(isolated, files):
        assert files == ["diagnostic-only.txt", "fixed-only.txt", "layer.txt"]
        assert (Path(isolated) / "layer.txt").read_text(
            encoding="utf-8",
        ) == "diagnostic\n"
        events.append("revert")
        real_revert_worktree(isolated, files)
        assert (Path(isolated) / "layer.txt").read_text(encoding="utf-8") == "base\n"
        events.append("reverted")

    monkeypatch.setattr(M.patchharness, "checkout", observed_checkout)
    monkeypatch.setattr(M.patchharness, "patch_files", observed_patch_files)
    monkeypatch.setattr(M.patchharness, "apply_patch", observed_apply_patch)
    monkeypatch.setattr(M.patchharness, "revert_worktree", observed_revert)
    monkeypatch.setattr(M, "TEMPLATE_PATCH", "patches/fixed.patch")
    monkeypatch.setattr(M, "PATCH_REL", "patches/diagnostic.patch")
    monkeypatch.setattr(M, "_repo_root", lambda: str(driver_root))
    monkeypatch.setattr(M, "_resolve_ccbench_dir", lambda _value: str(base))
    monkeypatch.setattr(M.pin, "CURRENT_PIN", head)

    contract = SimpleNamespace(
        env_tag="fixture", contract_sha256="1" * 64, clocks_per_us=2100,
        numactl=(), attestation_mode="required",
    )
    verified = SimpleNamespace(
        schema_version="calibration/v1", sha256="2" * 64,
        attestation_profile_sha256="3" * 64,
    )
    loaded = SimpleNamespace(verified=verified)
    toolchain = {"fixture": "toolchain"}
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2, "resolve_site_runtime",
        lambda: ("fixture-site", contract, object()),
    )
    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", lambda _c: loaded)
    monkeypatch.setattr(
        M.screening_driver, "attest_runtime_contract",
        lambda _c, verified_calibration=None: ({"fixture": "execution"}, verified),
    )
    monkeypatch.setattr(
        M.buildcache, "compilers_for_current_site", lambda: ("cc", "cxx"),
    )
    monkeypatch.setattr(
        M.buildcache, "observed_toolchain_manifest", lambda _cc, _cxx: toolchain,
    )
    monkeypatch.setattr(
        M, "_require_runtime_match", lambda _binding, _contract, _toolchain: [],
    )

    def resolve_evidence(genome, commit, *, ccbench_dir, cxx):
        assert commit == head and cxx == "cxx"
        assert ccbench_dir == captured["isolated"]
        state = (Path(ccbench_dir) / "layer.txt").read_text(
            encoding="utf-8",
        ).strip()
        expected = "diagnostic" if M.DIAGNOSTIC_FLAG in genome.flags else "fixed"
        assert state == expected
        events.append(f"evidence-{state}")
        token = "b" * 64 if state == "diagnostic" else "a" * 64
        return M.source_digest.SourceEvidence(
            schema_version=M.source_digest.SOURCE_EVIDENCE_SCHEMA,
            source_root=ccbench_dir,
            ccbench_commit=head,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token=token,
            source_bytes_sha256=token,
            tracked_clean=False,
            tracked_diff_sha256="c" * 64,
            tracked_paths=("layer.txt",),
        )

    monkeypatch.setattr(M.source_digest, "resolve_evidence", resolve_evidence)
    monkeypatch.setattr(
        M, "_assert_backoff_fixed_materialized",
        lambda isolated: events.append(
            "materialized-" + (Path(isolated) / "layer.txt").read_text(
                encoding="utf-8",
            ).strip()
        ),
    )
    monkeypatch.setattr(
        M, "_require_fixed_source_match",
        lambda _reference, _evidence: events.append("fixed-match"),
    )
    monkeypatch.setattr(M, "build_run_context", lambda **_kwargs: object())
    monkeypatch.setattr(M, "attest_generator_output", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())

    def build_v2(_genome, **kwargs):
        assert kwargs["ccbench_dir"] == captured["isolated"]
        assert (Path(kwargs["ccbench_dir"]) / "layer.txt").read_text(
            encoding="utf-8",
        ) == "diagnostic\n"
        events.append("build")
        return SimpleNamespace(binary="/fixture/ycsb_silo.exe", bin_sha256="d" * 64)

    monkeypatch.setattr(M.buildcache, "build_v2", build_v2)
    completion_raw = b"completion\n"
    monkeypatch.setattr(M, "_read_json_object", lambda _path: ({}, completion_raw))
    monkeypatch.setattr(M, "_verify_completion_artifacts", lambda *_args: {})

    reference = tmp_path / "reference"
    reference.mkdir()
    diagnostic = tmp_path / "diagnostic"
    binding = {
        "reference_root": str(reference.resolve()),
        "reference_genome": "silo|BACK_OFF=1,BACKOFF_FIXED=-1",
        "reference_source_evidence": {},
        "completion_sha256": hashlib.sha256(completion_raw).hexdigest(),
        "artifact_sha256": {},
        "campaign_id": "fixture-campaign",
        "reference_variant_id": "fixture-variant",
        "workload_coordinates": dict(M.WORKLOAD_BY_TAG[M.WORKLOAD]),
    }

    def run_rep(_binary, _flags, _numactl, *, timeout_s):
        assert timeout_s == 7
        assert Path(captured["isolated"]).is_dir()
        events.append("run")
        return _diagnostic_line()

    result = M.measure(
        reference_root=str(reference), diagnostic_root=str(diagnostic),
        cache_root=str(tmp_path / "cache"), ccbench_dir=str(base),
        binding_loader=lambda _root: binding, run_rep=run_rep,
        build_timeout_s=9, record_timeout_s=7, log=lambda _message: None,
    )

    assert result["manifest"]["status"] == "complete"
    assert events == [
        "checkout", "files-fixed", "files-diagnostic", "apply-fixed",
        "materialized-fixed", "evidence-fixed", "fixed-match",
        "apply-diagnostic", "materialized-diagnostic", "evidence-diagnostic",
        "build", "run", "revert", "reverted", "checkout-exit",
    ]
    assert not Path(captured["isolated"]).exists()
    assert layer.read_bytes() == before_bytes
    assert subprocess.check_output(
        ["git", "-C", str(base), "status", "--porcelain"], text=True,
    ) == before_status


def test_runtime_match_requires_every_flag_contract_numactl_and_toolchain():
    flags = {
        "thread_num": str(M.p2_2.THREADS),
        "ycsb_tuple_num": str(M.p2_2.RECORDS),
        "extime": str(M.EXTIME),
        "clocks_per_us": "2100",
        **M.WORKLOAD_BY_TAG[M.WORKLOAD],
    }
    contract = SimpleNamespace(
        env_tag="pegasus",
        contract_sha256="a" * 64,
        clocks_per_us=2100,
        numactl=(),
    )
    binding = {
        "runtime_flags": flags,
        "runtime_contract": {
            "env_tag": "pegasus",
            "contract_sha256": "a" * 64,
            "clocks_per_us": 2100,
            "numactl": [],
            "toolchain_manifest": {"cxx": "fixture"},
        },
    }
    assert M._flag_mapping(M._require_runtime_match(
        binding, contract, {"cxx": "fixture"},
    )) == flags
    run_cmd = "/tmp/ycsb_silo.exe " + " ".join(
        f"-{key}={value}" for key, value in flags.items()
    )
    assert M._runtime_flags(run_cmd, expected_numactl=[]) == flags
    with pytest.raises(RuntimeError, match="numactl prefix"):
        M._runtime_flags(
            "numactl --localalloc " + run_cmd,
            expected_numactl=[],
        )
    for field, value in (
        ("contract_sha256", "b" * 64),
        ("clocks_per_us", 2099),
        ("numactl", ["numactl"]),
    ):
        mutated = {
            **binding,
            "runtime_contract": {**binding["runtime_contract"], field: value},
        }
        with pytest.raises(RuntimeError, match="differs"):
            M._require_runtime_match(mutated, contract, {"cxx": "fixture"})


def test_patch_contains_no_combined_fixed_branch_or_non_silo_callsite():
    patch = (_ROOT / M.PATCH_REL).read_text(encoding="utf-8")
    assert "static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL" not in patch
    touched = set(re.findall(r"(?m)^diff --git a/(\S+) b/\S+$", patch))
    assert touched == {
        "cmake/Options.cmake",
        "include/backoff.hh",
        "cc/silo/transaction.cc",
    }
    assert "include/result.hh" not in patch
    assert "cc/silo/ycsb_silo.cc" not in patch


def test_reproduction_body_accepts_generic_clean_child_and_invokes_driver_once():
    body = (
        _ROOT
        / "output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh"
    ).read_text(encoding="utf-8")
    assert "PBS_JOBID" not in body
    assert "PBS_O_WORKDIR" not in body
    assert "PBS_NODEFILE" not in body
    assert "qstat" not in body
    invocations = [
        line for line in body.splitlines()
        if not line.lstrip().startswith("#")
        and "orchestrator/campaign/backoff_requested_us.py" in line
    ]
    assert len(invocations) == 1
    assert "--reference-root" in body and "--diagnostic-root" in body


def test_generic_dispatch_clean_child_contract_drops_pbs_envelope(monkeypatch):
    generic = DISPATCH.TASKS["generic"]
    assert generic.env_mode == "clean"
    assert generic.env_allowlist == frozenset()
    pbs_names = {"PBS_JOBID", "PBS_O_WORKDIR", "PBS_NODEFILE"}
    for name in pbs_names:
        monkeypatch.setenv(name, f"fixture-{name}")
    child_env = DISPATCH._child_environment(generic)
    assert set(child_env) <= DISPATCH._CLEAN_CHILD_ENV_KEYS
    assert pbs_names.isdisjoint(child_env)


def test_reproduction_body_binds_site_dispatch_budget_and_atomic_failure_log():
    body = (
        _ROOT
        / "output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh"
    ).read_text(encoding="utf-8")
    assert "site_policy.current_site(require_evidence=True)" in body
    assert "site_policy.PEGASUS_COMPUTE" in body
    assert "DISPATCH_WALLTIME=02:00:00" in body
    assert "WALLTIME_SECONDS=7200" in body
    assert 'test "$WALLTIME_SECONDS" -eq "$CALCULATED_WALLTIME_SECONDS"' in body
    assert 'TOTAL_BUDGET_SECONDS" -lt "$WALLTIME_SECONDS' in body
    component_names = (
        "ALLOCATION_EVIDENCE_BUDGET_SECONDS",
        "SOURCE_PREPARATION_BUDGET_SECONDS",
        "DEPENDENCY_BUILD_BUDGET_SECONDS",
        "PROVENANCE_BUDGET_SECONDS",
        "CCBENCH_BUILD_BUDGET_SECONDS",
        "RECORD_BUDGET_SECONDS",
        "SHUTDOWN_MARGIN_SECONDS",
    )
    components = {
        name: int(match.group(1))
        for name in component_names
        if (match := re.search(rf"(?m)^{name}=([0-9]+)$", body)) is not None
    }
    assert set(components) == set(component_names)
    assert sum(components.values()) == 3450
    assert sum(components.values()) < 7200
    assert 'timeout "$DRIVER_BUDGET_SECONDS"' in body
    assert '--build-timeout-seconds "$CCBENCH_BUILD_BUDGET_SECONDS"' in body
    assert '--record-timeout-seconds "$RECORD_BUDGET_SECONDS"' in body
    assert "trap on_error ERR" in body and "trap on_exit EXIT" in body
    assert '"status": status' in body
    assert '"returncode": int(rc)' in body
    assert '"stage": stage' in body
    assert '"job_token": job_token' in body
    assert '"compute_hostname": compute_hostname' in body
    assert '"compute_site": compute_site' in body
    assert 'mv -T "$STAGING_LOG" "$PUBLISHED_LOG"' in body
    assert "> >(tee" not in body and "2> >(tee" not in body


def test_reproduction_body_clean_child_rejects_noncompute_and_publishes_schema(
    tmp_path,
):
    body_path = (
        _ROOT
        / "output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh"
    )
    body = body_path.read_text(encoding="utf-8")
    log_parent = tmp_path / "job-logs"
    original_log_parent = (
        'LOG_PARENT="$REPO_ROOT/output/insights/'
        '2026-08-28_t1941-backoff-requested-us/job-logs"'
    )
    site_probe = "site = site_policy.current_site(require_evidence=True)"
    assert body.count(original_log_parent) == 1
    assert body.count(site_probe) == 1
    local_body = body.replace(
        original_log_parent,
        f"LOG_PARENT={shlex.quote(str(log_parent))}",
    ).replace(site_probe, "site = site_policy.OTHER")
    local_body_path = tmp_path / "job-body.sh"
    local_body_path.write_text(local_body, encoding="utf-8")

    clean_child_env = {
        name: os.environ[name]
        for name in (
            "HOME", "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "LOGNAME",
            "PATH", "TZ", "USER",
        )
        if name in os.environ
    }
    clean_child_env.setdefault("PATH", os.defpath)
    completed = subprocess.run(
        ["/bin/bash", str(local_body_path), "clean-child"],
        cwd=_ROOT,
        env=clean_child_env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert completed.returncode != 0
    assert "PBS compute allocation envelope is required" not in completed.stderr
    assert "PEGASUS_COMPUTE is required, observed=OTHER" in completed.stderr

    status = json.loads(
        (log_parent / "clean-child" / "job-status.json").read_text(
            encoding="utf-8",
        )
    )
    assert set(status) == {
        "schema_version",
        "job_token",
        "compute_hostname",
        "compute_site",
        "status",
        "returncode",
        "stage",
        "line",
    }
    assert status["schema_version"] == "backoff-requested-us-job-status/v2"
    assert status["job_token"] == "clean-child"
    assert status["compute_hostname"]
    assert status["compute_site"] == "OTHER"
    assert status["status"] == "failure"
    assert status["returncode"] == completed.returncode
    assert status["stage"] == "compute_site"
    assert status["line"] > 0


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
