## 1 束縛の鎖

現行 HEAD `259e02209c0202762e9a4b051f71e2f2657c69ee` には、materialized build に限れば次の鎖があります。ただし末端は consumer による実行証明ではなく producer 契約であり、さらに no-build 経路では鎖全体が省略されます。

1. 宣言 arm

   manifest の `arm` と `holdout` を閉集合として読み、H1/H2 × on/off/swapped の 6 cell を要求します。registry とも arm を含む完全 tuple で一致させます。

   - `orchestrator/campaign/trial_registry.py:743-781`
   - `orchestrator/campaign/trial_registry.py:1546-1554`
   - `orchestrator/campaign/trial_registry.py:1557-1579`

2. 宣言 arm → 権威 descriptor bytes

   受入側が `trial.arm` と `trial.holdout` から `resolve_arm_input` を呼び直します。

   - 呼び出し: `orchestrator/campaign/trial_registry.py:5444-5464`
   - on/off/swapped の選択、canonical bytes、content digest、arm binding digest の導出: `orchestrator/campaign/s8c_arm_inputs.py:434-493`
   - arm binding digest の preimage: `orchestrator/campaign/s8c_arm_inputs.py:424-431`

3. 権威 descriptor → report/run-start/cell/provider/proposal

   受入は report と run-start の自己申告が一致するだけでなく、上で再導出した値との一致を要求します。cell descriptor は bytes を canonical 化して再ハッシュします。

   - report/run-start と再導出値: `orchestrator/campaign/trial_registry.py:5905-5925`
   - cell descriptor bytes の再計算: `orchestrator/campaign/trial_registry.py:5961-5994`
   - `assert_execution_digest_chain` の必須呼び出し: `orchestrator/campaign/trial_registry.py:5998-6005`
   - provider payload bytes 内の descriptor 再計算: `orchestrator/campaign/autonomous_trial_completeness.py:938-1020`
   - proposal file 名、file hash、descriptor/arm digest: `orchestrator/campaign/autonomous_trial_completeness.py:902-935`

4. proposal coder wire → CCBench source preimage

   `verify_s8c_cross_binding` は正式受入ループから各 trial について呼ばれます。

   - 必須呼び出し: `orchestrator/campaign/trial_registry.py:6095-6104`
   - proposal bytes の再読と wire からの predicate 再導出: `orchestrator/campaign/autonomous_trial_completeness.py:3453-3577`
   - source preimage artifact の全 file hash 検査: `orchestrator/campaign/autonomous_trial_completeness.py:3339-3403`
   - 再導出 predicate が `cc/silo/transaction.cc` segment にだけ存在することの照合: `orchestrator/campaign/autonomous_trial_completeness.py:3639-3693`

5. source preimage → WAL source binding → build attempt

   source preimage の consumer 計算 SHA-256 を、WAL の `source_bytes_sha256`、`src_token`、`build_start.src_token` と照合します。

   - `orchestrator/campaign/autonomous_trial_completeness.py:4048-4075`
   - WAL binding/start の topology と source receipt 照合: `orchestrator/campaign/wal.py:1235-1374`

6. build attempt → bench attempt

   同じ `build_attempt_id` の bench が report harness と WAL に一意に存在すること、materialized cell ごとに最低 1 件 built-and-benched があることを要求します。

   - `orchestrator/campaign/autonomous_trial_completeness.py:3696-3773`
   - `orchestrator/campaign/autonomous_trial_completeness.py:4076-4108`
   - candidate ゼロ拒否: `orchestrator/campaign/autonomous_trial_completeness.py:4130-4136`

7. 途切れる辺: WAL source identity → 実際の compiler input → bench binary

   この辺は acceptance consumer が再検証していません。標準 producer は source evidence を作り、CMake の `-S` にその checkout を渡し、build 後に再照合し、返された `pf.binary` を bench します。

   - SourceEvidence 自身が mutable checkout の ABA/mixed-snapshot 窓を閉じないと明記: `orchestrator/campaign/source_digest.py:114-121`
   - source evidence の解決と WAL への source binding: `orchestrator/campaign/pipeline.py:1086-1103`, `orchestrator/campaign/pipeline.py:1127-1171`
   - 実 build の source root と build 後再照合: `orchestrator/campaign/buildcache.py:3049-3068`, `orchestrator/campaign/buildcache.py:3131-3164`
   - 返された perf binary を bench: `orchestrator/campaign/pipeline.py:1664-1689`
   - bench 実行と WAL 記録: `orchestrator/campaign/pipeline.py:739-754`, `orchestrator/campaign/pipeline.py:835-871`

   acceptance は buildcache completion、compiler input manifest、perf binary bytes を再読しません。`bench_done` に binary SHA-256 もなく、`build_done.perf_bin_sha256` と bench 実体を結ぶ consumer 照合がありません。

## 2 各辺の強さ

最優先の弱点は次の 3 件です。

| 辺 | 分類 | 根拠 |
|---|---|---|
| predicate digest equality | 述語が候補集合に含意されて恒真になっている辺 | proposal 側は mask から digest を再導出します (`autonomous_trial_completeness.py:3535-3540`)。WAL binding 側も constructor が digest を同じ mask の関数に固定します (`trigger_gate_binding.py:155-160`)。その後 mask 自体の一致を要求するため (`autonomous_trial_completeness.py:4015-4022`)、直前の predicate digest equality (`4007-4014`) は独立な証明を追加しません。 |
| WAL attempt/harness/bench の対応 | producer が書いた値どうしの照合 | verifier 自身が `attempt_topology_proof_kind = producer-self-consistency` と明記しています (`autonomous_trial_completeness.py:4157`)。 |
| source identity → 実 build/bench | producer の実行時契約に依存する辺 | verifier 自身が `build_execution_proof_kind = producer-execution-contract` と明記しています (`autonomous_trial_completeness.py:4158`)。acceptance consumer は compiler input や bench binary を再認証しません。 |

残りは以下です。

- manifest arm → expected descriptor/digests は、consumer が権威側から再導出した値との照合です。`trial_registry.py:5916-5925`。
- expected descriptor → cell/provider/proposal は、producer artifact の bytes を consumer が再読・再ハッシュして権威 digest と照合しています。`autonomous_trial_completeness.py:950-1020`, `trial_registry.py:5977-5994`。
- proposal wire → source preimage は consumer 再導出です。`autonomous_trial_completeness.py:3535-3540`, `3639-3693`。
- source preimage digest → WAL source fields は、consumer が artifact bytes から計算した値と producer WAL の照合です。`autonomous_trial_completeness.py:4048-4075`。
- provider raw response → proposal coder wire も consumer 独立照合ではありません。cross-binding は raw response と proposal を別々に読みますが (`autonomous_trial_completeness.py:4288-4344`)、raw bytes を再 parse して proposal の `coder` と比較しません。実際の連結は producer が parsed coder から proposal を書く処理に依存します。`p3_autonomous_workload_trial.py:3970-3984`, `4071-4085`。

なお、発行後の receipt verifier は cross-binding receipt 本文を保持・再検証せず、leaf digest 文字列から aggregate を計算し直すだけです。`orchestrator/campaign/s8c_acceptance_receipt.py:1199-1218`。初回受入時の検査を迂回するものではありませんが、後続検証は cross-binding 本文の自己完結した証明にはなっていません。

## 3 迂回経路

あります。

- build を行わない受理

  `do_build=False` では `verify_s8c_cross_binding` が全 field を `unbound_fields` に入れた no-build receipt を返すだけです。

  - `orchestrator/campaign/autonomous_trial_completeness.py:4165-4189`
  - early return: `orchestrator/campaign/autonomous_trial_completeness.py:4225-4230`

  `assert_trial_registry_acceptance` はこれを拒否せず、`no-build` reason を加えて acceptance receipt を発行します。

  - no-build 分岐: `orchestrator/campaign/trial_registry.py:6006-6013`
  - cross-binding 後も accepted へ追加: `orchestrator/campaign/trial_registry.py:6095-6104`
  - reason の追加と receipt 発行: `orchestrator/campaign/trial_registry.py:6210-6219`, `6256-6267`

  したがって、この関数による正式受入 receipt 発行に cross-source binding は必須ではありません。receipt は `certifying=False` であり、`no-build` が明示されますが、受入処理自体は成功します。`trial_registry.py:6251-6254`。

- 失敗 cell の読み飛ばし

  do-build の campaignless failure fallback は一旦収集対象外になりますが、後で明示的 hard failure になります。これは迂回できません。

  - 検出: `orchestrator/campaign/trial_registry.py:6021-6027`
  - hard failure: `orchestrator/campaign/trial_registry.py:6080-6085`

- 呼び手が差し込んだ driver

  materialized build では standard driver literal を要求するため通りません。`autonomous_trial_completeness.py:4262-4269`。ただし no-build return はこの検査より前なので、no-build なら injected driver でも cross-binding 側では拒否されません。`4229-4230`。

  report/start/finish の driver 一致自体は producer 自己整合です。`autonomous_trial_completeness.py:2299-2312`。

- 候補ゼロ

  materialized build では role attempt、proposal、cell proposal、built-and-benched の各非空条件があり、空振りできません。

  - role attempt: `autonomous_trial_completeness.py:3436-3450`
  - proposal: `autonomous_trial_completeness.py:3575-3577`
  - cell proposal: `autonomous_trial_completeness.py:3858-3866`
  - built-and-benched: `autonomous_trial_completeness.py:4130-4136`

  候補ゼロが許されるのは、上記 no-build receipt の経路です。

## 4 結論

**検査は存在しない、または必須経路にない**。

1. materialized build には proposal → source preimage → WAL attempt → bench attempt の cross-binding 検査があり、正式受入から呼ばれています。
2. しかし `do_build=False` は全 field が unbound のまま acceptance receipt 発行まで到達するため、正式受入全体の必須経路ではありません。
3. materialized build でも、実 compiler input と実 bench binary への最終辺は consumer 証明ではなく `producer-execution-contract` です。mutable source の ABA 窓と、bench binary bytes の再認証欠落が残ります。

## 総括

結論: cross-binding は実装済みだが、8c 正式受入の全経路では必須ではない。  
最大の懸念: no-build が unbound のまま受理され、build 経路も source → 実 binary → bench は producer 契約止まりである。  
pytest は実走しておらず、判定は現行 HEAD の静的検査による。