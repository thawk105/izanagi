# VHash の hot block (構成 B) を Cicada に入れた最初の実測 — 読み取り専用 95% でも同時刻の stock 比 0.98〜1.01、更新中心では key ごとの排他の待ちで 0.23〜0.80 倍。判定器は 5 腕で巡回なし (上限 indeterminate)、壊し 2 本はどちらも検出・帰属 (2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-hot-block-cicada` (branch `worktree-dev-wave-vhash-hot-block-cicada`)、起点 local main `8fe87f852` (開始 gate fresh rc 0、2026-09-29 22:1x JST)。CCBench submodule = pin C `68106660` (動かしていない)。
依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt` と同 dir の `common.txt`。job dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-cicada/` (Codex の prompt と報告、起動 script、変異 spec と ledger の原本)。
段 1〜6 の全文は `verbatim/`、計測の raw (xz) は `raw/`、変異の spec と ledger は `mutation/`、図と provenance は `figures/`。

**この資料の性能値は、正しさの判定器を通した構成 (5 腕すべて巡回なし、上限 indeterminate) の探索的な同時刻比較である。** 判定の上限が indeterminate なので「serializable」とは書かない。論文の H1 の確認段 (評価計画草稿の主指標 = commit 当たり LLC miss、確認段の新しい走行) の判定ではない。

## 1. 依頼と結論

依頼 (md_23): 直近 K 版の記述子を key ごとに連続配置する VHash の hot block (構成 B) を Cicada に inert patch で入れ、読み取り専用 (ro) の比率と snapshot の古さを軸に、stock と K = 1, 2, 4, 8 を同時刻に比べる。効かないはずの更新中心の条件も入れる。正しさは判定器で確かめ、hot block の取り違えを狙った壊した版の検出も確かめる。論文ストーリー 2 版目 §8.1 が「hot 配置を Cicada に入れた計測 (構成 B) は無い」としていた穴を埋める。

結論:

1. **読み取り専用 95% の条件でも、hot block は throughput をほとんど変えなかった。** 同時刻の stock に対する比の中央値は、GC 間隔 10 µs・1 ms・100 ms の 3 条件 × K 4 水準で 0.980〜1.011 (各 6 round、§5)。最も高いのは GC 100 ms・K=8 の 1.011 (範囲 1.006〜1.014)。通常 YCSB の rr95 は 0.927〜0.978。
   評価計画の草稿 v1 §5.5 (D2301、本 wave の結果より前に main に置かれた読み方) の語では、ro 95% の 12 組すべてが **「予備的に不支持 (差なし)」** (探索の 6 対では、対数比はすべて ±ln(1.10) 以内だった)。草稿の主 cell c23 (ro 95%・GC 100 µs) は測っておらず**欠測**。K\* の選択規則 (ro 95%・GC 10 µs で同点なら最小の K) では **K\* = 1** (§5.1)。
2. **更新を含む条件では大きく遅くなった。** rr50 と ro 0% (GC 10 µs・1 ms) は 0.23〜0.27 倍、rr5 は 0.54〜0.80 倍、ro 50% は GC 間隔と K によって 0.35〜1.00 倍 (§5)。草稿 §5.5 の語では、ro 0%・rr5・rr50 の全組と ro 50% の一部が **「予備的に不支持 (悪化)」** で、§5.5.2 P23-3 に従い書き込み側の費用として記録する。
3. **遅くなる原因は、hot を保守するための key ごとの排他 (seqlock の書き区間) の待ちである。** 診断計器 (別 build、1 走) で、更新中心の cell では 1 update commit あたりの書き区間の**待ち**が約 9.8 万〜11.8 万サイクル、**保持**が約 2,800〜3,800 サイクルだった。ro 95% では待ちが約 850〜1,400 サイクル (§6)。stock は挿入を lock なしの CAS だけで行う。偏り 0.9 の人気 key に 48 thread の書き手が集まると、排他が直列化の点になる。
4. **ro 95% で伸びない理由の一部は、奥の版が hot に収まらないことにある。** stock の第 1 段 (新しすぎる版を飛ばす走査) で飛ばした版数は、GC 100 ms の ro 95% で 0 版が 56%、1〜3 版 14%、4〜15 版 9%、16 版以上 21% (§6)。K=8 でも hot の外 (cold) に出た読みは 2,335 万回あった。GC 10 µs では 0 版が 82% で、飛ばす版がそもそも少ない。hot が省けるのは 1〜K 版を飛ばす読みの pointer 追跡だけで、それが全体に占める割合は小さい。ここまでは計器の数からの説明であり、利得が小さいことの因果の内訳ではない。
5. **正しさ: stock と K = 1, 2, 4, 8 の 5 腕は、3 つの trace cell すべてで巡回なし・integrity 良好・判定 indeterminate (rc 3)** (§3、trace job 0 は 2 回走らせて 2 回とも同じ)。md_11 の観測最良設定そのものは md_20 (`output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md`、main に着地済み) が判定器に掛けて巡回なしとしている。
6. **壊し 2 本はどちらも判定器が巡回として検出し、壊した読みに帰属した。** B1 (hot で 1 つ古い確定版を返す) は T1 で巡回 9、T2 で巡回 1,031 と orphan read 23 件。B2 (選んだ PENDING 版を待たずに飛ばす) は T1 で巡回 9、T2 で巡回 402。**B2 は結果前に「validation に止められて commit 0、検出 0」と予測したが、外れた** (T1 で commit した古い読み 67 件、T2 で 4,331 件)。機序は特定していない (§3.3)。
7. **メモリ: Tuple 1 個が stock 256 byte → K=1 は 256 (既存の余白に収まる)、K=2・4 は 320、K=8 は 384 byte** (実測 sizeof)。100 万 record で K=8 は約 +128 MB。perf 走の maxrss の中央値は stock 1.225 GB に対し K=8 1.306 GB (§7)。
8. **論文への含意 (次の版に使える結論):** この実装 (key ごとの seqlock で hot を列の先頭の写しに保つ) では、構成 B 単独は Cicada の中で throughput を上げなかった。H1 の「局所化で版探索が速くなる」は md_5 の Cicada の外の微小計測では支持されたが、Cicada の中では (a) 深い読みが K より奥に多い、(b) 浅い読みは元々速い、(c) 書き込み側の排他の費用が大きい、の 3 点で利得が現れなかった。構成 D 以降 (hot を前進の契機に使う) の価値は、hot 単独の読みの速さではなく別の効果で示す必要がある。

## 2. 設計 (patch と決めたこと)

`patches/cicada-vhash-hot-block-variant.patch` (pin C の `cc/cicada/include/tuple.hh`・`include/transaction.hh`・`transaction.cc` だけ、421 行)。設計の択一の記録は段 4 裁定 `verbatim/s4-ruling.md`。

- **hot の中身:** key (Tuple) ごとに `seq` (8 byte)・件数・K 個の記述子 `{wts, Version*}` を `latest_` の直後に置く。**物理的な版の列の先頭 min(K, 長さ) 件の写し**で、ABORTED・PENDING の版も含む。状態 (status) は写さず、選んだ版の `status_` を読む。値 (payload) は置かない (Cicada の値は HeapObject の別確保であり、md_5 で K=8 の inline 値は最新版の読みで散在 linked より遅かった)。K はコンパイル時の値 (1, 2, 4, 8) で、K ごとに別 binary。
- **ABORTED を hot から外す案は採らなかった。** 評価計画草稿 §2 の数え方 (ABORTED を除く) に合わせると、物理列との一致と `later_ver` (validation の read 再検査が辿り始める点) の意味が崩れる反例が段 2 で出た (`verbatim/s2-plan.md` §2)。構成 D を作るときに「hot miss = 論理 K 境界」の対応を取り直す必要がある。
- **一貫した読み (出典メモ §20.4 の複数 word の問題):** key ごとの seqlock。書き手は seq を偶→奇へ CAS (acq_rel) → release fence → 記述子を relaxed store → 奇→偶を release store。読み手は seq を acquire で読み、奇数なら stock の走査へ → 記述子を relaxed で写す → acquire fence → seq を読み直し、変わっていれば stock の走査へ。spin しない。pointer は再確認の後だけ参照する (Boehm 2012 の形)。
- **読み:** `read_internal` の第 1 段 (wts が対象時刻より新しい版を飛ばすループ) だけを置き換える。hot の中で wts ≤ trts の最初の記述子を選び、`later_ver` は物理の直前の記述子。全件が新しすぎれば最後の記述子から stock のループを続ける (cold)。第 2 段 (PENDING 待ち・ABORTED 飛ばし)・deleted の判定・read set の記録は stock のまま。
- **書き込みと GC:** validation の版の挿入 (位置探索と CAS) を key ごとの書き区間の中で行い、成功したら挿入位置 p < K のとき hot を shift する。**K>0 では位置探索を read 時の `later_ver_` からでなく列の先頭から行う** (hot に入れる位置を数えるため。書き区間の中では列が動かないので挿入位置は stock と同じ、段 6 のレビュー 2 本とも反例不成立)。GC は `gc_lock_` の後に書き区間を開き、切り離し点より古い記述子を消してから切り離し、区間を閉じてから版を再利用に回す。lock の順は `gc_lock_` → hot の一方向。
- **安全の論証 (証明ではない):** 読み手が選ぶ版は、seq を確かめた時点の物理列で stock の第 1 段が止まる版と同じ。GC の切り離し点は確定版で wts < MinRts ≤ 読み手の rts なので、読み手はその点より古い版を選ばない。確認の後に切り離し点がより新しく挿入されることは、ro では書き手の wts > rts、update では切り離し点の書き手が読み手の開始前に終わっていることから起きない。tx の途中で ThreadRtsArray を動かさない (stock のまま、md_14 の教訓)。stock の安全性への帰着であり、判定器の結果で代用しない。
- **macro (IZANAGI_ 接頭辞なし、D2288 の慣行):** `CICADA_VHASH_K` (未定義 = 0 = stock、1/2/4/8 以外は #error)、`CICADA_VHASH_COUNT` (診断計数。性能値に使わない)、`CICADA_VHASH_WL` (実行時 flag `--vhash_ronly_pct`、既定 -1 = YCSB の生成のまま。新しい手続きの初回 begin() だけで抽選し、ro なら全 op を READ、update なら少なくとも 1 op を write。先例は md_15 の `izanagi_ronly_pct`)。stock 対照も WL=1 の同じ patch で build する。分岐は owner TU `transaction.cc` と、それが include する 2 header だけ。各挿入の後に `#line`。
- **inert:** macro なしで pin と patch 後の `transaction.cc`・`util.cc`・`ycsb_cicada.cc` を同じ argv で前処理し一致 (段 5・6 の実装子が login で確認、段 6 fix で再確認)。
- **条件 gate への登録 (所有外の必要最小):** 3 macro を `orchestrator/campaign/condition_meaning_gate.py` に登録し、連動する在庫 (screening_driver の既定値・materializer・spawn site・性能 file の在庫・tests README) を足した。`CICADA_VHASH_COUNT` は分岐の多くが `#if CICADA_VHASH_K` の内側にあるので、gate の probe に companion `CICADA_VHASH_K=1` を固定した (md_6 の `CICADA_FWD_COUNT` と同じ形、`verbatim/s6-fix2-ruling.md`)。K=2/4/8 と K=0 の COUNT の意味の証拠は、その文脈では取っていない。

## 3. 正しさ

### 3.1 設定

trace build = pin C → `patches/instr-cicada-trace.patch` (bytes 不変、D2279) → 本 patch (→ 壊し patch)、TRACE=1、INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0・BACK_OFF=0 (md_11 の観測最良)。48 thread、`ycsb_tuple_num=200`、zipf 0.9、extime 1、group_commit 0。判定器 = `python -m verifier <dir> --json --quiet --protocol cicada --ccbench-root <src> --expected-commits N` (判定器の production は変えていない)。

| cell | ro 指定率 | gc_inter_us | ycsb_rratio | rmw | max_ope | 意図 |
|---|---:|---:|---:|---:|---:|---|
| T1 | 95 | 100000 | 50 | 0 | 10 | 古い snapshot の ro の深い読み (hot と cold の両方を通る) |
| T2 | 50 | 10 | 50 | 0 | 10 | 高頻度の GC と update の混在 (trim・切り離しと並行) |
| T3 | -1 | 100 | 0 | 1 | 5 | md_3 の cell W (rmw の書き込みが集中) |

### 3.2 5 腕の結果 (raw-trace-0.json = 2 回目、raw-trace-1.json)

| 腕 | T1 | T2 | T3 |
|---|---|---|---|
| stock (K=0) | 巡回 0、C 行 = commit 1,144,133 | 巡回 0、671,798 | 巡回 0、6,676 |
| K=1 | 巡回 0、1,180,055 | 巡回 0、429,635 | 巡回 0、226,591 |
| K=2 | 巡回 0、1,142,415 | 巡回 0、511,684 | 巡回 0、269,423 |
| K=4 | 巡回 0、1,135,771 | 巡回 0、430,050 | 巡回 0、235,572 |
| K=8 | 巡回 0、1,127,283 | 巡回 0、438,752 | 巡回 0、230,248 |

全 15 走で verdict indeterminate (rc 3)、integrity の数値項目すべて 0、trace の C 行数 = ベンチの commit 数。1 回目の trace job 0 (`raw/raw-trace-0.first.json.xz`、bnode005) の 10 走も同じく巡回 0・clean だった。**失格の腕は無い。**
T3 の stock の commit 数 (6,676) が K>0 (22.7 万〜26.9 万) より 2 桁少ない。trace build の 1 走ずつの値で性能値ではない。hot の書き区間が rmw の集中する 200 tuple で CAS の衝突を減らした可能性があるが、確かめていない。

### 3.3 壊し 2 本 (本 patch の上にだけ重ねる無条件 patch、K=4 の trace build)

| 壊し | cell | 判定 | 巡回数 | 事象 reached / changed / committed | 帰属 witness | integrity | 分類 |
|---|---|---|---:|---|---:|---|---|
| B1 `broken-cicada-vhash-stale-hot.patch` | T1 | non-serializable | 9 | 95,900 / 95,900 / 95,900 | 9 | clean | 巡回で検出・帰属 (clean) |
| B1 | T2 | non-serializable | 1,031 | 64,897 / 64,897 / 64,897 | 19 | orphan read 23 | 巡回で検出・帰属 (integrity 違反あり) |
| B2 `broken-cicada-vhash-skip-pending.patch` | T1 | non-serializable | 9 | 1,496 / 1,494 / 67 | 9 | clean | 巡回で検出・帰属 (clean) |
| B2 | T2 | non-serializable | 402 | 114,447 / 113,958 / 4,331 | 20 | clean | 巡回で検出・帰属 (clean) |

- 帰属規則は md_3 と同じ (判定器が出す代表 witness (最大 20 件) の rw 辺が、事象の txn・key・読んだ版に一致)。「帰属 witness」は一致した代表 witness の数。
- B1 は、元の選択版が確定版で、返す版 (1 つ古い記述子) が別の確定版のときだけ古い版を返す (段 6 fix で過大計数を直した)。T2 の orphan read は、返した古い版が GC で回収・再利用された後に読まれたと考えると筋が通るが、確かめていない。
- **B2 の予測外れ:** 段 4 で結果前に「ro tx では PENDING 版の wts は rts より大きく到達しない、update tx では validation (a) が止めるので commit 0・検出 0」と登録した (`verbatim/s4-ruling.md` §2.2)。観測は T1 で commit 67、T2 で commit 4,331、どちらも巡回として検出・帰属した。予測のどの前提が崩れたかは特定していない (候補: validation (a) が辿り始める `later_ver` の扱い、ro tx の rts と進行中の書き手の wts の関係)。予測は書き換えずに残す。
- 1 回目の trace job 0 では B1 T1 巡回 10・B2 T1 巡回 3 (帰属 10・3) の後、B1 T2 で driver が integrity 違反を例外にして job ごと止まった (§9)。

## 4. 計測の設定

- 計算ノード: Pegasus gen_S (Xeon Platinum 8468、48 core、HT 無効)、node 専有。各 job の冒頭と各 run の前に他の ycsb/bench process が無いことを記録 (全 job で 0 件)。
- build: 1 job (bnode 上で 17 binary、247 s) で作り、他の job は manifest の sha256 と ldd の解決先・依存 file の sha256 を照合して同じ binary を使った (全 job で `shared-verified`)。性能 build は TRACE=0・ADD_ANALYSIS=0・COUNT なしを compile command で検査。
- 共通 argv: `-thread_num=48 -ycsb_tuple_num=1000000 -ycsb_zipf_skew=0.9 -ycsb_max_ope=10 -ycsb_rmw=0 -extime=3 -clocks_per_us=2100`、cell ごとに `-ycsb_rratio`・`-gc_inter_us`・`--vhash_ronly_pct`。build 定数は §3.1 と同じ (md_11 の観測最良)。
- 格子 (12 cell): ro 指定率 {0, 50, 95}% × gc_inter_us {10, 1000, 100000} (update tx の読み比 50%) と、通常 YCSB の rr5 (gc 100)・rr50 (gc 100)・rr95 (gc 10) (ro 指定なし)。**「snapshot の古さ」の軸は GC 間隔で代用した。** GC 間隔は snapshot の古さそのものではなく、版の数や更新の進みも同時に変える (段 3 相談の指摘)。軸の名前は「GC 間隔」とする。
- 同時刻対照: 1 job の中で 12 cell × 5 腕を round ごとに回し、腕の順は round と cell で回転。3 job × 2 round = 6 round。比は同じ job・同じ round・同じ cell の K/stock。perf job 0・1 は bnode022、job 2 は bnode005。
- 統計: cell × K ごとに比の全 6 点・中央値・最小〜最大を示す。**有意とは書かない (探索段)。** round は 2 node に分かれており、node の差と K の効果は分けていない。

## 5. 結果: throughput の同時刻比 (K/stock、6 round の中央値 [最小, 最大])

| cell | stock 中央値 tps | K=1 | K=2 | K=4 | K=8 |
|---|---:|---|---|---|---|
| ro0-gc10 | 3,415,671 | 0.227 [0.221, 0.236] | 0.257 [0.249, 0.269] | 0.231 [0.223, 0.238] | 0.227 [0.214, 0.238] |
| ro0-gc1000 | 3,300,843 | 0.238 [0.234, 0.243] | 0.269 [0.262, 0.274] | 0.236 [0.233, 0.242] | 0.234 [0.229, 0.243] |
| ro0-gc100000 | 1,924,472 | 0.380 [0.362, 0.398] | 0.536 [0.506, 0.599] | 0.372 [0.359, 0.378] | 0.368 [0.363, 0.373] |
| ro50-gc10 | 5,318,972 | 0.631 [0.551, 0.721] | 0.935 [0.912, 0.954] | 0.355 [0.345, 0.367] | 0.347 [0.337, 0.348] |
| ro50-gc1000 | 4,726,358 | 0.961 [0.956, 0.969] | 0.967 [0.963, 0.977] | 0.548 [0.516, 0.593] | 0.479 [0.457, 0.512] |
| ro50-gc100000 | 1,026,373 | 0.995 [0.991, 1.011] | 1.003 [1.002, 1.018] | 0.988 [0.985, 1.005] | 0.974 [0.940, 0.987] |
| ro95-gc10 | 12,979,214 | 0.985 [0.976, 0.989] | 0.980 [0.977, 0.988] | 0.987 [0.985, 0.996] | 0.989 [0.983, 0.992] |
| ro95-gc1000 | 12,246,994 | 0.982 [0.974, 1.007] | 0.984 [0.972, 1.004] | 0.994 [0.990, 1.012] | 0.997 [0.989, 1.018] |
| ro95-gc100000 | 3,179,980 | 1.000 [0.992, 1.004] | 0.999 [0.995, 1.003] | 1.006 [1.000, 1.010] | 1.011 [1.006, 1.014] |
| rr5 | 2,252,995 | 0.686 [0.641, 0.698] | 0.795 [0.772, 0.823] | 0.553 [0.535, 0.567] | 0.537 [0.526, 0.551] |
| rr50 | 3,459,439 | 0.229 [0.222, 0.240] | 0.262 [0.252, 0.280] | 0.231 [0.227, 0.242] | 0.229 [0.217, 0.234] |
| rr95 | 10,949,809 | 0.978 [0.975, 1.015] | 0.978 [0.968, 1.003] | 0.957 [0.953, 0.984] | 0.927 [0.909, 0.948] |

(値は `raw/aggregate.json.xz` の `cells`、stock の中央値は `raw/raw-perf-*.json.xz` の perf 記録から。stock 中央値は 0.5 tps 単位を切り捨て。)

### 5.1 評価計画の草稿 v1 §5.5 による予備的な判定語

草稿 `docs/vhash-evaluation-preregistration-draft.md` v1 の §5.5 (D2301) は、md_21・md_23 の結果を見る前に探索段の読み方を固定した (commit `cb0f03e6f`、2026-09-29 22:59。本 wave の性能値の最初の raw は 2026-09-30 01:22)。**本 wave の計測は §5.5 を知る前 (段 4、2026-09-29 22:45) に設計したので、A/A 腕も主 cell c23 (ro 95%・GC 100 µs) も含まない。** 親が §5.5 を読んだのは結果を見た後だが、規則は変えずに aggregate の全点へ機械的に当てた (判定の script と出力は job dir の `judge-55.txt`)。

- δ_ex = ln(1.10) = 0.0953。d_i = ln(B_K / A) を同じ job・同じ round で対にし、n = 6。A/A 腕は無い (「予備的に支持」は出せず、出る場合は「判定不能 (A/A なし)」)。
- 語の順序の前段: 失格なし (5 腕とも門で巡回 0、§3)。門は完了 (壊し 2 本とも検出)。比較相手 A (観測最良設定) は md_20 が巡回なしを main に置いており、本 wave の K=0 の trace も巡回なし。性能値は性能用 build (計器も trace も無い、ro 指定率の制御は variant patch の WL の中) から取った。

| 比較 | 語 | 組 |
|---|---|---|
| P23-1 B_K 対 A | 予備的に不支持 (差なし) | ro95 の GC 10 µs・1 ms・100 ms × K 1/2/4/8 の 12 組、ro50-gc100000 の 4 組、ro50-gc1000 の K 1・2、ro50-gc10 の K 2、rr95 の K 1・2・4 |
| P23-1 B_K 対 A | 予備的に不支持 (悪化) | ro0 の 3 GC × 4 K の 12 組、rr5・rr50 の 8 組、ro50-gc1000 の K 4・8、ro50-gc10 の K 1・4・8 |
| P23-1 B_K 対 A | 判定不能 | rr95 の K 8 (d_i の最小 −0.0955 が −δ_ex を僅かに下回り、全 round が同じ語にそろわない) |
| P23-1 主 cell c23 | 欠測 | ro 95%・GC 100 µs は測っていない (近い cell へ切り替えない) |
| P23-2 用量 (差の差と R95 の B 対 A、同じ K・同じ GC) | 判定不能 | 12 組すべて。差の差は +0.51〜+1.53 で全 round が δ_ex を超えるが、A/A 腕が無いので支持の語を出せず、R95 の成分は差なし。差の差が大きいのは R0 側で B が大きく遅いためで、R95 側で速いためではない |
| P23-3 効かないはずの条件 (R0・Y5 = rr5) | 予備的に不支持 (悪化) | 書き込み側の費用として記録 (§6) |
| P23-4 snapshot の古さ | 記述のみ | GC 100 ms の水準は機序の確認に限り、「Cicada に対して速い」の根拠にしない |
| K\* の選択 | K\* = 1 | 選択に使う cell = ro95-gc10 (c23 が無いため)。B_K の throughput の反復中央値 K1 12,780,132・K2 12,748,836・K4 12,848,963・K8 12,848,792 tps。最良 (K4) と全 K が同点 (\|ln 比\| ≤ δ_ex) なので最小の K |

組の数: P23-1 は 12 cell × 4 K = 48 組 (+ 欠測の主 cell)、P23-2 は 3 GC × 4 K = 12 組。組ごとに独立に語を付けており、束ねた主張はしない。これは検定ではない (n = 6)。

![K と throughput (cell 別)](figures/fig-k.png)

**読み方 (fig-k)。** 横軸が cell、縦軸が同じ round の stock に対する比。菱形が中央値、小さい点が 6 round の全点、縦線が最小〜最大。破線 1.0 が stock。ro 95% の 3 cell と ro50-gc100000 だけが 1.0 付近で、更新を含む cell は大きく下回る。

![ro 比率と利得 (GC 間隔別)](figures/fig-ro.png)

**読み方 (fig-ro)。** 横軸が ro 指定率 (0・50・95%)、線が K × GC 間隔。ro 比率を上げると比は 1.0 に近づくが、1.0 を明確に上回る線は無い。**言えないこと:** 横軸は ro「指定率」で、実現した ro commit の割合は ro95 の COUNT 走で 0.950 (§6)。ro 比率を変えると update の数・版の生成・abort も同時に変わるので、この図は ro 比率の因果効果ではない。

![書き込み側の費用](figures/fig-write.png)

**読み方 (fig-write)。** 上段は更新中心の 4 cell の比。下段は ro0-gc10 の COUNT 走での、1 update commit あたりの hot 書き区間の**保持**サイクル (install_hold_cycles / update_commit)。**図の限界:** 下段は保持だけで、主因の**待ち** (1 commit あたり約 9.8 万〜11.8 万サイクル、§6 の表) を描いていない。書き込み側の費用の大きさは §6 の表で読む。

## 6. 診断計器 (COUNT、別 build、各 1 走、性能値ではない)

| cell | K | tps (COUNT build) | 実現 ro 割合 | hot で読んだ回数 | seq 奇数で stock へ | seq 変化で stock へ | cold へ出た回数 | 飛ばした版数 0 / 1〜3 / 4〜15 / 16+ | 書き区間の待ち / upd commit | 保持 / upd commit | GC 区間 / upd commit | upd abort / upd commit | sizeof(Tuple) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| ro95-gc100000 | 0 | 3,175,177 | 0.950 | 0 | 0 | 0 | 0 | 0.560 / 0.138 / 0.093 / 0.209 | 0 | 0 | 0 | 0.033 | 256 |
| ro95-gc100000 | 1 | 3,151,228 | 0.950 | 91,361,109 | 39,916 | 106 | 40,118,557 | 0.561 / 0.138 / 0.093 / 0.209 | 856 | 442 | 745 | 0.035 | 256 |
| ro95-gc100000 | 2 | 3,143,199 | 0.950 | 91,130,646 | 42,581 | 181 | 32,862,106 | 0.561 / 0.138 / 0.093 / 0.208 | 842 | 497 | 804 | 0.036 | 320 |
| ro95-gc100000 | 4 | 3,162,846 | 0.950 | 91,692,144 | 52,283 | 1,074 | 27,544,940 | 0.561 / 0.138 / 0.092 / 0.209 | 989 | 526 | 820 | 0.036 | 320 |
| ro95-gc100000 | 8 | 3,200,527 | 0.950 | 92,774,426 | 64,831 | 1,682 | 23,345,844 | 0.561 / 0.138 / 0.093 / 0.209 | 985 | 1,092 | 825 | 0.038 | 384 |
| ro95-gc10 | 0 | 12,693,711 | 0.950 | 0 | 0 | 0 | 0 | 0.820 / 0.088 / 0.058 / 0.034 | 0 | 0 | 0 | 0.104 | 256 |
| ro95-gc10 | 1 | 12,206,353 | 0.950 | 353,997,535 | 681,145 | 1,123 | 64,031,176 | 0.818 / 0.088 / 0.058 / 0.036 | 1,108 | 565 | 513 | 0.109 | 256 |
| ro95-gc10 | 2 | 12,196,271 | 0.950 | 353,745,481 | 680,431 | 2,129 | 46,049,623 | 0.819 / 0.088 / 0.058 / 0.035 | 1,159 | 583 | 553 | 0.114 | 320 |
| ro95-gc10 | 4 | 12,263,114 | 0.950 | 355,291,892 | 1,021,864 | 52,080 | 32,489,756 | 0.819 / 0.088 / 0.058 / 0.035 | 1,435 | 604 | 556 | 0.114 | 320 |
| ro95-gc10 | 8 | 12,177,599 | 0.950 | 352,578,280 | 1,255,034 | 57,580 | 21,102,736 | 0.819 / 0.088 / 0.058 / 0.035 | 1,431 | 1,388 | 570 | 0.116 | 384 |
| ro0-gc10 | 0 | 3,318,841 | 0.000 | 0 | 0 | 0 | 0 | 0.983 / 0.016 / 0.001 / 0.000 | 0 | 0 | 0 | 0.742 | 256 |
| ro0-gc10 | 1 | 689,040 | 0.000 | 15,912,252 | 651,392 | 3,161 | 6,937 | 0.999 / 0.000 / 0.000 / 0.000 | 118,404 | 2,998 | 410 | 0.693 | 256 |
| ro0-gc10 | 2 | 808,248 | 0.000 | 18,579,121 | 765,779 | 4,795 | 1,941 | 0.999 / 0.001 / 0.000 / 0.000 | 97,549 | 2,769 | 470 | 0.685 | 320 |
| ro0-gc10 | 4 | 697,567 | 0.000 | 16,132,772 | 663,267 | 8,065 | 692 | 0.999 / 0.000 / 0.000 / 0.000 | 116,495 | 3,090 | 432 | 0.699 | 320 |
| ro0-gc10 | 8 | 749,579 | 0.000 | 17,174,470 | 718,408 | 12,500 | 354 | 0.999 / 0.001 / 0.000 / 0.000 | 105,993 | 3,730 | 516 | 0.680 | 384 |
| rr50 | 0 | 3,532,517 | 0.001 | 0 | 0 | 0 | 0 | 0.982 / 0.017 / 0.001 / 0.000 | 0 | 0 | 0 | 0.736 | 256 |
| rr50 | 1 | 697,575 | 0.001 | 16,135,118 | 666,972 | 3,554 | 12,083 | 0.999 / 0.001 / 0.000 / 0.000 | 117,134 | 2,957 | 393 | 0.697 | 256 |
| rr50 | 2 | 751,934 | 0.001 | 17,688,261 | 717,875 | 5,546 | 6,362 | 0.999 / 0.001 / 0.000 / 0.000 | 106,979 | 2,946 | 402 | 0.727 | 320 |
| rr50 | 4 | 695,959 | 0.001 | 16,075,101 | 656,187 | 8,944 | 3,840 | 0.999 / 0.001 / 0.000 / 0.000 | 117,837 | 3,083 | 429 | 0.695 | 320 |
| rr50 | 8 | 727,159 | 0.001 | 16,731,280 | 691,787 | 12,988 | 2,735 | 0.999 / 0.001 / 0.000 / 0.000 | 110,155 | 3,782 | 451 | 0.690 | 384 |

(値は `raw/aggregate.json.xz` の `count` の各行の `count` 欄と `tuple_size_bytes`。サイクルは rdtscp の和を update commit 数で割った値。「飛ばした版数」は第 1 段で飛ばした論理的な版の数の分布で、stock と K で同じ定義。hot で省けた pointer 追跡の数そのものではない。)

- **書き区間の待ち:** 更新中心の cell で 1 update commit あたり 9.8 万〜11.8 万サイクル (保持の 30〜40 倍)。挿入 1 回ではなく commit あたりの値で、1 commit は約 5 key を書き、CAS 失敗と abort した tx の試行も含む (`install_count` は試行数)。
- **snapshot の遅れの計器は機能しなかった。** ro tx の begin 時の (wts − rts) を 2 冪 bucket (上限 2^16 ts 単位) で数えたが、全件が最上位の bucket に入り分解できなかった (Cicada の timestamp は rdtscp 由来で単位が大きい)。**snapshot の古さの効果は、実測の遅れでは言えない。**
- update tx の読みはほぼ先頭で終わる (ro0・rr50 で 0 版が 98%)。md_2・md_15 の結論と同じ向き。

## 7. メモリ

| 腕 | sizeof(Tuple) (実測、byte) | 100 万 record の増分 (解析値) | perf 走の maxrss 中央値 (kB、72 走) | 最小〜最大 (kB) |
|---|---:|---:|---:|---|
| stock | 256 | — | 1,224,758 | 1,080,840〜2,901,556 |
| K=1 | 256 | 0 | 1,192,418 | 1,082,224〜2,727,532 |
| K=2 | 320 | +64 MB | 1,266,346 | 1,143,072〜2,837,540 |
| K=4 | 320 | +64 MB | 1,244,692 | 1,144,092〜2,728,480 |
| K=8 | 384 | +128 MB | 1,306,332 | 1,207,476〜2,969,388 |

maxrss は GC 間隔と ro 比率で大きく変わる (最大 2.9 GB は GC 100 ms の cell)。腕の間の差は cell の間の差より小さい。版そのもの・allocator の予約は分けて測っていない。

## 8. 計算量 (この wave が計算ノードへ投げた全 job、NQSV の Elapse)

| job | request | node | Elapse | 結果 |
|---|---|---|---:|---|
| smoke1 (tip 297ad1dee) | 36580 | bnode005 | 101 s | COUNT の条件 gate 拒否で停止 (§9) |
| smoke2 (ae533473d) | 36606 | bnode001 | 308 s | 成功 |
| build (d109d4078) | 36619 | — | 247 s | 17 binary |
| perf 0 / 1 / 2 | 36631 他 | bnode022 / bnode022 / bnode005 | 518 / 518 / 521 s | 成功 |
| count | — | bnode005 | 85 s | 成功 |
| trace 0 (1 回目) | 36734 | bnode005 | 224 s | 壊しの T2 で停止 (§9) |
| trace 1 | — | bnode005 | 32 s | 成功 |
| trace 0 (2 回目、474552f1c) | 36754 | bnode020 | 254 s | 成功 |
| 変異 probe / 本走 1 / 本走 2 | 36638 / 36739 / 36779 | — | 231 / 233 / 412 s | §10 |
| 焦点走 3 本・provenance 監査 | — | — | 164 + 19 + 153 + 14 s | §10 |

計測 2,808 s + 変異 876 s + test 350 s = 4,034 node 秒 (約 1.12 node 時間)。受入全走の所要は worklog 側の記録。依頼の上限 2 node 時間未満。
**見積りの式のずれ (nit):** driver の `estimate` は trace job の所要を「2 job の走数の和」でなく「多い方 (14 走) × 2」で数える (段 6 焦点再レビューの所見)。過大側で、smoke2 の値では 2,432.3 node 秒 (現行式) 対 約 2,283.6 (和の式)。どちらも閾値 7,200 を大きく下回り、選んだ計画 (縮小なし) は同じ。修正は後続の backlog (`verbatim/s6-close-ruling.md`)。

## 9. 途中で起きたことと直したこと

- **smoke1 (計算ノード) で条件 gate が COUNT を拒否した。** 宣言 20 site に対し観測 8 site。COUNT の分岐の多くが `#if CICADA_VHASH_K` の内側にあり、gate の probe は K 未定義で前処理するので見えない (非活性の #if の内側は観測できない、既知の型)。companion `CICADA_VHASH_K=1` を固定して解消 (`verbatim/s6-fix2-ruling.md`)。
- **同じ計測木から 6 job を並列に投げ、5 本が rc 16 (orphan hold) で即座に止まった。** 同一 worktree からの dispatch は全種直列という既存の規律 (DW-C00) の読み落とし。止まった 5 本は子を起動しておらず計算は 0。残りを同じ木から 1 本ずつ流した。
- **trace job 0 (1 回目) が、壊し B1 の T2 走で判定器の integrity 違反 (orphan read 50、notes の先頭「988 cy…」= 巡回 988 とみられる) を例外にして job ごと止まった。** driver が壊し版にも integrity clean を要求していた。壊し版は記録して続けるように直し (`verbatim/s6-fix3-ruling.md`)、同じ binary で trace job 0 を取り直した。1 回目の raw は `raw/raw-trace-0.first.json.xz` に残す (1 回目の B1 T2 の数値は raw に無く、例外の本文 = 上の数だけが残っている)。
- **焦点走で本 wave が持ち込んだ回帰を 2 件見つけて直した。** 条件 gate の test の分岐条件を一般化して既存 macro (BACKOFF_REQUESTED_US) の照合を壊していた件と、新 driver の性能 file の在庫漏れ。

## 10. 検査と変異

- 焦点走 (計算ノード): tip 297ad1dee で 1,800 passed / 2 failed (上の回帰 2 件) → dd80b7156 で 347 passed / 1 failed (新 test の理由順) → d109d4078 で 1,735 passed・5 skipped・0 failed。
- 変異 (driver の fail-closed、`mutation/`): 独立 clone を対象 commit に固定し、`--task mutation` で計算ノードの 1 job に束ねて走らせた。本走 1 (d109d4078、spec sha256 `bbcd461d…`): baseline PASSED、M0 (docstring だけの等価変異) SURVIVED、M2〜M10 の 9 本すべて期待した node で KILLED、wrapper rc 0・共有木の検査一致。M1 (perf でない記録を表に入れる) は同じ入力を別の層 (run の鍵の検査) が先に拒否して赤の理由が 1 つにならないので登録しなかった。本走 2 (最終のコード tip 474552f1c、spec sha256 `7568ceeb…`、M11 = 壊し版の integrity 違反で job を止めるに戻す、を追加): baseline PASSED、M0 SURVIVED、M2〜M11 の 10 本すべて期待した node で KILLED、wrapper rc 0・共有木の検査一致 (412 s)。
- 変異の対象は driver と条件 gate の登録で、C++ の hot の保守そのものの検出力は壊し patch 2 本 (§3.3) で示した。

## 11. 確かめたこと・確かめていないこと

確かめたこと:
- hot block を入れた Cicada (K = 1, 2, 4, 8) が、3 つの trace cell で判定器を通った (巡回なし、上限 indeterminate)。壊し 2 本は巡回として検出・帰属した。
- 同時刻の stock 対照つきで、12 cell × 4 K の throughput 比 (各 6 round) と、代表 4 cell の診断計器の値。
- Tuple の大きさの実測と、maxrss。

確かめていないこと:
- 草稿 H1 の主指標 (commit 当たり LLC miss)。perf 計測はしていない。
- snapshot の古さそのものの効果 (計器が飽和、軸は GC 間隔で代用)。長い固定 snapshot (長い ro tx) は入れていない。
- TPC-C、scan、insert・delete を含む負荷。trace の射程は YCSB の point read / update。
- B2 の予測が外れた機序、B1 T2 の orphan read の機序、T3 の stock の commit 数が少ない理由。
- 書き区間の待ちを減らす設計 (例: 書き区間を CAS の後の hot 更新だけに縮める、hot の更新を遅らせる、key ごとの排他を使わない方式)。本 wave の実装はこの 1 つの設計点だけを測った。
- 「serializable」の主張 (判定の上限は indeterminate)。

## 12. 次の一手 (論文と実装)

1. 書き込み側の排他を CAS の外へ出す設計 (hot を列の写しとして遅れて更新してよい条件の論証を含む) を 1 つ試し、更新中心の cell の比がどこまで戻るかを測る。この wave の安全の論証 (§2) は「書き区間の中で列を変える」ことに頼っているので、そのまま流用できない。
2. 構成 D (hot の外れを前進の契機に使う) の価値を、hot 単独の読みの速さではなく前進の効果で測る。その前に「hot miss = 論理 K 境界」の対応 (ABORTED の扱い) を決め直す。
3. snapshot の遅れの計器の単位を直す (ts 単位の分布を µs に換算できる bucket に)。
4. B2 の予測外れの機序を小モデルか計器 build で調べる。

## 13. 再現

- 計測木: detached worktree を tip `d109d4078` (build・perf・count・trace 1) と `474552f1c` (trace 0 の 2 回目、driver の変更だけで binary は同じ manifest) に置き、`python3 tools/pegasus/dispatch_compute.py --task generic --walltime HH:MM:SS --queue-wait-timeout 3600 --overall-grace 3900 -- python3 -m orchestrator.campaign.vhash_cicada_hot_block <build|perf --job-index i|count|trace --job-index i> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --scratch-root <dir> --output <同じ out dir>`。同じ木から dispatch を並列にしない。
- 集計: `python3 -m orchestrator.campaign.vhash_cicada_hot_block aggregate --raw <raw-perf-0..2> <raw-count-0> <raw-trace-0> <raw-trace-1> --out <dir>`。作図: `python3 tools/plotting/plot_vhash_cicada_hot_block.py <aggregate.json> --out figures`。raw は `xz -dk raw/*.xz` で戻す。
- raw の原本の sha256 (xz 展開後): `manifest.json` 1509d954…、`raw-perf-0.json` e33b804c…、`raw-perf-1.json` e2bbd507…、`raw-perf-2.json` 95fd38b2…、`raw-count-0.json` 2ff50299…、`raw-trace-1.json` 8c0c4003…、`raw-trace-0.first.json` 5822b27c…、`smoke.json` (smoke2) 1ace2072…。`raw-trace-0.json` (2 回目) `a0a20c1c7920999c72c8135bcd8725488fae2bec1a88cad104537d478748e451`、`aggregate.json` `d4bc6b89e722dd595ec864bfec23a1ef1de81fdcf6977355027c14d9e33114af`。他の全 64 桁は job dir の `raw-copy-2.log`。
- §5.1 の判定語: 出力 `judge-55.txt` (sha256 d747b53e…)、script は repo 外の job dir `judge_55.py` (sha256 ccc5a6b2…、aggregate と raw-perf-0..2 を入力に δ_ex = ln(1.10) の §5.5.0 の語を付ける)。
