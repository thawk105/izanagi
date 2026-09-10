## 現行挙動

前提として、v2 の記録済み閉包は current working tree ではなく記録 commit の blob と照合されます。`_recorded_campaign_verifier_epoch` は [`artifact_admission.py:894`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:894>) から `_verify_committed_loader_binding` を呼び、後者は working tree を読まない [`verify_committed_contract_loader_binding`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:386>) を使います。これは current closure の可用性検査とは別です。

| purpose | current closure が読める | current closure が読めない |
|---|---|---|
| `HISTORICAL_RAW` | 中央 gate は [`artifact_admission.py:959-960`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:959>) で記録済み `CampaignVerifierEpoch` を即時返します。v2 なら `E1 / recorded-closure`、v1 なら `E0 / v1-authority-absent` です。完全 API は [`artifact_admission.py:1287`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1287>) で `HistoricalCampaignView` を返します。 | 同じです。`capture_contract_loader_binding` は呼ばれないため、current closure 不在を理由とする例外は上がりません。記録 commit 自体の破損、通常 admission、WAL 検査による別理由の拒否は残ります。 |
| `CERTIFIED_ACCEPTANCE`, 記録 epoch=`E1` | [`artifact_admission.py:963-971`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:963>) で実体 `contract_loader_binding.capture_contract_loader_binding()` が成功すると記録済み E1 を返します。記録閉包との一致は要求しません。その後、全 COMMIT の永続 certification を [`artifact_admission.py:1264-1271`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1264>) で検査し、通れば [`artifact_admission.py:1283-1286`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1283>) の `CertifiedCampaignView` を返します。 | 取得器が `ContractLoaderBindingError` を上げ、[`artifact_admission.py:967-970`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:967>) が `CampaignVerifierEpochRejected` に変換します。診断は `E1-stale / current-closure-unavailable` です。COMMIT 検査や view 発行には到達しません。 |
| `CERTIFIED_ACCEPTANCE`, 記録 epoch=`E0` | current closure を読む前に [`artifact_admission.py:961-962`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:961>) で `CampaignVerifierEpochRejected(E0)` です。 | 同じく E0 拒否です。`current-closure-unavailable` にはなりません。 |

実体取得器は exact 24 path を HEAD blob と live disk の双方から読み、差を [`contract_loader_binding.py:348-361`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:348>) で `contract-loader-drift` にします。24 path 定義には `artifact_admission.py` 自身が [`campaign_lock.py:49-74`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/campaign_lock.py:49>)、特に line 57 で含まれます。

## プラン (file:line 粒度)

1. [`artifact_admission.py:374-390`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:374>) の `HistoricalCampaignView` に、歴史 view 専用の read-only property `current_verifier_conformance` を追加し、常に exact `"unknown"` を返す。

   - これは「current closure を調べて unknown にする」のではなく、「歴史 purpose は current conformance を評価していない」という意味に固定する。
   - `CampaignVerifierEpoch`、`CertifiedCampaignView`、中央 gate は変更しない。
   - 既存の `verifier_assessment_basis` と同様、歴史 view にだけ存在させる。

2. [`layer3_report.py:588-617`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:588>) の歴史 report 構築で、`admitted_campaign.current_verifier_conformance` を top-level optional field `current_verifier_conformance` として投影する。

   - [`layer3_report.py:290-303`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:290>) の既存 `campaign_verifier_epoch` 投影は変えない。
   - 理由は、既存テストが nested epoch を [`test_layer3_report.py:1360-1369`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1360>) で exact dict 比較しており、nested field にすると禁止された既存期待値の書換えが不可避になるため。
   - top-level でも、記録 epoch と current conformance を同一 report 内で明示的に分離できる。

3. [`layer3_report.py:699-711`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:699>) の certified report への昇格直前に、歴史構築時の top-level `current_verifier_conformance` を明示的に除去する。

   - certified report は current gate を通った専用 view に基づくため、歴史用 `"unknown"` を残さない。
   - `require_admitted_campaign(... CERTIFIED_ACCEPTANCE)` と `require_certified_campaign_view` の順序・条件は変更しない。

4. [`layer3_schema.json:6-20`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:6>) に、`certifying_input=true` の report が top-level `current_verifier_conformance` を持つことを禁止する既存 conditional の拡張を加える。

5. [`layer3_schema.json:21-249`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:21>) の top-level `properties` に `current_verifier_conformance: {"const": "unknown"}` を追加する。ただし line 21 の `required` には追加しない。

   - v2 reader は v3 schema から admission field だけを除く [`layer3_report.py:262-268`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:262>) ため、optional なら保存済み v2/v3 の双方を維持できる。

6. [`test_artifact_admission.py:1559-1617`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1559>) の近傍へ、後述する実体取得器を使う正例・負例を新設する。既存テストの期待値、skip、削除には触れない。

7. [`test_layer3_report.py:1308-1390`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1308>) の近傍へ、歴史 report が top-level `"unknown"` を持つ正例を新設する。

8. [`test_layer3_report.py:1470-1545`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1470>) の保存済み report 互換性テスト群の近傍へ、新 field を欠く保存済み v2/v3 report が `_validate_schema` を通る正例を新設する。

9. [`test_layer3_report.py:1773-1805`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_layer3_report.py:1773>) の certified report 群の近傍へ、次の二点を新規テストとして追加する。

   - 正規の certified report には `current_verifier_conformance` が存在しない。
   - well-formed certified report に同 field を注入すると既存 schema 検証が拒否する。

## unknown 表示の載せ場所 — 択一と推奨

| 案 | Layer 3 schema/report | `s8b_oracle_artifacts.py` | 保存済み report |
|---|---|---|---|
| `CampaignVerifierEpoch` の新 field | epoch は [`artifact_admission.py:295-308`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:295>) で両 view に共有され、同じ epoch が [`artifact_admission.py:1272-1277`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1272>) から certified にも渡ります。歴史専用にするには purpose ごとの epoch 複製が必要です。また report 投影は [`layer3_report.py:290-303`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:290>) の明示列挙なので、field を足すだけでは表示まで届きません。 | official observations は exact key set を [`s8b_oracle_artifacts.py:45-53`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:45>) で固定し、追加 key を [`s8b_oracle_artifacts.py:164-168`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:164>) で拒否します。oracle へ投影するなら契約変更が必要です。 | schema の nested `required` [`layer3_schema.json:231`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:231>) に加えると旧 report が読めなくなります。optional にしても certified 診断への波及は残ります。 |
| `HistoricalCampaignView` の property | 歴史専用型 [`artifact_admission.py:374-390`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:374>) だけに置けます。Layer 3 は既に同 view の property を投影しています。top-level optional field として追加すれば nested epoch 契約と既存 exact test を保てます。 | oracle の epoch object へ投影しないため変更不要です。reason enum や exact key setも不変です。 | top-level `required` [`layer3_schema.json:21`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:21>) を変えなければ、field を欠く保存済み v2/v3 report は読み続けられます。 |

推奨は `HistoricalCampaignView.current_verifier_conformance == "unknown"` です。P1-2 の型選択を支持します。ただし report 内では nested `campaign_verifier_epoch` を拡張せず、top-level optional field とするのが、既存期待値を変更しないという今回の禁止条件まで同時に満たします。

## 正例・負例の設計

両テストとも次の同一構成を使います。

1. [`test_artifact_admission.py:403-423`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:403>) の `_committed_closure_repo` で本物の Git repo と exact 24 path を作る。
2. `_REPO_ROOT` だけをその隔離 repo へ向ける。`capture_contract_loader_binding`、`_run_git`、`_blob`、`_read_regular_file_no_follow` は差し替えない。
3. clean な状態で `_new_schema_campaign` を作り、記録 commit と blob digest を束縛する。
4. repo 内の `orchestrator/campaign/artifact_admission.py` に未 commit bytes を加える。
5. 実体 `contract_loader_binding.capture_contract_loader_binding()` を直接呼び、[`contract_loader_binding.py:356-359`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:356>) 由来の `ContractLoaderBindingError`、`contract-loader-drift` を確認する。

正例では、その同じ状態の campaign を `HISTORICAL_RAW` で読み、次を確認します。

- exact `HistoricalCampaignView` が返る。
- 記録 epoch は E1 のまま。
- `view.current_verifier_conformance == "unknown"`。
- `CampaignVerifierEpochRejected` は上がらない。

負例では、同じ状態を `CERTIFIED_ACCEPTANCE` で読み、次を確認します。

- exact `CampaignVerifierEpochRejected` が上がる。
- `epoch_state == "E1-stale"`。
- `reason_code == "current-closure-unavailable"`。
- certified view は発行されない。

既存 [`test_certified_acceptance_distinguishes_current_closure_unavailable:1559-1576`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1559>) は取得器そのものを `monkeypatch.setattr` で置き換えています。これは「取得器がエラーを返した後の例外変換」は固定しますが、実体取得器が real Git、24 path、HEAD blob、live disk を通って不在状態を作ることは証明しません。既存テストは残しますが、要求された機構正負例には数えません。

正例側で同じ差替えを使う案も採りません。歴史分岐が monkeypatch 済み関数を呼ばないことだけで緑になり、実体の `current-closure-unavailable` 状態を構成した証拠にならないためです。

## 変異候補

1. `artifact_admission.py:959-960` の historical early return を削除する変異。

   - 前段の記録 commit 検査は working tree を読まない [`contract_loader_binding.py:386-401`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:386>) ため、正しい fixture を拒否しません。
   - 後段の `HistoricalCampaignView` は記録 E1 を受けるだけです。
   - 変異時の赤理由は、歴史 purpose が line 966 の実体取得器へ落ちて `current-closure-unavailable` になったことだけです。

2. `artifact_admission.py:963-970` の certified capture/catch を bypass する変異。

   - 前段に current closure 検査はありません。
   - 後段の persisted COMMIT 検査と `CertifiedCampaignView` E1 検査は正しい fixture なら通ります。
   - 赤理由は、負例が certified view を受けてしまい、期待した fail-closed 例外が消えたことだけです。

3. 新設する `HistoricalCampaignView.current_verifier_conformance` の戻り値を `"unknown"` 以外へ変える変異。

   - admission の前後層はこの表示値を拒否条件に使いません。
   - 赤理由は property の exact 値不一致だけです。

4. `layer3_report.py:588-617` の top-level unknown 投影を削除する変異。

   - schema 上は optional なので前後の schema 層は欠落を拒否しません。
   - 赤理由は新規 report 正例の field 欠落だけです。

5. `layer3_schema.json:21` の top-level `required` に新 field を誤って加える変異。

   - 保存済み report fixture はそれ以外の schema 条件を満たします。
   - 赤理由は「保存済み report に optional field がない」だけに絞れます。

6. `layer3_schema.json:6-20` の certified-field 禁止を削除する変異。

   - 注入する certified report は receipt、admission、E1 の他条件を満たすようにします。
   - 赤理由は、certified report へ歴史専用 unknown を注入しても schema が拒否しなくなったことだけです。

7. `layer3_report.py:699-711` の certified 昇格時の field 除去を削除する変異。

   - receipt、campaign admission、E1 は先に通る正しい fixture を使います。
   - 赤理由は、歴史専用 field が残って certified schema に拒否されたことだけです。

候補から外す位置:

- [`contract_loader_binding.py:348-361`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:348>) の取得器内部: fixture 状態の事前確認と certified gate の双方が同時に崩れ、赤の観測点が複数になります。取得器自体の検出力は本 wave の変異対象にしません。
- [`artifact_admission.py:876-932`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:876>) の記録 commit 検査: 両 purpose より前で同じ入力を拒否し、D1163 が撤去対象外とした束縛です。
- [`artifact_admission.py:176-203`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:176>) と [`s8b_oracle_artifacts.py:188-246`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:188>) の state/reason 対応: dataclass、report schema、oracle の複数層が同じ不正を拒否し、赤理由を一層へ絞れません。
- [`artifact_admission.py:379-382`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:379>) の historical epoch state 検査: `CampaignVerifierEpoch` 自身の前段検査と重複します。

## 焦点走の file 集合

`orchestrator/tests/` に対して `artifact_admission`、`layer3_report`、`layer3_schema.json`、および親 brief が示す間接 consumer module 名を `rg` した参照関係から、焦点走を次の三群にします。

中核の変更・診断面:

- `orchestrator/tests/test_artifact_admission.py`
- `orchestrator/tests/test_layer3_report.py`
- `orchestrator/tests/test_t671_source_binding.py`
- `orchestrator/tests/test_critic.py`
- `orchestrator/tests/test_p3_b4_closed_critic.py`
- `orchestrator/tests/test_s1_report.py`
- `orchestrator/tests/test_s8b_oracle_report.py`
- `orchestrator/tests/test_s8b_oracle_driver.py`
- `orchestrator/tests/test_t1286_commit_receipt.py`

直接 `artifact_admission` を import する consumer:

- `test_backoff_consumers.py`
- `test_bench_first_real_wal.py`
- `test_campaign.py`
- `test_p3_autonomous_workload_trial.py`
- `test_p3_s4_loop.py`
- `test_p3_s4_loop_sort.py`
- `test_p3_s4_loop_trigger_gating.py`
- `test_paper_story_a1_paired.py`
- `test_s1_9pair_figure_provenance.py`
- `test_s6_sort_sweep.py`
- `test_s8a_trigger_sweep.py`

`layer3_report` または source/schema inventory を参照する consumer:

- `test_layer3_admission_diagnosis.py`
- `test_trial_registry.py`
- `test_autonomous_trial_completeness.py`
- `test_t126_qualification_artifacts.py`
- `test_ccbench_spawn_sites.py`
- `test_official_perf_closure.py`
- `test_t126_pegasus_tools.py`
- `test_campaign_lock_codec.py`
- `test_s8c_acceptance_receipt_v2.py`

`commit_receipt_support.py` は test helper なので独立 node にはせず、利用側テストに含めます。単なる report filename 文字列だけの一致は中核集合へ昇格させていません。

## 受理集合への影響

1. Historical view property 追加: 表示専用であり、どの gate 条件も変更しない。`CERTIFIED_ACCEPTANCE` の受理集合は不変。
2. Historical report 投影: `HISTORICAL_RAW` の admission 完了後に行う。purpose 付替えはなく、certified 受理集合は不変。
3. Certified report から unknown を除去: 既存 certified gate 通過後の表示整形だけであり、campaign の新規受理はない。
4. Schema の optional field: campaign admission ではなく report 表示契約の追加。certified では field を禁止するため、受理集合を広げない。
5. 保存済み report 互換性: 欠落を受理し続けるだけで、`CERTIFIED_ACCEPTANCE` campaign の条件は変えない。
6. 正負例追加: production 挙動を変えない。
7. 変異事前登録: 検証計画だけであり、production 受理集合を変えない。
8. 焦点走: 検査だけであり、production 受理集合を変えない。

特に、`require_persisted_certified_commit`、certified token 発行、exact `CertifiedCampaignView` 拒否、`current-closure-unavailable` の catch は一切変更しません。

## 未確認・リスク

- 実装、編集、pytest は実行していません。指定どおり静的検査のみです。
- production file を変更した未 commit 状態では、`artifact_admission.py` が閉包に含まれるため、certified 焦点テストの `current-closure-unavailable` は期待赤です。緑とは報告しません。
- top-level report field は、nested epoch の既存 exact expectationを変更しないための選択です。親 P1-2 の「Historical view property」は支持しますが、親 handoff の A4 が示唆する nested 配置からは一段ずらしています。
- 射影外の全 production consumer 本文までは精査していません。焦点集合は test 側の module 名参照と親 brief の既知 consumer に基づきます。
- repo 内の正負例と変異は事故的退行を検出しますが、D1163 が明記する同一権限主体の共謀改変への完全防壁ではありません。

## 総括

中央 gate は既に D1245 の purpose 分離を実装しています。必要な変更は gate の緩和ではなく、実体取得器を通した正負例による構造固定と、歴史 view/report への `current_verifier_conformance="unknown"` の追加です。

推奨案は、unknown を `HistoricalCampaignView` の property に置き、Layer 3 では optional な top-level fieldとして投影するものです。これなら保存済み report、oracle exact-key 契約、既存の nested epoch 期待値を維持しつつ、`CERTIFIED_ACCEPTANCE` の受理集合を一件も広げません。