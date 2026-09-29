# 依頼 (逐語、/dev-wave の引数)

[T-2872] MOCC read-heavy (48 thread・1,000,000 record・rr95、pin C) で stock 自体が 3/109 反復で G2
  を出す件を、(iii) MOCC 本体の欠陥か (iv) trace hook の影響かに切り分ける (裁定 D2277 項
  2「普通に使います。そして修理もします」、一次資料 output/insights/2026-09-27/t2868-mocc-g2-cause/README.md、既往
  T-2774 §7・T-2779 §3)。観測者効果の小さい計器で再現と帰属を取り、結論と CCBench 所見を output/README.md の形式で
  insight に構造化する。本 wave は切り分けまで。CCBench の MOCC 修理は [T-2854] の整形 commit と
  cc/mocc/transaction.cc で重なるので含めず、本体の欠陥と確定したら修理方針を次の一手に書く。稼働中の VHash wave
  が編集している orchestrator/campaign/condition_meaning_gate.py・screening_driver.py には触らない。probe・patch は
  Codex author (D95)。計算は job Elapse の実測単価で見積もり、2 node 時間以上ならユーザー確認後に投入。規律 2 は不変
  (t2849 の値は pin C 上の測定として有効 = 規律 7)。本題の切り分けだけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。
