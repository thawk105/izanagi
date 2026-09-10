# [T-2430] A-6 read-heavy の −5.78% は、近接条件の別実行 (B-10 の 3 block) が同符号・同程度で示し、名目待機会計と整合する — 反復 attempt は行わない

**種別:** 記録済み測定の事後再解析 (新しい測定は 1 件も行っていない、絶対規律 7)。
**すべて非認証である。** A-6 の 2 cell は同一 attempt の別 trace-enabled run で正しさが `certified` だが、
性能値そのものは認証されない (絶対規律 1・2)。B-10 と thread-scaling の値は `performance_certified = false` の
trace-disabled 測定である。ここにある値を根拠に variant を採用してはならない。
**本稿は機序を一意に同定しない。** 行ったのは「集約 abort 率を条件にして、ソース上の名目 2 µs/abort の
待機会計が観測された差と整合するか」を調べる事後整合性検査である。

- 日付: 2026-09-08
- wave: `worktree-dev-wave-t2430-a6-readheavy-mechanism` (local main `34af5a571` から)
- 一次資料: `output/insights/2026-09-08_t2411-a6-readheavy-submitted/README.md` (A-6 attempt の記録)、
  `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json` (A-6 権威 bytes)、
  `output/insights/2026-09-07_backoff-tail-mechanism/README.md` (会計式 (1) の正本)、
  `output/insights/2026-09-07_t1905-b10-readheavy-admit/README.md` (B-10 read-heavy 系列の限定受理)

## 0. 何が分かったか

A-6 attempt `a6-20260908b` (read-heavy、48 スレッド) で採用版 (`BACK_OFF=1, BACKOFF_FIXED=2`) が stock
(`BACK_OFF=0`) より **−5.784%** 遅かった。この 1 attempt・5 標本の中央値比較について、[T-2430] は
「反復 attempt で確かめるか、機序として説明する」ことを求めていた。答えは次の 3 つである。

1. **近接条件の別実行が同符号・同程度を示している。** B-10 read-heavy 本走 (job `977647.nqsv`、`bnode088`、
   2026-09-05、source `2a338449b`) は同じ 2 genome (`none` = `BACK_OFF=0, BACKOFF_FIXED=-1`、
   `constant-mu2` = `BACK_OFF=1, BACKOFF_FIXED=2`) を **1 job 内の 3 block × 5 標本**で測っており、効果は
   **−6.61% / −5.38% / −5.32%** (block 平均 −5.77%)。A-6 の −5.78% はこの帯に入る。15 標本ずつの範囲は
   重ならない (none 10.12〜10.52 Mtps、mu2 9.59〜9.66 Mtps)。両 arm の絶対水準は A-6 より 1.27% 高く、比だけが
   一致した。**これは「同条件かつ独立な再現」ではなく、別 node・別日・別 source・別 build 経路という近接条件の
   別実行 (実行機会は A-6 と合わせて 2 つ) による履歴的再現である** (§2 に一致項目と未照合項目を分ける)。
2. **差の大きさは名目待機会計で大部分が再構成できる。** ソース上、backoff は abort 経路からのみ 1 abort につき
   1 回 `b` µs の spin として入る。A-6 の集約 abort 率から 1 commit あたりの名目待機は
   `a₂·b = 0.1696 × 2 = 0.339 µs`、観測された集約時間の増分は `Δs = +0.292 µs` である。会計項だけで
   throughput 効果 −6.66% (実測 −5.78%)、別データの abort 1 回の費用 `r` で abort 減少の節約を差し引くと
   −5.87〜−5.95% になる。**一致の大部分は会計項で決まり、`r` が埋めるのは 0.9 ポイントの補正である。**
   B-10 側は backoff 呼出し回数を計数しており、呼出し回数 × 名目 2 µs が 48 worker × walltime の
   **6.0%** に相当する (実 spin 時間は計測していない)。
3. **したがって新しい反復 attempt は行わない。** 符号は近接条件の別実行で一致し、大きさは名目会計と整合する。
   `certification.json` の `a4_noise_floor_status` は producer が `"open"` を定数で書き validator がそれ以外を
   拒否するので、反復を何回行っても閉じない。反復で失うのは**別に schedule された attempt 間の変動の観測**であり、
   本稿はその不確かさを残した事後解析である。a4 を閉じるのは protocol の改版であり本 wave の scope 外。

**言えないこと。** 会計項 `a·b` は定義と計数から従う量で、経験的な内容は「commit 到達の費用 `u` と abort 1 回の
待ち以外の費用 `r` が backoff 量に依らない」という仮定と、別データの `r` にある。leader の backoff 更新
(`leaderBackoffWork`) が `BACK_OFF=1` 側でだけ走ること、abort ごとの関数呼出しと `rdtscp`、busy spin が
retry 頻度や cache に及ぼす効果は分離していない (§3)。abort 率の並びそのものを機序の説明とは呼ばない (§5)。

## 1. A-6 の値 (一次資料からの転記)

| cell | genome | 5 標本 (tps、記録順) | median | 母標準偏差 / median | abort 率 α | a = α/(1−α) | s = 48/T (µs/commit) |
|---|---|---|---:|---:|---:|---:|---:|
| `rr95-stock` | `BACK_OFF=0, BACKOFF_FIXED=-1` | 10365808, 10103030, 10029940, 10088796, 10073679 | 10,088,796 | 1.18% | 0.1547 | 0.1830 | 4.7578 |
| `rr95-fixed2` | `BACK_OFF=1, BACKOFF_FIXED=2` | 9753031, 9587735, 9488225, 9494008, 9505248 | 9,505,248 | 1.06% | 0.145 | 0.1696 | 5.0498 |

- 効果 = 9,505,248 / 10,088,796 − 1 = **−5.784%** (`certification.json` の `effects.rr95 = −0.0578`)。
- abort 率は campaign WAL の `bench_done.payload.leading_indicators.abort_rate` (perf build、集約 1 点) で、
  定義は `aborts / (aborts + commits)`。1 commit あたりの abort 回数は `a = α/(1−α)`。
- 実行 argv は WAL の `run_cmd` にある: `ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3
  -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio=95 -ycsb_rmw=0 -ycsb_max_ope=10`。
- 同 attempt の trace-enabled 正しさ走 (別 build、各 cell 5 回) の aborts/commits は stock 0.1771〜0.1792、
  採用版 0.1641〜0.1657。採用版/stock の比は trace 0.9265、perf 0.9267 で相対減少の向きと大きさが揃うが、
  絶対値は 3% 違う。**別 build の値なので perf build の集約 1 点の独立反復ではなく、相対減少の感度確認に留める。**
- 実行: `bnode031`、request `982234.nqsv`、2026-09-08 01:29〜02:42 JST、source `ae8a767eb`、pin `511c953`。

## 2. 近接条件の別実行 — B-10 read-heavy 本走の 3 block

B-10 read-heavy 正式系列 (`b10-backoff-shape-silo-read-heavy-formal-acf840c8`、job `977647.nqsv`、
`bnode088`、2026-09-05、source `2a338449b`、pin `511c953` + `patches/silo-backoff-fixed.patch`) は
`none` と `constant-mu2` を 3 block に含む。

| block | none median (cv) | constant-mu2 median (cv) | 効果 | a(none) 5 標本 | a(mu2) 5 標本 | backoff 呼出し (= abort 合計) | 要求待機量 / worker 時間 |
|---|---:|---:|---:|---:|---:|---:|---:|
| block-1 | 10,311,699 (0.95%) | 9,630,186 (0.28%) | **−6.609%** | 0.1827〜0.1840 | 0.1686〜0.1694 | 24,423,602 | 48.85 s / 812.9 s = 6.01% |
| block-2 | 10,179,288 (0.33%) | 9,631,925 (0.23%) | **−5.377%** | 0.1823〜0.1838 | 0.1688〜0.1696 | 24,440,757 | 48.88 s / 809.8 s = 6.04% |
| block-3 | 10,158,776 (0.34%) | 9,618,673 (0.18%) | **−5.317%** | 0.1824〜0.1835 | 0.1690〜0.1702 | 24,479,065 | 48.96 s / 809.5 s = 6.05% |

- 3 block の効果の平均は −5.768%。15 標本を束ねた median 比は −5.560%。
- A-6 の a (0.1830 / 0.1696) と B-10 の a (0.183 / 0.169) は 3 桁目まで一致する。この負荷では backoff 2 µs が
  abort を 7〜8% しか減らさないことが両実行で見える。
- `backoff_call_count` は record が持つ計数で、3 block とも abort 合計と一致する (呼出しは abort 経路からのみ)。
  `nominal_total_wait_us` は `呼出し × 2 µs` の**要求待機量**であり、rdtscp で目標 cycle まで回る spin の
  実時間ではない (実待ちは要求以上)。worker 時間 = 48 × 5 rep の walltime 合計 (walltime は 3.36〜3.40 s で
  extime 3 s より長い)。
- **3 block は同一 job・同一 node・同一 build の反復である。**「独立 3 回」でも「A-6 と合わせて 4 attempt」でもなく、
  実行機会は 2 つ (A-6 と B-10) である。

一致が確認できる項目と、確認できない項目:

| 項目 | A-6 | B-10 | 照合 |
|---|---|---|---|
| protocol / workload | silo / rratio 95 | silo / read-heavy (rratio 95) | 一致 |
| 2 genome | `(0,-1)` / `(1,2)` | `(0,-1)` / `(1,2)` + 共通 define | 一致 |
| 標本数 | 5 | 5 × 3 block | 一致 |
| CCBench pin / patch | `511c953` + fixed patch | `511c953` + fixed patch | 一致 |
| 実行 argv | WAL `run_cmd` に記録 (上記) | record に argv 無し、B-10 spec の 48 thread / 1M / zipf 0.9 / extime 3 と同値のはず | spec による一致、観測による一致ではない |
| node / 日付 | `bnode031` / 09-08 | `bnode088` / 09-05 | 異なる |
| source commit / build attempt / binary hash | `ae8a767eb` / A-6 staged 依存 | `2a338449b` / B-10 build 経路 | 異なる |
| 依存 (masstree / mimalloc) の版、`clocks_per_us` | A-6 は 2100 | 未記録 | 未照合 |

B-10 の block median は none で A-6 の 1.0127 倍、mu2 で 1.0128 倍と、両 arm がほぼ同じ水準だけ動いている。
**この 2 実行に限っては「絶対水準は約 1.3% 動き、比は 0.02 ポイントまで一致した」と言える。** 比の転移可能性一般の
証明ではない。

- 補助: thread-scaling 較正 (job `966607` / `966764`、2026-09-02、3 標本ずつ) の `zero-loop` (`BACK_OFF=1, FIXED=0`、
  呼出しは起きる) 対 `constant-mu2` は −4.57% / −4.99%。`zero-loop` は `none` と別点 (呼出し・`rdtscp`・leader work が残る)
  なので、0→2 µs の近傍感度確認としてのみ付記する。

## 3. 名目待機会計との整合 — なぜ 2 µs が 5.8% になるか

`output/insights/2026-09-07_backoff-tail-mechanism/README.md` の式 (1):

    s(b) = u + a(b) · (r + b)

`s = 48/T` は 1 commit あたりの 48 worker の集約時間、`a` は 1 commit あたりの abort 回数、`b` は静的 backoff 量 (µs)、
`u` は commit 到達の費用、`r` は abort 1 回の待ち以外の費用。**`a·b` の項は会計であり、仮説は `u` と `r` が `b` に
依らないことである** (同 README §0)。backoff はソース上 abort 経路からのみ 1 abort につき 1 回 `b` µs の spin として
入る (`cc/silo/transaction.cc` の `TxExecutor::abort()`、`patches/silo-backoff-fixed.patch` の静的枝)。

差分だけを見ると `u` は消える:

    Δs = a₂·b − (a₀ − a₂)·r

| 入力 | a₂·b | (a₀−a₂)·r | 予測 Δs | 実測 Δs | 予測効果 | 実測効果 |
|---|---:|---:|---:|---:|---:|---:|
| 会計項のみ (r = 0) | 0.3392 µs | 0 | +0.3392 µs | +0.2921 µs | −6.66% | −5.78% |
| 式 (1) の tail 6 点 fit、r = 2.836 (同 README §2 表) | 0.3392 µs | 0.0381 µs | +0.3011 µs | +0.2921 µs | −5.95% | −5.78% |
| 閉じた model H の 13 点 fit、r = 3.165 (同 README §4 表、H は確定した機序ではない) | 0.3392 µs | 0.0425 µs | +0.2967 µs | +0.2921 µs | −5.87% | −5.78% |

- 会計項だけで実測の差の 116% (時間差) を出し、`r` の項が 13〜15% を戻す。**一致の大部分は
  「abort 回数 × 名目 2 µs を数えたら差の大きさとほぼ同じだった」で説明され、`r` が担うのは小さい補正項の桁と符号までである。**
- 13 点 fit の b = 0 は `zero-loop` であって `none` ではないので、`none` への転移は直接検定していない。
- B-10 の 3 block に同じ差分式 (r = 3.165) を当てると予測 +0.293 / +0.294 / +0.297 µs、実測 +0.329 / +0.268 / +0.265 µs
  (ずれは約 10%)。要求待機量の占有率 6.0% は、A-6 の会計から出る `a₂·b / s₂ = 0.3392 / 5.0498 = 6.7%` と同じ桁にある
  (分母が walltime と 48/T で異なるので同一量ではない)。

**読み方。** read-heavy (rratio 95) でも zipf 0.9・48 スレッドでは attempt の 15% が abort する。1 abort あたり 2 µs の
固定待ちは abort 率を 15.5% から 14.5% へ 1 ポイントしか下げない。したがって名目待機 (0.17 回/commit × 2 µs ≈ 0.34 µs) を
ほぼ全額払い、節約 (abort 0.013 回/commit × 約 3 µs ≈ 0.04 µs) では回収できない。commit 1 回の集約時間 4.76 µs に対して
0.30 µs は 6% である。write-heavy で静的 backoff が throughput を上げるのは abort 率が 0.79 (b=0) から 0.39 (b=10) へ
大きく落ちるからで (`t2216_model_tail.json` の write-heavy 較正)、read-heavy では落とすべき abort が最初から少ない。
D1506 の「read-heavy の正直な答えは素のまま」は、この会計と大きさの桁まで整合する。

**分離していない項。** `BACK_OFF=1` 側では `leaderBackoffWork` (leader の `check_update_backoff` / `update_backoff`) が
静的枝でも走り、`none` では走らない。abort ごとの関数呼出しと `rdtscp` の費用、busy spin が retry 頻度・cache・共有資源に
及ぼす効果 (正負とも) も分離していない。静的枝は `Backoff_` の atomic load を実行しないので、それは候補ではない。
会計式の正本も convoy・cache 汚染・leader 更新の影響を排除していない。**名目待機会計だけで差の大部分を再構成でき、
追加の大きな正の費用を要求しない**、というのが言える範囲である。

## 4. 反復 attempt を行わない裁定と、その帰結

- 反復 attempt 1 回は約 73 分の計算ノード占有 (うち約 70 分が 48 スレッドの直列性検査) で、得られるのは同じ点の
  5 標本追加 (新しい raw・WAL・attempt identity・certification bytes) である。符号は近接条件の別実行と一致し、大きさは
  名目会計と整合するので、追加標本が結論の成立条件ではない (絶対規律 4・5)。
- 反復しても `a4_noise_floor_status` は `open` のまま (`orchestrator/campaign/paper_story_a2_certification.py` の
  producer が `"open"` を定数で書き、validator が `"open"` 以外を拒否する)。複数 attempt を集約する schema field も無い。
- **反復しないことで失うもの:** 別に schedule された attempt における符号と効果、すなわち attempt 間変動の観測。
  B-10 は build 経路と source が A-6 と違うので「A-6 protocol の再現」ではない。本稿はこの不確かさを残す。
- 反復を行う場合の手順は残しておく: 投入前に attempt ID・attempt 数 (各 5 標本)・停止基準
  (例: 効果の符号が 2 attempt 連続で一致したら停止) を事前登録として commit し、
  `orchestrator/campaign/paper_story_a6_certification.v2.json` の `tracked_destination` を新 leaf へ向ける
  (実装面なので Codex author、D95)。`canonical_policy_path` は shipped 2 path 以外の policy を拒否する。

## 5. A-2 結果稿の脚注との関係

`docs/paper-story/results/2026-09-07-a2-certification-reject.md` §3 の脚注は「abort 率は descriptive な集約 1 点で、
機序の同定にも使わない。backoff 有効側で abort 率が大きく下がりながら throughput も下がっている、という並びを機序の
説明として書かない」と定める。**本稿はこの禁止をそのまま維持する。** 本稿は abort 率から機序を同定しておらず、
集約 abort 率を条件にして名目待機会計との整合性を調べた事後検査である。§3 の数値 (0.3392 / 0.0425 / 0.2967 µs、−5.87%) は
その整合性検査の値であって、A-6 の機序説明として単独に立つものではない。残るのは throughput 差、ソース上の 2 µs 要求、
B-10 の別記録との整合である。A-2 (adaptive `BACK_OFF=1` の既定定数) と A-6 (静的 2 µs) は測った条件が違う。

## 6. 主張の上限

1. A-6 の abort 率は perf build の集約 1 点。trace build の 5 回は相対減少の感度確認で独立反復ではない。
2. `r` は read-heavy の別データ (tail 6 点 fit 2.836、閉じた model H 3.165) からの定数で、A-6 のデータでは当てていない。
   会計項だけで差の大部分が決まるので、`r` の値の選択は結論を変えない。
3. 会計式が無視する項 (§3 末尾) の寄与が無いことは示していない。残差が小さいという記述である。
4. B-10 の 3 block は同一 job・同一 node の反復で、独立な attempt ではない。B-10 record は実行 argv・依存版・
   `clocks_per_us` を持たず、A-6 との一致は spec による。
5. 性能値は非認証。A-6 の `reject` 判定は不変で、本稿はそれを追記で補うだけである (絶対規律 7)。

## 7. 段 3 敵対相談の所見と裁定

read-only codex 1 本 (レンズ A、`gpt-5.6-sol` / xhigh) が MF 6 件・SH 1 件を出し、全件 real・採用した。
初稿の「同条件で再現」「独立 3 回」「spin 時間の 6.0% を実測」「1.6% 一致で機序を確かめた」「A-2 の脚注は単独使用だけを
禁じた」「r=3.165 は式 (1) の fit」を、上の本文どおりに書き換えた。壊れなかったのは A-6 の負の効果、B-10 3 block の
同符号・同程度、名目会計が差の大部分を占めること、反復を行わない裁定である。逐語は wave の job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2430-a6-readheavy-mechanism/consult-a.md`、`s4-ruling.md`)。

## 8. 再現条件

| 項目 | 値 |
|---|---|
| A-6 生値 | `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/raw/rr95-{stock,fixed2}.json`、同 `campaigns/*/runs/wal.jsonl` |
| B-10 record | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-read-heavy-formal-acf840c8/runs/b10-backoff-shape-blocks/block-{1,2,3}--*--{none,constant-mu2}.json` |
| thread-scaling 較正 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/results/t2216_model_tail.json` の `calibrations.read-heavy.raw_cells` |
| 会計定数 | `output/insights/2026-09-07_backoff-tail-mechanism/README.md` §2 表 (read-heavy r=2.836) と §4 表 (u=4.102、r=3.165) |
| 解析 script | wave の job dir `analysis.py`、出力 `numbers.txt` (repo へは入れていない。u, r は定数として手入力) |
| 敵対相談 | 同 job dir `consult-a.md` (段 3、read-only codex 1 本)、裁定 `s4-ruling.md` |
