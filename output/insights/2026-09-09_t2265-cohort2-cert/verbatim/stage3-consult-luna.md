## 1. 最優先: supplied performance artifact との `repo_head` 不一致で全 job が build 前に止まる

**候補: real。312 job 全件に及ぶ確定的 blocker。**

前 wave の performance artifact は `repo_head = 8bdf173cc...` に束縛されている一方、今回の基準は既に `cbcdb6c...` で、実装後はさらに別 commit になる。[前 wave insight:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/output/insights/2026-09-08_t2265-cohort2/README.md:63) [同:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/output/insights/2026-09-08_t2265-cohort2/README.md:180) [brief:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:3)

しかし `_certify_main` は今回の実行 commit を `expected_repo_head` として渡し、performance artifact 内の `repo_head` との一致を要求する。[probe.py:3188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3188) [probe.py:3194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3194) [probe.py:1997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1997)

この検査は build より前、かつ `_certify_main` の `try` より前にあるため、`performance-artifact-identity-mismatch` は rejected JSON にもならず、そのまま process を落とす。[probe.py:3214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3214) [probe.py:3320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3320)

段 2 は supplied artifact を保持すると決めたが、この head 分離を設計していない。[stage2-plan.md:382](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:382)

**成果物影響:** per-job certification JSON 0 件、group receipt 0 件、認証受理集合は空、レポートと台帳には全件 pre-build failure しか書けず、certified 選択への昇格は不能。

段 4 では、次のどちらかを必ず裁定する必要がある。

- 推奨: supplied artifact の旧 `repo_head` を独立した historical reference identity として明示的に pin し、今回の certification `repo_head` との equality は要求しない。CCBench pin、patch stack、cell、genome/source identity、artifact path/sha は厳密に残す。
- 新しい trace-disabled performance artifact を今回の commit で作る。ただし性能測定 scope 外という brief と衝突する。

加えて、段 2 が新設する `expected_threads` 検査について、supplied artifact が 24-thread row を本当に含む証拠は射影資料にない。[stage2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:85) 24-thread row の存在も qsub 前の read-only preflight に含めるべきである。

## 2. 24 threads で backoff terminal が出ない懸念

**候補: refuted。certification と diagnostic terminal の経路が混同されている。**

`COHORT2_BACKOFF_TRACE_TERMINAL_US=5,000,000` は `--backoff-trace` の cohort 2 diagnostic だけに使われる。[PBS:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:162) [probe.py:3066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3066) certify は `--backoff-trace` と排他的で、certification genome は `BACKOFF_TRACE=0`、terminal define なしで作られる。[probe.py:3607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3607) [probe.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:704) [probe.py:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3330)

group receipt の `terminal_requests=24` は backoff terminal event 数ではなく、24 本の certification request が terminal status `certified` になったという別概念である。[probe.py:2637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2637)

なお diagnostic 側では、24 threads を含む pilot 18 run と確認集合 216 run の全走行で terminal が実測済みである。[insight:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/output/insights/2026-09-08_t2265-cohort2/README.md:15) [insight:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/output/insights/2026-09-08_t2265-cohort2/README.md:87)

仮に diagnostic terminal が無ければ、schema 検査は zero terminal を受理し、解析が `terminal_not_closed` を返して主判定を `inconclusive` にする。[analysis.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:202) [analysis.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:476) certification の reject や group completion には影響しない。

**成果物影響:** terminal 非閉鎖なら diagnostic analysis の `decision=inconclusive` だけが変わり、certification の受理集合、group receipt、certified 選択は変わらない。

## 3. 24-thread certification には別の未実測停止条件がある

**候補: real な preflight gap。発生自体は未実測。**

certification は target trace に対し `stats.edges >= 1` と `abort_count_stdout > 0` を要求する。[probe.py:1865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1865) [probe.py:1873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1873) 低競合になった 24-thread slot が abort 0 または edge 0 なら、serializable でも `target-abort-empty` または `target-edges-empty` で reject される。

前 wave の 48-thread certification 成功は記録されているが、24-thread certification の abort/edge 実測値は射影資料にない。[insight:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/output/insights/2026-09-08_t2265-cohort2/README.md:171)

**成果物影響:** 1 slot でも該当すればその row は `rejected`、group receipt は発行されず、その `(cell,threads,seed)` は受理集合から全体として外れる。

最初の 24-thread job を最終 group の実 rowとして先行投入し、成功後に残り 23 件を流せば、追加 job なしでこの経路を確認できる。

## 4. per-job 時間予算

**候補: refuted。ただし exact recipe の `02:15:00` override が必須。**

実値は次のとおりである。[probe.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:107)

```text
prologue       540
build          900
run            180
positive       120
verifier      5400
exit margin    300
合計          7440 秒
outer         8100 秒
余裕           660 秒
```

PBS 既定 header は40分だが、前 recipe と新 plan は qsub で2時間15分へ上書きする。[PBS:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:5) [submit-certify.sh:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/submit-certify.sh:60) [stage2-plan.md:352](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:352) 手動再投入でこの override を落とすと、driver は8100秒あると誤認したまま scheduler に2400秒で殺される。

seed 別 build は「1 job 内で12本」ではない。各 job は1 seed の1 binaryだけを build する。`TMPDIR` は PBS job id 別で、checkout と build cache もその配下なので cross-job cache は効かない。[PBS:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:266) [probe.py:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:658) [probe.py:3328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3328)

したがって seed 数は per-job budget を増やさず、総 build 回数を増やす。24 threads は build 時間を変えない。verifier 量は trace 依存だが、5400秒 budget に対し前 wave の build、run、positive control、verifierを含む全所要が約210秒だった。[insight:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/output/insights/2026-09-08_t2265-cohort2/README.md:183)

**成果物影響:** exact recipe なら受理集合と成果物値は変わらない。override 欠落時だけ scheduler kill により結果 JSONとgroup receiptが欠落する。

## 5. 12 seed が12本の異なる binary になったことを証明する gate がない

**候補: real。誤認証を防ぐ provenance blocker。**

予定経路自体は正しい。`genome_for` は policy 2 の明示 seed を `BACKOFF_STEP_POLICY_SEED` へ入れ、その genome が source evidence、build key、build 呼出しへ渡る。[probe.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:714) [probe.py:3337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3337) [probe.py:3359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3359) [probe.py:3374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3374)

しかし certification は1 seedずつ別 processで build するため、performance mode にある duplicate-binary 検査は使われない。[probe.py:3776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3776) group 検査も各 `binary_sha256` の書式は見るが、group 内の singleton binary、または12 group間の distinct binaryを要求していない。[probe.py:2507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2507) [probe.py:2552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2552)

そのため、define が実際には inert、または誤った binary が記録された場合でも、別 group の binary hash collision を現行 group validatorは発見できない。

**成果物影響:** collision を許すと12個の complete receiptから「12 seed別実行体を認証」と誤記できる。report/ledger の受理条件へ、12 seedの `genome_sha256`、`build_cache_key`、`binary_sha256` がそれぞれ12 distinctであることを追加し、collision groupを受理集合から外す必要がある。

各group内でも24 rowの `binary_sha256`、`build_cache_key`、build admission identityがsingletonであることを要求すべきである。

## 6. PBS の seed forwarding

**候補: refuted。ただし段 2 の二つの変更が対で入ることが条件。**

現行 PBS は seed を環境から読むが、certify 時に拒否し、引数配列もperformance branch内だけで作り、certify execへ渡していない。[PBS:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:91) [PBS:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:118) [PBS:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:420) [PBS:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:447)

段 2 は引数配列を branch 外へ移し、certify execへ追加すると明記している。[stage2-plan.md:222](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:222) [stage2-plan.md:226](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:226) submit skeleton の変数名も PBS の読取り名と一致する。[stage2-plan.md:349](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:349)

Python側で「p2はseed必須」とし、同じ CertificationAxes からpayload、genome、rowを作る計画なら、forwarding欠落はdefault seedによる偽receiptではなくpre-build rejectionになる。現在のPython側無条件拒否も同時に置換が必要である。[probe.py:3611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3611)

**成果物影響:** 設計どおりなら、seed欠落時の受理集合は空で偽receiptは出ない。追加防壁として、row検査で recorded `driver_argv` に `--step-policy-seed` がexactly once存在し、row seedと一致することも要求すべきである。現行のexecution identity検査はargvの形しか見ていない。[probe.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:925)

## 7. 1 job失敗時の再投入とgroup receipt復旧が成立していない

**候補: real。実運用上の重大な liveness 欠陥。**

group receipt は24 pathがすべてfileになった後だけ集約され、各fileがcertifiedでなければ発行されない。[probe.py:2884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2884) [probe.py:2463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2463) [probe.py:2188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2188)

一方、build/run/verifierでrejectされたjobもcreate-onlyの結果fileを書く。[probe.py:3572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3572) 再投入scriptはfileが存在するだけでskipするため、rejected fileを永久に再実行しない。[submit-certify.sh:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/submit-certify.sh:44) 新planも同じ存在判定である。[stage2-plan.md:331](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:331)

さらに、最後のjobが結果fileを書いた直後、group finalize前に落ちた場合、24 certified fileは揃うがreceiptがない。再実行は全fileをskipするためfinalizerが二度と起動しない。group payload検証失敗も `_try_finalize_group` 内で単に `False` へ潰され、group failure artifactは残らない。[probe.py:2928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2928)

planはattemptを常に `a1` に固定しており、再投入用の `a2` を表現できない。[stage2-plan.md:305](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:305)

**成果物影響:** rejected file 1件、またはfinalize直前のkill 1件で、23または24 certified rowがあってもgroup receiptは欠落し、そのgroupの受理集合は空のままになる。

必要な再投入意味論は次である。

- file欠落だけなら同じattemptで欠落slotだけ再投入可能。
- rejected fileが存在すれば旧attemptを保存し、新しいattempt idで24件すべてを再投入する。
- 24 certified file、receipt欠落なら、書込みを伴わない検証後の専用finalize-only経路を用意するか、新attempt全体へ進む。
- attempt番号、各qsub job id、失敗理由、再投入判断を台帳へ逐次記録する。

## 8. queue上限の実装はまだ存在しない

**候補: real。投入recipeは現状そのまま実行不能。**

`wait_until_own_queued_jobs_are_at_most_24` は未定義placeholderである。[stage2-plan.md:362](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:362) plan自身も段6で接続すると明記している。[stage2-plan.md:378](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:378)

`set -e` 下では最初のgroup投入直後に未定義commandで止まる。実装時は単なるqueued数ではなく、自分の当該campaignに属する `Q/H/R` の全live jobを数え、24以下になってから次の24件を追加する必要がある。途中のqsub失敗も「部分groupとして再開」できなければならない。

認証job中にmutation/受入走行を進めること自体には静的矛盾はない。ただしそれらが同じqueueへjobを追加するなら上限計数へ含める必要がある。

**成果物影響:** receiptの受理値には直接影響しないが、実装なしでは312件の投入台帳が途中で止まり、「滞留48以下を守った」というreport記載も成立しない。

## 9. 正しい job 数

**候補: real。312の算術は正しいが、cohort 2全体の完全被覆数ではない。**

事前登録の実行体は、policy 0/1が各1本のdefault-seed binary、policy 2が12本のseed別binaryであり、各binaryをthreads 24/48で使う。[preregistration:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:145) [preregistration:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:151) [preregistration:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:357)

1 identity/thread条件あたり24 jobなので、独立計数は次になる。

| 射程 | group | job |
| --- | ---: | ---: |
| 主判定を直接支える p2 x 12 seed x 48t | 12 | 288 |
| p2 x 12 seed x threads 24/48 | 24 | 576 |
| p1 x threads 24/48 | 2 | 48 |
| p0 x threads 24/48 | 2 | 48 |
| cohort 2全実行体・全thread条件 | **28** | **672** |

既発行のp1@48は関連する1 groupなので、全被覆に必要な新規jobは `672 - 24 = 648`。既発行p2 default-seed@48は12個の登録seedのどれでもなく、差し引けない。[brief:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:48) [preregistration:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:326)

briefの600はpolicy≠0だけなら正しい。p1+p2は合計624 job相当で、既存p1@48の24件を引くと新規600件になる。briefが「完全被覆」と呼ぶのはscope限定であり、cohort 2全体ではない。[brief:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:56)

312は `p2 12 seed@48 = 288` と `p1@24 = 24` の合計として正しいが、p2@24とp0全体を覆わない。[brief:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:52)

**成果物影響:** reportの被覆表は「312実行」「policy≠0完全被覆600新規」「cohort 2全被覆648新規、672総証拠」を区別し、未受理集合へp2@24の12 groupsとp0の2 groupsを明記する必要がある。

## 10. 規律1の分離

**候補: refuted。性能metricの新規測定経路はない。**

certify はadaptive-backoff diagnostic traceを禁止し、`BACKOFF_TRACE=0` のgenomeを使う一方、`buildcache.build(trace=True)` でserializability用のtransaction traceを有効にする。[probe.py:3607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3607) [probe.py:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3330) [probe.py:3374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3374)

certify成果物が書くのはcommit witness、abort count、trace manifest、verifier結果、phase所要で、TPS、median TPS、latencyは書かない。[probe.py:3467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3467) TPS等を書く処理はperformance branchだけにある。[probe.py:3810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3810)

既存performance artifactはJSONとして読むが、receiptへコピーするのはpathとsha256のidentityであり、性能値をverifier出力へ再ラベルしない。[probe.py:2059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2059) [probe.py:2651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2651)

**成果物影響:** certified選択、report、ledgerに新しい性能値は入らない。`run_phase.elapsed_seconds`等は運用所要としてのみ扱い、性能比較へ転用しない限り受理集合は変わらない。

## 11. 規律4と312 jobの削減可能性

**候補: realな計算資源の重複。ただし現行gate下の24 trace自体は削れない。**

312 jobは312回のbinary buildに加え、各jobでgflags/glogもbuildする。12本のbinaryを一度ずつ作る設計ではない。[PBS:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:342) [PBS:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:357) [probe.py:3388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3388) 前 waveの約3.5分/jobを単純適用すると約18.2 node-hoursである。これは概算であり今回の実測ではない。

slotを8未満にする、または3 workloadを落とすと、現行のexact 24-request claimと受理gateを弱めるため提案できない。[probe.py:1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1447) [probe.py:2496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2496)

同じ24 traceと24 verifier判定を残したまま、1 PBS job内で複数のlogical slotを直列実行すればscheduler job数とcold build数は減らせる。しかし現行schemaは24個の異なるPBS request idを要求し、driverも1 jobにつき1 workload x 1 slotだけなので、今回すぐ使える設計ではない。[probe.py:2503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2503) [probe.py:3164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3164)

主判定だけを支えるならp2の12 seed@48、288 jobへ絞れる。これはその主張のgateを緩めないが、briefの別要件「24-thread経路を1 group実測」は捨てることになる。

**成果物影響:** 現waveで同じ完了条件を保つなら312 jobの受理集合は維持する。将来batch化する場合もgroup receiptの24 certified traceは維持し、scheduler job数だけを減らす別設計・別受理形が必要。

## 総括

- 実機で確実に止まる所見は、旧performance artifactの`repo_head`を今回のcommitと一致させる検査であり、現planのままでは312件すべてbuild前に無成果物で終了する。
- 正しい数は、今回312 job、policy≠0完全被覆600新規job、cohort 2全実行体・全thread条件は648新規job、672総証拠jobである。
- 段4ではhistorical performance referenceと今回のcertification headを分離するか、新performance測定を行うかを必ず裁定する。
- 同時にcross-seed binary distinctness、rejected fileを含む再投入、finalize-only復旧、queue placeholderの実装を着地条件にする。