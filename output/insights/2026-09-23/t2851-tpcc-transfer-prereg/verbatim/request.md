# 依頼の逐語 (ユーザー直接起動の /dev-wave の引数、2026-09-23)

[T-2851] の残り (4) (P1、VLDB 差分分析 P4) — TPC-C の留保条件を、TPC-C の生成・探索・選択が始まる前に別の事前登録として固定する
  (docs のみ、D2212 項 2)。親の登録 = docs/unseen-condition-transfer-preregistration.md (§14「TPC-C の留保
  (必須の未完項目)」、留保の効力は着地時点 = D2223)、記録 = output/insights/2026-09-22/t2851-transfer-prereg/README.md、TPC-C の段分割 = D2219
  項 2 と output/insights/2026-09-21/tpcc-trace-certification-design/README.md。v1 と同じ流儀 (錨・1 因子ずつ・同等幅・区間) を TPC-C 段 1
  (NewOrder/Payment) と段 2 の取引構成へ当て、学習条件と留保条件の境界と、留保値を生成器・選択へ入れない規則を書く。T-2850
  の選択結果・測定の発効・runner 実装・計算は含めない。稼働 wave の file は触らない。本題の文書だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。規律 2 は緩めない。着手直前の local main から fresh worktree を作る。
