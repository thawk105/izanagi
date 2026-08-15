# 段 4 裁定 — [T-338] Q11 独立 validator (2026-08-16)

`authority: none` / `default_effect: no-state-change`

段 2 プラン (`verbatim/s2-plan.md`)、段 3 レンズ A (正しさ境界、`verbatim/s3-lensA.md`)、
段 3 レンズ B (NO-GO 破壊、`verbatim/s3-lensB.md`) の所見を real / refuted、採用 / 不採用、
scope 内 / 外に裁定する。

## 主裁定

**実装しない。** `4→7→8→9` とし、段 5・6 を飛ばす。実装差分ゼロのため変異 matrix は
`DW-S04` の免除条項の対象。受入全走は免除しない。

根拠は 3 つで、いずれも一次資料で親が検算済みである。

1. D162 決定 (10) の発火条件は連言であり、(ii)(iii) が不成立 (`trigger-audit.md`)。
   `DW-G04` は「発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ実装する。
   書けなければ設計メモに留める」と定める。
2. D229 決定 (6) が着手順序を `producer → pilot → validator/consumer → 本走` に固定し、
   「9 層 vertical slice を原子的に許可」も「D162 決定 (10) を明示的に書き換える」も却下済み。
3. 依頼が除外した [T-339] scope に、Q11 推奨 3 が RF calculator と schedule validator を
   明示的に置いている。validator の中核は依頼が実装するなと言った側にある。

## 所見の裁定

### real・採用 (裁定パッケージと worklog へ反映済み)

| # | 所見 | 裁定 |
|---|---|---|
| A1 / B6 | 後発裁定は 2 件でなく、D264 / D282 / D291 / D292 も拘束する。D229 の決定番号も取り違え | **real・採用。** README と worklog を訂正した |
| A2 / B3 | 「RF 実装 0」の一般化が過大。再利用可能部品 (D282 parser、receipt schema、T-126 台帳・FSM・投入束縛・原子公開・identity) は実在 | **real・採用。** 「RF calculator と consumer が 0」へ限定した |
| A3 / B4 | J は「規則」(D282 が digest 凍結済み) と「選択済み J」(未存在) を分けねばならない | **real・採用。** 親 brief の (P2) を訂正した。これは依頼の第 2 要求 (J 禁止のテスト固定) の可否に直結する |
| A4 | J の事後追加は 4 経路で迂回できる。再起票条件だけでは塞げない | **real・採用。** 下記「必須 kill として事前登録する変異」へ固定した |
| A5 / B6 | 「pilot 投入不可」は規範状態であり機械 gate ではない | **real・採用。** 根拠を decision 側の運用状態 block へ差し替えた |
| B1 | (i) の証拠は `892042` だが、別計測の attestation を合成してはならない | **real・採用。** `trigger-audit.md` に明記した |
| B2 | 「実装可能 slice 0 件」は広すぎる。権威を持たない producer / 台帳前段は D229 が禁じていない | **real・採用、ただし scope 外。** 依頼が除外した [T-339] 前段であり、本 wave では実装しない。択一 A の「次の一手」として返す |

### refuted

| # | 所見 | 裁定 |
|---|---|---|
| A6 | 恒真 gate と報告値の裏口について、段 2 の却下判断は妥当 | **refuted (= 問題なし)。** 段 2 は Fieller と ratio projection の二重比較 (D229 決定 (3) により恒真)、producer 申告 J と producer 選択 slot 数の一致、blob digest だけの一致、fixture だけの純関数、拒否枝しかない adapter、producer decision の持ち回りを、いずれも明示的に却下している |
| A7 | 「実装しない」ことで今すぐ失われる、安全に land 可能な RF 防御は無い | **refuted (= 見送りによる防御の喪失なし)。** 現行の適格性 field は entry-local な負制約として実際に検査されており、producer 自己申告から正例へ昇格する経路は存在しない。したがってコードを置かなくても受理集合は不変である |

## 必須 kill として事前登録する変異 (将来の validator wave が発火時に kill すること)

D229 決定 (8) が既に 3 件 (失敗した投入を台帳と raw の双方から落とす / 新しい親系列 ID を自己申告して
累積有意水準をリセットする / anomaly を clean と申告する) を必須 kill として置いている。
本 wave は、レンズ A 所見 4 が挙げた **J の事後追加に特化した 4 経路**を追加する。

1. 不利な系列を捨て、新しい `parent_series_id` / `family_root` を自己申告する。
2. pilot の raw を見た後に erratum を「本走前」として追加する
   (新 erratum は新 study を要求し、旧試行を保持することまで検査しなければならない)。
3. 不利な pilot receipt を発行せず、新しい study / slot 空間で pilot を再走する。
4. 同一 allocation・node・時間窓を複数 cluster ID へ分割する、または block を cluster へ読み替える。

いずれも「不利な試行を台帳と分母から消す」か「独立標本数 J を水増しする」方向に働き、成功すれば
正例の `not_certifiable` が `partial_recovery` へ反転して certified 選択・材料レポートの J・
全 attempt 参照・proof chain が変わる。**本 wave はこれらを実装しない** — 発火条件が揃うまで
実装しないという裁定に従い、事前登録として記録するだけである。

## 規律 2 の扱い

依頼は「再計算が一致しないときは fail-closed で判定不能にし、報告値を採る経路を残さないこと」を
求めた。本 wave はその経路を実装しないため、**報告値を採る経路を新設していない**。
現状は RF を消費する経路そのものが 0 件であり、producer 自己申告から正例へ昇格する経路は存在しない。
すなわち規律 2 は「緩めなかった」のではなく「緩める対象がまだ無い」状態のままである。

## [T-339] との境界 (worklog へ明記する)

本 wave が**実装しなかった**もの (= [T-339] 側に残るもの):

計測 producer / attempt registry / schedule validator / RF calculator / [T-337] の適格性権威 /
層 3 の次版 (`trial × candidate × workload × contrast` を key とする別区画) /
selector・材料レポートの consumer / 双射・変異検査。

本 wave が**確定させた**もの: 発火条件の項目別現況 (i 成立 / ii iii 不成立)、
実装候補 6 件の却下理由、J の「規則」と「選択済み値」の分離、J 事後追加の 4 必須 kill 変異。
