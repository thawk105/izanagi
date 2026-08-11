# 段 4 裁定 (親) — [T-756] FN-1 witness 検査

base = f4db7036 / ccbench pin d706650 (不変) / 実装面は Codex `role=author` が書く

## A. レンズ 2 (luna) の所見 — 親が独立に検算した結果

| ID | 判定 | 採否 | 親の検算 |
|---|---|---|---|
| L2-1 TPCC/BoMB は counter 増分前に `quit` を見る | **real** | **採用 (scope 内)** | `external/ccbench/include/tpcc.hh:110`–`112` を実読。`if (loadAcquire(tx.quit_)) return;` が `local_commit_counts_++` の**前**にある。YCSB (`ycsb.hh:160`–`167`) には同じ検査が無い。非対称は実在 |
| L2-2 `trace_dir` 再利用 + open 失敗で前 run の trace が残る | **real** | **採用 (scope 内)** | `trace.hh:49`–`62` は `open` の成否を見ない。pipeline は毎回 `mkdtemp` なので現行は安全だが、`_run_trace` の契約側に前提が書かれていない |
| L2-3 `parse_bench_stdout` の重複 last-wins | **real / blocker** | **採用 (scope 内)** | `calibrator/benchparse.py:26`–`36` を実読。`out[label] = value.strip()` で重複を拒否せず後勝ち。CCBench 正常出力は 1 回だけなので、重複は破損か注入の徴候 |
| L2-4 S2 calibration の verifier CLI に witness が渡らない | **real** | **採用 (scope 内)** | `s2_verify_calibration.py:130` が `commits` を既に取得済みで、`:155`–`:178` の CLI 起動には渡していない。**渡すコストが 2 行** |
| L2-5 新 abort reason が `LIVENESS_REASONS` に無い | **real** | **採用 (scope 内)** | `critic/digest.py:119`–`122` は 5 個のみ。未登録 reason は `other` へ落ち、variant・workload の帰属が消える = **規律 3 違反** |
| L2-6 変異表に新規 4 面の変異が無い | **real** | **採用** | 下の変異事前登録へ 4 件追加する |

**レンズ 2 が「破れなかった」と報告し、親が採用する事実:**

- `local_batch_commit_counts_` は本 pin の tree で**増分箇所が存在しない** (`result.hh:16`–`20`、
  `result.cc:685`–`690` の宣言・集計のみ)。よって `batch_commit_counts_ != 0` を fail-closed に
  しても**現在緑の run が赤になることはない**。親の懸念 (受入全走が丸ごと赤) は refuted。
- `parse.py:105`–`116` の last-wins は `dup_txids` を立てるので、同一 trace 内の重複 C は
  `len(txns)` 比較だけでは false-green にならない。
- 凍結証拠の byte pin は `raw-manifest.json` の `correctness/verifier.json` hash であり、
  witness なしの `result_to_dict` を不変に保つ限り再凍結の実機再走は不要。

## B. 裁定 (プラン v2 への差分)

段 2 プラン (`s2b-plan.md`) を基本採用し、次を**追加必須**とする。

1. **[L2-3 対応] witness 抽出は重複を fail-closed にする。** `commit_counts_` /
   `batch_commit_counts_` は `#` 前置でない行がそれぞれ**ちょうど 1 行**のときだけ受理し、
   0 行・2 行以上・非整数・負数はすべて `trace-no-commit-witness` で拒否する。
   `parse_bench_stdout` の辞書を witness の権威にしてはならない (last-wins が値を静かに変える)。
   **同 helper は pipeline 側に置き、既存の `benchparse` は変更しない** (計測層の consumer が他にある)。
2. **[L2-1 対応] 不変条件の前提を機械で pin する。** 「commit 後に無条件で counter を増やす」のは
   YCSB workload だけである。witness 検査を通す run は YCSB 由来であることを `_run_trace` の
   入口で fail-closed に確認する (trace binary の basename が `ycsb_` で始まること)。
   前提を満たさない binary は `trace-witness-unsupported-workload` で拒否する。
   **述語は「YCSB を許可」の allowlist 形とし、非 YCSB を黙って素通しする形にしない。**
3. **[L2-2 対応] witness run は空の trace_dir を要求する。** `_run_trace` の冒頭で
   `trace_dir` 内に `trace_*.log` が 0 件であることを確認し、非 0 なら fail-closed で拒否する
   (現行 pipeline は `mkdtemp` なので挙動不変、契約が明示されるだけ)。
4. **[L2-4 対応] S2 calibration も閉じる。** `verifier/cli.py` に `--expected-commits <int>` を
   足し (**単一 trace_dir のときだけ受理し、複数 dir と併用されたら rc 非 0 で拒否**)、
   `s2_verify_calibration.py:155`–`178` の `_verifier_run` へ `:130` で既に取得済みの `commits` を
   渡す。これで verify を通す live 経路の witness 未装備は pipeline / S2 の 2 系統ともゼロになる。
5. **[L2-5 対応] 新 reason を critic へ登録する。** `critic/digest.py` の `LIVENESS_REASONS` と
   `_LIVENESS_HINTS` へ新 reason 3 個 (`trace-no-commit-witness` /
   `trace-batch-commits-unattributed` / `trace-witness-unsupported-workload`) を追加し、
   `extra` に witness の期待・観測値と workload を載せる (規律 3)。
6. **[プランへの訂正] `_run_trace` の返り値は位置 5-tuple にせず `NamedTuple` にする。**
   位置 4/5 の取り違えは変異 10 が示すとおり静かに通る形であり、`typing.NamedTuple` は
   新 module も schema も増やさない (規律 5 に抵触しない)。既存 consumer は属性名で読む。

## C. 親 brief の訂正 (プランと レンズの指摘を採用)

- 「不一致なら indeterminate」→ **普遍なのは `certified=False`**。cycle が共存すれば verdict は
  `non-serializable` のまま。brief §2 S-1 の記述を訂正する。
- (P1)「witness は T marker より強い」→ **「通常 commit の個数完全性について強い」に限定**。
  FN-2・count 保存型の破損・別 run の stdout 誤結合は検出しない。
- 「部分 trace が certified」→ 条件付き。欠落後の残存 txid が `0..max` に見え、既存 integrity が
  clean で、残存 DSG が acyclic な場合に限る。
- DW-O09 の凍結証拠は **dict 等値比較**であって literal byte 比較ではない。byte 不変性は
  新設する専用 regression テストで別に固定する。
- (P2)「optional 側が fail-open にならない」は**成立しない**。上の裁定 4 で live 経路 2 系統を
  閉じたうえで、「直接 API と CLI の witness 省略呼び出しには旧挙動が残る」と明記する。

## E. レンズ 1 (sol) の所見 — 親の裁定

| ID | 判定 | 採否 |
|---|---|---|
| L1-11 変異 1 と 11 は生き残る (3/4/10 は帰属非一意、6 は条件付き) | **real / 最重要** | **採用。実効 gate へ再照準 (F28/DW-M01)** |
| L1-2 ladder が保存済み witness を捨てて certified evidence を作る | **real / blocker** | **採用 (scope 内)。凍結 `verifier.json` は変えず外側 gate で照合** |
| L1-3 既存 WAL の witness なし COMMIT が replay/guided で再流通 | **real / blocker** | **scope 外 → 裁定へ返す** (受理集合と campaign identity の変更) |
| L1-4 CLI 経由の coverage 系 4 driver が witness なし certified を材料値にする | **real** | **一部採用**: CLI flag と S2 は採用。coverage 系 4 driver は **scope 外 → 裁定へ返す** |
| L1-6 witness parser の一意性 | real | 採用 (L2-3 と同一。ladder の `silo_ladder_rung1.py:798`–`803` が厳格 parser の先例) |
| L1-7 witness は failure-independent ではない (common-mode) | **real** | **採用。「独立 witness」の語を捨て「trace 外 counter による個数 corroboration」と書く** |
| L1-8 新 reason が `s8b_abort_reason_contract.py` にも無い / renderer が integrity を隠す | real | 採用 |
| L1-9 出力形状 pin は 6 件 (親は 1 件) | real | 採用。consumer inventory を 6 件で確定 |
| L1-5 診断順序の変化 | nit | 採用 (matching witness + 既存 integrity-red の対照テストを足す) |
| L1-12 5-tuple と 2 つの独立 Optional の部分状態 | real | 採用。frozen dataclass + witness の both-or-none |
| L1-10 FN-2 権限外の認定は正しい | nit | 追認 |
| L1-13 batch 非 0 拒否は現行の緑を赤にしない | nit | 追認 (レンズ 2 と一致) |

**L1-2 を scope 内にする根拠 (DW-G04)**: 発火する実成果物が既に存在する —
`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/run.stdout:15`
の `480595` と同 `verifier.json:13` の `txns=480595`。新 gate は受入全走で実データに対して発火し、
両者が一致するので緑になる。凍結 bytes は 1 bit も変わらない。

**L1-3 / coverage 系 4 driver を scope 外にする根拠**: 前者は既存 COMMIT の受理集合と campaign
identity を変える裁定である。後者は 4 本のうち 3 本 (`s3_lock_coverage` / `s5_permutation_coverage` /
`s8a_trigger_coverage`) に**テストが 1 本も無く**、受入全走で検証できない変更になる。かつそれらの
`stock_silent_certified` / `skeleton_certified` は既に insights へ公表済みの材料値であり、
下に敷く gate を変えるのは材料主張の再解釈にあたる。

**DW-G05 (実装しない場合の成果物影響)**: coverage/oracle の `stock_silent_certified` /
`skeleton_certified` は、末尾欠落した trace でも真になりうる。既発行 insights の材料値はこの限界を
持つ。既存 campaign の受理集合・winner・fitness・guided の `final_pick` は新 gate 導入後も不変。

## F. 変異事前登録 (DW-M01。逐語 `old` は段 6 の最終 commit で確定させる = DW-M07)

schema = `izanagi-dev-wave-mutation-spec/v1`、key は 6 個固定
(`id` / `category` / `replacements` / `expected_status` / `expected_nodes` / `hang_risk`)。
全件 `expected_status=KILLED`・`hang_risk=false`。

| id | 位置と改変 | 単一理由性 | 期待して落ちる node |
|---|---|---|---|
| M01 **wave 前の形** | `verifier/core.py`: `observed_commits = len(txns)` → `= expected_commits` (恒等的に一致 = 実質無検査) | 前後に同入力を拒否する層なし (残存 txid 密連番・acyclic・他 integrity clean) | tail-gap 反転テスト |
| M02 | `verifier/model.py` `clean()`: commit-count 一致節を削除 | 同上 | 欠落注入 positive control |
| M03 **過剰拒否 正例** | `verifier/model.py` `clean()`: `==` → `!=` | 完全 trace + 正しい witness で他に赤要因なし | negative control (完全 trace が certified のまま) |
| M04 | `verifier/report.py`: `commit_witness` を witness 無しでも無条件挿入 | 判定層を通らない直列化 | byte regression + ladder recompute equality |
| M05 | `verifier/report.py`: `delta` を `expected - observed` に符号反転 | verdict 不変、完全一致 assert のみ赤 | 構造化 dict 完全一致テスト |
| M06 | witness parser: 重複行を last-wins で受理 | 重複 stdout 以外に赤要因なし | 重複 stdout control |
| M07 | witness parser: 欠落を `None` でなく 0 として受理 | | `trace-no-commit-witness` control |
| M08 | pipeline: batch 非 0 guard を `if False` | main witness を trace と一致させるので後段も緑 | batch 非 0 control |
| M09 | pipeline: verify 呼び出しの `expected_commits=` を削除 | 手前は全て正常 | tail-loss が verifier に届く control |
| M10 | pipeline: YCSB allowlist 述語を恒真化 | | `trace-witness-unsupported-workload` control |
| M11 | pipeline: 空 trace_dir 前提条件を `if False` | | 残骸 trace control |
| M12 | `silo_ladder_rung1.py`: 外側 witness 照合を削除 | ladder 固有 | ladder evidence の mismatch fixture |
| M13 | `critic/digest.py`: 新 reason を `LIVENESS_REASONS` から外す | 受理集合を変えず診断だけ落ちる → **diagnostic sensitivity pin として別枠記録** (DW-M08) | 構造化 rejection control |
| M14 | `verifier/cli.py`: `--expected-commits` を無視 | | S2 calibration 結線 control |

**L1-11 の再照準を反映済み**: 旧 #1 (core の mismatch 条件を恒偽化) と旧 #11 (notes 条件の反転) は
`notes` にしか効かず gate を通らないため**登録しない**。判定は `clean()` にあるので、そこへ照準する。
旧 #6 は「trace C 行数 ≠ stdout commit 数」を fixture で明示しないと同値で生存するため、M09 の
fixture 条件として明記する。

## D. scope 外 (裁定パッケージへ返す)

- **FN-2 (C 行 R/W 件数 + txn 終端マーカー)** — `ruling-package.md` で起票済み。
- **mocc への witness 検査の一般化** — L2-1 より、protocol/workload ごとに「commit 後 counter の
  終了契約」を個別に証明する必要がある。S1 移植 wave の前提として同パッケージへ追記する。
- **[L1-3] 既存 WAL の witness なし COMMIT の扱い** — (a) verifier-policy epoch を campaign
  identity に入れて再評価、(b) `legacy-no-commit-witness` として現行 certified 選択から除外、
  (c) 現状維持 (新 gate は本 commit 以降の run にのみ効くと明記) の三択。
- **[L1-4] coverage 系 4 driver の witness 結線** — `s3_lock_coverage` /
  `s5_permutation_coverage` / `s8a_trigger_coverage` / `t152_write_intent_coverage`。
