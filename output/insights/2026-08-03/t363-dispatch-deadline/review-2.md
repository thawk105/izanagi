結論は、実装コードの must-fix は 0 件です。既存テストの回帰も静的追跡上はありません。一方、親が予定している記録文言には過大主張となる must-fix が 1 件、fixture の拡張性に nit が 1 件あります。pytest・qsub・qdel・qstat は実行していません。

## Must-fix

### MF-1: 「順番待ちが実行予算を食う欠陥を塞いだ」は適用範囲を限定しないと誤り

(a) 主張

修正されるのは、`qstat` が `rc == 0` で、パーサが初めて `RUN` と認識した経路だけです。「実際の実行開始」や、すべての実行中ジョブを基準に予算を張り直すわけではありません。

未解決または観測上区別できない経路は次のとおりです。

- `rc != 0` だが stdout が `RUN` の場合、`run_seen=True` と `queue_wait_observed=True` にはなる一方、deadline は張り直されません。以後の正常な `RUN` でも `not run_seen` が偽なので再試行できません。
- ジョブが実行中でも、正常な qstat 出力が `UNKNOWN`、未認識状態、または `rc != 0` で `RUN` を含まなければ、submit 起点の queue/overall timeout がそのまま効きます。
- `Current State = pre-running` も `RUN` に分類されるため、実開始より前から実行予算を消費し得ます。
- poll 間で短い RUN を完全に見逃して `QUE → END` となる場合、処理自体は成功しますが、receipt は `queue_wait_observed=false` のままで、実行開始を観測した記録にはなりません。
- `QUE → UNKNOWN/QSTAT_ERROR` の間に実行が始まり、そのまま観測できない場合は、上記の見逃しが実害となって queue/overall timeout と active-job qdel に到達し得ます。

(b) file:line

- RUN 判定と、一度限りの reset: [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)
- queue/overall timeout 判定: [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1225)
- `pre-running` を RUN とするパーサ: [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:207)
- timeout 後の infra receipt と qdel: [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1367)
- `rc != 0 + RUN stdout` を固定する T3: [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1395)

(c) 成果物影響

- `rc != 0 + RUN`：dispatch receipt は最終的に `outcome.kind="infra"`、`rc=16`、`reason=...overall-timeout` になり得ますが、queue 観測値は既に記録されます。task-run 台帳の `exit_status` は 16、変異台帳は parse 可能な成功 receipt を得られず `PARSE_ERROR`、`completed` は増えません。
- RUN 中の `UNKNOWN`：既定値では先に `queue-wait-timeout`、条件次第で `overall-timeout` となり、receipt は infra/16、task-run も 16、変異台帳は `PARSE_ERROR` になり得ます。
- `pre-running`：receipt の `queue_wait_s` は pre-running 初観測までとなり、その後の待機時間が `walltime + overall_grace` を消費します。
- poll で RUN を見逃して正常終了：receipt は child の実 rc を返す一方、`queue_wait_observed=false`、`queue_wait_s` は終端観測までの上限値です。

(d) 提案する修正

コードは plan v2 の範囲どおりなので、段 7 の記録を次のように限定してください。

> qstat が rc=0 で RUN を返した経路に限り、実開始そのものではなく最初の RUN 観測時刻から `walltime + overall_grace` を一度だけ再設定し、submit 前後の順番待ちが親の post-RUN 待機上限を削る欠陥を修正した。rc≠0 の RUN stdout、RUN 未観測・UNKNOWN、pre-running と実開始の差、active job に対する例外時 qdel は未解決であり、D131 前提 6 の完了とは扱わない。

より広い主張を成立させるには、権威ある実開始時刻の取得と、観測不能時の timeout/qdel 方針を別タスクで設計する必要があります。

## Nit / backlog

### N-1: `nonce` 注入点は `log_style="job-name"` と完全には組み合わせられない

(a) 主張

`_dispatch(nonce=...)` は追加されましたが、`_Scheduler._finish()` の job-name 分岐は依然 `fixture-nonce` を assert し、ログ名も `izdw-fixture-no` に固定しています。また `nonce=None` や空文字では本体側が生成した実 nonce と helper の返却パスが一致しません。

(b) file:line

- 固定 nonce/log stem: [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:79)
- helper の nonce 注入と返却パス: [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:189)
- 本体の nonce 自動生成: [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:997)

(c) 成果物影響

既存呼び出しに custom nonce と job-name の組み合わせはないため、現行 receipt・task-run・変異台帳の値は変わりません。したがって must-fix ではなく nit/backlog です。

(d) 提案する修正

将来この seam を使う場合、`_finish()` が `cwd.name` から期待 job name を導出するようにし、helper は本体が確定した実 nonce を返す構造にしてください。

## 既存テスト回帰の全件確認

### R-0: 静的追跡上、赤になる既存 node は 0

(a) 主張

現ファイルの 64 test 関数から今回追加された T1/T2/T3 を除く 61 関数、parametrize 展開を含む既存 85 node を対象に追跡しました。実測ではありません。

(b) 全既存呼び出し

既存 `_dispatch(...)` 呼び出し 29 箇所：

`224, 263, 286, 313, 336, 361, 659, 676, 691, 705, 727, 763, 797, 840, 865, 937, 951, 980, 1018, 1039, 1065, 1100, 1148, 1163, 1246, 1255, 1282, 1480, 1696`

既存 `_Scheduler(...)` 構築 38 箇所：

`223, 256, 285, 307, 331, 352, 644, 671, 687, 699, 726, 762, 796, 839, 864, 936, 950, 966, 979, 1014, 1038, 1064, 1081, 1099, 1142, 1159, 1175, 1210, 1245, 1254, 1270, 1296, 1325, 1447, 1479, 1520, 1547, 1695`

直接 `DC.dispatch(...)` を呼ぶ既存箇所：

`967, 1082, 1177, 1221, 1305, 1327, 1449, 1521, 1549`

dispatch fixture を通らない既存 test 関数の開始行：

`346, 378, 398, 427, 474, 521, 569, 609, 738, 791, 806, 876, 891, 1006, 1047, 1126, 1130, 1472, 1587, 1602, 1654, 1674, 1713, 1735`

(c) 状態列と成果物への影響

- 新しい helper 引数を明示する既存呼び出しはありません。既定値 `poll=5`、`queue=20`、`accounting=0`、`nonce="fixture-nonce"` は旧 helper の埋め込み値と一致します。
- `qstat_error_stdout` の既定値は空文字で、旧 ERROR 応答と同じです。`initial_qstat_failures` の stdout も従来どおり空のままです。
- `QUE,ERROR,RUN,DONE` は RUN 初観測が t=10 となり deadline が 2100 から 2110 相当に延びますが、t=15 で終了するため assertion と receipt 値は変わりません。
- `initial_qstat_failures=1` は失敗 t=0、QUE t=5、RUN t=10、DONE t=15。deadline だけが 2100 から 2110 に延び、既存 assertion は不変です。
- `initial_qstat_failures=3` は可視化前に既存エラー経路へ入り、reset 分岐へ到達しません。
- 遅延 qsub のケースは旧 deadline が約 t=2118、新 deadline が約 t=2123ですが、END は t=28で影響しません。
- `walltime=1秒, grace=0, 最初からRUN` の既存 timeout test は旧・新とも deadline=t=1です。
- HLD、UNKNOWN、`QUE→DONE` など RUN を含まない既存ケースは分岐不変です。
- job-name の既存 test は既定 nonce のままなので `fixture-nonce` assertion を満たします。
- 既定 walltime `00:30:00` の既存ケースはいずれも t=10〜15程度で終端し、deadline の後方移動で赤にはなりません。
- 長い queue を持つ実利用では、意図どおり receipt が infra/16 から child の実 rc に変わり、それに伴い task-run の `exit_status` も 16 から実 rc に変わり得ます。

キーワード衝突については、新引数を直接指定しつつ同名キーを `**kwargs` にも入れれば Python の呼び出し境界で従来同様に二重指定エラーになります。既存呼び出しには該当がありません。以前は新しい各キーが `**kwargs` に入り、本体呼び出し時に固定引数と衝突していましたが、それを受理可能にする変更は今回意図された fixture API 拡張です。

(d) 提案する修正

既存テスト向けの修正は不要です。計算ノードで親が既存 85 node と追加 3 node を実測するまでは、「既存テスト成功」とは記録しないでください。

## 消費側と検査への波及

### C-0: consumer の構造的破壊はなく、意図された rc・identity の変化だけがある

(a) 主張

receipt schema、`run_seen`、`queue_wait_s` の既存意味は維持されており、各 consumer に追随修正は不要です。

(b)(c) file:line と成果物影響

| 消費側 | 静的判定 | 成果物への影響 |
|---|---|---|
| [run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/run_tests.py:826) | dispatch 呼び出し契約は不変 | 修正対象経路では task-run の `exit_status` が infra の 16 から pytest の実 rc に変わり得る。台帳 schema は不変 |
| [mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:475) | dispatcher SHA を identity に含める設計どおり | 現在の dirty tree で実行すれば HEAD 不一致として開始前に拒否される。commit 後は `dispatch_entrypoint_sha256` と `head` が新値になり、旧台帳の resume は拒否されるため fresh ledger が必要 |
| [mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1008) | receipt parser の schema 仮定は不変 | outer timeout は引き続き `PARSE_ERROR`、`completed` 非加算。修正後に child 完了まで届く経路では通常の実 rc を記録 |
| [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/check_docs.py:1841) | `_DISPATCH_SOURCE` は同じファイルを指し、解析対象の `TASKS`/`child_script` は未変更 | check の入力意味・出力 schema とも不変 |
| [guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/hooks/guard_bash.py:174) | `_SANCTIONED_PATHS` はパス一致であり内容 hash ではない | 許可・拒否判定は不変 |
| [check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/check_ai_provenance.py:1019) | `task="provenance"` の dispatch 契約は不変 | 修正対象経路では infra/16 ではなく provenance checker の実 rc が返り得る。task-run 台帳はこの直接経路では生成しない |

(d) 提案する修正

consumer のコード変更は不要です。変異試験は plan v2 どおり、統合 commit 後の clean tree から新しい台帳で開始してください。

## 契約・plan v2 照合

### K-0: 編集契約違反なし

(a) 主張

変更は指定された実装・テストの 2 ファイルだけで、stage、docs 編集、作業 commit はありません。

(b) 状態

- `git diff --stat`: 2 files changed, 125 insertions, 7 deletions
- unstaged: `tools/pegasus/dispatch_compute.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py`
- staged/untracked: なし
- HEAD: `1a3604b...`
- `main...HEAD`: `0 0`

(c) 成果物影響

docs、worklog、insights、dispatch receipt、task-run 台帳、変異台帳はこの実装子によって書き換えられていません。

(d) 提案する修正

なし。

### P-0: plan v2 と一致。追加 control だけが改善方向の逸脱

(a) 主張

- T1 は `QUE,QUE,RUN,RUN,DONE`、W=2、G=1、poll=1、queue=10、accounting=0で、rc=0、qdelなし、queue wait=2、観測=trueを確認しています。
- T2 は初回 RUN だけで deadline を張り直し、その後の RUN で再延長されないことを UNKNOWN 列で固定しています。
- T3 は `rc != 0 + stdout RUN` が deadline を張り直さないことを固定しています。
- receipt に新しい field はなく、`run_seen` と `queue_wait_s` の意味も変えていません。
- T3 に正常な RUN の対照群を加えた点だけが plan 記載より追加的ですが、誤った常時無効化を防ぐ改善方向の逸脱です。

(b) file:line

- 実装: [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)
- T1: [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1350)
- T2: [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1369)
- T3: [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1395)

(c) 成果物影響

T1/T2 対象経路では receipt の schema を変えず、`outcome.rc` が 16 から child rc、task-run の `exit_status` も同じ実 rcへ変わります。T3 対象経路は従来どおり infra/16です。

(d) 提案する修正

plan 対応のコード修正は不要です。追加 control は残すべきです。

## 静的検査の限界

必須ファイルと差分全文を読み、全 test 関数・call site・状態列を静的に追跡しました。変更 2 ファイルの構文解析と `git diff --check` は通過しましたが、Pegasus ログインノードの制約に従い pytest、qsub、qdel、qstat、重い checker は実行していません。

## 総括

- コード must-fix は 0 件で、既存 85 node は静的追跡上回帰なし。ただし実走結果ではない。
- 段 7 の記録は「rc=0 の初回 RUN 観測経路に限る」と限定することが must-fix。
- consumer・編集契約・receipt schema は整合し、custom nonce と job-name の組み合わせだけを nit/backlog とする。