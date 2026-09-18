## 実装した変更 (file ごと、関数名と要点)

**実装済み・未達です。13ファイルを変更しましたが、接続正例の `active-valid` 到達と受入完了は確認できていません。**

以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/` を表します。

| file | 変更 |
|---|---|
| `C/s8b_ratified_freeze.py` | 両 validated 型に `validation_root`・`search_report` を追加。完全一致検査・artifact 再捕捉後に resolve 済み root と deep-freeze 済み report を格納 |
| `C/t080_freeze_migration.py` | 束縛比較を `_assert_holdout_report_bindings` に抽出。委譲 predicate、receipt・adapter の任意 token 引数を追加。通常 scan の例外正規化を維持 |
| `C/s8b_oracle_driver.py` | P3' の解決順へ変更。campaign-start 前に再 launch・identity 比較・委譲付き receipt 再解決 |
| `T/test_s8b_ratified_freeze.py` | immutable token test、既存 receipt root に emitter を接続する分岐 |
| `T/test_t080_freeze_migration.py` | 委譲境界の負例、束縛4ケース、既存例外正規化 lambda の keyword 対応 |
| `T/test_s8b_oracle_driver.py` | S による copy 切り離し、copy 差分検査、memo 合成化、接続 fixture・境界 test |
| `T/test_s8b_floor_campaign.py` | 両 clone 経路で S を削除。親・削除集合・残存 mode/OID 検査。実 scan 負例3ケースと削除契約 test |
| `T/conftest.py` | memo consumer を8件へ追随 |
| `T/test_real_repo_serialization.py` | golden・導出・8/8 pin・literal consumer 2本を追随 |
| `T/test_ccbench_spawn_sites.py` | 同じ evaluate sink の行番号を1788→1803へ追随 |
| `T/test_s8b_gate_core_exact_launch_validated.py` | constructor 新 field と `Path` import |
| `T/test_s8b_holdout_admission.py` | constructor 新 field |
| `T/test_s8b_oracle_report.py` | `ReverifiedFreeze` constructor 新 field |

作業 worktree の commit、docs、tracked output、growth hold、走査除外、allowlist は変更していません。

## 委譲 predicate の署名と発火条件 (現物の逐語)

`C/t080_freeze_migration.py:2221`：

```python
def _holdout_layer2_delegation(
    *, root: Path, validation_head: Optional[str], launch_validated,
) -> Optional[Mapping]:
    """直前の full launch validation の report だけを委譲候補にする。

    名前集合の digest は内容の鮮度を証明しない。caller は各 receipt 境界の
    直前に launch_validate を実行し、返した report に凍結 doc の束縛を課す。
    """
    from . import s8b_ratified_freeze
    try:
        # Historical verification and lookalike objects are not admission tokens.
        if type(launch_validated) is not s8b_ratified_freeze.LaunchValidatedFreeze:
            return None
        if launch_validated.validation_root != Path(root).resolve():
            return None
        if not (launch_validated.activation_head == validation_head == _capture_head(root)):
            return None
        ratified = launch_validated.ratified
        if ratified.activation_head != validation_head:
            return None
        active = s8b_ratified_freeze.resolve_active_generation(root)
        if (active.activation_head != ratified.activation_head
                or active.generation_sha256 != ratified.sha256
                or active.generation_number != ratified.generation_number
                or active.generation_commit != ratified.generation_commit):
            return None
        if launch_validated.search_digest != s8b_ratified_freeze._enumeration_digest(root):
            return None
        _assert_holdout_report_bindings(ratified.document, launch_validated.search_report)
        return launch_validated.search_report
    except Exception:
        # Predicate failure restores the ordinary scan; its errors are not suppressed.
        return None
```

束縛 helper は rr80/rr20 集合、`match_convention`、`candidate_id`、`expressions` を比較します。`_verify_holdout_live_scan` は入力 `holdout_doc` に対しても同じ比較を実行し、委譲不成立時だけ `_assert_search_pass(report)` を課します。

## driver の呼出し順 (gate_check / run_block / campaign-start 前)

- `gate_check`：freeze 読込み→v1/v2 判定→v2 loader→launch→receipt 解決。成功時のみ token 付き。v1・各失敗経路も token なしで1回解決。
- `run_block`：loader→launch→token 付き receipt 解決→既存 gate／campaign value。
- campaign-start 前：実 `launch_validate` 再実行→freeze SHA・activation HEAD・search digest 比較→新 token で receipt 再解決→既存4要素の epoch 比較。

adapter への driver token 転送は追加していません。refusal return は静的検査で**15箇所を維持**しています。既存 `call_count == 2` と2要素 side effect の期待値は未変更ですが、該当 test の実行はできていません。

## 接続正例 fixture の結果 (active-valid に到達したか、障害の現物)

**`active-valid` 到達は未確認です。**

接続 fixture は、初期 commit 前に既存 g1・budget input・selector 証拠を取り除き、R 発行後に既存 ccbench pin を使って protocol／selector seed／C／G／A／X を積む構造にしました。receipt 接続分岐では `_prepare_emitter_base`・`_make_fixed_ccbench` を再実行しません。

実行障害は次の2点です。

1. 実 emitter の直接呼出しが sealed snapshot 内で停止：
   ```text
   PermissionError: [Errno 1] Operation not permitted
   ExpectedMaterializationError: snapshot cleanup failed
   ```
   socket 送信拒否に起因します。検査を置換して token を生成していません。
2. 接続 test を含む driver module の直接 import が既存 guard に拒否：
   ```text
   GrowthTestHoldBypassRefused
   IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1
   ```
   growth hold は解除していません。

したがって、接続 fixture は**実装済み・未達**です。

## 4 経路の切り離し (S、各経路の変更、登録簿の追随)

S は official namespace 配下全 path と `V2_CANDIDATE_REL` exact file のみです。

1. **output copy**：除外後の集合から ancestor を構成。候補 directory 内の無関係 file を残す差分・bytes 検査を追加。直接実行は driver import guard で未達。
2. **floor clone 2経路**：S が非空の場合だけ削除 commit。source HEAD、gitlink commit、削除 commit／残存 tree を分離して検査。局所削除契約 test と実 scan 3ケースは直接呼出し成功。
3. **memo**：`_run` と直接利用3関数を合成 resolution へ変更。登録簿・golden・導出・literal 2本を追随。独立 AST 集計で残存8関数と opt-out 2関数を確認。
4. **g7**：exact refusal 集合は変更していません。実行未確認。

既存 callable fixture の6関数／11 node consumer pin は変更していません。新接続 fixture は builder を直接使用します。

## 追加・変更した test の nodeid 一覧 (正例 / 負例 / 対照の別)

各 file の接頭辞は `orchestrator/tests/` です。

**`test_t080_freeze_migration.py`**

- 負例：`::test_layer2_delegation_rejects_wrong_activation_head`
- 負例・同名集合対照：`::test_layer2_delegation_rejects_foreign_root`
- 負例：`::test_layer2_delegation_rejects_enumeration_drift`
- 負例3型：`::test_layer2_delegation_rejects_nonlaunch_type`
- 負例：`::test_layer2_delegation_rejects_stale_generation_token`
- 負例：`::test_delegated_scan_keeps_frozen_document_bindings[expressions|match_convention|candidate_id|candidate_set]`
- 既存追随：`::test_gate_normalizes_unexpected_check_exceptions_and_continues_g5`

**`test_s8b_ratified_freeze.py`**

- 正例・不変性・型負例：`::test_launch_token_retains_immutable_scan_and_root`

**`test_s8b_oracle_driver.py`**

- 正例：`::test_t080_active_v2_delegation_accepts_full_receipt`
- 負例：`::test_t080_failed_launch_preserves_receipt_refusal`
- 負例：`::test_t080_unactivated_chain_hit_is_invalid`
- 負例：`::test_v1_gate_does_not_delegate_with_active_v2`
- 負例：`::test_t080_active_v2_preserves_nonlayer2_receipt_refusal`
- 負例：`::test_t080_delegated_campaign_start_rechecks_receipt[changed|missing]`
- 負例：`::test_t080_delegated_campaign_start_rejects_late_hit`
- 負例：`::test_t080_draft_rejects_synthetic_hit_outside_replay_deletions`
- copy 対照：`::test_t080_output_copy_visibility_matches_production_enumeration`
- constructor／memo 追随：`::test_gate_check_core_rejects_reverified_freeze_token`
- 同：`::test_cli_output_root_default_is_none_and_run_block_refuses_without_root`
- 同：`::test_two_real_subprocess_oracle_submissions_only_one_acquires_g12_claim`
- 同：`::test_v3_cli_subprocess_returns_rc_3_on_protocol_violation`
- 同：`::test_run_block_reuses_launch_validated_and_legacy_loader_is_dead`
- 同：`::test_run_block_verifies_manifest_once_and_reuses_object`

**`test_s8b_floor_campaign.py`**

- 負例・無害 bytes 対照：`::test_clean_scan_rejects_synthetic_chain_artifacts[official|candidate|both]`
- 削除集合・空集合対照：`::test_replay_clone_removes_only_declared_chain_artifacts`
- 履歴 assertion 追随：`::test_real_seal_protocol_to_floor_official_core_e2e`

**その他**

- `test_real_repo_serialization.py::test_receipt_memo_prewarm_wiring_is_controller_only_and_lazy`
- `test_real_repo_serialization.py::test_receipt_memo_real_xdist_order_has_no_worker_payer`
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered`

周辺3 module の変更は共有 constructor helper への新 field 追加です。

## 自己検証の結果 (直接呼出し・反実仮想)

**DIRECT_CALL_PASS**

- floor 実 scan 負例3ケース。無害 bytes 受理、投入 path の実 hit、clean scan 拒否を確認。
- `test_replay_clone_removes_only_declared_chain_artifacts`
- migration の既存例外正規化 test。
- gate-core の既存 `test_public_reread_v2_requires_launch_validated`、`test_public_reread_v2_ignores_injected_ratified`
- admission の `test_oracle_and_n_pilot_producers_use_measurement_generation_schema`
- report の `test_legacy_manifest_rejects_reverified_freeze`
- evaluate sink の既存 pin test。

**反実仮想**

m8a 相当として、プロセス内だけで `clean_scan_digest` の `_assert_search_pass(report)` 呼出しを除去。3ケースとも：

```text
Failed: DID NOT RAISE FloorCampaignError
```

復元後の3ケースも直接呼出し成功。その他の predicate 反実仮想は、実 token の生成障害により**未実施**です。

**実行阻害・失敗**

- 委譲境界5関数、束縛4ケース、immutable token test：sealed snapshot の socket 拒否。
- driver／serialization：module import 時の growth-hold guard。
- report の `test_store_reverification_expected_sha_comes_from_reverified_freeze`：直接呼出しで `ReportError: official output_root は repository 外でなければならない`。この失敗は未解決で、成功扱いにしていません。

変更 test module はすべて import を試行しました。上記2 module 以外は import 成功。全変更13ファイルの AST parse、`git diff --check` は成功しました。pytest／`tools/run_tests.py` は実行していません。

## 所有外への波及 (静的列挙)

指定された検索語で production／tests を検索しました。

- `verify_receipt`：driver、`s8b_holdout_freeze.py:1210`、migration CLI、migration／driver tests。token なし既存 caller の呼出し形は維持。
- `_resolve_t080_receipt`：driver 各経路、`real_repo_receipt_memo.py`、driftguards、serialization の生成スクリプト。
- `patch_driver_resolver`：残存 driver 4関数、driftguards。memo endpoint 自体は変更していません。
- validated constructor：driver 4箇所、report、gate-core、admission の直接構築を追随。兄弟型 `ReverifiedFreeze` を含みます。
- consumer 登録簿：conftest、serialization、`test_run_tests_task_run.py` の選択検査へ波及。
- 共有 fixture：新しい接続 test の実 root 読取り分類、既存 serialization／resource inventory との整合は未実走です。

## 変異事前登録への対応 (s4 の m0〜m11 それぞれの anchor 位置 = file と old 逐語の候補)

すべて production の候補位置です。m8a 以外は注入・kill 未確認です。

| ID | anchor | old 逐語候補 |
|---|---|---|
| m0-comment | `C/t080_freeze_migration.py:2231` | `# Historical verification and lookalike objects are not admission tokens.` |
| m1-subset | `C/s8b_ratified_freeze.py:3550` | `if current != expected:` |
| m2a-ignore-receipt | `C/s8b_oracle_driver.py:200` | `allowed=not merged,` |
| m2b-accept-invalid | 同`:219` | `raise OracleDriverError(` と直後の `"T-080 campaign epoch を active-valid/never-issued のどちらにも固定できない"` |
| m3-skip-zero-hit-without-token | `C/t080_freeze_migration.py:2274` | `if not delegated:` と直後の `holdout_module._assert_search_pass(report)` |
| m4a-drop-expressions | 同`:2215` | `if live.get("expressions") != unknownness.get("expressions"):` |
| m4b-drop-match-convention | 同`:2202` | `if report.get("match_convention") != holdout_doc.get("match_convention"):` |
| m5-drop-campaign-start-recheck | `C/s8b_oracle_driver.py:1540` | `campaign_start_resolution = _resolve_t080_receipt(` から epoch 比較まで |
| m6-drop-activation-head | `C/t080_freeze_migration.py:2236` | `if not (launch_validated.activation_head == validation_head == _capture_head(root)):` |
| m7-drop-enumeration-digest | 同`:2247` | `if launch_validated.search_digest != s8b_ratified_freeze._enumeration_digest(root):` |
| m8a-clean-scan-no-assert | `C/s8b_floor_campaign.py:5534` | `_holdout_freeze._assert_search_pass(report)` |
| m8b-draft-no-assert | `C/t080_freeze_migration.py:1728` | `search_assertion(report)` |
| m9-drop-root-binding | 同`:2234` | `if launch_validated.validation_root != Path(root).resolve():` |
| m10-drop-generation-recheck | 同`:2241` | `active = s8b_ratified_freeze.resolve_active_generation(root)` と続く4要素比較 |
| m11-stale-token-at-campaign-start | `C/s8b_oracle_driver.py:1532` | `fresh_validated = s8b_ratified_freeze.launch_validate(ratified, root)` |

m6 は outer HEAD 比較だけを除き、`validation_head == _capture_head(root)` を残す置換が必要です。

## 未完・未実走・懸念

- **接続正例未達**。実装の受理集合を保証する証拠は揃っていません。
- **receipt 削除ケースの仕様不整合**：tracked file 削除後も列挙 digest は同じですが、実 scan が次の拒否を返すことを直接確認しました。
  ```text
  git が列挙した検索対象が file ではない: README.md
  ```
  receipt も scan 対象なので、削除時は再 launch の拒否が epoch 比較より先に発火すると考えられます。新 test の `[missing]` は要求どおり epoch refusal を期待したままです。期待値を緩めていません。
- 接続 fixture の静的／履歴検査、非層2 refusal の単一理由性、campaign-start 境界、copy 契約、floor 既存5 node、g7、serialization は未実走。
- predicate 反実仮想、正式な変異 matrix、両木焦点走、全受入は未実施。
- 新 test の resource 分類と共有 fixture の統合確認が残っています。
- 報告用 file は作成していません。変更は未 commit で残しています。

## 総括

**実装済み・検証未達のため、着地可能とは判断しません。** floor の切り離しと実 scan 負例は直接確認できました。次段には、socket が使える実行面での接続正例・predicate 反実仮想・受入、および receipt 削除時の拒否理由の整合確認が必要です。