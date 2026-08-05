# [T-470] + [T-327] U-1/U-4/U-5 配線 wave — 逐語と変異台帳 (2026-08-05)

起動 admission (U-4 / U-1) と受入 receipt (U-5 / T-470) を必須配線にした dev-wave の凍結記録。
最優先要件は **U-4 = 未登録 ID の実走拒否**。実装 anchor commit は本 wave の
`feat(s8c): 起動 admission と受入 receipt を必須配線にする`。

## 収録物

|file|中身|
|---|---|
|`brief.md`|段 1 brief (scope 4 件、不変条件、前提実測 N1〜N6、provisional 裁定 P1〜P4)|
|`s2-plan.md`|段 2 codex プラン起草 (file:line 粒度)|
|`s3-lensA.md` / `s3-lensB.md`|段 3 敵対相談 2 レンズ (いずれも NO-GO)|
|`s4-ruling.md`|段 4 裁定 = プラン v2 差分。採否・scope・変異事前登録 m01〜m17|
|`s5-unitA.md` / `s5-unitA2.md` / `s5-unitB.md`|段 5 実装子の報告 (起動 gate / consumer test 是正 / receipt)|
|`s6-rev1.md` / `s6-rev2.md`|段 6 敵対レビュー 2 本 (いずれも NO-GO)|
|`s6-fix.md` / `s6-fix2.md` / `s6-fix3.md`|fix 3 巡の報告|
|`s6-refocus.md`|fix 後の焦点再レビュー (所見ごとの closed / partial / regressed 表)|
|`mutation-spec.json` / `mutation-ledger.json`|変異 matrix 本走 15 件|
|`mutation-spec-m13b.json` / `mutation-ledger-m13b.json`|補助変異 m13b (下記 erratum)|

## 変異結果

本走 15 件 + 補助 1 件 = **16 件すべて KILLED、SURVIVED 0 件**。

- 事前登録 node と実赤が完全一致: 8 件 (m01 / m04 / m06 / m07 / m10 / m11 / m12 / m14)。
- 実赤が事前登録の上位集合 (過剰検出): 6 件 (m02 / m03 / m08 / m15 / m16 / m17)。
  期待 node はすべて実赤に含まれる。m03 / m16 / m17 は holdout 表そのものや opt-in gate を
  壊すため、40 / 39 / 36 node が同時に赤くなる。
- **erratum (m13)**: 事前登録では `test_m13_reference_bytes_are_rehashed_not_self_compared` の
  5 param すべてが `_assert_digest` の変異で赤になると書いたが、実測では lifecycle param だけ
  赤にならなかった。lifecycle は全体 hash でなく **prefix hash** (`_assert_prefix_digest`) が
  守っているためで、照準の誤りである。実装の穴ではない。補助変異 **m13b** で
  `_assert_prefix_digest` の比較を自己一致へ倒し、lifecycle param が KILLED になることを実測した。
  初回結果は消さず両台帳を収録する。

`m16` / `m17` は過剰拒否 (承認外の over-reject) を検出する正例で、いずれも期待どおり赤くなった。

## 保証しない範囲 (本 wave が主張しないこと)

- `certifying=true` は構造的に発行されない。C02 の arm injective binding と T-295 approval
  record が無いため、受入 receipt は常に非認証で `non_certifying_reason_codes` が非空である。
- 一回性は単一 repository の共有 lifecycle ledger 内までで、worktree / clone 横断は保証しない。
- registry authority は履歴の一意性までで、approval authority ではない。
- certified 選択の consumer は現 checkout に存在しない。`build_accepted_report` は入口を用意した
  だけで、実 consumer への結線は後続タスクである。
- `s8b_floor_campaign --mode pilot` からの holdout 観測路は本 wave では閉じていない
  (裁定パッケージ U-B)。
