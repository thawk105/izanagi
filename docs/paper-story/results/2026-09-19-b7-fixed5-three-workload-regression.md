# 採用候補 fixed 5 µs の 3 workload 同時期測定 — attempt `b7f5-20260919a` で read-heavy に床値超の退行、write-heavy / balanced は退行なし (2026-09-19)

**これは投稿本文ではない。** 論文の結果節・表・図・限定へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** 2026-09-14 と 2026-09-16 の B-7 横断稿は、workload ごとに
**別の**採用値 (10 / 5 / 2 µs) を**別の** attempt で測ったものを事後に併記した材料であり、本稿とは測っている
候補も走行の単位も違う。両稿は凍結物として 1 byte も変えずに残り、本稿はそれらを数値の出所にしない。
**本稿は既存材料と併記するが、プールしない** (D1993 項 6)。併記は §3 に表を分けて置く。

**本稿が判定しないこと (最初に置く):** 見送り台帳 B-7 (全 workload の退行込み報告) の要件充足。D2044 項 3 は
「B-7 の要件充足へ昇格させない。現在ある記述的な報告は利用してよいが、要件を満たしたとは扱わない」と定めており、
本稿はその内側にとどまる。本稿が足すのは、D2044 項 3 が不足として挙げた「同一 variant の横断比較と床値超の判定」の
**材料**であって、要件充足の判定ではない。certification の昇格・新しい判定手順・追加の関門も本稿は行わない
(ユーザー裁定 2026-09-19、§5.4)。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**1 attempt = `b7f5-20260919a`** (study `paper-story-b7-fixed5-regression`、2026-09-19、request `10807.nqsv` /
`10808.nqsv` / `10809.nqsv`、source commit `c18a80967ed3d9a901b395116c23f90d6a554b36`)。
3 workload (rr5 write-heavy / rr50 balanced / rr95 read-heavy) × 2 cell (stock / fixed5) = **6 cell、各 5 標本、計 30 標本**。
3 workload は同じ study の中の独立した campaign (別 request・別 node) であり、**workload をまたぐ集計は作らない**。
本稿の主表が 3 行あるのは並記であって集計ではない。

### 0.2 書くもの

- 権威 bytes (`certification.json`) が持つ 6 cell の `performance.median_tps`・`effects`・`status`・`correctness`・
  `source_binding_status`・`src_token`・binary digest (§2.1、§2.4)。
- 各 cell の 5 標本と campaign WAL の `cv`・abort 率 (§2.2、§2.3)。
- **結果を見る前に固定した判定規則** (§1.4) を 3 workload に当てた結果 — 退行の有無を、符号を問わず同じ表に載せる (§2.1)。
- 「同一候補・同一ソース条件」が成果物で確かめられる範囲と、確かめられない範囲 (§1.2、§4)。
- 同時期性 — 3 request の投入・開始・終了と、各 arm の bench 時刻 (§1.3)。
- 既存材料 (2026-09-16 稿) との併記 (§3)。図の材料 (§2.5)。限定 (§4)。一次資料 (§5)。

### 0.3 書かないもの

- B-7 の要件充足、研究としての成功・失敗の宣告 (D12)、有意差判定、区間推定。
- 退行の機序、他の backoff 値・他の read 比率・他の機体・他の CCBench pin への転移。
- 3 workload の集計値、既存材料とのプール、前後比較 (絶対規律 7)。
- 「同一 binary」の主張 (§1.2)。文字どおりの同時実行の主張 (§1.3)。

### 0.4 主判定文 (結果節へ落とすときの形。文を分けたまま使う)

attempt `b7f5-20260919a` の trace-disabled 性能測定では、静的 backoff fixed 5 µs (T-1998 事前登録の採用 arm と同じ
genome・同じ source bytes digest) の median throughput は、stock (backoff 無し) に対して write-heavy で +67.8968%、
balanced で +12.6717%、read-heavy で **−11.3787%** だった。結果を見る前に固定した規則 (対差 < −床値、床値 = D1639 の
between-run CV) では、**read-heavy だけが床値超の退行**であり、write-heavy と balanced は退行なしである。
機構の outer status (3 workload の論理積) は `reject` で、これは read-heavy の対差が負であることの帰結である。
これは 1 attempt・各 5 標本の中央値比較であり、有意差・研究の失敗・B-7 の充足を判定するものではない。
別の trace-enabled 走行では 6 cell とも `correctness.status = certified`・anomaly 0 と記録されている (規律 1・2)。

---

## 1. 条件 — 結果を見る前に固定したもの

### 1.1 protocol と 6 cell

policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (schema `paper-story-a2-certification-policy/v2`、
study `paper-story-b7-fixed5-regression`、bytes SHA-256 `c6b24050d17c4bc552d254ce65e328b3a6edca919387b5720b4e025ea78b0df1`、
protocol SHA-256 `5653d439714e11df9de8f2bd3e697c038d0cfbb538c5f703e0749facbfe2998c`)。
A-2 / A-6 と同じ certification 経路 (`orchestrator/campaign/paper_story_a2_certification.py`) の **別 study instance** として
closed set へ追加したもので、A-6 追加 (commit `60605bec3`) と同形である。A-2 / A-6 の policy bytes と protocol SHA-256 は
変えていない。protocol SHA-256 は study・workloads・cells を preimage に含むので、本 study の値は A-2 / A-6 と**異なる**。

| workload | label | `rratio` | `adopted_backoff_us` | stock cell | adopted cell |
|---|---|---:|---:|---|---|
| rr5 | write-heavy | 5 | 5 | `rr5-stock` (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) | `rr5-fixed5` (`BACK_OFF=1`, `BACKOFF_FIXED=5`) |
| rr50 | balanced | 50 | 5 | `rr50-stock` (同上) | `rr50-fixed5` (同上) |
| rr95 | read-heavy | 95 | 5 | `rr95-stock` (同上) | `rr95-fixed5` (同上) |

**3 workload とも採用値は 5 µs である。** これが 2026-09-14 / 09-16 稿 (10 / 5 / 2 µs) との違いであり、本稿の純増である。
候補の genome は T-1998 事前登録 (`docs/t1998-balanced-stock-inline-preregistration.md` v1) §2 の target
(`BACK_OFF=1`、`BACKOFF_FIXED=5`) と同じで、stock は同 §2 の baseline (`BACK_OFF=0`、`BACKOFF_FIXED=-1`) と同じである。

共通条件は A-2 policy と同値: 性能側 records 1,000,000・threads 48・skew 0.9・rmw 0・max_ope 10・extime 3・reps 5・
base `L-W0`・wal 0・protocol silo、legacy 正しさ側 tuple 200・thread 4・skew 0.9・rratio 50・rmw true・max_ope 5・extime 1、
controlled define の基底 `NO_WAIT_LOCKING_IN_VALIDATION=1`・`NO_WAIT_OF_TICTOC=0`・`WAL=0`・`BACKOFF_NOINLINE=0`・`TRACE=0`。
効果の定義は `adopted_median / stock_median − 1`、集約は median、outer certification は「policy の workload 順の論理積」。
scheduler は `gen_S`、nodes 5 (検査の兄弟 node 4 本を含む)、walltime 12:00:00。

### 1.2 「同一候補・同一ソース条件」— 成果物で確かめた範囲

**3 workload の adopted cell は同じ source bytes から、workload ごとに別 node で別々に build されている。** 本稿は
「同一候補・同一ソース条件から workload ごとに別 build」と書き、「同一 binary」とは書かない。

| 項目 | rr5 | rr50 | rr95 | 出所 |
|---|---|---|---|---|
| adopted `src_token` = `source_bytes_sha256` | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` | 同左 | 同左 | 権威 bytes `cells[].src_token`、条件関門 receipt の source-evidence 行、WAL `build_start` |
| stock `source_bytes_sha256` (`src_token` は `stock`) | `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` | 同左 | 同左 | 条件関門 receipt の source-evidence 行、WAL `build_start` |
| patch 適用の tracked diff digest | `29aef2bc1b9f…` | 同左 | 同左 | 条件関門 receipt (`tracked_clean = false`) |
| CCBench pin | `511c953` | 同左 | 同左 | 権威 bytes `current_pin` |
| toolchain | `x86_64-linux-gnu-g++-11` (Ubuntu 11.4.0-1ubuntu1~22.04.3)、cmake 3.22.1 | 同左 | 同左 | raw cell `trace0_evidence.toolchain` |
| controlled define (adopted) | `CCBENCH_BACK_OFF=1`、`CCBENCH_BACKOFF_FIXED=5`、`CCBENCH_BACKOFF_NOINLINE=0`、`CCBENCH_TRACE=0`、他 3 つは基底どおり | 同左 | 同左 | raw cell `trace0_evidence.controlled_defines` |
| `source_binding_status` | `bound` (6 cell すべて) | | | 権威 bytes |

**T-1998 事前登録 §4.2 が固定した arm 別 source bytes digest と、3 workload の値は全桁一致する** (baseline `2d691b45…`、
target `678b7203…`)。事前登録は balanced の 1 対だけを対象とするので、この一致は「本 attempt の候補が事前登録の
target と同じ前処理後ソースである」ことを言うにとどまり、事前登録の主張が write-heavy / read-heavy へ拡張されたことを
意味しない。

binary は workload ごとに違う (`perf_bin_sha256`: `rr5-fixed5` `59d0b746…`、`rr50-fixed5` `e5996949…`、`rr95-fixed5` `259929bc…`。
stock も同様に 3 通り。全桁は §5.1)。configure argv は request ごとの依存物の絶対 path を含むので完全一致しない。
**同一性の主張は source bytes・define・toolchain・pin までである。**

### 1.3 実行 identity と同時期性

| 項目 | rr5 | rr50 | rr95 |
|---|---|---|---|
| request | `10807.nqsv` | `10808.nqsv` | `10809.nqsv` |
| Created (投入、JST) | 22:31:57 | 22:32:00 | 22:32:04 |
| Started → Ended (JST) | 22:36:11 → 22:42:33 | 22:59:21 → 23:13:17 | 22:49:05 → 23:09:19 |
| NQSV 会計 Elapse | 386 s | 841 s | 1218 s |
| queue 待ち (Created → Started) | 254 s | 1641 s | 1381 s |
| 割当 node (5 本、先頭を head と推定) | bnode051, 060, 107, 108, 132 | bnode060, 021, 107, 112, 108 | bnode084, 007, 126, 130, 022 |
| stock の bench 時刻 (WAL `bench_done` の ts、JST) | 22:39:39 | 23:09:35 | 22:58:14 |
| adopted の bench 時刻 (同上) | 22:42:32 | 23:13:17 | 23:09:18 |
| stock → adopted の間隔 | 2 分 53 秒 | 3 分 42 秒 | 11 分 4 秒 |
| `driver_rc` | 0 | 0 | 0 |

3 request は同じ attempt として 7 秒以内に投入され、**6 arm の bench は 22:39:39 から 23:13:17 の 33 分 38 秒の間に収まる**。
各 workload の stock 対照は、同じ request・同じ head node・同じ campaign の中で adopted の直前に測られている
(2 cell は build → 正しさ検査 → bench の順に連続する既存の経路)。**本稿が「同時期の対照」と言うのはこの形であり、
文字どおりの同時実行、workload 間の node 同一性、時間ドリフトの除去は主張しない。** rr5 と rr50 の割当に同じ node
(bnode060 / 107 / 108) が現れるが、両 request の実行時間帯 (22:36–22:42 と 22:59–23:13) は重ならない。
`~/.izanagi/bench.lock` による request 間の直列化 (2026-09-18 の T-2489 probe が強い推測として記録) は、
rr95 の stock → adopted 間隔 11 分の説明候補だが、本稿はそれを立証していない。

投入元は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/submit-tree` (source commit `c18a80967…`、tracked clean)、
job body `tools/pegasus/paper_story_a2_certification.sh` (sha256 `2a3205cf5c171563f715556e1ca347821df75f7dc3d74934511caf7a7e820d70`、
A-6 attempt `a6-20260908b` と同一 bytes)、投入 host `pegasus02`。環境契約 digest `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
は権威 bytes に field を持たないが、raw cell の `trace0_evidence.run_argv` の binary path (`…/cache/contracts/e576e9cd…/…`) に現れる。

### 1.4 判定規則 — 結果を見る前に固定した (段 4 裁定 2026-09-19、§5.4)

1. `median_w,arm` = 機構が受理した各 arm の 5 標本の median (権威 bytes `cells[].performance.median_tps`)。個々の比の median ではない。
2. `effect_w` = 機構の `effects[w]` (= `median_w,adopted / median_w,stock − 1`、未丸め)。
3. `floor_w` = D1639 の between-run noise floor = `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json`
   の `between_run.cv` の全桁: rr5 `0.009536033056996148`、rr50 `0.00725042525457718`、rr95 `0.0022283754708938273`
   (8 独立 session × 5 rep の session-median の変動係数、stock genome、同じ動作点)。
4. `regression_w` ⇔ `effect_w < −floor_w` (strict)。等号は退行に含めない。表示の丸めは判定の後。
5. `effect_w` が無い workload (anomaly → reject、unstable、source unbound、標本不備) は「判定不能」とし理由を書く。anomaly による reject は別欄に保持する (規律 2)。
6. 「退行なし」は「優越」でも「差が無いことの証明」でもない。床は旧 stock の session-median の変動の**下限**であり、本 attempt の effect の標準誤差・有意水準ではない。
7. outer status と `a4_noise_floor_status` は機構の出力として写すだけで、稿の床値判定で書き換えない。

床値 JSON の genome は `silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` (`BACKOFF_FIXED=-1` の
表記を持たない旧 canonical) で、本 attempt の stock (`BACKOFF_FIXED=-1` は patch の inert 既定) と設定上は同じだが、
旧 binary・toolchain との同一性は証明していない (§4)。床の出自はそのまま記し、本 attempt で再較正した床とは呼ばない。

---

## 2. 結果

### 2.1 主表 — 3 workload の対差と床値判定 (退行込み、符号を問わず同じ表)

| workload | stock median (tps) | fixed5 median (tps) | `effect_w` (機構の `effects`、未丸め) | 百分率 (丸め) | `−floor_w` (百分率) | 判定 (規則 v2) | 正しさ (別走行) |
|---|---:|---:|---|---:|---:|---|---|
| rr5 (write-heavy) | 2,354,846 | 3,953,710 | `0.6789675418265144` | +67.8968% | −0.9536% | **退行なし** | 2 cell とも certified、anomaly 0 |
| rr50 (balanced) | 3,832,768 | 4,318,443 | `0.12671651401806727` | +12.6717% | −0.7250% | **退行なし** | 同上 |
| rr95 (read-heavy) | 10,334,945 | 9,158,963 | `-0.11378696258180376` | −11.3787% | −0.2228% | **退行 (床値超)** | 同上 |

- `effect_w` は権威 bytes の `effects` を全桁転記した。表の median を入力した比の再計算は 3 件とも同じ値を返した
  (照合であって、権威は `effects` 側にある)。
- 判定は §1.4 の規則 4 による。rr95 は `−0.1137… < −0.0022…` で退行、rr5 と rr50 は正の effect で退行なし。
  **退行なしの 2 行は「優越」の判定ではない** (規則 6)。3 行とも `effect_w` が存在し、判定不能の行は無い。
- 機構の出力: outer `status` = `reject` (3 workload の論理積で、rr95 の effect が非正であることの帰結)、
  `a4_noise_floor_status` = `open`。**これは machinery の出力であり、稿の床値判定 (rr95 のみ退行) とは別の量である。**
  `reject` を「3 workload とも退行」と読んではならない。
- **`reject` は protocol の status であって、研究の失敗宣告ではない** (D12)。本稿は certification を主張しない
  (descriptive な使用、§5.4)。

### 2.2 6 cell の生標本 (記録順)

| cell | 5 標本 (tps、記録順) | median | WAL `cv` |
|---|---|---:|---:|
| `rr5-stock` | 2328992, 2423324, 2354846, 2347564, 2371395 | 2,354,846 | 0.0151646972311875 |
| `rr5-fixed5` | 4049702, 3954525, 3731893, 3942414, 3953710 | 3,953,710 | 0.02981794983162433 |
| `rr50-stock` | 4135929, 3769412, 3813768, 3878461, 3832768 | 3,832,768 | 0.037327242005970554 |
| `rr50-fixed5` | 4378198, 4318443, 4308209, 4333385, 4306001 | 4,318,443 | 0.006845243310507793 |
| `rr95-stock` | 10680928, 10171152, 10334445, 10334945, 10351729 | 10,334,945 | 0.017964051633260415 |
| `rr95-fixed5` | 9282678, 9137295, 9158963, 9119021, 9190899 | 9,158,963 | 0.007023717070984131 |

6 cell とも、durable な raw cell JSON の `performance.samples_tps` と campaign WAL の `bench_done.payload.tps` が同じ並びを
持つことを確かめた。**これは独立した再測定ではなく**、同じ 1 走行を producer が 2 か所へ書いたものである。
`unstable` は 6 cell とも `false`、`rep_notes` は空、`high_variance` は `false`。
`cv` は WAL の値をそのまま転記した。標本から `標本標準偏差 (n−1) / 標本平均` を計算すると 6 cell とも倍精度で一致した
(2026-09-16 稿 §2.3 と同じ確認であり、定義の断定ではない)。

### 2.3 abort 率 — 記述的な先行指標

| workload | stock | fixed5 |
|---|---:|---:|
| rr5 | 0.7881 | 0.4997 |
| rr50 | 0.681 | 0.4599 |
| rr95 | 0.1543 | 0.1345 |

出所は WAL `bench_done.payload.leading_indicators.abort_rate` (raw cell の `abort` は null)。perf は使っていない
(`use_perf = false`、`counter_status = not_required`)。LLC miss / IPC は null。

### 2.4 正しさ — 別走行で 6 cell とも certified

6 cell とも `correctness.status = certified`、`disposition = pass`、`legacy = pass`、`performance = pass`、
`legacy_repetitions_observed = 1`、`performance_repetitions_observed = 5`。durable な raw cell JSON でも、6 cell とも
`correctness.legacy` 1 件・`correctness.performance` 5 件の verdict がすべて `serializable`・`certified = true`・anomaly 0
(計 36 記録)。`build_evidence.performance_trace_disabled_build = true` で、性能値は trace 無効 build から来ている (規律 1)。
**退行した rr95-fixed5 も certified である。** 「正しさを保ったまま性能で負けた」と書けるのは検査された範囲についてであり、
正しさの合格は性能の優越の十分条件ではない。

### 2.5 図の材料

図はまだ無い。図を作るときの材料は次で足りる。

- 生値: §2.2 の 30 標本 (権威は durable の raw cell JSON `performance.samples_tps` と WAL `bench_done.payload.tps`)。
- 集約: 各 cell の median と `effects` (権威 bytes)。
- 基準線: 各 workload の stock median、および `−floor_w` (§1.4 の 3 値)。
- 反復 5 なので、描くなら点推定だけでなく不確かさ (t 分布の 95% CI) を付ける (`tools/plotting/FIGURE_CONVENTIONS.md` §2)。
- provenance: §5.1 の権威 bytes と sha256、§5.2 の durable path。図の値と表の値は同じ生値から同じ計算で出す。

---

## 3. 既存材料との併記 — 表を分け、プールしない

2026-09-16 稿 (`results/2026-09-16-b7-three-run-materials.md`) の主表は、workload ごとに別の採用値を別 attempt で測った
4 対比較である。本稿の主表と**同じ表に入れない**。並べるのは読み手が「同じ workload で採用値が違うとどう見えるか」を
追えるようにするためであり、前後比較・再現・集計のいずれでもない (絶対規律 7、D1993 項 6)。

| workload | 既存材料 (2026-09-16 稿の主表、attempt / 採用値 / 効果) | 本稿 (attempt `b7f5-20260919a`、採用値 5 µs、効果) |
|---|---|---|
| rr5 (write-heavy) | `t2364-20260907b` / 10 µs / +63.5485% | 5 µs / +67.8968% |
| rr50 (balanced) | `t2364-20260907b` / 5 µs / +14.4213%; [T-1998] / 5 µs / +11.2254% | 5 µs / +12.6717% |
| rr95 (read-heavy) | `a6-20260908b` / 2 µs / −5.7841% | 5 µs / −11.3787% |

既存材料の値は 2026-09-16 稿から**位置を示すためだけ**に引いた。その権威は各 attempt の一次資料にあり、本稿はそれを再照合
していない。左右の差 (例: rr95 の −5.78% と −11.38%) は採用値・attempt・日付・node が違うので、床値と比べる対差ではない。

---

## 4. 限定 (この結果が言わないこと)

1. **1 attempt・各 5 標本の中央値比較である。** 反復 attempt は無く、反復間の安定性へ一般化しない。
2. **床値判定は記述的である。** 床は 1 arm の between-run CV であり、2 arm の比の分散ではない (独立同分散なら比の CV は
   約 √2 倍)。ユーザー裁定どおり直接比較したが、有意差判定ではない。「退行なし」は差が無いことの証明ではない。
3. **床値 JSON の測定 (2026-09 上旬、別 binary・別 node) と本 attempt の stock の同一性は設定上のもの**で、
   binary・toolchain・node の同一性は証明していない。床は「下限」として記録されたものである (JSON の `notes`)。
4. **同一候補は source bytes・define・toolchain・pin まで**で、binary は workload ごとに別 build。configure argv は依存物の
   path を含み完全一致しない (§1.2)。
5. **同時期性は「同じ attempt・33 分 38 秒の窓・各 workload で stock 直後に adopted」まで** (§1.3)。文字どおりの同時実行では
   なく、request 間の lock 直列化の影響 (rr95 の 11 分の間隔) は立証していない。
6. **outer `reject` は 3 workload の論理積の出力**であり、rr95 の負の effect の帰結である。3 workload が退行したという意味でも、
   anomaly の意味でもない (anomaly は 0)。
7. **B-7 の要件充足は判定しない** (D2044 項 3)。本稿は「同一 variant の横断比較と床値超の判定」の材料を 1 attempt 分足したにとどまる。
8. **certification ではない。** A-2 / A-6 と同じ経路を descriptive に使った (ユーザー裁定)。昇格・新しい判定手順・追加関門は無い。
9. **T-1998 事前登録との関係は source digest の一致まで。** 事前登録は balanced の 1 対だけを対象とし、本 attempt はその
   consumer を通していない。事前登録の主張を他 workload へ広げるものではない。
10. **機序を述べない。** read-heavy で静的 5 µs が退行する理由 (abort 率 0.15 → 0.13 に対する backoff の待ち時間の寄与など) は
    本稿の範囲外である。
11. **perf 無し。** leading indicator は throughput と abort 率だけで、LLC miss・IPC は null。
12. **correctness の workload argv は独立に記録されていない** (`workload_argv_observation =
    not-independently-recorded-by-existing-pipeline`、権威 bytes の `independent_observation_limits`)。
13. **head node は割当一覧の先頭からの推定**であり、兄弟 node の実 hostname は成功 result に無い (A-6・T-2489 と同じ)。
14. **既存材料との併記 (§3) は位置の提示であって比較ではない。** 左右の値を引き算しない。

---

## 5. 一次資料

### 5.1 権威 bytes と転記元 (repo 内、tracked) — `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/`

| file | sha256 | 本稿での用途 |
|---|---|---|
| `certification.json` | `b6493e4eed17e23cbe10682af72e7c06b805ced1e13a329ffd13df896f4d5431` | §2.1 の median・`effects`・`status`・`a4_noise_floor_status`、§2.4 の correctness、§1.2 の `src_token`・binary digest、§1.1 の policy bytes (`policy_bytes_base64`)・`policy_sha256`・`protocol_sha256`・`source_commit`・`current_pin`・`request_ids` |
| `submission-receipt.json` | `31efdd5b2b3851787da107079d6353f497dae7c2d2b80a51dfac7aba08c7d67d` | §1.3 の request・投入元・job body sha・qsub argv |
| `completion-receipt.json` | `949603c74ec6c25c6178f119a9a251b5b922cd8c2e9f118a1cc92bf42c145105` | 3 request の terminal 観測 |
| `acquisition-receipt.json` | `b0b6b9640855f56164aa73ba2c0f06975f6240ba150485ea0b56f0a5a3c00778` | raw / campaign 証拠の束縛 |
| `raw-manifest.json` | `be8163da33416020de3bfdca136ceaff5430e0878c46abe90681e6b0d954f6ac` | durable raw 18 file の sha256 (§5.2 の raw cell JSON・campaign lock・WAL・claim) |
| `artifact-manifest.json` | `82226c771ad4e02d99f539a0be330a31aa1009923afa943177cb52ff9e34d251` | leaf の完全性 |
| `condition-gate-rr5.admissions.jsonl` | `03cb1521842228cb605ff918604a0b36fcbcdee3a5d8a3fc68f319c086cdee67` | §1.2 の source-evidence 行 (source bytes digest、tracked diff digest) |
| `condition-gate-rr50.admissions.jsonl` | `013dc48c8ff69e367a0368e0347dd899f399e36b9d1823f4d035d0d06161aa56` | 同上 |
| `condition-gate-rr95.admissions.jsonl` | `c6bf40c2ad9219fdb583f4b54e2967638dfabf720090aa282609b76af7a51453` | 同上 |
| `COMPLETE.json` | `b0baa555fbbe2bd0c0907cfe1f27c659cddde4899bc1a5a2220671709b7662d7` | materialize 完了 marker |

binary digest の全桁 (権威 bytes `cells[]`): `rr5-stock` perf `14d3a42bed57a77e98bce65407aae4b565cf053f37ee41f5ebf3d34ec4327ed5` /
trace `e7f2a4333d2f21cc0d57b421452efd0a61de10b063fddd65bf3b8493254e0eec`; `rr5-fixed5` perf `59d0b746ac2816c79ec26e83ebe6473ec7f2f10ec5958c8a11b3c21b0dfcda40` /
trace `06161641cda9f544f31e1520cc9a6f418cc7067b35a74f3068fdc37e7248e6ff`; `rr50-stock` perf `a9f6092e56eda1ead9b1ba977feccca5007d396a9f121093fb6099a0d73dbc04` /
trace `7b8613db298ba691045e13ce7872a5963826100030362b38bc2ca8bcd27ac0aa`; `rr50-fixed5` perf `e59969497a32b5991c8a929d09c60bcdd711a64e5be2a2c4d08297c88efd3164` /
trace `3f87ce14ef05ec2fe85832ab6a6f1b89b4c9b0994748d298aa9840d63f23e80d`; `rr95-stock` perf `5ed9797b879ce11d0ca5a90c481c755bc41a1842a14bd2f0bdc22c43f50de9ce` /
trace `10e1e7bb61530682276a37e8ab2d21cd8d1b4ebb1f37136de5650b4b73ac9076`; `rr95-fixed5` perf `259929bc7e314a4c8daf6b1c710ca89d3fc982f046c1c4dbe6beec48bc4e9f1e` /
trace `6fa0279e7c42e4e76ad31480efd62e6eb6777b0746dbcfe6d632aadc014bc956`。

### 5.2 durable authority (repo 外) — `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/`

- `jobs/<w>/raw/<w>-{stock,fixed5}.json` — §2.2 の生標本、§2.4 の 36 記録、§1.2 の toolchain・controlled define・run argv。
- `jobs/<w>/campaigns/paper-story-a2-<w>-paper-story-b7-fixed5-regression-<w>-<id>/runs/wal.jsonl`
  (`<id>` = rr5 `2b1c7c96`、rr50 `6e2177d3`、rr95 `78070af2`) — §1.3 の bench 時刻 (`bench_done.ts`)、§2.2 の `cv`、§2.3 の abort 率、
  §1.2 の `build_start` (genome・`src_token`・`source_bytes_sha256`)。
- `jobs/<w>/scheduler/job.stderr` (NQSV 会計: Created / Started / Ended / Elapse)、`allocation-qstat.stdout` (割当 node)、`request-id`。
- `jobs/<w>/compute-result.json` (`driver_rc`)、`receipts/{submission,completion,acquisition}.json`、`preregistration.json`。

### 5.3 repo 内 (tracked) の一次資料

- policy: `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (sha256 `c6b24050…`、§1.1)。
- 床値: `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` の `between_run.cv` (§1.4)。
- 候補の genome と source digest の照合先: `docs/t1998-balanced-stock-inline-preregistration.md` v1 §2・§4.2。
- 失敗条件 (e) の原文: `docs/phase3-main-experiment.md` (「(e) target workload では勝つが他の workload で floor 超の退行がある →
  『workload 特化』として退行込みで全 workload の結果を報告する」)。

### 5.4 裁定

- ユーザー裁定 (2026-09-19、dev-wave 引数): 候補 = T-1998 事前登録の採用 arm、床値 = D1639 の between-run noise floor、判定 = 対差が
  −floor を下回れば退行、退行込みで 3 workload 全件を報告、B-7 要件充足は判定しない (D2044 項 3 維持)、機構 = A-2 / A-6 の
  certification 経路を descriptive に使う、既存材料と併記しプールしない、scope 外 = certification の昇格・新 protocol・追加 gate。
- D1639 (床値 = between-run noise floor)、D2044 項 3 (B-7 未了で維持)、D1993 項 6 (プール禁止)、D1874 (T-1998 認可)、
  D2148 項 5 (A-2 の nodes=5)。
- 段 4 裁定 (判定規則 v2・再投入規則) は wave の insight (`output/insights/2026-09-19/t1998-b7-fixed5-three-workload/`) の
  `verbatim/ruling-s4.md` に逐語で置く。

### 5.5 値の出所 (転記した数値ごと)

| 値 | 出所 |
|---|---|
| median・`effects`・`status`・`a4_noise_floor_status`・correctness・`src_token`・`source_binding_status`・binary digest | `certification.json` |
| 5 標本・`unstable`・`rep_notes`・toolchain・controlled define・run argv・36 記録の verdict | durable raw cell JSON |
| `cv`・abort 率・bench 時刻・`build_start` の digest | durable campaign WAL |
| request・Created / Started / Ended / Elapse・割当 node | durable `scheduler/` (`job.stderr`、`allocation-qstat.stdout`) と `submission-receipt.json` |
| 床値 3 値 | 床値 JSON `between_run.cv` |
| 百分率・判定 | 本稿が §1.4 の規則で計算 (機構の出力ではない) |

### 5.6 同じ結果についての既存の記述 (本稿の出所ではない)

- 無い。本 attempt について、本稿の前に results 系列の稿は無い。wave の記録 insight は本稿と同じ commit で置く。
