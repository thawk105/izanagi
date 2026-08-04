# 段 4 裁定 — [T-244] D121 P4 batch freeze (2026-08-04)

親 = Claude (dev-wave manager)。対象 = s2-plan.md とレンズ 2 本 (s3-lensA.md / s3-lensB.md、
いずれも NO-GO)。

## 裁定: 本 wave では実装しない (4→7→8→9)

段 5・6 を飛ばす。プラン・レンズ所見・本裁定を insight として凍結し、設計択一 5 件 (W1〜W5) を
裁定パッケージとしてユーザーへ返す。実装差分がないため変異 matrix と受入全走は対象外である。

決め手は 3 点:

1. **U-D 裁定 (batch 第一級) の下で、独立 leaf は実装先として誤りになった。** batch は origin
   ledger の第一級 event と裁定済み (worklog (171))。独立 FSM leaf は将来の第一級実装との
   二重実装または非発火 prototype になる (A-09 / B-01 / B-07)。
2. **batch member identity が未裁定で、commitment preimage が決まらない。** distinct wire set
   (最大 32) では採用済み予算 `Q >= 1 + 32R + E_min` の replicate/query slot を表現できず、
   plan 自身が「別裁定が必要」と認めた (A-03 / B-02)。preimage が決まらない以上、
   codec だけの先行実装も golden 凍結も成立しない (A-08)。
3. **凍結境界の DW-G04 に対し、発火する既存 artifact path / 計測 ID を 1 件も書けない** (A-02)。
   D149 (P1) は golden 序列の監査手続きであり、DW-G04 の一般例外を作らない。

これは D147 (P3 差し戻し) と同じ帰結である: 未裁定設計を親の裁量で決めて実装することは
D121 却下案 (b)「未裁定設計の既成事実化」と同型であり採らない。

## 所見別裁定

| 所見 | real/refuted | 採否・処置 |
|---|---|---|
| A-01 (DW-O08 成立・段 1 巻き戻し) | **一部 refuted** | 巻き戻し要求は却下。`DW-O08` 本文の義務は「freeze 族の初期化 = submodule init を最初に行い、未初期化 skip を破損なしと報告しない」であり、brief 起草前 (startup 検査) に履行済み。golden 新設は freeze 族・oracle gate・proof chain の機構に触れない。条件表の trigger 文言と節本文の乖離は real とし、段 8 の改善候補へ。brief に O08 判定根拠が 1 行しかなかった点も real (本裁定で補記) |
| A-02 (DW-G04 迂回) | real | 採用。実装見送り根拠 3 |
| A-03 / B-02 (member identity 未裁定) | real | 採用。実装見送り根拠 2、裁定パッケージ W2 |
| A-04 (事前 commit は外部結果取得に恒真) | real | 採用。leaf 単体で閉じない事実として記録。producer/attestation 層の設計は W1 に含める |
| A-05 / B-04 (partial abort が抜け道) | real | 採用。W4 |
| A-06 / B-05 / B-06 (Kmax authority・class referent) | real | 採用。W5 |
| A-07 (brief の G/E 所有分離欠落) | real | 採用。erratum 2 として記録 (実装しないため実害はないが、brief の並列分割は D149 の順序・所有分離に反していた) |
| A-08 (golden 規範 bytes 未固定) | real | 採用。実装見送り根拠 2 の補強 |
| A-09 / B-01 (非第一級分岐の残置・U-D 矛盾) | real | 採用。実装見送り根拠 1、W1 |
| A-10 (変異候補が DW-M01 未達) | real | 採用。実装しないため登録なし。W1 の実装 wave で単一理由性を満たして再設計 |
| A-11 / B-08 (純増検出力の過大会計) | real | 採用。erratum 3: 検出力は入力点・テスト数でなく独立系譜と fault class で数える (D149)。T-126 系 (member 順序固定・完了前 terminal 拒否・duplicate 拒否) に部分重複があり「全部が純増」は誤り |
| B-03 (二値への早期縮退で evidence 参照喪失) | real | 採用。W3 |
| B-07 (DW-O13 判定・全層 scope) | real | 採用。brief の DW-O13 記載は「member wire 形式が実在 field」までが正で、発火 gate 入力の実在を示さない。全層の所有・順序・受理条件は W1 で構造化して返す |

## 裁定パッケージ (ユーザーへ返す 5 件)

- **W1 (実装先):** P4 batch freeze をどこで実装するか。
  **推奨 = P3 実装 wave (U-A〜U-G 裁定済みで再起票可) の中で、U-D 第一級の batch event /
  reducer として設計・実装する。** P4 は「batch cardinality・全候補の事前 commit・seal までの
  結果非公開」であり、origin ledger の event 文法・予算計数・tombstone と不可分。独立 leaf 先行は
  二重実装と非発火 prototype (D150 決定 (6)(a) の「実装のふりをした非適用」の温床) を作る。
  代案 = pure commitment codec だけ先行 leaf 化 (ただし W2 が決まるまで preimage が決まらない)。
  併せて producer・ledger・driver・consumer (P7)・proof chain の結線順と各層の受理条件を
  P3 実装 wave の設計に含める (B-07)。
- **W2 (batch member identity):** distinct wire set (最大 32) か、query/replicate ordinal 込みか。
  **推奨 = ordinal 込み** — 択一 1 の `Q >= 1 + 32R + E_min` は 32 候補 × R replicate の全 query を
  数える。distinct set では R 回の反復測定を表現できず、cardinality と Q 消費が実 query 数より
  小さく写る (A-03)。
- **W3 (結果の evidence 束縛):** batch member の結果を二値 outcome + 自己申告 class hash に
  縮退させるか、P3 旧設計の `result_ref_sha256` 相当の evidence digest へ束縛するか。
  **推奨 = evidence digest 束縛** — 二値だけでは consumer が結果の根拠を再導出できず、
  proof chain が未裏付け outcome を受理しうる (B-03)。公開 API の二値 alphabet (設計本文 §4③-6)
  は「公開面」の話であり、台帳内部の evidence 保持と矛盾しない。
- **W4 (abort / tombstone):** 早期停止時の残 member の扱い。
  **推奨 = 残 member を tombstone として消費し公開 transcript 長を固定する** (設計本文 §4③-5 の
  既定どおり)。部分結果に条件付けた abort の有無・時刻・terminal kind が結果 bit を運ぶ経路を
  塞ぐ (A-05 / B-04)。
- **W5 (floor / Kmax の authority):** cardinality floor と Kmax を誰が入れ、どの層が計数するか。
  **推奨 = origin-total の計数は P3 ledger、batch 層は authority receipt 由来の policy だけを受理
  (caller 生成 policy の禁止)、class referent の実在・完全性検証は P7 consumer 側の義務として
  明記する** (A-06 / B-05 / B-06)。

## 名乗りの制限 (D147 決定 (3)・D149 と同じ枠)

本 wave が残すのは「P4 の設計材料 (プラン + 敵対所見 + 裁定)」だけである。
「P4 実装」「P4 充足」「P4 prototype」のいずれも名乗らない。P4 は引き続き未充足、
cap-lift は FAIL、`MAX_APPROVED_GENERATIONS = 1` は不変。

## erratum (brief の訂正、履歴として凍結)

- erratum 1: U-A〜U-G は裁定済み (段 2 後に検出、brief 追記済み)。
- erratum 2: brief の並列分割「実装子 1 単位 (leaf + golden + テスト)」は D149 の G/E 所有分離に
  反していた (A-07)。
- erratum 3: 「純増検出力 = 本 wave のテスト全部」は過大 (A-11 / B-08)。
- erratum 4: brief の DW-O13 記載は gate 入力実在の証明にならない (B-07)。
