# 段 4 裁定 — [T-139] producer 実装 (dev-wave 2026-08-08)

**裁定: 実装しない。** 段 5・6 を飛ばし `4→7→8→9` とする (`DW-S04`)。
コードとテストは 1 行も land しない。本 wave の成果物は、敵対検証済みの記録項目案と裁定パッケージである。

## 0. 親の誤り (本節を正とする。brief.md は凍結記録として書き換えない)

- **誤り 1 (実装被覆)。** brief §6 と handoff は「実装被覆 0」と書いたが誤り。
  **D229 決定 (7) が既に「0/9 は過大」と訂正済み**であり、`orchestrator/qualification/` の
  試行台帳 (create-only・series-global)・系列 FSM・投入束縛・原子公開・identity が
  記録項目の要求に構造的に対応する (`docs/decisions.md:10761`)。
  正しい主張は「**T-139 固有の public API (`resolve_effective_preregistration` ほか) が 0 件**」であり、
  producer 機構一般の被覆は 0 ではない。両レンズが独立に指摘した。
- **誤り 2 (成果物影響表の条件付き性)。** brief §4 の 6 行は、追補 A・PBS 測定本体・
  publisher 結線・validator caller が揃った**後**の効果である。現時点では pilot 経路自体が存在せず、
  `verify_receipt` の production caller も計画に無い。表は「到達時の効果」と読み替える。
- **誤り 3 (verify_receipt の検出力)。** brief §4 の 6 行目は「別 checkout 測定の混入を検出する」と書いたが、
  実際に検出できるのは「producer が書いた 2 つの文書の食い違い」だけである。
  producer は期待された HEAD を受領証へ書けるため、実測 checkout の一致は証明されない。
  これは事前登録 §15「この gate が保証しないこと」および T-643 (ii) の「完全な偽造検出は見送り」と一致する。
- **`DW-O09` の実測 query を記録する (レンズ A nit 12)。** 実行した検索は
  (a) core path の literal 検索 (`orchestrator/ tools/ hooks/` = 0 件)、
  (b) core digest の literal 検索 (0 件)、(c) `FROZEN_MANIFEST` 収載の確認 (未収載)、
  (d) docs 側の path 検索 (roadmap / decisions / worklog / archive の散文参照のみ)。
  レンズ A・B が独立に再検索して同じ結論を得た。**pin 0 件の結論は支持されるが、これは現在の観測であって
  将来の不変条件ではない。** したがって resolver は F の full SHA を独立定数として持ち、毎回 F の blob を読む。

## 1. 所見の裁定 (real / refuted)

**両レンズ計 15 blocker + 6 must-fix + 1 nit を、親は全件 real と裁定する (refuted 0 件)。**
重複を統合すると独立な blocker は 11 件である。

| # | 所見 (統合後) | 出所 | 裁定 |
|---|---|---|---|
| B1 | 凍結 core の内部矛盾 — §14 の表は `a01`〜`a13`、§15 の gate と正例は `a01`〜`a12` | A3 / B1 | real・**ユーザー裁定へ** |
| B2 | D234「実装境界」と事前登録 §11 の段順序 (A→pilot→C) の衝突 | A7 / B2 | real・**ユーザー裁定へ** |
| B3 | 追補 A の値契約が空 — exact-key だけでは時間表・待機・driver 引数・`J`・`q`・alpha を固定できない | A1 / B5 | real・追補 A 待ち |
| B4 | a03 の恒真化を静的 resolver では防げない (定数指標・常に通る有限範囲) | A2 / B5 | real・段 C の再計算が要る |
| B5 | PBS 測定本体が追補 A 依存で書けず、前置・sink・registry だけ land すると「producer 実装済み」の誤記録になる | A4 / B4 | real・**本裁定の決め手** |
| B6 | 認可 sink の位置が誤り — 受領証を実際に書く `publish_raw_receipt` が binding を受けていない | B3 | real・次 wave の設計訂正 |
| B7 | 追補 A の study-wide な一回限り束縛が無く、pilot 1 の後に A2 へ差し替えられる | B6 | real・次 wave の設計 |
| B8 | 失敗 qsub / job 側 preflight reject を raw に残す authority と collector が無い (§13 否定検査 1 が閉じない) | B7 | real・次 wave の設計 |
| B9 | 受領証 schema から trace-enabled / trace-disabled の分離を再計算できない (絶対規律 1) | A6 | real・記録項目案で是正済み |
| B10 | preflight の source authority が未定義 — helper 1 枚だけを commit blob から実行しても、import される resolver が live worktree なら束縛されない (T-609 で実際に起きた欠陥の同型) | A5 | real・次 wave の設計 |
| B11 | 段 A 帰属の変異 6 件のうち 4 系統で単一理由帰属が不成立 (`DW-M01` / D190) | B8 | real・実装時に再照準 |

must-fix (A8 schema の条件付き制約不足、A9 過大主張、A10 downstream 禁止の欠如、A11 被覆、B9 テストの実効性、B10 純増の混同) はすべて real とし、
A9・A11・B10 は §0 で訂正済み、A8・A10・B9 は記録項目案と次 wave の scope へ反映した。

## 2. 「実装しない」の理由

1. **入力が存在しない。** 測定本体は追補 A の `a01`〜`a09` (時間予算・待機・driver 引数・arm identity・
   schedule seed) に依存する。これらは未確定であり、本 wave の scope 外である。
   測定本体なしに前置・sink・registry を land すると、台帳だけが「producer 実装済み」へ進む
   (`DW-G05` の逆、レンズ A・B が独立に blocker と判定)。
   worklog (305) の [T-139] 次の一手も **「次は追補 A → producer 実装 → pilot」**と記録している。
2. **凍結事前登録の内部矛盾は親が解けない (B1)。** `a01`〜`a12` と `a01`〜`a13` は exact-key のため
   **互いに素**であり、包含関係にない。どちらを採っても受理集合が動く。`a12` 読みは primary alpha 未固定の
   pilot を許し (規律 3 に抵触)、`a13` 読みは凍結 §15 が明示する正例を拒否する。
   **これは 2026-08-07 の裁定時点で未見の新事実である** — 裁定文にも worklog にも記録が無い。
3. **記録項目の確定は単独の裁定 gate である。** D229 決定 (7) の直前が
   「記録項目の確定を単独の裁定 gate にすることで緩和する」と定め、事前登録 §11 段 A も同じ。
   T-643 は (i) 認可の第一境界と (ii) trust root の 2 問を裁定したが、**記録項目そのものは裁定していない**。
4. **D234 の平明な読みを親が狭めない (B2)。** D234 実装境界は validator・consumer・投入 script まで
   producer 実装 wave の責務と逐語で書く。事前登録 §11 と D162 決定 (10) は逆の順序を要求する。
   親が片方を選ぶのは決定の非同値な読み替えであり、`DW-S04` が禁じる。

**代わりに実装しないと決めなかったもの:** 追補 A が無くても書ける部分 (resolver 単体) も検討したが、
B1 が resolver の exact-key 集合そのものを未決にするため、narrow slice でも完成しない。

## 3. 本 wave が納品するもの

1. **記録項目 (受領証 closed schema) の案** — 敵対検証済み。裁定 gate へ提出する形にする。
   B9 (trace / perf 分離)、A8 (条件付き制約)、A10 (evidence-only の明示) を反映する。
2. **裁定パッケージ 4 問** (B1、B2、記録項目の承認、次 wave の vertical slice 境界)。
3. **次 producer wave の vertical slice 定義** — 半実装を防ぐ切断点。
4. 親の誤り 3 件の訂正 (§0)。

## 4. 変異事前登録 (`DW-M01`)

**実装差分がゼロのため変異 matrix は射程外である。**
ただし [T-642] の裁定 (2026-08-08) に従い、**受入全走は走らせる** —
docs のみの wave でも `test_check_docs` / `test_spool_fold` が実 repo を読むため検出力がある。
(`docs/dev-wave/core.md` の `DW-S04` 本文は射程改訂が未実装のままだが、裁定の実質に従う。)

B11 の再照準案は次 wave のために記録し、本 wave では登録しない (登録対象の実装が無いため)。
