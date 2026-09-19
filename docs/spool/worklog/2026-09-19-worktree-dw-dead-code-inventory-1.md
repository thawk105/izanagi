---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: worktree-dw-dead-code-inventory
seq: 1
title: 参照されないコードの棚卸し — 全数走査で無参照 module は 0 件、歴史記録だけが参照する 6+1 file・test だけが参照する 48 file・完全一致の重複関数 118 組を inventory 化し、check_docs の重複 helper 1 本を統合 (−28 行)、削除は裁定パッケージへ (コード + docs、branch worktree-dw-dead-code-inventory)
---

## 本文

- 依頼 (ユーザー直接起票): orchestrator / tools / hooks の Python を import graph と参照 grep で棚卸しし、(A) 無参照 module と (C) 重複 helper を Codex author が削除・統合、(B) test だけが参照する module は test と対で扱い、(D) 歴史記録からだけ参照される module は削除せず裁定へ返す。
  実測は job dir の probe (`import_graph.py`、repo に入れない) で、Python 819 file と tracked text 26,383 file を走査した。結果: **A = 0 件**、D = 6 file / 679 行 + 事前登録文書だけが参照する 1 file、B1 (test だけ) = 29 file / 21,600 行、B2 (test + 運用文書) = 19 file / 15,216 行、C = 118 組 (1 本残しの単純合計 1,429 行)。
  依頼が例示した one-off script (`t1434_t1222_science_slice.py`・`t189_*.py`・`t2216_backoff_walk_model.py`) は全て自分の test か別 tool が参照しており A ではない。
- 段 1 の初回走査は拡張子 allowlist で `.tsv` を落とし、T-1994 の login probe 3 file を A と誤分類した。author 子 (Codex gpt-6-astra、medium) が削除前 grep で T-2638 の到達性台帳 (`output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv` 等) の参照 6 件を見つけて削除を保留した (fail-closed が機能)。走査対象を全 text へ広げて再走し、3 file は D として裁定へ回した。
  段 6 review (Codex read-only 1 本、2 レンズ) は must-fix 9 件を出し、うち real = probe が親 package の `__init__.py` への暗黙 import 辺を落としていた (`tools/spool_fold.py:1307` → `orchestrator/publication/__init__.py` が B1 に混入)・専用 test 行数の二重加算・C に test file 混入・「plotting は自己完結が規約」の誤読 (`tools/plotting/README.md:72–83` は再利用を認める)・parity test を「統合で恒真」とした誤読 (固定期待値との比較)・裁定表の未完成。refuted = C8 差分の意味論・循環 import・check_docs 自身の pin 破損、M1 の他層 mask、追加削除すべき file。probe を直して再走し README を書き直した。
- 実装は C8 = `tools/check_docs.py` の `_mask_html_comments` (27 行、`tools/dev_waves/launch_authority.py` の同名関数と空行以外 byte 一致) を削除して import へ置換 (commit 18736b502、+1/−29)。焦点走 644 passed / 3 skipped (request 11156.nqsv、Elapse 19 秒)、全史 provenance 11,635 件 新規違反なし。
  変異 M1 (`launch_authority._mask_html_comments` 先頭へ `return line, False`): 期待 node を確定できず初回を probe として走らせ (DW-M08 の erratum)、`test_check_docs.py` の 14 node が赤 (baseline 緑)。本走の結果と受入全走は insight §6。
- 裁定パッケージ (`output/insights/2026-09-19/dw-dead-code-inventory/README.md` §5、R1〜R8): R1 = D の 6 file を削除するか (推奨 a = 削除、記録はそのまま)、R2 = `s6_proposal_rounds_power.py` は事前登録 producer として残す、R3 = B1 のうち一回限りの解析・probe・移行 tool 17 対 (module 15,606 行) を専用 wave で対削除するか (推奨 a、`mutation_fanout.py`・`floor_liveness.py` を残す c も可)、R4 = B1 の凍結・gate 側 12 module は残す、R5 = gate tool 3 本の scope 系 helper 統合 (約 150 行) を専用 wave にするか (推奨 b = 見送り)、R6 = plotting / t189 の小さい 5 組 (約 90 行) は次に触る wave へ相乗り (推奨 a)、R7 = 残りは見送り、R8 = [T-2276] の扱い。
  {{T:dead-code-rulings}} で追跡する。
- 費用: codex author 1 本 (workspace-write、約 7 分)、review 1 本 (read-only、約 3 分)。probe の走査は 1 走 約 5 分 × 4 走。受入全走と land の所要は insight §6。

## 次の一手差分

### 更新

- [T-2276] **P3・裁定待ち**: 本 wave の全数走査で `p2_5.py`・`s6_amendment_20260713_fence.py` は歴史記録からだけ参照される D、`s6_proposal_rounds_power.py` は事前登録文書 `docs/phase3-main-experiment.md` だけが参照する producer と確定した。処置は {{T:dead-code-rulings}} の R1 (削除するか) と R2 (残す) の裁定に従い、R1 が (a) なら削除 wave で本項も閉じる。
  base: 29d216c3f79bd4cef302d512829ea195ee1ee8a3609819330504dde68845ceaa

### 新規

- {{T:dead-code-rulings}} **P2・ユーザー裁定待ち**: dead-code 棚卸しの裁定パッケージ R1〜R8 (`output/insights/2026-09-19/dw-dead-code-inventory/README.md` §5)。R1 (D 6 file の削除) と R3 (B1 の 17 対の削除) が (a) なら、Codex author の削除 wave を 1 本立てる (受理集合が変わるので敵対検証子付き)。R5 (gate tool の scope 系 helper 統合) は推奨 b = 見送り。
