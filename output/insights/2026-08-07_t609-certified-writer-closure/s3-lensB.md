判定は **NO-GO**。段 2 プランは P1 の build-v2 混同を正しく見抜いているが、writer sink の閉包、永続 proof、shell preflight の実効契約、T126 の履歴互換性が未解決である。以下は静的検査のみで、pytest・shell 実走は行っていない。

### 1. `run_campaign` だけを閉じても writer sink は閉じない

[severity: must-fix]

何が食い違うか:  
プランは 12 module・15 個の `run_campaign()` 呼出しへ必須引数を足せば Python 層が閉じるとしている。しかし実際の certified writer は `pipeline.evaluate()` であり、`run_campaign()` を通らない production 経路が残る。

根拠:

- `pipeline.evaluate()` は `env_contract=None` のまま直接呼べ、最終的に WAL COMMIT する。[pipeline.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:475) [pipeline.py:1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1009) [pipeline.py:1073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1073)
- `screening_driver.evaluate_candidate()` は直接 `evaluate()` を呼ぶ。[screening_driver.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:134) [screening_driver.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:171)
- その経路は `backoff_sweep`、`s6_sort_sweep`、`s8a_trigger_sweep` から現用される。[backoff_sweep.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_sweep.py:94) [s6_sort_sweep.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s6_sort_sweep.py:359) [s8a_trigger_sweep.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8a_trigger_sweep.py:463)
- `s1_direct_comparison.run_role()` も既定 `evaluate_fn=pipeline.evaluate` であり、認証前に campaign layout と session WAL を書く。[s1_direct_comparison.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s1_direct_comparison.py:626) [s1_direct_comparison.py:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s1_direct_comparison.py:657) [s1_direct_comparison.py:789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s1_direct_comparison.py:789)
- プランの AST テスト対象は `run_campaign` だけである。[s2-plan.md:229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:229)

提案:  
`execution_guard` が検証済み authorization receipt/capability を発行し、`pipeline.evaluate()` 自身が必須で再検算する構成にする。加えて各上位入口は、layout/WAL/event の最初の書込みより前に capability を得なければならない。`screening_driver.py`、`s1_direct_comparison.py` と対応テストは A の所有へ追加すべきである。

### 2. `authorization_contract` は「承認」ではなく自由構築可能なデータである

[severity: must-fix]

何が食い違うか:  
P1 の既存 `env_contract` 一斉配線は不要かつ有害である一方、プランの別引数も exact dataclass であるだけで、登録済み契約由来とは限らない。`OTHER` では constructed/stale contract が受理される。

根拠:

- 既存 `env_contract` は build-v2 selector である。[pipeline.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:515) [s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:118)
- `ExecutionEnvironmentContract` は通常の公開 dataclass で自由に構築できる。[env_contract.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:82)
- current-registry equality は `PEGASUS_COMPUTE` でしか要求されない。[loop.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:68)
- プラン自身も OTHER 上の constructed/stale contract を残すと認めている。[s2-plan.md:134](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:134)
- 分離後は `authorization_contract` と build selector `env_contract` が別契約を指せるが、整合検査が計画されていない。[s2-plan.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:84) [s2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:97)

提案:  
P1 の直接配線は実装しない。別 authorization 引数を採るなら、少なくとも `resolve_by_contract_sha256()` で登録済み世代への所属を検査する。[env_contract.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:355) build selector が非 `None` の場合は authorization contract との一致、または許可された cross-contract 関係を要求する。

current 世代だけを許すか、登録済み歴史世代も許すかは受理集合を変えるため、**裁定パッケージ候補**。

### 3. 認証結果が campaign identity・WAL に残らず、事後に「数えられない」

[severity: must-fix]

何が食い違うか:  
プランは mode=`none` の receipt 永続化を外す。そのため入口で引数を検査しても、保存済み certified record がどの契約で認証されたか証明できない。さらに旧・無契約 WAL の terminal recordを新しい認証済み起動がそのまま skip できる。

根拠:

- 現行は mode=`none` で receipt を返さない。[loop.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:84)
- receipt は一時的な `CampaignSummary` にしか載らない。[loop.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:55) [loop.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:188)
- campaign identity は意図的に env を含まない。[ident.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/ident.py:2)
- terminal WAL は認証契約を見ずに skip 集合へ入る。[loop.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:170)
- プランもこの欠落を裁定送りにしている。[s2-plan.md:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:87) [s2-plan.md:317](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:317)
- mode=`none` 用 receipt issuer/validator は既に存在する。[execution_guard.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:68) [execution_guard.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:89)

提案:  
既存 issuer を使い、contract SHA、receipt schema/hash を campaign lock と WAL COMMIT に束縛する。pre-T609 WAL と混在しない新 namespace/identity を作るか、無束縛 WAL の resume を拒否する必要がある。これは resume 受理集合を変えるので **裁定パッケージ候補**。

### 4. P2 は `PEGASUS_COMPUTE` 誤分類で両方向に破れる

[severity: must-fix]

何が食い違うか:  
site 判定は Pegasus 証拠を検査していない。偽 compute は Linux contract を新たに拒否し、実 compute の偽 OTHER は Linux contract を許してしまう。

根拠:

- コメントは hostname と affinity を権威とするが、関数に affinity 入力はなく、`bnode[0-9]+` だけで compute になる。PBS 環境も捨てる。[site_policy.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/site_policy.py:30)
- テストは NQSV/PBS 証拠なしの `bnode123.other.example` を compute と固定している。[test_site_policy.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_site_policy.py:60)
- compute equality を外れた `OTHER` は heavy-work gateで許可される。[buildcache.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:441)

具体例:

- CI/別施設ホスト名が `bnode123` なら、NQSV/PBS 証拠ゼロでも compute と誤認し Linux contract を拒否する。
- Pegasus PBS job が container/UTS namespace の別 hostname を見る場合、`PBS_JOBID` と NQSV があっても `OTHER` になり得る。後者のホスト配置の実在は推測だが、当該入力が `OTHER` になることはコードから確定する。

提案:  
hostname、NQSV、PBS job/binding、affinity/割当ホストを組み合わせた fail-closed 判定へ直し、preflight の injection testとは別に実 `current_site()` 結線を検査する。分類変更は受理集合を変えるため **裁定パッケージ候補**。

### 5. read-only preflight は「実行契約」ではなく静的資料検査に留まる

[severity: must-fix]

何が食い違うか:  
プランの preflight は registry/control/calibration bytesを検査するだけで、required contract の hardware attestation と single-process reservation を成立させない。

根拠:

- プランは明示的に hardware probe を呼ばない。[s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:159)
- required receipt は実 probe が全比較を通った後だけ発行される。[execution_guard.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:435)
- TSC probe は一時 directory、C source、binary を作る。[tsc.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/calibrator/tsc.py:65) [tsc.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/calibrator/tsc.py:88)
- isolation policy は contract の構成要素である。[env_contract.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:47)
- floor の reservation 検査は full attestation 後、出力直前まで遅い。[s8b_floor_campaign.py:2841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:2841) [s8b_floor_campaign.py:2892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:2892)
- T126 も scheduler binding を staging 作成後に組み立てる。[t126_qualification.sh:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:630)

提案:  
静的 preflight と full execution attestation を別名・別状態として記録する。reservation は qstat 出力をファイルへ落とさず既存 `reservation.read_binding/check_reservation()` に渡せるよう前置する。[reservation.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/reservation.py:159)

hardware probe の scratch まで write-zero に含めるなら、read-only な事前ビルド済み probe 等の別設計が必要で、**裁定パッケージ候補**。

### 6. 「最初の書込み」と「writer」の境界が定義されていない

[severity: must-fix]

何が食い違うか:  
job script 内の `mkdir` より前に preflight を置いても、submitter、qsub、PBS、trap の書込みは覆わない。また floor official core は現在無条件拒否なので、現時点では certified writer ではなく staging/failure writerである。

根拠:

- floor job body の最初の明示 mutation は `/scr` mkdir。[floor_campaign.sh:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:29)
- T126 は job-staging mkdir。[t126_qualification.sh:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:74)
- floor submitterは qsub 前に submission directory、captures、receiptを書く。[submit_floor.sh:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_floor.sh:274) [submit_floor.sh:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_floor.sh:369) [submit_floor.sh:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_floor.sh:427)
- T126 submitterも ledger/intent/invocationを qsub 前に書く。[submit_t126_qualification.sh:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:288) [submit_t126_qualification.sh:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:373) [submit_t126_qualification.sh:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:677)
- floor の ERR/signal trap は failure artifactを書く。[floor_campaign.sh:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:114) [floor_campaign.sh:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:180)
- T126 の EXIT trap も terminal resultを書く。[t126_qualification.sh:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:297)
- floor official core は無条件拒否される。[s8b_floor_campaign.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:204) wrapper はその official modeを呼ぶ。[floor_campaign.sh:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:894)
- PBS spool はプラン自身も範囲外と認めている。[s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:145)

PBS による `$TMPDIR` 事前作成、prologue/epilogue、filesystem atime は repo から確認できないため推測だが、少なくとも「存在しない」とは証明できない。

提案:  
台帳には次の限定文言を用いるべきである。

> PBS が job body を開始した後、当該 wrapper が明示的に管理する durable output および scratch を初めて変更する前に、submission/source identity・current registry・protocol/control・calibration bytes・compute-site の静的 read-only admission を完了する。qsub-side receipt/ledger、PBS spool/prologue/epilogue、scheduler-created `$TMPDIR`、filesystem atime、full hardware attestation probe の scratch は対象外である。

これを単に「write-zero」「最初の書込み前に契約保護」と略してはならない。floor を現行 certified writer と数えるか、future staging entry と数えるかも **裁定パッケージ候補**。前者だけが対象なら floor wrapper変更は現時点では実装不要である。

### 7. T126 helper pin は queued job の source-commit 隔離を壊す

[severity: must-fix]

何が食い違うか:  
投入時 commit A の wrapper が spool された後、checkout が commit B へ進むと、wrapper内 pinは A版 helperを要求するが、preflight は source staging 前なので現 worktreeの B版 helperを読む。従来は receipt の commit A を archiveして走れる経路が新たに拒否される。

根拠:

- submitter は投入時 `SOURCE_COMMIT` を取得する。[submit_t126_qualification.sh:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:76)
- qsub はその後に実行される。[submit_t126_qualification.sh:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:683)
- job は receipt の commit を取り出し、そこから source stage を作る。[t126_qualification.sh:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:416) [t126_qualification.sh:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:437)
- driver も stageされた sourceから起動する。[t126_qualification.sh:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:735)
- プランはこれより前に current helper bytes pinを検査する。[s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:182)

提案:  
選択肢は、helper closureを submit receiptと一緒に immutable package化する、wrapper内へ最小 bootstrapを埋める、source staging の書込みを preflight 境界の例外とする、または checkout不変を新規要件にする、のいずれか。最後の案は受理縮小なので **裁定パッケージ候補**。テストには「commit Aでsubmit材料作成→worktreeをBへ進める→Aのjob bodyを起動」を必須追加する。

### 8. helper を T126 v1 required-setへ足すと歴史 series が検証不能になる

[severity: must-fix]

何が食い違うか:  
`REQUIRED_CODE_IDENTITY_PATHS` は単なる future pin一覧ではなく、v1 preimageの exact key集合である。helper追加前の全 v1 seriesには新 keyがないため、current validatorで再検算できなくなる。

根拠:

- プランは helper を required code setへ追加する。[s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:157)
- `series_identity()` は required-setの完全一致を要求する。[contract.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:501)
- 外部 verifier も current required-setとの完全一致を要求する。[identity.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/identity.py:112)
- wrapper 自体は既に script identity対象である。[contract.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:67)

提案:  
helper SHA が wrapper bytesへ埋め込まれるなら、wrapper identityによる推移的 pinで足りるため required code setへ追加しない。直接 keyが必要なら `series-identity/v2` と v1 verifierを併存させる。後者は **裁定パッケージ候補**。

P4 の「凍結 bytes不変」は狭義には正しいが、「既存 T126 台帳を現行 verifierで比較可能」という一般化は反証される。

### 9. 220行・5責務の helper は既存正本の複製になる

[severity: must-fix]

何が食い違うか:  
新 helper内に strict JSON、protocol、registry、calibration、identityを再実装すると、後段 producerと入口で別仕様になる。これは防御の追加ではなく、第二の正本の新設である。

根拠:

- 計画された責務は [s2-plan.md:149](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:149)。
- stable regular-file read と canonical strict JSON は既存。[artifacts.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/artifacts.py:73) [artifacts.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/artifacts.py:537)
- floor current protocol検証は既存。[s8b_floor_campaign.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:340) [s8b_floor_campaign.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:384)
- T126 pure contract validatorも既存。[contract.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:127)
- calibration readerも既存。[env_attestation.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_attestation.py:1023)
- reservation と execution receipt validatorも既存。[reservation.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/reservation.py:218) [execution_guard.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:89)

`build_admission` は source authorityなので今回の env gateの代替ではないが、sealed contextと identityへの policy束縛という既存パターンは再利用できる。[build_admission.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/build_admission.py:147) [ident.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/ident.py:31)

提案:  
新設してよいのは薄い CLI adapterだけ。domain検証は既存関数へ配線し、private floor validatorは public leafへ昇格、T126 receipt/ledgerの inline shell検証は `qualification` 側の純関数へ抽出する。strict JSON readerを新設しない。二重 Python selectorも T-609 の目的には不要で、preflightで選んだ interpreterを後段でも再利用すべきである。

### 10. helper↔wrapper の相互 hash pinの向きが未定義

[severity: should-fix]

何が食い違うか:  
wrapper が helper hashをliteral pinし、helperも wrapper hashをliteral pinすると、どちらを更新しても相手の hashが変わる循環になる。プランは helperが wrapper identityをどこから得るかを定めていない。

根拠:  
helperの wrapper/helper identity検査と wrapper側 pinが併記されている。[s2-plan.md:152](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:152) [s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:157)

提案:  
依存方向を一方向に固定する。

`helper H → wrapperがSHA(H)を埋込 → submit receipt/seriesがSHA(wrapper)を記録 → helperはreceipt由来の期待wrapper hashを検査`

helper内に wrapper hash literalを置かなければ自己参照ではない。これは推測上の危険なので、実装前に planへ明記する。

### 11. A/B の path は字面上素集合だが、所有は独立していない

[severity: should-fix]

何が食い違うか:  
同じファイルを直接編集する予定はないが、B の wrapper/tests は A の helper bytes、imports、contract required-setへ依存する。

根拠:

- plan上の所有 path自体は重複していない。[s2-plan.md:212](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:212)
- floor fixture repoは限定されたファイルしかコピーせず、新 helperと依存 moduleを含まない。[test_pegasus_floor_tools.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_pegasus_floor_tools.py:169)
- T126 fixtureは A 所有 `REQUIRED_*_PATHS` を読み、その全ファイルを生成する。[test_t126_pegasus_tools.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_t126_pegasus_tools.py:651) [test_t126_pegasus_tools.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_t126_pegasus_tools.py:796)
- B wrapperは A helperの exact bytesをpinする計画である。[s2-plan.md:219](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:219)

共通 `conftest.py` は存在するが、今回の編集対象ではなく、この閉包専用 fixture/golden共有は見つからなかった。[conftest.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/conftest.py:108)

提案:  
直列順序を固定する。

1. A が domain API、全 Python入口、CLI/exit codeを確定
2. A の helper bytesをfreeze
3. B が fixture repo、wrapper、hash pin、shell testを更新
4. B 統合で A が変わったら B の pin/test作業を全て再実行
5. 最後に統合受入

「A先行」だけでなく、Aへの feedback時にB成果を無効化する規則が必要。

### 12. 提案テストは実装バグを落とし切れない

[severity: must-fix]

何が食い違うか:

- 引数省略テストは Python signature の `TypeError` を見るだけで、authorization実装や順序を通らない。
- 12 module/15 callの AST テストは、`authorization_contract=None` や forged valueでも keywordの存在だけで通り、新しい direct `pipeline.evaluate` 経路も検出しない。
- pure site injection は壊れた `current_site()` を検査しない。
- source文字列の「helper invocationがmkdirより前」は、`|| true`、無視された非0、前置trap/redirectionによる書込みを落とせない。
- commit A→checkout B の queued-job差分を検査しない。
- planに列挙された current hashを期待literalへ焼くと、正当な registry/helper更新で意味のない失敗になる。

根拠:

- 提案テスト一覧。[s2-plan.md:223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:223)
- injected fixture方針。[s2-plan.md:194](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:194)
- 現行代表テストは `_authorize_measurement` 自体を monkeypatchしている。[test_campaign.py:4100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:4100)

提案:

- `pipeline.evaluate` が authorization capabilityなしでは書けない runtime testを中心に置く。
- caller countではなく、sinkの必須 capabilityにより future callerも自動的に拒否する。
- shell負例は実 wrapperを temp fixtureで起動し、全 script-owned rootの前後snapshot、非0、stderr、trap marker不存在を検査する。
- site testは socket/NQSV/PBS境界だけをpatchし、実 `current_site()` を通す。
- helper 1 byte変更、wrapper失敗無視、trap前置、commit A/B driftをそれぞれ変異として落とす。
- hashは registry/committed fixture bytesから導出し、専用freeze test以外では重複literalを持たない。

### 13. 親の実測と P5 は実装前提として修正が必要

[severity: should-fix]

何が食い違うか:

- 実測1の `None` bypassは正しいが、writer sink全体の一般化は誤り。
- 実測2〜4の「14 caller」「contractを渡すのは2本」「残り全部NUMA一致」は誤り。段2自身が 12 module・15 call、trigger-gating既配線、`sanity_silo` の `numactl=None` を確認している。[s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:47) [s2-plan.md:62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:62)
- 実測5は正しいが、それ自体が `pipeline.evaluate` 一般経路の未閉包を示す。
- 実測6の既存 monkeypatch被覆は正しい。
- 実測7は floor最初のwriteを line 88ではなく line 30で見落としていた。
- 実測8の FROZEN bytes不変は狭義には正しいが、T126 exact-set互換性を含まない。
- P5 の「Pegasus login nodeで全走」は固定できない。runnerがメモリ量により local/dispatchを選ぶ。[AGENTS.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/AGENTS.md:31) [AGENTS.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/AGENTS.md:36)

提案:  
brief の実測台帳を修正し、受入は「`tools/run_tests.py` が決めた場所で実行、qsub実走なし」と書く。raw pytest禁止は維持する。[AGENTS.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/AGENTS.md:39)

## 総括

must-fix は **10件**。

1. `run_campaign` 外の writer sink未閉包
2. 自由構築 contractを承認扱い
3. contract/receiptの campaign identity・WAL未束縛
4. `PEGASUS_COMPUTE` 誤分類
5. 静的 preflightと実行契約の混同
6. write-zero/writer境界の未定義
7. queued T126 の source-commit隔離破壊
8. T126 v1 required-setの履歴破壊
9. 220行 helperによる既存正本の複製
10. 実効性の不足したテスト計画

反証できた provisional 判断:

- **P1:** 反証。既存 `env_contract` 一斉配線は build-v2 migrationになる。
- **P2:** 反証。site誤分類、未列挙direct writer、sanity値差、queued checkout driftがある。
- **P3:** 反証。成立するのは限定された「job-body/script-owned static admission before mutation」だけ。
- **P4:** 部分反証。FROZEN bytes不変は維持できるが、T126 v1 verifier/series比較可能性は壊れる。
- **P5:** 部分反証。qsubなしは妥当だが、実行場所は login固定でなく runner判断である。

判断は **NO-GO**。少なくとも writer sink閉包、永続契約束縛、shell claim境界、T126 source/identity互換性を再設計し、受理集合を変える選択肢は段4の裁定へ返すべきである。

実装しないほうがよい項目:

- P1 の既存 `env_contract` 一斉配線
- 独立した220行の5責務validator、重複strict JSON reader
- helperの T126 v1 `REQUIRED_CODE_IDENTITY_PATHS` 追加
- helper/wrapper双方への相手hash literal埋込み
- 同じ interpreterの二重selector
- 現行 TSC probeを「write-zero preflight」として前置すること
- hard-coded caller件数・working-tree hash・時刻・hostnameだけに依存するテスト
- 凍結成果物・既発行receiptの書換え

本レビューは read-only の静的検査であり、テストは未実走、緑とは判定していない。