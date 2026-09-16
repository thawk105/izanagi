# 親 brief — dev-wave t2117 (復元不能な当時の bytes 一致の撤去と恒久解)

## 研究前進

T-181 の reasoning routing benchmark は装置完了・認証済み再走まで済んだ計測装置
(`docs/phase3.md` の [T-181])。その oracle 材料である independent golden は、二経路を独立に
導いて一致を要求する。

- route A: `INTEGRATED_COMMIT` の blob へ fix2 の apply_patch を**逆適用**
- route B: `BASE_COMMIT` の blob へ author + fix1 の apply_patch を**順適用**
- `_compare_golden_routes` が両者の不一致を `ValidationError` で拒否

**この照合は現在どの常時実行 node からも到達しない。** 完了判定は、二経路照合の正例と
mismatch 負例が常時実行で走り、`_compare_golden_routes` を恒真化する変異で殺せること。

## scope (本題のみ)

1. `orchestrator/tests/test_codex_reasoning_ab.py:3568-3586`
   `test_m2_production_golden_requires_both_routes` が要求する
   「2026-07-29 の exact bytes 一致」を撤去する。
2. 同じ一般的性質を、既存の合成入力 helper を使う**常時実行 node** へ移す
   (正例 1 本 + mismatch 負例 1 本)。

## 確定済みユーザー裁定 (動かさない)

- 恒久 skip は採らない。被覆を暗黙に消し絶対規律 2 に触れる。
- 撤去するのは復元不能な当時の bytes 一致だけ。一般的な性質の検査は既存のまま残す。
- 撤去対象以外の完全性・意味的束縛は維持する。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- 射程は局所修復 (DW-G03 の独立 2 例は成立しない)。

## 不変条件

- `_require_pinned_rollouts` (`:794`) 本体と、その自己検査 3 node
  (`:963` `:975` `:988` の各 def) は**残す**。D1367 が定めた「名前の実在だけを見る」形を壊さない。
- `test_real_rollout_collector_golden_is_source_bound` (`:9152`) は **触らない**。D1615 が
  「静的 skip を足さない・参照の付け替え以外はコードを変えない・実データ依存 assert の切り出しは
  要求外の一般化」と裁定済み。
- `tools/codex_reasoning_ab.py` の `_LEGACY_SESSION_IDS` / `_LEGACY_ROLLOUT_SHA256` /
  `_LEGACY_PROMPT_SOURCE` は**当時の記録として残す** (絶対規律 7)。撤去するのは
  「現存 file と照合せよ」という要求だけであって、記録された値ではない。
- production 既定 `verify_source_sha=True` を変えない。
- **受理集合を広げない。** 今 `ValidationError` で拒否されるものが、変更後に通ってはいけない。
- 編集面は `orchestrator/tests/test_codex_reasoning_ab.py` の 1 file を既定とする。
  他 file へ広げる必要があるなら、その理由を file:line で書く。

## 親が実測した事実 (推測ではない)

すべて worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2117-legacy-bytes-removal` で実測。

1. 恒久解の**第一段は着地済み**。commit `f1a2183ef` ([T-2111]、D1382 第一段) が 24 node を
   合成入力で復帰させた。main の祖先であることを `git merge-base --is-ancestor` で確認した。
2. `_require_pinned_rollouts` の呼び出しは 4 箇所
   (`:969` `:982` `:993` `:3573`)。うち `:969` `:982` `:993` は guard 自身の正例・負例
   (`test_historical_rollout_guard_*`)。**production 経路は `:3573` の 1 箇所だけ**である。
   → 恒久沈黙している node は `test_m2_production_golden_requires_both_routes` の 1 件。
3. `derive_independent_golden` (`tools/codex_reasoning_ab.py:925`) のうち、rollout 参照より
   **後ろが全て未被覆**である。すなわち `_extract_apply_patches` (`:658`)、fix2 の枚数検査、
   route_a の `_apply_patch_set` reverse (`:784`)、route_b の
   `_apply_patch_set_independent` (`:892`)、`_compare_golden_routes` (`:912`)。
   既存の `test_derive_independent_golden_wires_pins` (`:8887`) と
   `test_external_manifest_golden_does_not_read_module_session_or_rollout_pins` (`:8922`) は
   3 回目の `_find_rollout` で `RuntimeError("wiring observed")` を投げて打ち切るため、
   ここへ到達しない。**これは親が 2 test の本文を読んで確認した読解であり、被覆計測ではない。**
4. 合成 fixture `benchmark_snapshots` (`:855`) は `prepared_golden=` を渡して golden 導出を
   迂回する。よってこの fixture 経由でも二経路は走らない。
5. 使える既存の合成入力 helper (いずれも同 test file 内):
   `_synthetic_task_manifest` (`:6581`)、`_write_synthetic_benchmark_rollout` (`:834`)、
   `_synthetic_benchmark_message` (`:813`)、`_write_pinned_rollout_stub` (`:802`)。
6. `derive_independent_golden` は `task_manifest=` と `verify_source_sha=` を受ける。
   `BASE_COMMIT` / `INTEGRATED_COMMIT` は module 定数であり、引数では差し替えられない。
   これらは repo 内の git object なので**復元可能**である (消えた `~/.codex` の rollout とは違う)。
7. node 名を手書き literal で pin する登録簿が 3 箇所ある。
   `orchestrator/tests/conftest.py` の `:397` 付近と `:552` 付近、
   `orchestrator/tests/test_real_repo_serialization.py` の `:52` 以降の golden 群。
   **`test_m2_production_golden_requires_both_routes` はどれにも載っていない**
   (`grep` で 0 件)。`_git(_ROOT, "show", ...)` を通るのに載っていないので、
   登録は fixture 由来の自動判定ではなく手書きである。
   → `benchmark_snapshots` を使わない新 node なら登録簿の更新は要らない、というのが
   親の provisional 判断 (P1-c)。**これは 3 箇所の grep 結果からの読解であり、
   登録簿の生成規則を読み切った結果ではない。** `test_real_repo_serialization.py:1586`
   `test_real_repo_group_collection_exactly_matches_canonical_nodes` が exact 一致を要求するので、
   誤れば受入が赤になる。
8. `orchestrator/tests/acceptance_duration_ledger.json` は add-only
   (`test_add_only_preserves_existing_entry_bytes_and_excludes_frozen_nodes`)。
   node 撤去で既存 entry を消す必要はない。
9. `tools/check_docs.py` に対象 2 file の whole-file SHA-256 pin は無い。
10. `output/insights/2026-07-30_t181-reasoning-ab/mutation-ledger-round1-erratum.json` が
    m2 を期待 node として記録している。**これは当時の記録なので改変しない** (絶対規律 7)。

## 親の provisional 裁定 (段 3 の攻撃対象)

- **(P1-a)** 恒久沈黙 node は m2 の 1 件だけ。根拠は実測 2。
- **(P1-b)** D1615 は m2 には及ばない。D1615 の主題は
  「terminal 分類は静的 skip を足すことではない」であり、対象は
  `test_real_rollout_collector_golden_is_source_bound` と明示されている。
  m2 は実際に skip している別件である。
- **(P1-c)** 新 node は `benchmark_snapshots` を使わず `tmp_path` 起点にすれば
  real-repo 登録簿の更新が要らない。根拠は実測 7。
- **(P1-d)** 二経路の独立性 (route A と route B が別の parser を通ること) は、
  合成入力でも保てる。route A は `_apply_patch_set`、route B は
  `_apply_patch_set_independent` という別実装を通るのが本質であり、
  入力 bytes が 2026-07-29 のものである必要はない。
