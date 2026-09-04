---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2252-self-inconsistent-floor
seq: 1
title: [T-2252] 自己整合しない較正を層 3 の within-run 床値に使わず、健全な世代の発効まで一致なしに保った — 除外は pin の path 単位でなく環境系列単位にし、宣言は層 3 に閉じた (コード + テスト + insight、branch worktree-dev-wave-t2252-self-inconsistent-floor、変異 8/8 KILLED + 等価変異 1 生存)
---

## 本文

- **D1537 の裁定を層 3 へ実装した。** 有効な契約が pin する較正の (path, sha256) が宣言集合
  (pegasus g1 の 1 件) に完全一致する campaign では、within-run の候補形成を pin 由来・直下 record
  由来とも行わず、`no-matching-env-record` にする。between-run と直下 record の一致判定、
  `genome-absent-legacy-record` の表示は不変。設計判断は {{D:self-inconsistent-floor-series-exclusion}}。
  全文と逐語・変異台帳は `output/insights/2026-09-04_t2252-self-inconsistent-floor/README.md`。
- **段 3 の 2 レンズが plan と brief を 2 点で覆した。** (1) レンズ A: pin の path 1 本だけを除外する
  plan は、同 bytes の直下 copy が別名で置かれた場合に一致が戻り、「一致候補 2 件で重複エラー」だった
  campaign が「直下 1 件の新規一致」へ転じる受理拡大も生む。親は除外を系列単位へ変えた。
  (2) レンズ B と A が独立に: 較正検証 leaf への共有 frozenset は新しい例外台帳であり、材料レポートの
  generator hash に束縛されず、silo ladder / T-126 の identity 閉包も動かす。親は宣言を
  `layer3_report.py` 自身へ置き、`test_env_contract.py` の既知例外集合は独立 oracle として据え置いた。
  brief (P2) の「bytes 検証を呼ばずに除外」は plan と両レンズが誤りと指摘し、検証を先に完遂する形に
  した。新 status 値は裁定が要求せず発効後に語義が古くなるため足さず、理由 key 1 つに留めた。
- **段 3 で refuted になった所見 3 件。** 宣言参照は「却下された再検査の関門」ではない (samples /
  tolerance を読んで述語を再実行するものが再検査、宣言参照は authority が解決した identity の比較)、
  `_registered_clock_self_audit` は恒真ではない、テストは空実装で緑にならない。
- **段 6 レビュー B の must-fix 2 件は test 側だけで、production の挙動は不変だった。** 新 fixture 2 つが
  genome 不在の within record を使い D1538 (今後の genome 不在 record は拒否) と逆向きの gate に
  なる点は canonical genome の追加で、改訂した registered-glob テストが再帰走査への退行を検出できなく
  なった点は `scanned_files == 1` の assert で閉じた。fix 子 1 本、焦点再レビューは 3 件 closed・退行なし。
- **既存成果物の値は 1 件も変わらない** (裁定の前提を実測): repo 内の層 3 レポート 7 件はすべて隣接
  lock が authority なし (v1) で linux-baremetal。変わるのは今後生産される pegasus g1 authority の
  campaign の within-run (None) と、全新規 report の `meta.generator.sha256` だけ。既存 report・
  dossier・T2136 変異台帳にある g1 値の写しは再発行しない。
- **変異は負例 8/8 KILLED、等価変異 1 件は期待どおり SURVIVED (baseline PASSED、期待 node 9 件完全一致)。**
  probe (全件 SURVIVED 期待で観測 node を収集) → 本走の 2 段で回し、本走は main 取り込み後の
  merge commit に束縛した。過剰拒否の正例 2 件 (宣言に g2 を足す、between_run にも除外を適用) は
  健全 g2 正例と系列単位テストがそれぞれ単独で殺した。検証前除外の変異は既存の SHA 不一致
  fail-closed テストが殺し、pin-missing で除外しない変異は改訂した pin-missing テストだけが殺した。
  レビュー B が静的に予想した期待 node は 9 件すべて観測と一致した。
  等価変異 (frozenset の literal 構文だけを変える) を 1 件混ぜ、harness の SURVIVED 検出の正例にした。
- **子は 8 本。** 段 2 plan 1、段 3 敵対相談 2、段 5 実装 1、段 6 レビュー 2・fix 1・焦点再レビュー 1。
  いずれも `check_codex_output.py` rc=0。実装子と fix 子は sandbox の dispatch preflight が rc=16 で
  pytest を実走できず、正しく「実装済み・未実走」と申告した。
- **親の実測。** 焦点走 1 (変更 test file 単独) 209 passed、焦点走 2 (変更 test file + consumer test
  8 file) 1172 passed、いずれも rc=0 (計算ノード dispatch)。full provenance 監査 (merge commit f541e725b 時点、
  計算ノード dispatch 976050) は 8,089 件・新規違反なし。受入全走は land の受領証を正本とする。
- **編集面重複は 0 件** (稼働 wave t2262-floor-staged-transport の未 commit 4 file と交わらない)。

## 次の一手差分

### 完了

- [T-2252] 自己整合しない較正を層 3 の within-run 床値に使わず、健全な世代の発効まで一致なしに保つ
  実装を D1537 のとおり完了した。健全な世代 (g2) の活性化は人間手番 (D437) で本 wave の対象外。
  remaining: none
  base: fbb94281ddb3f6b9cf6aabd063257fa8c51a9e846b8534ba17a8759830e5f52f
