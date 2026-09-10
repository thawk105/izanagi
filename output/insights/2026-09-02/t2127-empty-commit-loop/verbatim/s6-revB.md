## consumer 取り残しの検査

名前検索の和集合22 file、意味的 consumer 1 file、間接 consumer 2 fileを確認した。関数内 import、module 別名、動的 module 保持、中継関数も追跡した。部分適用と package 再 export は存在しない。

- 22 file: `artifact_admission.py`、`autonomous_trial_completeness.py`、backoff 系5 file、`layer3_report.py`、P3 系7 file、`paper_story_a2_certification.py`、`replay.py`、`s1_report.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`s8b_oracle_report.py`、`critic/digest.py`。
- 関数内 import の追加1 file: `orchestrator/verifier/commit_receipt.py:387-438`。`_assert_replay_admission_source` が exact view、同一 record、`STAGE_COMMIT` を要求するため、0件 viewからは到達不能。
- 間接 consumer: `orchestrator/campaign/search_baselines.py:303-305` と `orchestrator/campaign/guided.py:204,225,252`。いずれも `replay.load_landscape` の新 gate で覆われる。
- 再 export 相当: `p3_s4_loop_trigger_gating.py:59,1141-1149` は `p3_s4_loop` module属性経由。
- 動的保持: `p3_b4_wiring_probe.py:1178-1200,1453-1497` は importlibで保持した `artifact_admission` からviewを発行し、中継関数へ渡す。
- 0件を自前処理する代表例は `backoff_sweep_report.py:65-79`、`backoff_overthrottle.py:150-159,166-180`、`backoff_extended_sweep_report.py:459-512`、`s6_sort_sweep.py:527-567`、`s8a_trigger_sweep.py:629-669`、`critic/digest.py:688-747`。追加の存在 gate は不要。
- 新しい存在 gateが必要な2箇所は `replay.py:179-187` と `layer3_report.py:742-752` に配線済み。

**RB-01**

- 主張: 件数 field が「共通入口の投影であり、検証の証拠ではない」という裁定上の制限がdocstringに欠落している。さらにhelperのdocstringは「admitted COMMIT」と表現し、独立した検証証拠のように読める。
- 根拠の file:line: `adjudication.md:118-130`、`orchestrator/campaign/artifact_admission.py:331-338,1368-1377`。現行docstringは存在保証だけを説明し、件数が検証通過を証明しない点を記していない。
- 誤っていた場合に何が壊れるか: 将来consumerが件数またはhelperだけを検証済み証拠として扱い、単数helperの証拠検査を省略しうる。現在の2 production callerはproduction admission直後なので、直ちに受理集合が広がる問題ではない。
- 親が何を測れば決着するか: 不正なCOMMIT record、snapshot一致count 1、公開tokenからprivate viewを構築し、`require_certified_commit_evidence` が返ることを確認する。これはcode強化ではなく、裁定どおりdocstringへ非保証を明記すべき根拠になる。
- 判定: **must-fix**。token強化や新gateは足さず、契約記述だけを裁定へ合わせる。

## constructor 波及の検査

`CertifiedCampaignView(` は全6 call siteを確認した。

- production: `artifact_admission.py:1328-1334`
- test support: `commit_receipt_support.py:196-205`
- private test 2箇所: `test_artifact_admission.py:1714-1721,1770-1780`
- T1286 test 2箇所: `test_t1286_commit_receipt.py:431-442,534-543`

全箇所が必須fieldを渡している。productionは共通scanの戻り値、既存fixtureは各recordsから計算している。意図的な型・負数・不一致負例だけがoverride値を渡す。

`_CERTIFIED_VIEW_TOKEN` の利用もこのconstructor集合とconstructor内部のidentity検査に閉じている。`dataclasses.replace`、pickle再構築、constructorの部分適用は見つからなかった。

`commit_receipt_support.py` 自体は26 test fileからimportされるが、該当constructorを実行する `replay_evidence()` の直接利用先は `test_campaign.py:1345` と `test_guided.py:62`。取り残しはない。

## meta-test 追従の検査

新規test fileはないため、`test_plain_runner_coverage.py:44-84` のfile集合制約への追従は不要。

新しいproduction記号についても、固定public symbol一覧は見つからなかった。既存の内容走査では次を確認した。

- `test_t671_source_binding.py:688-722` はcontract-loader APIのcall siteだけを固定しており、今回の新helperは対象外。
- `test_official_perf_closure.py:27-42,225-235` は限定されたperf記号を走査しており、新しいadmission記号は対象外。
- `test_acceptance_schedule_order.py:660-715` はledgerをcollectionの90%以上という閾値で検査するだけで、新規7 nodeの欠落を必ずしも検出しない。
- `test_update_acceptance_duration_ledger.py:306-325` はJSON内部整合を検査するが、未登録nodeを検出しない。

静的にはledger以外のmeta-test追従漏れは見つからなかった。テストは実走していない。

## acceptance ledger の検査

**RB-02**

- 主張: 新規collect node 7件が `acceptance_duration_ledger.json` に未登録で、裁定節9の完了条件を満たしていない。
- 根拠の file:line: 新規nodeは `test_artifact_admission.py:1382-1386,1724-1754`、`test_bench_first_real_wal.py:359-391`、`test_layer3_report.py:1915-1937`。ledgerは既存parameterだけを `acceptance_duration_ledger.json:36` に持ち、`nodeid_count` は同file`:19523` の19519のまま。
- 誤っていた場合に何が壊れるか: acceptance schedulerが7 nodeを未知durationとして扱い、裁定のadd-only計測契約が未完了になる。90% coverage meta-testはこの欠落を見逃しうる。
- 親が何を測れば決着するか: 次の7 nodeを実走して実durationを得て、add-onlyで追加し、既存keyとdurationがbyte単位で不変、`nodeid_count` が7増えることを確認する。
  - `test_certified_commit_evidence_rejects_no_commit_campaign`
  - `test_certified_view_checks_every_commit[both-commits-valid]`
  - `test_certified_view_rejects_commit_count_snapshot_mismatch`
  - `test_certified_view_rejects_negative_commit_count`
  - `test_certified_view_rejects_non_exact_commit_count`
  - `test_real_wal_replay_landscape_rejects_e1_without_commit`
  - `test_accepted_report_rejects_no_commit_campaign`
- 判定: **must-fix**。現状はledger未変更なので、推定durationの混入、既存nodeのrename・削除はない。

## 凍結・pin への波及

- `artifact_admission.py`
  - exact 24-path contract-loader closure member: `campaign_lock.py:47-74`
  - B4 base/sort/trigger共通projection member: `p3_b4_closed_critic.py:623-678`
  - 自己SHAをdecisionへ投影: `artifact_admission.py:1083,1138,1193,1269`
  - SHAは `fb3e695a...` から `994d3f4b...` へ変化。
- `replay.py`
  - exact 24-path contract-loader closure member: `campaign_lock.py:70`
  - B4 projection memberではない。
  - SHAは `b5ed150e...` から `6110b424...` へ変化。
- `layer3_report.py`
  - contract-loader closure、B4 projectionのどちらにも含まれない。
  - 自己SHAを `meta.generator.sha256` へ投影: `layer3_report.py:645-652`
  - SHAは `362fb98f...` から `920a247a...` へ変化。

停止pinについて、v2 campaign lock内の `contract_loader_commit` と24-path blob hashは埋まったpinであり、旧closureに束縛されたcampaignのcertified readを停止させる。B4の `expected_closed_critic_projection_closure_sha256[base|sort|trigger]` は `docs/phase3-b4-reflux-ablation-preregistration.md:158-166` で未記入なので、現時点の停止pinではない。

Layer3の保存済み `meta.generator.sha256` は埋まっておりfresh比較へ波及するが、裁定が既存の不一致としてblocker外にしている。親はbase/sort/trigger projection SHAの前後値と、保存済みLayer3比較の実測結果を記録すべきである。

## 禁止 file と scope 逸脱の検査

review開始時はHEAD `77c4ec16f`、指定8 fileが未コミットだった。その後、作業中にHEADが `107fc0b98` へ外部更新された。現在はcleanで、同commitの差分は `s5-diff.txt` とbyte一致する。初回観測上、実装子のhandoff時点では未コミットだった。後続commitの実行主体はgit metadataだけでは確定できない。

変更fileは次の8件だけで、禁止file、`docs/`、`tools/`、`hooks/`、`external/` への変更はない。

- production 3 file
- test 4 file
- test support 1 file

追加機構は共通scan、必須count field、存在要求helper、裁定済み2 consumer配線、対応testだけである。epoch、overlay、token、exact型境界、互換層、外部8 consumer、禁止されたreport/sweep fileへの変更はない。

scope上の逸脱はないが、裁定が要求する契約記述の不足はRB-01、ledger未完了はRB-02として残る。

## 総括

静的レビュー結果は **must-fix 2件、nit 0件**。

consumer、constructor、禁止fileには取り残しを認めない。完了前に、RB-01のdocstring修正と、親実測によるRB-02のledger 7 node追加が必要である。pytestその他のテストは実走しておらず、緑は主張しない。