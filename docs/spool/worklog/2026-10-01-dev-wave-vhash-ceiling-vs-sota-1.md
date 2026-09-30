---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-vhash-ceiling-vs-sota
seq: 1
title: [T-2962] VHash md_42: 利得の天井を修正済みの最良 Cicada と区間 GC を相手に測り、今の VHash を主論文の候補から外す推奨を出した (branch worktree-dev-wave-vhash-ceiling-vs-sota)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_42.txt` (と同 dir の `common.txt`、依頼元・land 調整役からの追記 = 1 job 5 分目安で多数並行)。一次資料 `output/insights/2026-09-30/vhash-ceiling-vs-sota/README.md`、設計判断 {{D:vhash-ceiling-drop-current-arms}}。
- 結論 (一次資料 §5): 規則が選んだ代表 P3 の前進 C の 30 秒比較の比 0.981、隣接点 P2 0.993 → 事前記述 §2 の「1.2 未満かつ機構は発火」で**今の VHash を主論文の候補から外す推奨**。長い読み手の費用 R−LR / R は P3 1.98・P2 1.56 と大きいが、今の腕 (hot v2・C-min) はそれに触れない。正しさは 7 腕とも巡回 0 (上限 indeterminate)、壊し正例は巡回 43 で成立。
- 事前登録: §1〜§4 を計測の投入前に commit (034b7a9af)。段 6 の焦点再レビューの指摘で「大きく伸ばせる残存費用」の基準を計測前に erratum 1 で固定 (97d745fb8、R−LR / R 予備中央値 ≥1.5)。
- md_37 (hot v2) が wave 中に main へ着地したので依頼どおり M の腕に入れた (段 4)。md_39 (E の修理) は未着地で、待機型 2 点は欠測。
- 棄却・限定した所見: 親の提案 P4 (R−LR を天井の上限とする) は段 3 の相談 2 本が反証 → 対照に格下げ。段 6 のレビュー RB-8 (作図の CI・重なり検査は重い) は作図規約で refuted。焦点再レビュー 2 巡目の予算 gate 周りの所見 (FR2-1〜5・M25 の正例) は、fix 子が 3 回とも既存 test の期待値の許可不足で止まり、land 調整役と合意して打ち切り、運用で担保した 4 点と R−LR の揃いの確認結果を一次資料 §8 に書いた (DW-O16 の 3 巡上限)。
- 親が driver を使わずに集計した所: driver の aggregate は 30 秒比較の両点を代表点の GC 間隔で組むので P2 (100 µs) の対が作れず停止、診断の集約も前進 C の parser が長い tx の行を要求して停止。事前記述 §4.2 どおり点ごとの間隔で組む集計を driver の関数のまま repo 外で行い、逐語を一次資料 `verbatim/` に置いた。作図器も同じ理由で 30 秒比較を描けず、予備の図も表の見出しが重なったので載せていない。
- セッション異常: (1) 利用上限で 20:5x〜21:43 と 01:2x〜03:11 に停止 (後者は land 調整役の指示)。(2) Lustre の `git worktree add` が EINTR で rc=128 (既存 branch 指定の再作成で成功)。(3) 実装子 B の初回が docs の所有外 (`tools/plotting/README.md`) で実装 0 のまま停止 → prompt を直して再投入。(4) smoke の dispatch 親が login の qstat / qsub の 30 秒 timeout で rc=16 (子は rc 0) → runbook §7.6 どおり orphan hold を外した。(5) 変異本走が 2 回止まった (subTest の失敗が pytest の FAILED 行に出ず抽出不能、親の import が固定木に `__pycache__` を作り復元検査が停止) → 3 回に分けて 26 本すべて登録どおり。(6) main の取り込みで、git の自動 merge が両側の追加を足した登録 2 file (materializer 登録簿と build authority の test) が「両親と異なる実装面」として Codex author を要求 → main 側の版を採り、Codex の登録差分を別 commit で当て直した。(7) fix 6 の子が指示に反して子 branch で自分で commit した (差分は照合済み)。
- 受入 1 回目 (2026-10-01 05:02〜05:31、tested main 0c56385b9、tested tip bbfc29a33、post-claim merge 後 801592bf0) は赤 1 件で停止: `orchestrator/tests/test_plot_b7_fixed5_regression.py::test_real_figure_passes_layout_check` (FigureLayoutError: text bbox overlap '+30.0000%' / 'no regression')。本 wave も post-claim merge の取り込み分 (docs・insight だけ) もこの test と `tools/plotting/plot_b7_fixed5_regression.py` に触れていない (最終変更は T-2610)。計算ノードで同 file を単独再走して 42 passed で再現せず → 非帰属と判定し、受入を取り直した (DW-O18)。
- 受入 2 回目 (05:36〜06:03、tested tip 7ccb516e7) は 3 shard とも赤 0 件だが、junit 合成の件数照合 (`junit-tests`) で受領証が出なかった。本 wave の test の `subTest` 15 個が suite の `tests` 属性を 15 増やしていた (本 wave に帰属)。Codex の fix (9ea29f9df、`subTest` を外すだけ) で直し、単独走 35 passed、変異 M0・M1・M2・M8 を新 commit で取り直して登録どおり。受入を取り直した。
- 子の工数 (Codex): plan 1・相談 2・author 3・review 2・焦点再レビュー 2・fix 7。Claude の下書き子 (変異 spec) 1・棚卸し子 1。
- 計算ノード: smoke 3 回 (約 1,100 s、うち 3 回目 2 job は Elapse 未記録で見積り)、本計測 予備 12 job 1,841 s・30 秒比較 12 job と診断 4 job 1,648 s・正しさ検査 2 job 98 s、焦点走 5 回、変異本走 3 回。合計 約 1.5 node 時間 (2 node 時間未満)。受入全走は別。

## 次の一手差分

### 完了

- [T-2962] VHash の「提案が Cicada に勝てる負荷」の第 2 段 (md_42) を測った。長い読み手の負荷で、今の VHash (hot 配置 v2・前進 C の最小前進) の 30 秒比較の比は修正済みの最良 Cicada に対して 0.93〜0.99 で、事前記述の基準により主論文の候補から外す推奨を出した ({{D:vhash-ceiling-drop-current-arms}})。
  remaining: none
  base: 3257a8b186e83a18b75fde9e47a956643f8f77344cbd2e0a4ccd28d6fd4cc6ec

### 新規

- {{T:vhash-long-reader-mechanism-ceiling}} **P2・新規**: VHash の次の判断。長い読み手が修正済みの最良 Cicada に課す費用は大きい (R−LR / R が P3 1.98・P2 1.56) が、今の VHash の腕はそれに触れない ({{D:vhash-ceiling-drop-current-arms}})。長い読み手そのものの版保持を攻める機構 (長い読み手の snapshot を RA の中で安全に進める仕組み、または lock の無い区間 GC) の天井を安く測るかを、論文方針 (大きな性能向上が出たものだけ) に照らしてユーザーが決める。根拠: `output/insights/2026-09-30/vhash-ceiling-vs-sota/README.md` §5 項 2・5。
- {{T:vhash-ceiling-driver-repair}} **P3・新規**: md_42 の driver `orchestrator/campaign/vhash_ceiling_vs_sota.py` の修理。aggregate が 30 秒比較の両点を代表点の GC 間隔で組むので点ごとの間隔にする、`aggregate_diagnostics` の前進 C の parser が長い tx の行を要求する、作図器が 30 秒比較を描けず表の見出しが重なる、予算 gate の残所見 (段 6 の FR2-1〜5・M25 の正例)。この wave では親が repo 外の集計と運用で代替した (一次資料 §8)。VHash を続けるときだけ行う。
