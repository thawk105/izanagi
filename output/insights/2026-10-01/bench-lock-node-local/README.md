# bench lock の既定 path を node ローカルにする — 計算ノード smoke と変異の記録 (2026-10-01)

authority: none
default_effect: no-state-change

設計判断の正本は decisions の該当エントリ (wave `worktree-dev-wave-bench-lock-node-local`、bench_lock の既定 path を node ローカル固定名にする決定)。
本書は、判断を支える計算ノード上の観測と変異の結果だけを置く。生の結果ファイルは repo 外の
`/work/1/SFC/tanab/tmp/dw-bench-lock-node-local/` (smoke-run-1/、mutation-*-results.json) にある。

## 1. 何を確かめたか

`orchestrator/campaign/lock.py` の既定 lock を、home 共有 (Lustre) の `~/.izanagi/bench.lock` から
`/tmp/izanagi-bench-<uid>.lock` に移した。確かめたかったのは次の 3 点である。

- (a) 別 node の 2 job は、既定 lock を同時に保持できる (= 直列化されない)
- (b) 同じ node の 2 process は、既定 lock で排他される (= 測定の単独性は保たれる)
- (c) 対照: 共有 FS 上の同じ lock file なら、別 node でも直列になる (旧既定の挙動の再現)

## 2. smoke の方法

- repo 外の使い捨て probe が、計測用 checkout (detached efa6cf56c、lock.py は最終版と同じ bytes) から本番の `bench_lock()` を import する。
- generic dispatch で 2 job (participant A・B) を別 checkout から同時に投入した (request 40909.nqsv・40910.nqsv、walltime 5 分)。
- 共有 FS 上の handshake file で開始と各段の順序をそろえ、各区間の取得・解放の時刻 (epoch と monotonic) を記録した。
- 「相手の取得を自分の保持中に観測した」という握手 (因果) も記録した。
- 実 bench と WAL は通していない。前提なしで 5 分以内に通せる既存経路が無く、land 調整役と合意して lock 機構の確認に限った。

## 3. 結果

| 項目 | 観測 | 判定 |
|---|---|---|
| 割当て | A = bnode043、B = bnode042 (別 node)。各 Elapse 24 s | — |
| (a) 別 node・既定 lock | 保持区間の重なり 5.0096 s。A・B とも自分の保持中に相手の取得を受信 | 成立 (握手で因果的に示せる。時刻だけでも各 host ±1 s の誤差を仮定して 3.0 s 以上の重なり) |
| (b) 同一 node・2 process | bnode043: 重なり −0.00063 s、bnode042: −0.00079 s。親の保持中に子が BenchBusy、親の解放後に子が取得 | 両 node で pass |
| (c) 共有 FS の対照 lock | 重なり −0.0486 s (unlock 完了を終端)。B が A の保持中に BenchBusy、A の解放通知の後に B が取得 | 直列 (握手で因果的に示せる。時刻だけでは時計誤差の上限が未確立なので inconclusive) |
| `/tmp` | 専用 mount 無し。ローカル NVMe の xfs root FS (`/dev/nvme0n1p4`)。自 uid 以外の entry が 12 件 (userns では 65534 に見える) | job 専用の空の tmpfs ではない |
| 既定 lock file | 両 node とも開始時に不在、終了時に存在 | — |

判定器 (`judge.py`) の総合は inconclusive (rc=2) だった。原因は、時計誤差の上限を外部で確立していないことだけである。

## 4. 未確認のまま残すもの

- 同じ node の**別 job** が同じ lock file を見ること。上の (b) は同じ job 内の親子で、mount 情報からの推論にとどまる。
- job 終了後 (epilogue 後) に lock file が残ること。
- 実 bench と性能検証が、別 node で並行に走ることの WAL 時刻での確認。次の A-2 実走で行う。
- 依頼資料の「node ローカルなら約 3.3 node 時間」は未実測の試算で、wall 効果も未確認である。

## 5. 変異 (lock.py、テスト `orchestrator/tests/test_bench_lock_default.py`)

独立 clone (main = a6dea8eb1) の固定 commit で、計算ノード 1 job に束ねて走らせた。probe 走 (40918.nqsv) で観測 node を集め、
それを完全集合として登録した final 走 (40923.nqsv) で照合した。

| 変異 | 内容 | 期待 | final |
|---|---|---|---|
| M0 | コメントだけ (正例) | SURVIVED | SURVIVED |
| M1 | 既定を `~/.izanagi/bench.lock` に戻す (mkdir も) | KILLED 10 node | KILLED (期待 node と完全一致) |
| M2 | 既定を `tempfile.gettempdir()` 基準にする | KILLED 3 node | KILLED (期待 node と完全一致) |
| M3 | 名前から uid を落とす | KILLED 9 node | KILLED (期待 node と完全一致) |
| M4 | 非空 env を無視する | KILLED 6 node | KILLED (期待 node と完全一致) |
| M5 | 空文字 env を path として返す | KILLED 1 node | KILLED (期待 node と完全一致) |
| M6 | `LOCK_EX` を `LOCK_SH` にする | KILLED 1 node | KILLED (期待 node と完全一致) |
| M7 | 取得時の `os.utime(fd)` を削る | KILLED 1 node | KILLED (期待 node と完全一致) |

## 6. 検討して見送った分割案 (backlog)

A-2 を workload × cell の別 job に割る案は見送った。現行の契約は、workload ごとに 1 job で 2 cell が campaign・WAL・claim を共有する形である。
rr95 は 1 rep 約 7.7 分で、cell 単位に割っても 5 分目安に届かない。

段 3 の相談で、次の別案が出た。
- correctness 検証は workload × cell の job にする。
- 性能測定は workload ごとの stock/adopted pair job に残す。

性能比較を同一 node に残したまま、5 node を保持する時間を減らせる。ただし receipt と WAL の結合契約の変更が要る。
