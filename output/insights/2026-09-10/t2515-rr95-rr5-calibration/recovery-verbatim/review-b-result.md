## 総括

**GO**です。親の関連テスト実走と変異 probe へ進めます。コード上の must-fix は0件です。静的レビューのみであり、pytest green や最終 land 可はまだ主張しません。

## 所見

### real: M8 の期待失敗集合は8 node

[interpreter fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:593) は記録用 `python3.10` と終了97の裸 `python3` を分離し、[production 関門](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:431)を裸へ戻すM8を動的に識別します。

現コードの静的 call graph から、期待候補は次の8 nodeです。

- `test_certify_derives_protocol_target_and_binary_path[silo]`
- `test_certify_final_calibrate_binary_matches_built_binary[silo]`
- `test_certify_keeps_backoff_fixed_and_condition_gate_silo_only`
- `test_condition_gate_uses_smoke_checked_interpreter_selected_before_call`
- `test_default_silo_build_and_calibrate_argv_match_offline_contract`
- `test_certify_offline_fetchcontent_contract_is_identical_for_all_protocols`
- `test_certify_condition_gate_receives_the_same_fetchcontent_tokens`
- `test_certify_configure_use_site_passes_the_complete_configure_argv`

[reference mutation spec](/work/1/SFC/tanab/dev-wave-jobs/t2515-recovery-20260910/reference-mutation-spec.json:106)の単一 node は最終期待集合としては不足します。影響は、M8を正しくkillしても完全一致判定が赤になることです。最小対応は裁定どおり、親の初回 probe から `expected_nodes` を機械生成することです。これは実装欠陥ではなく予定済みの受入作業です。

### refuted: M5/M6 の後続関門mask

[負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1553)はclean repo、三者staging、dry-run helperを使用しています。[helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1595)は正常経路を `rc=0` まで到達可能にしているため、M5の `+5` とM6の `05` が正規化されれば期待 `rc=2` と食い違って赤になります。offline前提不足などによる同じ `rc=2` へのmaskはありません。修正不要です。

両shellの受理集合も exact `{5,20,50,80,95}` で一致し、submit側はpre-submit、receipt、qsub exportまで値を検査しています。

### refuted: interpreter選択の実効性不足

[選択処理](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:411)は候補自身でPython 3.10 smokeを通し、条件関門の唯一の呼出しより前に完了します。関門は選択済み絶対pathを使用し、timeout 300秒、macro、meaning、silo限定条件は不変です。静的assertだけでなく、上記poison fixtureがproduction関数を起動するため、M8の実害を検出できます。

### refuted: helper callerの更新漏れ

全repo参照を確認しました。

- `_run_submit_dry_run_in_clean_fixture`: 5 callerすべて5要素の戻り値へ更新済み
- `_calibrate_interpreter_fragment`: 2 callerとも新しい分割抽出と整合
- `_certify_toolchain_fragment`: 唯一のcallerと整合
- `_protocol_shell_observation`: `silo` consumerはM8を識別し、`mocc`と`tictoc`は不要な関門を呼びません

戻り値個数や抽出境界の不一致はありません。

### refuted: T-2535、T-2536、所有外への退行

T-2535の独立した verifier interpreter、三者source複製、pristine検査、5個のoffline FetchContent引数は[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:581)に保存されています。T-2536のaxis/cache検査領域は[test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:41)で差分なしです。

追跡差分は指定4実装fileと親READMEだけで、未追跡追加は親のfailure insight一式だけです。`e618883c2`から`2ff0ce2c9`までのmain後続も裁定docsのみで、対象5 fileとの重複はありません。

### refuted: READMEと失敗insightの過大主張

[親README](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/README.md:123)は5値whitelistとrr5/rr95手順を正しく記載しています。[failure insight](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/output/insights/2026-09-10_t2515-rr95-rr5-calibration/README.md:20)も保存7 artifactと一致し、Python 3.9失敗、後続のBACKOFF拒否、rr95 receipt値 `95` を区別しています。accepted calibrationや現在実装の受入成功は主張せず、裁定済みBACKOFF撤去を別変更単位として記録しています。M7はdocs整合pinに限定されており、runtime証明には数えていません。