# 生死確認 L0 の実測要約 ([T-2847] si-v2、2026-09-26)

pin C 68106660 + `patches/instr-si-trace-v2.patch` (build `V2`、裸マクロなし)、起動器 `launch_si_run.py` (sha256 2eb71e7284419feb1eba6aecde1a7d21e30878946fd0375d586f007e12fb9700)、`tools/pegasus/dispatch_compute.py --task generic`、`-clocks_per_us=2100`、run timeout 120 s、verifier `--protocol si` 証人なし。

cell: K = `ycsb_tuple_num=200 ycsb_zipf_skew=0.9 ycsb_rratio=50 ycsb_rmw=false ycsb_max_ope=10 extime=1`、W = `ycsb_tuple_num=200 ycsb_zipf_skew=0.9 ycsb_rratio=0 ycsb_rmw=true ycsb_max_ope=5 extime=1`。

## 1 回目 l0-a (request 29768.nqsv、bnode096、Elapse 36 s、wave commit a68c312ef)

build・4 run とも成功、C 行数 = E 行数。verify は全 run parse error: `malformed line 'C 0 \x00 1 1 3 5'`。原因 = si の `thid_` が `uint8_t` (`cc/si/include/transaction.hh:30`) で、stream へそのまま流すと文字になる。fix = `static_cast<std::size_t>(thid_)` (commit 0db1ae583、Codex fix)。

## 2 回目 l0-b (request 29774.nqsv、bnode095、Elapse 64 s、wave commit 0db1ae583)

| cell | C | R | W | E | verdict | 巡回 | integrity (orphan・version dup・dup txid・missing・genesis・版不一致・framing) | X/P/I |
|---|---|---|---|---|---|---|---|---|
| K t1 | 187,647 | 772,978 | 875,526 | 187,647 | indeterminate | 0 | すべて 0 | evidence-absent |
| K t4 | 174,799 | 719,461 | 814,818 | 174,799 | non-serializable | 2,443 | すべて 0 | evidence-absent |
| W t1 | 262,096 | 0 | 1,229,490 | 262,096 | indeterminate | 0 | すべて 0 | evidence-absent |
| W t4 | 222,974 | 0 | 1,046,154 | 222,974 | indeterminate | 0 | すべて 0 | evidence-absent |

- 生死確認は成立: pin 前進なしの patch で si の trace が現行 parser に受理され、framing violation 0 で verdict が出る。
- W (rmw=true) では R 行が 0 (update が同じ key の read set 要素を消す、SI:239-247)。rw 辺・wr 辺が trace から完全に消えるので、W 条件では巡回が構造的に出ない。
- これらは事前登録前の探索走で、段 4 の事前登録はこれを見た後に行う (V36 の期待自体は設計書 2026-09-22 §4.5 にある)。
