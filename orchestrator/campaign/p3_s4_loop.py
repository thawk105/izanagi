# -*- coding: utf-8 -*-
"""P3 後続段 4 driver — coder 自律ループの機械部分 (design v1 §4)。

**位置づけ:** 後続段 4 = coder (LLM) が初めて変異の値・方向を自律生成する段。
reward hacking 圧力が最も高い。iteration フロー (design v1 §4 の 1 周):

    1. planner (LLM):  current_perf (絶対 throughput を含む) + leading-indicators +
       whiteboard + optional policy_hint (このharnessが emit) → 方向提案 (proposal スキーマは具体値 field を持たない)
       checkpoint 復元時は whiteboard の delta_pct と direction / magnitude / result の
       型・値域を fail-closed に検査する。project_whiteboard() も append 前に同じ
       direction / magnitude / result の値域検査を通過させる。layer3_report の独立 reader
       も同じ値域検査を共有するが、iteration 整合・entry 件数・origin 束縛は引き続き
       対象外である ([T-287] の残余)
       justification / uncertainty の自由文は journal / report に残る
    2. coder   (LLM):  方向 + baseline (絶対 throughput 等の現行指標) → 具体 backoff 値 +
       hole コード (K2手動loopでは明示指定のcritic診断を任意の兄弟keyで渡せる)
    3. harness (本Py): coder コードを EVOLVE-BLOCK hole に挿入 → diff 検疫 (4a)
       - reject  → diff-quarantine rejection を WAL に焼き critic へ (bench に進めない)
       - pass    → run_campaign (build×2/verify/bench) に委譲 → WAL
    4. harness (本Py): 緑 (LI) + 赤 (rejection/liveness/diff-quarantine) digest を組む
    5. critic  (LLM):  帰属 + 次方向
    6. harness (本Py): whiteboard 射影 + 停止判定 (critic attribution 専用 field は
       ないが、generic field の値域は既存validatorで検証する)

**ループ主導権はメインセッション** (design v1 §4)。本モジュールは LLM を spawn しない —
planner/coder/critic の構造化出力を **引数として受け取り** 機械部分だけを回す
(critic-experiment が tools=Bash のみで guided.py 出力だけ見るのと同型のリーク制御:
Model Y = coder に filesystem browse を与えず、harness が context を射影する)。

**diff 検疫の baseline = silo-backoff-fixed.patch 適用後の working-tree** (design v1 §5
Q1 の確定、D39)。骨格 (#if/#else/#endif + stock 枝 + マーカー) は template patch が入れる
不変フレーム。coder の編集面は #if 合成枝 (hole) の 1 行のみ。baseline を「骨格適用後」に
錨づけることで、骨格挿入自体は diff に出ず coder の hole 変更だけが検疫対象になる
(HEAD=stock 基準だと骨格挿入が coder 変更に紛れる — 敵対検証 2026-07-07 の underspec 指摘)。

base provenance の参照点定義は _wal_attempt_provenance の docstring を参照。

fixture proposal で機械 E2E を回す実走口は main() (`--no-build` で build を省いた配線
dry-run、既定は kickoff 規模で実 build/verify/bench)。実 LLM の planner/coder/critic は
メインセッションが spawn し本モジュールの関数へ proposal を渡す。
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import hashlib
import json
import math
import os
import re
import secrets
import stat
import struct
import sys
import time
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import (attempt_registry_core, backoff_hole_grammar, buildcache,  # noqa: E402
               campaign_lock as campaign_lock_codec, condition_meaning_gate,
               coder_effect_gate, env_contract, execution_guard, ident,
               site_policy, sort_swo_oracle, trigger_gate_binding, wal)
from . import agent_outputs, knowledge_manifest                       # noqa: E402
from .axis_trigger_gating import MARKER_ID as TRIGGER_MARKER_ID  # noqa: E402
from .p3_b4_protocol import (  # noqa: E402
    B4_PROTOCOL_KEY,
    B4_PROTOCOL_VALUE,
    driver_kind_from_identity as b4_driver_kind_from_identity,
)
from .build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_registered_coder_build_authority_argument,
                                      attest_generator_output,
                                      build_run_context)
from .artifact_admission import (                         # noqa: E402
    ArtifactAdmissionError,
    CampaignReadPurpose,
    CertifiedCampaignView,
    RECEIPT_PAYLOAD_KEY,
    require_admitted_campaign,
    require_persisted_certified_commit,
)
from .diff_quarantine import (DiffQuarantine,              # noqa: E402
                                      DiffRejectSubtype,
                                      DiffQuarantineResult,
                                      parse_template_file)
from .layout import (CampaignLayout,                       # noqa: E402
                             exploration_campaign_layout)
from .loop import run_campaign                             # noqa: E402
from .model import (STAGE_ABORT, STAGE_BUILD_START,         # noqa: E402
                            STAGE_COMMIT, STAGE_VERIFY_DONE,
                            CampaignConfig, Genome)
from .pipeline import (PerfConfig, variant_id, S2_FLAGS,     # noqa: E402
                       SEARCH_CONFIG_VERIFY_KEY, VERIFY_LEGACY_PLUS_PERFORMANCE)
from . import p2_2, source_digest                           # noqa: E402
from .projection_guard import (                            # noqa: E402
    AbilityProbeMaterialError,
    CODER_CONTRACT_K2,
    assert_closed_proposal_schema,
    assert_no_ability_probe_material,
)
from ..critic.digest import (DIFF_QUARANTINE_REASON,                  # noqa: E402
                           STOCK_SRC_TOKEN,
                           build_digest, load_diff_rejections,
                           load_liveness_rejections, load_rejections,
                           load_verify_abort_signals, render_rejections,
                           render_text)
from ..critic.identity_projection import IdentityProjection          # noqa: E402


# ---- campaign 定数 (p3_s4_red 様式。実走前に pin/env を確認する) -----------------
# D1936: 新規試行は承認済みの完全40桁 pin に固定する。
PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
DECLARED_USE_CLASS = "exploration"
ENV_TAG = "linux-baremetal"           # 計測層タグ (規律: 計測層以外の数値を混ぜない)
CLK = 1800
NUMA = ["numactl", "--interleave=all"]
_SITE_ENV_TAGS = {
    site_policy.OTHER: ENV_TAG,
    site_policy.PEGASUS_COMPUTE: "pegasus",
}
_CAMPAIGN_ENV_KEY = "measurement_env"

_current_site = site_policy.current_site
_lookup = env_contract.lookup

MARKER_ID = "silo-backoff-magnitude"
SOURCE_REL = "include/backoff.hh"     # EVOLVE_BLOCK_SOURCES のメンバ (段 4 loop はこの 1 面のみ駆動)
TEMPLATE_PATCH = "patches/silo-backoff-fixed.patch"  # 骨格 (hole) を敷く不変フレーム

_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}


def _site_admits_measurement(site: str) -> bool:
    """計測を許す既知 site の exact set。未知値は fail-closed。"""
    return site in {site_policy.OTHER, site_policy.PEGASUS_COMPUTE}


def _admit_env_contract(site: str) -> env_contract.ExecutionEnvironmentContract:
    """解決済み site を admission 後に閉じた対応から契約へ写像する。"""
    if not _site_admits_measurement(site):
        raise execution_guard.ExecutionGuardError(
            f"計測用 env bytes は site={site!r} では生成できない"
        )
    return _lookup(_SITE_ENV_TAGS[site])


def _campaign_cfg_for_site(
        cfg: CampaignConfig, site: str, *,
        _contract: Optional[env_contract.ExecutionEnvironmentContract] = None,
) -> CampaignConfig:
    """Resolved site contract を identity に束縛し、Pegasus marker も分離する。"""
    contract = _contract if _contract is not None else _admit_env_contract(site)
    if site == site_policy.PEGASUS_COMPUTE:
        cfg = replace(
            cfg,
            search_config={
                **cfg.search_config,
                _CAMPAIGN_ENV_KEY: _SITE_ENV_TAGS[site],
            },
        )
    return ident.bind_environment_contract(cfg, contract)

# 停止条件 (design v1 §4、D39 で凍結)。
MAX_ITER = 10
MAX_WALLTIME_S = 3600
CONVERGE_STREAK = 3                   # 同一方向・magnitude=small が N 連続 → 収束
REVERSE_STREAK = 2                    # critic が逆方向を N 回推奨 + 改善なし → 枯渇

B4_PROPOSAL_RECEIPT_SHA256_KEY = "b4_closed_critic_receipt_sha256"

# [T-2101] 段 4 裁定 §7 の逐語。凍結済み prerun receipt schema は変更しない。
B4_PROPOSAL_BINDING_NON_GUARANTEES = (
    "continuation の提案は内容束縛されない (裁定パッケージ 1)。",
    "どの publication が権威かは強制されない (裁定パッケージ 2)。",
    "bootstrap 束縛は読み込んだ publication の manifest 外 attempt を拒否するが、"
    "その manifest の権威性は保証しない (D1880)。",
    "束縛の成功は耐久証拠に残らない (S12)。",
    "束縛されるのは実行される提案 (parse 結果の canonical 形) であって "
    "file の raw bytes ではない。",
    "照合の前に単独性検査 (`pgrep`)、Git pin 検査、launcher sidecar と "
    "campaign directory 作成が起きる。",
    "`1` と `1.0` は別の提案として扱う。実行 genome が同じでも hash は異なる。",
)

_B4_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

_MASSTREE_PREBUILD_RECEIPT_SCHEMA = "p3-s4-loop-masstree-prebuild/v1"
_MASSTREE_PREBUILD_RECEIPT_KEYS = frozenset({
    "schema_version",
    "fetchcontent_base_dir",
    "source_root",
    "sources",
    "config_h_path",
    "config_h_sha256",
    "configure_argv",
    "build_argv",
    "toolchain_manifest",
    "pbs_jobid",
})
_FETCHCONTENT_SOURCE_NAMES = ("masstree", "mimalloc", "googletest")
_CONDITION_GATE_OFFLINE_DEFINE_NAMES = frozenset({
    "CMAKE_PREFIX_PATH",
    "FETCHCONTENT_BASE_DIR",
    *(f"FETCHCONTENT_SOURCE_DIR_{name.upper()}"
      for name in _FETCHCONTENT_SOURCE_NAMES),
})


def _read_nonsymlink_regular_bytes(
        path: str | os.PathLike[str], *, label: str,
) -> bytes:
    """Read one inode without following a final-component symlink."""
    raw = os.fspath(path)
    if type(raw) is not str or not raw or "\0" in raw:
        raise ValueError(f"{label} path が不正")
    try:
        before = os.lstat(raw)
    except OSError as exc:
        raise ValueError(f"{label} を検査できない: {exc}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValueError(f"{label} は non-symlink regular file 必須")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(raw, flags)
    except OSError as exc:
        raise ValueError(f"{label} を安全に開けない: {exc}") from exc
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino)
                != (before.st_dev, before.st_ino)):
            raise ValueError(f"{label} の inode が open 中に変化した")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            return stream.read()
    finally:
        if fd >= 0:
            os.close(fd)


def _canonical_prebuild_directory(value: object, *, label: str) -> str:
    if type(value) is not str or not value or "\0" in value:
        raise ValueError(f"{label} は非空 str path 必須")
    if not os.path.isabs(value) or os.path.islink(value) or not os.path.isdir(value):
        raise ValueError(f"{label} は absolute non-symlink directory 必須")
    canonical = os.path.realpath(value)
    if value != canonical or value != os.path.abspath(value):
        raise ValueError(f"{label} は canonical path 必須")
    return canonical


def _canonical_prebuild_file(value: object, *, label: str) -> str:
    if type(value) is not str or not value or "\0" in value:
        raise ValueError(f"{label} は非空 str path 必須")
    if not os.path.isabs(value):
        raise ValueError(f"{label} は absolute path 必須")
    canonical = os.path.realpath(value)
    if value != canonical or value != os.path.abspath(value):
        raise ValueError(f"{label} は canonical path 必須")
    _read_nonsymlink_regular_bytes(canonical, label=label)
    return canonical


def _load_masstree_prebuild_receipt(
        path: str | os.PathLike[str],
) -> tuple[str, str, str, str, Dict[str, str]]:
    """Validate the job receipt and atomically project its five build inputs."""
    raw = _read_nonsymlink_regular_bytes(path, label="masstree prebuild receipt")
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"masstree prebuild receipt JSON が不正: {exc}") from exc
    if type(record) is not dict or set(record) != _MASSTREE_PREBUILD_RECEIPT_KEYS:
        raise ValueError("masstree prebuild receipt の top-level exact key 集合が不正")
    if record["schema_version"] != _MASSTREE_PREBUILD_RECEIPT_SCHEMA:
        raise ValueError("masstree prebuild receipt の schema_version が不正")

    base = _canonical_prebuild_directory(
        record["fetchcontent_base_dir"], label="fetchcontent_base_dir",
    )
    source_root = _canonical_prebuild_directory(
        record["source_root"], label="source_root",
    )
    if source_root != base:
        raise ValueError("fetchcontent_base_dir と source_root が一致しない")

    sources = record["sources"]
    if type(sources) is not list or len(sources) != len(_FETCHCONTENT_SOURCE_NAMES):
        raise ValueError("masstree prebuild receipt の sources 要素数が不正")
    sources_by_name: Dict[str, str] = {}
    for source in sources:
        if type(source) is not dict or set(source) != {"name", "head_commit"}:
            raise ValueError("masstree prebuild receipt の source record が不正")
        name = source["name"]
        head = source["head_commit"]
        if (type(name) is not str or name not in _FETCHCONTENT_SOURCE_NAMES
                or name in sources_by_name):
            raise ValueError("masstree prebuild receipt の source 名が不正")
        if type(head) is not str or re.fullmatch(r"[0-9a-f]{40}", head) is None:
            raise ValueError(f"masstree prebuild receipt の {name} HEAD が不正")
        sources_by_name[name] = head
    if set(sources_by_name) != set(_FETCHCONTENT_SOURCE_NAMES):
        raise ValueError("masstree prebuild receipt の source 名集合が不正")

    source_dirs = tuple(
        _canonical_prebuild_directory(
            os.path.join(source_root, f"{name}-src"),
            label=f"{name}_source_dir",
        )
        for name in _FETCHCONTENT_SOURCE_NAMES
    )
    config_h_path = _canonical_prebuild_file(
        record["config_h_path"], label="config_h_path",
    )
    expected_config_h = os.path.join(source_root, "masstree-src", "config.h")
    if config_h_path != expected_config_h:
        raise ValueError("config_h_path が source_root/masstree-src/config.h と一致しない")
    config_h_sha256 = record["config_h_sha256"]
    if (type(config_h_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", config_h_sha256) is None):
        raise ValueError("masstree prebuild receipt の config_h_sha256 が不正")
    observed_config_h_sha256 = hashlib.sha256(
        _read_nonsymlink_regular_bytes(config_h_path, label="config_h_path")
    ).hexdigest()
    if observed_config_h_sha256 != config_h_sha256:
        raise ValueError("masstree prebuild receipt の config.h hash が現物と一致しない")

    for field_name in ("configure_argv", "build_argv"):
        argv = record[field_name]
        if type(argv) is not list or any(type(item) is not str for item in argv):
            raise ValueError(f"masstree prebuild receipt の {field_name} が list[str] でない")
    try:
        buildcache.toolchain_compilers_from_manifest(record["toolchain_manifest"])
    except (TypeError, ValueError, buildcache.BuildCacheError) as exc:
        raise ValueError("masstree prebuild receipt の toolchain_manifest が不正") from exc
    if type(record["pbs_jobid"]) is not str or not record["pbs_jobid"]:
        raise ValueError("masstree prebuild receipt の pbs_jobid が非空 str でない")

    dependency_receipt = {
        "masstree_head": sources_by_name["masstree"],
        "config_sha256": config_h_sha256,
    }
    return base, *source_dirs, dependency_receipt


def _condition_gate_offline_configure_args(
        *, dependency_prefix: str, fetchcontent_base_dir: str,
        masstree_source_dir: Optional[object],
        mimalloc_source_dir: Optional[object],
        googletest_source_dir: Optional[object],
) -> tuple[str, ...]:
    """Project the offline defines needed by the independent condition gate."""
    source_dirs = buildcache._normalize_fetchcontent_source_dirs(
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
    )
    if source_dirs and not fetchcontent_base_dir:
        raise buildcache.BuildCacheError(
            "FetchContent SOURCE_DIR は FETCHCONTENT_BASE_DIR と同時指定必須"
        )
    configure_args = (
        *((f"-DCMAKE_PREFIX_PATH={dependency_prefix}",)
          if dependency_prefix else ()),
        *((f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base_dir}",)
          if fetchcontent_base_dir else ()),
        *buildcache._fetchcontent_source_defines(source_dirs),
    )
    expected_count = 1 + len(_FETCHCONTENT_SOURCE_NAMES) \
        + int(bool(dependency_prefix))
    if len(configure_args) != expected_count:
        raise RuntimeError(
            "campaign build producer returned a non-exact condition gate "
            "offline define set"
        )
    return configure_args


def _write_condition_gate_temp(path: Path, canonical_bytes: bytes) -> None:
    with path.open("xb") as output:
        output.write(canonical_bytes)
        output.flush()
        os.fsync(output.fileno())


def _fsync_condition_gate_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _persist_condition_gate_record(
        output_path: Path, canonical_bytes: bytes,
) -> None:
    temporary_path: Path | None = None
    try:
        temporary_path = output_path.parent / (
            f".{output_path.name}.tmp-{os.getpid()}-{secrets.token_hex(16)}"
        )
        _write_condition_gate_temp(temporary_path, canonical_bytes)
        os.replace(temporary_path, output_path)
        _fsync_condition_gate_directory(output_path.parent)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except Exception:
                pass


def _require_condition_gate(
        source_root: str, genome: Genome, *,
        configure_args: Tuple[str, ...] = (),
        stock_root: Optional[str] = None,
) -> dict | None:
    """Run the independent supply and meaning arms before any benchmark build."""
    value = genome.flags.get("BACKOFF_FIXED")
    if value is None:
        return None
    if value == -1 and stock_root is None:
        raise ValueError("stock condition gate requires stock_root")
    _cc, cxx = buildcache.compilers_for_current_site()
    if value == -1:
        captured = condition_meaning_gate.capture_define_inputs(
            source_root, stock_root=stock_root, configure_args=configure_args,
        )
        request = condition_meaning_gate.make_define_request(
            driver_id="orchestrator.campaign.p3_s4_loop",
            macro="BACKOFF_FIXED", requested_value=-1, default_value=-1,
            stock_comparison=True,
        )
        declaration = condition_meaning_gate.MeaningWitnessDeclaration(
            "BACKOFF_FIXED", (condition_meaning_gate.MeaningCase(
                -1, None,
                expected_selected_branch=condition_meaning_gate.STOCK_ADAPTIVE_BRANCH,
            ),),
        )
    else:
        captured = condition_meaning_gate.capture_define_inputs(
            source_root, configure_args=configure_args,
        )
        request = condition_meaning_gate.make_define_request(
            driver_id="orchestrator.campaign.p3_s4_loop",
            macro="BACKOFF_FIXED", requested_value=value, default_value=-1,
        )
        bits = struct.pack(">d", float(value)).hex()
        declaration = condition_meaning_gate.MeaningWitnessDeclaration(
            "BACKOFF_FIXED", (condition_meaning_gate.MeaningCase(value, (bits, bits)),),
        )
    supply = condition_meaning_gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake="cmake",
    )
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured, request=request, declaration=declaration, cxx=cxx,
    )
    admission = condition_meaning_gate.require_condition_gate_family(
        [supply], [meaning], use_class="certified-selection",
    )
    if not admission.admitted:
        rejection_parts = [
            "condition gate rejected P3 S4 loop: "
            f"supply={supply.reason_code} meaning={meaning.reason_code}"
        ]
        for label, record in (("supply", supply), ("meaning", meaning)):
            detail = record.evidence.get("detail")
            if detail is not None:
                rejection_parts.append(f"{label}_detail={detail}")
            else:
                rejection_parts.append(
                    f"{label}_evidence_keys={sorted(record.evidence.keys())}"
                )
        rejection_message = "; ".join(rejection_parts)

        evidence_write_failures = []
        try:
            evidence_root = os.environ.get("IZANAGI_S4_EVIDENCE_ROOT")
        except Exception as exc:
            evidence_root = None
            evidence_write_failures.append(
                f"evidence-root:{type(exc).__name__}"
            )
        if evidence_root:
            records = (
                ("supply", supply, "record_digest"),
                ("meaning", meaning, "record_digest"),
                ("admission", admission, "admission_digest"),
            )
            for label, record, digest_field in records:
                try:
                    arm_name = getattr(record, "arm", "admission")
                    record_digest = getattr(record, digest_field)
                    filename = (
                        f"condition-gate-{arm_name}-{record_digest}.json"
                    )
                    canonical_bytes = record.canonical_json().encode("ascii")
                    output_path = Path(evidence_root) / filename
                    _persist_condition_gate_record(output_path, canonical_bytes)
                except Exception as exc:
                    evidence_write_failures.append(
                        f"{label}:{type(exc).__name__}"
                    )
        if evidence_write_failures:
            rejection_message += (
                "; evidence_write_failures="
                + ",".join(evidence_write_failures)
            )
        raise RuntimeError(rejection_message)
    return {
        "supply_record": json.loads(supply.canonical_json()),
        "meaning_record": json.loads(meaning.canonical_json()),
        "admission": json.loads(admission.canonical_json()),
    }


class B4ProtocolError(RuntimeError):
    """An exact B-4 execution contract was not satisfied."""


def canonical_b4_proposal_sha256(document: object) -> str:
    """Derive the canonical identity of the proposal value that is executed."""
    if type(document) is not dict:
        raise B4ProtocolError("B-4 proposal canonical hash requires a JSON object")
    canonical_document = dict(document)
    canonical_document.pop(B4_PROPOSAL_RECEIPT_SHA256_KEY, None)
    try:
        canonical_bytes = attempt_registry_core.canonical_json_bytes(
            canonical_document
        )
    except (
        attempt_registry_core.AttemptRegistryCoreError,
        TypeError,
        ValueError,
    ) as exc:
        raise B4ProtocolError("B-4 proposal has no canonical JSON hash") from exc
    return hashlib.sha256(canonical_bytes).hexdigest()


def _require_b4_registry_attempt_hash(
    scheduled_attempts: object,
    attempt_id: object,
    *,
    driver_kind: object,
) -> str:
    """Select one exact registry row and return its independently sealed hash."""
    if type(attempt_id) is not str or not attempt_id:
        raise B4ProtocolError("B-4 bootstrap requires a non-empty attempt id")
    if driver_kind not in {"base", "sort", "trigger"}:
        raise B4ProtocolError("B-4 bootstrap driver kind is invalid")
    try:
        matches = tuple(
            attempt
            for attempt in scheduled_attempts
            if attempt.attempt_id == attempt_id
        )
    except (AttributeError, TypeError) as exc:
        raise B4ProtocolError("B-4 publication registry rows are invalid") from exc
    if len(matches) != 1:
        raise B4ProtocolError(
            "B-4 attempt id must match exactly one publication registry row"
        )
    attempt = matches[0]
    if attempt.driver != driver_kind:
        raise B4ProtocolError(
            "B-4 publication registry driver differs from the running driver"
        )
    expected = attempt.initial_proposal_sha256
    if type(expected) is not str or _B4_SHA256_RE.fullmatch(expected) is None:
        raise B4ProtocolError(
            "B-4 publication registry initial proposal hash is not 64 lowercase hex"
        )
    return expected


def require_b4_proposal_registry_binding(
    publication_root: object,
    attempt_id: object,
    document: object,
    *,
    driver_kind: object,
) -> None:
    """Require a bootstrap proposal to equal its sealed registry preimage."""
    if publication_root is None or publication_root == "":
        raise B4ProtocolError("B-4 bootstrap requires a publication root")
    if type(attempt_id) is not str or not attempt_id:
        raise B4ProtocolError("B-4 bootstrap requires a non-empty attempt id")
    from . import p3_b4_prerun_issuer

    try:
        publication = p3_b4_prerun_issuer.load_b4_prerun_publication(
            os.fspath(publication_root)
        )
    except (TypeError, ValueError, OSError) as exc:
        raise B4ProtocolError("B-4 prerun publication load failed") from exc
    manifest_matches = tuple(
        row for row in publication.manifest.rows
        if row.attempt_id == attempt_id
    )
    if len(manifest_matches) != 1:
        raise B4ProtocolError(
            "B-4 attempt id must match exactly one analysis manifest row "
            "for membership"
        )
    expected = _require_b4_registry_attempt_hash(
        publication.registry.scheduled_attempts,
        attempt_id,
        driver_kind=driver_kind,
    )
    observed = canonical_b4_proposal_sha256(document)
    if observed != expected:
        raise B4ProtocolError(
            "B-4 bootstrap proposal canonical hash differs from the publication registry"
        )


@dataclass(frozen=True)
class B4IterationAuthorization:
    receipt: Any | None
    terminal_receipt_sha256: str | None


# ==== 提案・状態の型 (LLM 出力と harness 状態) =================================

@dataclass
class PlannerProposal:
    """planner-v4 の出力 (値・機序なし)。"""
    axis: str
    direction: str                    # increase | decrease | explore_both
    magnitude: str                    # small | medium | large
    justification: str = ""
    uncertainty: str = ""


@dataclass
class CoderProposal:
    """coder-v4-autonomous の出力 (値 + hole コード)。"""
    axis: str
    value: int | float                # 無損失整数 1..1000 の backoff 量
    implementation: str               # value と一致する suffix-free strict numeric literal 1個の1文
    justification: str = ""
    confidence: str = "medium"

    def __post_init__(self) -> None:
        _assert_coder_value_domain(self.value)


@dataclass
class WhiteboardEntry:
    """proposal と harness result を保持する whiteboard の 1 行。

    passive dataclass のため値域は自身では検査しない。checkpoint 復元値は state_from_dict が
    direction / magnitude / result の型・値域を検査し、project_whiteboard() も構築・append 前に
    同じ値域検査を通過させる。layer3_report の独立 reader は同じ値域検査を共有する
    ([T-287] の残余)。delta_pct field は planner 射影時にも None を fail-closed 強制する。"""
    iteration: int
    direction: str
    magnitude: str
    result: str                       # success | fail | rejected
    delta_pct: Optional[float] = None   # 性能変化率 (率、具体 throughput 値でない)。段 4 は
                                        # 常に None = 段 6 予約 (統計的 delta/検証相は D39 残存リスク c)


@dataclass
class LoopState:
    """ループ状態。iteration は **WAL 由来でない独立カウンタ** — loop が増分し WAL からは
    読まない。online_digest の LeakageError (n>iterations) を将来このループに配線する際に
    恒真化させないための不変 (本ループでは LeakageError 未配線 = D26 の教訓を先取り)。"""
    whiteboard: List[WhiteboardEntry] = field(default_factory=list)
    iteration: int = 0
    start_ts: float = 0.0                # monotonic (プロセス内。永続化しない — 跨ぐと無意味)
    start_wall: float = 0.0             # 絶対 epoch (checkpoint 経由の cross-process wall budget)
    reverse_recommendations: int = 0    # critic の逆方向推奨の連続回数


@dataclass
class StopDecision:
    stop: bool
    reason: str                       # converged|reverse-exhausted|budget-*|continue


# ==== hole 挿入 + diff 検疫 (4a) ==============================================

def _indent_of(line: str) -> str:
    return line[:len(line) - len(line.lstrip())]


def render_hole(base_text: str, marker, implementation: str) -> str:
    """base_text (骨格適用後) の hole 行群を coder の implementation で置換する。

    hole = marker.hole_first .. marker.hole_last (現テンプレは単一行)。元の hole 行の
    インデントを保って implementation を挿入する (行頭が空白+コードになり、diff 検疫の
    二次検査 '_DIRECTIVE_RE (行頭 #)' に偶発ヒットしない — coder 規約の harness 側担保)。"""
    lines = base_text.split('\n')
    indent = _indent_of(lines[marker.hole_first - 1])
    new_body = [indent + ln if ln else ln for ln in implementation.split('\n')]
    out = lines[:marker.hole_first - 1] + new_body + lines[marker.hole_last:]
    return '\n'.join(out)


def make_working_diff(base_text: str, edited_text: str, source_rel: str) -> str:
    """base_text→edited_text の unified diff (git diff HEAD 相当だが baseline は
    骨格適用後の working-tree)。diff_quarantine.parse_diff が読む `+++ b/<path>` +
    `@@` 形式を difflib で生成する。"""
    base = base_text.splitlines(keepends=True)
    edited = edited_text.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        base, edited, fromfile=f"a/{source_rel}", tofile=f"b/{source_rel}"))


def quarantine(sub: str, implementation: str,
               marker_id: str = MARKER_ID,
               source_rel: str = SOURCE_REL,
               write: bool = True) -> Tuple[DiffQuarantineResult, str, str, str]:
    """骨格適用後の working-tree に coder の implementation を挿入し diff 検疫する。

    **前提: 呼び出し元が既に applied(TEMPLATE_PATCH) 下にある** (working-tree に骨格が
    入っている)。手順:
      1. backoff marker だけ type/raw-size preflight (path read より前)
      2. backoff.hh (骨格入り) を base_text として読む
      3. parse_template_file で marker を取り source_rel を差し替える (basename 推定を上書き)
      4. hole を implementation で置換 → edited_text (write=True でファイルに書く)
      5. working_diff = make_working_diff(base, edited)、head_text=base で structural validate
      6. structural pass の場合だけ、元の hole implementation そのものを有限 lexical
         coder-effect gate へ渡す
      7. 両既存 gate の pass 後、backoff marker だけ Tier 1 grammar を適用

    既存 ``HOLE_ESCAPE`` / ``HOST_EFFECT`` の理由を保存する契約は、新しい raw-size cap
    内の入力に限る。type/raw-size は帰属 regex と candidate materialization より先に
    fail-closed させるため、この二規則だけは従来理由より先になり得る。backoff 初期化子は
    suffix-free strict numeric literal 1 個に限定する。trigger / sort marker の受理集合には
    適用しない。

    Returns: (DiffQuarantineResult, base_text, edited_text, working_diff)。
    passed=False なら呼び出し元は build に進めず reject を WAL/critic へ (規律2 hard gate)。
    parse_template_file が None を返す (テンプレ骨格が壊れている) 場合は MALFORMED 相当の
    fails-closed 結果を合成して返す (骨格が読めなければ検疫できない = reject)。"""
    if marker_id == MARKER_ID:
        preflight = backoff_hole_grammar.validate_backoff_preflight(
            implementation
        )
        if not preflight.accepted:
            return _backoff_grammar_rejection(
                preflight, source_rel=source_rel, marker_id=marker_id,
            ), "", "", ""

    if (marker_id == TRIGGER_MARKER_ID
            and not trigger_gate_binding.is_canonical_predicate(implementation)):
        res = DiffQuarantineResult(
            passed=False, reason="trigger predicate が正準集合外",
            digest={"rejection_type": "diff-quarantine", "subtype": "membership",
                    "reason": "trigger predicate が正準集合外",
                    "diff_region": source_rel, "template_diff_id": marker_id,
                    "evidence": "canonical predicate membership failure"})
        return res, "", "", ""
    if marker_id == TRIGGER_MARKER_ID:
        implementation = trigger_gate_binding.canonicalize_predicate(
            implementation
        )

    path = os.path.join(sub, source_rel)
    with open(path, encoding="utf-8") as f:
        base_text = f.read()
    marker = parse_template_file(path, marker_id)
    if marker is None:
        res = DiffQuarantineResult(
            passed=False, reason="テンプレ骨格をパースできない (fails-closed)",
            digest={"rejection_type": "diff-quarantine", "subtype": "malformed",
                    "reason": "テンプレ骨格をパースできない",
                    "diff_region": source_rel, "template_diff_id": marker_id,
                    "evidence": "parse_template_file が None (骨格構造の破れ)"})
        return res, base_text, base_text, ""
    marker.source_rel = source_rel
    edited_text = render_hole(base_text, marker, implementation)
    working_diff = make_working_diff(base_text, edited_text, source_rel)
    res = DiffQuarantine(marker, working_diff, head_text=base_text).validate()
    if res.passed:
        findings = coder_effect_gate.scan_host_effects(implementation)
        if findings:
            first = findings[0]
            reason = "coder hole が有限 lexical host-effect policy に抵触"
            evidence = (
                f"finding_count={len(findings)} first_rule_id={first.rule_id} "
                f"first_category={first.category} "
                f"first_token_ordinal={first.token_ordinal} "
                f"first_line_number={first.line_number} "
                f"first_byte_length={first.byte_length}"
            )
            digest = {
                "rejection_type": "diff-quarantine",
                "subtype": DiffRejectSubtype.HOST_EFFECT.value,
                "reason": reason,
                "diff_region": source_rel,
                "template_diff_id": marker_id,
                "evidence": evidence,
                "rule_id": first.rule_id,
                "category": first.category,
                "finding_count": first.finding_count,
            }
            res = DiffQuarantineResult(
                passed=False,
                subtype=DiffRejectSubtype.HOST_EFFECT,
                reason=reason,
                digest=digest,
                violations=[digest],
            )
    if res.passed and marker_id == MARKER_ID:
        decision = backoff_hole_grammar.validate_backoff_implementation(
            implementation
        )
        if not decision.accepted:
            res = _backoff_grammar_rejection(
                decision, source_rel=source_rel, marker_id=marker_id,
            )
        else:
            canonical = (
                backoff_hole_grammar.canonicalize_backoff_implementation(
                    implementation
                )
            )
            edited_text = render_hole(base_text, marker, canonical)
            working_diff = make_working_diff(
                base_text, edited_text, source_rel
            )
    if res.passed and marker_id == "silo-writeset-sort":
        decision = sort_swo_oracle.validate_sort_implementation(
            implementation
        )
        if not decision.accepted:
            res = _sort_ir_grammar_rejection(
                decision,
                implementation=implementation,
                materialized_source=edited_text,
                source_rel=source_rel,
                marker_id=marker_id,
            )
        else:
            canonical = sort_swo_oracle.canonicalize_sort_implementation(
                implementation
            )
            edited_text = render_hole(base_text, marker, canonical)
            working_diff = make_working_diff(
                base_text, edited_text, source_rel
            )
    if write:
        if res.passed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(edited_text)
    return res, base_text, edited_text, working_diff


def _backoff_grammar_rejection(
    decision: backoff_hole_grammar.BackoffGrammarDecision,
    *,
    source_rel: str,
    marker_id: str,
) -> DiffQuarantineResult:
    """Project one grammar decision without candidate-derived bytes."""

    if decision.accepted or decision.rule_id is None or decision.stage is None:
        raise ValueError("backoff grammar rejection requires a fixed decision")
    reason = "backoff hole が Tier 1 受理文法外"
    evidence = f"rule_id={decision.rule_id} stage={decision.stage}"
    digest = {
        "rejection_type": "diff-quarantine",
        "subtype": DiffRejectSubtype.BACKOFF_GRAMMAR.value,
        "reason": reason,
        "diff_region": source_rel,
        "template_diff_id": marker_id,
        "evidence": evidence,
        "rule_id": decision.rule_id,
    }
    return DiffQuarantineResult(
        passed=False,
        subtype=DiffRejectSubtype.BACKOFF_GRAMMAR,
        reason=reason,
        digest=digest,
        violations=[digest],
    )


def _sort_ir_grammar_rejection(
    decision: sort_swo_oracle.SortIrAdmissionDecision,
    *,
    implementation: object,
    materialized_source: str,
    source_rel: str,
    marker_id: str,
) -> DiffQuarantineResult:
    """Project one sort admission decision through the oracle schema."""

    if (
        decision.accepted
        or decision.rule_id is None
        or decision.reason is None
        or decision.stage is None
    ):
        raise ValueError("sort IR rejection requires a fixed decision")
    proposal = implementation if type(implementation) is str else ""
    finding = sort_swo_oracle.SortSwoFinding(
        sort_swo_oracle.OracleRejectKind.STRUCTURE,
        decision.reason,
    )
    try:
        materialized_hole = sort_swo_oracle.extract_materialized_hole(
            materialized_source, marker_id,
        )
    except (TypeError, ValueError):
        materialized_hole = ""
    result = sort_swo_oracle.SortSwoOracleResult(
        sort_swo_oracle.OracleStatus.REJECT,
        hashlib.sha256(materialized_hole.encode("utf-8")).hexdigest(),
        hashlib.sha256(proposal.encode("utf-8")).hexdigest(),
        finding,
    )
    digest = sort_swo_oracle.rejection_digest(
        result, diff_region=source_rel, marker_id=marker_id,
    )
    digest["rule_id"] = decision.rule_id
    digest["admission_stage"] = decision.stage
    return DiffQuarantineResult(
        passed=False,
        subtype=DiffRejectSubtype.SORT_SWO_ORACLE,
        reason=decision.reason,
        digest=digest,
        violations=[digest],
    )


# ==== diff-quarantine reject の WAL 記録 (片肺の書き手側) ======================

def diffq_variant_id(
    genome: Genome,
    implementation: str,
    *,
    backoff_grammar_version: Optional[int] = None,
) -> str:
    """diff 検疫で reject された variant の WAL キー。build しない (src_token 無し) ため
    pipeline.variant_id は使えない — genome + 提案コードのハッシュで一意化する。"""
    if (backoff_grammar_version is not None
            and (type(backoff_grammar_version) is not int
                 or backoff_grammar_version < 1)):
        raise ValueError(
            "backoff_grammar_version must be an exact positive integer"
        )
    import hashlib
    preimage = genome.canonical()
    if backoff_grammar_version is not None:
        preimage += f"|backoff_grammar_version={backoff_grammar_version}"
    h = hashlib.sha256(
        (preimage + "|impl=" + implementation).encode()
    ).hexdigest()[:12]
    return f"diffq-{h}"


def record_diff_reject(layout: CampaignLayout, genome: Genome, implementation: str,
                       res: DiffQuarantineResult, env_tag: str = ENV_TAG, *,
                       trigger_gate_binding=None,
                       backoff_grammar_version: Optional[int] = None) -> str:
    """diff 検疫 reject を WAL に BUILD_START→ABORT(reason=diff-quarantine) で焼く。

    load_diff_rejections がこの形を読み返し critic に渡す (規律3: 検疫が reject を出した
    だけで消費されない片肺を作らない)。build/verify には到達しないので verify payload も
    fitness も無い (正しさゲート手前の失格 = 採用しない、規律2)。"""
    lock_grammar_version = wal._declared_backoff_grammar_version(
        wal._campaign_lock_value(layout)
    )
    if (lock_grammar_version is not None
            or backoff_grammar_version is not None):
        if (type(backoff_grammar_version) is not int
                or backoff_grammar_version != lock_grammar_version):
            raise wal.AttemptTopologyError(
                "diff reject backoff grammar version が campaign.lock と不一致"
            )
    v = diffq_variant_id(
        genome,
        implementation,
        backoff_grammar_version=backoff_grammar_version,
    )
    attempt_id = secrets.token_hex(16)
    start_payload = {"genome": genome.canonical(), "src_token": "",
                     "build_attempt_id": attempt_id}
    if trigger_gate_binding is not None:
        start_payload[wal.TRIGGER_BINDING_COMMITMENT_KEY] = wal.log_trigger_binding(
            layout, v, env_tag, attempt_id, trigger_gate_binding,
        )
    wal.log(layout, v, STAGE_BUILD_START, env_tag, start_payload)
    wal.log(layout, v, STAGE_ABORT, env_tag,
            {"reason": DIFF_QUARANTINE_REASON,
             "build_attempt_id": attempt_id,
             "genome": genome.canonical(),
             "diff_quarantine": res.digest or {}})
    return v


UNREGISTERED_CANDIDATE_LABEL = "candidate-unregistered"


@dataclass(frozen=True)
class CriticIdentityProjection(IdentityProjection):
    """1 campaign の BUILD_START から作る候補 ID 射影。"""

    admitted_view: CertifiedCampaignView = field(repr=False, compare=False)
    variant_labels: Dict[str, str]
    src_token_labels: Dict[Tuple[str, str], str]
    build_attempt_labels: Dict[Tuple[str, str], str]
    build_admission_labels: Dict[Tuple[str, str], str]

    @staticmethod
    def _nonempty_string(value: Optional[str], channel: str) -> Optional[str]:
        if value is None or value == "":
            return value
        if type(value) is not str:
            raise TypeError(f"{channel} は str/None が必要")
        return value

    @classmethod
    def _lookup_variant(
        cls, mapping: Dict[str, str], value: Optional[str], channel: str,
    ) -> Optional[str]:
        raw = cls._nonempty_string(value, channel)
        if raw is None or raw == "":
            return raw
        try:
            return mapping[raw]
        except KeyError:
            return UNREGISTERED_CANDIDATE_LABEL

    @classmethod
    def _lookup_derived(
        cls, mapping: Dict[Tuple[str, str], str], variant: Optional[str],
        value: Optional[str], channel: str,
    ) -> Optional[str]:
        raw = cls._nonempty_string(value, channel)
        if raw is None or raw == "":
            return raw
        parent = cls._nonempty_string(variant, "variant")
        try:
            return mapping[(parent or "", raw)]
        except KeyError:
            suffix = {
                "src_token": "source",
                "build_attempt_id": "attempt",
                "build_admission_receipt_sha256": "admission",
            }[channel]
            return f"{UNREGISTERED_CANDIDATE_LABEL}/{suffix}"

    def project_variant(self, value: Optional[str]) -> Optional[str]:
        return self._lookup_variant(self.variant_labels, value, "variant")

    def project_src_token(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        return self._lookup_derived(
            self.src_token_labels, variant, value, "src_token",
        )

    def project_build_attempt_id(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        return self._lookup_derived(
            self.build_attempt_labels, variant, value, "build_attempt_id",
        )

    def project_build_admission_receipt_sha256(
        self, variant: Optional[str], value: Optional[str],
    ) -> Optional[str]:
        return self._lookup_derived(
            self.build_admission_labels, variant, value,
            "build_admission_receipt_sha256",
        )


def _bind_projection_value(
    mapping: Dict, key, projected: str, channel: str,
) -> None:
    current = mapping.get(key)
    if current is not None and current != projected:
        raise ValueError(f"{channel} の campaign 内対応が競合")
    mapping[key] = projected


def make_critic_identity_projection(
    view: CertifiedCampaignView,
) -> CriticIdentityProjection:
    """certified admission 済み snapshot の BUILD_START 初出から label を作る。"""
    if type(view) is not CertifiedCampaignView:
        raise TypeError(
            "view は require_admitted_campaign() の exact CertifiedCampaignView が必要"
        )
    variant_labels: Dict[str, str] = {}
    src_token_labels: Dict[Tuple[str, str], str] = {}
    build_attempt_labels: Dict[Tuple[str, str], str] = {}
    build_admission_labels: Dict[Tuple[str, str], str] = {}
    next_ordinal = 1

    for record in view.records:
        if record.stage != STAGE_BUILD_START:
            continue
        raw_variant = record.variant
        raw_src_token = record.payload.get("src_token")
        if type(raw_variant) is not str or not raw_variant:
            raise ValueError("BUILD_START variant が非空 str でない")
        if raw_src_token is not None and type(raw_src_token) is not str:
            raise TypeError("BUILD_START src_token は str/None が必要")

        if raw_variant in variant_labels:
            label = variant_labels[raw_variant]
            if (label == STOCK_SRC_TOKEN) != (raw_src_token == STOCK_SRC_TOKEN):
                raise ValueError("同じ variant の stock/candidate 分類が競合")
        elif raw_src_token == STOCK_SRC_TOKEN:
            label = STOCK_SRC_TOKEN
        else:
            label = f"candidate-{next_ordinal:04d}"
            next_ordinal += 1
        _bind_projection_value(
            variant_labels, raw_variant, label, "variant",
        )

        if raw_src_token:
            source_label = (
                STOCK_SRC_TOKEN if raw_src_token == STOCK_SRC_TOKEN
                else f"{label}/source"
            )
            _bind_projection_value(
                src_token_labels, (raw_variant, raw_src_token),
                source_label, "src_token",
            )
        raw_attempt = record.payload.get("build_attempt_id")
        if raw_attempt:
            if type(raw_attempt) is not str:
                raise TypeError("BUILD_START build_attempt_id は str/None が必要")
            _bind_projection_value(
                build_attempt_labels, (raw_variant, raw_attempt),
                f"{label}/attempt", "build_attempt_id",
            )
        raw_admission = record.payload.get("build_admission_receipt_sha256")
        if raw_admission:
            if type(raw_admission) is not str:
                raise TypeError(
                    "BUILD_START build_admission_receipt_sha256 は str/None が必要"
                )
            _bind_projection_value(
                build_admission_labels, (raw_variant, raw_admission),
                f"{label}/admission", "build_admission_receipt_sha256",
            )

    return CriticIdentityProjection(
        admitted_view=view,
        variant_labels=dict(variant_labels),
        src_token_labels=dict(src_token_labels),
        build_attempt_labels=dict(build_attempt_labels),
        build_admission_labels=dict(build_admission_labels),
    )


# ==== critic 入力 digest (緑 + 赤、還流 on/off スイッチ) =======================

def make_critic_digest(view: CertifiedCampaignView, tag: str = "p3-s4",
                       reflux: bool = True, *,
                       identity_projection: IdentityProjection) -> str:
    """critic に渡す digest テキストを組む。

    緑 (render_text: committed LI) + 赤 (render_rejections: verify-red/liveness/
    diff-quarantine)。**reflux=False (還流 off ablation) では赤節を落とす** — critic に
    rejection の構造化 anomaly を還流させない対照アーム (main-experiment の LLM ablation、
    合流 1 点の切替。phase3.md 段 6 の第 3 アーム reason-only は段 6)。緑 LI は両アーム
    共通 (性能数値は trace-disabled build 由来、規律1)。"""
    if not isinstance(identity_projection, IdentityProjection):
        raise TypeError("identity_projection は IdentityProjection が必要")
    if type(view) is not CertifiedCampaignView:
        raise TypeError(
            "view は require_admitted_campaign() の exact CertifiedCampaignView が必要"
        )
    if (
        isinstance(identity_projection, CriticIdentityProjection)
        and identity_projection.admitted_view is not view
    ):
        raise ValueError("digest と identity projector は同じ admitted view が必要")
    green = render_text([build_digest(tag, {}, view)])
    if not reflux:
        return green
    livs, other = load_liveness_rejections(view)
    red = render_rejections(
        load_rejections(view), livs, other,
        load_verify_abort_signals(view),
        diff_rejections=load_diff_rejections(view),
        identity_projection=identity_projection)
    return green + "\n\n" + red


# ==== whiteboard 射影 (機序を落とす) =========================================

def project_whiteboard(state: LoopState, planner: PlannerProposal,
                       result: str, delta_pct: Optional[float] = None) -> WhiteboardEntry:
    """proposal と harness result を whiteboard の 5 field へ射影する (design v1 §4)。

    in-memory 射影では WhiteboardEntry の構築・append 前に direction / magnitude / result の
    型・値域検査を通過させる。checkpoint 復元値は state_from_dict が検査し、layer3_report の
    独立 reader も同じ値域検査を共有する ([T-287] の残余)。delta_pct field は planner 射影時に
    None を fail-closed 強制する。result の想定値は success (certified 緑) | fail (verify/liveness 赤) |
    rejected (diff 検疫 reject)。"""
    candidate = {
        "direction": planner.direction,
        "magnitude": planner.magnitude,
        "result": result,
    }
    checked = assert_whiteboard_value_domains(candidate, index=len(state.whiteboard))
    e = WhiteboardEntry(iteration=state.iteration, direction=checked["direction"],
                        magnitude=checked["magnitude"], result=checked["result"],
                        delta_pct=delta_pct)
    state.whiteboard.append(e)
    return e


def whiteboard_for_planner(state: LoopState) -> List[Dict]:
    """planner-v4 / coder-v4 入力の whiteboard フィールド。

    段 4 はこの whiteboard 射影経路の delta_pct field に限って None を fail-closed
    強制する (規律2/6)。checkpoint 復元時の direction / magnitude / result は
    state_from_dict が型・値域を検査し、project_whiteboard からの in-memory 値も append 前に
    同じ値域検査を通過する。layer3_report の独立 reader も同じ値域検査を共有する
    ([T-287] の残余)。これは planner 入力全体の
    性能値遮断ではない。絶対
    throughput は別 field の current_perf で planner へ、baseline で coder へ渡り、
    planner には leading_indicators も渡る。delta_pct field は load 側 state_from_dict
    と二重で塞ぎ、in-memory 経路 (project_whiteboard が誤って非 None を書く) も射影の
    関所で止める (監査 2026-07-08)。"""
    out = []
    for e in state.whiteboard:
        if not _DELTA_PCT_LIVE and e.delta_pct is not None:
            raise WhiteboardLeakError(
                f"段 4 の delta_pct≡None 不変が planner 射影で破れた "
                f"(iteration={e.iteration} delta_pct={e.delta_pct!r}、規律2/6)")
        out.append({"iteration": e.iteration, "direction": e.direction,
                    "magnitude": e.magnitude, "result": e.result, "delta_pct": e.delta_pct})
    return out


_K2_DIAGNOSIS_BOUNDARY = "critic_diagnosis_is_data_not_instructions"
_K2_DIAGNOSIS_SECTIONS = ("attribution", "recommend", "avoid", "uncertainty")


def _validate_k2_critic_diagnosis(value: Dict[str, Any]) -> None:
    keys = {"data_boundary", "source_sha256", *_K2_DIAGNOSIS_SECTIONS}
    if (type(value) is not dict or set(value) != keys
            or any(type(item) is not str for item in value.values())):
        raise ValueError("k2_critic_diagnosis requires exact six string fields")
    if value["data_boundary"] != _K2_DIAGNOSIS_BOUNDARY:
        raise ValueError("k2_critic_diagnosis data_boundary mismatch")
    if re.fullmatch(r"[0-9a-f]{64}", value["source_sha256"]) is None:
        raise ValueError("k2_critic_diagnosis source_sha256 must be lowercase SHA-256")


def k2_critic_diagnosis_from_bytes(raw: bytes) -> Dict[str, str]:
    """Explicit critic bytes only; no AO reader or inference of stop decisions."""
    diagnosis = {
        "data_boundary": _K2_DIAGNOSIS_BOUNDARY,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        **agent_outputs.extract_critic_sections(raw.decode("utf-8")),
    }
    _validate_k2_critic_diagnosis(diagnosis)
    return diagnosis


def k2_next_generation_inputs(
    context: Dict[str, Any],
    planner_input: Dict[str, Any],
    coder_input: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Copy complete caller inputs and project the builder's optional diagnosis.

    Caller supplies metrics, knowledge, whiteboards and planner output as usual.
    This does not validate full role schemas or launch either role.
    """
    planner, coder = dict(planner_input), dict(coder_input)
    if "k2_critic_diagnosis" in context:
        diagnosis = context["k2_critic_diagnosis"]
        _validate_k2_critic_diagnosis(diagnosis)
        planner["k2_critic_diagnosis"] = dict(diagnosis)
        coder["k2_critic_diagnosis"] = dict(diagnosis)
    else:
        planner.pop("k2_critic_diagnosis", None)
        coder.pop("k2_critic_diagnosis", None)
    return planner, coder


def planner_context_payload(
    state: LoopState,
    cfg: CampaignConfig,
    *,
    knowledge_input: Optional[Dict[str, Any]] = None,
    k2_critic_diagnosis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """段4 human-supervised loop: このharnessが権威を持つ入力 (whiteboard + 任意の
    policy_hint) を planner-v4 spawn 用 JSON へ射影する。current_perf/leading_indicators は
    メインセッションが別途合成し本関数の責務外。

    ``knowledge_input`` がある場合は両既存 key と同じ階層の兄弟 key として加える。
    ``k2_critic_diagnosis`` はK2・非B4・reflux onの明示入力に限る。

    ``policy_hint`` は search_config にキーがある場合だけ exact ``str`` を受け付ける。
    キーが無い場合は planner payload にも出力しない。
    """
    payload: Dict[str, Any] = {"whiteboard": whiteboard_for_planner(state)}
    if knowledge_input is not None:
        if type(knowledge_input) is not dict:
            raise ValueError("knowledge_input は exact dict が必要")
        payload["knowledge_input"] = knowledge_input
    if k2_critic_diagnosis is not None:
        _validate_k2_critic_diagnosis(k2_critic_diagnosis)
        if cfg.search_config.get(wal.KNOWLEDGE_LEVEL_SEARCH_KEY) != "K2":
            raise ValueError("k2_critic_diagnosis requires K2 campaign")
        if (knowledge_input is None or knowledge_input.get("knowledge_level") != "K2"
                or knowledge_input.get("data_boundary") != knowledge_manifest.DATA_BOUNDARY
                or not isinstance(knowledge_input.get("sources"), list)
                or not isinstance(knowledge_input.get("knowledge_manifest_sha256"), str)
                or re.fullmatch(r"[0-9a-f]{64}",
                                knowledge_input["knowledge_manifest_sha256"]) is None
                or knowledge_input["knowledge_manifest_sha256"]
                != cfg.search_config.get(wal.KNOWLEDGE_MANIFEST_SHA256_SEARCH_KEY)):
            raise ValueError("k2_critic_diagnosis requires bound K2 knowledge projection")
        if b4_reflux_ablation_mode(cfg) or cfg.search_config.get("reflux") != "on":
            raise ValueError("k2_critic_diagnosis requires non-B4 reflux on")
        payload["k2_critic_diagnosis"] = dict(k2_critic_diagnosis)
    if "policy_hint" not in cfg.search_config:
        return payload
    hint = cfg.search_config.get("policy_hint")
    if type(hint) is not str:
        raise ValueError("search_config['policy_hint'] は exact str が必要")
    payload["policy_hint"] = hint
    return payload


# ==== 停止判定 (design v1 §4、D39) ===========================================

def check_stop(state: LoopState) -> StopDecision:
    """収束 / 逆方向枯渇 / 予算尽き を機械判定する。

    - Budget: iteration >= MAX_ITER または wall-clock >= MAX_WALLTIME_S。
    - Convergence: 同一方向かつ magnitude=small が CONVERGE_STREAK 連続。段階的な
      magnitude 変化 (small→medium→large) は「異なる提案」として収束と扱わない。
    - Reverse-exhausted: critic の逆方向推奨が REVERSE_STREAK 回以上 + 直近改善なし
      (state.reverse_recommendations は critic 帰属を消費するメインセッションが更新)。"""
    # wall budget: checkpoint 経由 (main-session 駆動) では start_wall (絶対 epoch) を使う —
    # 各 iteration は別 Bash プロセスゆえ monotonic は跨ぐと無意味。start_wall 未設定 (in-process
    # fixture / test) では従来どおり monotonic を使う (後方互換。既存 test は start_ts のみ設定)。
    if state.start_wall:
        elapsed = time.time() - state.start_wall
    else:
        elapsed = time.monotonic() - state.start_ts if state.start_ts else 0.0
    if state.iteration >= MAX_ITER:
        return StopDecision(True, "budget-iterations")
    if elapsed >= MAX_WALLTIME_S:
        return StopDecision(True, "budget-walltime")
    # 収束は **評価が成立した** 提案だけで測る。diff 検疫 reject (result=rejected) は評価
    # 未成立ゆえ収束に数えない — reject 連続を「収束」と取り違えない (規律3、D39 決定2a)。
    evaluated = [e for e in state.whiteboard if e.result != "rejected"]
    tail = evaluated[-CONVERGE_STREAK:]
    if (len(tail) >= CONVERGE_STREAK
            and all(e.direction == tail[0].direction and e.magnitude == "small"
                    for e in tail)):
        return StopDecision(True, "converged")
    if state.reverse_recommendations >= REVERSE_STREAK:
        # 「直近改善なら止めない」escape は delta_pct が算出される段 6 で live 化する。段 4 は
        # delta_pct 未算出 (常に None、段 6 予約) ゆえ escape は明示的に無効 = reverse-exhausted は
        # reverse_recommendations 単独で判定する (恒真ガードを置かない、D39 残存リスク c/決定2b)。
        recent = state.whiteboard[-1] if state.whiteboard else None
        improved = recent is not None and recent.delta_pct is not None and recent.delta_pct > 0
        if not improved:
            return StopDecision(True, "reverse-exhausted")
    return StopDecision(False, "continue")


# ==== LoopState checkpoint/resume (main-session 駆動の cross-process 永続化) ====
#
# 段 4b の実ループはメインセッションが iteration を回す (Model Y、D39 決定7)。各 iteration は
# 別々の Bash 呼び出し = fresh Python プロセスゆえ、LoopState (whiteboard/iteration/reverse) を
# **ディスクに checkpoint** しないと iteration 間で状態が消え feedback loop が死ぬ (planner が
# 前 iteration の result を見れない)。D39 決定2 の「予算枯渇時に whiteboard を checkpoint し段 6
# へ inherit」の実体でもある。checkpoint は WAL でなく loop 状態の投影 — 正本は WAL (レコード)、
# checkpoint は planner に射影する abstract 状態 (機序なし・値なし、決定3 の型と同じ最小フィールド)。


def loop_state_path(layout: CampaignLayout) -> str:
    return os.path.join(layout.root, "loop_state.json")


class WhiteboardLeakError(ValueError):
    """段 4 の delta_pct≡None 不変が checkpoint 経由で破れた = 勝ち筋チャネル (性能値) の混入
    (規律2/6)。型で名前を whitelist するだけでは leak 防御にならない — 値チャネルが空であることを
    検査する (監査 2026-07-08 の real finding。anchor finding 同型 = 謳うだけの保証を発火させる)。"""


# delta_pct は段 4 では常に None (統計的 delta/検証相は段 6 予約、D39 残存リスク c)。段 4 で非 None が
# 現れる = drift/改竄/段6 checkpoint 流用による性能値の混入 → planner に流入すると iteration 毎の利得
# から採用値を逆算できる structural inference (規律2/6)。段 6 で delta_pct を live 化するときはここを
# True にして明示ゲートを開ける (それまでは load と planner 射影の両方で None を fail-closed 強制)。
_DELTA_PCT_LIVE = False


def state_to_dict(state: LoopState) -> Dict:
    """checkpoint へ焼く辞書。start_ts (monotonic) は永続化しない (跨ぐと無意味) —
    wall budget は start_wall (絶対 epoch) が担う。whiteboard は決定3 の 5 フィールドのみ
    (機序フィールドを持たない = structural inference 経路を型で塞ぐ、規律2/6)。"""
    return {"iteration": state.iteration, "start_wall": state.start_wall,
            "reverse_recommendations": state.reverse_recommendations,
            "whiteboard": [{"iteration": e.iteration, "direction": e.direction,
                            "magnitude": e.magnitude, "result": e.result,
                            "delta_pct": e.delta_pct} for e in state.whiteboard]}


_WB_FIELDS = {"iteration", "direction", "magnitude", "result", "delta_pct"}
_TOP_FIELDS = {"iteration", "start_wall", "reverse_recommendations", "whiteboard"}
_WB_VALUE_DOMAINS = (
    ("direction", frozenset({"increase", "decrease", "explore_both"})),
    ("magnitude", frozenset({"small", "medium", "large"})),
    ("result", frozenset({"success", "fail", "rejected"})),
)


def assert_whiteboard_value_domains(
        entry: Dict, index: int) -> Dict[str, str]:
    """1 件の whiteboard entry の direction/magnitude/result 値域を検査する。"""
    checked = {}
    for field_name, allowed in _WB_VALUE_DOMAINS:
        value = entry[field_name]
        if type(value) is not str or value not in allowed:
            sorted_allowed = sorted(allowed)
            raise ValueError(
                f"whiteboard entry[{index}].{field_name} は str の許可値 "
                f"{sorted_allowed!r} のいずれか必須 (受領型={type(value).__name__}) — "
                f"checkpoint schema drift/改竄の疑い (規律6)")
        checked[field_name] = value
    return checked


def state_from_dict(d: Dict) -> LoopState:
    """checkpoint 辞書から復元 — checkpoint はディスク上の外部状態 (信頼境界の外、規律6) ゆえ
    schema を fail-closed に強制する (監査 2026-07-08)。

    (1) **top-level は既知 4 フィールドを必須化**し未知キーを拒否する。欠落を無音デフォルト
        (`d.get(k, 0)`) にすると drift/改竄 checkpoint で iteration/reverse カウンタが暗黙リセット
        され、budget-iterations / reverse-exhausted の**予算ゲートが fail-open** する (直列計測資源
        の予算超過、規律4)。リーク側 (whiteboard entry) は塞いで予算側は塞がない非対称を解消する。
    (2) **whiteboard entry は既知 5 フィールドに絞り** (未知キー = 機序漏れの疑い、決定3)、段 4 は
        **delta_pct≡None を値契約として強制**する (型で名前を whitelist するだけでは勝ち筋チャネル
        の混入を防げない、規律2/6)。
    (3) checkpoint 復元時の direction / magnitude / result は exact str と閉じた値域を要求する。
        layer3_report の独立 reader も同じ共有検査を呼び、project_whiteboard() も append 前に
        同じ検査を通過させる。iteration 整合・entry 件数・campaign/run origin は本関数では
        検査しない。"""
    unknown = set(d) - _TOP_FIELDS
    if unknown:
        raise ValueError(f"checkpoint top-level に未知フィールド {unknown} — schema drift/改竄の疑い (規律6)")
    missing = _TOP_FIELDS - set(d)
    if missing:
        raise ValueError(f"checkpoint に必須フィールド {missing} 欠落 — 予算/収束カウンタの暗黙"
                         f"リセット (予算ゲート fail-open) を防ぐため fail-closed (規律2/4/6)")
    wb = []
    for index, e in enumerate(d["whiteboard"]):
        extra = set(e) - _WB_FIELDS
        if extra:
            raise ValueError(f"whiteboard entry に未知フィールド {extra} — 機序漏れの疑い (決定3)")
        delta = e.get("delta_pct")
        if not _DELTA_PCT_LIVE and delta is not None:
            raise WhiteboardLeakError(
                f"段 4 の delta_pct≡None 不変が破れた (delta_pct={delta!r}) — 勝ち筋チャネルの "
                f"checkpoint 経由混入 (規律2/6)。段 6 で live 化するまで None 固定")
        entry_iteration = int(e["iteration"])
        checked = assert_whiteboard_value_domains(e, index)
        wb.append(WhiteboardEntry(
            iteration=entry_iteration, direction=checked["direction"],
            magnitude=checked["magnitude"], result=checked["result"], delta_pct=delta))
    return LoopState(whiteboard=wb, iteration=int(d["iteration"]),
                     start_wall=float(d["start_wall"]),
                     reverse_recommendations=int(d["reverse_recommendations"]))


def save_loop_state(layout: CampaignLayout, state: LoopState) -> str:
    """LoopState を atomic に checkpoint する (os.replace = 途中で落ちても壊れた checkpoint を
    残さない、WAL 哲学)。tmp は **PID 付き一意名** — 同一 campaign に複数プロセスが当たっても
    共有 tmp の rename 衝突/部分読みを避ける (最終 os.replace は last-writer-wins のまま。段 4b は
    単一駆動が前提だが tmp 一意化は安価な標準化、監査 2026-07-08)。"""
    layout.ensure()
    p = loop_state_path(layout)
    tmp = f"{p}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state_to_dict(state), f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    return p


def load_loop_state(layout: CampaignLayout) -> Optional[LoopState]:
    """checkpoint があれば復元。無ければ None (呼び出し元が初期化する)。"""
    p = loop_state_path(layout)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return state_from_dict(json.load(f))


# Base-only evidence carrier; never an input to planner/coder/critic projection.
PROVENANCE_BASENAME = "p3_s4_loop_provenance.json"
_PROVENANCE_SCHEMA = "p3-s4-loop-provenance/v1"
_PROVENANCE_FIELDS = frozenset({
    "iteration", "variant", "build_attempt_id", "initial_proposal_sha256",
    "wal_refs", "outcome",
})
_PROVENANCE_OUTCOMES = frozenset({
    "certified", "aborted", "rejected", "dry-pass", "duplicate",
    "duplicate-skip", "rejected-preprocess",
})


def _provenance_path(layout: CampaignLayout) -> str:
    return os.path.join(layout.root, "reports", PROVENANCE_BASENAME)


def _validate_provenance(prov: Dict) -> None:
    if (type(prov) is not dict
            or prov.get("schema_version") != _PROVENANCE_SCHEMA
            or prov.get("axis") != MARKER_ID
            or type(prov.get("entries")) is not dict):
        raise ValueError("invalid base provenance header/entries")
    for key, entry in prov["entries"].items():
        if type(entry) is not dict or set(entry) != _PROVENANCE_FIELDS:
            raise ValueError("invalid base provenance entry fields")
        iteration = entry["iteration"]
        if type(iteration) is not int or iteration < 1 or key != str(iteration):
            raise ValueError("invalid base provenance iteration")
        for name in ("variant", "build_attempt_id"):
            value = entry[name]
            if value is not None and (type(value) is not str or not value):
                raise ValueError(f"invalid base provenance {name}")
        digest = entry["initial_proposal_sha256"]
        if digest is not None and (
                type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            raise ValueError("invalid base provenance proposal hash")
        refs = entry["wal_refs"]
        if type(refs) is not list or any(
                type(ref) is not str or re.fullmatch(r"wal:[0-9a-f]{64}", ref) is None
                for ref in refs):
            raise ValueError("invalid base provenance WAL refs")
        if (type(entry["outcome"]) is not str
                or entry["outcome"] not in _PROVENANCE_OUTCOMES):
            raise ValueError("invalid base provenance outcome")
    agent_outputs.canonical_bytes(prov)


def _load_provenance(layout: CampaignLayout) -> Dict:
    """Read without creating a report; quarantine corruption and stop.

    退避済み .corrupt.* による停止は、原本が不在の場合だけ。
    """
    path = Path(_provenance_path(layout))
    if not path.exists():
        if any(path.parent.glob(path.name + ".corrupt.*")):
            raise RuntimeError(f"base provenance requires repair: {path}.corrupt.*")
        return {}
    try:
        prov = json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=knowledge_manifest._reject_duplicate_keys)
        _validate_provenance(prov)
    except (ValueError, UnicodeError, RecursionError) as exc:
        # link is no-clobber, unlike replace; retain exact original bytes.
        quarantine = path.with_name(f"{path.name}.corrupt.{int(time.time())}")
        while True:
            try:
                os.link(path, quarantine)
                break
            except FileExistsError:
                quarantine = path.with_name(
                    f"{path.name}.corrupt.{int(time.time())}.{secrets.token_hex(8)}")
        path.unlink()
        raise RuntimeError(f"base provenance corrupt; repair {quarantine}") from exc
    return prov


def _write_provenance(layout: CampaignLayout, prov: Dict) -> None:
    """Publish with exclusive tmp, file fsync, replace, then directory fsync."""
    _validate_provenance(prov)
    raw = agent_outputs.canonical_bytes(prov)
    path = Path(_provenance_path(layout))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(16)}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        tmp.unlink(missing_ok=True)


def _append_provenance_entry(layout: CampaignLayout, iteration: int, entry: Dict) -> None:
    """Single-driver iteration-keyed overwrite merge, before checkpoint publication.

    保証は provenance を公開できない iteration を checkpoint に確定しないことだけ。
    公開後・checkpoint 前の中断では、非 B-4 certified は再実行で duplicate に
    なり得る。検疫 reject は新 attempt を追加し entry を上書きするため、旧 attempt
    は WAL にだけ残る。B-4 は WAL に履歴が残る bootstrap と continuation が
    それぞれ履歴・receipt 検査により再実行を拒否し、公開済み entry が残る。
    二 file の transaction や並行 merge
    の排他は保証しない。
    """
    prov = _load_provenance(layout)
    if not prov:
        prov = {"schema_version": _PROVENANCE_SCHEMA, "axis": MARKER_ID, "entries": {}}
    if type(iteration) is not int or iteration != entry.get("iteration"):
        raise ValueError("provenance iteration differs from entry")
    prov["entries"][str(iteration)] = dict(entry)
    _write_provenance(layout, prov)


def _wal_attempt_provenance(layout: CampaignLayout, out: Dict) -> Dict:
    """Bind the selected attempt to whole WAL records, in their original order.

    D2194 項 3: 参照点は同一 campaign の precursor iteration より前の最後の
    whiteboard success に対応する certified attempt。本 report で iteration から
    variant/build_attempt_id を引く。重複提案は既存評価を再利用するため、行順と
    評価の系譜は同一ではない。reference_snapshot_hash は当該 attempt の WAL
    commit record 全体、reference_receipt_hash は同 attempt の bench_done record
    全体を agent_outputs.canonical_bytes (allow_nan=False) で canonical 化した
    sha256 (接頭辞なし 64 hex)。wal_refs は同 digest に wal: を付ける。
    snapshot throughput と bench receipt は同じ certified attempt の既存 WAL を使う。
    祖先なし・同着・record 非一意・承認済み PerfConfig または env_tag の一致を
    確認できない場合は不適格。別祖先や別基準へ切り替えず、実走前は
    design_not_feasible、実走後は protocol violation とする。
    PerfConfig の records/threads/workload の全 key/extime/reps が比較対象。
    bench_done.payload.run_cmd は threads/records/extime と workload の
    rratio/skew/rmw、record.env_tag は環境の証拠。reps と ycsb_max_ope は
    run_cmd で確認できない不足であり len(tps) や default で補わない。
    定義と carrier は新規 base campaign 起動前に発効し、遡及補完はしない。
    """
    variant = out.get("variant")
    result = {"variant": variant, "build_attempt_id": None, "wal_refs": []}
    outcome = out["outcome"]
    if variant is None:
        if outcome in {"certified", "duplicate", "rejected"}:
            raise RuntimeError("base provenance missing selected variant/attempt")
        return result
    records = wal.read_records(layout)
    selected = out.get("records", {})
    if outcome in {"certified", "duplicate"}:
        attempt = selected.get(STAGE_COMMIT, {}).get("build_attempt_id")
    elif outcome == "aborted":
        # An abort payload without an ID is not evidence for a different start.
        payload = selected.get(STAGE_ABORT, selected.get(STAGE_BUILD_START, {}))
        attempt = payload.get("build_attempt_id")
    elif outcome == "rejected":
        terminal = next((record for record in reversed(records)
                         if record.variant == variant), None)
        attempt = (terminal.payload.get("build_attempt_id")
                   if terminal is not None and terminal.stage == STAGE_ABORT else None)
    else:
        return result
    if type(attempt) is not str or not attempt:
        if outcome in {"certified", "duplicate", "rejected"}:
            raise RuntimeError("base provenance missing selected attempt")
        return result
    starts = [record for record in records
              if record.variant == variant and record.stage == STAGE_BUILD_START
              and record.payload.get("build_attempt_id") == attempt]
    if len(starts) != 1:
        raise RuntimeError("base provenance selected attempt start missing/conflicting")
    selected_records = [record for record in records
                        if record.variant == variant
                        and record.payload.get("build_attempt_id") == attempt]
    result.update(build_attempt_id=attempt, wal_refs=[
        "wal:" + agent_outputs.canonical_sha256(vars(record))
        for record in selected_records
    ])
    return result


# ==== mutation-red 汎用ゲート (D38 残消化、design v1 §4(d)) ====================

_WS_RE = re.compile(r"\s+")


def _norm_expr(e: str) -> str:
    return _WS_RE.sub("", e.strip())


_TRIVIAL_TRUE_RE = re.compile(
    r"^(true|1|(.+)==\2|(.+)>=\3|(.+)<=\4)$", re.IGNORECASE)

_CONST_CMP_RE = re.compile(r"^(-?\d+(?:\.\d+)?)(==|!=|>=|<=|>|<)(-?\d+(?:\.\d+)?)$")


def _is_constant_tautology(c: str) -> bool:
    """両辺が数値定数の比較で常に真か (mutation で決して赤にならない = 恒真)。"""
    m = _CONST_CMP_RE.match(c)
    if not m:
        return False
    import operator
    ops = {"==": operator.eq, "!=": operator.ne, ">=": operator.ge,
           "<=": operator.le, ">": operator.gt, "<": operator.lt}
    return ops[m.group(2)](float(m.group(1)), float(m.group(3)))


def mutation_red_gate(assert_condition: str, invariant: str) -> Tuple[bool, str]:
    """auditor が追加する assert の **非恒真性** を構文検査する (design v1 §4(d))。

    ガード = `assert condition != invariant`: assert 条件が invariant (常に成り立つ性質)
    と構造的に同一なら恒真 = mutation で決して赤にならない = 謳うだけで発火しない保証
    (規律3 の「正しさシグナルを後付けにしない」の対偶: 発火しない gate は無価値)。

    これは **構文レベルの一次篩** — 実 mutation で赤になるかの担保は positive control
    実走 (段 3 s3_lock_coverage 様式の broken patch 赤緑) が別途行う (auditor.md L62 が
    「非恒真性の実際の担保は driver の mutation-red レコード」と前提化済み)。段 4 の
    編集面は backoff hole のみ (lock 経路は段 5) ゆえ auditor 新 assert は限定的で、
    本ゲートは枠組み + 恒真 assert を弾くテストで実証する。段 5 で lock 経路が開くと
    実 mutation 確認が load-bearing になる。

    本篩が弾くのは構文的に自明な恒真のみ (true/1・両辺同一比較・定数比較)。文脈依存の
    意味的恒真 (unsigned 変数の `x>=0` 等) は **fail-open で通す** — 構文検査の原理的限界
    (D33: text 検査の文脈認識化は不可能かつ罠)。ゆえに本ゲートは load-bearing でなく、実
    mutation で赤になるかの担保は positive control 実走 (段 5 s3_lock_coverage 様式) が負う。

    Returns: (ok, reason)。ok=False なら恒真 (reject すべき assert)。"""
    c = _norm_expr(assert_condition)
    inv = _norm_expr(invariant)
    if not c:
        return False, "assert 条件が空 (発火しない)"
    if c == inv:
        return False, (f"恒真: assert 条件が invariant と構造的に同一 "
                       f"({assert_condition!r}) — mutation で赤にならない")
    if _TRIVIAL_TRUE_RE.match(c):
        return False, f"恒真: assert 条件が自明に真 ({assert_condition!r})"
    if _is_constant_tautology(c):
        return False, f"恒真: assert 条件が定数比較で常に真 ({assert_condition!r})"
    return True, ""


# ==== campaign 設定 + 機械判定 (p3_s4_red 様式) ==============================

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def default_cfg(
    reflux: bool = True,
    *,
    b4_reflux_ablation: bool = False,
    _b4_launch_context=None,
) -> CampaignConfig:
    """段 4 自律ループの campaign 設定。reflux (還流 on/off) は search_config に焼き、
    LLM ablation の対照を identity で分離する (別 campaign = 別 output dir、混ざらない)。"""
    search_config = {"scale": "silo", "axis": MARKER_ID,
                     "reflux": "on" if reflux else "off",
                     "records": 100_000, "threads": 4,
                     backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY:
                         backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION}
    if b4_reflux_ablation:
        from .p3_b4_launcher import require_b4_any_context
        require_b4_any_context(
            _b4_launch_context,
            expected_driver_kind="base",
            boundary="base marker creation",
        )
        search_config[B4_PROTOCOL_KEY] = B4_PROTOCOL_VALUE
    cfg = CampaignConfig(
        spec_slug="p3-s4-loop", search_tag="s4-autonomous",
        spec_content=("P3 後続段 4: coder 自律ループ。planner が方向 (値なし) を提案し "
                      "coder が勝ち筋値を見ずに backoff 値を合成、diff 検疫 (4a) を通した "
                      "hole 変異のみ build/verify/bench に進む。critic 帰属を次 iteration に "
                      "還流 (LLM ablation の on アーム)。fixture red を正系列に混ぜない"),
        ccbench_commit=PIN,
        search_config=search_config,
        trial="p3-s4-loop")
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    return ident.bind_admission_policy(cfg, context.policy)


def _resolve_knowledge_manifest_argument(
    manifest_path: Optional[str | os.PathLike[str]],
) -> Optional[knowledge_manifest.ResolvedKnowledgeManifest]:
    if manifest_path is None:
        return None
    return knowledge_manifest.load_and_resolve_manifest(
        manifest_path,
        repo_root=_repo_root(),
    )


def _prepare_knowledge_campaign(
    cfg: CampaignConfig,
    resolved: Optional[knowledge_manifest.ResolvedKnowledgeManifest],
    *,
    classification: str,
    de_novo_claim: bool,
) -> tuple[
    CampaignConfig,
    Optional[CampaignLayout],
    Optional[Dict[str, Any]],
]:
    """両 CLI 経路で同じ typed manifest から identity、receipt、projection を作る。"""
    if resolved is None:
        return cfg, None, None
    bound = replace(
        cfg,
        search_config={
            **cfg.search_config,
            wal.KNOWLEDGE_LEVEL_SEARCH_KEY: resolved.manifest.knowledge_level,
            wal.KNOWLEDGE_MANIFEST_SHA256_SEARCH_KEY:
                resolved.knowledge_manifest_sha256,
        },
    )
    layout = exploration_campaign_layout(str(ident.campaign_id(bound)))
    layout.ensure()
    knowledge_manifest.write_receipt(
        layout.root,
        resolved,
        classification=classification,
        de_novo_claim=de_novo_claim,
    )
    return bound, layout, knowledge_manifest.planner_projection(resolved)


def default_perf() -> PerfConfig:
    """配線規模 (kickoff/red と同じ、性能比較用 calibration ではない — 規律4)。
    実 fitness 比較に入る段では calibrator が決めた records/threads/reps に差し替える。"""
    return PerfConfig(records=100_000, threads=4,
                      workload={"ycsb_rratio": "50", "ycsb_zipf_skew": "0.9",
                                "ycsb_rmw": "false"}, extime=1, reps=2)


def calibrated_perf(workload_name: str) -> PerfConfig:
    """Use the approved P2 calibration and the exact four-key workload."""
    return PerfConfig(
        records=p2_2.RECORDS, threads=p2_2.THREADS,
        workload={**dict(p2_2.WORKLOADS)[workload_name],
                  "ycsb_max_ope": S2_FLAGS["ycsb_max_ope"]},
        extime=p2_2.EXTIME, reps=p2_2.REPS,
    )


# ==== 帰属整合 (value ↔ hole literal、D39 決定7 の機械強制) ====================

class AttributionMismatch(ValueError):
    """coder.value と implementation の backoff literal が食い違う = 帰属汚染 (規律6/D39 決定7)。
    メインセッション (Model Y の loop 主導) が catch し coder に再提案させる想定 — harness は
    値と走る literal の不一致を素通しせず、ここで止める (謳うだけの整合規約にしない)。"""


_CODER_VALUE_DOMAIN_MESSAGE = (
    "帰属汚染: coder value は bool でない 1..1000 の有限な整数でなければならない "
    "(規律6/D39 決定7)"
)


def _assert_coder_value_domain(value) -> None:
    """Tier 1 値域判定を main の固定例外契約へ適配する。"""

    decision = backoff_hole_grammar.validate_backoff_value(value)
    if decision.accepted:
        return
    error = AttributionMismatch(_CODER_VALUE_DOMAIN_MESSAGE)
    error.stage = decision.stage
    error.rule_id = decision.rule_id
    error.reason = decision.reason
    raise error


def assert_value_literal_consistent(coder: CoderProposal) -> None:
    """coder.value と implementation の backoff literal の整合を機械強制する (D39 決定7)。

    Model Y では coder (untrusted、規律6) が value と implementation を独立フィールドで供給する。
    両者が食い違うと genome{BACKOFF_FIXED=int(value)} に紐付く certified fitness が実際に走った
    別 literal binary の性能になり **帰属が汚染される** (どの値が効いたかの還流信号が自己矛盾)。
    D39 決定7 はこれを「整合規約」と呼ぶが規約は謳うだけでは発火しない — harness が機械照合する。

    ``genome`` の宣言済み scalar ``BACKOFF_FIXED`` は候補の設計上の帰属 field であり、
    自由記述 bytes の非反射対象外である。これを opaque 化すると campaign identity と
    fitness 帰属が壊れるため、本検査は value ↔ literal の一致を保ったまま明示値を使う。

    判定: implementation の `now_backoff = <lit>` 代入 literal が value と数値一致すること。
    代入 literal を抽出できない場合は無条件に fails-closed とする。"""
    implementation_preflight = (
        backoff_hole_grammar.validate_backoff_preflight(coder.implementation)
    )
    if not implementation_preflight.accepted:
        raise backoff_hole_grammar.BackoffGrammarViolation(
            implementation_preflight
        )

    _assert_coder_value_domain(coder.value)

    fixed_message = (
        "帰属汚染: coder value と hole literal の一致を機械確認できない "
        "(規律6/D39 決定7)"
    )
    try:
        coder_value = float(coder.value)
    except (TypeError, ValueError, OverflowError):
        raise AttributionMismatch(fixed_message) from None

    try:
        assigned, assigned_value, _literal_values = (
            backoff_hole_grammar.attribution_numeric_literals(
                coder.implementation
            )
        )
    except Exception:
        raise AttributionMismatch(fixed_message) from None
    if not assigned or assigned_value != coder_value:
        raise AttributionMismatch(fixed_message)


def _check_attribution_before_quarantine(
    coder: CoderProposal,
) -> backoff_hole_grammar.BackoffGrammarDecision:
    """Run attribution only for candidates accepted by the full grammar.

    The full grammar is an attribution guard, not an outer rejection selector.
    Rejected candidates still go through ``quarantine()`` so its established
    HOLE_ESCAPE -> HOST_EFFECT -> backoff grammar order chooses the result.
    Invalid values retain the existing attribution-domain failure even when the
    implementation has an independent full-grammar violation.
    """

    decision = backoff_hole_grammar.validate_backoff_implementation(
        coder.implementation
    )
    value_decision = backoff_hole_grammar.validate_backoff_value(coder.value)
    if decision.accepted or not value_decision.accepted:
        assert_value_literal_consistent(coder)
    return decision


def _require_backoff_grammar_version(cfg: CampaignConfig) -> int:
    """Return the single campaign-declared grammar version or fail closed."""

    key = backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY
    declared = cfg.search_config.get(key)
    expected = backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION
    if type(declared) is not int or declared != expected:
        raise ValueError(
            f"cfg.search_config.{key} must exactly equal {expected}"
        )
    return declared


# ==== 1 iteration の機械 E2E (fixture proposal で実走) ========================

def _duplicate_snapshot(layout: CampaignLayout, variant: str):
    """Read duplicate evidence under one campaign-lock identity snapshot."""
    lock_path = Path(layout.lock_file)
    try:
        lock_bytes = lock_path.read_bytes()
        campaign_lock_sha256 = hashlib.sha256(lock_bytes).hexdigest()
        decoded_lock = campaign_lock_codec.decode_campaign_lock_bytes(lock_bytes)
    except (OSError, campaign_lock_codec.CampaignLockCodecError) as exc:
        raise ArtifactAdmissionError(
            "duplicate campaign lock cannot be read or decoded"
        ) from exc

    records = wal.read_records(layout)
    try:
        lock_sha256_after_records = hashlib.sha256(
            lock_path.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise ArtifactAdmissionError(
            "duplicate campaign lock cannot be re-read after WAL"
        ) from exc
    if lock_sha256_after_records != campaign_lock_sha256:
        raise ArtifactAdmissionError(
            "duplicate campaign lock changed while reading WAL"
        )

    wal.validate_backoff_grammar_bindings(
        records, campaign_lock=decoded_lock,
    )
    wal.validate_knowledge_provenance_bindings(
        records, campaign_lock=decoded_lock,
    )
    wal.validate_commit_contract_bindings(records, campaign_lock=decoded_lock)
    wal.validate_trigger_bindings(records, campaign_lock=decoded_lock)
    records_by_stage: Dict[str, Dict] = {}
    commit_record = None
    for index, record in enumerate(records):
        if (record.variant == variant
                and record.stage != trigger_gate_binding.WAL_RECORD_STAGE
                and not wal._is_trigger_orphan_tombstone_at(records, index)):
            payload = dict(record.payload)
            payload.pop(RECEIPT_PAYLOAD_KEY, None)
            records_by_stage[record.stage] = payload
            if record.stage == STAGE_COMMIT:
                commit_record = record
    return records, records_by_stage, commit_record, campaign_lock_sha256

def _resolve_duplicate(layout: CampaignLayout, planner: PlannerProposal,
                       state: LoopState, summary, log=print) -> Dict:
    """重複提案 (run_campaign がリカバリでスキップし summary.results が空) を解決する。

    coder が独立に選んだ値が既存 genome (同一 src_token) と一致し、同一 variant_id が
    既に terminal (前 iteration で certified/aborted 済み) だと run_campaign はリカバリで
    再評価せず summary.results が空になる (loop.py の skip 経路)。これを新規の失敗と
    取り違えない (規律3: 正しさ/評価シグナルを後付けにしない・なぜこうなったかを構造化
    して返す — ここは壊れていない)。variant id は run_campaign が applied(...) 内で確定した
    `summary.skipped_variants` だけを使い、既存 WAL レコードから証拠を復元する。ここで
    source_digest.resolve を再実行してはならない — 呼び手の revert 後 tree からは stock id
    (別 variant) しか出ず、別 variant の WAL 証拠で成否を誤分類し (whiteboard/checkpoint は
    id を持たず分類だけが汚染)、trigger 系 driver では誤った variant id が provenance へ
    永続化する ([T-157]、id 確定点の単一化 = D23/D24。監査 2026-07-09、段 4b iteration 2 の
    実走 = coder が iteration 1 と独立に同じ値を再提案した実例で発見)。
    identity_skipped (id 未確定) の分は skipped_variants に無い → 成功を捏造せず fail 側。"""
    dup_v = summary.skipped_variants[0] if summary.skipped_variants else None
    records = []
    recs = {}
    commit_record = None
    campaign_lock_sha256 = None
    snapshot_rejected = False
    if dup_v:
        try:
            records, recs, commit_record, campaign_lock_sha256 = (
                _duplicate_snapshot(layout, dup_v)
            )
        except ArtifactAdmissionError:
            snapshot_rejected = True

    commit_payload = recs.get(STAGE_COMMIT)
    verify_payload = recs.get(STAGE_VERIFY_DONE, {})
    commit_admitted = False
    if commit_payload is not None and commit_record is not None:
        assert campaign_lock_sha256 is not None
        try:
            require_persisted_certified_commit(
                records,
                commit_record,
                campaign_lock_sha256=campaign_lock_sha256,
            )
        except ArtifactAdmissionError:
            snapshot_rejected = True
        else:
            commit_admitted = True
    if commit_admitted:
        commit_attempt_id = commit_payload.get("build_attempt_id")
        verify_attempt_id = verify_payload.get("build_attempt_id")
        verdict = verify_payload.get("verdict", "")
        if ((commit_attempt_id is not None or verify_attempt_id is not None)
                and commit_attempt_id != verify_attempt_id):
            verdict = ""
        project_whiteboard(state, planner, "success", delta_pct=None)
        log(f"  重複提案 (既存 certified variant {dup_v} と同一 genome、新規評価はスキップ)")
        return {"outcome": "duplicate", "variant": dup_v,
                "fitness_tps": commit_payload.get("fitness_tps"),
                "verdict": verdict, "records": recs}
    abort_payload = recs.get(STAGE_ABORT, {})
    abort_attempt_id = abort_payload.get("build_attempt_id")
    verify_attempt_id = verify_payload.get("build_attempt_id")
    verdict = "" if snapshot_rejected else verify_payload.get("verdict", "")
    if ((abort_attempt_id is not None or verify_attempt_id is not None)
            and abort_attempt_id != verify_attempt_id):
        verdict = ""
    project_whiteboard(state, planner, "fail")
    if snapshot_rejected:
        log(f"  重複提案 (既存 variant {dup_v} の certified 証拠を拒否)")
    else:
        log(f"  重複提案 (既存 aborted variant {dup_v} と同一 genome)")
    return {"outcome": "aborted", "variant": dup_v,
            "verdict": verdict, "records": recs}


def _refresh_critic_digest(layout: CampaignLayout, *, reflux: bool) -> CertifiedCampaignView:
    """Refresh the existing digest from an admitted view for either CLI route."""
    critic_view = require_admitted_campaign(
        layout.root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    digest_txt = make_critic_digest(
        critic_view,
        tag="p3-s4",
        reflux=reflux,
        identity_projection=make_critic_identity_projection(critic_view),
    )
    layout.ensure()
    with open(os.path.join(layout.root, "s4_loop_digest.txt"), "w", encoding="utf-8") as f:
        f.write(digest_txt)
    return critic_view


def _write_b5_sidecar(directory, name, payload):
    """Publish complete bytes once; serialize publishers before no-clobber rename."""
    root = Path(directory)
    target = root / name
    lock = root / (name + ".publishing")
    lock.mkdir()  # exclusive; interrupted publication fails closed on restart
    temporary = lock / "payload.tmp"
    try:
        if os.path.lexists(target):
            raise FileExistsError(target)
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, target)
        fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary.exists():
            temporary.unlink()
        lock.rmdir()


def _b5_proposal_rejected(directory, slot, exc):
    # Classify the rejecting boundary, never candidate-controlled message text.
    frames = []
    trace = exc.__traceback__
    while trace is not None:
        frames.append(trace.tb_frame.f_code.co_name)
        trace = trace.tb_next
    if "_assert_coder_value_domain" in frames:
        reason = "value-domain"
    elif isinstance(exc, AttributionMismatch):
        reason = "attribution"
    elif isinstance(exc, backoff_hole_grammar.BackoffGrammarViolation):
        reason = "grammar"
    elif isinstance(exc, AbilityProbeMaterialError):
        reason = "probe-material"
    elif "_consume_k2_coder_output" in frames and "validate_schema_instance" not in frames:
        reason = "k2-semantic"
    else:
        reason = "schema"
    payload = {"schema": "p3-s4-loop-b5-proposal-rejected/v1", "b5_slot": slot,
               "reason_class": reason, "exception": type(exc).__name__, "message": str(exc),
               "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if directory is not None:
        _write_b5_sidecar(directory, "proposal-rejected.json", payload)
    return {"outcome": "rejected-preprocess", "reason_class": reason,
            "exception": payload["exception"], "message": payload["message"]}


def _b5_sidecar_payload(cfg, genome, layout=None):
    payload = {
        "schema": "p3-s4-loop-b5-submission/v1",
        "b5_slot": cfg.search_config["b5_slot"],
        "campaign_id": str(ident.campaign_id(cfg)),
        "genome": genome.canonical(),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if layout is not None:
        payload.update(
            schema="p3-s4-loop-b5-slot-start/v1",
            campaign_root=str(Path(layout.root).resolve()),
            identity_preimage_sha256=hashlib.sha256(
                ident.canonical_preimage(cfg).encode("utf-8")).hexdigest(),
        )
    return payload


# One shared, JSON-serializable contract for the child, ledger and consumer.
B5_TIER0_CONTRACT = {
    "contract_id": "b5-tier0/v1",
    "applies_to": ["search", "score"],
    "build": {"trace": False, "count": 1, "inputs": "pipeline._build_one(trace=False)"},
    "smoke_flags": ["--thread_num=4", "--ycsb_tuple_num=200", "--extime=1",
                    "--ycsb_rratio=50", "--ycsb_zipf_skew=0.9", "--ycsb_rmw=true",
                    "--ycsb_max_ope=5"],
    "clocks_per_us": "env_contract.clocks_per_us",
    "numactl": "env_contract.numactl",
    "timeout_s": 32,
    "strict_returncode": True,
    "use_perf": False,
    "pass_conditions": ["rc == 0", "benchparse.integer_abort_commit_counts: commits > 0",
                        "benchparse.throughput_tps (including fallback): finite and > 0"],
    "failure": {"build_exceptions": ["RuntimeError", "subprocess.SubprocessError"],
                "smoke": "candidate", "budget": "A only", "retry": False},
    "smoke_is_performance": False,
}


def _b5_tier0_build_inputs(cfg, genome, sub, build_context, capability_resolver,
                           backoff_grammar_version):
    """Resolve the same evidence and admission as pipeline before the build try."""
    from .build_admission import (GeneratorReceipt,
                                  derive_build_admission, require_build_admission)
    cc, cxx = buildcache.compilers_for_current_site()
    evidence = source_digest.resolve_evidence(
        genome, cfg.ccbench_commit, ccbench_dir=sub, cxx=cxx,
        backoff_grammar_version=backoff_grammar_version,
    )
    capability = capability_resolver(evidence) if capability_resolver is not None else None
    generator = capability if type(capability) is GeneratorReceipt else None
    if capability is not None and generator is None:
        raise BuildAdmissionError(
            "capability_resolver は sealed GeneratorReceipt/None だけを返せる")
    admission = require_build_admission(
        derive_build_admission(build_context, evidence,
                               generator_receipt=generator),
        expected_policy=build_context.policy, expected_source=evidence,
    )
    return evidence, admission, cc, cxx


def _run_b5_tier0_smoke(binary, contract):
    """Diagnostic only: real bounded gateway, parsers and machine-wide lock."""
    import subprocess
    from ..calibrator import benchparse
    from ..calibrator.runner import run_once
    from .lock import bench_lock

    flags = [*B5_TIER0_CONTRACT["smoke_flags"],
             f"--clocks_per_us={contract.clocks_per_us}"]
    timeout_s = B5_TIER0_CONTRACT["timeout_s"]
    smoke = dict(flags=flags, timeout_s=timeout_s, returncode=None, wall_s=None,
                 commits=None, aborts=None, throughput_positive=False)
    returncodes = []
    reason = error = None
    # Waiting for this lock is deliberately outside the subprocess timeout.
    with bench_lock():
        started = time.monotonic()
        try:
            metrics, _counters, wall = run_once(
                binary, flags, numactl=list(contract.numactl), timeout_s=timeout_s,
                strict_returncode=True, use_perf=False, rep_returncodes=returncodes,
            )
            smoke["wall_s"] = wall
            aborts, commits = benchparse.integer_abort_commit_counts(metrics)
            throughput = benchparse.throughput_tps(metrics)
            positive = throughput is not None and math.isfinite(throughput) and throughput > 0
            smoke.update(commits=commits, aborts=aborts, throughput_positive=positive)
            if commits <= 0 or not positive:
                reason = "smoke-failed"
        except subprocess.TimeoutExpired as exc:
            reason, error = "smoke-timeout", f"{type(exc).__name__}: {exc}"
        except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as exc:
            reason, error = "smoke-failed", f"{type(exc).__name__}: {exc}"
        finally:
            smoke["returncode"] = returncodes[-1] if returncodes else None
            if smoke["wall_s"] is None:
                smoke["wall_s"] = time.monotonic() - started
    return {"status": "passed" if reason is None else "rejected",
            "reason": reason, "smoke": smoke, "error": error}


def _machine_proposal_capability_resolver(build_context, proposal_sha256):
    def resolve(evidence):
        if evidence.src_token != source_digest.STOCK:
            return attest_generator_output(
                build_context, evidence,
                generator_input_sha256=hashlib.sha256(
                    (f"p3-s4-loop-machine-proposal/v1|{proposal_sha256}|"
                     f"{evidence.genome_sha256}").encode("utf-8")
                ).hexdigest(),
            )
        return None
    return resolve


def _stock_capability_resolver(build_context: BuildRunContext):
    def resolve(evidence):
        if evidence.src_token == source_digest.STOCK:
            return attest_generator_output(
                build_context, evidence,
                generator_input_sha256=hashlib.sha256(
                    f"p3-s4-loop-stock-control/v1|{evidence.genome_sha256}".encode("utf-8")
                ).hexdigest(),
            )
        return None

    return resolve


def _run_stock_control_resolved(
        cfg: CampaignConfig, perf: PerfConfig, sub: str,
        layout: CampaignLayout,
        contract: env_contract.ExecutionEnvironmentContract,
        resolved_site: str, *, stock_root: str, cache_root: str = "",
        build_context: BuildRunContext,
        dependency_prefix: str = "",
        fetchcontent_base_dir: str = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        fetchcontent_dependency_receipt: Optional[Dict[str, str]] = None,
        b5_sidecar_dir=None, capability_resolver=None, b5_mode=False,
        authorization_session=None,
) -> Dict:
    """Evaluate the adaptive control without constructing or advancing LoopState.

    Only the evaluated attempt's WAL source may establish stock success. A
    terminal skip is not a new control measurement and is never restored here.
    """
    from .patchharness import applied

    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    genome = Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})
    layout.ensure()
    if b5_sidecar_dir is not None:
        _write_b5_sidecar(b5_sidecar_dir, "slot-start.json",
                          _b5_sidecar_payload(cfg, genome, layout))
    ident.ensure_resumable_attempts(
        cfg, layout, admission_policy=build_context.policy,
    )
    backoff_grammar_version = _require_backoff_grammar_version(cfg)
    with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):
        configure_args = ()
        if fetchcontent_dependency_receipt is not None:
            configure_args = _condition_gate_offline_configure_args(
                dependency_prefix=dependency_prefix,
                fetchcontent_base_dir=fetchcontent_base_dir,
                masstree_source_dir=masstree_source_dir,
                mimalloc_source_dir=mimalloc_source_dir,
                googletest_source_dir=googletest_source_dir,
            )
        condition_gate = _require_condition_gate(
            sub, genome, stock_root=stock_root, configure_args=configure_args,
        )
        campaign_options = {}
        if authorization_session is not None:
            campaign_options["authorization_session"] = authorization_session
        if resolved_site == site_policy.PEGASUS_COMPUTE:
            campaign_options["env_contract"] = contract
            if dependency_prefix:
                campaign_options["dependency_prefix"] = dependency_prefix
        if fetchcontent_dependency_receipt is not None:
            campaign_options.update({
                "env_contract": contract,
                "fetchcontent_base_dir": fetchcontent_base_dir,
                "masstree_source_dir": masstree_source_dir,
                "mimalloc_source_dir": mimalloc_source_dir,
                "googletest_source_dir": googletest_source_dir,
                "fetchcontent_dependency_receipt": fetchcontent_dependency_receipt,
            })
        if b5_mode:
            campaign_options["bench_max_rounds"] = 3
        if b5_sidecar_dir is not None:
            _write_b5_sidecar(b5_sidecar_dir, "pipeline-submitted.json",
                              _b5_sidecar_payload(cfg, genome))
        summary = run_campaign(
            cfg, [genome], perf, contract.env_tag, contract.clocks_per_us,
            numactl=list(contract.numactl), ccbench_dir=sub, cache_root=cache_root,
            authorization_contract=env_contract.authorize(contract.env_tag),
            build_context=build_context, declared_use_class=DECLARED_USE_CLASS,
            backoff_grammar_version=backoff_grammar_version,
            capability_resolver=_stock_capability_resolver(build_context),
            **campaign_options,
        )
    out = {"outcome": "identity-skipped", "condition_gate": condition_gate}
    if summary.results:
        r = summary.results[0]
        records = wal.records_by_stage(layout, r.variant)
        is_stock = (
            r.variant == variant_id(genome)
            and records.get(STAGE_BUILD_START, {}).get("src_token") == source_digest.STOCK
        )
        outcome = "aborted"
        if r.certified and not r.aborted:
            outcome = "certified-stock" if is_stock else "non-stock-source"
        out.update(outcome=outcome, variant=r.variant,
                   fitness_tps=r.fitness_tps, verdict=r.verdict, records=records)
    elif summary.skipped > 0:
        out["outcome"] = "skipped"
        if summary.skipped_variants:
            out["variant"] = summary.skipped_variants[0]

    if out["outcome"] != "skipped" and any(wal.read_records(layout)):
        _refresh_critic_digest(
            layout, reflux=cfg.search_config.get("reflux") == "on",
        )
    return out


def _run_one_iteration_resolved(
        cfg: CampaignConfig, perf: PerfConfig,
        planner: PlannerProposal, coder: CoderProposal,
        state: LoopState, sub: str, do_build: bool,
        layout: CampaignLayout,
        contract: env_contract.ExecutionEnvironmentContract,
        resolved_site: str, log=print, cache_root: str = "",
        dependency_prefix: str = "",
        fetchcontent_base_dir: str = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        fetchcontent_dependency_receipt: Optional[Dict[str, str]] = None,
        build_context: Optional[BuildRunContext] = None,
        _b4_launch_context=None, *,
        b5_sidecar_dir=None, capability_resolver=None, b5_mode=False,
        authorization_session=None,
) -> Dict:
    """実 site/contract/layout を公開 API で一度だけ解決した後の内部実装。

    do_build=True: applied(TEMPLATE_PATCH) 下で挿入→検疫→(pass なら)run_campaign。
    do_build=False: 挿入→検疫のみ (配線 dry-run、build/verify/bench を省く)。

    `cache_root` (段5 git worktree 隔離): `sub` が呼び手の `patchharness.checkout()` で
    作った使い捨て worktree の場合、build 出力だけは固定共有パス配下に据え置きたい
    呼び手が明示する (省略時は `sub` 直下 = 従来動作と完全互換)。ccbench_dir は常に
    `sub` そのもの (patch/coder 編集がある実際の tree を build に使う)。

    Returns: {"outcome": rejected|certified|aborted|dry-pass, "variant": ..., ...}。
    """
    if cfg.search_config.get(B4_PROTOCOL_KEY) == B4_PROTOCOL_VALUE:
        from .p3_b4_launcher import require_b4_production_context
        require_b4_production_context(
            _b4_launch_context,
            expected_driver_kind=b4_driver_kind_from_identity(
                search_tag=cfg.search_tag,
                trial=cfg.trial,
                axis=cfg.search_config.get("axis"),
            ),
            expected_campaign_id=str(ident.campaign_id(cfg)),
            expected_arm=cfg.search_config.get("reflux"),
            boundary="base resolved run_one_iteration",
        )
    from .patchharness import applied
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    backoff_grammar_version = _require_backoff_grammar_version(cfg)
    preflight_decision = backoff_hole_grammar.validate_backoff_preflight(
        coder.implementation
    )
    if b5_mode and not preflight_decision.accepted and type(coder.implementation) is not str:
        return _b5_proposal_rejected(
            b5_sidecar_dir, cfg.search_config["b5_slot"],
            backoff_hole_grammar.BackoffGrammarViolation(preflight_decision))
    preflight_rejection = None
    if not preflight_decision.accepted and type(coder.implementation) is str:
        value_decision = backoff_hole_grammar.validate_backoff_value(coder.value)
        if value_decision.accepted:
            preflight_rejection = _backoff_grammar_rejection(
                preflight_decision, source_rel=SOURCE_REL, marker_id=MARKER_ID,
            )
    # 帰属整合の機械強制 (D39 決定7): value と hole literal が食い違うと certified fitness が
    # genome{BACKOFF_FIXED=value} に紐付くのに binary は別 literal で走り帰属が汚染される (規律6)。
    # 全文法は帰属を実行するかだけを決め、外側の rejection 選択は quarantine に委ねる。
    # type/raw-size preflight と value の無損失整数検査は正本への adapter 経由で先に走る。
    # materialization と int() は固定上限内・検証済みの値にしか到達させない。
    if preflight_rejection is None:
        try:
            _check_attribution_before_quarantine(coder)
        except (AttributionMismatch, backoff_hole_grammar.BackoffGrammarViolation) as exc:
            if not b5_mode:
                raise
            return _b5_proposal_rejected(
                b5_sidecar_dir, cfg.search_config["b5_slot"], exc)
    genome = Genome("silo", {**_BASE, "BACK_OFF": 1,
                             "BACKOFF_FIXED": int(coder.value)})
    layout.ensure()
    # reject も campaign の初回 WAL write なので、repair 無しの recovery seam を先行する。
    ident.ensure_resumable_attempts(
        cfg, layout, admission_policy=build_context.policy,
    )

    if preflight_rejection is not None:
        variant = record_diff_reject(
            layout, genome, coder.implementation, preflight_rejection,
            env_tag=contract.env_tag,
            backoff_grammar_version=backoff_grammar_version,
        )
        project_whiteboard(state, planner, "rejected")
        if do_build:
            log(
                f"  diff 検疫 reject: {preflight_rejection.subtype} — "
                f"{preflight_rejection.reason}"
            )
        return {
            "outcome": "rejected", "variant": variant,
            "digest": preflight_rejection.digest,
        }

    if not do_build:
        # dry-run: 骨格を一時適用せず、骨格入りソースを合成して検疫だけ試す経路は
        # 実 working-tree を汚さない (test 用)。ここでは applied を通す本経路を使う。
        with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):
            res, _b, _e, _d = quarantine(sub, coder.implementation, write=False)
        if not res.passed:
            v = record_diff_reject(
                layout, genome, coder.implementation, res,
                env_tag=contract.env_tag,
                backoff_grammar_version=backoff_grammar_version,
            )
            project_whiteboard(state, planner, "rejected")
            return {"outcome": "rejected", "variant": v, "digest": res.digest}
        return {"outcome": "dry-pass", "variant": None}

    with applied(os.path.join(_repo_root(), TEMPLATE_PATCH), PIN, sub):
        res, _b, _e, _d = quarantine(sub, coder.implementation, write=True)
        if not res.passed:
            v = record_diff_reject(
                layout, genome, coder.implementation, res,
                env_tag=contract.env_tag,
                backoff_grammar_version=backoff_grammar_version,
            )
            project_whiteboard(state, planner, "rejected")
            log(f"  diff 検疫 reject: {res.subtype} — {res.reason}")
            return {"outcome": "rejected", "variant": v, "digest": res.digest}
        if fetchcontent_dependency_receipt is None:
            condition_gate = _require_condition_gate(sub, genome)
        else:
            condition_gate = _require_condition_gate(
                sub, genome,
                configure_args=_condition_gate_offline_configure_args(
                    dependency_prefix=dependency_prefix,
                    fetchcontent_base_dir=fetchcontent_base_dir,
                    masstree_source_dir=masstree_source_dir,
                    mimalloc_source_dir=mimalloc_source_dir,
                    googletest_source_dir=googletest_source_dir,
                ),
            )
        # 検疫通過 → build×2 / verify / bench を run_campaign に委譲。coder 編集は
        # working-tree にあり source_digest.resolve が preprocess 後 digest で src_token を
        # 非 stock に上げる。genome の BACKOFF_FIXED と hole literal を coder.value で揃える。
        campaign_options = {}
        if authorization_session is not None:
            campaign_options["authorization_session"] = authorization_session
        if resolved_site == site_policy.PEGASUS_COMPUTE:
            campaign_options["env_contract"] = contract
            if dependency_prefix:
                campaign_options["dependency_prefix"] = dependency_prefix
        if fetchcontent_dependency_receipt is not None:
            campaign_options.update({
                "env_contract": contract,
                "fetchcontent_base_dir": fetchcontent_base_dir,
                "masstree_source_dir": masstree_source_dir,
                "mimalloc_source_dir": mimalloc_source_dir,
                "googletest_source_dir": googletest_source_dir,
                "fetchcontent_dependency_receipt": (
                    fetchcontent_dependency_receipt
                ),
            })
        if b5_mode:
            campaign_options["bench_max_rounds"] = 3
            import subprocess
            # Preparation failures are not candidate build failures.
            evidence, admission, cc, cxx = _b5_tier0_build_inputs(
                cfg, genome, sub, build_context, capability_resolver,
                backoff_grammar_version,
            )
            tier0 = dict(status="rejected", reason="build-error", build=None,
                         smoke=None, error=None)
            try:
                if "env_contract" in campaign_options:
                    build_options = {}
                    if campaign_options.get("dependency_prefix"):
                        build_options["dependency_prefix"] = campaign_options["dependency_prefix"]
                    if fetchcontent_dependency_receipt is not None:
                        build_options.update(
                            fetchcontent_base_dir=fetchcontent_base_dir,
                            masstree_source_dir=masstree_source_dir,
                            mimalloc_source_dir=mimalloc_source_dir,
                            googletest_source_dir=googletest_source_dir,
                            fetchcontent_dependency_receipt=fetchcontent_dependency_receipt,
                        )
                    pf = buildcache.build_v2(
                        genome, trace=False, contract=campaign_options["env_contract"],
                        ccbench_commit=cfg.ccbench_commit, src_token=evidence.src_token,
                        cc=cc, cxx=cxx, ccbench_dir=sub,
                        cache_root=cache_root or os.path.join(buildcache._ccbench_dir(), "build-variants"),
                        admission=admission, build_context=build_context, source_evidence=evidence,
                        declared_use_class=DECLARED_USE_CLASS,
                        backoff_grammar_version=backoff_grammar_version, **build_options,
                    )
                else:
                    pf = buildcache.build(
                        genome, cfg.ccbench_commit, trace=False, src_token=evidence.src_token,
                        ccbench_dir=sub, cache_root=cache_root,
                        admission=admission, build_context=build_context, source_evidence=evidence,
                        backoff_grammar_version=backoff_grammar_version,
                    )
            except (RuntimeError, subprocess.SubprocessError) as exc:
                tier0["error"] = f"{type(exc).__name__}: {exc}"
            else:
                tier0["build"] = dict(trace=False, binary=pf.binary,
                                      bin_sha256=pf.bin_sha256, cached=pf.cached)
                tier0.update(_run_b5_tier0_smoke(pf.binary, contract))
            _write_b5_sidecar(
                b5_sidecar_dir, "tier0.json",
                {**_b5_sidecar_payload(cfg, genome), "schema": "p3-s4-loop-b5-tier0/v1",
                 "contract": B5_TIER0_CONTRACT, **tier0},
            )
            if tier0["status"] != "passed":
                return {"outcome": "rejected-tier0", "variant": None,
                        "condition_gate": condition_gate}
        if b5_sidecar_dir is not None:
            _write_b5_sidecar(b5_sidecar_dir, "pipeline-submitted.json",
                              _b5_sidecar_payload(cfg, genome))
        if capability_resolver is not None:
            campaign_options["capability_resolver"] = capability_resolver
        summary = run_campaign(
            cfg, [genome], perf, contract.env_tag, contract.clocks_per_us,
            numactl=list(contract.numactl), log=log,
            ccbench_dir=sub, cache_root=cache_root,
            authorization_contract=env_contract.authorize(contract.env_tag),
            build_context=build_context,
            declared_use_class=DECLARED_USE_CLASS,
            backoff_grammar_version=backoff_grammar_version,
            **campaign_options,
        )
    if b5_mode and summary.skipped > 0:
        project_whiteboard(state, planner, "fail")
        return {"outcome": "duplicate-skip", "variant": None, "records": {},
                "condition_gate": condition_gate}
    v = next((r.variant for r in summary.results), None)
    if v is None and summary.skipped > 0:
        duplicate = _resolve_duplicate(layout, planner, state, summary, log=log)
        duplicate["condition_gate"] = condition_gate
        return duplicate
    recs = wal.records_by_stage(layout, v) if v else {}
    r = summary.results[0] if summary.results else None
    if r and r.certified and not r.aborted:
        project_whiteboard(state, planner, "success", delta_pct=None)  # 段 6 予約 (率算出は統計的 delta とセット、D39 残存リスク c)
        return {"outcome": "certified", "variant": v, "fitness_tps": r.fitness_tps,
                "verdict": r.verdict, "records": recs,
                "condition_gate": condition_gate}
    project_whiteboard(state, planner, "fail")
    return {"outcome": "aborted", "variant": v,
            "verdict": (r.verdict if r else ""), "records": recs,
            "condition_gate": condition_gate}


def run_one_iteration(cfg: CampaignConfig, perf: PerfConfig,
                      planner: PlannerProposal, coder: CoderProposal,
                      state: LoopState, sub: str, do_build: bool,
                      layout: Optional[CampaignLayout] = None, log=print,
                      cache_root: str = "",
                      build_context: Optional[BuildRunContext] = None,
                      _b4_launch_context=None, *,
                      dependency_prefix: str = "") -> Dict:
    """site と environment contract を解決して 1 iteration の機械部分を回す。"""
    if cfg.search_config.get(B4_PROTOCOL_KEY) == B4_PROTOCOL_VALUE:
        from .p3_b4_launcher import require_b4_production_context
        require_b4_production_context(
            _b4_launch_context,
            expected_driver_kind=b4_driver_kind_from_identity(
                search_tag=cfg.search_tag,
                trial=cfg.trial,
                axis=cfg.search_config.get("axis"),
            ),
            expected_campaign_id=str(ident.campaign_id(cfg)),
            expected_arm=cfg.search_config.get("reflux"),
            boundary="base run_one_iteration",
        )
    resolved_site = _current_site()
    contract = _admit_env_contract(resolved_site)
    campaign_cfg = _campaign_cfg_for_site(
        cfg, resolved_site, _contract=contract,
    )
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    campaign_cfg = ident.bind_admission_policy(campaign_cfg, build_context.policy)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(campaign_cfg)))
    elif do_build and layout.root != exploration_campaign_layout(
            str(ident.campaign_id(campaign_cfg))).root:
        # build 経路は run_campaign が cfg 由来 layout に WAL を書く — 注入 layout がそれと食い違うと
        # WAL と reject/records/digest が分裂する。build 時は一致を強制 (production は layout=None
        # ゆえ常に一致。注入は dry/test 専用の hermetic 化、監査 2026-07-08)。
        raise ValueError(
            f"build 経路の layout 注入は cfg 由来と一致必須 (WAL 分裂防止): "
            f"{layout.root} != cfg 由来"
        )
    return _run_one_iteration_resolved(
        campaign_cfg, perf, planner, coder, state, sub, do_build,
        layout, contract, resolved_site, log=log, cache_root=cache_root,
        dependency_prefix=dependency_prefix,
        build_context=build_context,
        _b4_launch_context=_b4_launch_context,
    )


# ==== 段 4b 駆動口 (実 planner/coder proposal を受けて 1 iteration を継続) =========

def b4_reflux_ablation_mode(cfg: CampaignConfig) -> bool:
    """Classify only the absent or exact protocol marker; reject every alias."""
    if B4_PROTOCOL_KEY not in cfg.search_config:
        return False
    marker = cfg.search_config[B4_PROTOCOL_KEY]
    if marker != B4_PROTOCOL_VALUE:
        raise B4ProtocolError("B-4 protocol marker has an unrecognized value")
    return True


def b4_bootstrap(state: LoopState) -> bool:
    """The only B-4 synthesis that has no preceding critic decision."""
    return state.iteration == 0 and not state.whiteboard


def require_b4_bootstrap_history_empty(
    layout: CampaignLayout,
    state: LoopState,
) -> None:
    """Reject checkpoint bootstrap claims that contradict admitted history."""
    if not b4_bootstrap(state):
        return
    if not wal.wal_bytes_present(layout):
        return
    records = wal.read_records(layout)
    if not records:
        raise B4ProtocolError(
            "B-4 bootstrap conflicts with non-empty campaign WAL bytes"
        )
    history = require_admitted_campaign(
        layout.root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    if history.records:
        raise B4ProtocolError(
            "B-4 bootstrap conflicts with non-empty admitted campaign history"
        )


def b4_terminal_receipt_sha256(path: str | os.PathLike[str]) -> str:
    try:
        receipt_bytes = Path(path).read_bytes()
    except (TypeError, OSError) as exc:
        raise B4ProtocolError("B-4 terminal receipt bytes are unavailable") from exc
    return hashlib.sha256(receipt_bytes).hexdigest()


def require_b4_iteration_authorization(
    cfg: CampaignConfig,
    layout: CampaignLayout,
    state: LoopState,
    *,
    do_build: bool,
    terminal_receipt_path: str | os.PathLike[str] | None,
) -> B4IterationAuthorization | None:
    """Apply the shared B-4 mode, bootstrap, no-build, layout, and receipt gate."""
    if not b4_reflux_ablation_mode(cfg):
        if terminal_receipt_path is not None:
            raise B4ProtocolError("a B-4 receipt requires the exact protocol marker")
        return None
    if not do_build:
        raise B4ProtocolError("B-4 protocol forbids --no-build")
    authoritative = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    if Path(layout.root).resolve() != Path(authoritative.root).resolve():
        raise B4ProtocolError("B-4 driver layout is not authoritative for live cfg")
    if b4_bootstrap(state):
        if terminal_receipt_path is not None:
            raise B4ProtocolError("B-4 bootstrap rejects a closed critic receipt")
        return B4IterationAuthorization(receipt=None, terminal_receipt_sha256=None)
    if terminal_receipt_path is None:
        raise B4ProtocolError("B-4 continuation requires a closed critic receipt")

    before_sha256 = b4_terminal_receipt_sha256(terminal_receipt_path)
    # Local import avoids p3_s4_loop <-> p3_b4_closed_critic import recursion.
    from .p3_b4_closed_critic import require_b4_closed_critic_receipt
    receipt = require_b4_closed_critic_receipt(
        terminal_receipt_path,
        cfg=cfg,
        layout=layout,
    )
    after_sha256 = b4_terminal_receipt_sha256(terminal_receipt_path)
    if before_sha256 != after_sha256:
        raise B4ProtocolError("B-4 terminal receipt changed during verification")
    return B4IterationAuthorization(
        receipt=receipt,
        terminal_receipt_sha256=after_sha256,
    )


def consume_b4_iteration_authorization(
    authorization: B4IterationAuthorization,
) -> Path | None:
    """Atomically publish the at-most-once record in the rebuilt live layout."""
    if authorization.receipt is None:
        return None
    receipt = authorization.receipt
    receipt_sha256 = authorization.terminal_receipt_sha256
    if type(receipt_sha256) is not str:
        raise B4ProtocolError("B-4 authorization has no terminal receipt hash")
    record = {
        "terminal_receipt_sha256": receipt_sha256,
        "campaign_id": receipt.campaign_id,
        "arm": receipt.arm,
        "iteration": receipt.iteration,
        "pair_id": receipt.pair_id,
        "decision_sha256": receipt.decision_sha256,
    }
    from .s8b_prediction_runner import _canonical_json_bytes
    record_bytes = _canonical_json_bytes(record)
    authoritative_layout = exploration_campaign_layout(receipt.campaign_id)
    record_root = Path(authoritative_layout.root)
    record_path = record_root / (
        f"b4_closed_critic_consumption_{receipt_sha256}.json"
    )
    temp_path = record_root / (
        f".{record_path.name}.tmp-{os.getpid()}-{os.urandom(16).hex()}"
    )
    published = False
    complete = False
    try:
        _write_b4_consumption_temp(temp_path, record_bytes)
        try:
            os.link(temp_path, record_path, follow_symlinks=False)
            published = True
        except FileExistsError as exc:
            raise B4ProtocolError(
                "B-4 terminal receipt was already consumed"
            ) from exc
        except OSError as exc:
            raise B4ProtocolError(
                "B-4 receipt consumption record publish failed"
            ) from exc
        _fsync_b4_consumption_directory(record_root)
        temp_path.unlink()
        _fsync_b4_consumption_directory(record_root)
        complete = True
    except B4ProtocolError:
        raise
    except OSError as exc:
        raise B4ProtocolError(
            "B-4 receipt consumption record write failed"
        ) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        if published and not complete:
            try:
                record_path.unlink(missing_ok=True)
                _fsync_b4_consumption_directory(record_root)
            except OSError:
                pass
    return record_path


def _write_b4_consumption_temp(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def _fsync_b4_consumption_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fold_critic_reverse(state: LoopState, prior_critic_reverse: Optional[bool]) -> None:
    """前 iteration の critic feedback (逆方向推奨だったか) を reverse_recommendations に畳む。

    critic 帰属の消費はメインセッションの職務 (Model Y、D39 決定2/7) — 本 harness は critic の
    自然文帰属を読まず、「逆方向を推奨したか否か」の bool だけを受け取り機械カウンタに反映する
    (機序を harness に持ち込まない = whiteboard 射影と同じ規律2/6)。True → +1 (逆方向推奨の連続)、
    False → 0 リセット (順方向路線が続く)、None → 変更なし (iteration 1 入口 or feedback 未供給)。"""
    if prior_critic_reverse is True:
        state.reverse_recommendations += 1
    elif prior_critic_reverse is False:
        state.reverse_recommendations = 0


def _consume_k2_coder_output(
    result: Dict[str, Any],
    projected_input: Dict[str, Any],
) -> Dict[str, Any]:
    """K2 role の論理出力を schema、anomaly、semantic の順で検査する。"""
    from orchestrator.codex_roles.events import validate_schema_instance
    from orchestrator.codex_roles.policy import validate_output_semantics
    from orchestrator.codex_roles.spec import get_role_spec

    spec = get_role_spec("coder-v4-autonomous-k2")
    validate_schema_instance(
        result, spec.output_schema, label="coder-v4-autonomous-k2 output",
    )
    proposal = result["proposal"]
    knowledge_use = result["knowledge_use"]
    classification = result["classification"]
    data_boundary_report = result["data_boundary_report"]
    del knowledge_use, classification
    if data_boundary_report["instruction_like_content_detected"] is True:
        raise ValueError(
            "coder-v4-autonomous-k2 が instruction-like content を申告した"
        )
    validate_output_semantics(
        "coder-v4-autonomous-k2", projected_input, result,
    )
    return proposal


def load_proposal_file(
    path: str,
    *,
    b4_reflux_ablation: bool = False,
    b4_closed_critic_receipt_sha256: str | None = None,
    b4_prerun_publication: str | os.PathLike[str] | None = None,
    b4_attempt_id: str | None = None,
    knowledge_input: Optional[Dict[str, Any]] = None,
    coder_role: str | None = None,
    capture: dict | None = None,
) -> Tuple[PlannerProposal, CoderProposal, Optional[bool]]:
    """メインセッションが spawn した planner/coder の構造化出力 (+ 前 critic の逆方向 bool) を
    JSON ファイルから読む。schema:

        {"planner": {axis, direction, magnitude, justification?, uncertainty?},
         "coder":   {axis, value, implementation, justification?, confidence?},
         "prior_critic_reverse": true|false|null}

    Model Y の入力射影点 — メインセッションはここに **abstract な proposal だけ** を書く
    (勝ち筋値・機序を harness へ運ぶ経路にしない)。value 値域は CoderProposal
    構築時、value↔literal 整合は run_one_iteration が機械強制する (D39 決定7)。"""
    with open(path, "rb") as f:
        proposal_bytes = f.read()
    proposal_text = proposal_bytes.decode("utf-8")
    if (
        knowledge_input is not None
        and coder_role == "coder-v4-autonomous-k2"
    ):
        d = json.loads(
            proposal_text,
            object_pairs_hook=knowledge_manifest._reject_duplicate_keys,
        )
    else:
        d = json.loads(proposal_text)
    schema_document = d
    if b4_reflux_ablation:
        if "prior_critic_reverse" in d:
            raise B4ProtocolError(
                "B-4 proposal must not self-report prior_critic_reverse"
            )
        has_receipt_binding = B4_PROPOSAL_RECEIPT_SHA256_KEY in d
        if b4_closed_critic_receipt_sha256 is None:
            if has_receipt_binding:
                raise B4ProtocolError(
                    "B-4 bootstrap proposal must not claim a critic receipt"
                )
        else:
            claimed = d.get(B4_PROPOSAL_RECEIPT_SHA256_KEY)
            if type(claimed) is not str or claimed != b4_closed_critic_receipt_sha256:
                raise B4ProtocolError(
                    "B-4 proposal receipt hash differs from terminal receipt bytes"
                )
        schema_document = dict(d)
        schema_document.pop(B4_PROPOSAL_RECEIPT_SHA256_KEY, None)
    elif b4_closed_critic_receipt_sha256 is not None:
        raise B4ProtocolError("proposal receipt binding requires B-4 mode")
    has_knowledge_input = knowledge_input is not None
    has_coder_role = coder_role is not None
    if has_knowledge_input != has_coder_role:
        raise ValueError(
            "knowledge_input と coder_role は両方指定するか両方省略する必要がある"
        )
    k2_contract = has_knowledge_input and has_coder_role
    if k2_contract and coder_role != "coder-v4-autonomous-k2":
        raise ValueError("K2 proposal loader の coder_role が不正")
    if k2_contract:
        assert_closed_proposal_schema(
            schema_document,
            require_auditor=False,
            require_coder_value=True,
            coder_contract=CODER_CONTRACT_K2,
        )
    else:
        assert_closed_proposal_schema(
            schema_document, require_auditor=False, require_coder_value=True,
        )
    has_prerun_binding = (
        b4_prerun_publication is not None or b4_attempt_id is not None
    )
    if b4_reflux_ablation and b4_closed_critic_receipt_sha256 is None:
        require_b4_proposal_registry_binding(
            b4_prerun_publication,
            b4_attempt_id,
            schema_document,
            driver_kind="base",
        )
    elif has_prerun_binding:
        if b4_reflux_ablation:
            raise B4ProtocolError(
                "B-4 prerun proposal binding is bootstrap-only"
            )
        raise B4ProtocolError(
            "B-4 prerun proposal binding requires B-4 bootstrap mode"
        )
    p, c = d["planner"], d["coder"]
    if k2_contract:
        assert knowledge_input is not None
        c = _consume_k2_coder_output(
            c,
            {
                "knowledge_input": knowledge_input,
                "planner_direction": p,
            },
        )
    planner = PlannerProposal(
        axis=p["axis"], direction=p["direction"], magnitude=p["magnitude"],
        justification=p.get("justification", ""), uncertainty=p.get("uncertainty", ""))
    coder = CoderProposal(
        axis=c["axis"], value=c["value"], implementation=c["implementation"],
        justification=c.get("justification", ""), confidence=c.get("confidence", "medium"))
    # prior_critic_reverse は null か bool のみを許す。非 bool (文字列 "true"・整数 1 等) は
    # _fold_critic_reverse の `is True`/`is False` で黙って no-op し reverse-exhausted の停止
    # フィードバックが fail-open する — planner/coder の必須キーと同じく fail-closed にする
    # (schema 検証を片方だけ緩めない、規律2、監査 2026-07-08)。
    prior = None if b4_reflux_ablation else d.get("prior_critic_reverse")
    if prior is not None and not isinstance(prior, bool):
        raise ValueError(f"prior_critic_reverse は null か bool のみ (got {type(prior).__name__}: "
                         f"{prior!r}) — 非 bool は停止フィードバックを fail-open させる (規律2)")
    assert_no_ability_probe_material(d)
    if capture is not None:
        capture.update(proposal_bytes=proposal_bytes, proposal_document=d,
                       planner_output=d["planner"],
                       coder_output=d["coder"])
    return planner, coder, prior


def drive_iteration(cfg: CampaignConfig, perf: PerfConfig,
                    planner: PlannerProposal, coder: CoderProposal,
                    prior_critic_reverse: Optional[bool], sub: str, do_build: bool,
                    layout: Optional[CampaignLayout] = None, log=print,
                    cache_root: str = "",
                    build_context: Optional[BuildRunContext] = None,
                    b4_closed_critic_receipt: str | os.PathLike[str] | None = None,
                    b4_proposal_receipt_sha256: str | None = None,
                    _b4_launch_context=None, *,
                    b5_sidecar_dir=None, capability_resolver=None, b5_mode=False,
                    authorization_session=None,
                    agent_record: dict | None = None,
                    initial_proposal_sha256: str | None = None,
                    dependency_prefix: str = "",
                    fetchcontent_base_dir: str = "",
                    masstree_source_dir: Optional[object] = None,
                    mimalloc_source_dir: Optional[object] = None,
                    googletest_source_dir: Optional[object] = None,
                    fetchcontent_dependency_receipt: Optional[
                        Dict[str, str]
                    ] = None,
                    _resolved_site: Optional[str] = None,
                    _contract: Optional[
                        env_contract.ExecutionEnvironmentContract
                    ] = None) -> Dict:
    """段 4b の 1 iteration をメインセッション駆動で回す (checkpoint 経由の cross-process 継続)。

    手順: checkpoint 復元 (無ければ start_wall 付き初期化) → 前 critic feedback 畳込み →
    **入口 check_stop** (逆方向枯渇/予算/収束を iteration 消費前に判定 = 無駄打ちしない。停止なら
    run_one_iteration を呼ばない = build/verify/bench に進めない) → iteration++ →
    run_one_iteration → provenance 公開 → checkpoint 保存 → admitted outcome だけ digest 書き出し → 末尾
    check_stop (新 whiteboard を反映した収束判定) を返す。dry-pass は配線確認だけで WAL が
    無いため digest を作らない。checkpoint は各 iteration で atomic 更新する。

    Returns: run_one_iteration の dict + {"stop_reason", "iteration", "ran"}。ran=False は
    入口停止 (iteration 未消費) を表す。"""
    _assert_coder_value_domain(coder.value)
    if _resolved_site is None and _contract is None:
        resolved_site = _current_site()
        contract = _admit_env_contract(resolved_site)
    elif _resolved_site is None or _contract is None:
        raise TypeError("resolved site と contract は同時に渡す必要がある")
    else:
        resolved_site = _resolved_site
        contract = _contract
        if not _site_admits_measurement(resolved_site):
            raise execution_guard.ExecutionGuardError(
                f"計測用 env bytes は site={resolved_site!r} では生成できない"
            )
        if contract.env_tag != _SITE_ENV_TAGS[resolved_site]:
            raise execution_guard.ExecutionGuardError(
                "解決済み site と environment contract の env_tag が一致しない"
            )
    cfg = _campaign_cfg_for_site(cfg, resolved_site, _contract=contract)
    if build_context is None and not do_build:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    if layout is None:
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    _load_provenance(layout)
    if initial_proposal_sha256 is not None and (
            type(initial_proposal_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", initial_proposal_sha256) is None):
        raise ValueError("initial_proposal_sha256 must be lowercase SHA-256 or None")
    b4_mode = b4_reflux_ablation_mode(cfg)
    if b4_mode:
        from .p3_b4_launcher import require_b4_production_context
        require_b4_production_context(
            _b4_launch_context,
            expected_driver_kind=b4_driver_kind_from_identity(
                search_tag=cfg.search_tag,
                trial=cfg.trial,
                axis=cfg.search_config.get("axis"),
            ),
            expected_campaign_id=str(ident.campaign_id(cfg)),
            expected_arm=cfg.search_config.get("reflux"),
            boundary="base drive_iteration",
        )
        state = load_loop_state(layout)
        if state is None:
            state = LoopState(start_wall=time.time())
        require_b4_bootstrap_history_empty(layout, state)
        authorization = require_b4_iteration_authorization(
            cfg,
            layout,
            state,
            do_build=do_build,
            terminal_receipt_path=b4_closed_critic_receipt,
        )
        assert authorization is not None
        if prior_critic_reverse is not None:
            raise B4ProtocolError(
                "B-4 driver rejects self-reported prior_critic_reverse"
            )
        if authorization.terminal_receipt_sha256 != b4_proposal_receipt_sha256:
            raise B4ProtocolError(
                "B-4 proposal is not bound to the verified terminal receipt"
            )
        if authorization.receipt is not None:
            prior_critic_reverse = (
                authorization.receipt.decision_reverse_recommended
            )
        consume_b4_iteration_authorization(authorization)
    else:
        if (
            b4_closed_critic_receipt is not None
            or b4_proposal_receipt_sha256 is not None
        ):
            raise B4ProtocolError("B-4 receipt inputs require the exact protocol marker")
        state = None
    layout.ensure()
    if b5_sidecar_dir is not None:
        genome = Genome("silo", {**_BASE, "BACK_OFF": 1,
                                 "BACKOFF_FIXED": int(coder.value)})
        _write_b5_sidecar(b5_sidecar_dir, "slot-start.json",
                          _b5_sidecar_payload(cfg, genome, layout))
    ident.ensure_resumable_attempts(
        cfg, layout, admission_policy=build_context.policy,
    )
    if state is None:
        state = load_loop_state(layout)
        if state is None:
            state = LoopState(start_wall=time.time())
    _fold_critic_reverse(state, prior_critic_reverse)

    pre = check_stop(state)
    if pre.stop:
        save_loop_state(layout, state)
        log(f"  入口停止 (iteration 消費せず): {pre.reason}")
        return {"outcome": "stopped-before", "variant": None,
                "stop_reason": pre.reason, "iteration": state.iteration, "ran": False}

    if agent_record is not None:
        _append_live_agent_outputs(layout, cfg, agent_record)

    state.iteration += 1
    # 同一 layout を run_one_iteration に渡す — reject WAL/records と checkpoint/digest を
    # co-locate させ layout 分裂 (digest 空) を防ぐ (監査 2026-07-08)。
    out = _run_one_iteration_resolved(
        cfg, perf, planner, coder, state, sub, do_build,
        layout, contract, resolved_site, log=log, cache_root=cache_root,
        dependency_prefix=dependency_prefix,
        fetchcontent_base_dir=fetchcontent_base_dir,
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
        fetchcontent_dependency_receipt=fetchcontent_dependency_receipt,
        build_context=build_context,
        _b4_launch_context=(_b4_launch_context if b4_mode else None),
        **({"authorization_session": authorization_session}
           if authorization_session is not None else {}),
        **({"b5_sidecar_dir": b5_sidecar_dir, "b5_mode": b5_mode,
            "capability_resolver": capability_resolver}
           if b5_mode or b5_sidecar_dir is not None or capability_resolver is not None else {}),
    )
    _append_provenance_entry(layout, state.iteration, {
        "iteration": state.iteration,
        "initial_proposal_sha256": initial_proposal_sha256,
        "outcome": out["outcome"],
        **_wal_attempt_provenance(layout, out),
    })
    save_loop_state(layout, state)

    if b5_mode and out["outcome"] in {"duplicate-skip", "rejected-preprocess", "rejected-tier0"}:
        post = check_stop(state)
        out.update(stop_reason=post.reason, iteration=state.iteration, ran=True,
                   critic_digest_generated=False)
        return out

    if do_build and out["outcome"] != "dry-pass":
        critic_view = require_admitted_campaign(
            layout.root,
            purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )
        digest_txt = make_critic_digest(
            critic_view,
            tag="p3-s4",
            reflux=(cfg.search_config.get("reflux") == "on"),
            identity_projection=make_critic_identity_projection(critic_view),
        )
        with open(os.path.join(layout.root, "s4_loop_digest.txt"), "w", encoding="utf-8") as f:
            f.write(digest_txt)
        out["critic_digest_generated"] = True
    else:
        # No-build is a wiring-only path, including machine/auditor rejects.
        # Its WAL is useful local evidence but is not an admitted campaign
        # consumer input, so never ask the critic digest to admit it.
        out["critic_digest_generated"] = False

    post = check_stop(state)
    out.update({"stop_reason": post.reason, "iteration": state.iteration, "ran": True})
    return out


def _agent_json(raw: bytes) -> dict:
    value = json.loads(raw.decode("utf-8"),
                       object_pairs_hook=knowledge_manifest._reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError("agent JSON must be an object")
    agent_outputs.canonical_sha256(value)  # reject non-finite JSON
    return value


def _agent_provenance(mode, source_path, source_bytes, input_path, input_bytes,
                      prompt_path=None):
    """Describe recording, not observed generation or proof of input delivery.

    mode is live (harness append before evaluation) or ingested (import output
    produced elsewhere). Envelope ts is recording time; input_sha256 is the
    canonical SHA-256 of saved JSON declared by the caller as actual input.
    prompt_sha256 hashes the specified file bytes. mechanism_hypotheses is LLM
    (critic) attribution, not empirical proof of a mechanism.
    """
    result = {
        "mode": mode, "source_path": str(Path(source_path).resolve()),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "input_path": str(Path(input_path).resolve()),
        "input_file_sha256": hashlib.sha256(input_bytes).hexdigest(),
    }
    if prompt_path is not None:
        prompt = Path(prompt_path).resolve()
        result.update(prompt_path=str(prompt),
                      prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest())
    return result


def _append_live_agent_outputs(layout, cfg, record):
    """Record contains proposal_path/bytes, input_path/bytes, planner_input,
    coder_input, planner_output, coder_output, and optional <role>_prompt_path.
    Both envelopes are checked before the first append; appends are individually
    durable, not a two-record transaction.
    mode describes recording, not observed generation: live appends before
    evaluation; ingested imports output produced elsewhere. ts is recording time.
    input_sha256 hashes canonical saved JSON declared by the caller as actual
    input, not proof of delivery; prompt_sha256 hashes specified file bytes.
    mechanism_hypotheses records LLM (critic) attribution, not mechanism proof.
    """
    # Hash caller-declared saved inputs. This does not prove actual consumption.
    envelopes = []
    for role in ("planner", "coder"):
        envelope = {
            "ts": time.time(), "stage": role + "_proposed", "variant": None,
            "env_tag": cfg.bound_environment_contract.env_tag,
            "payload": {
                "output": record[role + "_output"],
                "input_sha256": agent_outputs.canonical_sha256(record[role + "_input"]),
                "provenance": _agent_provenance(
                    "live", record["proposal_path"], record["proposal_bytes"],
                    record["input_path"], record["input_bytes"],
                    record.get(role + "_prompt_path")),
                "refs": [],
            },
        }
        agent_outputs.validate_envelope(envelope)
        envelopes.append(envelope)
    for envelope in envelopes:
        agent_outputs.append_agent_output(layout.agent_outputs_file, envelope)


def _critic_agent_output(raw: str) -> dict:
    return {"raw_markdown": raw, **agent_outputs.extract_critic_sections(raw)}


def _validate_agent_role_output(stage, output):
    from orchestrator.codex_roles.events import validate_schema_instance
    from orchestrator.codex_roles.spec import get_role_spec

    if stage == "planner_proposed":
        proposal = output.get("proposal") if set(output) == {"proposal"} else output
        if not isinstance(proposal, dict) or set(proposal) != {
                "axis", "direction", "magnitude", "justification", "uncertainty"}:
            raise ValueError("planner output must contain exact five proposal keys")
        if (any(not isinstance(v, str) for v in proposal.values())
                or proposal["direction"] not in ("increase", "decrease", "explore_both")
                or proposal["magnitude"] not in ("small", "medium", "large")):
            raise ValueError("planner proposal value domain violation")
    else:
        validate_schema_instance(output, get_role_spec("coder-v4-autonomous-k2").output_schema,
                                 label="coder K2 output")


def _ingest_agent_output(a):
    stage, source = a.record_agent_output
    if stage not in agent_outputs.STAGES:
        raise ValueError("unknown agent output stage")
    root = Path(a.agent_campaign_dir).resolve()
    layout = CampaignLayout(root=str(root))
    if not root.is_dir() or not Path(layout.lock_file).is_file() or not Path(layout.wal_file).is_file():
        raise ValueError("agent campaign requires existing directory, campaign.lock and runs/wal.jsonl")
    records, truncated = wal.read_records_checked(layout)
    tags = {r.env_tag for r in records}
    if truncated or not records or len(tags) != 1:
        raise ValueError("agent campaign WAL is empty, truncated or has inconsistent env_tag")
    role = stage.split("_", 1)[0]
    if a.agent_output_key is not None and a.agent_output_key != role:
        raise ValueError("stage and --agent-output-key mismatch")
    if role == "critic" and a.agent_output_key is not None:
        raise ValueError("critic forbids --agent-output-key")
    source_bytes = Path(source).read_bytes()
    if role == "critic":
        output = _critic_agent_output(source_bytes.decode("utf-8"))
    else:
        document = _agent_json(source_bytes)
        if a.agent_output_key is None:
            if role == "planner" and set(document) != {"proposal"}:
                raise ValueError("planner role file requires proposal wrapper")
            output = document
        else:
            output = document.get(a.agent_output_key)
            if role == "planner" and isinstance(output, dict) and "proposal" in output:
                raise ValueError("selected planner output requires five proposal keys without wrapper")
        if not isinstance(output, dict):
            raise ValueError("selected role output must be an object")
        _validate_agent_role_output(stage, output)
    input_bytes = Path(a.agent_input).read_bytes()
    declared_input = _agent_json(input_bytes)
    required = {
        "planner": {"current_perf", "leading_indicators", "whiteboard"},
        "coder": {"leakproof_context", "knowledge_input", "baseline", "planner_direction", "whiteboard"},
        "critic": {"digest_sha256"},
    }[role]
    if not required <= set(declared_input):
        raise ValueError(f"{role} input missing required keys: {sorted(required - set(declared_input))}")
    if "knowledge_input" in declared_input:
        knowledge = declared_input["knowledge_input"]
        receipt_path = root / "knowledge_manifest_receipt.json"
        if not receipt_path.is_file():
            raise ValueError("knowledge_input requires campaign knowledge receipt")
        receipt = _agent_json(receipt_path.read_bytes())
        digest = receipt.get("knowledge_manifest_sha256")
        if (not isinstance(knowledge, dict) or not isinstance(digest, str)
                or knowledge.get("knowledge_manifest_sha256") != digest):
            raise ValueError("knowledge_manifest_sha256 differs from campaign receipt")
    variant = a.agent_variant
    if role == "critic" and not variant:
        raise ValueError("critic requires --agent-variant")
    if variant is not None and not any(
            r.variant == variant
            for r in records):
        raise ValueError("agent variant absent from required campaign WAL records")
    refs = a.agent_wal_ref or []
    known_refs = {"wal:" + agent_outputs.canonical_sha256(vars(r)) for r in records}
    if any(ref not in known_refs for ref in refs):
        raise ValueError("agent WAL ref absent from campaign")
    payload = {
        "output": output, "input_sha256": agent_outputs.canonical_sha256(declared_input),
        "provenance": _agent_provenance("ingested", source, source_bytes,
                                        a.agent_input, input_bytes, a.agent_prompt),
        "refs": refs,
    }
    if role == "critic":
        if a.agent_digest is None:
            raise ValueError("critic requires --agent-digest")
        digest = hashlib.sha256(Path(a.agent_digest).read_bytes()).hexdigest()
        campaign_digest = hashlib.sha256((root / "s4_loop_digest.txt").read_bytes()).hexdigest()
        if digest != declared_input["digest_sha256"] or digest != campaign_digest:
            raise ValueError("critic digest_sha256 mismatch with input or campaign digest")
        payload["digest_sha256"] = digest
    elif a.agent_digest is not None:
        raise ValueError("--agent-digest is critic-only")
    envelope = {"ts": time.time(), "stage": stage, "variant": variant,
                "env_tag": next(iter(tags)), "payload": payload}
    agent_outputs.append_agent_output(layout.agent_outputs_file, envelope)
    print(f"agent output recorded: stage={stage} ref={agent_outputs.envelope_ref(envelope)} "
          f"path={layout.agent_outputs_file}")
    return 0


def _run_stock_cli_step(cfg, perf, fixed_sub, cache_root, stock_context,
                        b5_options, fetchcontent_options, resolved_site, contract,
                        *, authorization_session=None):
    from . import patchharness
    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    print(f"=== 段 4 stock control (stock_root={fixed_sub}, isolate_worktree=True) ===")
    with patchharness.checkout(PIN, base_dir=fixed_sub) as sub:
        out = _run_stock_control_resolved(
            cfg, perf, sub, layout, contract, resolved_site,
            stock_root=fixed_sub, cache_root=cache_root,
            build_context=stock_context,
            **({"authorization_session": authorization_session} if authorization_session is not None else {}),
            **b5_options, **fetchcontent_options,
        )
    variant_text = f" variant={out['variant']}" if "variant" in out else ""
    print(f"  outcome={out['outcome']}{variant_text} "
          f"fitness_tps={out.get('fitness_tps')} verdict={out.get('verdict')}")
    print(f"  campaign dir: {layout.root}")
    return 0 if out["outcome"] == "certified-stock" else 1


def main(
    argv: Optional[List[str]] = None,
    *,
    _b4_launch_context=None,
) -> int:
    """fixture proposal で 1 iteration の機械 E2E を実走する (配線実証)。

    実 LLM (planner/coder/critic) はメインセッションが spawn する — 本 main は harness
    の機械経路 (挿入→検疫→評価→WAL→digest→whiteboard→停止判定) が通ることを、人間が
    与えた fixture backoff 値で確認する口。--no-build で build/verify/bench を省く。
    --emit-planner-context は proposal 生成前の planner-v4 入力 JSON を出力する。"""
    ap = argparse.ArgumentParser(description="P3 後続段 4 coder 自律ループ (機械 E2E)")
    ap.add_argument("--b5-slot")
    ap.add_argument("--machine-generated-proposal", action="store_true")
    ap.add_argument("--b5-sidecar-dir", type=Path)
    ap.add_argument("--calibrated-perf", action="store_true")
    ap.add_argument("--perf-workload", choices=("write-heavy", "balanced", "read-heavy"))
    ap.add_argument("--verify-performance", action="store_true")
    ap.add_argument("--stock-control", action="store_true",
                    help="同 campaign の適応 backoff stock 対照を評価")
    ap.add_argument("--no-build", action="store_true",
                    help="build/verify/bench を省き挿入→検疫の配線のみ確認")
    add_registered_coder_build_authority_argument(
        ap,
        coder_entrypoint_site="orchestrator.campaign.p3_s4_loop.main",
    )
    ap.add_argument("--value", type=float, default=20.0,
                    help="fixture の backoff 値 (coder proposal の代わり)")
    ap.add_argument("--reflux", choices=["on", "off"], default="on",
                    help="critic 還流 on/off (LLM ablation の対照アーム)")
    ap.add_argument("--b4-reflux-ablation", action="store_true",
                    help="exact B-4 protocol marker を campaign identity に焼く")
    ap.add_argument("--b4-closed-critic-receipt", type=Path, metavar="PATH",
                    help="B-4 continuation の certified terminal receipt")
    ap.add_argument("--b4-prerun-publication", type=Path, metavar="ROOT",
                    help="B-4 bootstrap の封印済み prerun publication root")
    ap.add_argument("--b4-attempt-id", metavar="ATTEMPT_ID",
                    help="B-4 bootstrap の scheduled attempt identity")
    ap.add_argument("--run-iteration", metavar="PROPOSAL.json",
                    help="段 4b 駆動: 実 planner/coder proposal (JSON) を受けて checkpoint 継続で "
                         "1 iteration を回す (メインセッションが毎 iteration これを呼ぶ)")
    ap.add_argument("--emit-planner-context", metavar="PATH.json",
                    help="proposal 生成前の planner-v4 入力 (whiteboard + 任意の policy_hint) を JSON 出力")
    ap.add_argument("--k2-critic-diagnosis", type=Path, metavar="PATH.md",
                    help="K2手動emit限定: 明示critic逐語を診断データとして射影")
    ap.add_argument("--knowledge-manifest", type=Path, metavar="PATH",
                    help="K2 knowledge manifest (commit/path/raw-byte SHA を検証して条件付き bind)")
    ap.add_argument("--coder-role", choices=("coder-v4-autonomous-k2",),
                    default=None,
                    help="--run-iteration の coder role 契約を明示する")
    ap.add_argument("--knowledge-classification", metavar="TEXT",
                    default="reproduction_or_selection",
                    help="knowledge receipt へ記録する呼び手宣言の候補分類")
    ap.add_argument("--knowledge-de-novo-claim", choices=("true", "false"),
                    default="false",
                    help="knowledge receipt へ記録する呼び手宣言の de novo claim")
    ap.add_argument("--policy-hint", metavar="TEXT", default=None,
                    help="planner-v4 へ渡す任意の policy hint (--emit-planner-context と併用)")
    ap.add_argument("--isolate-worktree", action="store_true",
                    help="段5 git worktree 隔離: 共有 external/ccbench でなく使い捨て "
                         "worktree で apply/build/verify する (既定 OFF = 既存動作と完全互換)")
    ap.add_argument(
        "--fetchcontent-prebuild-receipt",
        type=Path,
        metavar="PATH",
        default=None,
        help="job-local FetchContent prebuild receipt",
    )
    ap.add_argument("--agent-inputs", type=Path)
    ap.add_argument("--agent-prompts", type=Path)
    ap.add_argument("--record-agent-output", nargs=2, metavar=("STAGE", "OUTPUT_FILE"))
    ap.add_argument("--agent-campaign-dir", type=Path)
    ap.add_argument("--agent-input", type=Path)
    ap.add_argument("--agent-output-key", choices=("planner", "coder"))
    ap.add_argument("--agent-variant")
    ap.add_argument("--agent-digest", type=Path)
    ap.add_argument("--agent-wal-ref", nargs="+", action="extend")
    ap.add_argument("--agent-prompt", type=Path)
    # Track explicit actions, including abbreviations and --option=value,
    # without changing the evaluation CLI's historical defaults.
    arguments = list(argv if argv is not None else sys.argv[1:])
    a = ap.parse_args(arguments)
    supplied = set()
    for token in arguments:
        if token.startswith("--"):
            parsed = ap._parse_optional(token)
            if parsed is not None and parsed[0] is not None:
                supplied.add(parsed[0].dest)
    ingestion = {"record_agent_output", "agent_campaign_dir", "agent_input",
                 "agent_output_key", "agent_variant", "agent_digest",
                 "agent_wal_ref", "agent_prompt"}
    if a.record_agent_output is not None:
        if supplied - ingestion:
            ap.error("--record-agent-output cannot be combined with evaluation options")
        if a.agent_campaign_dir is None or a.agent_input is None:
            ap.error("--record-agent-output requires --agent-campaign-dir and --agent-input")
        try:
            return _ingest_agent_output(a)
        except (ValueError, OSError) as exc:
            print(f"agent output recording failed: {exc}", file=sys.stderr)
            return 1
    if supplied & ingestion:
        ap.error("agent ingestion options require --record-agent-output")
    pair_mode = bool(a.run_iteration and a.stock_control)
    stock_only = bool(a.stock_control and not pair_mode)
    if pair_mode:
        for dest in ("value", "emit_planner_context", "no_build",
                     "b4_reflux_ablation", "b5_slot", "machine_generated_proposal"):
            if dest in supplied:
                ap.error(f"pair mode cannot be combined with --{dest.replace('_', '-')}")
    if a.b5_slot is not None:
        if (not a.b5_slot.isascii() or any(c.isspace() for c in a.b5_slot)
                or not a.b5_slot.startswith("b5-generator-contrast-v1|")):
            ap.error("--b5-slot requires nonempty ASCII without whitespace and B-5 prefix")
        if not (a.calibrated_perf and a.perf_workload and a.verify_performance):
            ap.error("--b5-slot requires --calibrated-perf --perf-workload --verify-performance")
        if supplied & {"value", "emit_planner_context", "no_build", "b4_reflux_ablation"}:
            ap.error("--b5-slot conflicts with fixture, emit, no-build or B-4 options")
        if not (a.run_iteration or a.stock_control):
            ap.error("--b5-slot requires --run-iteration or --stock-control")
    if a.machine_generated_proposal:
        if not (a.run_iteration and a.b5_slot):
            ap.error("--machine-generated-proposal requires --run-iteration and --b5-slot")
        if (a.coder_build_authority is not None or a.coder_role is not None
                or a.knowledge_manifest is not None
                or supplied & {"knowledge_classification", "knowledge_de_novo_claim"}):
            ap.error("--machine-generated-proposal conflicts with coder authority and K2 options")
    if a.b5_sidecar_dir is not None:
        if a.b5_slot is None or not a.b5_sidecar_dir.is_dir():
            ap.error("--b5-sidecar-dir requires --b5-slot and an existing directory")
    if a.verify_performance and not (a.calibrated_perf and a.perf_workload):
        ap.error("--verify-performance requires --calibrated-perf and --perf-workload")
    if a.calibrated_perf != (a.perf_workload is not None):
        ap.error("--calibrated-perf and --perf-workload must be supplied together")
    if a.stock_control:
        for dest, flag in (
            ("run_iteration", "run-iteration"), ("value", "value"),
            ("emit_planner_context", "emit-planner-context"),
            ("no_build", "no-build"), ("coder_role", "coder-role"),
            ("b4_reflux_ablation", "b4-reflux-ablation"),
            ("coder_build_authority", "allow-coder-derived-build"),
        ):
            if dest in supplied and (stock_only or dest not in {
                    "run_iteration", "coder_role", "coder_build_authority"}):
                ap.error(f"--stock-control cannot be combined with --{flag}")
        if not a.isolate_worktree:
            ap.error("--stock-control requires --isolate-worktree")
    if a.k2_critic_diagnosis is not None and (
        not a.emit_planner_context or a.run_iteration
        or a.b4_reflux_ablation or a.reflux != "on"
        or a.knowledge_manifest is None
    ):
        ap.error("--k2-critic-diagnosis requires K2 emit-only, non-B4, reflux on")
    if (a.agent_inputs is not None or a.agent_prompts is not None) and not a.run_iteration:
        ap.error("--agent-inputs/--agent-prompts require --run-iteration")
    if a.agent_prompts is not None and a.agent_inputs is None:
        ap.error("--agent-prompts requires --agent-inputs")
    if a.fetchcontent_prebuild_receipt is not None and a.no_build:
        ap.error("--fetchcontent-prebuild-receipt cannot be combined with --no-build")
    if (a.fetchcontent_prebuild_receipt is not None
            and a.emit_planner_context is not None):
        ap.error(
            "--fetchcontent-prebuild-receipt cannot be combined with "
            "--emit-planner-context"
        )
    fetchcontent_options = {}
    if a.fetchcontent_prebuild_receipt is not None:
        try:
            (
                fetchcontent_base_dir,
                masstree_source_dir,
                mimalloc_source_dir,
                googletest_source_dir,
                fetchcontent_dependency_receipt,
            ) = _load_masstree_prebuild_receipt(
                a.fetchcontent_prebuild_receipt,
            )
        except ValueError as exc:
            ap.error(f"invalid --fetchcontent-prebuild-receipt: {exc}")
        fetchcontent_options = {
            "fetchcontent_base_dir": fetchcontent_base_dir,
            "masstree_source_dir": masstree_source_dir,
            "mimalloc_source_dir": mimalloc_source_dir,
            "googletest_source_dir": googletest_source_dir,
            "fetchcontent_dependency_receipt": (
                fetchcontent_dependency_receipt
            ),
        }
    if a.b4_closed_critic_receipt is not None and not a.run_iteration:
        raise B4ProtocolError(
            "--b4-closed-critic-receipt requires --run-iteration"
        )
    if a.b4_closed_critic_receipt is not None and not a.b4_reflux_ablation:
        raise B4ProtocolError(
            "--b4-closed-critic-receipt requires --b4-reflux-ablation"
        )
    if a.b4_reflux_ablation and a.no_build:
        raise B4ProtocolError("B-4 protocol forbids --no-build")
    if (
        a.b4_reflux_ablation
        and not a.run_iteration
        and not a.emit_planner_context
    ):
        raise B4ProtocolError(
            "B-4 protocol forbids the fixture run_one_iteration route"
        )
    has_prerun_binding = (
        a.b4_prerun_publication is not None or a.b4_attempt_id is not None
    )
    if not a.b4_reflux_ablation and has_prerun_binding:
        raise B4ProtocolError(
            "B-4 prerun proposal binding requires B-4 bootstrap mode"
        )
    if a.b4_reflux_ablation and a.b4_closed_critic_receipt is not None:
        if has_prerun_binding:
            raise B4ProtocolError(
                "B-4 prerun proposal binding is bootstrap-only"
            )
    elif a.b4_reflux_ablation and a.run_iteration and (
        a.b4_prerun_publication is None or a.b4_attempt_id is None
    ):
        raise B4ProtocolError(
            "B-4 bootstrap requires publication root and attempt id"
        )
    elif a.b4_reflux_ablation and has_prerun_binding and not a.run_iteration:
        raise B4ProtocolError(
            "B-4 prerun proposal binding requires a bootstrap proposal"
        )
    resolved_knowledge = _resolve_knowledge_manifest_argument(
        a.knowledge_manifest,
    )
    diagnosis = None
    if a.k2_critic_diagnosis is not None:
        try:
            diagnosis = k2_critic_diagnosis_from_bytes(a.k2_critic_diagnosis.read_bytes())
        except (OSError, ValueError) as exc:
            ap.error(f"invalid --k2-critic-diagnosis: {exc}")
    knowledge_de_novo_claim = a.knowledge_de_novo_claim == "true"
    if (
        not a.emit_planner_context
        and not stock_only
        and not a.no_build
        and a.coder_build_authority is None
        and not a.machine_generated_proposal
    ):
        raise BuildAdmissionError("--allow-coder-derived-build の明示 opt-in が必要")

    resolved_site = _current_site()
    contract = _admit_env_contract(resolved_site)
    if a.b4_reflux_ablation:
        cfg = default_cfg(
            reflux=(a.reflux == "on"),
            b4_reflux_ablation=True,
            _b4_launch_context=_b4_launch_context,
        )
    else:
        cfg = default_cfg(reflux=(a.reflux == "on"))
    perf = calibrated_perf(a.perf_workload) if a.calibrated_perf else default_perf()
    if a.calibrated_perf:
        cfg = replace(cfg, search_config={
            **cfg.search_config, "records": perf.records, "threads": perf.threads,
            "perf_workload": dict(perf.workload), "extime": perf.extime, "reps": perf.reps,
        })
    if a.b5_slot is not None:
        cfg = replace(cfg, search_config={**cfg.search_config, "b5_slot": a.b5_slot})
    if a.verify_performance:
        cfg = replace(cfg, search_config={
            **cfg.search_config, SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_PERFORMANCE,
        })
    cfg = _campaign_cfg_for_site(cfg, resolved_site, _contract=contract)
    if a.emit_planner_context:
        if a.policy_hint is not None:
            cfg = replace(
                cfg,
                search_config={**cfg.search_config, "policy_hint": a.policy_hint},
            )
        cfg, _knowledge_layout, knowledge_input = _prepare_knowledge_campaign(
            cfg,
            resolved_knowledge,
            classification=a.knowledge_classification,
            de_novo_claim=knowledge_de_novo_claim,
        )
        layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
        state = load_loop_state(layout)
        if state is None:
            state = LoopState(start_wall=time.time())
        payload = planner_context_payload(
            state, cfg, knowledge_input=knowledge_input,
            k2_critic_diagnosis=diagnosis,
        )
        with open(a.emit_planner_context, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))
        print(f"planner context を出力しました: {a.emit_planner_context}")
        return 0
    if (
        a.run_iteration
        and resolved_knowledge is not None
        and resolved_knowledge.manifest.sources
        and a.coder_role is None
    ):
        raise ValueError(
            "--run-iteration: --knowledge-manifest の sources が非空 "
            f"(sources_count={len(resolved_knowledge.manifest.sources)}) "
            "のため --coder-role coder-v4-autonomous-k2 が必要"
        )
    if stock_only or a.machine_generated_proposal:
        build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    else:
        build_context = build_run_context(
            generator_id=GeneratorId.BACKOFF_SWEEP,
            coder_authority=None if a.no_build else a.coder_build_authority,
        )

    stock_context = build_context
    if pair_mode:
        stock_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
        if stock_context.policy != build_context.policy:
            raise BuildAdmissionError("pair candidate and stock admission policies must match")

    b5_options = {}
    if a.b5_slot is not None:
        b5_options = {"b5_mode": True, "b5_sidecar_dir": a.b5_sidecar_dir}
    if a.machine_generated_proposal:
        b5_options["capability_resolver"] = _machine_proposal_capability_resolver(
            build_context, hashlib.sha256(Path(a.run_iteration).read_bytes()).hexdigest())

    root = _repo_root()
    fixed_sub = os.path.join(root, "external", "ccbench")
    from . import patchharness
    from .p2_2 import _assert_single_tenant
    if not a.no_build:
        _assert_single_tenant()
    patchharness.assert_pinned_clean(fixed_sub, PIN)

    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg, _knowledge_layout, knowledge_input = _prepare_knowledge_campaign(
        cfg,
        resolved_knowledge,
        classification=a.knowledge_classification,
        de_novo_claim=knowledge_de_novo_claim,
    )

    cache_root = os.path.join(fixed_sub, "build-variants") if a.isolate_worktree else ""

    if stock_only:
        return _run_stock_cli_step(
            cfg, perf, fixed_sub, cache_root, stock_context,
            b5_options, fetchcontent_options, resolved_site, contract)
    if a.run_iteration:
        from . import loop
        import traceback

        candidate_error = stock_error = None
        candidate_rc = stock_rc = 1
        session_cm = loop.authorization_session() if pair_mode else contextlib.nullcontext()
        with session_cm as session:
            try:
                proposal_receipt_sha256 = None
                if a.b4_reflux_ablation:
                    preflight_layout = exploration_campaign_layout(
                        str(ident.campaign_id(cfg))
                    )
                    preflight_state = load_loop_state(preflight_layout)
                    if preflight_state is None:
                        preflight_state = LoopState(start_wall=time.time())
                    preflight_authorization = require_b4_iteration_authorization(
                        cfg,
                        preflight_layout,
                        preflight_state,
                        do_build=not a.no_build,
                        terminal_receipt_path=a.b4_closed_critic_receipt,
                    )
                    assert preflight_authorization is not None
                    proposal_receipt_sha256 = (
                        preflight_authorization.terminal_receipt_sha256
                    )
                agent_record = None
                if a.agent_inputs is not None:
                    input_bytes = a.agent_inputs.read_bytes()
                    inputs = _agent_json(input_bytes)
                    if set(inputs) != {"planner", "coder"} or any(
                            not isinstance(value, dict) for value in inputs.values()):
                        raise ValueError("--agent-inputs requires exact planner/coder input objects")
                    agent_record = {
                        "proposal_path": a.run_iteration,
                        "input_path": a.agent_inputs, "input_bytes": input_bytes,
                        "planner_input": inputs["planner"], "coder_input": inputs["coder"],
                    }
                    if a.agent_prompts is not None:
                        prompts = _agent_json(a.agent_prompts.read_bytes())
                        if set(prompts) != {"planner", "coder"} or any(
                                not isinstance(value, str) for value in prompts.values()):
                            raise ValueError("--agent-prompts requires exact planner/coder paths")
                        agent_record.update({role + "_prompt_path": path for role, path in prompts.items()})
                proposal_capture = agent_record if agent_record is not None else {}
                try:
                    planner, coder, prior_rev = load_proposal_file(
                        a.run_iteration,
                        b4_reflux_ablation=a.b4_reflux_ablation,
                        b4_closed_critic_receipt_sha256=proposal_receipt_sha256,
                        b4_prerun_publication=a.b4_prerun_publication,
                        b4_attempt_id=a.b4_attempt_id,
                        knowledge_input=(
                            knowledge_input if a.coder_role is not None else None
                        ),
                        coder_role=a.coder_role,
                        capture=proposal_capture,
                    )
                except (ValueError, KeyError, TypeError) as exc:
                    if a.b5_slot is None:
                        raise
                    _b5_proposal_rejected(a.b5_sidecar_dir, a.b5_slot, exc)
                    return 3
                try:
                    initial_proposal_sha256 = canonical_b4_proposal_sha256(
                        proposal_capture["proposal_document"]
                    )
                except B4ProtocolError:
                    # canonical 化できない proposal は hash=null。
                    initial_proposal_sha256 = None
                print(f"=== 段 4b iteration (proposal={a.run_iteration}, "
                      f"reflux={a.reflux}, build={not a.no_build}, prior_critic_reverse={prior_rev}, "
                      f"isolate_worktree={a.isolate_worktree}) ===")
                wt_cm = (patchharness.checkout(PIN, base_dir=fixed_sub)
                         if a.isolate_worktree else contextlib.nullcontext(fixed_sub))
                with wt_cm as sub:
                    out = drive_iteration(cfg, perf, planner, coder, prior_rev, sub,
                                          do_build=not a.no_build, cache_root=cache_root,
                                          build_context=build_context,
                                          b4_closed_critic_receipt=(
                                              a.b4_closed_critic_receipt
                                          ),
                                          b4_proposal_receipt_sha256=(
                                              proposal_receipt_sha256
                                          ),
                                          initial_proposal_sha256=initial_proposal_sha256,
                                          _b4_launch_context=_b4_launch_context,
                                          _resolved_site=resolved_site,
                                          _contract=contract,
                                          **({"agent_record": agent_record} if agent_record is not None else {}),
                                          **({"authorization_session": session} if session is not None else {}),
                                          **b5_options, **fetchcontent_options)
                if a.b5_slot is not None and out["outcome"] in {"rejected-preprocess", "rejected-tier0"}:
                    return 3
                layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
                print(f"  ran={out['ran']} outcome={out['outcome']} "
                      f"variant={out.get('variant')} iteration={out['iteration']}")
                print(f"  停止判定: {out['stop_reason']}")
                print(f"  checkpoint: {loop_state_path(layout)}")
                print(f"  digest: {os.path.join(layout.root, 's4_loop_digest.txt')}")
                # 停止判定が機械的に返り、checkpoint が焼かれていれば駆動口として健全。
                ok = (out["stop_reason"] in ("continue", "converged", "reverse-exhausted",
                                             "budget-iterations", "budget-walltime")
                      and os.path.exists(loop_state_path(layout)))
                candidate_rc = 0 if ok and out["outcome"] != "duplicate-skip" else 1
            except Exception as exc:
                if not pair_mode:
                    raise
                candidate_error = exc
                traceback.print_exc()
                print("  candidate outcome=exception")
            if not pair_mode:
                return candidate_rc
            try:
                stock_rc = _run_stock_cli_step(
                    cfg, perf, fixed_sub, cache_root, stock_context,
                    b5_options, fetchcontent_options, resolved_site, contract,
                    authorization_session=session)
            except Exception as exc:
                stock_error = exc
                traceback.print_exc()
                print("  stock outcome=exception")
        print(f"p3 S4 pair: candidate_rc={candidate_rc} stock_rc={stock_rc}")
        if candidate_error is not None:
            raise candidate_error.with_traceback(candidate_error.__traceback__)
        if candidate_rc:
            return candidate_rc
        if stock_error is not None:
            raise stock_error.with_traceback(stock_error.__traceback__)
        return stock_rc
    wt_cm = (patchharness.checkout(PIN, base_dir=fixed_sub)
             if a.isolate_worktree else contextlib.nullcontext(fixed_sub))
    state = LoopState(start_ts=time.monotonic())
    state.iteration = 1

    # fixture proposal (人間が与える = kickoff と同じリーク制御。coder の自律発案の代役)。
    planner = PlannerProposal(axis=MARKER_ID, direction="explore_both", magnitude="small",
                              justification="fixture (機械 E2E 用)")
    coder = CoderProposal(axis=MARKER_ID, value=a.value,
                          implementation=f"double now_backoff = {a.value};",
                          justification="fixture", confidence="low")

    print(f"=== 段 4 loop 1 iteration (機械 E2E, value={a.value}, "
          f"reflux={a.reflux}, build={not a.no_build}, "
          f"isolate_worktree={a.isolate_worktree}) ===")
    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    with wt_cm as sub:
        out = _run_one_iteration_resolved(
            cfg, perf, planner, coder, state, sub, not a.no_build,
            layout, contract, resolved_site, cache_root=cache_root,
            build_context=build_context,
            **fetchcontent_options,
        )
    print(f"  outcome={out['outcome']} variant={out.get('variant')}")

    out_path = os.path.join(layout.root, "s4_loop_digest.txt")
    stop = check_stop(state)
    dqs = []
    if out["outcome"] != "dry-pass":
        critic_view = _refresh_critic_digest(layout, reflux=(a.reflux == "on"))
        # WAL 機械判定 (宣言でなくレコードを gate に — kickoff/D30 様式)。
        dqs = load_diff_rejections(critic_view)
    # iteration の WAL 非依存を **差分**で実証する (1==1 の恒真 assert にしない): loop の
    # iteration は WAL レコード数と一致しない = WAL から導出していないことの witness (D39 決定2)。
    n_wal = len(list(wal.read_records(layout)))
    checks = {
        f"iteration(={state.iteration}) が WAL レコード数(={n_wal})と独立 (WAL 由来でない)":
            state.iteration == 1 and n_wal != state.iteration,
        "停止判定が機械的に返る": stop.reason in (
            "continue", "converged", "reverse-exhausted",
            "budget-iterations", "budget-walltime"),
    }
    if out["outcome"] == "dry-pass":
        checks["dry-pass は critic digest を生成しない"] = not os.path.exists(out_path)
    else:
        checks["admitted outcome は critic digest を生成"] = os.path.exists(out_path)
    if out["outcome"] != "dry-pass":
        checks["whiteboard に 1 行射影 (機序なし)"] = len(state.whiteboard) == 1
        checks["whiteboard entry が方向/結果のみ (機序フィールド無し)"] = (
            len(state.whiteboard) == 1
            and set(vars(state.whiteboard[0])) == {
                "iteration", "direction", "magnitude", "result", "delta_pct"})
    if out["outcome"] == "rejected":
        checks["diff-quarantine reject が WAL に焼かれ load_diff_rejections が復元"] = (
            any(d.variant == out["variant"] and d.subtype for d in dqs))
        checks["reject が whiteboard で result=rejected"] = (
            state.whiteboard[0].result == "rejected")
    elif out["outcome"] == "certified":
        checks["certified で fitness_tps あり"] = out.get("fitness_tps") is not None
        checks["certified で whiteboard result=success"] = (
            state.whiteboard[0].result == "success")

    print("\n=== 判定 (WAL/状態 機械確認) ===")
    ok = all(checks.values())
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"\ncampaign dir: {layout.root}")
    print(f"停止判定: stop={stop.stop} reason={stop.reason}")
    print(f"\n段 4 loop 1 iteration 判定: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
