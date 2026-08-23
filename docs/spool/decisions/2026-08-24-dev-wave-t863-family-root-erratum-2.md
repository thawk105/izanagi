---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t863-family-root-erratum
seq: 2
---

## {{D:t863-family-root-erratum}}. 公表 core v2 §8.1 の family_root 偽命題を限定訂正する

**決定:** 公表 core v2 §8.1 がいう「`family_root` が primary 系列と同じ commit である」は
偽である。次の記号を用いる。

```text
P = 88d68f9127b31df5aafc3d59607896626a1652e8
A = dce4ae4fed6f4fb33747165c5b92c16d01822850
I = individual_publication
R = alpha_reservation
```

公表側の根は `P`、primary 実台帳の根は `A` であり、`P != A` である。したがって §8.1 の
命題 `P = A` は、conformance、適合報告、proof chain の根拠に使ってはならない。この限定訂正は
`P` 自体を公表系列の根または D291 の `source_core.commit` の provenance として参照することを
禁じない。

公表 entry 空間と primary entry 空間の互いに素性は `(root, kind)` で成立する。任意の正整数
`n, m` について、`n = m` の場合を含めても `(P, I, n) != (A, R, m)` である。この量化は
ordinal の受理・発行を授権せず、数値 ordinal が常に異なるとも主張しない。共有しないのは
ordinal namespace と entry identity である。公表台帳が 0 byte でも、固定 literal と canonical
path の束縛が `(P, I)` を同定する。

**D291 の保存境界:** 本決定は D291 全体を supersede しない。次をすべて保存する。

- `approved_blobs` の 2 role と 2 承認三つ組:
  - `publication_core` =
    (`output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md`,
    `66934dda7f28893110a64a2011e213c2bda5e821`,
    `ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67`)
  - `source_addendum_b` =
    (`output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md`,
    `25a66d2042a4fff1021e033c23fc2b814a735de9`,
    `ad12b60d29bb94ff67c3302b0779cb4765cd1c77768149d7cf6587698febb048`)
- `document_relations` の 3 role を含む節全体の exact 一致、`exact_closure`、p01 / p02 の
  承認値と比較単位。
- D291 の fold trust root `F_p = b13b7ea840ad51199f40b3a534c9d1cdb422af2e`。
- 2 文書の `authority: none` bytes と、承認 authority を D291 が持つ境界。

これは blob approval の失効・更新・再承認ではなく、承認済み bytes 内の命題 `P = A` だけに
対する後続解釈の限定 override である。本決定は予約手続きの第三の authority ではない。予約の
authority を公表 core v2 の §8.1 / §8.2 と追補 P だけから解決する既存境界を保存する。

**operational boundary:** 本決定は、R2 の予約原子性、cross-worktree 一意性、予約 writer、
公表機構を完成・変更・授権しない。既存 validator、resolver、producer、consumer、受理集合、
固定 root / kind、両台帳の内容も変更しない。D291 の `pilot_submission = forbidden`、
`main_submission = forbidden`、`source_main_run_gate = not_implemented` はそのままである。
空の公表台帳を正例として読めることは、entry 追加や ordinal 発行の権限を意味しない。

**理由:** 実在する公表台帳 identity は `(P, I)`、primary 台帳の ordinal 1 entry は `(A, R, 1)`
であり、承認済み文書の `P = A` と両立しない。偽命題を残したままにすると、将来の consumer が
実台帳と矛盾する同一 commit を proof chain の根拠として適合報告へ取り込みうる。一方、承認文書を
編集すると D291 が承認した exact bytes ではなくなるため、canonical decision で命題の使用だけを
限定する。公表根 `P`、primary 根 `A`、公表 core の承認 blob commit `66934dda...`、D291 の fold
trust root `b13b7ea8...` は別の役割であり、相互に読み替えない。

**却下した選択肢:**

- 承認済み公表 core を直接編集する — D291 の exact-byte authority を失う。
- 公表根または primary 根を書き換えて同じ commit へ寄せる — 実台帳の provenance を改変する。
- `P` の利用を一般に禁止する — 公表根と `source_core.commit` という正当な役割まで失効させる。
- 本決定を予約 authority や ordinal 発行根拠にする — 公表 core v2 の閉じた予約 authority 境界を破る。
- 数値 ordinal の不一致だけで互いに素性を説明する — 両 namespace に同じ数値が存在する場合を扱えない。
- R2 原子性、予約 writer、公表機構も同時に実装する — 本訂正から独立した未完了面であり scope 外である。
