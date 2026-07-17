# -*- coding: utf-8 -*-
"""``env_contract`` leaf の契約を高水準で固定する (Lane E, F4 裁定)。

方針:
- 検証拒否は fail-closed で ``EnvContractError`` を投げること (型・slug・正整数・hex64・bool)。
- lookup は登録済み tag のみ成功し、値は手書き golden で照合、未知 tag は拒否。
- 不変性: dataclass frozen (代入で FrozenInstanceError)、REGISTRY は MappingProxyType
  で代入・追加が TypeError。
- p2_2 整合: 歴史的定数を変えずに contract と値一致のみ検査 (γ-15)。
- calibration_ref 実在性: path のファイルが repo に実在し sha256 が一致 (γ-2、改竄防止)。
- contract_sha256: 手計算可能な小 contract で golden 固定 + field 変更で変わることを検証 (δ-12)。
- AST 検査 (γ-16): env 固有 literal は registry 静的定義部にのみ出現を許す。恒真回避のため、
  検査関数自体の単体テスト (positive control) と、免除が load-bearing である証明を置く。

env 固有 golden literal (linux-baremetal / 1800 / --interleave=all) はこの test 内に
手書きで置く。この test ファイルは V2_ENV_NEUTRAL_MODULES に含まれないので AST 検査の
対象外である (契約の golden 照合には env 値の手書きが必須)。
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))

REPO_ROOT = ORCHESTRATOR.parent

from campaign import env_contract as ec  # noqa: E402
from campaign import p2_2  # noqa: E402


# --------------------------------------------------------------------------- #
# AST 検査の設定 (test が所有する。恒真回避のため機構は env_contract 側)           #
# --------------------------------------------------------------------------- #

# 禁止する env 固有 literal。
ENV_LITERAL_VALUES = ("linux-baremetal", "--interleave=all", 1800)

# (repo 相対 module path, registry 静的定義部の FunctionDef 名 or None)。
# None のモジュールは免除なし = literal の一切の出現を禁止。S+C wave で
# s8b_floor_campaign.py を (path, None) として追加する拡張点。
V2_ENV_NEUTRAL_MODULES = [
    ("orchestrator/campaign/env_contract.py", "_build_registry"),
]


def _valid_contract(**overrides) -> ec.ExecutionEnvironmentContract:
    """検証を通る最小 contract を作るヘルパ。overrides で 1 field だけ差し替える。"""
    base = dict(
        env_tag="test-env",
        clocks_per_us=1000,
        numactl=("numactl", "--interleave=all"),
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
    assert c.isolation_policy == ec.IsolationPolicy(single_process=False, allow_resume=True)
    assert c.calibration_ref.path == (
        "output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json"
    )
    assert c.calibration_ref.sha256 == (
        "751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5"
    )


@pytest.mark.parametrize("unknown", ["pegasus", "linux-baremetal-x", "", "unknown"])
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
# calibration_ref 実在性 — γ-2 (改竄・自由文化の防止)                              #
# --------------------------------------------------------------------------- #

def test_calibration_ref_file_exists_and_hash_matches():
    c = ec.lookup("linux-baremetal")
    path = REPO_ROOT / c.calibration_ref.path
    assert path.is_file(), f"calibration file missing: {path}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == c.calibration_ref.sha256


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
        "env_tag", "clocks_per_us", "numactl", "isolation_policy", "calibration_ref",
    }


# --------------------------------------------------------------------------- #
# contract_sha256 — δ-12                                                        #
# --------------------------------------------------------------------------- #

def _reference_sha256(env_tag, clocks_per_us, numactl, single_process, allow_resume,
                      cal_path, cal_sha) -> str:
    """production を import しない stdlib-only reference calculator。
    canonical JSON を独立に組み立てて sha256 する。"""
    obj = {
        "env_tag": env_tag,
        "clocks_per_us": clocks_per_us,
        "numactl": list(numactl),
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
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(path="p", sha256="0" * 64),
    )
    expected_json = (
        '{"calibration_ref":{"path":"p","sha256":"' + "0" * 64 + '"},'
        '"clocks_per_us":1,"env_tag":"t",'
        '"isolation_policy":{"allow_resume":false,"single_process":true},'
        '"numactl":[]}'
    )
    expected = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
    # 手書き hex golden (別経路で凍結)。
    assert expected == "cbfbf008e7d81403c615b9d1d9af341f6c4e211e69c6fa00ac84052caa5cf31d"
    assert c.contract_sha256 == expected


def test_contract_sha256_matches_independent_reference():
    c = ec.lookup("linux-baremetal")
    ref = _reference_sha256(
        env_tag="linux-baremetal",
        clocks_per_us=1800,
        numactl=("numactl", "--interleave=all"),
        single_process=False,
        allow_resume=True,
        cal_path="output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json",
        cal_sha="751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5",
    )
    assert c.contract_sha256 == ref


@pytest.mark.parametrize("overrides", [
    {"env_tag": "other-env"},
    {"clocks_per_us": 2000},
    {"numactl": ("numactl",)},
    {"numactl": ()},
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
