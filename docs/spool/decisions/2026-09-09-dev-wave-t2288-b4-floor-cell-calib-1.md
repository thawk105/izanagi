---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2288-b4-floor-cell-calib
seq: 1
---

## {{D:b4-floor-workload-keying-is-d15-conformant}}. 凍結 spec の calibration↔cell workload 一致要求は D15 準拠の正しい gate であり、緩めない

**決定:** `floor_pair_driver` の `_bind_checkout_inputs` が cell ごとに課す
`calibration.workload != dict(perf.workload)` 拒否は**欠陥ではなく、維持する**。
到達可能性 (既存の accepted calibration 1 件で複数 workload の spec を作れること) を理由に
この一致要求を外す案は採らない。より狭い変種 (calibration の workload が cell workload 集合の
いずれかと一致することだけを要求する形) も採らない。

**理由:**

- D15 が同じ案を明示的に却下している。却下欄の逐語は「D13 の『入力完全非依存』を維持し
  単一 calibration で済ませる: 飽和点が skew 依存と実測で割れた以上、虚偽。代表 workload 署名で
  分けるのが honest」である。D15 は calibration を (env, thread, 代表 workload) でキーすると決め、
  出力を workload 署名付きファイル名へ分ける実装まで採用している。
- 一致要求を外す案の論拠は「calibration が保証するのは records 飽和と環境であって workload 混合では
  ない」だった。これは成り立たない。登録済み calibration は `saturated=false` /
  `lower_bound_selected=true` で、選択根拠は実測 `maxrss` が L3 の 4 倍を超える最小 N である。
  `maxrss` は table 初期化個数だけで決まる定数ではなく、workload 実行後の process peak RSS である。
  read は値を deep copy し、write は新しい payload を確保し、RMW は両方を行うので、
  rratio・rmw・max_ope はいずれも resident peak に効く。
- 一致要求は「records に効く key だけ」へ縮約できない。skew はアクセス分布と miss 率系列を変え、
  rratio は READ/WRITE を選び、rmw は blind write と read-copy-write を切り替える。
  records に効かないと証明済みの workload key は存在しない。
- 外した場合の受理集合の拡大が実害を持つ。`calibration/v2` は workload を任意の `dict[str,str]`
  として受理し、exact な YCSB key 集合も非空性も要求しない。cell 側の exact 3-key 比較が
  唯一の拘束であり、それを外すと `workload={}` や異種 key の accepted calibration でも
  `records` が偶然一致すれば別 workload の cell を通せる。
- 絶対規律 2 の向きに反する。「到達可能性のために正しさゲートを緩める」変更である。

**却下した選択肢:**

- **workload 一致要求を外す** — 上記のとおり D15 が却下済みで、論拠も成り立たない。
- **calibration の workload が cell workload 集合のいずれかと一致することだけを要求する** —
  現行より狭い受理集合ではあるが、cell 自身の workload の校正を証明しない。規律 4 (レコード数が
  小さすぎると many-core の cache 競合が再現されず測定が楽観的に歪む) の充足を未証明のまま残す。
- **b10 の先例に合わせる** — b10 の formal run provenance は 3 workload すべてに同一 calibration を
  束縛し、束縛 field に workload を含めない。しかし同 provenance の `official_certification` は
  `false` である。certified でない実装先例は、B-4 の certified 受理集合を広げる権威にならない。
- **事前登録 §5 の校正済み `PerfConfig` 欄が単数であることを根拠にする** — 同欄は path と hash を
  置く 1 セルであるだけで、意味上の個数を 1 件に固定していない。同欄の解除条件は
  「calibrator が決めた値へ差し替えるまで記入しない」であり、文書のレイアウトから
  校正の個数を導くのは誤りである。

**限界 (主張せず明記する):** 本決定は「balanced の calibration を rr5 / rr95 の cell に使えない」ことを
言うだけで、rr5 / rr95 の飽和点や下限がどこにあるかは何も言わない。それは calibrator の実測事項である。

## {{D:b4-floor-cellset-not-expressible-in-one-spec}}. D1641 の凍結セル集合は現行設計では 1 spec に表現できない — 3 案とも既裁定に阻まれるので実装せず裁定へ返す

**決定:** D1641 が凍結したセル集合「3 workload × contention セル」と、保守側最大の対象集合
「凍結したセル集合 × 2 時間窓の全部」を **1 spec・1 成果物で測ることは、現行設計では不可能**である。
この事実を記録し、**本 wave ではコードを変更しない**。解消の 3 案はいずれも既裁定に阻まれるため、
択一をユーザー裁定へ返す。

原因は 2 つの組合せである。(a) D15 が calibration を (env, thread, 代表 workload) でキーすると
決めている。(b) 凍結 spec は `provenance.calibration` を 1 件しか持たず、`_bind_checkout_inputs` が
その 1 件を全 cell へ照合する。したがって 1 spec の cells は同一 workload しか持てない。

**理由:**

- **案 A (cell ごとに calibration を束縛する) は D1696 が禁じている。** 同決定は「測定前の
  follow-up wave で schema と validator を拡張する案は採らない」と定め、人手責任として残した 9 項目に
  「§5 のセル集合との一致」を含める。再訪条件 (人手の確認が実際に見落とした項目が 1 件でも出たとき) は
  未成立である。加えて DW-G04 の発火 artifact が無い — rr5 / rr95 の accepted calibration が 0 件なので、
  cell ごとに別 workload の calibration を束縛する spec を実 artifact で構成できない。
  issuer が `workload_identifier` を集合集約で作っていることは案 A を示唆するが、示唆は発火 artifact の
  代わりにならない。
- **案 B (workload ごとに 3 spec、3 成果物) は現行コードのまま表現できるが、下流に規則が無い。**
  事前登録 §5 の floor 欄は `artifact_path=<repo relative>; sha256=<lowercase hex64>` の pin 1 件を
  受ける文法であり、3 成果物の保守側最大をどう 1 件へ集約するかを定めていない。集約規則の新設は
  事前登録本文に関わるので D1383 により AI が既成事実にしない。
- **案 C (workload 一致要求を外す) は {{D:b4-floor-workload-keying-is-d15-conformant}} で不採用。**
- **D1696 の前提が成立していないことが新事実である。** 同決定は「§5 のセル集合との一致」を凍結 spec を
  書く人間の責任として残したが、それは spec がその一致を**表現できる**ことを前提にしている。
  実際には表現できない。人間が見落としたのではなく、書けない。この 1 点は再訪条件の文言
  (人手の確認が見落とした) には当たらないので、条件の自動成立とは扱わずユーザー裁定へ返す。
- **裁定に依存しない前進が 1 件ある。** rr5 / rr95 の accepted calibration は案 A でも案 B でも
  必要であり、D1641 決定 2 が測定を認可済みで操作は AI 委任である。calibrator の走行は
  ユーザー裁定を待たずに始められる。

**却下した選択肢:**

- **案 A を実装して裁定を後追いにする** — D1696 の明文に反し、発火 artifact も無い。
  利用できない受理集合だけが広がる。
- **案 B の集約規則を AI が起草して §5 へ書く** — D1383 と事前登録 §11 が「誰がどの証拠で
  floor 欄を発効させるかはユーザーが決める」と定めている。
- **本 wave を「blocker 解消」として記録する** — 実際には spec を構成できないので、
  利用不能な発行経路を利用可能と誤記することになる。
