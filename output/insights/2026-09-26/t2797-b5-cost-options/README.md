# [T-2797] B-5 本走の計算費用を削る案の比較 — **ユーザー裁定待ち** (2026-09-26)

B-5 本走 (D2227 項 2 で認可、総 wall 上限 680.7 node 時間) をユーザーが「図 1 枚に 680 node 時間はありえない」と差し戻したのを受け、
費用を削る案を正しさの検査 (規律 2) を弱めずに比べた。**提示だけで、本走・校正・新規の本走 job は投げていない。**
依頼の逐語は `verbatim/request.md`。問いは §7 の 1 本。

## 0. この文書が主張すること・しないこと

- **主張する:** 中断中の本走 block 1 stage 1 (12 job) の台帳と NQSV の記録から、1 session・1 系列・1 job の所要と、その内訳 (検証・build・bench・LLM 待ち) を実測として固定した (§2)。
  それを登録の構成数 (117 job・1,773 session) へ掛けた換算と、案 (1)(2)(3) を当てた試算を、出所を分けて示す (§4)。
  現行の cohort `b5-registered-v1` は、report の規則のままでは 6 比較すべてがすでに判定不能 (欠測) になっていることを示す (§3)。
- **主張しない:** 見積りは上限の保証ではない。並列化の倍率は §4.2 の実測範囲の外では試算である。
  LLM の週上限に対して 1 週間に何機会回せるかは、他 session と共有の枠なので測れていない (§5)。統計の検出力は未知の効果と分散に依存し、ここでは p 値の解像度だけを示す。
  **規律 2 を緩める案は出していない** (legacy 1 本 + 性能 trace 5 本、anomaly 即 reject、bench の前に検証、は全案で不変)。trace 本数を減らす案は勧めない (依頼の指示、§4.4)。

## 1. 要約

- **費用の中身 (実測):** 中断中の本走 block 1 stage 1 の 12 job は計 126,426 s (35.1 node 時間)。非 LLM の完走 6 系列では計算の **95.0 %** が検証
  (trace 取得 + verifier + 周辺処理) で、build・bench は合わせて 5 % 前後。LLM 系列 4 job の 37,107 s のうち計算は 12,994 s で、残りは LLM の応答待ちと 429 後の時間切れ待ちだった。
  **read-heavy が重い:** 非 LLM 系列 1 本 26,191〜26,846 s (write-heavy 6,902 s、balanced 9,149〜10,076 s)。1 session 585〜2,289 s で、発効束 §10 の試算 (817〜1,007 s) の最大 2.3 倍。
- **登録どおりの換算:** 図 1 枚 (B-5 全体) で **503〜637 node 時間** (LLM 1 系列の機会数 10〜30)。発効束の上限 680.7 h と整合する。うち read-heavy が 290〜332 h、LLM 待ちが 67〜201 h。
- **案ごとの node 時間 (§4、表 4.0):** (1) LLM 待ちを node 外へ = 439〜446 h。(2) 取得済み trace の同時検査は単独で 307〜332 h。(1)+(2) = **251〜275 h** (うち read-heavy 165〜176 h)。
  (3) の縮小 (事前登録の改訂) を重ねると、n = 9 で ×0.75、read-heavy を外すと read-heavy 分 (約 6 割) が消える。
- **先に問うべき新事実 (§3):** 現行 cohort `b5-registered-v1` は、report の規則 (`orchestrator/campaign/b5_generator_contrast_report.py`) のままでは
  **6 比較すべてがすでに判定不能 (欠測)**。LLM 4 系列 (3 workload) が 429 による提案待ちの時間切れで score を持たず、write-heavy の random 2 系列は系列開始 stock の品質欠測で終わった。
  費用を削って v1 を続けるのではなく、**v1 を block 1 stage 1 で閉じて開示し、実行契約を直した新 cohort を登録し直すか**が先の判断になる。
- **LLM の週上限 (§5):** stage 1 は LLM 4 系列の並走で、提案機会を計 22 回終えた時点 (投入から約 2 時間) で週上限 (429) に達した。登録どおりの LLM 需要は 360〜1,080 機会で、node 時間より暦時間の律速になりうる。
- **勧め (§6):** (1) と (2) は統計を変えずに node 時間を削れる (規律 2 の検査対象・判定・bench 前の関門は不変)。(3) は統計の強さを落とすので、§7 の問いでユーザーが選ぶ。

## 2. 出発点の実測 (block 1 stage 1、2026-09-23 21:53 JST 投入)

一次資料は本走 wave の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-main-run/`、読むだけ) の台帳 `ledgers/b5-registered-v1/block-1/*/*/*/events/*.json`
(各 event の `timing` と `provenance.proposal_wait_wall_s`)、`evidence/.../job.stderr` の NQSV `Elapse`、`driver-state/b1-s1/*/a-*/out.json` (LLM 親の終了記録)。
抜き出した表は `data/b1s1-jobs.tsv` (job 12 行) と `data/b1s1-sessions.tsv` (session 110 行 + 却下 12 行)。**時間だけを抜き、候補値と throughput は載せていない** (§8)。

| workload | arm / 系列 | job Elapse (s) | 終了理由 | 評価数 B / 原提案 A | 計算の和 (s) | LLM 待ちの和 (s) |
|---|---|---:|---|---:|---:|---:|
| write-heavy | llm r01 | 9,426 | proposal-wait-timeout | 1 / 14 | 638 | 6,051 (+ 時間切れ 2,703) |
| write-heavy | random r02・r03 | 294・296 | stock-unestablished | 0 / 0 | 263・265 | — |
| write-heavy | sweep r04 | 6,902 | b-complete | 10 / 10 | 6,868 | — |
| balanced | llm r01 | 9,776 | proposal-wait-timeout | 5 / 6 | 2,489 | 4,550 (+ 2,703) |
| balanced | random r02・sweep r03・r04 | 9,565・10,076・9,149 | b-complete | 10 / 10 | 9,531・10,041・9,114 | — |
| read-heavy | llm r01・r02 | 8,898・9,007 | proposal-wait-timeout | 2 / 3 | 4,901・4,966 | 1,261・1,306 (+ 2,703 ずつ) |
| read-heavy | sweep r03・random r04 | 26,191・26,846 | b-complete | 10 / 10 | 26,158・26,812 | — |

- **1 session (評価 1 回) の所要:** write-heavy 236〜513 s、balanced 257〜757 s、read-heavy 585〜2,289 s。系列開始 stock は 251〜265 / 299〜310 / 713〜725 s。
- **性能 trace 1 本の区間 (trace 取得 + verifier + 周辺処理):** write-heavy 33〜93 s、balanced 37〜141 s、read-heavy 106〜455 s。backoff の小さい候補ほど commit が多く長い。
  endpoint の再計測 (score 5 session) は探索中の最速候補を測るので、その系列で最も長い session になりやすい (read-heavy で 1 session 2,184〜2,289 s)。
- **内訳の割合 (非 LLM の完走 6 系列):** 検証 84,117 s / 計算 88,524 s = 95.0 % (write-heavy 89.1 %、balanced 92.3 %、read-heavy 97.3 %)。build は 1 回 9〜18 s、bench は 16.7〜16.9 s。
  job Elapse と計算の和の差 (job の準備・後片付け) は 29〜35 s。
- **系列の構成比 (非 LLM、1 系列の計算):** stock 1 回 + 評価 10 回 + score 5 回が、write-heavy 251 + 4,069 + 2,548 s、balanced 305 + 5,536 + 3,721 s、read-heavy 721 + 14,607 + 11,157 s。
- **LLM 1 機会の待ち (採用 + 却下、429 の時間切れを除く 22 件):** 255〜1,021 s、平均 599 s、中央 473 s (write-heavy 平均 466、balanced 910、read-heavy 642)。
  LLM 親は login node で動くが、待つ間も series job が計算 node を確保しているので job Elapse に入る。
- **品質欠測:** 系列開始 stock 12 件中 2 件 (write-heavy random の 2 系列とも、settled = false)、評価 70 件中 3 件、score 30 件中 0 件。
  [T-2850] 試走でも stock session 12 件中 5 件が同じ型 (bench 直前の静定待ち「1 分 load ≤ 4.0 を 20 s まで」の時間切れ)。直列の検証の直後の load は 4.0 未満だったので、
  検証の余熱だけでは説明できず、原因は未確定 ([T-2850] insight §1)。
- **write-heavy の LLM 系列の却下:** 14 機会のうち 12 件が `proposal-rejected`。理由はどれも「coder の `data_boundary_report` が `instruction_like_content_detected=true` を申告し、
  K2 consumer の検疫 (`_consume_k2_coder_output`) が拒否」で、多くが critic 診断の recommend 項 3 の見出しを指摘していた。A を消費し B を消費しない (登録どおり)。
  この率が続けば、この系列は A = 30 を使い切っても評価が数件にとどまる。原因は本 wave では調べていない (scope 外、§6 の注)。

## 3. 新事実: 現行 cohort は 6 比較すべてが判定不能 (欠測)

- **429 の記録:** LLM 4 系列の親は 2026-09-23 23:50〜23:52 JST に `api_error_status: 429`、`result: "You've hit your weekly limit · resets Sep 26, 6am (Asia/Tokyo)"` で終了した
  (`driver-state/b1-s1/b1-*/a-*/out.json`)。series job は提案を 2,703 s 待って `proposal-wait-timeout` で系列を終えた (`b5_generator_contrast.py` の handshake 待ち)。
- **report の扱い:** `_project` は `endpoint-fixed` と score 5 session の無い系列を欠測 (`unclassified-missing` など) とし、比較の判定は欠測が 1 系列でもあれば
  `indeterminate-missing` を返す (同 file の判定部、事前登録 §7.4 手順 2)。LLM の欠測は 3 workload すべてにあるので、**6 比較 (3 workload × 2 baseline) すべてが判定不能**になる。
- **回復できない分:** write-heavy random の 2 系列は系列開始 stock の品質欠測 (`stock-unestablished`)。事前登録 §5.3 は品質欠測を retry せず fallback でも埋めないので、
  **write-heavy の LLM 対 random は、LLM 系列を再開しても判定不能のまま**である。
- **再開の解釈はユーザー判断:** 429 を §3.3 の機械故障 (「候補と独立な依存物の供給障害」) とみなして LLM 系列を再開する経路は実装に無い。
  再開すると、同じ stage の他 arm が終わってから数日後に系列の続きが走る。block の時間分離 (§7.1) の前提も崩れる。
- **帰結:** 残り 8 stage に費用をかけても、v1 cohort は結論を出せない (少なくとも write-heavy の 1 比較は確定で判定不能)。
  事前登録 §7.4 は「本 v1 の主 cohort は 1 回だけ」「失敗後の再発火を独立の成功機会として隠さない」と定める。
  したがって、どの削減案を採る場合も、**v1 を stage 1 で閉じた事実を開示したうえで、新しい cohort (v2) として登録し直す**のが素直な形になる。
  v1 のまま実行契約を途中で変えると、同じ系列番号の 3 arm が違う契約で測られ、対差に契約差が入る。

## 4. 案の比較

### 4.0 一覧 (図 1 枚 = B-5 全体の node 時間、`data/cost-model.txt`)

出所: **実測** = §2 の値、**換算** = 実測を登録の構成数 (各セル 12 系列、117 job、block stock 9 job) へ掛けた値、**試算** = 仮定を置いた値。
LLM 系列の計算部分は同じ workload の非 LLM 系列と同じと置いた (換算)。block stock job は stock session 5 回 + 35 s で置いた (換算、B-5 での実測なし)。

| 案 | node 時間 (h) | うち read-heavy | 統計への影響 | 必要な改訂 |
|---|---:|---:|---|---|
| 現行 (LLM 1 系列 10〜30 機会) | 503〜637 | 290〜332 | — | — |
| (1) LLM 待ちを node 外へ (評価ごとの job 分割) | 439 (全 arm を分割すると 446) | 269〜272 | なし (n・B・session・trace 不変) | 発効束の実行契約と launcher・driver の実装 |
| (2) 取得済み trace の同時検査 (実測: 記憶量の小さい trace は 5 本同時で比 0.24〜0.26、read-heavy の重い trace は 2 本同時で 0.53) | 307〜332 (LLM 30 機会なら 442〜467) | 183〜194 | なし | pipeline の検証経路の実装と、静定待ちの上限を 60 s 以上へ |
| (1) 全 arm + (2) | **251〜275** | 165〜176 | なし | 上 2 つ |
| (1) + (2) + (3a) n = 12 → 9 | 189〜207 | — | 最小 p が 1/512。Holm 初段を通るのは 9 対すべて正のときだけ | 事前登録の改訂 (新 cohort) |
| (1) + (2) + (3b) read-heavy を外す | 86〜99 | 0 | 主張が 2 workload に縮む。族は 4 比較 (Holm 初段 0.0125) | 同上 |
| (1) + (2) + (3c) B = 10 → 6 | 193〜212 | 128〜137 | 検定の解像度は不変。探索の深さが変わり、問いが「評価 6 回で」になる | 同上 |
| (1) + (2) + (3a) + (3b) | 65〜75 | 0 | (3a) と (3b) の両方 | 同上 |

### 4.1 案 (1) LLM の応答待ちを計算ノードの外へ出す

- **いま起きていること:** series job は系列の最初から最後まで 1 つの node を確保し、LLM 親 (login node) が次の提案を書くまで待つ。
  stage 1 の LLM 4 job では 37,107 s のうち約 24,100 s (65 %) が待ちで、write-heavy では job の 93 % だった。
- **事前登録との関係:** §4.1 の運用契約は「各評価は `p3_s4_loop` の単回評価を fresh layout で 1 回呼び出す」。同機体・同 job を要求するのは
  §5.4 の「系列開始 stock と最初の評価」だけである。§11 は「親の待機、LLM の時間・費用は別欄に記録する」としている。
  したがって案 (1) は事前登録の改訂ではなく、**発効束の実行契約 (job の切り方、提案待ちの上限 2,700 s) の改訂**で足りる。発効束の改訂なので、ユーザーの承認 (再発効) は要る。
- **形 (1a、勧め):** job 1 = 系列開始 stock + 評価 1 (§5.4 どおり同 job)、job 2〜10 = 評価 1 回ずつ、job 11 = score 5 session。提案待ちは job の外 (login node の driver) に置く。
  - 削れる量: LLM 待ちの全部 = 67 h (10 機会) 〜 201 h (30 機会)。足す量: job の準備 35 s × 10 回 × 36 系列 = 3.5 h。
  - **対称性:** LLM arm だけを分割すると、LLM arm の endpoint 選択 (探索中の最大 throughput) だけが node 間の差を含む。
    random・sweep も同じ切り方にすれば、この差は全 arm に等しく入る (+7 h)。本 wave はこちらを勧める。
  - **429 への強さ:** 上限に当たっても node 時間を消費しない。系列は待つだけで、欠測にならない (提案待ちの上限を外すか、429 を §3.3 の機械故障 retry として扱う規則を v2 に書く)。
    ただし stage は LLM 系列が終わるまで閉じないので、暦時間は上限の解除まで延びる。
  - **増えるもの:** job 数が 117 → 約 1,200 (全 arm 分割時)。queue 待ちが評価ごとに入る (stage 1 では投入から系列開始まで約 35 s だった。混雑時は未測定)。
- **形 (1b、代案):** 1 job に LLM 系列を 2 本相乗りさせ、評価 1 回 (build・検証・bench) の全体を node 内の lock で直列にする。系列は 1 node に留まるが、
  write-heavy は評価 (約 420 s) が待ち (約 470 s) より短く隠しきれない。429 では相乗りの両系列が node を握ったまま止まる。実装も (1a) より大きい。勧めない。

### 4.2 案 (2) 検証の並列化

- **いまの実行 (コードの事実):** 評価 1 回の検証は legacy 1 本 → 性能 5 本を完全に直列で回し、各本は「trace 取得 (trace-enabled build を 1 回実行) → verifier」を
  同じ関数で順に行い、anomaly が出たらその場で reject して bench へ進まない (`orchestrator/campaign/pipeline.py` の `_run_one_pass`・`_execute_verification_repetition`・`evaluate`)。
  別 host へ散らす既存経路 (`_run_fanout_pass`) は B-10 系の generator 専用で B-5 からは届かない。届いても node 時間は減らない (使う node が増えるだけ)。
- **worker 数を増やす案は効かない (既存の実測):** verifier の worker 数は既定で `min(file 数, affinity, 16)` (`orchestrator/verifier/parse.py`)。
  D1553 の実測で 8 → 21.44 s、16 → 19.49 s、48 → 19.60 s と 16 で飽和している。閉路検出 (Tarjan SCC) と分類は 1 process のまま残る (`orchestrator/verifier/dsg.py`)。
- **効く形 = 取得済み trace の同時検査:** trace 5 本の**取得は今どおり直列・専有**で行い (取得中に他の負荷を載せると interleaving が変わり、検査対象そのものが変わる)、
  取得が済んだ 5 本の**検査だけ**を同時に走らせる。5 本すべてが通るまで bench へ進まない関門 (`evaluate`) は変えない。
  検査する trace・verifier・判定は同じなので、規律 2 の検査対象と判定は変わらない。失うのは「1 本目で anomaly が出たら残りを検査しない」早期打ち切りで、これは費用の差だけである。
- **実測 ([T-2850] session の script が計算 node で測定。最後の行の 1 job だけ本 wave の枠で数える):** trace は性能構成 (100 万レコード・48 thread・3 s) で直列に取得して残し、
  同じ verifier argv (worker 既定 16) で「1 本ずつ」と「同時」を測った。判定・取引数・辺数・閉路数は全行で直列と同時が一致し、OOM は 0。

| trace (代理を含む) | 1 本の取引数 | 直列 | 同時 | 比 | node 記憶量の最大 | 出所 |
|---|---:|---:|---:|---:|---:|---|
| write-heavy stock | 107〜113 万 | 5 本 177.6〜177.8 s | 5 本同時 42.8 s | 0.24 | 15.6 GiB | [T-2850] insight §3.2 |
| write-heavy B0-L-W0 (重い候補の代理) | 235〜238 万 | 5 本 396.8 s | 5 本同時 95.0 s | 0.24 | 27.4 GiB | 同上 |
| read-heavy stock | 552〜563 万 | 5 本 640.5 s | 5 本同時 166.2 s | 0.26 | 67.8 GiB | 同上 (生データを本 wave で検算) |
| read-heavy B0-L-W0 (重い候補の代理) | 1,689〜1,700 万 | 4 本 1,716.5 s (1 本 最大 RSS 41.1〜41.4 GiB) | 2 本同時 × 2 巡 907.2 s | 0.53 | 85.6 GiB | `vprobe/runs/vp-rh-b0lw0-c2/probe.json` (bnode099、job Elapse 2,899 s = 0.81 node 時間、本 wave の枠) |

  read-heavy の重い trace を 3 本同時にすると RSS が約 124 GiB で node の利用上限を超えるので測っていない。B-5 本走の read-heavy 候補は性能 trace 1 本 最大 455 s で、この代理 (1 本 約 430 s) と同じ重さである。
  候補そのもの (hole code の backoff) の trace では測っていない ([T-2850] insight §5 と同じ限定)。
- **B-5 への換算 (`data/cost-model.txt`):** 本走 stage 1 の session ごとに、性能 trace の区間から記憶量を RSS ≈ 40 GiB × 区間 / 418 s で見積もり (代理 2 点と整合)、枠 100 GiB で同時本数を決め、
  並列化しない部分 (1 本 3.4〜12 s、[T-2850] §4 の楽観 / 保守) を直列のまま残し、達成率 (5 本同時 0.77〜0.83、2 本同時 0.90〜0.95) と冷却 60 s を当てた。
  1 系列の計算は write-heavy ×0.51〜0.60、balanced ×0.44〜0.51、read-heavy ×0.60〜0.65 になる。read-heavy は重い候補が 2〜4 本同時に限られるので効きが小さい。
- **制約:** read-heavy の候補は検査 1 本の最大 RSS が約 40 GiB で、node の利用上限 (約 115 GiB) から同時 2 本までになる ([T-2850] session の連絡値)。
  5 本を 2 + 2 + 1 の 3 巡で回すので、read-heavy の検査の短縮は理想でも 5/3 倍までで、実測の達成率 (2 本同時で理想の 0.95) を当てると約 1.58 倍になる。利用上限 115 GiB は D1553 の記録。10 s trace では 16 worker の fork が copy-on-write で node の記憶量を使い切った先例 (D2160 項 4、原因は D2181 で除去) があり、同時検査の本数は記憶量で決まる。
- **静定待ちとの干渉:** 同時検査は bench 直前の load を上げる。いまでも静定待ち (20 s) の時間切れで品質欠測が出ている (§2) ので、同時検査を入れるなら検査後の冷却時間を実行契約に足す必要がある。
  実測: 同時検査の後に load1 が 4.0 以下へ戻るまで、rh stock の 5 本同時で 61 s、wh B0-L-W0 の 5 本同時で 39 s、wh stock で 3〜23 s、rh の重い trace の 2 本同時では待ち不要 (直後 1.96)。換算では全 session に 60 s を足した (保守側)。品質欠測は §7.4 で比較を判定不能にするので、費用より重い。
- **実装の置き場:** 検証経路 (正しさの関門) の変更なので、Codex author の実装・敵対レビュー・直列と同時で判定が一致することの正例 / 負例 (anomaly を含む trace で reject が保たれる) を要する。
  v1 の途中から変えると同じ cohort 内で検証の形が混ざるので、新 cohort から当てる。

### 4.3 案 (3) 系列数・候補数の縮小 (事前登録の改訂、ユーザー判断)

事前登録 §11 は「n = 9 などの縮小案は本 v1 に無い。採るなら主 cohort の結果を見る前に別仕様として固定する」と定める。v1 は block 1 stage 1 の結果が出ており、
本走 wave と本 wave がその一部を見ている (§8)。したがって縮小は **v2 の別仕様**として、閲覧済みの範囲を既知結果台帳に書いたうえで固定する。

| 縮小 | node 時間への効き | 統計の強さ (片側 exact 符号反転、Holm、family-wise α = 0.05) | 変わる主張 |
|---|---|---|---|
| (3a) n = 12 → 9 (3 block × 3 系列) | 全体 ×0.75 | 12 対: 11/12 正で p = 0.0032 (初段 0.0083 を通る)、10/12 で 0.0193 (通らない)。9 対: 9/9 正で 0.0020 (通る)、8/9 で 0.0195 (通らない)。**1 系列の負けも許さなくなる。** 副解析 (fallback 対を除く) の下限 6 対まで、除ける対が 6 → 3 に減る | なし (精度が落ちる) |
| n = 8 以下 | ×0.67 以下 | 8 対: 8/8 正で 0.0039、7/8 で 0.0352。3 block に均等に割れない。n = 6 は 6/6 正でも 0.0156 で初段を通らず、**優越を言える見込みが無くなる** | — |
| (3b) read-heavy を外す | read-heavy 分 (約 6 割) が消える | 族が 4 比較になり Holm 初段は 0.0125。残る比較の強さは変わらない | 主張が write-heavy・balanced の 2 workload に縮む |
| (3c) B = 10 → 6 | 探索部分 ×0.6 (全体で約 −22 %) | 検定の解像度は不変 | 問いが「評価 6 回で」に変わる。探索が浅くなり、差 (効果) が縮みうる。D39 決定 2 から継いだ「10」を離れる |

LLM の需要 (§5) は n と workload 数に比例して減る。n = 9 で ×0.75、read-heavy を外すと ×0.67。

### 4.4 勧めない案 (依頼の指示と規律 2)

- **trace 本数を減らす案** (score 5 session の検証を探索時の検証で代用する、同じ候補値の再検証を省く、trace の extime・thread を縮める):
  計算の 37〜42 % は score の 5 session で、そのほぼ全部が検証なので効き目は大きい。しかし各 session の前に検証を通す事前登録 §5.5 と、anomaly を拾う機会の数を減らす。依頼どおり勧めない。
- **verifier の判定や経路を軽くする案**、**性能を理由にした早期停止** (§3 が禁じる): 採らない。
- **別 node へ検証を散らす案:** 所要は縮むが node 時間は減らない。

## 5. LLM の週上限 (429) と暦時間

- **実測:** stage 1 は LLM 系列 4 本が並走し、2026-09-23 21:58 の最初の起動から 23:50 の 429 まで (約 1.9 時間) に提案機会を計 22 回終えた。
  そこで週上限に当たり、解除は 9 月 26 日 6 時 (JST) と表示された。週上限の枠はアカウント内の他 session と共有なので、**B-5 に 1 週間で何機会回せるかは測れていない。**
- **使用量の伸び:** 親は機会ごとに `--resume` で同じ session を続けるので、読み込む文脈 (cache read) が機会ごとに約 0.45 M token ずつ増える
  (write-heavy 系列: 1 機会目 2.0 M → 13 機会目 7.5 M、累積 62.5 M)。出力は 1 機会約 3.5 万 token でほぼ一定。
  429 までの stage 1 の総使用量は出力 1.14 M token・cache read 114 M token (`out.json` の `modelUsage`)。`total_cost_usd` は従量換算の目安で、請求額ではない。
- **登録どおりの需要:** 36 系列 × 10〜30 機会 = 360〜1,080 機会で、stage 1 の 22 機会の 16〜49 倍。機会数を write-heavy 系列の伸びで数えると、
  cache read は 10 機会止まりで stage 1 の約 14 倍、30 機会まで伸ばすと 1 系列約 260 M・全体で約 80 倍 (試算)。
- **案ごとの 429 の扱い:**

| 案 | 429 に当たったとき | 暦時間 |
|---|---|---|
| 現行 | 走行中の LLM 系列が 2,703 s 待って欠測で終わる (stage 1 で 4 系列)。node は待つ間も消費。比較は判定不能へ | 9 stage × 最長 job (read-heavy LLM 系列 9.1〜12.7 h) + block 間 2 h ≈ 3.5〜5 日 (queue と 429 を除く) |
| (1a) | node を消費しない。系列は解除まで止まり、欠測にならない (v2 に規則を書く) | LLM の枠が律速。1 週で回せる機会数に比例して延びる |
| (2) | 現行と同じ (待ちは node 上に残る) | 計算部分が縮む (read-heavy の非 LLM 系列 7.4 h → 4.5〜4.8 h) |
| (3a) / (3b) | 需要が ×0.75 / ×0.67 | 同じ比率で縮む |

## 6. 勧め

1. **v1 を block 1 stage 1 で閉じ、開示する** (§3)。消費は 35.1 node 時間。結果は主標本に入れず、閲覧の事実を既知結果台帳へ残す。
2. **v2 の実行契約に (1a) を全 arm へ当てる** (LLM 待ち 67〜201 h を node から外し、job 分割の準備 +10.5 h を足す)。統計は変わらない。429 で系列が欠測にならない規則も同時に書く。
3. **(2) の検査の同時実行を入れる** (§4.2 の実測で判定一致と冷却時間を確かめたうえで)。統計は変わらない。
4. **(3) はユーザーが選ぶ** (§7)。(1) + (2) だけでは 251〜275 h で、図 1 枚あたり百時間級が残る。残りの約 2/3 は read-heavy で、その重い trace は記憶量のために 2 本までしか同時に検査できない。
5. 注: write-heavy の LLM 系列の却下 (§2) は、B-5 を v2 で走らせる前に原因を確かめる必要がある (このままだと LLM arm が write-heavy で「生成不成立」になりやすい)。本 wave の scope 外なので調べていない。

## 7. ユーザーへの問い (**ユーザー裁定待ち**)

B-5 は、v1 を stage 1 で閉じて v2 として登録し直し、(1) LLM 待ちを node 外へ出す・(2) 検査の同時実行、を実装したうえで、次のどの規模で走らせますか。

| 択 | 規模 | node 時間 (図 1 枚) | 統計の強さ |
|---|---|---:|---|
| A | n = 12・3 workload (登録どおりの規模) | 251〜275 | 現行どおり (11/12 正で Holm 初段を通る) |
| B | n = 9・3 workload | 189〜207 | 9/9 正のときだけ初段を通る |
| C | n = 12・write-heavy と balanced の 2 workload | 86〜99 | 現行どおり。主張は 2 workload |
| D | B-5 を見送る (v1 の stage 1 は開示して閉じる) | 0 (実装費も不要) | — |

どの択でも、実装 (launcher・driver の job 分割、検証の同時実行) は dev-wave 2 本程度 (各 2 node 時間未満の検査) と、v2 の事前登録・発効束の作り直しが先に要る。
本 wave は (A)〜(C) のどれでも使える材料までで止め、実装は起票しない。

## 8. 既知結果の閲覧 (事前登録 §8 の差分台帳へ)

- 閲覧者: 本 wave の親 (Claude)。閲覧時点: 2026-09-26 14:07 JST (集計出力の mtime) 前後。対象: `b5-registered-v1` block 1 stage 1 の全 12 系列の台帳 event。
- 見たもの: 各 session の所要・品質・終了理由に加え、**候補値 (探索中の v と endpoint の v)** を集計の出力で見た。throughput は balanced の LLM 系列の評価 1 件
  (event 000008) の bench payload を 1 回見た。score の集計、系列間・arm 間の比較はしていない。
- 本文書の設計選択 (案と規模) は所要時間だけから作り、throughput は使っていない。ただし所要は候補値と相関する (backoff の小さい候補ほど検証が長い) ので、完全に結果から独立だとは言わない。

## 9. 一次資料と計算の方法

- 台帳・Elapse・LLM 親の終了記録: §2 の path (本走 wave の job dir、読むだけ)。
- 抜き出しと換算は repo 外の使い捨て script (本 wave の job dir `dev-wave-jobs/dev-wave-t2797-b5-cost-options/` の tmp) で行い、出力だけを `data/` に置いた。
  換算式: 1 系列の計算 = 同 workload の非 LLM 完走系列の job Elapse の平均 (B を変える案では評価 10 回分を B / 10 倍) × 案 (2) の比
  (案 (2) なしは 1。ありは §4.2 の session 別換算で得た workload 別の比を、楽観と保守の 2 通りで掛ける)。
  LLM 系列 = それ + 機会数 × 同 workload の平均待ち (案 (1) では待ちを除き、job 分割の準備 35 s × B を足す)。
  block stock = (stock session 平均 × 5 × stock の比 + 35 s) × 3 block。全体 = Σ_w [n × (3 arm の系列の和)] + block stock。
  write-heavy の非 LLM 完走系列は 1 本だけ (random 2 本は stock で終了) なので、write-heavy の値は 1 標本の換算である。
- 事前登録: `docs/b5-generator-contrast-preregistration.md` §3・§4.1・§5.3〜§5.5・§6・§7・§11。発効束: `output/insights/2026-09-22/t2797-effect-bundle/README.md` §6・§7・§10。
- [T-2850] の値 (試走 block 1 の評価内訳、検査の同時実行の実測): 着地済みの `output/insights/2026-09-26/t2850-trial-pause-cost-options/README.md` §2〜§3 (main `f5c7374ae`)。
  read-heavy の重い trace の同時 2 本は本 wave の枠で同 session の script が測った (生データ `dev-wave-jobs/dev-wave-t2850-trial-run/vprobe/runs/vp-rh-b0lw0-c2/probe.json`)。
