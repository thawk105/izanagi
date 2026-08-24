# paper-story A-3 — P2-4 性能値の estimand 統合

authority: none

default_effect: no-state-change

## 結論

P2-4 の旧環境における論文採用値は、trace-disabled inline sweep の workload 別結果として次の2件に固定する。

- write-heavy: no-backoff stock-best baseline に対し fixed 10us が **+38.3%**。
- balanced: no-backoff stock-best baseline に対し fixed 5us が **+11.3%**。

`backoff_profile_t48_skew0p9_rr5.json` から得る **+38.5%** は、別 CCBench commit、
`BACKOFF_NOINLINE=1`、`perf record`、3反復の機序診断 cell である。D20 が明記する通り headline throughput には使わない。
これは +38.3% の丸め違いではなく、同じ公称 contrast を別 operational regime で観測した値である。

write-heavy repro **+42.2%** と balanced repro **+11.7%** は、同じ intended contrast を別時刻・逆順で
実現して同方向だった定性的 corroboration である。事前登録された pooling 式がないため、元 sweep と平均しない。

本 report は既存 tracked 成果物の再計算だけであり、新規性能計測も correctness/certification の更新も行っていない。
現在の D496 契約下の fresh paired 値は別 A-1 wave の所有で、ここに混ぜない。

## 用語と estimand の三層

- **no-backoff stock-best**: `BACK_OFF=0`, `BACKOFF_FIXED=-1`。本 report の baseline。
- **stock adaptive**: `BACK_OFF=1`, `BACKOFF_FIXED=-1`。本 report の利得分母ではない。
- **fixed backoff**: `BACK_OFF=1`, `BACKOFF_FIXED=N`。sweep が workload ごとに選んだ treatment。

intended estimand は workload primitives、outcome、baseline、treatment で定める。
operational regime は source/build、計装、反復、集約、実行順で定める。
realization identity は artifact と測定時刻で定める。したがって sweep と repro は同じ intended estimand の別 realization、
profile は同じ公称 contrastでも headline と互換でない operational regime である。

## 条件表 — workload と treatment

| cell | 再計算値 | baseline | variant | workload | records | threads | skew | rratio | rmw |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| profile-write | +38.5% | BO=0, FIXED=-1, NI=1 | BO=1, FIXED=10, NI=1 | write-heavy | 1,000,000 | 48 | 0.9 | 5 | 0 |
| sweep-write | +38.3% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=10, NI=0 | write-heavy | 1,000,000 | 48 | 0.9 | 5 | 0 |
| sweep-balanced | +11.3% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=5, NI=0 | balanced | 1,000,000 | 48 | 0.9 | 50 | 0 |
| repro-write | +42.2% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=10, NI=0 | write-heavy | 1,000,000 | 48 | 0.9 | 5 | 0 |
| repro-balanced | +11.7% | BO=0, FIXED=-1, NI=0 | BO=1, FIXED=5, NI=0 | balanced | 1,000,000 | 48 | 0.9 | 50 | 0 |

略号は BO=`BACK_OFF`、FIXED=`BACKOFF_FIXED`、NI=`BACKOFF_NOINLINE`。NI=0 は configure command に
明示されない既定 inline buildであり、profileの NI=1 と区別する。

## 条件表 — build、反復、集約、時期

| cell | build / instrumentation | reps | aggregate | execution order | measurement time | role |
|---|---|---:|---|---|---|---|
| profile-write | ccbench `dff0f1e…`; TRACE=0; NI=1; `perf record cycles,instructions` | 3 | 各側 TPS median の比 | none→2→5→10→25→50→100us | absent | mechanism only; headline=no |
| sweep-write | ccbench `6656e93…`; Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | no-backoff→adaptive→2→5→10→25→50→100us | 2026-06-22 22:58:59–23:09:04 JST | legacy headline=yes |
| sweep-balanced | ccbench `6656e93…`; Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | no-backoff→adaptive→2→5→10→25→50→100us | 2026-06-22 23:09:04–23:14:19 JST | legacy headline=yes |
| repro-write | ccbench `6656e93…`; Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | fixed10→fixed5→no-backoff | 2026-06-28 14:57:00–14:59:02 JST | qualitative corroboration |
| repro-balanced | ccbench `6656e93…`; Release; gcc/g++-13; TRACE=0; `perf stat` | 5 | 各側 TPS median の比 | fixed5→fixed10→no-backoff | 2026-06-28 14:59:02–15:01:22 JST | qualitative corroboration |

profile JSON は measurement timestamp、compiler、binary digest を持たない。worklog は 2026-06-28 の P2-4 節、
artifact 収録 commit は 2026-06-29 05:27:13 JST だが、どちらも measurement time の代用にしない。
profile の CCBench full commit は同 artifact を生成した code commit の `CCBENCH_COMMIT` から束縛した。

## 再計算

全 cell で式は `100 * (variant_median / baseline_median - 1)`、表示は小数1桁への四捨五入である。

| cell | baseline median TPS | variant median TPS | 未丸め値 | 表示 |
|---|---:|---:|---:|---:|
| profile-write | 1,867,747 | 2,586,112 | 38.461579646% | +38.5% |
| sweep-write | 1,882,125 | 2,603,521 | 38.328803879% | +38.3% |
| sweep-balanced | 2,791,760 | 3,106,342 | 11.268232226% | +11.3% |
| repro-write | 1,827,281 | 2,599,032 | 42.234938140% | +42.2% |
| repro-balanced | 2,731,913 | 3,050,505 | 11.661864781% | +11.7% |

profile と sweep-write の導出値差は約 0.133 percentage points。しかし build、source commit、計装、
反復数、timestamp provenance が一致しないため、この小ささを丸め差の根拠にしない。

## 論文で使う表現

> 旧 linux-baremetal 環境の trace-disabled inline sweep では、no-backoff stock-best baseline に対し、
> sweep-selected fixed backoff の median throughput は write-heavy (fixed 10us) で 38.3%、
> balanced (fixed 5us) で 11.3% 高かった。別時刻・逆順の再測定でも両 workload は同方向だったが、
> これらは現在の paired campaign 契約より前の記述的結果である。

機序説明で profile を使う場合は次の限定を付ける。

> 別 CCBench commit の noinline perf-sampling 診断では、同じ公称 write-heavy contrast が 38.5% だった。
> この TPS は sampling overhead 込みであり、headline 値ではない。

## 言わないこと

- +38.5% と +38.3% を同じ測定の丸め違いとは言わない。
- baseline を stock adaptive と呼ばない。adaptive の TPS は sweep 表にあるが利得分母ではない。
- write-heavy fixed 10us と balanced fixed 5us を単一 treatment の一般効果として平均しない。
- repro 値を元 sweep と poolせず、「頑健性を定量証明した」とも言わない。
- profile から headline binary と同一の機序を直接証明したとは言わない。
- performance artifact から correctness、certification、safe を推論しない。A-2 の結果も本 reportへ後付けしない。

## source ledger

raw TPS と run条件は JSON/WAL/lockを一次とし、D18/D20、phase2、archive worklogは解釈・時系列の資料とする。

| artifact ID | tracked path | SHA-256 | containing repo commit | supported fields |
|---|---|---|---|---|
| profile-json | `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json` | `e99932213a571561c87f5ac253e19f59a81382718bb0cf08a9c64ea64281d184` | `b97ee91534d2b62de3341df3b257149a05dbf8ba` | workload, flags, reps, medians |
| profile-md | `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.md` | `7d419391f9e9f8e205d87b5ca5b0b16eb57b5ebc73ce904adf47c8ee64e9e8c8` | `b97ee91534d2b62de3341df3b257149a05dbf8ba` | mechanism-only role |
| sweep-write-lock | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/campaign.lock` | `493813a705e73908d8cbd99e55cba679f831b5cd3b8e1f40fc9f45d9dbee08ca` | `ed51c1bfa56a4773f86cfb5d5431c4bd92ef3239` | workload, scale, CCBench commit |
| sweep-write-wal | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl` | `9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926` | `ed51c1bfa56a4773f86cfb5d5431c4bd92ef3239` | flags, build, reps, medians, time |
| sweep-balanced-lock | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/campaign.lock` | `484c663ea167ec12ac1a44b30bf15353a3b66393ac6f528dacd4d97d3f67c857` | `ed51c1bfa56a4773f86cfb5d5431c4bd92ef3239` | workload, scale, CCBench commit |
| sweep-balanced-wal | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl` | `8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c` | `ed51c1bfa56a4773f86cfb5d5431c4bd92ef3239` | flags, build, reps, medians, time |
| repro-write-lock | `output/campaigns/backoff-repro-silo-write-heavy-repro-181607af/campaign.lock` | `181607af20cf9bcea32d0d3071a353ab5ac6ffa3f66f7bb3ff1d2d6b26170b9b` | `33efa5ecb8f9ab59edd23894c915855260a49d9e` | workload, order, CCBench commit |
| repro-write-wal | `output/campaigns/backoff-repro-silo-write-heavy-repro-181607af/runs/wal.jsonl` | `ea6f9e250960f1bccac3c6c8d5b5029bebebf01eee607e50493e8d6b2aa6f103` | `33efa5ecb8f9ab59edd23894c915855260a49d9e` | flags, build, reps, medians, time |
| repro-balanced-lock | `output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/campaign.lock` | `87dbbf504c8be9c637bb4b6297c15cabd4160cb6501cfcfbd76b09b50ce7ceaf` | `33efa5ecb8f9ab59edd23894c915855260a49d9e` | workload, order, CCBench commit |
| repro-balanced-wal | `output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/runs/wal.jsonl` | `7afeac668c8ba678f651ef9cab33f95fb87879f0034c138065b243913bb1dc92` | `33efa5ecb8f9ab59edd23894c915855260a49d9e` | flags, build, reps, medians, time |

CCBench full commitsは sweep/repro が `6656e9319566e602113edf46588de9a612d166a1`、profile が
`dff0f1ef2a4b84746f6463839e85b24301f4b16d`。profile binary digestは一次成果物に無く `absent` とする。

## 欠損と後続測定

A-3 の旧値統合に必要な新規測定 cell は **なし**。欠損は profile の exact measurement timestamp、compiler、
binary digestだが、profileをheadline不適格な機序診断へ限定する判定を妨げない。これらを推測で埋めない。

現在契約での性能比較は A-1、同一性能 workloadのcertificationは A-2 の別waveであり、A-3の後続測定指定ではない。
本 report の入力 allowlist は上の tracked P2-4 artifactsと指定された canonical docsに固定し、
wave開始後に生じたA-1/A-2成果物を参照・複製・要約・採用しない。

## Canonical pointers

- `docs/paper-story/2026-08-23.md` §2 P2-4 / §8 A-3
- `docs/phase2.md` P2-4
- `docs/archive/worklog-phase1-2.md` 2026-06-22 / 2026-06-28 P2-4
- `docs/decisions.md` D18 / D20 / D361

既存 paper-story snapshot は凍結した入力・監査対象であり、本 waveでは上書きしていない。
