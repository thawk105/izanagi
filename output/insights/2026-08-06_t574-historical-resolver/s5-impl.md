実装済み・pytest 未実走です。`pegasus02` は login node のため、規律どおり pytest は実行していません。commit / `git add` / docs 編集は禁止境界を維持しました。

## 受理・拒否境界

変更前:

- `launch_validate` と oracle report は、ともに current contract と記録 hash が一致する場合だけ受理。
- current=g2 / recorded=g1 は両経路で拒否。

変更後:

- `launch_validate` の受理集合は不変。live admission は引き続き current=g2 / recorded=g1 を拒否。
- 新規 `reverify_published_freeze` と C4 report だけが、登録済み recorded=g1 を解決して受理。
- malformed / unknown / 非一意 / cross-env / dishonest resolver / calibration 欠落・hash 不一致は current fallback なしで拒否。

## 変更 hunk

- [s8b_floor_contract.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_floor_contract.py:9)、[同:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_floor_contract.py:151)
  - caller policy を明記し、診断文を lookup policy 非依存に中立化。API 不変。
- [s8b_ratified_freeze.py:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:781)
  - frozen dataclass `ReverifiedFreeze` を追加。型分離が偽造耐性を主張しない旨を明記。
- [s8b_ratified_freeze.py:1811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:1811)、[同:2153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2153)、[同:2287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2287)、[同:2314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2314)
  - C2/C3/result/occurrence の全 edge を required `contract` 引数化。
- [s8b_ratified_freeze.py:2769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2769)、[同:2783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2783)、[同:2803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2803)、[同:2840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2840)
  - current/historical resolver adapter、1回解決 helper、resolver-required core を追加。
- [s8b_ratified_freeze.py:3234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:3234)、[同:3244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:3244)
  - current 固定 `launch_validate` と historical `reverify_published_freeze` を分離。
- [s8b_oracle_report.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1189)、[同:1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1382)、[同:1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_report.py:1731)
  - `_receipt_expectations` を resolver 必須化し、production caller を明示配線。CLI を read-only 入口へ変更。
- [test_s8b_ratified_verify.py:702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:702)、[同:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:760)、[同:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:804)、[同:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_ratified_verify.py:1308)
  - public 正例・拒否 matrix・同一 object plumbing・C3 構造 pin。
- [test_s8b_oracle_report.py:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1136)、[同:1919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1919)、[同:1973](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_s8b_oracle_report.py:1973)
  - CLI consumer、public C4 正例、7件の fail-closed matrix を更新・追加。

## Test nodeid と結果

以下はすべて実装済み・pytest 未実走です。

- `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_accepts_recorded_g1_under_g2_current_while_live_refuses`
- `...::test_public_reverify_resolver_refusals_do_not_fallback_to_current[malformed|unknown|ambiguous|cross-env|dishonest-resolver]`
- `...::test_public_reverify_calibration_refusals_do_not_fallback_to_current[missing-calibration|calibration-hash-mismatch]`
- `...::test_run_cmd_projection_uses_passed_contract_as_structural_pin`
- `...::test_production_shape_run_cmd_calls_exact_portable_matcher`
- `...::test_raw_scanner_and_occurrence_validator_equivalent_for_encodings`
- `...::test_ratified_journal_required_consumer_passes_contract_mode_and_verified`
- `orchestrator/tests/test_s8b_oracle_report.py::test_cli_official_resolves_ratified_freeze_and_verifies`
- `...::test_build_observations_accepts_recorded_g1_under_g2_current`
- `...::test_build_observations_historical_resolver_fails_closed_without_current_fallback[malformed|unknown|ambiguous|cross-env|dishonest-resolver|missing-calibration|calibration-hash-mismatch]`
- `...::test_manifest_contract_sha256_mismatch_with_registry_is_protocol_violation`
- `...::test_required_receipt_consumer_derives_mode_and_passes_verified_calibration`

実走済み meta-test:

- `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` — PASS
- `...::test_every_test_file_is_self_runnable_or_allowlisted` — PASS
- `...::test_this_metatest_is_itself_self_runnable` — PASS

結果: `3 passed, 0 failed, 0 skipped`（self-run harness）。

静的検査:

- 対象5ファイルの `python3 -m py_compile` — rc=0
- `git diff --check` — rc=0
- `python3 tools/check_codex_agents.py` — rc=0
- `python3 tools/check_docs.py` — rc=0
- 禁止語検索 — 0件
- 変更ファイルは指定3コード＋2テストのみ。保護対象・docs・output は無変更。

## 注入と波及

public API は意図的に resolver 引数を公開しないため、public 正例では module の current view / production resolver を test 内だけで patch しました。C4 も `_receipt_expectations` の seam を優先しつつ、`build_observations` の production caller 配線を殺すため public test だけ module patch が必要です。

所有外では、`s8b_oracle_driver` は引き続き `launch_validate` と `LaunchValidatedFreeze` を使うため live admission 不変です。共有 emitter fixture、oracle CLI consumer、floor contract caller、driver consumer tests には波及可能性があります。`s8b_floor_campaign`、loop、pipeline、trigger gating、fuse、registry、silo verifier は未変更です。親 docs 不在だけで赤になる変更対象 test は静的には確認されませんでした。

## 総括

- recorded hash を1回解決し、同一 contract object を C2/C3/result/occurrence へ伝播した。
- live `launch_validate` と read-only `reverify_published_freeze` を型・入口とも分離した。
- 残る赤は未確認で、対象 pytest と全走は計算ノードでの親実走が必須。
- 親は M1〜M7、上記 nodeid、全走、および driver の live admission 不変を必ず確認する。