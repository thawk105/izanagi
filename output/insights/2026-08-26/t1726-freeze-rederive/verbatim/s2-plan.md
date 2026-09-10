結論として、親 brief の P4 は実在し、P1 の「`resolve_arm_input` を呼ぶだけ」では不十分です。legacy freeze bytes と現在の `HOLDOUTS` を先に exact 束縛し、その後に resolver の digest を照合すれば、receipt schema を v4 に上げず v2/v3 を昇格できます。

書込み、pytest、import 実行は行っていません。以下は静的検査に基づく実装プランで、すべて未実走です。

## 1. 昇格の配置

対象は [`s8c_acceptance_receipt.py:2`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:2) と、その v2 test だけです。

1. module docstring の [`s8c_acceptance_receipt.py:4`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:4) を更新する。

   `trial_registry` / `layer3_report` 非依存は維持しつつ、「approval authority は推論しないが、記録された arm execution が ratified legacy freeze 由来であることは検証する」と責務を明記します。`certifying=false` の構造ゲートは [`s8c_acceptance_receipt.py:393`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:393) のままです。

2. import 群の [`s8c_acceptance_receipt.py:11`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:11) に次を追加する。

   - `s8b_holdout_freeze`
   - `s8b_ratified_freeze`
   - `s8c_arm_inputs`

3. 現行 digest helper の直後、[`s8c_acceptance_receipt.py:684`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:684) 付近に三つの helper を追加する。

   - `_holdout_authority_projection(entry, label)`

     `candidate_id`、`records`、`threads`、`ycsb` を plain JSON へ射影します。既存パターンは [`p3_autonomous_workload_trial.py:801`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/p3_autonomous_workload_trial.py:801) です。

   - `_require_ratified_legacy_arm_authority(root)`

     `s8b_ratified_freeze.load_legacy_freeze(root)` を呼び、`legacy.document["holdouts"]` の名前集合と各投影を `s8b_holdout_freeze.HOLDOUTS` に canonical bytes で exact 比較します。`RatifiedFreezeError` は新 gate `[receipt-freeze-arm-binding]` の `AcceptanceReceiptError` へ変換します。

   - `_assert_rederived_trial_arm_execution(root, trial)`

     `s8c_arm_inputs.resolve_arm_input(arm=trial.arm, holdout=trial.holdout, repository_root=root, commit=trial.measurement_head)` を呼び、expected の `content_digest_sha256` と `arm_binding_digest_sha256` を receipt の `trial.arm_execution` へ exact 比較します。`ArmInputError` も同じ gate へ変換します。

4. [`verify_acceptance_receipt:962-978`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:962) を次の順序にする。

   - v2/v3 の場合だけ、ループ前に `_require_ratified_legacy_arm_authority(root)` を一度呼ぶ。
   - 各 trial について、既存 `_verify_v2_trial_arm_execution` を先に実行する。
   - その成功後に `_assert_rederived_trial_arm_execution` を実行する。

   既存の receipt/report/run-start 三者検査を先に残すことで、既存 gate の失敗帰属を極力維持し、freeze 再導出を追加の論理積にします。

追加述語と受理集合への作用は次のとおりです。

- legacy freeze の読取りと固定 SHA-256 照合に失敗した receipt を新たに拒否するため、受理集合は狭くなる向きです。
- freeze holdout 投影と source `HOLDOUTS` が異なる状態を新たに拒否するため、in-source 定数だけを信頼する経路が除かれます。
- `measurement_head` で arm input を再導出できない trial を新たに拒否するため、履歴的 off artifact が欠けた receipt は受理されません。
- expected content digest と receipt digest が異なる自己整合 receipt を新たに拒否します。
- expected binding digest と receipt binding digest が異なる receipt を新たに拒否します。これは既存の自己入力 digest 検査とも重なりますが、expected tuple 全体を照合する防御であり、受理集合を広げません。

`verify_document` は呼びません。[`s8b_holdout_freeze.py:985`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_holdout_freeze.py:985) は現在の未知性 scan まで行い、実走後には意図的に失敗し得る関数だからです。receipt 時点の authority binding には固定 hash loader と holdout 投影比較を用います。

## 2. 権威の連鎖

### 共通の始点

1. legacy freeze の canonical path と trust-root digest は [`s8b_ratified_freeze.py:63-65`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_ratified_freeze.py:63) に固定されています。

2. `load_legacy_freeze` は path の bytes を読み、SHA-256 を定数と比較し、strict JSON として `LegacyFreeze` にします。[`s8b_ratified_freeze.py:1409-1427`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_ratified_freeze.py:1409)

3. 新 helper は `legacy.document["holdouts"]` と source [`s8b_holdout_freeze.HOLDOUTS:100-104`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_holdout_freeze.py:100) を投影単位で exact 比較します。

   既存実装でも、legacy document、producer entry、module `HOLDOUTS`、arm descriptor を [`p3_autonomous_workload_trial.py:825-851`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/p3_autonomous_workload_trial.py:825) と [`p3_autonomous_workload_trial.py:854-885`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/p3_autonomous_workload_trial.py:854) で順に束縛しています。新 helper はこの連鎖を receipt verifier 内で直接接続します。

### on / swapped

1. `resolve_arm_input` は candidate 集合を `_holdout_entries_by_candidate` で source `HOLDOUTS` から構成します。[`s8c_arm_inputs.py:186-195`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:186)

2. on は own candidate、swapped は [`DERANGEMENT`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_holdout_freeze.py:104) で選んだ candidate を `_descriptor_for_candidate` へ渡します。[`s8c_arm_inputs.py:434-458`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:434)

3. `_descriptor_for_candidate` は `s8b_descriptor.descriptor_for_holdout` で descriptor を生成します。[`s8c_arm_inputs.py:409-421`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:409)、[`s8b_descriptor.py:214-218`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_descriptor.py:214)

4. `canonical_execution_input_bytes` により canonical bytes 化し、SHA-256 を計算します。[`s8c_arm_inputs.py:87-114`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:87)、[`s8c_arm_inputs.py:465-478`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:465)

5. `_binding_digest` が `(holdout, arm, content_digest)` を domain-separated hash にします。[`s8c_arm_inputs.py:424-431`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:424)

6. `ResolvedArmInput` の両 digest は [`s8c_arm_inputs.py:476-493`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:476) で確定し、新 helper が receipt の [`arm_execution` fields](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:306) と比較します。

### off

1. `resolve_arm_input` は arm に関係なく `verify_off_neutral_artifacts` を呼びます。[`s8c_arm_inputs.py:459`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:459)

2. neutral descriptor の値は、source `HOLDOUTS` の両 endpoint と固定 midpoint authority を `_assert_neutral_authorities` が照合して導出します。[`s8c_arm_inputs.py:198-250`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:198)

3. `_artifact_payloads` が expected descriptor/freeze bytes を作ります。[`s8c_arm_inputs.py:253-263`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:253)

4. `_committed_regular_blob` は receipt の `measurement_head` を commit として off descriptor と sidecar を読みます。[`s8c_arm_inputs.py:336-365`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:336)

5. `verify_off_neutral_artifacts` が historical bytes を expected bytes、schema、size、digest へ照合します。[`s8c_arm_inputs.py:368-406`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:368)

6. 以後は on/swapped と共通で content digest、binding digest、receipt field の順に到達します。

### P4 の断絶箇所

現状の on/swapped は `_holdout_entries_by_candidate` と `_descriptor_for_candidate` が現在の source `HOLDOUTS` を読むだけです。[`s8c_arm_inputs.py:186-195`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:186)、[`s8c_arm_inputs.py:409-458`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:409)

ここでは `commit` も legacy freeze bytes も参照されません。`commit` が効くのは off artifact の [`s8c_arm_inputs.py:459`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:459) だけです。したがって、`resolve_arm_input` を単独で呼ぶ P1 は権威鎖として未完成です。新しい freeze document ↔ source `HOLDOUTS` の exact 比較が、この区間を閉じます。

## 3. 依存契約と import 循環

依存は成立します。

- `s8c_acceptance_receipt` の契約は `trial_registry` / `layer3_report` 非依存です。[`s8c_acceptance_receipt.py:4-7`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:4)
- `s8c_arm_inputs` は descriptor と holdout-freeze authority だけを import する leaf です。[`s8c_arm_inputs.py:2-6`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:2)、[`s8c_arm_inputs.py:21-22`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_arm_inputs.py:21)
- `s8b_ratified_freeze` の直接 import 群にも `trial_registry`、`layer3_report`、`s8c_acceptance_receipt` はありません。[`s8b_ratified_freeze.py:40-53`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_ratified_freeze.py:40)
- 逆向きには `trial_registry` が acceptance verifier と arm inputs を import しています。[`trial_registry.py:44-45`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/trial_registry.py:44)
- `layer3_report` も verifier を下流利用するだけです。[`layer3_report.py:607-622`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/layer3_report.py:607)

静的 import graph では `s8c_arm_inputs` または `s8b_ratified_freeze` から `s8c_acceptance_receipt`、`trial_registry`、`layer3_report` へ戻る path はありません。循環なしと判断します。

`p3_autonomous_workload_trial` 自体は import しません。既存パターンのロジックだけを局所 helper として移植します。

## 4. schema 世代別の扱い

| 世代 | `arm_execution` | 新 freeze gate | 受理集合への影響 |
|---|---:|---:|---|
| v1 | なし。parser が `None` を設定する。[`s8c_acceptance_receipt.py:466-471`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:466) | 発火しない | 現状から広がらないが、freeze 再導出なしの広い集合を維持する。C02 reason は必須のまま。 |
| v2 | あり | 全六セルで発火 | 自己整合していても freeze expected digest と異なる receipt を除外する。 |
| v3 | あり | v2 と同じく全六セルで発火 | v2 の新 gate に加え、既存 cross-binding aggregate 検査も維持する。[`s8c_acceptance_receipt.py:988-1000`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:988) |

分岐は既存の v2/v3 集合 [`s8c_acceptance_receipt.py:973-978`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:973) と同じにします。v1 fixture は legacy freeze を持たないままでよく、既存正例 [`test_s8c_acceptance_receipt.py:162-170`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt.py:162) の経路には新 gate が入りません。

## 5. positive control と正例

### fixture の実物化

[`test_s8c_acceptance_receipt_v2.py:64-157`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:64) を次のように変更します。

1. test module の import [`test_s8c_acceptance_receipt_v2.py:14`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:14) に `s8b_ratified_freeze` と `s8c_arm_inputs` を加える。

2. temp repo に正本の `V1_FREEZE_PATH` bytes をそのまま複製し、`generate_off_neutral_artifacts(repository_root=repo)` で off artifact を作る。

3. これらを最初の commit にし、その OID を六セル共通の `measurement_head` にする。現行の `"1" * 40` は [`test_s8c_acceptance_receipt_v2.py:98`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:98) と [`test_s8c_acceptance_receipt_v2.py:127`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:127) から除く。

4. 各セルの descriptor と arm execution を手書きする [`test_s8c_acceptance_receipt_v2.py:78-95`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:78) を `resolve_arm_input` の結果で置換する。descriptor は `resolved.canonical_input_bytes` を JSON decode して report cell に載せます。

これにより fixture 自体が固定 freeze、source authority、historical off artifact を通った producer-equivalent receipt になります。

### 自己整合した誤値の対照

[`test_s8c_acceptance_receipt_v2.py:289`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:289) 付近に、例えば `test_self_consistent_wrong_descriptor_is_rejected_by_freeze_rederivation` を追加します。

1. `_trial` [`test_s8c_acceptance_receipt_v2.py:165-169`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:165) で H1/on を選ぶ。
2. report cell の正しい descriptor を複製し、`descriptor["read_write"]["read_ratio_percent"]` を `"80"` から `"79"` へ変える。
3. `launch_admission.binding["ycsb_rratio"]` も `"79"` にする。
4. 誤 descriptor の canonical digest を receipt、report、run-start の `content_digest_sha256` に同期する。
5. `(H1, on, forged content digest)` から binding digest を再計算し、同じ三箇所へ同期する。
6. report/journal の SHA-256 と receipt bytes を更新して commit する。既存同期 helper は [`test_s8c_acceptance_receipt_v2.py:189-210`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:189) を拡張して再利用する。
7. 次の exact gate を要求する。

   `\[receipt-freeze-arm-binding\] content digest differs from ratified legacy freeze rederivation$`

この mutant は既存の cell descriptor hash、receipt/report equality、binding digest、run-start equality [`s8c_acceptance_receipt.py:788-821`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:788) をすべて満たし、新 gate だけで拒否される形にします。

### 正しい receipt の正例

実 resolver 化した fixture を使う既存 [`test_v2_producer_equivalent_full_verify_drops_only_c02:246-254`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:246) を正例にします。v2 の全六セルが新 gate を通り、既存の C02 reason-drop 条件も保たれることを確認する設計です。

追加で、同じ fixture を v3 に昇格する [`test_s8c_acceptance_receipt_v2.py:422-430`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:422) も新 gate の v3 被覆になります。

いずれも未実走です。

## 6. [T-1727] v4 の判断材料

v4 へ上げずに T-1726 は成立します。

既存 v2/v3 には再導出に必要な次の値が既にあります。

- `arm`
- `holdout`
- `measurement_head`
- `arm_execution.content_digest_sha256`
- `arm_execution.arm_binding_digest_sha256`

これらは [`s8c_acceptance_receipt.py:62-84`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:62) と [`s8c_acceptance_receipt.py:431-470`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:431) にあります。freeze SHA-256 は receipt に無くても、legacy authority が単一の `V1_FREEZE_SHA256` として固定され、verifier がその bytes を必ず読むため、受理判定自体は可能です。

serialized launch binding が `ycsb_rratio` 一本だけなのは [`trial_registry.py:4098-4115`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/trial_registry.py:4098) のとおりですが、digest は serialized condition からではなく fixed freeze、arm、holdout、measurement head から再導出するため、T-1726 の成立条件にはなりません。

v4 を見送る場合の残余は、「receipt 自身がどの freeze SHA-256 を使ったかを表示しない」ことです。ただし現行 legacy freeze は単一固定値なので、これは監査上の provenance 不足であって、今回追加する受理 gate の断絶ではありません。将来、複数 freeze authority の選択や `V1_FREEZE_SHA256` の置換を許す前には、v4 による authority identity の serialized binding が必要です。

今回 v4 を導入しないため、次は変更しません。

- schema version と exact key 集合 [`s8c_acceptance_receipt.py:23-84`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:23)
- receipt/report/run-start の canonical bytes
- `trial_registry.py` と `test_trial_registry.py`
- opaque baseline [`test_reflux_originless_compatibility.py:360`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_reflux_originless_compatibility.py:360)
- v3→v1 compatibility projection [`test_reflux_originless_compatibility.py:871`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_reflux_originless_compatibility.py:871)

したがって `_PRE_WAVE_ORIGINLESS_BASELINE` の更新を要求する案にはなりません。

## 総括

- 昇格の配置: `verify_acceptance_receipt` の v2/v3 経路へ、既存三者自己整合検査の後段として `[receipt-freeze-arm-binding]` gate を追加します。
- 権威の連鎖: P4 の断絶は確認済みです。`load_legacy_freeze` の固定 hash bytes と source `HOLDOUTS` を exact 比較してから `resolve_arm_input` を呼ぶことで、legacy freeze bytes から receipt の両 digest まで連結できます。
- [T-1727]: T-1726 の成立に v4 は不要です。v2/v3 bytes と exact key 集合を維持し、v4 は複数 freeze authority を導入する将来の provenance 世代交代まで見送るのが妥当です。
- 実行状況: 静的検査のみ。書込み・pytest ともに未実走です。