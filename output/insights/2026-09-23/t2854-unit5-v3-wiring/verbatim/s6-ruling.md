# [T-2854] 単位 5 — 段 6 裁定 (親、2026-09-23 20:5x JST)

入力: 統合 commit 599da1b85 (author 子 a2c836469 の限定 patch)、親の自走 (solo-verifier-1.log: 140 passed / 1 failed)、
焦点走 1 (focus-1.log、計算ノード 21117.nqsv、Elapse 460 秒: 7,924 passed / 15 skipped / 2 failed)、review A (codex/s6-review-A.md)、review B (codex/s6-review-B.md)。

焦点走の赤 2 件 = test_campaign.py::test_tpcc_executor_v3_v2_existence_and_witness、test_verifier.py::test_v3_district_lost_update_and_serial_control。
他 (inventory 4 群、受入所要台帳の meta 試験、consumer 57 file) は緑。

## 所見の裁定

| ID | 裁定 | fix の内容 |
|---|---|---|
| 親 F1 (lost update 試験の key `district` が 16 進でなく malformed、proof gate の引数が無く直列対照が certified にならない、lost 側の赤は malformed による偶然) | real、must-fix | key を有効な 16 進 (小文字・偶数桁) にし、直列対照が certified に届くよう既存の certified v3 試験と同じ proof gate の与え方を使う。lost update 側は malformed 0・framing 0 で non-serializable と ww / rw (表 1) を assert |
| RA1 / RB1 (executor 試験の key `district`、正例・witness 対照が汚染) | real、must-fix | 全 case の key を有効な 16 進にする。certified 正例は certified、witness 対照は notes が witness 不一致だけ |
| RA2 (v2 入力も malformed なので M8 が受理集合の変化で検出されない) | real、must-fix | v2 入力を verifier 単独なら certified になる形 (有効な key・witness 一致・X/P 充足) にし、v3 要求で reject されることを assert (M8 を当てれば abort が None になる形) |
| RB2 (critic digest.py の説明「YCSB allowlist 外」、pipeline の根拠コメントの削除) | 一部採用 | pipeline.py の `_run_trace` に根拠コメントを戻す (YCSB と TPC-C 段 1 の 2 つを allowlist する理由、TPC-C は CCBench 側の計数修正 = 設計 §3.5 を前提にし、v3 は verifier 後に要求する、を 2〜3 行)。critic/digest.py は触らない (説明が不正確になるのは production で TPC-C を build する経路ができた後。記録だけ) |
| RB3 (witness 3 case の重複) | nit、不採用 | 欠落形態の記録として残す |

## fix の規模上限
production 変更はコメントだけ (+≤ 5 行)。試験の追加削除は ≤ 80 行。新規 test 関数 0。既存試験の期待値は変えない (今回足した 5 本の中は直してよい)。
