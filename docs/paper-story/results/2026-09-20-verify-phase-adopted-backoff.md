# 採用候補 fixed 5 µs / fixed 10 µs の検証相の結果節 — 独立 8 反復 × 3 workload (extime 3 s) の trace 検証で両候補とも 24 枠 anomaly ゼロ (S-1 (iv 付属) 規則の準用、2026-09-19〜20)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** A-2 の稿 (`2026-09-07-a2-certification-observed-positive.md`) と
[T-1998] の稿 (`2026-09-18-t1998-balanced-stock-inline-accepted.md`) が書く性能の判定と、その別走行の正しさ記録
(legacy 条件 1 回、A-2 は performance 側 5 回) はそのまま残る。本稿が足すのは、**同じ 2 つの固定 backoff 設定を、
別の日に、別の build (trace-enabled) で、独立 8 反復 × 3 workload の長い trace に掛けた正しさ検証の結果**である
(絶対規律 7: 既存の certified 記録を昇格も降格もしない)。

**`pass` は本 wave の runner が段 4 裁定 §4.1 の規則を機械適用した出力であって、研究の成功宣告ではない (D12)。**
また **本稿は S-1 事前登録 (iv 付属) の充足ではない。** 同節の対象は系側 gate 構成 (g_rl / g_rt) であり、
2026-09-19 のユーザー裁定により対象を採用候補 2 genome へ変え、同節の反復数・校正規則・判定規則を**準用**した
追加検証である。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**1 検証相 (2 候補 × 3 workload × 8 独立反復 = 48 verify) の 1 完走**である。校正 (段 A、6 job、18 記録 = 実走 16 + 規則により未実走 2) と本走
(段 B、12 job、48 走) を Pegasus gen_S の計算ノードで 2026-09-19 22:46 (段 A 投入) 〜 2026-09-20 00:43 (段 B 最終 job 終了) JST に走らせた。
再投入・再検証は 0 回である。

### 0.2 書くもの

- 候補 2 genome の定義と identity (source digest)、既存記録 (T-1998 v1、A-2) との対応。
- 結果を見る前に固定した校正規則・判定規則と、校正で確定した extime。
- 候補別の 24 枠の verdict、校正で完走した verdict、未完走 (校正 10 s) の件数と保全先。
- 予算 (本走 job の実消費) と限定。

### 0.3 書かないもの

- 性能 (trace-enabled build の throughput は診断生値であって性能値ではない。規律 1)。
- 形式的信頼度 1−εⁿ (ε の定義・数値 seed・乱数列の独立性を記録できない)。
- A-2 / T-1998 / A-6 の性能判定の変更、既存 certified 記録の昇格・降格 (規律 7)。
- 未完走 2 件の原因の確定、verifier の並列 parse の機序。
- S-1 事前登録本文への追記 (凍結束縛により本 wave では未履行、§5)。

---

## 1. 対象と固定条件

### 1.1 候補

| 候補 | genome (silo、共通 `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0`) | 出所 | identity (`src_token` = `source_bytes_sha256`、現行 patch 適用下、`cxx="g++"`、候補ごとの 9 job で build 前後とも期待値と一致) |
|---|---|---|---|
| fixed-5 | `BACK_OFF=1, BACKOFF_FIXED=5` | T-1998 事前登録 v1 の target (= A-2 rr50 の採用値) | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` — **T-1998 v1 §5 の値と bytes 一致** |
| fixed-10 | `BACK_OFF=1, BACKOFF_FIXED=10` | A-2 rr5 の採用値 | `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d` |

A-2 attempt `t2364-20260907b` が記録した `src_token` (rr50-fixed5 `21def77c944b…`、rr5-fixed10 `955b452a332d…`) とは
両候補とも一致しない。A-2 の source commit `31ec382a7` は `patches/silo-backoff-fixed.patch` の改訂 `91a5bfca3`
(2026-09-07、静的 backoff の表現可能上限を 999 から 9999 µs へ拡張) を含まない。改訂の差分は生値 ≥ 3000 の復号分岐だけで、
5 µs / 10 µs が選ぶ分岐は不変である。**本稿の fixed-10 は「A-2 で採用された固定 10 µs という設定を、現行 patch の
trace-enabled build で検証した」ものであり、A-2 当時のソース・バイナリの再検証ではない。** fixed-5 は T-1998 v1 の target と
source bytes まで同一である。

### 1.2 固定条件

- CCBench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`、patch `silo-backoff-fixed.patch` (sha256 `a5e0710c3f767447…`)、
  configure `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_BACKOFF_FIXED=<5|10> -DCCBENCH_BACKOFF_NOINLINE=0
  -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0`、g++-11 (Ubuntu 11.4.0)。
- workload: `ycsb_tuple_num=1,000,000`、48 thread、Zipf 0.9、rmw 0、max_ope 10、`clocks_per_us=2100`、
  write-heavy (`rratio=5`) / balanced (`rratio=50`) / read-heavy (`rratio=95`)、numactl なし。
- 「seed×N」は独立 N 反復 (ycsb は CLI seed を持たず run ごとに自己シードする)。N = bench process が生成した trace の数。
- verifier: `python3.10 -B -m orchestrator.verifier <trace_dir> --json --expected-commits <commit witness> --protocol silo
  --ccbench-root <checkout>` (別 process、現行 module、file 別 sha256 は insight §4.2)。
- 各 verify は 1 node で build → bench → C 行数え直し → trace の保全 (zstd) → verifier の順。単独性検査を bench・verifier の直前に実行。
- 実行場所: Pegasus gen_S 計算ノード (各 job 1 node、node-local build)。cygnus (07-16 校正の環境) は使っていない。

---

## 2. 方法 — 結果を見る前に固定した規則

段 4 裁定 (作成時刻は裁定文書の自己記載で 2026-09-19 22:2x JST、sha256 `2f9d8eb1…`。段 A 後の計算結果の追補 §7 だけを足した版が `1ddd2386…`) が正本。

1. **校正 (段 A):** 各 (候補, workload) で extime {3, 6, 10} s を昇順に各 1 回 trace run + verifier 実走。verifier wall > 600 s、
   または verifier 未完走 (hard timeout 3600 s / kill / rc=2 / JSON 破損)、または bench 失敗で、その extime 以上を打ち切る。
   適格 = bench 完走 ∧ verifier 完走 ∧ `serializable` ∧ certified ∧ anomaly 0 ∧ verifier wall ≤ 600 s。
   候補の extime = 3 workload の適格集合の共通部分の最大値 (空なら「候補なし」で本走を投入しない、3 s へ丸めない)。
   校正で完走した verifier に anomaly があれば当該候補は即失格 (規律 2)。
2. **予算:** 「≤ 4 時間/候補」は本走 24 verify の job 実消費 (dispatch Elapse の和) に束縛。校正は別欄。
   本走見込みが 14400 s を超えれば 1 段下げ、3 s でも超えれば本走を投入しない (N_verify は削らない)。
3. **判定 (本走後):** 判定集合 = 本走 24 枠 ∪ 校正で完走した verdict。**失格** = 判定集合に anomaly 1 件以上。
   **pass** = 24 枠すべてが bench 完走・trace 保全済み・verifier 完走・`serializable`・certified・`anomaly_count` 0・identity 一致、
   かつ判定集合に anomaly 0。それ以外は**未確定**。校正の未完走は pass を妨げないが、件数と保全先を必ず開示する。
4. **未完走の扱い (07-16 校正器の「timeout = 校正全体の失敗」からの意図的変更):** 資源上限 (node DRAM 約 115 GiB) は正しさ
   シグナルではないため、校正 verifier の未完走は `indeterminate` として記録し、完走 prefix から extime を決める。
   本走 verifier の未完走は同一の保全済み trace で 1 回だけ再検証を許す (本 wave では発生せず 0 回)。

---

## 3. 結果

### 3.1 校正 (段 A、投入 2026-09-19 22:46 JST、最初の job 開始 22:49:38、最後の job 終了 2026-09-20 00:01:24 JST、request 10868〜10873.nqsv)

| 候補 | workload | 3 s | 6 s | 10 s | 適格集合 |
|---|---|---|---|---|---|
| fixed-5 | write-heavy | 2,530,609 commit、verifier 115.676 s、certified・anomaly 0 | 5,017,504 commit、247.475 s、certified・anomaly 0 | 8,323,838 commit、verifier が hard timeout 3600 s で未完走 (`indeterminate`) | {3, 6} |
| fixed-5 | balanced | 4,450,058 commit、166.645 s、certified・anomaly 0 | 8,855,503 commit、357.002 s、certified・anomaly 0 | 14,748,197 commit、verifier が 303.093 s で SIGKILL (`killed_unknown`、`indeterminate`) | {3, 6} |
| fixed-5 | read-heavy | 16,819,316 commit、416.111 s、certified・anomaly 0 | 32,754,846 commit、864.291 s、certified・anomaly 0 だが 600 s 超で不適格 | 規則により未実走 | {3} |
| fixed-10 | write-heavy | 2,532,560 commit、114.098 s、certified・anomaly 0 | 5,018,742 commit、250.556 s、certified・anomaly 0 | 8,348,584 commit、hard timeout 3600 s で未完走 (`indeterminate`) | {3, 6} |
| fixed-10 | balanced | 4,286,776 commit、159.191 s、certified・anomaly 0 | 8,604,257 commit、344.028 s、certified・anomaly 0 | 14,230,861 commit、294.880 s で SIGKILL (`killed_unknown`、`indeterminate`) | {3, 6} |
| fixed-10 | read-heavy | 15,437,721 commit、384.936 s、certified・anomaly 0 | 30,656,095 commit、807.805 s、certified・anomaly 0 だが 600 s 超で不適格 | 規則により未実走 | {3} |

- 共通部分は両候補とも {3} → **extime = 3 s** (fixed-5・fixed-10 とも)。決定は runner の `summarize` の出力 `summary-A.json` (生成 2026-09-20 00:02:02 JST) で機械的に定まり、段 4 裁定 §7 に追補として記録した (追補 file の mtime 00:04:05 JST、段 B の投入 00:04:14 JST。追補の見出しにある「00:05」は親の推定で誤り、insight §5.2 の erratum)。
- 校正で完走した verdict は候補あたり 6 件、すべて `serializable`・certified・anomaly 0。未完走は候補あたり 2 件 (balanced 10 s、write-heavy 10 s)。
  未完走の trace は zstd で保全済み (job dir `run/calib/<候補>-<workload>/extime-10/trace/`)。
- 本走見込み B̂(3) = fixed-5 6346.534 s、fixed-10 5998.965 s (≤ 14400 s、段下げなし)。校正の実消費 (dispatch Elapse の和) = fixed-5 6462 S、fixed-10 6339 S。校正 + 本走の合計 = fixed-5 12,778 S (3.55 h)、fixed-10 12,473 S (3.46 h) (本走の予算判定は本走のみ、§3.3)。

### 3.2 本走 (段 B、2026-09-20 00:04 〜 00:43 JST、request 11268〜11279.nqsv、12 job × 4 反復)

| 候補 | workload | 枠 | commit の範囲 | verifier wall s (最小〜最大、中央値) | verifier 主 process maxrss GiB | verdict |
|---|---|---|---|---|---|---|
| fixed-5 | write-heavy | 8 | 2,471,532〜2,517,433 | 113.5〜117.3 (114.6) | 9.5〜9.6 | 8/8 `serializable`・certified・anomaly 0 |
| fixed-5 | balanced | 8 | 4,365,454〜4,464,643 | 160.7〜165.3 (162.9) | 13.7〜14.0 | 8/8 `serializable`・certified・anomaly 0 |
| fixed-5 | read-heavy | 8 | 16,456,248〜16,860,602 | 405.6〜416.3 (412.2) | 42.2〜43.3 | 8/8 `serializable`・certified・anomaly 0 |
| fixed-10 | write-heavy | 8 | 2,516,870〜2,533,193 | 113.8〜118.4 (115.7) | 9.6〜9.7 | 8/8 `serializable`・certified・anomaly 0 |
| fixed-10 | balanced | 8 | 4,300,911〜4,345,781 | 157.8〜161.7 (159.3) | 13.5〜13.6 | 8/8 `serializable`・certified・anomaly 0 |
| fixed-10 | read-heavy | 8 | 15,688,765〜16,078,316 | 386.5〜398.3 (396.1) | 40.3〜41.3 | 8/8 `serializable`・certified・anomaly 0 |

全 48 枠で `bench_attempt_id = 1`、`verify_attempt_id = 1`、integrity clean、trace 保全完了、identity 一致。bench 失敗・verifier 未完走・再検証は 0 件。

### 3.3 判定

| 候補 | 判定 (`summarize` の出力) | 判定集合 | anomaly | 未完走 (校正、開示) | extime | 本走の実消費 (≤ 14400 S) |
|---|---|---|---|---|---|---|
| fixed-5 | **pass** | 30 件 (本走 24 + 校正完走 6) | 0 | 2 件 | 3 s | 6316 S (1.75 h) |
| fixed-10 | **pass** | 30 件 | 0 | 2 件 | 3 s | 6134 S (1.70 h) |

校正を足した合計消費は fixed-5 12,778 S、fixed-10 12,473 S (別欄、§3.1)。

書き方: 「fixed-5 と fixed-10 の各候補について、trace-enabled build の独立 8 反復 × 3 workload (extime 3 s、計 24 verify) と
校正で完走した 6 verify の計 30 verify すべてで verifier は `serializable`・certified を返し anomaly は 0 件だった。
校正の extime 10 s の走 2 件 (balanced、write-heavy) は verifier が完走せず verdict を持たない (trace は保全済み)。」
**「全走 anomaly ゼロ」「serializable であることが示された」「信頼度 1−εⁿ」とは書かない。**

---

## 4. 限定

1. 判定は操作的事実であり確率主張ではない。数値 seed・乱数列の独立性は記録できない (記録は rep-id・PID・開始時刻・argv)。
2. 性能値を含まない。trace-enabled build の commit 数は診断生値であり、A-2 / T-1998 / A-6 の性能値と比べない。
3. 判定集合は 30 件 / 候補。校正 10 s の未完走 2 件は verdict を持たない (anomaly でも pass でもない)。原因 (`killed_unknown` の OOM 推定、
   write-heavy 10 s の並列 parse の停滞) は確定していない。
4. identity は現行 source に束縛される。fixed-10 の source bytes は A-2 当時と `91a5bfca3` 分だけ異なる。既存 certified 記録の昇格・降格はしない。
5. 18 job の binary は node ごとの別 build で `binary_sha256` が異なる。正しさ検証は量を比べないので判定に影響しないが、
   「同一 binary で 24 反復した」とは書けない。source identity は候補ごとの 9 job で期待値と一致し、toolchain は 18 job で同一。
6. verifier は現行版 (2026-09-02 の並列化後)。07-16 の cygnus 校正 (verifier 433.3 / 974.7 s) とは code も環境も違い、数値は併記であって置き換えではない。
7. 校正の未完走を `indeterminate` として完走 prefix から extime を決めた規則は、07-16 校正器の「timeout = 校正全体の失敗」からの
   意図的変更である (D fragment 項 5)。
8. S-1 (iv 付属) の「確定値は本節へ日付付き追記」は本 wave では未履行の繰延べ (§5)。本稿は S-1 の充足ではない。
9. job の予約 walltime (校正 2 h、本走 3.5 h) に上限保証は無かった (校正 verifier の hard timeout 3600 s で上限式を引き直すと最悪 8760 s > 7200 s、runner 内の setup+build 2400 s は事後検査、保全に timeout なし)。実測の最大は dispatch Elapse 4063 S (runner の job wall 4057.876 s、校正 fixed-10 write-heavy) で予約内に収まったが、これは結果であって保証ではない (insight §7 項 9、§10 A7)。

---

## 5. 一次資料

- 記録 insight: `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` (条件・identity・校正 18 行・本走 48 枠・判定・限定・一次資料 path) と同 `verbatim/`。
- 集計 (判定の出所): job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/summary-B-fix1.json`
  (sha256 `f7248a7f1de6e41d2e7e4a5a9753d6752fc79fc41ae0ba4104a34f1cf9246e37`、runner v2 sha256 `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5`
  の `summarize --accept-ruling-sha 2f9d8eb1… --accept-ruling-sha 1ddd2386…`)。校正の集計 `run/summary-A.json` (sha256 `0ed068a6…`)。
- 各 verify の記録: `run/calib/<候補>-<workload>/extime-<e>/result.json` (18 件)、`run/verify/<候補>-<workload>-<k>/rep-<i>/attempt-1/result.json` (48 件)、
  verifier の生 JSON と stderr、bench stdout、保全 manifest と zstd trace (3072 file、原本 213.3 GB → 48.9 GB)。走行 runner v1 sha256 `91bbf85d594085a4900bb2e9272bd455cef18e83c258ccfe5828594c0afd82a7`。
- 規則: 段 4 裁定 `s4-ruling.md` (段 A 版 sha256 `2f9d8eb1e6520bb45cbb2eff76ede4286a23b39c29463cc50b18019ae97610cd`、追補版 `1ddd2386ef1f4558077fffbef4bcab882205f955a5e4c8f9375d01b64cfd9201`)、
  ユーザー裁定の控え `rulings-inbox/2026-09-19-verify-phase-adopted-backoff-authorization.md`、設計判断 = `docs/decisions.md` の
  「採用候補 2 genome の検証相は S-1 (iv 付属) の規則を準用した追加検証とし、extime は候補共通 3 s、校正確定値の記録先は decisions・insight・results 稿とする」
  (wave `dev-wave-verify-phase-adopted-backoff` の fragment を fold したもの。D 番号は `docs/spool/FOLDED.md` の受領証で引く)。
- 準用元: `docs/phase3-main-experiment.md` 層 1 (iv 付属)「検証相の拘束数値」と 2026-07-16 の校正確定追記。**同節への追記は本 wave では行っていない**
  (同文書は `output/s1-freeze/known_axes_freeze.json` の source sha256 として凍結され、追記は `verify_document` を赤にする。凍結の解除はユーザー明示命令のみ)。
- 候補の出所: `docs/t1998-balanced-stock-inline-preregistration.md` v1 §2 / §4.2 / §5、`docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md` §1 / §2、
  A-2 権威 bytes `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` (`cells[].src_token`)。
