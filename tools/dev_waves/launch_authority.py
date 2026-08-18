"""dev-wave Codex 起動値を docs の限定された規範行から導出する。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence


STAGES = ("plan", "consult", "author", "review", "fix", "focus")

_AUTHORITY_PATHS = (
    "docs/dev-wave/operations.md",
    "docs/dev-wave/workers.md",
)
_MODEL_SECTION = "DW-O01"
_REVIEW_SECTION = "DW-S06-A"
_FOCUS_SECTION = "DW-S06-C"
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_FENCE_OPEN_RE = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
)
_H2_RE = re.compile(
    r"^## (?P<id>DW-[A-Z][0-9]{2}(?:-[A-Z])?)(?:\s+—[^\r\n]*)?[ \t]*$"
)
_MODEL_LINE_V1_RE = re.compile(
    r"`<model>`: 段 3 のみ 2 本で `(?P<sol>gpt-[A-Za-z0-9._-]+)`"
    r"→`(?P<luna>gpt-[A-Za-z0-9._-]+)`、他段 "
    r"`(?P<other>gpt-[A-Za-z0-9._-]+)`。"
)
_MODEL_LINE_V2_RE = re.compile(
    r"`<model>`: 全段 `(?P<model>gpt-[A-Za-z0-9._-]+)` "
    r"\(段 3 の 2 本も同じ\)。"
)
_REVIEW_EFFORT_LINE_RE = re.compile(
    r"実装 wave は異なるレンズの敵対レビューを "
    r"`reasoning=(?P<effort>[A-Za-z0-9_-]+)` で必ず 2 本並列で行う。"
)
_FOCUS_EFFORT_LINE_RE = re.compile(
    r"並列 fix の統合後、焦点再レビューは全体へ "
    r"`reasoning=(?P<effort>[A-Za-z0-9_-]+)` で 1 本でよい。"
)


class AuthorityError(Exception):
    """docs authority が一意に確立できない。"""


@dataclass(frozen=True)
class AuthoritySection:
    path: str
    section: str
    sha256: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "section": self.section,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class AuthoritySnapshot:
    authority_commit: str
    sections: tuple[AuthoritySection, ...]
    digest: str
    consult_models: tuple[str, str]
    other_model: str
    review_effort: str
    focus_effort: str
    model_authority_version: Literal["v1", "v2"]

    def as_dict(self) -> dict[str, object]:
        return {
            "authority_commit": self.authority_commit,
            "sections": [section.as_dict() for section in self.sections],
            "digest": self.digest,
        }


@dataclass(frozen=True)
class LaunchRequirement:
    stage: str
    lane: str | None
    model: str
    effort: str | None
    effort_authority: str
    sections: tuple[AuthoritySection, ...]


def _validate_model_mapping(
    version: Literal["v1", "v2"],
    consult_models: tuple[str, str],
    other_model: str,
) -> None:
    if version == "v1":
        if consult_models[0] == consult_models[1]:
            raise AuthorityError("DW-O01: v1 の consult 2 レンズ model が同一")
        if other_model != consult_models[0]:
            raise AuthorityError(
                "DW-O01: 他段 model と consult sol model が一致しない"
            )
        return
    if version == "v2":
        if consult_models != (other_model, other_model):
            raise AuthorityError("DW-O01: v2 の全段 model が一致しない")
        return
    raise AuthorityError("DW-O01: model authority version が不正")


def _mask_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """HTML comment を同じ長さの空白へ置換し、行をまたぐ状態を返す。"""

    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                visible.append(" " * (len(line) - cursor))
                cursor = len(line)
            else:
                end += len("-->")
                visible.append(" " * (end - cursor))
                cursor = end
                in_comment = False
            continue
        start = line.find("<!--", cursor)
        if start < 0:
            visible.append(line[cursor:])
            cursor = len(line)
        else:
            visible.append(line[cursor:start])
            cursor = start
            in_comment = True
    return "".join(visible), in_comment


def visible_top_level_lines(
    text: str, *, reject_unicode_separators: bool = True
) -> list[tuple[str, int, str]]:
    """fence/comment/raw HTML を除いた可視行を offset 付きで返す。

    offset は入力 ``str`` の文字 offset である。空文字の行は不可視位置を表す。
    U+2028/U+2029 は Markdown 行境界の偽装に使えるため入力全体を拒否する。
    """

    if reject_unicode_separators and ("\u2028" in text or "\u2029" in text):
        raise AuthorityError("authority docs に U+2028/U+2029 がある")
    lines: list[tuple[str, int, str]] = []
    in_comment = False
    fence: tuple[str, int] | None = None
    raw_html_end: re.Pattern[str] | None = None
    raw_html_until_blank = False
    previous_line_blank = True
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        newline = raw_line[len(line) :]
        may_start_type7_html = previous_line_blank
        previous_line_blank = not line.strip()
        if raw_html_end is not None:
            lines.append(("", offset, newline))
            if raw_html_end.search(line):
                raw_html_end = None
            offset += len(raw_line)
            continue
        if raw_html_until_blank:
            if line.strip():
                lines.append(("", offset, newline))
                offset += len(raw_line)
                continue
            raw_html_until_blank = False
        if fence is not None:
            marker_char, marker_len = fence
            stripped = line.lstrip(" \t")
            indent = len(line) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue
        if not in_comment:
            fence_match = _FENCE_OPEN_RE.fullmatch(line)
            if fence_match is not None:
                marker = fence_match.group("marker")
                fence = (marker[0], len(marker))
                lines.append(("", offset, newline))
                offset += len(raw_line)
                continue
        visible, in_comment = _mask_html_comments(line, in_comment)
        fence_match = _FENCE_OPEN_RE.fullmatch(visible)
        if fence_match is not None:
            marker = fence_match.group("marker")
            fence = (marker[0], len(marker))
            lines.append(("", offset, newline))
            offset += len(raw_line)
            continue
        stripped = visible.lstrip(" \t")
        indent = len(visible) - len(stripped)
        if indent <= 3:
            raw_start = re.match(
                r"(?i)<(script|pre|style|textarea)(?:[ \t>]|$)", stripped
            )
            if raw_start is not None:
                tag = raw_start.group(1)
                end_re = re.compile(rf"(?i)</{re.escape(tag)}[ \t]*>")
                lines.append(("", offset, newline))
                if end_re.search(stripped) is None:
                    raw_html_end = end_re
                offset += len(raw_line)
                continue
            raw_delimiters = (
                (r"<\?", re.compile(r"\?>")),
                (r"<!\[CDATA\[", re.compile(r"\]\]>")),
                (r"<![A-Z]", re.compile(r">")),
            )
            delimiter = next(
                (
                    end_re
                    for start_re, end_re in raw_delimiters
                    if re.match(start_re, stripped)
                ),
                None,
            )
            if delimiter is not None:
                lines.append(("", offset, newline))
                if delimiter.search(stripped) is None:
                    raw_html_end = delimiter
                offset += len(raw_line)
                continue
            block_tag = re.match(
                r"(?i)</?(?:address|article|aside|base|basefont|blockquote|body|"
                r"caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|"
                r"fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|"
                r"head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|"
                r"nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
                r"table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[ \t/>]|$)",
                stripped,
            )
            if block_tag is not None:
                lines.append(("", offset, newline))
                raw_html_until_blank = True
                offset += len(raw_line)
                continue
            complete_tag = re.fullmatch(
                r"(?i)</?[A-Z][A-Z0-9-]*(?:[ \t]+[^<>]*)?[ \t]*/?>[ \t]*",
                stripped,
            )
            if may_start_type7_html and complete_tag is not None:
                lines.append(("", offset, newline))
                raw_html_until_blank = True
                offset += len(raw_line)
                continue
        lines.append((visible, offset, newline))
        offset += len(raw_line)
    return lines


def _unicode_separator_sentinels(text: str) -> dict[str, str]:
    first = "\ue000"
    second = "\ue001"
    while first in text:
        first += "\ue000"
    while second in text:
        second += "\ue001"
    return {"\u2028": first, "\u2029": second}


def visible_top_level_matches(
    text: str, pattern: re.Pattern[str], *, label: str
) -> list[re.Match[str]]:
    """可視 top-level の full-match を返し、候補位置の Unicode 偽装だけ拒否する。"""

    separator_sentinels = _unicode_separator_sentinels(text)
    protected = text.translate(str.maketrans(separator_sentinels))
    matches: list[re.Match[str]] = []
    sentinels = tuple(separator_sentinels.values())
    separator_re = re.compile("|".join(map(re.escape, sentinels)))
    for visible, _offset, _newline in visible_top_level_lines(
        protected, reject_unicode_separators=False
    ):
        if not any(sentinel in visible for sentinel in sentinels):
            if (match := pattern.fullmatch(visible)) is not None:
                matches.append(match)
            continue
        parts = separator_re.split(visible)
        candidates = {
            separator_re.sub("", visible),
            separator_re.sub(" ", visible),
            *parts,
        }
        if any(pattern.fullmatch(candidate) is not None for candidate in candidates):
            raise AuthorityError(
                f"{label}: 規範候補位置に U+2028/U+2029 がある"
            )
    return matches


def _visible_h2_sections(text: str, section_id: str) -> list[str]:
    lines = visible_top_level_lines(text, reject_unicode_separators=False)
    headings: list[tuple[str, int]] = []
    for visible, offset, _newline in lines:
        match = _H2_RE.fullmatch(visible)
        if match is not None:
            headings.append((match.group("id"), offset))
    matches: list[str] = []
    for index, (candidate, start) in enumerate(headings):
        if candidate != section_id:
            continue
        end = headings[index + 1][1] if index + 1 < len(headings) else len(text)
        matches.append(text[start:end])
    return matches


def _one_section(documents: Mapping[str, str], path: str, section: str) -> str:
    matches = _visible_h2_sections(documents[path], section)
    if len(matches) != 1:
        raise AuthorityError(f"{path}: {section} が {len(matches)} 件")
    return matches[0]


def _one_normative_line(section_text: str, pattern: re.Pattern[str], label: str) -> re.Match[str]:
    matches = visible_top_level_matches(section_text, pattern, label=label)
    if len(matches) != 1:
        raise AuthorityError(f"{label}: 規範行が {len(matches)} 件")
    return matches[0]


def _one_model_normative_line(
    section_text: str,
) -> tuple[Literal["v1", "v2"], re.Match[str]]:
    matches: list[tuple[Literal["v1", "v2"], re.Match[str]]] = []
    for version, pattern in (
        ("v1", _MODEL_LINE_V1_RE),
        ("v2", _MODEL_LINE_V2_RE),
    ):
        matches.extend(
            (version, match)
            for match in visible_top_level_matches(
                section_text, pattern, label=_MODEL_SECTION
            )
        )
    if len(matches) != 1:
        raise AuthorityError(f"{_MODEL_SECTION}: 規範行が {len(matches)} 件")
    return matches[0]


def _git(repo_root: Path, arguments: Sequence[str], *, text: bool = False) -> bytes | str:
    try:
        completed = subprocess.run(
            ["git", "-C", os.fspath(repo_root), *arguments],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuthorityError(f"git authority 読取に失敗: {exc}") from exc
    if completed.returncode != 0:
        raise AuthorityError("git authority 読取に失敗")
    return completed.stdout


def _resolve_commit(repo_root: Path, commit: str | None) -> str:
    target = "HEAD" if commit is None else commit
    resolved = str(
        _git(repo_root, ["rev-parse", "--verify", f"{target}^{{commit}}"], text=True)
    ).strip()
    if _COMMIT_RE.fullmatch(resolved) is None:
        raise AuthorityError("authority commit が hex40 ではない")
    return resolved


def _documents_at_commit(repo_root: Path, commit: str) -> dict[str, bytes]:
    return {
        path: bytes(_git(repo_root, ["show", f"{commit}:{path}"]))
        for path in _AUTHORITY_PATHS
    }


def _decode_documents(raw_documents: Mapping[str, bytes]) -> dict[str, str]:
    decoded: dict[str, str] = {}
    for path, raw in raw_documents.items():
        try:
            decoded[path] = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AuthorityError(f"{path}: UTF-8 ではない") from exc
    return decoded


def _aggregate_digest(commit: str, sections: Sequence[AuthoritySection]) -> str:
    payload = {
        "authority_commit": commit,
        "sections": [section.as_dict() for section in sections],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def snapshot_authority(
    repo_root: Path, *, commit: str | None = None
) -> AuthoritySnapshot:
    """commit の docs blob を読み、live 使用時は working tree と byte 比較する。"""

    root = repo_root.resolve()
    resolved = _resolve_commit(root, commit)
    raw_documents = _documents_at_commit(root, resolved)
    if commit is None:
        for path, committed in raw_documents.items():
            try:
                working = (root / path).read_bytes()
            except OSError as exc:
                raise AuthorityError(f"{path}: working tree を読めない") from exc
            if working != committed:
                raise AuthorityError(f"{path}: working tree が authority commit と異なる")
    documents = _decode_documents(raw_documents)
    model_section = _one_section(documents, _AUTHORITY_PATHS[0], _MODEL_SECTION)
    review_section = _one_section(documents, _AUTHORITY_PATHS[1], _REVIEW_SECTION)
    focus_section = _one_section(documents, _AUTHORITY_PATHS[1], _FOCUS_SECTION)
    model_version, model_match = _one_model_normative_line(model_section)
    review_match = _one_normative_line(
        review_section, _REVIEW_EFFORT_LINE_RE, _REVIEW_SECTION
    )
    focus_match = _one_normative_line(
        focus_section, _FOCUS_EFFORT_LINE_RE, _FOCUS_SECTION
    )
    if commit is None and model_version != "v2":
        raise AuthorityError("DW-O01: live authority は v2 でなければならない")
    if model_version == "v1":
        consult_models = (model_match.group("sol"), model_match.group("luna"))
        other_model = model_match.group("other")
    else:
        model = model_match.group("model")
        consult_models = (model, model)
        other_model = model
    _validate_model_mapping(model_version, consult_models, other_model)
    sections = tuple(
        AuthoritySection(
            path=path,
            section=section,
            sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )
        for path, section, raw in (
            (_AUTHORITY_PATHS[0], _MODEL_SECTION, model_section),
            (_AUTHORITY_PATHS[1], _REVIEW_SECTION, review_section),
            (_AUTHORITY_PATHS[1], _FOCUS_SECTION, focus_section),
        )
    )
    return AuthoritySnapshot(
        authority_commit=resolved,
        sections=sections,
        digest=_aggregate_digest(resolved, sections),
        consult_models=consult_models,
        other_model=other_model,
        review_effort=review_match.group("effort"),
        focus_effort=focus_match.group("effort"),
        model_authority_version=model_version,
    )


def derive_launch(
    snapshot: AuthoritySnapshot, *, stage: str, lane: str | None
) -> LaunchRequirement:
    _validate_model_mapping(
        snapshot.model_authority_version,
        snapshot.consult_models,
        snapshot.other_model,
    )
    if stage not in STAGES:
        raise AuthorityError(f"未知 stage: {stage}")
    if stage == "consult":
        if lane not in ("sol", "luna"):
            raise AuthorityError("consult は lane=sol/luna が必須")
        model = snapshot.consult_models[0 if lane == "sol" else 1]
    else:
        if lane is not None:
            raise AuthorityError("consult 以外では lane を指定できない")
        model = snapshot.other_model
    section_by_id = {section.section: section for section in snapshot.sections}
    used = [section_by_id[_MODEL_SECTION]]
    effort: str | None = None
    effort_authority = "unbound"
    if stage == "review":
        effort = snapshot.review_effort
        effort_authority = "docs"
        used.append(section_by_id[_REVIEW_SECTION])
    elif stage == "focus":
        effort = snapshot.focus_effort
        effort_authority = "docs"
        used.append(section_by_id[_FOCUS_SECTION])
    return LaunchRequirement(
        stage=stage,
        lane=lane,
        model=model,
        effort=effort,
        effort_authority=effort_authority,
        sections=tuple(used),
    )
