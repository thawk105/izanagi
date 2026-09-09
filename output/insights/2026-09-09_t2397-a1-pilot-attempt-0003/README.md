# A-1 pilot attempt-0003 の投入 — F870 は閉じ 3 job は preflight を通ったが、条件関門が 2 つの独立した理由で測定を拒否した (2026-09-09)

- `authority: none` / `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- 事前登録の正本: `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  (policy `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json`、study
  `paper-story-a1-20260901-balanced5-pilot-v1`)。本 wave はその値も規則も変えていない。
- 直前の一次資料: `output/insights/2026-09-07_a1-pilot-attempt-0002/README.md` (attempt-0002)、
  `output/insights/2026-09-08_t2396-a1-receipt-oslink/README.md` (F870 の修正)。
- 本文書は「何を投入し、何が起き、何が行われていないか」の記録である。**pilot の測定値は 1 点も無い。**

## 1. 依頼と実施範囲

依頼は「A-1 pilot の attempt-0003 を fresh wave で投入する。attempt-0002 は残す。投入元 checkout は
記録を書かない別 worktree にし、3 job の preflight 通過を確かめてから bench へ入れる。着手直前の
local main から fresh worktree。規律 2 を緩めない。本題の投入と記録だけ。仮想リスク向けの gate・
検査・台帳・一般化の追加は scope 外」。

実施したのは投入 1 回、その結果の観測、止まった層の実測、本記録である。driver・job body・policy・
fixture は 1 byte も編集していない。実装面の差分はゼロである。

## 2. 投入前に実測した前提

| 項目 | 値 |
|---|---|
| 着手時 local main | `cbcdb6c91bd2eced76bd6a82650204c357c1b299` |
| 記録用 worktree | `.claude/worktrees/dev-wave-t2397-a1-pilot-attempt3` (branch `worktree-dev-wave-t2397-a1-pilot-attempt3`、lock 済み) |
| 投入元 worktree (記録を書かない) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-pilot-attempt3/submit-tree` (detached、同 SHA) |
| [T-2396] の着地 | `72c9e5a7c` / `2c1127c94` / `b7b39dece` はいずれも local main の祖先 (`git merge-base --is-ancestor` rc=0) |
| driver の公開機構 | `orchestrator/campaign/paper_story_a1_paired.py:917` が `os.link(staging, path, follow_symlinks=False)` を呼ぶ |
| policy sha256 | `ed1c942f9d4bc24ab1bc6106caea672262c8634d32b022eca75b125811f7b825` |
| CCBench submodule (submit-tree) | `511c9538e4e8efa54b45cda62e72389ed3b706ec` = policy `canonical_pin`、tracked clean |
| 起動 gate | `tools/check_wave_startup.py --mode fresh --external-handoff <job dir>/handoff.md` rc=0 |
| 同名 wave / 編集面 | ListAgents・`git worktree list`・`dev-wave-jobs/` に同名なし |
| durable base の先行状態 | attempt-0001 / attempt-0002 とその intent の 4 件。`barrier/ready`・`barrier/bench-start` は両方とも空、`bench-go.json` は不在 |
| gen_S の混雑 (07:15 JST) | TOT 24 / QUE 0 / RUN 11 / HLD 13 (attempt-0002 時は TOT 174 / QUE 86) |

### 2.1 公開機構を durable base で 1 回試した

durable base (policy `execution.durable_measurement_base`、`stat -f` の fstype = `lustre`) の直下に
scratch を作り、production が使う 3 操作を 1 回ずつ実行して撤去した。base の一覧は probe の前後で
同一である。

| 操作 | 結果 |
|---|---|
| `renameat2(..., RENAME_NOREPLACE)` → 空き先 | rc=-1、errno=22 (EINVAL)。**F870 は今も再現する** |
| `os.link()` → 空き先 | 成功 |
| `os.link()` → 既存先 | errno=17 (EEXIST)。排他性は落ちていない |
| staging を unlink した後の宛先 bytes | 不変 |

**この probe が示すのは、その directory・その時点でこの 3 操作がこの結果を返したことだけである。**

### 2.2 login 側の gate を production 関数のまま順に通した

投入元 submit-tree を cwd にして、`run_submit` / `_run_submit_v3` が最初の `qsub` までに呼ぶ関数を
同じ順で実行した。何も書いていない。

`_repo_root`、`_load_policy_for_study`、`_require_policy_ready_for_execution`、
`_assert_submit_a1_noncertifying_markers`、HEAD 一致、`_parent_porcelain` (空)、
`_assert_ccbench_acceptance(boundary="login-submit")`、`_durable_measurement_base`、
`_validate_attempt_root`、証拠 namespace の空き検査、`_assert_no_prior_v3_bench_start`、
`_v3_group_intent` — 全通過。試算した group intent の sha256 は
`ea7104d8deb318066a6e66146861d2003c162ecd94c304f752358f8552c9d62a` で、**実際の投入が公開した
受領証の `intent_sha256` と一致した。**

`_assert_no_prior_v3_bench_start` が attempt-0001 / attempt-0002 を拒否しないことは、想定ではなく
実行で確かめている。

## 3. 段 3 の敵対相談と段 4 の裁定

read-only の codex 1 本に「受領証の公開から先に、実機で一度も実行されておらず、かつ決定的に失敗する
欠陥は残っていない」という親の provisional 命題を攻撃させた。子は「狭義の必ず失敗する欠陥は静的検査
では発見できなかった。命題は反証できない」と書いたうえで、条件付き競合 4 件を理由に停止を勧告した。

親の裁定は次のとおり。**投入する。**

| 所見 | 裁定 |
|---|---|
| 60 秒の受領証待機に時間保証がない | real (コード上の事実)、止める理由にならない。attempt-0002 の成果物から実測すると、3 本の qsub は約 2 秒で完了し (可視性 epoch 1788775386/386/387)、job が待ち始めたのはその 14〜21 秒後だった。受領証は job が待ち始める 10〜12 秒前に公開されていた。しかもこれは QUE 86 の混雑下の値である |
| job 本体の一度限りの `qstat` が Pre-running を観測して落ちうる | **refuted (実機で実測)。**§3.1 |
| `_exclusive_write` の部分公開競合 (`ready` / `bench-go.json`) | real、scope 外。実装面で Codex `role=author` が要る。T-2396 の段 6 が同族の所見を既に裁定へ返している。発火しても fail-closed で abort するだけで、誤った測定値を生まない |
| barrier timeout と残 walltime の契約不足 | real (コード上の事実)、止める理由にならない。attempt-0002 の実測で 3 job の起動差は約 8 秒 (QUE 86 の混雑下)、walltime は 6 時間 |
| F870 と同型の決定的 EINVAL は残っていない | 親の probe (§2.1) と一致。止めない |

相談子が停止根拠にした 4 件のうち、**実測で閉じられる型は 1 件だけで、それは実測して閉じた。**
残る 3 件は条件付きかつ fail-closed で、閉じるには実装が要る — ユーザーが scope 外と明示した領域である。

### 3.1 捨て job で `qstat` の遷移状態を実測した

投入前に、捨て request `986701.nqsv` を gen_S へ 1 本投げ、**job の shell が動いている時点**の生の
`qstat -f` を採取した。実機出力 (逐語、抜粋):

```
Request ID: 986701.nqsv
    Current State           = Running
    Previous State          = Pre-running
    State Transition Reason = PRERUN_SUCCESS
    Started Request Time = Wed Sep  9 07:43:37 2026
  Execution Hosts(JSVNO):
    bnode010(10)
```

job body が使う parser を `tools/pegasus/paper_story_a1_paired.sh` から逐語で切り出し、同じ入力へ
適用すると `bnode010` と `1788907417` を返した。`ASSIGNED_HOST == unavailable` にも
`SCHEDULER_STARTED_EPOCH == unavailable` にもならず、`hostname` も `bnode010` で一致するため
host 照合の refuse にも当たらない。5 秒後の再観測も同一だった。

## 4. attempt-0003 の投入と結果

07:47 JST、投入元 submit-tree を cwd にして login node で 1 回実行した。

```
python3 -B -m orchestrator.campaign.paper_story_a1_paired submit \
  --study-id paper-story-a1-20260901-balanced5-pilot-v1 \
  --expected-head cbcdb6c91bd2eced76bd6a82650204c357c1b299 \
  --attempt-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement/attempt-0003
```

**rc=0。stderr は空。** attempt-0003 に残った証拠:

- `receipts/submission.json` (11854 bytes、schema `paper-story-a1-paired-group-submission/v1`、
  route `direct-qsub-workload-fanout`、`intent_sha256` `ea7104d8…`)。
  **`receipts/submission-failure.json` は無い。**
- 3 workload すべての `jobs/<workload>/scheduler/` に `qsub.stdout`・空の `qsub.stderr`・
  `request-id`・`qstat-visibility.json`。request は write-heavy `986702.nqsv`、
  balanced `986703.nqsv`、read-heavy `986704.nqsv`。可視性はいずれも epoch 1788907627 で
  `visible: true` / `state: "QUE"` / `queue: "gen_S"`。

**F870 は実機で閉じた。** A-1 pilot で group 受領証が公開されたのはこれが初めてである。

## 5. 3 job は preflight を通過し、受領証も取得し、bench には 1 rep も入っていない

3 本とも計算ノードで起動し、`job-terminal.json` を残して終わった。

| workload | request | `expected_head == observed_head` | `porcelain` | `driver_rc` | `shell_rc` | terminal epoch |
|---|---|---|---|---|---|---|
| write-heavy | `0:986702.nqsv` | true | `""` | 2 | 2 | 1788907670 |
| balanced | `0:986703.nqsv` | true | `""` | 2 | 2 | 1788907665 |
| read-heavy | `0:986704.nqsv` | true | `""` | 2 | 2 | 1788907665 |

write-heavy の scheduler 記録は `Started Request Time: Wed Sep 9 07:47:14 2026`、
`Ended Request Time: Wed Sep 9 07:47:50 2026`、`Elapse: 40S` である。

**受領証の 60 秒待機は待機として一度も発火しなかった。** 受領証は 07:47:07〜08 に公開され、job が
起動したのは 07:47:14 である。3 job は待たずに受領証を取得し、preflight を通り、gflags と glog の
依存 staging まで完了している (`raw/dependency-staging/` に両者の configure・build・install の
stdout / stderr が揃っており、gflags の configure は
`Build files have been written to: /scr/0_986702.nqsv.attempt-0003.write-heavy.…/gflags-build` で
終わっている)。

`barrier/ready` と `barrier/bench-start` はいずれも空、`bench-go.json` は不在。**build も verify も
bench も 1 つも走っていない。**

## 6. 止まった層 — 条件関門が 2 つの独立した理由で拒否した

3 job の `job.stderr` の先頭行は 3 本とも同一で、逐語で次のとおりである。

```
paper-story A-1 refused: v3 BACKOFF_FIXED condition gate rejected measurement: supply-effectuation:configure-failed,supply-effectuation:configure-failed,runtime-meaning:materialized-decoder-invalid,runtime-meaning:materialized-branch-invalid
```

拒否は `_require_v3_backoff_fixed_condition_gate`
(`orchestrator/campaign/paper_story_a1_paired.py:6704`) から出ており、campaign の実行 (`bench`) の
手前にある。**関門は fail-closed で正しく働いている。緩めていない。**

関門は理由 code だけを拒否文へ載せ、arm record が持つ detail を捨てる。detail を読むため、
F855 の恒久対応が定めた形 (「`_require_condition_gate` と同じ関数列を呼んで supply / meaning の
全記録を出す probe」) の probe job を gen_S へ 1 本投げた (`986707.nqsv`、host は計算ノード、
site = `PEGASUS_COMPUTE`、cc = `gcc` / cxx = `g++`、cmake = `/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/cmake`)。

### 6.1 supply-effectuation が赤な理由 — 関門の configure に依存の供給が届いていない

probe が取った detail (逐語、改行は原文のまま):

```
process returned rc=1; stderr=b'cmake/data/share/cmake-3.25/Modules/FindPackageHandleStandardArgs.cmake:230 (message):\n  Could NOT find gflags (missing: gflags_LIBRARY_FILE gflags_INCLUDE_DIR)\nCall Stack (most recent call first):\n  /system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/python3.9/lib/python3.9/site-packages/cmake/data/share/cmake-3.25/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)\n  cmake/Findgflags.cmake:9 (find_package_handle_standard_args)\n  CMakeLists.txt:33 (find_package)\n\n\n'
```

BACKOFF_FIXED の 2 値 (`10` と `-1`) の両方で同じ detail が出る。

同じ probe が `captured.configure_args:` を `()` と印字した。A-1 の呼び出しは
`condition_meaning_gate.capture_define_inputs(source_root, stock_root=stock_root)`
(`paper_story_a1_paired.py:6721`) で、**configure 引数を 1 つも渡していない。**
同じ関門に届く他の production 経路は渡している —
`backoff_sweep.py:107` は `configure_args=configure_args` を渡し、
`screening_driver.py:189-196` は base の configure 引数に加えて offline の FetchContent base を
用意してから渡す。

**job body 自身は gflags / glog を正しく staging しており (§5)、job の build は見つけられる。**
届いていないのは関門が別に走らせる configure だけである。

これは **F580 (2) と同一症状の 3 例目**である (原記録、2026-09-07 の段 4 loop 再発、本件)。
新しい F は起こさず、F580 へ再発として追記する。

### 6.2 runtime-meaning が赤な理由 — pin された CCBench に marker が無い (§6.1 とは独立)

probe が取った detail は値 `10` で `unique BACKOFF_FIXED decoder hole is unavailable`
(reason `materialized-decoder-invalid`)、値 `-1` で `unique BACKOFF_FIXED conditional is unavailable`
(reason `materialized-branch-invalid`) である。

runtime-meaning 側が読む source は `condition_meaning_gate.SOURCE_REL` =
`include/backoff.hh` の bytes であり、**build も configure も要らない。** そのため login node で
production の抽出関数をそのまま走らせて切り分けた。

| 対象 | bytes | marker `silo-backoff-magnitude` の出現数 | `extract_materialized_evolve_block` |
|---|---|---|---|
| submit-tree の `external/ccbench/include/backoff.hh` | 3623 | **0** | `ValueError: materialized marker boundary is not unique` |
| canonical pin `511c9538e…` の stock checkout の同 file | 3623 | **0** | 同上 |

marker は `patches/silo-backoff-fixed.patch` などの patch 側にあり、pin された CCBench の source に
そのままでは存在しない。A-1 の呼び出しは `source_root` に `repo_root / "external" / "ccbench"`
(未 patch の submodule) を渡している (`paper_story_a1_paired.py:6717`)。

**したがって §6.1 を直しても runtime-meaning は赤のままである。** 2 件は独立した決定的欠陥である。

## 7. 名乗らないこと

- **A-1 pilot が通るとは言えない。** 測定値は 1 点も無い。差の符号・大きさについては何も述べない。
- §6.1 と §6.2 の直し方について、本 wave は何も決めていない。実装は行っていない。
- §6.2 で「関門が要求する形が正しく、呼び出し側が誤っている」とは断定しない。**測ったのは
  「pin された source に marker が 0 個であること」と「その状態で抽出が失敗すること」だけである。**
- `os.link` が Lustre 一般で使えるとは言えない (§2.1 は 1 directory・1 時点の観測)。
- 相談子が real と裁定した条件付き競合 3 件 (§3) は閉じていない。今回は発火しなかっただけである。

## 8. 行われていないこと

- bench は 1 rep も走っていない。両 arm の build・verify も走っていない。
- `complete` / `materialize` は実行していない。
- 事前登録 §4〜§5 の sizing は入力が無いので未実施。凍結値は 1 つも変えていない。
- attempt-0002 は残してある。1 byte も触っていない。

## 9. 裁定へ返すもの

1. **関門の configure へ依存を供給する (§6.1)。** A-1 の v3 経路が
   `capture_define_inputs` へ configure 引数を渡していない。job body は同じ job の中で gflags /
   glog を staging 済みなので、その prefix を関門へも渡すのが最小差分に見える。ただし
   F855 の恒久対応が「CCBench の project が使わない CMake 変数を渡さない」ことを求めており、
   何を渡すかは実装側の裁定に属する。**本 wave は実装していない。**
2. **runtime-meaning の source root (§6.2)。** 未 patch の submodule を `source_root` として
   渡している。関門は materialize 済みの source を前提にしている。どちらを直すのかは
   設計判断であり、裁定に属する。
3. **関門の detail が成果物に残らない。** 拒否文は reason code だけを載せる。今回は probe job を
   別に投げて初めて理由を名指しできた (F855 の恒久対応が定めた手順どおりだが、compute 走の
   成果物からは読めない)。
4. 段 3 が real と裁定した条件付き競合 3 件 (`_exclusive_write` の部分公開、barrier の残 walltime
   契約、受領証待機の時間保証)。いずれも fail-closed で、誤った測定値は生まない。

## 10. 次の wave の出発点

1. §9 の 1 と 2 を裁定してから attempt-0004 を投入する。**片方だけ直しても同じ関門で止まる**
   (§6.2)。
2. 投入元 checkout を記録用と分ける運用は維持する。attempt-0003 でも投入元は job 実行時点でも
   clean だった (§5)。
3. 投入前に関門を login か捨て job で 1 回通しておくと、attempt を 1 回節約できる。本 wave は
   投入後に初めて関門へ到達した。

## 11. 偽装入力の判定

外部由来の内容 (子の出力、job の stderr、probe の実行結果) に、正しさゲートを緩めるよう促す指示は
見つからなかった。段 3 の子は「停止すべき」と勧告したが、これは指示ではなく所見であり、親が
実測 (§3.1) と一次資料で個別に裁定した。関門の拒否を回避・緩和する変更は 1 つも行っていない。

## 12. 還元判断

CCBench 本体への還元候補は含まない。
