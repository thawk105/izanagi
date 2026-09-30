---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-vhash-eval-s2-plan
seq: 1
title: [T-2893] VHash md_40: 評価計画の草稿に U0 の確認段 S2 を S1 より先に発効できる単位 (§16) と前提の現在の状態 (§11.1) を足し、f_M,c の段と S2 の node 時間を積算した — 発効はしていない (docs のみ、計測なし、branch worktree-vhash-eval-s2-plan)
---

## 本文

- VHash 並行 wave md_40 (依頼 `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_40.txt`、写しは job dir `/work/SFC/tanab/tmp/vhash-eval-s2-plan-2026-09-30/request-md_40.txt`)。
  計画は草稿 `docs/vhash-evaluation-preregistration-draft.md` §16・§11.1、一次資料 `output/insights/2026-09-30/vhash-eval-s2-plan/README.md`、設計判断 {{D:vhash-eval-s2-first}}。
  §5.5 の規則・判定語・族 m = 19・区間と δ の式・S2 の cell と n は変えていない。探索段の結果を見た後の §5.5 の変更は無い。
- 段ごとの node 時間 (参考単価 5.8〜6.9 s / 走行): S0-M (f_M,c) 0.26〜0.31、S2 の門 0.37、S2 本走 1.13〜1.34 (700 走行)、計 1.76〜2.02。本 wave の計算ノードの使用は 0。
- 親が自分で確かめたこと: 区間の被覆の計算 (n・m ごと)、E 系 3 本・ro-gcflag・trace の patch が pin C の写しに fuzz なしで重なること (build・条件 gate は未確認)。生の出力は job dir の `coverage.stdout.txt`・`apply_check.stdout.txt`。
- 段構成は軽量版 (段 2・3 なし、実装面なし、変異 matrix は実装面の差分ゼロで免除)。事実の抽出に read-only の Explore 子 3 本 (sonnet) を使った。
- 段 6 の read-only review 1 本 (gpt-6-sol medium、7 call、299 秒) が NO-GO (must-fix 2・should 3・nit 1)。全件 real として採用した:
  must-fix 1 は、S2 の発効の後に族へ判定を足して m′ で読み直す手順が、§8.4 の「数え直しは発効の前に限る」と両立しない点 → 発効の後に足す判定は別の族にし、m′ ≤ 25 の境界は参考に下げた。
  must-fix 2 は、§7.2 規則 4 の「門未完了は族に入れない」と「測らない判定も m に残す」の衝突 → 規則 4 を性能値を使わない意味に読み、門の完了を構成 × workload 型ごとに見ると明記した。
  should は判定器の rc ∈ {0, 3} の明記、A_fix の経路の到達を門の走行全体の合計で求めること、smoke で 0 のときの調べ方。
- 焦点再レビュー 1 巡目 (6 call、223 秒) は前回 6 件を closed とし、新しい must-fix 1 件 (smoke の通過条件の「前進の成功」は公開への到達を保証しない) を出した → real として、通過条件を開始時より上げた公開の回数にした。焦点再レビュー 2 巡目 (3 call、82 秒) で GO (must-fix 0)。
- セッション異常: (1) worktree の submodule 初期化の 1 回目が `update-no-fetch` で rc 1、同じ呼び出しの再実行で通った。(2) 開始 gate を打った後で、handoff と依頼の写しを harness 既定の home の job dir から `/work/SFC/tanab/tmp/` へ移した (開始 gate の log は home の handoff path を記録)。
  (3) Explore 子を model 未指定で起動して hook に拒否され、sonnet を明示して起動し直した。(4) 凍結前の検出語の走査 (`s8b_holdout_freeze search`) は rc 1 だったが、hit は 2026-09-17 の既存 file 3 件 (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/`) だけで、本 wave の file は含まれない。
  (5) 受入 1 走目 (tip `0be247622`) が赤 4 件で rc 70: `test_env_contract_activation.py` の 3 件は `git archive HEAD` の 30 秒の時間切れ、`test_plot_b7_fixed5_regression.py::test_real_figure_passes_layout_check` は
  文字枠の重なり (合成データの作図で、同型の赤は worklog 1988 の受入でも非帰属と記録)。本 wave の差分は Markdown の docs・一次資料・fragment だけでこれらの test から到達しない。
  4 件を計算ノードで単独再走して全部緑 (`tools/run_tests.py --force-dispatch`、4 passed、18 秒) だったので非帰属と判定し、受入を 1 回だけ取り直した。

## 次の一手差分

### 更新

- [T-2893] **P2・草稿 v1 (未発効、S2 を先行できる形)**: VHash 論文の評価計画 (`docs/vhash-evaluation-preregistration-draft.md`、草稿 v1) を発効させる。
  v1 は md_21・md_23 の結果の読み方 (§5.5) を着地前に書き、確認段の族を m = 19 にした (D2301)。§5.5 は md_21・md_23 に当てて p* = c・K* = 1 とした (D2325、草稿 §15)。
  2026-09-30 (md_40): U0 の確認段 S2 (H4) は {{T:vhash-s2-activation}} で S1 より先に発効できる (草稿 §16、{{D:vhash-eval-s2-first}})。前提の現在の状態は草稿 §11.1。
  S1 (H1・H2・H3) の発効に残る条件: C_now の実装と門 (H3、担い手なし)、A と C に同じ計器 (H2a、担い手なし)、H1 の R の cell に md_23 の `CICADA_VHASH_WL` を組む追補、S1 の構成の門、
  throughput の D145 の意味の floor (md_35 の着地、取れなければ §8.3 の 2 案)、S1 の比較相手を A_fix (ro-gcflag 修正入り)・A_stock の 2 本にする追補 (D2322 項 2)、L-snap の生成器 (記述だけ)。
  揃ってから 1 タスクの job 合計ごとに実測単価で node 時間を計算し直し、2 node 時間以上のタスクはユーザーの確認を得て、日付付きの決定で発効させる。発効までは本計画の計測・計算投入をしない。設計の根拠は D2286 と D2301。
  base: 4ff44ca676eebc1fe995555f3ef5516674d8266d97a604b6e4b698107eb492e1

### 新規

- {{T:vhash-s2-activation}} **P2・新規 (md_39 の着地待ち、その後ユーザーの確認)**: U0 の確認段 S2 (H4: E_sp(c) 対 E_hb(c) と E_sp(c) 対 E_sp(a)、L-w の 4 cell) を草稿 §16 のとおり発効させる。
  発効に残る条件 (草稿 §16.8): md_39 の修理版 E の着地と §16.2 の名前の欄の記入、修理の型の条件 (smoke で 4 cell とも開始時より上げた公開の回数 ≥ 1、計数用 build がその回数を出すこと)、
  修理版 E + ro-gcflag・A_fix・A_stock の build と条件 gate と TRACE=0 の同一性、CCBench の修理の hunk が S2 の build で到達しないことの確認、L-w の f_T が無いときの択一 (推奨は D19 の下限)、
  M の範囲の確認 (待ちにしない)、ユーザーの確認 (node 時間 1.76〜2.02、削る順、本案の効果 E_sp(c) 対 A_fix を族に入れるか — 推奨は入れて m = 23)、発効の決定 (D 番号と草稿の SHA-256)。
  発効の後は S0-M (f_M,c、0.26〜0.31) と S2 の門 (0.37) → S2 本走 (1.13〜1.34)。C_now・H1・H2a・H5・H6・P5 の生成器を待たない。
