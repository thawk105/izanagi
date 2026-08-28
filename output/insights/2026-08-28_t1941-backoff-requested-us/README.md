# T-1941 adaptive backoff requested-us diagnostic

authority: none
default_effect: no-state-change

## 結論

Pegasus の balanced 1 workload x 1 rep で、Silo adaptive backoff の呼出回数と要求待ち量を直接観測した。
結果は診断専用であり、`certified: false`、`diagnostic_only: true`。headline TPS、formal B-10、floor、
fitness の利用資格はすべて `false` である。formal prereg の physical residual 1.0% exclusive 上限は
変更していない。

- 実装/fix tip: `5d278c612ac30a6969d57f4c8237bbcb03960e9e`
- 成功 request: `957236.nqsv`、compute `bnode047`、scheduler Elapse `80S`、child rc `0`
- 診断 root: `/work/1/SFC/tanab/b10-backoff-requested-us-runs/backoff-requested-us-t1941-5d278c612-6`
- rep SHA-256: `f9dc81e00b1836330936150a549bfab43b09bfd202f27c4bb2f45d39ba12aa1d`
- manifest SHA-256: `5eb418d25b9378e44172b15e01e9fda52593d98c745421fc0988d6dd3e6ebe49`
- dispatcher receipt SHA-256: `f319bdb29a9c902ff5209c2b963278976e90eba874b11fc8a9c2f51cf643bc8f`
- reference campaign: `b10-backoff-grid-silo-balanced-sweep-9ded73c4`
- reference adaptive variant: `602b4ce9c788`

## 診断値

| field | value | call比 |
|---|---:|---:|
| `call_count` | 931,274 | 100.000% |
| `requested_us_sum` | 125,899,500 | — |
| `state_0_call_count` | 480,120 | 51.555% |
| `state_100_call_count` | 238,132 | 25.571% |
| `state_200_call_count` | 57,590 | 6.184% |
| `state_300_call_count` | 33,173 | 3.562% |
| `state_400_call_count` | 25,461 | 2.734% |
| `state_500_call_count` | 19,724 | 2.118% |
| `state_600_call_count` | 17,576 | 1.887% |
| `state_700_call_count` | 15,756 | 1.692% |
| `state_800_call_count` | 15,907 | 1.708% |
| `state_900_call_count` | 15,654 | 1.681% |
| `state_1000_call_count` | 12,181 | 1.308% |
| `unknown_state_call_count` | 0 | 0.000% |
| `counter_overflowed` | false | — |

導出した平均要求待ち量は `125899500 / 931274 = 135.19060985273936 us/call`。これは診断値であり、
実時間 wait、TPS、floor、fitness、formal B-10 値ではない。bucket 合計は call count と一致し、加重和は
requested-us sum と一致する。

## 参照と境界

- workload は balanced、48 thread、1,000,000 record、extime 3 秒。
- requested grid intersection は `{0,100,...,1000}` の 11 状態。
- admitted realized intersection は F718 により 1000us を除く 10 状態。
- reference binary は historical attempt の build-cache receiptへ束縛し、live binary再hashは行っていない。
- diagnostic build binary SHA-256 は
  `1cd3bcba12c6404f3901ecb8bbf57cc8402f390e580fc8744e710436930427b6`。
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
6. request `957236.nqsv`: policy identity修正後の最終tipで成功、rc=0。本READMEの診断値はこのrunを正とする。

attempt 2〜6のraw job logは
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
