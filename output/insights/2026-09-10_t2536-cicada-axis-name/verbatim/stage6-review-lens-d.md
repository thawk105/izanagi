## 既存テストの赤判定

所見 D-1 — **refuted**。commit 後の意味変更で赤になる既存 nodeid は **0 件**。repo 内で cicada の `cmake_defines()` を呼ぶ既存テストはなく、該当呼出しは今回追加された三件だけだった。

固定期待値を確認した nodeid は以下。すべて silo/mocc または fallback で、出力は不変である。

- `orchestrator/tests/test_campaign.py::test_genome_canonical_deterministic` — silo の恒等写像を固定。[test_campaign.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_campaign.py:425)
- `orchestrator/tests/test_campaign.py::test_source_digest_effective_define_adapter_preserves_owner_and_rhs_mapping` — silo の未知軸 `BACKOFF_FIXED` fallback を固定。[test_campaign.py:11550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_campaign.py:11550)
- `orchestrator/tests/test_calibrator_certify.py::test_receipt_genome_derivation_names_mocc_and_preserves_non_axis_define` — mocc と追加 define の復元を固定。[test_calibrator_certify.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_calibrator_certify.py:431)
- `orchestrator/tests/test_calibrator_certify.py::test_cli_certified_attempt_and_published_artifact_record_receipt_genome` — silo receipt の canonical 値を固定。[test_calibrator_certify.py:1338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_calibrator_certify.py:1338)
- `orchestrator/tests/test_buildcache_v2.py::test_v2_generic_build_does_not_enter_post_oracle_protection_or_change_argv` — silo であり、期待側も `cmake_defines()` から導出している。[test_buildcache_v2.py:1449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_buildcache_v2.py:1449)
- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_five_field_cells_preserve_legacy_cell_and_genome_bytes` — silo の補助 define fallback を固定。[test_t2187_adaptive_const_probe.py:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_t2187_adaptive_const_probe.py:1438)
- `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_preserves_real_non_domain_build_inputs` — silo の恒等写像だけ。[test_screening_driver.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_screening_driver.py:601)

s1 goldensも silo 専用で、`canonical()` は不変、編集可能 Python の SHA-256 は形状だけを検査するため赤にならない。該当は `test_s1_known_axes_freeze.py::test_backoff_sweep_grid_matches_registered_golden`、`::test_goldens_helper_is_independent_of_production`、`test_s1_measurement_freeze.py::test_generate_builds_registered_cells_comparisons_and_schedule`。[s1_expected_goldens.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/s1_expected_goldens.py:10)

放置時の成果物影響: 既存期待値の変更は不要であり、変更すれば逆に既存契約を弱める。

## parser 再利用

所見 D-2 — **real**。`parse_options_defaults()` を「宣言済み cache 名一覧」として使うのは誤りである。

同 parser は空値を意図的に除外する。[source_digest.py:865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/source_digest.py:865) 既存テストも `INSERT_READ_DELAY_MS` が辞書に存在しないことを固定している。[test_campaign.py:11183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_campaign.py:11183) したがって新 helper の `cache_name in declared_cache_names` は、宣言の存在ではなく「非空の実効 default」を検査している。[test_pegasus_calibration_workload.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_pegasus_calibration_workload.py:45)

反例は、対応を一切変えずに次だけを行う正当な CCBench 変更である。

```cmake
set(CCBENCH_INLINE_VERSION_OPT_CICADA "" CACHE STRING "cicada")
```

cache 宣言と `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_CICADA}` は維持されるが、parser が名前を落とすため line 63 で偽赤になる。mapping parser の再利用は維持しつつ、宣言名検査を default 値の parser から分離する必要がある。

放置時の成果物影響: 正当な CCBench pin 前進を mapping drift と誤認し、成果物生成を不必要に停止する。

所見 D-3 — **refuted**。裸 option と universal/protocol 合成の現行利用は正しい。

- mocc の `RWLOCK` は裸として `bare_names` に入るが SPACES 軸ではないため、軸ループの `axis not in bare` に誤爆しない。
- `BACK_OFF` は universal 側、残りは protocol OPTIONS 側から取得され、両集合は `_parse_supplied_macro_details()` で合成される。[source_digest.py:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/source_digest.py:840)
- 既存 `test_source_digest_parse_bare_asymmetric_options_and_malformed_scope` と `test_wrong_cache_rhs_rejects_supply_value_mismatch` が裸 option、非対称 RHS、誤 RHS を独立に固定している。

放置時の成果物影響: 空値問題を除けば、現行4 protocol の表に誤分類は生じない。

## 焦点走ファイル集合

所見 D-4 — **real**。直接参照と2段参照から、少なくとも次を焦点走へ含める必要がある。

直接 consumer:

- `test_pegasus_calibration_workload.py`
- `test_campaign.py`
- `test_calibrator_certify.py`
- `test_buildcache_v2.py`
- `test_screening_driver.py`
- `test_condition_meaning_gate.py`
- `test_t2187_adaptive_const_probe.py`

2段 consumer:

- `Genome.cmake_defines()` → `buildcache._v2_commands()` / `buildcache.build()` → `pipeline.evaluate()` から `test_s1_direct_comparison.py`、`test_s1_known_axes_freeze.py`、`test_s1_measurement_freeze.py`
- `screening_driver.evaluate_candidate()` → `backoff_sweep` / `s6_sort_sweep` / `s8a_trigger_sweep` から `test_backoff_sweep.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_screening_opt_in.py`
- s2/s3/s3-mocc/s5 の直接 producer から `test_s5_permutation_coverage.py`、`test_mocc_proof_surface.py`、`test_ccbench_spawn_sites.py`、`test_p3_build_authority_cli.py`
- contract closure から `test_t671_source_binding.py`、`test_p3_b4_raw_record_producer.py`

`buildcache` の実 sink は v2 が [buildcache.py:1922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/buildcache.py:1922)、legacy が [buildcache.py:3139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/buildcache.py:3139)。s1 は module 名検索だけでは拾えず、`s1_direct_comparison → pipeline.evaluate → buildcache` と辿る必要がある。

放置時の成果物影響: helper 経由の argv、s1 freeze、condition gate、contract binding の崩れが受入全走まで潜伏する。

## import と初期化

所見 D-5 — **refuted**。循環、部分初期化、production import cost の問題は認められない。

`model.py` の runtime import は dataclass と typing だけで、`genome.py` を逆 import しない。[model.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/model.py:14) `cli.py` は変更前から `Genome` を同じ module から import 済み、`screening_driver.py` も同様であり、新しい module edge はない。追加表も17要素の literal で I/O はない。新テストの `calibrator.cli` top-level import は collection costを増やすが production 初期化には波及しない。

放置時の成果物影響: production の起動順序や部分初期化には影響しない。

## contract loader と commit 順序

所見 D-6 — **real**。`model.py` は contract loader closure に含まれる。[campaign_lock.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/campaign_lock.py:49) 特に path は line 91 に明記されている。

`capture_contract_loader_binding()` は current HEAD blob と disk bytes の完全一致を要求し、差があれば `contract-loader-drift` になる。[contract_loader_binding.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/contract_loader_binding.py:518) 現在は `model.py` が未 commit なので、順序は次に固定される。

1. 本 wave の4ファイルを同じ commit に入れる。
2. その commit 後に live binding を使う焦点テストを走らせる。
3. 新しい certifying `campaign.lock` は、その commit SHA と新しい `model.py` blob digest を記録してから発行する。

commit 前に走らせると、`test_p3_b4_raw_record_producer.py` の `certified_evidence` 系 nodeid、例えば `::test_m01_assembly_rederives_precursor_from_the_sealed_registry` と `::test_m05_campaign_lock_classification_and_receipt_share_one_byte_buffer` は `_writer_authority()` で赤になる。これは意味変更の回帰ではなく、commit 順序違反による期待された赤である。

放置時の成果物影響: 新規 campaign lock とそれに依存する認証成果物を発行できない。

## scope

所見 D-7 — **real**。新テストの `assert len(GENOME_AXIS_CMAKE_CACHE_VARIABLES) == 17` は、scope 外と裁定された「意図軸集合の独立 pin」の弱い実装になっている。[test_pegasus_calibration_workload.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_pegasus_calibration_workload.py:104)

表と SPACES 由来の CCBench 対応の exact 比較だけで本題は検査できる。固定値17は、SPACES、CCBench、表を同時に正当に拡張しても単独で赤になるため不要かつ裁定外である。

それ以外の scope 外項目は実装されていない。build-cache fingerprint、compile command 証明、cicada の certification whitelist 追加、CMake 制御フロー parser 強化、新規 test file は存在しない。既存の `{silo,mocc,tictoc}` whitelist テストも維持されている。

放置時の成果物影響: 将来の正当な軸追加を本 wave の無関係な固定値が阻止し、裁定外の軸集合管理を持ち込む。

## 総括

- must-fix: `parse_options_defaults()` を cache 宣言一覧として使う偽赤を除去し、空 default の反例を固定する。
- must-fix: scope 外の独立 cardinality pin `len(...) == 17` を外す。
- must-fix: `model.py` を含む commit を先に作り、その commit 後に live-binding 系焦点走と新規 lock 発行を行う。