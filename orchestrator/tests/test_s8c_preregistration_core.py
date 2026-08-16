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
sys.path.insert(0, str(_ORCHESTRATOR.parent))

from orchestrator.campaign import s8c_preregistration as M  # noqa: E402


EVIDENCE_CONTRACT_FILE = _ROOT / M.EVIDENCE_CONTRACT_PATH
LEGACY_NUL_CONTRACT = (
    b'{"conditions":[{"consumer_requirement":{"path":'
    b'"orchestrator/campaign/trial_registry.py\\u0000alias"}}]}'
)
LEGACY_NUL_CONTRACT_SHA256 = (
    "5203daa58be7cc33303ded109851d9ab9feabc34177a5aa0afef8488ccb6ba7b"
)
LEGACY_NUL_CONTRACT_POINTER = "/conditions/0/consumer_requirement/path"
LEGACY_CRLF_CONTRACTS = (
    (
        "cr",
        b'{"conditions":[{"consumer_requirement":{"path":'
        b'"orchestrator/campaign/trial_registry.py\\ralias"}}]}',
        "ee1a7db8c672524d752d1177439f373f83e4d2d6ec6b630300d2301f8c0afbec",
    ),
    (
        "lf",
        b'{"conditions":[{"consumer_requirement":{"path":'
        b'"orchestrator/campaign/trial_registry.py\\nalias"}}]}',
        "416e6b6b7c968eb1536c058f1ffd35b0d3a4b3c46b8bffb229eb75181958e85b",
    ),
)
LEGACY_CRLF_CONTRACT_POINTER = "/conditions/0/consumer_requirement/path"

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


def _contract_path_cases() -> tuple[tuple[str, tuple[str | int, ...]], ...]:
    """production helper から独立に、実契約の全 ``path`` 位置を文書順で列挙する。"""
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    cases: list[tuple[str, tuple[str | int, ...]]] = []

    def visit(node: object, pointer: str, selectors: tuple[str | int, ...]) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                child_pointer = f"{pointer}/{key}"
                child_selectors = (*selectors, key)
                if key == "path" and isinstance(child, str):
                    cases.append((child_pointer, child_selectors))
                visit(child, child_pointer, child_selectors)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{pointer}/{index}", (*selectors, index))

    visit(value, "", ())
    return tuple(cases)


EVIDENCE_CONTRACT_PATH_CASES = _contract_path_cases()


def _independent_evidence_contract_sha256(raw: bytes) -> str:
    """production hash helper を使わず evidence contract の hash を求める。"""
    value = json.loads(raw)
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(M._DOMAIN_EVIDENCE + canonical).hexdigest()


def _contract_with_selector_suffixes(
    *changes: tuple[tuple[str | int, ...], str],
) -> bytes:
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    for selectors, suffix in changes:
        target = value
        for selector in selectors[:-1]:
            target = target[selector]
        target[selectors[-1]] += suffix
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def _contract_with_path_suffix(*, owner: str, suffix: str) -> tuple[bytes, str]:
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    condition_index = len(value["conditions"]) - 1
    row = value["conditions"][condition_index]
    if owner == "required":
        evidence_index = len(row["required_evidence"]) - 1
        target = row["required_evidence"][evidence_index]
        pointer = (
            f"/conditions/{condition_index}"
            f"/required_evidence/{evidence_index}/path"
        )
    elif owner == "consumer":
        target = row["consumer_requirement"]
        pointer = f"/conditions/{condition_index}/consumer_requirement/path"
    else:
        raise AssertionError(owner)
    target["path"] += suffix
    return json.dumps(value, ensure_ascii=False).encode("utf-8"), pointer


def _contract_with_interior_path_control(
    *, owner: str, control: str
) -> tuple[bytes, str, str]:
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    condition_index = len(value["conditions"]) - 1
    row = value["conditions"][condition_index]
    if owner == "required":
        evidence_index = len(row["required_evidence"]) - 1
        target = row["required_evidence"][evidence_index]
        pointer = (
            f"/conditions/{condition_index}"
            f"/required_evidence/{evidence_index}/path"
        )
    elif owner == "consumer":
        target = row["consumer_requirement"]
        pointer = f"/conditions/{condition_index}/consumer_requirement/path"
    else:
        raise AssertionError(owner)
    original = target["path"]
    insertion_index = len(original) // 2
    target["path"] = (
        f"{original[:insertion_index]}{control}{original[insertion_index:]}"
    )
    return (
        json.dumps(value, ensure_ascii=False).encode("utf-8"),
        pointer,
        target["path"],
    )


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


def _legacy_record_raw(
    root: Path,
    generation: int,
    *,
    supersedes: str | None,
    ruling: str | None,
    reason: str = "fixture revision",
) -> bytes:
    document = json.loads(
        _record_raw(
            root,
            generation,
            supersedes=supersedes,
            ruling=ruling,
            reason=reason,
        )
    )
    document["schema_version"] = M.LEGACY_SCHEMA_VERSION
    del document["decider_version"]
    return M._canonical_bytes(document)


def _install_g1(root: Path) -> tuple[str, bytes]:
    raw = _record_raw(root, 1, supersedes=None, ruling=None, reason="initial contract")
    _write(root, M.generation_path(1), raw)
    return _commit(root, "install g1"), raw


def _install_legacy_v1_g1(root: Path) -> tuple[str, bytes]:
    raw = _legacy_record_raw(
        root, 1, supersedes=None, ruling=None, reason="initial legacy contract"
    )
    _write(root, M.generation_path(1), raw)
    return _commit(root, "install legacy v1 g1"), raw


def _install_legacy_nul_bound_g1(root: Path) -> str:
    """T-739 より前の hash literal に束縛した NUL 契約 g1 を導入する。"""
    assert b"\\u0000" in LEGACY_NUL_CONTRACT
    assert b"\x00" not in LEGACY_NUL_CONTRACT
    _write(root, M.EVIDENCE_CONTRACT_PATH, LEGACY_NUL_CONTRACT)
    contract = M.parse_preregistration_markdown(
        (root / M.SOURCE_PATH).read_bytes()
    )
    record_raw = M._canonical_bytes(
        M._record_document(
            1,
            None,
            contract,
            LEGACY_NUL_CONTRACT_SHA256,
            "pre-T-739 NUL fixture",
            None,
        )
    )
    _write(root, M.generation_path(1), record_raw)
    return _commit(root, "install legacy NUL-bound g1")


def _different_decider_version() -> str:
    prefix, version = M.DECIDER_VERSION.rsplit("/v", 1)
    return f"{prefix}/v{int(version) + 1}"


def _install_legacy_crlf_bound_g1(
    root: Path,
    *,
    raw: bytes,
    legacy_sha256: str,
) -> str:
    """T-787 より前の hash literal に束縛した CR/LF 契約 g1 を導入する。"""
    assert b"\\r" in raw or b"\\n" in raw
    assert b"\r" not in raw and b"\n" not in raw
    assert _independent_evidence_contract_sha256(raw) == legacy_sha256
    _write(root, M.EVIDENCE_CONTRACT_PATH, raw)
    contract = M.parse_preregistration_markdown(
        (root / M.SOURCE_PATH).read_bytes()
    )
    record_raw = M._canonical_bytes(
        M._record_document(
            1,
            None,
            contract,
            legacy_sha256,
            "pre-T-787 CR/LF fixture",
            None,
        )
    )
    _write(root, M.generation_path(1), record_raw)
    return _commit(root, "install legacy CR/LF-bound g1")


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


def _assert_tree_blob(root: Path, commit: str, path: str, expected: bytes) -> None:
    """Tree の exact path が intended blob を指すことを直接確認する。"""
    tree = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", commit],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    ).stdout
    expected_path = path.encode("utf-8")
    for entry in tree.split(b"\0"):
        metadata, separator, candidate_path = entry.partition(b"\t")
        if separator and candidate_path == expected_path:
            _, kind, object_id = metadata.split()
            assert kind == b"blob"
            actual = M._git(root, ["cat-file", "blob", object_id.decode("ascii")])
            assert actual == expected
            return
    pytest.fail(f"controlled fixture path is absent from tree: {path!r}")


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


def test_contract_path_inventory_has_expected_count() -> None:
    assert len(EVIDENCE_CONTRACT_PATH_CASES) == 39


@pytest.mark.parametrize(
    ("pointer", "selectors"),
    [
        pytest.param(pointer, selectors, id=pointer)
        for pointer, selectors in EVIDENCE_CONTRACT_PATH_CASES
    ],
)
def test_evidence_contract_hash_rejects_nul_at_every_consumed_path(
    pointer: str,
    selectors: tuple[str | int, ...],
) -> None:
    raw = _contract_with_selector_suffixes((selectors, "\x00alias"))
    assert b"\\u0000" in raw
    assert b"\x00" not in raw

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)


@pytest.mark.parametrize(
    ("pointer", "selectors", "control"),
    [
        pytest.param(pointer, selectors, control, id=f"{pointer}-{name}")
        for pointer, selectors in EVIDENCE_CONTRACT_PATH_CASES
        for name, control in (("cr", "\r"), ("lf", "\n"))
    ],
)
def test_evidence_contract_hash_rejects_crlf_at_every_consumed_path(
    pointer: str,
    selectors: tuple[str | int, ...],
    control: str,
) -> None:
    raw = _contract_with_selector_suffixes((selectors, f"{control}alias"))

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"
    assert control not in str(caught.value)


@pytest.mark.parametrize("owner", ["required", "consumer"])
def test_evidence_contract_hash_rejects_nul_at_interior_position(
    owner: str,
) -> None:
    raw, pointer, path = _contract_with_interior_path_control(
        owner=owner,
        control="\x00",
    )
    nul_index = path.index("\x00")
    assert not path.endswith("\x00")
    assert path[nul_index + 1 :]
    assert b"\\u0000" in raw
    assert b"\x00" not in raw

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)


@pytest.mark.parametrize("owner", ["required", "consumer"])
@pytest.mark.parametrize(
    "control",
    [pytest.param("\r", id="cr"), pytest.param("\n", id="lf")],
)
def test_evidence_contract_hash_rejects_crlf_at_interior_position(
    owner: str,
    control: str,
) -> None:
    raw, pointer, path = _contract_with_interior_path_control(
        owner=owner,
        control=control,
    )
    control_index = path.index(control)
    assert control_index > 0
    assert path[control_index + 1 :]

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"
    assert control not in str(caught.value)


@pytest.mark.parametrize(
    ("owner", "control"),
    [
        pytest.param("required", "\r", id="required-cr"),
        pytest.param("required", "\n", id="required-lf"),
        pytest.param("consumer", "\r", id="consumer-cr"),
        pytest.param("consumer", "\n", id="consumer-lf"),
    ],
)
def test_evidence_contract_hash_rejects_crlf_path_controls(
    owner: str,
    control: str,
) -> None:
    raw, pointer = _contract_with_path_suffix(owner=owner, suffix=control)

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"
    assert control not in str(caught.value)


@pytest.mark.parametrize(
    ("control", "expected_sha256"),
    [
        pytest.param(
            "\x00",
            "8b8aafceb9dd5c83bde977c106facb4257318222a8a36cab38a4f18d3ab87fdc",
            id="nul",
        ),
        pytest.param(
            "\r",
            "818001ee2e0cc0315809e5b2d72e0d565e78f43fca68743ed46ff99568dfa19b",
            id="cr",
        ),
        pytest.param(
            "\n",
            "0773bb625645523ed4104bbd23f5c9e23da74e3c2d5c99f02fe7f8fb65c878da",
            id="lf",
        ),
    ],
)
def test_evidence_contract_hash_accepts_non_path_controls(
    control: str,
    expected_sha256: str,
) -> None:
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    value["conditions"][0]["static_only_note"] += f"{control}data"
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    # literal は標準ライブラリの canonical JSON + domain prefix から独立計算した。
    assert _independent_evidence_contract_sha256(raw) == expected_sha256
    assert M.evidence_contract_sha256(raw) == expected_sha256


@pytest.mark.parametrize(
    ("value", "expected_sha256"),
    [
        pytest.param(
            {"path": "x\talias"},
            "ab8123ecb208946eccd77468dbc0a721215255dc6b644e9f530285aefb69b25a",
            id="path-tab",
        ),
        pytest.param(
            {"path": "x\balias"},
            "b52b6c89067c1c706d774dbc2ae5b4c2bb3d2dab15661dce600f6ea9c44defb1",
            id="path-bs",
        ),
        pytest.param(
            {"path": "x\falias"},
            "77d9bb63f22c3ecee608a6c99cd1b72b49caea7c1c2adce14d8503a737892e21",
            id="path-ff",
        ),
        pytest.param(
            {"path": "x\u0001alias"},
            "2113ff26058c8bbfa2c04920e33b65d0a329b010694002e321a94059d3e562c1",
            id="path-u0001",
        ),
        pytest.param(
            {"path": "x\u000balias"},
            "e27ced393e0b9ef4d95104c99d57afa293467c99e8b5cf825cc2e19080a7609b",
            id="path-vt",
        ),
        pytest.param(
            {"path": "x\u0085alias"},
            "70498a1fc93e1c8bca1e9fb3704c66092c73116c46ec41fbbbb4e19bd1ef7c9c",
            id="path-u0085",
        ),
        pytest.param(
            {"path": "x\u2028alias"},
            "9f1f6439805f51329f74c0f8ffc286203a3778e46db78e93193336c920805864",
            id="path-u2028",
        ),
        pytest.param(
            {"path": "x\u2029alias"},
            "e71bf3d33b9c48d250e90e7840b31fd132887b732ed986034bad2decdf8d5ee8",
            id="path-u2029",
        ),
        pytest.param(
            {"path": r"x\ralias"},
            "e9315e0a6a2f4124200d1fb98fe2f9197b8aaf8ac6f8223d48a7fd85a8296cee",
            id="path-literal-backslash-r",
        ),
        pytest.param(
            {"path": r"x\nalias"},
            "7a7901d7d26013eb7eae440b3718df6a4087acfa58bc233a25a7a3e9f8d8c178",
            id="path-literal-backslash-n",
        ),
        pytest.param(
            {"path": {"nested": "x\ralias"}},
            "0ad0978c428b8983ea777c5248f9e8656f457f4c41753e4807d23cf98d0038a9",
            id="non-string-path-dict",
        ),
        pytest.param(
            {"path": ["x\ralias"]},
            "d8d37e8203411029fbb08100ffc31cd78486e42cffcdd0f1ab1d3ab5223a35ff",
            id="non-string-path-list",
        ),
        pytest.param(
            {"path": 1},
            "c972129fb103a6986ba9634df52125dcd99d707d4615dabd36ad11c568988556",
            id="non-string-path-number",
        ),
        pytest.param(
            {"not_path": "x\ralias"},
            "acb12029d7838803747975637cd51436da06fbfa9f14e5726d810240fa0322c7",
            id="non-exact-key",
        ),
    ],
)
def test_evidence_contract_hash_accepts_values_outside_forbidden_boundary(
    value: object,
    expected_sha256: str,
) -> None:
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    # literal は production helper を使わず標準ライブラリだけで独立計算した。
    assert _independent_evidence_contract_sha256(raw) == expected_sha256
    assert M.evidence_contract_sha256(raw) == expected_sha256


@pytest.mark.parametrize(
    ("raw", "pointer"),
    [
        pytest.param(
            b'{"path":[{"path":"x\\ralias"}]}',
            "/path/0/path",
            id="list-under-non-string-path",
        ),
        pytest.param(
            b'{"path":{"x":[{"path":"x\\nalias"}]}}',
            "/path/x/0/path",
            id="deep-dict-under-non-string-path",
        ),
    ],
)
def test_evidence_contract_hash_rejects_inner_path_under_non_string_path(
    raw: bytes,
    pointer: str,
) -> None:
    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)
    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)


def test_evidence_contract_hash_preserves_first_nul_pointer_in_document_order() -> None:
    raw = b'{"z":{"path":"x\\u0000alias"},"a":{"path":"y\\u0000alias"}}'

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == "[evidence-contract-path-nul] '/z/path'"


@pytest.mark.parametrize(
    "control_escape",
    [pytest.param(b"\\r", id="cr"), pytest.param(b"\\n", id="lf")],
)
def test_evidence_contract_hash_preserves_first_crlf_pointer_in_document_order(
    control_escape: bytes,
) -> None:
    raw = (
        b'{"z":{"path":"x'
        + control_escape
        + b'alias"},"a":{"path":"y'
        + control_escape
        + b'alias"}}'
    )

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == "[evidence-contract-path-crlf] '/z/path'"


@pytest.mark.parametrize(
    ("first_escape", "later_escape"),
    [
        pytest.param(b"\\n", b"\\r", id="lf-before-cr"),
        pytest.param(b"\\r", b"\\n", id="cr-before-lf"),
    ],
)
def test_evidence_contract_hash_preserves_first_mixed_crlf_pointer_in_document_order(
    first_escape: bytes,
    later_escape: bytes,
) -> None:
    raw = (
        b'{"z":{"path":"x'
        + first_escape
        + b'alias"},"a":{"path":"y'
        + later_escape
        + b'alias"}}'
    )

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == "[evidence-contract-path-crlf] '/z/path'"


@pytest.mark.parametrize(
    "control",
    [pytest.param("\r", id="cr"), pytest.param("\n", id="lf")],
)
def test_evidence_contract_hash_preserves_nul_precedence_in_same_path(
    control: str,
) -> None:
    raw = json.dumps(
        {"path": f"x{control}alias\x00later"},
        ensure_ascii=False,
    ).encode("utf-8")

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == "[evidence-contract-path-nul] '/path'"
    assert control not in str(caught.value)
    assert "\x00" not in str(caught.value)


@pytest.mark.parametrize(
    "control",
    [pytest.param("\r", id="cr"), pytest.param("\n", id="lf")],
)
def test_evidence_contract_hash_preserves_later_nul_over_earlier_crlf(
    control: str,
) -> None:
    first_pointer, first_selectors = EVIDENCE_CONTRACT_PATH_CASES[0]
    last_pointer, last_selectors = EVIDENCE_CONTRACT_PATH_CASES[-1]
    assert first_pointer == "/conditions/0/required_evidence/0/path"
    assert last_pointer == "/conditions/11/consumer_requirement/path"
    raw = _contract_with_selector_suffixes(
        (first_selectors, f"{control}alias"),
        (last_selectors, "\x00alias"),
    )

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {last_pointer!r}"
    assert control not in str(caught.value)
    assert "\x00" not in str(caught.value)


@pytest.mark.parametrize(
    "control_escape",
    [pytest.param(b"\\r", id="cr"), pytest.param(b"\\n", id="lf")],
)
def test_evidence_contract_hash_rejects_root_string_path(
    control_escape: bytes,
) -> None:
    raw = b'{"path":"x' + control_escape + b'alias"}'

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == "[evidence-contract-path-crlf] '/path'"


@pytest.mark.parametrize(
    "control_escape",
    [pytest.param(b"\\r", id="cr"), pytest.param(b"\\n", id="lf")],
)
def test_evidence_contract_hash_rejects_root_list_path(
    control_escape: bytes,
) -> None:
    raw = b'[{"path":"x' + control_escape + b'alias"}]'

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == "[evidence-contract-path-crlf] '/0/path'"


@pytest.mark.parametrize(
    "control_escape",
    [pytest.param(b"\\r", id="cr"), pytest.param(b"\\n", id="lf")],
)
def test_evidence_contract_hash_rejects_deep_alternating_dict_list_path(
    control_escape: bytes,
) -> None:
    raw = (
        b'{"a":[{"b":[{"c":[{"d":[{"e":[{"path":"x'
        + control_escape
        + b'alias"}]}]}]}]}]}'
    )

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == (
        "[evidence-contract-path-crlf] '/a/0/b/0/c/0/d/0/e/0/path'"
    )


@pytest.mark.parametrize(
    ("raw", "pointer"),
    [
        pytest.param(
            b'{"conditions":{"path":"x\\u0000alias"}}',
            "/conditions/path",
            id="conditions-dict",
        ),
        pytest.param(
            b'{"conditions":[{"required_evidence":[[{"path":"x\\u0000alias"}]]}]}',
            "/conditions/0/required_evidence/0/0/path",
            id="non-dict-required-evidence-wrapper",
        ),
        pytest.param(
            b'{"metadata":{"path":"x\\u0000alias"}}',
            "/metadata/path",
            id="unknown-metadata-path",
        ),
    ],
)
def test_evidence_contract_hash_rejects_nul_in_malformed_shape_path(
    raw: bytes,
    pointer: str,
) -> None:
    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)
    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)


@pytest.mark.parametrize(
    ("template", "pointer"),
    [
        pytest.param(
            b'{"conditions":{"path":"x{control}alias"}}',
            "/conditions/path",
            id="conditions-dict",
        ),
        pytest.param(
            b'{"conditions":[{"required_evidence":[[{"path":"x{control}alias"}]]}]}',
            "/conditions/0/required_evidence/0/0/path",
            id="non-dict-required-evidence-wrapper",
        ),
        pytest.param(
            b'{"metadata":{"path":"x{control}alias"}}',
            "/metadata/path",
            id="unknown-metadata-path",
        ),
    ],
)
@pytest.mark.parametrize(
    "control_escape",
    [pytest.param(b"\\r", id="cr"), pytest.param(b"\\n", id="lf")],
)
def test_evidence_contract_hash_rejects_crlf_in_malformed_shape_path(
    template: bytes,
    pointer: str,
    control_escape: bytes,
) -> None:
    raw = template.replace(b"{control}", control_escape)
    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)
    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"


def test_evidence_contract_hash_preserves_canonicalization_reason_before_nul() -> None:
    raw = (
        b'{"conditions":[{"required_evidence":'
        b'[{"path":"x\\u0000\\ud800"}]}]}'
    )
    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)
    assert caught.value.reason == "evidence-contract-json"


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(b'{"path":"x\\r\\ud800"}', id="cr"),
        pytest.param(b'{"path":"x\\n\\ud800"}', id="lf"),
    ],
)
def test_evidence_contract_hash_preserves_canonicalization_reason_before_crlf(
    raw: bytes,
) -> None:
    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)
    assert caught.value.reason == "evidence-contract-json"


def test_current_evidence_contract_hash_is_frozen() -> None:
    assert M.evidence_contract_sha256(EVIDENCE_CONTRACT_FILE.read_bytes()) == (
        "983f5d7c3b20e653dcf9518d76d8bbfbd9607fadcdd1b9d0a7118dbd578adb89"
    )


def test_existing_g1_record_pins_are_unchanged() -> None:
    record = json.loads((_ROOT / M.generation_path(1)).read_bytes())
    assert record["evidence_contract_sha256"] == (
        "c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471"
    )
    assert record["protected_sha256"] == (
        "853e6c44442780f180997b86819efaa8cbf245ae15d1a37a83e5b9a4ee99286e"
    )
    assert record["generation_number"] == 1


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


def test_validate_condition_freeze_at_rejects_legacy_frozen_nul_path_contract(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    head = _install_legacy_nul_bound_g1(root)

    with pytest.raises(M.PreregistrationError) as caught:
        M.validate_condition_freeze_at(root, head)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == (
        f"[evidence-contract-path-nul] {LEGACY_NUL_CONTRACT_POINTER!r}"
    )
    assert "\x00" not in str(caught.value)


def test_activation_report_marks_legacy_nul_bound_freeze_invalid(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    head = _install_legacy_nul_bound_g1(root)

    report = M.activation_report_at(root, head)

    assert report.condition_freeze_valid is False
    assert report.freeze_reason_code == "evidence-contract-path-nul"
    assert report.freeze_generation is None
    assert report.protected_sha256 is None
    assert report.decider_version is None
    assert report.decider_version_matches is False
    assert report.decider_version_reason_code == "decider-version-unavailable"
    assert report.effective is False


@pytest.mark.parametrize(
    ("raw", "legacy_sha256"),
    [
        pytest.param(raw, legacy_sha256, id=name)
        for name, raw, legacy_sha256 in LEGACY_CRLF_CONTRACTS
    ],
)
def test_validate_condition_freeze_at_rejects_legacy_frozen_crlf_path_contract(
    tmp_path: Path,
    raw: bytes,
    legacy_sha256: str,
) -> None:
    root = _init_repo(tmp_path)
    head = _install_legacy_crlf_bound_g1(
        root,
        raw=raw,
        legacy_sha256=legacy_sha256,
    )

    with pytest.raises(M.PreregistrationError) as caught:
        M.validate_condition_freeze_at(root, head)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == (
        f"[evidence-contract-path-crlf] {LEGACY_CRLF_CONTRACT_POINTER!r}"
    )
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)


@pytest.mark.parametrize(
    ("raw", "legacy_sha256"),
    [
        pytest.param(raw, legacy_sha256, id=name)
        for name, raw, legacy_sha256 in LEGACY_CRLF_CONTRACTS
    ],
)
def test_validate_condition_freeze_at_rejects_legacy_crlf_ancestor_under_clean_revision(
    tmp_path: Path,
    raw: bytes,
    legacy_sha256: str,
) -> None:
    root = _init_repo(tmp_path)
    _install_legacy_crlf_bound_g1(
        root,
        raw=raw,
        legacy_sha256=legacy_sha256,
    )
    g1_raw = (root / M.generation_path(1)).read_bytes()
    _write(root, M.EVIDENCE_CONTRACT_PATH, b'{"predicates":[]}')
    head, _ = _install_revision(root, g1_raw, word="clean g2")

    with pytest.raises(M.PreregistrationError) as caught:
        M.validate_condition_freeze_at(root, head)

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == (
        f"[evidence-contract-path-crlf] {LEGACY_CRLF_CONTRACT_POINTER!r}"
    )
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)


@pytest.mark.parametrize(
    ("raw", "legacy_sha256"),
    [
        pytest.param(raw, legacy_sha256, id=name)
        for name, raw, legacy_sha256 in LEGACY_CRLF_CONTRACTS
    ],
)
def test_activation_report_marks_legacy_crlf_bound_freeze_invalid(
    tmp_path: Path,
    raw: bytes,
    legacy_sha256: str,
) -> None:
    root = _init_repo(tmp_path)
    head = _install_legacy_crlf_bound_g1(
        root,
        raw=raw,
        legacy_sha256=legacy_sha256,
    )

    report = M.activation_report_at(root, head)

    assert report.condition_freeze_valid is False
    assert report.freeze_reason_code == "evidence-contract-path-crlf"
    assert report.freeze_generation is None
    assert report.protected_sha256 is None
    assert report.decider_version is None
    assert report.decider_version_matches is False
    assert report.decider_version_reason_code == "decider-version-unavailable"
    assert report.effective is False


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


def test_record_schema_version_selects_exact_key_set_and_canonical_bytes(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    v2_raw = _record_raw(root, 1, supersedes=None, ruling=None)
    v2 = M._load_freeze_record(v2_raw, expected_generation=1)
    assert v2.schema_version == M.SCHEMA_VERSION
    assert v2.decider_version == M.DECIDER_VERSION

    v1_raw = _legacy_record_raw(root, 1, supersedes=None, ruling=None)
    v1 = M._load_freeze_record(v1_raw, expected_generation=1)
    assert v1.schema_version == M.LEGACY_SCHEMA_VERSION
    assert v1.decider_version is None

    unknown = json.loads(v2_raw)
    unknown["schema_version"] = "s8c-prereg-condition-freeze/v999"
    unknown.pop("decider_version")
    _assert_reason(
        "record-schema-version",
        M._load_freeze_record,
        M._canonical_bytes(unknown),
        expected_generation=1,
    )

    v1_extra = json.loads(v1_raw)
    v1_extra["decider_version"] = M.DECIDER_VERSION
    _assert_reason(
        "record-schema-keys",
        M._load_freeze_record,
        M._canonical_bytes(v1_extra),
        expected_generation=1,
    )

    v2_missing = json.loads(v2_raw)
    v2_missing.pop("decider_version")
    _assert_reason(
        "record-schema-keys",
        M._load_freeze_record,
        M._canonical_bytes(v2_missing),
        expected_generation=1,
    )

    for raw in (v1_raw, v2_raw):
        noncanonical = json.dumps(json.loads(raw), ensure_ascii=False, indent=2).encode()
        _assert_reason(
            "record-not-canonical",
            M._load_freeze_record,
            noncanonical,
            expected_generation=1,
        )


@pytest.mark.parametrize(
    "value",
    [None, 1, "s8c-decider/v0", "s8c-decider/v01", "s8c-decider/v1/extra"],
)
def test_v2_record_decider_version_has_closed_format(tmp_path: Path, value: object) -> None:
    root = _init_repo(tmp_path)
    document = json.loads(_record_raw(root, 1, supersedes=None, ruling=None))
    document["decider_version"] = value
    _assert_reason(
        "record-decider-version",
        M._load_freeze_record,
        M._canonical_bytes(document),
        expected_generation=1,
    )


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


def test_decider_version_mutation_is_generation_mutated(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _, raw = _install_g1(root)
    document = json.loads(raw)
    document["decider_version"] = _different_decider_version()
    _write(root, M.generation_path(1), M._canonical_bytes(document))
    head = _commit(root, "mutate g1 decider version")
    _assert_reason("generation-mutated", M.validate_condition_freeze_at, root, head)


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


def _history_transition_states() -> dict[str, M._HistoryState]:
    return {
        "g0": M._HistoryState(None, 0, None, ()),
        "other-g0": M._HistoryState("0" * 64, 0, None, ()),
        "g1": M._HistoryState("1" * 64, 1, "a" * 64, ("g1",)),
        "g1-tip-a": M._HistoryState("1" * 64, 1, "e" * 64, ("g1",)),
        "g1-tip-b": M._HistoryState("1" * 64, 1, "f" * 64, ("g1",)),
        "other-g1": M._HistoryState(None, 1, None, ("other-g1",)),
        "g2": M._HistoryState("2" * 64, 2, "b" * 64, ("g1", "g2")),
        "right-g2": M._HistoryState(
            "3" * 64, 2, "c" * 64, ("g1", "right-g2")
        ),
        "g3": M._HistoryState(
            "4" * 64, 3, "d" * 64, ("g1", "g2", "g3")
        ),
        "bad-g3": M._HistoryState(
            None, 3, None, ("unrelated-g1", "unrelated-g2", "bad-g3")
        ),
    }


def test_history_state_fields_are_pinned_for_deduplication() -> None:
    assert tuple(field.name for field in dataclasses.fields(M._HistoryState)) == (
        "protected_sha256",
        "tip_generation_number",
        "tip_record_sha256",
        "record_oids",
    )


@pytest.mark.parametrize(
    ("state_name", "parent_names"),
    (
        pytest.param(
            "g3",
            ("g1", "g2", "g3"),
            id="three-state-chain",
        ),
        pytest.param(
            "g1",
            ("g1", "g1", "g1", "g1"),
            id="four-equal-parent-states",
        ),
    ),
)
def test_n_parent_transition_accepts_unique_greatest_state(
    state_name: str, parent_names: tuple[str, ...]
) -> None:
    states = _history_transition_states()
    M._assert_history_transition(
        "merge-fixture",
        states[state_name],
        tuple(states[name] for name in parent_names),
    )


@pytest.mark.parametrize(
    ("state_name", "parent_names"),
    (
        pytest.param(
            "g2",
            ("g1", "g2", "right-g2"),
            id="same-generation-maxima",
        ),
        pytest.param(
            "bad-g3",
            ("g1", "g2", "bad-g3"),
            id="higher-generation-non-prefix",
        ),
    ),
)
def test_n_parent_transition_rejects_incomparable_maxima(
    state_name: str, parent_names: tuple[str, ...]
) -> None:
    states = _history_transition_states()
    _assert_reason(
        "merge-divergent-revision",
        M._assert_history_transition,
        "merge-fixture",
        states[state_name],
        tuple(states[name] for name in parent_names),
    )


@pytest.mark.parametrize(
    ("state_name", "parent_names", "expected_reason"),
    (
        pytest.param("g1", ("g1", "g1"), None, id="equal-accept"),
        pytest.param(
            "g2",
            ("g1", "g1"),
            "merge-state",
            id="equal-reject-merge-state",
        ),
        pytest.param(
            "g2", ("g2", "g1"), None, id="left-successor-accept"
        ),
        pytest.param(
            "g2", ("g1", "g2"), None, id="right-successor-accept"
        ),
        pytest.param(
            "g1",
            ("g1", "g2"),
            "merge-divergent-revision",
            id="successor-state-mismatch",
        ),
        pytest.param(
            "g2",
            ("g2", "right-g2"),
            "merge-divergent-revision",
            id="incomparable-reject",
        ),
    ),
)
def test_two_parent_transition_matrix_is_unchanged(
    state_name: str,
    parent_names: tuple[str, str],
    expected_reason: str | None,
) -> None:
    states = _history_transition_states()
    arguments = (
        "merge-fixture",
        states[state_name],
        tuple(states[name] for name in parent_names),
    )
    if expected_reason is None:
        M._assert_history_transition(*arguments)
    else:
        _assert_reason(expected_reason, M._assert_history_transition, *arguments)


def test_two_parent_transition_matches_legacy_reference_for_generated_states() -> None:
    @dataclasses.dataclass(frozen=True)
    class ReferenceState:
        protected_sha256: str | None
        tip_generation_number: int
        tip_record_sha256: str | None
        record_oids: tuple[str, ...]

    def reference(
        state: ReferenceState,
        left: ReferenceState,
        right: ReferenceState,
    ) -> str | None:
        def is_successor(
            newer: ReferenceState, older: ReferenceState
        ) -> bool:
            return (
                newer.tip_generation_number > older.tip_generation_number
                and newer.record_oids[: older.tip_generation_number]
                == older.record_oids
            )

        if left == right:
            return None if state == left else "merge-state"
        successor = (
            left
            if is_successor(left, right)
            else right
            if is_successor(right, left)
            else None
        )
        if successor is None or state != successor:
            return "merge-divergent-revision"
        return None

    generated_states = tuple(
        (
            state,
            ReferenceState(
                state.protected_sha256,
                state.tip_generation_number,
                state.tip_record_sha256,
                state.record_oids,
            ),
        )
        for state in _history_transition_states().values()
    )
    for state, reference_state in generated_states:
        for left, reference_left in generated_states:
            for right, reference_right in generated_states:
                try:
                    M._assert_history_transition(
                        "merge-fixture", state, (left, right)
                    )
                except M.PreregistrationError as caught:
                    actual = caught.reason
                else:
                    actual = None
                assert actual == reference(
                    reference_state, reference_left, reference_right
                ), (
                    state,
                    left,
                    right,
                )


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
    assert keys == M._FREEZE_KEYS_V2
    assert not keys & {
        "self_sha256",
        "record_sha256",
        "introduction_commit",
        "activation_commit",
    }


def test_matching_decider_version_preserves_activation_conjunction(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    assert report.condition_freeze_valid is True
    assert report.decider_version == M.DECIDER_VERSION
    assert report.decider_version_matches is True
    assert report.decider_version_reason_code == "decider-version-match"
    assert report.effective is True


def test_decider_version_binds_cross_module_semantics_to_v2() -> None:
    assert M.DECIDER_VERSION == "s8c-decider/v2"


def test_mismatched_decider_version_is_not_effective(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    document = json.loads(_record_raw(root, 1, supersedes=None, ruling=None))
    mismatched_version = _different_decider_version()
    document["decider_version"] = mismatched_version
    _write(root, M.generation_path(1), M._canonical_bytes(document))
    head = _commit(root, "install mismatched decider version g1")
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    assert report.condition_freeze_valid is True
    assert report.freeze_reason_code == "valid"
    assert report.decider_version == mismatched_version
    assert report.decider_version_matches is False
    assert report.decider_version_reason_code == "decider-version-mismatch"
    assert report.effective is False


def test_legacy_v1_tip_is_readable_but_not_effective(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_legacy_v1_g1(root)
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    assert report.condition_freeze_valid is True
    assert report.freeze_reason_code == "valid"
    assert report.decider_version is None
    assert report.decider_version_matches is False
    assert report.decider_version_reason_code == "decider-version-unbound"
    assert report.effective is False


def test_invalid_running_decider_version_cannot_activate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class InvalidRuntimeDecider(str):
        def __eq__(self, other: object) -> bool:
            return True

        __hash__ = str.__hash__

    root = _init_repo(tmp_path, filled=True)
    head, raw = _install_g1(root)
    recorded_version = json.loads(raw)["decider_version"]
    monkeypatch.setattr(M, "DECIDER_VERSION", InvalidRuntimeDecider("invalid-version"))
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    assert report.decider_version == recorded_version
    assert report.decider_version_matches is False
    assert report.decider_version_reason_code == "decider-version-mismatch"
    assert report.effective is False


def test_valid_hostile_str_subclass_cannot_fake_decider_version_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class HostileRuntimeDecider(str):
        def __eq__(self, other: object) -> bool:
            return True

        __hash__ = str.__hash__

    root = _init_repo(tmp_path, filled=True)
    head, raw = _install_g1(root)
    recorded_version = json.loads(raw)["decider_version"]
    monkeypatch.setattr(
        M, "DECIDER_VERSION", HostileRuntimeDecider(M.DECIDER_VERSION)
    )
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    assert report.decider_version == recorded_version
    assert report.decider_version_matches is False
    assert report.decider_version_reason_code == "decider-version-mismatch"
    assert report.effective is False


def test_activation_report_digest_binds_decider_and_projection_fields(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    original = M._activation_report_digest(report)
    replacements = (
        {"decider_version": _different_decider_version()},
        {"decider_version_matches": False},
        {"decider_version_reason_code": "decider-version-mismatch"},
        {"projection_module_blob_sha256": "0" * 64},
    )
    assert all(
        M._activation_report_digest(dataclasses.replace(report, **change)) != original
        for change in replacements
    )


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


def test_activation_report_records_all_module_blob_hashes_at_commit(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, filled=True)
    core_bytes = Path(M.__file__).read_bytes()
    from orchestrator.campaign import s8c_preregistration_evidence as evaluator_module

    evaluator = Path(evaluator_module.__file__).read_bytes()
    projection = Path(M.__file__).with_name("s8c_generation_projection.py").read_bytes()
    _write(root, M.CORE_MODULE_PATH, core_bytes)
    _write(root, M.EVALUATOR_MODULE_PATH, evaluator)
    _write(root, M.PROJECTION_MODULE_PATH, projection)
    _commit(root, "add evaluator fixture")
    head, _ = _install_g1(root)
    report = M.activation_report_at(root, head)
    assert report.core_module_blob_sha256 == hashlib.sha256(core_bytes).hexdigest()
    assert report.evaluator_module_blob_sha256 == hashlib.sha256(evaluator).hexdigest()
    assert report.projection_module_blob_sha256 == hashlib.sha256(projection).hexdigest()


@pytest.mark.parametrize(
    ("projection", "reason"),
    (
        pytest.param(None, "projection-module-absent-at-commit", id="absent"),
        pytest.param(b"# mismatched projection\n", "projection-blob-mismatch", id="mismatch"),
    ),
)
def test_projection_blob_must_match_live_module(
    tmp_path: Path, projection: bytes | None, reason: str
) -> None:
    root = _init_repo(tmp_path, filled=True)
    core_bytes = Path(M.__file__).read_bytes()
    from orchestrator.campaign import s8c_preregistration_evidence as evaluator_module

    _write(root, M.CORE_MODULE_PATH, core_bytes)
    _write(root, M.EVALUATOR_MODULE_PATH, Path(evaluator_module.__file__).read_bytes())
    if projection is not None:
        _write(root, M.PROJECTION_MODULE_PATH, projection)
    _commit(root, "install runtime module fixtures")
    head, _ = _install_g1(root)
    report = M.activation_report_at(root, head)
    assert len(report.predicates) == 12
    assert {item.status for item in report.predicates} == {M.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {reason}
    expected_hash = hashlib.sha256(projection).hexdigest() if projection is not None else None
    assert report.projection_module_blob_sha256 == expected_hash
    assert report.effective is False


def test_projection_file_read_failure_is_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _init_repo(tmp_path, filled=True)
    core_bytes = Path(M.__file__).read_bytes()
    from orchestrator.campaign import s8c_generation_projection as projection_module
    from orchestrator.campaign import s8c_preregistration_evidence as evaluator_module

    _write(root, M.CORE_MODULE_PATH, core_bytes)
    _write(root, M.EVALUATOR_MODULE_PATH, Path(evaluator_module.__file__).read_bytes())
    _write(root, M.PROJECTION_MODULE_PATH, b"")
    _commit(root, "install empty projection fixture")
    head, _ = _install_g1(root)
    monkeypatch.setattr(projection_module, "__file__", str(tmp_path / "missing.py"))
    report = M.activation_report_at(root, head)
    assert {item.status for item in report.predicates} == {M.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {
        "projection-file-read-error"
    }
    assert report.effective is False


def test_projection_import_failure_is_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _init_repo(tmp_path, filled=True)
    core_bytes = Path(M.__file__).read_bytes()
    from orchestrator.campaign import s8c_generation_projection as projection_module
    from orchestrator.campaign import s8c_preregistration_evidence as evaluator_module

    _write(root, M.CORE_MODULE_PATH, core_bytes)
    _write(
        root, M.EVALUATOR_MODULE_PATH, Path(evaluator_module.__file__).read_bytes()
    )
    _write(
        root, M.PROJECTION_MODULE_PATH, Path(projection_module.__file__).read_bytes()
    )
    _commit(root, "install runtime module fixtures")
    head, _ = _install_g1(root)
    original_import_module = M.importlib.import_module

    def import_with_broken_projection(name: str):
        if name == "orchestrator.campaign.s8c_generation_projection":
            raise ImportError("broken projection import")
        return original_import_module(name)

    monkeypatch.setattr(
        M.importlib, "import_module", import_with_broken_projection
    )
    report = M.activation_report_at(root, head)
    assert {item.status for item in report.predicates} == {M.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {
        "projection-import-error"
    }
    assert report.effective is False


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


def test_non_json_cli_reports_decider_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _init_repo(tmp_path, filled=True)
    head, _ = _install_g1(root)
    report = M._activation_report_at_for_test(
        root, head, registry=_Registry(M.PredicateStatus.SATISFIED)
    )
    monkeypatch.setattr(M, "activation_report_at", lambda repo_root, commit: report)
    assert M.main(["check", "--repo-root", str(root), "--commit", head]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line for line in lines if line.startswith("decider_version ")] == [
        "decider_version decider-version-match"
    ]


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


def test_prepare_revision_rejects_nul_path_contract_before_create(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    evidence_raw, pointer = _contract_with_path_suffix(
        owner="required",
        suffix="\x00alias",
    )
    _write(root, M.EVIDENCE_CONTRACT_PATH, evidence_raw)
    destination = root / M.generation_path(1)

    with pytest.raises(M.PreregistrationError) as caught:
        M.prepare_revision(
            root,
            revision_reason="must reject NUL path contract",
        )

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)
    assert not destination.exists()


def test_prepare_revision_rejects_nul_path_contract_with_existing_freeze(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _install_g1(root)
    evidence_raw, pointer = _contract_with_path_suffix(
        owner="consumer",
        suffix="\x00alias",
    )
    _write(root, M.EVIDENCE_CONTRACT_PATH, evidence_raw)
    destination = root / M.generation_path(2)

    with pytest.raises(M.PreregistrationError) as caught:
        M.prepare_revision(
            root,
            ruling_reference="D327",
            revision_reason="must reject NUL path contract",
        )

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)
    assert not destination.exists()


@pytest.mark.parametrize(
    "control",
    [pytest.param("\r", id="cr"), pytest.param("\n", id="lf")],
)
def test_prepare_revision_rejects_crlf_path_contract_before_create(
    tmp_path: Path,
    control: str,
) -> None:
    root = _init_repo(tmp_path)
    evidence_raw, pointer = _contract_with_path_suffix(
        owner="required",
        suffix=f"{control}alias",
    )
    _write(root, M.EVIDENCE_CONTRACT_PATH, evidence_raw)
    destination = root / M.generation_path(1)

    with pytest.raises(M.PreregistrationError) as caught:
        M.prepare_revision(
            root,
            revision_reason="must reject CR/LF path contract",
        )

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"
    assert control not in str(caught.value)
    assert not destination.exists()


@pytest.mark.parametrize(
    "control",
    [pytest.param("\r", id="cr"), pytest.param("\n", id="lf")],
)
def test_prepare_revision_rejects_crlf_path_contract_with_existing_freeze(
    tmp_path: Path,
    control: str,
) -> None:
    root = _init_repo(tmp_path)
    _install_g1(root)
    evidence_raw, pointer = _contract_with_path_suffix(
        owner="consumer",
        suffix=f"{control}alias",
    )
    _write(root, M.EVIDENCE_CONTRACT_PATH, evidence_raw)
    destination = root / M.generation_path(2)

    with pytest.raises(M.PreregistrationError) as caught:
        M.prepare_revision(
            root,
            ruling_reference="D327",
            revision_reason="must reject CR/LF path contract",
        )

    assert caught.value.reason == "evidence-contract-path-crlf"
    assert str(caught.value) == f"[evidence-contract-path-crlf] {pointer!r}"
    assert control not in str(caught.value)
    assert not destination.exists()


def test_prepare_revision_is_exclusive_create(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    destination = M.prepare_revision(
        root,
        revision_reason="initial generated contract",
    )
    assert destination == root / M.generation_path(1)
    raw = destination.read_bytes()
    document = json.loads(raw)
    assert M._canonical_bytes(document) == raw
    assert document["schema_version"] == M.SCHEMA_VERSION
    assert document["decider_version"] == M.DECIDER_VERSION
    loaded = M._load_freeze_record(raw, expected_generation=1)
    assert loaded.schema_version == M.SCHEMA_VERSION
    assert loaded.decider_version == M.DECIDER_VERSION
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
    "suffix",
    [
        pytest.param("\x00", id="trailing-nul"),
        pytest.param("\x00not-the-contract-path", id="embedded-nul"),
    ],
)
def test_read_blob_at_rejects_nul_alias(tmp_path: Path, suffix: str) -> None:
    root = _init_repo(tmp_path)
    prefix_path = "alias-target.txt"
    prefix_blob = b"nul-prefix-blob\n"
    _write(root, prefix_path, prefix_blob)
    head = _commit(root, "NUL alias fixture")
    candidate = prefix_path + suffix

    _assert_tree_blob(root, head, prefix_path, prefix_blob)
    assert candidate != prefix_path
    assert candidate == candidate.strip()
    assert _legacy_unframed_blob(root, head, candidate) == prefix_blob
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

    _assert_tree_blob(root, head, candidate, intended_blob)
    assert candidate == candidate.strip()
    assert intended_blob != prefix_blob
    assert _legacy_unframed_blob(root, head, candidate) == prefix_blob
    with pytest.raises(M.PreregistrationError) as caught:
        M.read_blob_at(root, head, candidate)
    assert caught.value.reason == "path-control-char"
    assert str(caught.value) == "path-control-char"


def test_read_blob_at_rejects_standalone_embedded_cr_as_policy(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    candidate = "alias-\r-target.txt"
    intended_blob = b"standalone-embedded-cr-blob\n"
    _write(root, candidate, intended_blob)
    head = _commit(root, "standalone embedded CR fixture")

    _assert_tree_blob(root, head, candidate, intended_blob)
    assert candidate == candidate.strip()
    assert _legacy_unframed_blob(root, head, candidate) == intended_blob
    with pytest.raises(M.PreregistrationError) as caught:
        M.read_blob_at(root, head, candidate)
    assert caught.value.reason == "path-control-char"
    assert str(caught.value) == "path-control-char"


def test_read_blob_at_accepts_embedded_tab_path(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    candidate = "nested/tab\tpath.py"
    payload = b"embedded-tab-path\n"
    _write(root, candidate, payload)
    head = _commit(root, "embedded TAB path")

    assert M.read_blob_at(root, head, candidate) == payload


def test_read_blob_at_uses_checked_text_without_str_subclass_format_hook(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _write(root, "alias-target.txt", b"wrong-prefix-blob\n")
    intended_path = "alias-target-controlled.txt"
    intended_blob = b"intended-subclass-path-blob\n"
    _write(root, intended_path, intended_blob)
    head = _commit(root, "str subclass format hook fixture")

    class FormattingPath(str):
        format_calls = 0

        def __format__(self, format_spec: str) -> str:
            self.format_calls += 1
            return "alias-target.txt\r"

    candidate = FormattingPath(intended_path)
    assert M.read_blob_at(root, head, candidate) == intended_blob
    assert candidate.format_calls == 0


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
