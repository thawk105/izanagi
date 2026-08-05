# -*- coding: utf-8 -*-
"""``env_contract`` leaf の契約を高水準で固定する (Lane E, F4 裁定)。

方針:
- 検証拒否は fail-closed で ``EnvContractError`` を投げること (型・slug・正整数・hex64・bool)。
- lookup は登録済み tag のみ成功し、値は手書き golden で照合、未知 tag は拒否。
- 不変性: dataclass frozen (代入で FrozenInstanceError)、REGISTRY は MappingProxyType
  で代入・追加が TypeError。
- p2_2 整合: 歴史的定数を変えずに contract と値一致のみ検査 (γ-15)。
- calibration_ref admission: 全 registry entry の canonical path・実在・sha256・artifact 意味を検証。
- contract_sha256: 手計算可能な小 contract で golden 固定 + field 変更で変わることを検証 (δ-12)。
- AST 検査 (γ-16): env 固有 literal は registry 静的定義部にのみ出現を許す。恒真回避のため、
  検査関数自体の単体テスト (positive control) と、免除が load-bearing である証明を置く。

env 固有 golden literal (linux-baremetal / pegasus 等) はこの test 内に
手書きで置く。この test ファイルは V2_ENV_NEUTRAL_MODULES に含まれないので AST 検査の
対象外である (契約の golden 照合には env 値の手書きが必須)。
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import pathlib
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))

REPO_ROOT = ORCHESTRATOR.parent

from campaign import env_attestation as ea  # noqa: E402
from campaign import env_contract as ec  # noqa: E402
from campaign import execution_guard as eg  # noqa: E402
from campaign import p2_2  # noqa: E402
from calibrator import effective_clock_policy  # noqa: E402


# --------------------------------------------------------------------------- #
# AST 検査の設定 (test が所有する。恒真回避のため機構は env_contract 側)           #
# --------------------------------------------------------------------------- #

# 禁止する env 固有 literal。
ENV_LITERAL_VALUES = (
    "linux-baremetal", "pegasus", "--interleave=all", "/scr", 1800, 2100,
)

LEGACY_CALIBRATION_ALLOWLIST = {
    "linux-baremetal": (
        "output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json",
        "751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5",
    ),
}

KNOWN_SELF_INCONSISTENT_CALIBRATIONS = {
    (
        "output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json",
        "753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49",
    ),
}

# (repo 相対 module path, registry 静的定義部の FunctionDef 名 or None)。
# None のモジュールは免除なし = literal の一切の出現を禁止。s8b_floor_campaign.py は env 契約を
# lookup 経由でのみ参照し env 固有 literal を持たないので region=None (免除なし) で検査する
# (S+C wave, γ-16)。免除でなく literal の除去で解消する。
V2_ENV_NEUTRAL_MODULES = [
    ("orchestrator/campaign/env_contract.py", "_build_registry"),
    ("orchestrator/campaign/execution_guard.py", None),
    ("orchestrator/campaign/env_attestation.py", None),
    ("orchestrator/campaign/reservation.py", None),
    ("orchestrator/campaign/durable_root.py", None),
    ("orchestrator/campaign/campaign_claim.py", None),
    ("orchestrator/campaign/buildcache.py", None),
    ("orchestrator/campaign/layout.py", None),
    ("orchestrator/campaign/s8b_oracle_driver.py", None),
    ("orchestrator/calibrator/schema_v2.py", None),
    ("orchestrator/calibrator/effective_clock_policy.py", None),
    ("orchestrator/calibrator/cli.py", None),
    ("orchestrator/calibrator/sweep.py", None),
    ("orchestrator/campaign/s8b_floor_campaign.py", None),
]

# 2100 は Pegasus の登録クロックである一方、既存 calibrator の CCBench generic fallback 値でもある。
# env 中立な後者だけを「関数・値・出現数」まで絞って免除する。他の禁止値は同関数内でも免除しない。
ENV_NEUTRAL_LITERAL_EXEMPTIONS = {
    "orchestrator/calibrator/sweep.py": ("_apply_clocks_fallback", 2100, 2),
}


def _valid_contract(**overrides) -> ec.ExecutionEnvironmentContract:
    """検証を通る最小 contract を作るヘルパ。overrides で 1 field だけ差し替える。"""
    base = dict(
        env_tag="test-env",
        clocks_per_us=1000,
        numactl=("numactl", "--interleave=all"),
        attestation_mode="none",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(path="output/x.json", sha256="0" * 64),
    )
    base.update(overrides)
    return ec.ExecutionEnvironmentContract(**base)


# --------------------------------------------------------------------------- #
# 検証拒否系 (fail-closed)                                                       #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bad_tag", [
    "Linux-Baremetal",   # 大文字
    "-leading-dash",     # 先頭記号
    ".leading-dot",      # 先頭ドット
    "has space",         # 空白
    "under_score/slash", # スラッシュ
    "",                  # 空
    "日本語",            # 非 ASCII
])
def test_rejects_invalid_slug(bad_tag):
    with pytest.raises(ec.EnvContractError):
        _valid_contract(env_tag=bad_tag)


def test_rejects_non_str_env_tag():
    with pytest.raises(ec.EnvContractError):
        _valid_contract(env_tag=123)


@pytest.mark.parametrize("bad_clk", [0, -1, -1800])
def test_rejects_nonpositive_clocks(bad_clk):
    with pytest.raises(ec.EnvContractError):
        _valid_contract(clocks_per_us=bad_clk)


@pytest.mark.parametrize("bad_clk", [1800.0, "1800", True, False])
def test_rejects_non_int_clocks(bad_clk):
    # bool は int のサブクラスだが正整数として受理してはいけない。
    with pytest.raises(ec.EnvContractError):
        _valid_contract(clocks_per_us=bad_clk)


@pytest.mark.parametrize("bad_numa", [
    None,                        # 未解決を型で禁止
    ["numactl"],                 # list は不可 (tuple のみ)
    "numactl",                   # str
    ("numactl", 5),              # 非 str 要素
    ("numactl", None),           # None 要素
])
def test_rejects_bad_numactl(bad_numa):
    with pytest.raises(ec.EnvContractError):
        _valid_contract(numactl=bad_numa)


def test_accepts_empty_numactl_tuple():
    # 空 tuple = 「解決済みで launch prefix なし」は正当 (None と区別)。
    c = _valid_contract(numactl=())
    assert c.numactl == ()


@pytest.mark.parametrize("bad_mode", [None, True, False, 0, "", "optional", "Required"])
def test_rejects_bad_attestation_mode(bad_mode):
    with pytest.raises(ec.EnvContractError):
        _valid_contract(attestation_mode=bad_mode)


@pytest.mark.parametrize("mode", ["none", "required"])
def test_accepts_exact_attestation_modes(mode):
    assert _valid_contract(attestation_mode=mode).attestation_mode == mode


def test_required_attestation_rejects_non_single_process():
    with pytest.raises(ec.EnvContractError, match="single_process=True"):
        _valid_contract(
            attestation_mode="required",
            isolation_policy=ec.IsolationPolicy(single_process=False, allow_resume=False),
        )


@pytest.mark.parametrize("bad_hex", [
    "0" * 63,           # 短い
    "0" * 65,           # 長い
    "g" * 64,           # 非 hex 文字
    "A" * 64,           # 大文字 hex
    "0" * 64 + " ",     # 末尾空白
    123,                # 非 str
])
def test_rejects_bad_calibration_sha256(bad_hex):
    with pytest.raises(ec.EnvContractError):
        ec.CalibrationRef(path="output/x.json", sha256=bad_hex)


@pytest.mark.parametrize("bad_path", ["", 123, None])
def test_rejects_bad_calibration_path(bad_path):
    with pytest.raises(ec.EnvContractError):
        ec.CalibrationRef(path=bad_path, sha256="0" * 64)


@pytest.mark.parametrize("field,bad", [
    ("single_process", 1),
    ("single_process", "true"),
    ("single_process", None),
    ("allow_resume", 0),
    ("allow_resume", "false"),
])
def test_rejects_non_bool_isolation(field, bad):
    kw = dict(single_process=True, allow_resume=False)
    kw[field] = bad
    with pytest.raises(ec.EnvContractError):
        ec.IsolationPolicy(**kw)


def test_rejects_wrong_nested_types():
    with pytest.raises(ec.EnvContractError):
        _valid_contract(isolation_policy={"single_process": True, "allow_resume": False})
    with pytest.raises(ec.EnvContractError):
        _valid_contract(calibration_ref={"path": "output/x.json", "sha256": "0" * 64})


# --------------------------------------------------------------------------- #
# lookup + 値 golden                                                            #
# --------------------------------------------------------------------------- #

def test_lookup_baremetal_golden():
    c = ec.lookup("linux-baremetal")
    # 手書き golden (実装出力の貼り付けではない)。
    assert c.env_tag == "linux-baremetal"
    assert c.clocks_per_us == 1800
    assert c.numactl == ("numactl", "--interleave=all")
    assert c.attestation_mode == "none"
    assert c.isolation_policy == ec.IsolationPolicy(single_process=False, allow_resume=True)
    assert c.calibration_ref.path == (
        "output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json"
    )
    assert c.calibration_ref.sha256 == (
        "751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5"
    )


def test_lookup_pegasus_golden():
    c = ec.lookup("pegasus")
    assert c.env_tag == "pegasus"
    assert c.clocks_per_us == 2100
    assert c.numactl == ()
    assert c.attestation_mode == "required"
    assert c.isolation_policy == ec.IsolationPolicy(single_process=True, allow_resume=False)
    assert c.calibration_ref.path == (
        "output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json"
    )
    assert c.calibration_ref.sha256 == (
        "753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49"
    )


@pytest.mark.parametrize("unknown", ["unregistered-env", "linux-baremetal-x", "", "unknown"])
def test_lookup_unknown_fails_closed(unknown):
    with pytest.raises(ec.EnvContractError):
        ec.lookup(unknown)


def test_lookup_non_str_fails_closed():
    with pytest.raises(ec.EnvContractError):
        ec.lookup(None)


# --------------------------------------------------------------------------- #
# 不変性                                                                         #
# --------------------------------------------------------------------------- #

def test_contract_is_frozen():
    c = ec.lookup("linux-baremetal")
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.clocks_per_us = 2100  # type: ignore[misc]


def test_nested_dataclasses_frozen():
    c = ec.lookup("linux-baremetal")
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.isolation_policy.allow_resume = False  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.calibration_ref.sha256 = "1" * 64  # type: ignore[misc]


def test_registry_is_read_only_mapping_proxy():
    from types import MappingProxyType
    assert isinstance(ec.REGISTRY, MappingProxyType)
    with pytest.raises(TypeError):
        ec.REGISTRY["pegasus"] = ec.lookup("linux-baremetal")  # type: ignore[index]
    with pytest.raises(TypeError):
        del ec.REGISTRY["linux-baremetal"]  # type: ignore[misc]


def test_no_register_api():
    # register API は存在しない (静的定義のみ)。
    assert not hasattr(ec, "register")
    assert not hasattr(ec, "register_contract")


def test_no_mutable_backing_dict_exposed():
    # MappingProxyType の裏側 dict が module 属性として露出すると
    # ec._REGISTRY[...] = ... の注入経路が開く (レビュー所見 R1-1)。
    # module 名前空間に生 dict の registry を束縛しないことを機械固定する。
    for name, value in vars(ec).items():
        if type(value) is dict and any(
            isinstance(v, ec.ExecutionEnvironmentContract) for v in value.values()
        ):
            raise AssertionError(f"生 dict の registry が露出している: {name}")


def test_forbidden_literals_cover_all_registry_values():
    # ENV_LITERAL_VALUES は registry と手動同期のため、entry 追加時の更新漏れで
    # 新 env の値が AST 検査を素通りする (レビュー所見 R2-3)。全 contract の
    # env 固有値が禁止集合に含まれることを機械 assert して同期を強制する。
    forbidden = set(ENV_LITERAL_VALUES)
    for tag, c in ec.REGISTRY.items():
        assert c.env_tag in forbidden, f"env_tag {c.env_tag!r} が ENV_LITERAL_VALUES にない"
        assert c.clocks_per_us in forbidden, (
            f"clocks_per_us {c.clocks_per_us!r} が ENV_LITERAL_VALUES にない"
        )
        for part in c.numactl:
            if part.startswith("--"):
                assert part in forbidden, f"numactl 引数 {part!r} が ENV_LITERAL_VALUES にない"


# --------------------------------------------------------------------------- #
# p2_2 整合 (値一致のみ、p2_2 は不変) — γ-15                                      #
# --------------------------------------------------------------------------- #

def test_matches_p2_2_constants():
    c = ec.lookup("linux-baremetal")
    assert c.env_tag == p2_2.ENV_TAG
    assert c.clocks_per_us == p2_2.CLK
    assert tuple(p2_2.NUMA) == c.numactl


# --------------------------------------------------------------------------- #
# calibration_ref admission — C3-8 / γ-2 (canonical path・改竄・意味検証)          #
# --------------------------------------------------------------------------- #

def _canonical_calibration_path(
        registry_key: str,
        contract: ec.ExecutionEnvironmentContract,
        repo_root: Path,
) -> Path:
    """登録 path が canonical repo-relative path で symlink を含まないことを固定する。"""
    relative = pathlib.PurePosixPath(contract.calibration_ref.path)
    assert not relative.is_absolute(), "calibration_ref.path must be repository-relative"
    assert relative.as_posix() == contract.calibration_ref.path, (
        "calibration_ref.path must use canonical POSIX spelling"
    )
    assert "." not in relative.parts and ".." not in relative.parts, (
        "calibration_ref.path must not contain dot or parent traversal"
    )
    expected_parent = pathlib.PurePosixPath(
        "output", "env", registry_key, "calibration",
    )
    try:
        relative.relative_to(expected_parent)
    except ValueError as exc:
        raise AssertionError(
            f"calibration_ref.path must be below {expected_parent.as_posix()}/"
        ) from exc

    root = repo_root.resolve(strict=True)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        assert not cursor.is_symlink(), f"calibration path contains symlink: {cursor}"
    resolved = (root / Path(*relative.parts)).resolve(strict=True)
    resolved.relative_to(root)
    resolved.relative_to((root / Path(*expected_parent.parts)).resolve(strict=True))
    assert resolved.is_file(), f"calibration file missing: {resolved}"
    return resolved


def _assert_pegasus_artifact_semantics(
        registry_key: str,
        contract: ec.ExecutionEnvironmentContract,
        artifact: dict,
) -> None:
    """W5 で凍結した Pegasus artifact の各意味核を独立に検査する。"""
    assert artifact.get("env_tag") == registry_key
    assert registry_key == contract.env_tag
    assert artifact.get("clocks_per_us") == contract.clocks_per_us
    assert artifact.get("schema_version") == "calibration/v2"
    assert artifact.get("threads") == 48
    workload = artifact.get("workload")
    assert type(workload) is dict
    assert workload.get("ycsb_zipf_skew") == "0.9"
    assert workload.get("ycsb_rratio") == "50"
    assert workload.get("ycsb_rmw") == "0"
    quality = artifact.get("quality")
    assert type(quality) is dict and quality.get("status") == "accepted"
    assert type(artifact.get("attestation_profile")) is dict
    assert type(artifact.get("acquisition_receipt")) is dict
    noise_floor = artifact.get("noise_floor")
    assert type(noise_floor) is dict and noise_floor.get("kind") == "within-run"


def _assert_registry_calibration(
        registry_key: str,
        contract: ec.ExecutionEnvironmentContract,
        repo_root: Path = REPO_ROOT,
) -> None:
    path = _canonical_calibration_path(registry_key, contract, repo_root)
    raw = path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    assert actual_sha == contract.calibration_ref.sha256, (
        f"calibration sha256 mismatch for {registry_key}: {actual_sha}"
    )
    artifact = json.loads(raw)
    assert type(artifact) is dict

    if registry_key in LEGACY_CALIBRATION_ALLOWLIST:
        assert contract.attestation_mode == "none"
        assert (contract.calibration_ref.path, contract.calibration_ref.sha256) == (
            LEGACY_CALIBRATION_ALLOWLIST[registry_key]
        )
        verified = ea.load_verified_calibration(contract, repo_root)
        assert verified.schema_version == "calibration/v1"
        return

    assert contract.attestation_mode == "required"
    _assert_pegasus_artifact_semantics(registry_key, contract, artifact)
    verified = ea.load_verified_calibration(contract, repo_root)
    assert verified.schema_version == "calibration/v2"
    assert verified.calibration is not None
    assert verified.calibration.attestation_profile is not None
    assert verified.calibration.acquisition_receipt is not None


def test_registry_calibration_refs_are_canonical_hash_bound_and_meaningful():
    for registry_key, contract in ec.REGISTRY.items():
        _assert_registry_calibration(registry_key, contract)


def _registry_clock_self_passes(profile) -> bool:
    expected = ea.expected_comparison_values(profile)["effective_clock.samples_mhz"]
    observed = {"samples_mhz": list(expected["samples_mhz"])}
    return eg.effective_clock_comparison_passes(expected, observed)


def test_registry_effective_clock_self_failures_are_exact_known_exception():
    """この既知例外は [T-419] の U-1/U-2 が閉じたときに削除する。"""
    assert len(KNOWN_SELF_INCONSISTENT_CALIBRATIONS) == 1
    self_failures = set()
    checked_entries = 0
    required_entries = 0

    for registry_key, contract in ec.REGISTRY.items():
        checked_entries += 1
        verified = ea.load_verified_calibration(contract, REPO_ROOT)
        if contract.attestation_mode == "none":
            assert verified.schema_version == "calibration/v1"
            assert verified.calibration is None
            continue

        assert contract.attestation_mode == "required"
        required_entries += 1
        assert verified.calibration is not None
        profile = verified.calibration.attestation_profile
        assert (profile.effective_clock.tolerance_pct
                == effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT)
        ref = (contract.calibration_ref.path, contract.calibration_ref.sha256)
        passes = _registry_clock_self_passes(profile)
        if not passes:
            self_failures.add(ref)
        if ref not in KNOWN_SELF_INCONSISTENT_CALIBRATIONS:
            assert passes, f"new self-inconsistent calibration: {registry_key} {ref}"

    assert checked_entries == 2
    assert required_entries == 1
    assert self_failures == KNOWN_SELF_INCONSISTENT_CALIBRATIONS

    base = ea.load_verified_calibration(ec.lookup("pegasus"), REPO_ROOT)
    assert base.calibration is not None
    synthetic = dataclasses.replace(
        base.calibration.attestation_profile,
        effective_clock=dataclasses.replace(
            base.calibration.attestation_profile.effective_clock,
            samples_mhz=[2101.0] * 47 + [3080.0],
            tolerance_pct=2.0,
        ),
    )
    assert not _registry_clock_self_passes(synthetic)


def test_registry_policy_equality_rejects_near_and_rounded_values():
    assert len(KNOWN_SELF_INCONSISTENT_CALIBRATIONS) == 1
    verified = ea.load_verified_calibration(ec.lookup("pegasus"), REPO_ROOT)
    assert verified.calibration is not None
    profile = verified.calibration.attestation_profile
    for tolerance in (
        math.nextafter(2.0, math.inf),
        math.nextafter(2.0, -math.inf),
        2.5,
        2.9,
    ):
        mutated = dataclasses.replace(
            profile,
            effective_clock=dataclasses.replace(
                profile.effective_clock, tolerance_pct=tolerance,
            ),
        )
        assert not _registry_clock_self_passes(mutated)


def test_legacy_calibration_allowlist_is_exact_and_closed():
    actual = {
        tag: (contract.calibration_ref.path, contract.calibration_ref.sha256)
        for tag, contract in ec.REGISTRY.items()
        if contract.attestation_mode == "none"
    }
    assert actual == LEGACY_CALIBRATION_ALLOWLIST
    for tag, contract in ec.REGISTRY.items():
        verified = ea.load_verified_calibration(contract, REPO_ROOT)
        if tag in LEGACY_CALIBRATION_ALLOWLIST:
            assert verified.schema_version == "calibration/v1"
        else:
            assert contract.attestation_mode == "required"
            assert verified.schema_version == "calibration/v2"


def _copy_pegasus_artifact(
        tmp_path: Path,
        raw: bytes,
        *,
        bound_sha256: str | None = None,
) -> ec.ExecutionEnvironmentContract:
    relative = Path(
        "output/env/pegasus/calibration/registered/calibration-copy.json"
    )
    destination = tmp_path / relative
    destination.parent.mkdir(parents=True)
    destination.write_bytes(raw)
    return dataclasses.replace(
        ec.lookup("pegasus"),
        calibration_ref=ec.CalibrationRef(
            path=relative.as_posix(),
            sha256=(bound_sha256 if bound_sha256 is not None
                    else hashlib.sha256(raw).hexdigest()),
        ),
    )


@pytest.mark.parametrize("mutation", [
    "env-tag", "clocks", "schema", "threads", "workload-skew",
    "workload-rratio", "workload-rmw", "quality", "attestation-profile",
    "acquisition-receipt", "noise-kind",
])
def test_pegasus_semantic_core_mutations_are_rejected(tmp_path, mutation):
    source = REPO_ROOT / ec.lookup("pegasus").calibration_ref.path
    artifact = json.loads(source.read_bytes())
    if mutation == "env-tag":
        artifact["env_tag"] = "wrong-env"
    elif mutation == "clocks":
        artifact["clocks_per_us"] = 2101
    elif mutation == "schema":
        artifact["schema_version"] = "calibration/v1"
    elif mutation == "threads":
        artifact["threads"] = 47
    elif mutation == "workload-skew":
        artifact["workload"]["ycsb_zipf_skew"] = "0.8"
    elif mutation == "workload-rratio":
        artifact["workload"]["ycsb_rratio"] = "49"
    elif mutation == "workload-rmw":
        artifact["workload"]["ycsb_rmw"] = "1"
    elif mutation == "quality":
        artifact["quality"] = {"status": "rejected", "reasons": ["mutation"]}
    elif mutation == "attestation-profile":
        del artifact["attestation_profile"]
    elif mutation == "acquisition-receipt":
        del artifact["acquisition_receipt"]
    elif mutation == "noise-kind":
        artifact["noise_floor"]["kind"] = "between-run"
    raw = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    contract = _copy_pegasus_artifact(tmp_path, raw)
    copied = json.loads((tmp_path / contract.calibration_ref.path).read_bytes())
    with pytest.raises(AssertionError):
        _assert_pegasus_artifact_semantics("pegasus", contract, copied)


@pytest.mark.parametrize("mutation", ["wrong-env-hash-copy", "missing-attestation"])
def test_pegasus_hash_bound_semantic_copies_are_rejected(tmp_path, mutation):
    source = REPO_ROOT / ec.lookup("pegasus").calibration_ref.path
    artifact = json.loads(source.read_bytes())
    if mutation == "wrong-env-hash-copy":
        artifact["env_tag"] = "wrong-env"
    else:
        del artifact["attestation_profile"]
    raw = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    contract = _copy_pegasus_artifact(tmp_path, raw)
    with pytest.raises((AssertionError, ea.AttestationError)):
        _assert_registry_calibration("pegasus", contract, tmp_path)


def test_pegasus_one_byte_mutation_is_rejected(tmp_path):
    base = ec.lookup("pegasus")
    source = REPO_ROOT / base.calibration_ref.path
    mutated = source.read_bytes() + b"\n"
    contract = _copy_pegasus_artifact(
        tmp_path, mutated, bound_sha256=base.calibration_ref.sha256,
    )
    with pytest.raises(AssertionError, match="sha256 mismatch"):
        _assert_registry_calibration("pegasus", contract, tmp_path)


@pytest.mark.parametrize("bad_path", [
    "/absolute/calibration.json",
    "output/env/pegasus/calibration/../escape.json",
    "output/env/wrong-env/calibration/artifact.json",
    "output//env/pegasus/calibration/artifact.json",
])
def test_calibration_path_canonical_checks_reject_bad_spellings(tmp_path, bad_path):
    contract = dataclasses.replace(
        ec.lookup("pegasus"),
        calibration_ref=ec.CalibrationRef(path=bad_path, sha256="0" * 64),
    )
    with pytest.raises(AssertionError):
        _canonical_calibration_path("pegasus", contract, tmp_path)


def test_calibration_path_rejects_symlink_escape(tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    relative = Path("output/env/pegasus/calibration/linked.json")
    linked = tmp_path / relative
    linked.parent.mkdir(parents=True)
    linked.symlink_to(outside)
    contract = dataclasses.replace(
        ec.lookup("pegasus"),
        calibration_ref=ec.CalibrationRef(
            path=relative.as_posix(), sha256=hashlib.sha256(b"{}").hexdigest(),
        ),
    )
    with pytest.raises(AssertionError, match="symlink"):
        _canonical_calibration_path("pegasus", contract, tmp_path)


def test_calibration_ref_has_no_free_text_note():
    # note のような自由文 field を後から生やしていないこと (γ-2)。
    field_names = {f.name for f in dataclasses.fields(ec.CalibrationRef)}
    assert field_names == {"path", "sha256"}


def test_contract_has_no_records_or_threads():
    # 契約は freeze holdout の座標 (records/threads) を持たない (δ-13)。
    field_names = {f.name for f in dataclasses.fields(ec.ExecutionEnvironmentContract)}
    assert "records" not in field_names
    assert "threads" not in field_names
    assert field_names == {
        "env_tag", "clocks_per_us", "numactl", "attestation_mode",
        "isolation_policy", "calibration_ref",
    }


# --------------------------------------------------------------------------- #
# contract_sha256 — δ-12                                                        #
# --------------------------------------------------------------------------- #

def _reference_sha256(env_tag, clocks_per_us, numactl, attestation_mode,
                      single_process, allow_resume,
                      cal_path, cal_sha) -> str:
    """production を import しない stdlib-only reference calculator。
    canonical JSON を独立に組み立てて sha256 する。"""
    obj = {
        "env_tag": env_tag,
        "clocks_per_us": clocks_per_us,
        "numactl": list(numactl),
        "attestation_mode": attestation_mode,
        "isolation_policy": {
            "single_process": single_process,
            "allow_resume": allow_resume,
        },
        "calibration_ref": {"path": cal_path, "sha256": cal_sha},
    }
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def test_contract_sha256_small_golden():
    # 手計算可能な小 contract。canonical JSON string まで手書きで固定する。
    c = ec.ExecutionEnvironmentContract(
        env_tag="t",
        clocks_per_us=1,
        numactl=(),
        attestation_mode="none",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(path="p", sha256="0" * 64),
    )
    expected_json = (
        '{"attestation_mode":"none",'
        '"calibration_ref":{"path":"p","sha256":"' + "0" * 64 + '"},'
        '"clocks_per_us":1,"env_tag":"t",'
        '"isolation_policy":{"allow_resume":false,"single_process":true},'
        '"numactl":[]}'
    )
    expected = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
    # 手書き hex golden (別経路で凍結)。
    assert expected == "e278d9dd18258b89a6590ed29c29e999d516c862cd2544b1416741b9e71aaf24"
    assert c.contract_sha256 == expected


def test_contract_sha256_matches_independent_reference():
    c = ec.lookup("linux-baremetal")
    ref = _reference_sha256(
        env_tag="linux-baremetal",
        clocks_per_us=1800,
        numactl=("numactl", "--interleave=all"),
        attestation_mode="none",
        single_process=False,
        allow_resume=True,
        cal_path="output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json",
        cal_sha="751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5",
    )
    assert ref == "1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7"
    assert c.contract_sha256 == ref


def test_pegasus_contract_sha256_golden():
    c = ec.lookup("pegasus")
    ref = _reference_sha256(
        env_tag="pegasus",
        clocks_per_us=2100,
        numactl=(),
        attestation_mode="required",
        single_process=True,
        allow_resume=False,
        cal_path="output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json",
        cal_sha="753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49",
    )
    assert ref == "e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01"
    assert c.contract_sha256 == ref


@pytest.mark.parametrize("overrides", [
    {"env_tag": "other-env"},
    {"clocks_per_us": 2000},
    {"numactl": ("numactl",)},
    {"numactl": ()},
    {"attestation_mode": "required"},
    {"isolation_policy": None},   # replaced below with valid variant
    {"calibration_ref": None},    # replaced below
])
def test_contract_sha256_changes_when_field_changes(overrides):
    base = _valid_contract()
    if overrides.get("isolation_policy", "keep") is None:
        overrides = {"isolation_policy": ec.IsolationPolicy(single_process=False, allow_resume=False)}
    if overrides.get("calibration_ref", "keep") is None:
        overrides = {"calibration_ref": ec.CalibrationRef(path="output/y.json", sha256="1" * 64)}
    mutated = _valid_contract(**overrides)
    assert base.contract_sha256 != mutated.contract_sha256


def test_contract_sha256_stable_and_hex64():
    c = ec.lookup("linux-baremetal")
    s1 = c.contract_sha256
    s2 = c.contract_sha256
    assert s1 == s2
    assert len(s1) == 64 and all(ch in "0123456789abcdef" for ch in s1)


# --------------------------------------------------------------------------- #
# AST 検査 (γ-16) — 恒真回避                                                     #
# --------------------------------------------------------------------------- #

def _read_module(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_v2_modules_have_no_env_literals_outside_registry():
    """各 v2 中立モジュールで、env 固有 literal が registry 静的定義部の外に現れないこと。"""
    for rel_path, region in V2_ENV_NEUTRAL_MODULES:
        source = _read_module(rel_path)
        exemption = ENV_NEUTRAL_LITERAL_EXEMPTIONS.get(rel_path)
        if exemption is not None:
            exempt_region, exempt_value, expected_count = exemption
            non_exempt_values = set(ENV_LITERAL_VALUES) - {exempt_value}
            assert ec.find_env_literals(source, non_exempt_values, region) == []
            assert ec.find_env_literals(source, (exempt_value,), exempt_region) == []
            assert len(ec.find_env_literals(source, (exempt_value,), None)) == expected_count
            continue
        hits = ec.find_env_literals(source, ENV_LITERAL_VALUES, region)
        assert hits == [], f"{rel_path}: env literal outside allowed region: {hits}"


def test_ast_check_is_not_vacuous_env_contract_has_literals():
    """恒真でない証明: env_contract.py も免除なし (region=None) で検査すれば literal を検出する。
    免除 (registry 定義部) が load-bearing であることを示す。"""
    source = _read_module("orchestrator/campaign/env_contract.py")
    no_exempt = ec.find_env_literals(source, ENV_LITERAL_VALUES, None)
    assert no_exempt, "免除なしでも literal を検出できないなら検査は恒真"
    # 免除ありでは空になる (registry 定義部にしか無い)。
    exempt = ec.find_env_literals(source, ENV_LITERAL_VALUES, "_build_registry")
    assert exempt == []


def test_find_env_literals_positive_control_outside_region():
    """検査関数の単体 positive control: 免除領域の外に literal がある合成 source で発火する。"""
    src = (
        "def unrelated():\n"
        "    x = 'linux-baremetal'\n"
        "    y = 1800\n"
        "    z = '--interleave=all'\n"
        "    return x, y, z\n"
        "def _build_registry():\n"
        "    return {}\n"
    )
    hits = ec.find_env_literals(src, ENV_LITERAL_VALUES, "_build_registry")
    values = sorted(str(v) for v, _ in hits)
    assert values == ["--interleave=all", "1800", "linux-baremetal"]


def test_find_env_literals_positive_control_inside_region_is_exempt():
    """同じ literal が免除領域 (_build_registry) の内側にあれば発火しない。"""
    src = (
        "def _build_registry():\n"
        "    return {'linux-baremetal': (1800, '--interleave=all')}\n"
    )
    assert ec.find_env_literals(src, ENV_LITERAL_VALUES, "_build_registry") == []
    # region 指定なしなら同じ literal を検出する (免除が効いていることの対照)。
    assert ec.find_env_literals(src, ENV_LITERAL_VALUES, None)


def test_find_env_literals_ignores_bool_lookalikes():
    """bool は int サブクラスだが env literal 対象外 (1800 と誤照合しない)。"""
    src = "flag = True\nother = False\n"
    assert ec.find_env_literals(src, (True, 1800), None) == []
