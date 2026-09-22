## 実装した内容

所有範囲の新規 **10 file** を実装しました。

| file | 内容・対応仕様 |
|---|---|
| `orchestrator/campaign/silo_function_policy_api.hh` | API 型・固定3署名。include・前処理指令なし。設計 §2.5 |
| `orchestrator/campaign/axis_silo_function_policy.py` | 軸定数、上限、enum 順、意味による7記録点の写像、方策一覧。設計 §2.5〜2.6 |
| `silo_function_policy_hand/abort0.cpp` | abort 後0、競合時即 abort |
| `silo_function_policy_hand/maxwait.cpp` | abort 後1000、競合時 retry・50 |
| `silo_function_policy_hand/static5.cpp` | abort 後5、競合時即 abort |
| `silo_function_policy_hand/static10.cpp` | abort 後10、競合時即 abort |
| `silo_function_policy_hand/retry.cpp` | abort 後0、競合時 retry・0 |
| `silo_function_policy_hand/huge.cpp` | abort 後4294967295、競合時即 abort |
| `orchestrator/tests/test_silo_function_policy_template.py` | 実 patch 適用、API 負対照、方策、要因、骨格、identity の8 test と自走 harness |
| `patches/silo-function-policy-variant.patch` | 以下の骨格。設計 §2.4〜2.6、裁定 A9・B7・§9 |

手書き6方策は `orchestrator/campaign/` 配下です。裁定 §3・B4 に従い、空の `PolicyState` と無名の未使用引数を使っています。

骨格 patch の hunk ごとの挙動：

| 原本位置 | ON | OFF |
|---|---|---|
| Options:24・67付近 | CACHE と universal define を追加 | 既定値0 |
| T:9後 | 値・前提 flag 検査、API byte 埋込み、単一 hole、状態・要因・固定seed PRNG・64bit待機器・noipa wrapper 3本 | API・hole・骨格を除去 |
| T:47 | abort hook →1000µs clamp→待機。分析計数を維持 | stock Backoff 呼出しを逐語保存 |
| T:56後 | 要因を unset に戻す。PolicyState は維持 | 追加処理なし |
| T:98 | insert_node 記録 | 追加処理なし |
| T:158〜184 | tuple ごと32周回、CAS失敗も計数。retry は50µs clamp後に再読込。上限・abort・未知値は prefix unlock 出口 | stock の条件分岐・goto を逐語保存 |
| T:187 | update_absent 記録。既存 absent 出口を維持 | stock |
| T:458・470・481 | read_tid・read_locked・node_validation 記録 | 追加処理なし |
| T:708後 | writePhase 後に成功通知を1回 | 追加処理なし |
| T:739 | scan_node 記録 | 追加処理なし |

CAS、`max_wset_` 更新、既存 TRACE ブロックは共通部に残しました。

## 確認の実測

- `git -C external/ccbench apply --check <patch>`：**rc=0**
- compiler：**g++ 11.4.0**
- 単独 TU：`-std=c++17 -Wall -Wextra -Werror -fsyntax-only`

| 方策 | rc |
|---|---:|
| abort0 | 0 |
| maxwait | 0 |
| static5 | 0 |
| static10 | 0 |
| retry | 0 |
| huge | 0 |

軸定数・新 test の `python3 -m py_compile`：**rc=0**。

以下はすべて **実装済み・未実走**。file は `orchestrator/tests/test_silo_function_policy_template.py` です。

- `test_patch_touch_set_marker_and_empty_stock`
- `test_flag_errors_require_closed_values_and_explicit_prerequisites`
- `test_api_bytes_and_one_byte_negative_control`
- `test_default_body_and_quarantine_parser`
- `test_axis_reason_enum_order_and_hand_policy_contracts`
- `test_reason_sites_are_bound_to_transaction_operations`
- `test_lock_bounds_reload_prefix_unlock_and_hook_lifetime`
- `test_source_identity_off_inert_on_honest_includes_and_trace_diff`

## 現行の受理・拒否挙動と波及

開始時は clean、終了時の `git status` は所有する新規10 file だけでした。既存実装・test・共有 fixture・submodule に変更はなく、既存3軸の受理集合を変更していません。

新骨格は、軸値の未供給・0/1以外、および ON 時の前提 flag 未定義・不一致を `#error` にします。方策文法の受理検査は別単位です。

静的に確認した追随先：

- `condition_meaning_gate.py`：define specs、branch witness、site count と対応する閉集合 test。
- `test_ccbench_spawn_sites.py`：patch define inventory に新 macro が加わるため、registry 一致・define/sink 検査に波及。後続 driver の spawn 登録も必要。
- `materializer_admission.py` と対応 test：後続 compile・coverage/smoke の実行入口登録。
- `test_campaign.py::test_axis_driver_source_rel_within_edit_surface`：新軸 module の追加対象。
- `test_p3_s4_loop.py` の patch 別 `IZANAGI_` 許容集合：今回の骨格には該当 token なし。後続 probe・変異 patch の追加時に追随。
- B/C の consumer：API header、方策 dir、骨格 wrapper・記録点を入力として利用。
- `source_digest` の編集面・ALLOWLIST：今回の2 path は既存集合内で、拡張不要。

これらの所有外 file は変更していません。

## 未了と疑問

OFF inert、ON honest、include 一致、diff-of-diffs は test を実装しましたが、**成立の実測は未了**です。実 CCBench build、動的 hook・上限・再読込の検証も未実施です。

実装上の未決事項はありません。`focus.cpp` は担当外として未作成です。

## 総括

単位 A の10 file を実装し、patch 適用検査・6方策の構文検査・Python 構文検査は成功しました。静的 test 8件は未実走です。

docs・既存 tracked file・submodule は未変更、index・履歴を書く git 操作は未実行です。作業 dir は削除済みです。