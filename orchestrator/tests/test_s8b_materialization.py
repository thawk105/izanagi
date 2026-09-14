# -*- coding: utf-8 -*-
"""共有 materialization モジュールの characterization / drift-guard / import 契約。

期待値はすべてテスト内に literal に固定した canonical bytes と SHA-256 (本番 helper を
呼んで計算しない — 恒真化禁止)。identity の値・manifest bytes が抽出前後で bit-exact に
不変であることを保証する道具。
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_materialization as M  # noqa: E402
from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.s1_direct_comparison import PreparedCell  # noqa: E402
from orchestrator.campaign.sort_swo_oracle import (  # noqa: E402
    SORT_SWO_GUARANTEE_BOUNDARY,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s8b_floor_evidence_fixture import (  # noqa: E402
    expected_portable_sort_swo_pass_receipt as _fixture_expected_portable,
    fake_sort_swo_pass_attempt as _fixture_fake_attempt,
)


def fake_sort_swo_pass_attempt() -> dict[str, object]:
    """旧 fixture を現行 raw receipt の exact schema へ射影する。"""
    attempt = _fixture_fake_attempt()
    raw = attempt["oracle_receipt"]
    assert isinstance(raw, dict)
    raw["guarantee_boundary"] = SORT_SWO_GUARANTEE_BOUNDARY
    return attempt


def expected_portable_sort_swo_pass_receipt(
    **identity: str,
) -> dict[str, object]:
    """本番 projector から独立して現行 portable receipt を再計算する。"""
    expected = _fixture_expected_portable(**identity)
    raw = fake_sort_swo_pass_attempt()["oracle_receipt"]
    assert isinstance(raw, dict)
    expected["guarantee_boundary"] = SORT_SWO_GUARANTEE_BOUNDARY
    canonical_raw = json.dumps(
        raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    expected["receipt_sha256"] = hashlib.sha256(canonical_raw).hexdigest()
    return expected


def _prepared(protocol: str, flags: dict, src_token: str) -> PreparedCell:
    return PreparedCell(
        genome=Genome(protocol, dict(flags)),
        src_token=src_token,
        ccbench_dir="/tmp/fixture-ccbench",
        cache_root="/tmp/fixture-cache",
    )


# --------------------------------------------------------------------------- #
# G-4: binding identity の literal golden (STOCK / 非 STOCK / Unicode・入れ子)  #
# --------------------------------------------------------------------------- #

def test_binding_from_prepared_stock_golden():
    """STOCK (src_token=='stock' → variant_id は src を省く旧 id)。"""
    entry = {"configuration": "stock", "flags": {"BACKOFF_FIXED": 0}}
    prepared = _prepared("silo", {"BACKOFF_FIXED": 0}, "stock")
    identity = M.binding_from_prepared(entry, prepared)
    assert identity == {
        "genome_canonical": "silo|BACKOFF_FIXED=0",
        "src_token": "stock",
        "variant_id": "bf5fcd7a997a",
        "entry_sha256":
            "57acf32ff528249c5e474cd2f6569ed4ed3581c85ae2fd7fb2a72be17e97729a",
        "binding_sha256":
            "e1df79581e810cefd9981e4fee13629cf29b2b299ccef7d018e6941092b7a23c",
    }
    # 4-key preimage (binding_sha256 を除く) の canonical bytes を literal で固定。
    assert set(identity) - {"binding_sha256"} == {
        "genome_canonical", "src_token", "variant_id", "entry_sha256",
    }
    preimage_bytes = (
        b'{"entry_sha256":"57acf32ff528249c5e474cd2f6569ed4ed3581c85ae2fd7fb2a72be17e97729a"'
        b',"genome_canonical":"silo|BACKOFF_FIXED=0","src_token":"stock"'
        b',"variant_id":"bf5fcd7a997a"}'
    )
    entry_bytes = b'{"configuration":"stock","flags":{"BACKOFF_FIXED":0}}'
    assert _independent_sha256(preimage_bytes) == identity["binding_sha256"]
    assert _independent_sha256(entry_bytes) == identity["entry_sha256"]


def test_binding_from_prepared_non_stock_golden():
    """非 STOCK (src_token 込みの variant_id、複数 flag)。"""
    entry = {
        "configuration": "backoff_fixed_best",
        "flags": {"BACKOFF_FIXED": 5, "SPIN": 1},
        "backoff_us": 5,
    }
    prepared = _prepared("silo", {"BACKOFF_FIXED": 5, "SPIN": 1}, "abc123def456")
    identity = M.binding_from_prepared(entry, prepared)
    assert identity == {
        "genome_canonical": "silo|BACKOFF_FIXED=5,SPIN=1",
        "src_token": "abc123def456",
        "variant_id": "ab3938671872",
        "entry_sha256":
            "3e076f35bc4197bc04c6f32445290e6aca24abf7d584dc1b9963eefe24283abe",
        "binding_sha256":
            "e34c7200fa5b0f7e5c5dce37d2ce721174cf19eafa84d92bbec423f568704bee",
    }
    preimage_bytes = (
        b'{"entry_sha256":"3e076f35bc4197bc04c6f32445290e6aca24abf7d584dc1b9963eefe24283abe"'
        b',"genome_canonical":"silo|BACKOFF_FIXED=5,SPIN=1","src_token":"abc123def456"'
        b',"variant_id":"ab3938671872"}'
    )
    entry_bytes = (
        b'{"backoff_us":5,"configuration":"backoff_fixed_best"'
        b',"flags":{"BACKOFF_FIXED":5,"SPIN":1}}'
    )
    assert _independent_sha256(preimage_bytes) == identity["binding_sha256"]
    assert _independent_sha256(entry_bytes) == identity["entry_sha256"]


def test_binding_from_prepared_unicode_nested_golden():
    """Unicode・入れ子・null を含む entry (ensure_ascii=False の非 ASCII を固定)。"""
    entry = {
        "configuration": "system_gate",
        "gate_predicate": "return café ≥ 0; // 日本語",
        "nested": {"b": [1, {"c": "λ"}], "a": None},
    }
    prepared = _prepared("silo", {"GATE": 1}, "uñic0de")
    identity = M.binding_from_prepared(entry, prepared)
    assert identity == {
        "genome_canonical": "silo|GATE=1",
        "src_token": "uñic0de",
        "variant_id": "8fa29084e95a",
        "entry_sha256":
            "c211c1d3a5be6dffe1e788e94c16c5c0a92fc18767dacc16a8f2dfbeefbe8ad0",
        "binding_sha256":
            "2b93c81cb2241cfa23dc0a0c1f52d2f04650c512e249b84a975017c417893683",
    }
    preimage_bytes = (
        '{"entry_sha256":"c211c1d3a5be6dffe1e788e94c16c5c0a92fc18767dacc16a8f2dfbeefbe8ad0"'
        ',"genome_canonical":"silo|GATE=1","src_token":"uñic0de"'
        ',"variant_id":"8fa29084e95a"}'
    ).encode("utf-8")
    entry_bytes = (
        '{"configuration":"system_gate"'
        ',"gate_predicate":"return café ≥ 0; // 日本語"'
        ',"nested":{"a":null,"b":[1,{"c":"λ"}]}}'
    ).encode("utf-8")
    assert _independent_sha256(preimage_bytes) == identity["binding_sha256"]
    assert _independent_sha256(entry_bytes) == identity["entry_sha256"]


def _independent_sha256(raw: bytes) -> str:
    """本番 helper を経由しない独立 SHA-256 (恒真化回避のための照合用)。"""
    return hashlib.sha256(raw).hexdigest()


def test_binding_from_prepared_rejects_non_prepared_cell():
    with pytest.raises(M.MaterializationError, match="PreparedCell でない"):
        M.binding_from_prepared({"configuration": "stock"}, {"not": "a cell"})


# --------------------------------------------------------------------------- #
# binding_entry: freeze からの entry 抽出                                       #
# --------------------------------------------------------------------------- #

def _freeze_with(entry) -> dict:
    return {
        "holdouts": {
            "H1": {"variant_binding": {"entries": {"stock": entry}}},
        },
    }


def test_binding_entry_returns_entry():
    entry = {"configuration": "stock", "flags": {"BACKOFF_FIXED": 0}}
    assert M.binding_entry(_freeze_with(entry), "H1", "stock") is entry


def test_binding_entry_missing_holdout_raises():
    entry = {"configuration": "stock"}
    with pytest.raises(M.MaterializationError, match="freeze binding がない"):
        M.binding_entry(_freeze_with(entry), "NOPE", "stock")


def test_binding_entry_non_object_entry_raises():
    with pytest.raises(M.MaterializationError, match="object でない"):
        M.binding_entry(_freeze_with(["not", "a", "map"]), "H1", "stock")


# --------------------------------------------------------------------------- #
# prepared_binding: contextmanager 分岐 (contextmanager 戻り / 素の値戻り)      #
# --------------------------------------------------------------------------- #

_ENTRY = {"configuration": "stock", "flags": {"BACKOFF_FIXED": 0}}
_FREEZE = {"holdouts": {"H1": {"variant_binding": {"entries": {"stock": _ENTRY}}}}}


def _cell() -> PreparedCell:
    return _prepared("silo", {"BACKOFF_FIXED": 0}, "stock")


def test_prepared_binding_contextmanager_branch():
    """prepare_fn が contextmanager を返す分岐。"""
    @contextlib.contextmanager
    def prepare_fn(cell, ccbench_pin, *, cxx):
        assert cell == {"configuration": "stock", "variant": _ENTRY}
        assert ccbench_pin == "pin-1"
        assert cxx == "site-cxx"
        yield _cell()

    with M.prepared_binding(
            freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
            ccbench_pin="pin-1", cxx="site-cxx",
            prepare_fn=prepare_fn) as (identity, prepared):
        assert identity["binding_sha256"] == (
            "e1df79581e810cefd9981e4fee13629cf29b2b299ccef7d018e6941092b7a23c"
        )
        assert isinstance(prepared, PreparedCell)


def test_prepared_binding_raw_value_branch():
    """prepare_fn が素の値 (contextmanager でない) を返す分岐 → nullcontext 包み。"""
    def prepare_fn(cell, ccbench_pin, *, cxx):
        return _cell()

    with M.prepared_binding(
            freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
            ccbench_pin="pin-1", cxx="site-cxx",
            prepare_fn=prepare_fn) as (identity, prepared):
        assert identity["variant_id"] == "bf5fcd7a997a"
        assert isinstance(prepared, PreparedCell)


# --------------------------------------------------------------------------- #
# G-5: ライフサイクル (alive flag / exit ちょうど 1 回 / 例外時 cleanup)         #
# --------------------------------------------------------------------------- #

class _AliveManager:
    """alive flag と exit 回数を観測する fake contextmanager。"""

    def __init__(self, resource, *, exit_raises=None):
        self.resource = resource
        self.alive = False
        self.enter_count = 0
        self.exit_count = 0
        self._exit_raises = exit_raises

    def __enter__(self):
        self.enter_count += 1
        self.alive = True
        return self.resource

    def __exit__(self, exc_type, exc, tb):
        self.exit_count += 1
        self.alive = False
        if self._exit_raises is not None:
            raise self._exit_raises
        return False


def test_prepared_binding_manager_alive_during_consumer_and_exits_once():
    mgr = _AliveManager(_cell())

    def prepare_fn(cell, ccbench_pin, *, cxx):
        return mgr

    with M.prepared_binding(
            freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
            ccbench_pin="pin-1", cxx="site-cxx",
            prepare_fn=prepare_fn) as (_identity, _prepared):
        # consumer 実行中は manager が生存している。
        assert mgr.alive is True
        assert mgr.exit_count == 0
    # 正常 exit はちょうど 1 回。
    assert mgr.alive is False
    assert mgr.exit_count == 1
    assert mgr.enter_count == 1


def test_prepared_binding_cleanup_on_identity_synthesis_exception():
    """identity 合成 (binding_from_prepared) が例外を投げても manager は cleanup される。"""
    # prepare_fn が PreparedCell でない資源を返すと binding_from_prepared が失敗する。
    mgr = _AliveManager({"not": "a prepared cell"})

    def prepare_fn(cell, ccbench_pin, *, cxx):
        return mgr

    with pytest.raises(M.MaterializationError):
        with M.prepared_binding(
                freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
                ccbench_pin="pin-1", cxx="site-cxx",
                prepare_fn=prepare_fn):
            pytest.fail("identity 合成失敗で body に入ってはならない")
    # 例外経路でも exit が呼ばれている (cleanup)。
    assert mgr.exit_count == 1
    assert mgr.alive is False


def test_prepared_binding_cleanup_exception_not_swallowed():
    """cleanup (manager __exit__) の例外は握りつぶさず伝播する (現行挙動固定)。"""
    boom = RuntimeError("cleanup failed")
    mgr = _AliveManager(_cell(), exit_raises=boom)

    def prepare_fn(cell, ccbench_pin, *, cxx):
        return mgr

    with pytest.raises(RuntimeError, match="cleanup failed"):
        with M.prepared_binding(
                freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
                ccbench_pin="pin-1", cxx="site-cxx",
                prepare_fn=prepare_fn):
            pass
    assert mgr.exit_count == 1


# --------------------------------------------------------------------------- #
# G-6 drift-guard: driver / manifest / report の binding キー集合の同値         #
# --------------------------------------------------------------------------- #

def test_binding_key_sets_are_equivalent_across_consumers():
    from orchestrator.campaign import s8b_oracle_driver as driver
    from orchestrator.campaign import s8b_oracle_manifest as manifest
    from orchestrator.campaign import s8b_oracle_report as report

    producer_keys = {
        "genome_canonical", "src_token", "variant_id", "entry_sha256",
        "binding_sha256",
    }
    cell_keys = {"holdout_id", "configuration_id"}

    # driver は producer 5 キーだけを検証する。
    assert driver._BINDING_KEYS == producer_keys
    # manifest / report は cell identity 2 キーを足した 7 キー集合。
    assert manifest._BINDING_KEYS == producer_keys | cell_keys
    assert report._BINDING_KEYS == producer_keys | cell_keys
    # producer 集合が両 verifier の cell 差し引きと同値であることを固定。
    assert driver._BINDING_KEYS == manifest._BINDING_KEYS - cell_keys
    assert driver._BINDING_KEYS == report._BINDING_KEYS - cell_keys


def test_binding_from_prepared_key_set_matches_driver_binding_keys():
    from orchestrator.campaign import s8b_oracle_driver as driver

    identity = M.binding_from_prepared(_ENTRY, _cell())
    assert set(identity) == driver._BINDING_KEYS


# --------------------------------------------------------------------------- #
# G-6 drift-guard: 同一 fixture 群に対する manifest/report verifier の受理/拒否   #
#   の同値 (キー集合は同じでも検証ロジックが分岐する drift を検出する)。          #
#   検証コード自体は変更しない — 現行挙動の同値を固定するだけ。                  #
# --------------------------------------------------------------------------- #

# manifest/report が共有する schema 検証次元 (キー集合・型・SHA-256 形式・
# binding_sha256 再計算) のみを突く fixture。cell identity 照合は両者で経路が
# 異なる (manifest は schedule cell 数/重複、report は渡した holdout/config) ため
# 意図的に一致させ、この同値テストの対象外とする。
def _valid_binding_entry() -> dict:
    return {
        "holdout_id": "H1",
        "configuration_id": "stock",
        "genome_canonical": "silo|BACKOFF_FIXED=0",
        "src_token": "stock",
        "variant_id": "bf5fcd7a997a",
        "entry_sha256":
            "57acf32ff528249c5e474cd2f6569ed4ed3581c85ae2fd7fb2a72be17e97729a",
        "binding_sha256":
            "e1df79581e810cefd9981e4fee13629cf29b2b299ccef7d018e6941092b7a23c",
    }


def _without(key: str) -> dict:
    entry = _valid_binding_entry()
    del entry[key]
    return entry


def _with_extra() -> dict:
    entry = _valid_binding_entry()
    entry["binary_sha256"] = "0" * 64
    return entry


def _mutate(key: str, value) -> dict:
    entry = _valid_binding_entry()
    entry[key] = value
    return entry


_DRIFT_FIXTURES = [
    ("valid", _valid_binding_entry(), True),
    ("missing_binding_sha256", _without("binding_sha256"), False),
    ("missing_variant_id", _without("variant_id"), False),
    ("extra_key", _with_extra(), False),
    ("variant_id_non_str", _mutate("variant_id", 123), False),
    ("entry_sha256_non_hex", _mutate("entry_sha256", "z" * 64), False),
    ("binding_sha256_wrong", _mutate("binding_sha256", "0" * 64), False),
    ("genome_canonical_empty", _mutate("genome_canonical", ""), False),
]


def _manifest_accepts(entry) -> bool:
    from orchestrator.campaign import s8b_oracle_manifest as manifest

    schedule = {"rows": [{"holdout_id": "H1", "configuration_id": "stock"}]}
    try:
        manifest._validate_binding_identity([entry], schedule=schedule)
        return True
    except manifest.ManifestError:
        return False


def _report_accepts(entry) -> bool:
    from orchestrator.campaign import s8b_oracle_report as report

    return report._binding_schema_issues(
        entry, holdout="H1", configuration="stock") == []


@pytest.mark.parametrize("name,entry,expected", _DRIFT_FIXTURES,
                         ids=[f[0] for f in _DRIFT_FIXTURES])
def test_manifest_report_binding_verdict_equivalent(name, entry, expected):
    """同一 binding fixture を manifest 検証経路と report 検証経路に通し、受理/拒否が
    両者で一致することを固定する。キー集合が同一でも共有 schema 検証ロジックが片方
    だけ変われば、この同値が破れて drift が露見する (G-6)。"""
    manifest_verdict = _manifest_accepts(entry)
    report_verdict = _report_accepts(entry)
    assert manifest_verdict == report_verdict, (
        name, manifest_verdict, report_verdict)
    # 絶対挙動も pin (どちらかが恒真化して両方 True に退化するのを防ぐ)。
    assert manifest_verdict is expected


# --------------------------------------------------------------------------- #
# G-3: 逆 import 禁止 (materialization は oracle/floor を import しない)         #
# --------------------------------------------------------------------------- #

def test_materialization_does_not_import_oracle_or_floor():
    src = (ORCHESTRATOR / "campaign" / "s8b_materialization.py").read_text(
        encoding="utf-8")
    # 実 import 文に oracle/floor が現れないこと (docstring 言及は許容)。
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert "s8b_oracle_driver" not in stripped
            assert "s8b_floor_campaign" not in stripped


# --------------------------------------------------------------------------- #
# G-4: floor build_cells + assemble_manifest の manifest.json golden           #
#   (固定 path/hash fake で抽出前後の manifest bytes 不変を証明する道具)         #
# --------------------------------------------------------------------------- #

class _FakeBuildResult:
    def __init__(
            self, canonical: str, contract_sha256: str, *, out_root: Path,
            ccbench_root: str, source_evidence):
        raw = canonical.encode("utf-8")
        self.bin_sha256 = hashlib.sha256(raw).hexdigest()
        binary = out_root / "fixed" / "bin" / self.bin_sha256
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(raw)
        self.binary = str(binary)
        self.bin_hash = self.bin_sha256[:16]
        self.configure_cmd = ["cfg", canonical]
        self.build_cmd = ["build", canonical]
        self.configure_argv = ["cfg", str(out_root.parent / "cc"), str(out_root), canonical]
        self.build_argv = ["build", str(out_root), canonical]
        self.cached = True
        self.ccbench_root = ccbench_root
        self.contract_sha256 = contract_sha256
        compiler_input = Path(ccbench_root) / "include" / "fixture.hh"
        self.compiler_input_manifest = {
            "schema_version": "s8b-compiler-input/v1",
            "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
            "target": "ycsb_silo.exe",
            "depfile_count": 1,
            "inputs": [{
                "path": "include/fixture.hh",
                "sha256": hashlib.sha256(
                    compiler_input.read_bytes()
                ).hexdigest(),
            }],
        }
        self.compiler_input_manifest_sha256 = hashlib.sha256(json.dumps(
            self.compiler_input_manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        from orchestrator.tests.s8b_v2_freeze_fixture import sealed_source_protection_fixture

        # The prewritten fixture binary is a cache hit, not a claimed compile.
        self.source_protection = sealed_source_protection_fixture(
            source=source_evidence, binary_sha256=self.bin_sha256,
            compiler_input_manifest_sha256=self.compiler_input_manifest_sha256,
        )
        self.source_snapshot_sha256 = self.source_protection.source_snapshot_sha256
        self.expected_materialization_sha256 = (
            self.source_protection.expected_materialization_sha256
        )


def test_floor_manifest_golden_stable(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_floor_manifest_golden_stable"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_floor_manifest_golden_stable(tmp_path):
    """固定 path/hash を返す fake build で manifest.json bytes を安定 hash で golden 固定。

    binding identity は共有 producer が生成するので、この golden が変われば binding か
    manifest 構造が抽出前後で変化したことを検出する。"""
    from orchestrator.tests.s8b_v2_freeze_fixture import sealed_source_protection_fixture

    from unittest import mock
    from orchestrator.campaign import s8b_floor_campaign as floor

    entry_stock = {"configuration": "stock", "flags": {"BACKOFF_FIXED": 0}}
    entry_v1 = {
        "configuration": "sort_best",
        "flags": {"BACKOFF_FIXED": 5, "SPIN": 1},
        "comparator": "return fixture_a < fixture_b;",
    }
    freeze = {"holdouts": {"H1": {"variant_binding": {"entries": {
        "stock": entry_stock, "sort_best": entry_v1}}}}}
    cells = [
        {"cell_id": "H1::stock", "holdout_id": "H1", "configuration_id": "stock",
         "records": 100, "threads": 4, "workload": "wl"},
        {"cell_id": "H1::sort_best", "holdout_id": "H1",
         "configuration_id": "sort_best",
         "records": 100, "threads": 4, "workload": "wl"},
    ]

    @contextlib.contextmanager
    def prepare_fn(cell, ccbench_pin, *, cxx):
        entry = cell["variant"]
        genome = Genome("silo", dict(entry["flags"]))
        token = hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
        ccbench = tmp_path / "cc"
        compiler_input = ccbench / "include" / "fixture.hh"
        compiler_input.parent.mkdir(parents=True, exist_ok=True)
        compiler_input.write_bytes(b"materialization golden compiler input\n")
        yield PreparedCell(genome=genome, src_token=token,
                           ccbench_dir=str(ccbench),
                           cache_root=str(tmp_path / "ca"),
                           oracle_attempt=(
                               fake_sort_swo_pass_attempt()
                               if cell["configuration"] == "sort_best" else None
                           ))

    contract = ec.lookup("linux-baremetal")
    verified_calibration = floor.env_attestation.load_verified_calibration(
        contract, ROOT,
    )

    def fixture_toolchain_binding(candidate, *, cc, cxx):
        assert candidate is verified_calibration
        return {
            "cc": {
                "requested": cc,
                "realpath": f"/fixture/toolchain/{cc}",
                "version_first_line": "fixture cc version",
                "version": "fixture cc version\nfixture cc detail",
            },
            "cxx": {
                "requested": cxx,
                "realpath": f"/fixture/toolchain/{cxx}",
                "version_first_line": "fixture cxx version",
                "version": "fixture cxx version\nfixture cxx detail",
            },
            "cmake": {
                "requested": "cmake",
                "realpath": "/fixture/toolchain/cmake",
                "version_first_line": "cmake version fixture",
                "version": "cmake version fixture\nfixture cmake detail",
            },
        }

    def fixture_evidence(genome, ccbench_commit, *, ccbench_dir="", **_ignored):
        source_sha = hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
        return floor.source_digest.SourceEvidence(
            schema_version=floor.source_digest.SOURCE_EVIDENCE_SCHEMA,
            source_root=str(Path(ccbench_dir).resolve()),
            ccbench_commit=ccbench_commit,
            genome_sha256=source_sha,
            src_token=source_sha,
            source_bytes_sha256=source_sha,
            tracked_clean=True,
            tracked_diff_sha256=floor.source_digest.EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )

    gate_state = {"digest": None}

    def fixture_expected_materialization(**kwargs):
        digest = hashlib.sha256(
            b"materialization-golden-expected\0"
            + json.dumps(
                kwargs["declaration"], ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        gate_state["digest"] = digest
        return digest

    def fixture_exact_materialization(_root, expected):
        assert expected == gate_state["digest"]
        return expected

    def fixture_protect_snapshot(root):
        return floor._expected_materialization.SnapshotPermissionState(
            root=str(root), modes=(), tree_digest=gate_state["digest"],
        )

    def fixture_build(genome, **kwargs):
        descriptor = kwargs["expected_materialization_descriptor"]
        return _FakeBuildResult(
            genome.canonical(), kwargs["contract"].contract_sha256,
            out_root=tmp_path / "out",
            ccbench_root=kwargs["ccbench_dir"],
            source_evidence=kwargs["source_evidence"],
        )

    with mock.patch.object(
            floor.buildcache, "build_v2",
            side_effect=fixture_build), \
            mock.patch.object(
                floor.source_digest, "resolve_evidence", fixture_evidence,
            ), \
            mock.patch.object(
                floor, "_bind_current_toolchain", fixture_toolchain_binding,
            ), \
            mock.patch.object(
                floor._expected_materialization,
                "produce_expected_materialization_from_declaration",
                fixture_expected_materialization,
            ), \
            mock.patch.object(
                floor._expected_materialization,
                "assert_expected_materialization",
                fixture_exact_materialization,
            ), \
            mock.patch.object(
                floor._expected_materialization,
                "make_snapshot_non_writable",
                fixture_protect_snapshot,
            ), \
            mock.patch.object(
                floor._expected_materialization,
                "restore_snapshot_permissions",
                lambda _state: None,
            ):
        built = floor.build_cells(
            freeze, cells, ccbench_pin="pin-x",
            out_root=tmp_path / "out", prepare_fn=prepare_fn,
            contract=contract, verified_calibration=verified_calibration)
    for record in built.values():
        record["store_path"] = str(tmp_path / "out" / "store" / record["binary_sha256"])
    built = floor.project_built_records(built, out_root=tmp_path / "out")

    # 共有 producer が生成した binding が build 記録に載っていること。
    assert built["H1::stock"]["binding"]["binding_sha256"] == (
        "3cc28be2200a465d44e74641c3949624718205283ba6113edb529a33e657a37a"
    )
    sort_record = built["H1::sort_best"]
    assert sort_record["sort_swo_oracle"] == (
        expected_portable_sort_swo_pass_receipt(
            cell_id="H1::sort_best", holdout_id="H1",
            configuration_id="sort_best",
            entry_sha256=sort_record["binding"]["entry_sha256"],
            binary_sha256=sort_record["binary_sha256"],
        )
    )

    # protocol は v2 形状 (blocks/replicates_per_block を廃し session_cv_max/
    # cell_cv_max を持つ)。manifest は v3、schedule は {seq, round, cell_id}。
    protocol = {
        "freeze": {"path": "p", "sha256": "f" * 64},
        "env_tag": "env-x", "ccbench_pin": "pin-x", "stock_configuration": "stock",
        "schedule_algorithm": floor.SCHEDULE_ALGORITHM, "master_seed": "seed",
        "n_sessions": 2, "reps": 3, "extime_s": 1,
        "session_cv_max": "0.10", "cell_cv_max": "0.15",
    }
    schedule = [
        {"seq": 0, "round": 1, "cell_id": "H1::stock"},
        {"seq": 1, "round": 1, "cell_id": "H1::sort_best"},
    ]
    manifest = floor.assemble_manifest(
        protocol=protocol, protocol_sha256="p" * 64, freeze_sha256="f" * 64,
        cells=cells, built=built, schedule=schedule)
    # _write_create_only_json と同一の serialize (indent=2, sort_keys, ensure_ascii=False)。
    payload = json.dumps(
        manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    actual_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert actual_sha256 == (
        "4b08f0cf4e1fdfc0448fc94ce09a4752e72ac13b7e3aecd502737368d134cd9b"
    ), actual_sha256


# --------------------------------------------------------------------------- #
# 境界変換: 共有 MaterializationError → consumer 固有例外 (from 付き, msg 一致)   #
# --------------------------------------------------------------------------- #

def test_oracle_boundary_converts_to_oracle_driver_error():
    from orchestrator.campaign import s8b_oracle_driver as driver

    def prepare_fn(cell, ccbench_pin, *, cxx):
        return {"not": "a prepared cell"}  # binding_from_prepared が拒否する

    with pytest.raises(driver.OracleDriverError) as excinfo:
        with driver._prepared_binding(
                freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
                ccbench_pin="pin-1", cxx="site-cxx",
                prepare_fn=prepare_fn):
            pass
    # reason 文字列は現行と一致 (WAL に載る), 因果は MaterializationError。
    assert str(excinfo.value) == "prepare_fn の戻り値が PreparedCell でない"
    assert isinstance(excinfo.value.__cause__, M.MaterializationError)


def test_floor_boundary_converts_to_floor_campaign_error():
    from orchestrator.campaign import s8b_floor_campaign as floor

    def prepare_fn(cell, ccbench_pin, *, cxx):
        return {"not": "a prepared cell"}

    with pytest.raises(floor.FloorCampaignError) as excinfo:
        with floor._prepared_binding(
                freeze=_FREEZE, holdout_id="H1", configuration_id="stock",
                ccbench_pin="pin-1", cxx="site-cxx",
                prepare_fn=prepare_fn):
            pass
    assert str(excinfo.value) == "prepare_fn の戻り値が PreparedCell でない"
    assert isinstance(excinfo.value.__cause__, M.MaterializationError)


# --------------------------------------------------------------------------- #
# G-9 cold-import smoke: floor 単独 / oracle 単独 / 両順序                       #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("imports", [
    ["orchestrator.campaign.s8b_floor_campaign"],
    ["orchestrator.campaign.s8b_oracle_driver"],
    [
        "orchestrator.campaign.s8b_floor_campaign",
        "orchestrator.campaign.s8b_oracle_driver",
    ],
    [
        "orchestrator.campaign.s8b_oracle_driver",
        "orchestrator.campaign.s8b_floor_campaign",
    ],
])
def test_cold_import_orders(imports):
    stmts = "; ".join(f"import {mod}" for mod in imports)
    script = f"import sys; sys.path.insert(0, {str(ORCHESTRATOR.parent)!r}); {stmts}"
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stdout, proc.stderr)
