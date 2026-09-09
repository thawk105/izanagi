# 段 4 裁定 (起草。レンズ B 反映前) — [T-2288]

## 結論: 実装しない (4 -> 7 -> 8 -> 9)

3 案すべてが既裁定に阻まれる。コード差分 0 で記録と裁定パッケージだけを成果物とする。

## 択一の再裁定

### (γ) calibration の workload 一致要求だけを外す — **不採用**

段 2 plan が選び、親 brief も (P1-a) で有力と見た案。**レンズ A が反証し、親が一次資料で確認した。**

D15 (`docs/decisions.md` の「D15. calibration: 飽和点が無い workload には下限基準を使う /
飽和点は workload (skew) 依存」) の却下欄に逐語でこうある。

> **D13 の「入力完全非依存」を維持し単一 calibration で済ませる**: 飽和点が skew 依存と実測で割れた
> 以上、虚偽。代表 workload 署名で分けるのが honest。

D15 は calibration を **(env, thread, 代表 workload)** でキーすると決めており、出力を
workload 署名付きファイル名へ分ける実装まで採用している。したがって現行 driver の
`calibration.workload != dict(perf.workload)` 拒否 (`floor_pair_driver.py` の cell 照合ループ) は
**D15 に整合する正しい gate であり、欠陥ではない**。親 brief の「repo の先例と整合しない」という
判定は誤りだった。

- b10 の先例は権威にならない。親が実測: `b10_backoff_shape_provenance.json` の
  `official_certification` は `false` である。certified でない実装先例で B-4 の受理集合を広げられない。
- 規律 2 に照らすと、(γ) は「到達可能性のために正しさゲートを緩める」向きである。**採らない。**
- レンズ A が挙げた (γ') (calibration workload が cell workload 集合のいずれかと一致することを要求) も、
  rr5 / rr95 の cell 自身の校正を証明しないので最終解にならない。同じ理由で不採用。

### (β) cell ごとに calibration を束縛する — **不採用 (本 wave では)**

D15 と D1641 を同時に満たす設計はこれである (issuer の `workload_identifier` が集合集約であることも
この形を示唆する)。しかし **D1696 (2026-09-07、ユーザー裁定、推奨どおり) が明示的に禁じている。**

> 測定前の follow-up wave で schema と validator を拡張する案は採らない。
> **再訪条件 = 人手の確認が実際に見落とした項目が 1 件でも出たとき。**

D1696 が人手責任として残した 9 項目には「**§5 のセル集合との一致**」が含まれる。再訪条件は未成立。
加えて DW-G04 の発火 artifact が無い — rr5 / rr95 の accepted calibration が 0 件なので、
cell ごとに別 workload の calibration を束縛する spec は現時点で構成できない。

### (α) workload ごとに 3 spec -> 3 成果物 — **不採用 (本 wave では)**

現行コードのままで表現できるが、事前登録 §5 の floor 欄は pin 1 件を受ける文法
(`artifact_path=...; sha256=...`) であり、3 成果物の保守側最大をどう 1 件へ集約するかの規則が無い。
集約規則の新設は事前登録本文に関わるので D1383 により AI が既成事実にしない。

## 真の詰まりと、D1696 に対する新事実

D1641 が凍結したセル集合「3 workload × contention セル」と、保守側最大の対象集合
「凍結したセル集合 × 2 時間窓の全部」を **1 spec・1 成果物で測ることは、現行設計では不可能**である。
原因は D15 の workload ごとの calibration キーと、凍結 spec が calibration を 1 件しか持たないことの組合せ。

**これは D1696 に対する新事実である。** D1696 は「§5 のセル集合との一致」を凍結 spec を書く人間の
責任として残したが、それは spec がその一致を**表現できる**ことを前提にしている。実際には表現できない。
人間が見落としたのではなく、書けないのである。よって D1696 の再訪条件の文言 (人手の確認が見落とした)
には当たらないが、前提が成立していない。**この 1 点をユーザー裁定へ返す。**

## 段 3 所見の裁定

| 所見 | 判定 | 扱い |
|---|---|---|
| A: D15 が単一 calibration を虚偽として却下済み | **real** | 採用。(γ) を不採用にした決定的根拠。親が D15 を一次資料で確認 |
| A: maxrss は workload 実行後の peak RSS であり table サイズ定数でない | **real** | 採用。(γ) の論拠「working set は workload 非依存」を崩す |
| A: `noise_floor.cv` は within-run であり between-run floor の代用でない (D1639) | **real** | 採用。ただし本 wave は floor 値を扱わないので影響は記録のみ |
| A: 規律 4 の充足 (rr5 / rr95 で L3 下限を満たす) は未証明 | **real** | 採用。rr5 / rr95 の calibrator 走行が要る根拠 |
| A: (γ') が実在し (γ) より狭い | **real** | 採用。ただし最終解でないので採らない |
| A: (γ'') は成立しない (records に効かないと証明済みの workload key は無い) | **refuted 側で一致** | 採用 (案として不成立) |
| A: 偶然 records が一致する任意 workload の再利用が通る | **real** | 採用。(γ) 不採用の補強 |
| A: calibration/v2 の workload は任意 `dict[str,str]` で、cell 側の exact 3-key 比較が唯一の拘束 | **real** | 採用。(γ) は最後の拒否を消すという指摘は正しい |
| A: 2 window 間の calibration 差替えは spec hash で塞がっている | **refuted (穴なし)** | 採用。既存 fail-closed の確認 |
| A: 拒否 2 行を説明 2 行へ置換する文面は D1374 型の過大表示 | **real** | 採用。実装しないので発生しない |
| A: D1641 / §5.1 の校正済み `PerfConfig` 条件を緩める | **real** | 採用 |
| A: §5 の単数欄から「1 calibration でよい」は導けない | **real** | 採用。親 brief の推論の誤りを認める |
| A: D1060 の向きと逆 (既存値を到達可能性の理由で権威へ昇格) | **real** | 採用 |
| A: D1696 は workload gate の削除を認可していない | **real** | 採用 |
| A: D1759 の producer 版境界の潜脱 (summary/v3 の受理 domain が入れ替わる) | **real** | 採用。実装しないので発生しない |
| A: D1377 / floor §5.1 の直接緩和は無い | **refuted (穴なし)** | 採用 |
| A: b10 は workload を束縛していないが provenance の key 欠落だけでは証明にならない | **real** | 採用。親が `official_certification=false` を実測して補強 |
| A: registered/unique calibration は 2 件で両方 rr50/t48 (表現修正) | **real (表現修正)** | 採用。「accepted file 2 件」ではなく「registered な unique calibration 2 件」と書く |
| A: resolver 配線と sentinel 挙動は親の主張どおり | **real (親の主張を支持)** | 採用 |
| 段 2: 親の行番号 3 箇所の誤り (`_bind_checkout_inputs` は 1122-1194、cell loop は 1181 開始、`_derive_identity` は 737-814、schema pin test は 629-633) | **real** | 採用。記録へ反映 |
| 段 2: 親の「209 node」は陳腐化、正しくは 210 | **real** | 採用。親が台帳で 210 件を独立確認 |
| 段 2: issuer docstring の `759-776, 1136-1147` は既に誤り | **real** | 採用。**ただし本 wave では直さない** (実装面差分 0 の裁定と両立させる。次タスクへ回す) |
| 段 2: 受入所要台帳を更新する | **不採用** | 親が実測: `conftest.py` は `nodeid_count != len(durations)` のときだけ台帳を破棄する fail-soft。実装しないので台帳も触らない |

## 変異事前登録

**実装面 (D95 決定 2) の差分が 0 なので DW-S04 により変異 matrix を免除する。** 受入全走は免除しない。

## 成果物

- worklog fragment (spool)。
- decisions fragment: 「現行 driver の workload 一致要求は D15 準拠であり欠陥ではない」と
  「D1641 のセル集合は現行設計で 1 spec に表現できない」の 2 点。
- failures fragment: 親が非 certified 先例 (b10) と文書レイアウト (§5 の単数欄) を根拠に、
  既裁定 (D15) が却下済みの受理集合拡大へ向かった near miss。防いだのは段 3 の敵対相談。
- insight dir: 一次資料 (brief v1 破棄の経緯、plan、レンズ A・B、本裁定)。
- 裁定パッケージ: 上記 3 案と D1696 の前提不成立。
- 次タスク: rr5 / rr95 (t=48, pegasus) の calibrator 走行。D1641 決定 2 が認可済み・操作は AI 委任。
  案 A・案 B のどちらでも必要。
