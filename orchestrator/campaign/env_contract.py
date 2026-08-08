# -*- coding: utf-8 -*-
"""実行環境契約 (F4 裁定) — 計測環境の同一性と活性化 authority。

型と世代 registry の import-time 構築は stdlib のみで完結し、activation record と
calibration の import / I/O は初回 Mapping 操作まで遅延する。env_tag 等価比較
(cygnus 固有値のハードコード) を、registry の fail-closed lookup へ置き換えるための
契約 dataclass と静的 registry を提供する。**このモジュールは何も強制しない宣言
field を持たない** (γ-3): 契約は「registry に登録された env の canonical な値集合」を
表現し、実環境 attestation・WAL root 検査・walltime 予約などの強制は driver / 登録段の
責務である。

契約が持たないもの (意図的):
- records / threads — freeze holdout が所有する動作点。契約はこれを上書きしない (δ-13)
- 自由文 note — calibration 参照は {path, sha256} の構造化参照のみ (γ-2)
- wal_root_policy / capture 列挙 — 宣言だけで発火しない恒真 field は置かない (γ-3)

registry は activation state から構築する read-only ``Mapping`` を
``MappingProxyType`` で公開し、register API を持たない (γ-13)。静的世代定義と reviewed
activation head 以外から env/current を注入する production 経路はない。
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import threading
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path, PurePosixPath
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
        if (self.attestation_mode == "required"
                and not self.isolation_policy.single_process):
            raise EnvContractError(
                "attestation_mode='required' は isolation_policy.single_process=True "
                "を必要とする"
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


@dataclass(frozen=True)
class GenerationEntry:
    """契約世代を表す。これは data であって権限ではない。issuer の型 gate に使わない。"""

    generation: int
    contract: ExecutionEnvironmentContract

    def __post_init__(self) -> None:
        if type(self.generation) is not int or self.generation <= 0:
            raise EnvContractError(
                f"generation は正整数でなければならない: {self.generation!r}"
            )
        if type(self.contract) is not ExecutionEnvironmentContract:
            raise EnvContractError(
                "contract は exact ExecutionEnvironmentContract でなければならない: "
                f"{self.contract!r}"
            )


def _leaf_json_pointers(value: object, pointer: str = "") -> dict[str, object]:
    """canonical object を leaf-level JSON Pointer と値の対応へ平坦化する。"""
    if type(value) is dict:
        if not value:
            return {pointer: value}
        flattened: dict[str, object] = {}
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            flattened.update(_leaf_json_pointers(child, f"{pointer}/{token}"))
        return flattened
    if type(value) in {list, tuple}:
        if not value:
            return {pointer: value}
        flattened = {}
        for index, child in enumerate(value):
            flattened.update(_leaf_json_pointers(child, f"{pointer}/{index}"))
        return flattened
    return {pointer: value}


def is_valid_successor(
    predecessor: ExecutionEnvironmentContract,
    successor: ExecutionEnvironmentContract,
) -> bool:
    """calibration path/SHA の対だけを変更する非同一 successor かを返す。"""
    if (type(predecessor) is not ExecutionEnvironmentContract
            or type(successor) is not ExecutionEnvironmentContract):
        return False
    before = _leaf_json_pointers(predecessor._canonical_obj())
    after = _leaf_json_pointers(successor._canonical_obj())
    differences = frozenset(
        pointer
        for pointer in before.keys() | after.keys()
        if pointer not in before
        or pointer not in after
        or before[pointer] != after[pointer]
    )
    allowed = frozenset({
        "/calibration_ref/path",
        "/calibration_ref/sha256",
    })
    if not differences or not differences <= allowed:
        return False
    return (
        ("/calibration_ref/path" in differences)
        == ("/calibration_ref/sha256" in differences)
    )


def _build_registry() -> dict[str, tuple[GenerationEntry, ...]]:
    """静的 registry を構築する。**env 固有 literal はこの関数の内部にのみ現れる。**

    登録済み calibration の bytes と契約値を静的に束縛する。
    """
    pegasus_g1 = GenerationEntry(
        generation=1,
        contract=ExecutionEnvironmentContract(
            env_tag="pegasus",
            clocks_per_us=2100,
            numactl=(),
            attestation_mode="required",
            isolation_policy=IsolationPolicy(single_process=True, allow_resume=False),
            calibration_ref=CalibrationRef(
                path=(
                    "output/env/pegasus/calibration/registered/"
                    "calibration-753f535a8d024727.json"
                ),
                sha256="753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49",
            ),
        ),
    )
    pegasus_g2 = GenerationEntry(
        generation=2,
        contract=replace(
            pegasus_g1.contract,
            calibration_ref=CalibrationRef(
                path=(
                    "output/env/pegasus/calibration/registered/"
                    "calibration-94a4b79fa31bba3c.json"
                ),
                sha256="94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9",
            ),
        ),
    )
    expected_pegasus_g2_sha256 = (
        "1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c"
    )
    if pegasus_g2.contract.contract_sha256 != expected_pegasus_g2_sha256:
        raise EnvContractError(
            "pegasus g2 contract_sha256 が reviewed golden と一致しない: "
            f"{pegasus_g2.contract.contract_sha256}"
        )
    return {
        "linux-baremetal": (
            GenerationEntry(
                generation=1,
                contract=ExecutionEnvironmentContract(
                    env_tag="linux-baremetal",
                    clocks_per_us=1800,
                    numactl=("numactl", "--interleave=all"),
                    attestation_mode="none",
                    isolation_policy=IsolationPolicy(single_process=False, allow_resume=True),
                    calibration_ref=CalibrationRef(
                        path=(
                            "output/env/linux-baremetal/calibration/"
                            "calibration_t48_skew0p9_rr50_rmw0.json"
                        ),
                        sha256="751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5",
                    ),
                ),
            ),
        ),
        "pegasus": (pegasus_g1, pegasus_g2),
    }


def _validate_generations_without_bootstrap_fuse(
    mapping: Mapping[str, tuple[GenerationEntry, ...]],
) -> None:
    """候補世代 mapping の構造と遷移を検証する。bootstrap fuse は含まない。"""
    seen_hashes: set[str] = set()
    for env_tag, sequence in mapping.items():
        if type(sequence) is not tuple or not sequence:
            raise EnvContractError(
                f"{env_tag!r} の世代列は非空 exact tuple でなければならない"
            )
        for expected_generation, entry in enumerate(sequence, start=1):
            if type(entry) is not GenerationEntry:
                raise EnvContractError(
                    f"{env_tag!r} の世代列要素は exact GenerationEntry でなければならない"
                )
            if entry.generation != expected_generation:
                raise EnvContractError(
                    f"{env_tag!r} の generation は順序どおり 1..N の連番でなければならない"
                )
            if entry.contract.env_tag != env_tag:
                raise EnvContractError(
                    f"mapping key {env_tag!r} と contract.env_tag "
                    f"{entry.contract.env_tag!r} が一致しない"
                )
            contract_sha256 = entry.contract.contract_sha256
            if contract_sha256 in seen_hashes:
                raise EnvContractError(
                    f"contract_sha256 が全 env・全世代で一意でない: {contract_sha256}"
                )
            seen_hashes.add(contract_sha256)
        for predecessor, successor in zip(sequence, sequence[1:]):
            if not is_valid_successor(predecessor.contract, successor.contract):
                raise EnvContractError(
                    f"{env_tag!r} に正当でない隣接 successor がある: "
                    f"g{predecessor.generation} -> g{successor.generation}"
                )


def validate_generations(
    mapping: Mapping[str, tuple[GenerationEntry, ...]],
) -> None:
    """候補世代 mapping の構造と隣接 successor を検証する。"""
    _validate_generations_without_bootstrap_fuse(mapping)


def _build_contract_sha256_index(
    mapping: Mapping[str, tuple[GenerationEntry, ...]],
) -> Mapping[str, tuple[GenerationEntry, ...]]:
    candidates: dict[str, list[GenerationEntry]] = {}
    for sequence in mapping.values():
        for entry in sequence:
            candidates.setdefault(entry.contract.contract_sha256, []).append(entry)
    return MappingProxyType({
        contract_sha256: tuple(entries)
        for contract_sha256, entries in candidates.items()
    })


# backing dict を module 名に束縛しない — MappingProxyType の裏側 dict へ到達する
# 注入経路 (ec._REGISTRY[...] = ...) を構造的に塞ぐ (レビュー所見 R1-1)。
GENERATIONS: Mapping[str, tuple[GenerationEntry, ...]] = MappingProxyType(
    _build_registry()
)
validate_generations(GENERATIONS)
_CONTRACT_SHA256_INDEX = _build_contract_sha256_index(GENERATIONS)

_ACTIVATION_HEAD_SERIAL: int = 1
_ACTIVATION_HEAD_STATE_SHA256: str = (
    "f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed"
)
_ACTIVATION_DIRECTORY = PurePosixPath(
    "orchestrator/campaign/env_contract_activations"
)


def _build_registered_contract_catalog() -> Mapping[str, tuple[tuple[int, str], ...]]:
    return MappingProxyType({
        env_tag: tuple(
            (entry.generation, entry.contract.contract_sha256)
            for entry in sequence
        )
        for env_tag, sequence in GENERATIONS.items()
    })


_REGISTERED_CONTRACT_CATALOG = _build_registered_contract_catalog()


@dataclass(frozen=True)
class _AuthoritySnapshot:
    state: object
    current: Mapping[str, ExecutionEnvironmentContract]


_AUTHORITY_LOCK = threading.Lock()
_AUTHORITY_PID = os.getpid()
_AUTHORITY_SNAPSHOT: _AuthoritySnapshot | None = None
_VERIFIED_CONTRACT_SHA256S: frozenset[str] = frozenset()


@dataclass(frozen=True)
class AuthorizedContract:
    """検証済み activation state と current contract の process-local receipt。"""

    contract: ExecutionEnvironmentContract
    activation_serial: int
    activation_state_sha256: str
    issued_pid: int
    process_seal: object
    _activation_state: object


_AUTHORIZATION_LOCK = threading.Lock()
_AUTHORIZATION_PID = os.getpid()
_AUTHORIZATION_PROCESS_SEAL = object()
_AUTHORIZED_CONTRACTS: dict[str, AuthorizedContract] = {}


def _repository_root() -> Path:
    """Source checkout / worktree / source-stage の root を ``__file__`` から解決する。"""
    try:
        module_path = Path(__file__).resolve(strict=True)
    except OSError as exc:
        raise EnvContractError(f"env_contract module path を解決できない: {exc}") from exc
    root = module_path.parents[2]
    sentinels = (
        root / "orchestrator" / "campaign" / "env_contract.py",
        root / Path(_ACTIVATION_DIRECTORY),
        root / "output",
    )
    if (not sentinels[0].is_file()
            or not sentinels[1].is_dir()
            or not sentinels[2].is_dir()):
        raise EnvContractError(
            "source checkout / worktree / source-stage の sentinel が揃っていない"
        )
    return root


def _verify_entry_calibration(entry: GenerationEntry, repo_root: Path) -> None:
    """選択された一行だけの calibration bytes と admission semantics を検証する。"""
    from . import calibration_verify

    contract = entry.contract
    if contract.attestation_mode == "required":
        expected_path = PurePosixPath(
            "output", "env", contract.env_tag, "calibration", "registered",
            f"calibration-{contract.calibration_ref.sha256[:16]}.json",
        )
        if PurePosixPath(contract.calibration_ref.path) != expected_path:
            raise EnvContractError(
                "required calibration path が content-addressed registered path でない: "
                f"{contract.calibration_ref.path!r}"
            )
    try:
        verified = calibration_verify.load_verified_calibration(
            env_tag=contract.env_tag,
            clocks_per_us=contract.clocks_per_us,
            attestation_mode=contract.attestation_mode,
            calibration_path=contract.calibration_ref.path,
            calibration_sha256=contract.calibration_ref.sha256,
            repo_root=repo_root,
        )
    except calibration_verify.AttestationError as exc:
        raise EnvContractError(
            f"active/historical contract の calibration 検証失敗: {exc}"
        ) from exc
    if contract.attestation_mode == "required":
        if verified.calibration is None or verified.calibration.quality.status != "accepted":
            raise EnvContractError("required calibration quality.status が accepted でない")


def _load_authority_snapshot() -> _AuthoritySnapshot:
    from . import env_contract_activation as activation

    repo_root = _repository_root()
    try:
        state = activation.load_activation_state(
            repo_root / Path(_ACTIVATION_DIRECTORY),
            registered_contracts=_REGISTERED_CONTRACT_CATALOG,
            expected_head_serial=_ACTIVATION_HEAD_SERIAL,
            expected_head_state_sha256=_ACTIVATION_HEAD_STATE_SHA256,
        )
    except activation.ActivationRecordError as exc:
        raise EnvContractError(f"activation authority 検証失敗: {exc}") from exc
    current: dict[str, ExecutionEnvironmentContract] = {}
    verified_hashes: set[str] = set()
    for row in state.active_contracts:
        sequence = GENERATIONS[row.env_tag]
        entry = sequence[row.generation - 1]
        if entry.contract.contract_sha256 != row.contract_sha256:
            raise EnvContractError("activation state と generation registry が load 後に不一致")
        _verify_entry_calibration(entry, repo_root)
        current[row.env_tag] = entry.contract
        verified_hashes.add(row.contract_sha256)
    global _VERIFIED_CONTRACT_SHA256S
    _VERIFIED_CONTRACT_SHA256S = frozenset(verified_hashes)
    return _AuthoritySnapshot(
        state=state,
        current=MappingProxyType(current),
    )


def _reset_authority_after_fork() -> None:
    global _AUTHORITY_LOCK, _AUTHORITY_PID, _AUTHORITY_SNAPSHOT
    global _VERIFIED_CONTRACT_SHA256S
    _AUTHORITY_LOCK = threading.Lock()
    _AUTHORITY_PID = os.getpid()
    _AUTHORITY_SNAPSHOT = None
    _VERIFIED_CONTRACT_SHA256S = frozenset()


os.register_at_fork(after_in_child=_reset_authority_after_fork)


def _reset_authorization_after_fork() -> None:
    """fork child で親の authorization lock、seal、receipt を継承しない。"""
    global _AUTHORIZATION_LOCK, _AUTHORIZATION_PID
    global _AUTHORIZATION_PROCESS_SEAL, _AUTHORIZED_CONTRACTS
    _AUTHORIZATION_LOCK = threading.Lock()
    _AUTHORIZATION_PID = os.getpid()
    _AUTHORIZATION_PROCESS_SEAL = object()
    _AUTHORIZED_CONTRACTS = {}


os.register_at_fork(after_in_child=_reset_authorization_after_fork)


def _authority_snapshot() -> _AuthoritySnapshot:
    global _AUTHORITY_PID, _AUTHORITY_SNAPSHOT
    if _AUTHORITY_PID != os.getpid():
        _reset_authority_after_fork()
    with _AUTHORITY_LOCK:
        if _AUTHORITY_PID != os.getpid():
            _reset_authority_after_fork()
            return _authority_snapshot()
        if _AUTHORITY_SNAPSHOT is None:
            _AUTHORITY_SNAPSHOT = _load_authority_snapshot()
        return _AUTHORITY_SNAPSHOT


def _clear_authority_cache_for_tests() -> None:
    """Test fixture 専用。production authority を変更せず process cache だけを捨てる。"""
    global _AUTHORITY_PID, _AUTHORITY_SNAPSHOT, _VERIFIED_CONTRACT_SHA256S
    with _AUTHORITY_LOCK:
        _AUTHORITY_PID = os.getpid()
        _AUTHORITY_SNAPSHOT = None
        _VERIFIED_CONTRACT_SHA256S = frozenset()
    with _AUTHORIZATION_LOCK:
        global _AUTHORIZED_CONTRACTS
        _AUTHORIZED_CONTRACTS = {}


def _ensure_calibration_verified(entry: GenerationEntry) -> None:
    global _VERIFIED_CONTRACT_SHA256S
    contract_sha256 = entry.contract.contract_sha256
    if contract_sha256 in _VERIFIED_CONTRACT_SHA256S:
        return
    with _AUTHORITY_LOCK:
        if contract_sha256 in _VERIFIED_CONTRACT_SHA256S:
            return
        _verify_entry_calibration(entry, _repository_root())
        _VERIFIED_CONTRACT_SHA256S = frozenset(
            (*_VERIFIED_CONTRACT_SHA256S, contract_sha256)
        )


class _ActivationRegistryView(Mapping[str, ExecutionEnvironmentContract]):
    """初回 Mapping 操作でだけ activation authority を load する read-only view。"""

    def __getitem__(self, env_tag: str) -> ExecutionEnvironmentContract:
        return _authority_snapshot().current[env_tag]

    def __iter__(self) -> Iterator[str]:
        return iter(_authority_snapshot().current)

    def __len__(self) -> int:
        return len(_authority_snapshot().current)


REGISTRY = MappingProxyType(_ActivationRegistryView())


def current_activation_state() -> object:
    """検証済み process-local activation state。receipt 単位が型付けして消費する。"""
    return _authority_snapshot().state


def authorize(env_tag: str) -> AuthorizedContract:
    """env_tag の current contract と activation receipt を一体で取得する。"""
    if type(env_tag) is not str:
        raise EnvContractError(
            f"env_tag は exact str でなければならない: {env_tag!r}"
        )
    snapshot = _authority_snapshot()
    try:
        contract = snapshot.current[env_tag]
    except (KeyError, TypeError):
        raise EnvContractError(
            f"未登録の env_tag: {env_tag!r} (登録済み: {sorted(snapshot.current)})"
        )
    state = snapshot.state
    with _AUTHORIZATION_LOCK:
        if _AUTHORIZATION_PID != os.getpid():
            raise EnvContractError(
                "authorization receipt issuer の PID が current process と一致しない"
            )
        current = _AUTHORIZED_CONTRACTS.get(env_tag)
        if (current is None
                or current.contract is not contract
                or current._activation_state is not state):
            current = AuthorizedContract(
                contract=contract,
                activation_serial=state.activation_serial,
                activation_state_sha256=state.activation_state_sha256,
                issued_pid=os.getpid(),
                process_seal=_AUTHORIZATION_PROCESS_SEAL,
                _activation_state=state,
            )
            _AUTHORIZED_CONTRACTS[env_tag] = current
        return current


def resolve_by_contract_sha256(
    contract_sha256: str,
    *,
    expected_env_tag: str | None = None,
) -> GenerationEntry:
    """全世代から hash-bound な GenerationEntry を一意に解決する。"""
    if type(contract_sha256) is not str or _HEX64_RE.fullmatch(contract_sha256) is None:
        raise EnvContractError(
            "contract_sha256 は 64 桁の小文字 hex でなければならない: "
            f"{contract_sha256!r}"
        )
    candidates = _CONTRACT_SHA256_INDEX.get(contract_sha256)
    if candidates is None:
        raise EnvContractError(f"未知の contract_sha256: {contract_sha256}")
    if len(candidates) != 1:
        raise EnvContractError(
            f"contract_sha256 を一意に解決できない: {contract_sha256}"
        )
    entry = candidates[0]
    state = _authority_snapshot().state
    if contract_sha256 not in state.ever_active_contract_sha256s:
        raise EnvContractError(
            "登録済みだが activation chain 上で ever-active でない contract_sha256: "
            f"{contract_sha256}"
        )
    if (expected_env_tag is not None
            and entry.contract.env_tag != expected_env_tag):
        raise EnvContractError(
            f"contract_sha256 の env_tag {entry.contract.env_tag!r} が "
            f"expected_env_tag {expected_env_tag!r} と一致しない"
        )
    _ensure_calibration_verified(entry)
    return entry


def lookup(env_tag: str) -> ExecutionEnvironmentContract:
    """env_tag → 契約。未登録は EnvContractError (fail-closed、曖昧な fallback なし)。"""
    try:
        return REGISTRY[env_tag]
    except (KeyError, TypeError):
        raise EnvContractError(
            f"未登録の env_tag: {env_tag!r} (登録済み: {sorted(REGISTRY)})"
        )


def lookup_required_attestation_contract() -> ExecutionEnvironmentContract:
    """Return the unique registered contract that requires attestation.

    The compute-site authorization rule consumes this registry property instead
    of duplicating an environment tag literal in an otherwise neutral module.
    Missing or ambiguous registry state fails closed.
    """
    candidates = tuple(
        contract
        for contract in REGISTRY.values()
        if contract.attestation_mode == "required"
    )
    if len(candidates) != 1:
        raise EnvContractError(
            "required attestation contract を一意に解決できない: "
            f"candidates={len(candidates)}"
        )
    return candidates[0]


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
