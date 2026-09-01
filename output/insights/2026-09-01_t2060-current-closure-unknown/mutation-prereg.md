# 変異事前登録と probe erratum — [T-2060]

固定 commit: `a05915d70e106275b579a7f4ceff911bf82dec0c` (段 6 fix を含む統合 commit)。
harness: `tools/mutation_worktree.py` → `tools/mutation_harness.py`、`--runner-mode dispatch`、
runner argv は `python3 tools/run_tests.py --force-dispatch` + 3 test file + `-q -rf`。
共有木の観測 root は `--source-repo /work/1/SFC/tanab/mutation-source-t2060`
(独立 clone。並行 land による共有木変化で rc=125 に落ちるのを構造的に断つため)。

## 事前登録 (段 4 で凍結、段 6 の fix 後に anchor を取り直した)

段 4 で 7 件を登録した。段 6 の fix で 2 点が変わったため取り直した。

- L1 の old 逐語が `report.pop("current_verifier_conformance", None)` から
  `report.pop("current_verifier_conformance")` へ変わった (PF-03)。
- PF-01 の修正で**新しい変異位置が 1 つ増えた** (保存済み report 比較の正規化)。M3 として追加。

計 8 件。**8 件すべて old 逐語が対象 file 内で一意であることを機械で確認した** (実装前後の 2 回)。

| ID | 位置 | 分類 | kill として数えるか |
|---|---|---|---|
| M1 | 中央 gate の歴史 early return を削除 | 境界 | 数える |
| M2 | certified 分岐の capture/catch を丸ごと削除 | 境界 | 数える |
| M3 | 保存済み report 比較の正規化を削除 | 境界 | 数える |
| C1 | schema の top-level `required` へ新 field を追加 (過剰拒否方向) | 境界 | 数える |
| C2 | schema の certified 側禁止句を削除 | 境界 | 数える |
| D1 | 表示 property の戻り値を `"unknown"` 以外へ変更 | 診断感度 | **数えない** |
| D2 | 歴史 report の top-level 投影を削除 | 診断感度 | **数えない** |
| L1 | certified 昇格時の field 除去を削除 | liveness | **数えない** |

**D1 / D2 を kill に数えない理由:** 受理集合も fail-closed 挙動も変えず、表示値だけを動かす
(DW-M03)。段 3 のレンズ A の所見 P-03 / M-03 をそのまま採用した。
**L1 を kill に数えない理由:** 安全側の fail-open ではなく「正常な certified report が生成
できなくなる」liveness 変異である (レンズ A の M-07)。

**過剰拒否の正例 (DW-M01):** C1 は受理集合を縮小する方向なので、承認外の過剰拒否を捕まえる正例
として `test_saved_report_without_current_verifier_conformance_remains_readable` (v2/v3 の
2 parametrize node) を登録する。

## probe (初回走行) — erratum

**期待 node の完全集合を事前に確定できなかったため、DW-M07 に従い初回は全件 `SURVIVED` 期待の
probe として登録し、観測 node を集めた。** この結果は消さずここへ残す。

- spec: `mutation-spec-probe.json` (sha256 `b58598a1db967acf03df13b250c424855fc19a0c4a522feaea1899dbebcde892`)
- 結果: `mutation-probe-out.json` / `mutation-probe-attempt-1.json`
- **baseline rc=0 (緑)。** collection rc=0。
- 8 変異すべて rc=1。probe の期待は `SURVIVED` だったため
  `summary = {KILLED: 0, MISMATCH: 8, SURVIVED: 0, TIMEOUT: 0, PARSE_ERROR: 0}`。
  **これは期待どおりの probe 結果であり、機構の失敗ではない。**

観測した失敗 node 数:

| ID | 失敗 node 数 |
|---|---|
| M1 | 171 |
| M2 | 64 |
| M3 | **1** |
| D1 | 115 |
| D2 | 10 |
| C1 | 8 |
| C2 | **1** |
| L1 | 4 |

**PF-02 の node 分割が実測で効いた。** 段 6 のレビュー B が「certified の正例と schema 負例が
同一 node にあり L1 と C2 の帰属が衝突する」と指摘した点は、分割後に
**C2 が `test_certified_schema_forbids_current_verifier_conformance` の 1 node だけ**、
L1 が `test_certified_report_omits_current_verifier_conformance` を含む別の 4 node、
という形で分離された。

**M3 は新設した回帰テスト 1 node だけで落ちる。** 保存済み report 比較の正規化は、
前後の層に同じ入力を拒否するものが無く、単一理由性が実測で成立している。

**D1 は 115 node で過剰決定である。** 表示 property の値は
(a) property の直接 assert と (b) schema の `const: "unknown"` の 2 層が同時に拒否する。
段 3 のレンズ A が M-03 で指摘したとおりであり、**だからこそ kill に数えず診断感度 pin として
別枠に置く。** 単独変異の証拠からは外す (DW-M03)。

**M1 は 171 node に波及する。** 歴史 early return を外すと、変異走行中の scratch worktree は
必ず dirty なので、実 repo root を使う歴史読取がすべて落ちる。前後に同じ入力を拒否する層は無い
(記録閉包の検査は commit blob だけを読み working tree を読まない) ため単一理由性は成立するが、
**node 数の多さは検出力の高さではなく波及の広さである。**

## 本走

- spec: `mutation-spec.json` (sha256 `d47ae50507f7fbcac1c80e4da2056c465deea144ce877d8c7772e04a5946862a`)
- probe の観測 node をそのまま `expected_nodes` の完全集合とし、`expected_status` を `KILLED` にした。
- 結果: `mutation-out.json` / `mutation-attempt-1.json`
