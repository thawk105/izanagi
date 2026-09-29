# 依頼 (ユーザー直接起動の `/dev-wave`、2026-09-29 09:42 JST 受領、引数の逐語)

[T-2865] silo-function-policy 軸 (D2214・段階 F = D2270) の研究系列を新しく 1
  本起こし、coder・auditor・critic を回して複数 iteration を Pegasus で実走する。機構は [T-2871] で着地済み (一次資料
  output/insights/2026-09-29/t2871-policy-loop-iter/README.md §5・§8)。着手直前の local main から新しい detached
  submit checkout を作って bootstrap stock から始め、2 本目以降の pair job は qsub --after で先に待ち行列へ入れる
  (walltime 予算 3,600 s は待ち行列込み、[T-2881]、runbook §8)。系列 B の記録は
  output/insights/2026-09-27/t2865-silo-policy-iter2/README.md。単価は pair Elapse 741〜793 s・bootstrap 309 s
  で、job 合計が 2 node 時間以上の見込みなら見積りを示してユーザー確認後に投入。auditor の出力形は runbook §1(d) の
  prompt 明記で回す (固定文面の改訂 [T-2870] は scope 外)。iteration ごとの certified / reject・anomaly の分類・stock
  比を insight に残す。コード変更は想定せず、要るなら Codex author (D95)。規律 2
  は緩めない。本題の実走だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
