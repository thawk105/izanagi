# [T-402] cross-node flock は排他された — Execution Host 照合まで通して確定

**実測日:** 2026-08-16 (JST)。**対象:** [T-402] (= [T-361] / D130 条件 2)。
**事前登録:** `verdict-preregistration.md` (実測前に commit 済み。実測後に編集していない)。
**anchor commit:** `f8e81568` (driver 実装 + 事前登録)、実走時 HEAD `b8a0e226` (main 取り込み後)。

---

## 1. 結論

`bnode003` と `bnode004` の間で、`/work` と `/home` の `flock` は **silent fail-open していない**。

| field | 値 |
|---|---|
| `dangerous` | **`false`** |
| `overall_verdict` | `BLOCKED_EXPECTED` |
| `result_state` | `FINAL` |
| `valid_for_safety_conclusion` | `true` |
| `errors` | `[]` |

凍結した 5 条件はすべて成立した (`authority_receipt`)。

| 条件 | 値 | 意味 |
|---|---|---|
| `A_observation_and_terminal` | `true` | `observation_valid` かつ `external_root_terminal_proven` |
| `H_execution_host_binding` | `true` | qstat の Execution Host と job marker の一対一照合が成立 |
| `S_probe_self_checks` | `true` | probe の自己検査が全通過 |
| `E_localflock_absent` | `true` | どちらの mount にも `localflock` が無い |
| `B_all_raw_outcomes_blocked` | `true` | raw outcome が各 6 件・全件 `BLOCKED` (controller が raw から再導出) |

**前回 (2026-08-03、request 882038) との差は、`H` が初めて `true` になったことだけである。**
`/work`・`/home` の 6/6 `BLOCKED` 自体は前回も観測されていたが、
「その 2 つの観測が本当に別ノードで起きた」ことを束縛できず `dangerous` は `null` だった。

## 2. Execution Host 照合の中身

| field | 値 |
|---|---|
| `execution_hosts_raw_order` | `["bnode003", "bnode004"]` |
| `execution_hosts_normalized_order` | `["bnode003", "bnode004"]` |
| `marker_host_set` | `["bnode003", "bnode004"]` |
| `one_to_one_job_number_host_binding` | `true` |
| `execution_host_validation.valid` | `true` |
| `execution_host_validation.errors` | `[]` |

qstat 側 (`Batch Job Number` → `Execution Host`) と compute node が書いた job marker
(job number と hostname) が、job number ごとに一致した。

## 3. filesystem 別の観測

| filesystem | `verdict` | `dangerous` | `localflock_absent` | raw outcome (6 件) |
|---|---|---|---|---|
| `/work` | `BLOCKED_EXPECTED` | `false` | `true` | `BLOCKED` × 6 |
| `/home` | `BLOCKED_EXPECTED` | `false` | `true` | `BLOCKED` × 6 |

`verdict` は producer の派生 field の転記ではなく、**controller が raw outcome list の型・件数・値を
検査して再導出した値**である (段 6 レビュー A #5 の指摘を受けた変更)。

## 4. 真因 — なぜ前回は確定できなかったか

**controller の実行時欠陥 (NameError) ではなかった。** 本 wave の段 4 で 3 点の実測により確定した。

1. 実際の `qstat -J -f` は `Request ID:` block 内に**単数形** `Execution Host = <host>` を出す。
   証拠 = `../2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/`
   `attempts/t362-mitigation/20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/`
   `raw/00025-lifecycle-qstat-attempt-1.stdout.raw`
2. 旧 parser が fullmatch を要求した見出し `Execution Hosts(JSVNO):` は、
   保存 evidence 全体で**出現 0 件**。さらに `"=" in stripped` で走査を打ち切るため
   実際の行は構造的に読めなかった。
3. **健全に完走した request 887918 (authoritative と判定された attempt) でも**
   `monitor.execution_hosts_raw_order` は `[]`、`execution_hosts_raw_evidence` は `null` だった。

2026-08-03 の attempt の保存 raw は `rbudgetcheck` / `qsub` / `qwait` の 3 command だけで、
**qstat には一度も到達していない**。したがって NameError は独立した別の欠陥であり、
**修正済みでも本件は直らなかった。素の再走は何度でも `dangerous: null` に終わっていた。**

## 5. 結論の射程 (事前登録どおり)

- **exact host pair は `bnode003` / `bnode004`。** 前回の `bnode001` / `bnode005` とは別である。
  PBS に host selector は無く、scheduler が割り当てた 2 台である。
- **当該 mount signature:**
  `/work` は Lustre で `rw,flock,user_xattr,lazystatfs,encrypt` (`localflock` は無い)。
  raw = `.../work/recon/mounts/proc-mounts.*.raw`。
- **gen_S 全体へ一般化しない。** 将来の kernel / mount 変更にも一般化しない。
- **この結果だけでは D130 条件 2 は閉じない。** 条件 2 が要求するのは
  「同一 repo で同時 1 本」の保証が bnode 間で成立することであり、
  1 host pair の 1 回の観測はその十分条件ではない。
- **D131 共通前提 1 (shared / legacy lock の移行と、移行期間に二重走行の窓を作らないこと) も
  閉じない。** 本 wave は移行窓に一切触れていない。
- probe 自身も同じ制約を `scope_limitations` に記録している
  (`Conclusions cannot be generalized beyond the recorded host pair, kernel, and mount snapshot.`
  ほか)。

## 6. 単独性 (未確認と記録する)

`#PBS -b 2` は 2 job の要求であって**ノード専有の証明ではない**。
本 attempt は各 execution host における**同居 job の snapshot を取得していない**。
したがって**単独性は未確認**である。専有を主張しない。
`flock` の排他観測はノード占有に依存しないため、この未確認は本 wave の結論を弱めないが、
所要時間や性能値を語る材料には使えない。

## 7. 資源

| 項目 | 投入前 | 投入後 | 上限 |
|---|---|---|---|
| request 数 | 4 | **5** | 6 |
| requested node-min | 19 | **29** | 40 |
| flock one-shot 消費 | 0 (field 不在) | **1** | 1 |

- 投入した request = `912550.nqsv`、leg = `t361-flock`、attempt = `...-t361-flock-a2-976fc6bbfdbb5894`、
  `submission_mode` = `flock-leg-only`、`admissible` = `true`。
- **`t362-mitigation` の authority は無傷**である
  (`authoritative_attempts` に `t361-flock` が追加されただけ)。
- `t362-default` / `t362-split-warning` は投入していない。

## 8. 証拠の所在

**raw evidence は旧 canonical root に残る** (controller の実装がそこへ固定して書く)。
本 insight は複製せず path で参照する。

- session: `../2026-08-03_t361-t362-cluster-probes/evidence/20260815T165532Z-203e1b799097dbd0/`
- attempt: 同 `attempts/t361-flock/20260815T165533Z-t361-flock-a2-976fc6bbfdbb5894/`
- 判定: 同 `work/controller/t361-finalized-result.json`
- probe 生結果: 同 `work/flock-result.json`
- mount raw: 同 `work/recon/mounts/`
- job marker: 同 `work/recon/job-markers/`

## 9. 検査

- driver 評価器テスト **126 passed** (計算ノード dispatch、request `912494.nqsv`)。
- 変異 matrix **6/6 KILLED、期待 node 完全一致** (`mutation-ledger-final.json`)。
  初回は期待 node 未確定のため probe とし、M1 (3 件) と M3 (2 件) の完全集合を実測で確定して
  再登録・再走した (erratum は §10)。
- `check_docs.py` / `check_ai_provenance.py` (全史) はいずれも緑。
- **受入全走は対象外。** production コードの差分はゼロであり、変更は
  `output/insights/**/driver/` 配下の使い捨て probe と test・README、および本 insight だけ。
  射程はエントリ (128) / (149) / (191) と同じ。

## 10. erratum — 変異期待 node の実測併合

初回の変異走行 (`mutation-ledger-probe.json`) では、親が推定した期待 node が M1 / M3 で不足し
`MISMATCH` になった。**初回を probe と明記し、実測した完全集合で再登録して再走した**
(`DW-M08` の手順)。初回の結果は消していない。

| 変異 | 初回の推定 | 実測した完全集合 |
|---|---|---|
| M1 | 1 件 | **3 件** (`..._rejects_two_job_pairs_in_one_target_block`, `..._rejects_three_target_blocks`, `test_safe_verdict_rechecks_exact_qstat_target_block_count`) |
| M3 | 1 件 | **2 件** (`test_flock_only_does_not_bypass_initial_point_gate`, `test_flock_only_target_is_exactly_t361_and_excludes_t362`) |
| M2 / M5 / M7 / P1 | 1 件 | 1 件 (推定どおり) |

初回・再走とも**全 6 変異が検出されている** (初回も失敗 node は 1 件以上あった)。
差は期待集合の完全性だけである。

## 11. 本 wave で親が犯した誤り (記録)

1. **(P3) の誤り。** 段 1 brief は「前回 host が空だったのは controller の NameError が原因」と
   書いたが、段 4 の実測で反証された (§4)。段 2 プランと段 3 レンズ A が独立に反証した。
2. **凍結済み事前登録に反する指示。** 段 6 fix 2 巡目で親は「1 block に 2 組の job/host も
   受理せよ」と指示した。しかし `verdict-preregistration.md` の `H` は
   「対象 block がちょうど 2 件」と**親自身が直前に凍結していた**。
   焦点再レビューが事前登録違反として検出し、親は指示を撤回した (fix 3 巡目 H2)。
   **結果として実測は凍結どおりの 2 block 形式で通っている。**
3. 段 6 fix 2 巡目が `_saved_submission_validation` の意味を変え、
   wave 開始時から存在した fail-closed テストを赤にした。fix 3 巡目で HEAD の意味へ戻した。
