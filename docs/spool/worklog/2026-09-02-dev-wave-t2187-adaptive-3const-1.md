---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2187-adaptive-3const
seq: 1
title: [T-2187] adaptive backoff の律速は刻みでなく更新間隔だった — 窓を 4 倍にすると刻みの選択問題が消える (code + docs + insight、branch worktree-dev-wave-t2187-adaptive-3const、変異 5/5 KILLED)
---

## 本文

- **ユーザー依頼:** 3 定数 (刻み / 上限 / 更新間隔) を測り切り、probe と図まで repo へ入れる。
  「端で最良のまま報告しない」「1 ノード直列は禁止」「各ジョブの CPU 時間/経過を報告する
  (1.0 近傍なら設計ミス)」「全体の壁時計 60 分以内」が明示条件。
- **測定結果の要点は {{D:adaptive-backoff-update-window-is-the-binding-constant}} と
  {{D:tuned-adaptive-is-the-baseline-not-stock-adaptive}}、材料は
  `output/insights/2026-09-02_cicada-adaptive-three-constants.md`。**
  D1475 の「刻み 0.5 µs が最良」は更新間隔 10 µs の下でだけ成り立つ局所的事実だった。
- **壁時計の予算について。** 計算ノード時間は 3 段合計 32.5 分の見積もりに対し実測 39 分
  (段 1 が 16.2 分、段 2 が 8.5 分、段 3 が 11.9 分) で、**投入設計は予算内**。
  ただし全体の壁時計は約 1 時間 50 分かかった。超過分は計算ではなく、
  子の往復 (実装 2 本 + 修正 4 本) と、実データでしか出ない欠陥の発見・修正である。
- **キュー待ちの実測。** 11:27 投入の canary は 25 分待った (`Planned Start Time` は
  2 時間先を指していたが、backfill が効いて 1/5 で済んだ)。**planner の推定を待ち時間として
  報告しない。** 12:15 の本走投入時は待ちゼロで 7 ノードとも即開始した。
  クラスタの空きは短時間で大きく変動する。
- **`gen_M` / `gen_L` は 1 ノード job の逃げ道にならない。** 同じ 149 ノードを共有し、かつ
  `qsub -q gen_M` は `[BSV ERANGE] ... (njobs: 1 limit: 32)` で拒否される
  (1 リクエストあたり最低 32 ノードの多ノード用キュー)。gen_S は `(min,max) = 1,31`。
- **ノードは rep の軸に割った。** 1 ジョブが格子の全セル × 全 workload を回すので、
  セル同士の比較はノード内で閉じる。一処置一ノードの割付け (完全交絡) は採っていない。
  95% CI は 7 ノード分の反復から t 分布で出した。
- **各ジョブの CPU 時間 / 経過:** 段 1 が 15.73〜15.85、段 2 が 20.26〜20.47、
  段 3 が 20.14〜20.58。21 ジョブとも 1.0 近傍ではない。
- **セッション異常 (自分の欠陥) 4 件。**
  (1) 子 3 本の prompt すべてで、最初の非空行を `AGENTS.md` の単独段 dispatch 宣言の
  exact 形式にしていなかった。**fix 子だけが正しく fail-closed** して何も変更せず戻り、
  1 往復を失った。author 2 本は通常手順へ落ちて作業を続けたので**成功したように見えていた**。
  (2) 変異走の投入 2 分後に insight を新規作成し、`mutation_worktree.py` の
  「source 木の観測 bytes 不変」事後検査に掛かって rc=125 で全損した。
  **失敗は最後にしか出ない**ので、走行中は動いているように見える。
  (3) 待ち手を `nohup ... &` で背景 Bash に包み、待ち手でなく包み手の rc=0 を完了と
  誤読しかけた。生存は `pgrep -fa` で確かめ直した。
  (4) 待ち手の中で `ls <glob> | wc -l` を使い、該当 0 件のときの `ls` の rc=2 が
  `set -e` + `pipefail` に伝播して待ち手が即死した。`find` へ直した。
- **実データでしか出ない欠陥 2 件を図が踏んだ (単体 22 件緑をすり抜けた)。**
  (a) `grid` の座標が `(step_us, update_us)` で、probe が構造的に必須とする無 backoff セル
  (3 定数が stock 値で埋まる) が陽性対照と必ず衝突し、**正しい入力では常に落ちる**状態だった。
  (b) 実寸 6x5 格子でレイアウト検査が発火した。
  **根因はどちらも合成テストの格子が 1 workload 2 セルしかなく、実寸の注記密度を
  一度も踏まないこと。** 修正で合成入力を実寸 (6x5 + 無 backoff、スレッド 8 点) へ揃えた。
  親の brief が schema で「無 backoff セルを格子上どう扱うか」を書かなかったのが上流原因である。
- **段 5 実装子が手書きした unified diff の hunk header が本文と不整合だった** (`+18,14` に対し
  本文 12 行、`+11,35` に対し 33 行)。`patch --dry-run` が `malformed patch` で rc=2。
  子が自力で直したが、**手書き diff の行数整合はどの検査にも掛かっていない。**
- **`qsub -v` は値を shell へ通す。** `.pbs` の env リスト区切りをセミコロンにすると投入自体が
  壊れる (`sh: 1: <要素>: not found`)。**キュー枠を消費しない対照実験**で確定させた —
  存在しない jobscript を指定して `qsub -v FOO='a;b;c'` を投げると shell 分割が観測でき、
  `a+b+c` では観測されない。区切りを `+` へ直した。
- 成果物はすべて**認証されていない**。trace-disabled の性能測定のみで直列性の検査を
  通していない。variant 採用の根拠には使えない (規律 2)。正しさは [T-2189] の担当。

## 次の一手差分

### 完了

- [T-2187] adaptive parameter probe (`.py` / `.pbs` / patch) と新図種を Codex author を立てて
  repo へ取り込み、3 定数を 3 段格子で測り切った。B-10 形状格子用の thread scaling probe は
  本項の対象から外し {{T:thread-scaling-probe-into-repo}} へ分けた。
  remaining: none
  base: 185ab2b466c7689f9c571ce3a6890c2b20753811d156f18e9a219e826bd38e68

### 更新

- [T-2188] **P2・更新**: 刻みに対する応答の非単調性は、更新間隔 10 µs の下でだけ現れる
  ことが分かった (間隔を 40 µs 以上にすると刻みへの感度が 1.02〜1.37 倍まで潰れる)。
  残る課題は機序の直接確認で、`Backoff_` の時系列と勾配符号の的中率を記録して
  「窓が狭いと符号がノイズ支配」を実証する。
  base: 3b26cf95c97d5d8d92bc1ca38eb48a0d15e16b155b44185c28a9d5db971ddae3
- [T-2190] **P3・ユーザー裁定待ち**: 上流 CCBench への還元候補が
  「`kIncrBackoff` の既定値」から「**更新間隔 10 µs と刻み 100 µs の組み合わせ**」へ変わった。
  材料は `output/insights/2026-09-02_cicada-adaptive-three-constants.md` に更新。
  単一環境・正しさ未検査・機序未確定という限界は同文書に明記済み。
  base: 57ddbb56ddb079b71515d6e17d65a8e9c3905022f39f034d0385770d04cd7f1b

### 新規

- {{T:thread-scaling-probe-into-repo}} **P3・新規**: B-10 形状格子用の thread scaling probe
  (`thread_scaling_probe.py` / `.pbs`) は repo 外
  (`izanagi-job-evidence/thread-scaling/`) のままである。再現に job evidence directory が要る。
  必要になった時点で Codex author を立てて取り込む。
- {{T:adaptive-update-window-onset}} **P3・新規**: 更新間隔 10 µs と 40 µs の間で、
  刻みへの感度が潰れる立ち上がりがどこにあるかを測る。本測定の間隔格子は等比 4 倍刻みで、
  10 と 40 の間に点が無い。
- {{T:figure-fixtures-must-match-real-grid-size}} **P2・新規**: 作図スクリプトの合成 fixture が
  実寸より小さいとレイアウト検査と座標衝突を素通りする。`tools/plotting/` の既存図種にも
  同じ穴が無いかを棚卸しし、fixture を実寸へ揃える規約を `FIGURE_CONVENTIONS.md` へ足すかを判断する。
- {{T:handwritten-patch-hunk-header-check}} **P3・新規**: 手書き unified diff の hunk header と
  本文行数の整合を機械検査する。今回は親が偶然見つけたが、どの gate にも掛かっていない。
