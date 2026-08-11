# [T-804] 変異 matrix 実測結果

anchor commit = `34ccac98549f2ad88ad15e8757dfd56340dd51eb`
spec = `mutation-spec.json` (sha256 `05a732ef62e3b8010c371f31a4681163c9bebb0841f1cf0f0e6af653406dbc62`)
runner = `tools/mutation_worktree.py`(使い捨て worktree) → `tools/run_tests.py --force-dispatch -rf`
対象 = `test_s8b_oracle_manifest.py` / `..._manifest_contract.py` / `..._driver.py` / `..._report.py` / `..._judge.py`

## 結論

**11 件すべて検出 (SURVIVED ゼロ、TIMEOUT ゼロ)。baseline は PASSED (赤 0)。**
7 件は事前登録した期待 node と完全一致。4 件は **期待 node が実際の赤の部分集合**だったため
MISMATCH となった。いずれも「変異が生き残った」ではなく「親の事前予測が狭すぎた」ことによる。

| ID | 位置 | 種別 | 結果 | 赤 node 数 |
|---|---|---|---|---|
| M0 | `verify_manifest` の approved spec 照合 block を全削除 (**wave 前の実コードの形**) | negative | MISMATCH (検出) | 8 |
| M1 | schedule の deep equality だけ削除 | negative | KILLED | 1 |
| M2 | campaign_ids の deep equality だけ削除 | negative | KILLED | 1 |
| M3 | run_contract の deep equality だけ削除 | negative | KILLED | 1 |
| M4 | `spec_sha256` の等値検査だけ削除 | negative | KILLED | 1 |
| M5 | seal wrapper の `approved_spec` に default を付ける (**fail-open 形**) | negative | KILLED | 1 |
| M6 | judge の expected_cells 束縛を削除 | negative | MISMATCH (検出) | 3 |
| M7 | report legacy 分岐で自己申告 `spec_sha256` をコピー (**ロンダリング形**) | negative | MISMATCH (検出) | 3 |
| M8 | gate 注入経路の spec hash 再束縛を削除 | negative | KILLED | 1 |
| M9 | spec 比較を過剰拒否側へ倒す (`==` → `is`) | **positive** | MISMATCH (検出) | 213 |
| M10 | 共有 `_validate_run_contract` を exact key 化 (= 撤回した P5) | **positive** | KILLED | 1 |

## MISMATCH 4 件の原因 (すべて親の予測不足、検査側の欠陥ではない)

1. **M0 — 層を跨ぐ結合を数え落とした。** 予測した 7 件 (manifest 層の投影別負例) は全部赤くなり、
   加えて `test_s8b_oracle_report.py::test_report_cli_accepts_matching_spec_then_rejects_one_other_spec_without_output`
   が赤くなった。verifier の spec 照合を消せば report 層の別 spec 拒否も同時に効かなくなるため、
   これが正しい挙動である。
2. **M6 / M7 — source hash pin が道連れになる。** 意図した node は赤くなったが、加えて
   `test_build_approved_valid_fixture_output_depends_only_on_spec_pin` と
   `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal` の 2 件が赤くなった。
   `PIN_GATE_SPEC_RAW` は `judge` / `report` / `artifacts` の **source SHA-256 を埋め込む** ため、
   これら 3 ファイルへのどんな変異も必ずこの 2 件を巻き込む。
   **この族のファイルを変異させる登録では、期待 node に pin 2 件を常に含める必要がある。**
3. **M9 — 過剰拒否変異の波及範囲を狭く見積もった。** 正当な manifest を拒否する変異は、
   意図した正例 1 件ではなく、verify を通す全テスト 213 件を赤にする。意図した正例
   (`test_verify_manifest_accepts_exact_approved_spec_projection`) は赤の中に含まれており、
   **過剰拒否の検出という目的自体は達成している。**

## 事前登録から除外した変異と理由 (段 4 裁定 §7)

- `generator_versions` の deep equality 削除 — `_validate_generators` が**前段で**同じ入力を
  拒否するため単一帰属が成立しない (段 3 レンズ A 所見 5)。
- run_contract の余剰 key 変異 — P5 撤回後は spec 完全一致比較が拒否するため二重拒否になる。

## 走行前に 1 度 fail-closed で停止した記録 (erratum)

初回投入は **走行ゼロで rc=2 停止**した。原因は親の spec の誤りで、parametrize の期待 node ID に
日本語を書いたが、**pytest は非 ASCII を `\uXXXX` へ正規化する**ため collection に実在しなかった。
harness の「期待 node が pytest collection に実在しない」検査が正しく発火した。
実 ID は `--collect-only` から採取して修正した。
なお **dispatch 経由の collect-only は stdout が切り詰められる** (421 件中 38 件しか出ない) ため、
node 一覧の採取はローカル collect で行った。
