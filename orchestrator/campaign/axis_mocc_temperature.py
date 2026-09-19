"""MOCC proof-only temperature predicate contract; exploration remains unapproved.

SYNTAX_CONTRACT_FORBIDDEN は禁止例の列挙であり完全な blacklist ではない。
DQ pass は物理行の封じ込めだけ。値渡し二引数と定数の比較・論理結合だけを許可し、
代入、pointer/reference、呼出し、型/global 定義を許可しない。
"""
from __future__ import annotations

import copy
import hashlib
import importlib
from pathlib import Path
import re
from . import pin

MARKER_ID = "mocc-temperature-predicate"
SOURCE_REL = "cc/mocc/transaction.cc"
TEMPLATE_PATCH = "mocc-temperature-predicate-variant.patch"
INSTRUMENTATION_PATCH = "instr-mocc-lock-coverage-temperature.patch"
FLAG = "MOCC_TEMP_PREDICATE"
PIN = pin.CURRENT_PIN
PROOF_PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
TEMPLATE_TOUCH_SET = frozenset({"cmake/Options.cmake", SOURCE_REL})
FROZEN_TEMPLATE_HOLE_BYTES = b"  return temp >= threshold;"
FROZEN_TEMPLATE_BLOCK_BYTES = (
    b"  // EVOLVE-BLOCK-BEGIN mocc-temperature-predicate\n"
    b"  // Pure comparison of temp, threshold and constants only; no calls or state.\n"
    b"#if MOCC_TEMP_PREDICATE\n"
    b"  return temp >= threshold;\n"
    b"#else\n"
    b"  return temp >= threshold;\n"
    b"#endif\n"
    b"  // EVOLVE-BLOCK-END mocc-temperature-predicate\n"
)
SYNTAX_CONTRACT_ALLOWED = ("temp", "threshold", "bool/integer constants")
SYNTAX_CONTRACT_FORBIDDEN = (
    "FLAGS_", "thid_", "result_", "read_set_", "write_set_", "node_map_",
    "CLL_", "RLL_", "rnd_", "TRACE", "getenv", "rdtsc", "rdtscp",
)
AUDITOR_MOCC_REQUIRED = {
    ("gallery", 8): "mocc では非 INSERT write の被覆を、CLL_ の `key_ == rcdptr_ && mode_ && lock_ == &rcdptr_->rwlock_` と RWLOCK counter `W_LOCKED` で確認する。",
    ("gallery", 9): "mocc では transaction.cc の tidword 比較 (e9e477ca:1010〜1013) と `W_LOCKED` / searchWriteSet 判定 (1024〜1036) の条件、read_set_ 全走査、abort を固定する。",
    ("gallery", 13): "mocc-temperature-predicate でも編集面は helper 内の単一述語行だけである。",
    ("gallery", 16): "mocc の読取契約は、値渡しされた temp と threshold、bool / 整数定数による比較・論理結合だけである。",
    ("checklist", 11): "mocc では mocc-temperature-predicate の適用済み骨格と実 diff を行単位で照合し、変更が helper の hole 一行だけに収まることを確認する。",
    ("checklist", 12): "mocc でも thread / key / storage による優先や fitness 適応を監査する。",
    ("checklist", 13): "mocc では temp / threshold の値渡し契約、helper 署名、四つの呼出側引数、温度記録、CLL_/RLL_ 骨格と970のfallbackの無改変を確認する。",
}


class MoccProofBindingError(ValueError):
    pass


def require_proof_binding(proof, *, repo_root, source_rel, template_patch,
                          ccbench_commit, instrumentation_patch):
    """Bind assets and consumer arguments; all_pass is deliberately separate."""
    def require(ok, message):
        if not ok:
            raise MoccProofBindingError(message)
    try:
        require(proof["schema_version"] == "s3-mocc-template-proof/v1", "schema")
        require(source_rel == SOURCE_REL, "consumer source")
        require(template_patch == "patches/" + TEMPLATE_PATCH, "consumer template path")
        require(instrumentation_patch == "patches/" + INSTRUMENTATION_PATCH, "consumer instrumentation path")
        require(ccbench_commit == proof["ccbench_commit"] == PROOF_PIN, "proof OID")
        template = proof["template"]
        for key, value in (("source_rel", source_rel), ("marker_id", MARKER_ID),
                           ("flag", FLAG), ("path", template_patch)):
            require(template[key] == value, key)
        require(sorted(template["touch_set"]) == sorted(TEMPLATE_TOUCH_SET), "template touch set")
        instrumentation = proof["patches"]["instrumentation"]
        require(instrumentation["path"] == instrumentation_patch, "instrumentation path")
        for record, relative in ((template, template_patch), (instrumentation, instrumentation_patch)):
            require(record["sha256"] == hashlib.sha256((Path(repo_root) / relative).read_bytes()).hexdigest(), "asset sha256")
    except (KeyError, TypeError, OSError, ValueError) as exc:
        raise MoccProofBindingError(str(exc)) from exc


def check_auditor_definition(text):
    sections = {}
    for section in re.split(r"(?m)^## ", text)[1:]:
        heading, _, body = section.partition("\n")
        key = ("gallery" if heading.startswith("CC 版 reward hack ギャラリー") else
               "checklist" if heading.startswith("何を見るか") else None)
        if key is not None:
            parts = re.split(r"(?m)^(\d+)\. ", body)
            sections[key] = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
    return {f"{section}_{number}": sentence in sections.get(section, {}).get(number, "")
            for (section, number), sentence in AUDITOR_MOCC_REQUIRED.items()}


_CORRECTNESS = frozenset({"verdict", "certified", "total_cycles", "lock_coverage_violations",
                          "permutation_violations", "x_reasons", "p_reasons", "integrity"})
_INTEGRITY = frozenset({"orphan_reads", "version_dups", "dup_txids", "genesis_commits",
    "missing_txids", "write_version_mismatch", "malformed_keys", "framing_violations",
    "framing_violation_details", "write_intent_violations", "lock_coverage_violations",
    "permutation_violations", "clean", "permutation_violation_details", "notes"})
_MACROS = frozenset({FLAG, "TRACE", "RWLOCK", "TEMPERATURE_RESET_OPT", "KEY_SORT"})


def auditor_projection(run_record):
    """Accept explicit correctness input; refuse raw timed benchmark records.

    The producer constructs this input from observations and binds it to candidate
    digests and effective macros. Unknown structured fields fail closed.
    """
    allowed = _CORRECTNESS | {"base_sha256", "source_sha256", "diff_sha256", "macro_context"}
    if not isinstance(run_record, dict) or set(run_record) != allowed:
        raise ValueError("auditor input must contain only the complete correctness projection")
    for key in ("base_sha256", "source_sha256", "diff_sha256"):
        if not isinstance(run_record[key], str) or not re.fullmatch(r"[0-9a-f]{64}", run_record[key]):
            raise ValueError("invalid attribution digest")
    if not isinstance(run_record["macro_context"], dict) or set(run_record["macro_context"]) != _MACROS:
        raise ValueError("macro context differs")
    if any(type(value) is not int or value not in (0, 1) for value in run_record["macro_context"].values()):
        raise ValueError("invalid effective macro value")
    integrity = run_record["integrity"]
    if not isinstance(integrity, dict) or set(integrity) != _INTEGRITY:
        raise ValueError("integrity fields differ")
    if (run_record["verdict"] not in ("serializable", "indeterminate", "non-serializable")
            or type(run_record["certified"]) is not bool or type(integrity["clean"]) is not bool):
        raise ValueError("invalid correctness scalars")
    for key in ("total_cycles", "lock_coverage_violations", "permutation_violations"):
        if type(run_record[key]) is not int or run_record[key] < 0:
            raise ValueError("invalid correctness count")
    for key in _INTEGRITY - {"clean", "notes", "framing_violation_details", "permutation_violation_details"}:
        if type(integrity[key]) is not int or integrity[key] < 0:
            raise ValueError("invalid integrity count")
    def fields(value, keys):
        if type(value) is not dict or set(value) != set(keys):
            raise ValueError("unknown integrity detail field")
    def rows(value):
        if type(value) is not list:
            raise ValueError("invalid integrity details")
        return value
    for row in rows(integrity["framing_violation_details"]):
        fields(row, ("kind", "txid", "expected_reads", "observed_reads", "expected_writes", "observed_writes"))
        if type(row["kind"]) is not str or any(v is not None and type(v) is not int for k,v in row.items() if k != "kind"):
            raise ValueError("invalid framing detail")
    details = integrity["permutation_violation_details"]
    fields(details, ("counts", "sample", "unknown_reason_sample"))
    fields(details["counts"], ("size-changed", "rcdptr-set-changed", "unknown"))
    if any(type(v) is not int or v < 0 for v in details["counts"].values()):
        raise ValueError("invalid permutation count")
    for row in rows(details["sample"]):
        fields(row, ("observation", "source_thread_hint", "source_thread_hint_basis"))
        fields(row["observation"], ("kind", "size_preserved", "rcdptr_multiset_preserved", "recognized"))
        if (type(row["observation"]["kind"]) is not str
                or any(v is not None and type(v) is not bool for k,v in row["observation"].items() if k != "kind")
                or row["source_thread_hint"] is not None and type(row["source_thread_hint"]) is not int
                or type(row["source_thread_hint_basis"]) is not str):
            raise ValueError("invalid permutation detail")
    for values in (integrity["notes"], details["unknown_reason_sample"]):
        if any(type(value) is not str for value in rows(values)):
            raise ValueError("invalid integrity note")
    for key, reasons in (("x_reasons", {"not-locked-at-entry", "lock-lost-before-write", "lock-lost-before-publish"}),
                         ("p_reasons", {"size-changed", "rcdptr-set-changed"})):
        values = run_record[key]
        if not isinstance(values, dict) or set(values) - reasons or any(type(v) is not int or v < 0 for v in values.values()):
            raise ValueError("reason fields differ")
    return copy.deepcopy(run_record)


def introduces_mocc_marker(patch_text):
    target, in_hunk = None, False
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            target, in_hunk = None, False
        elif line.startswith("+++ b/"):
            target, in_hunk = line[6:], False
        elif line.startswith("@@ "):
            in_hunk = True
        elif in_hunk and target == SOURCE_REL and line.startswith("+") and "EVOLVE-BLOCK-BEGIN" in line:
            return True
    return False


def mocc_axis_modules(campaign_dir):
    modules = []
    for path in sorted(Path(campaign_dir).glob("axis_*.py")):
        module = importlib.import_module("orchestrator.campaign." + path.stem)
        if (getattr(module, "SOURCE_REL", None) == SOURCE_REL
                and hasattr(module, "MARKER_ID") and hasattr(module, "TEMPLATE_PATCH")):
            modules.append(module)
    return tuple(modules)
