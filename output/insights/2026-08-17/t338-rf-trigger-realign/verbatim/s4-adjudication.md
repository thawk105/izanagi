# 段 4 裁定 — [T-338] RF 発火条件 / pilot 解禁条件の組み直し (2026-08-17)

親が段 2 プランと敵対 2 レンズ (A = 正しさ境界と規律 2、B = 整合と実効性) の所見を
real / refuted・採用 / 不採用・scope 内 / 外へ裁定した記録。両レンズとも総括は NO-GO であった。

## 裁定を決めた実測 (本裁定の中心)

レンズ A 所見 1 が突いた二択 —
「attestation の削除は (a) 評価領域を D282 pin 済み receipt に限れば恒真な重複削除、
(b) 限らなければ D162 発火証拠の受理拡大」— を、現物で解いた。

- D282 の承認 payload は `receipt_schema` を
  `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json`
  (sha256 `d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e`) に pin する。
- 手元の同 file の sha256 は pin と **exact 一致**する (実測)。
- その schema は `definitions/environment` の `required` に
  `attestation_mode` と `attestations` を持ち、`attestation_mode` は `{"const": "required"}`、
  `attestations` は `minItems: 2` の配列である。

**結論: (a) が成立する。** D162 決定 (10) の (ii) の評価領域を D282 pin 済み receipt へ束縛すれば、
attestation を (ii) の列挙から落としても受理集合は 1 mm も広がらない。attestation は
receipt schema 側で引き続き必須だからである。したがって本 wave は **(a) を明示的に固定**する。

副産物として、**D1 は証拠水準の引き下げではなく重複の削除である**ことが確定した。
`892042` が attestation を持たないことは事実だが、(ii) を満たす計測は `892042` ではなく
pilot receipt である (D229 決定 (6))。連鎖を実際に外すのは D2 の側である。

## レンズ A の裁定

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| 1. attestation 削除が恒真削除か受理拡大か未確定 | **real** | 採用 | 決定 (1) に評価領域の束縛を書き、「証拠水準を下げる」という説明を撤回する |
| 2. 残る 3 項は schema 上必須なので恒真、pre-validator では自己申告 | **real** | 部分採用 | 3 項を「存在」でなく「producer の自己申告以外の経路で計測時の実体と照合できること」と定義する。独立 verifier の実装は validator 本体であり本 D の scope 外 |
| 3. P5 の 3 条件が D292 の未定義を先取りし、(b) は D282 で既に確定済み | **real** | 採用 | 3 条件を「非網羅的な実装 backlog。解除の必要条件でも十分条件でもない」へ格下げし、(b) を「D282 pin 済み record-items / schema を強制する producer と semantic validator の実装」へ置換 |
| 4. 本 D 自体が解禁するという攻撃 | refuted | — | 文言を「将来の解除 decision が公表層完了を必要条件としない。現在の状態遷移は無い」へ狭める |
| 5. 「挙動・成果物も不変」は過大 | **real** (非 blocker) | 採用 | 変わる executable output を report の `decision_ids` と台帳採番へ限定して書く |
| 6. 前向き追記が D291 payload bytes を変える経路 | refuted | — | M2 の追認。変更なし |

## レンズ B の裁定

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| 1. land しても実装 wave は進まず、待ちが D292 の解禁 decision へ 1 段ずれるだけ | **部分 real** | 部分採用 | 「解禁は起きない」は real で、決定 (4) に明記する。**「実装 wave が進まない」は refuted** — 次の実装 wave (RF producer + attempt registry) は `pilot_submission` に依存せず、producer を止めていた D162 決定 (11) の閂は 2026-08-05 に [T-479] 択 (b) で解除済みである (archive worklog (199))。この実測を worklog に書く |
| 2. pilot 実走と公表台帳投入を分離する保存条件が不足 | **real** | 採用 | 決定 (3) に保存条項を足す — 追補 P の `requires_addendum_p`、P blob 未承認、p03 未確定、公表台帳への投入禁止は維持 |
| 3. 「D229 (6) を supersede しない」が D1 と衝突して読める | **real** | 採用 | 決定 (6) で分解する — D229 の順序と pilot 計測設計は保存し、D229 の非 supersede 宣言は D229 自身のものであって後続 canonical decision による D162 改訂を禁じない |
| 4. P4 の worklog action は二重在籍を作らない | refuted | — | `見送り` + H4 `研究・計測系` + `base` を維持 |
| 5. D3 の 2 段階化が紛れ込んでいる | refuted | — | 変更なし |
| 6. 「末文」の失効が一意に読めない | **real** | 採用 | 決定 (3) で exact 引用・発効時点・保存範囲を書く |
| 7. M5 の「live consumer は 1 つ」は過大 | **real** (nit) | 採用 | 「D291 の supersession semantics を消費する production consumer は 1 件。固定 ruling を読む generic reader は別にある」へ狭める |

## 親 brief の自己訂正

- **M1 は不正確だった。** 禁止は D291 の状態値と D292 の解除権威にも存在し、
  `addendum_p_freeze_precondition` の末文だけが禁止の実体ではない。段 2 が先に検出した。
- **M5 は過大だった。** レンズ B 所見 7・レンズ A 所見 5 のとおり狭める。
- **(P4) は誤りだった。** `更新` では active ID が二重在籍する。`見送り` が正しい (段 2 が倒した)。
- **(P5) は誤りだった。** 3 条件を完全リストとして書くと D292 が禁じた先行凍結になる。
- (P1) (P2) (P3) は維持する。

## scope と段構成

- 実装差分ゼロを維持する。コード・テスト・schema・凍結 artifact は 1 byte も変更しない。
- したがって `DW-S04` に従い段 5・6 を飛ばし `4→7→8→9` とする。変異 matrix は免除。
- **受入全走は免除しない。**
- scope 外の real 所見: レンズ A 所見 2 が求める「独立 actor による raw からの検証」は
  validator 本体の実装であり、本 wave では実装しない。決定 (5) の backlog へ置く。

## 変異事前登録

実装差分ゼロのため `DW-M01` の変異事前登録は行わない (`DW-S04` の免除条件に該当)。
