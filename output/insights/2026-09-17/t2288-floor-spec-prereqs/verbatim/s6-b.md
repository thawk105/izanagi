## path・sha256・数値

以下、`D` は検査対象 decisions fragment、`I` は insight README、`W` は worklog fragment、`R` は `output/env/pegasus/calibration/registered/`、`J` は同 `job-staging/`、`B` は指定 job dir を指す。

**refuted — 4 較正の path・完全 SHA・16 桁接頭辞・数値の誤りは確認しなかった。** 現物 bytes から SHA-256 を再計算した。

| R 配下のファイル | 完全 SHA-256 | records | submit_epoch |
|---|---|---:|---:|
| `calibration-753f535a8d024727.json` | `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49` | 1,000,000 | 1784404710 |
| `calibration-94a4b79fa31bba3c.json` | `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` | 1,000,000 | 1785983265 |
| `calibration-5c836a22eff9ab40.json` | `5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc` | 1,000,000 | 1789310388 |
| `calibration-2b7ba072b88023ae.json` | `2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067` | 2,000,000 | 1789523899 |

根拠は各 JSON の `saturation.records` と `acquisition_receipt.qsub.submit_epoch`。前者は順に行 1612 / 1612 / 1617 / 1618、後者は行 56 / 56 / 60 / 60。

**refuted — cell 値・既定値の誤り。**

- 4 件とも `threads=48`、`clocks_per_us=2100`、`env_tag="pegasus"`。
- workload は exact 3 key。`ycsb_rmw="0"`、`ycsb_zipf_skew="0.9"`、`ycsb_rratio` は順に `"50"` / `"50"` / `"95"` / `"5"`。各 JSON の行 1686 / 1686 / 1691 / 1692 で確認した。
- 4 job の argv に `--extime`、`--sweep-reps`、`--noise-reps`、`ycsb_max_ope` は無い。CLI 既定は `cli.py:150` の 3、`:151` の 3、`:152` の 10。CCBench 既定は `external/ccbench/include/ycsb.hh:22` の 10。
- runner は extime と workload を flag 化する (`runner.py:1119`、`:1125`)。反復は同じ flags に対するループ (`:1154`、`:1194`)。sweep の reps は各 records 点へ渡される (`sweep.py:101`)。

**nit — `I:39` の job 名は略記。** 実 directory は `0:867876.nqsv` 等であり、括弧内の `0:867876` 等には `.nqsv` が省かれている。D の対応式は正しい。

## 識別子

**refuted — 指定識別子の不存在・意味の取り違え。**

| 識別子 | 現物と意味 |
|---|---|
| `SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS` | `layer3_report.py:79`。g1 の path・完全 SHA の組 |
| `EFFECTIVE_CLOCK_METHOD` | `env_attestation.py:38`。現行 rotating-min method |
| `load_verified_calibration` | `calibration_verify.py:80`。hash を束縛して admission |
| `_bind_checkout_inputs` | `floor_pair_driver.py:1122`。較正・binary・receipt と cell の束縛 |
| `median/v1` | `floor_pair_driver.py:61`、`:953`。reducer 固定値。`:2794` の実装は奇数なら実標本値を返す |
| `floor-pair-spec/v3` | `floor_pair_driver.py:56` |
| `place_record` / `place` | `b4_binary_record.py:149`、`:249` |
| `output/env/<env_tag>/binaries/<sha256>` | `b4_binary_record.py:163` で構成 |

`PerfConfig.reps=5` も `pipeline.py:190` と一致する。

## 条件 3 と条件 5 の裏付け

**refuted — genome 不在 2 件の silo 判定を辿れないという疑い。** 両方について実際に追跡し、registered と argv が tracked であることも確認した。

| record | receipt の pbs_jobid → J 配下 directory | argv と receipt で一致した binary SHA |
|---|---|---|
| g1 `753f535a…` | `0:867876.nqsv` → `0:867876.nqsv/` | `9ef84125ca4b3067ebe346dd155b0e6f412d88b3689a2c5921ccbba4eff5925f` |
| g2 `94a4b79f…` | `0:892707.nqsv` → `0:892707.nqsv/` | `25c82a74bf98d303ebc8588e6d1a9e6344835eb58ae8186ba7dde9f5b5171993` |

各 record の行 8 が job ID、行 11 が receipt の binary SHA。各 `calibrate-argv.json:14` が `/scr/0_…/ccbench-build/cc/silo/ycsb_silo.exe`、`:16` が対応 SHA である。**job-staging の directory はコロンを保持する**。`/scr/` と `attempts/` の下線表記とは区別されている。

**refuted — 条件 5 の identity・method の誤り。**

- g1 は `R/calibration-753f535a8d024727.json:1442` で `proc-cpuinfo`。
- 他 7 件は全件、`env_attestation.EFFECTIVE_CLOCK_METHOD` と同じ `proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1`。
- `layer3_report.py:79` の除外集合は g1 の path と再計算した完全 SHA に一致。
- 自己不整合の既裁定は `docs/decisions.md:47614` の D1537 に存在する。

## 実装行の確認

**refuted — 「binder は protocol を照合しない」は実装と一致する。** `floor_pair_driver.py:1122` の関数は、binary・receipt 検査、較正 admission、accepted 検査に続いて、`:1185` 以降で env・threads・clocks・workload・records を照合する。較正 genome と対象 protocol の比較は無い。registered 配下限定も要求していない。

**refuted — 「verifier の現行 policy 照合は tolerance だけ」も当該 verifier について正しい。** `calibration_verify.py:116` で schema、`:121` で env、`:125` で clocks、`:130` で tolerance を検査する。現行 method 定数との比較は無い。

ただし、`env_contract.py:524` の新規 successor 発行経路には method 比較がある (`:538`)。D は較正 verifier に限定しているので、この別経路との矛盾はない。

**refuted — D1538 の consumer 限定が実装済みという読み。** `layer3_report.py:493` は genome 不在・within-run なら silo を返し、2 SHA の許可リストを照合しない。`I:123` と `W:32` の「未実装」は正しい。

## T-2697 と worklog の事実

**real — `W:35` の「計算ノード job は 0 本」は訂正が必要。**

`B/focus-after.log:4` に request `2285.nqsv`、`:6` に RUN、`:7` に END、`:19` に 255 passed がある。さらに実 receipt：

`output/pegasus-dispatch/96a4f4094af00bf80453f9a8a70f2991/receipt.json`

の `result.hostname="bnode014"`、`result.pbs_jobid="0:2285.nqsv"`、`result.child_rc=0` を確認した。現時点で少なくとも 1 本である。執筆後に増えた可能性はあるが、最終記録では更新が必要。

**refuted — T-2697 の配置規則が未着地、または tracked 化という疑い。** archive の行 1・46、`b4_binary_record.py:149` の配置処理、`:249` の `place` 分岐、`.gitignore:20` が記述と一致する。配置規則の着地と、この checkout での配置実行は別であり、W は後者を残作業としている。

**refuted — registered 件数・admission・§5 不変の誤り。**

- registered は現物・tracked とも 8 件。`load_verified_calibration` を `pegasus / 2100 / required` で実行し、**8/8 ADMITTED を独立に再現**した。
- 事前登録の HEAD と作業中 bytes の行 154〜167 は一致。両方の SHA-256 は `1762b7cc5158e080d2d4005184c16a802a14eda640190a340f48f2a6e59be423`。
- diff は §11 の 2 箇所への追記だけで、既存行の削除・変更は無い。
- tracked JSON の走査では accepted 較正 19 ファイルを検出。registered 8 件、その複製 9 件、別 SHA の mocc 2 件という内訳で、`I:103` と整合した。

**nit — 「codex 子 5 本」は起動数と完了数を分けると正確。** 検査時点の `B/*-out.md` と `B/*.log.done` は各 3 件で、plan 1・consult 2 の完了を示す。`B/manifest.json` の sessions は plan 1・consult 2・review 2 の 5 件。したがって起動数 5 は裏付くが、完了 5 本はまだ裏付かない。

## 総括

**real は 1 件：worklog の計算ノード job 数を更新する必要がある。** 指定された SHA・数値・識別子・条件 3/5・binder/verifier・T-2697 の主要な事実主張への攻撃は成立しなかった。

検査限界として、圧縮ファイル 1,771 件の件数は再確認したが、全件展開検索、全文 pin の完全逆引き、床値成果物の全域不存在までは独立に再証明していない。これらを全面検証済みとは扱わない。pytest・測定・配置操作は実行していない。