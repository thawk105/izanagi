## 総括

[T-804] は、manifest に `spec_sha256` を掲載するだけでは閉じない。正しい実装は次の三点を不可分にする。

1. `verify_manifest` に default なしの `approved_spec: ReviewedSpec` を渡す。
2. manifest の `spec_sha256` と approval pin を照合したうえで、manifest の六投影を approved spec から再導出・完全一致比較する。
3. driver 2 経路、report、observations、judge まで pin を伝播し、各層の実発火を negative test で証明する。

P1/P3/P4/P5 は賛成。P2 も、未発行で exact-key verifier が旧形を拒否する現状では賛成する。コード、テストとも未変更・未実走であり、以下は base `856f4d4c` の静的調査結果である。

## 1. schema の正確な変更

### Manifest

`orchestrator/campaign/s8b_oracle_manifest.py:43-48` の exact key 集合で、`manifest_id` の直後に追加する。

```diff
 _MANIFEST_KEYS = {
-    "schema_version", "manifest_id", "freeze", "known_axes_freeze",
+    "schema_version", "manifest_id", "spec_sha256", "freeze", "known_axes_freeze",
```

併せて次を required 引数にする。

- `_build_manifest_from_snapshot`: `orchestrator/campaign/s8b_oracle_manifest.py:710-715`
- `build_manifest`: `:787-790`
- `build_manifest_from_ratified`: `:810-813`

`orchestrator/campaign/s8b_oracle_manifest.py:764-782` の構築辞書では `schema_version` の直後へ置く。

```python
"schema_version": SCHEMA_VERSION,
"spec_sha256": _sha256_text(spec_sha256, field="spec_sha256"),
"freeze": freeze_record,
```

`build_approved_manifest` は `orchestrator/campaign/s8b_oracle_manifest.py:1143-1182` で既に捕捉した `approved.sha256` を `build_manifest_from_ratified(..., spec_sha256=approved.sha256)` へ渡す。

### `manifest_id` への影響

`orchestrator/campaign/s8b_oracle_manifest.py:706-707` の式自体は変更しない。

- build 側は `:783` で、`spec_sha256` を含む document に対して `_manifest_id(document)` を呼ぶ。
- verify 側は `:1088-1091` で `manifest_id` だけを除去するため、再計算 preimage に `spec_sha256` が残る。
- `manifest_sha256` (`:163-169`) と `VerifiedManifest.sha256` (`:1092-1095`) にも自動的に含まれる。

したがって、spec pin だけを変えて他 field が同一でも `manifest_id` と manifest canonical SHA-256 は変わる。特別な `pop("spec_sha256")` は入れない。

### Observations

`orchestrator/campaign/s8b_oracle_report.py:1718-1727` の出力辞書で `manifest_sha256` の直後へ追加する。

```diff
         "manifest_kind": manifest_kind,
         "manifest_sha256": manifest_sha,
+        "spec_sha256": spec_sha,
         "n_per_cell": n,
```

- `VerifiedManifest` 経路では、検証済み `document["spec_sha256"]` をコピーする。
- `LegacyManifest` の自己申告値はコピーせず `None` にする。schema_version を剥がした manifest が正しい hash 文字列だけを laundering する経路を作らないためである。
- `orchestrator/campaign/s8b_oracle_artifacts.py:149-153` は現在も version classifier であり exact top-level validator ではない。ここを別用途の exact validator に変えず、field の必須性と pin 一致は judge で発火させる。

`orchestrator/campaign/s8b_oracle_artifacts.py:20-21` の manifest / observations version は P2 のとおり `v1` を維持する。

## 2. `verify_manifest` と `seal_verifier` の同時変更

`typing` import (`orchestrator/campaign/s8b_oracle_manifest.py:18`) に `TYPE_CHECKING` を足し、型検査専用に `ReviewedSpec` を forward importする。runtime の exact type 検査は後述の canonical `s8b_oracle_spec` module 内 helper に置く。

逐語 diff 案は次のとおり。

```diff
@@ orchestrator/campaign/s8b_oracle_manifest.py:113-118 @@
     def seal_verifier(function):
-        def verified(path, *, root, freeze_document, freeze_sha256):
+        def verified(
+            path, *, root, freeze_document, freeze_sha256, approved_spec,
+        ):
             return function(
                 path, root=root, freeze_document=freeze_document,
-                freeze_sha256=freeze_sha256, _seal=seal,
+                freeze_sha256=freeze_sha256, approved_spec=approved_spec,
+                _seal=seal,
             )
```

```diff
@@ orchestrator/campaign/s8b_oracle_manifest.py:985-988 @@
 @_seal_verified_manifest
 def verify_manifest(
-    path, *, root, freeze_document, freeze_sha256, _seal,
+    path, *, root, freeze_document, freeze_sha256,
+    approved_spec: ReviewedSpec, _seal,
 ) -> VerifiedManifest:
```

`approved_spec` は両 signature とも keyword-only、default なしとする。wrapper が引数を落とせば既存の正常系 verify test が TypeError になることに加え、`inspect.signature` で default 不在も固定する。

`orchestrator/campaign/s8b_oracle_spec.py:51-58,79-153` を利用し、`validate_approved_spec_snapshot` 相当の helper を `:153` の直後へ追加する。内容は以下とする。

- `type(value) is ReviewedSpec` の canonical namespace exact 検査。
- `APPROVED_SPEC_SHA256` が `None` なら `no-approved-spec`。
- pin、`ReviewedSpec.sha256`、`sha256(raw_bytes)` の三者一致。
- `raw_bytes` を strict parseし、canonical bytes、`document`、再生成 schedule が object 内 snapshot と一致。
- `validate_reviewed_spec(..., root=root)` を再利用する。
- disk 上の spec は再読しない。

これにより、dataclass の属性だけを偽造・事後変更した object も verifier の権威にはならない。

## 3. 内容再導出照合

`verify_manifest` の既存検査順を緩めない。既存の schema、freeze、schedule self-hash、cell product、floor/budget、preimage、manifest ID 検査を残し、`orchestrator/campaign/s8b_oracle_manifest.py:1082-1086` の既存 reasons 検査後、`:1088` の manifest ID 検査前に approved projection の比較を置く。これなら従来の malformed input は従来 validator で先に落ちる。

| 投影 | expected の作り方 | 比較 |
|---|---|---|
| schedule | spec の `schedule_parameters` を `build_schedule` (`:219-268`) で再生成 | dict/list の deep equality。`n`、`master_seed`、blocks、全 row 順序を含む |
| campaign_ids | spec document の mapping。既存 `:1052-1058` で block 対応と一意性を検査 | dict deep equality |
| run_contract | manifest 側を `_validate_run_contract` (`:394-425`) で正規化 | spec の exact mapping と deep equality |
| binding_identity | manifest 側を `_validate_binding_identity` (`:485-535`) で正規化 | spec の list と順序込み deep equality |
| allowed_excluded_reasons | 既存 `:1082-1086` の型・重複検査結果 | list の順序込み deep equality |
| generator_versions | `_validate_generators` (`:428-468`) で exact key/path/実 byte hash を再検査 | spec mapping と deep equality |

さらに以下を独立に検査する。

- manifest の `spec_sha256` は `_sha256_text` で形式検査し、`approved_spec.sha256` と完全一致。
- manifest の `schedule_sha256` は従来どおり manifest schedule から再計算する。schedule 本体が spec 再生成値と一致するため、spec の `schedule_sha256` へ推移的に束縛される。
- `campaign_config_preimages` は既存 helper (`:695-703`) が schedule/run_contract/campaign_ids から再導出するため、三者を spec に束縛すれば独立の spec field は不要。
- freeze、known axes、floor/budget は approved spec の投影ではなく、既存の ratified freeze authority 検査を維持する。

攻撃 witness は「spec A の正しい SHA-256 を記録しつつ、別の有効な schedule/campaign/run contract を持ち、self-hash と manifest ID も再計算済みの manifest B」とする。hash 記録だけの実装なら B が通るが、上記 deep equality では落ちる。

P5 は `orchestrator/campaign/s8b_oracle_manifest.py:394-396` を独立に次へ変える。

```diff
-    if not isinstance(run_contract, Mapping) or not _RUN_CONTRACT_KEYS <= set(run_contract):
-        raise ManifestError("run_contract の必須 field が不足")
+    if not isinstance(run_contract, Mapping) or set(run_contract) != _RUN_CONTRACT_KEYS:
+        raise ManifestError("run_contract key 集合が不一致")
```

spec 全体比較が残っていても、この helper 自身の余剰 key 受理を残さない。

## 4. 各層への伝播

### Driver の standalone gate

`orchestrator/campaign/s8b_oracle_driver.py:35-44` で canonical `s8b_oracle_spec` を importする。

`_gate_check_core` の manifest branch (`:437-455`) で、freeze snapshot 捕捉後に次の順で実行する。

1. `approved = s8b_oracle_spec.load_approved_spec(root)`
2. `verify_manifest(..., approved_spec=approved)`

例外は既存どおり `manifest-verify:` refusal に変換する。pin が `None` の場合も許可側へ進まない。

### Driver の run flow

`run_block` の厳密 verify (`orchestrator/campaign/s8b_oracle_driver.py:1115-1129`) で approved spec を一度だけ loadし、同じ object を `verify_manifest` へ渡す。

verify 失敗後に `_gate_check_validated` → `_gate_check_core` が診断用再検査を行う可能性があるため、`_gate_check_core` (`:314-324`) と `_gate_check_validated` (`:543-560`) に private な `approved_spec` 伝播口を足し、load 成功後の再検査でも同じ object を使う。verifier 内で spec path を再読しない。

`config_for_block` (`orchestrator/campaign/s8b_oracle_manifest.py:1101-1124`) は変更しない。これは検証後の実行投影であり、未使用の `spec_sha256` を足しても受理集合を狭めないためである。

### Report

`orchestrator/campaign/s8b_oracle_report.py:39-47` で `s8b_oracle_spec` を importする。

official branch (`:1752-1762`) は ratified freeze の reverify 後に `load_approved_spec(root)` を一度呼び、同じ object を `verify_manifest(..., approved_spec=approved)` へ渡す。`:1767-1770` の例外集合には `ReviewedSpecError` を追加し、rc=2・output 不生成へ倒す。

`build_observations` (`:1599-1624`) は sealed `VerifiedManifest` からのみ spec hash を採る。LegacyManifest の値は権威にせず `None` とする。

### Judge

`orchestrator/campaign/s8b_oracle_judge.py:20-24` で canonical `s8b_oracle_spec` を importし、`judge_oracle` の top-level 検査 (`:137-143`) に次を追加する。

- module pin 自体が lowercase 64 hex でない、特に `None` なら `spec-sha256` reason。
- observations の `spec_sha256` が lowercase 64 hex でない、または module pin と不一致なら同 reason。
- mismatch 時は既存 `top_reasons` により verdict を `indeterminate` にする。

module 定数参照は I/O を行わないため、judge は入力とロード済み定数に対する純粋な決定関数のままである。一方、judge にできるのは pin 連続性の検査だけで、manifest 内容の再導出や observations の真正性証明はできない。この限界は主張に含める。

## 5. 伝播欠落の機械検査

### 静的 consumer pin

`orchestrator/tests/test_s8b_oracle_manifest.py:1323` の後へ、候補 nodeid  
`test_verify_manifest_consumer_modules_are_exactly_driver_and_report` を追加する。

AST で `orchestrator/campaign/*.py` を走査し、import alias を解決した `verify_manifest` call の module 集合を次へ完全一致させる。

```python
{
    "orchestrator/campaign/s8b_oracle_driver.py",
    "orchestrator/campaign/s8b_oracle_report.py",
}
```

併せて各 call が `approved_spec=` keyword を持つこと、公開 signature の `approved_spec` に default がないことを検査する。新 consumer は pin 更新と層別 negative test 追加なしには入れない。

### 層別 negative test

静的 pin 単独は「列挙しただけ」なので、次を本体にする。

- `orchestrator/tests/test_s8b_oracle_manifest.py`
  - `test_verify_manifest_rejects_valid_but_spec_divergent_projection`
  - field IDs: `schedule`, `campaign-ids`, `run-contract`, `binding-identity`, `excluded-reasons`, `generator-versions`
  - spec A の hash を manifest B に記録し、B の self-hash/preimage/manifest ID は正しく再生成する。
- `orchestrator/tests/test_s8b_oracle_driver.py`
  - `test_gate_check_rejects_manifest_derived_from_other_spec`
  - `test_run_block_rejects_manifest_derived_from_other_spec_without_side_effects`
  - 後者は `status=="refused"`、prepare/evaluate 0 回、campaign/budget/marker 不生成まで固定する。
- `orchestrator/tests/test_s8b_oracle_report.py`
  - `test_report_main_rejects_manifest_derived_from_other_spec_without_output`
  - real `verify_manifest` を通し、rc=2、output 不生成を確認する。verifier mock は使わない。
  - `test_legacy_manifest_cannot_launder_spec_sha256` で schema_version 剥離後の observations が `spec_sha256=None` になることも固定する。
- `orchestrator/tests/test_s8b_oracle_judge.py`
  - `test_spec_sha256_mismatch_forces_indeterminate`
  - 同じ otherwise-determinate observations で、pin 一致時は determinate、不一致時だけ indeterminate + `spec-sha256` reason になる metamorphic test とする。
  - `test_none_approved_spec_pin_is_fail_closed` も追加する。

P5 には `test_run_contract_rejects_extra_key` と、余剰 key を入れたうえで preimage/manifest ID を再計算した serialized manifest の verify 負例を置く。

## 6. 既存テストの影響棚卸し

静的な source/call-graph 調査結果は次のとおり。parametrize node 数は decorator を静的展開した値で、pytest collection 実測ではない。

| ファイル | direct `verify_manifest` 式 | 到達 test function | 展開 node |
|---|---:|---:|---:|
| `test_s8b_oracle_manifest.py` | 4 | 16 | 25 |
| `test_s8b_oracle_driver.py` | 4 | 49 | 53 |
| `test_s8b_oracle_report.py` | 1 | 92 | 144 |
| `test_s8b_binding_driftguards.py` | 0 | 2 | 2 |
| 合計 | 9 | 159 | 224 |

加えて、required `spec_sha256` を渡す必要がある既存 `build_manifest` source call は9箇所である。

- `test_s8b_oracle_manifest.py`: 6箇所
- `test_s8b_oracle_driver.py`: 1箇所
- `test_s8b_oracle_report.py`: 2箇所

judge の新 pin 検査により、`test_s8b_oracle_judge.py` の `judge_oracle` 利用は15 function／19 node が fixture 更新対象となる。

共通化は、現在の以下を新規 `orchestrator/tests/s8b_oracle_spec_fixture.py:new:1` へ抽出する。

- `_install_reviewed_spec_sources`: `test_s8b_oracle_manifest.py:188-195`
- `_reviewed_spec_document`: `:197-230`
- `_install_reviewed_spec`: `:244-249`

helper は以下を返す factory とする。

- 明示された schedule axes、run contract、campaign、binding、reasons、generator versions から作る `ReviewedSpec`
- 独立 serializer による raw bytes と SHA-256
- 必要なら temp repo の fixed path へ spec を設置し、canonical module の pin を monkeypatchする関数

negative test は「manifest に合わせて spec を自動生成する」fixture を使わず、spec A と manifest B を明示的に分離する。これを守らないと比較が恒真になる。

なお `_GENERATOR_SOURCES` (`s8b_oracle_manifest.py:53-61`) は report/judge/artifacts の実 byte hash を含む。B の編集後、A は `test_s8b_oracle_manifest.py:64-98` の独立 `PIN_GATE_SPEC_RAW` と `PIN_GATE_SPEC_SHA256` を最終 bytes に対して更新する必要がある。

## 7. 実装子2名への分割

### A — manifest/spec/機械検査

所有:

- `orchestrator/campaign/s8b_oracle_manifest.py`
- `orchestrator/campaign/s8b_oracle_spec.py`
- `orchestrator/tests/test_s8b_oracle_manifest.py`
- 新規 shared spec fixture
- consumer AST pin

### B — driver/report/judge/artifacts

所有:

- `orchestrator/campaign/s8b_oracle_driver.py`
- `orchestrator/campaign/s8b_oracle_report.py`
- `orchestrator/campaign/s8b_oracle_judge.py`
- `orchestrator/campaign/s8b_oracle_artifacts.py`（P2 採用時は version 定数を確認するだけで production diff 不要）
- 各対応 test と `test_s8b_binding_driftguards.py`

解消順序:

1. A が required API、wrapper、schema field、shared fixture を先に確定する。
2. B がその patch を取り込み、三 consumer と observations/judge を実装する。
3. A が B の最終 report/judge/artifacts bytes を取り込み、generator hash を含む独立 spec golden を更新する。
4. consumer pin と全 negative test を統合状態で確認する。

同一ファイル所有の重複はないが、generator hash と shared fixture は意味上の依存である。A/B を完全並列で終了扱いにせず、上記3の最終 A refresh を必須にする。

## 8. P1〜P5 への賛否

- **P1: 賛成。** required keyword、default なし、wrapper 同時更新は必須。さらに canonical exact type、pin/raw/document/schedule の in-memory snapshot 再検証を加える。
- **P2: 賛成。** 通常は required field 追加なら version bump が自然だが、本件は live artifact 0、旧形は `_MANIFEST_KEYS` で拒否、legacy 互換要求なしである。`docs/decisions.md:3677-3679` に「未発行なので v1 据え置き」の同型先例があり、`docs/decisions.md:8480-8483` の反対理由は persisted contract の in-place 変更である。最初の durable 発行後は同じ判断を再利用してはならない。
- **P3: 賛成。** judge の module pin 比較は純関数性を維持し、`None` も fail-closed にできる。ただし LegacyManifest の自己申告 hash を observations へ昇格させず、judge の保証を「pin continuity」に限定する。
- **P4: 賛成。** AST consumer pin は変更検知、層別 negative test は実効性証明として両方必要。後者なしでは恒真である。
- **P5: 賛成。** exact key 化は独立の穴を閉じる。spec deep equality と重複しても、builder・helper 単体の余剰 key 受理を残さず、受理集合の縮小方向だけである。

テストは一切実走しておらず、緑の主張はしない。ファイルへの書き込みも行っていない。