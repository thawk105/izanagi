## 前提の検査

主比較の位置と問題設定は正しい。ただし、**`artifact_admission.py` の比較先だけを替える実装では不十分**である。

- `artifact_admission.py:1364-1366` は purpose に関係なく現行 policy 一致を要求し、`:1370` で同じ policy を topology 検証へ渡している。
- **追加の停止点**として、`build_admission.py:709` が stock receipt の source commit を `CURRENT_PIN` と比較する。旧 pin の campaign は、policy hash の照合を直してもここで拒否される。
- generator／review の登録確認も `build_admission.py:548,718` で現行 enum を参照する。記録 policy を比較先にするなら、これらも記録 registry と照合する必要がある。現行 registry だけを見ると、記録 policy に存在しなかった ID を通す逆方向の誤りも残る。
- したがって、brief の「編集面が 1 module に収まる」と M6 の「純増は policy 層の 1 箇所だけ」は、そのまま実装範囲にはできない。
- M2 の現行 preimage、generator 7 member、review 3 member、`CURRENT_PIN = "511c953"` は一致する。「版上げは2事象」は pin／registry の変更を説明する範囲では正しいが、schema／authority literal の変更まで含む網羅的分類ではない。
- 現行 closure の実体は、既存テスト `test_artifact_admission.py:1287,1294` が固定する **63 path**。epoch の scope 文言にある “exact 62” を実数として扱わない。本件で文言・grammar は変更しない。
- M3 の Git 履歴、M4 の外部 root の20件、M5 の別 worktree の状態は今回再検証していない。許可された探索範囲外の実測を、本セッションの確認済み事実には数えない。

## プラン (file:line 粒度)

行番号は変更前の worktree 基準。新しい module は作らない。

**1. purpose 分岐を中央に置く**

[artifact_admission.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/campaign/artifact_admission.py:1364) の無条件一致要求を、既存 `:987` の decoder dispatch と同じ形の専用 helper に置き換える。

```python
_validate_read_purpose(purpose)
if purpose is CampaignReadPurpose.HISTORICAL_RAW:
    return decode_historical_build_admission_policy(recorded_preimage)
return require_current_policy_match(recorded_preimage)
```

これは**既存の v2 経路だけ**に適用する。v1 の post-policy 相当経路には現在の比較・検証を残す。これにより、v1＋build_admission の非認証ケースも意図せず広げない。

certified 側は `_current_policy()` との一致要求と既存例外文言を維持する。歴史側でも現行 policy を取得し、記録値との差を診断用に判定するが、差自体は拒否条件にしない。

`:1367` 以降は選択された入口で topology 検証を実行し、その後の以下を共通で通す。

- 歴史 grammar の COMMIT contract 照合 `:1377`
- trigger receipt／binding 検査 `:1380,1392`
- trigger provenance 検査 `:1400`
- build_start の source／lock／genome 照合 `:1403` 以降
- variant 再導出、lock／WAL bytes の再読照合 `:1426` 以降

overlay、v1 downgrade、pre-admission の各分岐は移動・変更しない。

**2. 記録 policy の専用入口と別返却型**

[build_admission.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/campaign/build_admission.py:258) の既存型に隣接して、独立した sealed immutable 型 `HistoricalBuildAdmissionPolicy` を置く。`BuildAdmissionPolicy` の subclass にはしない。

`:456` の factory 群の近傍に `decode_historical_build_admission_policy()` を追加する。

- exact dict、exact str key を要求する。
- key 集合は独立 literal とする。

```python
frozenset({
    "schema", "repo_stock_pin", "coder_authority",
    "generator_registry", "review_registry",
})
```

- schema は独立 literal `"build-admission-policy/v1"` と一致させる。
- pin／authority は文字列、registry は文字列の list という現行 preimage の形を要求する。値を現行 pin／enum に置換しない。
- canonical JSON と SHA-256 は既存 policy と同じ方法で計算する。registry の並べ替えなど、記録値の修復はしない。
- 既存 `BuildAdmissionPolicy.__init__`、`_new_policy()`、run context の発行経路は変更しない。

**3. receipt の構造検査を共有し、比較対象を分ける**

`build_admission.py:678` の `_validate_admission_body` と `:767` の persistent validator に対応する、歴史専用入口を追加する。

共有する検査本体には、各入口で確定した比較対象を渡す。

| 比較 | 現行入口 | 歴史入口 |
|---|---|---|
| receipt policy SHA | 現行 `BuildAdmissionPolicy.sha256` | 記録 policy の SHA |
| stock source commit `:709` | `CURRENT_PIN` | 記録 `repo_stock_pin` |
| generator ID `:548` | 現行登録確認 | 記録 `generator_registry` |
| review ID `:718` | 現行登録確認 | 記録 `review_registry` |
| coder authority `:734` | `_AUTHORITY_KIND` | 記録 `coder_authority` |

`:543` の generator body、`:564` の review receipt の検査も、source 束縛・schema・digest・exact keys を共有できる範囲で抽出する。歴史側で現行 `ReviewId` へ変換し直してから検証してはならない。

現行公開入口の exact 型要求と既存の登録確認は維持する。歴史入口は historical policy の exact 型を要求し、runtime の `BuildAdmission`／`ReviewReceipt` を発行せず、検査済み persistent body を返す。

**4. WAL の exact 型境界を維持する**

[wal.py:2120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/campaign/wal.py:2120) に歴史専用 topology 入口を隣接追加する。

- 既存 `_validate_attempt_topology` の `:2124` は exact `BuildAdmissionPolicy` のまま。
- 新入口は exact `HistoricalBuildAdmissionPolicy` を要求する。
- `:2126-2287` の topology 検査本体を共有する。各入口が束縛した receipt validator を、現在の `:2157` の呼出位置で必ず呼ぶ。
- 共通化はこの二入口のための private helper に限定し、拡張可能な validator registry は作らない。
- `:2474` の recovery 型 gate は変更しない。歴史 policy は recovery に渡せない。

これにより、現在 `_validate_attempt_topology` が行う全検査を歴史側でも実行し、検査の複製による脱落を避ける。

**5. 新識別子は admission decision の classification に置く**

`artifact_admission.py:1436` の decision 発行を、**v2・HISTORICAL_RAW・policy 不一致**の場合だけ次にする。

```text
classification = "historical-policy-version"
admission_status = "historical-not-reclassified"
policy_sha256 = 記録 policy の SHA-256
```

一致時は従来の `"admitted-new-schema" / "admitted"` のまま。

`CampaignAdmissionDecision.admitted`（`:310`）は既にこの historical status を受けられるため変更不要。`:314` の `as_receipt()` が新 classification を既存 field に投影する。新 field は不要。

**epoch は変更しない。** `CampaignVerifierEpoch.__post_init__` の reason 値域、`HistoricalCampaignVerifierEpoch` の scope、nested epoch object、`current-closure-unavailable` はすべてそのままにする。

`layer3_schema.json:293` の classification enum に新値を追加する。同ファイル `:12` の既存 `certifying_input=true` 条件では、classification を従来の2値に制限する。これは schema の受理形拡張を certified 側で相殺する変更であり、新たな認証要件の追加ではない。status の enum `:294` は変更不要。

**6. WAL の第2比較は変更しない**

`wal.py:2767-2779` の直接の呼び手は、同 module の `replay():2821` と `replay_a1_non_certifying():2829`。production の上流を helper 経由まで辿ると次のとおり。

| 上流の呼出箇所 | 渡される policy／間接経路 |
|---|---|
| `backoff_sweep.py:541` | `main → unexpected_abort → wal.replay`。`:536` で作る `replay_policy` |
| `s6_sort_sweep.py:432` | `run_sweep` の `build_context.policy` |
| `s8a_trigger_sweep.py:534` | `run_sweep` の `build_context.policy` |
| `screening_driver.py:592,649` | いずれも `build_context.policy` |
| `b10_backoff_shape_sweep.py:3562` | `build_context.policy` |
| `loop.py:576-579` | `run_campaign → ローカル replay alias → WAL wrapper`。必ず `build_context.policy` |
| `paper_story_a1_paired.py:5781-5785` | `collect_workload → replay_fn alias → WAL wrapper`。引数の `admission_policy` |

最後の `collect_workload` の production caller は同ファイルの3箇所。

- `_run_measurement_v3 → collect_workload`、`:7197-7202`：`build_context.policy`
- `run_measurement → collect_workload`、`:7446-7451`：`build_context.policy`
- `_revalidate_raw_wals → collect_workload`、`:7653-7658`：`context.policy`

したがって、これらの production call は `admission_policy is None` の比較を発火させない。引数省略を使う unit test／直接 API 呼出は引き続き発火し、現行不一致を拒否する。

歴史 consumer についても、例えば次の間接経路を確認した。

```text
online_digest → build_digest → load_workload
              → _committed_projection → replay_admitted_records
```

`replay_admitted_records`（`wal.py:2690`）は records の投影であり `_replay` を呼ばない。中央 admission も `read_records_checked → topology 検証` で、`_replay` を通らない。よって第2比較は本 wave の変更対象外である。

**7. production consumer への波及**

「変わる」は、他の必要条件を満たす旧 policy の v2 入力について、今回の policy 拒否を越えられるという意味である。全入力で report 完成まで保証する意味ではない。

| consumer | 本変更の影響 |
|---|---|
| `critic/digest.py:1236` | 変わる。`discover_p2_2_dir → discover_campaign_dir → require_admitted_campaign` の historical admission が通る。`:1631` の certified 入口は変更なし |
| `critic/online_digest.py:42` | 変わる。historical view を取得して digest へ渡せる |
| `campaign/p2_2_report.py:132` | 変わる。historical discover 経由で旧 policy の records を取得できる |
| `campaign/s1_report.py:302` | **変わらない。** lock bytes から epoch を検査するだけで、今回の policy admission を呼ばない。通常 decoder と E0 拒否も残る |
| `campaign/layer3_report.py:733` | 変わる。historical report が新 classification を表示できる。`:959,966` の certified report 経路は引き続き拒否 |
| `campaign/b10_backoff_static_tail_formal.py:352` | exploration の correctness mode 読取りが変わる。`:393` の certified 入力取得は変更なし |
| `campaign/replay.py:129,168` | historical purpose を受ける discover helper が変わる。`:179` の `load_landscape` は certified 固定なので変更なし |
| `tools/plotting/plot_s1_9pair.py:562` | 変わる。historical view を取得でき、`:593` の decision receipt に識別子が入る。別途の入力条件・digest 束縛は維持 |

既存 v1 corpus は別分岐なので、これらの consumer でも本件による変化はない。

## 択一と理由

**policy は別型・別入口を選ぶ。**

同型の再発行 factory を作れば WAL の exact 型検査をそのまま利用できる。しかし、記録由来の値が recovery や現行 persistent validator の型境界も通るようになり、「歴史専用」の区別を呼出規約に依存させる。

本案は D1653 の「別入口・別返却型」を policy 層にもそのまま適用する。通常入口の返却型・受理集合を広げず、歴史入口から現行 runtime 値を発行しない。そのために必要な WAL 内の検査本体共有は行うが、新 module や boolean 緩和は導入しない。入口を選ぶ中央の根拠は exact `purpose` のみである。

**形の定数は独立 literal を選ぶ。**

key 集合を `_new_policy().as_preimage()` から動的に導くと、将来の現行 schema 編集で歴史 parser の受理形も無言で変わる。D1653 の旧 tuple と同じ理由で固定する。ただし policy の JSON object は順序付き grammar ではないため、key の順序一致は要求しない。

独立 literal が現行 preimage の key 集合・schema と一致することはテストで固定する。将来 schema 自体が変わる場合は、そのテストで明示的な再検討を要求する。今回自動追従させるのは同じ形の policy の値変更である。

**識別子は classification を選ぶ。**

policy 差は verifier closure の reason ではない。epoch に混ぜると D1365 に反し、scope とも意味がずれる。既存 decision の classification と非認証 status を使えば、記録 policy の SHA と同じ診断面で表示でき、certifying status への誤読も避けられる。

## テスト設計

以下の名称は追加予定テスト名。

fixture は [test_artifact_admission.py:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/tests/test_artifact_admission.py:555) の `_new_schema_campaign` を基本にする。これは以下を既に使用している。

- `_write_campaign:315`：lock／WAL の作成
- `_record:327`：stage record の作成
- `_campaign_id_for_lock:337`：identity から directory 名を導出
- `_committed_closure_repo:474`：certified 正例の closure
- `_rewrite_v2_identity:357`、`_rewrite_wal:384`：負例の局所変更
- `_classify_as_trigger:649`：trigger binding／provenance の fixture

**policy 差の正例は、まず有効な campaign を発行し、その後テスト内で現行 policy を前進させる。** lock／receipt を不整合なまま書き換えて正例にしない。

| テスト | 内容・期待結果 |
|---|---|
| `test_historical_policy_version_reads_recorded_v2` | pin 前進／generator 追加／review 追加をパラメータ化。HISTORICAL_RAW が exact historical view を返し、記録 policy SHA、新 classification、unknown conformance、lock／WAL bytes 不変を確認 |
| `test_certified_rejects_recorded_policy_version` | 上と同じ campaign。CERTIFIED_ACCEPTANCE と `classify_campaign` が従来の policy 不一致文言で拒否。現行 closure は有効にして別理由の拒否で代用しない |
| `test_historical_policy_shape_is_exact` | key 欠落・余分 key・schema 違い・非 object・field 型違いを拒否。**WAL を空にした有効 v2 lock でも検査**し、receipt hash 不一致が形検査の代役にならないようにする |
| `test_current_policy_campaign_unchanged_for_both_purposes` | 両 purpose の成功、従来 classification／status／decision receipt、epoch を確認。既存 `:1291` の certified 正例構成を利用 |
| `test_historical_receipt_uses_recorded_policy_values` | stock・machine・review・coder の各 class で記録側との整合を検査。特に旧 stock pin の成功を必須にする |
| `test_historical_receipt_rejects_recorded_policy_mismatch` | 記録 pin と source の不一致、記録 registry にない ID、異なる authority、異なる policy SHA を拒否。receipt の outer SHA と伝播 SHA は整合させ、狙った比較まで到達させる |
| `test_historical_policy_drift_preserves_structure_checks` | policy 差がある fixture に topology、trigger binding、provenance、source、contract、variant の破損を個別に入れて拒否 |
| `test_historical_policy_drift_rechecks_bytes` | `:1186` の snapshot 再読テストを拡張。lock と WAL をそれぞれ検証中に変えた場合の拒否 |
| `test_historical_policy_cannot_enter_current_consumers` | historical policy を既存 topology／recovery／runtime validator へ渡すと exact 型で拒否。view も `require_certified_campaign_view` を通れない |
| `test_policy_shape_literal_matches_current_schema` | 独立 key／schema literal が現在の `_new_policy()` と一致することを固定 |

追加して次を回帰確認する。

- `:1751,1789` の旧 grammar：policy 差と組み合わせても historical のみ成功。
- `:2009` の exact view 境界、`:2117` の exact purpose。
- `:2246,2258,2288` の v1 downgrade／guided／pre-policy 判定。
- overlay 拒否 `:1225-1270`。
- `wal.replay(layout)` の policy 省略時：旧 policy は引き続き拒否。
- `test_layer3_report.py:1854,1877` を基に、新 classification の historical report が schema を通ること。
- `test_layer3_report.py:2500,2596,2714` 近傍で、certifying report／schema が新 classification を拒否すること。schema 単体テストでは既存の historical marker を除き、新 classification の拒否を独立に確かめる。

## 変異の候補

行は変更前の対応位置、テスト名は上記の追加予定名。

| # | 変異 | 赤になるべきテスト |
|---|---|---|
| 1 | `artifact_admission.py:1364` の新 dispatch を常に現行一致入口へ向ける | `test_historical_policy_version_reads_recorded_v2` |
| 2 | 同 dispatch の certified 側も記録 policy 入口へ向ける | `test_certified_rejects_recorded_policy_version` |
| 3 | `build_admission.py:456` 近傍の新 decoder で key 集合完全一致を削除する | 空 WAL を使う `test_historical_policy_shape_is_exact` の欠落／余分 key ケース |
| 4 | 同 decoder の schema literal 一致を削除する | 同テストの schema 違いケース |
| 5 | `wal.py:2157` 相当の歴史 receipt 呼出で、記録 policy SHA の代わりに現行 SHA を使う | `test_historical_policy_version_reads_recorded_v2` |
| 6 | `build_admission.py:709` 相当の歴史 stock 比較先を `CURRENT_PIN` に戻す | `test_historical_receipt_uses_recorded_policy_values` の旧 stock pin ケース |
| 7 | `build_admission.py:548` 相当の歴史 generator 登録確認を現行 registry に戻す | `test_historical_receipt_rejects_recorded_policy_mismatch` の「現行にはあるが記録 registry にはない ID」ケース |
| 8 | `artifact_admission.py:1436` の policy 差 decision を従来 classification／status に戻す | `test_historical_policy_version_reads_recorded_v2` の診断期待値 |
| 9 | `layer3_schema.json:12` に追加する certified 側 classification 制限だけ削除する | 新 classification を使う certifying schema 単体負例 |

3・4は receipt 検証による別理由の拒否を避け、7は digest を整合させた負例を使う。9も他の historical marker による拒否を避けるため、いずれも狙った述語の変更を検出できる。

## 残った不確実性

- 外部 corpus での発火件数・既存成果物への実際の影響件数は未確認。今回の正例は合成 fixture で立証する設計である。
- 新 factory／検査本体抽出に対する既存 AST audit の結果は未実測。実装時に既存監査を通し、歴史入口を runtime 発行許可へ広げて解決しない。
- 今回固定するのは `build-admission-policy/v1` の形である。将来の schema 変更や receipt grammar 変更まで自動互換にする案ではない。
- テスト、build、mutation run は実行していない。ファイルの編集・作成、commit、Git 状態変更も行っていない。

## 総括

**別型の歴史 policy decoder と専用検証入口を既存 module 内に設け、lock・receipt・source の比較先を記録 policy に統一する。** 構造検査は共有して維持し、識別子は `classification="historical-policy-version"` に出す。

certified の現行一致、exact view／epoch 境界、WAL replay の第2比較、v1・overlay・pre-admission の挙動、consumer の purpose 宣言は維持する。