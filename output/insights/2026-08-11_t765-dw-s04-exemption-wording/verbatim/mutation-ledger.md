# [T-765] 変異台帳 — gate 変異 1 件 (実効 gate へ再照準)

## 免除しない理由

本 wave は段 4 で **C=false** (規範文の置換を実装する通常経路であり `4→7→8→9` の「実装しない」経路
ではない)、**Z=true** (実装面差分ゼロ) と裁定した。`C∧Z=false` のため変異 matrix を免除しない。

## 実効 gate への再照準 (DW-M01 の F28 経路)

本 wave の変更を機械的に拒否できる層は `python3 tools/check_docs.py` の **L1 層予算だけ**である。
実 repo の L1 超過で赤になる **pytest node は存在しない** — `test_dev_wave_layer_budget_rejects_plus_one`
(`orchestrator/tests/test_check_docs.py:2632`) は `_build_min_repo()` の合成 repo を測り、
参照ファイルも同 726-760 行で合成するため実 repo の bytes を見ない。
よって `tools/mutation_harness.py` の pytest node 抽出では KILLED を構成できない (`DW-M08` の
期待 node 契約が成立しない)。親が `DW-O19` の規律で gate 変異を実行した。

## M0 — 正例 (確定文)

| 項目 | 値 |
|---|---|
| 対象 | `docs/dev-wave/core.md:79` (commit `d78db6b0`) |
| 逐語 | `免除は「実装しない」裁定済みかつ実装差分ゼロの wave の変異 matrix だけ。` (101 bytes) |
| 実測 | L1 = **10,624 / 10,625**、`python3 tools/check_docs.py` **rc=0** (`違反なし`) |

## M1 — gate 変異 (KILLED)

| 項目 | 値 |
|---|---|
| anchor | 上記 M0 の逐語 (統合 commit `d78db6b0` 後、clean tree を確認して注入) |
| 変異 | `免除は「実装しない」と裁定された実装面差分ゼロの wave の変異 matrix だけ。` (104 bytes) |
| 注入実在 | `git diff --stat` = `docs/dev-wave/core.md \| 2 +-` (1 insertion / 1 deletion、単一変異) |
| 期待 | rc=1 かつ finding は L1 超過 1 件のみ |
| **実測** | **rc=1**、`check_docs: 1 件の違反` / `docs/dev-wave/**: L1 unique footprint 10627 bytes > 予算 10625 bytes` |
| 単一理由性 | finding は 1 件のみ。他層 (L1.5・L2 単節・構造 lint) は緑のまま = 前後に同じ入力を拒否する層が無い |
| 判定 | **KILLED** |
| 復元 | `git checkout -- docs/dev-wave/core.md` → `git status --porcelain` 空、`git diff HEAD` 空、`check_docs` rc=0 |

**結果: 1/1 KILLED、SURVIVED 0、MISMATCH 0。**

## 機械変異では証明できないもの (KILLED と数えない)

**曖昧さの解消そのもの。** 本文の意味を pin する検査は repo に存在せず、条件語を削っても
H2 構造と byte 予算を守れば `check_docs` は緑になる。これを KILLED や緑として記録しない。
代替証拠は真理値表、独立 2 レンズの敵対相談 (段 3)、焦点レビュー 3 巡 (段 6)、consumer 棚卸し、
段 7 の逐語凍結である。
