## 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| Review A: 既存テストの期待値変更 | closed | `test_b4_fixture_main_rejects_run_one_iteration_bypass_m13` は元の `B4ProtocolError / "fixture run_one_iteration"` に復元された。`orchestrator/tests/test_p3_s4_loop.py:3093-3103`。G7 に伴う旧 CLI 3 件の置換は親受理どおり。 |
| Review A: G1 の test-only 受理 | 受理・未閉鎖 | `require_any_context` は test seal を引き続き受理する。`orchestrator/campaign/p3_b4_launcher.py:260-287`。base の G1 使用例は `p3_s4_loop.py:906-913`。A1 の裁定どおりであり、closed ではない。 |
| Review A: caller 鋳造可能 context / campaign 束縛 | partial | driver・campaign id・arm の exact 検査は `p3_b4_launcher.py:289-319` で閉じた。一方 production seal は公開関数の closure から取得でき、`_new_context` と組み合わせて verifier なしで鋳造できるため、鋳造部分は再発している。`p3_b4_launcher.py:95-117,232-287,582-589`。 |
| Review A: WAL 分類の fail-open / 定数複製 | closed | lock 不在だけ `None`、既存 lock の I/O・UTF-8・codec・形状不正は authorization 拒否となる。`orchestrator/campaign/wal.py:416-483`。識別語は `p3_b4_protocol.py:6-7` から import される。 |
| Review A: M08〜M16 の副作用帰属 | partial | M08〜M10 は権威 layout と iteration spy に修正済み。`test_p3_s4_loop.py:2565-2606`、sort `:960-998`、trigger `:2820-2863`。M11〜M16 は後述のとおり別の拒否層が残る。 |
| Review A: golden identity | closed | protocol 値は同一で、context は config に保存されない。`p3_b4_protocol.py:6-7`、`ident.py:150-189`。17 pin の変更はない。 |
| Review A: 既存 6 拒否 | closed | 6 分岐は `p3_s4_loop.py:1234-1273` に残り、直接検査と production-context 経由検査の双方がある。`test_p3_s4_loop.py:2609-2776`。 |
| Review A: G7〜G10 | closed | G7 hard-fail `p3_b4_closed_critic.py:1991-2000`、G8 registry `p3_b4_launcher.py:176-180`、G9 verifier-first `:321-338,478-518`、G10 共通 projection entry `p3_b4_closed_critic.py:638-642`。 |
| Review B: production 封印の無検証鋳造 | regressed | 旧 issuer 名は消えたが、`require_b4_any_context.__closure__` が `production_seal` を直接保持する。取得した seal と module 属性 `_new_context` で架空 hash の production context が `require_b4_production_context` を通ることを read-only probe で確認した。 |
| Review B: M08〜M10 の恒真な副作用 oracle | closed | G3 を外すと layout 作成後に state `iteration == 1` が wrapper へ渡り、後段 G2 で止まる。root 不在と spy 未到達の両 assertion が赤になる。`p3_s4_loop.py:1521-1547` と上記 3 test。 |
| Review B: 既存回帰テストの赤 | closed | 期待値は復元済み。親の焦点実測は現在 564 passed / 0 failed。これは親の実測引用であり、本レビューでは pytest 未実走。 |
| Review B: COMMIT 後の lock 再分類 | 受理・未閉鎖 | G4 は COMMIT 時の lock だけを分類する。`wal.py:493-505`。A2 の scope 外裁定どおりで、closed ではない。 |
| Review B: 発火しない入力と定数複製 | partial | G1 test seal は A1 として受理・未閉鎖。campaign/arm/driver exact 検査と定数共有は closed。`p3_b4_launcher.py:289-319`、`p3_b4_protocol.py:6-22`、`wal.py:463-505`。 |
| Review B / F7: 正例の実体主張 | closed | docstring は全差し替え対象を列挙し、routing のみを証明すると限定している。実 factory、driver main、WAL は未差替え。`test_p3_b4_closed_critic.py:2358-2374,2462-2499`。 |

## fix が作った新しい穴

有り。

### production seal の closure 漏出

`p3_b4_launcher` の全 module 属性は次のとおりだった。

- メタ属性: `__builtins__`, `__cached__`, `__doc__`, `__file__`, `__loader__`, `__name__`, `__package__`, `__spec__`
- 型・import: `Any`, `Arm`, `CampaignLayout`, `DriverKind`, `Iterator`, `Literal`, `Path`, `annotations`, `argparse`, `contextlib`, `contextvars`, `dataclass`, `exploration_campaign_layout`, `hashlib`, `ident`, `json`, `os`, `p3_b4_closed_critic`, `p3_s4_loop`, `p3_s4_loop_sort`, `p3_s4_loop_trigger_gating`, `replace`, `sys`, `verify_b4_admission_record`
- 定義/API: `B4LaunchContext`, `B4LauncherAuthorizationError`, `B4_LAUNCH_SIDECAR`, `B4_LAUNCH_SIDECAR_SCHEMA`, `DRIVER_REGISTRY`, `_B4_TEST_CONTEXT_SEAL`, `_canonical_json_bytes`, `_context_sha256`, `_context_value`, `_driver_argv`, `_driver_configs`, `_new_context`, `_validate_context_shape`, `create_b4_launch_context_for_test`, `launch_bootstrap`, `launch_continuation`, `main`, `require_b4_any_context`, `require_b4_production_context`, `verify_b4_launch_context`

旧 issuer 名は存在しない。しかし次の経路が残る。

1. `require_b4_any_context` は `production_seal` を直接 closure capture する。`p3_b4_launcher.py:260-278,582-589`。
2. `require_b4_any_context.__closure__` から seal を取得できる。
3. module 属性 `_new_context` は任意 seal・任意 admission hash・任意 campaign id を受ける。`:95-117`。
4. 生成値は `require_b4_production_context` を通る。`:289-319`。
5. issuer 自体も `launch_bootstrap.__closure__ → prepare_launch.__closure__ → issue_context` で到達可能。`:478-518`。

したがって別名や `partial` は無いが、closure 戻り値経路から issuer と seal の双方が漏れている。`test_production_issuer_and_activation_are_not_module_attributes` は旧 7 名の不在しか調べず、この経路でも通るため実効的な F1 oracle になっていない。`test_p3_b4_launcher.py:265-276`。

### 識別語と golden 17 件

値の変更は認めない。

- 定数は旧値と同一の `"b4_protocol"` / `"p3-b4-reflux-ablation/v1"`。`p3_b4_protocol.py:6-7`。
- 3 driver は同じ値を marker branchへ追加するだけ。base `p3_s4_loop.py:903-925`、sort `p3_s4_loop_sort.py:269-296`、trigger `p3_s4_loop_trigger_gating.py:564-590`。
- identity は `search_config` を正準 JSON 化し SHA-256 先頭 8 hex を使う。`ident.py:150-189`。
- 通常 base 2、sort 1、trigger の歴史 pin 8、marker on/off 6 の計17件は変更なし。marker 6件は `test_p3_b4_closed_critic.py:2760-2814`、trigger pin 8件は `test_p3_s4_loop_trigger_gating.py:128-150`。
- read-only probe でも base `2cd75697/9f43a5b8`、sort `081dd46f`、marker 6件 `ad0444da/8700ee8e/2c241821/df423528/2adb6cf7/6328b84a` を確認した。pytest 実走ではない。

protocol module が projection closure に入ったため admission projection hash は変わるが、campaign identity の byte 変更ではない。`p3_b4_closed_critic.py:638-642`。

### marker 不在の通常 campaign

余計な G4 実行経路はない。lock 不在なら `wal.py:418-419` で即 `None`、`_has_exact_b4_protocol_marker(None)` は false となり、G4 本体 `:496-505` は 1 行も実行されない。valid な unmarked lock でも同じ分岐になる。既存だが壊れた lock の拒否だけは F4 の明示指示どおりである。

### 既存テストの期待値

fix 2 回の全 hunk では、既存期待値の緩和、skip、xfail、test 削除はない。

- 赤だった fixture 期待値は元へ復元。
- M08〜M10 は恒真だった state-file 不在を削り、実 iteration wrapper の観測へ置換。
- M12/M13 の例外 match は維持。
- fix2 は `_production_launch_context` の campaign-id assertion を `test_p3_b4_closed_critic.py:128-134` に残し、入力だけを `_marked_driver_configs` `:158-163` へ変更している。

ただし新しい弱い oracle がある。`test_all_drivers_and_wal_import_the_protocol_constants` は文字列 object identity の `is` を使う。`"b4_protocol"` は別 module の同じ literal でも intern により `is` が成立し得るため、key だけを再複製する変異を殺せない。`test_p3_b4_launcher.py:410-414`。

## 変異 18 件の帰属判定

| 変異 | 期待して落ちる nodeid | 静的判定 |
|---|---|---|
| M01 | `test_p3_s4_loop.py::test_m01_b4_default_cfg_rejects_unsealed_marker_creation` | 単独帰属する。G1 を外すと cfg が返り `pytest.raises` が不成立。`test_p3_s4_loop.py:2523-2529`。 |
| M02 | `test_p3_s4_loop_sort.py::test_m02_b4_sort_default_cfg_rejects_unsealed_marker_creation` | 単独帰属する。`test_p3_s4_loop_sort.py:924-930`。 |
| M03 | `test_p3_s4_loop_trigger_gating.py::test_m03_b4_trigger_default_cfg_rejects_unsealed_marker_creation` | 単独帰属する。`test_p3_s4_loop_trigger_gating.py:2746-2752`。 |
| M04 | `test_p3_s4_loop.py::test_m04_b4_marked_run_one_iteration_direct_call_requires_launcher` | 単独帰属する。G2 を外すと `layout.ensure()` `p3_s4_loop.py:1148` に到達し root 不在 assertion が落ちる。 |
| M05 | `test_p3_s4_loop_sort.py::test_m05_b4_sort_run_one_iteration_direct_call_requires_launcher` | 単独帰属する。G2 後の `layout.ensure()` は `p3_s4_loop_sort.py:351`。 |
| M06 | `test_p3_s4_loop_trigger_gating.py::test_m06_b4_trigger_resolved_iteration_requires_launcher` | 単独帰属する。resolved G2 後の `layout.ensure()` は `p3_s4_loop_trigger_gating.py:742`。 |
| M07 | `test_p3_s4_loop_trigger_gating.py::test_m07_b4_trigger_public_iteration_requires_launcher` | 単独帰属する。G2 を外すと `_current_site` spy `:846` に到達する。 |
| M08 | `test_p3_s4_loop.py::test_m08_b4_drive_iteration_rejects_before_layout_and_state_progress` | 単独帰属する。G3 を外すと root 作成、iteration 1、wrapper 到達後に G2 が拒否する。`test_p3_s4_loop.py:2565-2606`。恒真ではない。 |
| M09 | `test_p3_s4_loop_sort.py::test_m09_b4_sort_drive_rejects_before_layout_and_state_progress` | 単独帰属する。共有 resolver を権威 layout に揃え、iteration 1 を観測する。`:960-998`。 |
| M10 | `test_p3_s4_loop_trigger_gating.py::test_m10_b4_trigger_drive_rejects_before_layout_and_state_progress` | 単独帰属する。T/L 両 resolver を同じ layout にしている。`:2820-2863`。 |
| M11 | `test_p3_b4_launcher.py::test_m11_real_wal_commit_requires_launch_sidecar` | 単独帰属しない。入力には active production context がなく、sidecar 実在検査を外しても `p3_b4_launcher.py:460-470` が拒否する。 |
| M12 | `test_p3_b4_launcher.py::test_m12_real_wal_commit_rejects_sidecar_for_another_campaign` | 単独帰属しない。campaign-id 専用検査を外しても、全 sidecar equality `p3_b4_launcher.py:472-475` が同じ改変を拒否する。 |
| M13 | `test_p3_b4_launcher.py::test_m13_real_wal_commit_rejects_sidecar_for_other_live_context` | 単独帰属しない。G4 context equality を外した後も commit receipt 不在で `wal.py:535-546` が拒否する。空 WAL の副作用は出るが COMMIT には到達しない。 |
| M14 | `test_p3_b4_launcher.py::test_m14_real_production_pair_factory_requires_launch_context` | 単独帰属しない。G5 を外すと missing admission path が `p3_b4_closed_critic.py:1234-1238` で拒否され、artifact 不在は不変。 |
| M15 | `test_p3_b4_launcher.py::test_m15_real_production_pair_factory_rejects_cross_driver_context` | 単独帰属しない。driver 比較を外しても sort context の campaign id が base cfg と異なり、`p3_b4_launcher.py:303-310` が拒否する。その後の admission も missing。 |
| M16 | `test_p3_b4_launcher.py::test_m16_test_seal_cannot_be_promoted_by_evidence_class` | 単独帰属しない。test-only 専用分岐 `:247-250` を外しても generic production-seal 分岐 `:251-257` が拒否し、さらに admission も missing。 |
| M17 | `test_p3_b4_launcher.py::test_m17_real_legacy_cli_hard_fails_before_factory` | 境界には単独帰属するが nodeid は独占しない。同じ G7 を `test_r7_a10_thin_cli...` と `test_closed_critic_cli_constructs_only...` も固定する。実装の前後に別拒否層はない。 |
| M18 | `test_p3_b4_launcher.py::test_m18_driver_registry_uses_real_main_object_identity` | registry identity へ直接帰属する。sort/trigger 変異はこの nodeid、base 変異は正例の `test_launcher_positive...` `:2499` も落とすため、nodeid の独占性だけはない。 |

## 残る must-fix

1. **Production seal の closure 漏出。**  
   成果物影響: verifier を通らない架空 admission hash の production context、sidecar、active contextを再構成でき、bootstrap 経由の certified COMMIT を起動器外から作れる。

2. **M11〜M16 の変異入力が過剰決定されたまま。**  
   成果物影響: sidecar・campaign binding・live context・factory seal の各 guard が退行しても、別 guard または receipt/admission 拒否により WAL/pair artifact 不在が維持され、18変異の帰属証拠を偽陽性で受理できる。

3. **F1 module-attribute testとprotocol-key共有 testの oracle不足。**  
   成果物影響: seal の再露出または marker key の局所複製を検査が通過し、架空 context の受理または将来の marker drift による G4 不発を見逃す。

## 総括

F2〜F7、M08〜M10、golden identity、既存6拒否、通常 campaign の非発火経路は静的には閉じている。  
A1 と A2 は親裁定どおり受理・未閉鎖である。  
最重要の F1 は closure introspection により再発しており、根本原因は閉じていない。  
M11〜M16 も狙った guard 以外の拒否層が残り、18変異すべての単独帰属は成立しない。  
pytest は実走していない。親の実測 564 passed / 0 failed のみを引用した。