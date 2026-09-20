# stock mocc の軽量 witness 4 arm × 60 走の結果節 — 軽量 witness on は 0/60・0/60、off は 1/60・1/60、片側 Fisher p=0.500、discriminator は未発火 (非 certifying の観測、2026-09-19)

**これは投稿本文ではない。** 論文の結果節・表・限定へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** `results/` に mocc についての稿はこれまで無く、本稿が最初である。
最新版 (`docs/paper-story/2026-09-19.md` §7 項 2) が書く stock mocc の非 certifying 観測 3 件 ([T-2774] / [T-2779] / [T-2780]) と、
同 README の追補 (worklog entry 1696) が加えた 4 件目の要約は変えない。**同版の「根因は未同定」「mocc は第 2 成功例とは書かない」は
本稿でも不変である。** 本稿は 1 wave の一次資料全体 (job dir の走ごとの JSON・集計・会計・事前登録・検査 log・hook commit の git object、
記録 insight の逐語) から作った単独稿であり、版・README 追補・worklog を数値の出所にしない ([T-2611] / [T-2674] の型)。

**限定を先に置く (§3 の要約)。**

1. **片側 Fisher p=0.500 と on 側の 0/60 は、同等性・効果なし・G2 不在のどれの証明でもない。** 設計仮定下の検出力は 0.105 (§1.3 の条件) で、
   この標本・条件では率差を検出できなかった、というのが本結果の言える範囲である。「軽量 witness が観測者効果を消した」「on では G2 が出ない」
   とは書かない。on の 0/60 は「率 0.017〜0.042 の事象を 60 走で引けなかった」とも両立する。
2. **非 certifying であり、TRACE=1 観測専用の合成 source で測っている。** 個別 verifier の `certified=true` (238 走) と arm 属性
   `observational_only=false` は本 wave・MOCC・軽量 witness の認証を意味しない。合成 source の TRACE=0 binary identity は未検査である (§1.6)。
3. **certified 昇格・pin 前進・変異探索の解禁は認可されていない** (ユーザー決定 2026-09-19、§1.1)。規律 2 (verifier / discriminator /
   X/P patch の受理集合は 1 文字も変えていない) と規律 7 ([T-1892] 5/42、[T-2774]、[T-2779] の値は各旧束縛で保持し、合算しない) を守る。
4. **検出力 0.105 は認可枠 60/arm の上限として明記する計算値であり、実測ではない。** ユーザー決定文の「80% 検出力の根拠 = 各 arm ≥56」は
   率 0.119 ([T-1892] 5/42) の条件付き計算で、観測率 0.0417 では成立しない (§1.3)。
5. **commit 数の on/off 比 (0.864 / 0.845) は曝露量の記録であって性能値ではない** (規律 1: trace-enabled build の値を性能に使わない)。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**1 wave (`dev-wave-mocc-witlight-arm-run`) の本走 4 block の 1 完走**である。本走 = 4 block (W1〜W4、4 node) × 15 round × 4 arm = 240 走
(arm ごと 60 走)。smoke 1 block (4 走、`--rounds 1`) は技術的受入のためだけに走らせ、分母に合算しない。Pegasus gen_S の計算ノードで
2026-09-19 22:27:21 (smoke の request 作成) 〜 23:02:04 JST (W4 の request 終了) に走った。再投入・補充・再試行・早期打切りは 0 回である。

### 0.2 書くもの

- 問い (i) (ii) と認可の範囲、結果を見る前に固定した事前登録・検出力とその適用条件・smoke の合格集合・欠測規則 (§1)。
- 測定条件と束縛 (pin、2 つの patch、hook commit W、source / runner / policy / toolchain の digest) と W の TRACE=0 preprocess identity (§1.5 / §1.6)。
- block 別・arm 別の k/m、Clopper–Pearson 両側 95%、主比較・副比較の片側 Fisher、G2 signal 2 走の内容、discriminator の到達点、曝露量 (commit 数)、smoke の検算 (§2)。
- この診断で識別できたこと・できなかったこと (§2.8)、限定 (§3)、欠落・未確認 (§4)、一次資料と転記元の SHA-256 (§5)。

### 0.3 書かないもの

- 性能 (trace-enabled build の commit 数は診断生値であって性能値ではない。規律 1)。
- G2 signal の根因、実 anomaly と torn read の別 (問い (ii) は識別対象 0 件で未到達)。
- [T-1892] / [T-2774] / [T-2779] との合算・プール・因果推定 (旧 heavyweight on arm を含まないため、軽量化の改善量は推定しない)。
- 次の実験の起動 (候補は記録 insight §6 に列挙済み。本稿は起動しない)。
- W の上流 (GitHub) への push (人間手番、D16)。「mocc は第 2 成功例」という記述。

---

## 1. 結果を見る前に固定したもの

### 1.1 認可と問い

ユーザー決定 (2026-09-19、記録 insight §0 の逐語): 「軽量 witness を hook branch に実装し、4 arm (witness 軽量 on / off × BACK_OFF 0 / 1) ×
各 60 走を計算ノードで取ることを認可する。非 certifying。certified 昇格・pin 前進・変異探索は認可しない」。

- 問い (i): `BACK_OFF=0` で軽量 witness on と off の G2 signal 検出率に差があるか。
- 問い (ii): 検出した各 G2 を payload lineage discriminator (`orchestrator/campaign/mocc_g2_discriminator.py`) で `supported` (実 anomaly と整合) /
  `contradicted` (torn read と整合) / blocker に分類できるか。
- 範囲外: gate・台帳の新設、CCBench 本体の恒久改変 (D16 の trace-hook 分類で hook branch に commit、上流 push は人間)、pin 前進、runner の改版、仮説 cell。
- 認可しないこと: mocc の certified 昇格判定、pin 前進 (D2114 項 3 / D1603)、変異探索の解禁 (D2134)。

### 1.2 事前登録 (job dir `s4-ruling.md` §3〜§4)

前 wave の段 4 裁定 file が結果前に固定した設計 (確定時刻は同 wave の handoff 記録で 22:16 JST。§4 項 1 に file の mtime との関係を書く)。

- **設計:** 4 block × 15 round × 4 arm、各 arm 計画数 60。round ごとに開始 arm を回転し、node k の arms JSON は arm 列を k−1 回転させる
  (4 node 合計で各 arm が各位置に 15 回)。**rounds は launcher 引数 (15) で固定し、結果を見て増減しない。** smoke と過去 wave は分母に含めない。
  cell = 3 秒・48 thread・10,000 records・rratio 50・rmw 0・max_ope 10・zipf 0.9。
- **主表示:** arm 別 k (G2 signal 走数) / m (有効 verdict 数、indeterminate を含み failure を含めない)、k/m (「G2 signal 検出率」)、Clopper–Pearson 両側 95%、
  `decisive_m`・failure・未収載数を併記。cycle 正の非 G2 現象が混在した場合は G2 件数で再計算する。indeterminate を「G2 なし」と書かない。
- **主比較** = `BACK_OFF=0` の `e9-witlight-wit` (on) 対 `e9-witlight-nowit` (off)、on 側が低い方向の片側 Fisher (参考値)。**副比較** = `BACK_OFF=1` の on / off。
  family 全体の効果をどちらか 1 つの p<.05 で宣言しない。block 別件数を併記。CP / Fisher は独立・同率 Bernoulli の参考値で、node 内相関・順序・時間変動を
  モデル化しない。固定時間の走あたり検出率であり、同じ commit 数への曝露比較ではない。
- **実用上の到達点** = on arm に G2 ≥1 件が出て discriminator の入力へ到達すること。呼出成功・正常完了 (`supported` / `contradicted` / blocker)・識別成功を
  別に数える。到達点は率差の有意性・根因・認証を意味しない。off arm の G2 は `not-run (witness-off)`。
- **欠測規則:** block ごとに (a) 保存済み / (b) 開始証拠あり未収載 / (c) 未開始確認済み / (d) 状態不明。主解析は (a)。補充しない。原本は書き換えない。
- **参考値の扱い:** [T-2779] の通常 arm 5/120 は旧 witness source・別 block・別日の参考値として併記し合算しない。旧 heavyweight on arm ([T-2774] instr-wit 0/40)
  を含まないため、軽量化の改善量を因果的に推定しない。

### 1.3 検出力と、その計算が成り立つ条件

事前登録が固定した検出力 (親が計算し、段 2 plan と段 3 レンズ B が独立に再計算して丸め精度で一致。本稿の執筆時にも独立再計算して一致した)。

| 仮定した off 率 | その出所 | 仮定した on 率 | 検出力 (K=60 / arm) |
|---|---|---:|---:|
| 0.0417 | [T-2779] 通常 arm 5/120 (旧 witness source・別日・別 block の観測率) | 0 (完全抑制) | **0.105** |
| 0.058 | [T-2774] witness off 3 arm 合算 7/120 (丸めた率。7/120 のままなら 0.272) | 0 (完全抑制) | 0.268 |
| 0.119 | [T-1892] 5/42 | 0 (完全抑制) | 0.856 |
| 0.0417 | [T-2779] 通常 arm 5/120 (1 行目と同じ出所) | 0.014 (部分抑制) | 0.050 |

**適用条件:** 片側 Fisher の正確検定、α=.05、両 arm とも独立・同率の Bernoulli 試行、等標本 K=60、対立仮説は「on 率が off 率より低い」。on=0 のとき
p<.05 になるのは off ≥5 のときだけである (off=4 で p=0.059、off=5 で 0.029)。node 内相関・回転順・時間変動はモデル化していない。

**「80% 検出力」の条件:** ユーザー決定文が根拠とした「各 arm ≥56 で検出力 80%」は率 0.119 ([T-1892] 5/42) の完全抑制に対する条件付き計算である
(K=56 で 0.812、K=60 で 0.856)。観測率 0.0417 では K=60 で 0.105 に留まり、80% は成立しない。**認可枠 60 を超えず、検出力はこの上限として明記する。
計算値であり実測ではない。**

### 1.4 smoke の技術的合格集合 (結果前に固定)

前提 = 4 走とも benchmark rc=0、build 4 arm 成功、raw 完全 (wrapper 複製の集合・bytes・sha が保存成功数と一致)、verifier JSON 整合、
binding 一致 (runner sha、arms JSON sha、X/P patch sha、witlight.patch sha、source sha 4 arm 同一、bo1 だけ `BACK_OFF=1`、wrapper sha を別束縛)。
この前提の下で verifier **rc=0** と **整合した G2 の rc=1** (現象名 G2・cycle 正・trace-manifest あり。on arm なら discriminator が正常完了し
`supported` / `contradicted` / blocker のいずれかを出す) を合格とする。on の rc=1 で blocker / 入力拒否なら原因を記録して技術的受入を保留し再試行しない。
rc=3 (indeterminate)・build / 計器故障・witness file 欠落は不合格。**結果を見て smoke を繰り返さない。** on arm の witness 検査: H = 各 file 先頭に正確に 1 行、
S の identity Counter = 標準 trace の W Counter、各 identity 1 件、C の write 数合計と一致、全 S で第 5 値 (保存 producer) == 第 2 値 (writer txid)、L / R 対応、
空集合どうしの一致は合格にしない。

### 1.5 測定条件と束縛

| 項目 | 値 |
|---|---|
| outer repo | main `a99425b66` (wave worktree + detached worktree 3 本、同 base)。CCBench gitlink `511c9538` は動かしていない |
| hook commit **W** | `5b02546fcd7b0302c8c92b6e05957541c9660902`、親 `e9e477ca1b55348ab4530de0b1cf663ce4555290`、tree `a41e6c54a43fb78044f3b8bd42ec7e4338476218`、branch `izanagi-t1943-mocc-g2-witlight`、touch = `cc/mocc/transaction.cc` +26/−6、include 行不変、`#line` 無し、author 日時 2026-09-19 22:23:41 JST。初版 `e0905b3d` (trailer 2 行) を 22:44 JST に message だけ amend (tree 不変)。trailer 3 行 = `role=author` (codex gpt-6-astra medium) / `role=reviewer` (同) / `role=manager` (claude-opus-5-1m xhigh)。GitHub 未 push (人間手番、D16)。自己完結 bundle `W.bundle` (3,215,451 byte、sha256 `874f6dc064bad128c3d310e49d55ea1f63d187cd0a6b9d98e292a84d3c1a4351`) |
| 測定用合成 source | pin `e9e477ca` + patches [X/P `patches/instr-mocc-lock-coverage.patch` (repo、D1686、sha256 `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48`)、`witlight.patch` (job dir、X/P 適用後 source に対する diff、`#line 115 / 1136 / 1201 / 1208` 付き、sha256 `0648e2c6de46319da02056cb516d706ff9f09c3c0ffb2cadb6c94ee069473363`)]。(e9e477ca + X/P + witlight.patch) と (e9e477ca + W + X/P) は `^#line` 行を除いた bytes が一致 (`check-patches.log` の V3 `MATCH`。39,378 byte という大きさは前 wave の段 6 レビュー A `codex/s6-review-A.md` の独立再構成の記録)。pin を W でなく `e9e477ca` に固定したのは、runner v5 の discriminator が `pin != e9e477ca` で `not-run (pin-outside-t1943)` になるためである |
| source file digest | `source_file_sha256` = `d22b8e439ef486019e2abc8b6bb1fe02edfb450655abc7999a13715e6b547264`、4 arm × 5 block (smoke 含む) で同一 (本稿で再照合)。on / off は実行時 env (`IZANAGI_MOCC_G2_WITNESS=1` + `IZANAGI_MOCC_G2_WITNESS_DIR`) だけの差。同 source・同 define でも runner は arm ごとに別 build し、binary sha は build ごとに異なる (path 埋込み等、命令列の一致は未確認) |
| runner | `probe/t2779_probe.py` v5、sha256 `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99` (40,315 byte、[T-2779] と同一 bytes、無変更)。本走は runner 直。smoke だけ観測 wrapper `probe/smoke_capture.py` (sha256 `65017778972c7dcab6b5bdd0da801da11fb7e923e1075d9755101ff90446bc55`) 経由 |
| policy / toolchain | `tools/pegasus/mocc_trace_v1_policy.json` sha256 `66ea7135c6d84cfd09013f33da23d8ca8015dcb547e34db7c802644f4986acd6`。gcc-11 / g++-11 (`/usr/bin/x86_64-linux-gnu-g++-11`)、version body sha256 `b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0`。5 block で同一 |
| configure | `-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0 -DCCBENCH_CCACHE=OFF` ([T-1943] pilot と同一基底)。bo1 arm は `-DCCBENCH_BACK_OFF=1` だけ置換 |
| 実行 argv | `-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3` |
| verifier | `python3.10 -m orchestrator.verifier <trace_dir> --json --protocol mocc --ccbench-root <arm の source> --expected-commits N` (outer `a99425b66`、timeout 300 s、変更なし)。discriminator は witness on かつ cycle 正の走だけ |
| arms JSON | node1 `ba740887…` / node2 `f5e80223…` / node3 `8db96f21…` / node4 `ab0e84b2…` (k−1 回転、object は同一 = 正規化 sha256 `a4af0e8a…`) |

| arm | pin | X/P | witlight | witness env | BACK_OFF | observational_only |
|---|---|---|---|---|---|---|
| e9-witlight-wit | e9e477ca | 有 | 有 | on | 0 | false |
| e9-witlight-nowit | e9e477ca | 有 | 有 | off | 0 | false |
| e9-witlight-wit-bo1 | e9e477ca | 有 | 有 | on | 1 | false |
| e9-witlight-nowit-bo1 | e9e477ca | 有 | 有 | off | 1 | false |

### 1.6 W の TRACE=0 preprocess identity (規律 1) と、その射程

`tools/check_trace0_preprocess_identity.py` (schema `izanagi-trace0-preprocess-identity/v2`、login で実走、`--cxx /usr/bin/x86_64-linux-gnu-g++-11`。checker は policy を受け取らない):

- `--old 511c9538 --new W` → top-level `result=pass`、`files[0].result=match` (`cc/mocc/transaction.cc`、16 context、正規化 preprocess 同一、include 活性同一)。
- `--old e9e477ca --new W` → `pass` / `match` (16 context、`old_is_ancestor_of_new = true`)。
- 負例: W に `#include <vector>` を `#if TRACE` 内に足した一時 commit は rc=1 (`include 行文字列（順序込み）が不一致`、preprocess 比較の前に include 契約で拒否 = 単一理由)。

**射程:** これは W 単体 (hook branch の commit) の identity であり、**測定に使った合成 source (e9e477ca + X/P + witlight.patch) の TRACE=0 binary identity は
本 wave で検査していない。** 合成 source は TRACE=1 専用の観測 build として扱い、性能値には使わない。W が `#if TRACE` の外を変えないことは
TRACE 外 31,698 byte の一致 (前 wave の段 6 レビュー A `codex/s6-review-A.md` の独立確認) と checker の `match` で示されている。

---

## 2. 結果

### 2.1 block 別 (NQSV の request 要約と runner の `started_at` / `finished_at`)

| block / request | hostname | Created / Started / Ended (JST、NQSV) | runner started / finished (UTC) | Elapse 秒 | arms JSON | on k/m | off k/m | on-bo1 k/m | off-bo1 k/m |
|---|---|---|---|---:|---|---:|---:|---:|---:|
| W1 / 10827.nqsv | bnode122 | 22:35:18 / 22:35:26 / 22:59:52 | 13:35:26.74 / 13:59:52.64 | 1471 | node1 (`ba740887…`) | 0/15 | **1/15** | 0/15 | 0/15 |
| W2 / 10828.nqsv | bnode119 | 22:35:37 / 22:35:44 / 23:00:08 | 13:35:45.37 / 14:00:08.61 | 1468 | node2 (`f5e80223…`) | 0/15 | 0/15 | 0/15 | 0/15 |
| W3 / 10835.nqsv | bnode121 | 22:35:56 / 22:36:13 / 23:00:29 | 13:36:13.88 / 14:00:29.84 | 1461 | node3 (`8db96f21…`) | 0/15 | 0/15 | 0/15 | **1/15** |
| W4 / 10837.nqsv | bnode109 | 22:36:16 / 22:37:43 / 23:02:04 | 13:37:44.61 / 14:02:04.81 | 1466 | node4 (`ab0e84b2…`) | 0/15 | 0/15 | 0/15 | 0/15 |

- 4 block とも dispatcher `.done=0`、child rc=0、runner `status=completed`、`planned_runs=60`、`rounds=15`、`runs` 60 件、`not_started=0`。
  欠測 (a) 保存済み = 60 / block、(b) (c) (d) = 0。各 arm の N = m = `decisive_m` = 60、failure = indeterminate = 0。
- benchmark rc=0 ×240。verifier rc=0 ×238、rc=1 ×2 (§2.4 の 2 走)。個別 verifier の `certified` は true 238 / false 2 (rc=1 の 2 走)。
- 回転: 各 arm が各位置 (1〜4) に 15 回ずつ (block 内は 4/4/4/3 の配分、4 block 合計で 15/15/15/15)。予定どおり、欠測なし。
- 4 block で runner sha、policy sha、toolchain、`repo_head`、workload argv、arm 別の pin / patch sha / witness / `observational_only` / source file sha が一致
  (本稿で 5 block の `bindings` を突合した。異なるのは arms JSON の回転、投入元 worktree、scratch path、binary sha だけ)。

### 2.2 arm 別

| arm | k/m | G2 signal 検出率 | Clopper–Pearson 両側 95% | 位置 1/2/3/4 | commit 数 平均 (走あたり) |
|---|---:|---:|---:|---|---:|
| e9-witlight-wit (on, BACK_OFF=0) | 0/60 | 0% | [0%, 5.963%] | 15/15/15/15 | 613,741.5 |
| e9-witlight-nowit (off, BACK_OFF=0) | 1/60 | 1.667% | [0.042%, 8.940%] | 15/15/15/15 | 710,659.4 |
| e9-witlight-wit-bo1 (on, BACK_OFF=1) | 0/60 | 0% | [0%, 5.963%] | 15/15/15/15 | 788,885.6 |
| e9-witlight-nowit-bo1 (off, BACK_OFF=1) | 1/60 | 1.667% | [0.042%, 8.940%] | 15/15/15/15 | 933,621.8 |

区間と母数は runner v5 の `summarize` (`summary.json`) と親の会計 (`parent-accounting.json`) が独立に計算して一致し、本稿の執筆時にも
独立再計算して一致した (CP 上限 0/60 = 0.059629、1/60 = [0.000422, 0.089399])。

### 2.3 主比較・副比較 (片側 Fisher、行 = on / off、列 = G2 / 非 G2、on 側が低い方向)

| 比較 | 2×2 表 | p (未調整) |
|---|---|---:|
| 主比較 BACK_OFF=0 (`e9-witlight-wit` 対 `e9-witlight-nowit`) | `[[0, 60], [1, 59]]` | **0.500** |
| 副比較 BACK_OFF=1 (`e9-witlight-wit-bo1` 対 `e9-witlight-nowit-bo1`) | `[[0, 60], [1, 59]]` | 0.500 |

書き方: 「BACK_OFF=0 でも BACK_OFF=1 でも、軽量 witness on の G2 signal 検出は 0/60、off は 1/60 で、on 側が低い方向の片側 Fisher は
どちらも未調整 p=0.500 だった。この標本・条件では on/off の率差を検出しなかった (設計仮定下の検出力は 0.105)。」
**「差がない」「同等」「on では出ない」とは書かない。** family 全体の効果をどちらか 1 つの p で宣言しない。

### 2.4 G2 signal 2 走 (いずれも witness off)

| block / ordinal (round) | arm | cycle (txid) | 現象 | 辺 (reason) | commit 数 | 生 trace |
|---|---|---|---|---|---:|---|
| W1 / 18 (round 5) | `e9-witlight-nowit` | 452883 ↔ 452884 | G2、長さ 2、両辺 rw | 452883→452884: key `0x2`、u_ver (38, 62) → v_ver (38, 67)。452884→452883: key `0x0`、(38, 65) → (38, 66) | 709,237 | 48 file、261,786,377 byte |
| W3 / 5 (round 2) | `e9-witlight-nowit-bo1` | 243580 ↔ 243582 | G2、長さ 2、両辺 rw | 243580→243582: key `0x4c`、(20, 2499) → (20, 2546) と key `0x1`、(20, 2544) → (20, 2546) の 2 reason。243582→243580: key `0x0`、(20, 2544) → (20, 2545) | 923,923 | 48 file、341,192,067 byte |

- 両走とも verifier `verdict=non-serializable`、`certified=false`、`total_cycles=1`、`anomaly_count=1`、現象名 `G2` (保存済み verifier JSON の
  `results[0].anomalies[]` で照合。親の会計 JSON `parent-accounting.json` の `phenomenon[]` 要素の `phenomena` / `anomalies` field は runner の縮約 record から取るため
  null で、現象名の証拠ではない)。非 G2 の cycle は 0。
- 形は [T-1892] / [T-2774] / [T-2779] の G2 (長さ 2・両辺 rw) と整合するが、**witness off なので payload lineage による識別はできない。**
  同一性・根因は本稿で主張しない。
- 生 trace は 2 走 × 48 file = 96 file、計 602,978,444 byte を job dir に保全し、trace-manifest と集合・サイズ・sha256 が一致 (`verify-manifests.log`、
  `source_oid e9e477ca match`、`ALL MATCH`)。

### 2.5 discriminator と実用上の到達点

- on arm に G2 signal が無いため discriminator は **0 件発火**。off arm の 2 件は `not-run (witness-off)`。`comparisons` は 0 件。
- 到達点 (呼出成功 / 正常完了 / 識別成功) は **いずれも 0**。問い (ii) は識別対象 0 件で未到達である。
- `summary.json` の `discriminator_counts` は 4 arm とも `not-run: 60`、`identification.g2_runs` は on 0 / off 1 ずつ、`identified_g2_runs` は 0。

### 2.6 曝露量 (走あたり commit 数の平均、同一 block 内対照。性能値ではない)

| 対 | on | off | on / off |
|---|---:|---:|---:|
| BACK_OFF=0 | 613,741.5 | 710,659.4 | 0.8636 (約 14% 少ない) |
| BACK_OFF=1 | 788,885.6 | 933,621.8 | 0.8450 (約 15% 少ない) |

軽量 witness でも L 行の出力・decode・push・unlock 後の S 出力は残るので、on の曝露量 (3 秒あたりの commit 数) は off より少ない。
記録 insight §6 の「on の曝露量は off の約 86%」は BACK_OFF=0 側の値である。**これは曝露量の記録であって性能主張ではない**
(TRACE=1 build、規律 1)。[T-2774] の heavyweight on (instr-wit) 541,601 対 off 711,199 (同 wave の記録 insight §1 の走あたり平均、旧束縛の転記。
本稿では再集計していない) は別日・別 node の値で、同時刻対照ではない。

### 2.7 smoke (request `10799.nqsv`、bnode084、Created 22:27:21 / Started 22:30:07 / Ended 22:32:31 JST、Elapse 148 秒、runner 13:30:08.95〜13:32:31.19 UTC)

- 4 走 (node1 JSON、rounds 1) とも benchmark rc=0、verifier rc=0、`status=no-g2`、`verdict=serializable`、cycle 0。build 4 arm、binding 一致 (§2.1 の突合に smoke を含む)。
  wrapper 複製 4 run / 288 file (manifest)。**技術的合格集合 (§1.4) の全項を満たし、smoke は 1 回だけ (再試行なし)。分母に合算していない。**
- on arm 2 走の witness 検算 (`check-smoke-witness-001.log` / `-003.log`): trace 48 file・witness 48 file、H は各 file 先頭に 1 行 (bad files 0)、
  S identity Counter = 標準 trace の W Counter (3,014,285 / 3,933,687 = C の write 数合計)、S identity の重複 0、L = R = C の read 数合計 (2,968,147 / 3,873,346)、
  **全 S で第 5 値 (保存 producer) == writer txid (不一致 0 行)**、W の op は全 `U`、L の producer は `G` (未書込 genesis) 9,895 / 9,946 + `T`。
  commit 数 613,418 / 800,450 (off 2 走は 725,862 / 957,171)。
- これは W の witness 文法・件数・順序・保存値の pass-through が smoke の正例で保たれたことを示す (静的 data flow の確認と併せて)。
  **runtime の不一致注入 (第 5 値が writer txid と異なる入力) は実施していない** (§4 項 4)。

### 2.8 この診断で識別できたこと・できなかったこと

| 識別できた (一次資料が直接示す) | 識別できなかった (本結果では言えない) |
|---|---|
| 4 arm × 60 走が計画どおり完全収載された (欠測 0、failure 0、indeterminate 0、回転 15/15/15/15) | 軽量 witness on と off の G2 signal 検出率の差 (p=0.500、検出力 0.105) |
| 軽量 witness on の G2 signal は BACK_OFF=0 / 1 とも 0/60 (CP 上限 5.963%) | 軽量 witness の観測者効果の有無・大きさ、「on では出ない」か「60 走で引けなかった」か |
| witness off では同一 source の G2 signal が、各 block に on/off 対照を置いた 4 block 合計で arm 別 1/60 ずつ (W1 の BACK_OFF=0 off、W3 の BACK_OFF=1 off、block 内の arm 分母は 15) 再現し、形 (長さ 2・両辺 rw) は [T-1892] 型と整合する | その 2 件の実 anomaly / torn read の別 (witness off なので payload lineage が無い)、根因 |
| on arm に G2 が無く、discriminator の入力に到達しなかった (到達点 0/0/0) | discriminator の実例での識別性能 (問い (ii)) |
| W は TRACE=0 preprocess identity を 2 本の正例で `pass` / `match`、負例で rc=1 (include 契約) | 合成 source (X/P + witlight.patch) の TRACE=0 binary identity、旧 off binary との命令列・TLS 領域・cache 挙動の同一性 |
| smoke の正例で witness 文法 (H 1 行、S = W Counter、第 5 値 == writer txid) が保たれた | 不一致値の runtime 注入に対する消費側の検出 (未実施) |
| on の曝露量は off の 0.864 (BACK_OFF=0) / 0.845 (BACK_OFF=1) | 性能 (TRACE=1 build の値は性能値でない)、[T-2774] heavyweight との因果的な改善量 |

---

## 3. 限定 — この結果が言わないこと

1. **非有意は同等性の証明ではなく、0 件は不在証明ではない。** p=0.500 は「60 走ずつで 1 件対 0 件」という表の帰結であり、on=0 のとき
   p<.05 になるのは off ≥5 だけである。設計仮定下の検出力 0.105 は低く、率差を検出できなかったことと率差が無いことは別である。
2. **検出力は認可枠 60/arm の上限として明記する計算値である。** 前提 (独立・同率 Bernoulli、等標本、完全抑制、off 率 = [T-2779] 通常 arm の観測率) の
   どれかが崩れれば数値は変わる。「80%」は率 0.119 の条件付き計算で、観測率では成立しない。認可枠は超えていない。
3. **非 certifying、TRACE=1 観測専用。** 個別 verifier の `certified=true` (238 走) と arm 属性 `observational_only=false` は本 wave・MOCC・軽量 witness の
   認証を意味しない。合成 source の TRACE=0 binary identity は未検査 (§1.6)。certified 昇格・pin 前進 (D2114 項 3 / D1603)・変異探索の解禁 (D2134) は
   認可されておらず、本稿もそれを求めない。規律 2 (anomaly 検出 variant の即 reject 契約、verifier / discriminator / X/P の受理集合) は不変。
4. **規律 7: 旧束縛の値を保持し、合算しない。** [T-1892] 5/42、[T-1943] `no-g2`、[T-2774] Q1 / Q2 (2/40、3/40、2/40、0/40、0/40)、[T-2779] 5/120・0/120・2/120 は
   各々の source・block・日付に束縛された記録のまま残る。本稿は off を arm 別に 1/60 ずつ書く (両 BACK_OFF を合算した 2/120 = 1.67% は記録 insight §6 の
   表現で、本稿では合算しない)。これを [T-2779] の通常 arm 5/120 と比べるのは別 source・別日の履歴的照合であり、率の標本誤差 (CP 区間は重なる) と
   node / 日の効果を分離しない。
5. **軽量化の改善量は推定しない。** 4 arm に旧 heavyweight on arm を含まないため、[T-2774] instr-wit 0/40 との比較は因果推定にならない。
6. **問い (ii) は未到達である。** discriminator の識別性能・実 anomaly / torn read の別・根因は本結果から言えない。off の 2 件を「G2 が再現した」と
   書くのは verifier の G2 signal の再現であって、根因の同定ではない。
7. **性能値を含まない (規律 1)。** commit 数は trace-enabled build の診断生値 = 曝露量であり、A-2 / A-6 / [T-1998] の性能値とも [T-2774] の commit 数とも比べない。
8. **統計は参考値である。** CP / Fisher は独立・同率 Bernoulli の下の値で、node 内相関・回転順・時間変動 (4 node で同時刻に走った 4 block、block 内で
   4 arm が順次) をモデル化していない。固定時間 3 秒の走あたり検出率であり、同じ commit 数への曝露比較ではない (on の曝露量は少ない)。
9. **W の「窓の短縮量」は未実測。** publish 後・unlock 前に残るのは decode + abort + 確保済み vector への push だけ、という処理構成の説明までであり、
   時間の短縮は測っていない。初回・capacity 増大時の `reserve` は write lock 保持中で残る観測者効果である。旧 off binary との同一性 (命令列・TLS・cache) も未実測。
10. **1 wave・1 日・4 node の測定である。** 別日・別 node・別 boot での反復は行っていない。node 専有は runner の `_assert_single_tenant()` の射程までで、実証していない。
11. **CCBench 上流に対しては報告まで。** W は D16 の trace-hook 分類で hook branch に置き、GitHub push・上流報告の送信は人間手番 (D2148 項 13)。gitlink は `511c9538` のまま。

---

## 4. 欠落 — 一次資料の対応が file だけからは確かめられない箇所

1. **事前登録 file の最終書込み時刻が本走の開始後にある。** `s4-ruling.md` の mtime は 2026-09-19 22:48:34 JST で、本走 4 block の開始 (22:35〜22:37) 後・
   終了 (22:59〜23:02) 前にあたる。file の §2 項 1 が amend 後の W OID (`5b02546f`、amend 22:44 JST) を含むことから、この書込みは §2 (設計の確定) への
   OID 反映と読めるが、§3〜§4 (事前登録・smoke 合格集合) がその時点で不変だったことは file 自体からは検証できない。「結果を見る前に確定 (22:16 JST)」は
   同 wave の handoff 記録と、段 3 レンズ B (22:12 JST の出力) が同じ検出力表・回転を独立に再計算し smoke 合格集合の結果前固定を must-fix として
   求めていたことによる。結果を見た後に §3〜§4 の数値が動いた証拠は無く、本稿はそのように扱うが、mtime による裏付けは無い。
2. **投入直前の `ps` 実測 (4 投入元で同一投入元の dispatch が 0 件) の保存証拠が無い** (22:27:13 と 22:35:10 JST に本 wave の dispatch 0 件、W4 投入後に 4 件、
   という実測は親の session 記録にあり保存 log には無い)。当時それ以外の同一投入元 dispatch が無かったことは遡及検証できず、未確認の事前条件として扱う
   (前 wave の段 6 レビュー B M1)。`check-base-dirs-2.log` (22:27 JST) と各 result の `bindings.base_dir` / `base_git_dir` の事後照合は保存されている —
   投入元は 4 つで、本走 W1〜W4 は相互に異なり、smoke と W1 は事前登録どおり (smoke の終端確認を挟んで) 同じ投入元 (wave worktree) を使った
   (記録 insight §7 の「5 request の投入元が相互に異なる」は誤記で、本稿の記述が原本の `bindings` に従う)。
3. **合成 source の TRACE=0 binary identity は未検査** (§1.6)。W 単体の preprocess identity と、W と witlight.patch の同内容性 (`#line` 除去後 39,378 byte 一致)
   から間接に言えるだけである。
4. **保存値の pass-through は静的確認 + smoke の正例まで。** 第 5 値が writer txid と異なる入力を runtime で注入し、消費側 `witness-post-store-token-mismatch` が
   発火することは本 wave では確認していない。
5. **検査 script の最終 rc は各検査の合否を集約していない** (前 wave の段 6 レビュー A S1)。V1〜V4 の合否は個別 log / JSON (`check-patches.log`、`check-identity.log`、
   `identity-*.json`、`identity-V2-negative.stderr`) で読む。
6. **binary sha は build ごとに異なり、命令列の一致は未確認。** 「同一 binary で 60 走した」とは書けない。source file sha と toolchain は 4 arm × 5 block の 20 組で一致し、configure の define は
   同じ arm の 5 block 間で一致する (arm 間には事前登録どおり `BACK_OFF` 0 / 1 の差だけがある)。
7. **本稿は job dir の原本 (repo 外) に束縛される。** repo 内の逐語 (`verbatim/`) は 17 file について行末空白を除去した可視文字不変の写しで、原本の sha256・byte 数・
   復元法は `verbatim/NORMALIZATION.md` にある。§5.1 の sha256 は job dir 原本を本稿の執筆時に再計算した値である。

---

## 5. 一次資料

### 5.1 job dir 原本 (repo 外、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/`) と SHA-256 — 本稿が 2026-09-20 に再計算した値

| file | SHA-256 | 内容 |
|---|---|---|
| `arm-W/summary.json` | `b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698` | runner v5 `summarize` の arm 別 N / m / k / `decisive_m` / CP / discriminator_counts / identification (schema `t2774-summary/v1`、入力 = W1〜W4 の result.json の sha256 を内包) |
| `arm-W/parent-accounting.json` | `20952bb6498d3a2935cb1797d53486b014929f6647c15642c37eb1c9405d0abe` | 親の独立会計: block 別 per_arm (n / m / k / rc / verifier_rc / positions)、arm 別 CP / positions / `commit_count_mean`、Fisher 2 表、phenomenon 2 件 (縮約 record)、discriminator 2 件 |
| `arm-W/W1/result.json` | `ca8ab3ff579e3fb55b97447ebb7b647d34806a6fd452ad410051aca9e5bd4b50` | W1 の 60 走 (bnode122) の走ごとの record + bindings |
| `arm-W/W2/result.json` | `473063aa741cc4c349931d987c902facbc5dcf6499b3692ea2cad3a27ac1e584` | W2 (bnode119) |
| `arm-W/W3/result.json` | `f68876600f1cd5b7300b030fb3cfa75509cc7a687858d6f12985051ce46e3642` | W3 (bnode121) |
| `arm-W/W4/result.json` | `197a2798de5ef53a7f6a32460f7ecfa5adbba8e853778b315d3b6e1839c36a6c` | W4 (bnode109) |
| `arm-W/smoke/result.json` | `a05f01950ebc0957405f14500d8ce0cb09a14fc1d480d6db774f526ea5daad19` | smoke 4 走 (bnode084) |
| `s4-ruling.md` | `d117465073f172f32e372e0a8163fce1bd75bf16ba5f2cecad21a14f6eb36b7c` | 前 wave の段 4 裁定 = 事前登録 §3、欠測規則・smoke 合格集合 §4、検査登録 §5 (mtime 22:48:34 JST、§4 項 1) |
| `s1-brief.md` | `d1477c36eca02b2291bc62cca3d27cd4036a950503902bab462627f3d6e4a044` | 前 wave の段 1 brief (mtime 21:51:27 JST) |
| `codex/s6-review-A.md` | `26eebea2b88444bc38ea67d3cd7dba88aa10fdd7c266c1594b90f5d5cf39a68f` | 前 wave の段 6 レビュー A の逐語 (W の同内容性 39,378 byte・TRACE 外 31,698 byte の独立再構成、mtime 22:43:17 JST) |
| `check-phenomenon.log` | `22b25008f551ca57d5cece72ab03091e554c2d264bbf1747583509866840ce74` | G2 2 走の現象名・長さ・辺種別の照合 |
| `verify-manifests.log` | `074dcce97ede28799cb004c7a636bdce187f81986ade73fc6b2f1ef289f247d9` | 生 trace 96 file / 602,978,444 byte の manifest 照合 (`ALL MATCH`) |
| `check-smoke-witness-001.log` / `-003.log` | `94e017747775df8cd22f4a92c066352152ecc5b422d93bb18823db29dcf7a3cb` / `97ee3dd3ebaa84ac6138314ff1626fe6620b82b8360a062f37b0d2e67128e096` | smoke on arm 2 走の witness 検算 |
| `identity-511c-to-W.json` / `identity-e9-to-W.json` | `3401913c4bcb8d2d36c626ac37dbd92eb1d1a8a1995b42451e18e014ec28f65a` / `911750ceeff01dcd50b862895907c6736352e9294213972454415514c17b7484` | W の TRACE=0 preprocess identity (`pass` / `match`)。負例は `identity-V2-negative.stderr` |
| `probe/W.patch` | `4ef9c387068abf9dcdd123ba87691b4d613cdb36fff9c541448c147367095aff` | W の diff 逐語 |
| `probe/witlight.patch` | `0648e2c6de46319da02056cb516d706ff9f09c3c0ffb2cadb6c94ee069473363` | 測定 patch (X/P 適用後 source に対する diff、`#line` 付き) |
| `probe/t2779_probe.py` / `probe/smoke_capture.py` | `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99` / `65017778972c7dcab6b5bdd0da801da11fb7e923e1075d9755101ff90446bc55` | runner v5 / smoke 観測 wrapper |
| `W.bundle` | `874f6dc064bad128c3d310e49d55ea1f63d187cd0a6b9d98e292a84d3c1a4351` | W の自己完結 bundle (完全履歴) |
| `dispatch-{smoke,W1,W2,W3,W4}.log` | `2edeb385…` / `a4430e28…` / `021a2876…` / `3f4d9fb3…` / `7be51410…` | NQSV の request ID・Created / Started / Ended・Elapse・child rc |
| `arm-W/W{1..4}/runs/<ordinal>-<arm>/` | (走ごと) | 各走の run / verifier JSON。G2 2 走は trace-manifest と生 trace (各 48 file) を含む |

### 5.2 repo 内 (tracked) の一次資料

- 記録 insight `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` (sha256 `a23f68e7310a5a1170ba4eb3ad8fca9c41431b0ce1960b7fcc03175fffa038bc`、commit `8458ae3f1`、2026-09-19 23:25:40 JST)
  と同 `verbatim/` (W.patch、witlight.patch、arms JSON ×4、smoke_capture.py、W-commit-message、s1〜s6 の逐語、summary / parent-accounting、identity JSON ×2 + 負例 stderr、
  check-*.log、W1〜W4 / smoke の result.json、`W1-018-e9-witlight-nowit/` と `W3-005-e9-witlight-nowit-bo1/` の run / verifier / trace-manifest / discriminator JSON、
  `W.bundle.sha256.txt`、`operational-facts.md`、`NORMALIZATION.md`)。§2.4 の cycle・key・version は同 verbatim の `verifier.json` (`results[0].anomalies[]`) から転記した。
- X/P patch `patches/instr-mocc-lock-coverage.patch` (D1686、sha256 `e9e65b78…`)。policy `tools/pegasus/mocc_trace_v1_policy.json` (sha256 `66ea7135…`)。
- hook commit W `5b02546fcd7b0302c8c92b6e05957541c9660902`: 本稿の執筆時に、local main から新規に作った worktree の submodule git dir (network fetch なし、
  local の submodule git dir から初期化) で `git cat-file -t` = commit、親 / tree / author 日時 / touch set / trailer 3 行を `git show` で再確認した。
  branch `izanagi-t1943-mocc-g2-witlight` の主 checkout の submodule git dir への fetch は前 wave の記録 (worklog entry 1696) による。GitHub 未 push。
- 前提となる観測の一次資料 (本稿の結果数値の出所ではない。§2.6 に参考値として置いた [T-2774] heavyweight の commit 数 541,601 / 711,199 だけは
  同 README §1 からの転記): `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md`、
  `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md` (§3 = W の静的設計)、`output/insights/2026-09-18/t2780-mocc-pilot-discriminator/README.md`。

### 5.3 裁定・決定

- ユーザー決定 2026-09-19 (§1.1 の逐語、記録 insight §0)。
- D16 (CCBench 改変の分類、trace-hook は hook branch、上流 push は人間)、D1686 (X/P patch)、D2114 項 3 / D1603 (pin 前進の認可境界)、D2134 (変異探索)、
  D2148 項 13 (上流向けは観測事実と限界の報告まで、送信は人間)、D2150 項 1 (候補 `e9e477ca` の pin 承認。GitHub 公開・取得確認の後に更新、本 wave は gitlink を動かしていない)。
- 前 wave の段 4 裁定 (`s4-ruling.md`): 段 3 must-fix 6 件全件 real・採用 (合成 source の TRACE=0 identity は未担保 → TRACE=1 観測専用と明記、brief の
  「非 certifying ⇒ 成果物影響なし」撤回、変異免除を outer repo の差分ゼロ範囲に限定、smoke 合格集合を結果前に固定、S 第 5 値の被覆、4 投入元の開始条件固定)。

### 5.4 値の出所 (転記した数値ごと)

| 本稿の値 | 出所 (file / field) |
|---|---|
| arm 別 N / m / k / failure / indeterminate / `decisive_m` / k_over_m / cp95 / discriminator_counts / identification | `arm-W/summary.json` `arms.<arm>` |
| block 別 hostname / status / planned / runs / not_started / rounds / started_at / finished_at / per_arm (n, m, k, rc, verifier_rc, positions) / arms_json_sha256 / runner_sha256 | `arm-W/parent-accounting.json` `blocks[]` |
| arm 別 positions (15/15/15/15) / `commit_count_mean` | 同 `arms.<arm>` (本稿で W1〜W4 の result.json から再計算して一致) |
| Fisher 2×2 表と p (0.5) | 同 `fisher.bo0` / `fisher.bo1` (本稿で超幾何分布から再計算して一致) |
| G2 2 走の block / ordinal / arm / round / rc / verifier_rc / verdict / total_cycles / commit_count、discriminator の status / reason | 同 `phenomenon[]` / `discriminator[]`、各走の `runs/<ordinal>-<arm>/run.json` |
| 現象名 G2・長さ 2・edge_types rw/rw・n_reasons [1,1] / [2,1] | `check-phenomenon.log`、各走の `verifier.json` `results[0].anomalies[]` |
| cycle の txid・key・u_ver / v_ver | 各走の `verifier.json` `results[0].anomalies[].edges[].reasons[]` |
| 生 trace 48 file × 2、261,786,377 / 341,192,067 / 計 602,978,444 byte、`source_oid e9e477ca match` | `verify-manifests.log`、各走の `trace-manifest.json` |
| benchmark rc=0 ×240、verifier rc=0 ×238 / rc=1 ×2、certified true 238 / false 2、位置配分 | W1〜W4 の `result.json` `runs[]` (`rc`、`verifier.rc`、`verifier.certified`、`order`) を本稿で集計 |
| pin / patches sha / witness / observational_only / source_file_sha256 / configure_defines / binary_sha256 | 各 block の `result.json` `bindings.arms.<arm>` |
| runner sha / bytes、repo_head、workload argv、policy sha、toolchain (cc / cxx path、version body sha)、base_dir / base_git_dir | 各 block の `result.json` `bindings` |
| request ID / Queue / Created / Started / Ended Request Time / Elapse / child rc | `dispatch-{smoke,W1..W4}.log` (NQSV の終了要約) |
| smoke 4 走の rc / verifier status / verdict / cycles / commit_count / witness flag / discriminator status | `arm-W/smoke/result.json` `runs[]` |
| smoke の witness 検算 (48/48、H bad 0、S = W = 3,014,285 / 3,933,687、L = R = 2,968,147 / 3,873,346、第 5 値不一致 0、G 9,895 / 9,946) | `check-smoke-witness-001.log` / `-003.log` |
| W の OID / 親 / tree / author 日時 / touch set (+26/−6) / trailer、初版 `e0905b3d` と amend 22:44 JST | submodule git object (`git show`)、`W.oid` / `W.oid.superseded`、前 wave の handoff (`HANDOFF.md`) |
| identity `pass` / `match` / 16 context / `old_is_ancestor_of_new`、負例の stderr | `identity-511c-to-W.json`、`identity-e9-to-W.json`、`identity-V2-negative.stderr` |
| 同内容性の `MATCH` (V3) と 4 系列 apply rc=0 | `check-patches.log` |
| 同内容性 39,378 byte (`#line` 除去後)、TRACE 外 31,698 byte | 前 wave の段 6 レビュー A の逐語 `codex/s6-review-A.md` (job dir、sha256 `26eebea2b88444bc38ea67d3cd7dba88aa10fdd7c266c1594b90f5d5cf39a68f`。repo 内の写しは記録 insight `verbatim/s6-reviewA.md`) |
| [T-2774] heavyweight on 541,601 / off 711,199 (§2.6 の参考値) | `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` §1 (旧束縛の記録からの転記。本稿では再集計していない) |
| smoke runner の `started_at` / `finished_at` (13:30:08.95 / 13:32:31.19 UTC) | `arm-W/smoke/result.json` のトップレベル (走ごとの `runs[].started_at` / `finished_at` とは別) |
| 事前登録 (設計・主表示・比較・到達点・欠測規則)、検出力表、smoke 合格集合 | `s4-ruling.md` §3 / §4 (逐語は記録 insight `verbatim/s4-ruling.md`) |
| 検出力の独立再計算 (0.105 / 0.268 / 0.856 / 0.050、off=4 で 0.059、off=5 で 0.029、K=56 で 0.812)、CP の独立再計算 | 本稿の執筆時の計算 (二項分布と超幾何分布の直接計算。一次資料と丸め精度で一致) |
| 事前登録の確定 22:16 JST、段 3 レンズ B 22:12 JST、W amend 22:44 JST、`ps` 実測 22:27:13 / 22:35:10 JST | 前 wave の `HANDOFF.md` (job dir)、`codex/s3-consult-B.md` の mtime |
| ユーザー決定の逐語、問い (i) (ii)、認可しないこと | 記録 insight §0 |

### 5.5 同じ結果についての既存の記述 (本稿の出所ではない)

- `docs/paper-story/README.md` の追補 (worklog entry 1696 の要約) と `docs/phase3.md` のチェック行 — ポインタと要約であり数値の出所ではない。
- worklog entry 1696 (`docs/archive/worklog-phase3-0920-1696-1697.md`) — wave の経緯 (段 3 must-fix、段 6 レビュー、隔離 session の罠) を書く。数値の出所ではない。
- 版 `docs/paper-story/2026-09-19.md` §7 項 2 — 観測 3 件 ([T-2774] / [T-2779] / [T-2780]) までを書き、本 wave の 4 件目は含まない。
- `results/` に mocc の既存の稿は無い。
