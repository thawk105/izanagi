## 総括

静的結論は「T-513 の実装方針は有効。ただし、plan の scope 記録とテスト検出力に補正が必要」です。

- 実所見: 2件
- must-fix: 0件
- scope 外の裁定パッケージ候補: 1件（T-515）
- pytest/build: 未実行。緑・確認済みとは扱っていない。

### 到達層の棚卸し

| 層 | 根拠 | plan |
|---|---|---|
| 骨格入力 | [patch line 102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:102) | 軸定数・drift test で参照 |
| template parser / hole 読み取り | [parse_template_file](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:540)、`hole_text` 構築 | 変更なし |
| materializer | [render_hole](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:170) | 変更なし |
| trigger canonicalizer | [canonicalize_predicate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/trigger_gate_binding.py:111) | 変更なし |
| quarantine / structural check | [quarantine](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:193)、[hole invariant](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:333) | 変更なし |
| build admission | [_require_materialized_trigger_predicate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:71) | exact 比較へ変更 |
| source identity / build | `source_digest.py` の `EVOLVE_BLOCK_SOURCES` と `buildcache` | hole の意味検査はしない |
| WAL / 8c closure | 既存の binding fields。8c は [mask/predicate/source](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-8c-formal-consumer-wiring/orchestrator/campaign/reflux_source_closure.py:79) を読む | 変更なし |

quarantine 経路では、`is_canonical_predicate` が外周空白を許しても、その直後に `canonicalize_predicate` が正準 emitter bytes へ戻すため、現在の clean → patch → `render_hole` 経路から外周空白・tab・4空白が hole に入る余地はない。[patchharness](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/patchharness.py:234) も適用前 clean を要求する。

### B-1 — producer scope の記録不足

trigger marker の本番 `quarantine` caller は、次の8箇所ある。

- `p3_s4_loop_trigger_gating.py`: 419, 840, 952 — `wire → parse_wire → emit_predicate`
- `p3_autonomous_workload_trial.py`: 659 — `wire → parse_wire → emit_predicate`
- `s8a_trigger_sweep.py`: 429, 451 — `combination → predicate_for`
- `s1_verify_extime_calibration.py`: 342 — `s8a.predicate_for` と freeze の一致検査後
- `s1_direct_comparison.py`: 565 — freeze の `gate_predicate`。外周空白は membership で許され得るが quarantine 内で正準化される

plan は `pipeline.py` と `s1_verify_extime_calibration.py` 以外の producer 経路を列挙していない。ただし、現状それらに同型 hole は残っていない。

成果物影響: 現在の受理集合は変わらないが、直さないと phase report / closure reference が「全 producer を調査済み」と誤って記録し、将来の raw-text producer の未検査経路を閉じたと誤認する。

### B-2 — 7 nodeid 中 3件は `.strip()` mutant を検出しない

静的予測は以下のとおり。

| nodeid | 旧 `.strip()` へ戻した場合 |
|---|---|
| `test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds` | 通る。標的 mutation 検出力なし |
| `test_trigger_binding_rejects_crossed_materialized_predicate_and_mask` | mask 不一致で従来どおり拒否。検出力なし |
| `test_trigger_predicate_hole_indent_matches_template_patch_bytes` | admission 実装と独立。検出力なし |
| `test_trigger_binding_rejects_materialized_predicate_with_outer_spaces` | 期待拒否が起きず落ちる |
| `test_trigger_binding_rejects_materialized_predicate_with_leading_tab` | 期待拒否が起きず落ちる |
| `test_trigger_binding_rejects_materialized_predicate_with_trailing_space` | 期待拒否が起きず落ちる |
| `test_trigger_binding_rejects_materialized_predicate_with_four_space_indent` | 期待拒否が起きず落ちる |

4–7 は plan 上 `_require_materialized_trigger_predicate` を直接呼ぶため、`is_canonical_predicate` で手前に止まる問題はない。

成果物影響: 1–3だけでは `.strip()` 回帰により外周空白 source が certified / WAL 受理集合へ戻るが、4–7が同じ mutant を捕捉するため、7件全体では実装回帰の検出力は残る。

### DW-O13

入力は存在する。骨格の実 payload は patch の [line 102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:102) にあり、patch 適用後の `cc/silo/transaction.cc` の marker hole になる。現在の stock submodule に marker がないのは、適用前だからであり、存在しない入力を前提にしてはいない。

### T-515

親の「現行到達不能」という結論は維持できる。ただし producer の列挙は wire/combo だけではなく、freeze の `gate_predicate` 経路も含めるべきである。いずれも現行では正準化後に materialize され、`diffq_variant_id` へ自由文字列が渡らない。

到達可能化する変更は、trigger quarantine の canonicalization を bypass するか、producer が自由文字列をそのまま `record_diff_reject` / `diffq_variant_id` に渡す変更である。

### 並行 wave と規模

plan は 8c 所有の `reflux_origin_artifacts.py`、`reflux_source_closure.py`、`s8b_descriptor.py`、`wal.py` を編集しない。`pipeline.py` の変更も既存 WAL binding fields の生成前 reject を増やすだけで、8c の schema / topology を壊す静的根拠はない。

新規 module や新規抽象はなく、軸定数1つ・admission比較・既存 renderer を使う fixture・drift test なので規模は妥当。

scope 外候補は、親 brief のとおり T-515 1件のみ。