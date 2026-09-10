# [T-2113] 生死確認 driver の逐語

repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2113-sort-oracle-ir-liveness/` に置いた
使い捨て driver の全文。実装面を repo へ入れないため `.md` へ逐語で貼る
(`docs/ai-provenance.md` の実装面は所在不問。probe-only は免除理由にならない)。

3 ファイルで合計 270 物理行。`DW-G01` の 100 行予算を超えている。理由は README §7 に記した。

- `liveness_driver.py` (132 行) — IR 型・admission・renderer・値域・evaluator・実 TU 実行
- `liveness_main.py` (138 行) — PC / M1 / M2 / M3 / M4 の本走
- `negative_control.py` — 負例対照

## liveness_driver.py

#!/usr/bin/env python3
"""[T-2113] sort SWO oracle を検証済み IR へ縮める方向の生死確認 (DW-G01)。repo 外・使い捨て。"""
import itertools, json, subprocess, sys, tempfile
from pathlib import Path

REPO = Path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness")
MASSTREE = Path("/work/1/SFC/tanab/ccbench-upstream-pr/build-baseline/_deps/masstree-src")
sys.path.insert(0, str(REPO))
from orchestrator.campaign import sort_swo_oracle as O          # noqa: E402
from orchestrator.campaign import s6_sort_sweep as S            # noqa: E402

MEMBER = {"storage": "storage_", "key": "key_", "pointer": "rcdptr_"}
DIRS = ("asc", "desc")
ARITY = {"const_false": 1, "single": 3, "lex2": 5, "lex3": 7}
SINK = {"render": 0, "evaluate": 0, "compile": 0}


def admit(raw):
    """JSON decode 後の値だけを受ける唯一の入口。評価前に fail-closed で拒否する。"""
    if type(raw) is not list and type(raw) is not tuple:
        raise ValueError("not-a-sequence")
    ir = tuple(raw)
    if not ir or type(ir[0]) is not str:
        raise ValueError("bad-opcode-type")
    if ir[0] not in ARITY:
        raise ValueError("unknown-opcode")
    if len(ir) != ARITY[ir[0]]:
        raise ValueError("bad-arity")
    seen = []
    for i in range(1, len(ir), 2):
        field, direction = ir[i], ir[i + 1]
        if type(field) is not str or type(direction) is not str:
            raise ValueError("bad-operand-type")
        if field not in MEMBER or direction not in DIRS:
            raise ValueError("bad-domain")
        if field in seen:
            raise ValueError("duplicate-field")
        seen.append(field)
    return ir


def one(member, direction):
    return (f"a.{member} < b.{member}" if direction == "asc"
            else f"b.{member} < a.{member}")


def mk(body_lines):
    body = "\n".join("         " + ln for ln in body_lines)
    return ("  sort(write_set_.begin(), write_set_.end(),\n"
            "       [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b)"
            " -> bool {\n" + body + "\n"
            "       });")


def render(ir):
    SINK["render"] += 1
    if ir[0] == "const_false":
        return ("  sort(write_set_.begin(), write_set_.end(),\n"
                "       [](const WriteElement<Tuple>&, const WriteElement<Tuple>&)"
                " -> bool {\n"
                "         return false;\n"
                "       });")
    pairs = [(MEMBER[ir[i]], ir[i + 1]) for i in range(1, len(ir), 2)]
    if ir[0] == "single":
        return mk([f"return {one(*pairs[0])};"])
    m1, d1 = pairs[0]
    pad = " " * (16 + 2 * len(m1))
    if ir[0] == "lex2":
        return mk([f"return a.{m1} != b.{m1} ? {one(m1, d1)}",
                   f"{pad}: {one(*pairs[1])};"])
    m2, d2 = pairs[1]
    return mk([f"return a.{m1} != b.{m1} ? {one(m1, d1)}",
               f"     : a.{m2} != b.{m2} ? {one(m2, d2)}",
               f"     : {one(*pairs[2])};"])


def domain():
    """3 field に対する相異なる field 辞書式比較の完全閉包 = 79 値。"""
    values = [("const_false",)]
    for depth, opcode in ((1, "single"), (2, "lex2"), (3, "lex3")):
        for fields in itertools.permutations(MEMBER, depth):
            for dirs in itertools.product(DIRS, repeat=depth):
                values.append((opcode,) + tuple(
                    x for pair in zip(fields, dirs) for x in pair))
    return values


def value(element, field):
    storage, key, kind, slot = element
    if field == "storage":
        return storage
    if field == "key":
        return key
    return 0 if kind == 0 else (1 + slot if kind == 1 else 5 + slot)


def evaluate(ir, lhs, rhs):
    SINK["evaluate"] += 1
    if ir[0] == "const_false":
        return False
    for i in range(1, len(ir), 2):
        a, b = value(lhs, ir[i]), value(rhs, ir[i])
        if a != b:
            return a < b if ir[i + 1] == "asc" else b < a
    return False


def python_matrix(ir, corpus):
    elements = O._CORPUS_TOPOLOGY[corpus]
    return bytes(1 if evaluate(ir, lhs, rhs) else 0
                 for lhs in elements for rhs in elements)


def real_matrices(statement, workdir, tag):
    """実 TU を compile し、実 broker で 2 corpus x 3 order の行列を取る。"""
    SINK["compile"] += 1
    source, executable = workdir / f"{tag}.cpp", workdir / f"{tag}.bin"
    source.write_text(O._translation_unit(statement), encoding="utf-8")
    command = O._compile_command(source, executable, compiler="g++",
                                 ccbench_dir=REPO / "external" / "ccbench",
                                 masstree_dir=MASSTREE)
    proc = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        return None, f"compile-rc={proc.returncode}:{proc.stderr[:200]}"
    out = {}
    for corpus in O._CORPORA:
        for order in O._ORDERS:
            matrix, finding = O._run_matrix(executable, corpus, order)
            if finding is not None or matrix is None:
                return None, f"run-finding={finding}"
            out[(corpus, order)] = matrix
    return out, None

## liveness_main.py

#!/usr/bin/env python3
"""[T-2113] 生死確認 driver の本走 (PC / M1 / M2 / M3 / M4)。repo 外・使い捨て。"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import liveness_driver as L  # noqa: E402

O = L.O
S = L.S

WIRE_CASES = [
    ('["single","key","asc"]', True, None),
    ('["const_false"]', True, None),
    ('["lex3","storage","asc","key","desc","pointer","asc"]', True, None),
    ('["call","key","asc"]', False, "unknown-opcode"),
    ('["single","key",true]', False, "bad-operand-type"),
    ('["single","key_);evil","asc"]', False, "bad-domain"),
    ('["single","key","sideways"]', False, "bad-domain"),
    ('["single","key"]', False, "bad-arity"),
    ('["single","key","asc","key","asc"]', False, "bad-arity"),
    ('["lex2","key","asc","key","desc"]', False, "duplicate-field"),
    ('"return a.key_ < b.key_;"', False, "not-a-sequence"),
    ('{"opcode":"single"}', False, "not-a-sequence"),
]


def authority_table():
    table = {
        "s_asc": ("single", "storage", "asc"),
        "s_desc": ("single", "storage", "desc"),
        "k_asc": ("single", "key", "asc"),
        "k_desc": ("single", "key", "desc"),
        "p_asc": ("single", "pointer", "asc"),
        "p_desc": ("single", "pointer", "desc"),
        "nosort": ("const_false",),
    }
    for second, letter in (("key", "k"), ("pointer", "p")):
        for d1, a1 in (("asc", "a"), ("desc", "d")):
            for d2, a2 in (("asc", "a"), ("desc", "d")):
                table[f"s{letter}_{a1}{a2}"] = ("lex2", "storage", d1, second, d2)
    return table


def main():
    result = {"driver": "t2113-liveness"}
    workdir = Path(tempfile.mkdtemp(prefix="t2113-"))
    result["workdir"] = str(workdir)

    control, error = L.real_matrices(O._TRUSTED_CONTROL_STATEMENT, workdir, "control")
    if control is None:
        result["status"] = "UNAVAILABLE"
        result["positive_control"] = error
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    result["positive_control"] = "ok"

    authority = authority_table()
    literals = {name: impl for name, _category, impl in S.CANDIDATES}
    m1, m1_bad = True, []
    if set(literals) != set(authority) or len(S.CANDIDATES) != 15:
        m1 = False
        m1_bad = ["authority-name-set-mismatch"]
    else:
        for name, ir in authority.items():
            rendered = L.render(L.admit(list(ir))).encode("utf-8")
            if rendered != literals[name].encode("utf-8"):
                m1 = False
                m1_bad.append(name)
    result["m1_emitter_byte_conformance"] = m1
    result["m1_mismatch"] = m1_bad

    m3, m3_bad = True, []
    for text, expect_ok, expect_reason in WIRE_CASES:
        before = dict(L.SINK)
        try:
            L.admit(json.loads(text))
            ok, reason = True, None
        except (ValueError, TypeError) as exc:
            ok, reason = False, str(exc)
        if ok != expect_ok or (not expect_ok and reason != expect_reason):
            m3 = False
            m3_bad.append({"case": text, "ok": ok, "reason": reason})
        if not expect_ok and dict(L.SINK) != before:
            m3 = False
            m3_bad.append({"case": text, "reached_sink": True})
    result["m3_wire_ingress_rejection"] = m3
    result["m3_failures"] = m3_bad

    values = L.domain()
    result["ir_domain_size"] = len(values)
    m2, m4, m2_bad, m4_bad = True, True, [], []
    for index, ir in enumerate(values):
        statement = L.render(L.admit(list(ir)))
        reason = O._validate_single_sort_statement(statement)
        if reason is not None:
            m4 = False
            m4_bad.append({"ir": ir, "reason": reason})
        matrices, error = L.real_matrices(statement, workdir, f"ir{index:03d}")
        if matrices is None:
            result["status"] = "FAIL"
            result["m2_error"] = {"ir": ir, "error": error}
            print(json.dumps(result, indent=2, sort_keys=True, default=str))
            return 3
        for corpus in O._CORPORA:
            expected = L.python_matrix(ir, corpus)
            for order in O._ORDERS:
                actual = matrices[(corpus, order)]
                if actual != expected:
                    cell = next(i for i in range(len(actual))
                                if actual[i] != expected[i])
                    m2 = False
                    m2_bad.append({
                        "ir": ir, "corpus": corpus, "order": order,
                        "lhs": cell // O._N, "rhs": cell % O._N,
                        "real": actual[cell], "python": expected[cell],
                    })
    result["m2_real_type_matrix_agreement"] = m2
    result["m2_mismatch"] = m2_bad[:5]
    result["m2_mismatch_count"] = len(m2_bad)
    result["m4_narrowing_direction"] = m4
    result["m4_failures"] = m4_bad[:5]

    result["corpus_sha256"] = O.CORPUS_SHA256
    result["tu_template_sha256"] = O.TU_TEMPLATE_SHA256
    result["guarantee_boundary"] = O.SORT_SWO_GUARANTEE_BOUNDARY
    result["dependency_manifest_verified"] = False
    result["ground_truth"] = "real-oracle-tu-and-broker"
    result["compile_count"] = L.SINK["compile"]
    result["status"] = "PASS" if (m1 and m2 and m3 and m4) else "FAIL"
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

## negative_control.py

#!/usr/bin/env python3
"""[T-2113] 負例対照: Python evaluator を意図的に壊すと M2 が赤になることを確かめる。

M2 の緑が恒真でないことの証拠。repo 外・使い捨て。実 TU 側は一切変えない。
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import liveness_driver as L  # noqa: E402

O = L.O
GOOD = L.value


def signed_storage(element, field):
    """storage_ を符号つき 32bit と誤解する。"""
    if field == "storage":
        raw = element[0]
        return raw - (1 << 32) if raw >= (1 << 31) else raw
    return GOOD(element, field)


def reversed_pointer(element, field):
    """arena の割当順を取り違え、aliases と separate の並びを逆にする。"""
    if field == "pointer":
        kind, slot = element[2], element[3]
        return 0 if kind == 0 else (7 + slot if kind == 1 else 1 + slot)
    return GOOD(element, field)


def nul_truncated_key(element, field):
    """key_ を C 文字列と誤解して最初の NUL で切る。"""
    if field == "key":
        raw = element[1]
        return raw.split(b"\0", 1)[0]
    return GOOD(element, field)


CASES = [
    ("signed-storage", signed_storage, ("single", "storage", "asc")),
    ("reversed-pointer-rank", reversed_pointer, ("single", "pointer", "asc")),
    ("nul-truncated-key", nul_truncated_key, ("single", "key", "asc")),
]


def main():
    workdir = Path(tempfile.mkdtemp(prefix="t2113-neg-"))
    report = []
    for name, mutation, ir in CASES:
        statement = L.render(L.admit(list(ir)))
        matrices, error = L.real_matrices(statement, workdir, name)
        if matrices is None:
            report.append({"mutation": name, "outcome": "DRIVER_ERROR", "error": error})
            continue
        L.value = GOOD
        clean_ok = all(matrices[(c, o)] == L.python_matrix(ir, c)
                       for c in O._CORPORA for o in O._ORDERS)
        L.value = mutation
        differing = [
            {"corpus": c, "cells": sum(
                1 for a, b in zip(matrices[(c, 0)], L.python_matrix(ir, c)) if a != b)}
            for c in O._CORPORA
        ]
        L.value = GOOD
        detected = any(entry["cells"] > 0 for entry in differing)
        report.append({
            "mutation": name, "ir": ir,
            "clean_evaluator_agrees": clean_ok,
            "mutated_evaluator_detected": detected,
            "differing_cells": differing,
            "outcome": "KILLED" if (clean_ok and detected) else "SURVIVED",
        })
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if all(r.get("outcome") == "KILLED" for r in report) else 1


if __name__ == "__main__":
    sys.exit(main())
