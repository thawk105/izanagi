# [T-659] 段 2 設計プラン

推奨は、(P1) source edit 自動化ではなく「record と exact head pin が同一 commit に入ったことを land 前に検査する gate」、(P2) activation 専用の手順型 maintenance window、(P3) その仕組みが land するまで serial ≥ 3 を許可しない、の三点です。

実装は行っておらず、pytest も実走していません。以下の行番号は現 worktree `ee2da0bf` 基準です。

## 先に必要な erratum 2

親 brief の erratum は、前半は正しい一方、後半の識別子名と識別範囲に再訂正が必要です。

- `activation_serial` / `activation_state_sha256` は `AuthorizedContract` の process-local field であり、guard が同一 state と照合するだけです。[env_contract.py:447–456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:447)、[execution_guard.py:70–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/execution_guard.py:70)
- durable execution receipt が持つ環境世代識別子は `contract_sha256` です。v1、v2 とも `activation_serial` はありません。[execution_guard.py:204–222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/execution_guard.py:204)、[execution_guard.py:620–633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/execution_guard.py:620)
- `evidence_contract_sha256` は別物です。これは段 8c の `s8c_preregistration_evidence_contract.v1.json` の意味内容 hash であり、env contract 世代を表しません。[s8c_preregistration.py:34–43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/s8c_preregistration.py:34)、[s8c_preregistration.py:330–337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/s8c_preregistration.py:330)
- D245 は一部 env の据置を許します。[decisions.md:11390–11399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/docs/decisions.md:11390) したがって `contract_sha256` で事後識別できるのは「その artifact が使った env の contract が実際に変わった場合」だけです。他 env が進んでも、自 env が据置なら旧新 activation state は区別できません。
- よって正しい表現は「変更された env の世代混在は、receipt-bearing な成果物について `contract_sha256` で事後分類できる」です。「全成果物の activation head を `evidence_contract_sha256` で識別できる」は DW-O13/D75 に反し、gate 入力に使えません。

親 brief の [実測訂正:25–27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:25) は、この erratum 2 を反映してから段 3 へ渡すべきです。

## 1. 窓の棚卸し

ここでいう fresh process は「対象 checkout/source-stage から新しく Python module を import する process」です。単なる fork は fresh import と同義ではありません。

| 状態 | filesystem / Git | fresh process | 既存 process・fork child | 配備上の意味 | 根拠 |
|---|---|---|---|---|---|
| S0: 発行前、head=n | record と定数が n で一致 | n を受理 | cache 済みなら n | 各 worktree は自分の n を持つ | head 定数 [env_contract.py:373–379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:373)、load [env_contract.py:519–530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:519) |
| S1: issuer が candidate を構築・検証中 | live directory は未変更。staging file は activation directory の親に作る | n | n | crash で `.stage` が残っても loader の列挙外 | issuer [45–94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:45)、loader は directory 内全 entry だけを見る [env_contract_activation.py:450–476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:450) |
| S2: record n+1 の hard-link publish 後、head=n | valid suffix は live、source pin は旧 | 同じ worktreeでは serial/hash 不一致で fail-closed | n を既に cache 済みなら n のまま続走。旧定数を import 済み・未 load の process は初回 load で拒否 | working tree の分裂状態。commit 前 | publish [95–106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:95)、pin 照合 [env_contract_activation.py:406–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:406)、実測 probe A [43–54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:43) |
| S2-crash: publish 後の異常終了 | Python 例外なら cleanup を試みる。SIGKILL/電源断なら record、または record+親側 stage が残りうる | head 不一致で拒否 | cache 済み n は続走 | issuer 再実行も `current_activation_state()` で head 不一致になり、手動 recovery が必要 | cleanup [107–134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:107)、authority load は発行前 [179–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:179) |
| S2-reverse: head=n+1、record=n | 手編集や逆順 crash で成立しうる | fail-closed | cache 済み n は続走 | source edit を先にしても安全性は上がらない | probe C [69–82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py:69) |
| S3: record と head が n+1、未 commit | 発行 worktreeだけ整合した dirty tree | 新しく importすれば n+1 | cache 済み n は続走。旧 module を import 済みの processは source file を自動 reload しない | 他 worktree/main は依然 n | cache [env_contract.py:576–586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:576)、cache 継続の既存テスト [test_env_contract_activation.py:1737–1748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/tests/test_env_contract_activation.py:1737) |
| S3-fork | child では cache・seal・receiptだけを reset | 親が新 module を import済みなら n+1 | 旧 module を持つ親から fork した child は旧定数を継承する。新 directoryに対しては拒否しうる。`exec` を伴わない fork は再起動確認にならない | 「fork時reset＝新head化」ではない | reset [env_contract.py:551–573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:551)、fork test [1751–1799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/tests/test_env_contract_activation.py:1751) |
| S4: 同一 commit C に両方 | Git tree C は整合。record-only/head-only commit はどちらも fresh load を拒否 | C の source-stageなら n+1 | C より前に起動した processは n | commit object の整合と、live worktreeへの配備は別 | 両 path は `git ls-files --stage` で tracked を確認。loader統合テスト [1498–1542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/tests/test_env_contract_activation.py:1498) |
| S5: wave branch に C、main/他 worktree は旧 | worktreeごとに checked-out tree が独立 | waveでは n+1、main/旧 worktreeでは n | 各 rootで既に cacheした版 | 「commit済み」だけでは全 checkout 配備にならない | issuer root は tool の `__file__` から決まる [159–165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:159)、runtime root も module `__file__` 基準 [env_contract.py:465–483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:465) |
| S6: main へ land 中 | 現行 land は main worktreeで `git merge --ff-only` を実行する。reader向けの二ファイル排他はない | 更新途中に起動すれば旧・新または split を読み、split は拒否 | 既存 n は継続 | commitの原子性は worktree更新の cross-file 原子性を意味しない | [dev_wave_land.py:1921–1933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:1921) |
| S6-queued/shared | job種別で異なる | T126 は submit時の `source_commit` を archiveして旧 C0 を整合したまま走れる。generic dispatch は request の `repo_root` を実行時に直接使う | queue中の job はまだ pgrep対象にならず、開始後に旧 head processとなりうる | pgrepだけでは drain 完了にならない | T126 [t126_qualification.sh:469–496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/t126_qualification.sh:469)、generic dispatch [dispatch_compute.py:567–590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/dispatch_compute.py:567) |
| S7: scoped process/jobをdrainし、Cからexec再起動 | 対象 rootはC、旧queued/running jobなし | n+1 | 旧 processなし | ここで初めて「全 scoped process が新head」 | fresh loadは exact pin経由 [env_contract.py:519–548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:519) |

並行 issuer は、双方が n+1 を作っても `os.link(... no-replace)` により一方しか publish できません。上書きの fail-open はありません。ただし勝者の publish 後から head 更新までの S2 は残ります。

### 「窓は2つ」の検証結果

安全性の観点では、親の二分法に fail-open の漏れはありません。しかし運用状態としては三つの barrier に分ける必要があります。

1. 発行 worktree内の authoring barrier: record発行からhead更新・同一commitまで。
2. deployment barrier: activation commitをmain、各実行checkout、source-stageへ展開するまで。
3. lineage barrier: 旧process、fork lineage、queued jobをdrainし、`exec`で再起動するまで。

親の「2窓」は、2を1へ含め、対象checkoutを一つに限定し、queued jobを既存processに含めるなら成立します。複数worktree/source-stageを許す現状では、その前提を明記しない「commit後〜全process再起動」だけでは不十分です。

## 2. (P1) atomic deployment の択一

厳密には、どの案も Git working tree上の二ファイル更新を一命令で原子化しません。判断対象は「split commitを防ぐか」「split working treeを短くするか」です。

| 案 | file:line単位の想定差分 | fail-closed | trust root | 最小性・評価 |
|---|---|---|---|---|
| A. 親案: issuerがsource headも書換え | `tools/issue_env_contract_activation.py:143–152,195–221` に exact旧値照合、置換数2、temp+rename+fsync、失敗時診断を約70–110行。`test_env_contract_activation.py:1867–2004` に約100–160行 | split方向はいずれもloaderが拒否。ただしSIGKILL後のrecord-only残骸は不可避 | runtime trust rootは現行source定数のまま。issuerがtrusted source editorになる | 操作は短いが同一commitを保証しない。「atomic」と名乗れない |
| B. 現状維持+runbookのみ | `docs/pegasus-runbook.md` に約30–50行、handoff文の参照追加約5行 | 現行挙動を完全保存 | 不変 | 最小だが、反復時の手順漏れを機械検出しない |
| C. headをtracked data file化 | 新規 `env_contract_activation_head.json` 1行、strict parser約50–80行、loader/tool約50–80行、identity closure/test約180–280行 | strict parse/exact pinなら保存可能 | source定数からdata blobへ移動。T126 identity [contract.py:38–76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/qualification/contract.py:38)、silo binding [silo_ladder_rung1.py:254–286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/silo_ladder_rung1.py:254)、T419 closure [t419_probe_causality.py:3491–3505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/probes/t419_probe_causality.py:3491) の追随必須 | file数は減らず、trust面だけ広がる。研究最優先に不適 |
| D. 同一commitのhistory/land gate | 新規 checker約130–200行、`tools/dev_wave_land.py:1709–1722` に呼出し約10–20行、専用test約160–240行、runbook約20行 | recordのみ/headのみ/splitした2commitをland前拒否。runtime exact pinは変更しない | runtime trust root不変。運用trust rootへtrusted-main checkerとland toolを追加 | 差分はAより大きいが、「split commitをmainへ出さない」を唯一機械保証する |

推奨は D です。A は便利ですが、同一commitという本件の deployment invariant を保証しません。D は次のように狭く設計します。

- candidate codeをimportせず、trusted main側のcheckerが Git blobを読む。
- 各 audited commitについて、親と比較したrecord集合と、`env_contract.py` の exact head tupleだけを比較する。
- record集合が変わったcommitではhead tupleも同じcommitで変わること、その逆も要求する。
- 末尾recordの既存 `activation_serial` / `activation_state_sha256` とsource定数がexact一致することを要求する。
- successor意味論は再実装せず、現行loader/D245へ残す。checkerはcommit topologyだけを所有する。
- `env_contract.py` の世代登録等、head tupleを変えない通常編集は受理する。
- checker導入commitより前のserial 2へ遡及せず、serial ≥ 3のactivation deltaから適用する。

## 3. (P2) quiesce/drain の択一

### A. 手順型 maintenance window — 推奨

親案を採りますが、二点を訂正します。

- `tools/wave_land_window.py` の受入leaseは並行dev-waveの受入・land予約であり、campaign processやPBS jobを排除しません。TTL失効後の旧holderを止めるfencing tokenもありません。[pegasus-runbook.md:739–770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/docs/pegasus-runbook.md:739) activation quiescenceの証明として再利用してはいけません。
- login nodeの `pgrep` だけでは計算nodeやqueued jobを覆いません。runbook自身もprocess確認は計測するcompute nodeで行うよう定めています。[pegasus-runbook.md:614–619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/docs/pegasus-runbook.md:614)

手順は次の順に固定します。

1. official/certified writerの新規submit・resume・forkを人手で凍結する。
2. 全既知submission receiptと`qstat`を照合し、旧source commitを持つqueued/running jobを完了または取消する。
3. 割当済みcompute nodeではprocess確認を行う。これは観測であってglobal proofとは名乗らない。
4. 対象worktreeを列挙し、activation commitからofficial outputを起動できるrootを一つに限定する。旧dev worktreeは残してよいが、official launcherとして使わない。
5. issuer実行、head edit、commit、P1 gate、landをmaintenance window内で行う。
6. activation commitのliteral `(activation_serial, activation_state_sha256)` をexpected値としてfresh-process smokeと照合する。「観測したterminal headをそのまま期待値にする」ことは禁止する。
7. 旧親からのforkではなく、activation commitのroot/source-stageから`exec`で全launcherを起動し直す。
8. 旧job/processがないことを再確認してからsubmit凍結を解除する。

これはmechanical quiescence証明ではなく、最小の運用契約です。

### B. issuerへのlive-process gate — 不採用

提案しません。入力が実在しません。

- 全consumer processを表すmanifest、process registry、deployment generation、全node共通leaseのいずれも現成果物にありません。
- `/proc`/`pgrep` は一nodeの瞬間値で、queued jobを含みません。
- generic dispatchのrequestには`repo_root`がありますがsource commitがなく、T126等のreceiptは個別schemaです。[dispatch_compute.py:1371–1389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/dispatch_compute.py:1371)、[submit_t126_qualification.sh:750–773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/submit_t126_qualification.sh:750)
- ローカル`pgrep`が0件というだけでissuerを通すgateは、他nodeの旧processを見落として偽の保証を作ります。

### C. `contract_sha256` による事後識別だけに委ねる案

補助診断としてのみ採用可能です。quiesceの代替にはしません。

- receipt-bearing artifactでは`contract_sha256`から登録世代を一意に解決できます。[env_contract.py:671–699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:671)
- receiptがない書込み口、据置env、activation stateだけを区別したい場合は識別不能です。
- 混在を検出したら、D195どおり同一commitで全legを再走します。新hashで古い値を書換えたり、混在許容を追加したりしません。[decisions.md:9471–9488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/docs/decisions.md:9471)
- missing receiptを新たに拒否する、全書込み口へactivation fieldを配線する、land側で混在を機械拒否する、の三つは行いません。これは[T-658]見送り範囲です。

## 4. (P3) serial ≥ 3 の順序

追補2を正とします。[stage1-brief.md:29–33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/stage1-brief.md:29) serial 2は[T-657] waveが一回限りの手動同一commit手順で実装中であり、本設計の導入条件にしません。

現時点のregistryはlinux-baremetal g1とPegasus g1/g2だけです。[env_contract.py:240–304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:240) 発行toolは未登録世代を拒否し、D245は全env据置を拒否するため、現材料だけでvalid serial 3を発行することはできません。[issue_env_contract_activation.py:179–200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:179)、[env_contract_activation.py:274–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:274)

推奨順序は次です。

1. [T-657]をそのwaveの不変条件どおりlandし、mainのbaselineをserial 2にする。
2. 本裁定パッケージをユーザーが裁定する。
3. 次弾でP1 gateとP2 runbookだけを実装してlandする。このwaveではactivationしない。
4. 新しいreviewed successor、較正、historical consumer、floor再発行材料が揃った時点で、別の明示的activation waveを起票する。
5. serial 3以降もmaintainerの明示CLIを唯一のtriggerとし、登録や較正完了による自動activationは置かない。

P1/P2がlandする前に二回目の手動activationを許すかが、残るP3裁定です。推奨は「許さない」です。

## 5. gate入力の実在台帳

| gate / 検査 | 使用する既存入力 | 実在箇所 | 判定 |
|---|---|---|---|
| candidate record検証 | `activation_serial`、`previous_activation_state_sha256`、`active_contracts`、`activation_state_sha256` | [env_contract_activation.py:17–28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:17)、issuer [195–212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/issue_env_contract_activation.py:195) | 既存gateを維持 |
| exact head pin | `_ACTIVATION_HEAD_SERIAL`、`_ACTIVATION_HEAD_STATE_SHA256` | [env_contract.py:373–376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:373) | serial+state hashを維持 |
| P1 co-commit gate | Git親/commit tree、activation record path、上記定数 | live path [env_contract.py:377–379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:377)、land audited closure [dev_wave_land.py:932–965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/dev_wave_land.py:932) | 新field不要 |
| deploy後smoke | 裁定済みactivation commitのliteral serial/hashと、loader結果 | state fields [env_contract_activation.py:74–81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract_activation.py:74)、API [env_contract.py:631–633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:631) | 観測値自己信頼にしない |
| worktree列挙 | Git worktree registry、module `__file__` root | [env_contract.py:465–483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/env_contract.py:465) | root列挙は可能、process利用有無は不明 |
| queued job drain | T126等の`source_commit`、scheduler job ID。generic dispatchの`repo_root` | [submit_t126_qualification.sh:750–773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/submit_t126_qualification.sh:750)、[dispatch_compute.py:1374–1380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/tools/pegasus/dispatch_compute.py:1374) | schema横断のaggregate inputなし。手順確認に限定 |
| live-process機械gate | 全node/queue/processのauthoritative roster | 不在 | 提案しない |
| 事後世代分類 | durable `contract_sha256` | [execution_guard.py:204–222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/execution_guard.py:204) | changed envかつreceipt-bearing artifactに限定 |
| `evidence_contract_sha256`利用 | s8c evidence document hash | [s8c_preregistration.py:330–337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t659-activation-deploy-window/orchestrator/campaign/s8c_preregistration.py:330) | env activation gateには使用禁止 |
| serial≥3適用開始 | recordの`activation_serial`とchecker導入commit | record schema上に実在 | 新しい`head`/`serial`/`state`名称を増やさない |

## 6. 次の実装waveのfile:line計画

推奨案が裁定された場合の実装面です。今回のwaveでは行いません。

1. 新規 `tools/check_env_contract_activation_deployment.py:1–約180`
   - trusted-main codeとしてGit blobを読む。
   - checker導入commit以降のrangeだけを検査。
   - record appendとhead tuple変更の同一commit性、旧record不変、terminal tuple一致を検査。
   - successor、較正、active set意味論は再実装しない。

2. `tools/dev_wave_land.py:1709–1722`
   - land lock取得後、audited closure確定後、`git merge`前にcheckerを呼ぶ。
   - ambiguity、parse不能、split commitはfail-closed。
   - candidate branch側のcheckerを実行せず、mainにland済みのcheckerを使う。

3. 新規 `orchestrator/tests/test_env_contract_activation_deployment.py`
   - 同一commit正例。
   - record-only、head-only、record→headの2commit、逆順2commitを拒否。
   - tipだけは整合しているsplit historyも拒否。
   - unrelatedな`env_contract.py`編集は受理。
   -旧record改変・削除と、terminal tuple不一致を拒否。
   - checker導入前のserial 2を遡及拒否しない。
   - activationを持ち込むmerge commitは、設計を単純に保つなら拒否する。

4. `docs/pegasus-runbook.md:739–810`
   - wave受入leaseとactivation maintenance windowを別契約として記載。
   - submit freeze、queue drain、各node確認、worktree scope、exec再起動、expected tuple smoke、解除順を記載。
   - global proofが存在しない既知限界を明記。

5. `tools/issue_env_contract_activation.py:143–152`
   - handoffに「forkだけでは再起動にならない」「P1 checkerを通す」「runbookのmaintenance window内で実行」を追加。
   - issuerのsource editは行わない。

6. `orchestrator/tests/test_env_contract_activation.py:1940–2004`
   - handoff文の新しい必須要素だけを固定。
   - 既存split両方向、cache、fork、source-stageテストは維持する。

## 7. 裁定パッケージの設問案

### R0 — 「全process」のdeployment domain

問い: 保証対象をどこまでとするか。

- A（推奨）: official/certified durable outputを書けるlauncher、子孫、queued/running jobを全worktree/source-stage横断で対象とする。read-only開発processや、official outputを起動しない旧worktreeは対象外。
- B: repoに関係する全processを文字どおり対象とする。この場合、現成果物にglobal process registryがないためT-659の現入力だけでは保証不能。別設計waveが必要。

見送り時の影響: 数値・runtime受理集合は不変ですが、「全process再起動」の意味が検証不能のまま残ります。

### R1 — P1の選択

問い: serial ≥ 3のactivation commitへ、どの結合を要求するか。

- D（推奨）: trusted-mainのco-commit land gate。
- A: issuerによるsource edit自動化だけ。
- B: 現状+runbookのみ。
- C: tracked head data file化。

見送り時の影響: Dは「land可能なGit履歴」をsplit commit分だけ狭めますが、runtime activation recordの受理集合・exact pin・数値は変えません。A/Bではruntime受理集合は不変のまま、人手漏れが残ります。CはT126/silo/T419のidentity入力を変え、将来成果物のsource identity hashまで波及します。

### R2 — P2の選択

問い: activation時の旧process/job混在をどう扱うか。

- A（推奨）: activation専用maintenance windowを手順型で実施し、`contract_sha256`事後分類を補助診断にする。
- C: quiesceを置かず、`contract_sha256`事後分類だけに委ねる。
- 「issuerのpgrep gate」は入力不在のため選択肢に入れない。

見送り時の影響: Aはscheduler上の実行可能時刻だけを狭め、artifact schema・数値・受理集合を変えません。Cではmixed legが生じた場合、D195により全leg再走が必要となり、certified値が確定不能になる時間が増えます。

### R3 — serial ≥ 3 の開始条件

問い: T-659実装land前に、T-657型の手動手順でもう一度activationしてよいか。

- A（推奨）: 許さない。T-657のserial 2だけを一回限りの例外とし、P1/P2 land後に明示activation waveを起票する。
- B: 新材料が先に揃った場合、serial 3をもう一度だけ手動で許す。
- C: 以後もrunbook-onlyで反復する。

見送り時の影響: Aは将来activationの時期だけを遅らせ、現行値・受理集合は不変です。B/Cはschema上は受理可能でも、本waveが閉じようとしている同じ運用窓を再演します。

## 8. 弱点・不確実性

- Git main worktree更新中のcross-file観測窓は、`git merge --ff-only`とreader lock不在からの静的推論です。専用race probeは実走していません。
- SIGKILL後のrecord/stage残骸も制御フローからの推論です。既存fault injectionは捕捉可能な例外までで、process kill境界を測っていません。
- 全launcherのqueue/source挙動は一様ではありません。T126とgeneric dispatchの違いは確認しましたが、全PBS wrapperの完全分類は別監査が必要です。
- [T-658]見送りにより、durable `contract_sha256` の全書込み口被覆率は100%ではありません。本案はその配線を増やしません。
- [T-657]は並行作業中です。land後にhead定数、初期record集合、テスト行番号を再読し、checkerのbaselineをserial 2へ置き直す必要があります。
- P1各案の行数は設計見積りで、T-657 land後に±30%程度動く可能性があります。
- 本回答は静的検査のみで、pytest緑や実機quiescenceを主張しません。

## 総括

- erratum 2として、世代識別fieldを`evidence_contract_sha256`ではなく限定付き`contract_sha256`へ訂正する。
- 窓はauthoring、deployment、旧lineage drainの3 barrierとして扱う。
- P1推奨はtrusted-mainの同一commit land gate。runtime exact pinは変更しない。
- issuerによるsource editは操作短縮にすぎず、atomicity保証には数えない。
- P2推奨はactivation専用maintenance window。既存wave leaseやlogin-node pgrepを証明に使わない。
- [T-658]を復活させず、post-hoc hashは補助診断に限定する。
- [T-657]のserial 2は予定どおり先行し、serial ≥ 3はT-659実装landまで許可しない。
- 実装前にR0〜R3を一問ずつユーザー裁定へ返す。