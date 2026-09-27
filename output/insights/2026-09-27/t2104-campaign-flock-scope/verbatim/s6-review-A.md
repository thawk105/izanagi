## 所見

1. **must-fix — `orchestrator/tests/test_p3_s4_loop.py:7218`**
   preflight probe の到達回数 `1` は、実経路と一致しない。正常な coder では `_run_one_iteration_resolved` が `validate_backoff_preflight` を呼び、その後 `_check_attribution_before_quarantine` → `assert_value_literal_consistent` が同じ関数を再度呼ぶ（`p3_s4_loop.py:2470, 1975–1976, 1929`）。したがって実行が checkpoint まで進めば `hits` は **2** になる。これは静的推論であり、実走確認は親の担当。
   **成果物影響:** 焦点走が実装の保持区間に関係なく赤になり、B-4 記録・block score・verdict の修正を受け入れ判定できない。
   **推奨:** 実経路に合わせて 2 回の到達を assert し、両回で producer path が busy である検査を維持する。

## 総括

**NO-GO。must-fix は所見 1。** 静的検査では、公式 B-4 の main→driver→run_campaign に保持区間の窓や正しさゲートの緩和は見つからなかった。M1〜M8 の変異位置と対応する検出 test も確認できた。テストの緑、旧版での期待赤、既存 suite と構造 pin の適合は実走結果として扱っていない。