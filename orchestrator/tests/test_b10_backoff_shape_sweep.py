# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import tarfile
from types import SimpleNamespace
from fractions import Fraction
from pathlib import Path

import pytest

from orchestrator.campaign import b10_backoff_shape_sweep as B
from orchestrator.campaign.layout import CampaignLayout


ROOT = Path(__file__).resolve().parents[2]


def _patch_bytes() -> bytes:
    return (ROOT / B.PATCH_REL).read_bytes()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fixture_source() -> bytes:
    return (
        b"#include <cstdint>\n"
        b"class Backoff {\n"
        b" public:\n"
        b"  static void backoff() {\n"
        b"    uint64_t start = 0;\n"
        b"    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude\n"
        b"#if BACKOFF_FIXED >= 0\n"
        + B.EXPECTED_HOLE_LINE.encode("utf-8") + b"\n"
        b"#else\n"
        b"    double now_backoff = Backoff_.load(std::memory_order_acquire);\n"
        b"#endif\n"
        b"    // EVOLVE-BLOCK-END silo-backoff-magnitude\n"
        b"    while (rdtscp() - start <= now_backoff) { pause(); }\n"
        b"  }\n"
        b"};\n"
    )


def _fixture_tree(tmp_path: Path, source: bytes | None = None) -> tuple[Path, bytes, bytes]:
    source_bytes = _fixture_source() if source is None else source
    options = b"set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING fixture)\n"
    (tmp_path / "include").mkdir()
    (tmp_path / "cmake").mkdir()
    (tmp_path / B.SOURCE_REL).write_bytes(source_bytes)
    (tmp_path / B.OPTIONS_REL).write_bytes(options)
    return tmp_path, source_bytes, options


def _passing_applied_tree(tmp_path: Path, **overrides):
    tree, source, options = _fixture_tree(tmp_path, overrides.pop("source", None))
    patch = _patch_bytes()
    defaults = {
        "patch_bytes": patch,
        "patch_sha256": _sha(patch),
        "expected_options_sha256": _sha(options),
        "expected_frame_sha256": B._frame_sha256(source),
        "digest_compute": lambda *_args: "same",
        "digest_baseline": lambda *_args: "same",
        "token_resolver": lambda *_args: "stock",
        "applied_paths": tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    }
    defaults.update(overrides)
    return B.validate_applied_tree(tree, **defaults)


def _expect_code(code: str, fn) -> None:
    with pytest.raises(B.PreflightError) as caught:
        fn()
    assert caught.value.code == code


def _complete_records(*, underexposed=None, unstable=None, uncertified=None):
    rows = []
    for workload in B.WORKLOADS:
        for block_id in B.BLOCK_IDS:
            for mean_us in B.MEANS_US:
                for shape, _code in B.SHAPES:
                    key = (workload, block_id, shape, mean_us)
                    abort_count = 9 if key == underexposed else 100
                    row = {
                        "workload": workload,
                        "block_id": block_id,
                        "shape": shape,
                        "mean_us": mean_us,
                        "median_tps": 100.0 if shape == "constant" else 101.0,
                        "abort_count": abort_count,
                        "backoff_call_count": abort_count,
                        "certified": key != uncertified,
                        "unstable": key == unstable,
                        "missing": False,
                    }
                    rows.append(row)
    return rows


def _prereg_doc() -> bytes:
    patch_sha = _sha(_patch_bytes())
    return (
        f"b10_patch_sha256: {patch_sha}\n"
        f"b10_formula_sha256: {B.FORMULA_SHA256}\n"
        "b10_minimum_abort_calls: 10\n"
        "b10_expression_eval_p99_cycles: 12\n"
        "b10_physical_residual_upper_pct: 0.9\n"
        "b10_equivalence_margin_pct: 3.0\n"
    ).encode("utf-8")


def _mock_prereg_git(monkeypatch, root: Path, *, status="", blob=None, ancestor_rc=0):
    prereg = _prereg_doc()
    committed_blob = prereg if blob is None else blob
    patch = _patch_bytes()

    def fake_git(_root, *args, binary=False):
        assert Path(_root) == root.resolve()
        if args[:3] == ("rev-parse", "--verify", "HEAD^{commit}"):
            return "f" * 40 + "\n"
        if args[:2] == ("status", "--porcelain"):
            return status
        if args[:2] == ("show", "a" * 40 + ":docs/b10-backoff-shape-preregistration.md"):
            return committed_blob
        if args[:2] == ("rev-parse", "a" * 40 + ":docs/b10-backoff-shape-preregistration.md"):
            return "b" * 40 + "\n"
        if args[:2] == ("show", "a" * 40 + ":patches/silo-backoff-fixed.patch"):
            return patch
        raise AssertionError(args)

    monkeypatch.setattr(B, "_git", fake_git)
    monkeypatch.setattr(
        B.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=ancestor_rc),
    )


def test_m01_patch_path_widening_is_rejected_for_one_reason():
    mutated = _patch_bytes().replace(
        b"diff --git a/include/backoff.hh b/include/backoff.hh",
        b"diff --git a/cc/silo/transaction.cc b/cc/silo/transaction.cc",
    )
    _expect_code("patch-paths", lambda: B.validate_patch_bytes(mutated, _sha(mutated)))


def test_m02_patch_sha_bypass_witness_is_rejected_for_one_reason():
    patch = _patch_bytes()
    _expect_code("patch-sha", lambda: B.validate_patch_bytes(patch, "0" * 64))


def test_m03_duplicate_marker_is_rejected_for_one_reason(tmp_path: Path):
    source = _fixture_source().replace(
        b"    // EVOLVE-BLOCK-END silo-backoff-magnitude\n",
        b"    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude\n"
        b"    // EVOLVE-BLOCK-END silo-backoff-magnitude\n",
    )
    _expect_code("markers", lambda: _passing_applied_tree(tmp_path, source=source))


def test_m04_hole_substring_match_is_rejected_for_one_reason(tmp_path: Path):
    source = _fixture_source().replace(
        B.EXPECTED_HOLE_LINE.encode("utf-8"),
        B.EXPECTED_HOLE_LINE.encode("utf-8") + b" /* appended */",
    )
    _expect_code("hole", lambda: _passing_applied_tree(tmp_path, source=source))


def test_m05_wait_loop_mutation_is_rejected_for_one_reason(tmp_path: Path):
    original = _fixture_source()
    mutated = original.replace(b"pause();", b"pause(); pause();")
    _expect_code(
        "frame",
        lambda: _passing_applied_tree(
            tmp_path, source=mutated,
            expected_frame_sha256=B._frame_sha256(original),
        ),
    )


def test_m06_nonstock_inert_token_is_rejected_for_one_reason(tmp_path: Path):
    _expect_code(
        "inert-token",
        lambda: _passing_applied_tree(
            tmp_path, token_resolver=lambda *_args: "1" * 64,
        ),
    )


def test_m07_unapplied_patch_is_not_a_success(tmp_path: Path):
    source = b"class Backoff { static void backoff() {} };\n"
    _fixture_tree(tmp_path, source)
    patch = _patch_bytes()
    _expect_code(
        "patch-unapplied",
        lambda: B.validate_applied_tree(
            tmp_path,
            patch_bytes=patch,
            patch_sha256=_sha(patch),
            expected_options_sha256=_sha((tmp_path / B.OPTIONS_REL).read_bytes()),
            expected_frame_sha256="0" * 64,
            digest_compute=lambda *_args: "same",
            digest_baseline=lambda *_args: "same",
            token_resolver=lambda *_args: "stock",
            applied_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
        ),
    )


def test_m08_legacy_wal_without_binding_is_rejected_for_one_reason(
    tmp_path: Path, monkeypatch,
):
    layout = CampaignLayout(str(tmp_path / "campaign"))
    Path(layout.root).mkdir()
    Path(layout.runs_dir).mkdir()
    Path(layout.lock_file).write_text("legacy", encoding="utf-8")
    Path(layout.wal_file).write_text("\n", encoding="utf-8")
    binding = B.PreregistrationBinding("a" * 40, "b" * 40, "c" * 64, "d" * 64)
    monkeypatch.setattr(B.wal, "read_lock", lambda _layout: "legacy")
    monkeypatch.setattr(B, "_decode_lock_search_config", lambda _raw: {})
    _expect_code("resume-binding", lambda: B.assert_resumable_binding(layout, binding))


def test_preregistration_dirty_tree_is_rejected_before_blob_admission(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / B.PREREG_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(_prereg_doc())
    (tmp_path / B.PATCH_REL).parent.mkdir(parents=True)
    (tmp_path / B.PATCH_REL).write_bytes(_patch_bytes())
    _mock_prereg_git(monkeypatch, tmp_path, status=" M tracked.py\n")
    _expect_code(
        "dirty",
        lambda: B.load_preregistration(tmp_path, B.PREREG_REL, "a" * 40),
    )


def test_preregistration_nonancestor_commit_is_rejected(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / B.PREREG_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(_prereg_doc())
    (tmp_path / B.PATCH_REL).parent.mkdir(parents=True)
    (tmp_path / B.PATCH_REL).write_bytes(_patch_bytes())
    _mock_prereg_git(monkeypatch, tmp_path, ancestor_rc=1)
    _expect_code(
        "prereg-ancestor",
        lambda: B.load_preregistration(tmp_path, B.PREREG_REL, "a" * 40),
    )


def test_preregistration_blob_mismatch_is_rejected(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / B.PREREG_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(_prereg_doc())
    (tmp_path / B.PATCH_REL).parent.mkdir(parents=True)
    (tmp_path / B.PATCH_REL).write_bytes(_patch_bytes())
    _mock_prereg_git(monkeypatch, tmp_path, blob=b"different\n")
    _expect_code(
        "prereg-blob",
        lambda: B.load_preregistration(tmp_path, B.PREREG_REL, "a" * 40),
    )


def test_preregistration_matching_commit_blob_patch_and_formula_are_accepted(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / B.PREREG_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(_prereg_doc())
    (tmp_path / B.PATCH_REL).parent.mkdir(parents=True)
    (tmp_path / B.PATCH_REL).write_bytes(_patch_bytes())
    _mock_prereg_git(monkeypatch, tmp_path)
    prereg = B.load_preregistration(tmp_path, B.PREREG_REL, "a" * 40)
    assert prereg.binding.prereg_commit == "a" * 40
    assert prereg.binding.prereg_blob_sha == "b" * 40
    assert prereg.binding.patch_sha256 == _sha(_patch_bytes())
    assert prereg.binding.formula_sha256 == B.FORMULA_SHA256
    assert prereg.minimum_abort_calls == 10
    assert prereg.expression_eval_p99_cycles == 12
    assert prereg.physical_residual_upper_pct == 0.9
    assert prereg.equivalence_margin_pct == 3.0


def test_m09_shape_code_three_is_rejected_instead_of_falling_back():
    _expect = lambda: B.decode(3002)
    with pytest.raises(ValueError, match="grid 外"):
        _expect()


def test_m10_underexposed_cell_is_indeterminate_not_success_or_failure():
    key = ("read-heavy", "block-1", "binary", 2)
    result = B.judge(_complete_records(underexposed=key), minimum_abort_calls=10)
    family = next(
        item for item in result["families"]
        if item["workload"] == "read-heavy" and item["shape"] == "binary"
    )
    assert family["outcome"] == "indeterminate"
    assert family["pairs"] == 17
    assert family["raw_p"] == 1.0


def test_m11_raw_p_cannot_bypass_holm_family_correction():
    raw = {f"family-{index}": (0.02 if index == 0 else 1.0) for index in range(6)}
    adjusted = B.holm_adjust(raw)
    assert raw["family-0"] < B.ALPHA
    assert adjusted["family-0"] == pytest.approx(0.12)
    assert adjusted["family-0"] > B.ALPHA


def test_m12_sign_flip_test_is_two_sided_not_fixed_one_sided():
    assert B.sign_flip_permutation_pvalue([1.0] * 5) == Fraction(2, 32)


def test_m13_half_width_lower_bound_matches_exact_model():
    for mean_us in B.MEANS_US:
        encoded = B.encode("symmetric-modulo", mean_us)
        observed = {
            B.exact_model(encoded, start)
            for start in (0, 1, 2, (1 << 63), (1 << 64) - 1)
        }
        assert min(observed) >= Fraction(mean_us, 2)
        assert max(observed) <= Fraction(3 * mean_us, 2)
        assert Fraction(0) not in observed


def test_m14_different_random_mixers_are_rejected_for_one_reason():
    mutated = B.EXPECTED_HOLE_LINE.replace(
        "0x9e3779b97f4a7c15ULL) >> 63) *",
        "0xd1b54a32d192ed03ULL) >> 63) *",
        1,
    )
    _expect_code("mixer", lambda: B.validate_formula_contract(mutated))


def test_p01_registered_patch_hole_frame_and_inert_binding_are_accepted(tmp_path: Path):
    evidence = _passing_applied_tree(tmp_path)
    assert evidence["patch_sha256"] == _sha(_patch_bytes())
    assert len(evidence["inert_references"]) == 2
    assert {row["src_token"] for row in evidence["inert_references"]} == {"stock"}


def test_actual_patch_is_applied_in_isolation_and_inert_gate_does_not_skip(tmp_path: Path):
    compiler = next(
        (path for name in ("g++-13", "g++-12", "g++") if (path := shutil.which(name))),
        None,
    )
    assert compiler is not None, "source-digest inert witness requires a C++ compiler"
    patch_program = shutil.which("patch")
    assert patch_program is not None, "actual isolated patch witness requires patch(1)"
    archived = subprocess.run(
        ["git", "-C", str(ROOT / "external/ccbench"), "archive", B.PIN],
        capture_output=True,
    )
    assert archived.returncode == 0, archived.stderr.decode(errors="replace")
    stock = tmp_path / "stock"
    applied = tmp_path / "applied"
    stock.mkdir()
    applied.mkdir()
    for destination in (stock, applied):
        with tarfile.open(fileobj=io.BytesIO(archived.stdout), mode="r:") as archive:
            members = archive.getmembers()
            assert all(
                not member.name.startswith("/")
                and ".." not in Path(member.name).parts
                and not member.issym()
                and not member.islnk()
                for member in members
            )
            archive.extractall(destination, members=members)
    patched = subprocess.run(
        [patch_program, "-s", "-d", str(applied), "-p1", "-i", str(ROOT / B.PATCH_REL)],
        capture_output=True, text=True,
    )
    assert patched.returncode == 0, patched.stdout + patched.stderr
    cache = {}

    def compute_at(genome, directory, cxx):
        key = (genome.canonical(), str(directory), cxx)
        if key not in cache:
            cache[key] = B.source_digest.compute(genome, str(directory), cxx)
        return cache[key]

    def baseline(genome, _commit, _directory, cxx):
        return compute_at(genome, stock, cxx)

    def token(genome, commit, directory, cxx):
        return "stock" if compute_at(genome, directory, cxx) == baseline(
            genome, commit, directory, cxx,
        ) else "candidate"

    patch = _patch_bytes()
    evidence = B.validate_applied_tree(
        applied,
        patch_bytes=patch,
        patch_sha256=_sha(patch),
        cxx=compiler,
        digest_compute=compute_at,
        digest_baseline=baseline,
        token_resolver=token,
        applied_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    )
    assert len(evidence["inert_references"]) == 2


def test_p02_all_18_encodings_are_bijective():
    encoded = {B.encode(shape, mean_us) for shape, _code in B.SHAPES for mean_us in B.MEANS_US}
    assert len(encoded) == 18
    assert {B.decode(value) for value in encoded} == {
        (shape, mean_us) for shape, _code in B.SHAPES for mean_us in B.MEANS_US
    }


def test_p03_legacy_zero_through_999_is_numerically_identical():
    for value in range(1000):
        assert B.exact_model(value, 0) == Fraction(value)
        assert B.exact_model(value, (1 << 64) - 1) == Fraction(value)


def test_p04_three_reference_points_and_full_grid_are_accepted():
    refs = dict(B.reference_genomes())
    assert set(refs) == {"none", "adaptive", "zero-loop"}
    assert refs["none"].flags["BACK_OFF"] == 0
    assert refs["none"].flags["BACKOFF_FIXED"] == -1
    assert refs["adaptive"].flags["BACK_OFF"] == 1
    assert refs["adaptive"].flags["BACKOFF_FIXED"] == -1
    assert refs["zero-loop"].flags["BACK_OFF"] == 1
    assert refs["zero-loop"].flags["BACKOFF_FIXED"] == 0
    assert len(B.genomes()) == 21


def test_exact_finite_models_have_mean_exactly_mu_for_all_shapes():
    width = 16
    mask = (1 << width) - 1
    lower_mask = (1 << (width - 1)) - 1
    multiplier = B.MIXER & mask
    assert multiplier % 2 == 1
    for mean_us in B.MEANS_US:
        constant = []
        symmetric = []
        binary = []
        for start in range(1 << width):
            mixed = (start * multiplier) & mask
            high = mixed >> (width - 1)
            low = mixed & lower_mask
            residue = low % (2 * mean_us + 1)
            offset = 2 * mean_us - residue if high else residue
            constant.append(Fraction(mean_us))
            symmetric.append(Fraction(mean_us + offset, 2))
            binary.append(Fraction(mean_us + high * 2 * mean_us, 2))
        for values in (constant, symmetric, binary):
            assert sum(values, Fraction()) / len(values) == Fraction(mean_us)


def test_exact_model_binary_arms_and_symmetric_bounds_for_odd_means():
    for mean_us in (5, 25):
        binary = B.encode("binary", mean_us)
        # MIXER is odd, so start=0 has high bit 0.  Search one finite witness for high bit 1.
        high_start = next(
            start for start in range(1, 1000)
            if (((start * B.MIXER) & B._MASK64) >> 63) == 1
        )
        assert B.exact_model(binary, 0) == Fraction(mean_us, 2)
        assert B.exact_model(binary, high_start) == Fraction(3 * mean_us, 2)
        symmetric = B.encode("symmetric-modulo", mean_us)
        for start in (0, high_start, (1 << 64) - 1):
            value = B.exact_model(symmetric, start)
            assert Fraction(mean_us, 2) <= value <= Fraction(3 * mean_us, 2)


def test_block_orders_are_distinct_complete_identity_bearing_permutations():
    orders = [B.block_run_order(block) for block in B.BLOCK_IDS]
    expected = {name for name, _genome in B.named_genomes()}
    assert len(set(orders)) == 3
    assert all(len(order) == 21 and set(order) == expected for order in orders)


def test_config_uses_calibration_records_and_binds_preregistration():
    binding = B.PreregistrationBinding("a" * 40, "b" * 40, "c" * 64, B.FORMULA_SHA256)
    prereg = B.Preregistration(binding, B.PREREG_REL, 123)
    calibration = B.CalibrationSelection(
        path="artifact.json", sha256="e" * 64, schema_version="calibration/v2",
        records=765432, threads=48, env_tag="pegasus", clocks_per_us=2100,
        saturated=False, lower_bound_selected=True, cache_floor_warning=False,
    )
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    contract = B.env_contract.GENERATIONS["pegasus"][-1].contract
    cfg = B.config_for("balanced", prereg, calibration, context, contract)
    perf = B.perf_for("balanced", calibration)
    assert cfg.search_config["records"] == 765432
    assert perf.records == 765432
    assert cfg.search_config["preregistration_binding"] == binding.as_dict()
    assert cfg.search_config[B.SEARCH_CONFIG_VERIFY_KEY] == B.VERIFY_LEGACY_PLUS_PERFORMANCE
    assert "screening" not in cfg.search_config


@pytest.mark.parametrize(
    ("quality", "saturation"),
    (
        ("rejected", {"records": 10, "saturated": True,
                      "lower_bound_selected": False, "cache_floor_warning": False}),
        ("accepted", None),
        ("accepted", {"records": 10, "saturated": False,
                      "lower_bound_selected": False, "cache_floor_warning": False}),
        ("accepted", {"records": 10, "saturated": True,
                      "lower_bound_selected": False, "cache_floor_warning": True}),
    ),
)
def test_rejected_missing_null_or_cache_warning_calibration_fails_before_run(
    monkeypatch, quality, saturation,
):
    contract = B.env_contract.GENERATIONS["pegasus"][-1].contract
    parsed = SimpleNamespace(
        saturation=saturation,
        quality=SimpleNamespace(status=quality),
        threads=48,
        env_tag="pegasus",
        clocks_per_us=2100,
    )
    loaded = SimpleNamespace(
        parsed=parsed,
        verified=SimpleNamespace(schema_version="calibration/v2"),
    )
    monkeypatch.setattr(B.p2_2, "_load_calibration_once", lambda _contract: loaded)
    _expect_code("calibration", lambda: B.load_calibration(contract))


def test_each_generator_receipt_commits_the_exact_preregistration_bundle():
    binding = B.PreregistrationBinding("a" * 40, "b" * 40, "c" * 64, "d" * 64)
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    evidence = B.source_digest.SourceEvidence(
        schema_version=B.source_digest.SOURCE_EVIDENCE_SCHEMA,
        source_root="/tmp/b10-source-fixture",
        ccbench_commit=B.PIN,
        genome_sha256="e" * 64,
        src_token="f" * 64,
        source_bytes_sha256="1" * 64,
        tracked_clean=False,
        tracked_diff_sha256="2" * 64,
        tracked_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    )
    receipt = B._formula_generator_resolver(context, binding)(evidence).as_receipt()
    assert receipt["generator_input_sha256"] == binding.binding_sha256
    assert receipt["source"] == evidence.as_receipt()


def test_each_build_start_carries_all_four_explicit_binding_values(monkeypatch):
    binding = B.PreregistrationBinding("a" * 40, "b" * 40, "c" * 64, "d" * 64)
    captured = []

    def fake_log(layout, variant, stage, env_tag, payload, *args, **kwargs):
        captured.append((stage, payload))

    monkeypatch.setattr(B.wal, "log", fake_log)
    with B.bind_build_start_wal(binding):
        B.wal.log(None, "variant", B.STAGE_BUILD_START, "pegasus", {
            "build_attempt_id": "attempt",
        })
        B.wal.log(None, "variant", "verify_done", "pegasus", {"other": True})
    assert captured[0][1][B.B10_BUILD_START_BINDING_KEY] == binding.as_dict()
    assert captured[1][1] == {"other": True}
    assert B.wal.log is fake_log


def test_missing_uncertified_and_unstable_pairs_are_indeterminate():
    keys = (
        ("balanced", "block-1", "binary", 2),
        ("balanced", "block-2", "binary", 5),
    )
    for selector in ("unstable", "uncertified"):
        kwargs = {selector: keys[0]}
        result = B.judge(_complete_records(**kwargs), minimum_abort_calls=10)
        family = next(
            row for row in result["families"]
            if row["workload"] == "balanced" and row["shape"] == "binary"
        )
        assert family["outcome"] == "indeterminate"
    rows = _complete_records()
    rows = [
        row for row in rows
        if (row["workload"], row["block_id"], row["shape"], row["mean_us"]) != keys[1]
    ]
    result = B.judge(rows, minimum_abort_calls=10)
    family = next(
        row for row in result["families"]
        if row["workload"] == "balanced" and row["shape"] == "binary"
    )
    assert family["outcome"] == "indeterminate"


def test_cell_effects_cover_all_54_factorial_cells_with_ci():
    effects = B.cell_effects(_complete_records(), minimum_abort_calls=10)
    assert len(effects) == 54
    assert all(row["status"] == "estimable" for row in effects)
    assert all(row["ci95_low"] is not None and row["ci95_high"] is not None for row in effects)
    assert {row["equivalence_relation"] for row in effects} <= {
        "inside-equivalence-range", "outside-equivalence-range",
        "overlaps-equivalence-boundary",
    }


def test_nominal_wait_uses_abort_calls_times_target_mean():
    assert B._nominal_wait(123, 25) == 3075
    assert B._nominal_wait(123, 0) == 0
    assert B._nominal_wait(123, None) is None


def test_actual_patch_has_only_one_authorized_hole_line_and_exact_formula_sha():
    patch = _patch_bytes()
    assert B.validate_patch_bytes(patch, _sha(patch)) == _sha(patch)
    assert patch.count(b"+" + B.EXPECTED_HOLE_LINE.encode("utf-8")) == 1
    assert hashlib.sha256(B.EXPECTED_HOLE_LINE.encode("utf-8")).hexdigest() == B.FORMULA_SHA256


def test_actual_cpp_expression_compiles_with_werror_and_matches_fraction_model(tmp_path: Path):
    compiler = next(
        (path for name in ("g++-13", "g++-12", "g++") if (path := shutil.which(name))),
        None,
    )
    if compiler is None:
        pytest.skip("C++ compiler unavailable; explicit environment-detected skip")
    source = tmp_path / "b10_expr.cc"
    binary = tmp_path / "b10_expr"
    source.write_text(
        "#include <cstdint>\n"
        "#include <cstdlib>\n"
        "#include <iomanip>\n"
        "#include <iostream>\n"
        "using std::uint64_t;\n"
        "int main(int argc, char** argv) {\n"
        "  if (argc != 3) return 2;\n"
        "  const uint64_t BACKOFF_FIXED = std::strtoull(argv[1], nullptr, 10);\n"
        "  const uint64_t start = std::strtoull(argv[2], nullptr, 10);\n"
        f"{B.EXPECTED_HOLE_LINE}\n"
        "  std::cout << std::setprecision(17) << now_backoff << '\\n';\n"
        "  return 0;\n"
        "}\n",
        encoding="utf-8",
    )
    compiled = subprocess.run(
        [compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        capture_output=True, text=True,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    starts = (0, 1, 2, 17, (1 << 63) - 1, 1 << 63, (1 << 64) - 1)
    for shape, _code in B.SHAPES:
        for mean_us in B.MEANS_US:
            encoded = B.encode(shape, mean_us)
            for start in starts:
                completed = subprocess.run(
                    [str(binary), str(encoded), str(start)],
                    capture_output=True, text=True,
                )
                assert completed.returncode == 0, completed.stderr
                assert Fraction(completed.stdout.strip()) == B.exact_model(encoded, start)


def test_pegasus_submit_and_job_scripts_are_syntax_valid_and_use_pbs_contract():
    submit = ROOT / "tools/pegasus/submit_b10_backoff_shape.sh"
    job = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    for path in (submit, job):
        completed = subprocess.run(
            ["bash", "-n", str(path)], capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
    submit_text = submit.read_text(encoding="utf-8")
    job_text = job.read_text(encoding="utf-8")
    assert "qsub -o" in submit_text and "-v \"$export_spec\"" in submit_text
    assert "dispatch_compute.py" not in submit_text + job_text
    assert "#PBS -q gen_S" in job_text
    assert "^bnode[0-9]+$" in job_text
    assert "IZANAGI_RESERVATION_JOB_ID" in job_text
    assert "b10_backoff_shape_sweep" in job_text


def test_plain_runner_executes_this_file_instead_of_false_green():
    source = Path(__file__).read_text(encoding="utf-8")
    assert "pytest.main" in source.split("__main__", 1)[1]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
