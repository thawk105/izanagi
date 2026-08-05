# 段 1 brief — [T-244] P4 実装 (batch freeze の W2/W3 適合 + P4 充足判定)

- wave: dev-wave-t244-p4-batch-freeze / branch `worktree-dev-wave-t244-p4-batch-freeze` / base main `55c2e84`
- 依頼 (command 引数): 「[T-244] P4 実装 — (186) で起票可、W2/W3 の適合 + P4 充足判定まで」

## scope

D121 P4 (batch cardinality / 全候補の事前 commit / seal までの結果非公開) を、既存の origin ledger
第一級 batch event へ **D153 W1〜W5 適合**として実装し、**P4 充足を判定する**。
編集面は `orchestrator/campaign/reflux_origin_ledger.py` と
`orchestrator/tests/test_reflux_origin_ledger.py` に限る。production 結線は本 wave の面ではない
(並行 wave `dev-wave-t244-p3-producer-wiring` が所有)。

## 確定済みユーザー裁定 (推測ではなく一次資料で確認済み)

- **W1〜W5 全件を D153 推奨どおり採用** (2026-08-04 /rulings 3 回目、発話「推奨通りで」。
  一次控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` §7)。
  W1 実装先 = ledger 内の第一級 batch event / reducer。W2 member identity = query/replicate ordinal 込み。
  W3 結果の evidence 束縛 = evidence digest 束縛。W4 早期停止 = 残 member を tombstone として消費し
  公開 transcript 長を固定。W5 = origin-total の計数は ledger、batch 層は authority receipt 由来 policy
  のみ受理、class referent の実在・完全性検証は formal consumer 側の義務。
- **名乗り制限** (D153 決定 3 + D159 決定 4 の U-G 会計) — 実測が支持しない限り「P4 充足」と書かない。
- 設計入力: [T-460]、[T-186] (a) seal ceremony (いずれも「P3+P4 実装 wave の設計入力へ」)。

## 段 1 前提実測 (親が worktree 内で実測、`55c2e84`)

1. **W1 seam は実在** — `reflux_origin_ledger.py:445-493` の 5 event と `:887-1065` の reducer。
2. **W2 は非適合 (実測)** — `:904-908` が candidate commitment の distinct を、`:964-965` が candidate
   平文の distinct を強制する。D153 が「反復測定を表現できない」と却下した distinct wire set 設計
   そのままであり、replicate ordinal は preimage に存在しない。
3. **W3 は非適合 (実測)** — `EvidenceReference` は authority manifest の 2 field (`:228-229`) だけで
   使われ、batch 結果には束縛が無い。`result_sha256s` は任意 64hex の自己申告で、`outcomes` は
   自由文字列 — `:1001-1009` は "accepted"/"rejected" 以外を素通しし、その場合 constraint 検査も
   発火しない。
4. **W4 は部分的** — batch 単位 tombstone は `:1026-1034` に実在し予算 refund もしない。member 単位の
   消費と「公開 transcript 長の固定」が W2 の ordinal 導入後も成り立つかは段 2 の file:line 判定へ。
5. **W5 は適合見込み** — floor は manifest budget 由来で `sealed_queries` により判定 (`:1051-1055`)。
   ただし class referent の義務分界がコード上に明示されていない。
6. **凍結 bytes の pin 閉包 (DW-O09)** — `FROZEN_MANIFEST` に reflux 系 hit 0 件。凍結成果物は非対象。
   ただしテスト内の **独立 golden** が canonical bytes を pin する (`test_reflux_origin_ledger.py:315-410`)。
   event schema を変えると golden は必ず動くので、**意図的更新の対象として事前宣言する**
   (実装子が黙って期待値を書き換えるのは (186) で起きた契約違反であり、本 wave では止めて報告させる)。
7. **受理集合の現状** — production caller ゼロ・authority registry 空 (D159 決定 4) を実測で維持。

## 不変条件 (緩めない)

- 規律 2: seal までの結果非公開 (commit-reveal privacy) を弱める変異は採らない。
- D159 の既存保証 — salt 再利用拒否・exact class 一致・wire 正準性検証・単一 in-flight batch — を後退させない。
- production caller ゼロ / authority 空を維持する (結線は別 wave の面)。
- 独立 golden は「実装から生成しない literal」であり続ける (自己参照 hash を作らない)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** member identity を `(candidate_wire, query_ordinal, replicate_ordinal)` 込みの preimage とし、
  distinct 強制を「ordinal 込み member の distinct」へ置換する。同一 wire の R 回反復を許す。
- **(P2)** W3 は `result_sha256s` を evidence digest として型付けし、outcome を閉じた語彙へ限定した上で
  seal 時に outcome ↔ evidence digest の対応を検証する。
- **(P3)** P4 充足判定は U-G と同型の会計 (producer 結線 + consumer 要求まで含めて数える) を既定とし、
  本 wave は「P4 適合 batch freeze prototype」までを名乗る。

## DW-G05 成果物影響

- W2 非適合を放置すると、予算下限式が要求する replicate を batch が表現できず、certifiable seal の
  query floor 判定が実 query 数より小さく写る → **certifiable と名乗れる origin の集合が実際より広くなる**。
- W3 非適合を放置すると、proof chain が未裏付けの outcome を受理し、**材料レポートの outcome 値が
  evidence と対応しない**まま certified 選択の根拠に入る。
- W4/W5 の残余は、確定後に同じ形で 1 行ずつ書く。

## 軽量版判定 (DW-C00)

本 wave は「正しさ防壁に触る」「受理集合が変わる」に該当する (commit-reveal と floor 判定の意味を
変える)。よって**軽量版にしない** — 段 2・3 と段 6 の review 子を省かない。

## 分割方針

段 2 = codex read-only 1 本 (file:line プラン)。段 3 = 敵対 2 レンズ並列 (A: 恒真ゲート・受理集合拡大、
B: 整合・consumer・golden/凍結)。段 5 = codex author (ledger 面とテスト面を所有分離)。
段 6 = 敵対レビュー 2 本 + fix。
