静的レビューでは、production 実装そのものよりも、MF3a のテスト防壁に 1 件の blocker を確認しました。pytest・build・collect-only は実行しておらず、緑とは扱っていません。

## 所見 1 — producer 非依存性テストが禁止変異 M6 を殺せない

- **判定: real（blocker）。** テストは consumer `S` を先に import し（[test_s1_direct_comparison.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:35)）、その後 producer を monkeypatch しています（[同:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:487)）。allowlist は module import 時に評価済みなので（[s1_direct_comparison.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:49)）、禁止変異 `_PREPARE_CELL_CONFIGURATIONS = frozenset(s1_measurement_freeze.CONFIGURATIONS)` でも monkeypatch 前の6値を保持し、当該テストは通ります。固定6値の等価検査（[test_s1_direct_comparison.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:425)）も現行 producer が6値なので M6 を区別できません。
- **成果物影響:** この禁止変異を見逃すと、将来の第7構成が4分岐を抜けて flags-only の `src_token`／`variant_id` を得て、certified 選択の候補、材料レポートの configuration/binding 参照、試行台帳の受理行へ追加されます（fall-through は [s1_direct_comparison.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:526)、[同:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:572)）。
- **最小対処:** producer を monkeypatchした後に `s1_direct_comparison.py` を別 module 名で隔離 importし、その fresh module の集合と `prepare_cell` 拒否を検査してください。既存の隔離 import 先例は [test_trigger_gate_binding.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_trigger_gate_binding.py:253) です。その上で M6 が実際に KILLED になることを確認します。

## 所見 2 — trigger 正準化による意図外の受理集合変更は見つからない

- **判定: refuted。** membership は正準化より先に評価され、非memberは即 `passed=False` です（[p3_s4_loop.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:202)）。正準化はその後かつ trigger marker のみに限定されています（[同:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:211)）。公開 membership も従来どおり `text.strip()` と同じ key 集合です（[trigger_gate_binding.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:100)、[同:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:113)）。
- **成果物影響:** 許可された padded member の successful source／`src_token`／variant 統合以外に、拒否入力が certified 選択・材料レポート・試行台帳へ新規流入する経路はありません。
- **最小対処:** production 変更は不要です。membership-before-fold の順序を維持してください。

## 所見 3 — comparator・6構成・flags-only の不変条件は維持される

- **判定: refuted。** trigger marker、sort marker、backoff marker は別値です（[axis_trigger_gating.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/axis_trigger_gating.py:23)、[p3_s4_loop_sort.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_sort.py:96)、[p3_s4_loop.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:87)）。`sort_best` は comparator を未変更で共有 quarantine へ渡します（[s1_direct_comparison.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:539)）。固定 allowlist は producer 2面の現行6値と一致し、`stock_common`／`p2_2_flag_opt` は4分岐に入らず従来どおり flags-only yield です（[同:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:49)、[同:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:526)、[同:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:572)）。
- **成果物影響:** 現行6構成の受理集合、sort comparator bytes、それらから得る source/token/variant、材料・台帳参照は不変です。
- **最小対処:** production 変更は不要です。所見1のテストだけを修正してください。

## 所見 4 — 新設拒否が retry や例外処理から fail-open する経路はない

- **判定: refuted。** 未知構成は flags 解釈・checkout 前に `DriverError` となり（[s1_direct_comparison.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:502)）、S1 はこれを retry せず再送出し（[同:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:817)）、CLI は refused 終了にします（[同:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:897)）。Oracle も恒久 prepare 失敗を `binding-refused` にし（[s8b_oracle_driver.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1410)）、最終状態を `protocol_violation` に倒します（[同:1482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1482)）。
- **成果物影響:** 拒否対象が certified 扱いされず、材料レポートや試行台帳では成功行ではなく refusal／protocol violation になります。
- **最小対処:** なし。

## 所見 5 — 新しい import 時 `RuntimeError` は正常な32本では発火しない

- **判定: refuted。** emitter は5個の相異なる enum memberを mask の bit ごとに固定順で追加します（[reflux_ir.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/reflux_ir.py:31)、[同:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/reflux_ir.py:117)）。異なる mask は少なくとも1項の有無が異なるため、32出力は strip 後も一意です。したがって重複検査（[trigger_gate_binding.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:84)）は正常 import では発火しません。
- **成果物影響:** 正常 import 停止による certified 選択・材料生成・試行台帳の欠落は生じません。
- **最小対処:** なし。

## 所見 6 — 凍結成果物 bytes の変更はない

- **判定: refuted。** 実差分は production 3ファイルと test 3ファイルだけです。`FROZEN_MANIFEST` の23対象（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_frozen_artifacts.py:38)）を独立に SHA-256 再計算し、23/23 が literal と一致しました。`git diff --check` にも診断はありませんでした。
- **成果物影響:** 凍結 bytes、そこを参照する freeze hash・材料参照・既存試行台帳参照は不変です。
- **最小対処:** なし。

## 総括

- **NO-GO。**
- production の正準化位置、marker 限定、6構成、flags-only、fail-closed、凍結 bytes は静的には成立しています。
- ただし must-fix MF3a が禁止変異 M6 を殺せず、独立 allowlist の防壁を認証できません。
- 最小修正は producer monkeypatch 後の隔離再importテストと、M6 の実 kill 確認です。
- pytest・build・collect-only は実行しておらず、緑の主張はしていません。