# S-1 最終候補 (系側 gate 構成 g_rl / g_rt) の B-8 検証の結果節 — 独立 8 反復 × 3 workload、extime 10 s の trace 検証で 24 枠すべて anomaly ゼロ、runner の 3 値判定は `pass` (事前登録 v1 の発効後、2026-09-21)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** D2160 の検証相の稿 (`2026-09-20-verify-phase-adopted-backoff.md`、採用静的 backoff
2 genome、extime 3 s) が書く結果はそのまま残る。本稿が足すのは、**S-1 の最終候補そのもの (系側 gate 構成 g_rl / g_rt) を、
発効した事前登録 v1 の規則の下で、独立 8 反復 × 3 workload × extime 10 s の長い trace に掛けた正しさ検証の結果**である。

**`pass` は runner が事前登録 §6 の規則を機械適用した出力であって、研究の成功宣告ではない (D12)。**
**本稿は S-1 事前登録 (iv 付属) の充足ではない** — S-1 は「独立した検証相を持たない」と自ら明記しており、その事実は変わらない。
本稿は B-8 の別登録 (`docs/b8-final-candidate-longrun-verify-preregistration.md` v1) の結果である。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**1 対象 (案 A = 系側 gate 構成 g_rl / g_rt) × 3 workload × 8 独立反復 = 24 verify の 1 完走**である。
校正 (段 A、3 job、6 記録) と本走 (段 B、6 job、24 走) を Pegasus gen_S の計算ノードで
2026-09-21 08:45 (段 A 投入) 〜 10:13 (段 B 最終 job 終了) JST に走らせた。**再投入・`--resume`・再検証は 0 回**である。

### 0.2 書くもの

- 対象の定義と identity (source digest)、発効した事前登録の束縛 (規則 file と発効束の sha256)。
- 結果を見る前に固定した校正規則・判定規則と、校正が機械的に決めた extime。
- 24 枠の verdict、校正で完走した 6 件の verdict、判定集合の件数、規約不適合・未完走・bench 失敗の件数 (いずれも 0)。
- 予算 (本走 job の実消費 = dispatch Elapse の和) と限定。

### 0.3 書かないもの

- 性能 (trace-enabled build の正しさ専用走であり throughput を測っていない。規律 1)。
- 形式的信頼度 1−εⁿ、「証明」「保証」「信頼度」(事前登録 §1.2 / §13)。
- S-1a / S-1b の判定の変更、既存 certified 記録の昇格・降格 (規律 7)。
- 案 B (採用静的 backoff 2 genome、D2160) の判定の変更、両者の性能・正しさの比較。
- 「異なる乱数列であることを検証した」(seed 値は記録していない。事前登録 §3.4)。

---

## 1. 対象と固定条件

### 1.1 対象 (案 A)

S-1 の最終候補である**系側 gate 構成**。silo の genome
`BACKOFF_TRIGGER_GATING=1, BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0` に対し、
gate 述語を凍結 JSON (`output/s1-freeze/known_axes_freeze.json` の `entries.<w>.system_gate`) の逐語で hole へ書き込む。

| 構成 | gate 述語 (逐語) | 担当 workload | identity (`src_token` = `source_bytes_sha256`、24 枠すべてで build 前後とも期待値と一致) |
|---|---|---|---|
| g_rl | `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset \|\| izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;` | balanced, read-heavy | `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d` |
| g_rt | `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset \|\| izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;` | write-heavy | `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833` |

**この identity は現行 pin `e9e477ca…` と現行 patch に束縛される。** 07-16 の S-1 検証相校正 (cygnus、旧 verifier、旧 pin
`d706650c…`) が記録した g_rl の `src_token` `4608a96e…` とは一致しない。**本稿は「S-1 campaign 当時のソース・バイナリの
再検証」ではなく、「S-1 の最終候補という設定を、現行 pin・現行 patch の trace-enabled build で検証した」ものである。**
**「同一 binary で 24 反復」とは書かない** — binary は node ごとの別 build であり、source identity と toolchain の同一性だけを主張する。

### 1.2 固定条件

- CCBench pin `e9e477ca1b55348ab4530de0b1cf663ce4555290` (`pin.CURRENT_PIN` と submodule gitlink が一致)、
  template patch `patches/silo-backoff-trigger-gating-variant.patch` (sha256 `31316713b9783fc7…`)、
  configure `-DCCBENCH_TRACE=1 -DCCBENCH_BACKOFF_TRIGGER_GATING=1 -DCCBENCH_BACK_OFF=1
  -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0`、
  g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3)、python 3.10.12。
- workload: `ycsb_tuple_num=1,000,000`、48 thread、Zipf 0.9、`ycsb_rmw=0`、`ycsb_max_ope=10`、`clocks_per_us=2100`、
  write-heavy (`rratio=5`) / balanced (`rratio=50`) / read-heavy (`rratio=95`)、numactl なし。
- **「種を変えた 8 反復」= 8 個の独立な bench process** (各 process の各 worker thread が `std::random_device` から自己シード)。
  記録するのは rep-id・bench の PID・開始時刻・argv 全文・node 名・binary sha256・source identity・trace の量であり、**seed 値は記録しない**
  (CCBench に seed の flag は無い)。24 枠の PID は重複しない。
- verifier: `python3 -B -m orchestrator.verifier <trace_dir> --json --expected-commits <commit witness> --protocol silo
  --ccbench-root <checkout>` (別 process)。module 9 file の sha256 は発効束に固定し、校正と本走で同一の版を使った (`--lenient` は使わない)。
- 各 verify は 1 node で build → bench → C 行の数え直し → trace の保全 (zstd) → verifier の順。単独性検査を bench・verifier の直前に実行。
- 実行場所: Pegasus gen_S 計算ノード (各 job 1 node、node-local build)。cygnus は使っていない。
- **束縛:** 30 record すべてが規則 file (事前登録 v1) の sha256 `6ccb18c73b80ba42031f1373d48baa2e3fe441e0370a208836a6d75a9504f7c5` と
  発効束の sha256 `059536a7359406182c622172354207e147ad2811ba0b4d9286982778b3807c1b` を持つ。

---

## 2. 方法 — 結果を見る前に固定した規則

正本は事前登録 v1 (発効 commit `624c84986`、D2194 項 1、2026-09-21)。**発効前に校正・本走は走らせていない。**

1. **校正 (段 A):** 各 workload で extime {6, 10} s を昇順に各 1 回 trace run + verifier 実走。
   適格 = bench 完走 ∧ trace 保全済み ∧ verifier 完走 ∧ `serializable` ∧ certified ∧ anomaly 0 ∧ identity 一致 ∧ verifier wall ≤ 1800 s。
   verifier wall > 1800 s・未完走・bench 失敗で、その extime 以上を打ち切る。
   対象の extime = 3 workload の適格集合の共通部分の最大値 (空なら「候補なし」で本走を投入しない。**6 s へも 3 s へも丸めない**)。
   校正で完走した verifier に anomaly が 1 件でもあれば即失格 (規律 2)。
2. **予算:** 本走 24 verify の job 実消費 (dispatch Elapse の和) ≤ 14,400 s / 対象。校正は別欄。
   見込み B(E) が 14,400 s を超えれば適格集合の共通部分の中で 1 段下げ、下げる先が無ければ本走を投入しない (反復数は削らない)。
3. **判定 (本走後、順序付き 3 値を 1 度だけ評価):** 判定集合 = 本走 24 枠 ∪ 校正で完走した verdict。
   **失格** = 判定集合に `anomaly_count` ≥ 1 または verdict が `serializable` でない verify が 1 件以上 (rc=3 の `indeterminate` verdict を含む)。
   **pass** = 失格でなく、本走 24 枠すべてが bench 完走・trace 保全済み・verifier 完走・`serializable`・certified・anomaly 0・identity 一致。
   それ以外は**未確定**。校正の完走 verdict に certified は要求しない (件数と理由を開示する)。
4. **bench 失敗は再生成しない。** 1 件でもあれば pass にならず、校正で出れば本走を投入しない。
5. **本走 verifier の未完走:** 保全済みで verifier 未開始の枠は同じ job を `--resume` で再開し初回 verifier を走らせる。
   verifier が起動済みで未完走の枠は同一の保全済み trace に対する再検証を 1 回だけ許す。anomaly の枠は再検証しない (規律 2)。
   **本走ではどちらも発生しなかった (0 回)。**

---

## 3. 結果

### 3.1 校正 (段 A、2026-09-21 08:45 投入 → 09:11 JST 最終 job 終了、request 14640–14642.nqsv、3 job)

**6 行すべてが適格** (bench 完走・保全済み・verifier 完走・`serializable`・certified・anomaly 0・identity 一致・verifier wall ≤ 1800 s)。
打ち切り 0 件、未完走 0 件、bench 失敗 0 件、certified でない verdict 0 件。

| workload (gate) | extime | commit witness (= C 行数え直し) | bench s | count s | preserve s | verifier wall s | verdict / certified / anomaly |
|---|---:|---:|---:|---:|---:|---:|---|
| write-heavy (g_rt) | 6 | 5,031,651 | 6.36 | 5.01 | 8.61 | 173.5 | serializable / true / 0 |
| write-heavy (g_rt) | 10 | 8,386,125 | 10.38 | 8.38 | 12.91 | 296.7 | serializable / true / 0 |
| balanced (g_rl) | 6 | 4,365,476 | 6.35 | 4.32 | 8.33 | 129.8 | serializable / true / 0 |
| balanced (g_rl) | 10 | 7,291,602 | 10.35 | 7.18 | 12.30 | 221.0 | serializable / true / 0 |
| read-heavy (g_rl) | 6 | 11,820,251 | 6.34 | 11.74 | 18.68 | 290.5 | serializable / true / 0 |
| read-heavy (g_rl) | 10 | 19,605,018 | 10.34 | 19.39 | 29.24 | 491.4 | serializable / true / 0 |

適格集合は 3 workload とも {6, 10}、共通部分 {6, 10}、**その最大値 = extime 10 s**。
本走の見込み B(10) = 9,289.3 s ≤ 14,400 s なので段下げ無し (B(6) = 5,608.6 s は参考値)。

### 3.2 本走 (段 B、2026-09-21 09:17 投入 → 10:13 JST 最終 job 終了、request 14686–14691.nqsv、6 job × 4 反復)

**24 枠すべてが bench 完走・trace 保全済み・verifier 完走・`serializable`・certified・`anomaly_count` = 0・identity 一致。**

| workload (gate) | n | commit witness の範囲 | verifier wall s (min–max / 平均) | bench s | count s | preserve s | node | 保全 (zstd) |
|---|---:|---|---|---|---|---|---|---:|
| write-heavy (g_rt) | 8 | 8,334,626 – 8,419,456 | 293.9 – 296.5 / 295.3 | 10.33–10.36 | 8.3–8.4 | 12.6–13.4 | bnode019, bnode025 | 3.97 GiB |
| balanced (g_rl) | 8 | 7,165,219 – 7,317,347 | 217.4 – 222.0 / 219.2 | 10.34–10.37 | 7.1–7.2 | 11.9–12.4 | bnode020, bnode026 | 4.75 GiB |
| read-heavy (g_rl) | 8 | 19,689,835 – 19,949,054 | 492.5 – 500.6 / 496.4 | 10.34–10.39 | 19.7–20.3 | 29.1–29.8 | bnode023, bnode028 | 14.20 GiB |

- 各 workload の 8 反復は 2 job (rep 1–4 / rep 5–8) に分かれ、job ごとに別 node で走った。24 枠の bench PID は重複しない。
- trace は verify 後も削除せず zstd で保全した。保全先は job dir `run/verify/<workload>-j<n>/rep-*/` (`/work` lustre)、合計 22.9 GiB。

### 3.3 判定

**`decision` = `pass`** (runner v5 の `summarize` が事前登録 §6.1 の順序付き 3 値を 1 度だけ評価した出力。
評価順序の記録は「1 失格 → 不一致」「2 pass → 一致」)。

| 量 | 値 |
|---|---:|
| 判定集合 | **30** (本走 24 + 校正の完走 verdict 6) |
| anomaly を検出した verify | **0** |
| `serializable` でない verdict | **0** |
| 失格 record | **0** |
| 校正の certified でない verdict | 0 |
| 校正の未完走 (indeterminate) | 0 |
| bench 失敗 | 0 |
| 規約不適合 (record 段 / job 段) | 0 / 0 |
| `not_run` | 0 |
| 再検証 (`reverify`) / 再開 (`--resume`) | 0 / 0 |
| extime | 10 s (初期選択も 10、段下げ無し) |
| 反復数 | 8 / workload (削っていない)、3 workload で 24 verify |

**B-8 の 3 要件はこの結果で揃った:** 対象 = S-1 の最終候補 (案 A)、種 = 独立 process の自己シード (事前登録 §3.2、発効時に
論文ストーリー §8 の仕分け (2) をこの定義へ改める限定を明記した)、長時間 = extime 10 s (開発相および D2160 の検証相が用いた 3 s より長い)。

### 3.4 費用 (§7)

| 段 | job 数 | 実消費 (dispatch Elapse の和) | 予算 |
|---|---:|---:|---|
| 段 B (本走) | 6 | **9,280 S** | ≤ 14,400 s / 対象 (満たす) |
| 段 A (校正) | 3 | 1,920 S | 別欄 (上限に含めない) |

runner の内部 monotonic 集計 (`consumed_job_wall_s`) は段 A 1,904.7 s / 段 B 9,249.5 s で、判定には dispatch Elapse の和を用いた。
queue 待ちと親の待機は含まない (別欄: 段 B は 09:17 投入 → 10:13 終了)。計画拘束の不充足は 0 件。

---

## 4. 限定

1. **`pass` は規則の機械適用の出力であって、研究の成功宣告ではない** (D12)。
2. **certified の保証範囲を超えない。** verifier は観測した trace の依存グラフについて判定するのであって、
   predicate / phantom / fairness / 未観測の実行を保証しない。**「serializable であることが示された」「証明した」とは書かない。**
3. **「種を変えた」は独立 process の自己シードという操作的定義**であり、seed 値は記録していない。
   独立性は操作的仮定で、`std::random_device` の実装は測っていない。同じ 32 bit 値の再出現は検査できない。
4. **「長時間」は extime 10 s** という操作的定義である。長さ・反復数の検出力は主張しない。
5. **性能値を含まない。** trace-enabled build の正しさ専用走であり、throughput は測っていない (規律 1)。
6. **identity は現行 pin・現行 patch に束縛される** (§1.1)。旧 pin の S-1 campaign とは source bytes が異なる。
   binary は node ごとの別 build である。
7. **S-1a の不成立・S-1b の性格 (結果既知の追試) を変えない。** 本結果を S-1 (iv 付属) の充足として扱わない。
   S-1 campaign の certified 記録・`s_prime_final_report.md`・`known_axes_freeze.json` の bytes は変えない (規律 7)。
8. **案 B (採用静的 backoff 2 genome、D2160、extime 3 s) の結果・判定を変えない。** 対象が違う。両者を比較しない。
9. **D2160 の校正で 10 s が未完走だったこととは比較しない。** 対象も verifier の版も違う。本走で 10 s が完走したことは
   「verifier が改善した」ことの測定ではない。
10. **事前登録の失敗条件のうち扱うのは (a) だけ** (合成が certified を破るか)。(b)〜(e) について本結果から何も言えない。
11. **1 回の cohort の結果である。** 別の日・別の node 集合での再現は取っていない。

---

## 5. 一次資料

- 発効と実行の記録 (発効束・校正・本走・判定・限定): `output/insights/2026-09-21/t2807-b8-effective/README.md`
- 発効束 JSON (runner の `--bundle`): `output/insights/2026-09-21/t2807-b8-effective/verbatim/b8-effective-bundle.json` (sha256 `059536a7…`)
- 事前登録 v1 (規則の正本、発効 commit `624c84986`): `docs/b8-final-candidate-longrun-verify-preregistration.md` (sha256 `6ccb18c7…`)
- 裁定: D2194 項 1 (発効と本走の承認)、D2186 項 1 (段階認可と定義の確認)、D2190 (runner v5 と発効束 draft)
- 発効前試走 (identity 導出、判定集合外の既知結果): `output/insights/2026-09-20/t2807-b8-prerun/README.md`
- 機械集計: job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-effective/run/` の `summary-final.json`
  (sha256 `ee94bdf2044976fddf9a22c439ca78ec493dda0fd43a31e51c758668e46c5001`) / `summary-final.md`、
  `calib/<workload>/calib.json`、`verify/<workload>-j<n>/rep-*/attempt-1/result.json`、保全 trace (zstd、22.9 GiB)。
  runner v5 は repo 外 (`dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py`、sha256 `4ff6652a…`、D95)。
