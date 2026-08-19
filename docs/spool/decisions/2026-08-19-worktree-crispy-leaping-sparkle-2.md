---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: worktree-crispy-leaping-sparkle
seq: 2
---

## {{D:operations-section-registry-union}}. 新規 L2 節は `_OPERATION_NUMBERS` から独立した union で登録する

**決定:** `docs/dev-wave/operations.md` へ新規 L2 節を追加するとき、`tools/check_docs.py` の
`REQUIRED_REFERENCE_SECTIONS["docs/dev-wave/operations.md"]` は `_OPERATION_NUMBERS` 由来の
内包表記と新節 ID の union (`{f"DW-O{i:02d}" for i in _OPERATION_NUMBERS} | {"DW-O<NN>"}`) で
登録し、`_OPERATION_NUMBERS` 自体は変更しない。番号は過去に削除された ID (現在 `DW-O07`/
`DW-O15`) を再利用せず、未使用の番号を新たに使う。

**理由:**
- `_OPERATION_NUMBERS` を変更すると `_ALL_OPERATIONS` も連動して広がり、
  `.claude/commands/dev-wave.md` の段5/段6 `|C|` 行 (range 表記のセル) も編集対象になる。
  同ファイルは L0 command entry として byte 予算の余白がほぼ無い (実測 8 bytes/9500) ため、
  この波及コストを負えない。独立 union なら波及しない。
- 削除済み ID の再利用は復活そのものに新規裁定が要る (2026-08-18 commit `ebf6b133` の
  コミットメッセージが明記)。

**却下した選択肢:**
- `_OPERATION_NUMBERS` へ新番号を直接追加する — 上記の波及コストを負う。
- 削除済み番号 (`DW-O07`) を再利用する — 復活の新規裁定が別途要る。
- `docs/dev-wave/core.md` の `DW-C0x` 系 (前例 `DW-C01`) へ収容する — 既存 `DW-C01` は
  991/1000 bytes で新規追加の余地がなく、新設 `DW-C02` も選べたが、`operations.md` 内に
  留めるほうが `DW-O18` と主題的に近く、条件 dispatch 側の変更も row 18 の cell 拡張だけで
  済み最小コストだった。
