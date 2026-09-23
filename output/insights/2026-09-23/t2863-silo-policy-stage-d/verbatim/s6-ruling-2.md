# 段 6 裁定 2 巡目 — [T-2863] (2026-09-23、親 = Claude manager)

入力: 初走 job 2・3・5 の結果 JSON (commit `ce4985ab2` の run、dispatch_compute --task generic、request 20182〜20189.nqsv のうち 3 本、各 Elapse 428〜434 秒)。

| ID | 判定 | 裁定 |
|---|---|---|
| G1 (親の実測) | real | 結果 JSON の `pbs_jobid` が null。`dispatch_compute --task generic` は env_mode=clean で子の環境変数を消すため、run は PBS_JOBID を読めない。aggregate は「initial PBS_JOBID missing or duplicated」で error になり二値が null に固定される。fix: aggregate の job 識別を (hostname, started_at) の組にし、初走 8 job の組が互いに異なること・再測の組が初走のどれとも異ならないことを要求する。`pbs_jobid` は非 null の場合だけ従来どおり重複・一致を検査する。run は変えない (計測済み)。dispatch の request ID は親が dispatch log から insight に記録する |

変異の追加登録 (fix 前): M-AGG-JOBID (再測と初走の (hostname, started_at) 同一検査を除去 → 同じ走を再測として渡しても null にならない)。

## 焦点再レビュー 1 巡目 (s6-focus-1.md、NO-GO) の裁定

| ID | 判定 | 裁定 |
|---|---|---|
| RA1・RA2・RA3/RB1 | closed (対応表どおり) | — |
| F1 (記録の `numa: true` は legacy verify に当たらない) | real (nit) | 不採用。各走の実コマンド (numactl の有無を含む) は結果 JSON の `command` に残り、二値・受理集合は変わらない。insight に「workload.numa は性能構成 verify と bench の条件」と明記する。計測済みの run は変えない |
| F2 (対照の genome.protocol を照合しない) | refuted (仮想リスク) | 不採用。run は protocol を "silo" に固定して書き、別 protocol の JSON を集計へ渡す経路は本 wave に無い (DW-G05) |
| RB2・RB3 の再評価 (時間切れで欠測 → null) | refuted (実測) | 初走 job 2・3・5 の Elapse は 428〜434 秒で walltime 1,800 秒の 1/4 未満。時間切れによる欠測は起きていない |

## 実行上の erratum (2026-09-23 14:3x JST)

- 初走 job 7 (20185.nqsv、計測木 recon-7) が 14:08 から PRR のまま 20 分以上起動しない。qdel はせず (F47 の投入停止ラッチ)、同じ job 7 を計測木 recon-2 から別 request で投げ直した (tag `initial-7b`)。集計には 2 本のうち**先に完了した方**を使う。選択は完了順で結果の値に依存しないので偏りは入らない。後から完了した方も捨てずに記録する (node 時間に数える)。
