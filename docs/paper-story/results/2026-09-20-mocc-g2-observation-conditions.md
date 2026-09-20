# stock mocc の G2 signal の観測条件の分離 — witness off に固定した 3 arm × 各 120 走で通常 5/120・診断 0/120・`BACK_OFF=1` 2/120 (非 certifying の観測記録、[T-2779]、2026-09-18)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

---

## 0. 位置づけ — 限定を先に、次に何を書くか

### 0.1 この稿が言わないこと (先に読む)

1. **非 certifying の観測記録である。** 本稿のどの数値も headline・certified 選択・floor・oracle・fitness の根拠にしない。
   個別 verifier 出力の `certified: true` (353 走) と arm 定義の `observational_only: false` (通常・`BACK_OFF=1` arm) は runner の
   field であって、本観測の認証を意味しない。mocc の certified 昇格判定は本稿で行わない。
2. **TRACE=1 の観測専用 build である。** 全 arm が `-DCCBENCH_TRACE=1` で、X/P 計装 patch (D1686、`#if TRACE` 内の lock 被覆・
   permutation 検査) を当てた producer である (絶対規律 1: 性能計測用 build ではなく、性能値を含まない)。
3. **pin 前進なし。** CCBench の gitlink は `511c9538` のまま。producer の source は hook branch 先端 `e9e477ca` である。候補 `e9e477ca`
   への pin 前進は D2150 項 1 で承認されたが未実施であり、D2159 も探索・pin 前進・軸採用を認可していない。本稿は前進の根拠にならない。
4. **頻度差から `BACK_OFF=1` の抑制効果や正しさを結論しない。** 主比較 ② (`BACK_OFF=1` 2/120 対 通常 5/120) の片側 Fisher は
   未調整 p = 0.2230864755 で、事前登録の言い方は「この標本・条件では低下を検出できない」まで。効果ゼロ・同等性・「backoff が G2 を
   抑える」「backoff 下でも正しい」のいずれも書かない。`BACK_OFF=1` の arm にも signal が 2 件ある。
5. **G2 signal の再現を根因確定としない** (D2148 項 13、上流向け報告 [T-2791] の限定と同じ)。診断 arm の 0/120 は「固定条件で、
   2 変更を束ねた介入と検出率低下が整合する」までで、cold 側検査と validation 再読の寄与、経路 (i)/(ii)、実装 / hook / verifier 仮定の
   三分岐は識別できない。診断 patch は拒否条件を足して受理集合を縮小する介入であり、元実装の根因同定にも修正版の認証にも読み替えない。
6. **陰性結果を「G2 が無い」証拠にしない。** 0 件は不在証明ではなく、非有意は同等性証明ではない。
7. **全走 witness off である。** discriminator は 360 走すべて `not-run (witness-off)` で、7 件の signal の実行順序 (読み値の出所照合)
   を discriminator で同定したものではない。
8. **主比較 2 本の family 全体で有意とは判定しない。** 診断側の未調整 p = 0.0299507441 は単一比較の参考値であり、多重比較の調整を
   していない。CP 区間と Fisher は独立・同率 Bernoulli を仮定し、node 内相関・回転順・時間変動をモデル化していない。
9. **規律 2 は緩めない。** verifier / discriminator の受理集合は本観測で 1 文字も変えていない。anomaly を検出した走の即 reject 契約、
   [T-1892] の 5/42、[T-1943] の `no-g2`、[T-2774] Q1 / Q2 の判定は各旧束縛で保持する (絶対規律 7)。
10. **性能・throughput を書かない。** §3 の commit 数は TRACE=1 build の診断生値 (trace の規模) であって性能値ではなく、arm 間の
    throughput 比較にも signal / commit の率にも使わない。

### 0.2 この稿の単位

**runner v5 (`t2779_probe.py`) の非 certifying 観測 1 試行 = 4 block (B1〜B4) × 30 round × 3 arm = 360 走 (各 arm 120 走) の 1 完走**
である。Pegasus gen_S の計算ノード 4 台で 2026-09-18 15:50 (4 block 投入) 〜 16:37:04 JST (最終 block 終了) に走らせ、
smoke 1 block (3 走、別 node) は本走に合算しない。再投入・補充・再計測は 0 回である。

results 系列の「1 結果 = 1 protocol の完走」に当たるのは、**段 4 裁定 (`s4-ruling.md`) が結果を見る前に固定した単一の観測 protocol
(標本 = 4 block × 30 round × 3 arm、主比較 2 本、主表示、欠測規則) を 4 block で完走した 1 結果**である。certification 経路でも campaign
経路でもなく、単一の outer status を持たない。status 欄に相当するのは runner の機械集計 (`summary.json`、schema `t2774-summary/v1`) の
arm 別 k / m である。

### 0.3 書くもの

- 3 arm の定義と固定 cell、identity の束縛 (pin・patch sha・define・source sha・runner sha)。
- 結果を見る前に固定した事前登録 (主比較 2 本、主表示、欠測規則、標本の根拠 = 計算値)。
- block 別・arm 別の k / m、合算の k / m と Clopper–Pearson 両側 95% 区間、主比較 2 本の片側 Fisher の未調整 p、G2 7 走の verifier 出力の構造、
  全 360 走の verifier / integrity / discriminator の会計、欠測会計。
- 成果物に無い情報・束縛の範囲・本稿で未照合の対応 (§4)、限定 (§5)、一次資料 (§6)。図は無い。

### 0.4 書かないもの

- witness 軽量化の静的設計 (一次資料 insight §3)。本稿の結果ではなく、その後の実走 (別 insight) も本稿の出所ではない (§6.5)。
- [T-2774] の率 (2/40 等) の再掲。本試行の事前登録が置いた基準率 (0.058 / 0.05) は設計仮定として §2 に書き、[T-2774] の結果としては書かない。
- 生 trace の再解析 (7 走の thread id 対応表の作成を含む)、実行順序・読み値の出所の同定 (§4)。

---

## 1. 対象と固定条件

### 1.1 問い

[T-2774] の次の一手として、discriminator の観測条件 (witness on) で G2 signal が 0/40 になる理由を分離する。本試行が実走したのは
次の 2 問である (3 問目の witness 軽量化は静的設計まで、§0.4)。

- ① 診断 patch (validation の版再読 + cold 側 abort、`mocc-close-version-counter-gap.patch`) を witness off で走らせ、同一 block で
  通常 arm と検出率を比べる。
- ② `BACK_OFF=1` の witness off arm で、`BACK_OFF` だけの変更による検出率差を witness と分離して見る。

### 1.2 3 arm

| arm | pin | patch | witness | `CCBENCH_BACK_OFF` | `observational_only` | source (`transaction.cc` 適用後) sha256 |
|---|---|---|---|---|---|---|
| `e9-instr-nowit` (通常) | `e9e477ca` | X/P | off | 0 | false | `bd0add59890a60150b9c650155943ddd0c1e91eeccc0121a6b674c834b3ed04c` |
| `e9-diag-nowit` (診断) | `e9e477ca` | X/P + 診断 | off | 0 | true | `1c5da7c8439144d02621071622e5eba31f1ff583c4fbda5efdfe7483c2c3168a` |
| `e9-instr-nowit-bo1` (backoff) | `e9e477ca` | X/P | off | **1** | false | `bd0add59890a60150b9c650155943ddd0c1e91eeccc0121a6b674c834b3ed04c` (通常と同一、define だけ違う) |

- pin = `e9e477ca1b55348ab4530de0b1cf663ce4555290` (hook branch `izanagi-t1943-mocc-g2-readfrom-witness` 先端、witness コードあり)。
  gitlink `511c9538` は動かしていない。
- X/P 計装 patch = repo の `patches/instr-mocc-lock-coverage.patch` (sha256 `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48`、
  4,080 byte、D1686)。診断 patch = `mocc-close-version-counter-gap.patch` (sha256 `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d`、
  1,168 byte、[T-2774] job dir 由来、本試行 job dir `verbatim/` の写し)。診断 patch の中身は 2 hunk — read 側で `RWLOCK` の
  `ldAcqCounter() == W_LOCKED` なら `ERROR_LOCK_FAILED` で abort、validation 側で counter 検査後に tidword を再読し epoch / tid が変わっていれば
  `failed_verification_` を立てて abort (`#line` で行番号を保つ)。
- witness は env 未設定 (全 arm off)。arm 定義は `arms-t2779.json` (sha256 `4f6aaf5a172eb8eb737bd0ec6e2fcc52e92b5dce2691803f65d8f34e327ebb56`)。
- `observational_only` は「診断介入の観測専用」という位置づけを run / discriminator 記録へ写す runner の field であり、個別 verifier の判定を
  書き換える処理ではない (診断 arm だけ true)。

### 1.3 固定 cell と build

- workload argv (全走同一): `-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`。
  [T-2774] と同じ固定 cell (3 秒・48 thread・10,000 record・rratio 50・rmw 0・max_ope 10・zipf 0.9)。
- configure 基底 = [T-1943] pilot と同一: `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1
  -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (+ `-DCCBENCH_CCACHE=OFF`)。
  backoff arm は `-DCCBENCH_BACK_OFF=1` だけを置換 ([T-2774] Q1 の `KEY_SORT=0` / `TEMPERATURE_RESET_OPT=1` は持ち込まない)。
- toolchain: `/usr/bin/x86_64-linux-gnu-gcc-11` / `g++-11` (version 本文 sha256 `b713e6ab…`、4 block + smoke で同一)。
  policy `tools/pegasus/mocc_trace_v1_policy.json` (sha256 `66ea7135c6d84cfd09013f33da23d8ca8015dcb547e34db7c802644f4986acd6`)。
- 各走: 別 trace dir → `python3.10 -B -m orchestrator.verifier <trace_dir> --json --protocol mocc --ccbench-root <arm の source>
  --expected-commits <commit 数>` (timeout 300 s、outer main `c8e8dc06f` の module) → cycle 正の走だけ trace-manifest を作り生 trace を退避 →
  走ごとに JSON を逐次保存。discriminator は witness off なので `not-run`。runner は開始時と各走前に `_assert_single_tenant()` を呼ぶ
  (既存検査の射程内で、node 専有の実証ではない)。

### 1.4 identity の束縛 (4 block の照合)

runner `t2779_probe.py` v5 (sha256 `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99`、40,315 byte、[T-2774] v4 起点、
Codex `role=author`、差分 `v4-to-v5.diff` sha256 `e6979b71…`)、outer `repo_head` `c8e8dc06f33891aa2fd6345063b30ca11b52fe6d`、workload argv、
arm ごとの pin・patch sha・witness・`observational_only`・configure define・source sha256、arms JSON sha、policy sha、toolchain は
**4 block の `result.json.bindings` で全部一致**する (本稿執筆時に現物で再照合)。**binary sha256 は block ごとに異なる** (node-local build、
例: B1 通常 `4317ea39…`、診断 `077fabf8…`、backoff `3bf14e56…`)。source と build の一時 path、投入元 worktree (B1 = wave worktree、
B2〜B4 = `t2779-node2/3/4`) も block ごとに異なる。「同一 binary で 120 走した」とは書けない。

### 1.5 実行 identity

| block | request | node | Created / Started / Ended (JST、NQSV 要約) | Elapse (S) | 投入元 |
|---|---|---|---|---:|---|
| smoke (合算しない) | `5875.nqsv` | bnode049 | 15:36:29 / 15:46:26 / 15:48:17 | 116 | wave worktree |
| B1 | `5894.nqsv` | bnode037 | 15:50:01 / 15:59:55 / 16:37:04 | 2233 | wave worktree |
| B2 | `5895.nqsv` | bnode042 | 15:50:07 / 15:50:15 / 16:27:12 | 2222 | `t2779-node2` |
| B3 | `5897.nqsv` | bnode044 | 15:50:14 / 15:55:36 / 16:32:39 | 2227 | `t2779-node3` |
| B4 | `5898.nqsv` | bnode045 | 15:50:21 / 15:50:29 / 16:27:34 | 2229 | `t2779-node4` |

queue `gen_S`、generic dispatch、walltime 02:30:00。4 block の job 実消費 (Elapse の和) = 8,911 S (2.48 h)、smoke 116 S は別欄。
`result.json` の `started_at` / `finished_at` (UTC、秒未満切り捨て) は B1 06:59:56 / 07:37:04、B2 06:50:16 / 07:27:12、B3 06:55:37 / 07:32:38、
B4 06:50:29 / 07:27:33 で、NQSV の Started / Ended (JST = UTC + 9 h) と 0〜1 秒の差で整合する。

---

## 2. 方法 — 結果を見る前に固定した規則

段 4 裁定 `s4-ruling.md` (sha256 `14dbfd6c2f6b101888948c0505c903d78b35e9903f60ec42b3f1c7ed68eb8d6a`、12,366 byte、mtime 2026-09-18
15:26:11 JST = smoke 投入 15:36:29 より前) の項 6 が事前登録の逐語、項 7 が診断 arm の結果別の主張範囲である。
同文書の見出しは「15:30 JST 起草」と自己記載しており、mtime と 4 分ずれる (本稿は mtime を採る)。

1. **標本:** 4 block × 30 round × 3 arm、各 round で 3 arm を 1 回ずつ、開始 arm を round ごとに回転 (`round_order` ABC / BCA / CAB、
   30 は 3 の倍数なので各 node で各 arm が各位置に 10 回)。計画数は各 arm 120 走で**結果を見て増減しない**。smoke と [T-2774] Q1 / Q2 は合算しない。
   launcher は round 数を引数で受け (`--rounds 30`)、本走 4 block の実値が 30 であることを `result.json.rounds` で確認した。
2. **主比較 (2 本固定):** ① `e9-diag-nowit` 対 `e9-instr-nowit`、② `e9-instr-nowit-bo1` 対 `e9-instr-nowit`。介入側の検出率が低下する方向の
   片側 Fisher を参考値、主表示は arm 別 k / m と Clopper–Pearson 両側 95% 区間。2 比較の未調整 p を示し、どちらか 1 つの p < .05 で family
   全体の効果とは判定しない。block 別件数を併記し、合算値だけから node 一般の効果を主張しない。
3. **分母:** 計画数 120、保存済み走数 N、有効 verifier 判定数 m、G2 signal 数 k、failure、indeterminate、未開始を分ける。主区間は k / m。
   failure・未開始を no-G2 と数えず、indeterminate も certified no-G2 と同一視しない。
4. **欠測規則:** 集計締切は 4 block の dispatch `.done` が揃った時点、または最初の投入から walltime + grace (13,200 秒) の早い方。block ごとに
   (a) 保存済み (`result.json.runs` 収載)、(b) 開始証拠あり・未収載、(c) 未開始確認済み、(d) 状態不明を区別し、主解析は (a) だけ。揃わない block は
   補充せず、完走 block だけを事後選択したとは書かず、不足を明示する。原本は書き換えない。
5. **標本の根拠 (計算値、実測ではない):** `s4-ruling.md` 項 6 の逐語 (空白整形なし) は「検出力は独立試行・等標本・完全抑制・単一比較の片側 α=.05 の設計仮定で、基準率 0.058 なら 83%、直接対応 arm の点推定 0.05 なら 72% (計算値であり実測ではない)」まで。
   基準率の由来 (0.058 = [T-2774] の witness off 合算 7/120 = 0.058333… を丸めた値、0.05 = 直接対応 arm の 2/40) と、部分抑制 (0.058 対 0.02) で 0.30、2 比較で各 α = .025 なら 0.058 対 0 で約 0.70 という追加の値は、
   事前登録本文ではなく記録 insight §4 の親の設計説明にある。本稿執筆時の独立再計算 (K = 120、丸め前) は 0.831467 / 0.721809 / 0.302390 / 0.701730。
6. **診断 arm の結果別の主張範囲 (逐語):** 低下 → 「固定条件で、2 変更を束ねた介入と検出率低下が整合する」まで。差なし → 「この標本・条件では
   低下を検出できない」。診断でも正例 → 「当該 producer / 計器条件で signal が残る」。
7. 変異 matrix は repo の実装面差分ゼロで免除、受入全走は免除しない。CCBench 本体の改変は D16 / D18 / D20 に従い insight の構造化まで。

---

## 3. 結果

### 3.1 block 別・arm 別の k / m

| block | node | 通常 k/m | 診断 k/m | backoff k/m | 保存済み (a) | (b) / (c) / (d) |
|---|---|---:|---:|---:|---:|---|
| B1 | bnode037 | 1/30 | 0/30 | 0/30 | 90 | 0 / 0 / 0 |
| B2 | bnode042 | 2/30 | 0/30 | 2/30 | 90 | 0 / 0 / 0 |
| B3 | bnode044 | 1/30 | 0/30 | 0/30 | 90 | 0 / 0 / 0 |
| B4 | bnode045 | 1/30 | 0/30 | 0/30 | 90 | 0 / 0 / 0 |
| 合算 | — | **5/120** | **0/120** | **2/120** | 360 | 0 / 0 / 0 |

4 block とも `status: completed`、`not_started: 0`、`runs` 90 件、run directory 90 個、ordinal 1〜90 に重複なし。全 arm で計画数 = N = m = 120、
failure = indeterminate = 未開始 = 0。backoff arm の 2 件は B2 に集中し、B1 / B3 / B4 は 0/30 である (block 別併記の意味はここにある)。

### 3.2 合算の検出率と Clopper–Pearson 両側 95% 区間 (`summary.json`)

| arm | k/m | 検出率 | CP 95% 区間 | `decisive_m` |
|---|---:|---:|---|---:|
| `e9-instr-nowit` (通常) | 5/120 | 4.1667% | [1.3665%, 9.4559%] | 120 |
| `e9-diag-nowit` (診断) | 0/120 | 0% | [0%, 3.0273%] | 120 |
| `e9-instr-nowit-bo1` (backoff) | 2/120 | 1.6667% | [0.2025%, 5.8909%] | 120 |

`summary.json` の生値: 通常 `k_over_m` 0.041666666666666664、`cp95` [0.013665384116789837, 0.09455879997593641]、診断 0.0、[0.0, 0.03027297257742008]、
backoff 0.016666666666666666、[0.0020248223376931147, 0.05890921946702635]。`denominator` は「m は有効 verifier 判定 (indeterminate 込み)、
`decisive_m` は zero-cycle indeterminate を除く、failure も indeterminate も no-g2 ではない」、`interval_assumption` は「独立 Bernoulli、node 依存は
未モデル化」。本稿執筆時に 4 block の `result.json` から k / m を独立に再集計し、CP 区間を独立に再計算して全桁一致した。

### 3.3 主比較 2 本の片側 Fisher (参考値、未調整)

行 = 介入 / 通常、列 = G2 / 非 G2 で、診断 `[[0, 120], [5, 115]]`、backoff `[[2, 118], [5, 115]]`。介入側の G2 数を x、観測値を k、両群合計を K として
`sum(comb(120, x) · comb(120, K − x) / comb(240, K), x = 0..k)`。

| 比較 | 表 | 未調整片側 p | 事前登録の言い方 |
|---|---|---:|---|
| ① 診断 対 通常 | 0/120 対 5/120 | **0.0299507441** | 固定条件で、2 変更を束ねた介入と検出率低下が整合する (三分岐は識別できない) |
| ② backoff 対 通常 | 2/120 対 5/120 | **0.2230864755** | この標本・条件では低下を検出できない (効果ゼロ・同等性は言えない) |

本稿執筆時に超幾何和を独立に再計算し、両 p 値とも全桁一致した。2 比較の family 全体で有意とは判定しない (§0.1 項 8)。

### 3.4 G2 signal 7 走の verifier 出力

7 走とも `verdict: non-serializable`、`certified: false`、`total_cycles: 1`、`anomaly_count: 1`、anomaly は `phenomenon: G2`、`length: 2`、
2 辺とも `types: ["rw"]`、`integrity.clean: true` (orphan / dup / genesis / missing / mismatch / framing / lock 被覆 / write intent / permutation
違反すべて 0)。verifier process は rc = 1、timeout なし。値は各走の `verifier.json` の書写である。thread id は `verifier.json` に無く生 trace の
C 行にある (§4 項 12)。実行順序・読み値の出所の同定は含まない。

| 走 (block / ordinal) | arm | round / 位置 | cycle (txid) | 辺 1: key、`u_ver` → `v_ver` | 辺 2: key、`u_ver` → `v_ver` | commit 数 |
|---|---|---|---|---|---|---:|
| B1 / 082 | 通常 | 28 / 1 | 406139 → 406140 → 406139 | `…0005`、[42, 175] → [42, 177] | `…0002`、[42, 169] → [42, 176] | 706,655 |
| B2 / 030 | backoff | 10 / 3 | 444929 → 444930 → 444929 | `…0001`、[36, 3228] → [36, 3230] | `…0003`、[36, 3215] → [36, 3229] | 940,610 |
| B2 / 033 | 通常 | 11 / 3 | 77262 → 77263 → 77262 | `…0024`、[8, 3992] → [8, 4051] | `…0001`、[8, 4048] → [8, 4050] | 729,683 |
| B2 / 069 | 通常 | 23 / 3 | 664344 → 664346 → 664344 | `…0001`、[59, 2574] → [59, 2577] | `…0000`、[59, 2570] → [59, 2575] | 697,384 |
| B2 / 077 | backoff | 26 / 2 | 188924 → 188925 → 188924 | `…0001`、[16, 855] → [16, 857] | `…0003`、[16, 854] → [16, 856] | 911,995 |
| B3 / 006 | 通常 | 2 / 3 | 336032 → 336033 → 336032 | `…0000`、[36, 233] → [36, 236] | `…0001`、[36, 233] → [36, 235] | 694,541 |
| B4 / 080 | 通常 | 27 / 2 | 268125 → 268126 → 268125 | `…0000`、[29, 1964] → [29, 1966] | `…0001`、[29, 1964] → [29, 1965] | 694,992 |

- key は 16 桁 hex の下 4 桁、版は `[epoch, tid]` の生値。「位置」は当該 round の `order` 内での arm の順番 (1〜3)。7 走の位置は 1 / 3 / 3 / 3 / 2 / 3 / 2 で、
  偏りの有無を判定する設計にはなっていない。
- 7 走の生 trace (各 48 file、計 336 file、1,981,789,619 byte) は job dir の `runs/<ordinal>-<arm>/trace/` に保全され、各 `trace-manifest.json`
  (schema `mocc-g2-standard-trace-manifest/v1`、`source_oid` `e9e477ca…`、arm の `binary_sha256`、workload) の file 名・size・sha256 と
  **336/336 一致**する (回収 wave の `recovery-raw-hashes.log` と本稿執筆時の再照合の両方)。
- commit 数は TRACE=1 build の診断生値 (trace の規模) であって性能値ではない (§0.1 項 10)。参考として 120 走の範囲は 通常 438,124〜752,037、
  診断 587,282〜751,790、backoff 887,969〜964,464 で、arm 間の比較・率への換算はしない。

### 3.5 全 360 走の会計

| 区分 | 走数 | verifier | rc | discriminator |
|---|---:|---|---|---|
| G2 signal | 7 | `g2` / `non-serializable` / certified false / cycle 1 | 1 | `not-run` (witness-off) |
| 非 G2 | 353 | `no-g2` / `serializable` / certified true / cycle 0 / anomaly 0 | 0 | `not-run` (witness-off) |

全 360 走で bench rc = 0・timeout なし (bench 実走 3.068〜3.121 s)、verifier timeout なし (wall 通常 10.4〜20.2 s、診断 14.6〜19.8 s、backoff 24.0〜26.9 s)、
`integrity.clean` 360/360。`summary.json` の `discriminator_counts` は 3 arm とも `not-run: 120`、`identification.identified_g2_runs` は 0。

### 3.6 書き方

「witness off に固定した同一 cell で、各 block 内に 3 arm を回転配置した 4 block (別 node、各 arm 合計 120 走) について、通常 arm は 5/120
(CP 95% [1.37%, 9.46%])、診断 patch arm は 0/120 ([0%, 3.03%])、
`BACK_OFF=1` arm は 2/120 ([0.20%, 5.89%]) の G2 signal を得た。介入側が低下する方向の片側 Fisher (未調整) は診断 0.0300、backoff 0.2231。
前者は固定条件で 2 変更を束ねた介入と検出率低下が整合するという材料まで、後者はこの標本・条件では低下を検出できない。7 件の signal はいずれも
長さ 2・両辺 rw の G2 で、生 trace を保全した。全走 witness off のため discriminator は走っていない。」
**「診断 patch が G2 を止めた」「backoff は G2 に影響しない / G2 を抑える」「有意」「G2 が無い」「根因」とは書かない。**

---

## 4. 成果物に無い情報・束縛の範囲・本稿で未照合の対応

**成果物に無い (存在しない):**

1. 非 G2 353 走の生 trace。runner は cycle 正の走だけ trace を退避し、353 走の run directory に `trace/` は無い。353 走の再検証は verifier JSON と
   run JSON の記録に限られ、生 trace からはやり直せない。
2. verifier module の file 別 sha256。走行記録は argv (`-m orchestrator.verifier … --protocol mocc`) と cwd (wave worktree、outer `c8e8dc06f`) を持つが、
   verifier の file digest を持たない。束縛は outer commit までである。
3. G2 cycle の実行順序・読み値の出所照合。全走 witness off で discriminator は `not-run` であり、`verifier.json` の anomaly は txid・key・版 (`[epoch, tid]`)
   までである (thread id は verifier 出力には無いが生 trace にはある — 項 12)。
4. witness on の対照 arm。本試行は witness off に固定した 3 arm だけで、witness on / off を同一 block で比べていない。
5. 数値 seed。ycsb は CLI seed を持たず走ごとに自己シードする。記録は ordinal・round・開始時刻・argv。
6. node 専有の実証。runner の `_assert_single_tenant()` は既存検査の射程内で、4 node の同時刻の他 process の記録は無い。
7. 性能値。TRACE=1 build の commit 数は診断生値 (§3.4)。

**束縛の範囲 (あるが射程が限られる):**

8. binary は block ごとの node-local build で sha256 が異なる (§1.4)。source sha256・define・toolchain の一致までが束縛である。
9. 診断 patch の原本は [T-2774] job dir にあり、本試行 job dir `verbatim/` の写し (sha256 一致) を適用した。repo の insight `verbatim/` にある
   `.patch.txt` 2 本は末尾空白の正規化で原本と bytes が異なり、原本 sha は同 dir の `whitespace-errata.json` に記録されている (§6.1)。
10. 事前登録は job dir の `s4-ruling.md` (mtime 15:26:11 JST) で、凍結 gate に束縛された文書ではない。「結果を見る前に確定」の根拠は mtime と smoke /
    本走の投入時刻の順序である。

**本稿で未照合の対応:**

11. smoke 3 走 (`5875.nqsv`、bnode049、3 走とも `no-g2`) の bindings を本走と照合したのは runner sha・policy sha・toolchain までで、合算しない
    走なので arm の source sha は照合していない。
12. G2 cycle の thread id。生 trace の C 行は `C <txid> <thid> <epoch> <tid> <read_set 数> <write_set 数>` の順で書かれ (source `transaction.cc` の
    `writePhase()`、`#if TRACE` 内)、B1/082 では `trace_33.log` に `C 406139 33 42 176 4 6`、`trace_0.log` に `C 406140 0 42 177 6 4` がある
    (txid 406139 は thread 33、406140 は thread 0)。本稿で現物を確かめたのはこの 1 対だけで、7 走 14 txid の対応表は作っていない。
13. [T-2774] の基準率 (7/120、2/40) は事前登録の設計仮定として写し、[T-2774] の一次資料へは本稿で再照合していない。

---

## 5. 限定 (この結果が言わないこと)

§0.1 の 10 項に加えて:

11. 診断 arm の 0/120 は「当該 producer / 計器条件で 120 走の間に signal が出なかった」までで、CP 上限 3.03% が示すとおり率 0 を意味しない。
12. backoff arm の signal 2 件は B2 に集中する。block 別の差 (B2 2/30、他 0/30) から node・時刻の効果を主張しない。
13. 検出力 0.83 / 0.72 は設計仮定 (独立・等標本・完全抑制・単一比較) の計算値であり、この試行の実測ではない。部分抑制なら 0.30 まで落ちる。
14. 「`BACK_OFF=1` は witness と分離した」は設計 (全走 witness off) の記述であって、witness on での backoff の挙動を言わない。
15. 診断 patch の 2 変更 (cold 側 abort、validation の再読) は束ねて入れたので、どちらが低下に寄与したかを分離できない。
16. 本稿の producer (X/P 計装付き `e9e477ca`) は certified 系列の producer ではない。本観測は between-run floor の生成可否 (D1373 の関門) を
    検査したものでも変えたものでもなく、mocc の certified 系列・floor・oracle に何も足さない。
17. 生 trace の保全は「再解析できる」ことであって、再解析したことではない。§3.1・§3.4・§3.5 の会計と G2 の構造は走行時の verifier / run JSON からの
    転記で、生 trace からの再検証は行っていない (§4 項 12 の 1 対を除く)。時刻・Elapse は NQSV 要約、検出力は設計計算値、Fisher / CP は
    `summary.json`・記録 insight の値と本稿執筆時の独立再計算の一致までである。
18. 同一 cell の反復であっても、4 block は別 node・別 binary・別 時刻であり、「同一条件の 120 反復」とは書けない (§1.4)。

---

## 6. 一次資料

### 6.1 repo 内 (tracked、commit `69fa71cd3`)

- 記録 insight: `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md` (sha256 `559d8e68ee9d875bd9580ef08e70a9c3641019d225c6d7579a8958a0767a9724`、
  18,497 byte)。§0 問い、§2 束縛、§3 静的設計、§4 実走設計、§5 結果と欠測会計、§6 解釈の上限、§7 中断回収の範囲。
- 集計 (k / m・CP 区間の出所): 同 dir `summary.json` (sha256 `fee7803f27bbdf2637b4d4f667430e379e1a89f09d47b4056a1892b14a765459`、3,612 byte)。
  `inputs` に 4 block の `result.json` の path と sha256 を持つ。
- 同 dir `verbatim/`: `B1-result.json`〜`B4-result.json` (job dir 原本と sha256 一致)、`s4-ruling.md` (原本と一致 `14dbfd6c…`)、`arms-t2779.json`、
  `t2779_probe.py.txt` (原本と一致 `7907a545…`)、`v4-to-v5.diff.txt`、G2 7 走の `run.json` / `verifier.json` / `trace-manifest.json`、
  `dispatch-B1〜B4.log`、`recovery-raw-hashes.log` (sha256 `96195423…`、7 走 PASS 48 / TOTAL 336 1981789619)、`whitespace-errata.json`
  (sha256 `8edb281d…`、`.patch.txt` 2 本と log 等の原本 sha・末尾空白位置)、段 2 / 3 / 5 / 回収レビュー A・B の逐語、`mocc-transaction-e9e477ca.cc.txt`。
- X/P 計装 patch: `patches/instr-mocc-lock-coverage.patch` (sha256 `e9e65b78…`、job dir `verbatim/` の写しと一致)。policy: `tools/pegasus/mocc_trace_v1_policy.json`
  (sha256 `66ea7135…`)。

### 6.2 job dir (repo 外、durable authority) — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/`

| file | sha256 | byte |
|---|---|---:|
| `arm-B/B1/result.json` | `db26afc7fcab7772c672cf5b112f05f58d9c3e72d77a20fd176840aacd60e427` | 277,951 |
| `arm-B/B2/result.json` | `f5cdf50fda33162039107480d0646e05d736883b83471f2a7c3da0f9200ccdb7` | 274,819 |
| `arm-B/B3/result.json` | `c883caa298584ebb0d20609618ddd8de413d6cab14e2ed45109c3b9f5643075d` | 274,669 |
| `arm-B/B4/result.json` | `7e43392f4af7fc64c86ce6b86fa9d79b020187b3ed712c3561b8f0f26667ea25` | 274,679 |
| `arm-B/smoke/result.json` | `7a45a4f257dfe6772044bf163a9b6728b6a572cc3d19a8ec305ff9876ea4f381` | 23,256 |
| `s4-ruling.md` | `14dbfd6c2f6b101888948c0505c903d78b35e9903f60ec42b3f1c7ed68eb8d6a` | 12,366 |
| `probe/t2779_probe.py` | `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99` | 40,315 |
| `probe/arms-t2779.json` | `4f6aaf5a172eb8eb737bd0ec6e2fcc52e92b5dce2691803f65d8f34e327ebb56` | 1,124 |
| `probe/v4-to-v5.diff` | `e6979b719766013495f5e485228dcfc64c1c723bb4ec76e46092f322aaa4a547` | 9,956 |
| `verbatim/instr-mocc-lock-coverage.patch` | `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48` | 4,080 |
| `verbatim/mocc-close-version-counter-gap.patch` | `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d` | 1,168 |
| `dispatch-B1.log` / `B2` / `B3` / `B4` / `smoke` | `14a6b8ed…` / `d297be26…` / `e1cb1b06…` / `2bf96c2d…` / `3b108bc4…` | 4,249 / 4,145 / 4,144 / 4,145 / 4,230 |

各走の記録: `arm-B/<block>/runs/<ordinal>-<arm>/{run.json, verifier.json, discriminator.json, run.stdout, run.stderr, verifier.stderr}` (360 走)。
G2 7 走はさらに `trace-manifest.json` と `trace/trace_<0..47>.log`。7 走の `run.json` / `verifier.json` / `trace-manifest.json` の sha256:

| 走 | `run.json` | `verifier.json` | `trace-manifest.json` |
|---|---|---|---|
| B1/082 | `93c5720b…` | `15df9bfd…` | `396b21f4…` |
| B2/030 | `426f61cd…` | `a5897657…` | `2711e346…` |
| B2/033 | `60dd6615…` | `6bff0611…` | `f784a70f…` |
| B2/069 | `ba96a940…` | `71cb8ce7…` | `7313e9be…` |
| B2/077 | `9b487685…` | `604cb14d…` | `38de1696…` |
| B3/006 | `22987d19…` | `bb8c86ed…` | `7f3680d4…` |
| B4/080 | `9211fc0e…` | `c4b936cc…` | `e6cf802b…` |

(全桁は本稿の記録 insight `output/insights/2026-09-20/mocc-g2-observation-results-doc/README.md` の照合表に置く。)

### 6.3 値の出所

| 本稿の値 | 出所 |
|---|---|
| block 別 k / m、N・m・failure・indeterminate・未開始、rounds、hostname、started / finished | `arm-B/<block>/result.json` (`runs[].verifier.status`、`summary`、`rounds`、`not_started`) |
| 合算 k / m、CP 区間、`decisive_m`、`discriminator_counts`、`identification` | insight `summary.json` |
| Fisher の表と p | insight README §5 の逐語 (本稿執筆時に超幾何和を独立再計算し一致) |
| G2 7 走の cycle・key・版・commit 数・位置 | 各走の `verifier.json` (`results[0].anomalies`)、`run.json` (`round`、`order`、`commit_count`) |
| 生 trace の file 数・byte・sha 一致 | 各走の `trace-manifest.json` と `trace/` の現物 (本稿執筆時に 336 file を再 hash)、`recovery-raw-hashes.log` |
| request・node・Created / Started / Ended・Elapse | `dispatch-<block>.log` の NQSV 終了要約 |
| identity (pin・patch sha・define・source sha・binary sha・runner sha・policy sha・toolchain) | `result.json.bindings` (4 block + smoke) |
| 事前登録 (標本・主比較・主表示・欠測規則)・主張範囲・検出力 0.83 / 0.72 | `s4-ruling.md` 項 3・6・7 (逐語) |
| 基準率の由来 (7/120・2/40)、部分抑制 0.30、2 比較 0.70 | 記録 insight README §4 (親の設計説明。事前登録本文には無い) |
| 検出力 4 値の丸め前の値、Fisher p・CP 区間の一致確認 | 本稿執筆時の独立再計算 (本 wave の job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/scratch/` の使い捨て script、出力は記録 insight §4) |
| 診断 patch の中身 | `verbatim/mocc-close-version-counter-gap.patch` |

### 6.4 裁定

- D2148 項 13 (MOCC は観測事実と限界の報告までとし修正 PR は見送る。G2 signal の再現を根因確定とせず、witness on の出所照合未達と hook / verifier
  仮定の分岐を明記。診断 patch の取り込み・pin 前進・certified 昇格は認可しない) — 上流向け報告 [T-2791] の限定と同じ。
- D2150 項 1 (候補 `e9e477ca` への pin 前進の承認、未実施)、D2159 (探索・pin 前進・正式な軸採用を認可しない)、D2114 項 3 / D1603 (pin 前進の手続き)、
  D2134 (変異探索の解禁は別裁定)、D1686 (X/P 計装)、D16 / D18 / D20 (CCBench 改変の扱い)、D12 (protocol の出力と研究の成否の分離)。
- phase doc の [T-2779] 項 (`docs/phase3.md`、済): 「各 120 走で通常 5、診断 0、BACK_OFF=1 は 2 signal。非 certifying で、昇格・pin・探索の扱いは不変」。

### 6.5 関係する既存記録 (本稿の出所ではない)

- 前段: `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` ([T-2774]、witness on / off の観測、本試行の問いと基準率の出所)。
- 同時期: `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/README.md` ([T-2780]、pilot の discriminator 配線)。
- 後段: `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` (§3 の静的設計を hook branch に実装した 4 arm の実走。本稿はその値を引かない)。
- 版: `docs/paper-story/2026-09-19.md` (§2 (c) と注記が本観測に触れるが、本稿の数値の出所にしていない)。同版の注記のとおり、本試行の全 arm は
  X/P 計装 patch を当てた producer である。
