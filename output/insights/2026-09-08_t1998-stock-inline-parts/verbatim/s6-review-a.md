## 段 3 所見の閉じ具合

| 段 3 の所見 | closed / partial / regressed | 根拠 (file:line) |
|---|---|---|
| A-1 診断 build の排除 | partial | arm 別 source digest は比較するが、診断 marker は configure argv の完全一致 2 形式しか拒否しない。`orchestrator/campaign/t1998_stock_inline_pair.py:449-495` |
| A-2 script digest / repository commit の束縛 | closed | result、reservation、lock authority、job-body digest を結合している。`orchestrator/campaign/t1998_stock_inline_pair.py:727-755,803-813`、`tools/pegasus/a5_second_boot_backoff_sweep.sh:378-388,414-445` |
| A-3 gitlink の 40 桁 exact / 短縮 prefix | closed | 40 桁だけ exact、7〜39 桁は lowercase prefix として分岐し、full identity ではないことも返す。`orchestrator/campaign/t1998_stock_inline_pair.py:84-93,736-796,935-946` |
| A-4 arm 固有 source identity | closed | baseline / target の preregistration を別型で持ち、それぞれの `source_bytes_sha256` と比較する。`orchestrator/campaign/t1998_stock_inline_pair.py:141-169,449-467,883-902` |
| A-5 `pair-cardinality` の帰属 | closed | 冗長 gate であることを明記し、変異証拠に数えていない。`orchestrator/campaign/t1998_stock_inline_pair.py:843-860` |
| A-6 構造化拒否 | partial | 型には field / expected / actual / arm があるが、global admission の全失敗を baseline に帰属させるため、原因 arm が誤る。`orchestrator/campaign/t1998_stock_inline_pair.py:172-203,675-684` |

## 新しい所見

### 所見 1 — typed CMake define で診断 build が source digest ごと素通りする

**根拠 (file:line)**

診断検査は `-DCCBENCH_BACKOFF_NOINLINE=1` と `-DBACKOFF_NOINLINE=1` の完全一致だけです。`orchestrator/campaign/t1998_stock_inline_pair.py:469-488`

一方、source digest は genome と source bytes から計算され、記録済み configure override は preimage に含みません。`orchestrator/campaign/source_digest.py:2046-2072`

テストも source digest を実計算せず固定文字列で組み立て、完全一致形式だけを負例にしています。`orchestrator/tests/test_t1998_stock_inline_pair.py:112-117,176-187,215-219,458-472`

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

正例 root の target `perf_configure_cmd` に `-DCCBENCH_BACKOFF_NOINLINE:STRING=1` を加え、result の WAL SHA だけ更新する。build-start の canonical genome と preregistered source digest は変わらないため `source-identity-unbound` は発火せず、typed define は `diagnostic_markers` にも一致しない。

実効 build は `BACKOFF_NOINLINE=1` なのに consumer は `accepted` を返し、診断 throughput を headline 値として扱う。

**直し方の方向**

pair の configure argv について `-DNAME[:TYPE]=VALUE` を正規化し、noinline の実効値を検査する。少なくとも literal token 集合ではなく、sanctioned builder が生成する configure 契約との一致に落とす。

### 所見 2 — attempt に属さない anomaly record を追加すると規律 2 を迂回できる

**根拠 (file:line)**

WAL topology は `verify_done` / `bench_done` に `build_attempt_id` が無ければ検査せず通します。`orchestrator/campaign/wal.py:2217-2221`

certified admission は COMMIT より前にある同一 attempt ID の verify だけを検査します。`orchestrator/campaign/artifact_admission.py:752-790`

consumer も fixed pair では同一 attempt ID の一件だけを取得して verify payload を捨て、他点では stage 集合しか見ません。`orchestrator/campaign/t1998_stock_inline_pair.py:420-432,861-881`

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

正例 WAL の off-pair variant に、次の `verify_done` を追加する。

- `build_attempt_id` は欠落
- `verdict="serializable"`
- `certified=True`
- `anomalies=1`

既存の正常 verify と COMMIT は残し、result の WAL SHA を更新する。topology と certified admission は追加 record を無視し、consumer は stage が存在することだけを見て `accepted` を返す。

同じ variant の WAL に anomaly が明記されているのに headline 適格と結論するため、規律 2 の実効的な抜け道である。

**直し方の方向**

T-1998 の 8 点について、全 verify / bench record が一意の build attempt に属することを stage-shape 条件に含める。orphan signal を内容判定から除外するのでなく拒否する。

### 所見 3 — executable は argv 内に一度現れるだけで「実行された」と判定される

**根拠 (file:line)**

consumer は configure の build directory から期待 path を作り、`run_cmd` のどこかにその token が一度あれば通します。argv の実行位置や wrapper 構造は確認しません。`orchestrator/campaign/t1998_stock_inline_pair.py:502-517`

テストは正常な `numactl ... ycsb_silo.exe` だけで、decoy token の負例がありません。`orchestrator/tests/test_t1998_stock_inline_pair.py:249-259`

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

target の `run_cmd` を次に変え、TPS payload と result projection は維持する。

```text
/bin/true /fixture/build/<target>/perf/cc/silo/ycsb_silo.exe
```

期待 path は argv に一度あるため検査を通るが、実行される program は `/bin/true` である。consumer は記録 TPS が performance binary から得られたと誤認して `accepted` を返す。

**直し方の方向**

producer が許す wrapper 列を含む exact argv grammar を検証し、期待 binary が実行対象位置にあることを要求する。

### 所見 4 — 対外診断点の正例テストは、束縛した job body が生成不能な root を受理している

**根拠 (file:line)**

fixture は off-pair genome に `BACKOFF_NOINLINE=1` を追加しながら、result を直接生成できます。`orchestrator/tests/test_t1998_stock_inline_pair.py:168-187,278-330`

その root を明示的に正例として受理しています。`orchestrator/tests/test_t1998_stock_inline_pair.py:475-478`

しかし実 job-body finalizer は canonical 8 genome の完全一致を要求し、診断 key が加わった genome では result を発行しません。`tools/pegasus/a5_second_boot_backoff_sweep.sh:649-690,723-725`

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

テスト自身の `_write_producer(tmp_path, off_pair_diagnostic_ordinal=1)` が具体例である。consumer は `accepted` を返すが、その root は preregistered job-body digest が表す A-5 finalizerから発行され得ない。

固定対の TPS 自体は同じでも、「束縛済み sanctioned producer の complete output」という provenance 結論が偽になる。

**直し方の方向**

他 6 点の TPS や configure 内容は読まず、genome identity の集合だけは A-5 の canonical 8 点と一致させる。これは内容評価ではなく producer stage-shape の束縛として扱える。

### 所見 5 — target の admission failure が baseline 原因として記録される

**根拠 (file:line)**

`require_admitted_campaign` の例外は一律 `_reject(...)` へ渡され、arm の既定値 `baseline` が使われます。`orchestrator/campaign/t1998_stock_inline_pair.py:251-260,675-684`

既存テストは最初の COMMIT を変異させるだけで、target 帰属を検査しません。`orchestrator/tests/test_t1998_stock_inline_pair.py:530-547`

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

target COMMIT の `commit_verification_receipt.receipt_id` だけを変異させ、result の WAL SHA を更新する。admission は正しく拒否するが、consumer の構造化結果は `arm="baseline"`、`field="certified_campaign_admission"` になる。

「target receipt が原因」という再検証可能な帰属を失い、baseline failure と誤記録する。

**直し方の方向**

global admission failure に baseline を代入しない。共通・帰属不能を表す arm を持つか、上流から構造化された offending variant を受け取る。後者は scope 外変更を伴うため、必要なら「scope 外・裁定パッケージ候補」とする。

### 所見 6 — queue preflight が別 queue の ENA / ACT を拾う

**根拠 (file:line)**

`gen_S`、`ENA`、`ACT` を出力全体で独立検索しており、同じ行に属することを要求しません。`tools/pegasus/submit_t1998_balanced_stock_inline.sh:68-77`

launcher 契約テストも文字列の存在だけを検査しています。`orchestrator/tests/test_t1998_launcher_contract.py:68-96`

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

`qstat -Q` が次を返す場合、検査は成功する。

```text
gen_S DIS INA
gen_L ENA ACT
```

停止中の `gen_S` を利用可能と誈認して qsub へ進む。6 passed はこの分岐を実行していないため検出しない。

**直し方の方向**

`gen_S` の一行を一意に抽出し、その行の ENA / STS 列だけを exact に検査する。

## 恒真・冗長になっている検査

| 拒否コード | 単独発火の状態 | 根拠 |
|---|---|---|
| `producer-artifact-missing` | 発火する | result、reservation、campaign 欠損で直接到達。`t1998_stock_inline_pair.py:288-309,623-673` |
| `producer-artifact-invalid` | mixed | JSON 不正は到達するが、lock decode / v2 authority 検査は certified admission 後なので安定した同一 bytes では先に admission が拒否する。`:713-724` |
| `producer-failure-receipt` | 発火する | admission 前に sibling を直接検査。`:625-630` |
| `result-contract-mismatch` | 発火する | result 単独変異で到達。`:635-644` |
| `producer-artifact-binding-mismatch` | mixed | result SHA、reservation、node は到達する。`admission.lock_sha256` / `admission.wal_sha256` は同じ bytes から view が算出済みで、実質 TOCTOU guard。`:696-710` |
| `repository-identity-mismatch` | 発火する | preregistration、result、reservation、lock authority の独立比較。`:727-755` |
| `gitlink-identity-mismatch` | mixed | result / reservation / lock は発火する。WAL gitlink は admission が既に `source.ccbench_commit == lock.ccbench_commit` を要求し、lock も先に prefix 検査済みなので単独発火不能。`:758-796`、`artifact_admission.py:1407-1419` |
| `environment-identity-mismatch` | mixed | lock 対 preregistration と non-COMMIT env tag は到達する。COMMIT contract digest は admission が lock 一致を先に要求するため冗長。`:434-447,797-802` |
| `launcher-script-identity-mismatch` | 発火する | reservation digest と preregistration の独立比較。`:803-813` |
| `source-identity-unbound` | 発火する | preregistered arm digest だけを変えれば到達する。ただし所見 1 の configure override は覆わない。`:449-467` |
| `diagnostic-build` | 発火するが不完全 | literal marker は単独発火する。`:476-488,828-834` |
| `performance-build-not-trace-disabled` | 発火するが一部が弱い | trace 値等は到達するが executable 条件は所見 3 の偽陽性を持つ。`:469-517` |
| `pair-value-mismatch` | synthetic root では発火する | admission 後の TPS / result projection 変異で到達する。genuine finalizer は一部を先に検査する。`:519-567,919-933` |
| `toolchain-identity-mismatch` | 発火する | target digest または manifest の差で到達する。`:569-581,903-917` |
| `preregistered-pair-mismatch` | 発火する | caller が canonical genome を違えて渡せば到達。arm 定数照合自体は恒真ではない。`:402-408` |
| `pair-cardinality` | 冗長、明記済み | genuine finalizer / admission が先行。`:366-388,843-860` |
| `producer-rejected-variant` | mixed | admission wrapper は発火する。後段の receipt 欠損、abort、stage 欠損は genuine finalizer / admission に先取りされる冗長 gate。`:582-595,675-684,843-881` |

追加の dead branch として、`_arm_decision()` の `expected_genome` は呼出し側から必ず固定定数が渡るため、`expected_genome` 内の `BACKOFF_NOINLINE=1` 検査は恒偽です。診断 genome は前段で処理されます。`orchestrator/campaign/t1998_stock_inline_pair.py:483-488,883-902`

テストは public admission と実 receipt 発行経路を使用していますが、source digest、result、reservation は fixture が直接構成しています。したがって source 解決と job-body finalizer の結合は通っていません。launcher の 6 test も全て source text の静的検査であり、queue parser や qsub 境界の実行テストではありません。揮発 payload を期待値へ固定する問題は見当たりません。

## 総括

blocking は三点です。

- typed CMake define による診断 build の headline 混入
- attempt 非帰属 anomaly による規律 2 の迂回
- argv 内の decoy binary token による性能 executable の誤帰属

加えて、off-pair 正例は sanctioned finalizer が生成不能な root を受理し、A-6 の arm 帰属と launcher queue preflightにも偽結論があります。親の緑はこれらの入力を通っていません。

静的検査のみを行い、file 変更、test、build、benchmark、測定は実行していません。現物は review 時点で commit `0df429a21`、作業木 clean でした。