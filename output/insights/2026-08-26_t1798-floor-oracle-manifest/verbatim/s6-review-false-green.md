### 所見 1: production 系列は floor 経路を通らず、必須 3 変異すべてで系列自身は緑のまま
- 深刻度: must-fix
- 偽緑の経路: (a) floor が oracle へ `source_root` を渡す、(b) floor の post-oracle capability から canonical root を落とす、(c) cache-hit 固有の二根再検査を削除する、のどれでも対象系列は緑のまま。oracle root と capability をテスト自身が直接組み立て、hit 前後に drift も入れていない。
- 根拠: `orchestrator/tests/test_buildcache_v2.py:480-530`, `orchestrator/campaign/s8b_floor_campaign.py:4141-4153`, `orchestrator/campaign/s8b_floor_campaign.py:4218-4235`, `orchestrator/campaign/buildcache.py:2244-2267`
- 成果物影響: certified 選択が oracle と別 root の binary や二根未再検査の cache hit を受理し、材料レポートの canonical 参照と試行台帳の miss/hit 記録が同じ因果系列を表さなくなる。
- 提案: `build_cells` の canonical 生成、実 `prepare_cell` の oracle 呼出し、`_post_oracle_dependency_binding`、exact `build_v2` までを一続きに通し、hit 中 drift を注入する系列へ置き換える。

補足すると、各変異を別々に捕まえるテストは存在する。(a) は `test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle`、(b) は literal capability と旧 5-key 拒否、(c) は cache-hit drift テストが赤になる。しかし裁定は「同じ production 系列テスト自身が 3 変異で赤」を要求しており、その条件は満たしていない。

### 所見 2: floor の prebuild から canonical 生成への接続は一度も実 production 実装で試されない
- 深刻度: must-fix
- 偽緑の経路: `_materialize_floor_oracle_dependency` を binding の素通しにする、または `_prepare_floor_oracle_dependency` からその呼出しを除いても、generator テストと系列テストは materializer を直接呼び、floor テストは adapter または prepare 全体を monkeypatch するため緑になり得る。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:3107-3173`, `orchestrator/campaign/s8b_floor_campaign.py:3293-3298`, `orchestrator/tests/test_s8b_floor_campaign.py:2845-2859`, `orchestrator/tests/test_s8b_floor_campaign.py:2947-2961`, `orchestrator/tests/test_buildcache_v2.py:473-476`
- 成果物影響: fresh floor が canonical material を生成せず停止して試行台帳を欠落させるか、誤った root を補った mutant では certified 選択と材料レポートへ未検証 root が入る。
- 提案: prebuild 自体は合成してよいが、`_prepare_floor_oracle_dependency` から production adapter と material sink までを置換せず通す正例を追加する。

### 所見 3: 系列の合成 VCS root は production Git 前提を満たさず、固定 state で検査を迂回している
- 深刻度: must-fix
- 偽緑の経路: production の `_probe_git_source`、Git subprocess、HEAD/top-level/tracked 再観測を壊しても、対象系列は `_GitSourceState` を返す monkeypatch で緑のまま。
- 根拠: `orchestrator/tests/test_buildcache_v2.py:456-472`, `orchestrator/campaign/sort_swo_dependency_material.py:101-123`, `orchestrator/campaign/sort_swo_dependency_material.py:167-211`, `orchestrator/campaign/sort_swo_dependency_material.py:352-386`
- 成果物影響: 材料レポートが「実 source の HEAD と tracked 集合から導出した」と記録しても、その出所を検査しない root が certified 選択の受理材料になり得る。
- 提案: pinned commit object と index を持つ実 checkout を使うか、production Git probe を通す独立な正例と系列を結合する。

fix 子の「VCS repository として初期化し、期待 HEAD を設定」は production 前提の再現ではない。`git init` 後に `.git/HEAD` へ pinned hash を直接書いただけで、その commit object を作っておらず、tracked file を `git add` していない。この root が満たさない条件は次のとおり。

- `git rev-parse --verify HEAD` で実在 commit を一意に取得できること。
- `git ls-files --cached -z` が非空の tracked 99 path を返すこと。
- tracked 集合を Git index から導出すること。
- materialize 前後と build 境界で HEAD、top-level、tracked 集合を再観測すること。
- floor の policy pin、tracked-clean、toolchain manifest、source inode、captured policy pins の検査を通ること。
- `config.h` と archive が production prebuild recipe により生成されたこと。ここでは config は fixture copy、archive は任意文字列である。

canonical non-symlink directory、regular `config.h`、`<base>/masstree-src` という path 形だけは満たしている。

### 所見 4: 実 root opt-in は generator だけであり、skip により実 root の全系列は未証明
- 深刻度: must-fix
- 偽緑の経路: `IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` が無ければ production materializer を呼ぶ前に skip する。残る系列は Git probe を固定値化し、実 configure/build を `_fake_build_environment` で置換するため、実 prebuilt root からの build miss/hit が空でも全体結果は 1 skipped と多数 passed になる。
- 根拠: `orchestrator/tests/test_sort_swo_dependency_material.py:238-260`, `orchestrator/tests/test_buildcache_v2.py:215-293`, `orchestrator/tests/test_buildcache_v2.py:509-530`, `s4-ruling.md:132-144`
- 成果物影響: certified 選択、材料レポート、試行台帳のいずれにも、実 prebuilt rootから oracle PASS、実 build、cache hit まで通った根拠を付けられない。
- 提案: opt-in node を generator で終わらせず oracle PASSと post-oracle `build_v2` miss/hitまで延長し、裁定どおり親が 1 回成功実測する。

親の既存実測は実 rootから oracle PASSまでであり、実装後の post-oracle build miss/hitは示していない。したがって残りのテストだけで「production 系列が通る」とは言えない。

### 所見 5: manifest 変異テストは production generator を一度も変異させていない
- 深刻度: nit
- 偽緑の経路: `sort_swo_dependency_material` 全体を no-op にしても、fixture の `SHA256SUMS` を直接編集して既存 oracle verifierを呼ぶ M01-M03 テストは期待どおり赤を観測できる。
- 根拠: `orchestrator/tests/test_sort_swo_dependency_material.py:211-235`
- 成果物影響: 他の generator 正例が pinned manifest を検査するため、単独では certified 選択、材料レポート、試行台帳の受理集合を変えない。
- 提案: 変異を fixture 出力ではなく production generator の宣言集合、区切り、並び順へ照準する。

### 所見 6: phase marker に追加した canonical 参照は assert されていない
- 深刻度: nit
- 偽緑の経路: `_write_phase_marker` から `oracle_dependency_root` と `dependency_manifest_sha256` の追加を削除しても、変更された marker テストは config、toolchain、archive だけを検査して緑のまま。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:3393-3399`, `orchestrator/tests/test_s8b_floor_campaign.py:4797-4834`, `orchestrator/tests/test_s8b_floor_campaign.py:4837-4846`
- 成果物影響: certified 選択、材料レポート、試行台帳の値は直接変わらず、private phase marker の診断参照だけが欠落する。
- 提案: なし

### production 系列テストの判定 (本物か、迂回か)

判定は「部分的に本物だが、裁定上は迂回」である。

本当に通っているもの:

- production `materialize_canonical_dependency` の copy、manifest生成、既存 oracle pin検証。
- production `resolve_oracle_environment`。
- production `check_materialized_sort_swo` の compileとexecute。
- production `build_v2` の cache制御、二根検査呼出し、missとhitの判定。

迂回しているもの:

- floor の prebuild、canonical adapter、oracle root配線。
- floor の post-oracle capability生成。
- production Git probeと前後の Git state再観測。
- production CMake configureとycsb build。
- production site、ccbench commit、source evidence、trace diff、trace symbol検査。
- cache-hit固有二根検査の検出力。driftを入れていないため削除しても緑。

3変異の静的判定は、(a) 緑、(b) 緑、(c) 緑である。別テストを合算すれば各変異は検出されるが、「同一実行で production 全系列」という裁定条件は満たさない。

### 実装を no-op にしても緑のままのテスト一覧

- `_probe_git_source` を no-opまたは固定値化しても緑:
  - `test_materialize_uses_rule_derived_inventory_and_generated_pin`
  - `test_materialize_manifest_mismatch_has_fixed_reason_and_bounded_hashes`
  - `test_source_symlink_is_not_copied`
  - `test_two_root_verifier_rejects_live_tracked_byte_drift`
  - `test_manifest_line_builder_matches_pinned_fixture_exactly`
  - production 系列テスト

- `_run_git` の subprocess実装を壊しても緑:
  - `test_empty_tracked_list_is_rejected_instead_of_becoming_empty_inventory`

- 新設 material module全体を no-opにしても独立に緑:
  - `test_manifest_mutations_have_one_exact_verifier_reason`

- real-root環境変数未設定時に material実装全体を実行しない:
  - `test_real_prebuilt_masstree_material_is_pinned_when_explicitly_configured`

- floor canonical adapterまたはその接続を no-opにしても緑:
  - `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once`
  - `test_floor_dependency_prebuild_captures_shared_policy_pins_once`
  - production 系列テスト
  - canonical準備を monkeypatchする変更済み `build_cells` 系テスト群

- 新しい canonical postflight を no-opにしても旧 gateで緑または意図した赤:
  - `test_floor_strict_postflight_rejects_run_local_dependency_replacement`
  - `test_floor_postflight_staged_source_set_and_expected_hash_are_enforced`
  - `test_build_cells_production_postflight_rejects_dependency_drift`

- manifest mismatch の production変換を no-opにしても緑:
  - `test_floor_canonical_manifest_diagnostic_records_both_hashes_only`
  - data classの直列化しか呼んでおらず、materializer例外からの変換を通さない。

一方、次は対応する production gateを実際に守っており、対象 no-opでは緑にならない。

- `test_post_oracle_binding_requires_receipt_to_match_canonical_and_source`
- `test_v2_post_oracle_rejects_legacy_five_key_capability`
- `test_v2_post_oracle_cache_hit_rechecks_two_roots_before_return`
- 変更された canonical manifest、tracked byte、config drift拒否の3テスト
- `test_tracked_path_normalization_is_fail_closed`

### 親の疑義 A1 への判定

疑義A1は refuted と判定する。既定値変更は、共有 PASS attempt の既存値と新設された `_post_oracle_dependency_binding` の config一致検査を整合させる変更である。共有 PASS attempt側は以前から同じ hashを持つ。

根拠は `orchestrator/tests/s8b_floor_evidence_fixture.py:35-56`、`orchestrator/tests/test_s8b_floor_campaign.py:328-333`、`orchestrator/campaign/s8b_floor_campaign.py:2191-2216`。

値へ依存するテストは次の群である。

- capabilityとfloor配線:
  - `test_post_oracle_binding_requires_receipt_to_match_canonical_and_source`
  - `test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle`
  - `test_dependency_bound_sort_best_rejects_nonexact_builder_before_call`
  - `test_dependency_bound_sort_best_default_builder_receives_literal_capability`
  - `test_production_floor_preflight_marker_precedes_toolchain_and_dependency_probes`
  - `test_production_floor_prebuilds_one_shared_dependency_and_injects_only_sort`

- prebuild:
  - `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once`
  - `test_floor_dependency_prebuild_captures_shared_policy_pins_once`

- postflight:
  - `test_floor_postflight_gate_rejects_source_override_and_accepts_base_only`
  - `test_floor_strict_postflight_rejects_captured_payload_pin_mixture`
  - `test_floor_postflight_staged_source_set_and_expected_hash_are_enforced`
  - `test_floor_postflight_cache_hit_uses_content_receipt_not_prior_absolute_root`
  - `test_floor_postflight_gate_rejects_effective_root_and_content_drift`
  - `test_floor_postflight_gate_classifies_head_drift`
  - `test_floor_postflight_rejects_build_result_toolchain_mismatch`
  - `test_floor_postflight_rejects_binding_toolchain_hash_only_mismatch`
  - `test_build_cells_production_postflight_rejects_dependency_drift`

- failure記録とmarker:
  - `test_floor_postflight_failure_persists_unavailable_before_binary_admission`
  - `test_sort_best_build_failure_persists_bounded_exception_diagnostic`
  - `test_phase_marker_is_create_only_fsynced_private_and_carries_dependency_hash`
  - `test_floor_phase_marker_carries_run_local_archive_sha256`

意味が変わったのは成功系で、以前の相互に無関係な任意値から「共有 PASS receiptとbindingが一致する正例」になった。これは骨抜きではなく、新しい一致禁止を通すための正規化である。`0`、`d`、旧 `"b"*64` との不一致は新 hashでも維持されている。既存契約が literal `"b"*64` を要求する3箇所は明示的な `dataclasses.replace` で保存されており、一貫している。

### 自走 harness と meta-test

`test_sort_swo_dependency_material.py:263-264` に `pytest.main([__file__])` を呼ぶ `__main__` harnessがある。

allowlistには登録されておらず、これは正しい。`test_plain_runner_coverage.py:44-70` はdirectory内の全 `test_*.py` を列挙し、`pytest.main` signalを検出する。さらに同fileの77-86行は、自走可能fileがallowlistへ残ることを拒否する。したがってこのmeta-testは新設fileを実際に読んでいる。

`test_pytest_collection_config.py` は新設fileを個別には見ていない。実 repoに対して明示収集するのは既存 `test_sort_swo_oracle.py` であり、新設名をassertしていない。`pytest.ini` の `testpaths=orchestrator/tests` は新設fileを通常収集範囲へ入れるが、このmeta-test 147 passed自体は新設file収集の証明ではない。

## 総括

裁定が必須化した「同一実行の production 全系列」は未成立である。系列内の canonical生成と実 oracle PASS、buildcache miss/hitは実体がある一方、最重要のfloor接続、capability生成、real Git state、cache-hit変異、実buildを迂回している。特に要求された3変異は系列自身では全て緑のままである。

共有config fixtureの疑義A1、自走harness、plain-runner allowlist関係は問題なし。親が確認した1 skippedは、実 rootからpost-oracle build miss/hitまでの未証明を隠している。