# [T-2117] 復元不能な歴史 bytes 要求の撤去と恒久解 — 逐語と変異台帳

- wave: `dev-wave-t2117-legacy-bytes-removal`
- branch: `worktree-dev-wave-t2117-legacy-bytes-removal`
- base: local main `d97c423bd`
- 実装 commit: `d4537e0ab`
- 日付: 2026-09-16

## 何をしたか

`~/.codex/sessions` の 2026-07 分 rollout がストレージ運用で消えたことにより恒久 skip に
落ちていた `test_m2_production_golden_requires_both_routes` から、復元不能な
「2026-07-29 の exact bytes 一致」要求だけを撤去し、同じ性質を合成入力の常時実行 node へ戻した。

D1382 の第二段にあたる。第一段 (24 node の合成入力復帰) は [T-2111] の `f1a2183ef` で着地済み。

## 段 1 で実測した残差

- `_require_pinned_rollouts` の production 呼び出しは
  `orchestrator/tests/test_codex_reasoning_ab.py:3573` の 1 箇所だけだった。
  他の 3 箇所 (`:969` `:982` `:993`) は guard 自身の正例・負例である。
  → **`_require_pinned_rollouts` 経由で恒久沈黙していた node は 1 件**。
- その 1 件が守っていた `derive_independent_golden` の二経路照合は、
  **どの常時実行 node からも到達していなかった**。
  既存の `test_derive_independent_golden_wires_pins` と
  `test_external_manifest_golden_does_not_read_module_session_or_rollout_pins` は
  3 回目の `_find_rollout` で `RuntimeError` を投げて打ち切るため、
  patch 抽出・route A・route B・`_compare_golden_routes` へ到達しない。
  合成 fixture `benchmark_snapshots` は `prepared_golden=` を渡して golden 導出を迂回する。
  **この読解は後述の変更前変異走 (5/5 SURVIVED) が実測で裏付けた。**
- [T-2125] は `orchestrator/campaign/artifact_admission.py` の `current-closure-unavailable`
  が主題で、対象 file が重ならない。重複修正ではない。

## 採った形

- 旧 node を**関数ごと残し**、`TOOL._sessions_default()` 参照・`_require_pinned_rollouts` 呼び出し・
  歴史 golden の SHA-256 assert を撤去した。
- `tmp_path` に小さな git repo を作って base / integrated の 2 commit を置き、
  `TOOL.BASE_COMMIT` / `TOOL.INTEGRATED_COMMIT` だけを `monkeypatch` する。
  4 状態 (`base` / `authored` / `golden` / `integrated`) を test 側の literal で定義し、
  author / fix1 / fix2 の合成 rollout に apply_patch を 1 件ずつ入れる。
- 隣に mismatch 負例 `test_m2_production_golden_rejects_route_mismatch` を新設した。
  fix1 の追加側だけを `golden-mismatch` に変え、除去側は据え置く。
- `tools/codex_reasoning_ab.py` は 1 byte も変えていない。登録簿も変えていない。

## 段 3 の敵対 2 レンズ (blocker ゼロ)

両レンズとも「plan を採ってよい」。real な所見は 3 件。

1. **route B へ渡るのは list ではなく generator である。**
   観測のために `list(patches)` で実体化したら、その list を実関数へ渡さないと
   route B が `base` のままになり、正しい入力なのに偽の mismatch で落ちる。
   実装子への指示に入れ、実装は実体化した列を渡している。
2. **負例は除去側を据え置き追加側だけ変える。**
   除去側を変えると patch context 不一致で `_compare_golden_routes` へ到達する前に
   別の `ValidationError` が出て、「到達前の失敗」を「mismatch 検出」と取り違える。
   負例は `rc` と `reasons` を完全一致で固定してこれを見分ける。
3. **親 brief の前提 2 つが一般化しすぎていた。** 段 4 で限定した。
   - 「恒久沈黙は 1 件だけ」→「`_require_pinned_rollouts` 経由の沈黙は 1 件だけ」。
     別 guard・別条件分岐による沈黙を排除したとは主張しない。
   - 「`benchmark_snapshots` を使わなければ登録簿の更新は要らない」→
     「function scope の `tmp_path` / `monkeypatch` だけを使い、どの session/module scope
     共有 fixture も使わない今回の構成に限る」。
     `orchestrator/tests/test_real_repo_serialization.py` の consumer 閉包は
     登録済み node を seed とし、他の共有 fixture も対象に含むため。

## 段 6 の敵対 2 レンズ (blocker・must-fix ゼロ)

- レンズ A が事前登録 5 変異を 1 件ずつ机上で当て、期待 node が赤になると判定した。
  とくに M1 (比較関数の恒真化) は**負例だけが殺し正例は緑のまま**、
  M2 (比較呼び出しの省略) は**両方が赤**という区別を確認した。後述の実測と一致した。
- **nit 1**: 負例末尾の `assert expected_a != expected_b` は test 側 literal 同士の比較で恒真。
  何も守っていない。ただし手前の `pytest.raises` が M1 を捕えるため害はない。**直していない。**
- **nit 2**: 一時 repo の commit は system git 設定に依存する
  (`commit.gpgsign=true` で署名鍵が無い、失敗する `core.hooksPath` など)。観測はしていない。
- **scope 外 1**: 新 2 node は `verify_source_sha` の拒否能力を証明しない。
  合成入力は常に正しい SHA を持つため。本 wave の撤去で新たに生じた穴ではなく既存の被覆限界。
- **scope 外 2**: commit 定数を差し替えるため、歴史 patch の複雑な hunk 処理との
  統合保証は引き継がない。段 4 で受容済みの代償。

## 実測

### 焦点走 (`tools/run_tests.py` 経由、計算ノード dispatch)

| 範囲 | 結果 |
|---|---|
| `test_codex_reasoning_ab.py -k "m2_production_golden or historical_rollout_guard or derive_independent_golden or external_manifest_golden"` | 8 passed (5.14s) |
| `test_real_repo_serialization.py` / `test_acceptance_schedule_order.py` / `test_update_acceptance_duration_ledger.py` / `test_hold_inventory.py` / `test_growth_test_holds_contract.py` | 276 passed, 1 skipped (63.60s) |

node 集合を検査する meta-test (登録簿の exact 一致、所要台帳の add-only、hold 台帳) はいずれも
赤にならなかった。登録簿の更新は不要という段 4 の裁定が実測で支持された。

### 変異 matrix — 新旧両走 (DW-M08)

本 wave は production 差分ゼロのテスト強化なので、同じ 5 変異を変更後と変更前の双方へ当てた。
runner はどちらも
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_reasoning_ab.py -rf -p no:cacheprovider`、
`--runner-mode dispatch`。各変異の置換は両走とも `anchor_counts = {"0": 1}` で、
DW-M04 の一箇所性を満たす。

| | 変更後 (`d4537e0ab`) | 変更前 (`d97c423bd`) |
|---|---|---|
| spec | `spec-after.json` sha256 `20abb039…db372` | `spec-before.json` sha256 `202e630b…ba548` |
| 台帳 | `result-after.json` | `result-before.json` |
| baseline | **PASSED** | **PASSED** |
| 結果 | **KILLED 5 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0** | **SURVIVED 5 / KILLED 0 / MISMATCH 0 / TIMEOUT 0** |
| 期待一致 | 5/5 | 5/5 |

**変更前はどの変異も 1 node も落とさなかった。** これが「この wave が塞いだ穴」の直接証拠である。
変更後の KILLED 件数だけでは、その変異がもともと別の node に殺されていた可能性を排除できない。

| ID | 変異 (`tools/codex_reasoning_ab.py`) | 変更後の実失敗 node | 変更前 |
|---|---|---|---|
| M1 | `_compare_golden_routes` の `if reasons:` を `if False:` にする | **負例のみ** | 0 件 |
| M2 | `derive_independent_golden` 末尾を `return dict(route_a)` にする | 正例 + 負例 | 0 件 |
| M3 | route A の `reverse=True` を `False` にする | 正例 + 負例 | 0 件 |
| M4 | route B の patch 順を `("fix1", "author")` に反転 | 正例 + 負例 | 0 件 |
| M5 | route B を `_apply_patch_set_independent` から `_apply_patch_set` へ差し替え | 正例 + 負例 | 0 件 |

**M1 の結果が本 wave の要点である。** 比較関数の中身を恒真化する変異は
**新設した負例だけが殺し、正例は緑のまま**だった。二経路照合という性質は正例を積んでも
守れず、負例が無ければ検出できない。この node が沈黙していた間、まさにこの穴が空いていた。

所要のばらつき (変更後 M4 = 807 秒、変更前 M5 = 301 秒、他は 84〜96 秒) は計算ノードの
混雑による待ちであって変異の性質ではない。同じ runner・同じ collection である。

### 道具側で実測した 2 件 (実装の問題ではない)

1. **`tools/mutation_worktree.py` は作った使い捨て worktree の submodule を初期化しない。**
   そのため変更前走の baseline が 27 errors で `PARSE_ERROR` になり、
   本文は `submodule is not initialized: external/ccbench/third_party/shirakami` だった。
   DW-C01 は「全新規 worktree を `tools/dev_wave_submodule_init.py` で再帰初期化する」と定めるが、
   この wrapper 自身は行わない。
2. **同 wrapper の `--resume` は baseline を再走しない** (`baseline=0 run(s)`)。
   前回の `PARSE_ERROR` をそのまま使うため、baseline が壊れた状態からは回復できない。
   さらに同 wrapper の「source/main 共有木の観測 bytes が不変」という事後検査が
   `共有木の事後検査に失敗` で落ちた。この機体では多数の wave が同時に走るため構造的に破れる。

対処は、既にできていた container repo (`--commit` の worktree、submodule 初期化済み) に対して
`tools/mutation_harness.py` を直接当てることで、これは成功した。
