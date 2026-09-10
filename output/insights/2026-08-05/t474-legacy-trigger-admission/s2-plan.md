## 結論

採るべき方向は、方向 A の狭い実装です。

ただし「marker 欠落全般」ではなく、既存の Git snapshot 証明を通った歴史枝かつ `is_trigger_machine_campaign_lock(lock)` の 6 件だけを `legacy-unclassified` にする形に限定します。旧 proposal 1 件は既に overlay-denied です。

方向 B は証拠不足を表示できますが、`require_admitted_campaign` が引き続き `AdmittedCampaign` を発行するため、「admitted view を名乗らせない」という今回の裁定を満たしません。

## 最優先の不一致

指定された一次控えの[択一 C:97](</work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-t409-implementation-superseded.md:97>)には、選択肢と「親の推奨 = (a) の縮小版」はありますが、ユーザーが実際に選択した旨の記録はありません。一方、[親 brief:7](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s1-brief.md:7>)と今回のユーザーメッセージは、それを明示的なユーザー裁定として扱っています。

本設計では現在の直接指示を権威として方向 A を選びますが、land 前には「2026-08-05 の裁定が D160 決定 5 の当該結果を supersede する」と durable に記録すべきです。これを記録できない場合、B へ読み替えるのではなく実装を止めるべきです。

## M1〜M6 の独立裏取り

### M1 — 一致

旧 trigger campaign は snapshot `e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e` と現 tree の双方で同じ 7 件でした。

| 対象 | 件数 | 現状 |
|---|---:|---|
| `p3-s8a-trigger-loop-…-3f72ecd5` | 1 | overlay record の lock/WAL hash と一致し、`legacy-unclassified` |
| balanced machine sweep | 2 | lock/WAL の 4 blob が snapshot と一致 |
| read-heavy machine sweep | 2 | lock/WAL の 4 blob が snapshot と一致 |
| write-heavy machine sweep | 2 | lock/WAL の 4 blob が snapshot と一致 |

6 sweep の lock はいずれも `axis=silo-backoff-trigger-gating`、`generator=reason-subset-v1`、`space=reason-subsets(effective)+identall+stock` で、`build_admission` を持ちません。したがって以下の経路になります。

1. [artifact_admission.py:591](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:591>)で歴史枝へ入る。
2. [artifact_admission.py:593](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:593>)の path・lock・WAL snapshot 照合を通る。
3. [artifact_admission.py:606](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:606>)で `historical-not-reclassified` を返す。
4. [artifact_admission.py:95](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:95>)の `!= "legacy-unclassified"` により `admitted is True`。
5. [artifact_admission.py:707](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:707>)が `AdmittedCampaign` を発行する。

`validate_trigger_bindings` の呼び出しは post-policy 部分の[artifact_admission.py:641](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:641>)だけです。歴史枝は line 619 で return するため、trigger 束縛検証は一切走りません。

### M2 — 一致

6 provenance の `entries[*].implementation` は合計 39 件でした。

- 34 件の実述語は、mask `0, 1, 4, 5, 8, 9, 12, 13, 31` に対応する 9 種の文字列です。
- 全て[reflux_ir.py:117](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/reflux_ir.py:117>)の emitter 形式と byte 一致し、[trigger_gate_binding.py:82](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/trigger_gate_binding.py:82>)の 32 点閉集合に含まれます。
- 残り 5 件は `stock` entry の日本語説明です。述語ではありませんが同名の `implementation` field に入っています。

したがって「実述語の membership 違反ゼロ」は正しい一方、`implementation` field 全体を無条件に述語として扱う consumer から見れば 5 件は非正準です。二義化は実在します。

### M3 — 一致

[D160:7930](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/decisions.md:7930>)は、proposal trigger にだけ marker/binding を要求し、機械 sweep 6 件の遡及被害ゼロを主張しています。また[D160:7955](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/decisions.md:7955>)は次を明示的に却下しています。

- marker 欠落 artifact の包括 legacy 化
- 全 trigger campaign への binding 遡及要求による 6 sweep の拒否反転

方向 A は拒否結果を反転させるため、この結果については後発裁定による明示的 supersession が必要です。ただし今回提案する A は「marker 欠落だけ」を根拠にせず、Git snapshot 一致と機械 sweep lock の連言に限定するため、包括的 downgrade 分類とは異なります。

### M4 — 一致

[wal.py:753](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/wal.py:753>)では、proposal でない場合、binding record がなく、かつ machine classifier が真なら、そのまま `{}` を返します。述語文字列・mask・provenance の membership は読みません。

これを固定しているのが[test_artifact_admission.py:340](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:340>)です。post-policy machine sweep の membership 証拠不足は方向 A 後も残ります。

### M5 — 限定付きで一致

二つの既存テストは実在します。ただし意味を分ける必要があります。

- [test_post_policy_trigger_machine_sweep_does_not_require_binding:340](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:340>)は post-policy machine sweep を直接 pin しています。
- [test_exact_pre_policy_git_snapshot_artifact_remains_readable:647](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:647>)の対象は非 trigger の `p2-2-silo-balanced-…` です。

後者は歴史枝一般の正例ですが、6 件の歴史 trigger sweep を直接 pin してはいません。親 brief 後段の「歴史 trigger の正例/反例テストは 0」と整合します。

### M6 — repo 内について一致

- [FROZEN_MANIFEST:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_frozen_artifacts.py:38>)は output 23 件だけで、`artifact_admission.py` を含みません。
- [s8b_oracle_manifest.py:44](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8b_oracle_manifest.py:44>)の generator source 5 件にも含まれません。
- tracked JSON/JSONL で `admission_decision` を持つ persisted artifact は 0 件でした。旧 trigger の persisted Layer3 は proposal 1 件が v1、machine sweep 6 件が v2で、全て admission receipt を持ちません。
- `known_axes_freeze.json` は[s8a source pin:51](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/output/s1-freeze/known_axes_freeze.json:51>)に旧 SHA `3e94735a…` を記録していますが、現ファイル SHA は `8911dd24…` でした。非接触判断は正しいです。

留保として、`artifact_admission.py` 自身の SHA は[artifact_admission.py:529](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:529>)で receipt に入ります。したがって repo 外に旧 v3 receipt が存在すれば、編集後の[完全一致照合:1010](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/autonomous_trial_completeness.py:1010>)には通りません。「persisted artifact を壊さない」は repo 内では確認できましたが、repo 外まで一般化できません。

## 方向比較

| 方向 | 裁定への適合 | 受理集合 | 成果物・実装費用 |
|---|---|---|---|
| A | 適合。「admitted view」を実際に拒否する | 6 件縮小 | production 1 file。旧 v2 bytes は維持するが、6 campaign からの新規 Layer3 生成は拒否 |
| B | 不適合。admitted view は発行し続ける | 不変 | decision/schema の版上げ、Layer3、完全一致 consumer、複数テストの改訂が必要 |
| C | 不適合。現状を固定するだけ | 不変 | 最小だが裁定成果なし |

方向 B を別タスクとして正しく実装するなら、閉集合は次の 4 値です。

| 入力 | `trigger_membership_evidence` |
|---|---|
| 検証済み post-policy proposal | `binding-proven` |
| post-policy machine sweep | `machine-sweep-unbound` |
| pre-policy trigger、overlay-denied trigger | `legacy-unbound` |
| 非 trigger | `not-applicable` |
| malformed / unknown post-policy trigger | decision を発行せず拒否 |

ただし現行の decision schema は[artifact_admission.py:31](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:31>)で v1、Layer3 は[layer3_schema.json:8](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_schema.json:8>)で v3です。必須 field を同じ版へ足すのは wire contract の in-place 変更です。B なら decision v2・Layer3 v4へ上げ、[layer3_report.py:192](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:192>)に旧 v3 decision-v1 と v2-without-decision の互換 reader が必要です。親 P3 のまま v1/v3へ field を足す案は採れません。

## 採用する方向 A の実装プラン

### Production gate

[artifact_admission.py:591–619](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:591>)だけを変更します。

- Git snapshot 証明と TOCTOU 再照合を通した後に `wal.is_trigger_machine_campaign_lock(lock)` を評価する。
- 真なら現在 line 608 の `admission_status` を `legacy-unclassified`、偽なら従来どおり `historical-not-reclassified` とする。
- `classification="historical-pre-admission-schema"`、hash、overlay provenance は変更しない。
- 新しい status や decision field は増やさない。既存の[admitted property:95](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:95>)と[require gate:707](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:707>)をそのまま使う。
- 新 reinspection ledger は作らない。既存の[Git snapshot 三点照合:371](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:371>)が既に path・lock・WAL の exact 台帳として機能しており、snapshot 内 trigger は 7 件だけです。

これにより repo corpus の受理集合は正確に 6 件縮小します。旧 proposal 1 件は既に拒否済み、post-policy machine sweep と非 trigger historical campaign は不変です。

### テスト追加

[orchestrator/tests/test_artifact_admission.py:51](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:51>)付近に 6 campaign ID の独立 literal 集合を置き、次を追加します。

- `orchestrator/tests/test_artifact_admission.py::test_exact_pre_policy_trigger_machine_sweep_is_not_admitted[<campaign-id>]`
  - 6 件を parameterize。
  - `classification == historical-pre-admission-schema`
  - `admission_status == legacy-unclassified`
  - `overlay_record_key is None`
  - `require_admitted_campaign` が `CampaignNotAdmitted`

[orchestrator/tests/test_layer3_report.py:30](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_layer3_report.py:30>)に代表 sweep path を一つ加え、[既存 legacy rejection test:252](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_layer3_report.py:252>)の隣へ追加します。

- `orchestrator/tests/test_layer3_report.py::test_real_historical_trigger_machine_sweep_cannot_issue_new_layer3_report`
  - `Layer3ReportError` / `legacy-unclassified`
  - 出力ファイルが作られないこと

変更せず残す負の対照は次です。

- `test_post_policy_trigger_machine_sweep_does_not_require_binding`
- `test_exact_pre_policy_git_snapshot_artifact_remains_readable`
- `test_legacy_v2_report_schema_remains_readable`
- `test_three_legacy_campaigns_are_denied`

これらの期待値を変更して赤を消す設計は不採用です。

### Schema・persisted artifact

方向 A では次を変更しません。

- `layer3_schema.json`
- `layer3_report.py` の production code
- `autonomous_trial_completeness.py`
- `CampaignAdmissionDecision.as_receipt`
- decision / Layer3 schema version

既存 6 件の v2 Layer3 bytes と schema-readable 性は維持します。一方、その underlying campaign から新しい admitted v3 report を再発行できなくなるのは、今回の裁定そのものです。

### 非接触面

以下は編集対象外です。

- `orchestrator/campaign/s8a_trigger_sweep.py`
- `output/s1-freeze/` 全体
- `orchestrator/campaign/s1_direct_comparison.py`
- `orchestrator/campaign/s1_verify_extime_calibration.py`
- 既存 campaign、WAL、provenance、Layer3 report の全 bytes

D160 の canonical ledger を直接編集せず、land 時の spool decision で「後発裁定による限定 supersession」を記録します。

## 変異事前登録

| Gate | 無効化の署名 | 赤になるべきテスト |
|---|---|---|
| A1: 歴史 machine 判定 | `wal.is_trigger_machine_campaign_lock(lock)` を `False` に置換 | 新規 `test_exact_pre_policy_trigger_machine_sweep_is_not_admitted[*]`、新規 Layer3 rejection |
| A1: negative status | machine 時の `"legacy-unclassified"` を `"historical-not-reclassified"` に置換 | 同上 |
| A2: view 発行拒否 | [line 712](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:712>)の条件を `if False` にする、または raise を除去 | 新規 artifact test、既存 `test_three_legacy_campaigns_are_denied`、新規 Layer3 rejection |
| A3: Layer3 consumer 境界 | [line 375](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:375>)を `classify_campaign` 等へ置換して raw view を得る | 新規 `test_real_historical_trigger_machine_sweep_cannot_issue_new_layer3_report` |
| A4: scope を post-policy へ拡大 | machine 判定を歴史枝の外へ移す | 既存 `test_post_policy_trigger_machine_sweep_does_not_require_binding` |
| A5: 全歴史 artifact を拒否 | machine predicate を定数 `True` にする | 既存 `test_exact_pre_policy_git_snapshot_artifact_remains_readable` |

検出力の穴は一つ残ります。machine classifier を単なる `search_config.axis == TRIGGER_AXIS` に広げても、現 snapshot の trigger 7 件は proposal 1 + machine 6 しかないため、corpus ベースのテストは同じ結果になります。これは「未知形の歴史 trigger まで拒否する」という受理集合縮小を検出できません。親は machine-only を契約として固定するか、全歴史 trigger 拒否まで裁定を広げるかを明示すべきです。

また方向 A は post-policy machine sweep の membership 穴 M4を閉じません。そこを閉じる変異を入れても本 wave の新テストは要求しないため、B 相当の claim-boundary 改訂は別変更単位です。

テストは実行していません。以上は静的読解、Git snapshot blob の SHA-256 照合、tracked artifact の列挙結果です。

## 総括

採る方向: snapshot 証明済みの歴史 machine sweep 6 件だけを拒否する、狭い方向 A。B は admitted view を残すため本裁定の代替になりません。

最大の risk: D160 決定 5 の結果を覆す点と、repo 外に旧 decision-v1/v3 receipt が存在した場合の validator SHA drift です。

親が裁定すべき点: 現在の直接ユーザー裁定を D160 の限定 supersession として durable に記録すること、および拒否範囲を machine-only に固定するか全歴史 trigger へ広げるかです。