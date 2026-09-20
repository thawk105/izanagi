# 段 1 brief — [T-2802] s8b_holdout_admission の attempt ledger 回復 (二乗構造) の局所修正

作成 2026-09-20 07:14 JST (mtime)。着手 local main `b7f970dfa`、wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery` (branch `worktree-dev-wave-t2802-floor-attempt-recovery`)。

## 研究前進 (土台)

受入全走 (48 worker) の worker 時間 17,959 s のうち `test_s8b_floor_campaign.py` が 2,368 s (13 %、6 file 中最大) で、その主因が production `s8b_holdout_admission._floor_attempt_recovery_candidate_locked` の attempt ledger 回復 (attempt 数に対し二乗、98 attempt で `_canonical_floor_attempt_ledger_row` 9,604 回、profile 9.9 s 中 9.1 s、約 90 node × 5.8 s) である (insight `output/insights/2026-09-19/acceptance-worker-time-trim/README.md`、`verbatim/stage1-prof-summary.md`)。止めている研究 = 全 dev-wave の周回 (受入 wall 300 s 目標 T-2273、現状 shard-0 で 336〜481 s)。最小差分 = 候補関数の 1 呼び出し (root lock 保持中) の中で claim 射影 (claim 文書 + main ledger 行 + canonical key) を claim digest ごとに 1 回だけ導出して再利用する (per-call memo)。

## scope

- 対象: `orchestrator/campaign/s8b_holdout_admission.py` の `_floor_attempt_recovery_candidate_locked` (:5230-5311) と、それが marker / A 行ごとに呼ぶ `_canonical_floor_attempt_ledger_row` (:4670-4793、v1 経路は main ledger を全読し行ごとに `_claim_digest` = sha256) / `_canonical_measurement_generation_floor_attempt_ledger_row` (:4796-4937) / `_measurement_generation_main_ledger_row` (:4940-4952)。呼び出し元 `consume_attempt_ticket` (:4349-4392)、`floor_attempt_requires_cut6_replay` (:5327-5352) は attempt ごとに 1 回呼ぶ (これが二乗の外側)。
- test: `orchestrator/tests/test_s8b_holdout_admission.py` の cut6 群 (:2633-2765) に、複数 marker・複数 claim (複数 cell) で旧挙動と同じ受理・拒否になる正例と、memo が検査を飛ばしていないことを示す負例を足す。既存 test の期待値は変えない。
- A/B: T-2766 の launcher / 集計器 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/{run-measure.sh,run-series2.sh,...}`、逐語 `output/insights/2026-09-19/t2766-pairing-ab/probe-source.md`) を本 wave 用に改変 (A/B を env でなく worktree で切替、指標に floor file の worker 秒を追加)。job dir に置き repo へ入れない。Codex author。
- scope 外 (実装しない): 呼び出しを跨ぐ cache・module 変数・新 gate・新台帳・一般化、`floor_attempt_requires_cut6_replay` / `consume_attempt_ticket` の意味変更、`_real_output_snapshot` など他の律速、fixture 側の変更、受理集合を変えるあらゆる変更。

## 確定済みユーザー裁定 (引数 + 既裁定)

- Codex author (D95)。親は実装面を編集しない。
- 判定を緩める変更は不可 (規律 2)。受理集合 (拒否・受理の判定) を変えないことを変異 (正例・負例) で示す。
- 効果は受入 shard の同一 tip 型の対比較 (T-2766 の型、D2164): 同一 SHA の clean worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入、隣接対 3 組 (A,B / B,A / A,B)。n=1 の前後比較を効果と書かない (D2068「同一 tree 内で方式を交互に測った対比較に限る」、D2148)。
- 本題の局所修正だけ。

## 不変条件 (受理集合)

- (I1) 任意の root 状態 (marker 集合・attempt ledger・main ledger・claim 群) に対し、新旧の候補関数の (戻り値、例外の有無、例外 message) が一致する。
- (I2) 全 marker と全 A 行の検査 — unsafe entry、非 canonical file 名、identity 重複、marker なし A 行、A 行 ≠ marker、非 canonical bytes (`_read_canonical_document`)、claim / main ledger との完全再導出不一致 (MUT-A2) — は 1 件も落とさない。memo は「claim digest → claim 射影」だけで、marker の field を信用する経路を作らない。
- (I3) MUT-A6 (completed attempt の再発行拒否)、M+A+ 拒否、marker 不在時 None、target ≠ canonical の拒否は不変。
- (I4) memo の寿命は候補関数の 1 呼び出し (= root lock 保持中)。関数外へ持ち出さない。lock 外の読取りを増やさない。
- (I5) 書込み経路 (`_append_ledger`、`_write_exclusive`)、marker / ledger の書式・file 名は不変。`__all__`、公開 signature (`test_floor_recovery_query_signatures_expose_only_admission_verdict_inputs`) 不変。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) root lock 保持中は claim 文書と main ledger が不変である (main ledger の書き手 4 箇所 :1909/:2169/:3168/:3797 は全て `_locked` 内、claim は reservation 時に 1 回書く)。よって 1 呼び出し内で claim 射影を 1 回導出して再利用しても、marker ごとに再読した場合と同じ結果になる。
- (P2) 主要な二乗項は「marker / A 行ごとの claim 読取 + main ledger 全読 + main 行ごとの sha256」であり、これを claim digest ごと 1 回にすれば 9.1 s → 1 s 未満/test になる。残る O(N²) は marker file の読取 (k 件/呼) と A 行の dict 比較で、受理集合の意味上 (毎呼び出しで全 marker を検証) 落とせない。実測で確認する (段 5 login 単独走の durations、段 6 焦点走)。
- (P3) 誤り発生順序: claim 段階の拒否 (claim 読取不能・shape・key・digest・main 行数・main 不一致) は同 claim の最初の marker で発火し関数を抜ける。旧実装も同じ marker で同じ message を raise するので観測差なし。ただし target 導出 (:5236) が最初に走るので、target の claim に関する拒否は marker loop 前に出る (新旧同じ)。
- (P4) 効果の指標: 一次 = 3 shard の junit を合算した `test_s8b_floor_campaign.py` の testcase time 合計 (worker 秒)、二次 = shard-0 (最遅 shard) の W_max (記述的、floor node が律速 worker に居るとは限らない)。事前登録は段 4。

## DW-G05 (成果物影響)

放置時: 受入 worker 時間に ~520 s/走 (90 × 5.8、48w では比例せず) が残り、certified 選択・レポート・台帳の値・受理集合・参照は変わらない (性能のみ)。must-fix 基準は「受理集合が変わる」所見だけ。性能に関する所見は実測が無い限り nit。

## 成果物の形

1. 実装 commit (Codex author、production + test、`AI-Agent:` trailer)。
2. 変異 matrix (DW-M01 で事前登録、独立 clone、計算ノード): 判定を緩める変異 ≥ 5 (memo を marker field 信用に変える / A 行の marker 照合を飛ばす / 重複 identity 検査を外す / completed 拒否を外す / main ledger 不一致を無視) が KILLED、等価変異 1 が SURVIVED。
3. 焦点走 (変更 test file + consumer: `test_s8b_floor_campaign.py`、`test_s8b_oracle_n_pilot.py` 等、DW-O26 で参照関係から列挙)。
4. A/B 対比較: A = 着手 main `b7f970dfa` の clean worktree、B = 実装 tip の wave worktree。隣接対 3 組、直接投入。集計は Codex author の集計器。
5. insight `output/insights/2026-09-20/t2802-floor-attempt-recovery/README.md` (対表・変異台帳・逐語)、worklog fragment、decisions fragment (per-call memo を採り cross-call cache を採らない理由)。

## 分割方針・環境

- 段 2 plan 1 本 (read-only codex、`--reasoning`)、段 3 consult 1 本 2 レンズ (正しさ境界 = 受理集合 / 実効性・過剰)、段 5 author 1 本 (production + test)、A/B launcher・集計器の改変は別 author 1 本 (job dir)、段 6 review 2 本 + fix。
- 焦点走・変異・A/B は Pegasus 計算ノード (runbook `docs/pegasus-runbook.md`)。login は collect-only と `test_s8b_holdout_admission.py` 単独走 (数十秒) まで。
- 変更面の実アンカー: 上記 scope の行番号 (HEAD `b7f970dfa`)。
