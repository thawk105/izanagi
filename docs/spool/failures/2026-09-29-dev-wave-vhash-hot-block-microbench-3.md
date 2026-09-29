---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-hot-block-microbench
seq: 3
---

## 新規

### {{F:microbench-key-chain-short-period}}. 微小計測の依存連鎖のキー列が固定増分の線形合同列で短周期になり、「LLC 外」の作業集合が意図より桁違いに小さかった [計測汚染] [テスト代表性]

- 事象: VHash の hot block 微小計測 (`tools/vhash_microbench/hot_block_bench.cc`) の読み側の計時 loop は、次のキーを `(idx × 1664525 + 選んだ版 ID + 1013904223) mod n` で決めていた。同じ深さの cell では版 ID が全キー共通の定数なので、これは固定増分の線形合同列になり、周期が n より大幅に短かった。同じ式で 300 万歩辿って数えると、n=1,775,815 の cell で 45 キー、他の「LLC 外」の cell でも 6,145〜393,216 キーしか訪れない。計算ノードの本走 4 shard (約 0.87 node 時間) の読み側の値は、作業集合の一部が cache に乗った状態の値で、図と結論に使えなかった。親が値を表にしたときの違和感 (LLC 外の external 16 B が 15 ns、pilot が 8×LLC まで飽和しない、cache-misses/op が条件間で不規則) から検算して見つけた。敵対レビュー 2 本・焦点再レビュー 2 巡は挙げなかった。
- 根本原因: 「依存連鎖を作る」ために結果を次の添字の式に混ぜたが、その結果が条件内で定数になりうることと、法 n が 2 のべき乗でないと線形合同列が全周期にならないことを検査していなかった。selfcheck と checksum の照合は「4 方式が同じ答えを返すか」を見ており、「計測がどの作業集合を触ったか」は見ていなかった (正しさの検査が通っても、条件の名前どおりの負荷かは別)。
- 恒久対応: キー列を 2 のべき乗を法とする全周期列から n 以上の値を飛ばす固定列にし、結果は計時外に得た不透明な 0 を介して依存だけを残した (commit 375e15a42)。bench のテスト `orchestrator/tests/test_vhash_hot_block_bench.py::test_read_key_sequence_full_period` が n 歩で全キーを 1 回ずつ訪れることを実際の n で検査し、旧い式に戻す変異で赤になる (45 キー訪問を再現)。読み側は取り直した (一次資料 `output/insights/2026-09-29/vhash-hot-block-microbench/README.md` §7)。
- 再発検知: 微小計測・合成負荷の生成器を足すときは、キー列の周期と実際に訪れる要素数を条件の名前 (「LLC 外」など) と照合する検査を置く。値を表にして条件間の不規則さ (飽和しない、miss 数が単調でない) を見たら、生成器の作業集合を先に数える。

### {{F:dispatch-overall-timeout-includes-queue}}. generic dispatch の全体時間上限は RUN 観測まで待ち行列の時間を含み、混雑時に queue-wait-timeout より先に取り消される [手順漏れ]

- 事象: 2026-09-29 に `tools/pegasus/dispatch_compute.py --task generic --walltime 00:30:00 --queue-wait-timeout 3600` で投げた pilot (request 33801.nqsv) が、35 分 QUE のまま `overall-timeout` (rc=16、`child_started: true` だが子の rc は無し) で終わり、dispatcher が qdel した。子は一度も走らなかった。
- 根本原因: 全体時間上限は「投入時刻 + walltime + `--overall-grace` (既定 300 秒)」で、RUN を観測したときにだけ起点が付け替わる (`tools/pegasus/dispatch_compute.py` の `total_deadline`)。待ち上限 (3600 秒) を広げても、walltime + 300 秒を超えて待つと先に全体上限へ達する。**初出は 2026-08-04 の [T-425] (受入 dispatch が 55 分 QUE のまま overall-timeout) で、その知識は AI の記憶だけにあり、failures 台帳と runbook に無かった。** 今回は記憶を引かずに投入して再発した。
- 恒久対応: `docs/pegasus-runbook.md` の generic task 節に「`--overall-grace` を `--queue-wait-timeout` 以上にする」を追記した。本 wave の再投入は `--overall-grace 3900` で通った。
- 再発検知: `IZANAGI_DISPATCH_OUTCOME_V1` に `"reason":"overall-timeout"` が出て、receipt の `state_history` が全部 `QUE` なら本項である。
