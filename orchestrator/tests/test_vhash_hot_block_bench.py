"""Contract checks for the isolated VHash hot block benchmark."""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/vhash_microbench/hot_block_bench.cc"
DRIVER = ROOT / "tools/vhash_microbench/run_hot_block.py"
EXPECTED_EVENTS = ("cycles:u", "instructions:u", "cache-references:u",
                   "cache-misses:u", "branch-misses:u")
spec = importlib.util.spec_from_file_location("run_hot_block", DRIVER)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)

VECTORS = {
    "newest_committed", "hot_tail_committed", "first_cold_committed",
    "deep_cold_committed", "all_newer_than_ts", "candidate_pending",
    "pending_newer_than_ts_skipped", "pending_between_committed",
    "aborted_then_committed", "hot_all_aborted_then_cold_committed",
    "aborted_then_cold_pending", "aborted_then_cold_deleted",
    "candidate_deleted", "equal_ts", "k_boundary_each_K", "write_version_ids",
    "write_value_bytes", "state_cell_candidate_pending",
    "state_cell_pending_newer_than_ts", "state_cell_aborted_then_committed",
    "state_cell_candidate_deleted",
}


def test_cpp_selfcheck(tmp_path):
    compiler = shutil.which("g++-12")
    assert compiler, "g++-12 required for the acceptance bench"
    version = subprocess.run([compiler, "--version"], capture_output=True, text=True)
    assert version.returncode == 0, version.stderr
    binary = tmp_path / "hot_block_bench"
    build = subprocess.run([compiler, *bench.FLAGS, str(SOURCE), "-o", str(binary)],
                           capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    check = subprocess.run([str(binary), "--selfcheck"], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr + check.stdout
    result = json.loads(check.stdout)
    assert result["passed"] is True
    assert VECTORS <= set(result["vectors"])
    assert result["random_cases"] >= 256
    assert result["failures"] == []


def test_manifest_counts_and_duplicates():
    cells = bench.make_manifest()
    assert {group: sum(c["group"] == group for c in cells)
            for group in ("k", "depth", "state", "value", "write")} == {
                "k": 24, "depth": 22, "state": 16, "value": 48, "write": 36}
    assert len({c["cell_id"] for c in cells}) == len(cells)
    pilot = bench.make_pilot_manifest(1024 * 1024, lambda _c, _a: 280, 1 << 30)
    assert len(pilot) == 5
    assert len({c["cell_id"] for c in pilot}) == 5
    assert all(c["depth"] == 1 for c in cells if c["group"] == "state")
    with pytest.raises(ValueError, match="duplicate cell"):
        bench.validate_manifest(cells + [dict(cells[0])])
    with pytest.raises(ValueError, match="duplicate cell"):
        bench.validate_manifest(pilot + [dict(pilot[0])])


def test_objdump_scalar_vector_rejection():
    good = """
0000 <select_contig_scalar>:
  0: mov (%rax),%rcx
  4: cmp %rdx,%rcx
000f <select_contig_simd>:
  f: vpcmpgtq %ymm0,%ymm1,%ymm2
  13: vmovmskpd %ymm2,%eax
"""
    assert bench.check_objdump(good)["passed"] is True
    bad = good.replace("  4: cmp %rdx,%rcx", "  4: vpcmpgtq %ymm0,%ymm1,%ymm2")
    assert bench.check_objdump(bad)["passed"] is False


def test_cell_contract_and_footprint(tmp_path):
    compiler = shutil.which("g++-12")
    assert compiler, "g++-12 required for the acceptance bench"
    binary = tmp_path / "hot_block_bench"
    build = subprocess.run([compiler, *bench.FLAGS, str(SOURCE), "-o", str(binary)],
                           capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    for side, arms, mode, bytes_ in (
        ("read", bench.READ_ARMS, "inline", 16),
        ("read", bench.READ_ARMS, "external", 16),
        ("write", bench.WRITE_ARMS, "external", 64),
        ("write", bench.WRITE_ARMS, "inline", 16),
    ):
        cell = dict(K=3, depth=1 if side == "read" else None, n_keys=64,
                    side=side, value_mode=mode, value_bytes=bytes_,
                    state_pattern="pending_newer_than_ts" if side == "read" else None)
        result = subprocess.run([str(binary), "--cell", json.dumps(cell), "--arms",
                                 ",".join(arms), "--reps", "8", "--ops", "100"],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["ops"] == 100
        assert payload["shared_value_pool_bytes"] == (64 * 7 * bytes_ if side == "read" and mode == "external" else 0)
        assert len(payload["arms"]) == len(arms)
        for arm in payload["arms"]:
            size = subprocess.run([str(binary), "--footprint", json.dumps(dict(cell, ops=100)),
                                   "--arm", arm["arm"]], capture_output=True, text=True)
            assert size.returncode == 0, size.stderr
            per_key = json.loads(size.stdout)["footprint_per_key_bytes"]
            assert arm["footprint_per_key_bytes"] == per_key
            assert arm["footprint_bytes"] == 64 * per_key
            assert len(arm["reps"]) == 8
            assert {rep["checksum"] for rep in arm["reps"]} == {payload["expected_checksum"]}
            assert sorted(rep["order_pos"] for rep in arm["reps"]) == (
                [0, 0, 1, 1, 2, 2, 3, 3] if len(arms) == 4 else [0, 0, 0, 0, 1, 1, 1, 1])


def test_skewed_write_capacity_precedes_timing(tmp_path):
    compiler = shutil.which("g++-12")
    assert compiler, "g++-12 required for the acceptance bench"
    binary = tmp_path / "hot_block_bench"
    build = subprocess.run([compiler, *bench.FLAGS, str(SOURCE), "-o", str(binary)],
                           capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    small = dict(K=3, n_keys=3, side="write", value_mode="external", value_bytes=1, ops=10)
    small_run = subprocess.run([str(binary), "--cell", json.dumps(small), "--arms", "block",
                                "--reps", "1", "--ops", "10"], capture_output=True, text=True)
    assert small_run.returncode == 0, small_run.stderr
    small_size = subprocess.run([str(binary), "--footprint", json.dumps(small), "--arm", "block"],
                                capture_output=True, text=True)
    assert small_size.returncode == 0, small_size.stderr
    assert json.loads(small_run.stdout)["arms"][0]["footprint_per_key_bytes"] == json.loads(small_size.stdout)["footprint_per_key_bytes"]
    cell = dict(K=3, n_keys=1, side="write", value_mode="external", value_bytes=1)
    argv = [str(binary), "--cell", json.dumps(cell), "--arms", "block", "--reps", "1", "--ops", "32769"]
    result = subprocess.run(argv, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["ops"] == 32769
    rejected = subprocess.run([str(binary), "--cell", json.dumps(dict(cell, memory_limit_bytes=4096)),
                               "--arms", "block", "--reps", "1", "--ops", "32769"],
                              capture_output=True, text=True)
    assert rejected.returncode != 0
    assert "write capacity exceeds memory limit" in rejected.stderr


def test_node_stride_and_hot_cold_slot(tmp_path):
    compiler = shutil.which("g++-12")
    assert compiler, "g++-12 required for the acceptance bench"
    binary = tmp_path / "hot_block_bench"
    build = subprocess.run([compiler, *bench.FLAGS, str(SOURCE), "-o", str(binary)],
                           capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    for mode, size, stride in (("none", 0, 64), ("external", 16, 64),
                               ("inline", 16, 64), ("inline", 256, 320)):
        cell = dict(K=4, depth=0, n_keys=1, side="read",
                    value_mode=mode, value_bytes=size)
        result = subprocess.run([str(binary), "--footprint", json.dumps(cell),
                                 "--arm", "linked_local"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        per_key = json.loads(result.stdout)["footprint_per_key_bytes"]
        # version_count(4, 0) = 8; linked heads take 8 B per key.
        assert per_key == 8 + 8 * stride + (8 * size if mode == "external" else 0)
    check = subprocess.run([str(binary), "--selfcheck"], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr + check.stdout
    assert "hot_does_not_read_cold_slot" in json.loads(check.stdout)["vectors"]


def test_perf_csv_requires_complete_unmultiplexed_events():
    assert tuple(bench.EVENTS.split(",")) == EXPECTED_EVENTS
    for names in (EXPECTED_EVENTS[:4], EXPECTED_EVENTS[4:]):
        lines = ["1,,%s,100000,100.00" % name for name in names]
        parsed = bench.parse_perf_csv("\n".join(lines), names)
        assert set(parsed) == set(names)
        assert parsed[names[0]]["run_time_ns"] == 100000
        assert parsed[names[0]]["running_pct"] == 100.0
        with pytest.raises(RuntimeError, match="missing"):
            bench.parse_perf_csv("\n".join(lines[:-1]), names)
        with pytest.raises(RuntimeError, match="multiplexed"):
            bench.parse_perf_csv("\n".join(lines).replace("100.00", "99.00", 1), names)


def _run():
    with tempfile.TemporaryDirectory(prefix="vhash-hot-test-") as directory:
        tmp_path = pathlib.Path(directory)
        test_cpp_selfcheck(tmp_path)
        test_manifest_counts_and_duplicates()
        test_objdump_scalar_vector_rejection()
        test_cell_contract_and_footprint(tmp_path)
        test_skewed_write_capacity_precedes_timing(tmp_path)
        test_perf_csv_requires_complete_unmultiplexed_events()
        test_node_stride_and_hot_cold_slot(tmp_path)
    print("7 tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
