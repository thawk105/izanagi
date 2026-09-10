authority: none
default_effect: no-state-change

# T-126 FR3 closure — 段4裁定 / plan v2

## 結論

段5へ進む。段2 planはそのまま採用せず、段3のauthority / crash reviewが示した反例を
current sourceで照合し、FR3-1〜4の成果物境界を閉じる次のplan v2へ差し替える。
実装は相互依存するartifact semanticsを持つため単一workspace-write author unitとする。

review正本:

- `.codex/dev-wave-t126-fr3-closure-jobs/review-authority/output.md`
- `.codex/dev-wave-t126-fr3-closure-jobs/review-crash/output.md`

## 所見裁定

| 所見 | 裁定 | 採否 / 最小境界 |
|---|---|---|
| A1 resume-unboundの並行二重qsub | real / BLOCKER / scope内 | durable create-only invocation claimをqsub前に取得し、既存claimがあれば新qsubを禁止する |
| A2 qsub非0でもscheduler受理済みの可能性 | real / BLOCKER / scope内 | qsub invocation後にdurable bindingが無ければrcにかかわらず自動再投入を禁止。nonce付きscheduler証拠がないためavailabilityよりvalidityを優先する |
| A3 invalid canonical削除でmissing retryへ昇格 | real / BLOCKER / scope内 | normal submitのmissing/invalidをともにnonretryへ単調化。pre-attempt recoveryは独立recovered evidenceだけに限定 |
| A4 binding v2 consumer意味分岐 | real / HIGH / scope内 | exact keys / exact int / strict UTF-8 / stdout grammar / v1拒否の共通corpusをjob prologue、driver run/verify、collector、public verifierへ通す |
| A5 v1 historical compatibility | real / HIGH / scope内 | repoにdurable v1実成果物がないためcompatibilityを削除。fixtureもv2のみ |
| A6 M8a/M8dのmask | real / HIGH / scope内 | invocation claim枝へ再照準し、pointer-null fixtureはcanonical/accounting同RCでM6cを避ける |
| A7 accounting walltimeとcanonical elapsedの同値 | real / MEDIUM / scope外 | scheduler丸めの一次契約がないため同値を主張しない。RC/job/Wmax/順序だけをanchorとする |
| A8 production publisherとfixture blob不一致 | real / MEDIUM / scope内 | exact production scriptをfixture commitへ入れ、同じblobをspooled `$0`として実行する |
| A9 failure classのeligible list誤追加 | real / MEDIUM / scope内 | exact eligible tuple pinとreceipt/retry/ledger各拒否controlを追加する |
| A10 login-side collectorのpersistent import | real / HIGH / scope外 | qualification receiptはevidence-onlyで、本waveのlive runはclean committed worktreeを前後照合する。production gate前の別裁定packageへ送る |
| C1 publish完了後killでcanonical/accounting不一致 | real / BLOCKER / scope内 | canonicalをsuperseded evidenceとして保存し、accounting-derived nonretry failureへ閉じる |
| C2 early `job-staging` がreconciliation外 | real / BLOCKER / scope内 | durable bindingのjob ID / nonceに束縛したexact job-stagingとattemptの両namespaceを同じaccounting-first規則で閉じる |
| C3 spooled script hashとcommitted blobのpublic edge欠落 | real / BLOCKER / scope内 | submission hash = series preimage script identity = committed blob、job-result hash = submission hashを共通public validatorで再導出 |
| C4 staging name/inode/nlink不変条件 | real / HIGH / scope内 | exact suffix、uid/mode、dev/ino/nlinkを検査し、異常時はmutationなしで拒否 |
| C5 production fixture偽装 | real / HIGH / scope内 | `_attempt` placeholderへpost-hoc hashを入れず、production shell bytesをfixture Git blobと実 `$0`の両方に使う |
| C6 directory fsync / rerun検出力 | real / MEDIUM / scope内 | target+stageはdir fsync→unlink→dir fsync、targetlessはunlink→dir fsync。rerun収束fixtureを追加 |
| C7 early publisher interpreter | real / MEDIUM / scope内 | trap前に実在Pythonを選び、全terminal pathを同じ`-I -S -B` interpreterへ固定 |
| C8 commit済みidentityからliveへの順序 | real / HIGH / 親運用 | integrated commit→clean exact-commit worktree→計算node受入→mutation復元照合→再受入→同一commit live qsubの順を固定 |

`DW-G02/G05`により、上表のscope内所見はreceipt、attempt ledger、retry authority、実行bytes参照を
実際に変えるためblocker / must-fixとする。一般的なsame-UID syscall間race、自動repair、未使用
submission directory清掃、node/power-loss一般化はscope外。hard crashの主張はprocess deathと
scheduler signalまでに限定し、power-loss durabilityの一般保証へ拡張しない。

## plan v2

### P1. qsub invocation / binding authority

1. qsub前にsubmission directoryへexact create-only `qsub-invocation.json`を発行する。
   nonce、intent SHA、retry indexだけを含み、既存時は新qsubを一切実行しない。
2. `t126-qsub-binding/v2`はqsub rc=0後だけatomic publishする。exact keysはschema、job ID、
   nonce、intent SHA、exact intのreturncode=0、strict raw stdout。job IDはstdoutから再導出する。
3. binding publish後・ledger bind前のcrashだけはv2 exact bytesからledgerを冪等bindする。
   invocationだけ、stdout/rcだけ、rc非0、binding stagingだけの状態は自動再投入せずfail-closed。
4. `submission_cancelled`からの自動reclaimは廃止する。qsub呼出後のrc非0を「未受理」と扱わない。
5. durable v1 artifactは存在しないためv1 consumerを残さず、全production / fixtureをv2へ揃える。

### P2. job-result reconciliation / canonical monotonicity

6. accountingのjob ID / Wmax / terminal RCを先に確認した後、attempt直下とexact job-stagingの
   両namespaceをreconcileする。別job accountingでは一切mutationしない。
7. targetless stagingは完全bytesでも昇格せず破棄。target+single stagingはexact lifecycle
   name、regular/non-symlink、owner/mode、same dev/ino、nlink=2、exact bytesを満たす場合だけtarget採用。
8. multiple、symlink、nonregular、別inode、extra hardlink、bytes mismatchは何も削除せず拒否する。
9. valid canonicalとaccountingが不一致ならcanonicalを消さずsuperseded evidenceとしてclosureに含め、
   `job-result-accounting-mismatch`、terminal=null、retry=falseのfailureへ閉じる。
10. targetless publish crashまたはclean accountingでcanonical欠落/invalidなら
    `job-result-publication-failed`、retry=falseへ閉じる。両classはeligible tupleへ追加しない。
11. normal submitのcanonical missing / invalidは削除・coherent rehashでretry permissiveにならない。
    retry可能なpre-attempt recoveryは独立したrecovered-qsub-binding proofだけに限定する。
12. collectとpublic verifyは同じcanonical resolution / failure derivationを使い、pointer、
    copy、canonical bytes、accounting RC/class/timing順序を再導出する。

### P3. persistent import除去 / identity

13. terminal publisherはproduction job scriptに埋めたstdlib-only bytesとし、repo package、
    `$REPO_ROOT/orchestrator`、`PYTHONPATH`を一切importしない。
14. trap前にPython 3.10+の実体を選び、`-I -S -B`で全normal/TERM/HUP/EXIT pathを実行する。
15. embedded publisherはcurrent atomic protocolを自己完結して実装し、同じcrash injection seamを持つ。
16. submit receipt / bindingのscript hash、series preimage script identity、committed Git blob、
    runtime `$0`、job-resultのhashを同じpublic validatorで連結する。自己申告hashだけを増やさない。
17. fixtureはexact production `t126_qualification.sh`をfixture Git commitへ入れ、そのcommitted
    blobを実際のspooled `$0`としてfull shellから実行する。placeholderとpost-hoc rehashで代替しない。

### P4. consumer / parent boundary

18. binding v2境界corpusをjob prologue、driver run、driver verify、collector reconstruction、
    public verifierへ共通適用する。bool returncode、extra key、余剰stdout、job normalization差を拒否する。
19. failure schemaへ2 classを追加し、protocol eligible tuple、receipt retry field、public retry validator、
    attempt ledgerの4層でfalse固定を確認する。
20. authorはcode / tests / executable scripts / machine-consumed schemaだけを編集する。docs、
    handoff、worklog、decision、mutation台帳、commitは親所有。
21. `tools/pegasus/policy.json`のmain統合は親が行い、T-126 root keysとT-139
    `silo_ladder_rung1` objectを両方保持する。

## 変異事前登録

既登録M1〜M7（SPRT境界、Layer3 lineage、snapshot hash、settled、exact S2 evidence、
accounting closure、retry制限）は削除・弱化せず、実装後anchorを再照準する。

| ID | 単一変異 | 唯一の期待赤 |
|---|---|---|
| M8a | qsub invocation claim既存でもqsubを実行 | barrier付き並行submitでqsub回数が2 |
| M8b | binding無しresume-unboundでraw stdoutをauthority化 | rc0 stdout / binding欠落の曖昧windowがbindされる |
| M8c | qsub rc非0後の自動再投入を許可 | accepted-unknown状態から2回目qsubが発生 |
| M8d | binding v2のexact returncode型/値gateを除去 | boolまたは非0bindingがconsumerへ到達 |
| M9a | targetless full stagingをcanonicalへ昇格 | after-fsync crashがnonretry failureでなくfinal化 |
| M9b | after-publish staging cleanupを除去 | valid target後もclosure manifestがstagingで赤 |
| M9c | exact job-staging reconciliationを除去 | early trap crashが永久open |
| M9d | same-inode/nlink gateを除去 |別inode同bytesまたはextra hardlinkが採用 |
| M10a | normal canonical missing/invalidをretry可能にする | invalid→missing coherent rehashがretry authority取得 |
| M10b | valid canonicalの非null exact pointer条件を除去 | canonical/accounting同RCのpointer-null receiptがvalid化 |
| M10c | canonical/accounting mismatch failure closureを除去 | publish後killがfinal/failureどちらにも閉じない |
| M10d | 新failure classをeligible tupleへ追加 | retry field / validator / ledgerのいずれかがtrue化 |
| M11a | submission script hashとseries committed blobのedgeを除去 | coherent X≠C rewriteがpublic verifyを通る |
| M11b | terminal publisherをpersistent package importへ戻す | post-submit dirty sentinelが実行される |

各mutationは対象anchorより前のgateを正例に揃え、M10bはcanonical/accountingを同一RCにしてM6cの
maskを避ける。directory fsyncは通常の受理集合を変えないためmutation killに数えず、呼出順と
rerun収束のdiagnostic sensitivity pinとする。正例はplain rc0 binding、valid after-publish、
normal exact canonical、pre-attempt recovered evidence、unrelated worktree dirtを維持する。

## 段5所有

単一author unit。許可範囲は次だけとする。

- `orchestrator/qualification/**`
- `orchestrator/tests/test_t126_*.py`
- `tools/pegasus/submit_t126_qualification.sh`
- `tools/pegasus/t126_qualification.sh`

`docs/**`、`output/**`、handoff、Git index、commit、`tools/pegasus/policy.json`、
既存campaign / freeze / submoduleはno-touch。

## scope外裁定package

login-side `collect_t126_qualification.py`がpersistent worktree packageをimportするため、machine receiptが
実行collector bytesそのものを機械束縛しない所見はreal。ただし本waveのFR3-4はjob terminal publisherの
persistent import除去であり、collector実行面の隔離は新しい実行authority設計になるため自動拡張しない。
推奨はproduction gate waveの前に、recorded commitから展開したimmutable collectorを実行する別task。
本waveのlive smokeはevidence-onlyのまま、clean committed worktreeの前後照合をreceiptと一緒に記録する。
