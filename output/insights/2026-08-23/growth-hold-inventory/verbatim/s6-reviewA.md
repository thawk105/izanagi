## 所見

### 1. [real] must-fix: inventory の独立 oracle が旧 59 件のまま

[test_hold_inventory.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:51) は解除した 14 node を引き続き期待集合へ含め、残存 2 node にも旧共通 reason を期待しています。同 helper は期待集合と registry の完全一致を要求するため [L359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:359) で必ず `AssertionError` になります。

独立再構成結果は次のとおりです。

- hard-code: 59 件
- 現 registry: 45 件
- stale extra: 裁定で再導入した 14 件
- 残存 2 件: reason mismatch

この helper は JSON inventory 検査 [L537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:537) と human 出力検査 [L724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:724) の双方から使われます。

裁定は同ファイルを許可面に含めず、3 ファイル以外を禁止しています [s4-ruling.md:184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s4-ruling.md:184)。したがって親が編集面を拡張し、14 件を期待集合から除外して残存 2 件の新 reason を独立 pin する必要があります。

影響: 実 `hold_inventory()` は count 45 と新 reason を出しますが、既定受理集合は少なくとも上記 2 test を赤として本成果物を拒否します。certified 選択値自体は変わらず、台帳・レポートの exact-oracle 受理だけが壊れます。

### 2. [refuted] 裁定 node の削除・残存数に不一致はない

裁定の 14 件 [s4-ruling.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s4-ruling.md:70) と HEAD 対 worktree の registry 差分を照合しました。

| node | 実関数 | registry |
|---|---:|---|
| `test_m2_production_golden_requires_both_routes` | [L1976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1976) | hold 削除 |
| `test_m3_snapshot_mode_change` | [L1995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1995) | hold 削除 |
| `test_m3_symbolic_head_is_required` | [L2007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2007) | hold 削除 |
| `test_m3_ignored_extra_and_missing` | [L2017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2017) | hold 削除 |
| `test_m3_focus_artifact_directions` | [L2044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2044) | hold 削除 |
| `test_m1_snapshot_head_pin_is_independent` | [L1967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1967) | hold 削除 |
| `test_verify_replays_complete_fake_codex_experiment` | [L6204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6204) | hold 削除 |
| `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure` | [L1780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1780) | hold 削除 |
| `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested` | [L1912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1912) | hold 削除 |
| `test_agent_sandbox_binds_exclude_attempt_receipt_directory` | [L6180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6180) | hold 削除 |
| `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation` | [L7392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:7392) | hold 削除 |
| `test_attempt_four_is_rejected_before_launch` | [L7372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:7372) | hold 削除 |
| `test_pos_neg_submodule_initialization_state_mismatch_is_rejected` | [L4645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4645) | hold 削除 |
| `test_prompt_replacement_count_zero_expected_and_excess` | [L6100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6100) | hold 削除 |

残存は裁定どおり次の 2 件だけです。

- `test_forbidden_commits_are_unreachable_in_both_cases`: registry [L110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:110)、関数 [L1615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1615)
- `test_parent_numstat_controls_remain_pinned`: registry [L125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:125)、関数 [L1604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1604)

独立差分は `59 -> 45`、削除 14、追加 0、reason 変更 2、他 file の 43 hold 行の値変更 0 です。

影響: 意図どおり 14 node が既定受理集合へ戻り、台帳 count は 45、残存 skip 集合は上記 2 件になります。余分な解除・保留はありません。

### 3. [refuted] 3 pin の誤計算はない

変更後 registry から独立に再計算した結果です。

- count: `45`
- key SHA: `5a5f7a4f918684cbde6b9267d5535455974d441fa847ab8f070cc8b2e77d3429`
- row SHA: `8cf20b5f685a38bd9aee4e306792a509d5ebc0314a436a1e16c0fc129466d945`

これは [L43-L45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:43) と一致します。row payload も指定どおり、sorted items の `[key, hold_axis, ruling, correctness_gate]` を compact JSON 化しています [L253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:253)。

影響: contract、台帳 count、key 参照、row 契約 digest は同じ 45 行集合を指します。誤った受理集合や参照 hash は生じません。

### 4. [refuted] 禁止面・別 wave 箇所への接触はない

実 worktree の変更 path は次の 3 ファイルだけです。全差分にもこの 3 section しかありません [s5-diff.txt:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s5-diff.txt:1)、[L74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s5-diff.txt:74)、[L90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s5-diff.txt:90)。

`test_growth_test_holds_contract.py` の唯一の hunk は L43-L45 です。指定された L1266、L1827、L1924、L1949、L1985、L2079 付近には diff がありません。

`conftest.py`、`tools/hold_inventory.py`、`tools/codex_reasoning_ab.py`、`docs/` にも変更はありません。

影響: 別 wave の subprocess 色制御、既定収集、台帳生成、production resolver の受理集合や出力値は本差分から変化しません。

### 5. [refuted] 固定 rollout path と POS provenance は一致し、SHA 検査も弱くない

`_HISTORICAL_SESSIONS` は `/home/SFC/tanab/.codex/sessions` [test_codex_reasoning_ab.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:70)、`_REAL_ROLLOUT` はその配下の ID `019faca2-6e1f-7601-bfc7-be27edcfb4ba` を suffix に持つ固定 path です [L87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:87)。

POS の session ID は [tools/codex_reasoning_ab.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:71) から manifest provenance [L203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:203) と `SESSION_IDS` [L240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:240) へ導出されます。

corpus 内でこの ID を含む 165 file の `session_meta` を絞った結果、同 ID を所有する file は `_REAL_ROLLOUT` の 1 件だけでした。したがって旧 `_find_rollout(..., SESSION_IDS["POS"])` の一意返却 path と一致します。

`_verify_rollout_sha` は label から期待 SHA を取り、path の全 byte を SHA-256 化し、不一致なら `RC_SNAPSHOT` の `ValidationError` を投げます [tools/codex_reasoning_ab.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:495)。path、session metadata、corpus 内一意性は検査しませんが、実 file hash は POS pin `9b90...032b` と一致しました。旧 setup にはこの位置での SHA 検査が無かったため、固定 source の byte identity は弱くなっていません。

影響: certified 選択とレポートの source byte は引き続き POS hash に固定され、別 rollout を誤参照する受理集合拡大はありません。

### 6. [real] 裁定済みの検出力差: 実 corpus に対する unpinned 一意解決は通らなくなる

旧 `_find_rollout` は全 corpus から session owner を集め、0 件・複数件も拒否します [tools/codex_reasoning_ab.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/codex_reasoning_ab.py:483)。固定 path 化により、この実 corpus integration は当該既定 node から失われます。

ただし unpinned の意味論は既定の合成 corpus node に残っています。metadata identity と成功経路は [test_codex_reasoning_ab.py:4874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4874)、後続 metadata は [L4925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4925)、0 件・重複拒否は [L4935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:4935) が動的に検査します。これらは現在の 2 件の hold に含まれません。

影響: corpus に別の POS-owned rollout が増えた場合、旧 node は拒否しましたが新 node は固定 file が正しい限り受理します。一方、certified 選択・レポートの入力 byte は固定 SHA のままです。これは [s4-ruling.md:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s4-ruling.md:111) が明示的に採った交換であり、must-fix とは判定しません。

### 7. [refuted] sentinel と barrier node に不整合はない

2 reason の sentinel は [growth_test_holds.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:121) と [L138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:138) にあります。

- いずれも改行を含まない valid JSON で、`json.loads` 成功
- `advisory` は「記録であり自動解除条件ではない」「既定 evaluator は存在しない」と明記
- barrier node は実在:
  - `test_snapshot_submodule_object_store_is_recursive` [L2059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:2059)
  - `test_task_manifest_binds_frozen_provenance_to_literal_values` [L1412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:1412)
- 両 barrier とも現在の hold 2 件には含まれない
- `0.01`、`6.91`、`0.045`、`0.031`、`5,505 file`、`13,908 entry` は裁定値 [s4-ruling.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/s4-ruling.md:89) と一致

影響: 台帳の再評価記録、barrier 参照、観測値は正しい対象を指し、存在しない node による誤誘導はありません。

### 8. [refuted] `enforce_held_functions` は zero-hold にならず、解除関数の namespace 残存も安全

対象 file の hold は実際に 2 件です。`enforce_held_functions` は registry から対象 filename の node だけを抽出し [growth_test_holds.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:652)、0 件の場合だけ [L657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:657) で拒否します。

missing/non-callable 検査と wrapper 適用の対象も、その 2 件から生成した `function_names` だけです [L660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:660)。解除した 14 関数が namespace に残ることは走査・拒否条件になりません。module 末尾の呼出し [test_codex_reasoning_ab.py:9157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:9157) は成立します。

影響: 2 件だけが guard 対象として残り、解除した 14 件は既定受理集合へ戻ります。module import や台帳生成が zero-hold 例外で停止することはありません。

## 総括

must-fix は 1 件です。

1. `test_hold_inventory.py` の旧 59 件 exact oracle を、45 件と残存 2 件の新 reason に更新する。現裁定では禁止 path なので、親による編集面拡張が必要です。

それ以外は裁定、14/2 の閉包、3 pin、sentinel、barrier、固定 rollout SHA、guard、禁止面のすべてで一致しています。実 corpus resolver coverage の喪失だけは `[real]` ですが、合成 corpus の既定 node で意味論を維持する裁定済み交換です。

pytest は実走しておらず、緑とは申告しません。