## 前回 6 件の対応

1. **closed** — ゼロ abort 規則は分類表の先頭へ統合された。[§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:291) は「**上から順に判定する。先に当たった分類を採り、後の分類は見ない**」に続けて、両端全ゼロを `saturated`、正値から全ゼロを `declining` とする。分散なしは「**1・2 に当たらず**」に限定され、§5 も `"single_table_no_separate_zero_abort_table": true` と同順序である。

2. **closed** — [§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:297) は分散なし区間について「`qL` / `qU` / `U` / `L` / `U_flat` を**すべて `null`**」と逐語化し、[§5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:757) も同じ 5 field を null とする。

3. **closed** — [§4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:338) の後二状態はともに「**`indeterminate` が 0 件**」を含み、persistent location の存在と不存在が互いの否定になった。§5 の `indeterminate_interval_count == 0` も一致する。workload 状態は評価順なしでも排他的である。

4. **closed** — [§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:322) は `j=1` を「1250 マイクロ秒以下」「下端なし」「左側打切り」とし、「位置を `1250` という点として報告してはならない」と明記した。両側 bracket の最左は `1768`、`[1250,1768]`。§5 も同じである。

5. **partial** — [§5 `analysis_input_contract`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:620) に多くの `wal_stage` / `payload_key` は加わったが、`backoff_us` だけは両方を欠く。また必須 provenance 8 field 中 `source_measurement` は `fields[]` 自体に無い。counter の `"payload_key": "to-be-added-per-rep-by-the-formal-driver"` と `rep_index` の `"position-in-the-tps-array..."` は実在 key ではない。したがって「各 field へ付けた」は成立していない。

6. **closed** — [§8.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:1002) は投入前条件を、consumer 発火、性能 counter 永続化、observation provenance、5 verify records/cell、correctness mode 座標の記録と比較、の 5 件へ増やした。§5 の 5 要素とも一致する。

## 破壊の試み

### 1. 全域性

区間分類について、次の境界入力を試した。

- 両端とも abort `[0,0,0,0,0]`、commit `[10000,10000,10000,10000,10000]` は規則 1 の `saturated`。
- 左端 abort `[995,998,1000,1002,1005]`、commit は各値との和が 10000、右端 abort は全ゼロ、commit は全 10000 とすると規則 2 の `declining`。
- 左端 abort `[1000,1000,1000,1000,1000]`、commit 全 9000、右端 abort 全 900、commit 全 9100 は正値・分散和ゼロなので規則 3 の `indeterminate`。
- 左端全ゼロ、右端 abort 全 10、commit 全 9990 は対数前に `invalid`。
- 通常の正値・正分散区間は、`U <= 0.05`、`L > 0.05`、残余の三分岐で覆われる。

したがって、**分類名、workload 状態、選択後の aggregate verdict 自体に未分類入力は作れなかった**。ただし上記の正値から全ゼロへ落ちる正常入力では、`declining` は決まる一方、`qhat/qL/qU/U/L/U_flat` の値が決まらない。[§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:293) は規則 1 を 0、規則 3 を null とするが、規則 2 には値がなく、315 行の「0 または null」からも一方を選べない。**完全な report 出力としての全域性は破れた。**

### 2. 一意性

- ゼロ abort の 3 規則は、規則 3 の「1・2 に当たらず」により条件自体が排他。
- 通常区間は `qL <= qU` から `U >= L` なので、`U <= 0.05` と `L > 0.05` は同時成立しない。
- workload 状態は `indeterminate == 0` と persistent location の存在・不存在により、評価順なしで排他。
- 非 `invalid` の aggregate 4 規則も workload 状態の直積上で排他。

一方、aggregate の `invalid` は他の数値状態と同時成立する。たとえば全 tail cell が全ゼロで各 workload は `saturated` でも、後述する workload 座標不一致が failure 17 を成立させる。この場合、raw 条件では `invalid` と `saturated-in-all-workloads` が重なるが、[§4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:347) と §5 の `first-match-wins` により選択結果だけは `invalid` に一意化される。したがって「上から順」で救っているのは `invalid` との重なりであり、「複数の verdict を同時に満たす状態は存在しない」は raw 条件については偽である。

### 3. 散文と spec

- **real:** [§4.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:199) の workload 座標 5 / 50 / 95 と、[§4.9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:418) および [§5 `cohort_identity`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:866) の「`workload_coordinates` を 3 lock 間で一致」は衝突する。正しいのは、各 job が自分の登録行へ一致し、3 job の集合が 5 / 50 / 95 を成すという §4.2 と failure 16 の側である。
- **real:** [§0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:13) の「placeholder は無く、すべての値が確定」と、§5 の `"to-be-added-per-rep-by-the-formal-driver"` は両立しない。正しい契約は §0 であり、§5 が exact key を固定すべきである。
- **real:** 正値から全ゼロの診断値は散文・JSONとも未確定。分類 `declining` は正しいが、対数を取らないなら各 slope/effect field を null とするなど、値を明示する必要がある。
- **real, nit:** [§4.1 の最初の記載](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:172) は正しい `0.34642〜0.34673` だが、同節後半は `0.3464〜0.3467` とし、実最大 `0.346724613` を含まない。前者が正しい。
- **refuted:** §7 の散文 18 項と §5 の 23 item は、散文 13・15・binary 取り違えを分割した差であり、失敗集合の差ではない。
- **refuted:** [地図](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:29) の 7 点＋境界 1 点、3 分割、上限継続、投入前条件という要約は本体構造と一致する。ただし workload 座標の矛盾により、そこで案内する非 `invalid` 結末は現状では到達不能である。
- **refuted:** §6 の多重度・参考値、§9 の主張範囲には新しい食い違いを作れなかった。

### 4. 到達不能

failure 17 を無視すれば、主要状態はすべて構成できる。

- `saturated`: 全 7 tail cell で abort を `[0,0,0,0,0]`、commit を全 1000000、throughput を `[999000,999500,1000000,1000500,1001000]` とする。全区間が saturated、`j=1`、位置は「1250 以下」の左打切りになる。
- `not-observed`: 各 `b_1..b_7` の平均 abort count を `[320000,160000,80000,40000,20000,10000,5000]` とし、各 cell の 5 rep を `[M-20,M-10,M,M+10,M+20]`、commit を `1000000-abort` とする。最大 abort CV は約 0.00316、各区間はほぼ半減なので全て `declining` となり、persistent saturation は存在しない。

これを登録どおり 3 workload へ複製すると、read ratio は 5 / 50 / 95 になる。ところが §4.9 と JSON は `workload_coordinates` の相互一致を要求するため failure 17 が必ず発火し、aggregate は両例とも `invalid` になる。したがって現行 spec では、`saturated-in-all-workloads`、`not-observed-in-any-workload`、混在 verdict、`indeterminate-in-region` の**全てが実質到達不能**である。

探索の実 lock も実際に `ycsb_rratio` が [write-heavy の 5](/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-write-heavy/campaigns/t2418-backoff-static-explore-v1-silo-write-heavy-sweep-c9cea61a/campaign.lock:1)、[balanced の 50](/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8/campaign.lock:1)、[read-heavy の 95](/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-read-heavy/campaigns/t2418-backoff-static-explore-v1-silo-read-heavy-sweep-a3c44399/campaign.lock:1) と異なる。

### 5. 過剰な失敗

探索成果物を丸ごと formal 入力へ流用すると、少なくとも §7 の 1、3、4、5、6、11、12、15、16 が発火する。1 verify/cell、性能 counter 不在、印字 abort 率、3 static 点だけ、探索標本、`t2418-explore` という出所、formal hash 不在、格子・順序違いによるもので、いずれも探索流用を拒否する正しい発火である。

数値だけを見ると、探索 static 点の throughput CV は 0.001822〜0.006508、量子化 abort 率からの参考 CV 最大も 0.0061515 で、failure 7 は発火しない。[write-heavy report](/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-write-heavy/campaigns/t2418-backoff-static-explore-v1-silo-write-heavy-sweep-c9cea61a/reports/t2418-backoff-static-explore-write-heavy.json:1) など 3 report と一致する。全 15 `verify_done.payload.workload.tag` は `legacy` なので failure 18 も発火しない。

**過剰なのは failure 17 だけである。** registered workload 座標が異なるという正常事実を cohort identity mismatch にしてしまい、探索流用だけでなく正常な formal cohort も殺す。

### 6. field 出所

現物 WAL の stage は `build_start`、`build_done`、`verify_done`、`bench_done`、`commit` の 5 種だけである。代表例は [balanced WAL](/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8/runs/wal.jsonl:1)。

| field | 現物との照合 |
|---|---|
| `throughput_tps_reps` / `throughput_tps_cv` | 一致。`bench_done.payload.tps` / `.cv`。 |
| `trace_disabled_binary_sha256` | 一致。`build_done.payload.perf_bin_sha256`。同じ record に別値の `trace_bin_sha256` もある。 |
| `canonical_genome` | 一致。`build_start.payload.genome`。 |
| `attempt_id` | 一致。`build_done.payload.build_attempt_id`。 |
| correctness の `certified` / `anomalies` / mode | key は一致。`verify_done.payload.certified`、`.anomalies`、`.workload.tag`。mode の現物値は全件 `legacy`。 |
| performance counter 配列 | 不在。`bench_done` にあるのは `tps` と単一の `leading_indicators.abort_rate`。文書自身の開示どおり。 |
| `backoff_us` | `fields[]` に `wal_stage` / `payload_key` がない。現物は `build_start.payload.genome` の `BACKOFF_FIXED` raw を decode して得る。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1047) もこの経路である。 |
| `rep_index` | `bench_done` にその key はない。現 report の `reps[].rep` は transient capture を `enumerate` して生成されるだけで、WAL へ残らない。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:817) |
| `correctness_verify_records` | field 型は `array[5] of record` だが `payload_key` は scalar の `certified`。record 集合の source path になっていない。 |
| `correctness_anomalies` | formal では 5 record から 5 値が出るのに型は単一 `integer`。配列・合計・最大のどれか未定義。 |
| `source_run_kind` | `campaign-envelope` という WAL stage は無い。現物は `campaign.lock.identity_preimage` を JSON parse した `.search_config.run_kind`、または非権威 report の top-level field。 |
| `campaign_id` | WAL payload には無く、現実装は campaign directory の basename から得る。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1041) |
| `campaign_lock_digest` / `wal_record_digest` | 現物に同名 key はなく、raw bytes・canonical JSON・admitted representation のどれを hash するか未定義。 |
| `source_measurement` | provenance では必須だが `analysis_input_contract.fields[]` に無い。現 report には `trace_disabled` があるが、report verdicts は非権威とする契約と衝突する。 |

### 7. 新しい矛盾

- 修正 1 は分類衝突を閉じたが、正値から全ゼロの診断値を未定義のまま単一表へ持ち込んだ。
- 修正 5 は `"to-be-added..."` という未確定 key を導入し、§0 の「placeholder は無い」と衝突した。
- 修正 6 の mode 座標は現物 WAL に既に `legacy` として存在する。§8.1 の「report には無い」は事実だが、権威を WAL とした §4.6 との関係では report 不在を source 不在と扱ってはならない。
- 修正 2、3、4 自体には別の回帰を作れなかった。
- workload 座標の相互一致問題は今回の 1〜6 が持ち込んだものではないが、前回監査で見落とされた real defect である。

## 新しい所見

### [real] [must-fix] 正常な 3 workload が failure 17 で必ず無効になる

根拠: [§4.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:199) は read ratio 5 / 50 / 95 を登録する一方、[§4.9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:418) と §5 は `workload_coordinates` を 3 lock 間で一致させる。

成果物影響: 正常な全 formal cohort が `invalid` となり、全ての科学的 aggregate verdict が到達不能になる。

docs-only 修正: 相互一致集合から job 固有座標を外し、各 lock が対応する登録行へ一致し、3 job の集合が write-heavy / balanced / read-heavy を重複なく全て含む、とする。

### [real] [must-fix] field-source 修正は coverage と exact path の両方が未完

根拠: [§5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:620) で `backoff_us` は stage/key を欠き、必須 `source_measurement` は mapping 自体がない。counter と `rep_index` の `payload_key` は key ではなく説明文で、campaign/WAL digest の導出 bytes も未定義である。

成果物影響: 同一 WAL を consumer A は導出可能として受理し、consumer B は source 不明として failure 15 または `any_field_without_a_resolvable_source` で拒否できる。

docs-only 修正: 各 field に actual stage、exact dot path、配列からの対応規則、hash 対象 bytes を固定し、future key にも最終的な literal 名を与える。

### [real] [must-fix] 正値から全ゼロの正常区間で診断出力が total でない

根拠: [§4.4 規則 2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:293) は `declining` と「対数を取らない」だけを定め、規則 1 の 0、規則 3 の null に相当する値を定めない。§5 も `"reduction is complete"` だけである。

成果物影響: 同一の positive-to-zero observation から、診断 field の省略、0、null、非有限値という異なる report が生成できる。

docs-only 修正: 分類は `declining` のまま、少なくとも `qhat/qL/qU/U/L/U_flat` の各値を明示する。対数を取らない契約と JSON 安全性からは、理由付き null が最も一貫する。

### [real] [nit] aggregate の raw 条件は排他的ではない

根拠: failure と数値 workload 状態は同時成立できる。正しい一意化根拠は `first-match-wins` であり、「複数の verdict を同時に満たす状態は存在しない」という散文ではない。

成果物影響: 選択 verdict は変わらないが、条件排他性を検証する consumer や説明文の解釈が変わる。

### [real] [nit] 半オクターブ対数比の旧丸めが 1 か所残る

根拠: [§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:183) の `0.3464〜0.3467` は実最大 `0.346724613` を含まない。同節 175 行の `0.34642〜0.34673` が正しい。

成果物影響: 格子・受理集合・verdict は変わらず、説明値だけが変わる。

## 総括

前回修正 1〜4・6 は closed、field 出所の修正 5 は partial である。  
最重要 defect は workload 座標の相互一致で、正常な 5 / 50 / 95 cohort を failure 17 が必ず無効にする。  
したがって現在は `saturated` と `not-observed-in-any-workload` を含む全非 `invalid` 集約 verdict が実質到達不能である。  
区間・workload の数理分類自体は排他的かつ全域だが、positive-to-zero の診断値と WAL source path は未完である。  
read-only の `jq` / `grep` による静的照合のみで、pytest・本走・コード変更は行っていない。