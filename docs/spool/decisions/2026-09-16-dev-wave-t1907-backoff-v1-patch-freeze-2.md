---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t1907-backoff-v1-patch-freeze
seq: 2
---

## {{D:v1-patch-alias-freeze}}. 別名凍結する v1 patch は式 v2 導入直前の版とし、consumer の配線と bytes pin は足さない

**決定:** D1098 / D1281 の「v1 patch の別名凍結」は、`patches/silo-backoff-fixed.patch` の履歴のうち
**合成枝の式が v2 へ変わる直前の版** (git blob `f7a54445764025112317151106712bb9d97678ab`、
sha256 `35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911`) を、
`patches/silo-backoff-fixed-v1.patch` として bytes のまま保存することで実装する。
旧 consumer を v1 へ配線し直すこと、この file の bytes を pin する検査、`patches/ledger.json` への entry は足さない。

**理由:**
- 起票元 (2026-08-26 の裁定パッケージ A-2) の論点は「合成枝の式が v1 から v2 へ変わった」ことであり、
  その直接の前像がこの版である。`git diff` で v2 との差は式 1 行だけと確認した。
- 旧 static-backoff sweep の 3 WAL を生んだ patch の bytes は WAL にも lock にも記録が無く、生成期 (2026-06-22〜28)
  の初版 `476a128` を選んでも「生成時の bytes」と証明できない。初版は noinline 計器・EVOLVE-BLOCK マーカー・
  `BACKOFF_FIXED` 未供給時の `#error` を含まず、保存する v1 の骨格として不完全である。
- ユーザーの依頼が「対象は既存 v1 の保存に限定する」「仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」と定めた。現行 consumer が旧 campaign へ追記する経路は、現行の campaign identity が
  admission policy を必ず束縛し、policy を持たない旧 lock を照合で拒否するため成立しない (コードの読解)。
- `patches/` 直下の別名は、既存の在庫検査 (define 在庫と `IZANAGI_` token 在庫) の走査対象に自然に入り、
  新しい macro も token も加えないので既存テストの期待値を変えない (焦点走 10 passed、変異 M1 KILLED)。

**却下した選択肢:**
- 初版 `476a128` を凍結する — 旧 WAL の生成期に当たるが、生成時の bytes である証明が無く、骨格も不完全。
- 旧 consumer を v1 patch へ配線し直す — 依頼の「保存に限定」を超え、D1098 の「旧消費者はそのまま動き」を
  実現するには identity の版分けが要る (D1281 が却下した移行の一部を再導入する)。
- 保存 bytes の sha256 を pin するテストを足す — 依頼が scope 外とした。式の改変 (変異 M2) と内容の喪失 (M4) を
  既存テストが検出しないことは、隠さず記録した。
- `patches/` 配下に版別のサブディレクトリを作る — 直下 `*.patch` の在庫検査から外れ、既存の命名慣行とも違う。
