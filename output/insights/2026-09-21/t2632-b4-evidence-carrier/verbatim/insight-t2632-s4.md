### 4.1 量の所在 (現存)

certified な走行の session-level throughput は WAL `commit.fitness_tps` と `bench_done.median_tps` / `tps[]` にあり (T-2102)、各 record は
canonical JSON の sha256 `wal:<sha256>` で一意に名指せる。**実装は 2 つある** — `agent_outputs.canonical_bytes` (`sort_keys` /
`ensure_ascii=False` / `separators=(",", ":")` / **`allow_nan=False`**) と `layer3_report._canonical_bytes` (同じ引数で `allow_nan` 指定なし)。
`layer3_report.canonical_record_ref` が `agent_outputs` の関数を呼ぶのは `ao` 経路だけで、`wal` 経路は独自実装を使う。現物の有限 JSON では
両者の bytes は同一で、本書の ref は `agent_outputs.canonical_sha256(vars(record))` で計算し、trigger の `layer3_report.runs[].source_ref` と
値が一致した (レビューが独立再計算)。非有限値の受理域だけが異なる。
3 campaign の certified 6 variant について (`verbatim/parent-edge-probe.json` の `reference_candidates`):

| campaign | variant | fitness_tps | env_tag | `bench_done.run_cmd` から読める PerfConfig | commit record の ref |
|---|---|---|---|---|---|
| base | `20bbb4c1a855` | 491,796.5 | linux-baremetal | threads 4 / records 100000 / extime 1 / clocks 1800 / rratio 50 / skew 0.9 / rmw false | `wal:9bce3bc47e9d1b603cf39733df061bb41fe8e4704234d239c0f60751cb10d989` |
| base | `27d1d016998e` | 525,721.5 | linux-baremetal | 同上 | `wal:98af80643f35475046303f0abedfd9dd4e0e2ced77eb353f17181fe888975e60` |
| base | `dad58f9f9000` | 487,088.5 | linux-baremetal | 同上 | `wal:6e598a426dee8bccd7ab65d7f0dc3b522323b064f4b7e9a56c582bc2742d0d47` |
| sort | `aa32126d769f` | 274,871.5 | linux-baremetal | 同上 | `wal:d3c74339da9f706053a6eaddcd1c0ab9290628495a5abb56526dae08744bcb98` |
| trigger | `e1785940172e` | 275,614.5 | linux-baremetal | 同上 | `wal:4f40b669b157d87ee69a2c7cf2995ae9f1700911513ab7147ac3f9983c111a1e` |
| trigger | `ca5206c3dac5` | 276,472.0 | linux-baremetal | 同上 | `wal:2d68cc8a15d25fe1bc5cd1d3af27fa8a76ba1bfdd242217442a437d371ff05fa` |

trigger の `layer3_report.json` の `runs[].source_ref` 2 件は、本書が再計算した `bench_done` record の ref と一致する
(`source_refs_match_bench_wal_refs = true`)。**この ref 形は現存し、消費側 (layer3) の先例もある。**

### 4.2 閉じない理由 3 つ

1. **object の不在。** `reference_snapshot_hash` / `reference_receipt_hash` が何の bytes の sha256 かを定める producer・定義が、照合した
   範囲に無い。根拠は module 名だけではない — `orchestrator/campaign/` に `snapshot` / `receipt` を名に持つ B-4 用 module も
   `throughput receipt` 型も無く、加えて B-4 参照 field (`reference_*`) の構築点を辿ると実祖先から構成する production producer は無く、
   事前登録 consumer の自己検査用 fixture だけである (T-2102 と同じ結論。レビューが独立に照合)。WAL record の canonical hash を
   receipt hash と**読む**ことはできるが、それは新しい定義 (裁定) であって現存資料の読み出しではない。
2. **祖先関係の不在。** 「precursor から祖先方向へ辿って最初に現れる certified」を決めるには precursor と各 certified の系譜が要る。
   3 campaign の WAL には `parent` / `ancestor` / `iteration` の文字列が無い (親の probe は WAL 文字列だけを検索した。loop_state には
   `iteration` が top-level と whiteboard 行にあり、文字列出現は base 5 / sort 2 / trigger 3 — レビューの再計数)。loop_state の `iteration` と
   行順は**順序の情報**ではあるが、それを proposal の祖先関係と定める契約は事前登録にも code にも無く、重複提案 (§3.1) は新しい評価を
   作らないので行順と評価の系譜は同一でない。行順で読むにしても辺 A の行 ↔ variant 対応が要る — それが base で壊れている。
   つまり不足は「順序情報そのものの欠落」ではなく「既存の順序の意味と、行 → attempt の対応の未確定」である。
3. **一致条件の不成立。** §5.1.1 は receipt を `PerfConfig` と `env_tag` の一致で特定する。`PerfConfig` (`pipeline.PerfConfig`) は
   `records / threads / workload / extime / reps` の 5 field で、`bench_done.run_cmd` から読めるのは threads・records・extime と workload の
   3 key (rratio / skew / rmw) だけである — **`reps` は宣言値として現れず (`tps[]` の長さから推定できるだけ)、`ycsb_max_ope` は run_cmd に
   無い。** 現物 6 variant は `env_tag=linux-baremetal`・`default_perf()` の動作点 (records 100000 / threads 4 / extime 1 / reps 2) であり、
   §5 の 2 欄が Pegasus 較正値 (records 1M / 1M / 2M、threads 48、`env_tag=pegasus`) で記入されれば一致し得ない。つまり現物の certified 行は、
   B-4 本走の参照点には**なれない**ことが今日の時点で確定している — D2150 項 2 (2026-09-18) が B-4 本走の site を Pegasus 計算ノード・
   tag `pegasus`、`PerfConfig` を較正 3 件の出力値 + 復元値 + 選択値 (reps 候補 5 は候補のまま) で確定している (記入は D1483 の順序後)。

### 4.3 判定

**閉じない。** 参照点の object (何を snapshot / receipt と呼び何の bytes を hash するか) と祖先関係 (同 campaign の whiteboard 順序か、
別の系譜か) の**定義**が先に要り、定義後に carrier (辺 A と同じ side channel に `reference` 欄を持たせるのが自然) が要る (§7 の裁定 2)。
