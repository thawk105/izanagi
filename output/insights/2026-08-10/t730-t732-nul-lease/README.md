# [T-730] / [T-732] wave の逐語と台帳 (2026-08-10)

worklog エントリの実体。branch `worktree-dev-wave-t730-t732-nul-lease-merge`、
統合 commit `131c65f1`、受入 tip `fbc95b2f`。

## 何をした wave か

- **[T-730]** 証拠 path の NUL を `_safe_path` と `read_blob_at` の 2 層で fail-closed 拒否した
  (ユーザー裁定 (a)、rulings-inbox §58)。
- **[T-732]** 受入 lease の待ち手契約 (`docs/pegasus-runbook.md` §7.3) を正本化した
  (ユーザー裁定 (a))。裁定文の実体は commit `69379268` で既に landed 済みで、
  本 wave が入れたのは残余の精密化である。

## ファイル

| ファイル | 中身 |
|---|---|
| `probe_v2_out.txt` | 裁定前提の実測 v2。wave 前 source (`6a159e0d` の archive) に対し、blob 型・完全 OID・full sha256 を assert した出力 |
| `s2-plan.md` | 段 2 プラン起草 (codex, read-only, reasoning=max) |
| `s3-lens-a.md` | 段 3 敵対相談レンズ A (正しさ境界)。NO-GO / must-fix 2 |
| `s3-lens-b.md` | 段 3 敵対相談レンズ B (裁定整合)。NO-GO / must-fix 5 |
| `s4-ruling.md` | 段 4 の裁定表・プラン v2・変異事前登録・裁定パッケージ |
| `s6-lens-c.md` | 段 6 敵対レビュー C (実装の正しさ)。GO / must-fix 0 |
| `s6-lens-d.md` | 段 6 敵対レビュー D (検出力と裁定整合)。NO-GO / must-fix 3 |
| `mutation-spec.json` | 変異事前登録 (7 件)。sha256 = `044267f378df0ba58f58e8f5411c64d12df8ce07e76b0d10a047df11534328ec` |
| `mutation-ledger.json` | 変異本走の台帳。7/7 KILLED、事前登録と完全一致 |

## 実測値

- **受入全走**: rc=0 / 7982 passed / 20 skipped / 490.59 秒 (request `900358.nqsv`、tip `fbc95b2f`)。
- **対象テスト**: 178 passed / rc=0 (fix 後、commit 前の 1 走)。
- **変異**: 7/7 KILLED、SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、baseline rc=0
  (対象 commit `131c65f1`、`tools/mutation_worktree.py` の使い捨て worktree)。
- **裁定前提 (probe v2)**: `HEAD:CLAUDE.md` と `HEAD:CLAUDE.md\x00not-the-contract-path` は
  同一 blob record (OID `1744da0e…`、13812 bytes、sha256 `1dfb04e9…` 一致)。TAB は `missing`。
  wave 前の両防壁とも NUL を素通しし、`read_blob_at` は契約 path と異なる文字列で同一 blob を返した。

## 変異の対応表

| # | 変異 | 期待赤 node | 結果 |
|---|---|---|---|
| M01 | 層 1 を **wave 前の逐語**へ戻す | predicates 5 node | KILLED (完全一致) |
| M01b | 層 1 の NUL 選言だけを外す | predicates 3 node | KILLED (完全一致) |
| M02 | 層 2 を **wave 前の逐語**へ戻す | core 2 node | KILLED (完全一致) |
| M03 | 層 1 を C0 一般拒否へ過剰一般化 | predicates TAB 正例 1 node | KILLED (完全一致) |
| M04 | 層 2 を C0 一般拒否へ過剰一般化 | core TAB 正例 1 node | KILLED (完全一致) |
| M05 | 層 1 の exact `str` 固定を外す | predicates 2 node | KILLED (完全一致) |
| M06 | 検査は exact のまま返却だけ元 value | predicates 1 node | KILLED (完全一致) |

M01 / M02 は「禁止したい形を wave 前の実コードが使っていた」ケースの逐語同型変異である。
M03 / M04 は承認外の過剰拒否 (受理集合の縮小しすぎ) を検出する正例側の変異である。
M06 は段 6 レビュー C2 の指摘で追加した。

## 裁定パッケージ (ユーザーへ返した項目)

worklog の `### 次の一手` の新規 4 項が正本。凍結層の NUL gate、正本の受入待ち手 script、
failures fragment の supersede 文法、非 `str` 入力の契約の 4 件。
