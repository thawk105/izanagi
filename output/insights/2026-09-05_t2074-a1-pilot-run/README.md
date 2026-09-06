# [T-2074] A-1 pilot の実走 wave — 投入は driver の qstat 可視性判定で bench 前に失敗した (2026-09-05)

- `authority: none` / `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- 事前登録の正本: `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  (policy `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json`、study
  `paper-story-a1-20260901-balanced5-pilot-v1`)。本 wave はその値も規則も変えていない。
- 本文書は「何を投入し、何が起き、何が行われていないか」の記録である。**pilot の測定値は 1 点も無い。**

## 1. 依頼と実施範囲

依頼は「発効済みの A-1 pilot を固定 checkout から Pegasus 計算ノードへ workload 別に投入し、complete /
materialize / §5 の sizing まで行って記録する。driver と job body は編集しない ([T-2301] が編集中)」。
本 wave が実施したのは投入 1 回とその失敗の原因特定までで、bench・complete・materialize・sizing は
行われていない (§6)。

## 2. 投入前に実測した前提

| 項目 | 値 |
|---|---|
| 固定 checkout | `.claude/worktrees/dev-wave-t2074-a1-pilot-run`、HEAD 97ee3cd3a49ebc62914909012687bccd907ac4ae (= 着手時 local main) |
| CCBench submodule | 511c9538e4e8efa54b45cda62e72389ed3b706ec (policy の `canonical_pin` と一致) |
| 起動 gate | `tools/check_wave_startup.py --mode fresh --external-handoff <job dir>/handoff.md` rc=0 |
| 同名 wave / 編集面 | ListAgents・worktree 一覧・`dev-wave-jobs/` に同名なし。本 wave の新規 path は全 worktree に不在 |
| durable base | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement` は投入前に未存在 (先行 attempt なし) |
| gen_S の混雑 (13:10 JST) | QUE 168 / RUN 59 / HLD 20、自分の RUN 1 |

## 3. attempt-0001 の投入と結果

13:12 JST、固定 checkout を cwd にして login node で次を 1 回実行した。

```
python3 -B -m orchestrator.campaign.paper_story_a1_paired submit \
  --study-id paper-story-a1-20260901-balanced5-pilot-v1 \
  --expected-head 97ee3cd3a49ebc62914909012687bccd907ac4ae \
  --attempt-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement/attempt-0001
```

rc=2、stderr は次の 1 行。

```
paper-story A-1 refused: qsub request identity/visibility is indeterminate
```

attempt-0001 に残った証拠:

- `attempt-0001.intent.json` (group intent、`intent_sha256` 00682d45…)。
- `jobs/write-heavy/scheduler/qsub.stdout` = `Request 978193.nqsv submitted to queue: gen_S.`、
  `qsub.stderr` は空、`request-id` = `978193.nqsv`。`qstat-visibility.json` は無い。
- `jobs/balanced/scheduler/` と `jobs/read-heavy/scheduler/` は空 (qsub 未実行)。
- `receipts/submission-failure.json`: `status = not-successful`、
  `reason = scheduler-or-infrastructure-failure-before-bench`、jobs = write-heavy `indeterminate`
  (returncode 0、request_id null)、balanced / read-heavy `not-attempted`。
- `barrier/ready/`・`barrier/bench-start/` は空、`bench-go.json` は無い。

driver は `_run_submit_v3` で write-heavy の qsub を受理させ、request-id を書いた直後の
`_observe_qstat_visibility` で例外を出し、failure receipt を書いて止まった (受理済み request は
取り消さない設計)。

## 4. 原因 — driver の正規表現が NQSV の `qstat -f` 書式と一致しない

`_observe_qstat_visibility` は `qstat -f <request>` の出力から次の 2 行を要求する。

```
state : (?im)^\s*(?:job_state|State)\s*[:=]\s*([A-Za-z]+)\s*$
queue : (?im)^\s*(?:queue|Queue)\s*[:=]\s*(\S+)\s*$
```

同じ request に対する実機の出力 (13:14 JST、逐語、抜粋):

```
Request ID: 978193.nqsv
    Request Name = paper_story_a1_paired.sh
    Current State           = Queued
    Previous State          = Staging
    State Transition Time   = Sat Sep  5 13:12:21 2026
    State Transition Reason = STAGEIN_SUCCESS
    Queue = gen_S@nqsv (Execution Queue)
```

- 状態行は先頭語が `Current` なので `^\s*State` に一致せず、`state = None`。
- 待ち行列行は `\S+` が `gen_S@nqsv` を取った後に ` (Execution Queue)` が残り `\s*$` に一致せず、
  `queue = None`。
- したがって `state not in NQSV_QSTAT_STATES or queue != "gen_S"` が常に真で、**環境や混雑によらず
  決定的に落ちる。** `Request ID: 978193.nqsv` の行は一致するので `visible` 自体は真だった。

履歴:

- この関数は dd6ec73b9 (2026-08-29、`AI-Agent: product=codex; model=gpt-5.6-sol; role=author`) が
  driver に `submit` を持ち込んだときに入り、abff80d1b (2026-09-03、v3 の 3 job 分割) はそのまま
  v3 経路へ呼び出しを足した。本文は導入時から変わっていない。
- 8/25 の v2 受領証 (`…/dev-wave-paper-story-a1-paired-20260824/measurement/attempt-0003.submission.json`、
  `qstat_visibility.state = "STG"`) は c5978fe79 (2026-08-25「A-1 の PBS 観測を NQSV の実挙動へ
  合わせる」) 時点の投入器が作ったもので、本関数の実績ではない。**本関数が実機で通った記録は無い。**
- A-1 の tests (`orchestrator/tests/test_paper_story_a1_job_contract.py` ほか) は
  `job_state = F` / `exit_status = 0` の PBS-Pro 型 fixture で緑になっており、実機の書式を代表しない。
- 同じ regex 族は `_parse_qstat_terminal` (`complete` の `scheduler-end-state` 経路) にもある。
  NQSV は終了後の request を `qstat -f` に出さないので、生きるのは `request-disappeared-after-visibility`
  経路だけである。
- 同じ repo の `tools/pegasus/dispatch_compute.py` (`_scheduler_state`) は `State` と `Current State`
  の両方を解釈し、`orchestrator/tests/test_pegasus_dispatch_compute.py` は
  `Current State = Queued` → `QUE` の写像を fixture で固定している。A-1 driver はこれを使っていない。

## 5. 段 4 の裁定

- real: 上記の欠陥。scope 外: 修正には driver の編集が要り、依頼が禁じ、[T-2301] が同 file を編集中。
- **実装しない。** 修正は後続 wave (Codex author、[T-2301] 着地後) へ返す。方向は
  `dispatch_compute` の実証済み解釈へ揃え、実機 `qstat -f` の逐語を fixture にした正例・負例を
  同じ commit で足すこと。受理集合を広げる変更なので、状態語の閉集合 `NQSV_QSTAT_STATES` は
  実書式の語 (`Queued`、`Staging`、`Running` など) を既存の 3 文字語へ写像する形にし、未知語の
  拒否は残す。
- 規律 2 は触れていない (verifier・correctness gate は一切変えていない)。

## 6. 行われていないこと

- bench は 1 rep も走っていない。両 arm の build・verify も走っていない。
- `complete` / `materialize` は実行していない (入力が無い)。
- 事前登録 §4〜§5 の sizing (`tools/size_paper_story_a1_balanced.py` /
  `tools/verify_paper_story_a1_balanced_sizing.py`) は入力が無いので未実施。凍結値 (探索 20,000 /
  認証 100,000、n 28〜4096、root seed 原像) は 1 つも変えていない。
- §7.2 のとおり、差の符号・大きさについては何も述べない。

## 7. 受理された request 978193 の終端 — 本 wave 自身の untracked file で job body の preflight が拒否した

- 978193.nqsv は 13:18:37 JST に計算ノードで開始し、13:18:40 に終了した (Elapse 7 s)。
- `jobs/write-heavy/scheduler/job.stderr` の先頭行は `paper-story A-1 job refused: working tree is dirty`。
  job body は `compute-job-body-preflight` で、`PBS_O_WORKDIR` (= 投入元の固定 checkout) の
  `status --porcelain --untracked-files=all` (submodule は無視) が空であることを要求する。
- 空でなかったのは、**親が 13:17:39 に同じ worktree へ本 wave の failures fragment
  (`docs/spool/failures/2026-09-05-dev-wave-t2074-a1-pilot-run-2.md`、untracked) を書いていた**
  ためである。submit 時 (13:12) の tree は clean で、driver の login 側検査は通っていた。
- したがって、job body が group receipt を 60 秒待って prebench failure を書く経路は本 wave では
  観測していない。preflight のほうが先に落ちた。
- 運用上の含意: **投入元の固定 checkout は、3 job すべてが preflight を通るまで untracked を含めて
  1 byte も汚してはならない。** 混雑時は job の開始が数時間ずれるので、記録を書く wave worktree と
  投入元 checkout を分ける (投入専用の worktree を同じ SHA で別に持つ) のが安全である。
  本 wave は結果的に汚したが、attempt-0001 は §4 の欠陥で既に失敗しており、この汚れが測定を
  失わせたわけではない。F849 (実装子が編集中の worktree を cwd にした dispatch) と同じ族の再発として
  台帳へ追記した。

## 8. 次の wave の出発点

1. worklog fragment で採番する新規 T (A-1 driver の qstat 観測を実書式へ): `_observe_qstat_visibility` と
   `_parse_qstat_terminal` を実書式へ。[T-2301] 着地後、Codex author、編集面の重複検査。
2. fix 着地後に fresh wave で attempt-0002 を投入する。attempt-0001 は残す (`.intent.json`・
   `receipts/submission-failure.json`・`barrier/` が残るが、ready / bench-go / bench-start が無いので
   `_assert_no_prior_v3_bench_start` は拒否しない)。再走理由は §6.4 の
   `scheduler-or-infrastructure-failure-before-bench`。
3. 投入元 checkout は記録を書かない別 worktree にし、3 job の preflight 通過 (`jobs/<workload>/`
   に accounting file が増え、`job.stderr` に refuse が無い) を確かめるまで触らない。
4. 3 job の終端は request ID の行頭照合で待ち、`complete` → `materialize` → §4〜§5 の sizing へ進む。

## 9. 還元判断

CCBench 本体への還元候補は含まない。
