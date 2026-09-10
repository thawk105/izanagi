NO-GO

product の latch poisoning は閉じています。しかし、変異の完全な期待 node 集合が未登録で、grace 脱落変異も現状は semantic kill ではありません。以下は全て静的追跡であり、pytest・`qsub`・`qdel`・`qstat` は実行していません。

## 対応表

| 対象所見 | 判定 | 独立判定 |
|---|---|---|
| レビュー1 Must-fix 1 | closed | `run_seen` と `run_deadline_rebased` が分離され、偽 RUN 後の trusted RUN で回復する |
| レビュー1 Must-fix 2 | partial | 完全な期待 node 集合は導出できるが、plan v2 は古く、spec への登録も未実施 |
| レビュー1 N1 | partial | grace 脱落は V1 と非等価になったが、現 fixture では診断値だけの赤 |
| レビュー1 N2 | closed | T2/T3 の dict・履歴全体比較は除去され、必要 field だけになった |
| レビュー2 MF-1 | partial | 限定方針は正しいが、提案文の旧 latch 説明と「submit 前後」は現差分に不正確 |
| レビュー2 N-1 | partial | nonce seam は未修正だが、現行呼び出しに影響しない nit/backlog |

`regressed` と判定する既存所見はありません。

## レビュー1 Must-fix 1 — closed

(a) 主張

独立 latch により root cause は閉じています。[dispatch_compute.py:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1216) では `run_seen` に関係なく、最初の `rc=0/RUN` が `run_deadline_rebased` を立てます。

時刻展開は `D0=3` として次のとおりです。

- `t=1 rc=153/stdout RUN`: `run_seen=True`、queue wait=1、latch は偽、D=3。
- `t=2 rc=0/RUN`: `run_seen` は既に真だが、独立 latch により D=`2+2+1=5`。
- `t=3 RUN`: 継続。
- `t=4 END`: deadline 判定より先に終端し成功。

latch を `run_seen` に戻すと `t=2` の張り直しが消え、`t=3` で timeout になるため、[回帰テスト:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1438) が直接赤になります。

残る経路は別物です。

- `rc≠0/stdout RUN`しか観測できなければ張り直さず、初期 overall deadline が効く。
- `rc=0` でも request 不在なら RUN より [END 判定:1188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1188) が優先される。
- `pre-running` は [RUN に分類:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:220) され、実開始前に張り直し得る。
- poll 間の RUN を見逃した `QUE→END` は成功するが、`queue_wait_observed=false` のまま。[既存テスト:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1244)
- RUN を見逃して UNKNOWN/QSTAT_ERROR が続けば、queue/overall timeout と active-job qdel に到達し得る。
- 起点は実 RUN 開始ではなく初観測なので、実開始との差は最大 poll・qstat 所要等だけ残る。

(b) file:line

[dispatch_compute.py:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1047)、[同:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1216)、[回帰テスト:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1438)。

(c) 成果物影響

偽 RUN 後に trusted RUN が来る経路では、receipt/task-run が infra/16 ではなく child の実 rc まで到達でき、変異台帳の `PARSE_ERROR` 化を回避できます。

(d) 提案する修正

root cause に対する追加 production 修正は不要です。上記観測不能経路を「未解決」と記録してください。

## レビュー1 Must-fix 2 — partial

(a) 主張

現差分に対する完全な赤集合は以下です。現在は65 test関数・89 nodeで、下記以外が赤になる静的経路はありません。

| 略号 | 正確な nodeid |
|---|---|
| A | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_walltime_plus_grace_bound_qdels_running_job` |
| B | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_queue_wait_does_not_consume_observed_run_budget` |
| C | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_post_run_unknown_state_uses_first_observation_deadline` |
| D | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_nonzero_qstat_run_stdout_does_not_restart_deadline` |
| E | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_trusted_run_after_nonzero_run_stdout_restarts_deadline` |
| F | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_unknown_scheduler_state_remains_bounded_by_overall_timeout` |

| 変異 | 全赤集合 | 時刻展開 |
|---|---|---|
| 張り直しを `submitted_at` 起点へ戻す | B, C, D, E | B/E は D=3・`t=3` timeout。C/D trusted は最終時刻が4→3 |
| `overall_grace_s` を落とす | C, D | trusted RUN の D=4→3、両 node の最終時刻が4→3 |
| RUN 観測ごとに張り直す | A, C | A は D=`1→2→3` で `t=3 END` 成功、C は D=`4→5` で `t=5 END` 成功 |
| `rc == 0` gate を恒真化 | D | untrusted RUN で D=3→4、`t=4 END` 成功 |
| latch を `run_seen` へ戻す | E | 偽 RUN が latch を潰し、`t=3` timeout |
| deadline 判定を `if False` | A, C, D, F | 各有限 fixture が既定 DONE まで進み成功 |

[plan-v2.md:77](/work/1/SFC/tanab/izanagi-jobs/466a006d/t363/plan-v2.md:77) の表は、旧 V2 の削除変異と主検出先だけを記したままです。また fix 報告の submitted-at 集合には E がなく、P1 の集合自体もありません。

V3 と deadline 無効化は `hang_risk=true` が必要です。実 scheduler が RUN を返し続ける場合、前者は毎 poll で D を未来へ送り、後者は `run_seen` 後に上界を失います。現 fake scheduler は状態列消費後に DONE を返すため、この test file 自体では hang しません。ただし dispatch mode の自己参照では外側 dispatcher が timeout/PARSE_ERROR に倒れる可能性があります。

(b) file:line

各 node は [test file:1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1324)–1483。完全一致判定は [mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1191)。

(c) 成果物影響

集合を省略すると、変異台帳は `KILLED` でなく `MISMATCH` を記録し、`summary.KILLED` と `matches_expectation` が誤ります。

(d) 提案する修正

commit 後の anchor で上記集合をそのまま spec に事前登録し、V3/P1 は `hang_risk=true` にしてください。外側 dispatch の `PARSE_ERROR` は node kill に数えないでください。

## レビュー1 N1 — partial、条件付き must-fix

(a) 主張

grace 脱落は V1 と異なる赤集合になったため、旧「等価な2変異」の問題は解消方向です。しかし C/D は baseline でも mutant でも `INFRA_RC`、qdel、`overall-timeout` のままです。赤になるのは `state_history[-1].elapsed_s` の4→3だけで、現 fixture 上の受理集合は変わりません。

したがって、これは [DW-M03/M08](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/dev-wave/mutation.md:16) 上の semantic kill ではなく diagnostic sensitivity pin です。

(b) file:line

[T2:1383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1383)–1388、[T3:1427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1427)–1435。

(c) 成果物影響

このまま `KILLED` と登録すると、変異台帳が診断時刻の差を受理集合耐性として数え、`summary.KILLED` を1件過大計上します。

(d) 提案する修正

`KILLED` に数えるなら、例えば `QUE,RUN,UNKNOWN,UNKNOWN,DONE`、W=2、G=1、poll=1 の正例を追加してください。baseline は D=4で `t=4 END` を受理し、grace 脱落は D=3で `t=3 UNKNOWN` を timeout するため受理集合差になります。追加しないなら別枠の diagnostic pin と明記してください。

## レビュー1 N2 — closed

(a) 主張

T2 は最終 `elapsed_s` と RUN 存在、T3 は必要な時刻・状態・queue field の個別比較へ縮小されています。任意の診断 key 追加で赤になる全 dict 等価は消え、上記6変異への検出力は維持されています。

(b) file:line

[T2:1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1385)、[T3:1427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1427)。

(c) 成果物影響

harmless な `state_history` 診断 key 追加だけで変異台帳が `MISMATCH` になる脆さは除去されています。

(d) 提案する修正

追加修正は不要です。ただし grace 脱落を kill とするなら、N1 の semantic fixture が別途必要です。

## 退行監査 — 静的な既存赤は0

(a) 主張

`run_seen`、`queue_wait_s`、`queue_wait_observed`、`state_history` の既存意味は保存されています。

- `run_seen` は従来どおり、rc に関係なく最初の文字列 RUN で一度だけ立つ。
- queue wait はその最初の文字列 RUN の時刻を保持し、後続 trusted RUN で上書きされない。
- RUN 未観測の END では終端時刻を上限として `queue_wait_observed=false` を記録する。
- `state_history` は RUN/END処理より前に同じ schema で追記される。
- helper の旧既定値は維持され、ERROR stdout の既定も空文字。
- 旧85 nodeについて、近接 deadline を持つ既存 RUN test は `t=0 RUN` なので新旧 D=1、UNKNOWN/HLD は新分岐へ入らない。他の default fixture は D より十分前に DONE となる。

(b) file:line

[dispatch_compute.py:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1197)–1244、[fixture:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:40)–219。

(c) 成果物影響

receipt schema と既存診断値は不変で、修正対象経路だけ outcome/task-run rc が意図どおり infra/16 から実 child rc へ変わります。

(d) 提案する修正

コード修正は不要です。ただしこれは実測ではなく、親による計算ノード上の89 node受入が必要です。

## レビュー2 MF-1 — partial

(a) 主張

限定方針自体は正しいですが、提案文は2点不正確です。

- [review-2.md:13](/work/1/SFC/tanab/izanagi-jobs/466a006d/t363/stage6/review-2.md:13) の「後続正常 RUN でも再試行不能」は、独立 latch により解消済み。
- [同:38](/work/1/SFC/tanab/izanagi-jobs/466a006d/t363/stage6/review-2.md:38) の「submit 前後」は過大。初期 deadline は qsub 応答後の `submitted_at` 起点であり、修正対象はそこから trusted RUN 観測までです。

(b) file:line

[submitted_at:1097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1097)、[初期 deadline:1182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1182)、[張り直し:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1216)。

(c) 成果物影響

旧文言を worklog/insights に書くと、閉じた rc≠0→rc=0 回復経路を未解決と誤記し、修正範囲を qsub 前へ過大化します。

(d) 提案する修正

段7では次の限定表現に置き換えてください。

> qsub の成功応答後、qstat の rc=0 応答が当該 request を含み、パーサが最初に RUN と判定した観測時刻から、親の監視 deadline を `walltime + overall_grace` へ一度だけ張り直した。これにより、qsub 応答から当該観測までの経過が post-observation 予算を削る経路を修正した。rc≠0 の RUN stdout だけでは張り直さないが、後続の rc=0/request-present RUN で回復する。RUN 未観測・UNKNOWN、poll による RUN 見逃し、rc=0/request 不在の END 扱い、pre-running と実開始の差、active job への例外時 qdel は未解決であり、D131 前提6の完了とは扱わない。

## レビュー2 N-1 — partial、nit/backlog

(a) 主張

custom nonce と `log_style="job-name"` の不整合、および `nonce=None/""` と helper 返却パスの不一致は残っています。現行 test 呼び出しには該当しません。

(b) file:line

[固定 job-name:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:79)、[helper:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:189)、[nonce生成:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:997)。

(c) 成果物影響

現行 receipt・task-run・変異台帳には該当呼び出しがなく、値への影響はありません。

(d) 提案する修正

must-fix にせず nit/backlog を維持してください。将来は実 nonce を helper から返し、job name を `cwd.name` から導出します。

## 総括

- latch poisoning の production root cause は closed で、既存意味の静的退行も見つかりません。
- NO-GO理由は、完全な期待 node 登録の未反映と、grace 脱落を semantic kill と数べない点です。
- pytest・PBS操作・変異実走は未実施で、実測判定は親の計算ノード走行待ちです。