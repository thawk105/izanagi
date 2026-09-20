# 段 4 裁定 — [T-2813] (2026-09-20 21:10 JST、軽量版: 段 2・3 省略)

## 1. 裁定 inbox の再走査

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-20-rulings-full26-verdicts.md` (mtime 19:50 JST) の項 5 は D2186 項 5 と同文。
wave 開始後の更新なし。新事実なし。

## 2. (P1) 新本文の確定 — real、採用

- 新本文 = `verbatim/dw-o26-new-section.md`、**998 bytes** (見出し + 空行 + 本文 8 行 + 末尾改行、NFC)。単節予算 1000 以内。
- D782 / D961 の手順は **1 段目 (既存記述の削減) で閉じた**。2 段目 (独立 3 例) と 3 段目 (上限引き上げ) には進まない。上限は上げない → 報告対象外。
- 削減した語句 (すべて根拠説明で、義務ではない):
  | 削った語句 | 理由 |
  |---|---|
  | 「名前の推測でなく」 | 「参照関係で引いた」が含意 |
  | 「の変更は公開 API の」 | 「consumer 表に出ない」に含意 |
  | 「production 全体を」→「production を」 | grep 対象は production 全体のまま |
  | 「この拡張を欠く焦点走は、…初回実測でも取り逃す」→「欠くと…取り逃す」 | 根拠説明の短縮。attack 文字列「静的レビューが見落とした破れを」と F242 は 1 行内に保持 |
  | 「並行投入は orphan hold で rc=16 になる」 | DW-C00 (L1) が同文「並行はorphan holdでrc=16、`DW-O26`」を保持、全文複製の解消 |
  | 「（全走緑は file 単独緑を含意しない）」 | 根拠説明 |
  | 「受入全走前」→「受入前」、「焦点走に含める」→「含める」(メタテストの文) | 文脈で一意 |
  | 「変更した」→「変更」(3 箇所)、「焦点走対象 file 集合」→「焦点走 file 集合」 | 短縮 |
- 保持した 6 義務: (1) 参照関係で引く (2) private symbol は symbol 名で production を grep (3) 同一 worktree の dispatch は全種直列 (4) 変更 test file は受入前に単独走
  (5) 新規 test file の走は file 集合列挙のメタテストも含める (6) 並行 wave の相乗り・受入後に足さない。
- 新句 (裁定 D2186 項 5 の文言) との差: `orchestrator/tests/` prefix を落とす (4 群は全て `orchestrator/tests/` 直下で file 名は repo 内で一意、`git ls-files` で実測)、
  「wave は、」の読点を落とす、括弧は既存本文の全角に揃える。4 群の名指し (2 つの説明句を含む) と「参照関係に依らず焦点走に含める」は逐語。
- 名指しの 2 test は実在: `test_campaign.py:4836 test_certified_writer_authorization_caller_inventory_is_closed`、
  `test_official_perf_closure.py:912 test_outer_perf_file_and_added_guard_inventory_is_exact`。

## 3. scope / 変更面 v2

1. 親 (docs): `docs/dev-wave/operations.md` DW-O26 節を新本文へ置換 → docs commit (親 author)。
2. Codex author (実装面): `tools/check_docs.py` `DEV_WAVE_DW_O26_SECTION_LITERAL` を新本文へ、`orchestrator/tests/test_check_docs.py` `_SYNTHETIC_DW_O26_SECTION` を
   新本文へ、bytes assert `== 979` → `== 998` (L9486)。`o26_contract_weakened` (L7149) の attack 文字列は新本文に 1 回残るので不変。他に DW-O26 本文へ依存する
   test があれば追随 (子が `grep -n "DW-O26\|焦点走の consumer" orchestrator/tests/` で閉包を引く)。
3. 触らない: `docs/failures.md` の DW-O26 逐語引用 (歴史記録)、`docs/dev-wave/core.md`、L1 / L1.5 予算、他の pin 節、guard 類。

## 4. 変異事前登録 (DW-M01、実装前)

| ID | 位置 | 変異 | 期待する赤 (1 理由) |
|---|---|---|---|
| M1 | `tools/check_docs.py` `DEV_WAVE_DW_O26_SECTION_LITERAL` | 「4 群」→「5 群」(1 文字) | `test_check_docs.py::test_dev_wave_exact_visible_section_literals_are_independent` 系 (literal == fixture) が不一致で赤 |
| M2 | `orchestrator/tests/test_check_docs.py` bytes assert | `== 998` → `== 979` | 同 file の bytes assert が赤 (理由 = bytes) |
| M3 | `orchestrator/tests/test_check_docs.py` `_SYNTHETIC_DW_O26_SECTION` | 末尾の 1 文「並行 wave が…足さない。」を削る | fixture ≠ literal で literal 比較が赤 (M1 と同 node でも変異位置が異なる) |
| M4 | `docs/dev-wave/operations.md` DW-O26 節 (tracked、DW-O19 で即時復元) | 本文末尾に「。」1 文字追加 (1001 bytes) | 実 repo `python3 tools/check_docs.py` が exact pin 不一致 + 単節予算超過で赤 (赤理由 2 つ → M4 は harness 登録せず親の手動 probe とし、pin 不一致だけを確認する変異は M4' = 「4 群」→「5 群」で 998 bytes 維持) |

実装後に各変異の「同じ入力を拒否する層が前後・内側に無い」を確認し、確認できない変異は登録から外す (F28)。段 6 の変異 harness の spec は
`docs/dev-wave/mutation.md` DW-M02〜M08 を読んでから書く。

## 5. 軽量版の根拠

設計択一なし (裁定が文言まで決めている)、正しさ防壁 (verifier / gate) に触れない、受理集合は exact 述語の置換で 1 → 1。段 6 は read-only レビュー 1 本
(義務の欠落・裁定文言とのずれ・pin 整合の 3 レンズを 1 本で) + 変異 matrix + 焦点走 + 受入。
