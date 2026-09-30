1. **must — `login-collection.log` の bytes と失敗時の rc が一致しない。** 旧経路は `subprocess.run(text=True)` で locale に従って復号し、改行を正規化する。前倒し経路は UTF-8 の `errors="replace"` で復号する（[run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-pyc-warm/tools/run_tests.py:1475)、同:1550）。**放置時:** CRLF 等の出力で log bytes が変わり、不正な UTF-8 が stderr にある場合は旧経路の rc 16 が前倒し経路で rc 0 になりうる。**修正:** 従来と同じ復号・改行処理を共通化し、CRLF と不正 byte の差分テストを加える。

2. **should — `main` 後半全体の再インデントは局所化できる。** 前倒し process を所有する必要があるのは、起動後から preflight・dispatch の終了までだが、非 shard の通常実行まで `try/finally` に入っている（同:2693–2841）。差分は `run_tests.py` が **+229/−127** で、段 4 の +150 行目安を超える。**放置時:** 直ちに受理集合は変わらないが、非対象経路の変更面と今後の rc 回帰リスクが増える。**修正:** 前倒し対象の preflight と dispatch を小さな所有スコープに切り出し、非対象経路の既存ブロックを維持する。

3. **should — 成功後の子孫停止は検証されていない。** `collected=True` になると `close()` は process group を停止せず終了する（同:1485–1514）。追加テストが PID と子孫を確認するのは preflight 赤だけで、成功テストは起動回数と log を見る（[test_run_tests_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-pyc-warm/orchestrator/tests/test_run_tests_shards.py:847)、同:860）。**放置時:** collection 親だけが終了し子孫が残る場合、成功 rc と成果物を出した後も process が残りうる。**修正:** 「孤児を残さない」の対象に成功後の子孫を含めるか明記し、含めるなら成功経路でも group の消滅を検査・保証する。

4. **should — 採算と集合不変はまだ実測で成立していない。** 新テストは `main → _dispatch_result → run_parallel` を通し、M1〜M6 の対象となる起動、再利用、log、赤経路の回収、marker、fallback をそれぞれ検査している。一方、偽 worker と偽 merge を使うため、実 shard の `observed_universe` 一致は検査しない（同:759–816）。**放置時:** pre 約40秒短縮と受理集合一致を未確認のまま land 判断することになる。**修正:** 段 4 で事前登録した同時刻対照と受入全走で判定する。現時点で両者は未実施。

**反証できず:** 既存テストの期待値は差分上変更されていない。非 shard・marker 不在・内部 spec・非 LOGIN の起動条件、preflight の呼出し順、5100 秒 deadline の起点、command・env・exclusions は静的には維持されている。一時 file と process group は大量出力時の詰まり防止と赤経路の回収に根拠があり、3 MB テストもその性質を検査している。ただし M1〜M6 の変異実走は未実施。

## 総括

**NO-GO。** log bytes と rc の不変条件に具体的な反例がある。加えて、規模超過の局所化と成功時の process 寿命を確認し、事前登録した対照で利益と受理集合を実測する必要がある。