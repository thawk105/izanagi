---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t2074-a1-pilot-run
seq: 1
title: [T-2074] A-1 pilot を固定 checkout から投入したが、driver の qstat 可視性判定が NQSV の書式と合わず bench 前に group 投入が失敗した — 修正は driver 編集を要し本 wave の scope 外 (docs のみ、branch worktree-dev-wave-t2074-a1-pilot-run、実装面の差分 0)
---

## 本文

- **投入は 1 回行い、bench には入っていない。** local main 97ee3cd3a から fresh worktree を作り、CCBench
  submodule を canonical pin 511c9538 で初期化し、起動 gate (fresh) rc=0 を得てから、13:12 JST に
  `submit --study-id paper-story-a1-20260901-balanced5-pilot-v1 --expected-head 97ee3cd3a… --attempt-root
  <durable base>/attempt-0001` を login node で実行した。rc=2、stderr は `paper-story A-1 refused: qsub
  request identity/visibility is indeterminate`。driver / job body / policy / 事前登録本文は 1 byte も
  編集していない。
- **write-heavy の qsub は受理され (request 978193.nqsv、gen_S)、request-id まで書けた直後に
  `_observe_qstat_visibility` が拒否した。** balanced / read-heavy は未投入。attempt-0001 には
  `receipts/submission-failure.json` (`reason = scheduler-or-infrastructure-failure-before-bench`、
  write-heavy `indeterminate`、残り 2 つ `not-attempted`) が残る。逐語と時刻は
  `output/insights/2026-09-05_t2074-a1-pilot-run/README.md`。
- **原因は決定的で、環境や混雑によらない。** driver は `qstat -f` の出力に `State = <状態>` と
  `Queue = gen_S` の行を要求するが、この機体の NQSV は `Current State           = Queued` と
  `Queue = gen_S@nqsv (Execution Queue)` を出す。状態行は先頭語が `Current` なので一致せず、
  待ち行列行は `@nqsv (Execution Queue)` の後続で一致しない。同じ regex 族は `complete` の
  `scheduler-end-state` 経路 (`_parse_qstat_terminal`) にもある。
- **この判定は dd6ec73b9 (2026-08-29、Codex author) が driver に `submit` を持ち込んだときに入り、
  以後どの study でも実機で通っていない。** 8/25 の v2 受領証 (attempt-0003、state `STG`) は
  それ以前の投入器が作ったもので、本関数の実績ではない。A-1 の tests は `job_state = F` /
  `exit_status = 0` の PBS-Pro 型 fixture で緑になっており、実機の書式を代表していない。同じ repo の
  `tools/pegasus/dispatch_compute.py` は `Current State` を解釈する実証済みの parser を持つ。
  失敗の型は {{F:a1-qstat-visibility-regex-never-live-tested}}。
- **段 4 の裁定: 実装しない。** 依頼が driver と job body の編集を禁じ、稼働中の [T-2301] が同 file を
  編集中である。修正は {{T:a1-driver-qstat-observation-fix}} (Codex author) へ返し、着地後に fresh wave
  で attempt-0002 として投入し直す。attempt-0001 は bench-start に達していないので、D1295 決定 7 の
  group 再投入禁止には当たらない (driver の `_assert_no_prior_v3_bench_start` は ready / bench-go の
  無い prior attempt を拒否しない)。再走理由は §6.4 の `scheduler-or-infrastructure-failure-before-bench`
  に該当する。
- **pilot の測定と反復数の探索は行われていない。** 事前登録 §4〜§5 の sizing は入力が無いので未実施であり、
  §7.2 のとおり差の符号・大きさについて何も述べない。§5 の凍結値 (探索 20,000 / 認証 100,000、
  n 28〜4096、root seed 原像) は本 wave で 1 つも変えていない。
- **受理された request 978193 は 13:18:37 JST に開始し 7 秒で `working tree is dirty` により job body の
  preflight で止まった。** 汚れの正体は、親が 13:17 に投入元の固定 checkout へ書いた本 wave の failures
  fragment (untracked) である。job body は `PBS_O_WORKDIR` に untracked を含む clean を要求する。
  attempt-0001 は既に §4 の欠陥で失敗していたので測定は失っていないが、混雑で job の開始が数時間
  ずれる環境では、**投入元 checkout は 3 job が preflight を通るまで 1 byte も汚せない**。次の wave は
  記録を書く worktree と投入専用 worktree を分ける (insight README §7〜§8)。
- 実装面の差分は 0、Codex 子は起動していない (軽量版、段 2・3・5・6 の子ゼロ)。

## 次の一手差分

### 更新

- [T-2074] **P1・実走 1 回目 (2026-09-05、attempt-0001) は driver の qstat 可視性判定の欠陥で bench 前に失敗 → {{T:a1-driver-qstat-observation-fix}} の着地待ち**:
  fix 着地後に fresh wave で attempt-0002 を投入する。pilot の測定・sizing・本走 policy の凍結・本走は
  未着手のまま。
  base: 2d0a18a21f2f0502f78c8be78d5bec1b0c1ad009f034faf60ccb45e0ba26cd1e

### 新規

- {{T:a1-driver-qstat-observation-fix}} **P1・新規 (2026-09-05 実測、{{F:a1-qstat-visibility-regex-never-live-tested}})**:
  `orchestrator/campaign/paper_story_a1_paired.py` の `_observe_qstat_visibility` と `_parse_qstat_terminal`
  を NQSV の実書式 (`Current State = Queued` / `Queue = gen_S@nqsv (Execution Queue)`、終了後は
  `qstat -f` に出ない) へ合わせる。`tools/pegasus/dispatch_compute.py` の `Current State` 解釈へ揃え、
  実機 `qstat -f` の逐語を fixture にした正例・負例を同じ commit で足す。Codex author。[T-2301]
  (同 file の `submit --study-id` 既定撤去) の着地後に着手し、編集面の重複検査を行う。受理集合を
  広げる方向 (実機の状態を受理) なので、状態語の閉集合 `NQSV_QSTAT_STATES` は実書式の語へ写像する
  形にし、未知語の拒否は残す。
  着地後の再投入 (attempt-0002) は fresh wave で行い、投入元 checkout は記録を書かない別 worktree にする。
