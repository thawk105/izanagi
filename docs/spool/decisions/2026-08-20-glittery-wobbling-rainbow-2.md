---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: glittery-wobbling-rainbow
seq: 2
---

## {{D:t1403-mitigation-leg-sigterm-confirmed}}. mitigation leg 構成で NQSV が walltime 打ち切り時に SIGTERM を配送することを実測で確認した

**決定 (1): `elapstim_req="max,warn"` (warn < max) + `--warning-signal=elapstim:SIGTERM` +
`--accept-sigterm=yes` の "mitigation leg" (D139 決定4 が存在を未実測としていた構成) は、実際に
計算ノードで捕捉可能な SIGTERM を配送する。** Pegasus `gen_S`、request `927684.nqsv` (max=180s,
warn=120s) で実測した。根拠はスケジューラ自身の出力である。

```text
%NQSV(INFO): Batch job received signal SIGTERM. (Exceeded per-req elapse time limit)
```

probe (`tools/pegasus/probes/t1403_walltime_sigterm_probe.py` の `run_workload`) 自身の signal
handler が実際に SIGTERM を catch し、受信から約 1.6 ミリ秒後に正常終了した
(`SIGTERM_CAUGHT_CLEAN_EXIT`)。D139 決定1 が実測した既定構成 (`--accept-sigterm` 省略・警告値省略)
での SIGKILL 直送・grace 皆無とは異なる挙動である。

**決定 (2): scheduler 会計ベースの grace は 9.97 秒だった。** NQSV 会計の `Elapse` (129S、job 開始から
job 完全終了まで) と、probe checkpoint の `sigterm_received_at` (119.03 秒) の差である。probe 自身の
自己申告 grace (約 1.6ms) より大きいのは、NQSV 側の job 終端検出・会計確定オーバーヘッドを含むためで、
どちらも `output/insights/2026-08-20_t1403-walltime-sigterm-mitigation-leg.md` に両方残す。

**決定 (3): この結果は現行 `floor_campaign.sh` の構成には適用されない。** 現行 `floor_campaign.sh`
(`--accept-sigterm=yes` のみ、`elapstim_req` は単一値) は本決定の測定対象と異なる構成であり、
D546 決定2 の「実測するまで結論しない」は現行構成についてはなお成立する。`floor_campaign.sh` /
`dispatch_compute.py` の production 設定は本 wave で変更していない。mitigation leg を production
へ適用するかは別途裁定する。

**理由:**
- D139 決定4 が「捕捉可能な構成の有無は未解決である」「実測するまで結論しない」と明記しており、
  本 wave はその実測を担った。
- 判定語彙は実測前に固定した (`SIGTERM_CAUGHT_CLEAN_EXIT` / `SIGTERM_CAUGHT_THEN_KILLED` /
  `NO_SIGNAL_OBSERVED_SIGKILLED` / `UNKNOWN`) — D139 の「観測されなかった signal は推定しない」規律を
  継承する。verdict は checkpoint (probe 自己申告) と NQSV 会計 (scheduler 側) の両方が揃って
  初めて `SIGTERM_CAUGHT_CLEAN_EXIT` と判定される。

**却下した選択肢:**
- **`floor_campaign.sh` 自体に mitigation leg を追加してから実測する。** 却下。観測目的の変更を
  production 設定へ先に反映すると、実測前に結論を先取りすることになる (D546 決定2 が戒める形)。
  独立 probe で先に実測し、production 適用は結果を見てから別途裁定する。
- **`dispatch_compute.py` の汎用 dispatch 経路を使う。** 却下。同ツールは pytest/provenance の
  dev harness 専用 (`TASKS` が2種類のみ) であり、mitigation leg の PBS directive を持たない。
  D139 自身も「実harnessを使い捨てcheckout上でwalltime killする」を却下し probe 側で測る方針を
  採っており、同じ判断を踏襲した。
