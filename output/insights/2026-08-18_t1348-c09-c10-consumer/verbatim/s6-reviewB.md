## 総括

着地不可。blocker 1件、must-fix 3件、nit 1件です。親実測の build 正例赤は実装上の再現性ある拒否です。pytestは実行していません。

### 1. Layer 3 の `trigger_binding` を C10 が誤って除外

深刻度: blocker

該当: [autonomous_trial_completeness.py:3325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3325)、[autonomous_trial_completeness.py:3345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3345)、[layer3_report.py:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/layer3_report.py:525)

Layer 3 は全 WAL record を `variants` と `source_refs` に射影する一方、C10 は `trigger_binding` を除いた集合と比較しています。

放置時: 実際の trigger binding 付き build report が C10 で拒否され、6 report build 正例と build 受理集合が常に赤になります。

### 2. admission failure の正当経路を C10 前段で拒否

深刻度: must-fix

該当: [autonomous_trial_completeness.py:2964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:2964)、[autonomous_trial_completeness.py:3015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3015)、[autonomous_trial_completeness.py:3206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3206)、[autonomous_trial_completeness.py:3224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3224)

role-attempt と proposal を無条件に要求してから、persisted Layer 3 不在の failure cell を処理しています。

放置時: 生成前に失敗した正当な failure cell は `layer3-chain-absent` を付ける分岐へ到達できず、裁定が許容した非認証受理集合から除外されます。

### 3. receipt parser の欠落 `schema_version` が raw `KeyError` 化

深刻度: must-fix

該当: [s8c_acceptance_receipt.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/s8c_acceptance_receipt.py:345)

v1/v2 の既存実装では exact key 検査が先でしたが、現在は `value["schema_version"]` を先に参照します。

放置時: `schema_version` 欠落の v1/v2/v3 bytes が `AcceptanceReceiptError` ではなく `KeyError` となり、既存 consumer の fail-closed 例外契約が変わります。

### 4. `layer3-chain-absent` の逐語 pin がない

深刻度: must-fix

該当: [trial_registry.py:3003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/trial_registry.py:3003)、[test_trial_registry.py:1336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/tests/test_trial_registry.py:1336)

tracked test を検索した範囲では、この新 reason code を期待する failure-cell テストがありません。build 正例は `t468` しか pin していません。

放置時: reason append の削除や条件誤りがテストで赤くならず、receipt の reason code 集合が黙って変わります。

### 5. 受入時間が campaign files 数に比例

深刻度: nit

該当: [autonomous_trial_completeness.py:2857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:2857)、[trial_registry.py:2905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/trial_registry.py:2905)、[trial_registry.py:2919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/trial_registry.py:2919)

C10 が campaign tree 全体を `rglob` し、各 artifact を再読・再ハッシュします。C09 の Layer 3 fresh rebuild と重複し、6 report fixture では campaign file 数、WAL record 数、provider/proposal 数に比例します。

放置時: 大きい campaign ほど acceptance の I/O と実行時間が増えます。

### Schema key 閉包

| schema | top-level | trial | 判定 |
|---|---|---|---|
| v1 | `BASE` | v1 keys | v2 の `arm_execution`、v3 leaf、origin は unknown |
| v2 | `BASE` | v2 keys、origin は任意 | v1 shape は missing、v3 leaf は unknown |
| v3 | `BASE + cross_binding_receipt_sha256` | v2 keys + v3 leaf、origin は任意 | aggregate または leaf 欠落は missing |
| 全 schema | `schema_version` 欠落 | - | 現状だけ raw `KeyError` |

`LEGACY_SCHEMA_VERSION` の production consumer は receipt module 内の v1 parse/verify 分岐だけで、既存 v1 fixture と Layer 3 import は残っています。v1/v2 の通常 key 閉包自体には、上記の欠落 `schema_version` 以外の穴は見つかりません。

### Pin 閉包

| pin | 現在の位置 | 判定 |
|---|---|---|
| C09 `trial_registry.py / assert_campaign_layer3_chain` | `test_s8c_preregistration_invariant.py:73`、呼出し `trial_registry.py:2905` | `classify` の同一 path symbol 分岐で CHECKS。適切 |
| C10 verifier 定義 | `test_s8c_preregistration_invariant.py:75`、定義 `autonomous_trial_completeness.py:3096` | CHECKS。適切 |
| C10 verifier consumer | `test_s8c_preregistration_invariant.py:76`、呼出し `trial_registry.py:2919` | CHECKS。適切 |
| `test_acceptance_v2...` 改名 | `test_trial_registry.py:2872` | v3 名へ更新済み。tracked path 側にも旧名 pin は見つからず |
| `_project_t822_receipt_v2_to_v1` 改名 | `test_reflux_originless_compatibility.py:604`、呼出し `:798` 他 | v3 名へ更新済み。旧名 pin は見つからず |
| v1/v2/v3 reason 集合 | receipt v1、v2、v3 の各 fixture | 既存集合は閉じている |
| `layer3-chain-absent` | `trial_registry.py:3003` | **未 pin。must-fix** |

`classify` の順序では、non-identifier、declared-unimplemented、同一 path symbol、different-module の順です。今回移動した3 pin は import または定義が同一 path に存在するため、CHECKS 移動は過不足ありません。`assert_trial_registry_acceptance` の different-module 除外と `authoritative bytes reread` の non-identifier 除外も妥当です。

### 反証できなかった点

- 12 field の通常経路は、bytes 再読、hash比較、WAL/L3 projection、admission decision 比較のいずれも失敗時に `_fail` へ到達します。ただし正例 fixture は `trigger_binding` を除外しており、実 build 統合の反証にはなっていません。
- `verify_autonomous_trial_files` からの呼出しは [autonomous_trial_completeness.py:3812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3812) にあります。
- no-build の `mode` と12 fieldの明示的 unbound、条件付き `no-build` reason は親裁定どおりです。
- working tree hash、時刻、絶対 path の固定値を期待値へ焼き込んだ箇所は見つかりません。
- `git diff` は指定どおり9 fileで、docs差分はありません。契約 JSON、評価器、凍結 record、producer の既存 Layer 3 呼出しにも差分はありません。
- もう一つの親実測赤である [test_s8c_preregistration_predicates.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/tests/test_s8c_preregistration_predicates.py:159) は、未 commit 状態表の tripwire として説明され、独立した実装回帰とは扱いません。

### そのまま着地させてよい部分

blocker を含む production file 全体は着地不可です。局所的には、v1/v2 凍結 fixture の保持、v3 aggregate 再計算テスト、v3 から v1 への projection 更新、C09/C10 の machine pin 移動、CLI verifier 呼出し、docs・契約・producer scope の不変部分はそのまま維持できます。