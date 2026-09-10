## 所見

1. 対象 `s2-plan.md:36`、`orchestrator/campaign/p3_s4_loop.py:90,1058-1090`、`orchestrator/campaign/loop.py:239-260,377-386`: P4 反転後、内部の `main → drive_iteration → run_one_iteration` 連鎖は admission を通るが、module 上へ公開された `p3_s4_loop.run_campaign` へ `default_cfg()` を直接渡す経路は通らない。変更前は linux 契約の再 bind が `ident.py:113-117` で止まったが、変更後は任意の active contractを直接 bindでき、compute 契約でも `_CAMPAIGN_ENV_KEY` が付かない。成果物への影響: fresh root では Pegasus の WAL・性能値が OTHER と同じ campaign-id に置かれ、後続の linux 実行は lock の契約不一致で拒否されるため、受理集合と namespace 分離の主張が崩れる。重大度: must-fix。

2. 対象 `s2-plan.md:59-63`、`orchestrator/campaign/p3_b4_launcher.py:147-174,516-556`、`orchestrator/campaign/p3_b4_closed_critic.py:1984-2032`: Pegasus compute の正式 B4 経路は build へ到達しない。launcher と closed-critic の config factory は base だけ site projectionせず、raw campaign-id へ context・sidecar・receiptを束縛する一方、計画後の base `main` は `measurement_env="pegasus"` を加えた別 ID を `drive_iteration` へ渡す。そこで `p3_s4_loop.py:1814-1825` の launcher gate が campaign-id 不一致を拒否する。成果物への影響: raw ID 側に sidecarが残るが、site-aware ID 側では `run_campaign`、build、WALへ到達しない。重大度: must-fix。

3. 対象 `s2-plan.md:38-65`、移植元 `p3_s4_loop_trigger_gating.py:633-662,900-906,1037-1043`: 移植元の `_assert_layout_matches_campaign` と `_with_campaign_location` が計画から落ちている。移植先の既存検査 `p3_s4_loop.py:1438-1446` は `do_build=True` にしか効かず、site projection後の最終 ID を返却値にも載せない。成果物への影響: `do_build=False` の注入 caller は compute cfg の lock・reject WAL・checkpointを別名 layoutへ書け、戻り値から正しい campaign-id/layoutを回収できない。重大度: must-fix。

4. 対象 `s2-plan.md:59-63,69-83`: `main` の injection は「paired」とだけ書かれ、両指定時の site admission と `contract.env_tag` 照合、その拒否型が明記されていない。移植元で三拒否があるのは `drive_iteration` の `p3_s4_loop_trigger_gating.py:1013-1028` だけで、移植元 `main` には injection 自体がない。単一の atomic-pair testも三入口ごとの検査を要求していない。成果物への影響: `--emit-planner-context` は downstream の drive/run検査へ到達せず早期 returnするため、main側で照合を落とすと不受理 site・不一致契約由来の checkpoint参照や planner contextが生成される。重大度: must-fix。

5. 対象 `s2-plan.md:47`、移植元 `p3_s4_loop_trigger_gating.py:1013-1047`: `run_one_iteration` では paired-injection判定を既存 B4 gateの後へ置く計画だが、移植元 driveは paired判定を B4 gateより前に行う。したがって B4 marked cfgと不正 contextを伴う片側注入は、約束した `TypeError` ではなく `B4LauncherAuthorizationError` が先に出る。成果物への影響: fail-closed自体は維持され、成果物は生成されないが、呼び手の例外契約が一致しない。重大度: nit。

6. 対象 `s2-plan.md:38-47,59-63`、移植元 `p3_s4_loop_trigger_gating.py:863-870,984-1002,1181-1185`: `_resolved_site` / `_contract` が移植元に存在するのは driveだけであり、run_oneとmainへの追加は移植ではなく新しい公開 seamである。成果物への影響:三拒否を正しく実装すれば直ちに値は変わらないが、独立した admission実装面とテスト面が二つ増える。重大度: backlog。

## 親 brief への指摘

実測値は再確認できた。現在の hostnameは `pegasus02`、`site_policy.current_site()` は `PEGASUS_LOGIN`、pegasus契約は `2100 / () / allow_resume=False / required`、linux-baremetal契約は `1800 / ("numactl","--interleave=all") / allow_resume=True / none` である。また `p3_s4_loop.py:62-65` は現状 `execution_guard` と `site_policy` を importしていない。

ラベル値の受理集合については、`s2-plan.md:32` の `{OTHER, PEGASUS_COMPUTE}` は移植元 `p3_s4_loop_trigger_gating.py:444-455` と同一であり、run_oneとdriveについては片側注入 `TypeError`、不受理 siteとenv-tag不一致の `ExecutionGuardError`も計画に書かれている。ただし mainについては所見4の欠落がある。

`s1-brief.md:26-29,41` の「login nodeでは fail-closed」「未知 siteは fail-closed」は現在の観測には正しいが、物理環境全般へは一般化できない。`site_policy.py:39-46` は未知 hostnameを OTHERへ倒し、Pegasus名でもNQSV証拠が取れなければOTHERへ倒す。さらに `_has_nqsv` は観測例外を証拠なしへ変換する `site_policy.py:51-63`。`current_site()` は既定で `require_evidence=False` なので、これは sourceにも計画にも残る物理 site fallbackである。

P1は移す必要がある。ただし、移さない場合に成果物の値が静かに誤るわけではない。Pegasus authorizationへ旧 `CLK=1800` と旧NUMAを渡すと、`execution_guard.py:120-135` が、`loop.py:171-178` の最初の書込み前 gateで拒否するため、新しいWALやbench成果物は生じない。防壁がなければ `pipeline.py:420-422,739-750` のtrace・bench起動値と、それから導く `bench_done.fitness_tps` が誤る。現コードでの実際の帰結は「buildへ到達しない」である。

P2の署名判断は正しい。`loop.py:239-260` は `env_contract` と `dependency_prefix` を受理し、`:531-540` からevaluateへ渡し、`pipeline.py:1201-1256` で `env_contract` がbuild_v2を選ぶ。ただし `s1-brief.md:57-58` は両者を一括して「無ければbuild不可」と一般化しすぎている。`env_contract` はcontract-aware buildに必要だが、空のprefixは `buildcache.py:2283-2286,2470-2478` でambient `CMAKE_PREFIX_PATH` を保持するため、`dependency_prefix` の明示値が常に必須とはいえない。また計画上のmain/CLIには非空prefixの供給口がなく、実効値の所有者はscope外のjob scriptかambient環境である。

親briefの四形だけでは、移植元のsite-aware layout照合、最終campaign位置の返却、B4上流config factoryまで覆えない。したがって「移植」の所有範囲が狭すぎる。

## scope 外だが real な所見

1. 裁定候補: `_assert_resume_allowed` を外した場合、`p3_s4_loop.py:1858-1861` のlock確立とincomplete WAL recoveryはclaim取得前に走り、停止済みなら`:1868-1873`、diff-rejectなら`:1453-1492,1885` でcheckpointやWALも更新できる。一方、valid候補の二度目のbuildは `loop.py:198-229` のone-shot claimと `campaign_claim.py:383-434` に通常拒否される。したがって「常にiterationを増やしてcheckpointを上書きする」という `s2-plan.md:105` の説明は過大であり、正確には「pre-build recovery、停止、reject面は変更可能だが、既存claim下のbuildは止まる」である。

2. 裁定候補: provenanceを外してもattestationとbuildは実行できるが、`loop.py:179-193,383-386,459` のexecution receiptはin-memory summaryにだけ残り、移植先 `p3_s4_loop.py:1503` 以降で捨てられる。移植元は `p3_s4_loop_trigger_gating.py:821-829` でsite、contract hash、receiptを永続化する。結果としてprocess終了後、campaign.lockの契約hashは残るが、実機attestation receiptへのcaller-side参照は残らない。

3. 裁定候補: C5を物理host分類まで強制するなら、`site_policy.current_site(require_evidence=False)` のOTHER fallbackを受容するかは別途判断が必要である。これは今回の移植で新設された穴ではなく、移植元にもある既存境界である。

## 総括

- 最大の欠陥は、P4で未束縛化した `default_cfg()` から公開 `run_campaign` へ直接進め、site admissionとcompute identity markerを迂回できる点である。
- 内部の通常連鎖は閉じているが、module/API全体の受理集合は閉じていない。
- 段4では、この直接seamを閉じるか保証範囲から明示除外するか、さらにB4上流factoryをscopeへ含めるかを必ず裁定すべきである。
- `_assert_resume_allowed` とexecution receipt永続化は実装要求ではなく、Pegasus運用で受容する残存リスクとして別裁定にするべきである。
- pytestは実走しておらず、以上は静的検査とread-onlyのhostname・契約値probeによる。