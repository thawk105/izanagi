"""T-1943 fixed-cell payload-lineage discriminator contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign import mocc_g2_discriminator as DISC


KEY_A = "0000000000000000"
KEY_B = "0000000000000001"
SOURCE_OID = "a" * 40
BINARY_SHA = "b" * 64


def _write_manifest(
    path: Path,
    root: Path,
    *,
    schema: str,
    kind: str,
    pattern: str,
) -> None:
    files = []
    for candidate in sorted(root.glob(pattern)):
        raw = candidate.read_bytes()
        files.append(
            {
                "name": candidate.name,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            }
        )
    path.write_text(
        json.dumps(
            {
                "schema_version": schema,
                "artifact_kind": kind,
                "root_dir": str(root),
                "source_oid": SOURCE_OID,
                "binary_sha256": BINARY_SHA,
                "workload": dict(DISC.EXACT_WORKLOAD),
                "files": files,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _anomaly() -> dict[str, object]:
    return {
        "phenomenon": "G2",
        "length": 2,
        "cycle": [0, 1],
        "edges": [
            {
                "from": 0,
                "to": 1,
                "types": ["rw"],
                "reasons": [
                    {
                        "type": "rw",
                        "key": KEY_B,
                        "u_ver": [1, 0],
                        "v_ver": [1, 2],
                    }
                ],
            },
            {
                "from": 1,
                "to": 0,
                "types": ["rw"],
                "reasons": [
                    {
                        "type": "rw",
                        "key": KEY_A,
                        "u_ver": [1, 0],
                        "v_ver": [1, 1],
                    }
                ],
            },
        ],
    }


def _verifier(trace_dir: Path) -> dict[str, object]:
    anomaly = _anomaly()
    result = {
        "trace_dir": str(trace_dir),
        "verdict": "non-serializable",
        "certified": False,
        "serializable": False,
        "stats": {"txns": 2, "reads": 2, "writes": 2, "keys": 2, "edges": 2},
        "integrity": {"clean": True},
        "anomaly_count": 1,
        "total_cycles": 1,
        "anomalies": [anomaly],
    }
    return {
        "runs": 1,
        "certified_serializable": 0,
        "non_serializable": 1,
        "indeterminate": 0,
        "results": [result],
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    trace_dir = tmp_path / "trace"
    witness_dir = tmp_path / "witness"
    trace_dir.mkdir()
    witness_dir.mkdir()
    (trace_dir / "trace_0.log").write_text(
        "".join(
            (
                f"C 0 0 1 1 1 1\n",
                f"R 0 {KEY_B} 1 0\n",
                f"W 0 {KEY_A} U 1 1\n",
                "E 0\n",
                f"C 1 0 1 2 1 1\n",
                f"R 1 {KEY_A} 1 0\n",
                f"W 1 {KEY_B} U 1 2\n",
                "E 1\n",
            )
        ),
        encoding="ascii",
    )
    (witness_dir / "witness_0.log").write_text(
        "".join(
            (
                "H IZANAGI_MOCC_G2_WATERMARK_V1 1\n",
                f"L 0 {KEY_B} 1 0 G -\n",
                f"S 0 {KEY_A} 1 1 0\n",
                f"L 1 {KEY_A} 1 0 G -\n",
                f"S 1 {KEY_B} 1 2 1\n",
            )
        ),
        encoding="ascii",
    )
    trace_manifest = tmp_path / "trace-manifest.json"
    witness_manifest = tmp_path / "witness-manifest.json"
    verifier_path = tmp_path / "verifier.json"
    _write_manifest(
        trace_manifest,
        trace_dir,
        schema=DISC.TRACE_MANIFEST_SCHEMA,
        kind="standard-trace",
        pattern="trace_*.log",
    )
    _write_manifest(
        witness_manifest,
        witness_dir,
        schema=DISC.WITNESS_MANIFEST_SCHEMA,
        kind="payload-witness",
        pattern="witness_*.log",
    )
    verifier_path.write_text(
        json.dumps(_verifier(trace_dir), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return trace_manifest, witness_manifest, verifier_path, trace_dir, witness_dir


def _rewrite_manifest(path: Path, root: Path, *, witness: bool) -> None:
    _write_manifest(
        path,
        root,
        schema=(DISC.WITNESS_MANIFEST_SCHEMA if witness else DISC.TRACE_MANIFEST_SCHEMA),
        kind=("payload-witness" if witness else "standard-trace"),
        pattern=("witness_*.log" if witness else "trace_*.log"),
    )


def test_clean_two_rw_edge_payload_lineage_is_supported(tmp_path: Path) -> None:
    trace_manifest, witness_manifest, verifier, _trace, _witness = _fixture(tmp_path)
    result = DISC.discriminate(trace_manifest, witness_manifest, verifier)
    assert result["conclusion"] == "supported"
    assert result["blockers"] == []
    assert len(result["comparisons"]) == 2
    assert result["limits"] == {
        "writer_version_verified": False,
        "write_store_order_verified_beyond_post_store_token": False,
        "commit_order_verified": False,
        "mocc_root_cause_verified": False,
        "serializable_elevation_allowed": False,
    }


def test_non_genesis_writer_lineage_is_supported_alongside_genesis(
    tmp_path: Path,
) -> None:
    trace_manifest, witness_manifest, verifier_path, trace, witness = _fixture(
        tmp_path
    )
    trace_path = trace / "trace_0.log"
    trace_path.write_text(
        "".join(
            (
                f"C 2 0 1 1 0 1\n",
                f"W 2 {KEY_B} U 1 1\n",
                "E 2\n",
                f"C 0 0 1 2 1 1\n",
                f"R 0 {KEY_B} 1 1\n",
                f"W 0 {KEY_A} U 1 2\n",
                "E 0\n",
                f"C 1 0 1 3 1 1\n",
                f"R 1 {KEY_A} 1 0\n",
                f"W 1 {KEY_B} U 1 3\n",
                "E 1\n",
            )
        ),
        encoding="ascii",
    )
    witness_path = witness / "witness_0.log"
    witness_path.write_text(
        "".join(
            (
                "H IZANAGI_MOCC_G2_WATERMARK_V1 1\n",
                f"S 2 {KEY_B} 1 1 2\n",
                f"L 0 {KEY_B} 1 1 T 2\n",
                f"S 0 {KEY_A} 1 2 0\n",
                f"L 1 {KEY_A} 1 0 G -\n",
                f"S 1 {KEY_B} 1 3 1\n",
            )
        ),
        encoding="ascii",
    )
    verifier = json.loads(verifier_path.read_text(encoding="utf-8"))
    anomaly = verifier["results"][0]["anomalies"][0]
    anomaly["edges"][0]["reasons"][0].update(
        {"u_ver": [1, 1], "v_ver": [1, 3]}
    )
    anomaly["edges"][1]["reasons"][0]["v_ver"] = [1, 2]
    verifier_path.write_text(
        json.dumps(verifier, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    _rewrite_manifest(trace_manifest, trace, witness=False)
    _rewrite_manifest(witness_manifest, witness, witness=True)

    result = DISC.discriminate(trace_manifest, witness_manifest, verifier_path)

    assert result["conclusion"] == "supported"
    assert result["blockers"] == []
    assert result["comparisons"] == [
        {
            "reader_txid": 0,
            "key": KEY_B,
            "reader_version": [1, 1],
            "expected_payload_producer": "2",
            "observed_payload_producer": "2",
        },
        {
            "reader_txid": 1,
            "key": KEY_A,
            "reader_version": [1, 0],
            "expected_payload_producer": "genesis",
            "observed_payload_producer": "genesis",
        },
    ]


def test_payload_producer_mismatch_is_contradicted_not_serializable(
    tmp_path: Path,
) -> None:
    trace_manifest, witness_manifest, verifier, _trace, witness = _fixture(tmp_path)
    path = witness / "witness_0.log"
    path.write_text(
        path.read_text(encoding="ascii").replace(
            f"L 1 {KEY_A} 1 0 G -", f"L 1 {KEY_A} 1 0 T 0"
        ),
        encoding="ascii",
    )
    _rewrite_manifest(witness_manifest, witness, witness=True)
    result = DISC.discriminate(trace_manifest, witness_manifest, verifier)
    assert result["conclusion"] == "contradicted"
    assert result["limits"]["serializable_elevation_allowed"] is False


def test_implicit_genesis_and_explicit_writer_collision_is_indeterminate(
    tmp_path: Path,
) -> None:
    trace_manifest, witness_manifest, verifier, trace, witness = _fixture(tmp_path)
    with (trace / "trace_0.log").open("a", encoding="ascii") as handle:
        handle.write(f"C 2 0 1 0 0 1\nW 2 {KEY_B} U 1 0\nE 2\n")
    with (witness / "witness_0.log").open("a", encoding="ascii") as handle:
        handle.write(f"S 2 {KEY_B} 1 0 2\n")
    _rewrite_manifest(trace_manifest, trace, witness=False)
    _rewrite_manifest(witness_manifest, witness, witness=True)

    result = DISC.discriminate(trace_manifest, witness_manifest, verifier)

    assert result["conclusion"] == "indeterminate"
    assert result["blockers"] == [
        "standard-trace-implicit-genesis-producer-collision"
    ]
    assert result["comparisons"] == []


def test_post_store_token_mismatch_is_single_reason_indeterminate(
    tmp_path: Path,
) -> None:
    trace_manifest, witness_manifest, verifier, _trace, witness = _fixture(tmp_path)
    path = witness / "witness_0.log"
    path.write_text(
        path.read_text(encoding="ascii").replace(
            f"S 1 {KEY_B} 1 2 1", f"S 1 {KEY_B} 1 2 2"
        ),
        encoding="ascii",
    )
    _rewrite_manifest(witness_manifest, witness, witness=True)

    result = DISC.discriminate(trace_manifest, witness_manifest, verifier)

    assert result["conclusion"] == "indeterminate"
    assert result["blockers"] == ["witness-post-store-token-mismatch"]
    assert result["comparisons"] == []


@pytest.mark.parametrize(
    "mutation,expected_blocker",
    (
        pytest.param("dirty-and-mismatch", "verifier-integrity-dirty", id="dirty"),
        pytest.param(
            "missing-lineage",
            "witness-lineage-missing-duplicate-or-orphan",
            id="missing",
        ),
        pytest.param("duplicate-lineage", "witness-duplicate-lineage", id="duplicate"),
        pytest.param(
            "orphan-lineage",
            "witness-lineage-missing-duplicate-or-orphan",
            id="orphan",
        ),
        pytest.param(
            "identity-collision",
            "standard-trace-producer-identity-collision",
            id="identity-collision",
        ),
        pytest.param(
            "reason-multiplicity",
            "rw-reason-multiplicity-mismatch",
            id="reason-multiplicity",
        ),
        pytest.param(
            "anomaly-truncation",
            "verifier-anomaly-list-truncated",
            id="anomaly-truncation",
        ),
        pytest.param(
            "missing-post-store",
            "witness-store-missing-duplicate-or-orphan",
            id="missing-post-store",
        ),
        pytest.param(
            "thread-identity",
            "standard-trace-thread-identity-collision",
            id="thread-identity",
        ),
        pytest.param(
            "cycle-edge-projection",
            "verifier-cycle-edge-projection-mismatch",
            id="cycle-edge-projection",
        ),
        pytest.param(
            "verifier-indeterminate",
            "verifier-verdict-indeterminate",
            id="verifier-indeterminate",
        ),
    ),
)
def test_ambiguity_precedes_payload_comparison(
    tmp_path: Path, mutation: str, expected_blocker: str
) -> None:
    trace_manifest, witness_manifest, verifier_path, trace, witness = _fixture(tmp_path)
    verifier = json.loads(verifier_path.read_text(encoding="utf-8"))
    witness_path = witness / "witness_0.log"
    trace_path = trace / "trace_0.log"
    if mutation == "dirty-and-mismatch":
        verifier["results"][0]["integrity"]["clean"] = False
        witness_path.write_text(
            witness_path.read_text(encoding="ascii").replace(
                f"L 1 {KEY_A} 1 0 G -", f"L 1 {KEY_A} 1 0 T 0"
            ),
            encoding="ascii",
        )
    elif mutation == "missing-lineage":
        witness_path.write_text(
            witness_path.read_text(encoding="ascii").replace(
                f"L 1 {KEY_A} 1 0 G -\n", ""
            ),
            encoding="ascii",
        )
    elif mutation == "duplicate-lineage":
        with witness_path.open("a", encoding="ascii") as handle:
            handle.write(f"L 1 {KEY_A} 1 0 G -\n")
    elif mutation == "orphan-lineage":
        with witness_path.open("a", encoding="ascii") as handle:
            handle.write(f"L 99 {KEY_A} 1 0 G -\n")
    elif mutation == "identity-collision":
        with trace_path.open("a", encoding="ascii") as handle:
            handle.write(f"C 2 0 1 1 0 1\nW 2 {KEY_A} U 1 1\nE 2\n")
        with witness_path.open("a", encoding="ascii") as handle:
            handle.write(f"S 2 {KEY_A} 1 1 2\n")
    elif mutation == "reason-multiplicity":
        reasons = verifier["results"][0]["anomalies"][0]["edges"][0]["reasons"]
        reasons.append(copy.deepcopy(reasons[0]))
    elif mutation == "anomaly-truncation":
        verifier["results"][0]["total_cycles"] = 2
    elif mutation == "missing-post-store":
        witness_path.write_text(
            witness_path.read_text(encoding="ascii").replace(
                f"S 1 {KEY_B} 1 2 1\n", ""
            ),
            encoding="ascii",
        )
    elif mutation == "thread-identity":
        trace_path.write_text(
            trace_path.read_text(encoding="ascii").replace(
                "C 0 0 1 1 1 1", "C 0 1 1 1 1 1"
            ),
            encoding="ascii",
        )
    elif mutation == "cycle-edge-projection":
        verifier["results"][0]["anomalies"][0]["cycle"] = [1, 0]
    elif mutation == "verifier-indeterminate":
        verifier["results"][0]["verdict"] = "indeterminate"
        verifier.update(
            {"certified_serializable": 0, "non_serializable": 0, "indeterminate": 1}
        )
    else:
        raise AssertionError(mutation)
    verifier_path.write_text(
        json.dumps(verifier, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    _rewrite_manifest(trace_manifest, trace, witness=False)
    _rewrite_manifest(witness_manifest, witness, witness=True)
    result = DISC.discriminate(trace_manifest, witness_manifest, verifier_path)
    assert result["conclusion"] == "indeterminate"
    assert expected_blocker in result["blockers"]
    assert result["comparisons"] == []


def test_no_g2_is_terminal_without_payload_comparison(tmp_path: Path) -> None:
    trace_manifest, witness_manifest, verifier_path, _trace, _witness = _fixture(tmp_path)
    verifier = json.loads(verifier_path.read_text(encoding="utf-8"))
    result = verifier["results"][0]
    result.update(
        {
            "verdict": "serializable",
            "certified": True,
            "serializable": True,
            "anomaly_count": 0,
            "total_cycles": 0,
            "anomalies": [],
        }
    )
    verifier.update(
        {"certified_serializable": 1, "non_serializable": 0, "indeterminate": 0}
    )
    verifier_path.write_text(
        json.dumps(verifier, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    outcome = DISC.discriminate(trace_manifest, witness_manifest, verifier_path)
    assert outcome["conclusion"] == "no-g2"
    assert outcome["comparisons"] == []


def test_cli_output_is_create_only_and_manifest_hashes_are_enforced(
    tmp_path: Path,
) -> None:
    trace_manifest, witness_manifest, verifier, trace, _witness = _fixture(tmp_path)
    output = tmp_path / "result.json"
    argv = [
        "--trace-manifest", str(trace_manifest),
        "--witness-manifest", str(witness_manifest),
        "--verifier", str(verifier),
        "--output", str(output),
    ]
    assert DISC.main(argv) == 0
    original = output.read_bytes()
    assert DISC.main(argv) == 2
    assert output.read_bytes() == original
    with (trace / "trace_0.log").open("a", encoding="ascii") as handle:
        handle.write("E 99\n")
    with pytest.raises(DISC.DiscriminatorError, match="changed after manifest"):
        DISC.discriminate(trace_manifest, witness_manifest, verifier)


def test_txid_beyond_watermark_range_is_rejected(tmp_path: Path) -> None:
    trace_manifest, witness_manifest, verifier, trace, _witness = _fixture(tmp_path)
    path = trace / "trace_0.log"
    path.write_text(
        path.read_text(encoding="ascii").replace(
            "C 0 0 1 1 1 1", f"C {1 << 48} 0 1 1 1 1"
        ),
        encoding="ascii",
    )
    _rewrite_manifest(trace_manifest, trace, witness=False)
    with pytest.raises(DISC.DiscriminatorError, match="watermark range"):
        DISC.discriminate(trace_manifest, witness_manifest, verifier)


def test_verifier_booleans_must_match_verdict(tmp_path: Path) -> None:
    trace_manifest, witness_manifest, verifier_path, _trace, _witness = _fixture(
        tmp_path
    )
    verifier = json.loads(verifier_path.read_text(encoding="utf-8"))
    verifier["results"][0]["certified"] = True
    verifier_path.write_text(
        json.dumps(verifier, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(DISC.DiscriminatorError, match="booleans contradict"):
        DISC.discriminate(trace_manifest, witness_manifest, verifier_path)


def test_verifier_runs_rejects_json_boolean(tmp_path: Path) -> None:
    trace_manifest, witness_manifest, verifier_path, _trace, _witness = _fixture(
        tmp_path
    )
    verifier = json.loads(verifier_path.read_text(encoding="utf-8"))
    verifier["runs"] = True
    verifier_path.write_text(
        json.dumps(verifier, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(DISC.DiscriminatorError, match="exactly one run"):
        DISC.discriminate(trace_manifest, witness_manifest, verifier_path)


def test_transaction_watermark_surface_is_trace_guarded_and_post_store() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "external/ccbench/cc/mocc/transaction.cc"
    ).read_text(encoding="utf-8")
    assert "#include <cstring>" not in source
    assert "#include <cstdlib>" not in source
    trace_depth = 0
    conditional_stack: list[bool] = []
    guarded_occurrences = 0
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#if"):
            is_trace = stripped == "#if TRACE"
            conditional_stack.append(is_trace or trace_depth > 0)
            trace_depth = sum(conditional_stack)
        elif stripped.startswith("#endif"):
            assert conditional_stack
            conditional_stack.pop()
            trace_depth = sum(conditional_stack)
        if "izanagi_mocc_g2" in line:
            guarded_occurrences += 1
            assert trace_depth > 0, line
    assert guarded_occurrences >= 12
    assert "izanagi_mocc_g2_decode(read.body_, producer)" in source
    assert "izanagi_mocc_g2_decode(write.rcdptr_->body_, stored_producer)" in source
    stamp = source.index("izanagi_mocc_g2_stamp((*itr).body_, izanagi_txid)")
    payload_store = source.index("memcpy((*itr).rcdptr_->body_.get_val_ptr()", stamp)
    tid_store = source.index("__atomic_store_n(&((*itr).rcdptr_->tidword_.obj_)", payload_store)
    post_store = source.index("izanagi_mocc_g2_emit_post_store", tid_store)
    assert stamp < payload_store < tid_store < post_store
