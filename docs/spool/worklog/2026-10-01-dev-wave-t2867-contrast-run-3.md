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
- 親の誤り (続き): main の取り込み (D2335 = Codex 子を gpt-6-astra・ultra へ改訂し、ultra の委任を prompt で禁じる) の後、codex の起動前に DW-O01 を読み直さず、
  1 回目の記録 review が委任して launcher に不受理 (`delegation_detected`) にされた。取り直しでは委任禁止を明記して受理された。
  同じ理由で、review の所見を反映した 2 commit の trailer に reviewer を `gpt-6-sol`・`medium` と誤記した (receipt の実値は `gpt-6-astra`・`ultra`)。
  2 commit は local の wave branch にしか無かったので、land 前に 1 commit へまとめ直して正しい trailer を付けた (元の tip は ref `t2867-backup-wrong-trailer-4d50f2db8` に退避)。
- 記録 review の裁定 (一次資料 `verbatim/s6-ruling-3-records.md`): 1 回目の所見 5 件と取り直しの残り 3 件をすべて real として直し、3 巡目は投げず親の照合で閉じた。
  その過程で、事前登録 §5.2 の「numactl interleave」が Pegasus では prefix なしで走った食い違いを見つけ、本書の Erratum 16.1 に追記した (1 NUMA ノードで全 slot 同条件、判定は変わらない)。
- 受入 acc1 (2026-10-01 07:19〜07:32、post-claim merge 後の tip `aa42a70b0`): 5 failed / 28,701 passed / 74 skipped。赤はすべて `test_ccbench_spawn_sites.py` で、
  gate を後回しにした build の台帳が `run_stock_control` の `run_campaign` 呼出しを行番号 446 で固定していたのに、本 wave の driver 修正で 455 へ動いたため (自分起因)。
  焦点走に driver の consumer であるこの試験を入れていなかった親の見落とし (DW-O26)。段 6 裁定 4 (一次資料 `verbatim/s6-ruling-4-spawn-sites.md`) でこの 2 つの数値だけの変更を許し、
  Codex fix が 455 に合わせた (commit b4495e27f)。焦点走 (login の上限付き local 実行) で spawn-sites 5 件は緑、赤 4 件は `test_p3_s4_loop_policy.py` の
  `IZANAGI_EXPLORATION_OUTPUT_ROOT は repository 外` (login の `/tmp/.git` による既知の偽赤、受入の全走では緑)。
- 受入 acc2 (07:43〜08:08、tip `df9d528e6`): 2 failed / 28,704 passed / 74 skipped。赤は `test_b5_contrast_launch.py::test_v2_three_429s_restart_stock_then_accept_same_a_and_evaluate`
  (5,000 tick を 1 ms 間隔で回す loop が「first evaluation did not finish」で時間切れ) と `test_plot_b7_fixed5_regression.py::test_bbox_overlap_is_a_failure` (文字配置の重なり検査)。
  どちらも acc1 から後の本 wave の差分 (spawn-sites の行番号 2 つと docs) から到達せず、acc1 では緑。単独再走で 2 件とも緑 (非再現) → 非帰属と判定し (DW-O18)、受入を取り直した。
- 計算ノード: 本走 579 job・63.53 node 時間 (見積り 61〜70)。前走・自己試験・焦点走・変異で約 3 node 時間。LLM は 249 機会 (直列 45.1 時間)。
- 子の工数: Codex author 2 (駆動 loop・driver 修正)、review 1、fix 2、焦点再レビュー 1。Claude role `auditor` 1 (公平性の目視)。

## 次の一手差分

### 完了

- [T-2867] 関数方策の軸の生成器対照 (4 arm × n = 12) を発効させ ({{D:silo-policy-contrast-v1-effective}})、本走 48 系列と参照 3 本を完走し、report を実台帳で 1 回通した。
  4 比較とも比較 floor 内の同等 (条件付き優越なし)、欠測・anomaly 0。一次資料 `output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md` (report `report-v1.json`、公平性の目視 §6.1)。
  D2305 項 2 の「T-2867 の本走の目処が立った時点で T-2850 を新しい提案として示す」の契機が成立した (次の /rulings で扱う)。
  remaining: none
  base: 322ce6dd16b2174b55257b45a1f01de807d1e2f36d24836bd533a5aad81dc8df
