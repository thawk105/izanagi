# A-1 pilot attempt-0002 の投入 — F852 は閉じたが、group receipt の公開が Lustre で決定的に失敗した (2026-09-07)

- `authority: none` / `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- 事前登録の正本: `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  (policy `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json`、study
  `paper-story-a1-20260901-balanced5-pilot-v1`)。本 wave はその値も規則も変えていない。
- 直前の一次資料: `output/insights/2026-09-05_t2074-a1-pilot-run/README.md` (attempt-0001)、
  `output/insights/2026-09-07_t2349-a1-qstat-format/README.md` (F852 の修正)。
- 本文書は「何を投入し、何が起き、何が行われていないか」の記録である。**pilot の測定値は 1 点も無い。**

## 1. 依頼と実施範囲

依頼は「A-1 pilot の attempt-0002 を fresh wave で投入する。投入元 checkout は記録を書かない別
worktree にし、3 job の preflight 通過を投入前に実測で示す。生存判定は `qstat` 一覧の行頭 ID 照合で行う。
測定・sizing・本走 policy の凍結は attempt-0002 の結果を見てから。本題の投入と記録だけ」。

実施したのは投入 1 回、その結果の観測、原因の実測、本記録である。bench・`complete`・`materialize`・
sizing は行っていない (§7)。driver・job body・policy・fixture は 1 byte も編集していない。

## 2. 投入前に実測した前提

| 項目 | 値 |
|---|---|
| 着手時 local main | `cf4273f5671ecda87c6f1b76148df239ce043ead` |
| 記録用 worktree | `.claude/worktrees/dev-wave-a1-pilot-attempt2` (branch `worktree-dev-wave-a1-pilot-attempt2`) |
| 投入元 worktree (記録を書かない) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-pilot-attempt2/submit-tree` (detached、同 SHA) |
| [T-2349] の着地 | `a18501d6a` / `d5ccda357` はいずれも local main の祖先 (`git merge-base --is-ancestor` rc=0) |
| 事前登録 README の sha256 | `8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc` = policy `preregistration.sha256` |
| CCBench submodule | `511c9538e4e8efa54b45cda62e72389ed3b706ec` = policy `canonical_pin` = driver `CANONICAL_CCBENCH_OID` |
| policy sha256 | `ed1c942f9d4bc24ab1bc6106caea672262c8634d32b022eca75b125811f7b825` |
| 起動 gate | `tools/check_wave_startup.py --mode fresh --external-handoff <job dir>/handoff.md` rc=0 |
| 同名 wave / 編集面 | ListAgents・`git worktree list`・`dev-wave-jobs/` に同名なし。本 wave の新規 path は全 worktree に不在 |
| durable base の先行状態 | `attempt-0001` と `attempt-0001.intent.json` のみ。`barrier/ready`・`barrier/bench-start` は空、`bench-go.json` 不在 |
| gen_S の混雑 (18:41 JST) | TOT 174 / QUE 86 / RUN 44 / HLD 44 |

投入前に、driver の login 側 gate を production 関数のまま順に呼んで全通過を確かめた
(`_require_policy_ready_for_execution`、`_assert_submit_a1_noncertifying_markers`、HEAD 一致、
`_parent_porcelain` = 空、`_assert_ccbench_acceptance(boundary="login-submit")`、
`_validate_attempt_root`、`_assert_no_prior_v3_bench_start`、`_canonical_qsub_contract`)。
`_assert_no_prior_v3_bench_start` が attempt-0001 を拒否しないことは、想定ではなく実行で確かめている。

## 3. F852 は実機で閉じている — 投入前に生きた request で 1 回通した

本番投入の前に、捨て request `981329.nqsv` を gen_S へ 1 本投げ、その生きた `qstat -f` 出力に対して
production の `_observe_qstat_visibility` を呼んだ。

実機出力 (逐語、抜粋):

```
Request ID: 981329.nqsv
    Request Name = qstat_probe.sh
    Current State           = Running
    Previous State          = Pre-running
    Queue = gen_S@nqsv (Execution Queue)
```

判定結果:

```
{'request_id': '981329.nqsv', 'visible': True, 'state': 'RUN', 'queue': 'gen_S',
 'observed_epoch': 1788775311}
```

F852 の時点ではこの入力に対し `state = None` / `queue = None` となって例外が出ていた。
本番の 3 request でも同じ関数が `visible: true` / `state: "QUE"` / `queue: "gen_S"` を書いており
(`jobs/<workload>/scheduler/qstat-visibility.json`)、**F852 は再発していない。**

## 4. attempt-0002 の投入と結果

19:03 JST、投入元 submit-tree を cwd にして login node で 1 回実行した。

```
python3 -B -m orchestrator.campaign.paper_story_a1_paired submit \
  --study-id paper-story-a1-20260901-balanced5-pilot-v1 \
  --expected-head cf4273f5671ecda87c6f1b76148df239ce043ead \
  --attempt-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement/attempt-0002
```

rc=2、stderr は次の 1 行。

```
paper-story A-1 refused: no-replace submission receipt publish failed: Invalid argument
```

attempt-0002 に残った証拠:

- `attempt-0002.intent.json` (group intent、`intent_sha256` b3768c22…)。
- 3 workload すべての `jobs/<workload>/scheduler/` に `qsub.stdout`・空の `qsub.stderr`・
  `request-id`・`qstat-visibility.json`。request は write-heavy `981331.nqsv`、
  balanced `981332.nqsv`、read-heavy `981333.nqsv`。
- `receipts/submission-failure.json`: `status = not-successful`、
  `reason = scheduler-or-infrastructure-failure-before-bench`、jobs は 3 本とも
  `accepted` (returncode 0、request_id あり)。
- `receipts/submission.json` (group receipt) は**無い**。
- `barrier/ready`・`barrier/bench-start` は空、`bench-go.json` は無い。

つまり **3 本の qsub はすべて受理され、qstat 可視性判定も 3 本とも通り、group receipt を公開する
最後の 1 手だけが落ちた。**

## 5. 原因 — Lustre は `renameat2(RENAME_NOREPLACE)` を実装していない

`_publish_submission_receipt` は staging file を書いてから
`_renameat2_directory(staging, path, _RENAME_NOREPLACE)` で完成名へ移す。この呼び出しが
`EINVAL` を返した。

durable base (policy `execution.durable_measurement_base` が固定する `/work` 配下) の file system は
`stat -f` で `lustre` である。同じ directory で実測した結果:

| 操作 | 結果 |
|---|---|
| `renameat2(..., RENAME_NOREPLACE)` → 空き先 | rc=-1、errno=22 (Invalid argument) |
| `renameat2(..., flags=0)` → 空き先 | rc=0 |
| `os.link()` → 空き先 | 成功 (公開できる) |
| `os.link()` → 既存先 | errno=17 (File exists) |
| `os.rename()` → 既存先 | 黙って上書きする |

比較のため tmpfs (`/tmp`) では `renameat2(..., RENAME_NOREPLACE)` が rc=0 で成功する。
すなわち **flag 自体は kernel にあるが、Lustre がこの flag を受け付けない。**
durable base は policy が Lustre 上に固定しているので、この経路は混雑や時刻によらず決定的に落ちる。

**この経路が実機で通った記録は無い。** attempt-0001 は 1 段手前の qstat 可視性判定 (F852) で
落ちていたため、group receipt の公開まで到達したのは本 attempt が初めてである。F852 と同じ型
—「実機で一度も通していない手順を投入 gate に置いた」— の再発であり、失敗した層だけが違う。

### 同じ driver は、別の経路では既にこの問題を解いている

`_observe_materialization_publish` は、公開先と同じ file system で `RENAME_NOREPLACE` を実際に 1 回
試し、`EINVAL` なら `PUBLISH_EINVAL_FALLBACK` を選ぶ。つまり「この flag が使えない file system が
ある」ことは driver 内で既に認識され、materialize 側には機構がある。**submission receipt の公開だけが
その機構を持たない。**

ただし materialize 側の fallback は driver 自身が
"Fallback publication is not atomic no-replace against a non-cooperating writer." と書いているとおり、
排他性を落とす。あちらは **directory** を公開するため `os.link()` を使えないという事情がある。
submission receipt は **file** なので、§5 の実測どおり `os.link()` が空き先に成功し既存先に `EEXIST` を
返す — 排他性を落とさずに Lustre で公開できる。修正の方向はこの差に依存する。

## 6. 3 job は body preflight を通過し、bench には 1 rep も入っていない

3 本とも計算ノードで起動し、`job-terminal.json` を残して終わった。write-heavy (`981331.nqsv`) の例:

- `expected_head` = `observed_head` = `cf4273f5671ecda87c6f1b76148df239ce043ead`
- `porcelain` = `""` (投入元 submit-tree は job 実行時点でも clean だった)
- `pbs_o_workdir` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-pilot-attempt2/submit-tree`
- `status` = `failed`、`driver_rc` = 125、`shell_rc` = 2
- `job.stderr` の先頭行 = `paper-story A-1 job refused: acquisition receipt did not appear within 60 seconds`

**この拒否は preflight の後段にある。** HEAD 一致と working tree の clean は job body 内で検査され、
その結果が terminal に記録されている — つまり `compute-job-body-preflight` は 3 本とも通り、
その後に group receipt を 60 秒待って現れず、fail-closed で bench に入らず終わった。
attempt-0001 では投入元 worktree を親自身が汚したために preflight で落ちており、この経路は
観測できていなかった。**記録を書く worktree と投入元 checkout を分ける運用は、実測で効いている。**

barrier に ready は 1 つも書かれておらず、arm の build も verify も走っていない。

## 7. 段 4 の裁定

- **real:** §5 の欠陥。`_publish_submission_receipt` は Lustre 上の durable base で決定的に失敗し、
  A-1 の group 投入は現行コードでは成立しない。
- **scope 外 — 実装しない。** 依頼は「本題の投入と記録だけ」で、修正は driver の実装面 (D95 決定 2) に
  当たる。加えて公開の排他性という正しさ側の性質に触れるため、方向の決定はユーザー裁定に返す。
  attempt-0001 が F852 を修正せず [T-2349] へ返したのと同じ扱いである。
- 規律 2 は触れていない。verifier・correctness gate は 1 行も変えておらず、
  受理集合を広げる変更も行っていない。失敗した投入を成功として記録していない。
- **公開の受理集合を広げる修正を無検討で採らないこと。** 素の rename への退避は既存先を黙って
  上書きするので、「submission receipt は一度しか公開されない」という fail-closed 性を落とす。

### ユーザーへ返す裁定 — 公開機構をどう直すか

| 案 | 排他性 | Lustre での可否 | 備考 |
|---|---|---|---|
| A. `os.link()` + staging の unlink | 保つ (既存先は `EEXIST`) | 実測で可 | file の公開に限る。§5 で測定済み |
| B. materialize と同じ probe + `EINVAL` fallback | 落ちる (非協調の書き手に対して非原子) | 可 | driver 内に前例があるが、directory 公開向けの妥協 |
| C. 完成名を `O_EXCL` で直接開いて書く | 保つ | 可 | staging を経ないので、部分書き込みが完成名に見える窓ができる |

親の推奨は **A** である。排他性を落とさず、実測済みで、materialize 側の妥協を submission receipt へ
持ち込まない。ただし採否と、`complete` / `materialize` の同族経路をどこまで同じ commit で直すかは
ユーザー裁定に属する。実装は Codex `role=author` が持つ。

## 8. 行われていないこと

- bench は 1 rep も走っていない。両 arm の build・verify も走っていない。
- `complete` / `materialize` は実行していない (group receipt が無いので入力が無い)。
- 事前登録 §4〜§5 の sizing は入力が無いので未実施。凍結値は 1 つも変えていない。
- 差の符号・大きさについては何も述べない。
- attempt-0003 は投入していない。修正が着地するまで投入しても同じ場所で落ちる。

## 9. 次の wave の出発点

1. §7 の裁定を受けて、`_publish_submission_receipt` の公開機構を Lustre で成立する形へ直す
   (Codex author、編集面の重複検査、正例・負例を同じ commit で足す)。
   `complete` の completion receipt 公開と materialize 側も同族として棚卸しする。
2. 修正着地後に fresh wave で attempt-0003 を投入する。attempt-0002 は残す
   (`ready` / `bench-go` / `bench-start` がいずれも無いので `_assert_no_prior_v3_bench_start` は
   拒否しない)。再走理由は attempt-0002 の failure receipt が記録した
   `scheduler-or-infrastructure-failure-before-bench`。
3. 投入元 checkout を記録用と分ける運用は維持する (§6 で効いていることを実測した)。
4. 3 job の終端は `qstat` 一覧の行頭 ID 照合で待つ。`qstat -f` は終了済み request でも rc=0 を返す。

## 10. 還元判断

CCBench 本体への還元候補は含まない。
