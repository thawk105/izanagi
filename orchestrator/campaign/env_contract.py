# -*- coding: utf-8 -*-
"""実行環境契約 (F4 裁定) — 計測環境の同一性を型で凍結する中立 leaf。

このモジュールは stdlib のみ・campaign 内 import なしの葉である。env_tag 等価比較
(cygnus 固有値のハードコード) を、registry の fail-closed lookup へ置き換えるための
契約 dataclass と静的 registry を提供する。**このモジュールは何も強制しない宣言
field を持たない** (γ-3): 契約は「registry に登録された env の canonical な値集合」を
表現し、実環境 attestation・WAL root 検査・walltime 予約などの強制は driver / 登録段の
責務である。

契約が持たないもの (意図的):
- records / threads — freeze holdout が所有する動作点。契約はこれを上書きしない (δ-13)
- 自由文 note — calibration 参照は {path, sha256} の構造化参照のみ (γ-2)
- wal_root_policy / capture 列挙 — 宣言だけで発火しない恒真 field は置かない (γ-3)

registry は private dict を ``MappingProxyType`` で公開するのみで register API を持たない
(γ-13)。静的定義以外から env を注入する経路はない。
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Tuple

# env 固有 literal はこのモジュールでは ``_build_registry`` の内部にのみ現れる。
# その他の場所 (lookup / validation / property) は env 中立でなければならず、
# test_env_contract.py の AST 検査がこの不変条件を機械的に固定する (γ-16)。

_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")


class EnvContractError(ValueError):
    """契約検証・lookup の fail-closed 失敗。"""


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise EnvContractError(f"{name} は bool でなければならない: {value!r}")
    return value


@dataclass(frozen=True)
class IsolationPolicy:
    """計測 process の単独性ポリシ (γ-5)。

    single_process: campaign を単一 process で完遂する要件か。
    allow_resume: 別 process からの --resume を許すか (Pegasus 登録段では False)。
    """

    single_process: bool
    allow_resume: bool

    def __post_init__(self) -> None:
        _require_bool("single_process", self.single_process)
        _require_bool("allow_resume", self.allow_resume)


@dataclass(frozen=True)
class CalibrationRef:
    """calibration 成果物への構造化参照 (γ-2)。自由文 note は持たない。

    path: repo root からの相対 path。sha256: その byte 列の 64 hex。
    """

    path: str
    sha256: str

    def __post_init__(self) -> None:
        if type(self.path) is not str or not self.path:
            raise EnvContractError(f"calibration_ref.path は非空 str でなければならない: {self.path!r}")
        if type(self.sha256) is not str or _HEX64_RE.fullmatch(self.sha256) is None:
            raise EnvContractError(
                f"calibration_ref.sha256 は 64 桁の小文字 hex でなければならない: {self.sha256!r}"
            )


@dataclass(frozen=True)
class ExecutionEnvironmentContract:
    """registry に登録された 1 env の canonical な値集合。dataclass 自身が同一性の正本。

    fields:
      env_tag: str (slug ``[a-z0-9][a-z0-9._-]*``)
      clocks_per_us: int (正整数)
      numactl: tuple[str, ...] — 空 tuple = 「解決済みで launch prefix なし」として正当。
               None は不可 (未解決と解決済み空を型で区別する)
      attestation_mode: ``none`` | ``required``。required = 実行直前にハード仕様
               attestation が必須 (Pegasus 登録段、runbook §7)。
      isolation_policy: IsolationPolicy
      calibration_ref: CalibrationRef
    """

    env_tag: str
    clocks_per_us: int
    numactl: Tuple[str, ...]
    attestation_mode: str
    isolation_policy: IsolationPolicy
    calibration_ref: CalibrationRef

    def __post_init__(self) -> None:
        if type(self.env_tag) is not str or _SLUG_RE.fullmatch(self.env_tag) is None:
            raise EnvContractError(
                f"env_tag は slug [a-z0-9][a-z0-9._-]* でなければならない: {self.env_tag!r}"
            )
        if type(self.clocks_per_us) is not int or self.clocks_per_us <= 0:
            # type(...) is not int で bool を弾く (True は int のサブクラス)。
            raise EnvContractError(
                f"clocks_per_us は正整数でなければならない: {self.clocks_per_us!r}"
            )
        if type(self.numactl) is not tuple:
            raise EnvContractError(
                f"numactl は tuple でなければならない (None/list 不可): {self.numactl!r}"
            )
        for i, part in enumerate(self.numactl):
            if type(part) is not str:
                raise EnvContractError(
                    f"numactl[{i}] は str でなければならない: {part!r}"
                )
        if type(self.attestation_mode) is not str or self.attestation_mode not in {
            "none", "required",
        }:
            raise EnvContractError(
                "attestation_mode は 'none' または 'required' でなければならない: "
                f"{self.attestation_mode!r}"
            )
        if not isinstance(self.isolation_policy, IsolationPolicy):
            raise EnvContractError(
                f"isolation_policy は IsolationPolicy でなければならない: {self.isolation_policy!r}"
            )
        if not isinstance(self.calibration_ref, CalibrationRef):
            raise EnvContractError(
                f"calibration_ref は CalibrationRef でなければならない: {self.calibration_ref!r}"
            )

    def _canonical_obj(self) -> dict:
        """全 field の canonical な dict 表現。asdict は tuple を tuple のまま保持し、
        json.dumps がそれを JSON array として直列化する。"""
        return asdict(self)

    @property
    def contract_sha256(self) -> str:
        """全 field の canonical JSON (sort_keys, separators=(",",":"), ensure_ascii)
        の sha256。dataclass 自身の同一性 fingerprint (δ-12)。"""
        blob = json.dumps(
            self._canonical_obj(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _build_registry() -> dict:
    """静的 registry を構築する。**env 固有 literal はこの関数の内部にのみ現れる。**

    現在は linux-baremetal (cygnus 値) の 1 エントリのみ。Pegasus entry は D59 の
    4 条件が満たされる登録段まで足さない。
    """
    return {
        "linux-baremetal": ExecutionEnvironmentContract(
            env_tag="linux-baremetal",
            clocks_per_us=1800,
            numactl=("numactl", "--interleave=all"),
            attestation_mode="none",
            isolation_policy=IsolationPolicy(single_process=False, allow_resume=True),
            calibration_ref=CalibrationRef(
                path="output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json",
                sha256="751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5",
            ),
        ),
    }


# backing dict を module 名に束縛しない — MappingProxyType の裏側 dict へ到達する
# 注入経路 (ec._REGISTRY[...] = ...) を構造的に塞ぐ (レビュー所見 R1-1)。
REGISTRY = MappingProxyType(_build_registry())


def lookup(env_tag: str) -> ExecutionEnvironmentContract:
    """env_tag → 契約。未登録は EnvContractError (fail-closed、曖昧な fallback なし)。"""
    try:
        return REGISTRY[env_tag]
    except (KeyError, TypeError):
        raise EnvContractError(
            f"未登録の env_tag: {env_tag!r} (登録済み: {sorted(REGISTRY)})"
        )


# --------------------------------------------------------------------------- #
# env-literal AST 検査 (γ-16) — v2 モジュール閉包に env 固有 literal を禁止する。   #
# 検査「機構」だけをここに置く。禁止 literal 集合・対象モジュール一覧は test 側が    #
# 所有し引数で渡す。こうすることでこのモジュール本体は env 中立を保ち (禁止 literal   #
# の一覧を持たない)、自己参照で自分自身を発火させることがない。                        #
# --------------------------------------------------------------------------- #


def _region_node_ids(tree: ast.AST, region_name: str) -> set:
    """``region_name`` の FunctionDef 部分木に属する全ノードの id 集合。

    見つからなければ空集合 (= どの literal も免除されない)。
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == region_name:
            return {id(n) for n in ast.walk(node)}
    return set()


def find_env_literals(source: str, forbidden, allowed_region: str | None = None) -> list:
    """``source`` を parse し ``forbidden`` に含まれる env 固有 literal の
    (value, lineno) を返す。

    ``forbidden``: 禁止する literal 値の集合 (呼び手が所有。bool は int の
        サブクラスだが常に対象外)。
    ``allowed_region``: FunctionDef 名を渡すと、その部分木の中の literal だけを免除する。
        None なら一切免除しない。免除は「registry 静的定義部のみ許可」を実現し、定義部の
        外 (lookup / validation / property / 他モジュール) での出現を発火させる。
        恒真ではない: env_contract.py 自身も allowed_region=None で検査すれば literal を検出する。

    保証範囲: これは「literal の不在」の検査であって「値の不在」ではない。連結・join・
    chr() 等で計算された env 値、および forbidden 集合にない値 (別 env の数値等) は
    検出しない。偶発 hardcode の防止を狙いとし、故意の難読化には防壁を主張しない。
    """
    forbidden = set(forbidden)
    tree = ast.parse(source)
    exempt = _region_node_ids(tree, allowed_region) if allowed_region else set()
    hits: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool):
                continue
            if value in forbidden and id(node) not in exempt:
                hits.append((value, getattr(node, "lineno", -1)))
    return hits
