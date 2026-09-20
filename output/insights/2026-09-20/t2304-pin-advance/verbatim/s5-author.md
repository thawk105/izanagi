## 変更の要約

実装済みです。tracked 8 file を変更し、使い捨て probe 2 本を追加しました。

| file | 変更 |
|---|---|
| `orchestrator/campaign/s8b_approved.py` | full SHA を `e9e477ca1b55348ab4530de0b1cf663ce4555290` に更新。説明 2 箇所も追随。他の定数・関数・凍結 SHA は保持 |
| `orchestrator/campaign/pin.py` | `CURRENT_PIN = "e9e477c"`。前進履歴、D2150 項 1、T-2304、候補取得確認を追記 |
| `test_p3_build_authority_cli.py` | 独立 pin literal 1 箇所 |
| `test_p3_s4_loop_sort.py` | 同 1 箇所 |
| `test_p3_s4_loop_trigger_gating.py` | 同 1 箇所 |
| `test_s6_sort_sweep.py` | 同 1 箇所 |
| `test_s8a_trigger_sweep.py` | 同 2 箇所 |
| `test_t126_qualification_driver.py` | 同 1 箇所 |

`PREVIOUS_PIN`・`KICKOFF_PIN`・`KICKOFF_PIN_FULL` は指定どおり据え置きました。`buildcache.py`、docs、gitlink は編集していません。Git の add / commit / checkout / stash は実行していません。

## 追随・据え置きの分類表

行番号は入力資料の変更前番号です。以下の file はすべて `orchestrator/tests/` 配下です。

**53 行＝A 7 行・B 46 行。** A の差分が literal 置換だけであること、B の該当 file が HEAD と byte 一致することを確認しました。

| file:line | 群 | 理由 |
|---|---|---|
| `test_b10_extended_figure_provenance.py:200` | B | 旧測定 provenance fixture |
| `test_b10_extended_figure_provenance.py:204` | B | 同 fixture の gitlink |
| `test_b10_extended_figure_provenance.py:231` | B | 同 fixture の source identity |
| `test_backoff_counterfactual_analysis.py:27` | B | 旧解析系列の固定 pin |
| `test_backoff_policy_performance_analysis.py:36` | B | 旧比較系列の固定 pin |
| `test_backoff_policy_performance_analysis.py:203` | B | 同系列の source fixture |
| `test_backoff_policy_performance_analysis.py:305` | B | 同系列の document fixture |
| `test_backoff_policy_performance_analysis.py:806` | B | fixture 内の pin 不一致変異 |
| `test_backoff_policy_performance_analysis.py:860` | B | fixture 内の pin 不一致変異 |
| `test_backoff_profile_pegasus.py:47` | B | 旧 profile receipt fixture |
| `test_backoff_requested_us.py:589` | B | source とその複製 reference の比較。現行 pin と照合しない |
| `test_dynamic_backoff_transitions.py:17` | B | 固定旧 source の patch 検査 |
| `test_mocc_proof_surface.py:29` | B | instrumentation 拒否の旧 pin control |
| `test_mocc_proof_surface.py:397` | B | 上記 control の test 名 |
| `test_mocc_proof_surface.py:407` | B | 上記 control の失敗メッセージ |
| `test_mocc_trace_job_contract.py:32` | B | 比較 policy の BASE_OID |
| `test_mocc_trace_pair.py:20` | B | 比較 pair の BASE_OID |
| `test_p3_build_authority_cli.py:196` | A | 実 stock admission と現行 driver pin を独立 literal で拘束 |
| `test_p3_s4_loop_job_contract.py:1184` | B | 模擬 repo の Git 応答 |
| `test_p3_s4_loop_job_contract.py:1243` | B | 同じ模擬 repo の Python 応答 |
| `test_p3_s4_loop_sort.py:781` | A | 実 default config と `S.PIN` の一致 |
| `test_p3_s4_loop_trigger_gating.py:2170` | A | 実 default config と `T.PIN` の一致 |
| `test_paper_story_a1_job_contract.py:463` | B | A-1 旧 canonical pin の checkout fixture |
| `test_paper_story_a1_job_contract.py:471` | B | 同 fixture の HEAD 確認 |
| `test_paper_story_a1_paired.py:1632` | B | A-1 v3 登録契約の canonical pin |
| `test_paper_story_a2_certification.py:1023` | B | 既存 A6 取得記録 fixture |
| `test_paper_story_a2_certification.py:1077` | B | 同 fixture の読取り期待値 |
| `test_paper_story_a2_certification.py:3820` | B | full/short 正規化用の合成 pin |
| `test_paper_story_a2_certification.py:3827` | B | 同 cohort の short pin |
| `test_paper_story_a2_certification.py:3830` | B | 正規化結果の独立期待値 |
| `test_plot_a2_certification.py:123` | B | plot 用旧 source fixture |
| `test_plot_a2_certification.py:127` | B | 同 cell fixture |
| `test_plot_a2_certification.py:148` | B | 同 certification fixture |
| `test_plot_a2_certification.py:179` | B | 同 manifest fixture |
| `test_plot_a2_certification.py:228` | B | 同 source evidence fixture |
| `test_plot_a2_certification.py:327` | B | 同 manifest fixture |
| `test_plot_a2_certification.py:1464` | B | fixture の provenance 表示期待値 |
| `test_plot_a2_certification.py:1509` | B | fixture の provenance 表示期待値 |
| `test_plot_b10_static_tail_formal.py:72` | B | 旧 report の admission fixture |
| `test_plot_dynamic_backoff.py:38` | B | 旧 plot 系列の short pin |
| `test_plot_dynamic_backoff.py:39` | B | 同 full pin |
| `test_plot_t2187_adaptive_consts.py:120` | B | 旧 probe document fixture |
| `test_plot_t2187_adaptive_consts.py:121` | B | 同 fixture の HEAD |
| `test_s6_sort_sweep.py:390` | A | 公開 sweep が現行 pin を pipeline に渡すことを拘束 |
| `test_s8a_trigger_sweep.py:108` | A | 現行 sweep が消費する characterization の pin |
| `test_s8a_trigger_sweep.py:485` | A | 公開 sweep が現行 pin を pipeline に渡すことを拘束 |
| `test_s8b_floor_campaign.py:2276` | B | `_git_stdout` を mock した hold/release control |
| `test_s8b_floor_campaign.py:12253` | B | 旧凍結 protocol の filename |
| `test_s8b_protocol_builder.py:55` | B | 旧凍結 protocol の canonical bytes |
| `test_t126_qualification_driver.py:785` | A | source evidence が実 `build_admission.CURRENT_PIN` 比較に届き、STOCK_BASELINE を要求 |
| `test_t1998_stock_inline_pair.py:54` | B | 固定旧比較系列の short gitlink |
| `test_t1998_stock_inline_pair.py:55` | B | 同 full gitlink |
| `test_t2187_adaptive_const_probe.py:47` | B | 固定旧 source の probe fixture |

consumer 33 file のうち、上表と重複しない 25 file も確認しました。「記号参照のみ」は今回の旧 pin literal 集合との対比を指します。

| file | 判定 |
|---|---|
| `commit_receipt_support.py` | 記号参照のみ、変更不要 |
| `growth_test_holds.py` | 記号参照のみ、変更不要（説明文字列） |
| `test_artifact_admission.py` | 記号参照のみ、変更不要 |
| `test_autonomous_trial_completeness.py` | 記号参照のみ、変更不要 |
| `test_b10_backoff_static_tail_formal.py` | 記号参照のみ、変更不要 |
| `test_backoff_extended_sweep.py` | 記号参照のみ、変更不要（模擬 pin 注入） |
| `test_bench_first_real_wal.py` | 記号参照のみ、変更不要 |
| `test_build_admission.py` | 記号参照のみ、変更不要 |
| `test_build_site_gate.py` | 記号参照のみ、変更不要 |
| `test_buildcache_v2.py` | 記号参照のみ、変更不要 |
| `test_campaign.py` | 記号参照のみ、変更不要。歴史 golden の `KICKOFF_PIN_FULL` も保持 |
| `test_check_docs.py` | 記号参照のみ、変更不要（模擬 `pin.py`） |
| `test_critic.py` | 記号参照のみ、変更不要 |
| `test_growth_test_holds_contract.py` | 記号参照のみ、変更不要（説明文字列） |
| `test_guided.py` | 記号参照のみ、変更不要 |
| `test_hold_inventory.py` | 記号参照のみ、変更不要（説明文字列） |
| `test_layer3_report.py` | 記号参照のみ、変更不要 |
| `test_mocc_template_proof.py` | 記号参照のみ、変更不要 |
| `test_paper_story_a2_job_contract.py` | 記号参照のみ、変更不要 |
| `test_s1_measurement_freeze.py` | 記号参照のみ、変更不要 |
| `test_s8b_approved.py` | 記号参照のみ、変更不要。実 gitlink と照合 |
| `test_s8b_prediction_runner.py` | 記号参照のみ、変更不要 |
| `test_t126_qualification_artifacts.py` | 記号参照のみ、変更不要 |
| `test_t1286_commit_receipt.py` | 記号参照のみ、変更不要 |
| `test_verifier.py` | 記号参照のみ、変更不要 |

## 実走結果

成功した確認：

- `git ls-tree HEAD external/ccbench`：候補 full SHA と一致。
- `git -C external/ccbench rev-parse HEAD`：同じ候補 full SHA。
- pin 整合確認：rc=0。出力：

```text
e9e477c e9e477ca1b55348ab4530de0b1cf663ce4555290
```

- probe の `bash -n`、`python3 -m py_compile`：rc=0。
- `git diff --check`：rc=0。
- A の test 差分が literal 置換だけ、B の file が byte 不変：確認成功。

**pytest 実走済み node は 0 件です。** `test_s8b_approved.py` と群 A の全 6 file を一括指定しましたが、collection 前に拒否されました。全 7 file が未実走です。

主要な未実走 node：

| file | node |
|---|---|
| `test_s8b_approved.py` | `test_ccbench_full_sha_is_40hex_and_current_pin_is_prefix` |
| `test_s8b_approved.py` | `test_ccbench_full_sha_matches_real_gitlink` |
| `test_p3_s4_loop_sort.py` | `test_default_cfg_axis_is_sort_marker` |
| `test_p3_s4_loop_trigger_gating.py` | `test_default_cfg_wires_s2_verify_and_axis` |
| `test_s6_sort_sweep.py` | `test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes` |
| `test_s8a_trigger_sweep.py` | `test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes` |
| `test_p3_build_authority_cli.py` | `test_stock_machine_and_opted_in_coder_paths_remain_accepted` |
| `test_p3_build_authority_cli.py` | `test_authorityless_trigger_coder_is_rejected_before_build_spy` |
| `test_t126_qualification_driver.py` | `test_qualification_stock_source_reaches_build_with_exact_class` |

`_EXPECTED_REPO_STOCK_PIN` を使う MUT-2 killer 候補は上表の authority CLI 2 node です。変異検証は未実走です。

## probe の説明

追加先は `tools/dev-wave-probe/` です。**両 probe の本体は実行していません。**

| file | 引数・出力 |
|---|---|
| `t2304_shape_probe_job.sh` | `<login\|compute> <configure\|build>`。ログは `$J/shape-probe/$tag.out`、終了 rc は `$tag.done` |
| `t2304_masstree_shape_probe.py` | `<repo_root> <build_dir> <out_json>`。schema は `t2304-shape-probe/v1` |

shell は候補 HEAD 不一致を rc=13 で拒否し、実 checkout を `cp -a` で snapshot 化します。base-only FetchContent、指定 compiler・prefix・disconnected 引数で configure します。build mode は TRACE=0/1 の `ycsb_mocc.exe` をそれぞれ `-j "$(nproc)"` で build し、rc と実体を記録します。

Python は指定の本番 check 2 本を順に呼び、成否、返り値、例外型・文・cause 連鎖を JSON に残します。cache の該当全行、pairs block の逐語、両 file の SHA-256 も記録します。両 check 成功で rc=0、失敗なら rc=3 です。

T-1997 雛形からの主な変更は、引数による実行面の分離、候補 HEAD の強制照合、mocc の TRACE=0/1 build、disconnected check の追加、JSON 出力、EXIT trap による終了記録です。

## 波及

- `build_admission.py:674–676`：stock token・tracked clean に加えて、新 `CURRENT_PIN` と一致する source だけが STOCK_BASELINE になります。
- `paper_story_a2_certification.py:3694–3696`：現行 canonical short pin の照合が新値へ移ります。
- `s1_measurement_freeze.py:437`：hold 解除時の recorded/current pin 照合が新値へ移ります。hold 中は既存の held marker 経路です。
- `tools/pegasus/paper_story_a2_certification.sh:306,307` と `submit_paper_story_a2_certification.sh:213` の `^[0-9a-f]{7}$` に新値は適合します。
- floor の指定説明には訂正があります。現行 `s8b_floor_campaign.py:1296` は **builder の実 gitlink と承認定数の一致検査**であり、更新後は新 gitlink を受理します。旧凍結 protocol をこの行が直接拒否するわけではありません。歴史 protocol の検証と現行実行への適格性は別で、旧 bytes は保持しました。⑤の新系列は未着手です。

## 未了・懸念

親に残る作業は pytest・受入・変異検証、probe の job dir への退避と実走、その結果による buildcache docstring 更新、docs 更新、gitlink と定数の同一 commit 化です。clang 14 の比較未完了は既承認の限界として残します。

自動実行審査（PreToolUse `guard_bash`）が pytest コマンドを拒否しました。理由は「Pegasus ログインノードでは pytest を直接実行できないため、計算ノードを使うこと」です。迂回していません。

## 総括

pin 更新、A 7 行の追随、B 46 行の保持、probe 2 本の作成を完了しました。静的確認と構文検査は成功しています。pytest と生成物形の実測は未実走であり、テスト合格は主張しません。