# 段 1 brief — [T-244] P3 分割の次弾: U-4 候補数と member 行数の分離

前提実測は同 directory の `parent-measured.md` (M1〜M7)。すべて本 checkout の一次資料。

## scope の選定 (依頼の二択に対する親の判断)

依頼は「report v3 か origin-proofs sidecar (U-4)」の二択だが、**どちらもそのままでは実装できない**。
M1 により ledger に production consumer が無く、sidecar の batch/seal/authority field を埋める
実 artifact path が存在しない (`DW-G04` の発火 gate 不成立)。report v3 は sidecar への参照なので
同じ理由で成立しない。

よって本 wave は、この分割項のうち**今 fireable な核である U-4 の記録形分離だけ**を scope とする。
sidecar 本体と report v3 は「wiring 待ちで実装不能」として裁定パッケージへ返す。

## scope (in)

1. **member 行数と候補数を別 field として記録する。** ledger が `BatchSealed` 受理時に
   開示された候補平文から候補数を計算し (M3、自己申告にしない)、公開面へ載せる。
2. **公開面の `cardinality` 名を member 行数と分かる名前へ改める。** 対象は event dataclass /
   payload key / `OriginSnapshot` / policy field / 拒否理由文字列。(P2)
3. **候補数 1 の記録を「候補 2 点以上の証拠」として受理させない gate を、既存発火路に載せる。** (P1)
4. 新しい D (D96 の同一変更単位) と境界テストを同じ commit に含める。

## scope (out)

origin-proofs sidecar / report v3 / completeness / critic 後置 (U-8) / ever-issued cell 台帳 (U-3) /
production provisioning / authority entry の追加。いずれも別 wave か裁定待ち。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 「受理不能」は `QueryFloorConstraint` へ候補数の下限を足し、`OriginSealed` 受理時の
  既存 floor 検査枝で拒否する形にする。**代替**: (a) `BudgetPolicy` に seal ごとの
  `distinct_candidate_min` を置く (b) 記録するだけで拒否しない。(b) は U-4 の要求を満たさない。
- **(P2)** `cardinality` を member 行数の名前へ改名する。**代替**: 改名せず field を足すだけ。
  改名すると独立 golden と拒否理由の literal を広く更新する。
- **(P3)** D189 に倣い schema ID / domain / runtime path の版は上げない (M7 で前提が成立)。
- **(P4)** 段 2/3 を省く軽量版にはしない。受理集合が変わり、正しさ防壁 (P4 証拠の受理) に触るため。

## 不変条件

- **I1** `reflux_origin_authority_v2.json` を変更しない。`origins` は `[]` のまま。
- **I2** production provisioning を解禁しない。production 初期化禁止は不変。
- **I3** **現行の受理集合を既定で狭めない。** 単一候補 × R replicate の batch は、authority が
   明示的に候補数下限を要求した場合を除き、従来どおり受理できること。
- **I4** 候補平文・salt を新しい公開面へ漏らさない。載せるのは数だけとする。
- **I5** 検査を恒真にしない。候補数を誤って member 行数で埋める実装が**赤くなる負例**を必ず置く。
- **I6** D114 の cap=1、D166 の P4 FAIL、P3 FAIL は不変。

## 成果物影響 (`DW-G05`)

実装しない場合、将来の P4 / 軸 (iii) consumer が member 行数 (`cardinality` /
`sealed_queries`) を候補数と読み、**単一候補 × R replicate の記録を「候補 2 点以上の batch」として
証拠に受理しうる** (M4 でこの誤認が現に成立することを確認した)。
certified 選択・材料レポート・試行台帳・proof chain の**現在値と参照は不変**である
(production entry 0 件、tracked な出力 bytes 無し。M2/M6)。

## 名乗りの上限

名乗ってよいのは **ledger の記録形における member 行数と候補数の分離、および authority が要求した
場合の候補数下限の強制**まで。**名乗らない**: P3 / P4 充足・軸 (iii) anti-oracle・
origin-proofs sidecar・report v3・completeness・U-1〜U-3 の完了・物理 query 数の証明・
production provisioning・certified 選択・cap 引上げ。

## 成果物の形

`orchestrator/campaign/reflux_origin_ledger.py` の変更 +
`orchestrator/tests/test_reflux_origin_ledger.py` の境界テスト + 新 D + worklog fragment。

## 分割方針

編集面が 2 file で、実装と境界テストが同一 file 群を触る。**実装子は 1 単位**とし並列分割しない。
段 3 の敵対相談と段 6 のレビューだけを 2 レンズ並列にする。
