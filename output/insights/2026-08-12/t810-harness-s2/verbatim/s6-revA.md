# 判定: **NO-GO**

静的監査のみ実施した。pytest は未実走。以下は land blocker を含む。

### 1. guard / budget receipt が自己申告だけで受理される — blocker

- file:line: [t810_coordinator.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:225), [t810_coordinator.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:256), [test_t810_coordinator.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:38)
- 具体入力 → `budget.status="unratified"`、guard identity `unresolved` の policy に、`{"launch_intent_sha256": X, "decision":"admitted"}` と `{"launch_intent_sha256": X, "admitted":true}` を渡すと、coordinator は schema・policy digest・ledger reservation を検証せず manifest を作れる。
- 成果物影響: 予算台帳を一切消費せず、guard 不成立の attempt が terminal/certified 候補の受理集合へ入る。
- 修正案: full admission-policy loader、typed guard/budget receipt validator、ledger-after digest を coordinator 入口で検証し、guard 両相と予約成功を production orchestration に直結する。

### 2. canonical qsub が production から切断され、任意 argv を実行できる — blocker

- file:line: [t810_harness_schema.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_harness_schema.py:303), [t810_coordinator.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:318), [t810_pbs_wrapper.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:155)
- 具体入力 → `qsub_argv=["/bin/sh","-c","touch /repo/pwn; echo 1.server","-o",OUT,"-e",ERR]` は `-o/-e` だけ満たせば schema を通り、そのまま `_scheduler_effect()` で実行される。ratified project/queue/walltime は参照されない。
- 成果物影響: repo 書込みや非 qsub process を起こした attempt でも submission receipt と後段 terminal を生成でき、測定受理集合が任意コマンドまで広がる。
- 修正案: ratified policy から coordinator 自身が canonical argv を再構成して exact 一致を確認し、adapter でも先頭・全 option・script path を再検査する。

### 3. ready/ack/completion が事前投入可能で、開始 spread が実受領時刻を測っていない — blocker

- file:line: [t810_coordinator.py:774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:774), [t810_coordinator.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:801)
- 具体入力 → config に 13 件の ack を coordinator 起動前から入れると、release 後に list を走査した時刻が「受領時刻」として記録される。ノードが release を見ていなくても `spread≈0` で合格する。
- 成果物影響: 実開始が5秒を超えた、または一度も開始していない attempt が `valid` となり、レポートの occasion と性能値が偽装される。
- 修正案: config 内 event を廃し、create-only receipt を release 後に監視して、coordinator が実際に読み取った瞬間を単一 monotonic clock で刻む。

### 4. node receipt の hash chain と digest が検証されない — blocker

- file:line: [t810_coordinator.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:349), [t810_coordinator.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:592), [test_t810_coordinator.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:155)
- 具体入力 → preflight、ack、measurement、terminal をすべて `sequence=0, previous_event_sha256=null` の独立 dict にし、`node_receipt_sha256` に任意64桁を置いても受理される。テスト fixture 自身がこの形である。
- 成果物影響: 実在しない測定・receipt を13件合成して `valid` terminal と throughput 行列を作れる。
- 修正案: node JSONL の実 bytes を読み、sequence、previous digest、event 順序、最終 file digest を一括検証し、caller 提供 digest を信用しない。

### 5. state 2 の脱落を `terminal_reduced` に昇格できる — blocker

- file:line: [t810_pbs_wrapper.py:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:673), [t810_coordinator.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:601), [t810_coordinator.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:626)
- 具体入力 → 1 job が ack 後に `dependency_manifest_mismatch` terminal を出して測定せず、残り12件が完了すると、coordinator は terminal reason を無視して「12 complete」だけから `terminal_reduced` を返す。完成 job の `post_inventory_mismatch` terminal も、rounds/hash が揃えば `valid` にできる。
- 成果物影響: 本来推定禁止の state 2/3 attempt から12/13ノード推定値が生成され、certified 選択が変わる。
- 修正案: §5.4どおり全 node terminal の境界/reason を上から先に集約し、state 1–3 が一件でもあれば completion 数判定へ進まない。

### 6. `presence_valid=false` の `valid` / `terminal_reduced` を schema が受理する — blocker

- file:line: [t810_harness_schema.py:702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_harness_schema.py:702)
- 具体入力 → 13完了・reason=`all_jobs_complete` の terminal で expected/actual presence を不一致にし、`presence_valid=false` と自己申告すると validator は整合した boolean として通す。12完了でも同様。
- 成果物影響: presence matrix 違反を含む attempt が certified 受理集合へ残る。
- 修正案: `valid` と `terminal_reduced` は再計算結果が必ず `True` でなければ拒否し、不一致は state 3 のみ許す。

### 7. 「repo 外」判定が現在の worktree しか守らない — blocker

- file:line: [t810_coordinator.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:121), [t810_budget.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_budget.py:400)
- 具体入力 → 現 worktree から見て sibling である `/work/1/SFC/tanab/izanagi/output/t810` を output/ledger root にすると検査を通るが、そこは main repository 内である。manifest、PBS `-o/-e`、ledger が repo に書かれる。
- 成果物影響: 禁止された repo 流入により validator inventory・台帳・レポート参照が汚染される。
- 修正案: git common-dir と全 worktree、`.git` ancestor、承認済み外部root allowlistを作成前に検査し、ledger/PBS/cwdへ共通適用する。

### 8. benchmark allowlist が caller の自己申告で恒真化される — blocker

- file:line: [t810_runner_policy.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_runner_policy.py:32), [t810_runner_policy.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_runner_policy.py:70), [t810_pbs_wrapper.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:464)
- 具体入力 → `/tmp/report-writer` を executable とし、その任意 argv・path・digest を同じ WrapperRequest と witness に書けば exact 比較は成立する。名前に `certify` 等を含めなければ calibration/report writer でも実行される。
- 成果物影響: prereg の CCBench argv 以外の process が作った性能値や禁止 receipt がレポート・certified 選択へ混入する。
- 修正案: executable/hash/argv は verified preregistration と build manifest から導出し、WrapperRequest からの自己申告を廃止する。

### 9. budget finalize witness は「64桁の存在」しか証明しない — must-fix

- file:line: [t810_budget.py:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_budget.py:560), [test_t810_budget.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_budget.py:248)
- 具体入力 → `outcome="qdel-confirmed-before-start", witness_sha256="c"*64` だけで reservation を `released` にできる。qdel、cancel、未開始の receipt は読まれない。
- 成果物影響: consumed であるべき node-seconds が残枠へ戻り、後続 admission の受理集合と台帳 remaining 値が増える。
- 修正案: outcome ごとの typed witness をロード・内容検証し、その canonical digest と reservation/job identity を照合する。

### 10. witness gate を迂回できる import 経路が残る — must-fix

- file:line: [t810_coordinator.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:219), [t810_coordinator.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:893), [t810_runner_policy.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_runner_policy.py:118), [t810_pbs_wrapper.py:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:507), [t810_guard.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_guard.py:429)
- 具体入力 → `_subprocess_scheduler(argv,...)` と `_subprocess_runner(argv,...)` は witness 無しで直接 import・実行可能。`_run_wrapper(..., measurement_run=evil)` も任意 effect に到達する。`prepare_group()` は witness 無しで filesystem を変更し、`withdraw_b_group(..., witness=None)` も authorization 前に `publish_cancel()` を呼ぶ。
- 成果物影響: scheduler/benchmark/repo書込みを authorization receipt と結び付けられず、receipt・台帳・terminal の由来集合が拡大する。
- 修正案: low-level adapter 自身へ検証済み authorization token を必須化し、production effect と fixture seam を別 module/型に隔離する。

## テストの実効性 — must-fix

- [test_t810_coordinator.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:419) の `test_authorized_production_core...` は public `coordinate()`、wrapper、guard、budget を通らず、事前合成 event・偽 receipt・private seam を使う。production 統合テストではない。
- [test_t810_coordinator.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:87) は非正規 `guard/v1` / `budget/v1` receipt を正例にしており、所見1を期待値で固定している。
- [test_t810_pbs_wrapper.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_pbs_wrapper.py:281) は cancel を wrapper 開始前から置くため、[t810_pbs_wrapper.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:687) の「第2再確認」を削除しても最初の確認で赤になり、変異を殺せない。
- [test_t810_pbs_wrapper.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_pbs_wrapper.py:400) の AST tripwire は wrapper と runner しか走査せず、coordinator の `subprocess.run` と guard を対象外にしている。
- [test_t810_harness_schema.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_harness_schema.py:212) と [test_t810_coordinator.py:413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:413) は production の表を列挙して同じ表から期待値を得る恒真テストで、protocol 行の削除・付替えを独立に検出しない。
- 成果物影響: テスト全緑でも無測定 `valid`、state 2 の `terminal_reduced`、repo流入、無根拠 ledger release が残る。
- 修正案: 正本 literal を独立 fixture に固定し、file-backed production orchestration と実 cancel 挿入点を通す negative integration test を追加する。

6 commit 内に substantive な test 削除、skip、xfail 化は見つからなかった。

## 変異耐性（静的判定）

| 変異 | 判定 | 根拠 |
|---|---|---|
| hostname 異なり数検査の除去 | KILLED | `test_ready_barrier_recomputes_raw_evidence[duplicate_host]` |
| spread 上限の緩和 | KILLED | 5秒−1ns / 5秒 / 5秒+1ns の境界 assertion |
| cancel 第2再確認の除去 | **SURVIVED** | cancel fixture が最初から存在し、第1確認が mask |
| argv exact の部分一致化 | KILLED | coordinator の追加引数 fixture、runner の prefix/suffix fixture |
| 未知 job_state の無害化 | KILLED | `test_unknown_state_has_dedicated_deny_reason` |
| unratified の ratified 扱い | KILLED | budget unratified deny、qsub generation deny |
| ledger genesis 照合の除去 | KILLED | `test_different_genesis_ledger_is_rejected` |

## 総括

- **NO-GO。**
- coordinator は guard・budget・canonical qsub を production 経路に結線していない。
- ready/ack/completion は事前合成可能で、5秒 spread は実受領を測っていない。
- node receipt の chain/digest が未検証で、測定全体を dict literal から偽造できる。
- state 2 の1 job 脱落が `terminal_reduced` に昇格する。
- `presence_valid=false` でも `valid` を schema が受理する。
- main repo/sibling worktree への書込みを「外部」と誤認する。
- benchmark allowlist と budget finalize witness は自己申告で恒真化できる。
- cancel 再確認除去の変異だけは現テストで生存する。