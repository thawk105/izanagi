# T-1941 adaptive backoff requested-us diagnostic

authority: none
default_effect: no-state-change

## 結論

Pegasus の balanced 1 workload x 1 rep で、Silo adaptive backoff の呼出回数と要求待ち量を直接観測した。
結果は診断専用であり、`certified: false`、`diagnostic_only: true`。headline TPS、formal B-10、floor、
fitness の利用資格はすべて `false` である。formal prereg の physical residual 1.0% exclusive 上限は
変更していない。

- 実装 anchor: `a4b87728908451986e172c1e29741a40f6a630bd`
- 成功 request: `957182.nqsv`、compute `bnode035`、scheduler Elapse `65S`、child rc `0`
- 診断 root: `/work/1/SFC/tanab/b10-backoff-requested-us-runs/backoff-requested-us-t1941-a4b877289-5`
- rep SHA-256: `5f5439079323bff24975b4cfdde1f9eeb0d1cd4ce64eb85f54851033a85b6f0e`
- manifest SHA-256: `04a61fe34877e0cc1fdc35cd10f8a75cc9fb3d5975b5fc7a1b7ddf6bd7ec0968`
- dispatcher receipt SHA-256: `1fb8f9e924bf491a72f4c341c3da6507dbe40db5f704a84181d4c0587f29510e`
- reference campaign: `b10-backoff-grid-silo-balanced-sweep-9ded73c4`
- reference adaptive variant: `602b4ce9c788`

## 診断値

| field | value | call比 |
|---|---:|---:|
| `call_count` | 944,141 | 100.000% |
| `requested_us_sum` | 125,930,900 | — |
| `state_0_call_count` | 495,387 | 52.470% |
| `state_100_call_count` | 237,045 | 25.107% |
| `state_200_call_count` | 57,030 | 6.040% |
| `state_300_call_count` | 31,747 | 3.363% |
| `state_400_call_count` | 23,581 | 2.498% |
| `state_500_call_count` | 21,045 | 2.229% |
| `state_600_call_count` | 17,265 | 1.829% |
| `state_700_call_count` | 17,553 | 1.859% |
| `state_800_call_count` | 16,657 | 1.764% |
| `state_900_call_count` | 14,613 | 1.548% |
| `state_1000_call_count` | 12,218 | 1.294% |
| `unknown_state_call_count` | 0 | 0.000% |
| `counter_overflowed` | false | — |

導出した平均要求待ち量は `125930900 / 944141 = 133.38145467679087 us/call`。これは診断値であり、
実時間 wait、TPS、floor、fitness、formal B-10 値ではない。bucket 合計は call count と一致し、加重和は
requested-us sum と一致する。

## 参照と境界

- workload は balanced、48 thread、1,000,000 record、extime 3 秒。
- requested grid intersection は `{0,100,...,1000}` の 11 状態。
- admitted realized intersection は F718 により 1000us を除く 10 状態。
- reference binary は historical attempt の build-cache receiptへ束縛し、live binary再hashは行っていない。
- diagnostic build binary SHA-256 は
  `eb799ddc6d1af520e8b6df0c93eb5db80177f237a22328e2bedbc7b95f8c9d4d`。
- diagnostic patch は `cmake/Options.cmake`、`include/backoff.hh`、`cc/silo/transaction.cc` の
  既存 source-digest allowlist 内3fileだけを変更する。default 0では計装をpreprocess除去する。
- per-call更新はheap-backed worker-local TLS counterだけで、共有registry同期はworker初回登録時だけ。
  process exitで15 fieldを1行集約する。

## 実装・検査

- 関連test: `53 passed`。
- final mutation: baseline PASSED、13/13 KILLED、MISMATCH/SURVIVED/TIMEOUT/PARSE_ERROR 0。
  詳細は `mutation-summary.json`。
- `python3 tools/check_codex_agents.py`: rc 0、native active 0 / dormant 13。
- `python3 tools/check_docs.py`: rc 0。
- AI provenance: implementation anchorまで新規違反0。既知違反は既知台帳どおりで、本waveの緑に数えない。

## 実走の失敗履歴

1. request `956566.nqsv`: generic clean childにPBS変数が無く入口rc=2。
2. request `956676.nqsv`: nested `patchharness.applied()`のflock自己待ち。687秒で停止、rc=143。
3. request `956904.nqsv`: 低context patchがproduction `git apply`で拒否、rc=1。
4. request `957062.nqsv`: `result.hh`/`ycsb_silo.cc` のallowlist外変更をsource_digestが拒否、rc=1。
5. request `957182.nqsv`: 成功、rc=0。

attempt 2〜5のraw job logは
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1941-backoff-requested-us/captured-job-logs/` に逐語保存した。
dispatcher receiptは `output/pegasus-dispatch/` の
各request directoryにあり、上記失敗順のSHA-256は
`40afa2dd...`、`cd63dfb4...`、`0b2d4799...`、`82fcb2ea...`、成功分は`1fb8f9e9...`。

## 限界とscope外

- 1 workload x 1 rep のため、rep安定性、分位点、自己相関、thread間同時値率、3 workload一般化は主張しない。
- 1000us fixed符号化衝突は修理しない。
- diagnostic値をheadline、formal B-10、floor、fitnessへ流用しない。
- 一般trace framework、全CC共通計装、新launcherは作らない。

還元判断: 対象はIzanagi診断計装であり、CCBench上流還元は行わない。
