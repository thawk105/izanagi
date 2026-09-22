# [T-2853] 再現パッケージ初段 — 親の計画 v1 (段 3 相談の攻撃対象)

作成: 2026-09-22 09:3x JST、親 (Claude)。作業木 = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-repro-package-estimate`
(以下 W、HEAD = local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d`)。job dir = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-repro-package-estimate` (以下 J)。

## 0. 依頼 (逐語は J/materials/request.md) と scope

- 公開対象 (コード・生成パッチ・入出力・探索設定・失敗候補を含む実験データ・図表の生成手順) ごとに、trace 量と保存費を既存記録から
  仮定付きの幅で見積もる。LLM の再生成と保存済み候補の再検証・再計測を分けた再実行の形を整理する。
- 計算なし (login の du / ls / JSON 集計と既存記録のみ)。実験の再走・公開そのもの・gate / 検査 / 台帳の追加・凍結 chain は scope 外。
  provenance は粗い粒度 (D320: システム名・モデル表示名・おおよその時期) で足りる。
- 成果物 = insight `W/output/insights/2026-09-22/t2853-repro-package-estimate/README.md` (docs のみ、実装面の差分ゼロ) + worklog fragment。
- 根拠の裁定: D2212 項 6 (失敗候補込み公開可、実験と並行、D320、凍結 chain なし)、項 4 (計算 2 node 時間以上は都度確認)。
  「ユーザー裁定へ返す」は恒久的に採らない運用なので、本計画の択は相談を経て親が決める。

## 1. 外部条件 (Web、2026-09-22 08:5x JST 取得、逐語抜粋は J/web-evidence.md)

- VLDB Vol.20 EA&B: 全実験データと関連ソフトウェアの公開が必須 ("there are no excuses")。初回投稿時点で全実験の再現パッケージへのリンク +
  実行手順が必須。置き場は恒久性のある公開アーカイブ (公開 GitHub 可、個人サイト不可)。容量・形式・匿名性の記述は取得本文に無い。
  call for research track: EA&B の貢献は "insights into workloads and reusable artifacts such as benchmark suites or traces"。
- Zenodo: 1 レコード 100 file・合計 50 GB (50,000,000,000 bytes)、20 file 超は ZIP 推奨、アカウントに追加 150 GB の配分枠。
  料金の記述は取得ページに無い。1 レコード最大 200 GB への増枠は二次情報のみ (公式ページ 404) で**未確認**。
- GitHub: 1 file 100 MiB で拒否、50 MiB で警告、repo は 1 GB 未満推奨・5 GB 未満を強く推奨。

## 2. 前提の訂正 (新事実)

一次資料 gap-analysis §4 P0 の「balanced 10 秒で 32 GiB、read-heavy 6 秒で約 81 GiB、ノード上限約 115 GiB」の GiB 値は
**verifier の node peak メモリ** (改修後 verifier、`W/output/insights/2026-09-20/verifier-capacity/README.md` §4 表の「新 同」列: balanced 10 s 32.4、
read-heavy 6 s 81.2) であって trace file の量ではない。trace file の量は §3 の実測。

## 3. 実測・記録 (出所種別: 記録 = 文書の値、実測 = 本 wave の login 実測、換算 = 記録/実測からの計算)

### 3.1 trace の保存方針
- 標準の評価経路は検証 1 反復ごとに trace を一時 dir に出し、検証後に削除する: `W/orchestrator/campaign/pipeline.py` の
  `_run_one_repetition` 相当 (mkdtemp `izanagi_eval_trace_` → `finally: shutil.rmtree`、およそ 2160〜2178 行)。[記録=コード]
- 例外は repo 外 runner (`verify_phase_runner.py`、job dir 保管) が検証前に zstd -T0 -3 で保全した 2 系列だけ:
  D2160 検証相 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run`) と B-8 (`.../dev-wave-t2807-b8-effective/run`)。[記録]
- trace の行形式は text、1 event 1 行 (`W/external/ccbench/include/trace.hh` の 17〜20 行付近: `C`/`R`/`W` 行)。[記録=コード]

### 3.2 保全 2 系列の集計 (親の実測、J の script `aggregate_preserved_traces.py`、log は J/preserved-traces-aggregate*.log)
- D2160: 64 走・3,072 file、原本 213,338,672,445 B → 保存 48,928,578,277 B (4.360)、32.35 B/行。記録 (`W/output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` §4 保全行) と bytes 一致。
  3 s 走の原本中央値 write-heavy 0.922 / balanced 1.565 / read-heavy 5.758 GiB、保存 0.149 / 0.354 / 1.414 GiB。
- B-8: 30 走・1,440 file、原本 133,510,417,298 B → 保存 29,492,613,303 B (4.527)、32.98 B/行。10 s 走の原本中央値 wh 3.153 / bal 2.655 / rh 7.157 GiB、
  保存 0.497 / 0.593 / 1.774 GiB。記録 (`W/output/insights/2026-09-21/t2807-b8-effective/README.md` の保全量: 本走 24,614,435,537 B + 校正 4,878,177,766 B) と一致。
- du -sb: D2160 job dir 全体 48,989,490,231 B、B-8 run 29,497,099,557 B (親の実測 09:3x)。
- 1 秒あたり原本 (換算): wh ≈ 0.31 GiB/s (両系列同じ)、bal 0.27 (B-8) 〜 0.52 (D2160)、rh 0.72 (B-8) 〜 1.92 (D2160) GiB/s。
  候補の処理量で balanced 約 2 倍、read-heavy 約 2.7 倍振れる。圧縮率は workload で決まり wh 6.2〜6.35、bal 4.4〜4.5、rh 4.03〜4.07。
- 判定の要約: result.json 45.6〜54.9 KB/走、verifier.json ≤ 1.27 KB/走。[実測]
- 条件: どちらも Silo・48 thread・YCSB zipf 0.9・Pegasus gen_S。trace-enabled build (規律 1 の検証用 build)。

### 3.3 今後の実験で候補 1 件が生む trace (換算)
- 評価経路の本規模検証は候補 1 件 = legacy 小構成 1 本 (200 tuple / 4 thread / 1 s) + performance 検証 5 反復 (1M / 48 / 3 s)
  (`W/orchestrator/campaign/pipeline.py` の `CorrectnessWorkload` / `performance_correctness_workload`、B-5 事前登録 `W/docs/b5-generator-contrast-preregistration.md` §5.5、動作点は同 258 行付近)。
- 候補 1 件 (5 × 3 s = 15 s) の原本: wh 4.6、bal 4.0〜7.8、rh 10.7〜28.8 GiB。保存 (zstd -3): wh 0.75、bal 0.89〜1.77、rh 2.66〜7.07 GiB。
- 3 workload 等配分の平均: 保存 1.43〜3.19 GiB / 候補、原本 6.4〜13.7 GiB / 候補。
- 規模 (Codex 案、gap-analysis §4 P3、候補評価数は未確定の提案値): 試走 480 候補 → 保存 0.67〜1.50 TiB (原本 3.0〜6.4 TiB)。本比較 3,600 候補 → 保存 5.0〜11.2 TiB。
- 仮定: Silo と同程度の trace 率を第 2 プロトコル (MOCC)・TPC-C にも置く (未測定)。rejected 候補は 1 反復目で止まる (pipeline は 1 件失敗で即 reject) ので上限側。

### 3.4 trace 以外の公開対象 (調査子 ② の login 実測、親が一部照合)
- (a) コード: W の追跡 file 32,761 本 971,743,653 B、うち output/・docs/ を除く 62,272,655 B。CCBench submodule 追跡 12,030,047 B。.git pack 約 508 MiB。
- (b) 生成パッチ: `W/patches/` 36 file 284,375 B (1 本 0.5〜2 KB)。campaign の `variants/` dir は 30 campaign のどれにも無い。現行の候補は hole への整数 literal (B-5 事前登録冒頭) で、genome + src_token と提案 JSON で表される。
- (c)(e) 入出力・実験データ: output/ 追跡 29,594 file 847,642,838 B。内訳 insights 618,792,439 B (最大は文献検索の束 98.6 MB)、env 219,098,496 B (うち追跡下の生 trace 4 file 119,606,673 B = silo_ladder_rung1)、s6-rounds (P2-5 の LLM 提案記録) 6,764,001 B、campaigns (lock + WAL 30 組) 1,828,610 B。
- job dir にだけある実験データ (親の実測 du -sb): B-5 試走 `dev-wave-t2797-b5-contrast` 全体 2,661,132,881 B だが実験データ部分 (ledgers 2,179,722 / materials 1,528,922 / report-pilot-final.json 890,213 ほか) は数 MB で、残りは repo の写し (submit-tree 1,026,782,920、mutation-source 1,606,090,617)。K2 pair 948,279,603 B、A-1 attempt2 996,651,773 B (いずれも写しを含む、内訳未測定)。
- (d) 探索設定: campaign.lock 30、事前登録 docs 17 本 639,847 B、凍結・事前登録 JSON (s1-freeze 80,856 / s8b-freeze 79,426 / s8c 33,127 B)。
- (f) 図表: `W/tools/plotting/` 19 file 697,025 B、`W/docs/paper-story/figures/` 56 file 7,045,996 B (png 20 / pdf 17 / provenance.json 18)、結果稿 21 file 810,275 B。
- trace 以外の合計: 約 1.1〜1.5 GB (insight・開発記録を全部含めた上限側)。論文の根拠に絞れば数十 MB 規模 (未集計)。
- Pegasus 保存容量 (check_quota、J/check-quota.log): SFC group /work 使用 4,330,395,672 KB、soft 91,268,055,040 KB、hard 96,636,764,160 KB (group 共有)。

### 3.5 再実行に関わる記録
- 評価の唯一の入口 `pipeline.evaluate` (`W/orchestrator/campaign/pipeline.py` 2585 行付近) は LLM を呼ばない。保存済み提案 JSON を
  `W/orchestrator/campaign/p3_s4_loop.py --run-iteration` (3475 行付近) に渡せば LLM なしで評価が回る。R と G の分岐は「提案 JSON をどう作ったか」。
- 任意のコード patch (P1 の関数単位空間) を受ける評価入口は無い (P1 未実装)。
- 記録済み campaign.lock の書式 drift: B-5 試走の lock は exact-63 grammar で、現行 checkout の certified 経路では読めず `HISTORICAL_RAW` でだけ読める
  (`W/docs/paper-story/2026-09-21c.md` 1186〜1188 行、D2194 項 4 (2))。
- 費用: B-5 試走 4 job 合計 61,261 s = 17.0 node 時間 / 53 session。1 session の固有費 217〜509 s (中央値 498 s)、内訳 build 15〜17 s、legacy verify 7〜16 s、
  performance verify 5 rep × 34〜91 s、bench 16.8〜17.0 s (`W/output/insights/2026-09-20/t2797-b5-contrast/README.md` §8 の表)。
  B-8 の 10 s 検証: 本走 24 本 9,280 s、校正 6 本 1,920 s (Elapse 和) → 1 本 ≈ 0.10〜0.11 node 時間 (換算)。
- LLM 生成: 1 巡 10〜13 分 (critic 4〜5 分)。exact model ID は Agent tool の返答に載らず機械記録なし。記録できるのは agent 定義 (`model: opus` / `effort: high`) と
  親 session の model 設定 (同 README §8.1)。
- 環境: 同一機内のノード間差の実測は無い (`W/docs/pegasus-node-variance-protocol.md` 冒頭)。Pegasus 以外の機械での再計測を論じた文書は見つからない。
- データ消失の前例: K2 手動 loop 3 巡の campaign 原本が 2026-09-20 に job dir 側で消失し、一部は派生物からの再構成 (F1034、
  `W/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` §5.1、`W/output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md`)。

## 4. 親が決める事項 (provisional、攻撃対象)

- **(P1) trace の公開範囲は T1 (標本) を採る。**
  - T0 = trace を公開しない (判定の要約 verifier.json / result.json / WAL と再生成手順だけ)。量 ≈ 0。
  - T1 = 判定の要約は全候補分 + trace は標本: (i) 既存の保全 2 系列 (78.5 GB、系列ごとに 1 レコード、各 ≤ 50 GB に収まる。48 file/走なので走ごとに tar)、
    (ii) 今後の実験は系列ごとに stock と選択候補の各 workload 1 本 (6 本 × 1 反復 ≈ 保存 1.9〜3.8 GiB / 系列)、
    (iii) anomaly で reject した候補は反例の検証に要る部分 (witness の key に触れる全行 + 関係 txn の commit 行) を全件。全 trace は保存しない。
  - T2 = 全 trace。試走 480 候補で保存 0.67〜1.50 TiB、本比較で 5.0〜11.2 TiB。Zenodo の 1 レコード 50 GB に対し 14〜230 レコード相当で、公開も Pegasus 保存も非現実的。
  - T1 を選ぶ理由: EA&B の "all experimental data" は判定と計測の値で満たし、trace は再生成手順で補う。反例は小さく残せる。量は公開アーカイブの上限内。
  - T1 (iii) の射影 (key 射影) は実装が要る (本 wave では作らない、欠け部品として列挙)。射影が cycle の再検出に足りるかは未証明で攻撃対象。
- **(P2) 再実行を 3 経路に分けて定義する。**
  - R1 再判定: 保存済み trace を同じ verifier に再投入する。決定的。原本がある保全 2 系列と T1 の標本だけが対象。
  - R2 再実行: 保存済み候補 (genome + src_token + 提案 JSON / 将来は patch) を LLM なしで、trace 有効 build で新しい履歴を取り検証 → trace 無効 build で計測 (規律 1)。
    **新しい履歴の判定であって原判定の再確認ではない** (並行実行は非決定的)。anomaly なら即 reject (規律 2)。計測は同時刻の stock 対照との比で報告する。
  - G 再生成: 同じ探索設定で LLM に候補を作り直させる。モデル表示名と時期を記録し (D320)、結果は分布として比べる (bytes 一致を求めない)。
  - R2 は記録時点のコード一式 (実験系列ごとの checkout の archive) で回す。現行コードで読めない旧書式 (exact-63) があるため。これは凍結 chain ではなく
    「再実行に要る道具を同梱する」だけで、pin 照合や同一性検査は足さない。
- **(P3) 費用の見積り (計算の予約ではない)。**
  - R2 の単価は B-5 固有費 217〜509 s / session (1 候補 1 workload)。主要図の再実行は Codex 案の「実験予算の 10〜20%」を仮置きとして据え、実験系列ごとに
    (候補数 × 単価) で出す。投入前に 2 node 時間以上ならユーザー確認 (D2212 項 4)。
  - R1 の単価は 10 s trace 1 本 ≈ 0.10〜0.11 node 時間 (B-8)、3 s trace は verifier-capacity §4 の新 verifier wall 84〜433 s。
  - G の単価は 1 巡 10〜13 分の LLM 直列時間 (node 時間と別)。
- **(P4) 環境の留保。** 他機での再計測は絶対値の再現を約束しない。論文の主張は同時刻 stock 比と床値で書き、パッケージの手順にもそう書く。
- **(P5) job dir にしかない実験データの回収。** 実験と並行でパッケージ用の置き場へ写すことを推奨として書く (F1034 の前例)。仕組みの実装・台帳化はしない。
- **(P6) 欠け部品の列挙 (実装しない)**: 任意 patch を受ける R2 入口、T1 (iii) の key 射影、標準経路での標本 trace の保全口、実行手順書 (README)、
  モデル表示名の候補単位の記録。

## 5. 攻撃してほしい点 (親が自信の無い順)

1. T1 で EA&B の "all experimental data (no excuses)" を満たすと言えるか。trace を落とすことが「データを出さない」ことにならないか。
2. key 射影 (T1 (iii)) で anomaly の再検出が成立するか (DSG の辺が射影で失われないか、version order の決め方)。
3. R1/R2/G の区別と、R2 を「記録時点の checkout で回す」ことが規律 7 (現行コードとの差だけで無効にしない) と整合するか、凍結 chain の再導入になっていないか。
4. §3.3 の換算 (候補 1 件 = 15 s の本規模 trace) が評価経路の実際と合うか。legacy 1 本の寄与、rejected 候補の扱い、S2 構成との違い。
5. 数値の出所: 本計画の数値を一次資料・実測 log と照合し、食い違いを列挙する。
