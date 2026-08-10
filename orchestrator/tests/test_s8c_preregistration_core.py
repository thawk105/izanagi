# -*- coding: utf-8 -*-
"""s8c preregistration parser / freeze / activation core の攻撃 matrix。

Git 履歴を使うテストはすべて tmp_path 内の使い捨て repository で行う。実 repository の
freeze namespace や履歴には触れない。
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import s8c_preregistration as M  # noqa: E402


FIELD_NAMES = (
    "累積ベンチ実時間の総上限と arm ごと・holdout ごとの上限",
    "env_tag (実測環境)",
    "対象別 between-run floor (H1 / H2)",
    "master_seed",
    "検定 4 点 (n / 検定単位 / 検定力 / 総予算)",
    "未既知性再確認の証跡 (a) 検索対象 dir 一覧 / (b) 検索式 / (c) 一致 0 件の出力 hash / (d) positive control の hit 数 / (e) 確認者",
    "swapped 対応表の固定日時と bytes hash",
    "実走前に確定する 6 cell manifest (trial id、arm、holdout、campaign id)",
    "実行責任者・開始時刻",
)


def _markdown(*, filled: bool = False, condition_word: str = "保証") -> bytes:
    value = '`{"v":1}`' if filled else "未記入"
    table = "\n".join(f"|{name}|{value}|" for name in FIELD_NAMES)
    conditions = []
    for number in range(1, 13):
        if number == 1:
            conditions.append(
                f"1. **条件一の先頭句**を{condition_word}する。\n"
                "   この継続行の否定や数値 48 も同じ条件本文である。"
            )
        else:
            conditions.append(f"{number}. 条件 {number} を機械検査する。")
    condition_text = "\n".join(conditions)
    return (
        "# fixture\n\n"
        "## 0. 表記\n補助規約。\n\n"
        "## 1. 効力\n本文 **alpha**。\n\n"
        "## 2. scope\n本文 beta。\n\n"
        "## 3. gate\n本文 gamma。\n\n"
        "## 4. 固有事項\n本文 delta。\n\n"
        "## 5. 数値欄\n\n|欄|値|\n|---|---|\n"
        f"{table}\n\n"
        "## 6. 前提条件\n\n"
        f"{condition_text}\n\n"
        "**現状は未充足。**\n\n"
        "### 発効ポリシー\n"
        "freeze と全述語の conjunction。approval 宣言物は置かない。\n\n"
        "## 7. 全件報告\n本文 epsilon。\n"
    ).encode("utf-8")


def _git(root: Path, *args: str, input_bytes: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    ).stdout.decode("utf-8").strip()


def _init_repo(tmp_path: Path, *, filled: bool = False) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    _write(root, M.SOURCE_PATH, _markdown(filled=filled))
    _write(root, M.EVIDENCE_CONTRACT_PATH, b'{"predicates":[]}')
    _write(root, "docs/decisions.md", b"## D327. Initial fixture ruling\n")
    _write(root, "docs/worklog.md", b"fixture\n")
    _commit(root, "base")
    return root


def _write(root: Path, relative: str, raw: bytes) -> None:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)


def _commit(root: Path, subject: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject)
    return _git(root, "rev-parse", "HEAD")


def _record_raw(
    root: Path,
    generation: int,
    *,
    supersedes: str | None,
    ruling: str | None,
    reason: str = "fixture revision",
) -> bytes:
    contract = M.parse_preregistration_markdown((root / M.SOURCE_PATH).read_bytes())
    evidence_sha = M.evidence_contract_sha256(
        (root / M.EVIDENCE_CONTRACT_PATH).read_bytes()
    )
    return M._canonical_bytes(
        M._record_document(
            generation,
            supersedes,
            contract,
            evidence_sha,
            reason,
            ruling,
        )
    )


def _install_g1(root: Path) -> tuple[str, bytes]:
    raw = _record_raw(root, 1, supersedes=None, ruling=None, reason="initial contract")
    _write(root, M.generation_path(1), raw)
    return _commit(root, "install g1"), raw


def _install_revision(
    root: Path,
    previous_raw: bytes,
    *,
    word: str,
    ruling: str = "D999",
    put_ruling_in_ledger: bool = True,
) -> tuple[str, bytes]:
    source = (root / M.SOURCE_PATH).read_bytes().replace(b"fixture revision sentinel", b"unused")
    text = source.decode("utf-8").replace("本文 epsilon。", f"本文 epsilon。{word}")
    _write(root, M.SOURCE_PATH, text.encode("utf-8"))
    if put_ruling_in_ledger:
        decisions = (root / "docs/decisions.md").read_text(encoding="utf-8")
        (root / "docs/decisions.md").write_text(
            decisions + f"\n## {ruling}. Permits this revision\n", encoding="utf-8"
        )
    raw = _record_raw(
        root,
        2,
        supersedes=hashlib.sha256(previous_raw).hexdigest(),
        ruling=ruling,
    )
    _write(root, M.generation_path(2), raw)
    return _commit(root, f"revision {word}"), raw


class _Registry:
    def __init__(self, statuses) -> None:
        self.statuses = statuses

    def evaluate_all(self, commit: str, *, repo_root: Path):
        del commit, repo_root
        return tuple(
            M.PredicateResult(
                identifier,
                self.statuses.get(identifier, M.PredicateStatus.SATISFIED)
                if isinstance(self.statuses, dict)
                else self.statuses,
                "fixture",
                (),
            )
            for identifier in M.PREDICATE_IDS
        )


def _assert_reason(reason: str, function, *args, **kwargs) -> None:
    with pytest.raises(M.PreregistrationError) as caught:
        function(*args, **kwargs)
    assert caught.value.reason == reason


def _legacy_unframed_blob(root: Path, commit: str, path: str) -> bytes:
    """Path guard 導入前の line-based batch request を fixture 内で再現する。"""
    resolved = M.resolve_commit(root, commit)
    result = M._git_text(
        root,
        ["cat-file", "--batch-check"],
        stdin=f"{resolved}:{path}\n".encode(),
    )
    tokens = result.split()
    assert len(tokens) >= 3
    assert M._OBJECT_ID_RE.fullmatch(tokens[0])
    assert tokens[1] == "blob"
    assert tokens[2].isdigit()
    return M._git(root, ["cat-file", "blob", tokens[0]])


def test_current_markdown_extracts_nine_fields_and_conditions_1_to_12() -> None:
    contract = M.parse_preregistration_markdown(
        (_ROOT / M.SOURCE_PATH).read_bytes()
    )
    assert len(contract.section5_field_names) == 9
    assert contract.section5_field_names == frozenset(FIELD_NAMES)
    assert [number for number, _ in contract.section6_conditions] == list(range(1, 13))
    assert "100k / 4" in dict(contract.section6_conditions)[1]


def test_heading_rewording_changes_hash_but_missing_duplicate_and_level_change_fail() -> None:
    raw = _markdown()
    original = M.parse_preregistration_markdown(raw)
    renamed = raw.replace("## 4. 固有事項".encode(), "## 4. 参考資料（非規範）".encode())
    assert M.parse_preregistration_markdown(renamed).normative_body_sha256 != original.normative_body_sha256

    missing = raw.replace(b"## 4. ", b"## x. ", 1)
    _assert_reason("section-missing", M.parse_preregistration_markdown, missing)
    duplicate = raw.replace(b"## 5. ", b"## 4. ", 1)
    _assert_reason("section-duplicate", M.parse_preregistration_markdown, duplicate)
    wrong_level = raw.replace(b"## 6. ", b"### 6. ", 1)
    _assert_reason("heading-level", M.parse_preregistration_markdown, wrong_level)


def test_table_lexer_handles_escaped_pipe_and_code_span() -> None:
    assert M.split_markdown_table_row(r"| left \| right | `a|b` |") == [
        "left | right",
        "`a|b`",
    ]
    raw = _markdown().replace(
        f"|{FIELD_NAMES[0]}|未記入|".encode(),
        b"|escaped \\| field|`{\"value\":\"a|b\"}`|",
    )
    contract = M.parse_preregistration_markdown(raw)
    assert "escaped | field" in contract.section5_field_names


def test_layout_only_whitespace_line_wrap_and_bold_preserve_hashes() -> None:
    original = M.parse_preregistration_markdown(_markdown())
    changed = _markdown().replace(
        "1. **条件一の先頭句**を保証する。\n   この継続行".encode(),
        "1. 条件一の先頭句を保証する。   この継続行".encode(),
    ).replace("本文 **alpha**。".encode(), "本文     alpha。".encode())
    layout = M.parse_preregistration_markdown(changed)
    assert layout.section6_conditions_sha256 == original.section6_conditions_sha256
    assert layout.normative_body_sha256 == original.normative_body_sha256
    assert layout.section5_field_names_sha256 == original.section5_field_names_sha256


def test_paragraph_list_and_fenced_code_node_kind_changes_hash() -> None:
    raw = _markdown()
    original = M.parse_preregistration_markdown(raw)
    as_list = raw.replace("本文 **alpha**。".encode(), "- 本文 **alpha**。".encode())
    as_code = raw.replace(
        "本文 gamma。".encode(),
        "```text\n本文 gamma。\n```".encode(),
    )
    assert M.parse_preregistration_markdown(as_list).normative_body_sha256 != original.normative_body_sha256
    assert M.parse_preregistration_markdown(as_code).normative_body_sha256 != original.normative_body_sha256


def test_fence_scanner_uses_commonmark_marker_width_info_and_indent() -> None:
    raw = _markdown()
    original = M.parse_preregistration_markdown(raw)
    as_indented_tilde_code = raw.replace(
        "本文 gamma。".encode(),
        "   ~~~~ text extra\n   本文 gamma。\n  ~~~~~".encode(),
    )
    changed = M.parse_preregistration_markdown(as_indented_tilde_code)
    assert changed.normative_body_sha256 != original.normative_body_sha256

    with_non_closing_runs = raw.replace(
        "本文 gamma。".encode(),
        "````text\n~~~\n```\n```` trailing\n本文 gamma。\n`````".encode(),
    )
    assert (
        M.parse_preregistration_markdown(with_non_closing_runs).normative_body_sha256
        != original.normative_body_sha256
    )

    for invalid_close in (
        "````text\n本文 gamma。\n```",  # opening fence より短い
        "````text\n本文 gamma。\n~~~~",  # marker が異なる
        "````text\n本文 gamma。\n    ````",  # closing fence の indent が 4 spaces
        "````text\n本文 gamma。\n```` trailing",  # closing fence に info は置けない
    ):
        rejected = raw.replace("本文 gamma。".encode(), invalid_close.encode())
        _assert_reason("unclosed-fence", M.parse_preregistration_markdown, rejected)


def test_list_item_fence_exact_fixture_is_rejected_fail_closed() -> None:
    raw = _markdown().replace(
        "本文 delta。".encode(),
        (
            "- ```\n"
            "  停止: 固定世代数で停止する。性能目標による早期停止を置かない\n"
            "  (Best-of-N と選択的報告になるため)。role 応答の schema 違反は再試行しない。\n"
            "    ```"
        ).encode(),
    )
    _assert_reason("container-fence", M.parse_preregistration_markdown, raw)


def test_section6_list_container_fence_is_rejected_fail_closed() -> None:
    raw = _markdown().replace(
        "   この継続行の否定や数値 48 も同じ条件本文である。".encode(),
        (
            "   この継続行の否定や数値 48 も同じ条件本文である。\n"
            "   ```text\n"
            "   条件一を code block へ降格する。\n"
            "   ```"
        ).encode(),
    )
    _assert_reason("container-fence", M.parse_preregistration_markdown, raw)


def test_normalization_v2_conformance_corpus() -> None:
    """parser の意味変更は version 据え置きのまま通さず、hash 差分として露出させる。"""

    assert M.NORMALIZATION_VERSION == "s8c-prereg-markdown/v2"
    raw = _markdown()
    accepted = {
        "base": raw,
        "backtick-no-info-indent-0": raw.replace(
            "本文 gamma。".encode(), b"```\ncode\n```"
        ),
        "backtick-info-indent-1": raw.replace(
            "本文 gamma。".encode(), b" ```text\n code\n ```"
        ),
        "tilde-no-info-indent-2": raw.replace(
            "本文 gamma。".encode(), b"  ~~~\n  code\n  ~~~"
        ),
        "tilde-info-indent-3": raw.replace(
            "本文 gamma。".encode(), b"   ~~~~ text extra\n   code\n   ~~~~"
        ),
        "inline-code-span": raw.replace(
            "本文 beta。".encode(), "本文 `beta`。".encode()
        ),
        "heading-reword": raw.replace(
            "## 4. 固有事項".encode(), "## 4. 参考資料（非規範）".encode()
        ),
        "layout-only": raw.replace(
            "1. **条件一の先頭句**を保証する。\n   この継続行".encode(),
            "1. 条件一の先頭句を保証する。   この継続行".encode(),
        ).replace("本文 **alpha**。".encode(), "本文     alpha。".encode()),
    }
    field_hash = "4d082de6c6a19691dd8bad27127e9ebb03fdacc500aab555310c7883b7ba2635"
    condition_hash = "c2427eb7c76956a94e495ab32bb7d2c41b3dd14fb9b7b025e95370dbe7caf967"
    normative_hashes = {
        "base": "f691f266877b5b4eb9f3339e4942b41176a231851c42d840d738eafb82917d5a",
        "backtick-no-info-indent-0": "27cc5c41b070b3134f33aa79ad614f14ac5f8287dedb65b6bc64357a6a2ab567",
        "backtick-info-indent-1": "f4d3afc990aeb7d8cea7fffceca3dedd51cac2e6573e7fa4601aede2b1dbb941",
        "tilde-no-info-indent-2": "27cc5c41b070b3134f33aa79ad614f14ac5f8287dedb65b6bc64357a6a2ab567",
        "tilde-info-indent-3": "803271bb565be49962a1acfa2cc2c964bcae174215718fb15b1fee7c5bf8a8d5",
        "inline-code-span": "f691f266877b5b4eb9f3339e4942b41176a231851c42d840d738eafb82917d5a",
        "heading-reword": "9b62cb215a8eb2968df2fe8a785a7b6ef59a00356ece78590c64142e842b3668",
        "layout-only": "f691f266877b5b4eb9f3339e4942b41176a231851c42d840d738eafb82917d5a",
    }
    for name, fixture in accepted.items():
        contract = M.parse_preregistration_markdown(fixture)
        assert (
            contract.section5_field_names_sha256,
            contract.section6_conditions_sha256,
            contract.normative_body_sha256,
        ) == (field_hash, condition_hash, normative_hashes[name]), name

    rejected = {
        "list-container-fence": raw.replace(
            "本文 delta。".encode(), b"- ```\n  hidden\n    ```"
        ),
        "unclosed-fence": raw.replace(
            "本文 gamma。".encode(), b"```text\nunclosed"
        ),
    }
    reasons = {
        "list-container-fence": "container-fence",
        "unclosed-fence": "unclosed-fence",
    }
    for name, fixture in rejected.items():
        with pytest.raises(M.PreregistrationError) as caught:
            M.parse_preregistration_markdown(fixture)
        assert caught.value.reason == reasons[name], name


def test_field_set_is_order_independent_but_names_and_normative_policy_are_protected() -> None:
    raw = _markdown()
    original = M.parse_preregistration_markdown(raw)
    first = f"|{FIELD_NAMES[0]}|未記入|".encode()
    second = f"|{FIELD_NAMES[1]}|未記入|".encode()
    reordered = raw.replace(first + b"\n" + second, second + b"\n" + first)
    renamed = raw.replace(FIELD_NAMES[0].encode(), b"renamed budget field", 1)
    policy = raw.replace(b"conjunction", b"disjunction", 1)
    section0 = raw.replace("補助規約。".encode(), "補助規約を変更。".encode(), 1)
    assert M.parse_preregistration_markdown(reordered).section5_field_names_sha256 == original.section5_field_names_sha256
    assert M.parse_preregistration_markdown(renamed).section5_field_names_sha256 != original.section5_field_names_sha256
    assert M.parse_preregistration_markdown(policy).normative_body_sha256 != original.normative_body_sha256
    assert M.parse_preregistration_markdown(section0).normative_body_sha256 == original.normative_body_sha256


def test_evidence_contract_hash_is_semantic_canonical_json() -> None:
    compact = b'{"a":1,"b":[2,3]}'
    formatted = b'{\n  "b": [2, 3],\n  "a": 1\n}'
    assert M.evidence_contract_sha256(compact) == M.evidence_contract_sha256(formatted)


@pytest.mark.parametrize(
    "old,new",
    [
        ("保証", "確認"),
        ("数値 48", "数値 47"),
        ("否定や数値", "数値"),
        ("条件 2", "条件 二"),
        ("機械検査する。", "機械検査する！"),
    ],
)
def test_word_number_negation_and_punctuation_change_condition_hash(old: str, new: str) -> None:
    raw = _markdown()
    changed = raw.replace(old.encode(), new.encode(), 1)
    assert (
        M.parse_preregistration_markdown(changed).section6_conditions_sha256
        != M.parse_preregistration_markdown(raw).section6_conditions_sha256
    )


def test_condition_order_and_continuation_are_part_of_hash() -> None:
    raw = _markdown()
    original = M.parse_preregistration_markdown(raw)
    swapped = raw.replace(b"2. \xe6\x9d\xa1\xe4\xbb\xb6 2", b"2. \xe6\x9d\xa1\xe4\xbb\xb6 3", 1).replace(
        b"3. \xe6\x9d\xa1\xe4\xbb\xb6 3", b"3. \xe6\x9d\xa1\xe4\xbb\xb6 2", 1
    )
    continuation = raw.replace("この継続行の否定".encode(), "この継続行の肯定".encode())
    assert M.parse_preregistration_markdown(swapped).section6_conditions_sha256 != original.section6_conditions_sha256
    assert M.parse_preregistration_markdown(continuation).section6_conditions_sha256 != original.section6_conditions_sha256
    assert "継続行" in dict(original.section6_conditions)[1]


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda raw: raw.replace(b"7. \xe6\x9d\xa1\xe4\xbb\xb6 7", b"8. \xe6\x9d\xa1\xe4\xbb\xb6 7"), "condition-numbering"),
        (lambda raw: raw.replace(b"12. \xe6\x9d\xa1\xe4\xbb\xb6 12", b"13. \xe6\x9d\xa1\xe4\xbb\xb6 12"), "condition-numbering"),
        (lambda raw: raw.replace(b"12. \xe6\x9d\xa1\xe4\xbb\xb6 12", b"    12. \xe6\x9d\xa1\xe4\xbb\xb6 12"), "condition-nested-replacement"),
        (lambda raw: raw + b"\n```python\nunclosed\n", "unclosed-fence"),
        (lambda raw: raw.replace(b"\xe6\x9c\xac\xe6\x96\x87 beta\xe3\x80\x82", b"[ref]: target"), "reference-link-definition"),
        (lambda raw: raw.replace(b"\xe6\x9c\xac\xe6\x96\x87 beta\xe3\x80\x82", b"<div>hidden</div>"), "raw-html"),
    ],
)
def test_parser_rejects_numbering_fence_reference_definition_and_html(mutation, reason) -> None:
    _assert_reason(reason, M.parse_preregistration_markdown, mutation(_markdown()))


def test_section5_placeholder_and_arbitrary_nonempty_are_not_filled() -> None:
    raw = _markdown().replace(b"|master_seed|\xe6\x9c\xaa\xe8\xa8\x98\xe5\x85\xa5|", b"|master_seed|arbitrary text|")
    raw = raw.replace(
        f"|{FIELD_NAMES[0]}|未記入|".encode(),
        f"|{FIELD_NAMES[0]}|（未記入）|".encode(),
    )
    findings = {item.name: item for item in M.parse_preregistration_markdown(raw).section5_findings}
    assert findings[FIELD_NAMES[0]].status is M.FieldStatus.UNFILLED
    assert findings["master_seed"].status is M.FieldStatus.INVALID
    assert all(item.status is not M.FieldStatus.FILLED for item in findings.values())


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("null", "json-null"),
        ('""', "json-empty-string"),
        ('"未記入"', "json-placeholder-string"),
        ('"（未記入）"', "json-placeholder-string"),
        ("[]", "json-empty-container"),
        ("{}", "json-empty-container"),
    ],
)
def test_section5_json_semantic_empty_values_are_unfilled(value: str, reason: str) -> None:
    raw = _markdown().replace(
        b"|master_seed|\xe6\x9c\xaa\xe8\xa8\x98\xe5\x85\xa5|",
        f"|master_seed|`{value}`|".encode(),
    )
    finding = next(
        item
        for item in M.parse_preregistration_markdown(raw).section5_findings
        if item.name == "master_seed"
    )
    assert finding.status is M.FieldStatus.UNFILLED
    assert finding.reason_code == reason


def test_recorded_revision_is_accepted_and_ruling_is_checked_at_revision_commit(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _, g1 = _install_g1(root)
    head, _ = _install_revision(root, g1, word="changed")
    validation = M.validate_condition_freeze_at(root, head)
    assert validation.generation_number == 2


def test_operational_artifacts_do_not_enter_closed_freeze_namespace(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _install_g1(root)
    _write(root, "output/s8c-preregistration/trial-manifest.v1.json", b"{}")
    head = _commit(root, "operational artifact outside freeze ledger")
    assert M.validate_condition_freeze_at(root, head).generation_number == 1

    _write(root, f"{M.FREEZE_DIR}/unknown.json", b"{}")
    rejected = _commit(root, "unknown freeze ledger artifact")
    _assert_reason("freeze-namespace-unknown", M.validate_condition_freeze_at, root, rejected)


def test_unrecorded_change_is_rejected_even_after_revert(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _, _ = _install_g1(root)
    original = (root / M.SOURCE_PATH).read_bytes()
    _write(root, M.SOURCE_PATH, original.replace(b"epsilon", b"epsilon changed"))
    _commit(root, "unrecorded mutation")
    _write(root, M.SOURCE_PATH, original)
    head = _commit(root, "revert mutation")
    _assert_reason("record-protected-mismatch", M.validate_condition_freeze_at, root, head)


def test_generation_gap_bad_supersedes_unknown_key_and_noncanonical_are_rejected(tmp_path: Path) -> None:
    gap = _init_repo(tmp_path / "gap")
    _write(gap, M.generation_path(2), _record_raw(gap, 2, supersedes="0" * 64, ruling="D2"))
    gap_head = _commit(gap, "gap")
    _assert_reason("generation-gap", M.validate_condition_freeze_at, gap, gap_head)

    bad_chain = _init_repo(tmp_path / "bad-chain")
    _, g1 = _install_g1(bad_chain)
    source = (bad_chain / M.SOURCE_PATH).read_bytes().replace(b"epsilon", b"epsilon changed")
    _write(bad_chain, M.SOURCE_PATH, source)
    (bad_chain / "docs/decisions.md").write_text("## D2. Fixture\n", encoding="utf-8")
    _write(bad_chain, M.generation_path(2), _record_raw(bad_chain, 2, supersedes="0" * 64, ruling="D2"))
    bad_head = _commit(bad_chain, "bad supersedes")
    _assert_reason("generation-supersedes", M.validate_condition_freeze_at, bad_chain, bad_head)

    for name, transform, reason in (
        ("unknown", lambda doc: {**doc, "self_sha256": "0" * 64}, "record-schema-keys"),
        ("noncanonical", lambda doc: doc, "record-not-canonical"),
    ):
        root = _init_repo(tmp_path / name)
        canonical = _record_raw(root, 1, supersedes=None, ruling=None)
        document = json.loads(canonical)
        document = transform(document)
        raw = (
            M._canonical_bytes(document)
            if name == "unknown"
            else json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
        )
        _write(root, M.generation_path(1), raw)
        head = _commit(root, name)
        _assert_reason(reason, M.validate_condition_freeze_at, root, head)


def test_generation_mutation_and_delete_readd_are_rejected(tmp_path: Path) -> None:
    mutated = _init_repo(tmp_path / "mutated")
    _, g1 = _install_g1(mutated)
    document = json.loads(g1)
    document["revision_reason"] = "mutated in place"
    _write(mutated, M.generation_path(1), M._canonical_bytes(document))
    mutated_head = _commit(mutated, "mutate g1")
    _assert_reason("generation-mutated", M.validate_condition_freeze_at, mutated, mutated_head)

    deleted = _init_repo(tmp_path / "deleted")
    _, original = _install_g1(deleted)
    (deleted / M.generation_path(1)).unlink()
    _commit(deleted, "delete g1")
    _write(deleted, M.generation_path(1), original)
    readded = _commit(deleted, "readd g1")
    _assert_reason("generation-deleted", M.validate_condition_freeze_at, deleted, readded)


def test_generation_added_without_protected_change_is_spurious(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _, g1 = _install_g1(root)
    (root / "docs/decisions.md").write_text("## D2. Spurious revision\n", encoding="utf-8")
    g2 = _record_raw(
        root,
        2,
        supersedes=hashlib.sha256(g1).hexdigest(),
        ruling="D2",
    )
    _write(root, M.generation_path(2), g2)
    head = _commit(root, "spurious g2")
    _assert_reason("spurious-revision", M.validate_condition_freeze_at, root, head)


def test_valid_successor_merge_is_accepted(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    g1_head, g1 = _install_g1(root)
    _git(root, "checkout", "-q", "-b", "revision")
    _install_revision(root, g1, word="branch revision")
    _git(root, "checkout", "-q", "main")
    assert _git(root, "rev-parse", "HEAD") == g1_head
    _write(root, "README.md", b"unrelated\n")
    _commit(root, "main unrelated")
    _git(root, "merge", "-q", "--no-ff", "revision", "-m", "valid merge")
    validation = M.validate_condition_freeze_at(root, "HEAD")
    assert validation.generation_number == 2


def test_successor_merge_rejects_merge_commit_with_different_state(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    g1_head, g1 = _install_g1(root)
    _git(root, "checkout", "-q", "-b", "revision")
    _, g2 = _install_revision(root, g1, word="branch revision")

    _git(root, "checkout", "-q", "main")
    assert _git(root, "rev-parse", "HEAD") == g1_head
    _write(root, "README.md", b"unrelated\n")
    _commit(root, "main unrelated")
    _git(root, "merge", "-q", "--no-ff", "--no-commit", "revision")

    source = (root / M.SOURCE_PATH).read_bytes().replace(
        b"branch revision", b"merge revision"
    )
    _write(root, M.SOURCE_PATH, source)
    decisions = (root / "docs/decisions.md").read_text(encoding="utf-8")
    (root / "docs/decisions.md").write_text(
        decisions + "\n## D3. Permits merge revision\n", encoding="utf-8"
    )
    g3 = _record_raw(
        root,
        3,
        supersedes=hashlib.sha256(g2).hexdigest(),
        ruling="D3",
        reason="merge revision",
    )
    _write(root, M.generation_path(3), g3)
    merge_head = _commit(root, "merge with distinct successor state")

    _assert_reason(
        "merge-divergent-revision",
        M.validate_condition_freeze_at,
        root,
        merge_head,
    )


def test_mutually_different_revisions_merge_fails_closed(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    g1_head, g1 = _install_g1(root)
    _git(root, "checkout", "-q", "-b", "left")
    _install_revision(root, g1, word="left", ruling="D1")
    left_doc = (root / M.SOURCE_PATH).read_bytes()
    left_g2 = (root / M.generation_path(2)).read_bytes()
    _git(root, "checkout", "-q", "-B", "main", g1_head)
    _install_revision(root, g1, word="right", ruling="D2")
    merge = subprocess.run(
        ["git", "merge", "--no-ff", "left", "-m", "divergent merge"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    assert merge.returncode != 0
    _write(root, M.SOURCE_PATH, left_doc)
    _write(root, M.generation_path(2), left_g2)
    _commit(root, "resolve divergent merge")
    with pytest.raises(M.PreregistrationError) as caught:
        M.validate_condition_freeze_at(root, "HEAD")
    assert caught.value.reason in {"generation-mutated", "generation-fork", "merge-divergent-revision"}


def test_merge_transition_alone_rejects_mutually_divergent_revisions() -> None:
    """m14: generation mutation 等の先行 guard を通さず merge 規則だけを撃つ。"""
    left = M._HistoryState("1" * 64, 2, "a" * 64, ("g1", "left-g2"))
    right = M._HistoryState("2" * 64, 2, "b" * 64, ("g1", "right-g2"))
    with pytest.raises(M.PreregistrationError) as caught:
        M._assert_history_transition("merge-fixture", left, (left, right))
    assert caught.value.reason == "merge-divergent-revision"


def test_same_revision_introduced_on_two_forks_is_rejected(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    g1_head, g1 = _install_g1(root)
    _git(root, "checkout", "-q", "-b", "one")
    _install_revision(root, g1, word="same", ruling="D3")
    one_head = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "-q", "-B", "two", g1_head)
    _write(root, "two-marker.txt", b"make the second introduction commit distinct\n")
    _commit(root, "second branch marker")
    _install_revision(root, g1, word="same", ruling="D3")
    _git(root, "merge", "-q", "--no-ff", "one", "-m", "same bytes fork")
    assert _git(root, "rev-parse", "one") == one_head
    _assert_reason("generation-fork", M.validate_condition_freeze_at, root, "HEAD")


def _effective_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, M.ActivationReport, M.EffectivePreregistration]:
    root = _init_repo(tmp_path, filled=True)
    head, _raw = _install_g1(root)
    report = M._activation_report_at_for_test(
        root,
        head,
        registry=_Registry(M.PredicateStatus.SATISFIED),
    )
    assert report.effective is True
    capability = M._construct_effective(report)
    monkeypatch.setattr(M, "activation_report_at", lambda repo_root, commit: report)
    return root, report, capability


def test_require_effective_preregistration_accepts_exact_recomputed_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, report, capability = _effective_fixture(tmp_path, monkeypatch)
    assert M.require_effective_preregistration(
        capability,
        repo_root=root,
        commit=report.commit,
    ) is report


@pytest.mark.parametrize("capability", [None, object()], ids=["none", "wrong-type"])
def test_require_effective_preregistration_rejects_missing_or_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capability: object,
) -> None:
    root, report, _valid = _effective_fixture(tmp_path, monkeypatch)
    _assert_reason(
        "effective-capability-type",
        M.require_effective_preregistration,
        capability,
        repo_root=root,
        commit=report.commit,
    )


def test_require_effective_preregistration_rejects_different_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _report, capability = _effective_fixture(tmp_path, monkeypatch)
    _assert_reason(
        "effective-capability-commit",
        M.require_effective_preregistration,
        capability,
        repo_root=root,
        commit="0" * 40,
    )


def test_require_effective_preregistration_rejects_tampered_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, report, capability = _effective_fixture(tmp_path, monkeypatch)
    object.__setattr__(capability, "_report_digest_sha256", "0" * 64)
    _assert_reason(
        "effective-capability-digest",
        M.require_effective_preregistration,
        capability,
        repo_root=root,
        commit=report.commit,
    )


def test_revision_requires_ruling_reference_and_existing_ledger_entry(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "missing")
    _, g1 = _install_g1(root)
    _write(root, M.SOURCE_PATH, (root / M.SOURCE_PATH).read_bytes().replace(b"epsilon", b"changed"))
    raw = _record_raw(
        root,
        2,
        supersedes=hashlib.sha256(g1).hexdigest(),
        ruling=None,
    )
    _write(root, M.generation_path(2), raw)
    head = _commit(root, "missing ruling")
    _assert_reason("record-ruling-reference", M.validate_condition_freeze_at, root, head)

    absent = _init_repo(tmp_path / "absent")
    _, absent_g1 = _install_g1(absent)
    absent_head, _ = _install_revision(
        absent,
        absent_g1,
        word="changed",
        ruling="D404",
        put_ruling_in_ledger=False,
    )
    _assert_reason("ruling-not-found", M.validate_condition_freeze_at, absent, absent_head)


def test_revision_ruling_must_be_structured_decisions_heading(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _, g1 = _install_g1(root)
    source = (root / M.SOURCE_PATH).read_text(encoding="utf-8").replace(
        "本文 epsilon。", "本文 epsilon。changed"
    )
    _write(root, M.SOURCE_PATH, source.encode())
    _write(root, "docs/archive/decoy.md", b"## D404. Archive is not authority\n")
    decisions = (root / "docs/decisions.md").read_text(encoding="utf-8")
    (root / "docs/decisions.md").write_text(
        decisions
        + "D404 appears only as free text\n"
        + "```markdown\n## D404. Fenced decoy\n```\n"
        + "<!--\n## D404. 実在しない裁定\n-->\n",
        encoding="utf-8",
    )
    _write(
        root,
        M.generation_path(2),
        _record_raw(
            root,
            2,
            supersedes=hashlib.sha256(g1).hexdigest(),
            ruling="D404",
        ),
    )
    head = _commit(root, "decoy ruling reference")
    _assert_reason("ruling-not-found", M.validate_condition_freeze_at, root, head)


def test_record_schema_has_no_self_or_commit_hash_fields(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    raw = _record_raw(root, 1, supersedes=None, ruling=None)
    keys = set(json.loads(raw))
    assert keys == M._FREEZE_KEYS
    assert not keys & {
        "self_sha256",
        "record_sha256",
        "introduction_commit",
        "activation_commit",
    }


@pytest.mark.parametrize(
    "status",
    [
        M.PredicateStatus.UNSATISFIED,
        M.PredicateStatus.EVIDENCE_UNDEFINED,
        M.PredicateStatus.ERROR,
        M.PredicateStatus.NOT_EVALUATED,
    ],
)
def test_every_non_satisfied_status_keeps_effective_false(tmp_path: Path, status) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    report = M._activation_report_at_for_test(root, head, registry=_Registry(status))
    assert report.condition_freeze_valid
    assert not report.effective


@pytest.mark.parametrize(
    "non_satisfied",
    [
        M.PredicateStatus.UNSATISFIED,
        M.PredicateStatus.EVIDENCE_UNDEFINED,
        M.PredicateStatus.ERROR,
        M.PredicateStatus.NOT_EVALUATED,
    ],
)
@pytest.mark.parametrize("position", range(12))
def test_effective_requires_all_twelve(tmp_path: Path, non_satisfied, position: int) -> None:
    """m01: 11 SATISFIED + 1 false を全 12 位置で拒否する。"""
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    statuses = {M.PREDICATE_IDS[position]: non_satisfied}
    report = M._activation_report_at_for_test(root, head, registry=_Registry(statuses))
    assert report.condition_freeze_valid
    assert report.effective is False


def test_missing_evaluator_module_yields_twelve_evidence_undefined(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    head, _ = _install_g1(root)
    report = M.activation_report_at(root, head)
    assert len(report.predicates) == 12
    assert {item.id for item in report.predicates} == set(M.PREDICATE_IDS)
    assert {item.status for item in report.predicates} == {M.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {"core-module-absent-at-commit"}
    assert report.core_module_blob_sha256 is None
    assert report.evaluator_module_blob_sha256 is None


def test_activation_report_records_both_module_blob_hashes_at_commit(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    core_bytes = Path(M.__file__).read_bytes()
    from campaign import s8c_preregistration_evidence as evaluator_module

    evaluator = Path(evaluator_module.__file__).read_bytes()
    _write(root, M.CORE_MODULE_PATH, core_bytes)
    _write(root, M.EVALUATOR_MODULE_PATH, evaluator)
    _commit(root, "add evaluator fixture")
    head, _ = _install_g1(root)
    report = M.activation_report_at(root, head)
    assert report.core_module_blob_sha256 == hashlib.sha256(core_bytes).hexdigest()
    assert report.evaluator_module_blob_sha256 == hashlib.sha256(evaluator).hexdigest()


def test_private_conjunction_helper_reads_commit_blob_not_dirty_worktree(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    _write(root, M.SOURCE_PATH, _markdown(filled=False, condition_word="dirty"))
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    assert report.effective
    assert all(item.status is M.FieldStatus.FILLED for item in report.section5_findings)


def test_production_entrypoints_do_not_accept_registry_injection() -> None:
    assert "registry" not in inspect.signature(M.activation_report_at).parameters
    assert "registry" not in inspect.signature(M.effective_at).parameters


def test_cli_has_only_check_and_prepare_revision_commands() -> None:
    parser = M._build_parser()
    subparser_action = next(
        action for action in parser._actions if isinstance(action, __import__("argparse")._SubParsersAction)
    )
    assert set(subparser_action.choices) == {"check", "prepare-revision"}
    assert not {"approve", "activate", "revoke"} & set(subparser_action.choices)


def test_effective_preregistration_cannot_be_constructed_or_dataclass_replaced(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    with pytest.raises(TypeError):
        M.EffectivePreregistration(report, "0" * 64)
    effective = M._construct_effective(report)
    assert dataclasses.is_dataclass(effective)
    assert effective.commit == head
    assert effective.report_digest_sha256 == M._activation_report_digest(report)
    assert "Python の型は信頼境界" in (M.EffectivePreregistration.__doc__ or "")
    assert isinstance(report.predicates, tuple)
    assert all(isinstance(item.evidence, tuple) for item in report.predicates)
    with pytest.raises(TypeError):
        dataclasses.replace(effective)
    with pytest.raises(dataclasses.FrozenInstanceError):
        effective._report = report


def test_prepare_revision_is_exclusive_create(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    destination = M.prepare_revision(
        root,
        revision_reason="initial generated contract",
    )
    assert destination == root / M.generation_path(1)
    raw = destination.read_bytes()
    assert M._canonical_bytes(json.loads(raw)) == raw
    with pytest.raises(M.PreregistrationError) as caught:
        M.prepare_revision(
            root,
            revision_reason="initial generated contract",
        )
    assert caught.value.reason == "revision-exists"


def test_read_blob_at_accepts_normal_path(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, "nested/evidence.txt", b"normal-path\n")
    head = _commit(root, "normal path")

    assert M.read_blob_at(root, head, "nested/evidence.txt") == b"normal-path\n"
    assert M.read_blob_at(  # type: ignore[arg-type]
        root, head, Path("nested/evidence.txt")
    ) == b"normal-path\n"


def test_read_blob_at_rejects_trailing_cr_without_aliasing(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, "alias-target.txt", b"prefix-blob\n")
    head = _commit(root, "trailing CR alias fixture")
    candidate = "alias-target.txt\r"

    assert _legacy_unframed_blob(root, head, candidate) == b"prefix-blob\n"
    with pytest.raises(M.PreregistrationError) as caught:
        M.read_blob_at(root, head, candidate)
    assert caught.value.reason == "path-control-char"
    assert str(caught.value) == "path-control-char"


@pytest.mark.parametrize(
    "control",
    [
        # Git は LF で request を分け、直前の CR も終端として落とす。
        pytest.param("\r\n", id="embedded-cr"),
        pytest.param("\n", id="embedded-lf"),
    ],
)
def test_read_blob_at_rejects_embedded_path_control_chars(
    tmp_path: Path, control: str
) -> None:
    root = _init_repo(tmp_path)
    candidate = f"alias-{control}HEAD:-target.txt"
    prefix_blob = b"wrong-prefix-blob\n"
    intended_blob = b"intended-controlled-path-blob\n"
    _write(root, "alias-", prefix_blob)
    _write(root, "-target.txt", b"second-request-blob\n")
    _write(root, candidate, intended_blob)
    head = _commit(root, "embedded control alias fixture")

    assert candidate == candidate.strip()
    assert intended_blob != prefix_blob
    assert _legacy_unframed_blob(root, head, candidate) == prefix_blob
    with pytest.raises(M.PreregistrationError) as caught:
        M.read_blob_at(root, head, candidate)
    assert caught.value.reason == "path-control-char"
    assert str(caught.value) == "path-control-char"


def test_read_blob_at_rejects_control_chars_after_single_stringification(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _write(root, "alias-target.txt", b"prefix-blob\n")
    head = _commit(root, "non-string path fixture")

    class StringablePath:
        calls = 0

        def __str__(self) -> str:
            self.calls += 1
            return "alias-target.txt\r"

    candidate = StringablePath()
    with pytest.raises(M.PreregistrationError) as caught:
        M.read_blob_at(root, head, candidate)  # type: ignore[arg-type]
    assert candidate.calls == 1
    assert caught.value.reason == "path-control-char"
    assert str(caught.value) == "path-control-char"


def test_git_timeout_generation_commit_and_blob_limits_fail_closed(
    tmp_path: Path, monkeypatch
) -> None:
    with pytest.raises(M.PreregistrationError) as generation:
        M.generation_path(M.MAX_GENERATIONS + 1)
    assert generation.value.reason == "generation-limit"

    generation_root = _init_repo(tmp_path / "generation-limit")
    oversized_path = (
        f"{M.FREEZE_DIR}/{M.FREEZE_BASENAME}.g{M.MAX_GENERATIONS + 1}.json"
    )
    _write(generation_root, oversized_path, b"{}")
    _commit(generation_root, "oversized generation")
    _assert_reason(
        "generation-limit",
        M.prepare_revision,
        generation_root,
        revision_reason="must reject before constructing a huge range",
    )

    root = _init_repo(tmp_path / "commit-limit")
    _write(root, "marker", b"second\n")
    head = _commit(root, "second")
    monkeypatch.setattr(M, "MAX_COMMITS", 1)
    _assert_reason("commit-limit", M._commit_graph, root, head)

    blob_root = _init_repo(tmp_path / "blob-limit")
    _write(blob_root, "large.bin", b"1234")
    blob_head = _commit(blob_root, "large blob")
    monkeypatch.setattr(M, "MAX_BLOB_BYTES", 3)
    _assert_reason("blob-byte-limit", M.read_blob_at, blob_root, blob_head, "large.bin")

    def timeout(*args, **kwargs):
        del args, kwargs
        raise subprocess.TimeoutExpired("git", M.GIT_TIMEOUT_SECONDS)

    monkeypatch.setattr(M.subprocess, "run", timeout)
    _assert_reason("git-timeout", M._git, root, ["status", "--short"])


def test_git_timeout_budget_constants_match_preregistered_measurement() -> None:
    assert M.GIT_TIMEOUT_SECONDS == 15.0
    assert M.GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST == 0.0086
    assert M.GIT_TIMEOUT_CAP_SECONDS == 300.0
    assert M.GIT_TIMEOUT_CAP_SECONDS != (
        M.GIT_TIMEOUT_SECONDS
        + M.MAX_BATCH_REQUESTS * M.GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST
    )


@pytest.mark.parametrize(
    ("stdin", "expected"),
    [
        pytest.param(None, 15.0, id="no-stdin"),
        pytest.param(b"", 15.0, id="empty-stdin"),
        pytest.param(b"x\n" * 7_005, 75.243, id="legal-linear-example"),
        pytest.param(
            b"x\n" * M.MAX_BATCH_REQUESTS,
            300.0,
            id="max-batch-requests",
        ),
        pytest.param(
            b"x\n" * (M.MAX_BATCH_REQUESTS + 1),
            300.0,
            id="above-max-batch-requests",
        ),
        pytest.param(b"unterminated", 15.0086, id="no-trailing-lf"),
        pytest.param(b"x" * 1_000, 15.0086, id="not-byte-length"),
        pytest.param(b"x\ry", 15.0086, id="lf-framing-only"),
    ],
)
def test_git_timeout_budget_from_request_count(
    stdin: bytes | None, expected: float
) -> None:
    assert M._git_timeout_budget_seconds(stdin) == expected


def test_git_timeout_budget_never_exceeds_absolute_cap() -> None:
    amplified = b"x\n" * (M.MAX_BATCH_REQUESTS * 2)
    assert M._git_timeout_budget_seconds(amplified) == M.GIT_TIMEOUT_CAP_SECONDS


def test_git_timeout_budget_clamps_requests_before_rate_amplification(
    monkeypatch,
) -> None:
    monkeypatch.setattr(M, "GIT_TIMEOUT_CAP_SECONDS", 1_000.0)
    at_limit = b"x\n" * M.MAX_BATCH_REQUESTS
    amplified = b"x\n" * (M.MAX_BATCH_REQUESTS * 2)
    expected = (
        M.GIT_TIMEOUT_SECONDS
        + M.MAX_BATCH_REQUESTS * M.GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST
    )
    assert M._git_timeout_budget_seconds(at_limit) == expected
    assert M._git_timeout_budget_seconds(amplified) == expected


def test_git_uses_one_internal_budget_and_preserves_timeout_reason(
    tmp_path: Path, monkeypatch
) -> None:
    stdin = b"x\n" * (M.MAX_BATCH_REQUESTS * 2)
    budget_calls: list[bytes | None] = []
    run_timeouts: list[float] = []
    expected_timeout = 123.25

    def budget(value: bytes | None) -> float:
        budget_calls.append(value)
        return expected_timeout

    def complete(command, **kwargs):
        del command
        run_timeouts.append(kwargs["timeout"])
        return object()

    monkeypatch.setattr(M, "_git_timeout_budget_seconds", budget)
    monkeypatch.setattr(M.subprocess, "run", complete)
    assert M._git(tmp_path, ["cat-file", "--batch-check"], stdin=stdin) == b""
    assert budget_calls == [stdin]
    assert run_timeouts == [expected_timeout]

    timeout_calls = 0

    def timeout(command, **kwargs):
        nonlocal timeout_calls
        timeout_calls += 1
        assert kwargs["timeout"] == expected_timeout
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(M.subprocess, "run", timeout)
    _assert_reason(
        "git-timeout",
        M._git,
        tmp_path,
        ["cat-file", "--batch-check"],
        stdin=stdin,
    )
    assert timeout_calls == 1


def test_git_budget_caller_surfaces_match_exact_contract() -> None:
    empty = inspect.Parameter.empty
    positional = inspect.Parameter.POSITIONAL_OR_KEYWORD
    keyword_only = inspect.Parameter.KEYWORD_ONLY
    expected_signatures = {
        "_git": (
            ("root", positional, empty),
            ("args", positional, empty),
            ("stdin", keyword_only, None),
        ),
        "_git_text": (
            ("root", positional, empty),
            ("args", positional, empty),
            ("stdin", keyword_only, None),
        ),
        "validate_condition_freeze_at": (
            ("repo_root", positional, empty),
            ("commit", positional, "HEAD"),
        ),
        "prepare_revision": (
            ("repo_root", positional, empty),
            ("ruling_reference", keyword_only, None),
            ("revision_reason", keyword_only, empty),
            ("commit", keyword_only, "HEAD"),
        ),
    }
    functions = (
        M._git,
        M._git_text,
        M.validate_condition_freeze_at,
        M.prepare_revision,
    )
    actual_signatures = {
        function.__name__: tuple(
            (parameter.name, parameter.kind, parameter.default)
            for parameter in inspect.signature(function).parameters.values()
        )
        for function in functions
    }
    assert actual_signatures == expected_signatures

    parsers = [((), M._build_parser())]
    option_strings: set[str] = set()
    action_surfaces: dict[tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...]] = {}
    for path, parser in parsers:
        actions: list[tuple[str, tuple[str, ...]]] = []
        for action in parser._actions:
            option_strings.update(action.option_strings)
            actions.append((action.dest, tuple(action.option_strings)))
            if isinstance(action, argparse._SubParsersAction):
                parsers.extend(
                    ((*path, command), child)
                    for command, child in action.choices.items()
                )
        action_surfaces[path] = tuple(actions)

    assert option_strings == {
        "-h",
        "--help",
        "--commit",
        "--repo-root",
        "--json",
        "--ruling-reference",
        "--revision-reason",
    }
    assert action_surfaces == {
        (): (("help", ("-h", "--help")), ("command", ())),
        ("check",): (
            ("help", ("-h", "--help")),
            ("commit", ("--commit",)),
            ("repo_root", ("--repo-root",)),
            ("json_output", ("--json",)),
        ),
        ("prepare-revision",): (
            ("help", ("-h", "--help")),
            ("commit", ("--commit",)),
            ("repo_root", ("--repo-root",)),
            ("ruling_reference", ("--ruling-reference",)),
            ("revision_reason", ("--revision-reason",)),
        ),
    }


def test_git_failed_reason_is_preserved_with_computed_budget(
    tmp_path: Path, monkeypatch
) -> None:
    def fail(command, **kwargs):
        del kwargs
        raise subprocess.CalledProcessError(2, command, stderr=b"fixture failure")

    monkeypatch.setattr(M.subprocess, "run", fail)
    _assert_reason("git-failed", M._git, tmp_path, ["status", "--short"])


def test_git_input_limit_stops_before_subprocess(tmp_path: Path, monkeypatch) -> None:
    calls = 0
    budget_calls = 0

    def must_not_budget(*args, **kwargs):
        nonlocal budget_calls
        budget_calls += 1
        raise AssertionError("input limit 後に git 予算を計算してはならない")

    def must_not_run(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("input limit 後に git subprocess を起動してはならない")

    monkeypatch.setattr(M, "MAX_GIT_INPUT_BYTES", 3)
    monkeypatch.setattr(M, "_git_timeout_budget_seconds", must_not_budget)
    monkeypatch.setattr(M.subprocess, "run", must_not_run)
    _assert_reason("git-input-limit", M._git, tmp_path, ["cat-file"], stdin=b"1234")
    assert budget_calls == 0
    assert calls == 0


def test_git_output_limit_stops_repository_probe(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def oversized_output(command, **kwargs):
        calls.append(tuple(command))
        kwargs["stdout"].write(b"false\n")
        return object()

    monkeypatch.setattr(M, "MAX_GIT_OUTPUT_BYTES", 3)
    monkeypatch.setattr(M.subprocess, "run", oversized_output)
    _assert_reason("git-output-limit", M._assert_repository_safe, tmp_path)
    assert len(calls) == 1
    assert "--is-shallow-repository" in calls[0]


def test_batch_request_limit_stops_before_git(tmp_path: Path, monkeypatch) -> None:
    calls = 0

    def must_not_run(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("batch request limit 後に git を呼んではならない")

    monkeypatch.setattr(M, "MAX_BATCH_REQUESTS", 1)
    monkeypatch.setattr(M, "_git", must_not_run)
    _assert_reason(
        "batch-request-limit",
        M._batch_oids,
        tmp_path,
        ("a" * 40, "b" * 40),
        ("path",),
    )
    assert calls == 0


def test_total_blob_limit_stops_before_blob_batch(tmp_path: Path, monkeypatch) -> None:
    first = "a" * 40
    second = "b" * 40
    batch_calls = 0

    def size_headers(*args, **kwargs):
        del args, kwargs
        return f"{first} blob 2\n{second} blob 2"

    def must_not_read_blobs(*args, **kwargs):
        nonlocal batch_calls
        batch_calls += 1
        raise AssertionError("total blob limit 後に blob batch を読んではならない")

    monkeypatch.setattr(M, "MAX_TOTAL_BLOB_BYTES", 3)
    monkeypatch.setattr(M, "_git_text", size_headers)
    monkeypatch.setattr(M, "_git", must_not_read_blobs)
    _assert_reason("blob-total-byte-limit", M._batch_blob_bytes, tmp_path, (first, second))
    assert batch_calls == 0
