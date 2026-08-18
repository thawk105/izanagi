---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t688-job-kill-evidence-r2
seq: 2
---

## {{D:floor-job-accept-sigterm}}. 床値 job の signal trap を到達可能にし、主張は配送に限る

**決定 (1): `tools/pegasus/floor_campaign.sh` へ `#PBS --accept-sigterm=yes` を置く。**
記法は単一トークン形とする。根拠は repo 内の既存 probe
(`output/insights/2026-08-03_t361-t362-cluster-probes/driver/signal_walltime_mitigation.pbs`) と
既裁定本文であり、空白区切りの実例は repo 内に存在しない。

**決定 (2): この変更が主張するのは「SIGTERM が送られてくれば受け取れる」までである。**
walltime 打ち切りで NQSV が SIGTERM を送るかは未解決のままとする。既裁定が、捕捉可能な構成には
`elapstim_req="max,warn"` (warn < max) と `--warning-signal=elapstim:SIGTERM` も要ると記し、
**実測するまで結論しない**と定めている。本 wave はその実測を行っていない。
したがって「walltime で `signalled` が残るようになった」と書いてはならない。

**決定 (3): 診断のための値を計測 process へ到達させない。**
checkpoint path と evidence root の環境変数は、driver が runner を呼ぶ前に private state へ
取り込んで `os.environ` から削除する。実測 subprocess の環境に checkpoint 系 key が存在しない
ことを production 形のテストで固定する。

**決定 (4): partial-log と checkpoint は診断専用であり、計測値・certified 選択の権威にしない。**
書き込み先を repository の外に置くことでこれを構造的に担保する。`output/` へ untracked を
1 つも足さない。権威 `journal.jsonl` の strict 性 (末尾不完全行で全体を拒否する挙動) は
1 bit も変えず、緩和は診断専用 reader 側にだけ作る。

**理由:**
- NQSV は既定で `Accept Sigterm = No` であり、その状態が PBS job から `bash -c` まで継承される。
  そのため床値 job の signal trap は一度も発火しえず、`signalled` の記録は原理的に不可能だった
  ({{F:floor-signal-trap-unreachable}})。checkpoint 機構を足すだけではこの経路は死んだままになる。
- 決定 (2) を明記するのは、直したことと被覆できたことを混同しないためである。qdel のように
  外から TERM が送られる経路では実際に記録されるが、walltime は別問題である。
- 決定 (3) は絶対規律 1 (観測者効果の分離) の直接の適用である。診断設定が計測入力に混入すれば、
  将来それを解釈する binary が入ったとき sample・walltime・失敗判定、ひいては certified 選択が
  診断設定に依存しうる。

**却下した選択肢:**
- **W1 (interpreter 解決前) を保証範囲から外す。** 却下。そこは G1 の最重要窓であり、外すと機構の
  目的が消える。T-688 が名指しする SIGKILL・OOM・walltime はいずれも process 単位の kill であり、
  `write()` が戻った時点でデータは失われない。`fsync` が防ぐのは node crash であって process kill
  ではない。したがって素の bash 追記で足りる。ただし過剰主張を避けるため、行ごとに
  `durability` を `process-kill` と `fsynced` で書き分ける。
- **checkpoint を repo 内 `output/` へ置いて既存 consumer をそのまま使う。** 却下。`output/` は
  dirty 検査から除外されるため誤書き込みが受入で見えず、かつ診断が計測値の権威へ昇格する経路を
  残す。consumer 側 (`floor_liveness`) を同じ wave で拡張する方を採った。
