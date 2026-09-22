# [T-2853] 再現パッケージの初段 — 公開対象ごとの trace 量と保存費の見積り、再実行の 3 経路 (計算なし)

- 作成: 2026-09-22 JST。wave `worktree-dev-wave-t2853-repro-package-estimate` (背景 job)、着手時の基準 = local main `8fd2a2f5c`、
  記録前に local main `ad4bd2bb7` へ fast-forward した (取り込んだ変更は他 wave の記録と D2219 で、本文の実測値に影響しない)。
- 依頼の逐語と T-2853 の起票本文: `verbatim/request.md`。根拠の裁定: D2212 項 4・項 6、D320。一次資料: `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P6。
- 段 3 相談 2 本 (決定レンズ / 攻撃レンズ) の逐語は `verbatim/s3-consult-A.md`・`verbatim/s3-consult-B.md`、親の計画 v1 は `verbatim/plan-v1.md`、
  段 4 裁定は `verbatim/s4-ruling.md` (訂正は §12 の erratum)、段 6 レビューは `verbatim/s6-review.md`。本文の方針 (§7・§8) は段 4 裁定の結論で、ユーザー裁定ではない (「裁定へ返す」は採らない運用、相談を経た親の決定)。
- 実測 log (逐語) は `verbatim/*.log`。集計に使った script は repo 外の job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-repro-package-estimate/` に置き、
  repo へは入れていない (実装面にしないため)。sha256 は §13。

## 0. 結論

1. **一次資料 P0 の「balanced 10 秒で 32 GiB、read-heavy 6 秒で約 81 GiB」は trace の量ではなく verifier のメモリ使用量のピークである。** trace file の量は
   balanced 10 秒で 2.63〜5.49 GiB、read-heavy 6 秒で 4.18〜11.89 GiB (§3、§4、保全 2 系列の実走の範囲)。
2. **現行の標準評価経路は検証のたびに trace を消す。** 本 wave が調べた範囲 (評価経路のコード、job dir の保全 2 系列、repo の追跡 file) で原本を確認できたのは、
   repo 外 runner が zstd で保全した 2 系列 (D2160 検証相 64 走、B-8 30 走) の計 78,421,191,580 B (78.42 GB) と、追跡下の旧形式 trace 4 file (119,606,673 B) である。
   S-1a の 324 件検証、B-5 試走、K2 手動 loop などは `pipeline.evaluate` を通っており、今回の調査では原履歴を確認できず、現時点で公開対象に含められない (§4.3)。
   他の保存経路・複製の不在は調べていない。
3. trace 以外の公開対象 (コード・生成パッチ・入出力・探索設定・実験データ・図表) は、repo の追跡分を全部数えても約 0.97 GB (うち追跡下の生 trace 約 0.12 GB) で、MB〜GB 級に収まる。
   量を支配するのは trace で、今後の実験では B-5 型の完走評価 1 件あたり保存 (zstd) 1.43〜3.19 GiB という条件付きシナリオ値になる (§5、§6)。
4. **保存・公開の方針 (段 4 の決定):** 今後の論文根拠の実験は作業保管を全量 (zstd) で残し、公開は主張の役割で分ける — 検証が主題の実験と anomaly を
   検出した反復は全 trace、探索比較の certified 反復は標本 + 判定要約の全件。**この方針で EA&B の要件を満たすかは未確認** (規定は保存粒度を定めていない) (§7)。
5. **再実行は 3 経路に分ける:** R1 再判定 (保存 trace を verifier に掛け直す)、R2 再実行 (保存候補を LLM なしで動かし新しい履歴を検証・計測する)、
   G 再生成 (同じ探索設定で LLM に候補を作り直させる)。R2 は原判定の再確認ではなく新しい有限履歴の判定である (§8)。
6. 保存費の金額は未確認 (取得した公式ページに料金の記述が無い)。容量は公開アーカイブ Zenodo の 1 レコード上限 (100 file・50 GB) を単位に数えると、
   既存 2 系列は 2 レコード、B-5 型 480 件の全量は 14.8〜32.9 レコード相当 (§5.2、§6)。

## 1. 範囲と言わないこと

- 計算ノードは使っていない。login での `du` / `ls` / JSON の集計 / `check_quota` / `zstd -dc` の先頭読み、既存記録の読取、公式ページの取得だけである。
- 実験の再走・公開そのもの・gate / 検査 / 台帳の追加・凍結 chain は scope 外。欠け部品 (§11) は列挙だけで実装しない。
- trace 容量の新規実測 (P0 の容量測定) は [T-2847] の担当で、本稿は既存記録と保全済みの記録からの換算に留める。
- §6 の数値は **Silo・YCSB・48 thread の 2 系列から作った条件付きシナリオ値**であり、上下限でも予測区間でもない。MOCC・TPC-C・関数単位の候補 (P1) の
  trace 率は未測定である。
- 本稿は保存方針と再実行経路の設計であって、パッケージが EA&B の要件を満たすことの証明ではない。

## 2. 外部条件 (2026-09-22 08:5x JST 取得、逐語抜粋は `verbatim/web-evidence.md`)

| 項目 | 内容 | 出所 |
|---|---|---|
| EA&B の公開義務 | "required to make available all experimental data and related software (there are no excuses)"、再現性委員会の評価を受ける | https://www.vldb.org/2027/submission-guidelines.html |
| 時期 | Vol.20 は初回投稿時点で "a link to the full reproducibility package of all experiments, data, and artifacts with meaningful instructions on how to run the experiments" が必須 | 同上 |
| 置き場 | 恒久性のある公開アーカイブ (例: 公開 GitHub)。個人 web サイト不可 | 同上 |
| 容量・形式・匿名性 | 取得した本文に記述なし (追加の Web 検索でも見つからない) | 同上、https://vldb.org/2027/call-for-research-track.html |
| EA&B の貢献の例 | "reusable artifacts such as benchmark suites or traces" | call for research track |
| Zenodo | 1 レコード 100 file・合計 50 GB (50,000,000,000 B)、20 file 超は ZIP 推奨、アカウントに追加 150 GB の配分枠。料金の記述なし。1 レコード最大 200 GB への増枠は二次情報のみで**未確認** (公式ページが 404) | https://help.zenodo.org/docs/deposit/manage-files/、…/manage-quota/ |
| GitHub | 1 file 100 MiB で拒否、50 MiB で警告、repo は 1 GB 未満推奨・5 GB 未満を強く推奨 | https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github |

## 3. 前提の訂正 — 32 / 81 GiB はメモリであって trace の量ではない

一次資料 `gap-analysis.md` §4 P0 の「balanced 10 秒で 32 GiB、read-heavy 6 秒で約 81 GiB、ノード上限約 115 GiB」の GiB 値は、
`output/insights/2026-09-20/verifier-capacity/README.md` §4 の表で改修後 verifier の **node peak メモリ** (balanced 10 s 32.4 GiB、read-heavy 6 s 81.2 GiB) に当たる。
同じ trace の file 量は §4.2 の表のとおり (balanced 10 s 5.29〜5.49 GiB、read-heavy 6 s 11.1〜11.9 GiB、どちらも D2160 の候補)。
「ノード上限約 115 GiB」は verifier のメモリの制約であり、公開量の制約ではない。

## 4. trace の現況

### 4.1 標準経路は検証後に削除する

- `orchestrator/campaign/pipeline.py` 2160 行で 1 反復ごとに一時 dir (`izanagi_eval_trace_`) を作り、2178 行の `finally: shutil.rmtree(tdir, ...)` で検証後に消す。
  現行の標準経路には圧縮・保全の仕組みが無い (過去の全版の挙動は本 wave では遡っていない)。
- 例外は repo 外 runner (`verify_phase_runner.py`、job dir 保管) が verifier 起動前に全 trace を inventory (file 別 sha256 / bytes / 行数) し、
  `zstd -T0 -3` で job dir へ保全した 2 系列だけである (`output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` §4 の保全の行、
  `output/insights/2026-09-21/t2807-b8-effective/README.md` の保全量の行)。

### 4.2 保全 2 系列の集計 (preservation.json 記録の集計、log は `verbatim/preserved-traces-aggregate-*.log`)

集計は各走の `preservation.json` に記録された原本 bytes・行数・保存 bytes の和である。圧縮 file の完全性・復元可能性は検査していない。
保存 bytes の合計は既存記録 (§4.1 の 2 本の insight) と一致する。run dir 全体の `du -sb` (`verbatim/du-jobdirs.log`) は trace 以外の file も含むので、
保存 bytes より D2160 で 8,829,362 B、B-8 で 4,486,254 B 大きい。

| 系列 | 走 | file | 原本 B | 保存 B (zstd -3) | 圧縮率 | 1 行 | du -sb (job dir 側) |
|---|---:|---:|---:|---:|---:|---:|---:|
| D2160 検証相 (候補 fixed-5 / fixed-10、`dev-wave-verify-phase-adopted-backoff/run`) | 64 | 3,072 | 213,338,672,445 | 48,928,578,277 | 4.360 | 32.35 B | 48,937,407,639 (run) |
| B-8 (S-1 最終候補、`dev-wave-t2807-b8-effective/run`) | 30 | 1,440 | 133,510,417,298 | 29,492,613,303 | 4.527 | 32.98 B | 29,497,099,557 |
| 計 | 94 | 4,512 | 346,849,089,743 | **78,421,191,580** (78.42 GB) | | | |

1 走あたり (中央値、GiB):

| workload | D2160 3 s 原本 / 保存 | D2160 6 s / 10 s 原本 | B-8 10 s 原本 / 保存 | 圧縮率 (両系列) |
|---|---|---|---|---|
| write-heavy | 0.922 / 0.149 | 1.870 / 3.139 | 3.153 / 0.497 | 6.19〜6.35 |
| balanced | 1.565 / 0.354 | 3.187 / 5.392 | 2.655 / 0.593 | 4.42〜4.52 |
| read-heavy | 5.758 / 1.414 | 11.499 / (10 s は無し) | 7.157 / 1.774 | 4.03〜4.07 |

- 1 秒あたりの原本は write-heavy 約 0.31 GiB (両系列同じ)、balanced 0.27 (B-8) 〜 0.52 (D2160)、read-heavy 0.72 (B-8) 〜 1.92 (D2160) GiB。
  **同じ workload でも候補の処理量で 2〜2.7 倍振れる。** 圧縮率はこの 2 系列では workload ごとに近い値だった (表の範囲は workload × 秒数ごとの中央値の範囲で、
  個別の走には read-heavy 4.08 もある。他のプロトコル・異常候補への一般化はしない)。
- 条件はどちらも Silo・48 thread・YCSB zipf 0.9・trace 有効 build (規律 1 の検証用 build)・Pegasus 計算ノード。
- 判定の要約は result.json 45,636〜54,933 B/走、verifier.json 最大 1,268 B/走。**D2160 の 10 s 校正 4 走 (両候補の balanced と write-heavy) は
  verifier.json が 0 B** (旧 verifier が timeout / kill で完走しなかった indeterminate の走、`verify-phase-adopted-backoff/README.md` §5.1・§5.3)。
  保全の成功と判定の取得は別である (保全 64 走に対し判定集合は 60 件)。

### 4.3 trace の形式と、原履歴を失った範囲

- 形式は text 1 event 1 行。Silo は `external/ccbench/cc/silo/transaction.cc` 594〜605 行で 7 項目の commit 行
  `C <txid> <thid> <epoch> <tid> <read_count> <write_count>` (v2) を直接出す。`include/trace.hh` 78 行の 5 項目 `emit_commit` (v1) は SI 用に残っている。
  現行 parser (`orchestrator/verifier/parse.py` 323 行付近) は 5 項目の C 行を拒否する。保全 2 系列の実物は 7 項目 (親が `zstd -dc` で先頭を確認)。
- 追跡下の生 trace 4 file (`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/traces/`、119,606,673 B、
  2026-07-29 の劣化梯子 rung 1 特性評価) は 5 項目の C 行 (v1) で、**現行 verifier では再判定できない** (当時の道具が要る実例、§8.1)。
- **原履歴を確認できない範囲:** 一時 dir の作成と検証後の削除は、`pipeline.py` の初版 `181a30e75` (2026-06-19、134 行と 164 行) と現行版 (2160 行と 2178 行) の
  両方にある。`git log -S` では `izanagi_eval_trace_` と `shutil.rmtree(tdir` の出現数が変わった commit は初版の 1 件だけで、それ以外に出現数の変更は検出されなかった。
  これは文字列の出現数の確認であって、全中間版の実行挙動 (条件分岐・呼出経路・別の保全処理) や別コピーの不在を証明しない。
  この範囲で `pipeline.evaluate` を通った系列の例: S-1a (324 件の検証、全件 certified・anomaly 0。内訳は legacy 306 件 + s2 18 件 — floor / block1 / block2 は
  session ごとに legacy 1 件、develop は 18 cell ごとに legacy と s2 の 2 件、`docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md` §1.4)、
  B-5 試走 (53 session、`p3_s4_loop` 経由)、K2 手動 loop (3 件。campaign 原本も 2026-09-20 に cleanup の worktree 撤去で失われた、F1034)。
  **今回の調査ではこれらの原履歴を確認できず、現時点で公開対象に含められない。** 公開できるのは判定の要約・WAL・計測値・再実行手順である。
- P2-5 は既存評価の再生 (「replay = 新規計測ゼロ」、`docs/paper-story/2026-09-21c.md` 481 行) で、それ自身は trace を生んでいない。入力になった評価や
  静的 backoff の sweep (旧 linux-baremetal 機) など、個別の系列の trace の保存状況は本 wave では確認していない。

## 5. 公開対象 6 種の量と保存費

### 5.1 対象別の表 (実測は 2026-09-22 09:3x〜09:4x JST、`verbatim/repo-sizes.log`・`verbatim/du-jobdirs.log`)

| 対象 | 現存量 (出所) | 将来量の仮定 | 未集計の範囲 |
|---|---|---|---|
| (a) コード | izanagi の追跡 file のうち output/・docs/ 以外 1,416 本 50,054,091 B (実測)。CCBench submodule の追跡 405 本 12,030,047 B (調査子の実測)。docs/ 1,750 本 61,828,160 B (実測)。git の pack 約 508 MiB (調査子の実測) | 実験系列ごとに当時のコード一式を同梱する場合、系列数 × 約 62 MB (izanagi のコード + CCBench、履歴なし)。同じコードを使う系列は共用する (§8.2) | 系列ごとの checkout の数、repo 外 runner・依存物の量 |
| (b) 生成パッチ | `patches/` 36 file 284,375 B (実測、`verbatim/repo-sizes.log`)。うち .patch 34 本 209,398 B (最小 497 B、最大 86,001 B、平均約 6.2 KB、`verbatim/patches-sizes.log`)。`patches/README.md` の分類と file 名から、赤検出用の意図的な壊し (broken-\*)、検証計装 (instr-\*)、合成軸の骨格・合成 variant (silo-backoff-\*・cicada-adaptive-\*・SS2PL スタディなど)、劣化 rung に当たる。**variant-\*.patch 3 本は coder (LLM) の EVOLVE-BLOCK 編集を orchestrator が監査して patch 化したもの** (`patches/README.md` の「variant-\*.patch — coder 編集の固定」節) で、歴史的な LLM 生成物を含む。一方、B-5 試走など探索ループの候補全件に対応する patch の保管は今回確認しておらず、現行の候補の保存表現は genome + src_token と提案 JSON である。campaign の `variants/` dir は `output/campaigns/` の 30 campaign のどれにも無い (調査子の実測) | P1 (関数単位) の候補を既存 patch 並みの 1 本数 KB と置けば 480 件で数 MB (仮定、未測定) | 提案 JSON の所在 (job dir) と件数 |
| (c) 入出力 (計測の入力・結果・LLM の入出力) | output/ の追跡 29,594 本 847,642,838 B (実測)。うち insights 618,792,439 B (最大は文献検索の束)、env 219,098,496 B (うち追跡下の生 trace 119,606,673 B)、P2-5 の LLM 提案記録 `output/s6-rounds/` 6,764,001 B。B-5 試走の LLM 資料は job dir 側に `materials/llm` (round-1〜10・critic-1〜9) 1,518,618 B と `ledgers/llm` 1,080,381 B、repo 内の insight `output/insights/2026-09-20/t2797-b5-contrast/` に `llm/` (prompt・request・proposal、`MANIFEST.sha256`) 851,937 B・`verbatim/` 360,797 B・`ledgers/` 1,166,900 B がある (実測、`verbatim/du-b5-llm.log`)。両者の重複関係と、prompt・応答の全量は未集計 | LLM 資料は 1 系列 10 巡で数 MB 規模 (job dir 側 2 dir の合計が約 2.6 MB、重複除去前) | job dir にある系列別の入出力 (A-1・K2 pair など、写しを含む dir 全体は各約 0.95〜1.0 GB だが実験データ部分は未測定) |
| (d) 探索設定 | campaign.lock 30 (`output/campaigns/` 全体 123 file 1,828,610 B — lock と WAL の 30 組に summary 等を含む)、事前登録 docs 17 本 639,847 B (調査子の実測)、凍結・事前登録 JSON (s1-freeze 80,856 / s8b-freeze 79,426 / s8c 33,127 B、実測) | 実験 1 本あたり数十〜百数十 KB の事前登録 (既存の分布からの換算) | 旧書式の lock を読むための当時の道具 (§8.2) |
| (e) 失敗候補を含む実験データ | WAL と判定要約 (result.json 45.6〜54.9 KB/走、verifier.json ≤ 1.3 KB/走)、保全 2 系列の trace 78,421,191,580 B (§4.2) | trace は §6・§7 のシナリオ。判定要約は走数 × 約 50 KB | job dir にだけある失敗記録、anomaly witness 付き verifier.json の大きさ (異常例の記録が無い) |
| (f) 図表の生成手順 | `tools/plotting/` 19 本 697,025 B、`docs/paper-story/figures/` 56 本 7,045,996 B (png 20 / pdf 17 / provenance.json 18)、結果稿 `docs/paper-story/results/` 21 本 810,275 B (実測)。図の入力は WAL と `reports/*.dat` (`tools/plotting/FIGURE_CONVENTIONS.md` §1)、入力の path と SHA-256 は `<出力>.provenance.json` (同 §6) | 図 1 枚あたり数十〜数百 KB | 図が引く job dir 側の入力 |

- repo の追跡分の総量は 959,525,089 B (izanagi のみ、実測) + CCBench 12,030,047 B で約 0.97 GB。これは開発記録と追跡下の生 trace 119,606,673 B を含む現存量であって、
  パッケージの上限ではない (job dir 側の入出力・系列別のコード一式・job dir の保全 trace を含まない)。
- job dir にある系列の dir 全体は大きいが、多くは repo の写しである。例: B-5 試走 `dev-wave-t2797-b5-contrast` 全体 2,661,132,881 B のうち、
  投入用の repo 写し `submit-tree` 1,026,782,920 B と変異検査用の写し `mutation-source` 1,606,090,617 B で 98.9% を占める (実測)。

### 5.2 保存費

保存費は論理容量・作業保管・公開・金額を別欄で扱う。容量枠の存在を「無料」「確保済み」と言い換えない。

| 欄 | 内容 |
|---|---|
| 論理容量 | trace 以外 ≈ 1 GB 級 (§5.1)。trace は既存 78.42 GB + 今後の実験のシナリオ (§6) |
| 作業保管 (Pegasus) | SFC group の /work quota (`verbatim/check-quota.log`、KiB 単位と読むと soft 85.00 TiB・hard 90.00 TiB ちょうど): 使用 4.03 TiB、soft までの余裕 80.97 TiB。**group 共有で予約ではない** |
| 公開 | Zenodo は 1 レコード 100 file・50 GB。既存 2 系列は系列ごとに 1 レコードへ収まる (D2160 48.93 GB、B-8 29.49 GB) が、file 数が 3,072 / 1,440 なので走ごとの束ね (tar) が要る。GitHub は repo 1〜5 GB が目安で trace には向かない |
| 金額 | **未確認。** 取得した Zenodo・GitHub のページに料金の記述が無く、Pegasus の保存に課金があるかも未確認。費用式は `保存費 = Σ(保存量 × 単価 × 保持期間 × 複製数)` で、単価が決まれば上の量を入れて出す |

## 6. trace 量の条件付きシナリオ (算式と値は `verbatim/scenario-calc.log`)

算式: `保存量 = Σ_条件 (候補数 × 実際に取得した反復数 × trace 秒数 × 1 秒あたり原本 ÷ 圧縮率) + legacy 等`。
率は §4.2 の 2 系列 (B-8 率 / D2160 率) を使う。**どちらも条件付きの値で、上下限ではない。**

- **B-5 型の完走評価 1 件** = legacy 小構成 1 本 (200 tuple / 4 thread / 1 s、`pipeline.py` 147 行の既定) を通過し、本規模の performance 検証
  (1,000,000 records / 48 thread / 3 s、B-5 事前登録 §5.5・258 行、`pipeline.py` 193 行) を 5 反復完走した評価。legacy 分は含めない。
  - 1 件の保存量: write-heavy 0.75、balanced 0.89〜1.77、read-heavy 2.66〜7.07 GiB。3 workload 等配分の平均 1.43〜3.19 GiB (原本 6.48〜13.74 GiB)。
  - 480 件 (Codex 案の P3 試走の候補評価数): 保存 0.67〜1.50 TiB、Zenodo 50 GB 換算 14.8〜32.9 レコード。3,600 件: 保存 5.03〜11.23 TiB、110.7〜247.0 レコード。
  - 注意: 480 件の元案は 2 プロトコル × 2 課題 (gap-analysis §4 P3) で、YCSB 3 workload の等配分ではない。S2 構成は 1 反復 (`pipeline.py` 159・176 行)。
    anomaly で reject された候補は最初に失敗した反復で止まる (1〜5 反復目のどこでも起こりうる)。build や legacy で止まれば本規模 trace はゼロ。
    retry・stock 対照・品質再測定・並列 fan-out で開始済みの反復は含めない。
- **anomaly を検出した反復だけを残す場合** (3 s trace 1 本 / 候補、等配分): 保存 0.286〜0.639 GiB / 候補。rejected が 48 件なら 13.7〜30.7 GiB、144 件なら 41.2〜92.0 GiB。
  k 反復目で失敗した候補の全反復を残すなら k 倍 (k ≤ 5)。異常候補の trace 率が正常候補と同程度という仮定は未測定。
- **標本** (stock と選択候補 × 3 workload × 3 s 1 本): 保存 1.72〜3.83 GiB / 系列。
- 相談 A の静的読解 (`verbatim/s3-consult-A.md` A5・A6): 選んだ key の全アクセスと、それらの key に触れた全 txn の C 行を順序どおり残す射影なら、
  その key が支える依存辺 (ww・wr・rw) は保たれる。**元の履歴に cycle があり、そのうち少なくとも 1 つの cycle の全辺を支える key をすべて選んだときに限り**、
  その cycle を再検出できる (例えば 2 つの key がそれぞれ A→B と B→A を支えるとき、片方の key だけを残すと cycle は消える)。元と同じ witness・全 cycle 数・
  integrity は再現しない。**射影は実装も実証もしていない。**

## 7. trace の保存・公開方針 (段 4 の決定)

| 対象 | 作業保管 | 公開 |
|---|---|---|
| 既存の保全 2 系列 (D2160・B-8) | そのまま | 公開候補 (系列ごとに 1 レコード、走ごとに束ねる) |
| 原履歴を確認できない系列 (§4.3) | 今回の調査では確認できず、現時点で含められない (他の保存経路・複製は未調査) | 判定要約・WAL・計測値・再実行手順。原履歴を含められないことをパッケージに明記する |
| 今後: 検証が主題の実験 (P0 の小履歴コーパスと実 trace 10〜20 本、検証費用・検出力の測定) | 全量 (zstd) | 全 trace |
| 今後: anomaly を検出した反復 (失敗候補の中核) | 全量 (zstd) | 全 trace |
| 今後: 探索比較の certified 反復 (P2・P3) | **全量 (zstd)** | 標本 (§6) + 全候補の判定要約・WAL |

- **理由:** 消した trace は戻らない。公開の保存粒度を規定が定めていない以上、今後の論文根拠の実験は作業保管を全量側に倒し、公開範囲の最終確定は
  投稿前のパッケージ組み立て時に行う。作業保管の全量は B-5 型 480 件で 0.67〜1.50 TiB (シナリオ値) で、quota の余裕 80.97 TiB (共有) の内側である。
  保全の手間は B-8 の実測で 10 s trace 1 本あたり 11.9〜29.8 s (`t2807-b8-effective/README.md` の preserve 列)。
- **要件充足は未確認。** 本方針で EA&B の "all experimental data" を満たすとは言わない。取得した規定は trace の保存粒度を定めていない。
- **最強の反論 (相談 B M1、記録として残す):** 本研究の中心命題は検証費用と検出結果を含み、trace はその実験の入力で判定要約はその派生物である。
  探索比較の certified 反復を標本にすると、非採用候補の判定・検証負荷を第三者が原履歴で再評価できない。→ 作業保管を全量にしたので、投稿前に公開を全量側
  (Zenodo で数十〜数百レコード) へ切り替える余地は残る。
- 不採用: T0 (trace を公開しない) — 既存の保全履歴まで外す理由が無い。T2 を公開の既定にすること — 現段階で確定しない (保存不能だからではない)。
  key 射影を保存の前提にすること — 未実装・未実証 (§6)。
- **今の標準経路は trace を消すので、作業保管の全量には保全口の実装が要る** (§11、本 wave では作らない)。

## 8. 再実行の 3 経路

### 8.1 定義

| 経路 | 何をするか | 入力 | 何を再現し何を再現しないか |
|---|---|---|---|
| **R1 再判定** | 保存 trace を verifier に掛け直す。決定的 | 保存 trace と、当時の判定に使った関連入力 (期待 commit 数・protocol・CCBench の source context)、当時の verifier の版 | 同じ履歴に対する判定を再現する。**verifier の版が変われば「保存履歴に対する新しい版での再評価」として別の結果にする** — 旧判定は保持し、新しい版が通ったことを理由に遡って certified へ昇格させない (規律 7)。旧形式 (5 項目の C 行) の trace は現行 parser で読めないので当時の道具で読む |
| **R2 再実行** | 保存候補 (genome + src_token + 提案 JSON、将来は patch) を LLM なしで、trace 有効 build で新しい履歴を取って検証 → trace 無効 build で計測する (規律 1) | 候補、系列に対応するコードと道具、環境契約 (env tag)、対象機で較正した床値、同時刻の stock と強い基準 | **新しい有限履歴の判定であって原判定の再確認ではない** (並行実行は非決定的)。anomaly が出たら即 reject (規律 2) し理由を構造化して返す (規律 3)。旧 campaign の再開とは別物 (drift した旧 lock は保存して再走しない、`docs/paper-story/2026-09-21c.md` 1182 行) |
| **G 再生成** | 同じ探索設定で LLM に候補を作り直させる | 探索設定・prompt・知識射影・役割定義、モデル表示名と時期 | 各候補は R2 と同じ正しさ・性能評価を通し、失敗理由を構造化して次の提案へ返す (規律 3)。結果は bytes の一致でなく、**独立した探索の反復**同士で分布として比べる。モデル更新後の G はその時期の追試として区別する |

### 8.2 コードと道具の同梱

- 既定経路として、実験系列に対応するコードと道具 (CCBench の pin と当てた patch、repo 外 runner、依存物) を同梱する。記録済みの campaign.lock には旧書式
  (exact-63) のものがあり、現行 checkout の certified 経路では読めず歴史閲覧 (`HISTORICAL_RAW`) でだけ読める (`docs/paper-story/2026-09-21c.md` 1186〜1188 行)。
- **これは凍結 chain ではない。** pin 照合・同一性検査・署名は足さない。新しい測定を当時のコードとの同一性で拘束しない (規律 7)。R2 を当時の checkout に
  一律に限定もしない — 旧記録の閲覧・再解析と、新しい履歴の取得は別の問題である。同じコードを使う系列は共用する。
- archive があるだけで再実行可能とは認定しない。実行手順 (§11) で具体化してはじめて使える。

### 8.3 既存の入口

- R2 の入口: 評価の唯一の経路 `pipeline.evaluate` (`orchestrator/campaign/pipeline.py` 2585 行) は LLM を呼ばない。保存済みの提案 JSON を
  `orchestrator/campaign/p3_s4_loop.py` の `--run-iteration PROPOSAL.json` (3475 行) に渡せば LLM なしで評価が回る。**R2 と G の分かれ目は CLI ではなく
  提案 JSON をどう作ったか**である。
- 任意のコード patch (P1 の関数単位の空間) を受ける評価入口は無い (P1 は未実装)。
- R1 の先例: `output/insights/2026-09-20/verifier-capacity/README.md` §4 は、保全済み trace を復元し、同じ node で旧 verifier (`947fd160a`) と改修版を
  別 process で順に掛け、14 本すべてで verdict・`result_to_dict` が一致したことを記録している。これは「保存履歴に対する新しい版での再評価」(§8.1) の実例である。
  標準経路には保存 trace を受ける入口が無い (上の再判定は repo 外 probe で行われた)。

### 8.4 主張ごとの再現対象

- 保存データからの再解析: 論文の集計値・判定区分・図の導出を再現する (図は WAL と .dat から描き直す)。
- R2: 新しい観測履歴に正しさ判定を行い、対象機で較正した変動幅と、同条件の stock・強い基準 (既知最良 `p2_2_flag_opt` を外さない) との比較を報告する。
  元の倍率や順位の一致は約束しない。**他機では絶対値だけでなく stock 比も変わりうる** (同一機内のノード間差さえ未測定、`docs/pegasus-node-variance-protocol.md` 冒頭)。
  Pegasus の床値を他機へ持ち込まない。
- G: 独立探索ごとの有効候補率・異常検出率・費用対成果・未知条件への転移を非 LLM 手法と比べる。同等幅などは結果を見る前に定める (各実験の事前登録の仕事)。

## 9. 費用 (計算の予約ではない)

費用は 4 区分に分ける。**job 占有は待ちを含み、固有費は含まない。** node を確保したまま LLM の手番を待てば、その時間は node 時間にも入る。

| 区分 | 記録された単価 | 出所 |
|---|---|---|
| 図の描き直し (保存データから) | 計測機の外で行う (node 時間ゼロ) | `tools/plotting/FIGURE_CONVENTIONS.md` §7 |
| R1 の純 verifier | 10 s trace 1 本: write-heavy 295.3 / balanced 219.2 / read-heavy 496.4 s (B-8 本走の平均)、3 s trace 1 本: 84〜433 s (改修後 verifier) | `t2807-b8-effective/README.md` の本走表、`verifier-capacity/README.md` §4 |
| R2 の評価固有費 | 1 session (1 候補 × 1 workload) 217〜509 s (中央値 498 s、待ちがほぼ無い直接実測は 499〜510 s)。内訳 build 15〜17 s、legacy verify 7〜16 s、performance verify 5 rep × 34〜91 s、bench 16.8〜17.0 s | `t2797-b5-contrast/README.md` §6.3 (実測) と §8.2 (外挿) |
| G の親手番 | 1 巡 10〜13 分 (critic 4〜5 分を含み、保存・検査・prompt 生成を含む)。node 時間とは別に LLM の直列時間として数える | 同 §6.3 |

系列ごとの過去の実消費 (同じ構成で再走した場合の参考値。準備・stock・retry・待ちを含む):

| 系列 | 過去の実消費 | 出所 |
|---|---|---|
| B-5 試走 (53 session、LLM・random・sweep・block stock) | job Elapse 計 61,261 s = 17.0 node 時間。home 共有 lock の待ち推定は計約 31,575 s (session の subprocess wall 合計 53,805 s の 59%、job Elapse に対しては約 51.5%)、LLM handshake 待ち約 7,360 s は job Elapse に含まれる。固有費合計 22,230 s (元資料の表記 6.18 h、換算 6.17 h) | `t2797-b5-contrast/README.md` §6.3 |
| B-8 (24 本の 10 s 検証 + 校正 6 本) | 本走 9,280 s (2.58 node 時間) + 校正 1,920 s = 3.11 node 時間 | `t2807-b8-effective/README.md` |
| D2160 検証相 (2 候補 × 30 判定) | 校正 + 本走 fixed-5 12,778 s + fixed-10 12,473 s = 25,251 s = 7.01 node 時間 | `verify-phase-adopted-backoff/README.md` 145 行 (§5.2 の別欄を参照する行) |
| S-1a (324 件の検証を含む直接比較) | 時間台帳 spent 22,943.7 s (旧 linux-baremetal 機、Pegasus の node 時間ではない) | `docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md` §1.4 |
| P2-5・静的 backoff の sweep・K2 | 未集計 | — |

- 主要図の再実行費は、図ごとに「描き直し / R2 / 独立探索のやり直し」のどれかを決め、候補数 × 単価、または上の過去の実消費で積み上げる。
  Codex 案の「実験予算の 10〜20%」は積み上げを点検する参考値に下げる。
- 投入するタスクの job 合計が 2 node 時間以上なら、投入前に見積りを示してユーザー確認を取る (D2212 項 4。開発の検査 = 受入・焦点走・変異の計算も同じ線で数え、
  見積りは job Elapse の実測単価で出す — D2219 項 1、2026-09-22)。例えば B-5 試走の 53 session を R2 で測り直すと、
  固有費だけで 3.19〜7.49 h (単価 217〜509 s × 53、`verbatim/scenario-calc.log` G) なので確認対象になる。元試走の占有 17.0 node 時間は LLM handshake 待ちと
  lock 待ちを含む実績であり、保存候補を使う R2 の占有見積りとしては使わない (R2 では LLM を呼ばず、node-local lock なら lock 待ちも変わる)。

## 10. provenance (D320 の粗い粒度)

- 論文が要るのは「どのシステムで何が生み出せたか」とおおよその時期 (D320)。再現パッケージの provenance はシステム名・モデル表示名・おおよその時期の
  粗い粒度で足り、凍結 chain は足さない (D2212 項 6、D320 を引く)。
- 既にある記録: WAL の各行に `variant`・`stage`・`env_tag`・`ts` (`orchestrator/campaign/wal.py` 1585〜1592 行)、source の証拠に `ccbench_commit`・`genome_sha256`・
  `src_token` (`orchestrator/campaign/source_digest.py` 181 行の `SourceEvidence`)、B-5 台帳の見出しに `repo_head`・`pin`・`perf_config`・`job.host` など
  (`orchestrator/campaign/b5_generator_contrast.py` 572〜585 行)。
- モデル: exact model ID は Agent tool の返答に載らず機械記録されていない。記録できるのは役割定義の `model` / `effort` と親 session の model 設定
  (`t2797-b5-contrast/README.md` §8.1)。**D2212 項 6 はモデル表示名で足りるとしているので、系列単位の表示名と時期で足り、候補ごとの記録機構は要らない。**

## 11. 欠け部品と job dir の回収 (列挙だけ、実装しない)

- **再実行に必要:**
  - 標準経路の trace 保全口 (作業保管を全量にするため。今は検証後に削除する)。
  - 任意のコード patch を受ける R2 の入口 (P1 の空間用)。
  - R1 の入力一式の保存 (trace と当時の関連入力・verifier の版)。
  - 実験系列ごとの実行手順書 ("meaningful instructions")。
- **任意 (容量削減):** key 射影 (§6)。
- **散文の記録で足りる:** モデル表示名と時期 (系列単位)。
- **job dir の回収 (推奨):** 論文根拠の実験データのうち job dir にだけあるもの (B-5 試走の台帳・入力素材・報告、D2160・B-8 の保全 trace と runner、
  K2 pair、A-1 の attempt データ) を、実験と並行で cleanup の対象外の保存先へ写す。既存の proof chain を移動・編集せず、写しを official の正本へ昇格させない。
  **本 wave では回収していない。** 使い捨て領域の撤去で実験の原本を失った前例がある — cleanup の引き渡し script の退避 tar が空のまま worktree 4 本を撤去し、
  K2 手動 loop の campaign 原本を失った (F1034、`output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md`)。

## 12. 段 3 相談と段 4 裁定

段 3 は read-only codex 2 本 (consult、lane luna、reasoning medium) を 09:36 に並列起動し、A は 09:41、B は 09:40 に rc=0 で終わった
(`tools/check_codex_output.py` 受理 rc=0)。段 2 plan は親の計画 v1 で代えた。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| B-M1 / A-A9 | T1 で EA&B の要件を満たすとは断定できない | real | §7 で「未確認」と明記、最強の反論を記録、作業保管を全量に |
| B-M2 / A-A6 | 未証明の key 射影を前提にしない。anomaly 反復は全 trace | real | §6・§7 |
| A-A5 | 全アクセス + 関係 txn の C 行を残す射影なら辺は保たれる | 攻撃不成立 | §6 に射程つきで記録 |
| B-M3 / A-A7 | 幅は上下限でなく条件付きシナリオ値。候補 1 件 = B-5 型完走評価 | real | §6 |
| B-M4 | 6 対象別の量・仮定・未集計・金額 | real | §5 |
| B-M5 / A-A8 | 図ごとの積み上げ、費用区分の混同 | real | §9 |
| B-S1 / A-A10 | T2 の保存不能の断定、quota 単位、レコード数の誤り | real | §5.2・§6・§7 |
| A-A1 / B-R1 | コード同梱は規律 7・凍結 chain 禁止に反しない | 攻撃不成立 | §8.2 (言い換えを採用) |
| B-S2 / A-A1 後段 | R2 を当時の checkout に一律に限定しない、旧 campaign の再開と同義にしない | real | §8.1・§8.2 |
| A-A2 | R2 = 新しい有限履歴の判定 | 攻撃不成立 | §8.1 |
| A-A3 | R1 に関連入力と版の扱いが要る | real | §8.1 |
| A-A3 付随 | trace.hh v1 と現行 parser が合わず再現手順が成立しない | 一部 real | Silo は transaction.cc で v2 を直接出し保全 trace も v2 なので当たらない。追跡下の旧 trace 4 file (v1) には当たる (§4.3) |
| A-A4 | G にも毎反復の検証と理由の還流 | real | §8.1 |
| B-S3 | key 射影と候補単位のモデル記録を必須にしない | real | §10・§11 |
| B-S4 | 主張ごとの再現対象 | real | §8.4 |
| B-R2 | job dir の回収は機構でなく保存行為 | 攻撃不成立 | §11 |
| 数値 | 0 B の verifier.json、78.42 GB、標本下端 1.72 GiB、patch 量、圧縮率の一般化、集計の射程、kB 表記、B-5 費用表の節 | real | 反映 |

**段 4 裁定の訂正 (erratum):** 段 4 裁定 (`verbatim/s4-ruling.md`、逐語のまま保存) は「0 B の verifier.json は親の再照合で 3 走、相談の 4 件は誤り」としたが、
**正しくは 4 走で、相談の指摘が正しかった。** 親の再照合は、見出しが 1 行だけの旧入力 (job dir の `preserved-traces-aggregate.log`、先頭のデータ行が 2 行目) に
awk の行番号条件 (`NR>2`) を掛け、先頭のデータ行 (`calib/fixed-10-balanced/extime-10`) を読み飛ばしていた (verbatim の `-d2160.log` は ROOT 行が増えた版で、同じ条件でも落ちない)。
段 6 レビューの M1 で判明し、§4.2 を 4 走に直した。同裁定の「保存 bytes は du と一致」も誤記で、§4.2 のとおり run dir の du は trace 以外を含む。

段 6 は read-only codex 1 本 (review、09:50〜09:54、rc=0、受理 rc=0、`verbatim/s6-review.md`) で、NO-GO (must-fix 3・should 4・nit 4) だった。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| R-M1 | 0 B の verifier.json は 4 走 | real | §4.2 と上の erratum |
| R-M2 | P2-5 は replay で trace を生んでいない。「原本は 2 系列と 4 file だけ」は調査範囲を超える | real | §0・§4.1・§4.3・§7 を調査範囲に限定。初版と現行版に削除処理があり、当該文字列の出現数の変更は初版以外に検出されなかったことを追記 |
| R-M3 | 射影で cycle を再検出できるのは、cycle の全辺を支える key を選んだときに限る | real | §6 |
| R-S1 | 保存 bytes と run dir の du は一致しない | real | §4.2 |
| R-S2 | patch の内訳と分類、campaign 総量の中身の根拠 | real | §5.1 (b)(d)、`verbatim/patches-sizes.log` を追加。分類は `patches/README.md` と file 名による |
| R-S3 | B-5 の `llm/` が未集計 | real | 実測して §5.1 (c)、`verbatim/du-b5-llm.log` |
| R-S4 | lock 待ち 59% の分母、17.0 node 時間を R2 の占有に転用 | real | §9 |
| R-N1〜N4 | 圧縮率の範囲の意味、S-1a の内訳、0.97 GB に生 trace を含む、6.17 h とモデル表示名の出所 | real | §4.2・§4.3・§0・§5.1・§9・§10 |

焦点再レビュー 1 巡目 (focus、10:08〜10:12、rc=0、受理 rc=0、`verbatim/s6-focus-1.md`) は NO-GO (closed 8 / partial 2 / regressed 1)。
残りは R-M2 (git 履歴の確認を全期間・全系列の削除へ広げていた)、R-S2 (variant-\*.patch は LLM 編集を patch 化したもの)、R-S3 (B-5 の LLM 資料は repo 内の insight にもある、
修正で入れた「job dir にだけ」が後退) で、§0・§4.3・§5.1・§7 と erratum を直した。
焦点再レビュー 2 巡目 (focus、10:15〜10:17、rc=0、受理 rc=0、`verbatim/s6-focus-2.md`) は **GO** (全 11 件で closed 10 / partial 1 / regressed 0、must-fix・should 0)。
残った nit (上表 R-M2 の処置欄に「初版から続くことを確認」という強い表現が残っていた) は処置欄を直して閉じた。

## 13. 出所と逐語

- `verbatim/request.md` — 依頼と T-2853 起票本文の逐語。
- `verbatim/web-evidence.md` — 公式ページの逐語抜粋と取得時刻。
- `verbatim/plan-v1.md` — 段 3 に渡した親の計画 v1 (訂正前の値を含む。本文の値が正)。
- `verbatim/s3-consult-A.md`・`verbatim/s3-consult-B.md` — 段 3 相談の逐語。
- `verbatim/s4-ruling.md` — 段 4 裁定。
- `verbatim/preserved-traces-aggregate-d2160.log`・`verbatim/preserved-traces-aggregate-b8.log` — 保全 2 系列の集計 (script `aggregate_preserved_traces.py`、
  sha256 `1a8ee329224a269fa1bf49d6a6babae559203d16bb068d4121cb5660a8a71cf6`)。
- `verbatim/repo-sizes.log` — 追跡 file の接頭辞別集計 (`git ls-files -z` の出力を script `sum_tracked.py`、
  sha256 `f35520e0e1eb8cd321ec10b96ab4572c1f32cb53d87b1a000895b9f8df6d69c5` で集計、gitlink の CCBench は数えない)。
- `verbatim/scenario-calc.log` — §6・§9 の換算 (script `scenario_calc.py`、sha256 `19a5ad624d8cb123697a0be95b8675412c9547c7e02edeca5d5f9caf4bdac85c`)。
- `verbatim/du-jobdirs.log`・`verbatim/du-b5-llm.log`・`verbatim/check-quota.log` — job dir の `du -sb` と `check_quota` の出力
  (du は同じ呼び出しで親 dir を先に数えると配下を重複として省くので、内訳は別の呼び出しで取った)。
- `verbatim/patches-sizes.log` — `patches/` の file 別の大きさ。
- `verbatim/s6-review.md`・`verbatim/s6-focus-*.md` — 段 6 レビューと焦点再レビューの逐語。
- script 3 本は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-repro-package-estimate/` にある (repo 外、生存保証なし)。
- 調査子 (Claude Explore、sonnet) 3 本の報告は会話内のみで、本文に使った値は親が一次資料・実測で照合したもの (CCBench の追跡 bytes・git pack・`variants/` 不在は調査子の実測を写した)。
