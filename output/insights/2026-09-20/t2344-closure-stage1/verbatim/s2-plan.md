## 方針と確認範囲

**T-2429 の末尾追加と T-2483 の兄弟 validator を組み合わせる案を採ります。** production 3 file と tests 5 file を同 commit で変更します。以下の行番号は変更前です。

指定された必読10 file はすべて読み取り可能でした。指定の2 commit の `--stat`、現行コード、consumer、関連テストを静的に確認しました。ファイル変更・commit・pytest 実行はしていません。固定 hash の確認だけ、production を import しないメモリ内計算で行いました。

通常 decoder の **v2 authority grammar は exact-85 のみ**とし、v1 の既存仕様は維持します。exact-63／62／24 は歴史専用の別返却型で扱います。

## 1. campaign_lock.py の変更

対象：[campaign_lock.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/campaign/campaign_lock.py:49)

`:47` のコメントを `exact 85 path` に変更し、`:49` の tuple を次に置き換えます。既存63本の順序は維持し、最後の22本だけを path の sorted 順で追加しています。

```python
CONTRACT_LOADER_RELATIVE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
    "orchestrator/campaign/verify_fanout_worker.py",
    "orchestrator/calibrator/analyze.py",
    "orchestrator/calibrator/benchparse.py",
    "orchestrator/calibrator/model.py",
    "orchestrator/calibrator/perfparse.py",
    "orchestrator/calibrator/tsc.py",
    "orchestrator/campaign/agent_outputs.py",
    "orchestrator/campaign/backoff_hole_grammar.py",
    "orchestrator/campaign/durable_root.py",
    "orchestrator/campaign/materializer_admission.py",
    "orchestrator/campaign/p3_b4_admission_record.py",
    "orchestrator/campaign/p3_b4_closed_critic.py",
    "orchestrator/campaign/p3_s4_loop.py",
    "orchestrator/campaign/p3_s4_loop_sort.py",
    "orchestrator/campaign/p3_s4_loop_trigger_gating.py",
    "orchestrator/campaign/paper_story_a1_source.py",
    "orchestrator/campaign/pin.py",
    "orchestrator/campaign/reflux_result_evidence.py",
    "orchestrator/campaign/s8b_compiler_input.py",
    "orchestrator/campaign/s8b_expected_materialization.py",
    "orchestrator/campaign/silo_ladder_rung1.py",
    "orchestrator/campaign/sort_swo_dependency_material.py",
    "orchestrator/critic/digest.py",
)
```

**独立 literal：** `T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS` を、`T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS` の閉じ括弧 `:209` 直後に置きます。内容は変更前 `:50–112` の63行をそのまま独立記述します。上記の先頭63行に一致しますが、実装を slice・展開・連結による導出にはしません。

変更骨格：

```diff
@@ HistoricalCampaignLockAuthority.__post_init__ :279
         if type(grammar) is not tuple or grammar not in (
             CONTRACT_LOADER_RELATIVE_PATHS,
             PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS,
             T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS,
+            T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS,
         ):
```

`:494–539` の validator の直後に、兄弟として
`_validate_t2429_exact63_historical_authority(value)` を追加します。既存62 validator を複製し、3か所の tuple 参照だけを63定数へ変更します。

```python
def _validate_t2429_exact63_historical_authority(
        value: Any,
) -> HistoricalCampaignLockAuthority:
    # exact AUTHORITY_KEYS、正の exact int の検査は62版と同一。
    ...
    expected_wire_order = tuple(sorted(
        T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS
    ))
    if (type(blob_sha256s) is not dict
            or tuple(blob_sha256s) != expected_wire_order):
        raise CampaignLockCodecError(
            "authority.contract_loader_blob_sha256s の歴史 grammar が不正"
        )
    checked_blobs = {
        path: _require_hex(
            blob_sha256s[path], width=64,
            label=f"authority.contract_loader_blob_sha256s[{path!r}]",
        )
        for path in T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS
    }
    return HistoricalCampaignLockAuthority(
        # environment hash、activation hash、commit の検査も62版と同一。
        ...
        contract_loader_blob_sha256s=checked_blobs,
        recorded_contract_loader_relative_paths=(
            T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS
        ),
    )
```

`decode_historical_campaign_lock :680` は次の4分岐です。

```diff
@@ :683
-    """現行・T733 exact-62・pre-T733 exact-24 を歴史閲覧用に decode する。"""
+    """現行・T2429 exact-63・T733 exact-62・pre-T733 exact-24 を歴史閲覧用に decode する。"""

@@ :705
     # current_wire_order は更新後の exact-85。
     if type(blob_sha256s) is dict and tuple(blob_sha256s) == current_wire_order:
         return _historical_decoded_from_current(decode_campaign_lock(text))

@@ :715
     if (type(blob_sha256s) is dict
             and tuple(blob_sha256s)
+            == tuple(sorted(T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS))):
+        authority = _validate_t2429_exact63_historical_authority(authority_value)
+    elif (type(blob_sha256s) is dict
+            and tuple(blob_sha256s)
             == tuple(sorted(T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS))):
         authority = _validate_t733_exact62_historical_authority(authority_value)
     else:
         authority = _validate_pre_t733_historical_authority(authority_value)
```

最後の `else` は任意 grammar の受理ではありません。既存24 validator が exact 一致を検査し、未知 grammar を拒否します。

**共通化より兄弟追加が規律を守りやすい理由：** T-2483 と同じく、24／62 validator の検査順・例外・返却値を変更せずに済みます。共通 helper の引数誤りで複数の歴史 grammar を同時に緩める変更も避けられ、差分を63固有部分に限定できます。

なお、順序には二種類あります。wire は canonical JSON の **sorted path 順**、返却 authority と epoch は **独立 literal の宣言順**です。入力キーを並べ替えてから検証する実装にはしません。

## 2. artifact_admission.py の scope と4分岐

対象：[artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/campaign/artifact_admission.py:76)

現行2定数の確定案は次です。P4 の内訳「63＋22」は D2081 条件2に従って落とします。

```python
CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (curated exact 85 path; source-import 推移閉包ではない; "
    "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
    "2026-09-20 (f94b61fc8) の実測では 163 module、うち収載 85)"
)
CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "同実測の発見集合の未収載 78 module、同発見集合に入らない module、"
    "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
    "package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、"
    "外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり "
    "(収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない"
)
```

D2081 の4条件を満たします。発見集合の定義・日付・commit・数値を明記し、内訳を落とし、非 import 委譲の例外句を維持し、実行時計算や発行器名を追加しません。

`:98` の62歴史 scope 定数群の後に、次を**独立文字列として凍結**します。これは変更前 `:76–86` と連結後の文字列が byte 単位で同一です。

```python
T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (curated exact 63 path; source-import 推移閉包ではない; "
    "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
    "2026-09-16 (a1b40608c) の実測では 162 module、うち収載 63)"
)
T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "同実測の発見集合の未収載 99 module、同発見集合に入らない module、"
    "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
    "package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、"
    "外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり "
    "(収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない"
)
```

4か所の差分骨格：

```diff
@@ HistoricalCampaignVerifierEpoch.__post_init__ :249
             and (self.identity_scope, self.excluded_scope) in (
                 # 既存24組、62組
+                (T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE,
+                 T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE),
             )

@@ _RecordedCampaignVerifierEpoch.__post_init__ :306
+            elif scopes == (
+                T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE,
+                T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,
+            ):
+                expected_paths = (
+                    campaign_lock.T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS
+                )
             else:
                 raise TypeError(...)

@@ _verify_committed_loader_binding :1055
                 in (campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS,
-                    campaign_lock.T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS)):
+                    campaign_lock.T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS,
+                    campaign_lock.T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS)):
             contract_loader_binding.verify_committed_contract_loader_blobs(
                 authority.contract_loader_commit,
                 authority.contract_loader_blob_sha256s,
                 authority.recorded_contract_loader_relative_paths,
             )
             return

@@ _recorded_campaign_verifier_epoch :1126、現行elseの直前
+    elif relative_paths == campaign_lock.T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS:
+        diagnostic = HistoricalCampaignVerifierEpoch(
+            campaign_verifier_epoch=display,
+            state="E1",
+            reason_code="recorded-closure",
+            identity_scope=T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE,
+            excluded_scope=T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,
+        )
     else:
         diagnostic = CampaignVerifierEpoch(...)
```

`:1106–1110` の hash preimage は変更しません。**scope は hash に含まれていません。** 記録順で hash を算出し、その grammar 固有の scope を診断へ添える現行仕様を維持します。

`:1082` と `:1185` の説明には exact-63 を追記します。`:1016` の目的別 decoder 選択、`:1157` の certified gate は変更しません。

## 3. contract_loader_binding.py

対象：[contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/campaign/contract_loader_binding.py:577)

**変更は `:2,58,61` の docstring の63→85だけで足ります。**

実コードでは `verify_committed_contract_loader_blobs :577` が `relative_paths: tuple[str, ...]` を受け、`:585–587` でその引数をそのまま `_iter_blobs` に渡しています。現行 tuple との一致検査も `ContractLoaderBinding` の構築もありません。

さらに `_iter_blobs :350` は与えられた列を `tuple(relative_paths)` として扱い、各 path の安全性を検査して blob を取得します。従って63／62／24の記録 tuple をそのまま照合できます。grammar の白名単は呼出し側の codec／authority が担い、この関数へ追加しません。

## 4. 独立 literal・固定値・新設テスト

対象5 file：

- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_t671_source_binding.py:104)
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_artifact_admission.py:283)
- [test_campaign_lock_codec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_campaign_lock_codec.py:100)
- [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_layer3_report.py:1915)
- [test_s1_9pair_figure_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_s1_9pair_figure_provenance.py:74)

| file:line | 追随内容 |
|---|---|
| `test_t671_source_binding.py:104` | 22本の独立 literal `_T2344_ENFORCEMENT_SOURCE_PATH_SUFFIX` を直前に追加。期待列を既存24＋既存39＋新22の展開で構成する。production 定数は参照しない |
| 同 `:264–272` | 件数24、39を維持、新 suffix の22を追加、合計を85へ |
| 同 `:438,573,621,750` | fixture／parametrize が独立期待列を使うので85本へ自動拡張。捕捉・live drift・lock/WAL不変・dirty fixture を新22本でも検査 |
| `test_artifact_admission.py:283` | `_EXPECTED_E1_CLOSURE_PATHS` に22本を独立記述して85へ |
| 同 `:349,352` | 下記の新しい固定値に変更 |
| 同 `:761` | fixture docstring の `exact 63-path` を85へ |
| 同 `:1447` | 新 scope 2文を production 定数参照ではなく独立文字列で期待する |
| 同 `:1574,1581` | 件数63→85 |
| 同 `:591` 付近 | exact-63 の独立63 literal、固定 epoch、固定 path hash を追加。62の固定値は不変 |
| `test_campaign_lock_codec.py:100–129` | `_authority()` は現行 tuple を列挙するため85へ自動追随。`:112` の `start=4` は維持 |
| 同 `:19,563` | 既存62 literal／helper は維持。63独立 literal と `_t2429_exact63_v2_value()` を兄弟追加 |
| `test_layer3_report.py:569` | `_historical_exact_grammar_campaign` に63分岐を追加し、新しい test-only rewrite helper を呼ぶ |
| 同 `:1915,1943,2020` | 歴史 param を `[63, 62, 24]` にする |
| 同 `:1933` | 歴史 epoch 表へ63の固定値を追加 |
| 同 `:1994,2002` | 現行 param と条件を63→85へ |
| 同 `:2047` | `test_material_knowledge_identity_argument_preserves_current_and_v1` の現行ラベルも63→85へ |
| `test_s1_9pair_figure_provenance.py:74–90` | `CURRENT_E0_EPOCH` の scope 2文だけ新文面へ。`:92` 以降の `FROZEN_E0_EPOCH` は不変 |

固定値は次になります。

```python
_FIXED_SYNTHETIC_E1_EPOCH = (
    "E1:bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7"
)
_FIXED_ORDERED_CLOSURE_PATHS_SHA256 = (
    "bea3624661166dbe20df206ebd1e4f855f8c13e39721ab67e8b19d981bd6b5a1"
)

_FIXED_T2429_EXACT63_EPOCH = (
    "E1:73f334f62ec13c394aae3d4787b80117562187984b6e0e372f2c0f7058b8ced2"
)
_FIXED_T2429_EXACT63_PATH_SHA256 = (
    "2247e5312a327caca9d0d4be081457eaf196513764010f64ccad1561409399ec"
)
```

**親による repo 外での独立導出手順：**

1. 変更前 test の独立63 literal を repo 外の計算入力へ転記する。
2. `layer1-edges.json` の22 key を sorted 順で末尾へ追加し、85本・重複なしを確認する。
3. production の import、tuple、epoch helper を使用せず、以下を計算する。
4. 結果だけを test の固定文字列として貼る。テスト実行時に固定値を再生成しない。

```python
# paths は独立に転記した宣言順の85 path。
# index は1始まり。改行は LF 1 byte。
blob_i = SHA256(f"epoch closure fixture {index}\n".encode("ascii")).digest()

epoch = "E1:" + SHA256(
    b"campaign-verifier-epoch/v1"
    + b"".join(path.encode("utf-8") + b"\0" + blob_i
               for index, path in enumerate(paths, 1))
).hexdigest()

ordered_path_hash = SHA256(
    b"".join(path.encode("utf-8") + b"\0" for path in paths)
).hexdigest()
```

domain の後に余分な NUL は入りません。blob 部分は hex のASCII文字列ではなく32-byte digestです。本段でも変更前の test literal と指定JSONから同式をメモリ内計算し、上記値を得ました。63の位置が変わらないため、歴史63の固定値は変更前の現行固定値と一致します。

**新設63テストは既存62テストの兄弟とします。** 以下は提案 node 名です。

| 配置先・先例 | 新設 node と主張 |
|---|---|
| codec `:575` | `test_t2429_exact63_uses_dedicated_historical_decoder_type`：str／bytes decoder とも厳密に `DecodedHistoricalCampaignLock`、authority の宣言順63、通常 identity 検証には渡せない |
| codec `:598` | `test_t2429_exact63_remains_rejected_by_normal_decoder`：通常str／bytes decoder が exact-key で拒否 |
| codec `:610` | `test_t2429_exact63_rejects_unknown_grammars`：subset／superset／同数別集合／wire順序違い。兄弟 validator と歴史 decoder の両方で拒否 |
| codec `:636` | `test_t2429_exact63_authority_requires_exact_declared_order`：宣言 grammar の変形、map順序違い、authority key・serial・各digest不正を検査 |
| admission `:3206` | `test_t2429_exact63_is_readable_only_as_recorded_historical_epoch`：HISTORICAL_RAW成功、固定epoch、旧scopeの独立文字列、`unknown`、dirty liveでも歴史値不変、lock/WAL bytes不変 |
| admission `:3250` | `test_t2429_exact63_is_rejected_for_certified_use`：view API／epoch API／`classify_campaign` が codec 段で拒否 |
| admission `:3269` | `test_unknown_t2429_exact63_grammar_is_rejected_for_both_read_purposes`：未知4変形を両purpose・両APIで拒否 |
| admission `:3301` | `test_t2429_exact63_rejects_each_recorded_commit_blob_mismatch`：独立63 literal の全pathをparametrizeし、両歴史APIで対象pathを含む blob-mismatch |
| admission `:3323` | `test_t2429_exact63_epoch_requires_matching_scope_and_paths`：63 scope組の片側差し替え、24／62／85 mapとの不一致、map順序違いを拒否 |

新しい63 rewrite helper は**合成 fixture 専用**です。記録済み lock の書換えには使用しません。

## 5. 既存の否定側テストの棚卸し

ここでいう「grammar」は enforcement source の path grammar です。WAL stage、report JSON、policy shape の未知値テストとは区別します。

| 既存 node・行 | 変形／判定 | 追随 |
|---|---|---|
| codec `test_historical_decoder_rejects_unknown_blob_map_grammars :249` | 24→23、24＋worker→25、24の1本をworkerへ置換。すべて未知 | 維持 |
| codec `test_historical_decoder_rejects_reordered_blob_map_wire_keys :269` | 24のwire順序違い | 維持 |
| codec `test_t733_exact62_rejects_unknown_grammars :610` | 61、62＋`unknown_t2483.py`→63、62の置換、順序違い | 63本のケースもworkerを欠く別集合なので未知。維持 |
| codec `test_t733_exact62_authority_requires_exact_declared_order :636` | 上と同じ宣言tuple変形、およびblob map順序違い | すべて不正のまま。維持 |
| codec `test_v2_rejects_extra_authority_and_blob_keys :331` | 現行＋`extra.py`、またはauthority余分key | 更新後86本。不正のまま |
| codec `test_v2_rejects_each_missing_enforcement_source_blob_key :344` | 現行から各1本欠落 | 更新後84本で未知。現行63時にworker欠落が既知62となる場合も、通常decoder拒否の主張は正しかった |
| codec `test_v2_rejects_legacy_exact_two_source_blob_keys :357` | 2本 | 未収載のまま |
| codec `test_v2_rejects_pre_wave_exact_twelve_source_blob_keys :378` | 12本 | 未収載のまま |
| admission `test_unknown_pre_t733_grammar_is_rejected_for_both_read_purposes :2102` | 23、25、同数置換、順序違い | すべて未知。維持 |
| admission `test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes :3269` | 61、unknown path付き63、同数置換、順序違い | すべて未知。維持 |

`test_layer3_report.py` には、**source path の未知 grammar を生成して拒否させる既存テストはありません**。`:1944` は既知の歴史62／24を certified で拒否するテストです。63を追加します。`:5619` の `test_verification_closure_unknown_mutation_rejected` は検証payloadのAST上の未知書込みを扱い、source path grammar とは無関係です。

新しい63否定例では、先例の `paths[:-1]` を機械的にコピーしてはいけません。63の末尾 `verify_fanout_worker.py` を落とすと既知の exact-62 になります。

具体的には次を採ります。

- **subset：** `env_contract.py` を落とす。62本だがworkerを含むので既知62とは異なる。
- **superset：** `unknown_t2344.py` を加える。64本。
- **同数別集合：** `env_contract.py` を `unknown_t2344.py` へ置換する。63本だが別集合。
- **順序違い：** wire key の先頭2本を交換し、`sort_keys=False` で出す。宣言tupleの順序違いも authority を直接構築して別途検査する。

各未知 fixture について、wire列が85／63／62／24のどの sorted tuple とも一致しないことを拒否呼出し前に検査します。また現行85から1本を落とした84 grammar の歴史decoder拒否も、新 codec node のケースに加えます。これにより、既知63の歴史受理を「未知拒否」の期待へ混ぜません。

## 6. 歴史 decoder／authority の consumer

repo 内 Python の直接参照は以下です。`campaign_lock.py` 内部の構築・wrapperも含めています。

| consumer | 参照位置 | exact-63前進後の挙動 |
|---|---|---|
| `campaign_lock.py` | authority型宣言 `:267,299`、現行からの変換 `:433`、24／62 validator `:449,494`、decoder `:680`、bytes wrapper `:870,880` | 63が現行変換から専用63 validatorへ移る。返却は歴史型のまま |
| `artifact_admission.py` | wrapper `:1005,1009`、purpose dispatch `:1024`、authority型による記録順選択 `:1099` | 63を旧scope付き `HistoricalCampaignVerifierEpoch` にする。committed照合は63専用tuple。certifiedはcodecで拒否 |
| `b10_backoff_shape_sweep.py` | decode `:3135`、pre-T733限定 `:3141` | **63は引き続き拒否。** pre-T733 exact-24限定を変更しない |
| `b10_backoff_static_tail_formal.py` | `load_explore_correctness_mode :351–353` | exact-63 explorationを歴史経路で読め続ける。run_kind／mode検査は維持 |
| 同 | `load_formal_campaign :393`、通常decode `:396`、certified admission `:398` | exact-63 formalは新checkoutから拒否される。歴史経路へのfallbackは追加しない |
| `layer3_report.py` | `_read_campaign_lock :119–139` | historical reportでは63を読め続け、epoch投影が63歴史scopeになる。accepted reportは通常decoderで63を拒否 |
| `test_b10_backoff_shape_sweep.py` | `:2537` | 既存24 fixtureの歴史decode。変更不要 |
| `test_campaign_lock_codec.py` | decode `:219,266,284,578,579,633`、authority型／構築 `:585,642` | 既存24／62テストを維持し、前節の63兄弟テストを追加 |

特に、`load_explore_correctness_mode` の読取り継続と `load_formal_campaign` の拒否は別の帰結です。後者を通すための decoder／purpose 変更は行いません。

## 7. live検証が広がる範囲と既存test・運用

追加でclean committedを要求されるのは、節1末尾の22本すべてです。列挙を短くすると次です。

- calibrator：`analyze.py`、`benchparse.py`、`model.py`、`perfparse.py`、`tsc.py`
- campaign：`agent_outputs.py`、`backoff_hole_grammar.py`、`durable_root.py`、`materializer_admission.py`、`p3_b4_admission_record.py`、`p3_b4_closed_critic.py`、`p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_s4_loop_trigger_gating.py`、`paper_story_a1_source.py`、`pin.py`、`reflux_result_evidence.py`、`s8b_compiler_input.py`、`s8b_expected_materialization.py`、`silo_ladder_rung1.py`、`sort_swo_dependency_material.py`
- critic：`digest.py`

実際の条件は「repo全体の `git status` が空」ではありません。

- `capture_contract_loader_binding :518` は、各収載pathがHEAD blobとして取得でき、安全に読める通常fileであり、**disk bytes＝HEAD blob**を要求します。
- `verify_live_contract_loader_binding :535` は、**記録digest＝記録commit blob、disk bytes＝記録commit blob**を要求します。現在HEADと記録commitの一致そのものは要求しません。
- certified読取は `artifact_admission.py:1173` でcaptureし、現在の85本が利用可能かを検査します。記録epochと現在epochの同一性は追加しません。
- 新規起動は `ident.py:584 → :280`、resumeは `ident.py:392` から既存live検査へ入り、新22本も対象になります。

**loop／criticの実コードとtestで確認した点：**

| 箇所 | 確認結果 |
|---|---|
| `p3_s4_loop.py:1903,2278,2742` | certified admissionを実際に呼ぶ |
| `p3_s4_loop_sort.py:623,844` | 同上 |
| `p3_s4_loop_trigger_gating.py:1164` | 同上 |
| `p3_b4_closed_critic.py:773,1823` | snapshot／receipt再検査でcertified admissionを呼ぶ |
| 各loopの `run_campaign` 呼出し：base `:1986,2165`、sort `:413`、trigger `:811` | campaign起動経路もlive検査の対象 |
| `test_p3_s4_loop.py:1007`、sort test `:182`、trigger test `:248` | `_critic_view` は共有fixture lockを作った後、実certified admissionを呼ぶ |
| `test_p3_b4_closed_critic.py:282` | `_admitted_digest` が実certified admissionを呼ぶ |
| `campaign_lock_test_support.py:10–18` | fixture lockはHEAD blobから作り、dirty diskを無視する。ただし後続certified admissionのcaptureは省略しない |
| `test_p3_s4_loop.py:3508,3544,4579` | 編集対象はtmp下の候補source。収載するPython driver自体のdirty化ではない |
| `test_p3_b4_closed_critic.py:605,1986` | projectionのsource bytesを読むテスト。対象Python fileを書き換える処理ではない |
| `tools/pegasus/p3_s4_loop_pegasus.sh:237–242` | 既にsuperprojectのtracked dirtyを起動前拒否。新22本の未コミット編集もこの運用では従来から拒否される |

調べたテストには、これら4つのPython fileを意図的にdirtyにしてcertified成功を期待するケースは見つかりませんでした。ただし、**開発者がそれらを編集したcheckoutで既存criticテストを走らせる場合、従来通った実certified読取が新たに拒否されます。** これは共有fixture helperがHEAD blobを使っていても起きます。

docs検索では `docs/archive/worklog-phase3-0702-0713.md:808` に未コミットの `p3_s4_loop.py` とcampaign実走の過去記録がありました。現在のcertified契約以前の記録であり、現運用の許容根拠にはしません。現在の外部稼働状態はこの静的検査では確認していません。

テスト側では、既存T671の全path drift parametrizeが新22本を覆います。加えて `test_artifact_admission.py:1939` のdirty→拒否／commit後→受理の既存パターンに、新22本を対象とする兄弟 node `test_t2344_certified_acceptance_rejects_each_new_source_drift` を追加すれば、loop／criticを含む中央certified gateの帰結を直接確認できます。

## 8. 変異事前登録候補

以下は**未実行の候補**です。新設node名は節4・7の提案名です。

**正例：収載追加が実際に効くことを検査する変異**

| 何を変異させるか | 落ちるべきtest node |
|---|---|
| production85 tupleから `calibrator/analyze.py` を1本削除 | `test_t671_source_binding.py::test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths` |
| 追加22本のうち隣接2本を交換 | 上記独立literal test、`test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture` の固定epoch |
| productionとtest期待列の両方で同じ2本を交換し、固定値は維持 | `test_certified_acceptance_admits_exact_e1_fixture` の固定epoch／ordered-path hash |
| live比較のループで新path `p3_s4_loop.py` をskip | `test_t671_source_binding.py::test_live_verification_rejects_each_dirty_enforcement_source[p3_s4_loop.py]` |
| captureで `p3_b4_closed_critic.py` のdisk照合をskip | `test_loader_drift_rejected_before_campaign_lock_or_wal_bytes[p3_b4_closed_critic.py]`、新 `test_t2344_certified_acceptance_rejects_each_new_source_drift` の該当param |
| exact-63の記録blob照合からworkerをskip | 新 `test_t2429_exact63_rejects_each_recorded_commit_blob_mismatch` のworker param |
| 63歴史scopeに新85 scopeを割り当てる | 新 `test_t2429_exact63_is_readable_only_as_recorded_historical_epoch`、scope/map対応test |

**負例：未収載・未知 grammar と認証境界を検査する変異**

| 何を変異させるか | 落ちるべきtest node |
|---|---|
| `HistoricalCampaignLockAuthority.__post_init__` のexact tuple白名単を「63を含むsuperset可」へ緩める | 新 `test_t2429_exact63_authority_requires_exact_declared_order` の64本superset直接構築 |
| 63兄弟validatorのwire比較を集合比較へ変える | 新 `test_t2429_exact63_rejects_unknown_grammars[order]` の**validator直接呼出し**。outer canonical検査による代替拒否では済ませない |
| 63兄弟validatorをsubset許容へ変える | 同nodeのsubset直接呼出し。欠落はworkerではなく `env_contract.py` |
| 通常 `_validate_authority` の受理集合へexact-63を加え、返却mapも63で構成する | 新 `test_t2429_exact63_remains_rejected_by_normal_decoder`、`test_t2429_exact63_is_rejected_for_certified_use` |
| 歴史63を現行分岐へ送るだけに変更 | 新 `test_t2429_exact63_uses_dedicated_historical_decoder_type`／歴史admission正例。通常decoderが63を拒否するので歴史正例が赤 |
| 歴史decoderと対応validatorのgrammar選択を63 superset許容へ変更 | 新 `test_unknown_t2429_exact63_grammar_is_rejected_for_both_read_purposes[superset]`。期待する失敗段はcodec |
| 現行85から1本欠けた84を歴史decoderで受理する | 新codec未知grammarの84ケース |

最後から2つ目のように複数のexact検査がある候補では、**白名単だけを緩めても後段が拒否して生き残る可能性があります。** 事前登録では変更箇所を明記し、局所validator／authorityの直接テストと、目的別APIの経路テストを分けます。単なる例外発生ではなく、codec拒否・blob拒否・live拒否のどれを検査するかを固定します。

## 総括

既存63の順序を保って22本を末尾追加し、exact-63はT-2483同型の独立literal・兄弟validator・旧scopeで収載します。
通常v2 grammarは85のみ、歴史63／62／24の別型・記録blob照合・epoch hash式を維持します。
最大の実装リスクは、63の末尾削除を未知例にして既知62と衝突させることと、wire順／宣言順の混同です。
運用上は旧63 campaignの新checkoutでのcertified拒否と、新22本のdirtyによるlive拒否が生じます。
本段は静的確認と独立hash計算のみで、変更・pytest・変異実走は行っていません。