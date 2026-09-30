---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-t2867-contrast-run
seq: 3
title: [T-2867] 関数方策の軸の生成器対照を発効させ 4 arm × 12 系列を完走、report は 4 比較とも比較 floor 内の同等 (docs + driver の最小修正 1 + insight、branch worktree-dev-wave-t2867-contrast-run)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_11.txt` と `common-4.txt` (逐語は一次資料 `output/insights/2026-09-30/t2867-silo-policy-contrast-run/verbatim/`)。発効の決定は {{D:silo-policy-contrast-v1-effective}}。
- 結論 (一次資料 §0・§6): 51 項目 (48 系列 + 参照 3) すべて `b-complete`、欠測・fallback・anomaly 0。report は 4 比較とも「同等 (観測差が floor 内)」で、どの LLM 構成も条件付き優越を満たさない (失敗条件 (c) の成立)。
  族 B の raw p 0.042・0.045 が最小だが Holm の初段 0.025 に届かず、median(d) 0.011〜0.018 も δ 0.0296 以下。score の median はどの arm も約 3.93 M tps。
- 段 4 の親の裁定 (P1): 未実走部品 (score・参照・進化×IR) は v1 の外の試験版 cohort で先に確かめた。台帳が checkout の HEAD を束縛するので、v1 の中の欠陥は直せず欠測になるため。
  前走で参照 job の静的 10 µs の condition gate の欠陥 (config.h 不在) を見つけ、Codex author の最小修正 (`1da88472b`、変異 2/2 KILLED) で直してから本走した。
- 駆動 loop (repo の外、Codex author): 段 6 review 1 本 NO-GO (must-fix 4) → fix 1 → 焦点再レビュー 1 NO-GO (新 2 件) は親が nit として閉じた (結果の値を変えない) → 実機の再起動で見つけた欠陥を fix 2。
- ユーザー指示 (land 調整役・md_11 の作成元が中継): (1) 2026-09-30 19:5x「計算 job は 1 本 5 分目安に分割」— 本走の job 1・score・参照は事前登録 §5.6 が固定した同時刻対照の単位なので、中継の指示どおり登録を優先して完走させ、一次資料 §7 に書いた。
  (2) 2 ノード時間超の計算は land 調整役へ相談 (本走は D2305 項 1 で確認済みなので対象外)。(3) 10/1 00:4x〜03:10 の利用上限の一旦停止 — loop に pause file を置いて新規の LLM 親・job を止め、03:11 の再開連絡で外した。
  (4) 10/1 00:3x「同じ原因で 2 回失敗したら止めて相談・自己振り返り」— 振り返りを {{F:guard-computed-args-repeated}} と F26・F273・F859 の再発として記録し、SELF-REVIEW を送った。
- 利用上限 (429): 2026-09-30 20:10〜20:57 JST に 4 機会が保留 (各 4 回再開)、欠測なし。この session 自身も同時刻に上限で止まり、ユーザーの「戻った」で再開した。
- 二重担当: 同じ本走の引き継ぎとして md_24 の session が 2026-09-30 21:47 JST に起動し、md_11 の続行を確かめて何も書かずに譲った。
- 親の誤り: 子 worktree への `cd` (F859 再発)、同一 worktree の並行 dispatch による orphan hold (F273 再発)、並行 `worktree add` の rc=128 (F26 再発)、焦点走の最中に未 commit の fragment を書いて
  `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` を 1 件赤にした (コード非帰属)、公平性の目視に渡した射影に探索時の性能値を入れていた (auditor が本文の構造だけから所見を出したと明記)。
- 計算ノード: 本走 579 job・63.53 node 時間 (見積り 61〜70)。前走・自己試験・焦点走・変異で約 3 node 時間。LLM は 249 機会 (直列 45.1 時間)。
- 子の工数: Codex author 2 (駆動 loop・driver 修正)、review 1、fix 2、焦点再レビュー 1。Claude role `auditor` 1 (公平性の目視)。

## 次の一手差分

### 完了

- [T-2867] 関数方策の軸の生成器対照 (4 arm × n = 12) を発効させ ({{D:silo-policy-contrast-v1-effective}})、本走 48 系列と参照 3 本を完走し、report を実台帳で 1 回通した。
  4 比較とも比較 floor 内の同等 (条件付き優越なし)、欠測・anomaly 0。一次資料 `output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md` (report `report-v1.json`、公平性の目視 §6.1)。
  D2305 項 2 の「T-2867 の本走の目処が立った時点で T-2850 を新しい提案として示す」の契機が成立した (次の /rulings で扱う)。
  remaining: none
  base: 322ce6dd16b2174b55257b45a1f01de807d1e2f36d24836bd533a5aad81dc8df
