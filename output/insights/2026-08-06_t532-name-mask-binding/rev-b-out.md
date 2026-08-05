## 所見 1 — import 時の index 構築が consumer の拒否・診断境界を迂回する

種別: import 副作用

根拠: 作業差分の [s1_known_axes_freeze.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:117) に `_TRIGGER_NAME_MASK_INDEX = _build_trigger_name_mask_index()` があり、import 中に実行される。一方、[s1_measurement_freeze.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_measurement_freeze.py:25)、[s1_verify_extime_calibration.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_verify_extime_calibration.py:41)、[s8b_oracle_driver.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_driver.py:52) はこれを各 `main()` の例外境界より前で import する。追加テストも [test_s1_known_axes_freeze.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:143) で、既に import 済みの module に対して builder を直呼びするだけである。

影響: emitter 名重複や alias 衝突が起きると、measurement/extime の `fails-closed:` 診断、oracle driver の JSON error、pytest の個別テスト失敗へ到達せず、raw import traceback／collection error になる。`s1_direct_comparison` も [s1_direct_comparison.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_direct_comparison.py:134) では `ImportError` しか変換しないため、import 中の `FreezeError` が `DriverError` 境界を抜ける。T-080 は遅延 import だが、[t080_freeze_migration.py:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/t080_freeze_migration.py:1806) の import が同関数内の `try` より前にある。

重大度: must-fix

提案: index と `expected_names` を初回 `_require_trigger_name_mask_binding()` 呼出し時に構築・成功後キャッシュする。これなら各 consumer の既存例外境界内で `FreezeError` として赤になり、import と pytest collection は維持できる。衝突を注入して「consumer import は成功し、最初の検査呼出しが失敗する」回帰テストを追加する。

## その他の照合結果

- 非正準述語は新 helper が最初に既存 `_require_canonical_trigger_predicate()` を呼ぶため、例外型と逐語診断は静的には保存されている。
- `test_reflux_ir.py` の既存 golden は独立 literal tripwire、新検査は production gate であり、役割の二重化ではない。
- 共有 golden は未変更。新しい S-1 テストは引数なしで、binding テストは既存の `pytest.main` 自走 harness 内にある。
- 凍結 JSON、`s8a_trigger_sweep.py`、`axis_trigger_gating.py` は差分なし。binding から s8a の import もない。
- `__all__` 完全一致検査、star-import consumer、WAL schema との動的結合は見つからなかった。
- `impl-out.md` の変更内容は差分と一致するが、「診断到達」には所見 1 の例外がある。`git diff --check` と禁止面の差分なしは再確認した。pytest、`py_compile`、`check_*` は本レビューでは実行していない。

## 総括

**NO-GO**。  
import 時 fail-closed が複数 consumer の構造化拒否と pytest collection を破壊する must-fix が 1 件ある。  
初回検査呼出しへの遅延化後に再レビューすべきである。