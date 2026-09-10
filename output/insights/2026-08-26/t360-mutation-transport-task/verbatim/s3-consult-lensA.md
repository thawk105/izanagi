静的検査のみ実施した。pytest は実走しておらず、緑とは報告しない。

## 1. queue 待ち中の request と task 契約が固定されていない

- **所見**: task 名の二重照合はあるが、親が承認した request bytes、`repo_root`、`child_script` の意味は queue 待ち中に変えられ、最終 receipt が実行内容と食い違いうる。
- **なぜ real か**: 親は [dispatch_compute.py:2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:2548) で `request.json` を書くが、その hash を job script、result、receipt のどこにも束縛しない。compute 側は後から同 file を読み、request 内の `repo_root` をそのまま child path に使う [dispatch_compute.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:688)、[dispatch_compute.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:696)、[dispatch_compute.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:720)。一方、receipt の `request.args` は親のメモリ上の元引数で作られる [dispatch_compute.py:2530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:2530)。result は task、args、request hashを返さない [dispatch_compute.py:732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:732)。さらに `--job-run <任意path>` は公開 CLI 分岐であり、親を経由しない [dispatch_compute.py:3487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:3487)。
- **壊れ方**: 親が mutation Aのspec、commit、outを承認して qsubする → queue 待ち中に同一ユーザーの別 process が `request.json` を別の自己整合した mutation Bへ変更する、または `repo_root` を別 checkoutへ変更する → 子はBを実行するが、親 receipt はAを記録する。親と子のtask名照合は両方通る。
- **重大度**: 正しさ防壁
- **提案**: mutation は新しい request schemaに限定し、親が作った canonical request SHA-256と task-contract IDをjob scriptへ埋め込む。`_job_run` は実際に読んだbytes、module自身のrepo root、task-contract IDを照合し、resultへ同hashを返す。親はそのhashをreceiptへ結ぶ。mutation の直接 `--job-run` はこの束縛が無ければ拒否する。

## 2. 新 task と古い `_job_run` の名前閉包自体は fail-closed

- **所見**: 「新しい親が mutation request を投入し、起動時に古い `_job_run` が読む」経路では、mutation は実行されず rc=16へ閉じる。
- **なぜ real か**: v1は必ず`tests`へ写像され、v2だけがtask名を読む [dispatch_compute.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:649)。親は qsub 前に `task in TASKS` を要求し [dispatch_compute.py:2398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:2398)、子も独立に要求する [dispatch_compute.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:688)。
- **壊れ方**: 新コードで mutation request を投入 → queue 待ち中にdispatcherをmutation未実装版へ戻す → 古い子は未知taskとしてbootstrap段でresult rc=16を書く → 親は`stage != child`をinfra失敗にする [dispatch_compute.py:3132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:3132)。誤実行にはならない。逆向きは、古い親がmutationをqsub前に拒否する。
- **重大度**: nit
- **提案**: この時系列を直接固定する回帰テストを追加する。ただし所見1のtask意味論とrequest bytesの未固定は別途直す必要がある。

## 3. v1互換 request は全キー強制で過剰拒否されうる

- **所見**: 現行の正規tests/provenance requestは壊れないが、プランの「v1 requestも通る」は歴史上の正規v1集合全体には成り立たない。
- **なぜ real か**: 現行tests requestは次の7キーの任意部分集合だけである: `PYTEST_ADDOPTS`、`IZANAGI_TEST_NPROC`、`IZANAGI_TEST_TRIGGER`、`IZANAGI_TASK_RUN_SIDECAR`、`IZANAGI_TASK_RUN_AUTO_RECORD`、`PYTHONDONTWRITEBYTECODE`、`IZANAGI_RUN_GROWTH_HELD_TESTS` [dispatch_compute.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:110)。親はこの集合へ射影する [dispatch_compute.py:2487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:2487)。provenanceは空集合である [dispatch_compute.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:128)。しかしv1を生成していた元版 `a34266d2:tools/pegasus/dispatch_compute.py:39-44` は正規allowlistに `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` も含めていた。現行v1テストは`PYTEST_ADDOPTS`の一例しか覆わない [test_pegasus_dispatch_compute.py:4202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:4202)。
- **壊れ方**: 元のv1親が削除許可キー付きrequestを生成 → 新しい全キー強制を持つ子が読む → 現行tests allowlist外としてchild未起動のrc=16になる。これは正規v1受理集合の縮小である。現在の正規v2生成物が落ちる経路は見つからなかった。
- **重大度**: 受理集合
- **提案**: v1用の凍結されたexact legacy allowlistを別に持つか、v1互換の終了と受理集合縮小を段4で明示裁定する。「現行allowlist内のv1正例1本」だけで互換を主張しない。

## 4. 全キー強制後も `env_allowlist` は子環境全体を閉じない

- **所見**: プランの検査はrequest overlayだけを閉じ、`os.environ.copy()`由来の未列挙キーはtests/provenance childへ残る。
- **なぜ real か**: `_job_run` はcompute processの環境全体を複製してからrequest値を重ねる [dispatch_compute.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:709)。job scriptが除くのはtask-run marker群だけである [dispatch_compute.py:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:573)。したがってprovenanceの`env_allowlist=frozenset()`も「空のchild environment」を意味しない。プランの`env_mode="clean"`はmutationだけに置かれている [plan.md:116-121](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t360-mutation-transport-task/s2/plan.md:116)。
- **壊れ方**: compute job環境に`PYTHONPATH`、`LD_PRELOAD`、`TMPDIR`、色制御envなどが存在する → requestの全キー検査は通る → childは未列挙値を継承する。schedulerが何を実際に継承するかは今回静的検査では確定しておらず、この入力条件部分は推測である。
- **重大度**: 実効性
- **提案**: `env_allowlist`が「requestからの上書きだけ」を意味するのか「最終child env」を意味するのか契約名を明確にする。後者なら全task共通builderが必要だが、tests/provenanceの受理集合変更になるため段4裁定へ返す。

## 5. 内側のschemaとbaselineは保たれるが、outer transport identityが欠ける

- **所見**: spec v1とbaseline緑必須は計算ノードでも同じharnessが強制する一方、outer-dispatch/inner-localではdispatcher bytesとledger HEADの結び付きが失われる。
- **なぜ real か**: specはexact field集合と`izanagi-dev-wave-mutation-spec/v1`を検査する [mutation_harness.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:518)。baselineはmutation開始前に`PASSED/rc=0/failed_nodes=[]`を要求する [mutation_harness.py:3093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:3093)。localでも`run_tests.py`はdisposable checkoutのHEAD blobと照合される [mutation_harness.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:761)。ただしdispatcherのHEAD blob照合は`runner_mode == "dispatch"`でしか走らない [mutation_harness.py:800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:800)。現行mergerは逆に`runner_mode=="dispatch"`とdispatcher blobを必須にする [mutation_fanout_contract.py:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout_contract.py:805)、[mutation_fanout_contract.py:1101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout_contract.py:1101)。
- **壊れ方**: outer dispatcherはHEAD X、wrapperは`--commit Y`のcheckoutでlocal harnessを実行 → ledgerはrunner/harness Yだけを証明し、実際に投入を解釈したdispatcher Xは証明しない。現行mergerをそのままなら恒偽で拒否し、local対応のためdispatcher検査だけ外せば証拠穴になる。
- **重大度**: 正しさ防壁
- **提案**: mutation taskではouter repo HEADと`--commit`を一致させ、outer receiptにdispatcher実行bytes、HEAD blob、task-contract ID、request hashを追加する。mergerはinner dispatch hashの代わりにこのouter証拠を必須にする。

## 6. task追加だけでは束ねtransportが実効化しない

- **所見**: fanout連携を「採る場合だけ」としたままでは、D842の成果であるqueue回数削減を発火させるproduction callerが存在しない。
- **なぜ real か**: 現行fanoutはwrapperを`--runner-mode dispatch`で起動する [mutation_fanout.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout.py:656)。harnessのcollectionは`tests` taskを作り [mutation_harness.py:1366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:1366)、baselineと各mutationは同じ`run_tests.py`を起動してlogin側で自己dispatchする。プランはcaller変更をfanout採用時だけとしている [plan.md:176-182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t360-mutation-transport-task/s2/plan.md:176)。公式dev-wave契約もなお`runner-mode dispatch`と`--force-dispatch`を必須にする [mutation.md:43-54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/dev-wave/mutation.md:43)。
- **壊れ方**: `TASKS["mutation"]`とtask表だけlandする → 通常のdev-waveは旧commandを使い続ける → baseline、mutationごとのqsubが残り、T-360の成果物影響は改善しない。fanoutだけlocal化してmergerを変えなければ、request数とrunner modeの既存gateで全件拒否される。
- **重大度**: 実効性
- **提案**: 段4で必ず1つのproduction producerを選ぶ。fanoutを選ぶならD433、outer receipt、merger、driver、公式`docs/dev-wave/mutation.md`とrunbook §7.4まで同じscopeに入れる。D433を含められないなら、非fanoutのfull-spec wrapper callerを正規入口として実装し、fanout未対応を明記する。

## 7. rc衝突はfanout層に実在するが、infraをKILLEDと読む向きは見つからない

- **所見**: dispatcher rc=16はmutation rcと衝突しないが、fanoutのrc=2と125は内側の意味と衝突し、raw rcだけでは原因を復元できない。
- **なぜ real か**:
  - harness: 0=全期待一致、1=期待不一致、2=fail-closed停止、128+signal [mutation_harness.py:3171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:3171)。
  - wrapper: child rcを伝播し、wrapper失敗は125 [mutation_worktree.py:988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_worktree.py:988)。
  - dispatcher: infraは16、会計確認済みchild rcはそのまま返す [dispatch_compute.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:40)、[dispatch_compute.py:3144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:3144)。
  - fanout: infraは2、launcher失敗は125、terminal shardは0/1だけ [mutation_fanout.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout.py:45)、[mutation_fanout.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout.py:769)。
- **壊れ方**: harness contract停止rc=2 → outer process rc=2 → fanout自身のinfra rc=2へ潰れる。wrapper失敗125とlauncher自身の125も区別不能になる。向きは「mutation側のfail-closed理由をinfraへ潰す」であり、infraを「変異を殺せた」と読む向きではない。KILLED判定はpytest rc=1と失敗node完全一致を要する [mutation_harness.py:1983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_harness.py:1983)ため、infraからKILLEDへの誤分類経路は見つからなかった。
- **重大度**: 正しさ防壁
- **提案**: fanout採用時はraw rcを分類根拠にせず、dispatcher `outcome.kind`、`accounting_verified`、outer child rc、wrapper child rc、launcher rcを別fieldで必須化する。プランの方向は正しい。

## 8. site gate案にはlogin false-negativeがある

- **所見**: 正常なouter jobでは入れ子qsubは起きないが、プランの`current_site()`既定呼出しではNQSV証拠を読めないPegasus loginを`OTHER`としてlocal許可する。
- **なぜ real か**: job scriptと`_job_run`はchild起動前に独立してbnodeを要求する [dispatch_compute.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:602)、[dispatch_compute.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:705)。`run_tests.py`がqsubするのはLOGINだけで、SUSPECTは拒否する [run_tests.py:2606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/run_tests.py:2606)、[run_tests.py:2620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/run_tests.py:2620)。一方、`site_policy.classify_site("pegasus02", ..., has_nqsv=False)`はOTHERである [site_policy.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/campaign/site_policy.py:30)。`require_evidence=True`ならSUSPECTへ閉じる [site_policy.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/campaign/site_policy.py:66)が、プランは既定呼出しである [plan.md:66-80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t360-mutation-transport-task/s2/plan.md:66)。
- **壊れ方**: pegasus02上でqsub/qstat検索とmarker観測が失敗 → harness/worktreeのlocal gateはOTHERとして通す → `run_tests.py`もOTHERとしてlogin上でpytestを直実行する。正常なouter compute経路では、hostname取得失敗はSUSPECTまたはOTHERとなり、前者は拒否、後者はlocalなので入れ子qsubにはならない。
- **重大度**: 正しさ防壁
- **提案**: task由来local経路は明示capabilityで識別し、`current_site(require_evidence=True) == PEGASUS_COMPUTE`だけを許可する。一般の非Pegasus local利用はtask外で維持する。hostname例外、NQSV証拠欠落、矛盾したlogin分類を正負例で固定する。

## 9. M3の「D103はglobだけ」は狭すぎる

- **所見**: D103はglob拒否だけでなく、sanctioned entrypoint自身を第一層のfail-closed境界としているため、任意command taskはその境界も変更する。
- **なぜ real か**: D103決定5は第一層をsanctioned entrypoint、第二層をhook、第三層を規律と定義する [decisions.md:4599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/decisions.md:4599)。D105も任意command化を明示的に拒否した [decisions.md:4710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/decisions.md:4710)。実装上もdispatcherは`local-ok`で [admission_registry.json:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/admission_registry.json:34)、hookはsanctioned targetを重量command解析前に許可する [guard_bash.py:1226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/hooks/guard_bash.py:1226)。
- **壊れ方**: `--task generic -- <任意argv>`を実装 → hookはdispatcher exact pathで早期許可 → sanctioned entrypointが任意exec trampolineになる。これはglobを追加しなくてもD103第一層の信頼範囲を広げる。
- **重大度**: 正しさ防壁
- **提案**: 任意command taskは実装しない。固定child、固定env、固定argv policyのclosed profile追加方式だけを一般化と呼ぶ。真のgenericを要求するならD103とD105の境界変更として段4からユーザー裁定へ返す。

## 10. M5のliteral freeze主張は破れなかったが、広い「pinなし」は破れる

- **所見**: `output/s8b-freeze`とadmission registryにdispatcher SHA pinは見つからなかったが、既存fanout proof chainにはdispatcher HEAD blobの厳密なpinがある。
- **なぜ real か**: registry項目は4文字列fieldだけでSHAを持たない [admission_registry.json:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/admission_registry.json:34)。一方、fanout mergerは実行中mergerのHEADをledger HEADと一致させ、dispatcher blobを取得する [mutation_fanout_contract.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout_contract.py:232)。そのblobをledgerのdispatch identityと比較する [mutation_fanout_contract.py:1101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/mutation_fanout_contract.py:1101)。
- **壊れ方**: 古いHEADで作った未merge shardをdispatcher変更後のHEADからmergeする → current merger HEAD不一致で拒否される。したがって「変更後も常にHEAD追随で整合」はpending fanout evidenceには一般化できない。既に完成した凍結bytesをT-360が直接変更する経路は見つからなかった。
- **重大度**: 実効性
- **提案**: frozen成果物非改変と、開発fanoutの固定HEAD再検証を別主張に分ける。local ledgerへ移す際も既存pinを削るのでなく、outer dispatcher identityへ移植する。

## 総括

### (a) must-fix

1. request bytes、canonical repo root、task-contract、実行dispatcher identityをqueue境界越しに束縛する。
2. outer-dispatch/inner-local用の証拠consumerを実装し、既存fanoutのdispatcher pinをouter receiptへ移す。
3. production callerと公式dev-wave文書までscopeに入れ、task追加だけの恒真成果物を避ける。
4. task由来local経路は証拠必須のexact COMPUTEに限定する。
5. fanoutを採るならrc=2/125を構造化fieldで分離する。

### (b) 親が段4で裁定すべき論点

1. v1の歴史的allowlistを維持するか、互換終了と受理集合縮小を承認するか。
2. D433を含めてfanoutを正規producerにするか、非fanout full-spec callerを先に正規化するか。
3. `env_allowlist`をrequest overlay契約に限定するか、最終child env全体までclean化するか。
4. mutation taskで`--commit == outer repo HEAD`を必須にするか、旧commit実行を許す別のidentity契約を作るか。
5. generic taskを不採用と確定するか、D103/D105を明示的にsupersedeするか。

### (c) 攻撃したが破れなかった箇所

- 新mutation requestを古い`_job_run`が読む名前閉包はrc=16へfail-closedし、誤実行しない。
- 現行の正規tests/provenance requestは現在のallowlist全キー強制で落ちない。
- spec v1 exact検査、固定HEADのrunner/harness照合、baseline緑必須はinner localでも残る。
- 正常なouter compute経路では二重bnode gateがあり、`run_tests.py`はcomputeでqsubしない。
- dispatcher infra rc=16と定義済みmutation top-level rcの衝突は見つからなかった。
- infra失敗をmutationのKILLEDとして数える経路は見つからなかった。
- `output/s8b-freeze`またはadmission registryによるdispatcher frozen-bytes SHA pinは探したが見つからなかった。