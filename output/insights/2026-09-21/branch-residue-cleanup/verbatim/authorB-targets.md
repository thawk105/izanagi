# author B の追随対象 (親が 2026-09-21 03:25 JST に現物から測った値。production 定数から再計算しない)

base commit (author B 木の HEAD): `5e3d8f3b8` (= wave 木 HEAD、T-2814 land 版 main `e07c220a0` を取り込み済み)。

## 1. `.claude/commands/cleanup-branches.md` (親が起草済み、編集しない)

- bytes (UTF-8、末尾 LF 込み): **7055**
- sha256: **3d675f09e6eea7eb6647e0be78f4843fecd6407662cbbe4e849844f559955c2b**
- 最長行: 105 chars (予算 110 は不変)
- 新予算: `TextLimit(7_055, 110)` (完成 bytes と同値、D704 / D2043 型、余白 0)

追随する定数:
- `tools/check_docs.py` L286 `".claude/commands/cleanup-branches.md": TextLimit(6_204, 110)` → `TextLimit(7_055, 110)`
- `tools/check_docs.py` L788-790 `CLEANUP_COMMAND_SHA256 = ("c8db749b…")` → 上の sha256
- `orchestrator/tests/test_check_docs.py`: `_SYNTHETIC_CLEANUP_COMMAND` (全文 literal) を新本文へ、`_EXPECTED_CLEANUP_COMMAND_SHA256` を上の sha256 へ、
  `test_cleanup_command_budget_is_pinned_and_enforced` (L9949-) の `TextLimit(6_204, 110)` → `TextLimit(7_055, 110)`、`6_201` (2 か所) → `7_055`、
  `oversized = original + "\n" + "x" * 3` → 超過が `7_059 bytes > 予算 7_055 bytes` になるよう合わせる (padding の値と期待文字列を同時に)。
  1-byte 負例 (`test_cleanup_command_one_byte_change_is_rejected` 等) は新本文で成立するよう保つ。

## 2. `.agents/skills/cleanup-branches/SKILL.md` (本 wave で不変)

- bytes 3060、sha256 `3cf0344df609115811d30a30ffe875cca1756e5a5a9aaa2c26e3c9f278269930` (T-2814 が追随済み)。`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` は触らない。

## 3. `docs/dev-wave/operations.md` の `DW-O28` 節 (親が起草済み、編集しない)

- 節 bytes (見出しから file 末尾まで、末尾 LF 込み): **994**
- 本文は現物 (`docs/dev-wave/operations.md` の `## DW-O28 — land 後の自己撤去` から末尾) を byte 一致で写す。

追随する定数:
- `tools/check_docs.py` L629 `DEV_WAVE_DW_O28_SECTION_LITERAL = """## DW-O28 — land 後の自己撤去 … """` → 現物と byte 一致 (末尾 LF の扱いは既存 literal の慣行どおり)
- `orchestrator/tests/test_check_docs.py` L189 `_SYNTHETIC_DW_O28_SECTION` → 同じ本文、L9492 / L9689 の `== 996` → `== 994`

## 4. 検証

- `python3 tools/check_docs.py` を worktree root で実走し rc 0 (違反 0 件) を報告する。
- `test_check_docs.py` は login では実走できない (親が計算ノードへ dispatch する)。
