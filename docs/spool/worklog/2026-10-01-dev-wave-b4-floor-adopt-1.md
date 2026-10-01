---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-b4-floor-adopt
seq: 1
title: [T-2288] B-4 床値の集約を採用し pin 値を確定したが、§5 floor セルへの記入は保留した — 記入すると binary を置いていない checkout で材料レポートが止まり B-4 系 test が 34 failed + 2 errors になるため (docs + insight、branch worktree-dev-wave-b4-floor-adopt)
---

## 本文

- 依頼 (md_3) は「採用裁定を行い、採用なら事前登録 §5 floor 欄へ記入する。docs のみ・計算 0」。採用裁定は {{D:b4-floor-adopt-defer-entry}}。
  **依頼は完了していない** — 記入を試した木で B-4 系 16 file + `test_check_docs.py` を `tools/run_tests.py` の自動判定で走らせると
  (計算ノード request `40678.nqsv`) 34 failed, 1258 passed, 3 skipped, 2 errors、記入を戻した木では赤の 4 file が 259 passed だった。
  runner の failure digest に抜粋の残った 11 件のうち 10 件は spec が束縛する binary の lstat 失敗、1 件は wiring probe が未 commit の
  文書差分を拾ったもの。digest に抜粋の無い 25 件のうち 2 件はログ冒頭の詳細から同じ lstat 失敗 (1 件は行番号からの推定) で、
  23 件は個別未確認。記入は戻してあり、事前登録の bytes は変えていない。
- 段 2・3 は省き、親の provisional 裁定を read-only codex 2 本 (sol・luna、ultra) で攻撃させた。レンズ A は記入保留を支持しつつ
  説明の一般化と完了扱いを直す条件で NO-GO、レンズ B は記入保留に限り GO。親は所見 14 件 (A 8・B 6) を裁定し、
  real と採った所見はすべて記録へ反映した (表は `output/insights/2026-10-01/t2288-floor-adoption/README.md`)。実装面の差分はゼロ。
- 記録後に read-only の独立レビュー 1 本を投じ、NO-GO (must 1: 事前無作為化を前 wave の記録に依拠させたが同記録に確認が無い、
  should 2) を受けて 3 件とも real と裁定し記録を直した。事前無作為化は「確認していない」と書いている。
- submit-tree (`…/dev-wave-t2288-floor-pair-w1/submit-tree`) は開始時点で既に存在しなかった。撤去操作はしていない。
- 計算: 焦点走 2 回 (Elapse 141 s と、4 file の基準走 5 分 22 秒) と、path 誤りで 0 件だった 1 回。

## 次の一手差分

### 更新

- [T-2288] **P1・採用裁定済み ({{D:b4-floor-adopt-defer-entry}})、§5 floor セルの記入が残る (実装 wave・Codex author)**: 記入値は
  `artifact_path=output/env/pegasus/floor-pair/t2288-f1/b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json; sha256=4896a1fd1735667c62a6ce8200d3f70faf9bc0d08e0afe7c6970e61f69d7dbdf`
  で確定済み。記入すると binary (`output/env/pegasus/binaries/7cdf0dc3…`、ignored) を置いていない checkout で resolver が pin を拒否し、
  材料レポートが評価器の前で止まる。次の wave は (a) `test_p3_b4_material_report.py` と `test_p3_b4_raw_record_producer.py` の文書入力を
  fixture へ切り替え、(b) 実文書を読む `test_resolver_real_preregistration_is_absent` を登録後の期待へ更新し、(c) 実文書を消費する
  checkout に既存の `b4_binary_record place` で binary を置いて通ることを確かめ、同じ commit で floor セルを記入する。binary・receipt・
  calibration の検査は緩めない。材料は `output/insights/2026-10-01/t2288-floor-adoption/README.md` の「記入の試行」。
  base: a5c467d1e4a1d7d825f366ecca14c9d16f62166d50092addc1e5df4c24afdead
