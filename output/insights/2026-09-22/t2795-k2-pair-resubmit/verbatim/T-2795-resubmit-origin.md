# 依頼の逐語 (ユーザー直接起動の `/dev-wave` の引数、2026-09-22 08:4x JST)

[T-2795] (P1、D2211 項 1 で認可済み) K2 の同 job pair (候補 + stock) を再投入 1 job。候補と stock がともに certified かつ stock の
  src_token == STOCK なら 4 巡目 1 job (新規生成 1 回 + 同 job stock 対照、入力は D2194 項 2 の択 A = round 3 の repo 内派生物から射影)
  を続けて投入し、不成立なら D2187 どおり認定せず報告して止める (再投入で救済しない)。経路 H (D1777)、起動口は
  tools/pegasus/p3_s4_loop_pegasus.sh の --stock-control (D2205 で修復済み)。lock 済みの dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair
  (原本の唯一の現物) は動かさず、着手直前の local main から新しい submit-tree を作る。投入前に 2 job と付随検査の合計 node 時間を見積もり、2
  node 時間以上ならユーザー確認 (D2212 項 4)。epoch 差と派生入力の限定を記録に開示。正本
  output/insights/2026-09-21/t2795-pair-repair/README.md、output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md。規律 2
  を緩めない。本題だけ、gate・検査・台帳の追加は scope 外。
