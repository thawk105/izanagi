## 6. 裁定パッケージ — 契約 (a) の候補と実測値の対応 (本 wave は決めない)

記号: P = 前段 (≈ 1.3〜2 秒、harness の時計は dispatcher より約 2 秒早い)、Q = `queue_wait_timeout_s` (既定 900、D612 上書きで 1,200〜3,600)、W = walltime (3,600)、G = `overall_grace_s` (既定 300、上書き 600)、A = 回収猶予 60、C = cleanup 予算 90。dispatcher 自身の最長は `P + max(Q, q + W + G) + A + C` (q = 実際の queue 待ち)。

### 6.1 候補

| 候補 | 契約 | 必要な外側値 (既定 / 上書き 3600・600) | 過去 3,849 件での harness 先行発火 | 帰結 |
| --- | --- | --- | --- | --- |
| (a-1) 全区間を覆う | harness は dispatcher より先に切らない: `timeout_seconds ≥ P + Q + W + G + A + C` | 4,952 / 7,952 秒 | 0 件 (最長 1,784 秒) | timeout は全部 dispatcher の in-band (rc=16、fresh-qstat gate、`--resume` 可)。orphan hold は harness からは出ない。`hang_timeout_seconds` も同じ値になり、`DW-M06` の「dispatch では hang_timeout < walltime」と両立しない (改訂が要る) |
| (a-2) queue 待ち + grace を覆う (現行 collection gate の式) | `timeout_seconds ≥ Q + G`、RUN 中は dispatcher に委ねる | 1,200 / 4,200 秒 | 1,200 秒で 10 件 (0.26%): QUE 1 / RUN・Pre-running 9 → orphan hold 9 | 現状維持。`hang_timeout_seconds` は gate の対象外のまま (t2195 の 900 は既定でも Q+G=1,200 未満) |
| (a-3) queue 待ちだけを覆い、hang は dispatcher の walltime に委ねる | `hang_timeout_seconds` を外側 watchdog から外す (dispatch では job を kill できない、F901) か `= timeout_seconds` に固定 | (a-1) と同じ | 0 件 | hang_risk の意味を「local probe で観測し erratum で残す」(F901 の運用) に一本化。DW-M06 改訂が要る |
| (a-4) 区間認識の watchdog | harness が dispatcher の進行 (`compute-visible.json` の有無 = job 開始) を見て区間ごとに上限を持つ | 実装が要る ([T-2071] 見送りの再訪) | — | 受理集合に触れる新機構。本 wave の scope 外 |

### 6.2 実測が示す制約 (どの候補にも共通)

- queue 待ち ≥ 900 秒は 0.23% (9 / 3,849)、≥ 1,200 秒は 1 件、≥ 1,800 秒は 0 件。Pre-running ≥ 300 秒は 2.2%、≥ 600 秒は 0.37%。RUN (実) p99 207 秒、max 1,121 秒。
- **発火区間ごとの帰結**: QUE 中 → dispatcher が 0.3 秒以内に qdel し job は残らない (SIGTERM 4 件 + dispatcher 自身の Q timeout 3 件 = 7/8、例外は今朝の Staging 1 件 10.5 秒・remain=true)。Pre-running / RUN 中 → qdel せず job は自然終了まで残る (receipt 6 件 + 本 wave の run2 = 7/7)。harness 側は区間に依らず rc=2 + 変異残置 + hold。
- 投入時の gen_S QUE 数は自分の queue 待ち・Pre-running の予測にならない (§2)。よって「混雑時だけ値を変える」運用は receipt の preflight では組めない。
- D612 の上書きは queue 待ちの上限を伸ばすだけで、Pre-running・RUN の長さは変えない。

### 6.3 (c) 理由付き早期診断の具体案 (受理集合を動かさない、D2044 項 29 で採用済み、本 wave では実装しない)

1. 起動時: `hang_timeout_seconds < Q + G` および `timeout_seconds < P + Q + W + G + A + C` を、拒否せず stderr に理由付きで出す (どの区間で先行発火しうるか、過去 receipt での確率)。現行の collection gate は `timeout_seconds` しか見ないので、`hang_timeout_seconds` は無診断で通る。
2. 発火時: `orphan-stop.json` に submission dir の `compute-visible.json` の有無 (job が node で始まったか) と receipt の `qdel.gate.reason` を写す。「job が走っていないのに hold になった」(Pre-running 発火) と「job が走っている」を区別でき、復旧の待ち時間の見込みが立つ。

### 6.4 親の推奨 (裁定ではない)

(a-1) を `timeout_seconds` の契約とし、`hang_timeout_seconds` は (a-3) で外側から外す。理由: harness は dispatch mode で job を止められないので、先に切っても「hold + 変異残置 + job は自然終了まで残る」が増えるだけで、待ち時間は減らない (F901 の 45 分は dispatcher に任せても同じ)。in-band に寄せると rc=16 → `--resume` で続けられ、hold の手動復旧 (F453 / F530 の型) が消える。費用は 1 dispatch あたり最長 4,952 / 7,952 秒を harness が待つことだが、過去 3,849 件でその長さに達した dispatch は無い。関連の見送り [T-2071] (queue / Pre-running と child 実行の timeout 分離) は (a-4) に相当し、(a-1)/(a-3) を採るなら不要になる。

裁定に必要な追加の実測は無い。DW-M06 / DW-M07 の改訂と collection gate の式の扱い (D2044 項 29 の (b) 不採用と両立させる形) は裁定後の実装 wave が持つ。
