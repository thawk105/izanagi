# -*- coding: utf-8 -*-
"""T-126 Pegasus fixed envelope と post-job 二相 receipt を検査する。"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import shlex
import signal
import stat
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path
from orchestrator.campaign.silo_ladder_rung1 import THIRD_PARTY_STAGING_RELATIVE

import pytest
from jsonschema import Draft7Validator

pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_HERE.parents[1]))

from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from pegasus_policy_expected_goldens import (  # noqa: E402
    EXPECTED_CURRENT_PEGASUS_POLICY_SHA256,
    EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256,
)

_SIGNAL_RESET_LAUNCHER_MARKER = (
    b'{"final_sighup":"SIG_DFL","final_sighup_blocked":false,'
    b'"final_sigterm":"SIG_DFL","final_sigterm_blocked":false,'
    b'"initial_sighup":"SIG_IGN","initial_sighup_blocked":true,'
    b'"initial_sigterm":"SIG_IGN","initial_sigterm_blocked":true}\n')
PREFLIGHT_HELPER_RELATIVE = (
    "orchestrator/campaign/certified_writer_preflight.py"
)
_SIGNAL_IGNORE_EXEC_LAUNCHER = (
    "import os,signal,sys\n"
    "python,inner,bash,argv0,script,marker=sys.argv[1:]\n"
    "signal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
    "signal.signal(signal.SIGHUP,signal.SIG_IGN)\n"
    "signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGHUP})\n"
    "initial_mask=signal.pthread_sigmask(signal.SIG_BLOCK,set())\n"
    "if (signal.getsignal(signal.SIGTERM) is not signal.SIG_IGN\n"
    "        or signal.getsignal(signal.SIGHUP) is not signal.SIG_IGN\n"
    "        or signal.SIGTERM not in initial_mask\n"
    "        or signal.SIGHUP not in initial_mask):\n"
    "    raise SystemExit('signal ignore setup failed')\n"
    "os.execve(python,[python,'-I','-S','-B','-c',inner,\n"
    "                  bash,argv0,script,marker],os.environ)\n"
)
_SIGNAL_RESET_EXEC_LAUNCHER = (
    "import os,signal,sys\n"
    "bash,argv0,script,marker=sys.argv[1:]\n"
    "initial_sigterm=signal.getsignal(signal.SIGTERM)\n"
    "initial_sighup=signal.getsignal(signal.SIGHUP)\n"
    "initial_mask=signal.pthread_sigmask(signal.SIG_BLOCK,set())\n"
    "if (initial_sigterm is not signal.SIG_IGN\n"
    "        or initial_sighup is not signal.SIG_IGN\n"
    "        or signal.SIGTERM not in initial_mask\n"
    "        or signal.SIGHUP not in initial_mask):\n"
    "    raise SystemExit('signal ignore inheritance failed')\n"
    "signal.signal(signal.SIGTERM,signal.SIG_DFL)\n"
    "signal.signal(signal.SIGHUP,signal.SIG_DFL)\n"
    "signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGHUP})\n"
    "final_sigterm=signal.getsignal(signal.SIGTERM)\n"
    "final_sighup=signal.getsignal(signal.SIGHUP)\n"
    "final_mask=signal.pthread_sigmask(signal.SIG_BLOCK,set())\n"
    "if (final_sigterm is not signal.SIG_DFL\n"
    "        or final_sighup is not signal.SIG_DFL\n"
    "        or signal.SIGTERM in final_mask\n"
    "        or signal.SIGHUP in final_mask):\n"
    "    raise SystemExit('signal reset failed')\n"
    "if marker:\n"
    f"    data={_SIGNAL_RESET_LAUNCHER_MARKER!r}\n"
    "    fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
    "    try:\n"
    "        offset=0\n"
    "        while offset<len(data):\n"
    "            written=os.write(fd,data[offset:])\n"
    "            if written<=0:\n"
    "                raise OSError('launcher marker write made no progress')\n"
    "            offset+=written\n"
    "        os.fsync(fd)\n"
    "    finally:\n"
    "        os.close(fd)\n"
    "    dfd=os.open(os.path.dirname(marker) or '.',\n"
    "                os.O_RDONLY|getattr(os,'O_DIRECTORY',0))\n"
    "    try:\n"
    "        os.fsync(dfd)\n"
    "    finally:\n"
    "        os.close(dfd)\n"
    "os.execve(bash,[argv0,script],os.environ)\n"
)

T126_MUTATION_REGISTRY = {
    "M1": {
        "old_anchor": "contract.observe_relative strict upper boundary",
        "mutant": "change strict boundary to inclusive",
        "node": "orchestrator/tests/test_t126_qualification_contract.py::"
                "test_m1_exact_threshold_is_zero_side_and_strictly_above_is_one",
    },
    "M2a": {
        "old_anchor": "layer3 ancestor qualification marker scan",
        "mutant": "ignore ancestor marker",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m2a_ancestor_marker_alone_rejects_formal_shape",
    },
    "M2b": {
        "old_anchor": "layer3 recursive campaign-lock lineage gate",
        "mutant": "ignore nested lock lineage",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m2b_lock_lineage_alone_rejects_without_shape_mask",
    },
    "M2c": {
        "old_anchor": "layer3 recursive WAL lineage gate",
        "mutant": "ignore nested WAL lineage",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_layer3_rejects_qualification_lineage_nested_in_formal_wal",
    },
    "M3": {
        "old_anchor": "artifacts.snapshot_source full SHA equality",
        "mutant": "accept wrong registered source SHA",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m3_source_snapshot_requires_the_registered_full_hash",
    },
    "M4a": {
        "old_anchor": "pipeline producer require_settled gate",
        "mutant": "emit terminal commit when settle is false",
        "node": "orchestrator/tests/test_t126_qualification_driver.py::"
                "test_m4a_producer_settled_gate_rejects_before_terminal_commit",
    },
    "M4b": {
        "old_anchor": "artifact consumer bench settled-is-true gate",
        "mutant": "accept settled false evidence",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m4_settled_false_rejects_and_full_evidence_accepts",
    },
    "M5a": {
        "old_anchor": "member evidence exact legacy/S2 tag order",
        "mutant": "accept swapped verify tags",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m5a_exact_s2_tag_order_has_no_argv_mask",
    },
    "M5b": {
        "old_anchor": "member evidence tag-specific exact argv",
        "mutant": "accept altered S2 argv flag",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m5b_s2_exact_argv_flag_has_no_shape_or_tag_mask",
    },
    "M6a": {
        "old_anchor": "collector mandatory regular accounting read",
        "mutant": "fail open when accounting is absent",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m6a_missing_accounting_file_is_the_only_negative_then_closes",
    },
    "M6b": {
        "old_anchor": "collector common exact accounting job-ID helper",
        "mutant": "accept foreign accounting job ID",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m6b_exact_accounting_job_id_is_single_effective_anchor",
    },
    "M6c": {
        "old_anchor": "collector common accounting/job-result RC equality",
        "mutant": "accept mismatched scheduler and declared RC",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m6c_accounting_rc_vs_job_rc_closes_as_exact_mismatch",
    },
    "M6d": {
        "old_anchor": "public final receipt canonical series pointer",
        "mutant": "accept alternate final series pointer",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m6d_final_series_pointer_swap_is_single_closure_reason",
    },
    "M7a": {
        "old_anchor": "attempt ledger initial-intent state-new gate",
        "mutant": "allow duplicate initial submission",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m7a_series_ledger_rejects_duplicate_initial_submission",
    },
    "M7b": {
        "old_anchor": "retry admission last-retry-index-zero gate",
        "mutant": "allow retry of retry",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m7b_series_ledger_rejects_retry_of_retry",
    },
    "M7c": {
        "old_anchor": "retry admission pre-observation predicate",
        "mutant": "allow retry after first observation",
        "node": "orchestrator/tests/test_t126_qualification_artifacts.py::"
                "test_m7c_series_ledger_rejects_retry_after_first_observation",
    },
    "M8a": {
        "old_anchor": "submit create-only qsub invocation claim",
        "mutant": "execute qsub when invocation claim already exists",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m8a_create_only_invocation_claim_serializes_parallel_submit",
    },
    "M8b": {
        "old_anchor": "resume-unbound binding-only authority gate",
        "mutant": "bind raw qsub stdout without binding",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m8b_post_qsub_prebinding_crash_never_uses_raw_stdout_authority",
    },
    "M8c": {
        "old_anchor": "accepted-unknown invocation claim closure",
        "mutant": "automatically resubmit after nonzero qsub",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m8c_qsub_nonzero_is_accepted_unknown_and_never_resubmitted",
    },
    "M8d": {
        "old_anchor": "binding v2 exact return-code/schema classifier",
        "mutant": "accept bool or nonzero binding return code",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m8d_binding_v2_exact_corpus_and_all_consumer_wiring",
    },
    "M9a": {
        "old_anchor": "targetless staging discard rule",
        "mutant": "promote targetless full staging",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9a_targetless_full_staging_is_discarded_to_nonretry_failure",
    },
    "M9b": {
        "old_anchor": "after-publish staging cleanup",
        "mutant": "retain valid after-publish staging",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9b_after_publish_stage_cleanup_and_collector_rerun_converge",
    },
    "M9c": {
        "old_anchor": "exact early job-staging reconciliation",
        "mutant": "ignore bound early job-staging",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9c_exact_early_job_staging_is_recovered_and_closed",
    },
    "M9d": {
        "old_anchor": "publisher same-inode and exact-nlink preflight",
        "mutant": "accept different inode or external hardlink",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9d_inode_and_nlink_anomalies_are_nonmutating_rejections",
    },
    "M9e": {
        "old_anchor": "attempt staging retirement before series verification",
        "mutant": "retire attempt staging only after series verification",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9e_after_publish_retirement_precedes_series_verification",
    },
    "M9g": {
        "old_anchor": "attempt staging retirement before rejection returns",
        "mutant": "restore retirement to its pre-rejection-return position",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9g_attempt_retirement_is_not_skipped_by_rejection_returns",
    },
    "M9h": {
        "old_anchor": "attempt stage retirement after both preflights",
        "mutant": "retire attempt staging between the two preflights",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_cross_namespace_preflight_rejects_before_attempt_stage_retire",
    },
    "M9i": {
        "old_anchor": "single-source early-retirable staging lifecycle set",
        "mutant": "admit targetless into the early-retirable lifecycle set",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9i_targetless_attempt_staging_is_not_retired_before_verification",
    },
    "M9j": {
        "old_anchor": "valid canonical versus rejected early result fail-closed",
        "mutant": "publish an unverifiable receipt for the rejected conflict",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m9j_valid_canonical_with_rejected_early_result_fails_closed",
    },
    "M10a": {
        "old_anchor": "normal invalid/missing monotonic origin gate",
        "mutant": "grant retry after invalid-to-missing rewrite",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m10a_invalid_to_missing_coherent_rehash_cannot_gain_retry",
    },
    "M10b": {
        "old_anchor": "valid canonical non-null exact receipt pointer",
        "mutant": "accept pointer-null canonical",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m10b_valid_canonical_requires_nonnull_exact_pointer",
    },
    "M10c": {
        "old_anchor": "canonical/accounting mismatch failure closure",
        "mutant": "leave publish-then-kill unclosed",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m10c_publish_then_scheduler_kill_closes_accounting_mismatch",
    },
    "M10d": {
        "old_anchor": "new failure classes excluded at four retry layers",
        "mutant": "add new failure class to retry eligibility",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m10d_new_failure_classes_are_disjoint_from_all_retry_authority",
    },
    "M11a": {
        "old_anchor": "submission script hash to committed series blob edge",
        "mutant": "remove committed blob identity edge",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m11a_coherent_submission_job_rewrite_cannot_cross_committed_blob_edge",
    },
    "M11b": {
        "old_anchor": "embedded stdlib-only isolated terminal publisher",
        "mutant": "restore persistent package import",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m11b_exact_spooled_script_uses_embedded_isolated_publisher",
    },
    "M12": {
        "old_anchor": "live qualification schema bytes equality",
        "mutant": "ignore live qualification schema byte drift",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m12_relaxed_live_schema_cannot_expand_receipt_acceptance",
    },
    "M13": {
        "old_anchor": "qualification schema memo/live bytes equality",
        "mutant": "ignore qualification schema memo drift",
        "node": "orchestrator/tests/test_t126_pegasus_tools.py::"
                "test_m13_qualification_schema_memo_drift_fails_closed",
    },
}

# collector.collect() の逐語断片。M9e / M9g は「削除」ではなく「移動」変異な
# ので、anchor と replacement は移動元から移動先までを丸ごと含む必要がある。
# 各断片は production の該当行と逐語一致し、そのまま連結して構文的に正しい
# Python になる。
_T126_COLLECT_RETIRE_CALL = (
    "    _retire_after_publish_attempt_staging("
    "attempt_dir, attempt_preflight)\n")
_T126_COLLECT_SERIES_BLOCK = (
    "    series_path = attempt_dir / \"series-result.json\"\n"
    "    series_present = series_path.is_file() and not series_path.is_symlink()\n"
    "    series = load_json_strict(series_path) if series_present else None\n"
    "    if series_present:\n"
    "        verification = verify_attempt(attempt_dir)\n"
    "        if verification.integrity_status != \"valid\":\n"
    "            raise CollectionError(\n"
    "                \"series result failed read-only verification: \"\n"
    "                + \"; \".join(verification.errors))\n"
    "        terminal = series[\"terminal\"]\n"
    "        observations = len(series[\"bits\"])\n"
    "    else:\n"
    "        terminal = None\n"
    "        ledger = attempt_dir / \"series-ledger.jsonl\"\n"
    "        if ((not ledger.is_file() or ledger.is_symlink())\n"
    "                and not recovered_pre_attempt):\n"
    "            raise CollectionError(\n"
    "                \"attempt failure is missing its canonical series ledger\")\n"
    "        observations = (\n"
    "            0 if recovered_pre_attempt\n"
    "            else replay_ledger(\n"
    "                load_jsonl_strict(ledger), protocol).observations_recorded)\n"
)
_T126_COLLECT_RECONCILE_HEAD = (
    "    canonical_state, canonical_job_result_bytes, result = (\n")
_T126_COLLECT_RECONCILE_TAIL = (
    "        _reconcile_job_results(\n"
    "            capability=capability, attempt_dir=attempt_dir, submit=submit,\n"
    "            protocol=protocol, series_preimage=series_preimage,\n"
    "            series=series, accounting=accounting_record,\n"
    "            observations_recorded=observations,\n"
    "            recovered_pre_attempt=recovered_pre_attempt,\n"
    "            attempt_preflight=attempt_preflight,\n"
    "            staging_preflight=staging_preflight))\n"
)
_T126_M9E_ANCHOR = (
    _T126_COLLECT_RETIRE_CALL
    + "\n"
    + _T126_COLLECT_SERIES_BLOCK
    + _T126_COLLECT_RECONCILE_HEAD)
_T126_M9E_REPLACEMENT = (
    "\n"
    + _T126_COLLECT_SERIES_BLOCK
    + _T126_COLLECT_RETIRE_CALL
    + _T126_COLLECT_RECONCILE_HEAD)
_T126_M9G_ANCHOR = _T126_M9E_ANCHOR + _T126_COLLECT_RECONCILE_TAIL
_T126_M9G_REPLACEMENT = (
    "\n"
    + _T126_COLLECT_SERIES_BLOCK
    + _T126_COLLECT_RECONCILE_HEAD
    + _T126_COLLECT_RECONCILE_TAIL
    + "    if canonical_state not in {\"semantic-conflict\", \"invalid\"}:\n"
    + "    " + _T126_COLLECT_RETIRE_CALL)

# M9h は retire を「両 namespace の preflight 後」から「attempt 側 preflight の
# 直後」へ移す変異である。移動元 (`collect()` から呼ばれる helper 本体) と移動先
# (`_preflight_job_result_namespaces` の 2 呼出しの間) は別関数なので、両方を 1
# つの連続 anchor で表すために `_preflight_job_result_namespaces` の定義から
# `_retire_after_publish_attempt_staging` の定義末尾までを丸ごと抱える。
# replacement は inline 挿入と helper の no-op 化を同時に行う。helper を no-op に
# しないと `collect()` に残る呼出しが同じ stage を二重 unlink し、
# `FileNotFoundError` の escape で無関係なテストを巻き添えにする。
_T126_PREFLIGHT_HEAD = (
    "def _preflight_job_result_namespaces(\n"
    "        *, capability, attempt_dir: Path, submit: Mapping[str, Any],\n"
    ") -> tuple[\n"
    "        tuple[str, bytes | None, dict[str, Any] | None, Path | None,\n"
    "              str | None],\n"
    "        tuple[str, bytes | None, dict[str, Any] | None, Path | None,\n"
    "              str | None]]:\n"
    "    \"\"\"Preflight both publisher namespaces before either one is "
    "mutated.\"\"\"\n"
    "    attempt_preflight = _reconcile_result_namespace(\n"
    "        attempt_dir, submit=submit, label=\"attempt\")\n"
)
_T126_PREFLIGHT_TAIL = (
    "    staging_dir = _job_staging_directory(capability.root, submit)\n"
    "    staging_preflight = _reconcile_result_namespace(\n"
    "        staging_dir, submit=submit, label=\"early job-staging\")\n"
    "    return attempt_preflight, staging_preflight\n"
    "\n"
    "\n"
    "def _retire_after_publish_attempt_staging(\n"
    "        attempt_dir: Path,\n"
    "        attempt_preflight: tuple[\n"
    "            str, bytes | None, dict[str, Any] | None, Path | None,\n"
    "            str | None]) -> None:\n"
)
_T126_RETIRE_BODY = (
    "    \"\"\"Retire the attempt stage that is only a second name for the "
    "canonical.\n"
    "\n"
    "    An after-publish stage shares inode and bytes with the canonical "
    "entry, so\n"
    "    unlinking it loses no information. A targetless stage is the only "
    "copy of\n"
    "    its bytes, and the structural fail-closed rejections that still run "
    "below\n"
    "    (series verification, series ledger, semantic gates) must be able to "
    "refuse\n"
    "    without mutating it; targetless staging is therefore left to the "
    "in-function\n"
    "    apply that runs after the global preflight and the semantic checks.\n"
    "    \"\"\"\n"
    "    (_state, _bytes, _value, stage, lifecycle) = attempt_preflight\n"
    "    if lifecycle not in _EARLY_RETIRABLE_LIFECYCLES:\n"
    "        return\n"
    "    _apply_result_reconciliation(attempt_dir, stage, lifecycle)\n"
)
_T126_M9H_ANCHOR = (
    _T126_PREFLIGHT_HEAD + _T126_PREFLIGHT_TAIL + _T126_RETIRE_BODY)
_T126_M9H_REPLACEMENT = (
    _T126_PREFLIGHT_HEAD
    + "    (_state, _bytes, _value, stage, lifecycle) = attempt_preflight\n"
    + "    if lifecycle in _EARLY_RETIRABLE_LIFECYCLES:\n"
    + "        _apply_result_reconciliation(attempt_dir, stage, lifecycle)\n"
    + _T126_PREFLIGHT_TAIL
    + "    \"\"\"mutant: retirement moved into the namespace "
      "preflight.\"\"\"\n"
    + "    return\n")

_T126_MUTATION_TRANSFORMS = {
    "M1": (
        "orchestrator/qualification/contract.py",
        "if subject > reference * (1.0 + threshold):",
        "if subject >= reference * (1.0 + threshold):",
    ),
    "M2a": (
        "orchestrator/campaign/layer3_report.py",
        "    _reject_qualification_ancestry(\n"
        "        campaign_dir, _qualification_ancestry_bound(campaign_dir, output_root),\n"
        "    )\n",
        "    # mutant: ancestor qualification marker ignored\n",
    ),
    "M2b": (
        "orchestrator/campaign/layer3_report.py",
        "    if _contains_qualification_lineage(lock):\n",
        "    if False and _contains_qualification_lineage(lock):\n",
    ),
    "M2c": (
        "orchestrator/campaign/layer3_report.py",
        "    if _contains_qualification_lineage(records):\n",
        "    if False and _contains_qualification_lineage(records):\n",
    ),
    "M3": (
        "orchestrator/qualification/artifacts.py",
        "    if actual != expected_sha256:\n",
        "    if False and actual != expected_sha256:\n",
    ),
    "M4a": (
        "orchestrator/campaign/pipeline.py",
        "    if require_settled and (not settled or settled.get(\"settled\") is not True):\n",
        "    if False and require_settled and (not settled or settled.get(\"settled\") is not True):\n",
    ),
    "M4b": (
        "orchestrator/qualification/artifacts.py",
        "    if (bench.get(\"settled\") is not True\n",
        "    if (False\n",
    ),
    "M5a": (
        "orchestrator/qualification/artifacts.py",
        "    if [row.get(\"workload\", {}).get(\"tag\") for row in verify_rows] != [\"legacy\", \"s2\"]:\n",
        "    if False and [row.get(\"workload\", {}).get(\"tag\") for row in verify_rows] != [\"legacy\", \"s2\"]:\n",
    ),
    "M5b": (
        "orchestrator/qualification/artifacts.py",
        "                or argv[1:] != exact_flags.get(tag)\n",
        "                or False\n",
    ),
    "M6a": (
        "orchestrator/qualification/collector.py",
        "    accounting_bytes = read_regular_file(accounting)\n",
        "    accounting_bytes = (read_regular_file(accounting) if accounting.exists() else b\"Request ID = 123.server\\nExit_status = 34\\nresources_used.walltime = 1\\n\")\n",
    ),
    "M6b": (
        "orchestrator/qualification/collector.py",
        "    if (accounting[\"job_id\"] != _normalize_job_id(job_id)\n",
        "    if (False\n",
    ),
    "M6c": (
        "orchestrator/qualification/collector.py",
        "        and (job_result[\"driver_rc\"] != accounting[\"exit_status\"]\n",
        "        and (False\n",
    ),
    "M6d": (
        "orchestrator/qualification/collector.py",
        "            expected_pointer_paths[\"series_result\"] = (\n                attempt_dir / \"series-result.json\")\n",
        "            expected_pointer_paths[\"series_result\"] = paths[\"series_result\"]\n",
    ),
    "M7a": (
        "orchestrator/qualification/attempt_ledger.py",
        "            if state != \"new\":\n",
        "            if False and state != \"new\":\n",
    ),
    "M7b": (
        "orchestrator/qualification/attempt_ledger.py",
        "    if last_retry_index != 0:\n",
        "    if False and last_retry_index != 0:\n",
    ),
    "M7c": (
        "orchestrator/qualification/attempt_ledger.py",
        "    if (observations_recorded != 0 or terminal is not None\n",
        "    if (False or terminal is not None\n",
    ),
    "M8a": (
        "tools/pegasus/submit_t126_qualification.sh",
        "      if ! recover_or_reject_unbound_invocation; then\n        exit 4\n      fi\n",
        "      INVOCATION_SHA256=$(load_qsub_invocation_claim)\n      RESERVATION_STATE=\"reserved-existing-invocation\"\n",
    ),
    "M8b": (
        "tools/pegasus/submit_t126_qualification.sh",
        "recover_or_reject_unbound_invocation() {\n  echo \"qsub invocation has no durable v2 binding; automatic resubmit is forbidden\" >&2\n  return 1\n}\n",
        "recover_or_reject_unbound_invocation() {\n  JOB_ID=$(publish_qsub_binding)\n  bind_qsub_attempt\n  RESERVATION_STATE=\"resume-bound\"\n  return 0\n}\n",
    ),
    "M8c": (
        "tools/pegasus/submit_t126_qualification.sh",
        "  if [[ \"$qsub_rc\" -ne 0 ]]; then\n    exit \"$qsub_rc\"\n  fi\n",
        "  if [[ \"$qsub_rc\" -ne 0 ]]; then\n    rm -f -- \"$SUBMISSION_DIR/qsub-invocation.json\"\n    exit \"$qsub_rc\"\n  fi\n",
    ),
    "M8d": (
        "tools/pegasus/t126_qualification.sh",
        "        or binding[\"qsub_returncode\"]!=0 \\\n",
        "",
    ),
    "M9a": (
        "orchestrator/qualification/collector.py",
        "            \"missing\", None, None, stage,\n            \"targetless\" if stage is not None else None)\n",
        "            *_decode_job_result(stage, submit), stage,\n            \"after-publish\" if stage is not None else None)\n",
    ),
    "M9b": (
        "orchestrator/qualification/collector.py",
        "    stage.unlink()\n    _fsync_directory(directory)\n",
        "    # mutant: valid after-publish stage retained\n",
    ),
    "M9c": (
        "orchestrator/qualification/collector.py",
        "    if staging_state == \"missing\":\n        return attempt_state, attempt_bytes, attempt_value\n",
        "    if True:\n        return attempt_state, attempt_bytes, attempt_value\n",
    ),
    "M9d": (
        "orchestrator/qualification/collector.py",
        "                != (target_stat.st_dev, target_stat.st_ino)\n",
        "                != (stage_stat.st_dev, stage_stat.st_ino)\n",
    ),
    "M9e": (
        "orchestrator/qualification/collector.py",
        _T126_M9E_ANCHOR,
        _T126_M9E_REPLACEMENT,
    ),
    "M9g": (
        "orchestrator/qualification/collector.py",
        _T126_M9G_ANCHOR,
        _T126_M9G_REPLACEMENT,
    ),
    "M9h": (
        "orchestrator/qualification/collector.py",
        _T126_M9H_ANCHOR,
        _T126_M9H_REPLACEMENT,
    ),
    # 早期回収の可否は `_EARLY_RETIRABLE_LIFECYCLES` の 1 行が単一の正本であ
    # り、`_retire_after_publish_attempt_staging` と `_reconcile_job_results`
    # の in-function apply はこの定数の補集合を担当する。したがって定数へ
    # "targetless" を足す 1 行変異は「targetless を検証前に破棄する」だけを
    # 変え、二重 unlink (FileNotFoundError の escape) を生まない。
    "M9i": (
        "orchestrator/qualification/collector.py",
        "_EARLY_RETIRABLE_LIFECYCLES = (\"after-publish\",)\n",
        "_EARLY_RETIRABLE_LIFECYCLES = (\"after-publish\", \"targetless\")\n",
    ),
    "M9j": (
        "orchestrator/qualification/collector.py",
        "        canonical_conflicts = attempt_state == \"valid\"\n"
        "        if canonical_conflicts:\n"
        "            try:\n"
        "                _validate_job_result_semantics(\n"
        "                    attempt_value, submit=submit, "
        "protocol=protocol,\n"
        "                    series_preimage=series_preimage, series=series)\n"
        "            except (CollectionError, QualificationArtifactError):\n"
        "                canonical_conflicts = False\n"
        "        if canonical_conflicts:\n"
        "            raise CollectionError(\n"
        "                \"attempt canonical conflicts with a rejected early job-result\")\n"
        "        return \"invalid\", rejected_bytes, None\n",
        "        return \"invalid\", rejected_bytes, None\n",
    ),
    "M10a": (
        "orchestrator/qualification/collector.py",
        "            elif canonical_state == \"missing\":\n                expected_failure = \"job-result-publication-failed\"\n",
        "            elif canonical_state == \"missing\":\n                expected_failure = \"pre-member-infrastructure\"\n",
    ),
    "M10b": (
        "orchestrator/qualification/collector.py",
        "        if pointer_missing_canonical:\n",
        "        if False and pointer_missing_canonical:\n",
    ),
    "M10c": (
        "orchestrator/qualification/collector.py",
        "    elif accounting_mismatch:\n        failure_class = \"job-result-accounting-mismatch\"\n",
        "    elif accounting_mismatch:\n        raise CollectionError(\"mutant leaves accounting mismatch open\")\n",
    ),
    "M10d": (
        "orchestrator/qualification/artifacts.py",
        "    \"job-result-accounting-mismatch\",\n",
        "",
    ),
    "M11a": (
        "orchestrator/qualification/identity.py",
        "            or submitted != committed):\n",
        "            or False):\n",
    ),
    "M11b": (
        "tools/pegasus/t126_qualification.sh",
        "import json,os,re,secrets,stat,sys,time\n",
        "import json,os,re,secrets,stat,sys,time\nsys.path.insert(0,os.environ[\"IZANAGI_T126_TEST_PERSISTENT_PACKAGE_ROOT\"])\nfrom orchestrator.qualification.atomic_publish import publish_bytes as _persistent_publish\n",
    ),
    "M12": (
        "orchestrator/qualification/identity.py",
        "        if hashlib.sha256(live).hexdigest() != expected:\n",
        "        if False and hashlib.sha256(live).hexdigest() != expected:\n",
    ),
    "M13": (
        "orchestrator/qualification/artifacts.py",
        "    if memoized != live:\n",
        "    if False and memoized != live:\n",
    ),
}
for _mutation_id, (_source_path, _anchor, _replacement) in (
        _T126_MUTATION_TRANSFORMS.items()):
    _row = T126_MUTATION_REGISTRY[_mutation_id]
    _row["source_path"] = _source_path
    _row["old_anchor"] = _anchor
    _row["replacement"] = _replacement
    del _row["mutant"]

from orchestrator.qualification import (  # noqa: E402
    artifacts as qualification_artifacts,
    collector,
    t126_driver,
)
from orchestrator.qualification.atomic_publish import (  # noqa: E402
    AtomicPublishError,
    publish_bytes,
)
from orchestrator.qualification.artifacts import (  # noqa: E402
    QUALIFICATION_SCHEMA_RELATIVE_PATHS,
    QualificationArtifactError,
    QualificationRoot,
    QualificationEventSink,
    create_attempt,
    create_json,
    file_record,
    load_json_strict,
    load_jsonl_strict,
    snapshot_source,
    validate_json_schema,
    validate_member_evidence,
    validate_failure_receipt_for_retry,
    validate_retry_history,
)
from orchestrator.qualification.attempt_ledger import (  # noqa: E402
    AttemptLedgerError,
    SeriesAttemptLedger,
)
from orchestrator.qualification.contract import load_protocol  # noqa: E402
from orchestrator.qualification.contract import (  # noqa: E402
    REGISTERED_DEPENDENCY_BUILD_ARGV,
    ProtocolError,
    REQUIRED_CODE_IDENTITY_PATHS,
    REQUIRED_SCRIPT_IDENTITY_PATHS,
    RESERVATION_POLICY_RELATIVE_PATH,
    attempt_identity,
    protocol_sha256,
    series_identity,
    validate_protocol,
)
from orchestrator.qualification.qsub_binding import (  # noqa: E402
    QsubBindingError,
    validate_qsub_binding,
)
from orchestrator.qualification.retry_index import (  # noqa: E402
    RetryIndexError,
    validate_retry_index,
)
from orchestrator.qualification.series import SeriesFSM  # noqa: E402
from orchestrator.qualification.t126_driver import (  # noqa: E402
    _member_identity,
    _parse_genome,
    verify as verify_attempt,
)
from orchestrator.qualification.identity import (  # noqa: E402
    IdentityVerificationError,
    verify_recorded_series_identity,
)


def _canonical(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8") + b"\n"
    )
    path.chmod(0o600)
    return path


def _directory_snapshot(directory: Path):
    return {
        path.name: (
            path.lstat().st_mode, path.lstat().st_uid,
            path.lstat().st_dev, path.lstat().st_ino,
            path.lstat().st_nlink, path.lstat().st_size,
            ("symlink", os.readlink(path))
            if path.is_symlink()
            else ("regular", path.read_bytes())
            if path.is_file()
            else ("other", None),
        )
        for path in sorted(directory.iterdir())
    }


def _path_tree_snapshot(root: Path) -> object:
    if not os.path.lexists(root):
        return None
    paths = [root]
    if root.is_dir() and not root.is_symlink():
        paths.extend(sorted(root.rglob("*")))
    snapshot = []
    for path in paths:
        info = path.lstat()
        relative = "." if path == root else path.relative_to(root).as_posix()
        if path.is_symlink():
            payload = ("symlink", os.readlink(path))
        elif path.is_file():
            payload = ("file", path.read_bytes())
        elif path.is_dir():
            payload = ("directory", None)
        else:
            payload = ("other", None)
        snapshot.append((relative, stat.S_IMODE(info.st_mode), payload))
    return tuple(snapshot)


def _fixture_preflight_source() -> str:
    return (
        "import argparse,json,os,sys\n"
        "parser=argparse.ArgumentParser()\n"
        "parser.add_argument('mode',choices=('floor','t126'))\n"
        "parser.add_argument('--repo-root',required=True)\n"
        "parser.add_argument('--receipt',required=True)\n"
        "args=parser.parse_args()\n"
        "expected=os.path.join(args.repo_root,'output','env','pegasus',"
        "'qualification','t126','submissions',os.environ["
        "'IZANAGI_SUBMISSION_NONCE'],'submit-receipt.json')\n"
        "if args.mode!='t126' or args.receipt!=expected:\n"
        "    raise SystemExit(4)\n"
        "rc=int(os.environ.get('IZANAGI_TEST_PREFLIGHT_RC','0'))\n"
        "if rc not in (0,3,4): raise SystemExit(4)\n"
        "if rc:\n"
        "    print(json.dumps({'gate':'fixture','reason':'rejected'},"
        "sort_keys=True,separators=(',',':')),file=sys.stderr)\n"
        "raise SystemExit(rc)\n"
    )


def _embedded_terminal_publisher_source() -> str:
    script = (
        _ROOT / "tools/pegasus/t126_qualification.sh"
    ).read_text(encoding="utf-8")
    start = script.index("import json,os,re,secrets,stat,sys,time\n")
    end = script.index("\nPY\n}", start)
    return script[start:end]


def _fixture_job_result(
        layout, external_path: Path, value: dict[str, object]) -> Path:
    """Artificial canonical fixture; production-shell fixtures never use it."""
    external = _canonical(external_path, value)
    canonical = layout.attempt_dir / "job-result.json"
    canonical.write_bytes(external.read_bytes())
    canonical.chmod(0o600)
    return external


def _rehash_attempt_outcomes(
        ledger_dir: Path, *, payload_update: dict[str, object]) -> None:
    events = [
        load_json_strict(path) for path in sorted(ledger_dir.glob("*.json"))]
    previous = "0" * 64
    for index, event in enumerate(events):
        event["previous_event_sha256"] = previous
        if event["event_type"] in {
                "attempt_outcome_pending", "attempt_outcome"}:
            event["payload"].update(payload_update)
        unhashed = {
            key: value for key, value in event.items()
            if key != "event_sha256"}
        event["event_sha256"] = hashlib.sha256(json.dumps(
            unhashed, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("ascii")).hexdigest()
        previous = event["event_sha256"]
        _canonical(ledger_dir / f"{index:04d}.json", event)


def _job_value(
        job_script_hash: str, *, rc: int = 34,
        failure: str = "pre-member-infrastructure"):
    return {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": rc,
        "failure_class": failure, "nonce": "1" * 32,
        "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    }


def _rehash_receipt_ledger(
        receipt_path: Path, capability, receipt: dict[str, object]) -> None:
    _canonical(receipt_path, receipt)
    receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    ledger_dir = (
        capability.root / "series" / receipt["qualification_series_id"]
        / "attempt-ledger")
    _rehash_attempt_outcomes(
        ledger_dir, payload_update={
            "failure_class": receipt["failure_class"],
            "receipt_sha256": receipt_sha,
        })


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.hooksPath=", "-C", str(repo), *args],
        text=True,
    ).strip()


def _run_t126_admission_fixture(
    tmp_path: Path, *, preflight_rc: int
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path, Path, object, object]:
    repo = tmp_path / "admission-repo"
    script = repo / "tools/pegasus/t126_qualification.sh"
    script.parent.mkdir(parents=True)
    shutil.copy2(_ROOT / "tools/pegasus/t126_qualification.sh", script)
    helper = repo / PREFLIGHT_HELPER_RELATIVE
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(_fixture_preflight_source(), encoding="utf-8")
    (repo / "output").mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture committed admission helper")
    source_commit = _git(repo, "rev-parse", "HEAD")
    # Exercise queued-job isolation: the worktree is newer than the receipt.
    (repo / "queue-drift.txt").write_text("later checkout\n", encoding="utf-8")
    _git(repo, "add", "queue-drift.txt")
    _git(repo, "commit", "-qm", "advance fixture checkout")
    nonce = "b" * 32
    receipt = (
        repo / "output/env/pegasus/qualification/t126/submissions"
        / nonce / "submit-receipt.json"
    )
    _canonical(receipt, {"source_commit": source_commit})
    bin_dir = tmp_path / "job-bin"
    bin_dir.mkdir()
    mkdir_marker = tmp_path / "mkdir-invoked"
    driver_marker = tmp_path / "driver-invoked"
    (bin_dir / "mkdir").write_text(
        "#!/bin/sh\n"
        f": > {shlex.quote(str(mkdir_marker))}\n"
        "exit 1\n",
        encoding="utf-8",
    )
    (bin_dir / "mkdir").chmod(0o755)
    real_python = str(Path(sys.executable).resolve(strict=True))
    (bin_dir / "python3").write_text(
        "#!/bin/sh\n"
        "case \" $* \" in\n"
        f"  *t126_driver.py*) : > {shlex.quote(str(driver_marker))} ;;\n"
        "esac\n"
        f"exec {shlex.quote(real_python)} \"$@\"\n",
        encoding="utf-8",
    )
    (bin_dir / "python3").chmod(0o755)
    job_id = "t126-preflight-" + hashlib.sha256(
        str(tmp_path).encode("utf-8")
    ).hexdigest()[:12]
    scratch = Path("/scr") / f"{job_id}-t126"
    output_before = _path_tree_snapshot(repo / "output")
    scratch_before = _path_tree_snapshot(scratch)
    env = {
        **os.environ,
        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
        "PBS_JOBID": job_id,
        "PBS_O_WORKDIR": str(repo),
        "IZANAGI_SUBMISSION_NONCE": nonce,
        "IZANAGI_TEST_PREFLIGHT_RC": str(preflight_rc),
    }
    completed = subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return (
        completed,
        repo,
        scratch,
        mkdir_marker,
        driver_marker,
        output_before,
        scratch_before,
    )


def _dependency(tmp_path: Path, name: str) -> tuple[Path, str, str]:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    (repo / "source.txt").write_text(name + "\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", name)
    commit = _git(repo, "rev-parse", "HEAD")
    return repo, commit, _git(repo, "rev-parse", "HEAD^{tree}")


def _attempt(
        tmp_path: Path, digit: str, *, clean: bool = False,
        job_id: str = "123.server",
        reservation_policy_overrides: dict[str, object] | None = None,
        job_scratch_root: Path | None = None):
    repo = tmp_path / f"repo-{digit}"
    repo.mkdir()
    gflags, gflags_commit, gflags_tree = _dependency(tmp_path, f"gflags-{digit}")
    glog, glog_commit, glog_tree = _dependency(tmp_path, f"glog-{digit}")
    protocol = load_protocol()
    for relative in REQUIRED_CODE_IDENTITY_PATHS | REQUIRED_SCRIPT_IDENTITY_PATHS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "orchestrator/qualification/t126_control_v1.json":
            shutil.copy2(
                _ROOT / "orchestrator/qualification/t126_control_v1.json", path)
        elif relative in QUALIFICATION_SCHEMA_RELATIVE_PATHS:
            shutil.copy2(_ROOT / relative, path)
        elif relative == RESERVATION_POLICY_RELATIVE_PATH:
            if reservation_policy_overrides is None:
                shutil.copy2(_ROOT / RESERVATION_POLICY_RELATIVE_PATH, path)
            else:
                reservation_policy = json.loads(
                    (_ROOT / RESERVATION_POLICY_RELATIVE_PATH).read_text(
                        encoding="utf-8"))
                reservation_policy.update(reservation_policy_overrides)
                path.write_text(
                    json.dumps(reservation_policy) + "\n", encoding="utf-8")
        elif relative == "tools/pegasus/policy.json":
            policy = json.loads(
                (_ROOT / relative).read_text(encoding="utf-8"))
            policy.update({
                "gflags_expected_head": gflags_commit,
                "glog_expected_head": glog_commit,
            })
            path.write_text(json.dumps(policy) + "\n", encoding="utf-8")
        elif relative == "tools/pegasus/t126_qualification.sh":
            source = _ROOT / relative
            source_mode = stat.S_IMODE(source.stat().st_mode)
            # Git records only whether the owner's executable bit is present.
            assert source_mode & stat.S_IXUSR
            if job_scratch_root is None:
                shutil.copy2(source, path)
            else:
                job_source = source.read_text(encoding="utf-8")
                scratch_assignment = (
                    'SCR_ROOT="/scr/${PBS_JOBID//:/_}-t126"')
                assert job_source.count(scratch_assignment) == 1
                job_source = job_source.replace(
                    scratch_assignment,
                    f"SCR_ROOT={shlex.quote(str(job_scratch_root))}")
                path.write_text(job_source, encoding="utf-8")
                shutil.copymode(source, path)
            assert stat.S_IMODE(path.stat().st_mode) == source_mode
        else:
            path.write_text(f"fixture {relative}\n", encoding="utf-8")
    # The adapter is deliberately not a REQUIRED_CODE_IDENTITY_PATHS member:
    # the committed wrapper resolves it transitively from source_commit.
    helper = repo / PREFLIGHT_HELPER_RELATIVE
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(_fixture_preflight_source(), encoding="utf-8")
    for source_key in ("campaign_lock_path", "wal_path"):
        relative = protocol["source"][source_key]
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_ROOT / relative, path)
    ccbench = tmp_path / f"ccbench-{digit}"
    ccbench.mkdir()
    _git(ccbench, "init", "-q")
    _git(ccbench, "config", "user.email", "fixture@example.invalid")
    _git(ccbench, "config", "user.name", "Fixture")
    (ccbench / "CMakeLists.txt").write_text("fixture\n", encoding="utf-8")
    _git(ccbench, "add", ".")
    _git(ccbench, "commit", "-qm", "ccbench")
    (repo / "external").mkdir(exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
         str(ccbench), "external/ccbench")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    gitlink = _git(repo, "rev-parse", "HEAD:external/ccbench")
    staging = repo / THIRD_PARTY_STAGING_RELATIVE
    staging.mkdir(parents=True)
    gflags.rename(staging / "gflags")
    glog.rename(staging / "glog")

    external = (
        repo / "output/env/pegasus/qualification/t126/submissions"
        / ("1" * 32))
    external.mkdir(parents=True)
    executable = Path(sys.executable).resolve()
    executable_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    executable_row = {
        "path": str(executable), "sha256": executable_hash,
        "version": sys.version.splitlines()[0],
    }
    build_argv = json.loads(json.dumps(REGISTERED_DEPENDENCY_BUILD_ARGV))
    toolchain = {
        "schema_version": "t126-toolchain-manifest/v1",
        "executables": {
            name: dict(executable_row)
            for name in ("python", "cc", "cxx", "cmake", "perf")
        },
        "dependencies": {
            "gflags": {"commit": gflags_commit, "tree": gflags_tree},
            "glog": {"commit": glog_commit, "tree": glog_tree},
        },
        "build_argv": build_argv,
    }
    code_identity = {}
    script_identity = {}
    for relative in REQUIRED_CODE_IDENTITY_PATHS:
        blob = subprocess.check_output(
            ["git", "-C", str(repo), "cat-file", "blob", f"{commit}:{relative}"])
        code_identity[relative] = hashlib.sha256(blob).hexdigest()
    for relative in REQUIRED_SCRIPT_IDENTITY_PATHS:
        blob = subprocess.check_output(
            ["git", "-C", str(repo), "cat-file", "blob", f"{commit}:{relative}"])
        script_identity[relative] = hashlib.sha256(blob).hexdigest()
    series_preimage = {
        "schema_version": "t126-qualification-series-identity/v1",
        "protocol_sha256": protocol_sha256(protocol),
        "superproject_commit": commit,
        "superproject_tree": tree,
        "ccbench_gitlink": gitlink,
        "source_snapshots": {
            "campaign_lock": {
                "path": protocol["source"]["campaign_lock_path"],
                "sha256": protocol["source"]["campaign_lock_sha256"],
            },
            "wal": {
                "path": protocol["source"]["wal_path"],
                "sha256": protocol["source"]["wal_sha256"],
            },
        },
        "pair_roles": protocol["source"]["members"],
        "workload": protocol["workload"],
        "verification": protocol["verification"],
        "threshold": protocol["threshold"],
        "sprt": protocol["sprt"],
        "timing": protocol["timing"],
        "order_seed": protocol["order"]["seed"],
        "code_identity": code_identity,
        "script_identity": script_identity,
        "toolchain_manifest": toolchain,
    }
    series_id = series_identity(series_preimage)
    source_stage_identity = {
        "source_commit": series_preimage["superproject_commit"],
        "source_tree": series_preimage["superproject_tree"],
        "ccbench_gitlink": series_preimage["ccbench_gitlink"],
        "job_script_sha256": series_preimage["script_identity"][
            "tools/pegasus/t126_qualification.sh"],
        "protocol_sha256": series_preimage["code_identity"][
            "orchestrator/qualification/t126_control_v1.json"],
    }
    intent = _canonical(external / "submission-intent.json", {
        "schema_version": "t126-qualification-submission-intent/v1",
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "qualification_series_id": series_id,
        "nonce": "1" * 32,
        "retry_index": 0,
        "retry_from_attempt_id": None,
        "retry_from_receipt_sha256": None,
        "prepared_epoch": 1,
    })
    intent_hash = hashlib.sha256(intent.read_bytes()).hexdigest()
    attempt_preimage = {
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": series_id,
        "pbs_job_id": job_id,
        "nonce": "1" * 32,
        "retry_index": 0,
        "submission_intent_sha256": intent_hash,
    }
    attempt_id = attempt_identity(attempt_preimage)
    job_script_hash = script_identity["tools/pegasus/t126_qualification.sh"]
    invocation = _canonical(external / "qsub-invocation.json", {
        "nonce": "1" * 32,
        "retry_index": 0,
        "submission_intent_sha256": intent_hash,
    })
    invocation_hash = hashlib.sha256(invocation.read_bytes()).hexdigest()
    binding = _canonical(external / "qsub-binding.json", {
        "schema_version": "t126-qsub-binding/v2",
        "job_id": job_id, "nonce": "1" * 32,
        "submission_intent_sha256": intent_hash,
        "qsub_invocation_sha256": invocation_hash,
        "retry_index": 0,
        "qsub_returncode": 0,
        "qsub_stdout_raw": f"Request {job_id} submitted.\n",
    })
    binding_hash = hashlib.sha256(binding.read_bytes()).hexdigest()
    submit = _canonical(external / "submit-receipt.json", {
        "schema_version": "t126-qualification-submit-receipt/v1",
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "qualification_series_id": series_id,
        "qualification_attempt_id": attempt_id,
        "job_id": job_id,
        "nonce": "1" * 32,
        **source_stage_identity,
        "collector_sha256": series_preimage["script_identity"][
            "tools/pegasus/collect_t126_qualification.py"],
        "retry_index": 0,
        "submission_intent_sha256": intent_hash,
        "qsub_invocation_sha256": invocation_hash,
        "qsub_binding_sha256": binding_hash,
    })
    root = QualificationRoot(repo)
    capability = root.issue()
    layout = create_attempt(
        root, capability, series_id=series_id, attempt_id=attempt_id)
    create_json(
        capability, f"attempts/{attempt_id}/protocol.json", protocol)
    create_json(
        capability, f"attempts/{attempt_id}/series-identity.json",
        series_preimage)
    create_json(
        capability, f"attempts/{attempt_id}/attempt-identity.json",
        attempt_preimage)
    prefix = f"attempts/{attempt_id}"
    lock = snapshot_source(
        capability, repo / protocol["source"]["campaign_lock_path"],
        f"{prefix}/source/campaign.lock.snapshot",
        expected_sha256=protocol["source"]["campaign_lock_sha256"])
    wal = snapshot_source(
        capability, repo / protocol["source"]["wal_path"],
        f"{prefix}/source/source-wal.snapshot.jsonl",
        expected_sha256=protocol["source"]["wal_sha256"])
    submit_snapshot = snapshot_source(
        capability, submit, f"{prefix}/source/submission-receipt.snapshot.json",
        expected_sha256=hashlib.sha256(submit.read_bytes()).hexdigest())
    binding_snapshot = snapshot_source(
        capability, binding, f"{prefix}/source/qsub-binding.snapshot.json",
        expected_sha256=binding_hash)
    invocation_snapshot = snapshot_source(
        capability, invocation,
        f"{prefix}/source/qsub-invocation.snapshot.json",
        expected_sha256=invocation_hash)
    for row in (
            lock, wal, submit_snapshot, binding_snapshot,
            invocation_snapshot):
        row["path"] = str(Path(row["path"]).relative_to(prefix))
    create_json(capability, f"{prefix}/source/source-snapshots.json", {
        "schema_version": "t126-qualification-source-snapshots/v1",
        "campaign_lock": {
            "original_path": protocol["source"]["campaign_lock_path"], **lock},
        "wal": {"original_path": protocol["source"]["wal_path"], **wal},
        "submission_receipt": {
            "original_path": (
                "output/env/pegasus/qualification/t126/submissions/"
                + "1" * 32 + "/submit-receipt.json"),
            **submit_snapshot},
        "qsub_binding": {
            "original_path": "external/qsub-binding.json", **binding_snapshot},
        "qsub_invocation": {
            "original_path": "external/qsub-invocation.json",
            **invocation_snapshot},
    })
    toolchain_path = _canonical(
        layout.attempt_dir / "prologue/toolchain-manifest.json", toolchain)
    perf_text = (
        "1,LLC-load-misses\n1,LLC-loads\n"
        "1,instructions\n1,cycles\n")
    _canonical(layout.attempt_dir / "prologue/source-stage-evidence.json", {
        "schema_version": "t126-source-stage-evidence/v1",
        **source_stage_identity,
        "tracked_only": True,
        "immutable_mode": True,
        "policy_sha256": code_identity["tools/pegasus/policy.json"],
        "reservation_policy_sha256": code_identity[
            RESERVATION_POLICY_RELATIVE_PATH],
        "driver_sha256": code_identity[
            "orchestrator/qualification/t126_driver.py"],
        "toolchain_manifest_sha256": hashlib.sha256(
            toolchain_path.read_bytes()).hexdigest(),
        "perf_smoke_returncode": 0,
        "perf_smoke_stdout": "", "perf_smoke_stderr": perf_text,
    })
    create_json(capability, f"{prefix}/reservation.json", {
        "job_id": job_id, "host": "pegasus", "boot_id": "boot",
    })
    fsm = SeriesFSM(
        capability, layout.ledger_relpath, {
            "qualification_series_id": series_id,
            "qualification_attempt_id": attempt_id,
            "pbs_job_id": job_id, "host": "pegasus",
            "boot_id": "boot", "controller_pid": 123,
        }, protocol)
    fsm.open()
    if not clean:
        fsm.reject("pre-member-infrastructure", {"phase": "prologue"})
    else:
        rounds = []
        for round_index in (1, 2):
            order = fsm.open_round(round_index)
            members = {}
            for role in order:
                median = 90.0 if role == "subject" else 100.0
                sink = QualificationEventSink(
                    capability, layout, round_index=round_index, role=role,
                    source_lock_identity_sha256=(
                        protocol["source"]["campaign_lock_sha256"]
                    ),
                )
                payloads = [
                    ("build_start", {"genome": "silo|BACK_OFF=1", "src_token": "x"}),
                    ("build_done", {
                        "trace_bin_sha256": "a" * 64,
                        "perf_bin_sha256": "b" * 64,
                    }),
                    ("verify_done", {
                        "workload": {"tag": "legacy"}, "certified": True,
                        "commits": 10, "aborts": 2, "anomalies": 0,
                        "argv": [
                            "/x/trace", "-ycsb_tuple_num=200",
                            "-ycsb_zipf_skew=0.9", "-ycsb_rratio=50",
                            "-ycsb_rmw=true", "-ycsb_max_ope=5",
                            "-thread_num=4", "-extime=1",
                            "-clocks_per_us=2100",
                        ], "binary_sha256": "a" * 64,
                    }),
                    ("verify_done", {
                        "workload": {"tag": "s2"}, "certified": True,
                        "commits": 20, "aborts": 3, "anomalies": 0,
                        "argv": [
                            "/x/trace", "-ycsb_tuple_num=1000000",
                            "-ycsb_zipf_skew=0.9", "-ycsb_rratio=50",
                            "-ycsb_rmw=false", "-ycsb_max_ope=10",
                            "-thread_num=48", "-extime=3",
                            "-clocks_per_us=2100",
                        ], "binary_sha256": "a" * 64,
                    }),
                    ("bench_done", {
                        "tps": [median] * 5, "median_tps": median,
                        "rep_returncodes": [0] * 5, "settled": True,
                        "unstable": False, "rounds": 1,
                    }),
                    ("commit", {
                        "fitness_tps": median,
                        "verify_configs": ["legacy", "s2"],
                    }),
                ]
                for stage, payload in payloads:
                    if stage == "commit":
                        receipt = receipt_support.qualification_receipt(
                            "variant", payload,
                            lock_identity_sha256=(
                                protocol["source"]["campaign_lock_sha256"]
                            ),
                            operation_identity=f"round-{round_index}-{role}",
                        )
                        sink.emit(
                            layout, "variant", stage, "pegasus", payload,
                            commit_receipt=receipt,
                        )
                    else:
                        sink.emit(layout, "variant", stage, "pegasus", payload)
                event_path = (
                    layout.attempt_dir
                    / f"rounds/{round_index:04d}/{role}/evaluation-events.jsonl")
                admitted = validate_member_evidence(
                    load_jsonl_strict(event_path), expected_role=role,
                    expected_round=round_index,
                    expected_perf_observation=None,
                    expected_lock_identity_sha256=(
                        protocol["source"]["campaign_lock_sha256"]
                    ),
                )
                runtime = {
                    "schema_version": "t126-qualification-member-runtime/v1",
                    "round_index": round_index, "member_role": role,
                    "source_wal_variant":
                        protocol["source"]["members"][role]["source_wal_variant"],
                    "genome": protocol["source"]["members"][role]["genome"],
                    "full_source_digest": ("c" if role == "subject" else "d") * 64,
                    "live_member_id": _member_identity(
                        ccbench_gitlink=gitlink,
                        source_token=("c" if role == "subject" else "d") * 64,
                        genome=_parse_genome(
                            protocol["source"]["members"][role]["genome"]),
                        role=role,
                    ),
                }
                create_json(
                    capability,
                    f"attempts/{attempt_id}/rounds/{round_index:04d}/"
                    f"{role}/member-runtime.json",
                    runtime)
                admitted.update({
                    "live_member_id": runtime["live_member_id"],
                    "full_source_digest": runtime["full_source_digest"],
                    "source_wal_variant": runtime["source_wal_variant"],
                    "evidence_ref": file_record(
                        event_path, relative_to=layout.attempt_dir),
                    "terminal_monotonic": float(round_index),
                })
                members[role] = admitted
                fsm.member_terminal(
                    round_index, role, median, admitted["evidence_ref"])
            decision = fsm.round_terminal(
                round_index, subject_median_tps=90.0,
                reference_median_tps=100.0)
            payload = fsm.events[-1]["payload"]
            rounds.append({
                "round_index": round_index, "member_order": list(order),
                "subject": members["subject"], "reference": members["reference"],
                "relative": payload["relative"], "direction": payload["direction"],
                "bit": payload["bit"], "llr_hex": payload["llr_hex"],
                "sprt_terminal": decision,
            })
            if decision == "continuing":
                fsm.wait_satisfied(round_index, 1800.0)
        fsm.terminal(2)
        manifest = [
            file_record(path, relative_to=layout.attempt_dir)
            for path in sorted(layout.attempt_dir.rglob("*"))
            if path.is_file() and not path.is_symlink()
        ]
        series_result = {
            "schema_version": "t126-qualification-series-result/v1",
            "qualification_lineage": "t126-only",
            "authority": "evidence-only/no-promotion",
            "hold_enforced": False, "statistical_claim": "none",
            "qualification_series_id": series_id,
            "qualification_attempt_id": attempt_id,
            "terminal": "lower_boundary", "execution_integrity": "valid",
            "expectation_match": "not-applicable-observational-smoke",
            "bits": [0, 0], "rounds": rounds,
            "ledger": file_record(
                layout.attempt_dir / "series-ledger.jsonl",
                relative_to=layout.attempt_dir),
            "evidence_manifest": manifest,
            "timing_envelope": {
                "job_started_monotonic_ns": 1,
                "completed_monotonic_ns": 2,
                "elapsed_ns": 1, "wmax_s": 29100,
            },
        }
        validate_json_schema(
            "t126_series_result_schema.json", series_result)
        create_json(
            capability, f"attempts/{attempt_id}/series-result.json",
            series_result)
    attempt_ledger = SeriesAttemptLedger(
        capability, series_id, protocol["retry"]["eligible_reasons"])
    attempt_ledger.claim_initial(
        nonce="1" * 32, submission_intent_sha256=intent_hash)
    attempt_ledger.bind_submitted(
        retry_index=0, nonce="1" * 32, job_id=job_id,
        attempt_id=attempt_id,
        qsub_invocation_sha256=invocation_hash,
        submission_evidence_sha256=binding_hash)
    scheduler_suffix = job_id.split(".", 1)[0]
    stdout = external / f"job.o{scheduler_suffix}"
    stderr = external / f"job.e{scheduler_suffix}"
    accounting = external / "accounting"
    stdout.parent.mkdir(parents=True, exist_ok=True)
    stdout.write_text("job stdout\n", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    accounting.write_text(
                          f"Request ID = {job_id}\n"
                          "Exit_status = 0\nresources_used.walltime = 1\n",
                          encoding="utf-8")
    return (repo, capability, layout, attempt_id, submit, stdout, stderr,
            accounting, job_script_hash)


def test_reservation_policy_and_job_headers_freeze_wmax_and_walltime():
    reservation_policy = json.loads(
        (_ROOT / RESERVATION_POLICY_RELATIVE_PATH).read_text())
    calculated = (
        reservation_policy["t126_qualification_prologue_cap_s"]
        + 16 * reservation_policy["t126_qualification_member_cap_s"]
        + 7 * reservation_policy["t126_qualification_round_gap_s"]
        + reservation_policy["t126_qualification_attestation_cap_s"]
        + reservation_policy["t126_qualification_finalize_reserve_s"]
    )
    assert reservation_policy["t126_qualification_walltime"] == "10:00:00"
    assert reservation_policy["t126_qualification_walltime_s"] == 36000
    assert reservation_policy["t126_qualification_member_cap_s"] == 900
    assert reservation_policy["t126_qualification_round_gap_s"] == 1800
    assert reservation_policy["t126_qualification_prologue_cap_s"] == 900
    assert reservation_policy["t126_qualification_attestation_cap_s"] == 600
    assert reservation_policy["t126_qualification_finalize_reserve_s"] == 600
    assert reservation_policy["t126_qualification_wmax_s"] == 29100
    assert calculated == reservation_policy["t126_qualification_wmax_s"] == 29100
    assert reservation_policy["t126_qualification_walltime_s"] == 36000
    assert reservation_policy["t126_qualification_walltime"] == "10:00:00"
    script = (_ROOT / "tools/pegasus/t126_qualification.sh").read_text()
    assert "#PBS -l elapstim_req=10:00:00" in script
    assert "run_with_budget 120" in script and "run_with_budget 180" in script
    assert "gcc-13" in script and "g++-13" in script


def test_shared_pegasus_policy_owns_no_t126_qualification_keys():
    """T-126 keys stay out of the byte-pinned shared policy.

    共有 policy の正当な更新では凍結 evidence を書き換えず、歴史 binding と
    現行 bytes を分離する。接頭辞走査は ``t126_`` key を拒否し、現行 bytes の
    明示 sha256 pin は key 名変更、接頭辞なし key 追加、値の書換え、空白だけの
    整形を含む無断 drift を赤にする。凍結 binding は歴史 oracle と一致し、
    現行値とは不一致でなければならない。
    """
    policy_relative = "tools/pegasus/policy.json"
    policy_path = _ROOT / policy_relative
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert not [key for key in policy if key.startswith("t126_")]
    assert RESERVATION_POLICY_RELATIVE_PATH in REQUIRED_CODE_IDENTITY_PATHS
    assert "orchestrator/campaign/build_admission.py" in REQUIRED_CODE_IDENTITY_PATHS
    pinned = json.loads(
        (_ROOT / "output/env/pegasus/silo_ladder_rung1"
         / "silo_ladder_rung1.json").read_text(encoding="utf-8"))
    pinned_policy = pinned["binding"]["policy"]
    assert pinned_policy["path"] == policy_relative
    current_policy_sha256 = hashlib.sha256(
        policy_path.read_bytes()).hexdigest()
    assert current_policy_sha256 == EXPECTED_CURRENT_PEGASUS_POLICY_SHA256, (
        "intentional policy update requires refreshing the single shared "
        "EXPECTED_CURRENT_PEGASUS_POLICY_SHA256 golden in "
        "orchestrator/tests/pegasus_policy_expected_goldens.py: "
        f"sha256({policy_relative})={current_policy_sha256}"
    )
    assert pinned_policy["sha256"] == EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256
    assert pinned_policy["sha256"] != current_policy_sha256


def test_required_code_identity_closes_activation_receipt_imports_without_records():
    required = {
        "orchestrator/campaign/__init__.py",
        "orchestrator/campaign/calibration_verify.py",
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/env_contract_activation.py",
        "orchestrator/campaign/env_attestation.py",
        "orchestrator/campaign/execution_guard.py",
        "orchestrator/campaign/site_policy.py",
        "orchestrator/calibrator/__init__.py",
        "orchestrator/calibrator/effective_clock_policy.py",
        "orchestrator/calibrator/schema_v2.py",
        "orchestrator/calibrator/tsc.py",
    }
    assert required <= REQUIRED_CODE_IDENTITY_PATHS
    record_directory = "orchestrator/campaign/env_contract_activations"
    assert not {
        path for path in REQUIRED_CODE_IDENTITY_PATHS
        if path == record_directory or path.startswith(record_directory + "/")
    }


def test_series_preimage_exact_code_identity_set_tracks_activation_closure(
    tmp_path,
):
    (_, _, layout, _, _, _, _, _, _) = _attempt(
        tmp_path, "activation-identity-closure"
    )
    preimage = load_json_strict(layout.attempt_dir / "series-identity.json")
    assert set(preimage["code_identity"]) == REQUIRED_CODE_IDENTITY_PATHS
    assert series_identity(preimage)

    missing_leaf = deepcopy(preimage)
    missing_leaf["code_identity"].pop(
        "orchestrator/campaign/env_contract_activation.py"
    )
    with pytest.raises(ProtocolError, match="required set mismatch"):
        series_identity(missing_leaf)


@pytest.mark.parametrize(
    "relative",
    sorted(REQUIRED_CODE_IDENTITY_PATHS | REQUIRED_SCRIPT_IDENTITY_PATHS),
)
def test_every_required_identity_path_is_tracked_in_this_repo(relative):
    """Every identity input must be a tracked blob of THIS repository.

    ``series_identity`` hashes ``git cat-file blob`` output for each of these
    paths, and the submit script refuses to run when one of them is untracked.
    An identity path that exists only in the working tree would therefore make
    the contract unsatisfiable at submission time while every in-process test
    (which stages its own fixture repository) still passes.  This is the only
    check that binds the constant set to the real repository index.
    """
    completed = subprocess.run(
        ["git", "-c", "core.hooksPath=", "-C", str(_ROOT),
         "ls-files", "--error-unmatch", "--", relative],
        text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, (
        f"required identity path is not tracked: {relative}\n"
        + completed.stderr)


def test_reservation_policy_wiring_is_pinned_to_the_contract_constant():
    """Pin the hand-copied reservation-policy wiring to the contract constant.

    The reservation policy has one producer pair (the submit script, which
    reads the repository copy, and the job script, which reads the source-stage
    copy and hashes it into the prologue evidence) and one consumer
    (``_verify_prologue_evidence``).  The relative path is copied verbatim into
    the shells, where no import can keep it equal to
    ``RESERVATION_POLICY_RELATIVE_PATH``; nothing but this test fails when a
    rename leaves one of those copies behind.
    """
    relative = RESERVATION_POLICY_RELATIVE_PATH
    submit = (
        _ROOT / "tools/pegasus/submit_t126_qualification.sh"
    ).read_text(encoding="utf-8")
    job = (
        _ROOT / "tools/pegasus/t126_qualification.sh"
    ).read_text(encoding="utf-8")
    driver = (
        _ROOT / "orchestrator/qualification/t126_driver.py"
    ).read_text(encoding="utf-8")

    # Producer 1: the submit script resolves, guards and tracked-checks the
    # repository copy of exactly this path.
    assert f'RESERVATION_POLICY="$REPO_ROOT/{relative}"' in submit
    assert (
        '[[ -f "$RESERVATION_POLICY" && ! -L "$RESERVATION_POLICY" ]]'
        in submit)
    assert submit.count(f"\n  {relative} \\\n") == 2
    assert (
        'git -C "$REPO_ROOT" ls-files --error-unmatch -- "$tracked"' in submit)

    # Producer 2: the job script reads the source-stage copy of the same path
    # and writes its sha256 under the evidence key the consumer requires.
    assert f'RESERVATION_POLICY="$SOURCE_STAGE/{relative}"' in job
    assert (
        '   "reservation_policy_sha256":digest(os.path.join(\n'
        f'       source,"{relative}")),\n'
    ) in job

    # Consumer: the driver compares that evidence key against the identity
    # registered under the same constant.
    assert (
        'value["reservation_policy_sha256"] != identities[ '
        'RESERVATION_POLICY_RELATIVE_PATH]'
    ) in re.sub(r"\s+", " ", driver)

    # The file the three sites reach is the v1 reservation policy document.
    assert json.loads(
        (_ROOT / relative).read_text(encoding="utf-8")
    )["schema_version"] == "t126-qualification-reservation-policy/v1"


@pytest.mark.parametrize(
    "relative",
    [
        "tools/pegasus/submit_t126_qualification.sh",
        "tools/pegasus/t126_qualification.sh",
    ],
)
def test_shell_scripts_pass_bash_syntax(relative):
    completed = subprocess.run(
        ["bash", "-n", str(_ROOT / relative)],
        text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_t126_wrapper_preflight_rejection_is_nonmutating_and_starts_no_driver(
        tmp_path):
    (
        completed,
        repo,
        scratch,
        mkdir_marker,
        driver_marker,
        output_before,
        scratch_before,
    ) = _run_t126_admission_fixture(tmp_path, preflight_rc=3)

    assert completed.returncode == 3
    assert completed.stdout == ""
    assert completed.stderr == '{"gate":"fixture","reason":"rejected"}\n'
    assert _path_tree_snapshot(repo / "output") == output_before
    assert _path_tree_snapshot(scratch) == scratch_before
    assert not mkdir_marker.exists()
    assert not driver_marker.exists()
    assert not list((repo / "output").rglob("job-result.json"))
    assert not list((repo / "output").rglob("target-rejection.json"))
    assert not (repo / "output/env/pegasus/qualification/t126/job-staging").exists()


def test_t126_wrapper_accepting_source_commit_preflight_reaches_first_write(
        tmp_path):
    (
        completed,
        repo,
        scratch,
        mkdir_marker,
        driver_marker,
        output_before,
        scratch_before,
    ) = _run_t126_admission_fixture(tmp_path, preflight_rc=0)

    # The mkdir sentinel is the first wrapper-owned mutation attempt.  It
    # fails deliberately, before any durable namespace is created.
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert mkdir_marker.is_file()
    assert not driver_marker.exists()
    assert _path_tree_snapshot(repo / "output") == output_before
    assert _path_tree_snapshot(scratch) == scratch_before


def test_t126_wrapper_streams_helper_blob_without_hash_literal() -> None:
    source = (
        _ROOT / "tools/pegasus/t126_qualification.sh"
    ).read_text(encoding="utf-8")
    assert (
        'git -C "$REPO_ROOT" cat-file blob "$PREFLIGHT_HELPER_SPEC"'
        in source
    )
    assert (
        '| "$PY" -I -B - t126 --repo-root "$REPO_ROOT"'
        in source
    )
    preflight = source[:source.index('mkdir -p "$QUAL_ROOT/job-staging"')]
    assert not re.search(r"[0-9a-f]{64}", preflight)


@pytest.mark.parametrize("target_name", ["submit-receipt.json", "job-result.json"])
@pytest.mark.parametrize(
    ("boundary", "published"),
    [
        ("after-open", False),
        ("after-short-write", False),
        ("after-fsync", False),
        ("after-publish", True),
    ],
)
def test_shell_publishers_recover_all_hard_crash_boundaries(
        tmp_path, target_name, boundary, published):
    target = tmp_path / target_name
    data = b'{"complete":true}\n'
    program = (
        "from pathlib import Path\n"
        "from orchestrator.qualification.atomic_publish import publish_bytes\n"
        f"publish_bytes(Path({str(target)!r}),{data!r},"
        f"crash_boundary={boundary!r})\n")
    crashed = subprocess.run(
        [sys.executable, "-I", "-B", "-c",
         "import sys;"
         f"sys.path.insert(0,{str(_HERE.parents[1])!r});"
         + program],
        capture_output=True, text=True)
    assert crashed.returncode in {91, 92, 93, 94}
    assert target.exists() is published
    assert list(tmp_path.glob(f".{target_name}.create-*"))
    recovered = publish_bytes(target, data)
    assert recovered.read_bytes() == data
    assert not list(tmp_path.glob(f".{target_name}.create-*"))


@pytest.mark.parametrize("target_present", [False, True])
@pytest.mark.parametrize(
    "suffix",
    [
        "0-0123456789abcdef",
        "00-0123456789abcdef",
        "001-0123456789abcdef",
        "pid-0123456789abcdef",
        "123-0123456789abcdeF",
        "123-0123456789abcde",
        "123-0123456789abcdef0",
    ],
)
def test_persistent_publisher_rejects_generator_unreachable_suffixes(
        tmp_path, target_present, suffix):
    target = tmp_path / "publisher.json"
    data = b'{"complete":true}\n'
    if target_present:
        target.write_bytes(data)
        target.chmod(0o600)
    stage = tmp_path / f".{target.name}.create-{suffix}"
    if target_present:
        os.link(target, stage)
    else:
        stage.write_bytes(data)
        stage.chmod(0o600)
    before = _directory_snapshot(tmp_path)
    with pytest.raises(AtomicPublishError):
        publish_bytes(target, data)
    assert _directory_snapshot(tmp_path) == before


@pytest.mark.parametrize("target_present", [False, True])
@pytest.mark.parametrize(
    "suffix",
    [
        "0-0123456789abcdef",
        "00-0123456789abcdef",
        "001-0123456789abcdef",
        "pid-0123456789abcdef",
        "123-0123456789abcdeF",
        "123-0123456789abcde",
        "123-0123456789abcdef0",
    ],
)
def test_embedded_terminal_publisher_rejects_generator_unreachable_suffixes(
        tmp_path, target_present, suffix):
    target = tmp_path / "job-result.json"
    if target_present:
        target.write_bytes(b"canonical-placeholder\n")
        target.chmod(0o600)
    stage = tmp_path / f".{target.name}.create-{suffix}"
    if target_present:
        os.link(target, stage)
    else:
        stage.write_bytes(b"abandoned-placeholder\n")
        stage.chmod(0o600)
    before = _directory_snapshot(tmp_path)
    completed = subprocess.run(
        [
            sys.executable, "-I", "-S", "-B", "-c",
            _embedded_terminal_publisher_source(),
            str(target), "123.server", "34", "a" * 64, "1" * 32,
            "1", "2", "29100", "0", "b" * 64, "c" * 64,
        ],
        capture_output=True, text=True)
    assert completed.returncode != 0
    assert _directory_snapshot(tmp_path) == before


def test_partial_canonical_job_result_closes_via_accounting_recovery(tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "j")
    partial = layout.attempt_dir / "job-result.json"
    partial.write_bytes(b'{"partial":')
    partial.chmod(0o600)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 137\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    value = load_json_strict(receipt)
    assert value["attempt_phase"] == "job-result-recovery"
    assert value["job_result"] is None
    assert value["failure_class"] == "job-result-publication-failed"
    assert value["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "valid"


@pytest.mark.parametrize(
    ("clean", "rc", "failure"),
    [(False, 34, "pre-member-infrastructure"), (True, 0, "none")],
)
def test_semantic_invalid_job_result_closes_idempotently_as_nonretry(
        tmp_path, clean, rc, failure):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, f"semantic-{rc}", clean=clean)
    value = _job_value(job_script_hash, rc=rc, failure=failure)
    value["wmax_s"] = 29101
    _canonical(layout.attempt_dir / "job-result.json", value)
    accounting.write_text(
        f"Request ID = 123.server\nExit_status = {rc}\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    ledger_dir = (
        QualificationRoot(repo).path / "series"
        / load_json_strict(first)["qualification_series_id"]
        / "attempt-ledger")
    ledger_bytes = {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))}
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(second)
    assert second == first and second.read_bytes() == first_bytes
    assert {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))} == ledger_bytes
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["job_result"] is None
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        second, repo_root=repo).integrity_status == "valid"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            second, repo, load_protocol())


@pytest.mark.parametrize("semantic_fault", ["wmax", "series-timing"])
def test_semantic_invalid_early_result_is_preserved_before_adoption(
        tmp_path, semantic_fault):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, "early-semantic-" + semantic_fault, clean=True)
    timing = load_json_strict(
        layout.attempt_dir / "series-result.json")["timing_envelope"]
    value = _job_value(job_script_hash, rc=0, failure="none")
    value.update({
        "job_started_monotonic_ns": timing["job_started_monotonic_ns"],
        "completed_monotonic_ns": timing["completed_monotonic_ns"],
        "elapsed_ns": (
            timing["completed_monotonic_ns"]
            - timing["job_started_monotonic_ns"]),
    })
    if semantic_fault == "wmax":
        value["wmax_s"] = 29101
    else:
        value["job_started_monotonic_ns"] += 1
        value["elapsed_ns"] = (
            value["completed_monotonic_ns"]
            - value["job_started_monotonic_ns"])
    early = (
        capability.root / "job-staging"
        / ("123.server." + "1" * 32))
    early.mkdir(parents=True)
    original = _canonical(early / "job-result.json", value)
    original_stat = original.lstat()
    original_bytes = original.read_bytes()
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    evidence_path = (
        layout.attempt_dir / "rejected-evidence/early-job-result.json")
    evidence_bytes = evidence_path.read_bytes()
    ledger_dir = (
        capability.root / "series" / load_json_strict(first)[
            "qualification_series_id"] / "attempt-ledger")
    ledger_bytes = {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))}
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    evidence = load_json_strict(evidence_path)
    assert second == first and second.read_bytes() == first.read_bytes()
    assert evidence_path.read_bytes() == evidence_bytes
    assert {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))} == ledger_bytes
    assert original.read_bytes() == original_bytes
    assert not (layout.attempt_dir / "job-result.json").exists()
    assert evidence["source_path"] == original.relative_to(
        capability.root).as_posix()
    assert evidence["sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert {
        key: evidence[key]
        for key in (
            "st_dev", "st_ino", "st_nlink", "st_mode", "st_uid", "st_size")
    } == {
        "st_dev": original_stat.st_dev,
        "st_ino": original_stat.st_ino,
        "st_nlink": original_stat.st_nlink,
        "st_mode": original_stat.st_mode,
        "st_uid": original_stat.st_uid,
        "st_size": original_stat.st_size,
    }
    receipt = load_json_strict(second)
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False


@pytest.mark.parametrize("target_rejection", [False, True])
@pytest.mark.parametrize("semantic_fault", ["wmax", "series-timing"])
def test_semantic_invalid_early_conflict_preserves_b_and_closes_with_a(
        tmp_path, semantic_fault, target_rejection):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path,
         f"early-conflict-{semantic_fault}-{int(target_rejection)}",
         clean=True)
    timing = load_json_strict(
        layout.attempt_dir / "series-result.json")["timing_envelope"]
    canonical_value = _job_value(job_script_hash, rc=0, failure="none")
    canonical_value.update({
        "job_started_monotonic_ns": timing["job_started_monotonic_ns"],
        "completed_monotonic_ns": timing["completed_monotonic_ns"],
        "elapsed_ns": (
            timing["completed_monotonic_ns"]
            - timing["job_started_monotonic_ns"]),
    })
    canonical = _canonical(
        layout.attempt_dir / "job-result.json", canonical_value)
    canonical_bytes = canonical.read_bytes()
    canonical_stat = canonical.lstat()
    rejected_value = deepcopy(canonical_value)
    if semantic_fault == "wmax":
        rejected_value["wmax_s"] = 29101
    else:
        rejected_value["job_started_monotonic_ns"] += 1
        rejected_value["elapsed_ns"] = (
            rejected_value["completed_monotonic_ns"]
            - rejected_value["job_started_monotonic_ns"])
    early = (
        capability.root / "job-staging"
        / ("123.server." + "1" * 32))
    rejected = _canonical(early / "job-result.json", rejected_value)
    rejected_bytes = rejected.read_bytes()
    rejected_stat = rejected.lstat()
    if target_rejection:
        _canonical(early / "target-rejection.json", {
            "schema_version": "t126-job-result-target-rejection/v1",
            "qualification_series_id":
                load_json_strict(submit)["qualification_series_id"],
            "qualification_attempt_id": attempt_id,
            "pbs_job_id": "123.server",
            "nonce": "1" * 32,
            "reason": "submitted-attempt-target-invalid",
        })
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    evidence_path = (
        layout.attempt_dir / "rejected-evidence/early-job-result.json")
    evidence_bytes = evidence_path.read_bytes()
    ledger_dir = (
        capability.root / "series" / load_json_strict(first)[
            "qualification_series_id"] / "attempt-ledger")
    ledger_bytes = {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))}
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first and second.read_bytes() == first_bytes
    assert evidence_path.read_bytes() == evidence_bytes
    assert {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))} == ledger_bytes
    assert canonical.read_bytes() == canonical_bytes
    assert rejected.read_bytes() == rejected_bytes
    assert (
        canonical.lstat().st_dev, canonical.lstat().st_ino,
        canonical.lstat().st_nlink, canonical.lstat().st_mode,
        canonical.lstat().st_uid, canonical.lstat().st_size,
    ) == (
        canonical_stat.st_dev, canonical_stat.st_ino,
        canonical_stat.st_nlink, canonical_stat.st_mode,
        canonical_stat.st_uid, canonical_stat.st_size,
    )
    evidence = load_json_strict(evidence_path)
    assert evidence["source_path"] == rejected.relative_to(
        capability.root).as_posix()
    assert evidence["sha256"] == hashlib.sha256(rejected_bytes).hexdigest()
    assert {
        key: evidence[key]
        for key in (
            "st_dev", "st_ino", "st_nlink", "st_mode", "st_uid", "st_size")
    } == {
        "st_dev": rejected_stat.st_dev,
        "st_ino": rejected_stat.st_ino,
        "st_nlink": rejected_stat.st_nlink,
        "st_mode": rejected_stat.st_mode,
        "st_uid": rejected_stat.st_uid,
        "st_size": rejected_stat.st_size,
    }
    receipt = load_json_strict(second)
    assert receipt["job_result"] is not None
    assert (layout.attempt_dir / receipt["job_result"]["path"]
            ).read_bytes() == canonical_bytes
    assert receipt["attempt_phase"] == "job-result-recovery"
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        second, repo_root=repo).integrity_status == "valid"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            second, repo, load_protocol())
    assert SeriesAttemptLedger(
        capability, receipt["qualification_series_id"],
        load_protocol()["retry"]["eligible_reasons"]).replay.state == (
            "initial_failed")


def test_series_verifier_admits_only_phase_two_rejected_evidence_namespace(
        tmp_path):
    (_, _, layout, _, _, _, _, _, _) = _attempt(
        tmp_path, "series-phase-two-rejected", clean=True)
    rejected = _canonical(
        layout.attempt_dir / "rejected-evidence/reason.json",
        {"reason": "semantic-invalid-early-result"})
    assert rejected.is_file()
    assert verify_attempt(
        layout.attempt_dir).integrity_status == "valid"

    unrelated = _canonical(
        layout.attempt_dir / "unreferenced-arbitrary.json",
        {"unrelated": True})
    assert unrelated.is_file()
    verified = verify_attempt(layout.attempt_dir)
    assert verified.integrity_status == "invalid"
    assert "unreferenced in-job evidence: ['unreferenced-arbitrary.json']" in (
        " ".join(verified.errors))


@pytest.mark.parametrize("caller", ["receipt", "rejected-evidence"])
def test_shared_create_writer_collector_callers_preserve_unsafe_stage(
        tmp_path, caller):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "writer-" + caller)
    if caller == "receipt":
        stage = layout.attempt_dir / (
            ".attempt-failure-receipt.json.create-malformed")
    else:
        early = (
            capability.root / "job-staging"
            / ("123.server." + "1" * 32))
        early.mkdir(parents=True)
        rejected = early / "job-result.json"
        rejected.write_bytes(b'{"invalid":')
        rejected.chmod(0o600)
        evidence_dir = layout.attempt_dir / "rejected-evidence"
        evidence_dir.mkdir()
        stage = evidence_dir / (
            ".early-job-result.bytes.create-malformed")
    stage.write_bytes(b"unsafe-stage\n")
    stage.chmod(0o600)
    stage_stat = stage.lstat()
    stage_bytes = stage.read_bytes()
    with pytest.raises(QualificationArtifactError):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    current = stage.lstat()
    assert (
        current.st_dev, current.st_ino, current.st_nlink,
        current.st_mode, current.st_uid, current.st_size,
    ) == (
        stage_stat.st_dev, stage_stat.st_ino, stage_stat.st_nlink,
        stage_stat.st_mode, stage_stat.st_uid, stage_stat.st_size,
    )
    assert stage.read_bytes() == stage_bytes


def test_submitter_has_exact_opt_in_and_imports_persistent_publisher():
    script = (_ROOT / "tools/pegasus/submit_t126_qualification.sh").read_text()
    assert 'qsub -v "IZANAGI_SUBMISSION_NONCE=$NONCE" "$JOB_SCRIPT"' in script
    assert "--retry-from" in script
    assert "validate_failure_receipt_for_retry" in script
    assert "SeriesAttemptLedger" in script
    assert "claim_initial" in script and "claim_retry" in script
    assert '"retry_from_series_id":retry_series_id or None' in script
    assert "full source/tree/gitlink identity unavailable" in script
    assert "required execution input is not tracked" in script
    assert "from orchestrator.qualification.atomic_publish import publish_bytes" in script


def test_job_script_has_no_persistent_import_and_has_isolated_publisher():
    job_script = (_ROOT / "tools/pegasus/t126_qualification.sh").read_text()
    assert "from orchestrator.qualification.atomic_publish import publish_bytes" not in job_script
    assert '"$PY" -I -S -B - "$JOB_RESULT"' in job_script
    assert "import json,os,re,secrets,stat,sys,time" in job_script
    assert 'ATTEMPT_DIR="$QUAL_ROOT/attempts/$SUBMITTED_ATTEMPT_ID"' in job_script
    assert "Driver stdout is diagnostic only" in job_script


def test_m6a_missing_accounting_file_is_the_only_negative_then_closes(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "b")
    job = _fixture_job_result(
        layout, accounting.parent / "job.json",
        {
            "schema_version": "t126-qualification-job-result/v1",
            "pbs_jobid": "123.server", "driver_rc": 34,
            "failure_class": "pre-member-infrastructure",
            "nonce": "1" * 32, "job_script_sha256": job_script_hash,
            "completed_epoch": 1, "job_started_monotonic_ns": 1,
            "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
        },
    )
    accounting.unlink()
    with pytest.raises(
            QualificationArtifactError, match="cannot open regular file"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting,
        )
    assert not (layout.attempt_dir / "post-job").exists()

    accounting.write_text(
        "Request ID = 123.server\n"
        "Exit_status = 34\nresources_used.walltime = 1\n",
        encoding="utf-8",
    )
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting,
    )
    receipt = load_json_strict(receipt_path)
    assert receipt["schema_version"] == (
        "t126-qualification-attempt-failure-receipt/v1")
    assert receipt["observations_recorded"] == 0
    assert receipt["retry_eligible"] is True
    assert validate_failure_receipt_for_retry(
        receipt_path, repo, load_protocol())["qualification_attempt_id"] == attempt_id
    assert not (layout.attempt_dir / "final-qualification-receipt.json").exists()
    schema = json.loads((_ROOT / "orchestrator/qualification/"
                         "t126_failure_receipt_schema.json").read_text())
    assert list(Draft7Validator(schema).iter_errors(receipt)) == []
    nested_bad = dict(receipt, submission_receipt={})
    assert list(Draft7Validator(schema).iter_errors(nested_bad))


@pytest.mark.parametrize(
    "failure_class",
    ["job-result-publication-failed", "job-result-accounting-mismatch"])
def test_failure_schema_forces_new_classes_nonretry(failure_class):
    record = {"path": "evidence", "size": 0, "sha256": "0" * 64}
    receipt = {
        "schema_version":
            "t126-qualification-attempt-failure-receipt/v1",
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "qualification_series_id": "1" * 64,
        "qualification_attempt_id": "2" * 64,
        "job_id": "123.server",
        "retry_index": 0,
        "scheduler_exit_status": 34,
        "submission_receipt": record,
        "submission_evidence_kind": "submit-receipt",
        "qsub_binding": None,
        "job_result": None,
        "scheduler_stdout": record,
        "scheduler_stderr": record,
        "accounting": record,
        "closure_manifest": [record],
        "attempt_phase": "job-result-recovery",
        "failure_class": failure_class,
        "observations_recorded": 0,
        "retry_eligible": False,
    }
    schema = json.loads((_ROOT / "orchestrator/qualification/"
                         "t126_failure_receipt_schema.json").read_text())
    assert list(Draft7Validator(schema).iter_errors(receipt)) == []
    receipt["retry_eligible"] = True
    assert list(Draft7Validator(schema).iter_errors(receipt))


def test_accounting_missing_request_is_the_only_invalid_field():
    data = (
        b"Exit_status = 34\n"
        b"resources_used.walltime = 1\n")
    with pytest.raises(
            collector.CollectionError, match="one exact request ID"):
        collector._parse_accounting(data)


def test_m6b_exact_accounting_job_id_is_single_effective_anchor(
        tmp_path, monkeypatch):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "6")
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 999.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="canonical job ID"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert not (layout.attempt_dir / "post-job").exists()
    monkeypatch.setattr(
        collector, "_validate_accounting_result_anchor",
        lambda *_args, **_kwargs: None)
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "valid"


def test_m6c_accounting_rc_vs_job_rc_closes_as_exact_mismatch(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "7")
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "member-rejected",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 30\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    value = load_json_strict(receipt)
    assert value["failure_class"] == "job-result-accounting-mismatch"
    assert value["attempt_phase"] == "job-result-accounting-mismatch"
    assert value["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "valid"


def test_series_result_and_post_job_final_receipt_are_distinct(
        tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "c", clean=True)
    job = _fixture_job_result(
        layout, accounting.parent / "job.json",
        {
            "schema_version": "t126-qualification-job-result/v1",
            "pbs_jobid": "123.server", "driver_rc": 0,
            "failure_class": "none", "nonce": "1" * 32,
            "job_script_sha256": job_script_hash, "completed_epoch": 1,
            "job_started_monotonic_ns": 1,
            "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
        },
    )
    final_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting,
    )
    final = load_json_strict(final_path)
    series = load_json_strict(layout.attempt_dir / "series-result.json")
    assert final["schema_version"] == "t126-qualification-final-receipt/v1"
    assert final["series_result"]["path"] == "series-result.json"
    assert (layout.attempt_dir / "series-result.json").is_file()
    assert not (layout.attempt_dir / "attempt-failure-receipt.json").exists()
    schema = json.loads((_ROOT / "orchestrator/qualification/"
                         "t126_final_receipt_schema.json").read_text())
    assert list(Draft7Validator(schema).iter_errors(final)) == []
    assert list(Draft7Validator(schema).iter_errors(
        dict(final, closure_manifest=[{}])))
    series_schema = json.loads(
        (_ROOT / "orchestrator/qualification/"
         "t126_series_result_schema.json").read_text())
    assert list(Draft7Validator(series_schema).iter_errors(series)) == []
    bad_series = json.loads(json.dumps(series))
    bad_series["rounds"][0]["subject"]["evidence_ref"] = {}
    assert list(Draft7Validator(series_schema).iter_errors(bad_series))
    event = load_jsonl_strict(layout.attempt_dir / "series-ledger.jsonl")[0]
    event_schema = json.loads(
        (_ROOT / "orchestrator/qualification/"
         "t126_event_schema.json").read_text())
    assert list(Draft7Validator(event_schema).iter_errors(event)) == []
    bad_event = json.loads(json.dumps(event))
    bad_event["identity"] = {}
    assert list(Draft7Validator(event_schema).iter_errors(bad_event))
    verified = collector.verify_post_job_receipt(final_path, repo_root=repo)
    assert verified.integrity_status == "valid"
    scheduler_copy = layout.attempt_dir / final["scheduler_stdout"]["path"]
    scheduler_copy.write_text("tampered\n", encoding="utf-8")
    tampered = collector.verify_post_job_receipt(final_path, repo_root=repo)
    assert tampered.integrity_status == "invalid"


def test_collector_fault_injection_and_success_rerun_are_exact_idempotent(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "d")
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    tripped = {"value": False}

    def fail_once(stage):
        if stage == "after-accounting-copy" and not tripped["value"]:
            tripped["value"] = True
            raise OSError("simulated quota boundary")

    with pytest.raises(OSError, match="quota"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting, fault_inject=fail_once)
    assert not (layout.attempt_dir / "attempt-failure-receipt.json").exists()
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first
    assert hashlib.sha256(second.read_bytes()).hexdigest() == first_hash


@pytest.mark.parametrize(
    ("stage", "digit"),
    [("after-receipt-publish", "p"), ("after-outcome-pending", "q")],
)
def test_receipt_is_invalid_until_idempotent_outcome_finalize(
        tmp_path, stage, digit):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, digit)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")

    def crash(current):
        if current == stage:
            raise OSError("transaction crash")

    with pytest.raises(OSError, match="transaction"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting, fault_inject=crash)
    receipt = layout.attempt_dir / "attempt-failure-receipt.json"
    assert receipt.is_file()
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "invalid"
    finalized = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert finalized == receipt
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "valid"


@pytest.mark.parametrize(
    ("ledger_shape", "digit"),
    [("missing", "u"), ("intent-only", "v"), ("other-attempt", "w")],
)
def test_collect_rejects_missing_partial_or_other_attempt_ledger_before_writes(
        tmp_path, ledger_shape, digit):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, digit)
    series_preimage = load_json_strict(layout.attempt_dir / "series-identity.json")
    series_id = series_identity(series_preimage)
    ledger_dir = (
        capability.root / "series" / series_id / "attempt-ledger")
    shutil.rmtree(ledger_dir)
    protocol = load_protocol(layout.attempt_dir / "protocol.json")
    if ledger_shape != "missing":
        ledger = SeriesAttemptLedger(
            capability, series_id, protocol["retry"]["eligible_reasons"])
        ledger.claim_initial(
            nonce="1" * 32,
            submission_intent_sha256=load_json_strict(
                layout.attempt_dir / "attempt-identity.json"
            )["submission_intent_sha256"])
        if ledger_shape == "other-attempt":
            ledger.bind_submitted(
                retry_index=0, nonce="1" * 32, job_id="999.server",
                attempt_id="f" * 64,
                qsub_invocation_sha256="d" * 64,
                submission_evidence_sha256="e" * 64)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(
            collector.CollectionError, match="ledger|submitted attempt"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert not (layout.attempt_dir / "post-job").exists()


def test_final_receipt_becomes_invalid_if_ledger_outcome_is_removed(tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "y", clean=True)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 0, "failure_class": "none",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    series_id = load_json_strict(receipt)["qualification_series_id"]
    ledger_dir = capability.root / "series" / series_id / "attempt-ledger"
    (ledger_dir / "0003.json").unlink()
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "invalid"


@pytest.mark.parametrize(
    "payload_update",
    [
        {"terminal": "upper_boundary"},
        {"observations_recorded": 1},
    ],
)
def test_ledger_outcome_semantics_cannot_be_coherently_rehashed(
        tmp_path, payload_update):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "l", clean=True)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 0, "failure_class": "none",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    value = load_json_strict(receipt)
    ledger_dir = (
        capability.root / "series" / value["qualification_series_id"]
        / "attempt-ledger")
    _rehash_attempt_outcomes(ledger_dir, payload_update=payload_update)
    verified = collector.verify_post_job_receipt(receipt, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "semantic payload/state" in " ".join(verified.errors)


def test_ledger_failure_class_cannot_be_coherently_rehashed(tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "m")
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    value = load_json_strict(receipt)
    ledger_dir = (
        capability.root / "series" / value["qualification_series_id"]
        / "attempt-ledger")
    _rehash_attempt_outcomes(
        ledger_dir, payload_update={"failure_class": "pre-attestation"})
    verified = collector.verify_post_job_receipt(receipt, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "semantic payload/state" in " ".join(verified.errors)


def test_post_verifier_rejects_semantic_job_result_after_coherent_hash_rewrite(
        tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "x", clean=True)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 0, "failure_class": "none",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    pointed = layout.attempt_dir / receipt["job_result"]["path"]
    _canonical(pointed, {})
    replacement = file_record(pointed, relative_to=layout.attempt_dir)
    receipt["job_result"] = replacement
    receipt["closure_manifest"] = [
        replacement if row["path"] == replacement["path"] else row
        for row in receipt["closure_manifest"]
    ]
    _canonical(receipt_path, receipt)
    receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    series_id = receipt["qualification_series_id"]
    ledger_dir = capability.root / "series" / series_id / "attempt-ledger"
    events = [
        load_json_strict(path)
        for path in sorted(ledger_dir.glob("*.json"))
    ]
    for index in (2, 3):
        events[index]["payload"]["receipt_sha256"] = receipt_sha
        if index == 3:
            events[index]["previous_event_sha256"] = events[2]["event_sha256"]
        unhashed = {
            key: value for key, value in events[index].items()
            if key != "event_sha256"
        }
        events[index]["event_sha256"] = hashlib.sha256(json.dumps(
            unhashed, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("ascii")).hexdigest()
        if index == 2:
            events[3]["previous_event_sha256"] = events[2]["event_sha256"]
        _canonical(ledger_dir / f"{index:04d}.json", events[index])
    verified = collector.verify_post_job_receipt(
        receipt_path, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "job-result" in " ".join(verified.errors)


def test_m6d_final_series_pointer_swap_is_single_closure_reason(tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "8", clean=True)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 0, "failure_class": "none",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    alternate = layout.attempt_dir / "post-job/alternate-series-result.json"
    shutil.copy2(layout.attempt_dir / "series-result.json", alternate)
    alternate_record = file_record(alternate, relative_to=layout.attempt_dir)
    receipt["series_result"] = alternate_record
    receipt["closure_manifest"].append(alternate_record)
    receipt["closure_manifest"].sort(key=lambda row: row["path"])
    _canonical(receipt_path, receipt)
    receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    ledger_dir = (
        capability.root / "series" / receipt["qualification_series_id"]
        / "attempt-ledger")
    pending = load_json_strict(ledger_dir / "0002.json")
    pending["payload"]["receipt_sha256"] = receipt_sha
    pending["event_sha256"] = hashlib.sha256(json.dumps(
        {key: value for key, value in pending.items()
         if key != "event_sha256"},
        sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")).hexdigest()
    _canonical(ledger_dir / "0002.json", pending)
    final = load_json_strict(ledger_dir / "0003.json")
    final["previous_event_sha256"] = pending["event_sha256"]
    final["payload"]["receipt_sha256"] = receipt_sha
    final["event_sha256"] = hashlib.sha256(json.dumps(
        {key: value for key, value in final.items()
         if key != "event_sha256"},
        sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")).hexdigest()
    _canonical(ledger_dir / "0003.json", final)
    verified = collector.verify_post_job_receipt(
        receipt_path, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "canonical artifact path" in " ".join(verified.errors)


def test_canonical_rc30_job_result_is_authoritative_when_cli_omits_it(tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "r")
    _canonical(layout.attempt_dir / "job-result.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 30,
        "failure_class": "member-rejected", "nonce": "1" * 32,
        "job_script_sha256": job_script_hash, "completed_epoch": 1,
        "job_started_monotonic_ns": 1, "completed_monotonic_ns": 2,
        "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 30\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt = load_json_strict(collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting))
    assert receipt["failure_class"] == "member-rejected"
    assert receipt["retry_eligible"] is False
    assert receipt["attempt_phase"] == "attempt"


def test_public_verifier_reanchors_coherent_rc30_to_rc34_swap(tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "n")
    canonical = _canonical(layout.attempt_dir / "job-result.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 30,
        "failure_class": "member-rejected", "nonce": "1" * 32,
        "job_script_sha256": job_script_hash, "completed_epoch": 1,
        "job_started_monotonic_ns": 1, "completed_monotonic_ns": 2,
        "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 30\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert load_json_strict(canonical)["driver_rc"] == 30
    receipt = load_json_strict(receipt_path)
    pointed = layout.attempt_dir / receipt["job_result"]["path"]
    _canonical(pointed, {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure", "nonce": "1" * 32,
        "job_script_sha256": job_script_hash, "completed_epoch": 1,
        "job_started_monotonic_ns": 1, "completed_monotonic_ns": 2,
        "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting_copy = layout.attempt_dir / receipt["accounting"]["path"]
    accounting_copy.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    replacements = {
        receipt["job_result"]["path"]:
            file_record(pointed, relative_to=layout.attempt_dir),
        receipt["accounting"]["path"]:
            file_record(accounting_copy, relative_to=layout.attempt_dir),
    }
    receipt["job_result"] = replacements[receipt["job_result"]["path"]]
    receipt["accounting"] = replacements[receipt["accounting"]["path"]]
    receipt["closure_manifest"] = [
        replacements.get(row["path"], row)
        for row in receipt["closure_manifest"]]
    receipt["scheduler_exit_status"] = 34
    receipt["failure_class"] = "pre-member-infrastructure"
    receipt["retry_eligible"] = True
    _canonical(receipt_path, receipt)
    receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    ledger_dir = (
        capability.root / "series" / receipt["qualification_series_id"]
        / "attempt-ledger")
    _rehash_attempt_outcomes(
        ledger_dir, payload_update={
            "failure_class": "pre-member-infrastructure",
            "receipt_sha256": receipt_sha,
        })
    verified = collector.verify_post_job_receipt(receipt_path, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "canonical attempt bytes" in " ".join(verified.errors)


def test_final_consumer_rejects_job_series_start_and_completion_mismatch(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "o", clean=True)
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 0, "failure_class": "none",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 0,
        "completed_monotonic_ns": 1, "elapsed_ns": 1, "wmax_s": 29100,
    })
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    value = load_json_strict(receipt)
    assert value["failure_class"] == "job-result-publication-failed"
    assert value["retry_eligible"] is False
    assert not (layout.attempt_dir / "final-qualification-receipt.json").exists()
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "valid"


@pytest.mark.parametrize(
    ("rc", "failure", "digit"),
    [
        (143, "job-result-publication-failed", "t"),
        (129, "job-result-publication-failed", "h"),
        (137, "job-result-publication-failed", "k"),
    ],
)
def test_late_terminal_after_series_result_closes_as_failure(
        tmp_path, rc, failure, digit):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, digit, clean=True)
    accounting.write_text(
        f"Request ID = 123.server\nExit_status = {rc}\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["attempt_phase"] == "job-result-recovery"
    assert receipt["failure_class"] == failure
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"


@pytest.mark.parametrize("payload", [{}, {"extra": True}])
def test_job_result_exact_schema_rejects_empty_and_extra_keys(
        tmp_path, payload):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "j")
    job = _canonical(accounting.parent / "bad-job.json", payload)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="job-result"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)


def test_coherent_alternate_scheduler_job_swap_cannot_replace_attempt_binding(
        tmp_path):
    (repo, _, layout, attempt_id, submit, _, _,
     _, job_script_hash) = _attempt(tmp_path, "z")
    swapped_dir = tmp_path / "swapped"
    swapped_intent = load_json_strict(
        layout.attempt_dir / "attempt-identity.json")[
            "submission_intent_sha256"]
    swapped_invocation = _canonical(
        swapped_dir / "qsub-invocation.json", {
            "nonce": "2" * 32, "retry_index": 0,
            "submission_intent_sha256": swapped_intent,
        })
    swapped_invocation_sha = hashlib.sha256(
        swapped_invocation.read_bytes()).hexdigest()
    swapped_binding = _canonical(swapped_dir / "qsub-binding.json", {
        "schema_version": "t126-qsub-binding/v2",
        "job_id": "999.server", "nonce": "2" * 32,
        "submission_intent_sha256": swapped_intent,
        "qsub_invocation_sha256": swapped_invocation_sha,
        "retry_index": 0, "qsub_returncode": 0,
        "qsub_stdout_raw": "Request 999.server submitted.\n",
    })
    original = load_json_strict(submit)
    swapped = dict(
        original, job_id="999.server", nonce="2" * 32,
        qsub_invocation_sha256=swapped_invocation_sha,
        qsub_binding_sha256=hashlib.sha256(
            swapped_binding.read_bytes()).hexdigest())
    swapped_attempt = attempt_identity({
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": original["qualification_series_id"],
        "pbs_job_id": "999.server", "nonce": "2" * 32,
        "retry_index": 0,
        "submission_intent_sha256":
            original["submission_intent_sha256"],
    })
    swapped["qualification_attempt_id"] = swapped_attempt
    swapped_submit = _canonical(swapped_dir / "submit-receipt.json", swapped)
    swapped_job = _canonical(swapped_dir / "job-result.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "999.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "2" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    swapped_stdout = swapped_dir / "job.o999"
    swapped_stderr = swapped_dir / "job.e999"
    swapped_accounting = swapped_dir / "accounting"
    swapped_stdout.write_text("", encoding="utf-8")
    swapped_stderr.write_text("", encoding="utf-8")
    swapped_accounting.write_text(
        "Request ID = 999.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(
            collector.CollectionError, match="attempt|ledger|canonical root"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=swapped_submit, job_result=swapped_job,
            scheduler_stdout=swapped_stdout, scheduler_stderr=swapped_stderr,
            accounting=swapped_accounting)
    assert not (layout.attempt_dir / "post-job").exists()


def test_collector_rejects_static_nonce_parent_symlink_before_write(tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "i")
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    nonce_dir = submit.parent
    outside = tmp_path / "moved-valid-submission"
    nonce_dir.rename(outside)
    nonce_dir.symlink_to(outside, target_is_directory=True)
    with pytest.raises(collector.CollectionError, match="contains a symlink"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=nonce_dir / submit.name, job_result=job,
            scheduler_stdout=outside / stdout.name,
            scheduler_stderr=outside / stderr.name,
            accounting=outside / accounting.name)
    assert not (layout.attempt_dir / "post-job").exists()


def test_collector_rejects_substring_job_id_same_output_and_receipt_tamper(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "e")
    job = _fixture_job_result(layout, accounting.parent / "job.json", {
        "schema_version": "t126-qualification-job-result/v1",
        "pbs_jobid": "123.server", "driver_rc": 34,
        "failure_class": "pre-member-infrastructure",
        "nonce": "1" * 32, "job_script_sha256": job_script_hash,
        "completed_epoch": 1, "job_started_monotonic_ns": 1,
        "completed_monotonic_ns": 2, "elapsed_ns": 1, "wmax_s": 29100,
    })
    accounting.write_text(
        "Request ID = 9123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="canonical job ID"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="canonical .o/.e|distinct"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stdout,
            accounting=accounting)
    tampered_submit = _canonical(accounting.parent / "tampered-submit.json", {
        **json.loads(submit.read_text()), "request": {"queue": "other"},
    })
    with pytest.raises(collector.CollectionError, match="canonical nonce path"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=tampered_submit, job_result=job,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)


def test_accounting_only_sigkill_recovers_pre_attempt_failure_namespace(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "f")
    submission_dir = (
        repo / "output/env/pegasus/qualification/t126/submissions" / ("1" * 32))
    submission_dir.mkdir(parents=True, exist_ok=True)
    bound_submit = submission_dir / "submit-receipt.json"
    assert bound_submit == submit
    shutil.copy2(
        layout.attempt_dir / "series-identity.json",
        submission_dir / "series-identity.json")
    assert submit.with_name("qsub-binding.json").is_file()
    backup = tmp_path / "pre-attempt-backup"
    layout.attempt_dir.rename(backup)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 137\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit.with_name("qsub-binding.json"),
        job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["attempt_phase"] == "pre-attempt-recovery"
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            receipt_path, repo, load_protocol())


def test_deleted_normal_submit_cannot_be_reclassified_into_recovered_retry(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "deleted-normal")
    submission_dir = submit.parent
    shutil.copy2(
        layout.attempt_dir / "series-identity.json",
        submission_dir / "series-identity.json")
    binding = submit.with_name("qsub-binding.json")
    submit.unlink()
    layout.attempt_dir.rename(tmp_path / "deleted-normal-attempt")
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 137\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=binding, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["submission_evidence_kind"] == "recovered-qsub-binding"
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            receipt_path, repo, load_protocol())


def test_recorded_schema_live_bytes_match_committed_identity(tmp_path):
    (repo, _, layout, _, _, _, _, _, _) = _attempt(tmp_path, "schema-match")
    preimage = load_json_strict(layout.attempt_dir / "series-identity.json")
    protocol = load_protocol(layout.attempt_dir / "protocol.json")
    policy = json.loads(
        (repo / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    reservation_policy = json.loads(
        (repo / RESERVATION_POLICY_RELATIVE_PATH).read_text(encoding="utf-8"))

    assert QUALIFICATION_SCHEMA_RELATIVE_PATHS == frozenset({
        "orchestrator/qualification/t126_marker_schema.json",
        "orchestrator/qualification/t126_event_schema.json",
        "orchestrator/qualification/t126_evaluation_event_schema.json",
        "orchestrator/qualification/t126_series_result_schema.json",
        "orchestrator/qualification/t126_final_receipt_schema.json",
        "orchestrator/qualification/t126_failure_receipt_schema.json",
    })
    assert verify_recorded_series_identity(
        git_repo_root=repo, attempt_dir=layout.attempt_dir,
        preimage=preimage, protocol=protocol, policy=policy,
        reservation_policy=reservation_policy,
    ) == series_identity(preimage)


def test_m12_relaxed_live_schema_cannot_expand_receipt_acceptance(
        monkeypatch, tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "m12")
    job = _fixture_job_result(
        layout, accounting.parent / "job.json",
        _job_value(job_script_hash))
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=job,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"

    receipt = load_json_strict(receipt_path)
    del receipt["authority"]
    _rehash_receipt_ledger(receipt_path, capability, receipt)
    original = collector.verify_post_job_receipt(receipt_path, repo_root=repo)
    assert original.integrity_status == "invalid"
    assert "authority" in " ".join(original.errors)

    schema_name = "t126_failure_receipt_schema.json"
    real_schema_bytes = qualification_artifacts.qualification_schema_bytes
    schema = json.loads(real_schema_bytes(schema_name))
    assert "authority" in schema["required"]
    assert schema["additionalProperties"] is False
    del schema["required"]
    relaxed = json.dumps(schema).encode("utf-8")
    assert not list(Draft7Validator(schema).iter_errors(receipt))

    def relaxed_schema_bytes(name):
        if name == schema_name:
            return relaxed
        return real_schema_bytes(name)

    monkeypatch.setattr(
        qualification_artifacts,
        "qualification_schema_bytes",
        relaxed_schema_bytes)
    verified = collector.verify_post_job_receipt(receipt_path, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "live qualification schema differs" in " ".join(verified.errors)


def test_m13_qualification_schema_memo_drift_fails_closed(monkeypatch):
    schema_name = "t126_failure_receipt_schema.json"
    schema_path = _ROOT / "orchestrator/qualification" / schema_name
    disk_bytes = schema_path.read_bytes()
    memo = qualification_artifacts._QUALIFICATION_SCHEMA_BYTES

    monkeypatch.setitem(memo, schema_name, disk_bytes)
    assert qualification_artifacts.qualification_schema_bytes(
        schema_name) is disk_bytes

    drifted = b"memoized qualification schema differs from disk"
    assert drifted != disk_bytes
    monkeypatch.setitem(memo, schema_name, drifted)
    with pytest.raises(QualificationArtifactError, match=schema_name):
        qualification_artifacts.qualification_schema_bytes(schema_name)
    assert memo[schema_name] is drifted


def test_identity_consumer_rejects_git_chain_tool_hash_and_snapshot_traversal(
        tmp_path):
    (repo, _, layout, _, _, _, _, _, _) = _attempt(tmp_path, "9")
    preimage = load_json_strict(layout.attempt_dir / "series-identity.json")
    protocol = load_protocol(layout.attempt_dir / "protocol.json")
    policy = json.loads(
        (repo / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    reservation_policy = json.loads(
        (repo / RESERVATION_POLICY_RELATIVE_PATH).read_text(encoding="utf-8"))
    bad_tree = json.loads(json.dumps(preimage))
    bad_tree["superproject_tree"] = "0" * 40
    with pytest.raises(IdentityVerificationError, match="tree/gitlink"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=bad_tree, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy)
    bad_tool = json.loads(json.dumps(preimage))
    bad_tool["toolchain_manifest"]["executables"]["python"]["sha256"] = "0" * 64
    with pytest.raises(IdentityVerificationError, match="executable hash"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=bad_tool, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy)
    manifest_path = layout.attempt_dir / "source/source-snapshots.json"
    manifest = load_json_strict(manifest_path)
    manifest["campaign_lock"]["path"] = "../outside"
    manifest_path.write_bytes(
        json.dumps(
            manifest, sort_keys=True, separators=(",", ":")
        ).encode("ascii") + b"\n")
    with pytest.raises(IdentityVerificationError, match="unsafe"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=preimage, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy)


def test_identity_consumer_rejects_protocol_policy_dependency_and_build_argv_tamper(
        tmp_path):
    (repo, _, layout, _, _, _, _, _, _) = _attempt(tmp_path, "i")
    preimage = load_json_strict(layout.attempt_dir / "series-identity.json")
    protocol = load_protocol(layout.attempt_dir / "protocol.json")
    policy = json.loads(
        (repo / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    reservation_policy = json.loads(
        (repo / RESERVATION_POLICY_RELATIVE_PATH).read_text(encoding="utf-8"))

    shadow = json.loads(json.dumps(preimage))
    shadow["workload"]["threads"] = 47
    with pytest.raises(IdentityVerificationError, match="source pair|snapshot"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=shadow, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy)

    build = json.loads(json.dumps(preimage))
    build["toolchain_manifest"]["build_argv"]["gflags_build"][-1] = "47"
    with pytest.raises(IdentityVerificationError, match="build argv"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=build, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy)

    dependency = json.loads(json.dumps(preimage))
    dep_repo = repo / THIRD_PARTY_STAGING_RELATIVE / "gflags"
    (dep_repo / "second.txt").write_text("second\n", encoding="utf-8")
    _git(dep_repo, "add", ".")
    _git(dep_repo, "commit", "-qm", "second")
    dependency["toolchain_manifest"]["dependencies"]["gflags"] = {
        "commit": _git(dep_repo, "rev-parse", "HEAD"),
        "tree": _git(dep_repo, "rev-parse", "HEAD^{tree}"),
    }
    with pytest.raises(IdentityVerificationError, match="expected head"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=dependency, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy)

    changed_policy = dict(policy, gflags_expected_head="0" * 40)
    with pytest.raises(IdentityVerificationError, match="approved policy"):
        verify_recorded_series_identity(
            git_repo_root=repo, attempt_dir=layout.attempt_dir,
            preimage=preimage, protocol=protocol, policy=changed_policy,
            reservation_policy=reservation_policy)

    for mutation in (
            {"t126_qualification_wmax_s": 29101},
            {"t126_qualification_walltime": "09:00:00"},
            {"t126_qualification_member_term_grace_s": 11},
    ):
        changed_reservation_policy = dict(reservation_policy, **mutation)
        with pytest.raises(
                IdentityVerificationError, match="approved reservation policy"):
            verify_recorded_series_identity(
                git_repo_root=repo, attempt_dir=layout.attempt_dir,
                preimage=preimage, protocol=protocol, policy=policy,
                reservation_policy=changed_reservation_policy)


def test_consumer_rejects_coherently_rehashed_source_stage_perf_claim(
        tmp_path):
    (_, _, layout, _, _, _, _, _, _) = _attempt(
        tmp_path, "g", clean=True)
    evidence_path = layout.attempt_dir / "prologue/source-stage-evidence.json"
    evidence = load_json_strict(evidence_path)
    evidence["tracked_only"] = False
    _canonical(evidence_path, evidence)
    result_path = layout.attempt_dir / "series-result.json"
    result = load_json_strict(result_path)
    replacement = file_record(evidence_path, relative_to=layout.attempt_dir)
    result["evidence_manifest"] = [
        replacement if row["path"] == replacement["path"] else row
        for row in result["evidence_manifest"]
    ]
    _canonical(result_path, result)
    verified = verify_attempt(layout.attempt_dir)
    assert verified.integrity_status == "invalid"
    assert "prologue" in " ".join(verified.errors)


def _install_python3_wrapper(
        fake_bin: Path, calls: Path, *,
        injection_marker: Path | None = None) -> Path:
    wrapper = fake_bin / "python3"
    real_python = str(Path(sys.executable).resolve(strict=True))
    marker = "" if injection_marker is None else str(injection_marker)
    wrapper.write_text(
        "#!/bin/sh\n"
        "kind=other\n"
        "target=0\n"
        "for arg in \"$@\"; do\n"
        "  case \"$arg\" in\n"
        "    *sys.version_info*) kind=version ;;\n"
        "    *time.monotonic_ns*) kind=monotonic ;;\n"
        "    */submit-receipt.json) kind=receipt ;;\n"
        "    */t126_reservation_policy_v1.json) kind=reservation; target=1 ;;\n"
        "  esac\n"
        "done\n"
        f"printf '%s\\n' \"$kind\" >> {shlex.quote(str(calls))}\n"
        f"injection_marker={shlex.quote(marker)}\n"
        "if [ \"$target\" -eq 1 ] && [ -n \"$injection_marker\" ] "
        "&& [ ! -e \"$injection_marker\" ]; then\n"
        f"  {shlex.quote(real_python)} \"$@\"\n"
        "  rc=$?\n"
        "  [ \"$rc\" -eq 0 ] || exit \"$rc\"\n"
        "  : > \"$injection_marker\"\n"
        f"  printf '%s\\n' injected >> {shlex.quote(str(calls))}\n"
        "  exit 73\n"
        "fi\n"
        f"exec {shlex.quote(real_python)} \"$@\"\n",
        encoding="utf-8")
    wrapper.chmod(0o755)
    assert wrapper.is_file() and not wrapper.is_symlink()
    return wrapper


def _install_job_dependency_marker(
        fake_bin: Path, repo: Path, marker: Path) -> None:
    policy = json.loads(
        (repo / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    gflags_source = str(repo / THIRD_PARTY_STAGING_RELATIVE / "gflags")
    real_git = shutil.which("git")
    assert real_git is not None
    wrapper = fake_bin / "git"
    wrapper.write_text(
        "#!/bin/sh\n"
        f"if [ \"$1\" = -C ] && [ \"$2\" = {shlex.quote(gflags_source)} ] "
        "&& [ \"$3\" = rev-parse ] && [ \"$4\" = HEAD ]; then\n"
        f"  : > {shlex.quote(str(marker))}\n"
        "  exit 73\n"
        "fi\n"
        f"exec {shlex.quote(real_git)} \"$@\"\n",
        encoding="utf-8")
    wrapper.chmod(0o755)


def _submit_fixture(
        tmp_path: Path, *,
        reservation_policy_overrides: dict[str, object] | None = None,
        ) -> tuple[Path, Path, Path]:
    repo = tmp_path / "submit-repo"
    shutil.copytree(
        _ROOT / "orchestrator", repo / "orchestrator",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    tools = repo / "tools/pegasus"
    tools.mkdir(parents=True)
    for name in (
            "submit_t126_qualification.sh", "t126_qualification.sh",
            "collect_t126_qualification.py", "policy.json"):
        shutil.copy2(_ROOT / "tools/pegasus" / name, tools / name)
    for key in ("campaign_lock_path", "wal_path"):
        relative = load_protocol()["source"][key]
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_ROOT / relative, target)
    gflags, gflags_commit, _ = _dependency(tmp_path, "submit-gflags")
    glog, glog_commit, _ = _dependency(tmp_path, "submit-glog")
    fake_bin = tmp_path / "submit-bin"
    fake_bin.mkdir()
    calls = tmp_path / "submit-calls"
    for compiler in ("gcc-13", "g++-13"):
        path = fake_bin / compiler
        path.write_text(
            "#!/bin/sh\nprintf '%s\\n' 'fixture compiler 1'\n",
            encoding="utf-8")
        path.chmod(0o755)
    perf = fake_bin / "perf-real"
    perf.write_text(
        "#!/bin/sh\n"
        "case \" $* \" in\n"
        "  *' --version '*) printf '%s\\n' 'perf fixture 1'; exit 0 ;;\n"
        "esac\n"
        "output=; previous=\n"
        "for argument in \"$@\"; do\n"
        "  [ \"$previous\" != -o ] || output=$argument\n"
        "  previous=$argument\n"
        "done\n"
        "events='1,,LLC-load-misses\n1,,LLC-loads\n"
        "1,,instructions\n1,,cycles'\n"
        "if [ -n \"$output\" ]; then\n"
        "  printf '%s\\n' \"$events\" > \"$output\"\n"
        "else\n"
        "  printf '%s\\n' \"$events\" >&2\n"
        "fi\n",
        encoding="utf-8")
    perf.chmod(0o755)
    policy_path = tools / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy.update({
        "gflags_expected_head": gflags_commit,
        "glog_expected_head": glog_commit,
        "perf_candidates": [str(perf)],
    })
    policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")
    if reservation_policy_overrides is not None:
        reservation_policy_path = repo / RESERVATION_POLICY_RELATIVE_PATH
        reservation_policy = json.loads(
            reservation_policy_path.read_text(encoding="utf-8"))
        reservation_policy.update(reservation_policy_overrides)
        reservation_policy_path.write_text(
            json.dumps(reservation_policy) + "\n", encoding="utf-8")
    ccbench = tmp_path / "submit-ccbench"
    ccbench.mkdir()
    _git(ccbench, "init", "-q")
    _git(ccbench, "config", "user.email", "fixture@example.invalid")
    _git(ccbench, "config", "user.name", "Fixture")
    (ccbench / "CMakeLists.txt").write_text("fixture\n", encoding="utf-8")
    _git(ccbench, "add", ".")
    _git(ccbench, "commit", "-qm", "ccbench")
    (repo / "external").mkdir()
    (repo / "output").mkdir(exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
         str(ccbench), "external/ccbench")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "submit fixture")
    staging = repo / THIRD_PARTY_STAGING_RELATIVE
    staging.mkdir(parents=True)
    gflags.rename(staging / "gflags")
    glog.rename(staging / "glog")
    return repo, fake_bin, calls


def _install_scheduler_stubs(
        fake_bin: Path, calls: Path, *, visible_job: str = "98765.nqsv",
        perf_unsupported: bool = False) -> Path:
    for name in ("pegasusinfo", "rbudgetcheck", "check_quota"):
        body = {
            "pegasusinfo": "Pegasus fixture",
            "rbudgetcheck": "remaining 100",
            "check_quota": "10%",
        }[name]
        path = fake_bin / name
        path.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' {shlex.quote(name)} >> {shlex.quote(str(calls))}\n"
            f"printf '%s\\n' {shlex.quote(body)}\n",
            encoding="utf-8")
        path.chmod(0o755)
    qstat = fake_bin / "qstat"
    qstat.write_text(
        "#!/bin/sh\n"
        f"printf 'qstat %s\\n' \"$*\" >> {shlex.quote(str(calls))}\n"
        "if [ \"$1\" = -Q ]; then\n"
        "  printf '%s\\n' 'gen_S ENABLE ACTIVE Max: 86400S'\n"
        "else\n"
        f"  printf '%s\\n' 'Request ID = {visible_job}'\n"
        "fi\n",
        encoding="utf-8")
    qstat.chmod(0o755)
    qsub_args = fake_bin.parent / "qsub.args"
    qsub = fake_bin / "qsub"
    qsub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\0' \"$@\" > {shlex.quote(str(qsub_args))}\n"
        f"printf '%s\\n' qsub >> {shlex.quote(str(calls))}\n"
        "printf '%s\\n' 'Request 98765.nqsv submitted.'\n",
        encoding="utf-8")
    qsub.chmod(0o755)
    if perf_unsupported:
        perf = fake_bin / "perf-real"
        perf.write_text(
            "#!/bin/sh\n"
            "case \" $* \" in\n"
            "  *' --version '*) printf '%s\\n' 'perf fixture 1' ;;\n"
            "  *) printf '%s\\n' '<not supported>' >&2 ;;\n"
            "esac\n",
            encoding="utf-8")
        perf.chmod(0o755)
        literal_perf = fake_bin / "perf"
        literal_perf.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
        literal_perf.chmod(0o755)
    return qsub_args


def _run_submit(
        repo: Path, fake_bin: Path, *,
        extra_env: dict[str, str] | None = None,
        retry_from: Path | None = None,
        dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra_env or {})
    argv = ["bash", str(repo / "tools/pegasus/submit_t126_qualification.sh")]
    if dry_run:
        argv.append("--dry-run")
    if retry_from is not None:
        argv.extend(["--retry-from", str(retry_from)])
    return subprocess.run(
        argv, cwd=repo, env=env, capture_output=True, text=True)


@pytest.mark.parametrize(
    ("prologue_cap_s", "attestation_cap_s", "finalize_reserve_s"),
    [(1500, 0, 600), (1500, 600, 0), (900, 1200, 0)],
)
def test_submit_rejects_compensating_cap_drift_before_scheduler_calls(
        tmp_path, prologue_cap_s, attestation_cap_s, finalize_reserve_s):
    repo, fake_bin, scheduler_calls = _submit_fixture(
        tmp_path,
        reservation_policy_overrides={
            "t126_qualification_prologue_cap_s": prologue_cap_s,
            "t126_qualification_attestation_cap_s": attestation_cap_s,
            "t126_qualification_finalize_reserve_s": finalize_reserve_s,
        })
    _install_scheduler_stubs(fake_bin, scheduler_calls)
    _install_python3_wrapper(fake_bin, tmp_path / "python-calls")

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "T-126 reservation policy mismatch\n"
    assert not scheduler_calls.exists()


def test_submit_rejects_nul_in_walltime_before_scheduler_calls(tmp_path):
    repo, fake_bin, scheduler_calls = _submit_fixture(
        tmp_path,
        reservation_policy_overrides={
            "t126_qualification_walltime": "10:00:" + chr(0) + "00",
        })
    _install_scheduler_stubs(fake_bin, scheduler_calls)
    _install_python3_wrapper(fake_bin, tmp_path / "python-calls")

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "T-126 reservation policy mismatch\n"
    assert not scheduler_calls.exists()


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("t126_qualification_member_cap_s", 900.0),
        ("t126_qualification_round_gap_s", 1800.0),
        ("t126_qualification_prologue_cap_s", 900.0),
        ("t126_qualification_attestation_cap_s", 600.0),
        ("t126_qualification_finalize_reserve_s", 600.0),
    ],
    ids=[
        "member-cap", "round-gap", "prologue-cap", "attestation-cap",
        "finalize-reserve",
    ],
)
def test_submit_rejects_each_single_layer_equal_float_type_drift(
        tmp_path, key, bad_value):
    """Each equal-float passes value checks, leaving only strict-int rejection."""
    repo, fake_bin, scheduler_calls = _submit_fixture(
        tmp_path, reservation_policy_overrides={key: bad_value})
    _install_scheduler_stubs(fake_bin, scheduler_calls)
    _install_python3_wrapper(fake_bin, tmp_path / "python-calls")

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "T-126 reservation policy type mismatch\n"
    assert not scheduler_calls.exists()


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("t126_qualification_walltime_s", 36000.0),
        ("t126_qualification_wmax_s", 29100.0),
    ],
    ids=["walltime-s", "wmax"],
)
def test_submit_rejects_each_mapping_masked_equal_float_type_drift(
        tmp_path, key, bad_value):
    """These equal-floats kill only a Python-type + Bash-mapping mutation."""
    repo, fake_bin, scheduler_calls = _submit_fixture(
        tmp_path, reservation_policy_overrides={key: bad_value})
    _install_scheduler_stubs(fake_bin, scheduler_calls)
    _install_python3_wrapper(fake_bin, tmp_path / "python-calls")

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "T-126 reservation policy type mismatch\n"
    assert not scheduler_calls.exists()


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("t126_qualification_attestation_cap_s", 600.0000000000001),
        ("t126_qualification_round_gap_s", True),
        ("t126_qualification_walltime", 10),
    ],
    ids=["near-float", "bool", "walltime-not-string"],
)
def test_submit_rejects_overdetermined_reservation_policy_type_drift(
        tmp_path, key, bad_value):
    """Pin diagnostics, not semantic kills: value/sum checks also reject.

    In particular, no non-string JSON value is ``==`` to the canonical
    walltime string, so its type guard is redundant on the accepted set.
    """
    repo, fake_bin, scheduler_calls = _submit_fixture(
        tmp_path, reservation_policy_overrides={key: bad_value})
    _install_scheduler_stubs(fake_bin, scheduler_calls)
    _install_python3_wrapper(fake_bin, tmp_path / "python-calls")

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "T-126 reservation policy type mismatch\n"
    assert not scheduler_calls.exists()


def test_submit_reservation_reader_rejects_python_failure_after_complete_output(
        tmp_path):
    repo, fake_bin, scheduler_calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, scheduler_calls)
    python_calls = tmp_path / "python-calls"
    injection_marker = tmp_path / "reservation-reader-injected"
    _install_python3_wrapper(
        fake_bin, python_calls, injection_marker=injection_marker)

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert injection_marker.is_file()
    assert python_calls.read_text(encoding="utf-8").splitlines().count(
        "reservation") == 1
    assert python_calls.read_text(encoding="utf-8").splitlines().count(
        "injected") == 1
    assert not scheduler_calls.exists()


@pytest.mark.parametrize("boolean_index", [False, True])
def test_submit_resume_rejects_boolean_invocation_retry_index(
        tmp_path, boolean_index):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    first = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_CRASH_AFTER_QSUB": "1"})
    assert first.returncode != 0
    claim = next((
        repo / "output/env/pegasus/qualification/t126/submissions"
    ).glob("*/qsub-invocation.json"))
    value = load_json_strict(claim)
    value["retry_index"] = boolean_index
    _canonical(claim, value)
    second = _run_submit(repo, fake_bin)
    assert second.returncode == 4
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1


def _materialize_regular_rejected_attempt(
        repo: Path, submit_receipt: Path):
    """Use production recovery/FSM helpers to create a normal attempt ledger."""
    submit = load_json_strict(submit_receipt)
    root = QualificationRoot(repo)
    capability = root.issue()
    created = collector._recover_pre_attempt(
        repo_root=repo, root=root, capability=capability,
        attempt_id=submit["qualification_attempt_id"],
        submission_receipt=submit_receipt,
        submission_bytes=submit_receipt.read_bytes())
    assert created is True
    layout = root.layout(submit["qualification_attempt_id"])
    protocol = load_protocol(layout.attempt_dir / "protocol.json")
    fsm = SeriesFSM(
        capability, layout.ledger_relpath, {
            "qualification_series_id": submit["qualification_series_id"],
            "qualification_attempt_id": submit["qualification_attempt_id"],
            "pbs_job_id": submit["job_id"],
            "host": "pegasus", "boot_id": "fixture-boot",
            "controller_pid": 123,
        }, protocol)
    fsm.open()
    fsm.reject("pre-member-infrastructure", {"phase": "prologue"})
    job_result = _job_value(submit["job_script_sha256"])
    job_result["pbs_jobid"] = submit["job_id"]
    job_result["nonce"] = submit["nonce"]
    _canonical(layout.attempt_dir / "job-result.json", job_result)
    return layout


def test_fake_qsub_qstat_exact_visibility_and_durable_receipt(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    qsub_args = _install_scheduler_stubs(fake_bin, calls)
    result = _run_submit(repo, fake_bin)
    assert result.returncode == 0, result.stderr
    receipts = list((repo / "output/env/pegasus/qualification/t126/submissions"
                     ).glob("*/submit-receipt.json"))
    assert len(receipts) == 1
    receipt = load_json_strict(receipts[0])
    assert receipt["job_id"] == "98765.nqsv"
    assert receipt["qualification_attempt_id"]
    toolchain = load_json_strict(receipts[0].with_name("toolchain-manifest.json"))
    assert set(toolchain) == {
        "schema_version", "executables", "dependencies", "build_argv"}
    assert set(toolchain["executables"]) == {
        "python", "cc", "cxx", "cmake", "perf"}
    args = [item.decode() for item in qsub_args.read_bytes().split(b"\0") if item]
    assert args == [
        "-v", "IZANAGI_SUBMISSION_NONCE=" + receipt["nonce"],
        str(repo / "tools/pegasus/t126_qualification.sh"),
    ]
    assert "qstat -f 98765.nqsv" in calls.read_text(encoding="utf-8")


def test_duplicate_initial_is_rejected_before_any_additional_qsub(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    first = _run_submit(repo, fake_bin)
    assert first.returncode == 0, first.stderr
    duplicate = _run_submit(repo, fake_bin)
    assert duplicate.returncode != 0
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1


def test_dry_run_does_not_consume_series_before_real_submit(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    dry = _run_submit(repo, fake_bin, dry_run=True)
    assert dry.returncode == 0, dry.stderr
    series_root = (
        repo / "output/env/pegasus/qualification/t126/series")
    assert not list(series_root.rglob("*.json"))
    real = _run_submit(repo, fake_bin)
    assert real.returncode == 0, real.stderr
    receipts = list((
        repo / "output/env/pegasus/qualification/t126/submissions"
    ).glob("*/submit-receipt.json"))
    assert len(receipts) == 2
    assert sum(not load_json_strict(path)["dry_run"] for path in receipts) == 1


def test_m8c_qsub_nonzero_is_accepted_unknown_and_never_resubmitted(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    qsub = fake_bin / "qsub"
    qsub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' qsub >> {shlex.quote(str(calls))}\n"
        "exit 17\n",
        encoding="utf-8")
    qsub.chmod(0o755)
    failed = _run_submit(repo, fake_bin)
    assert failed.returncode == 17
    series_root = repo / "output/env/pegasus/qualification/t126/series"
    protocol = load_protocol(
        repo / "orchestrator/qualification/t126_control_v1.json")
    series_dir = next(series_root.iterdir())
    state = SeriesAttemptLedger(
        QualificationRoot(repo).issue(), series_dir.name,
        protocol["retry"]["eligible_reasons"]).replay
    assert state.state == "initial_intent" and state.attempt_count == 0
    _install_scheduler_stubs(fake_bin, calls)
    resumed = _run_submit(repo, fake_bin)
    qsub_count = calls.read_text(
        encoding="utf-8").splitlines().count("qsub")
    receipts = list((
        repo / "output/env/pegasus/qualification/t126/submissions"
    ).glob("*/submit-receipt.json"))
    assert (resumed.returncode, qsub_count, receipts) == (4, 1, [])


def test_qsub_visibility_mismatch_leaves_intent_binding_but_no_receipt(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls, visible_job="other.nqsv")
    result = _run_submit(repo, fake_bin)
    assert result.returncode == 4
    submissions = list((repo / "output/env/pegasus/qualification/t126/submissions"
                        ).glob("*"))
    assert len(submissions) == 1
    assert (submissions[0] / "submission-intent.json").is_file()
    assert (submissions[0] / "qsub-binding.json").is_file()
    assert not (submissions[0] / "submit-receipt.json").exists()
    intent = load_json_strict(submissions[0] / "submission-intent.json")
    binding = load_json_strict(submissions[0] / "qsub-binding.json")
    attempt_id = attempt_identity({
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": intent["qualification_series_id"],
        "pbs_job_id": binding["job_id"], "nonce": binding["nonce"],
        "retry_index": intent["retry_index"],
        "submission_intent_sha256": hashlib.sha256(
            (submissions[0] / "submission-intent.json").read_bytes()).hexdigest(),
    })
    stdout = tmp_path / "job.o98765"
    stderr = tmp_path / "job.e98765"
    accounting = tmp_path / "accounting"
    stdout.write_text("", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    accounting.write_text(
        "Request ID = 98765.nqsv\nExit_status = 137\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    partial_receipt = submissions[0] / "submit-receipt.json"
    partial_receipt.write_bytes(b'{"partial":')
    with pytest.raises(
            collector.CollectionError, match="submission evidence JSON"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=partial_receipt,
            job_result=None, scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    receipt = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submissions[0] / "qsub-binding.json",
        job_result=None, scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    recovered = load_json_strict(receipt)
    assert recovered["submission_evidence_kind"] == "recovered-qsub-binding"
    assert recovered["failure_class"] == "job-result-publication-failed"
    assert recovered["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        receipt, repo_root=repo).integrity_status == "valid"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            receipt, repo, load_protocol())


def test_post_qsub_receipt_write_failure_is_durably_bound_and_fail_closed(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    result = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_FAIL_RECEIPT_WRITE": "1"})
    assert result.returncode == 4
    submission = next((repo / "output/env/pegasus/qualification/t126/submissions"
                       ).iterdir())
    assert (submission / "submission-intent.json").is_file()
    assert (submission / "qsub-binding.json").is_file()
    assert not (submission / "submit-receipt.json").exists()
    assert "qsub" in calls.read_text(encoding="utf-8")
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1
    resumed = _run_submit(repo, fake_bin)
    assert resumed.returncode == 0, resumed.stderr
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1


def test_m8b_post_qsub_prebinding_crash_never_uses_raw_stdout_authority(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    crashed = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_CRASH_AFTER_QSUB": "1"})
    assert crashed.returncode == -9
    resumed = _run_submit(repo, fake_bin)
    submission = next((
        repo / "output/env/pegasus/qualification/t126/submissions").iterdir())
    protocol = load_protocol(
        repo / "orchestrator/qualification/t126_control_v1.json")
    series_dir = next((
        repo / "output/env/pegasus/qualification/t126/series").iterdir())
    state = SeriesAttemptLedger(
        QualificationRoot(repo).issue(), series_dir.name,
        protocol["retry"]["eligible_reasons"]).replay
    observation = (
        resumed.returncode,
        calls.read_text(encoding="utf-8").splitlines().count("qsub"),
        (submission / "qsub-invocation.json").is_file(),
        (submission / "qsub-binding.json").exists(),
        (submission / "submit-receipt.json").exists(),
        state.state,
    )
    assert observation == (4, 1, True, False, False, "initial_intent")


def test_binding_publish_before_ledger_bind_is_exactly_recoverable(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    crashed = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_CRASH_AFTER_BINDING": "1"})
    assert crashed.returncode == -9
    submission = next((
        repo / "output/env/pegasus/qualification/t126/submissions").iterdir())
    binding = load_json_strict(submission / "qsub-binding.json")
    assert binding["schema_version"] == "t126-qsub-binding/v2"
    resumed = _run_submit(repo, fake_bin)
    assert resumed.returncode == 0, resumed.stderr
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1


def test_binding_staging_without_canonical_never_authorizes_resubmit(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    crashed = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_CRASH_AFTER_QSUB": "1"})
    assert crashed.returncode == -9
    submission = next((
        repo / "output/env/pegasus/qualification/t126/submissions").iterdir())
    intent = load_json_strict(submission / "submission-intent.json")
    stage = submission / (
        ".qsub-binding.json.create-123-0123456789abcdef")
    _canonical(stage, {
        "schema_version": "t126-qsub-binding/v2",
        "job_id": "98765.nqsv",
        "nonce": intent["nonce"],
        "submission_intent_sha256": hashlib.sha256(
            (submission / "submission-intent.json").read_bytes()).hexdigest(),
        "qsub_invocation_sha256": hashlib.sha256(
            (submission / "qsub-invocation.json").read_bytes()).hexdigest(),
        "retry_index": intent["retry_index"],
        "qsub_returncode": 0,
        "qsub_stdout_raw": "Request 98765.nqsv submitted.\n",
    })
    resumed = _run_submit(repo, fake_bin)
    assert resumed.returncode == 4
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1
    assert stage.exists()
    assert not (submission / "qsub-binding.json").exists()


@pytest.mark.parametrize(
    "boundary",
    ["after-open", "after-short-write", "after-fsync", "after-publish"],
)
def test_submit_receipt_hard_crash_recovers_without_second_qsub(
        tmp_path, boundary):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    crashed = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_RECEIPT_CRASH": boundary})
    assert crashed.returncode in {91, 92, 93, 94}
    resumed = _run_submit(repo, fake_bin)
    assert resumed.returncode == 0, resumed.stderr
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1
    receipt = next((
        repo / "output/env/pegasus/qualification/t126/submissions"
    ).glob("*/submit-receipt.json"))
    assert load_json_strict(receipt)["job_id"] == "98765.nqsv"
    assert not list(receipt.parent.glob(".submit-receipt.json.create-*"))


def test_one_authorized_retry_submit_collector_chain_is_accepted_once(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    initial_submit = _run_submit(repo, fake_bin)
    assert initial_submit.returncode == 0, initial_submit.stderr
    submissions = (
        repo / "output/env/pegasus/qualification/t126/submissions")
    initial_receipt = next(submissions.glob("*/submit-receipt.json"))
    initial = load_json_strict(initial_receipt)
    _materialize_regular_rejected_attempt(repo, initial_receipt)
    stdout = tmp_path / "retry-job.o98765"
    stderr = tmp_path / "retry-job.e98765"
    accounting = tmp_path / "retry-accounting"
    stdout.write_text("", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    accounting.write_text(
        "Request ID = 98765.nqsv\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    initial_failure = collector.collect(
        repo_root=repo,
        attempt_id=initial["qualification_attempt_id"],
        submission_receipt=initial_receipt,
        job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert load_json_strict(initial_failure)["retry_eligible"] is True

    retry_submit = _run_submit(
        repo, fake_bin, retry_from=initial_failure)
    assert retry_submit.returncode == 0, retry_submit.stderr
    retry_receipt = next(
        path for path in submissions.glob("*/submit-receipt.json")
        if path != initial_receipt)
    retry = load_json_strict(retry_receipt)
    assert retry["retry_index"] == 1
    assert retry["retry_from_attempt_id"] == initial[
        "qualification_attempt_id"]
    _materialize_regular_rejected_attempt(repo, retry_receipt)
    retry_failure = collector.collect(
        repo_root=repo,
        attempt_id=retry["qualification_attempt_id"],
        submission_receipt=retry_receipt, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert load_json_strict(retry_failure)["retry_eligible"] is False
    protocol = load_protocol(
        repo / "orchestrator/qualification/t126_control_v1.json")
    state = SeriesAttemptLedger(
        QualificationRoot(repo).issue(),
        retry["qualification_series_id"],
        protocol["retry"]["eligible_reasons"],
    ).replay
    assert state.state == "retry_failed"
    assert state.attempt_count == 2


def test_submit_rejects_symlink_component_hidden_drift_and_skip_worktree(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "output/env").parent.mkdir(parents=True, exist_ok=True)
    (repo / "output/env").symlink_to(outside, target_is_directory=True)
    symlinked = _run_submit(repo, fake_bin)
    assert symlinked.returncode == 2
    assert list(outside.iterdir()) == []

    repo2, fake_bin2, calls2 = _submit_fixture(tmp_path / "hidden")
    _install_scheduler_stubs(fake_bin2, calls2)
    relative = "orchestrator/qualification/submission.py"
    _git(repo2, "update-index", "--assume-unchanged", relative)
    (repo2 / relative).write_text("hidden drift\n", encoding="utf-8")
    hidden = _run_submit(repo2, fake_bin2)
    assert hidden.returncode == 2
    assert "assume-unchanged" in hidden.stderr

    repo_skip, fake_bin_skip, calls_skip = _submit_fixture(
        tmp_path / "skip-worktree")
    _install_scheduler_stubs(fake_bin_skip, calls_skip)
    transitive = "orchestrator/qualification/t126_driver.py"
    _git(repo_skip, "update-index", "--skip-worktree", transitive)
    (repo_skip / transitive).write_text(
        "raise RuntimeError('must never import persistent drift')\n",
        encoding="utf-8")
    skipped = _run_submit(repo_skip, fake_bin_skip)
    assert skipped.returncode == 2
    assert "assume-unchanged/skip-worktree" in skipped.stderr
    assert not calls_skip.exists()


def test_submit_index_flag_gate_is_pipefail_safe_and_clean_repo_proceeds(
        tmp_path):
    submit_source = (
        _ROOT / "tools/pegasus/submit_t126_qualification.sh"
    ).read_text(encoding="utf-8")
    expected_gate = (
        "index_flags_rc=0\n"
        "INDEX_FLAGS=$(git -C \"$REPO_ROOT\" ls-files -v) "
        "|| index_flags_rc=$?\n"
        "if [[ \"$index_flags_rc\" -ne 0 ]]; then\n"
        "  exit \"$index_flags_rc\"\n"
        "fi\n"
        "if grep -Eq '^[a-zS]' <<<\"$INDEX_FLAGS\"; then\n"
    )
    assert submit_source.count(expected_gate) == 1
    assert "ls-files -v | grep -Eq '^[a-zS]'" not in submit_source

    flagged_repo, flagged_bin, flagged_calls = _submit_fixture(
        tmp_path / "flagged")
    _install_scheduler_stubs(flagged_bin, flagged_calls)
    relative = "orchestrator/qualification/submission.py"
    clean_rows = _git(flagged_repo, "ls-files", "-v").splitlines()
    assert clean_rows
    assert not any(re.match(r"^[a-zS]", row) for row in clean_rows)
    _git(flagged_repo, "update-index", "--assume-unchanged", relative)
    flagged_rows = _git(flagged_repo, "ls-files", "-v").splitlines()
    assert flagged_rows
    assert any(re.match(r"^[a-zS]", row) for row in flagged_rows)

    flagged = _run_submit(flagged_repo, flagged_bin)

    assert flagged.returncode == 2
    assert flagged.stdout == ""
    assert flagged.stderr == (
        "assume-unchanged/skip-worktree source is forbidden\n")
    assert "hidden dirty execution input" not in flagged.stderr
    assert not flagged_calls.exists()

    clean_repo, clean_bin, clean_calls = _submit_fixture(tmp_path / "clean")
    _install_scheduler_stubs(clean_bin, clean_calls)
    clean_rows = _git(clean_repo, "ls-files", "-v").splitlines()
    assert clean_rows
    assert not any(re.match(r"^[a-zS]", row) for row in clean_rows)

    accepted = _run_submit(clean_repo, clean_bin)

    assert accepted.returncode == 0, accepted.stderr
    assert "assume-unchanged/skip-worktree" not in accepted.stderr
    assert clean_calls.read_text(encoding="utf-8").splitlines().count(
        "qsub") == 1


def test_submit_index_flag_git_failure_is_not_no_match(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    real_git = shutil.which("git")
    assert real_git is not None
    git_wrapper = fake_bin / "git"
    git_wrapper.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = -C ] && [ \"$3\" = ls-files ] "
        "&& [ \"$4\" = -v ]; then\n"
        "  printf '%s\\n' 'injected ls-files failure' >&2\n"
        "  exit 73\n"
        "fi\n"
        f"exec {shlex.quote(real_git)} \"$@\"\n",
        encoding="utf-8")
    git_wrapper.chmod(0o755)

    failed = _run_submit(repo, fake_bin)

    assert failed.returncode == 73
    assert failed.stdout == ""
    assert failed.stderr == "injected ls-files failure\n"
    assert not calls.exists()


def test_submit_unsupported_policy_perf_uses_canonical_degraded_toolchain(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls, perf_unsupported=True)

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 0, completed.stderr
    toolchain_path = next((
        repo / "output/env/pegasus/qualification/t126/submissions"
    ).glob("*/toolchain-manifest.json"))
    toolchain = load_json_strict(toolchain_path)
    assert set(toolchain) == {
        "schema_version", "executables", "dependencies", "build_argv",
        "perf_preflight",
    }
    assert set(toolchain["executables"]) == {
        "python", "cc", "cxx", "cmake"}
    assert toolchain["perf_preflight"]["status"] == "unavailable"
    assert toolchain["perf_preflight"]["available"] is False
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1


def test_submit_probe_error_remains_fail_closed_before_qsub(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls, perf_unsupported=True)
    literal_perf = fake_bin / "perf"
    literal_perf.write_text("#!/bin/sh\nkill -TERM $$\n", encoding="utf-8")
    literal_perf.chmod(0o755)

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert "perf preflight failed" in completed.stderr
    assert "qsub" not in calls.read_text(encoding="utf-8")


def test_submit_perf_present_keeps_policy_candidate_smoke_rejection(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls, perf_unsupported=True)
    literal_perf = fake_bin / "perf"
    literal_perf.write_text(
        "#!/bin/sh\n"
        "output=; previous=\n"
        "for argument in \"$@\"; do\n"
        "  [ \"$previous\" != -o ] || output=$argument\n"
        "  previous=$argument\n"
        "done\n"
        "printf '%s\\n' '1,,LLC-load-misses' '1,,LLC-loads' "
        "'1,,instructions' '1,,cycles' > \"$output\"\n",
        encoding="utf-8")
    literal_perf.chmod(0o755)

    completed = _run_submit(repo, fake_bin)

    assert completed.returncode == 2
    assert "perf candidate is not functional" in completed.stderr
    assert "qsub" not in calls.read_text(encoding="utf-8")


def test_submit_untracked_scan_failure_is_fail_closed_before_qsub(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    real_git = shutil.which("git")
    assert real_git
    git_stub = fake_bin / "git"
    git_stub.write_text(
        "#!/bin/sh\n"
        "case \" $* \" in\n"
        "  *' ls-files --others --exclude-standard -z '*) exit 73 ;;\n"
        "esac\n"
        f"exec {shlex.quote(real_git)} \"$@\"\n",
        encoding="utf-8")
    git_stub.chmod(0o755)
    result = _run_submit(repo, fake_bin)
    assert result.returncode == 73
    assert "cannot inspect untracked" in result.stderr
    assert not calls.exists()


def test_m8a_create_only_invocation_claim_serializes_parallel_submit(
        tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    entered = tmp_path / "qsub-entered"
    release = tmp_path / "qsub-release"
    qsub = fake_bin / "qsub"
    qsub.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' qsub >> {shlex.quote(str(calls))}\n"
        f": > {shlex.quote(str(entered))}\n"
        f"while [ ! -e {shlex.quote(str(release))} ]; do sleep 0.01; done\n"
        "printf '%s\\n' 'Request 98765.nqsv submitted.'\n",
        encoding="utf-8")
    qsub.chmod(0o755)
    env = {
        **os.environ,
        "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    argv = ["bash", str(repo / "tools/pegasus/submit_t126_qualification.sh")]
    first = subprocess.Popen(
        argv, cwd=repo, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = None
    first_stdout = first_stderr = ""
    try:
        deadline = time.monotonic() + 20
        while not entered.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert entered.exists()
        second = subprocess.Popen(
            argv, cwd=repo, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            qsub_count = (
                calls.read_text(encoding="utf-8").splitlines().count("qsub")
                if calls.exists() else 0)
            if second.poll() is not None or qsub_count >= 2:
                break
            time.sleep(0.01)
    finally:
        release.touch()
        if second is not None and second.poll() is None:
            second.communicate(timeout=20)
        first_stdout, first_stderr = first.communicate(timeout=20)
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1
    assert first.returncode == 0, first_stderr + first_stdout
    claims = list((
        repo / "output/env/pegasus/qualification/t126/submissions"
    ).glob("*/qsub-invocation.json"))
    assert len(claims) == 1
    assert set(load_json_strict(claims[0])) == {
        "nonce", "retry_index", "submission_intent_sha256"}


def test_invocation_claim_short_write_is_completed_and_bound(tmp_path):
    repo, fake_bin, calls = _submit_fixture(tmp_path)
    _install_scheduler_stubs(fake_bin, calls)
    submitted = _run_submit(
        repo, fake_bin,
        extra_env={"IZANAGI_T126_TEST_INVOCATION_SHORT_WRITE": "1"})
    assert submitted.returncode == 0, submitted.stderr
    submission = next((
        repo / "output/env/pegasus/qualification/t126/submissions").iterdir())
    claim = submission / "qsub-invocation.json"
    raw = claim.read_bytes()
    value = load_json_strict(claim)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    claim_sha = hashlib.sha256(raw).hexdigest()
    assert load_json_strict(
        submission / "qsub-binding.json")["qsub_invocation_sha256"] == claim_sha
    assert load_json_strict(
        submission / "submit-receipt.json")[
            "qsub_invocation_sha256"] == claim_sha
    receipt = load_json_strict(submission / "submit-receipt.json")
    protocol = load_protocol(
        repo / "orchestrator/qualification/t126_control_v1.json")
    assert SeriesAttemptLedger(
        QualificationRoot(repo).issue(),
        receipt["qualification_series_id"],
        protocol["retry"]["eligible_reasons"],
    ).replay.last_qsub_invocation_sha256 == claim_sha
    assert calls.read_text(encoding="utf-8").splitlines().count("qsub") == 1


def test_m8d_binding_v2_exact_corpus_and_all_consumer_wiring(tmp_path):
    valid = {
        "schema_version": "t126-qsub-binding/v2",
        "job_id": "123.server",
        "nonce": "1" * 32,
        "submission_intent_sha256": "2" * 64,
        "qsub_invocation_sha256": "3" * 64,
        "retry_index": 0,
        "qsub_returncode": 0,
        "qsub_stdout_raw": "Request 123.server submitted.\n",
    }
    assert validate_qsub_binding(valid)["job_id"] == "123.server"
    mutations = []
    for key, value in (
            ("qsub_returncode", False),
            ("qsub_returncode", 1),
            ("retry_index", False),
            ("qsub_invocation_sha256", "not-a-sha"),
            ("qsub_stdout_raw", "Request 123.server submitted.\nextra\n"),
            ("job_id", "0:123.server"),
            ("schema_version", "t126-qsub-binding/v1")):
        row = dict(valid)
        row[key] = value
        mutations.append(row)
    mutations.append({**valid, "extra": True})
    for row in mutations:
        with pytest.raises(QsubBindingError):
            validate_qsub_binding(row)
    (repo, _, _, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "8d")
    binding = submit.with_name("qsub-binding.json")
    original = load_json_strict(binding)
    invalid = dict(original)
    invalid["qsub_returncode"] = 1
    _canonical(binding, invalid)
    assert {
        key: value for key, value in invalid.items()
        if key != "qsub_returncode"
    } == {
        key: value for key, value in original.items()
        if key != "qsub_returncode"
    }
    assert original["qsub_returncode"] == 0
    assert type(original["qsub_returncode"]) is int
    assert invalid["qsub_returncode"] == 1
    assert type(invalid["qsub_returncode"]) is int
    assert not (
        type(invalid["qsub_returncode"]) is int
        and invalid["qsub_returncode"] == 0)
    with pytest.raises(QsubBindingError) as rejected:
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert type(rejected.value) is QsubBindingError

    (job_repo, job_capability, _, _, job_submit, _, _, _, _) = _attempt(
        tmp_path, "8d-job")
    job_binding = job_submit.with_name("qsub-binding.json")
    job_binding_value = load_json_strict(job_binding)
    job_binding_value["qsub_returncode"] = 1
    _canonical(job_binding, job_binding_value)
    binding_sha = hashlib.sha256(job_binding.read_bytes()).hexdigest()
    job_submit_value = load_json_strict(job_submit)
    job_submit_value["qsub_binding_sha256"] = binding_sha
    _canonical(job_submit, job_submit_value)
    ledger_dir = (
        job_capability.root / "series"
        / job_submit_value["qualification_series_id"] / "attempt-ledger")
    events = [
        load_json_strict(path)
        for path in sorted(ledger_dir.glob("*.json"))]
    previous = "0" * 64
    for index, event in enumerate(events):
        event["previous_event_sha256"] = previous
        if event["event_type"] == "initial_submitted":
            event["payload"]["submission_evidence_sha256"] = binding_sha
        unhashed = {
            key: value for key, value in event.items()
            if key != "event_sha256"}
        event["event_sha256"] = hashlib.sha256(json.dumps(
            unhashed, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("ascii")).hexdigest()
        previous = event["event_sha256"]
        _canonical(ledger_dir / f"{index:04d}.json", event)
    completed = _run_bound_job_terminal(
        job_repo, nonce="1" * 32)
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "durable qsub/ledger binding mismatch\n"

    (driver_repo, _, driver_layout, _, _, _, _, _, _) = _attempt(
        tmp_path, "8d-driver", clean=True)
    driver_manifest_path = (
        driver_layout.attempt_dir / "source/source-snapshots.json")
    driver_manifest = load_json_strict(driver_manifest_path)
    driver_binding = (
        driver_layout.attempt_dir
        / driver_manifest["qsub_binding"]["path"])
    driver_binding_value = load_json_strict(driver_binding)
    driver_binding_value["qsub_returncode"] = 1
    _canonical(driver_binding, driver_binding_value)
    driver_manifest["qsub_binding"].update(file_record(
        driver_binding, relative_to=driver_layout.attempt_dir))
    _canonical(driver_manifest_path, driver_manifest)
    driver_verified = verify_attempt(driver_layout.attempt_dir)
    assert driver_verified.integrity_status == "invalid"
    assert "QsubBindingError" in " ".join(driver_verified.errors)

    (public_repo, public_capability, public_layout, public_attempt,
     public_submit, public_stdout, public_stderr, public_accounting,
     _) = _attempt(tmp_path, "8d-public")
    public_accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    public_receipt_path = collector.collect(
        repo_root=public_repo, attempt_id=public_attempt,
        submission_receipt=public_submit, job_result=None,
        scheduler_stdout=public_stdout, scheduler_stderr=public_stderr,
        accounting=public_accounting)
    public_manifest_path = (
        public_layout.attempt_dir / "source/source-snapshots.json")
    public_manifest = load_json_strict(public_manifest_path)
    public_binding = (
        public_layout.attempt_dir
        / public_manifest["qsub_binding"]["path"])
    public_binding_value = load_json_strict(public_binding)
    public_binding_value["qsub_returncode"] = 1
    _canonical(public_binding, public_binding_value)
    public_manifest["qsub_binding"].update(file_record(
        public_binding, relative_to=public_layout.attempt_dir))
    _canonical(public_manifest_path, public_manifest)
    public_receipt = load_json_strict(public_receipt_path)
    replacements = {
        path.relative_to(public_layout.attempt_dir).as_posix():
            file_record(path, relative_to=public_layout.attempt_dir)
        for path in (public_binding, public_manifest_path)
    }
    public_receipt["closure_manifest"] = [
        replacements.get(row["path"], row)
        for row in public_receipt["closure_manifest"]]
    _rehash_receipt_ledger(
        public_receipt_path, public_capability, public_receipt)
    public_verified = collector.verify_post_job_receipt(
        public_receipt_path, repo_root=public_repo)
    assert public_verified.integrity_status == "invalid"
    assert "QsubBindingError" in " ".join(public_verified.errors)


@pytest.mark.parametrize("boolean_index", [False, True])
def test_retry_index_boolean_is_rejected_by_python_production_consumers(
        tmp_path, boolean_index):
    with pytest.raises(RetryIndexError):
        validate_retry_index(boolean_index)
    with pytest.raises(ProtocolError):
        attempt_identity({
            "schema_version": "t126-qualification-attempt-identity/v1",
            "qualification_series_id": "1" * 64,
            "pbs_job_id": "123.server",
            "nonce": "2" * 32,
            "retry_index": boolean_index,
            "submission_intent_sha256": "3" * 64,
        })
    binding = {
        "schema_version": "t126-qsub-binding/v2",
        "job_id": "123.server",
        "nonce": "1" * 32,
        "submission_intent_sha256": "2" * 64,
        "qsub_invocation_sha256": "3" * 64,
        "retry_index": boolean_index,
        "qsub_returncode": 0,
        "qsub_stdout_raw": "Request 123.server submitted.\n",
    }
    with pytest.raises(QsubBindingError):
        validate_qsub_binding(binding)
    with pytest.raises(collector.CollectionError):
        collector._exact_retry_index(boolean_index, "test consumer")
    with pytest.raises(t126_driver.QualificationDriverError):
        t126_driver._exact_retry_index(boolean_index, "test consumer")
    _, _, capability = _root_for_retry_index_test(tmp_path)
    ledger = SeriesAttemptLedger(
        capability, "4" * 64,
        load_protocol()["retry"]["eligible_reasons"])
    ledger.claim_initial(
        nonce="5" * 32, submission_intent_sha256="6" * 64)
    with pytest.raises(AttemptLedgerError):
        ledger.bind_submitted(
            retry_index=boolean_index, nonce="5" * 32,
            job_id="123.server", attempt_id="7" * 64,
            qsub_invocation_sha256="8" * 64,
            submission_evidence_sha256="9" * 64)


def _root_for_retry_index_test(tmp_path):
    repo = tmp_path / "retry-index-ledger"
    repo.mkdir()
    root = QualificationRoot(repo)
    return repo, root, root.issue()


@pytest.mark.parametrize("boolean_index", [False, True])
def test_job_prologue_rejects_boolean_submission_retry_index(
        tmp_path, boolean_index):
    (repo, _, _, _, submit, _, _, _, _) = _attempt(
        tmp_path, "job-index-" + str(boolean_index).lower())
    value = load_json_strict(submit)
    value["retry_index"] = boolean_index
    _canonical(submit, value)
    completed = _run_bound_job_terminal(repo, nonce="1" * 32)
    assert completed.returncode == 2


def test_binding_v2_consumer_wiring_diagnostic_is_present():
    driver_source = (
        _ROOT / "orchestrator/qualification/t126_driver.py"
    ).read_text(encoding="utf-8")
    collector_source = (
        _ROOT / "orchestrator/qualification/collector.py"
    ).read_text(encoding="utf-8")
    job_source = (
        _ROOT / "tools/pegasus/t126_qualification.sh"
    ).read_text(encoding="utf-8")
    assert driver_source.count("validate_qsub_binding(") == 2
    assert collector_source.count("validate_qsub_binding(") == 4
    assert "set(binding)!=binding_keys" in job_source
    assert 'binding["schema_version"]!="t126-qsub-binding/v2"' in job_source
    assert 'type(binding.get("qsub_stdout_raw")) is not str' in job_source
    assert 'type(binding["qsub_returncode"]) is not int' in job_source
    assert "or derived!=job" in job_source


def _after_publish_entries(directory: Path, data: bytes):
    directory.mkdir(parents=True, exist_ok=True)
    stage = directory / ".job-result.json.create-123-0123456789abcdef"
    stage.write_bytes(data)
    stage.chmod(0o600)
    target = directory / "job-result.json"
    os.link(stage, target)
    return target, stage


def _run_bound_job_terminal(
        repo: Path, *, nonce: str, job_id: str = "123.server",
        extra_env: dict[str, str] | None = None,
        signal_reset_marker: Path | None = None):
    env = {
        **os.environ,
        "PBS_JOBID": job_id,
        "PBS_O_WORKDIR": str(repo),
        "IZANAGI_SUBMISSION_NONCE": nonce,
        "IZANAGI_T126_TEST_EXIT_AFTER_BINDING": "34",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    env.update(extra_env or {})
    bash = shutil.which("bash")
    assert bash is not None
    bash_executable = str(Path(bash).resolve(strict=True))
    script = str(repo / "tools/pegasus/t126_qualification.sh")
    return subprocess.run(
        [
            sys.executable, "-I", "-S", "-B", "-c",
            _SIGNAL_IGNORE_EXEC_LAUNCHER,
            sys.executable, _SIGNAL_RESET_EXEC_LAUNCHER,
            bash_executable, "bash", script,
            str(signal_reset_marker) if signal_reset_marker is not None else "",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=20)


def _run_job_reservation_probe(
        tmp_path: Path, digit: str, *,
        reservation_policy_overrides: dict[str, object] | None = None,
        inject_late_failure: bool = False):
    scratch_root = tmp_path / f"job-scratch-{digit}"
    (repo, _, _, _, _, _, _, _, _) = _attempt(
        tmp_path, digit,
        reservation_policy_overrides=reservation_policy_overrides,
        job_scratch_root=scratch_root)
    fake_bin = tmp_path / f"job-bin-{digit}"
    fake_bin.mkdir()
    python_calls = tmp_path / f"python-calls-{digit}"
    injection_marker = tmp_path / f"python-injection-{digit}"
    python_wrapper = _install_python3_wrapper(
        fake_bin, python_calls,
        injection_marker=injection_marker if inject_late_failure else None)
    downstream_marker = tmp_path / f"dependency-marker-{digit}"
    _install_job_dependency_marker(fake_bin, repo, downstream_marker)
    completed = _run_bound_job_terminal(
        repo, nonce="1" * 32,
        extra_env={
            "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
            "IZANAGI_T126_TEST_EXIT_AFTER_BINDING": "",
        })
    return (
        completed, repo, python_wrapper, python_calls, injection_marker,
        downstream_marker)


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        (None, None),
        ("t126_qualification_walltime", "09:59:59"),
        ("t126_qualification_walltime_s", 35999),
        ("t126_qualification_member_cap_s", 901),
        ("t126_qualification_round_gap_s", 1801),
        ("t126_qualification_prologue_cap_s", 901),
        ("t126_qualification_attestation_cap_s", 601),
        ("t126_qualification_finalize_reserve_s", 601),
        ("t126_qualification_wmax_s", 29099),
    ],
    ids=[
        "canonical", "walltime", "walltime-s", "member-cap", "round-gap",
        "prologue-cap", "attestation-cap", "finalize-reserve", "wmax",
    ],
)
def test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value(
        tmp_path, key, bad_value):
    case_root = tmp_path / ("canonical" if key is None else key)
    case_root.mkdir()
    overrides = {} if key is None else {key: bad_value}

    completed, _, _, _, _, downstream_marker = _run_job_reservation_probe(
        case_root, "case", reservation_policy_overrides=overrides)

    assert completed.returncode == 2
    assert completed.stdout == ""
    if key is None:
        assert downstream_marker.is_file()
        assert completed.stderr == (
            "dependency source is not pinned-clean: "
            + str(case_root / "repo-case" / THIRD_PARTY_STAGING_RELATIVE / "gflags")
            + "\n")
    else:
        assert completed.stderr == "qualification envelope mismatch\n"
        assert not downstream_marker.exists()


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("t126_qualification_member_cap_s", 900.0),
        ("t126_qualification_round_gap_s", 1800.0),
        ("t126_qualification_attestation_cap_s", 600.0),
        ("t126_qualification_finalize_reserve_s", 600.0),
    ],
    ids=["member-cap", "round-gap", "attestation-cap", "finalize-reserve"],
)
def test_job_rejects_each_single_layer_equal_float_type_drift(
        tmp_path, key, bad_value):
    """Each equal-float passes value checks, leaving only strict-int rejection."""
    (completed, _, _, _, _, downstream_marker) = _run_job_reservation_probe(
        tmp_path, "single-type", reservation_policy_overrides={key: bad_value})

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "qualification envelope type mismatch\n"
    assert not downstream_marker.exists()


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("t126_qualification_walltime_s", 36000.0),
        ("t126_qualification_wmax_s", 29100.0),
        ("t126_qualification_prologue_cap_s", 900.0),
    ],
    ids=["walltime-s", "wmax", "prologue-cap"],
)
def test_job_rejects_each_mapping_masked_equal_float_type_drift(
        tmp_path, key, bad_value):
    """These equal-floats kill only a Python-type + Bash-mapping mutation."""
    (completed, _, _, _, _, downstream_marker) = _run_job_reservation_probe(
        tmp_path, "masked-type", reservation_policy_overrides={key: bad_value})

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "qualification envelope type mismatch\n"
    assert not downstream_marker.exists()


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("t126_qualification_attestation_cap_s", 600.0000000000001),
        ("t126_qualification_round_gap_s", True),
        ("t126_qualification_walltime", 10),
    ],
    ids=["near-float", "bool", "walltime-not-string"],
)
def test_job_rejects_overdetermined_reservation_policy_type_drift(
        tmp_path, key, bad_value):
    """Pin diagnostics, not semantic kills: value checks also reject.

    In particular, no non-string JSON value is ``==`` to the canonical
    walltime string, so its type guard is redundant on the accepted set.
    """
    (completed, _, _, _, _, downstream_marker) = _run_job_reservation_probe(
        tmp_path, "diagnostic-type",
        reservation_policy_overrides={key: bad_value})

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == "qualification envelope type mismatch\n"
    assert not downstream_marker.exists()


def test_job_reservation_reader_rejects_python_failure_after_complete_output(
        tmp_path):
    (completed, repo, python_wrapper, python_calls, injection_marker,
     downstream_marker) = _run_job_reservation_probe(
         tmp_path, "late", inject_late_failure=True)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert injection_marker.is_file()
    assert not downstream_marker.exists()
    first_calls = python_calls.read_text(encoding="utf-8").splitlines()
    assert first_calls.count("version") == 1
    assert first_calls.count("monotonic") >= 1
    assert first_calls.count("receipt") >= 1
    assert first_calls.count("reservation") == 1
    assert first_calls.count("injected") == 1

    delegated = subprocess.run(
        [
            str(python_wrapper), "-I", "-S", "-B", "-",
            str(repo / RESERVATION_POLICY_RELATIVE_PATH),
        ],
        input=(
            "import json,sys\n"
            "p=json.load(open(sys.argv[1],encoding='utf-8'))\n"
            "for key in ('t126_qualification_walltime_s',"
            "'t126_qualification_wmax_s',"
            "'t126_qualification_prologue_cap_s'): print(p[key])\n"
        ),
        capture_output=True, text=True, timeout=20)
    assert delegated.returncode == 0
    assert delegated.stdout == "36000\n29100\n900\n"
    final_calls = python_calls.read_text(encoding="utf-8").splitlines()
    assert final_calls.count("reservation") == 2
    assert final_calls.count("injected") == 1


def _embedded_job_publisher_source() -> str:
    source = (
        _ROOT / "tools/pegasus/t126_qualification.sh"
    ).read_text(encoding="utf-8")
    marker = (
        "    \"$SUBMITTED_ATTEMPT_ID\" <<'PY' || true\n")
    start = source.index(marker) + len(marker)
    return source[start:source.index("\nPY\n", start)]


def _namespace_inode_snapshot(directory: Path):
    snapshot = {}
    for path in sorted(directory.iterdir()):
        current = path.lstat()
        if path.is_symlink():
            payload = ("symlink", os.readlink(path))
        elif path.is_file():
            payload = ("regular", path.read_bytes())
        else:
            payload = ("other", None)
        snapshot[path.name] = (
            current.st_mode, current.st_uid, current.st_gid,
            current.st_dev, current.st_ino, current.st_nlink,
            current.st_size, payload)
    return snapshot


@pytest.mark.parametrize(
    "shape",
    ["multiple", "suffix", "mode", "symlink", "nonregular",
     "external-hardlink"],
)
def test_embedded_publisher_global_preflight_is_nonmutating(
        tmp_path, shape):
    directory = tmp_path / "publisher"
    directory.mkdir()
    first = directory / ".job-result.json.create-123-0123456789abcdef"
    if shape == "symlink":
        outside = tmp_path / "outside"
        outside.write_bytes(b"outside")
        first.symlink_to(outside)
    elif shape == "nonregular":
        first.mkdir()
    else:
        first.write_bytes(b"staged")
        first.chmod(0o644 if shape == "mode" else 0o600)
    if shape == "multiple":
        second = directory / ".job-result.json.create-124-fedcba9876543210"
        second.write_bytes(b"second")
        second.chmod(0o600)
    elif shape == "suffix":
        first.rename(directory / ".job-result.json.create-malformed")
    elif shape == "external-hardlink":
        os.link(first, tmp_path / "external-hardlink")
    before = _namespace_inode_snapshot(directory)
    target = directory / "job-result.json"
    completed = subprocess.run(
        [
            sys.executable, "-I", "-S", "-B", "-",
            str(target), "123.server", "34", "a" * 64, "1" * 32,
            "1", "2", "29100", "0", "", "",
        ],
        input=_embedded_job_publisher_source(),
        capture_output=True, text=True, timeout=20)
    assert completed.returncode != 0
    assert _namespace_inode_snapshot(directory) == before


def test_embedded_publisher_preflight_contract_covers_unforgeable_uid_gate():
    publisher = _embedded_job_publisher_source()
    assert "current.st_uid!=os.getuid()" in publisher
    assert "stat.S_IMODE(current.st_mode)!=0o600" in publisher
    assert "current.st_nlink!=expected_nlink" in publisher
    assert "pattern.fullmatch(entry.name) is None" in publisher


@pytest.mark.parametrize(
    "pointer_mutation",
    ["none", "valid", "attempt", "series", "job", "nonce", "extra", "symlink"],
)
def test_submitted_attempt_is_sole_terminal_publisher_target(
        tmp_path, pointer_mutation):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "target-" + pointer_mutation)
    submission = load_json_strict(submit)
    expected = {
        "schema_version": "t126-qualification-attempt-pointer/v1",
        "qualification_series_id": submission["qualification_series_id"],
        "qualification_attempt_id": attempt_id,
        "pbs_job_id": "123.server",
        "nonce": "1" * 32,
    }
    extra_env = {}
    foreign_attempt = (
        QualificationRoot(repo).path / "attempts" / ("f" * 64))
    if pointer_mutation != "none":
        pointer = dict(expected)
        if pointer_mutation == "attempt":
            pointer["qualification_attempt_id"] = "f" * 64
            foreign_attempt.mkdir()
        elif pointer_mutation == "series":
            pointer["qualification_series_id"] = "e" * 64
        elif pointer_mutation == "job":
            pointer["pbs_job_id"] = "999.server"
        elif pointer_mutation == "nonce":
            pointer["nonce"] = "2" * 32
        elif pointer_mutation == "extra":
            pointer["extra"] = True
        source = _canonical(tmp_path / "pointer.json", pointer)
        if pointer_mutation == "symlink":
            extra_env["IZANAGI_T126_TEST_POINTER_SYMLINK_TARGET"] = str(source)
        else:
            extra_env["IZANAGI_T126_TEST_POINTER_SOURCE"] = str(source)
    completed = _run_bound_job_terminal(
        repo, nonce="1" * 32, extra_env=extra_env)
    assert completed.returncode == 34, completed.stderr
    early = (
        QualificationRoot(repo).path / "job-staging"
        / ("123.server." + "1" * 32))
    canonical = layout.attempt_dir / "job-result.json"
    if pointer_mutation in {"none", "valid"}:
        assert canonical.is_file()
        assert not (early / "job-result.json").exists()
        return
    assert not canonical.exists()
    assert not (foreign_attempt / "job-result.json").exists()
    assert (early / "job-result.json").is_file()
    assert (early / "target-rejection.json").is_file()
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False
    assert receipt["job_result"] is None
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"
    protocol = load_protocol()
    assert SeriesAttemptLedger(
        QualificationRoot(repo).issue(),
        receipt["qualification_series_id"],
        protocol["retry"]["eligible_reasons"]).replay.state == "initial_failed"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            receipt_path, repo, protocol)


@pytest.mark.parametrize(
    ("boundary", "job_id"),
    [
        ("", "12690001.nqsv"),
        ("after-open", "12690002.nqsv"),
        ("after-short-write", "12690003.nqsv"),
        ("after-fsync", "12690004.nqsv"),
        ("after-publish", "12690005.nqsv"),
    ])
def test_exact_committed_signal_publisher_collector_rerun_chain(
        tmp_path, boundary, job_id):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(
         tmp_path, "signal-" + (boundary or "normal"), job_id=job_id)
    parent_signal_dispositions = {
        signal.SIGTERM: signal.getsignal(signal.SIGTERM),
        signal.SIGHUP: signal.getsignal(signal.SIGHUP),
    }
    launcher_marker = tmp_path / "signal-reset-launcher.json"
    assert not launcher_marker.exists()
    extra_env = {"IZANAGI_T126_TEST_SIGNAL_AFTER_BINDING": "TERM"}
    if boundary:
        extra_env["IZANAGI_T126_TEST_JOB_RESULT_CRASH"] = boundary
    completed = _run_bound_job_terminal(
        repo, nonce="1" * 32, job_id=job_id, extra_env=extra_env,
        signal_reset_marker=launcher_marker)
    assert {
        sig: signal.getsignal(sig) for sig in parent_signal_dispositions
    } == parent_signal_dispositions
    assert launcher_marker.is_file(), completed.stderr
    assert launcher_marker.read_bytes() == _SIGNAL_RESET_LAUNCHER_MARKER
    assert completed.returncode == 143, completed.stderr
    script = repo / "tools/pegasus/t126_qualification.sh"
    committed = subprocess.check_output([
        "git", "-C", str(repo), "cat-file", "blob",
        "HEAD:tools/pegasus/t126_qualification.sh"])
    assert script.read_bytes() == committed
    accounting.write_text(
        f"Request ID = {job_id}\nExit_status = 143\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    series_id = load_json_strict(first)["qualification_series_id"]
    ledger_dir = (
        QualificationRoot(repo).path / "series" / series_id
        / "attempt-ledger")
    first_ledger = {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))}
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(second)
    assert second == first and second.read_bytes() == first_bytes
    assert {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))} == first_ledger
    assert receipt["failure_class"] == (
        "scheduler-terminated"
        if boundary in {"", "after-publish"}
        else "job-result-publication-failed")
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        second, repo_root=repo).integrity_status == "valid"
    protocol = load_protocol()
    assert SeriesAttemptLedger(
        QualificationRoot(repo).issue(), series_id,
        protocol["retry"]["eligible_reasons"]).replay.state == "initial_failed"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(
            second, repo, protocol)


@pytest.mark.parametrize(
    "boundary", ["after-open", "after-short-write", "after-fsync"])
def test_rejected_target_publisher_crash_closes_nonretry(
        tmp_path, boundary):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "rejected-crash-" + boundary)
    submission = load_json_strict(submit)
    pointer = _canonical(tmp_path / "foreign-pointer.json", {
        "schema_version": "t126-qualification-attempt-pointer/v1",
        "qualification_series_id": submission["qualification_series_id"],
        "qualification_attempt_id": "f" * 64,
        "pbs_job_id": "123.server",
        "nonce": "1" * 32,
    })
    completed = _run_bound_job_terminal(
        repo, nonce="1" * 32, extra_env={
            "IZANAGI_T126_TEST_POINTER_SOURCE": str(pointer),
            "IZANAGI_T126_TEST_JOB_RESULT_CRASH": boundary,
        })
    assert completed.returncode == 34, completed.stderr
    assert not (layout.attempt_dir / "job-result.json").exists()
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = receipt_path.read_bytes()
    rerun = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(rerun)
    assert rerun.read_bytes() == first_bytes
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False
    assert collector.verify_post_job_receipt(
        rerun, repo_root=repo).integrity_status == "valid"
    protocol = load_protocol()
    assert SeriesAttemptLedger(
        QualificationRoot(repo).issue(),
        receipt["qualification_series_id"],
        protocol["retry"]["eligible_reasons"]).replay.state == "initial_failed"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(rerun, repo, protocol)


def test_terminal_publisher_rejects_submitted_attempt_symlink_ancestor(
        tmp_path):
    (repo, _, _, _, _, _, _, _, _) = _attempt(
        tmp_path, "target-symlink-ancestor")
    root = QualificationRoot(repo).path
    attempts = root / "attempts"
    attempts.rename(root / "attempts-preserved")
    outside = tmp_path / "foreign-attempts"
    outside.mkdir()
    attempts.symlink_to(outside, target_is_directory=True)
    completed = _run_bound_job_terminal(repo, nonce="1" * 32)
    assert completed.returncode == 34, completed.stderr
    assert list(outside.iterdir()) == []
    early = (
        root / "job-staging" / ("123.server." + "1" * 32))
    assert (early / "job-result.json").is_file()
    assert (early / "target-rejection.json").is_file()


@pytest.mark.parametrize("namespace", ["attempt", "early-job"])
def test_m9a_targetless_full_staging_is_discarded_to_nonretry_failure(
        tmp_path, namespace):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, "9a-" + namespace)
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    stage_dir = layout.attempt_dir
    if namespace == "early-job":
        stage_dir = (
            capability.root / "job-staging"
            / ("123.server." + "1" * 32))
        stage_dir.mkdir(parents=True)
    stage = stage_dir / ".job-result.json.create-123-0123456789abcdef"
    stage.write_bytes(data)
    stage.chmod(0o600)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["retry_eligible"] is False
    assert receipt["job_result"] is None
    assert not stage.exists()
    assert not (layout.attempt_dir / "job-result.json").exists()


def test_m9b_after_publish_stage_cleanup_and_collector_rerun_converge(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9b")
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    target, stage = _after_publish_entries(layout.attempt_dir, data)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    assert target.is_file() and not stage.exists()
    assert target.stat().st_nlink == 1
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first and second.read_bytes() == first_bytes


def test_m9c_exact_early_job_staging_is_recovered_and_closed(
        tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9c")
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    early = (
        capability.root / "job-staging"
        / ("123.server." + "1" * 32))
    target, stage = _after_publish_entries(early, data)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["job_result"] is not None
    assert (layout.attempt_dir / "job-result.json").read_bytes() == data
    assert not target.exists() and not stage.exists()
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"


@pytest.mark.parametrize("shape", ["different-inode", "extra-hardlink"])
def test_m9d_inode_and_nlink_anomalies_are_nonmutating_rejections(
        tmp_path, shape):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9d-" + shape)
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    stage = (
        layout.attempt_dir
        / ".job-result.json.create-123-0123456789abcdef")
    target = layout.attempt_dir / "job-result.json"
    stage.write_bytes(data)
    stage.chmod(0o600)
    if shape == "different-inode":
        target.write_bytes(data)
        target.chmod(0o600)
        early = (
            capability.root / "job-staging"
            / ("123.server." + "1" * 32))
        early.mkdir(parents=True)
        os.link(target, early / "job-result.json")
        os.link(
            stage,
            early / ".job-result.json.create-123-0123456789abcdef")
        assert target.stat().st_nlink == stage.stat().st_nlink == 2
        assert target.stat().st_ino != stage.stat().st_ino
    else:
        os.link(stage, target)
        os.link(stage, tmp_path / "third-hardlink")
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="nlink|inode"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert target.exists() and stage.exists()


@pytest.mark.parametrize("shape", ["malformed-name", "symlink", "multiple"])
def test_reconciliation_rejects_ambiguous_staging_without_mutation(
        tmp_path, shape):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9x-" + shape)
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    if shape == "malformed-name":
        entries = [layout.attempt_dir / ".job-result.json.create-evil"]
        entries[0].write_bytes(data)
    elif shape == "symlink":
        outside = tmp_path / "outside-stage"
        outside.write_bytes(data)
        entries = [
            layout.attempt_dir
            / ".job-result.json.create-123-0123456789abcdef"]
        entries[0].symlink_to(outside)
    else:
        entries = [
            layout.attempt_dir
            / f".job-result.json.create-{pid}-0123456789abcdef"
            for pid in (123, 124)]
        for entry in entries:
            entry.write_bytes(data)
            entry.chmod(0o600)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="staging|multiple"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert all(entry.exists() or entry.is_symlink() for entry in entries)


@pytest.mark.parametrize("namespace", ["attempt", "early-job"])
def test_collector_rejects_generator_unreachable_staging_suffixes(
        tmp_path, namespace):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, "canonical-suffix-" + namespace)
    directory = layout.attempt_dir
    if namespace == "early-job":
        directory = (
            capability.root / "job-staging"
            / ("123.server." + "1" * 32))
        directory.mkdir(parents=True)
    data = _canonical(
        tmp_path / "canonical-suffix-payload.json",
        _job_value(job_script_hash)).read_bytes()
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    suffixes = [
        "0-0123456789abcdef",
        "00-0123456789abcdef",
        "001-0123456789abcdef",
        "pid-0123456789abcdef",
        "123-0123456789abcdeF",
        "123-0123456789abcde",
        "123-0123456789abcdef0",
    ]
    for target_present in (False, True):
        for suffix in suffixes:
            target = directory / "job-result.json"
            if target_present:
                target.write_bytes(data)
                target.chmod(0o600)
            stage = directory / f".job-result.json.create-{suffix}"
            if target_present:
                os.link(target, stage)
            else:
                stage.write_bytes(data)
                stage.chmod(0o600)
            before = _directory_snapshot(directory)
            with pytest.raises(
                    collector.CollectionError, match="staging name"):
                collector.collect(
                    repo_root=repo, attempt_id=attempt_id,
                    submission_receipt=submit, job_result=None,
                    scheduler_stdout=stdout, scheduler_stderr=stderr,
                    accounting=accounting)
            assert _directory_snapshot(directory) == before
            stage.unlink()
            if target_present:
                target.unlink()


def test_cross_namespace_preflight_rejects_before_any_cleanup(tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9-preflight")
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    attempt_stage = (
        layout.attempt_dir
        / ".job-result.json.create-123-0123456789abcdef")
    attempt_stage.write_bytes(data)
    attempt_stage.chmod(0o600)
    early = (
        capability.root / "job-staging"
        / ("123.server." + "1" * 32))
    early.mkdir(parents=True)
    malformed = early / ".job-result.json.create-ambiguous"
    malformed.write_bytes(data)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(collector.CollectionError, match="staging name"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert attempt_stage.exists()
    assert malformed.exists()


def test_reconciliation_fsync_order_brackets_after_publish_unlink(
        tmp_path, monkeypatch):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9fsync")
    data = _canonical(
        tmp_path / "payload.json", _job_value(job_script_hash)).read_bytes()
    _, stage = _after_publish_entries(layout.attempt_dir, data)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    observed = []
    real_fsync = collector._fsync_directory

    def record(path):
        if path == layout.attempt_dir:
            observed.append(stage.exists())
        real_fsync(path)

    monkeypatch.setattr(collector, "_fsync_directory", record)
    collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert observed[:2] == [True, False]


def _series_clean_job_value(layout, job_script_hash: str):
    """Semantically valid canonical for a completed `clean=True` series."""
    timing = load_json_strict(
        layout.attempt_dir / "series-result.json")["timing_envelope"]
    value = _job_value(job_script_hash, rc=0, failure="none")
    value.update({
        "job_started_monotonic_ns": timing["job_started_monotonic_ns"],
        "completed_monotonic_ns": timing["completed_monotonic_ns"],
        "elapsed_ns": (
            timing["completed_monotonic_ns"]
            - timing["job_started_monotonic_ns"]),
    })
    return value


def _after_publish_stage_from_canonical(canonical: Path) -> Path:
    """Publisher crash between `os.link` and `os.unlink`; canonical is first."""
    stage = (
        canonical.parent / ".job-result.json.create-123-0123456789abcdef")
    os.link(canonical, stage)
    return stage


def _ledger_state(capability, series_id: str) -> str:
    return SeriesAttemptLedger(
        capability, series_id,
        load_protocol()["retry"]["eligible_reasons"]).replay.state


def _no_receipt(attempt_dir: Path) -> bool:
    return not (
        (attempt_dir / "final-qualification-receipt.json").exists()
        or (attempt_dir / "attempt-failure-receipt.json").exists())


def test_m9e_after_publish_retirement_precedes_series_verification(tmp_path):
    """S1: a completed series whose publisher died between link and unlink.

    唯一の制約対象は「attempt の after-publish stage の回収が
    `verify_attempt` より前にあること」である。

    receipt の field assertion は `collect()` が返る前に公開 verifier
    (`_verify_post_job_receipt`) の再導出を自己検証するため恒真であり、
    独立な証拠になるのは filesystem (stage 消滅 / `st_nlink` / bytes 不変)、
    ledger 状態、`validate_failure_receipt_for_retry` の raise の 3 種だけ
    である。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9e", clean=True)
    canonical = _canonical(
        layout.attempt_dir / "job-result.json",
        _series_clean_job_value(layout, job_script_hash))
    canonical_bytes = canonical.read_bytes()
    stage = _after_publish_stage_from_canonical(canonical)
    assert canonical.stat().st_nlink == stage.stat().st_nlink == 2
    assert (canonical.stat().st_dev, canonical.stat().st_ino) == (
        stage.stat().st_dev, stage.stat().st_ino)
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    receipt = load_json_strict(first)
    assert receipt["schema_version"] == "t126-qualification-final-receipt/v1"
    assert (layout.attempt_dir / "final-qualification-receipt.json").is_file()
    assert receipt["terminal"] == "lower_boundary"
    assert receipt["job_result"] is not None
    assert not stage.exists()
    assert canonical.is_file() and canonical.read_bytes() == canonical_bytes
    assert canonical.stat().st_nlink == 1
    assert collector.verify_post_job_receipt(
        first, repo_root=repo).integrity_status == "valid"
    series_id = receipt["qualification_series_id"]
    assert _ledger_state(capability, series_id) == "terminal"
    ledger_dir = (
        capability.root / "series" / series_id / "attempt-ledger")
    ledger_bytes = {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))}
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first and second.read_bytes() == first_bytes
    assert {
        path.name: path.read_bytes()
        for path in sorted(ledger_dir.glob("*.json"))} == ledger_bytes
    assert canonical.read_bytes() == canonical_bytes


def test_m9g_attempt_retirement_is_not_skipped_by_rejection_returns(tmp_path):
    """S2: semantic-conflict return must not strand A's after-publish stage.

    receipt の field assertion は `collect()` の自己検証から恒真に従う。
    独立な証拠は filesystem (stage 消滅 / `st_nlink` / A と B の bytes・stat
    不変)、ledger 状態、`validate_failure_receipt_for_retry` の raise である。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "9g")
    canonical_value = _job_value(job_script_hash)
    canonical = _canonical(
        layout.attempt_dir / "job-result.json", canonical_value)
    canonical_bytes = canonical.read_bytes()
    stage = _after_publish_stage_from_canonical(canonical)
    assert canonical.stat().st_nlink == stage.stat().st_nlink == 2
    rejected_value = deepcopy(canonical_value)
    rejected_value["wmax_s"] = 29101
    early = (
        capability.root / "job-staging" / ("123.server." + "1" * 32))
    rejected = _canonical(early / "job-result.json", rejected_value)
    rejected_bytes = rejected.read_bytes()
    rejected_stat = rejected.lstat()
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    receipt = load_json_strict(first)
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["attempt_phase"] == "job-result-recovery"
    assert receipt["retry_eligible"] is False
    assert receipt["job_result"] is not None
    assert (layout.attempt_dir / receipt["job_result"]["path"]
            ).read_bytes() == canonical_bytes
    assert not stage.exists()
    assert canonical.read_bytes() == canonical_bytes
    assert canonical.stat().st_nlink == 1
    assert rejected.read_bytes() == rejected_bytes
    assert (
        rejected.lstat().st_dev, rejected.lstat().st_ino,
        rejected.lstat().st_nlink, rejected.lstat().st_mode,
        rejected.lstat().st_uid, rejected.lstat().st_size,
    ) == (
        rejected_stat.st_dev, rejected_stat.st_ino, rejected_stat.st_nlink,
        rejected_stat.st_mode, rejected_stat.st_uid, rejected_stat.st_size,
    )
    evidence = load_json_strict(
        layout.attempt_dir / "rejected-evidence/early-job-result.json")
    assert evidence["source_path"] == rejected.relative_to(
        capability.root).as_posix()
    assert evidence["sha256"] == hashlib.sha256(rejected_bytes).hexdigest()
    assert {
        key: evidence[key]
        for key in (
            "st_dev", "st_ino", "st_nlink", "st_mode", "st_uid", "st_size")
    } == {
        "st_dev": rejected_stat.st_dev,
        "st_ino": rejected_stat.st_ino,
        "st_nlink": rejected_stat.st_nlink,
        "st_mode": rejected_stat.st_mode,
        "st_uid": rejected_stat.st_uid,
        "st_size": rejected_stat.st_size,
    }
    assert collector.verify_post_job_receipt(
        first, repo_root=repo).integrity_status == "valid"
    assert _ledger_state(
        capability, receipt["qualification_series_id"]) == "initial_failed"
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first and second.read_bytes() == first_bytes


def test_invalid_return_does_not_strand_attempt_staging(tmp_path):
    """`invalid` return でも A の stage は回収される (guard は不発火)。

    A は構造不正 (`attempt_state == "invalid"`) なので、P4 の fail-closed
    guard の第 1 条件 (`attempt_state == "valid"`) が成立せず、第 2 条件の
    意味検証まで進まない。

    receipt の field assertion は `collect()` の自己検証から恒真に従う。
    独立な証拠は filesystem (stage 消滅 / `st_nlink` / A と B の bytes 不変)
    と ledger 状態である。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "invalid-return")
    canonical = layout.attempt_dir / "job-result.json"
    canonical.write_bytes(b'{"partial":')
    canonical.chmod(0o600)
    stage = _after_publish_stage_from_canonical(canonical)
    assert canonical.stat().st_nlink == stage.stat().st_nlink == 2
    early = (
        capability.root / "job-staging" / ("123.server." + "1" * 32))
    early.mkdir(parents=True)
    rejected = early / "job-result.json"
    rejected.write_bytes(b'{"invalid":')
    rejected.chmod(0o600)
    rejected_bytes = rejected.read_bytes()
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    receipt = load_json_strict(first)
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["job_result"] is None
    assert receipt["retry_eligible"] is False
    assert not stage.exists()
    assert canonical.read_bytes() == b'{"partial":'
    assert canonical.stat().st_nlink == 1
    assert rejected.read_bytes() == rejected_bytes
    assert (
        layout.attempt_dir / "rejected-evidence/early-job-result.bytes"
    ).read_bytes() == rejected_bytes
    evidence = load_json_strict(
        layout.attempt_dir / "rejected-evidence/early-job-result.json")
    assert evidence["sha256"] == hashlib.sha256(rejected_bytes).hexdigest()
    assert collector.verify_post_job_receipt(
        first, repo_root=repo).integrity_status == "valid"
    assert _ledger_state(
        capability, receipt["qualification_series_id"]) == "initial_failed"
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first and second.read_bytes() == first_bytes


def test_series_after_publish_semantic_conflict_closes_with_preserved_b(
        tmp_path):
    """S1×S2 直積の終端記録 + T1 の series 側 witness。

    「回収が `verify_attempt` と semantic-conflict return の両方より前」の
    うち、本テストが単独で張るのは前半だけである。`clean=True` なので
    `verify_attempt` の分岐に必ず入り、retire を後ろへ動かす登録変異
    (M9e / M9g) では常にそこで死ぬ。後半 (拒否 return より前) を張るのは
    `clean=False` の T3 / T4 である。本テスト固有の価値は直積の終端
    (`observations_recorded == 2` / `retry_eligible is False` /
    `validate_failure_receipt_for_retry` の raise) の記録にある。

    receipt の field assertion は `collect()` の自己検証から恒真に従う。
    独立な証拠は filesystem、ledger 状態、上記 raise の 3 種である。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, "series-conflict", clean=True)
    canonical_value = _series_clean_job_value(layout, job_script_hash)
    canonical = _canonical(
        layout.attempt_dir / "job-result.json", canonical_value)
    canonical_bytes = canonical.read_bytes()
    stage = _after_publish_stage_from_canonical(canonical)
    assert canonical.stat().st_nlink == stage.stat().st_nlink == 2
    rejected_value = deepcopy(canonical_value)
    rejected_value["wmax_s"] = 29101
    early = (
        capability.root / "job-staging" / ("123.server." + "1" * 32))
    rejected = _canonical(early / "job-result.json", rejected_value)
    rejected_bytes = rejected.read_bytes()
    rejected_stat = rejected.lstat()
    first = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    first_bytes = first.read_bytes()
    receipt = load_json_strict(first)
    assert receipt["schema_version"] == (
        "t126-qualification-attempt-failure-receipt/v1")
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["attempt_phase"] == "job-result-recovery"
    assert receipt["job_result"] is not None
    assert receipt["observations_recorded"] == 2
    assert receipt["retry_eligible"] is False
    assert not stage.exists()
    assert canonical.read_bytes() == canonical_bytes
    assert canonical.stat().st_nlink == 1
    assert rejected.read_bytes() == rejected_bytes
    evidence = load_json_strict(
        layout.attempt_dir / "rejected-evidence/early-job-result.json")
    assert evidence["source_path"] == rejected.relative_to(
        capability.root).as_posix()
    assert evidence["sha256"] == hashlib.sha256(rejected_bytes).hexdigest()
    assert evidence["st_ino"] == rejected_stat.st_ino
    assert collector.verify_post_job_receipt(
        first, repo_root=repo).integrity_status == "valid"
    assert _ledger_state(
        capability, receipt["qualification_series_id"]) == "initial_failed"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(first, repo, load_protocol())
    second = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    assert second == first and second.read_bytes() == first_bytes


@pytest.mark.parametrize(
    "shape", ["early-malformed-name", "different-inode", "extra-hardlink"])
def test_cross_namespace_preflight_rejects_before_attempt_stage_retire(
        tmp_path, shape):
    """global preflight が両 namespace を検査してから retire すること。

    順序を張るのは `early-malformed-name` の 1 shape であり、それを赤に
    する登録変異が **M9h** (retire を 2 本の `_reconcile_result_namespace`
    呼出しの間へ移す移動変異) である。`different-inode` /
    `extra-hardlink` は attempt 側 preflight 自身が先に raise するため
    順序制約を exercise せず、M9d の冗長 gate (series あり側の網羅目的)
    として置く。単独変異の証拠には数えない。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, "preflight-" + shape, clean=True)
    canonical = _canonical(
        layout.attempt_dir / "job-result.json",
        _series_clean_job_value(layout, job_script_hash))
    canonical_bytes = canonical.read_bytes()
    stage = (
        layout.attempt_dir
        / ".job-result.json.create-123-0123456789abcdef")
    early = (
        capability.root / "job-staging" / ("123.server." + "1" * 32))
    if shape == "early-malformed-name":
        os.link(canonical, stage)
        early.mkdir(parents=True)
        malformed = early / ".job-result.json.create-ambiguous"
        malformed.write_bytes(canonical_bytes)
        malformed.chmod(0o600)
    elif shape == "different-inode":
        stage.write_bytes(canonical_bytes)
        stage.chmod(0o600)
        early.mkdir(parents=True)
        os.link(canonical, early / "job-result.json")
        os.link(
            stage, early / ".job-result.json.create-123-0123456789abcdef")
        assert canonical.stat().st_ino != stage.stat().st_ino
    else:
        os.link(canonical, stage)
        os.link(canonical, tmp_path / "third-hardlink")
    stage_stat = stage.lstat()
    canonical_stat = canonical.lstat()
    early_before = _directory_snapshot(early) if early.is_dir() else None
    series_id = load_json_strict(submit)["qualification_series_id"]
    with pytest.raises(
            collector.CollectionError, match="staging name|inode|nlink"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert stage.is_file()
    assert stage.lstat().st_nlink == stage_stat.st_nlink
    assert stage.lstat().st_ino == stage_stat.st_ino
    assert canonical.read_bytes() == canonical_bytes
    assert (
        canonical.lstat().st_dev, canonical.lstat().st_ino,
        canonical.lstat().st_nlink, canonical.lstat().st_mode,
        canonical.lstat().st_uid, canonical.lstat().st_size,
    ) == (
        canonical_stat.st_dev, canonical_stat.st_ino,
        canonical_stat.st_nlink, canonical_stat.st_mode,
        canonical_stat.st_uid, canonical_stat.st_size,
    )
    if early_before is not None:
        assert _directory_snapshot(early) == early_before
    assert _no_receipt(layout.attempt_dir)
    assert _ledger_state(capability, series_id) == "initial_submitted"


def test_attempt_closure_rejects_unreconcilable_staging_bytes(tmp_path):
    """`_manifest` の abandoned staging 規則を message 単位で独立に pin する。

    この stage は reconciler の回収対象名 (`.job-result.json.create-` の
    attempt 直下) ではないため、必ず closure manifest まで到達する。
    collector 自身の receipt publish crash 残余 (裁定パッケージの B4) が
    残るため、この規則は本 wave の修正後も production で有効である。
    """
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "closure-staging")
    stage = (
        layout.attempt_dir
        / "prologue/.toolchain-manifest.json.create-123-0123456789abcdef")
    stage.write_bytes(b"abandoned staging\n")
    stage.chmod(0o600)
    stage_bytes = stage.read_bytes()
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    with pytest.raises(
            collector.CollectionError,
            match="attempt closure contains abandoned staging bytes"):
        collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)
    assert stage.is_file() and stage.read_bytes() == stage_bytes
    assert _no_receipt(layout.attempt_dir)


@pytest.mark.parametrize("semantics", ["semantic-valid", "semantic-invalid"])
@pytest.mark.parametrize("clean", [False, True])
@pytest.mark.parametrize("stage", [False, True])
def test_m9j_valid_canonical_with_rejected_early_result_fails_closed(
        tmp_path, stage, clean, semantics):
    """B 拒否時の A の扱いは、公開 gate と同じ意味判定で分岐する。

    `semantics` が本テストの中心である。`semantic-valid` は P4 の
    fail-closed guard が発火する側で、`semantic-invalid` (構造は valid・
    意味検証だけ落ちる canonical) は **guard が発火してはならない**側の正例
    である。後者が `job-result-publication-failed` の failure receipt へ閉じ
    ることは、guard が公開側 `pointer_missing_canonical` の判定より広く発火
    して受理集合を pre-image より狭めていないことの検出点になる。

    `stage` は load-bearing である。after-publish stage は canonical の第二の
    名前なので guard の raise より前に回収され、`stage_path` の消滅と
    canonical の `st_nlink == 1` がそれを固定する。したがって本テストは
    「無変更拒否」ではなく「receipt / ledger は無変更、A の bytes は不変、
    唯一の複製を壊さない情報保存的 retire だけが起きる」を pin する。

    `clean` は再走収束が所有外の除外規則に依存する点を張る。series あり側で
    1 走目に作られる `rejected-evidence/**` を 2 走目の `verify_attempt` が
    無視することは `t126_driver.py` の除外規則に依存しており、そこが動けば
    2 走目の終端が変わる。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, f"9j-{int(stage)}{int(clean)}-{semantics}", clean=clean)
    canonical_value = (
        _series_clean_job_value(layout, job_script_hash) if clean
        else _job_value(job_script_hash))
    if semantics == "semantic-invalid":
        # 構造 (`_job_result_fields`) は通り、意味検証
        # (`_validate_job_result_semantics`) の Wmax 判定だけが落ちる。
        canonical_value["wmax_s"] = 29101
    canonical = _canonical(
        layout.attempt_dir / "job-result.json", canonical_value)
    canonical_bytes = canonical.read_bytes()
    stage_path = None
    if stage:
        stage_path = _after_publish_stage_from_canonical(canonical)
        assert canonical.stat().st_nlink == stage_path.stat().st_nlink == 2
    early = (
        capability.root / "job-staging" / ("123.server." + "1" * 32))
    early.mkdir(parents=True)
    rejected = early / "job-result.json"
    rejected.write_bytes(b'{"invalid":')
    rejected.chmod(0o600)
    rejected_bytes = rejected.read_bytes()
    if not clean:
        accounting.write_text(
            "Request ID = 123.server\nExit_status = 34\n"
            "resources_used.walltime = 1\n", encoding="utf-8")
    series_id = load_json_strict(submit)["qualification_series_id"]

    def _collect():
        return collector.collect(
            repo_root=repo, attempt_id=attempt_id,
            submission_receipt=submit, job_result=None,
            scheduler_stdout=stdout, scheduler_stderr=stderr,
            accounting=accounting)

    def _assert_b_preserved():
        assert rejected.read_bytes() == rejected_bytes
        assert (
            layout.attempt_dir / "rejected-evidence/early-job-result.bytes"
        ).read_bytes() == rejected_bytes
        evidence = load_json_strict(
            layout.attempt_dir / "rejected-evidence/early-job-result.json")
        assert evidence["sha256"] == hashlib.sha256(
            rejected_bytes).hexdigest()
        assert evidence["source_path"] == rejected.relative_to(
            capability.root).as_posix()

    if semantics == "semantic-valid":
        for _ in range(2):
            with pytest.raises(
                    collector.CollectionError,
                    match=("attempt canonical conflicts with a rejected "
                           "early job-result")):
                _collect()
            assert _no_receipt(layout.attempt_dir)
            assert _ledger_state(capability, series_id) == "initial_submitted"
            assert canonical.read_bytes() == canonical_bytes
            assert canonical.stat().st_nlink == 1
            if stage:
                assert not stage_path.exists()
            _assert_b_preserved()
        return

    first = _collect()
    first_bytes = first.read_bytes()
    receipt = load_json_strict(first)
    assert receipt["schema_version"] == (
        "t126-qualification-attempt-failure-receipt/v1")
    assert receipt["failure_class"] == "job-result-publication-failed"
    assert receipt["attempt_phase"] == "job-result-recovery"
    assert receipt["job_result"] is None
    assert receipt["retry_eligible"] is False
    assert canonical.read_bytes() == canonical_bytes
    assert canonical.stat().st_nlink == 1
    if stage:
        assert not stage_path.exists()
    _assert_b_preserved()
    assert collector.verify_post_job_receipt(
        first, repo_root=repo).integrity_status == "valid"
    assert _ledger_state(capability, series_id) == "initial_failed"
    with pytest.raises(QualificationArtifactError):
        validate_failure_receipt_for_retry(first, repo, load_protocol())
    second = _collect()
    assert second == first and second.read_bytes() == first_bytes


@pytest.mark.parametrize("payload", ["empty", "complete"])
def test_m9i_targetless_attempt_staging_is_not_retired_before_verification(
        tmp_path, payload):
    """正例: targetless stage は fail-closed 拒否の前に破棄してはならない。

    `payload` は production の 3 crash 窓のうち両端 (0 byte / 完全 bytes) を
    張る。S1' (series 完走 × targetless) は本 wave の scope 外であり、
    ここでは現行の拒否挙動と非破壊性だけを固定する。
    """
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(
         tmp_path, "9i-" + payload, clean=True)
    data = (
        b"" if payload == "empty"
        else _canonical(
            tmp_path / "targetless-payload.json",
            _series_clean_job_value(layout, job_script_hash)).read_bytes())
    stage = (
        layout.attempt_dir
        / ".job-result.json.create-123-0123456789abcdef")
    stage.write_bytes(data)
    stage.chmod(0o600)
    assert stage.stat().st_nlink == 1
    series_id = load_json_strict(submit)["qualification_series_id"]
    for _ in range(2):
        with pytest.raises(collector.CollectionError) as excinfo:
            collector.collect(
                repo_root=repo, attempt_id=attempt_id,
                submission_receipt=submit, job_result=None,
                scheduler_stdout=stdout, scheduler_stderr=stderr,
                accounting=accounting)
        message = str(excinfo.value)
        assert "series result failed read-only verification" in message
        assert "unreferenced in-job evidence" in message
        assert ".job-result.json.create-123-0123456789abcdef" in message
        assert stage.is_file() and stage.stat().st_nlink == 1
        assert stage.read_bytes() == data
        assert not (layout.attempt_dir / "job-result.json").exists()
        assert _no_receipt(layout.attempt_dir)
        assert _ledger_state(capability, series_id) == "initial_submitted"


def test_m10a_invalid_to_missing_coherent_rehash_cannot_gain_retry(
        tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, _) = _attempt(tmp_path, "10a")
    canonical = layout.attempt_dir / "job-result.json"
    canonical.write_bytes(b'{"partial":')
    canonical.chmod(0o600)
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    original = load_json_strict(receipt_path)
    assert original["failure_class"] == "job-result-publication-failed"
    assert original["retry_eligible"] is False
    canonical.unlink()
    forged = deepcopy(original)
    forged["failure_class"] = "pre-member-infrastructure"
    forged["retry_eligible"] = True
    forged["closure_manifest"] = [
        row for row in forged["closure_manifest"]
        if row["path"] != "job-result.json"]
    _rehash_receipt_ledger(receipt_path, capability, forged)
    verified = collector.verify_post_job_receipt(
        receipt_path, repo_root=repo)
    try:
        validate_failure_receipt_for_retry(
            receipt_path, repo, load_protocol())
    except QualificationArtifactError:
        retry_admitted = False
    else:
        retry_admitted = True
    ledger = SeriesAttemptLedger(
        capability, forged["qualification_series_id"],
        load_protocol()["retry"]["eligible_reasons"])
    if not retry_admitted:
        ledger_admitted = False
    else:
        try:
            ledger.claim_retry(
                nonce="e" * 32,
                submission_intent_sha256="f" * 64,
                retry_from_attempt_id=attempt_id,
                retry_from_receipt_sha256=hashlib.sha256(
                    receipt_path.read_bytes()).hexdigest())
        except AttemptLedgerError:
            ledger_admitted = False
        else:
            ledger_admitted = True
    assert (
        verified.integrity_status, retry_admitted, ledger_admitted
    ) == ("invalid", False, False)


def test_m10b_valid_canonical_requires_nonnull_exact_pointer(tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "10b")
    _canonical(
        layout.attempt_dir / "job-result.json",
        _job_value(job_script_hash, rc=30, failure="member-rejected"))
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 30\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    forged = deepcopy(load_json_strict(receipt_path))
    pointed = layout.attempt_dir / forged["job_result"]["path"]
    pointed.unlink()
    pointed_path = forged["job_result"]["path"]
    forged["job_result"] = None
    forged["attempt_phase"] = "job-result-recovery"
    forged["failure_class"] = "job-result-publication-failed"
    forged["retry_eligible"] = False
    forged["closure_manifest"] = [
        row for row in forged["closure_manifest"]
        if row["path"] != pointed_path]
    _rehash_receipt_ledger(receipt_path, capability, forged)
    verified = collector.verify_post_job_receipt(
        receipt_path, repo_root=repo)
    assert verified.integrity_status == "invalid"


def test_m10c_publish_then_scheduler_kill_closes_accounting_mismatch(
        tmp_path):
    (repo, _, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "10c", clean=True)
    canonical = _canonical(
        layout.attempt_dir / "job-result.json",
        _job_value(job_script_hash, rc=0, failure="none"))
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 137\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = load_json_strict(receipt_path)
    assert receipt["failure_class"] == "job-result-accounting-mismatch"
    assert receipt["attempt_phase"] == "job-result-accounting-mismatch"
    assert receipt["job_result"] is not None
    assert receipt["retry_eligible"] is False
    assert canonical.is_file()
    assert not (layout.attempt_dir / "final-qualification-receipt.json").exists()
    assert collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status == "valid"


def test_m10d_new_failure_classes_are_disjoint_from_all_retry_authority(
        tmp_path):
    protocol = load_protocol()
    expanded = deepcopy(protocol)
    expanded["retry"]["eligible_reasons"].extend([
        "job-result-publication-failed",
        "job-result-accounting-mismatch",
    ])
    history_admission = {}
    for failure in (
            "job-result-publication-failed",
            "job-result-accounting-mismatch"):
        history_admission[failure] = validate_retry_history([{
            "attempt_id": "a" * 64,
            "observations_recorded": 0,
            "terminal": None,
            "failure_reason": failure,
        }], expanded)
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "10d", clean=True)
    _canonical(
        layout.attempt_dir / "job-result.json",
        _job_value(job_script_hash, rc=0, failure="none"))
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 137\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    forged = deepcopy(load_json_strict(receipt_path))
    forged["retry_eligible"] = True
    _rehash_receipt_ledger(receipt_path, capability, forged)
    public_status = collector.verify_post_job_receipt(
        receipt_path, repo_root=repo).integrity_status
    try:
        validate_failure_receipt_for_retry(
            receipt_path, repo, expanded)
    except QualificationArtifactError:
        retry_admitted = False
    else:
        retry_admitted = True
    series_id = forged["qualification_series_id"]
    ledger = SeriesAttemptLedger(
        capability, series_id, expanded["retry"]["eligible_reasons"])
    try:
        ledger.claim_retry(
            nonce="e" * 32,
            submission_intent_sha256="f" * 64,
            retry_from_attempt_id=attempt_id,
            retry_from_receipt_sha256=hashlib.sha256(
                receipt_path.read_bytes()).hexdigest())
    except AttemptLedgerError:
        ledger_admitted = False
    else:
        ledger_admitted = True
    assert history_admission == {
        "job-result-publication-failed": False,
        "job-result-accounting-mismatch": False,
    }
    assert (public_status, retry_admitted, ledger_admitted) == (
        "invalid", False, False)


def test_retry_protocol_eligible_reason_set_is_frozen():
    protocol = load_protocol()
    assert protocol["retry"]["eligible_reasons"] == [
        "pre-attempt-infrastructure", "pre-member-infrastructure",
        "pre-attestation", "reservation-unavailable"]
    for failure in (
            "job-result-publication-failed",
            "job-result-accounting-mismatch"):
        mutated = deepcopy(protocol)
        mutated["retry"]["eligible_reasons"].append(failure)
        with pytest.raises(ProtocolError, match="retry contract"):
            validate_protocol(mutated)


def test_m11a_coherent_submission_job_rewrite_cannot_cross_committed_blob_edge(
        tmp_path):
    (repo, capability, layout, attempt_id, submit, stdout, stderr,
     accounting, job_script_hash) = _attempt(tmp_path, "11a")
    canonical = _canonical(
        layout.attempt_dir / "job-result.json",
        _job_value(job_script_hash))
    accounting.write_text(
        "Request ID = 123.server\nExit_status = 34\n"
        "resources_used.walltime = 1\n", encoding="utf-8")
    receipt_path = collector.collect(
        repo_root=repo, attempt_id=attempt_id,
        submission_receipt=submit, job_result=None,
        scheduler_stdout=stdout, scheduler_stderr=stderr,
        accounting=accounting)
    receipt = deepcopy(load_json_strict(receipt_path))
    replacement_hash = "e" * 64
    source_manifest_path = (
        layout.attempt_dir / "source/source-snapshots.json")
    source_manifest = load_json_strict(source_manifest_path)
    submission_paths = [
        layout.attempt_dir
        / source_manifest["submission_receipt"]["path"],
        layout.attempt_dir / receipt["submission_receipt"]["path"],
    ]
    for path in submission_paths:
        value = load_json_strict(path)
        value["job_script_sha256"] = replacement_hash
        _canonical(path, value)
    source_manifest["submission_receipt"].update(file_record(
        submission_paths[0], relative_to=layout.attempt_dir))
    _canonical(source_manifest_path, source_manifest)
    for path in (
            canonical,
            layout.attempt_dir / receipt["job_result"]["path"]):
        value = load_json_strict(path)
        value["job_script_sha256"] = replacement_hash
        _canonical(path, value)
    replacements = {
        path.relative_to(layout.attempt_dir).as_posix():
            file_record(path, relative_to=layout.attempt_dir)
        for path in (
            source_manifest_path, *submission_paths, canonical,
            layout.attempt_dir / receipt["job_result"]["path"])
    }
    receipt["submission_receipt"] = replacements[
        submission_paths[1].relative_to(layout.attempt_dir).as_posix()]
    receipt["job_result"] = replacements[
        receipt["job_result"]["path"]]
    receipt["closure_manifest"] = [
        replacements.get(row["path"], row)
        for row in receipt["closure_manifest"]]
    _rehash_receipt_ledger(receipt_path, capability, receipt)
    verified = collector.verify_post_job_receipt(
        receipt_path, repo_root=repo)
    assert verified.integrity_status == "invalid"
    assert "committed series blob" in " ".join(verified.errors)


@pytest.mark.parametrize(
    ("boundary", "published", "complete_staging"),
    [
        ("", True, False),
        ("after-open", False, False),
        ("after-short-write", False, False),
        ("after-fsync", False, True),
        ("after-publish", True, True),
    ],
)
def test_m11b_exact_spooled_script_uses_embedded_isolated_publisher(
        tmp_path, boundary, published, complete_staging):
    repo = tmp_path / "publisher-repo"
    script = repo / "tools/pegasus/t126_qualification.sh"
    script.parent.mkdir(parents=True)
    shutil.copy2(_ROOT / "tools/pegasus/t126_qualification.sh", script)
    helper = repo / PREFLIGHT_HELPER_RELATIVE
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(_fixture_preflight_source(), encoding="utf-8")
    nonce = "a" * 32
    receipt = (
        repo / "output/env/pegasus/qualification/t126/submissions"
        / nonce / "submit-receipt.json")
    _canonical(receipt, {})
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "exact production spool")
    commit = _git(repo, "rev-parse", "HEAD")
    _canonical(receipt, {"source_commit": commit})
    committed = subprocess.check_output(
        ["git", "-C", str(repo), "cat-file", "blob",
         f"{commit}:tools/pegasus/t126_qualification.sh"])
    sentinel_root = tmp_path / "sentinel"
    package = sentinel_root / "orchestrator" / "qualification"
    package.mkdir(parents=True)
    (package.parent / "__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    sentinel = tmp_path / "persistent-import-ran"
    (package / "atomic_publish.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n"
        "raise RuntimeError('persistent package imported')\n",
        encoding="utf-8")
    job_env = {
        **os.environ,
        "PBS_JOBID": "123.server",
        "PBS_O_WORKDIR": str(repo),
        "IZANAGI_SUBMISSION_NONCE": nonce,
        "PYTHONPATH": str(sentinel_root),
        "IZANAGI_T126_TEST_PERSISTENT_PACKAGE_ROOT": str(sentinel_root),
    }
    if boundary:
        job_env["IZANAGI_T126_TEST_JOB_RESULT_CRASH"] = boundary
    completed = subprocess.run(
        ["bash", str(script)], cwd=repo,
        env=job_env,
        capture_output=True, text=True, timeout=20)
    assert completed.returncode == 2
    result_dir = (
        repo / "output/env/pegasus/qualification/t126/job-staging"
        / f"123.server.{nonce}")
    result_path = result_dir / "job-result.json"
    stages = list(result_dir.glob(".job-result.json.create-*"))
    assert result_path.exists() is published
    assert bool(stages) is bool(boundary)
    if complete_staging:
        staged_result = load_json_strict(stages[0])
        assert staged_result["job_script_sha256"] == hashlib.sha256(
            committed).hexdigest()
    if published:
        result = load_json_strict(result_path)
        assert result["job_script_sha256"] == hashlib.sha256(
            committed).hexdigest()
    if boundary == "after-publish":
        assert result_path.stat().st_ino == stages[0].stat().st_ino
        assert result_path.stat().st_nlink == 2
    exact_hash = hashlib.sha256(committed).hexdigest()
    assert hashlib.sha256(script.read_bytes()).hexdigest() == exact_hash
    assert not sentinel.exists()


def test_fr3_mutation_node_registry_is_exact_and_complete():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    actual = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and re.fullmatch(r"test_m(?:8[a-j]|9[a-j]|10[a-j]|11[a-j]|12|13)_.+",
                         node.name)
    }
    expected = {
        "test_m8a_create_only_invocation_claim_serializes_parallel_submit",
        "test_m8b_post_qsub_prebinding_crash_never_uses_raw_stdout_authority",
        "test_m8c_qsub_nonzero_is_accepted_unknown_and_never_resubmitted",
        "test_m8d_binding_v2_exact_corpus_and_all_consumer_wiring",
        "test_m9a_targetless_full_staging_is_discarded_to_nonretry_failure",
        "test_m9b_after_publish_stage_cleanup_and_collector_rerun_converge",
        "test_m9c_exact_early_job_staging_is_recovered_and_closed",
        "test_m9d_inode_and_nlink_anomalies_are_nonmutating_rejections",
        "test_m9e_after_publish_retirement_precedes_series_verification",
        "test_m9g_attempt_retirement_is_not_skipped_by_rejection_returns",
        "test_m9i_targetless_attempt_staging_is_not_retired_before_verification",
        "test_m9j_valid_canonical_with_rejected_early_result_fails_closed",
        "test_m10a_invalid_to_missing_coherent_rehash_cannot_gain_retry",
        "test_m10b_valid_canonical_requires_nonnull_exact_pointer",
        "test_m10c_publish_then_scheduler_kill_closes_accounting_mismatch",
        "test_m10d_new_failure_classes_are_disjoint_from_all_retry_authority",
        "test_m11a_coherent_submission_job_rewrite_cannot_cross_committed_blob_edge",
        "test_m11b_exact_spooled_script_uses_embedded_isolated_publisher",
        "test_m12_relaxed_live_schema_cannot_expand_receipt_acceptance",
        "test_m13_qualification_schema_memo_drift_fails_closed",
    }
    assert actual == expected
    assert set(T126_MUTATION_REGISTRY) == {
        "M1", "M2a", "M2b", "M2c", "M3", "M4a", "M4b", "M5a", "M5b",
        "M6a", "M6b", "M6c", "M6d", "M7a", "M7b", "M7c",
        "M8a", "M8b", "M8c", "M8d",
        "M9a", "M9b", "M9c", "M9d", "M9e", "M9g", "M9h", "M9i", "M9j",
        "M10a", "M10b", "M10c", "M10d", "M11a", "M11b", "M12", "M13",
    }
    parsed = {}
    transforms = set()
    for mutation_id, row in T126_MUTATION_REGISTRY.items():
        assert set(row) == {
            "source_path", "old_anchor", "replacement", "node"}
        assert row["source_path"] and row["old_anchor"]
        source_path = _ROOT / row["source_path"]
        assert source_path.is_file(), mutation_id
        source = source_path.read_text(encoding="utf-8")
        assert source.count(row["old_anchor"]) == 1, mutation_id
        assert row["replacement"] != row["old_anchor"], mutation_id
        transformed = source.replace(
            row["old_anchor"], row["replacement"], 1)
        assert transformed != source, mutation_id
        transform = (
            row["source_path"], row["old_anchor"], row["replacement"])
        assert transform not in transforms, mutation_id
        transforms.add(transform)
        relative, node = row["node"].split("::", 1)
        if relative not in parsed:
            parsed[relative] = {
                item.name for item in ast.parse(
                    (_ROOT / relative).read_text(encoding="utf-8")).body
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert node in parsed[relative], mutation_id
    # M9e は retire 呼出しの位置だけを動かす純粋な移動変異である。anchor と
    # replacement の行の多重集合が一致することを機械で保証し、「削除ではなく
    # 移動」を目視レビュー任せにしない。M9g は拒否 return を跨がせるための
    # guard 行 (`if canonical_state not in ...`) を、M9h は helper の no-op 化
    # (docstring と本体の書き換え) を、M9i は定数へ要素を足す行の書き換えを
    # 伴うため、いずれも行の多重集合は保存されず対象外である。
    m9e = T126_MUTATION_REGISTRY["M9e"]
    assert sorted(m9e["old_anchor"].splitlines()) == sorted(
        m9e["replacement"].splitlines())


def test_submission_durable_json_completes_partial_write(monkeypatch, tmp_path):
    from orchestrator.qualification import submission

    expected = b'{"payload":"partial-write"}\n'
    write_results = []
    real_os = submission.os

    class OsProxy:
        def __getattr__(self, name):
            return getattr(real_os, name)

    def partial_write(fd, data):
        requested = len(data)
        written = real_os.write(fd, data[:min(3, requested)])
        write_results.append((requested, written))
        return written

    target = tmp_path / "submission.json"
    proxy = OsProxy()
    proxy.write = partial_write
    with monkeypatch.context() as patch:
        patch.setattr(submission, "os", proxy)
        submission._durable_json(target, {"payload": "partial-write"})

    assert target.read_bytes() == expected
    assert sum(written < requested for requested, written in write_results) >= 2


def test_submission_durable_json_rejects_zero_write(monkeypatch, tmp_path):
    from orchestrator.qualification import submission

    real_os = submission.os
    write_calls = 0

    class OsProxy:
        def __getattr__(self, name):
            return getattr(real_os, name)

    def zero_write(_fd, _data):
        nonlocal write_calls
        write_calls += 1
        if write_calls > 1:
            pytest.fail("submission retried after a zero-byte write")
        return 0

    target = tmp_path / "submission.json"
    proxy = OsProxy()
    proxy.write = zero_write
    with monkeypatch.context() as patch:
        patch.setattr(submission, "os", proxy)
        with pytest.raises(submission.SubmissionPreparationError):
            submission._durable_json(target, {"payload": "zero-write"})

    assert write_calls == 1


def _canonical_perf_receipt(*, available: bool) -> dict[str, object]:
    events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
    return {
        "schema": "izanagi-perf-preflight/v1",
        "status": "available" if available else "unavailable",
        "available": available,
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv", "-e",
            ",".join(events), "--", "/bin/true",
        ],
        "rc": 0 if available else None,
        "parsed_events": events if available else [],
        "reason": "available" if available else "perf-not-found",
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


def _run_copied_toolchain_validator(
        tmp_path: Path, *, toolchain: dict[str, object],
        compute_receipt: dict[str, object]):
    script = (_ROOT / "tools/pegasus/t126_qualification.sh").read_text(
        encoding="utf-8")
    command = script.index(
        '"$PY" -I -S -B - "$JOB_STAGING/toolchain-manifest.json"')
    start = script.index("import hashlib,json,os,sys\n", command)
    body = script[start:script.index("\nPY\n", start)]
    manifest_path = _canonical(tmp_path / "toolchain.json", toolchain)
    receipt_path = _canonical(tmp_path / "compute-receipt.json", compute_receipt)
    executable = str(Path(sys.executable).resolve(strict=True))
    return subprocess.run(
        [
            sys.executable, "-I", "-S", "-B", "-",
            str(manifest_path), executable, executable, executable, executable,
            executable, "6" * 40, "7" * 40, str(receipt_path), str(_ROOT),
        ],
        input=body, text=True, capture_output=True,
    )


def _toolchain_fixture(*, degraded: bool) -> dict[str, object]:
    executable = Path(sys.executable).resolve(strict=True)
    row = {
        "path": str(executable),
        "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "version": "fixture 1",
    }
    names = ("python", "cc", "cxx", "cmake") if degraded else (
        "python", "cc", "cxx", "cmake", "perf")
    value = {
        "schema_version": "t126-toolchain-manifest/v1",
        "executables": {name: dict(row) for name in names},
        "dependencies": {
            "gflags": {"commit": "6" * 40, "tree": "8" * 40},
            "glog": {"commit": "7" * 40, "tree": "9" * 40},
        },
        "build_argv": {},
    }
    if degraded:
        value["perf_preflight"] = _canonical_perf_receipt(available=False)
    return value


def test_copied_toolchain_rehash_is_compute_perf_conditional(tmp_path):
    submission_perf = _toolchain_fixture(degraded=False)
    compute_degraded = _run_copied_toolchain_validator(
        tmp_path / "submission-true-compute-false",
        toolchain=submission_perf,
        compute_receipt=_canonical_perf_receipt(available=False),
    )
    assert compute_degraded.returncode == 0, compute_degraded.stderr

    missing_compute_perf = _run_copied_toolchain_validator(
        tmp_path / "submission-false-compute-true",
        toolchain=_toolchain_fixture(degraded=True),
        compute_receipt=_canonical_perf_receipt(available=True),
    )
    assert missing_compute_perf.returncode != 0
    assert "compute perf requires submission perf identity" in (
        missing_compute_perf.stderr)

    drifted = _toolchain_fixture(degraded=False)
    drifted["executables"]["perf"]["sha256"] = "f" * 64
    perf_hash = _run_copied_toolchain_validator(
        tmp_path / "compute-true-hash-drift",
        toolchain=drifted,
        compute_receipt=_canonical_perf_receipt(available=True),
    )
    assert perf_hash.returncode != 0
    assert "tool hash mismatch: perf" in perf_hash.stderr


def _run_candidate_preflight_block(
        tmp_path: Path, *, functional_candidate: bool):
    script = (_ROOT / "tools/pegasus/t126_qualification.sh").read_text(
        encoding="utf-8")
    start = script.index('PERF_REAL=""\n')
    end = script.index("readarray -t SUBMIT_ID", start)
    block = script[start:end]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(parents=True)
    for name in ("grep", "mkdir", "ln"):
        resolved = shutil.which(name)
        assert resolved is not None
        (fake_bin / name).symlink_to(resolved)
    candidate = tmp_path / "policy-perf"
    if functional_candidate:
        candidate.write_text(
            "#!/bin/sh\n"
            "output=; previous=\n"
            "for argument in \"$@\"; do\n"
            "  [ \"$previous\" != -o ] || output=$argument\n"
            "  previous=$argument\n"
            "done\n"
            "events='1,,LLC-load-misses\n1,,LLC-loads\n"
            "1,,instructions\n1,,cycles'\n"
            "if [ -n \"$output\" ]; then\n"
            "  printf '%s\\n' \"$events\" > \"$output\"\n"
            "else\n"
            "  printf '%s\\n' \"$events\" >&2\n"
            "fi\n",
            encoding="utf-8")
        candidate.chmod(0o755)
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"perf_candidates": [str(candidate)]}) + "\n")
    staging = tmp_path / "staging"
    scratch = tmp_path / "scratch"
    staging.mkdir()
    scratch.mkdir()
    prefix = (
        "set -Eeuo pipefail\n"
        f"PY={shlex.quote(str(Path(sys.executable).resolve(strict=True)))}\n"
        f"SOURCE_STAGE={shlex.quote(str(_ROOT))}\n"
        f"POLICY={shlex.quote(str(policy))}\n"
        f"JOB_STAGING={shlex.quote(str(staging))}\n"
        f"SCR_ROOT={shlex.quote(str(scratch))}\n"
        f"PATH={shlex.quote(str(fake_bin))}\nexport PATH\n"
        "run_with_budget() { shift; \"$@\"; }\n"
        "check_job_deadline() { :; }\n"
    )
    suffix = "printf '%s|%s\\n' \"$USE_PERF\" \"$PERF_REAL\"\n"
    bash = shutil.which("bash")
    assert bash is not None
    completed = subprocess.run(
        [bash, "-c", prefix + block + suffix],
        capture_output=True, text=True,
    )
    receipt = load_json_strict(staging / "perf-preflight.json")
    return completed, receipt, candidate


def _run_degraded_source_stage_evidence_builder(tmp_path: Path):
    script = (_ROOT / "tools/pegasus/t126_qualification.sh").read_text(
        encoding="utf-8")
    command = script.index('"$JOB_STAGING/source-stage-evidence.json"')
    start = script.index("import hashlib,json,os,sys\n", command)
    body = script[start:script.index("\nPY\n", start)]
    target = tmp_path / "source-stage-evidence.json"
    toolchain = _canonical(tmp_path / "toolchain.json", {})
    receipt = _canonical(
        tmp_path / "perf-preflight.json",
        _canonical_perf_receipt(available=False))
    completed = subprocess.run(
        [
            sys.executable, "-I", "-S", "-B", "-", str(target),
            "a" * 40, "b" * 40, "c" * 40, str(_ROOT), str(toolchain),
            str(tmp_path / "absent-perf.stdout"),
            str(tmp_path / "absent-perf.stderr"), str(receipt), "0",
        ],
        input=body, text=True, capture_output=True,
    )
    return completed, load_json_strict(target)


def test_literal_perf_absent_functional_policy_candidate_stays_perf_present(
        tmp_path):
    completed, receipt, candidate = _run_candidate_preflight_block(
        tmp_path, functional_candidate=True)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == f"1|{candidate}"
    assert receipt["status"] == "available"
    assert receipt["available"] is True


def test_candidate_exhaustion_uses_canonical_unavailable_without_early_exit(
        tmp_path):
    completed, receipt, candidate = _run_candidate_preflight_block(
        tmp_path, functional_candidate=False)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "0|"
    assert not candidate.exists()
    assert receipt["status"] == "unavailable"
    assert receipt["available"] is False
    evidence_run, evidence = _run_degraded_source_stage_evidence_builder(
        tmp_path / "evidence")
    assert evidence_run.returncode == 0, evidence_run.stderr
    assert evidence["perf_observation"] == {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": _canonical_perf_receipt(available=False),
        "claim_scope": {
            "throughput": "eligible", "perf_required": "unsupported"},
    }
    assert not {
        "perf_smoke_returncode", "perf_smoke_stdout", "perf_smoke_stderr",
    } & set(evidence)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
