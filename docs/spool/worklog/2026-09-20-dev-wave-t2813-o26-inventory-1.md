---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2813-o26-inventory
seq: 1
title: [T-2813] DW-O26 に「production file を変えた wave は inventory test 4 群を参照関係に依らず焦点走に含める」の 1 句を足し、exact pin (check_docs literal・test fixture) を 998/1000 bytes の新本文へ追随した — 単節予算は D782 手順 1 段目 (既存記述の削減) で収容し上限は不変、T-2292 の契約側更新を同じ変更単位で閉じた (docs + tools/check_docs.py + test、branch worktree-dev-wave-t2813-o26-inventory、Codex author 1 本・レビュー 1 本 GO・変異 matrix 3/3 KILLED + 等価 1 SURVIVED + docs 側 手動 1 KILLED)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2813-origin.md`) の範囲で 1 wave。裁定 = D2186 項 5 (採用)、予算処理の委任 = D782 / D961、
  実装面 = D95。一次資料は `output/insights/2026-09-20/t2813-o26-inventory/README.md` (brief・裁定・author / レビュー逐語・変異台帳・焦点走 log)。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/HANDOFF.md`。
- 起点 local main `f94b61fc8` から fresh worktree (開始 gate rc=0)。軽量版: 段 2・3 省略 (設計択一なし・正しさ防壁に触れない・受理集合は exact 述語の置換で
  1 → 1)、段 6 = read-only レビュー 1 本 + 変異 matrix + 焦点走 + 受入。条件 DW-O08 / O09 / O10 / O13 は非成立 (根拠は brief)。
- **収容 (D782 / D961 の手順):** DW-O26 は L2 単節予算 1000 に対し 979 bytes、裁定の新句は 331 bytes。1 段目 (既存記述の削減) で **998 bytes** に収め、
  2 段目 (独立 3 例) と 3 段目 (最小増分) には進まず、**上限は上げていない**。落としたのは根拠説明 4 件 (「名前の推測でなく」「初回実測でも」「全走緑は file
  単独緑を含意しない」「並行投入は orphan hold で rc=16 になる」= DW-C00 が同文を保持) と義務文の短縮 5 件で、6 義務と F242 参照は保持。新句は
  `orchestrator/tests/` prefix を落とす以外 4 群の名指しと「参照関係に依らず焦点走に含める」を逐語 (4 群の file 名は repo 内で一意)。
- 実装: 親 docs commit `0bb4365a2` → Codex author (unit worktree `.codex/worktrees/t2813-unit-impl`、終端 `93604a077`) → 統合 `c805a53a7` (literal / 独立 fixture /
  bytes assert 979 → 998 / M8 変異 case の削除対象を新文へ追随、他の旧本文依存なし) → 記録前に local main `eb6aa98de` を固定 SHA で merge (`15781341b`、変更面は
  main 側で不変)。裁定の「fixture placeholder (DW-O25)」は不要だった (新 D / F 番号なし、prefix 省略で合成 fixture の path 実在検査にも掛からない)。
- 段 6 レビュー (gpt-6-astra、3 レンズ 1 本): GO、must-fix 0 / nit 1。nit = 4 群は T-2292 起点 (entry 1238) の「process 起動一覧 / subprocess guard」型
  (`test_ccbench_spawn_sites.py`、`test_check_subprocess_bytecode_guard.py`) を含まない → real・scope 外 (裁定「この 1 句だけ」)、insight §7 に裁定パッケージ候補
  (択 (a) 4 群へ 2 file 追加 = D2186 項 5 の再裁定、(b) 据え置き)。反証「削減表の分類が粗い (3 件は義務文の短縮)」は採用し段 6 裁定で訂正。
- 変異 matrix (独立 clone `mutation-source` = `c805a53a7`、dispatch、probe → final): baseline PASSED、**KILLED 3/3 (期待 node 完全一致 336 / 1 / 336)、等価 1 SURVIVED、
  MISMATCH 0**。docs 側 M4' (「4 群」→「5 群」) は実 repo 正例 test 3 件が growth hold `docs_bytes` で pytest から外れているため harness に載せず、DW-O19 の手動 probe で
  `check_docs` rc=1 (exact 不一致 1 件のみ) を実測し復元・HEAD 照合済み。
- 焦点走 focus-1 (request 13595.nqsv、runner 報告 78.61 秒): 19 file = 変更 test 1 + `tools/check_docs.py` の consumer 14 + inventory 4 群 (新 DW-O26 の規則を本 wave 自身に
  適用) → 3832 passed / 16 skipped / 0 failed。`check_docs` 違反なし、`git diff --check` rc=0、provenance 全史 rc=0 (12062 件)。受入は記録 commit と段 8 の後に
  `dev_wave_wait.py acceptance` で投入し、結果は受領証 (job dir) と land の記録が持つ。
- 言わないこと: T-2292 起点の process 起動一覧 / subprocess guard 型が 4 群で被覆された。受入を代替した。上限を上げた。
- 事故: なし。M4' 手動 probe の `check_docs` が login で 2 分超 (背景化) は所要の話で事故ではない。
- 工数: codex 2 本 (author 1、review 1)、計算ノード job = 焦点走 1 + 変異 probe 5 run + final 5 run + 受入。

## 次の一手差分

### 完了

- [T-2813] DW-O26 の 1 句追加と exact pin の追随を着地した。予算は削減で収容し上限は不変。残る型 (process 起動一覧 / subprocess guard) は insight §7 の
  裁定パッケージ候補で、本 wave の scope 外。
  remaining: none
  base: 3ae725df0e5465241541fc39b07dcda23cd83af2bf27944c52db9bd84816c4eb
- [T-2292] DW-O26 の契約側 (check_docs literal・test fixture) の更新を T-2813 と同じ変更単位で行った。起点が挙げた process 起動一覧 / subprocess guard の型は
  4 群に含まれず、insight §7 の裁定パッケージ候補として次回 /rulings へ (新規 T は起票しない)。
  remaining: none
  base: e9db659d8fd2eccd8fabaa3d2fe45724e5f850969214943ad9cfa29851196ff3
