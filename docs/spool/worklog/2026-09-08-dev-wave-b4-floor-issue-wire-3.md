---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-b4-floor-issue-wire
seq: 3
title: B-4 の権威 floor 成果物の発行機構と材料レポートへの配線を同一変更単位で建てた — 変異が非保証の未保護を暴き、走行中に producer が v3 へ上がって前提が覆った (コード + テスト + docs、branch worktree-dev-wave-b4-floor-issue-wire、変異 baseline PASSED・KILLED 14・SURVIVED 0・MISMATCH 0)
---

## 本文

D1592 の却下欄が名指しした「実 producer の接続と同じ変更単位」がこの wave である。
production の分析経路が無条件に floor 不在を渡し、どんな測定を入れても分析 verdict が
1 種類しか出なかった欠陥を、発行機構と配線を 1 つの変更単位として閉じた。
一次資料は `output/insights/2026-09-08_b4-floor-issue-wire/`。

**段 3 の 2 レンズが丸めの向きで正面から対立し、両方が正しかった。** 一方は「1 ULP の切上げでは
exact D を覆わない」、他方は「切上げは未裁定の値改変である」。親が数値で追試して両方を確認し、
**丸めそのものを廃止**する形で解いた。設計判断は {{D:floor-exact-no-rounding}}。

**敵対レビュー 2 本が見逃した実欠陥を、変異走行が 1 件暴いた** ({{F:non-guarantee-verbatim-unpinned}})。
成果物の非保証の逐語が test で守られておらず、偽の主張へ反転しても緑のままだった。

**走行中に別 wave が main へ着地し、producer の版が上がって段 4 裁定の前提が覆った。**
段 4 は「版 pin の前進は着地後の follow-up」としていたが、取り込んだ時点で旧版 pin の consumer は
実 producer の出力を全て拒否する。D1530 が禁じた「使われない防壁」になるため再裁定し、
版の前進を同じ wave に含めた。判断の形は {{D:floor-schema-pin-single-value}}。
その結果 1 件の非保証が事実に反することになり、実際に証明していないことへ差し替えた。

**権威 floor の発行を実際に通すには、独立した 2 つの障害が残る。** 一方だけ直しても通らない。
(1) D1641 が成果物名へ求める 5 要素のうち `protocol` が凍結 spec に存在せず、build receipt からも
導出できない。issuer は推測せず欠落名を付けて拒否する。(2) 別 wave が報告した凍結 spec loader の
hash 不動点により、spec 自体が作成不能である。

**棄却 finding はゼロ。** 段 3 で 11 件、段 6 で 8 件の所見が出て、いずれも real と裁定した。
段 6 の 1 件 (段 4 が明示しない一般 hardening 群) だけは、再導出が意味を持つ前提・producer の形の
写し・既存の同型拒否と同じ、という理由で scope 内と裁定して残した。

**親の手順違反 1 件。** 変異走行中に insight を repo へ書き、harness が untracked を検出して
fail-closed で止まった。変異注入前だったので損害は無い。harness が正しく止めた。

## 次の一手差分

### 新規

- {{T:b4-floor-protocol-identity}} **P1・新規**: D1641 が権威 floor 成果物の名前へ求める 5 要素のうち
  `protocol` が凍結 spec に存在せず、build receipt からも導出できない。v2 でも v3 でも spec の
  exact top-level key 集合に無い。issuer は推測せず欠落名を付けて発行を拒否するため、
  **この 1 点だけで権威 floor は発行できない。** 択一: (a) 凍結 spec に `protocol` を足す
  (対照対 driver の凍結作業に含める)、(b) D1641 の命名要素を 4 要素へ訂正する追記。**推奨 (a)。**
- {{T:b4-prereg-s11-stale}} **P2・新規**: 事前登録 §11 は「材料レポートの生成器は本書を読まず、
  評価器へ無条件に floor 不在を渡す」と書くが、本 wave 以降は §5 を読んで floor を渡す。
  記述が事実に反する。段 4 裁定が doc 非改変を定めたため本 wave では直していない。
  **推奨: §5 記入を担当する wave が §11 を追記で訂正する。**
- {{T:b4-floor-d-exact-rational}} **P3・新規**: binary64 の中間丸めにより、記録された float D は
  同じ入力を exact 有理数で計算した D より小さいことがある (実例で差 5.55e-17、相対 1e-16)。
  床値が真の D より小さいと、境界の block が tie から勝敗へ変わりうる。
  本 wave は値を変えない方針を採り、限界を非保証へ明記して逃げている。
  択一: (a) 現状維持 + 非保証明記、(b) D の式を exact 有理数で凍結し直す (driver 側の凍結作業に含める)。
  **推奨 (b)。** ただし実効上の大きさは床値の典型値の 14 桁下である。
- {{T:b4-summary-relation-checks}} **P3・新規**: 権威 floor の発行機構は summary の関係検査を
  していない。`window_artifacts` の重複、campaign stratum の重複、`planned` と残存標本数の不整合を
  受理する。これは D1696 が人手責任に残した面なので本 wave では足していない。
  **再訪条件 = 人手の確認が実際に見落とした項目が 1 件でも出たとき (D1696 の逐語)。**
