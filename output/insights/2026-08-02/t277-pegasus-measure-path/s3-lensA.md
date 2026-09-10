## 所見

### [A-1] `site` 注入により最下流の build gate を偽装できる

深刻度: **BLOCKER**

根拠:

- [s2-plan.md:30-42](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:30) は、公開 API で受け取った `site` を `pipeline.evaluate` から `build_v2` へ伝播させる。
- [buildcache.py:335-337](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:335) の `_resolve_site` は、明示された `site` を現在地と照合せず、そのまま信頼する。
- [buildcache.py:779-788](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:779) の最終的な heavy-work gate も、その注入値だけを見る。
- [pipeline.py:473-496](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:473) の Pegasus 契約照合は `qualification_policy is not None` の場合だけである。
- [env_contract.py:1-9](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/env_contract.py:1) 自身も、契約 dataclass は enforcement ではないと明記している。
- 過去型では F14「効かない flag を guard と呼ぶ」、F21「実成果物に結び付かない gate」に該当する（[failures.md:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/failures.md:147)、[failures.md:263](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/failures.md:263)）。

具体的な失敗シナリオ:

Pegasus ログインノード上の直接 caller が、`qualification_policy=None`、`site=PEGASUS_COMPUTE`、Pegasus の `env_contract/env_tag/clocks_per_us` を渡して `pipeline.evaluate` を呼ぶ。実在する attestation・reservation・claim を一度も得ずに `_run` が build を許可し、検証が通れば Pegasus 契約名付きの WAL と binary receipt が生成される。

計画された通常 trigger 経路では `load_verified_calibration` を `run_campaign` 前に呼ぶため、そこだけを「事後の飾り」とは断定しない。しかし enforcement は公開 sink まで閉じておらず、保証は全称命題になっていない。

提案:

`site` を権限値として公開引数にしない。最終 sink で `current_site()` を再取得し、caller の値は照合用 expected value に格下げする。Pegasus build は偽造不能な execution capability と attestation receipt を `_run` 自身が検査し、generic `evaluate` から裸で到達できない構造にする。

---

### [A-2] `LOGIN/SUSPECT` 拒否は PATH と hostname で fail-open する

深刻度: **BLOCKER**

根拠:

- [site_policy.py:16-17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/site_policy.py:16) は hostname の正規表現だけで login/compute 候補を決める。
- [site_policy.py:29-45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/site_policy.py:29) は `bnode[0-9]+` を affinity や scheduler allocation と無関係に `PEGASUS_COMPUTE` とする一方、Pegasus login 名でも NQSV が見えなければ `OTHER` に落とす。
- NQSV 判定は [site_policy.py:48-54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/site_policy.py:48) の `PATH` 上の `qsub/qstat` の有無だけである。
- その fail-open 挙動は既存テストにも固定されている（[test_site_policy.py:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_site_policy.py:45)、[test_site_policy.py:114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_site_policy.py:114)）。
- [site_policy.py:74-76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/site_policy.py:74) は `OTHER` を heavy-work 許可側に置く。

具体的な失敗シナリオ:

`pegasus01` 上で module/PATH 設定漏れにより `qstat` が見えない。分類結果は `OTHER` となり、S1 の許可集合 `{OTHER, PEGASUS_COMPUTE}` を通過する。`_admit_env_contract(OTHER)` は Pegasus 契約を要求せず、build・bench がログインノードで実行され、linux-baremetal 扱いの WAL が生成される。逆方向には、攻撃者が hostname を `bnode123` にできる非 Pegasus 機で `PEGASUS_COMPUTE` が成立する。

提案:

Pegasus 系 hostname で scheduler authority を確認できない場合は `SUSPECT` に閉じる。compute 判定には allocation ID、scheduler が与えた host、boot ID、affinity/cpuset を束縛した wrapper receipt を要求する。`OTHER` の heavy-work 許可を維持するなら「Pegasus ではない」ことを積極的に証明させる。

---

### [A-3] `measurement_lease` は取得証明ではなく、caller が構築できる dataclass である

深刻度: **BLOCKER**

根拠:

- [s2-plan.md:65-75](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:65) は lease の campaign ID、PID、starttime、reservation field を検査するが、排他的取得の実在を検査するとは書いていない。
- [campaign_claim.py:62-67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/campaign_claim.py:62) の `AcquiredClaim` は public な frozen dataclass であり、誰でも直接構築できる。
- 実際の `O_EXCL`、書込み、fsync は [campaign_claim.py:167-227](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/campaign_claim.py:167) の `acquire_claim` を通った場合だけである。
- 既存 floor consumer は外から lease を信じず、その場で `acquire_claim` している（[s8b_floor_campaign.py:2821](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8b_floor_campaign.py:2821)）。
- 新規テスト案は通常の claim 衝突を扱うが、public constructor による偽造入力を含まない（[s2-plan.md:175-184](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:175)）。これは F9/F21/F72 の再発である。

具体的な失敗シナリオ:

二つのプロセスが、それぞれ自 PID と starttime を持つ `ClaimRecord` と `AcquiredClaim` を直接構築して loop sink に渡す。どちらも field 検査を通り、同じ campaign を同時に計測する。両成果物には `single_process=true` と claim provenance が記録されるが、排他取得は一度も行われていない。

提案:

lease を caller から受け取らず、authoritative sink 内で取得する。どうしても渡すなら、共通 durable claim root、正規化パス、所有権、`O_NOFOLLOW`、canonical bytes、inode/device、現在保持中の lock を sink で再検証する。偽造 `AcquiredClaim` と claim file 不在を positive-control テストに入れる。

---

### [A-4] fixture auditor と build の programmatic bypass が残る

深刻度: **BLOCKER**

根拠:

- [p3_autonomous_workload_trial.py:361-369](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_autonomous_workload_trial.py:361) の fixture auditor は常に `verdict: pass` を返す。
- [p3_autonomous_workload_trial.py:990-1005](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_autonomous_workload_trial.py:990) の `run_trial` は `provider_kind` と実際の `providers` を独立に受け取る。
- fixture build の拒否は CLI main の [p3_autonomous_workload_trial.py:1111-1114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_autonomous_workload_trial.py:1111) にしかない。
- D106 も programmatic `run_trial(do_build=True)` が開いていることを既知の穴として記録している（[decisions.md:4838](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/decisions.md:4838)）。
- 計画は compute capability を `run_trial` に増やすが、この既知 sink を閉じていない。

具体的な失敗シナリオ:

caller が `provider_kind="claude-headless"` と報告させつつ、実体は fixture providers、`do_build=True` で `run_trial` を直接呼ぶ。no-op auditor が pass を返し、build/verifier が通れば「Claude planner/auditor を経た」ように見える COMMIT/report が生成される。

提案:

CLI、`run_trial`、`_run_workload` の全三入口で同じ closed policy を強制する。`provider_kind` は provider instance から導出し、fixture を含む場合は build/measure/COMMIT を構造的に不可能にする。F72 型の入口列挙テストを置く。

---

### [A-5] D108 の禁止構造と domain result が未解決のまま

深刻度: **BLOCKER**

根拠:

- D108 は supervisor/LLM を login、mechanical worker を compute と分離する（[decisions.md:4955-4970](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/decisions.md:4955)）。
- 同時に、diff reject・build error・verifier red が child rc 0 で戻るため、campaign task より先に domain-result 契約が必要だとしている（[decisions.md:4978-5008](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/decisions.md:4978)）。
- runbook も compute 上の `claude -p` 禁止を解除していない（[pegasus-runbook.md:390-405](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/pegasus-runbook.md:390)）。
- trigger main は outcome を表示しても reject を exit failure に反映しない（[p3_s4_loop_trigger_gating.py:600-615](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_s4_loop_trigger_gating.py:600)）。
- autonomous report は reject/abort を `complete` から除外せず（[p3_autonomous_workload_trial.py:711-720](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_autonomous_workload_trial.py:711)）、main は `complete` なら rc 0 を返す（[p3_autonomous_workload_trial.py:1148-1153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_autonomous_workload_trial.py:1148)）。
- 計画自身が D108 を supersede するか worker-only と読むか未決定のままである（[s2-plan.md:107-110](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:107)、[s2-plan.md:230-234](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:230)）。

具体的な失敗シナリオ:

diff 検疫 reject または verifier-red が発生する。内部 outcome は rejected/aborted だが、top-level report は `complete`、process は rc 0 で終了する。scheduler 側は transport success を科学的成功として記録し、COMMIT 不在の run が成功件数に入る。逆に full 8c を compute へ丸ごと置けば Claude provider 実行禁止に違反する。

提案:

実装前に D108 の設計決定を確定する。login supervisor と compute worker を分け、閉じた domain result に `outcome/stage/reason/WAL digest/provenance digest` を必須化する。transport rc と科学的 verdict を別フィールドで扱い、上位 consumer が後者を必ず検査する。

---

### [A-6] reservation が host と wrapper authority を検証していない

深刻度: **MAJOR**

根拠:

- 計画は reservation が PBS job、host、boot、deadline を検証すると主張する（[s2-plan.md:78-84](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:78)）。
- しかし [reservation.py:218-270](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/reservation.py:218) は現在の PBS job ID、boot ID、時刻、capacity を見るだけで、binding の `host` を現在 hostname と照合せず、`script_sha256` や nonce の発行 authority も検証しない。
- 計画はこの module を変更しない（[s2-plan.md:97-105](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:97)）。
- `required_s` と `safety_margin_s` の算出式も計画にない。D106 は `max_wall_s` が hard safety ではないことを既に記録している（[decisions.md:4824](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/decisions.md:4824)）。

具体的な失敗シナリオ:

現在の PBS job ID と boot ID だけをコピーし、host と script hash を別ジョブ由来にした binding、または `required_s=1` の過小申告を与える。検査は通り、残時間が不足した run が開始される。ジョブ終了で途中成果物を失う一方、receipt には reservation-bound と記録される。

提案:

wrapper が署名または owner-only atomic file で発行した reservation capability を要求し、host、job ID、boot ID、script hash、deadline、nonce をまとめて照合する。stage ごとの最大時間から required budget を決め、build 前・bench 前・COMMIT 前に再検査する。

---

### [A-7] durable proof の主張に path enforcement がない

深刻度: **BLOCKER**

根拠:

- `/scr` は job-local で終了時に削除され、唯一の copy を置けない（[pegasus-runbook.md:228-238](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/pegasus-runbook.md:228)）。
- 計画は cache/dependency だけを `/scr` に置き、WAL・report・claim は repo/output に永続化すると述べる（[s2-plan.md:210-214](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:210)）。
- しかし CLI は任意の `--run-root` を受け取る（[p3_autonomous_workload_trial.py:1104-1118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/p3_autonomous_workload_trial.py:1104)）。
- layout 作成は [layout.py:197-200](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/layout.py:197) の `os.makedirs` であり、symlink/mount 境界を拒否しない。
- リポジトリには durable-root 検証器があるが（[durable_root.py:196-231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/durable_root.py:196)）、計画は authoritative entrypoint で使わない。
- また full build identity は成功後の `STAGE_BUILD_DONE` にしか投影されない計画である（[s2-plan.md:30-42](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:30)）。trace build 後に perf build が失敗すると、`/scr` の staging とともに失敗 preimage が消える。

具体的な失敗シナリオ:

`--run-root /scr/<job>/trial`、または `output/campaigns` を `/scr` への symlink にして実行する。run 中は report/receipt/WAL が見えるが、ジョブ終了後に消失し、残った summary から claim・attempt・build identity を再構成できない。別シナリオでは trace build 成功後の perf build-error により、成功時だけ書く identity が一度も durable WAL に残らない。

提案:

全 entrypoint で `durable_root` allowlist を強制し、`/scr`、`:` を含む path、symlink、mount crossing を最初の write 前に拒否する。build の完全な予定 identity は `BUILD_START` に durable 記録し、失敗時にも toolchain/dependency manifest と stage receipt を残す。fresh namespace の作成・清掃責任も wrapper に一本化する。

---

### [A-8] dependency prefix は文字列だけで、trace/perf の同一依存物を証明しない

深刻度: **MAJOR**

根拠:

- 計画は `dependency_prefix` を v2 identity に追加するが、その内容 hash ではなく path string だけである（[s2-plan.md:12-28](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:12)）。
- この欠陥は計画自身も未解決リスクとして認めている（[s2-plan.md:232-240](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:232)）。
- pipeline は trace binary と perf binary を順に別 build する（[pipeline.py:559-598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:559)）。
- `_assert_trace_diff` は CCBench source diff、`_assert_no_trace_symbols` は `izanagi_trace` symbol だけを見る（[pipeline.py:699-715](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:699)、[pipeline.py:748-776](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:748)）。外部 headers/libs の同一性を検査しない。

具体的な失敗シナリオ:

`/scr/job/deps` に依存物 A を置いて trace build し、同じ path の内容を B に置換して perf build する。identity 上の prefix は同一で、source diff と trace symbol 検査も通る。結果として trace/perf は異なる依存物で作られたのに、「trace だけが差分」という receipt が生成される。ジョブ終了後は A/B の実体も失われる。

提案:

依存 headers/libs、source HEAD、configure argv を含む immutable dependency manifest を hash 化し、trace 前と perf 後に再照合する。owner-only namespace と atomic publish を使い、その digest を build identity、WAL、receipt に束縛する。

---

### [A-9] `certify_calibration.sh` は planned route の生死確認にならない

深刻度: **MAJOR**

根拠:

- certify は Release、sanitizer off、`IZANAGI_TRACE=0`、`BACK_OFF=0` 等で `ycsb_silo` 一つを build する（[certify_calibration.sh:495-517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/certify_calibration.sh:495)）。
- trigger genome は `BACK_OFF=1` と trigger-gating option を使う（[axis_trigger_gating.py:31-32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/axis_trigger_gating.py:31)）。
- planned route は trace-enabled と trace-disabled の二 build、claim、attestation、reservation、domain result を必要とする。
- CCBench の third-party 構成には FetchContent 経路もある（[ThirdParty.cmake:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/bench/ccbench/cmake/ThirdParty.cmake:35)）。
- 親 brief の P3 は既存 certify 成果物で代替しようとしている（[brief.md:46-48](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/brief.md:46)）が、計画自身も同一経路でないと認める（[s2-plan.md:218-224](/home/SFC/tanab/.claude/jobs/c63830dc/tmp/wave-t277/s2-plan.md:218)）。

具体的な失敗シナリオ:

certify の単一 perf build は成功しているため operational と判断する。しかし planned route の trace configure、trigger option、staged dependency、または二段目 build だけが失敗する。初回本計測で build-error となり、A-5 の rc/status 問題により scheduler には成功として帰る。

提案:

D108 が要求する disposable worker で、planned v2 entrypoint、同じ genome/configure、trace/perf 二 build、claim/attestation/reservation、domain result までを一度通す。certify 実績は toolchain の部分証拠に格下げする。

## 親 brief の誤り

- **「LOGIN/SUSPECT は拒否のまま」という一般化は反証できる。** enum 値そのものへの拒否は残るが、Pegasus login は PATH から `qsub/qstat` が消えるだけで `OTHER` になり、許可側へ落ちる（[test_site_policy.py:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_site_policy.py:45)）。「Pegasus login で heavy work は拒否される」という環境保証にはなっていない。

- **「env_attestation の既存 consumer は s8b のみ」は誤り。** T126 driver も import し、calibration load・probe・compare を行っている（[t126_driver.py:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/t126_driver.py:27)、[t126_driver.py:439](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/t126_driver.py:439)）。

- **`contract_sha256` consumer の列挙も閉じていない。** silo ladder は契約を読み（[silo_ladder_rung1.py:1967](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/qualification/silo_ladder_rung1.py:1967)）、その evidence test も artifact binding を検査する（[test_silo_ladder_rung1_evidence.py:1219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1219)）。F30「direct reference だけで consumer を数える」の再発である。

- **「既存被覆はここまで」は過少申告である。** direct trigger 境界以外にも、site classification と heavy-work gate のテストが存在する（[test_site_policy.py:59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_site_policy.py:59)、[test_build_site_gate.py:171](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_build_site_gate.py:171)）。しかも一部は今回攻撃した fail-open を仕様として固定している。

- **P3 の代替証拠は反証できる。** certify と planned route は configure option、trace 二 build、対象入口、claim/attestation/reservation のいずれも同一でない。

- **「registry を触らなければ contract SHA は不変」「凍結 bytes 0 変更」は、現プラン記載どおり実装される限り反証できず。** ただし consumer 列挙が誤っているため、その不変性検査の分母を brief の grep 結果だけに依存してはならない。

## GO / NO-GO

**NO-GO。** site と lease が偽造可能で、D108 の実行配置・domain-result 契約も未決定である。  
さらに durable proof と trace/perf 依存物同一性が保証されず、誤った成功成果物を生成できる。  
静的レビューのみ実施し、pytest を含むテストは実行していない。

## 総括

- 通常経路の attestation 順序は build 前だが、下位 sink と programmatic entrypoint が迂回路として残る。
- 最大の破綻は、`site` と `AcquiredClaim` を「権限」ではなく caller の申告として信頼する点である。
- PATH 依存分類により、Pegasus login は明示的拒否を受けず `OTHER` へ逃げられる。
- D108 を未決定のまま新しい決定文で曖昧化しても、禁止された実行配置と rc 0 問題は消えない。
- `/scr` の内容 hash と durable-root enforcement がないため、観測者効果と proof chain の双方を証明できない。
- 現プランは F9/F14/F21/F22/F30/F72 型の既知失敗を複数再演している。