# [T-2853] 残り (5) 主要図の再実行計画 — 図ごとの経路 (描き直し / R2 / 独立探索のやり直し) と node 時間の積み上げ (計算なし)

- 作成: 2026-09-23 JST。wave `worktree-t2853-rerun-plan` (背景 job)、着手時の基準 = local main `65fd1422f`。依頼の逐語は `verbatim/request.md`、開始 gate は `verbatim/startup-gate.log` (rc=0)。
- 正本の前段: `output/insights/2026-09-22/t2853-repro-package-estimate/README.md` (以下「見積り稿」) の §8 (3 経路) と §9 (単価)、
  `output/insights/2026-09-23/t2853-repro-package-archive/README.md` (以下「写し稿」) の §2 (写し) と §4 (系列ごとの手順)。
- 根拠の裁定: D2212 項 4 (1 タスクで投げる job の合計が 2 node 時間以上なら投入前にユーザー確認)、D2219 項 1 (開発の検査も同じ線で数え、見積りは job の Elapse の実測単価で出す)、
  D2212 項 6・D320 (provenance は粗い粒度)、D2211 項 10・D2212 項 5 (A-1 の 3 本目は今は走らせない、旧系列の再開は論文の必須経路から外す)。
- **job は投げていない。** 計算ノードは使わず、login での読み取り (結果稿・insight・provenance・job 会計の記録、WAL の時刻差の計測) だけである。
  本稿は計画であり、計算の投入の承認ではない。段 6 の read-only レビュー (NO-GO、must-fix 6) を反映した版である (§7)。

## 0. 結論

1. **論文の主張の再現に要る最小の経路は描き直し (保存データからの再描画、node 時間 0) である。** 20 図の内訳は次のとおり。
   - **生成器があり、いまの入力で描き直せる 17 図** (fig2b・fig2c・fig3b・fig3c・fig4〜fig15 と fig8b)。図の値は WAL・`.dat`・凍結 report・`certification.json`・
     結果稿の逐語から描かれており、測定をやり直さなくても図と集計値は再現できる (見積り稿 §8.4 の「保存データからの再解析」)。
   - **生成器を作る必要がある fig1**。値の出所 `output/campaigns/p2-5-summary.json` は追跡下に残るが、生成器が repo に無い (§3.1)。
   - **対象外の 2 図** (fig2・fig3)。凍結物で、後継図 (fig2b・fig3c) を使う。
2. **R2 (保存した固定の genome を LLM なしで計算ノードで検証・計測し直す) を推奨できるのは 9 図** (fig2b・fig2c・fig4・fig6・fig8・fig8b・fig10・fig11・fig13。fig8 は fig8b の測り直しに含まれる)。
   fig15 は R2 ではなく **固定条件の観測の再実施** (TRACE=1 の非 certifying 観測で、検証の後に trace 無効で計測する R2 の形をしていない) になる。
   fig5・fig7 は測り直しても用途制限が残るので推奨せず、fig9・fig14 は保留の裁定で今は走らせない。fig2・fig3・fig3b・fig3c・fig12 は値を持たないか使わない図で R2 に該当しない。
   fig1 は下地の P2-2 fitness 表だけが測り直しの対象になる。R1 (保存 trace の再判定) の対象になる図は無い — R1 の入力一式があるのは D2160 検証相と B-8 だけで (写し稿 §5)、どちらも図を持たない。
3. **独立探索のやり直し (G) が要る図は無い。** LLM が関わる図は fig1 (P2-5 の誘導探索) と fig12 (K2 手動 loop のデータフロー模式図、値なし) だけで、どちらも描き直しで足りる。
   fig1 の P2-5 は保存した fitness 表の上を LLM critic が辿る**再生**で、再生のやり直しは node 時間 0・LLM の直列時間だけである。これは G ではない。
   G (同じ探索設定で LLM に候補を作り直させる) は、作り直した各候補を R2 と同じ正しさ・性能評価に通すので、候補数 × R2 の単価の node 時間がかかる (見積り稿 §8.1・§9)。
   G は任意の追試として計画に入れない。fig12 の背景の K2 は論文の必須経路の外 (D2211 項 1)。
4. **図ごとに 1 タスクとして投げた場合、Elapse の単価で 2 node 時間以上になり投入時にユーザー確認が要るのは fig10 と fig5/fig7 (推奨しない) の 2 件である。fig13 と fig4 は単価が無く未判定。**
   - fig10: NQSV の Elapse × 確保 node 数で 3.40 node 時間。
   - fig5 / fig7: 同じ測定で 2.02 node 時間。
   - fig13: job の Elapse の記録が無く、実消費の見積りは未確定。確保枠 (walltime) は 3 job で 48 h、投入〜完了の差 18.68 h は queue の待ちを含む参考値で、どちらも Elapse ではない。
     単価の無いまま投げるなら確保枠 48 h を示して確認を取る (保守側の運用で、D2212 項 4 の線の判定そのものではない)。
   - fig4: 旧 linux-baremetal 機の時間台帳 6.37 h は Pegasus の node 時間ではない。Pegasus での投入形 (job 数・node 数・walltime) が決まった時点で見積もり、判定する。
   - 1 本ずつで 2 node 時間未満と見込む図のうち、fig6・fig11・fig15 は (a) の Elapse から出した値である (fig6・fig11 の 5 node 形は B-7 の (a) を当てた試算)。
     fig1・fig2b・fig2c・fig8・fig8b は (a) が無く代理値 ((b)・(c)・試算) から出したので、「不要」は**暫定**であり、投入形を決めた段階で (a) で見積もって確定する。
   **複数の図を 1 タスクに束ねると合計で線を越えうる** (§4)。
5. 推奨する実行順は「描き直し → 入力の写しを足す → R2 は論文投稿前に、投げる単位を決めて見積りを示し、確認を取ってから」である (§5)。

## 1. 範囲と言わないこと

- 図の母集合は `docs/paper-story/figures/README.md` の「図の一覧」の 20 図 (fig1〜fig15 と枝番) とした。ComSys 2026 原稿
  (`output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex`) が `\includegraphics` で載せるのは fig2b・fig4・fig9・fig14・fig15 の 5 図で、
  A-2・A-6・B-7 の値 (fig6・fig11・fig10 と同じ値) は表で載せている (調査子の報告を親が照合)。**どれを VLDB 稿の図にするかは論文側の仕事で、本稿は決めない。**
  論文図へ未昇格の参考図 (`t2187_stage2_thread_axis`、同 README の「調整済み adaptive の実対照」節) は母集合に入れない。
- 触れないもの: (1) 標準経路の trace 保全口と (1') R1 の入力一式の組は [T-2849] の担当、(4) P1 の関数単位の候補を受ける R2 の入口は P1 と同じ wave の担当。
  gate・検査・台帳・一般化・生成器の新規作成・写しの実行はしていない。
- **node 時間は上下限ではない。** 所要の出所を次の 5 種に分けて書く。D2219 項 1 が見積りに使うとする単価は (a) だけで、他は (a) が無いときの代わりである。
  - (a) **Elapse** — NQSV の会計の Elapse (結果稿・job.stderr の記録)。
  - (b) **driver 記録** — driver や runner が自ら記録した所要 (例: B-10 の `job_elapsed_s`。後始末の前に書かれ、job の最終終了までを含まない)。
  - (c) **WAL 時刻差** — 本 wave が WAL の ts の先頭〜末尾から測った値 (`verbatim/wal-span.log`)。
  - (d) **投入〜完了** — 投入時刻と完了時刻の差で queue の待ちを含む。
  - (e) **walltime 上限** — 単価が無いときに使う、確保する枠の上限。
  これらに node 数・job 数を掛けた値は「換算」、別系列の単価を当てた値は「試算」と書く。
- R2 の見積りは「元と同じ設計を 1 回測り直す」場合の値である。R2 は新しい有限履歴の判定であって原判定の再確認ではなく、元の倍率・順位の一致は約束しない (見積り稿 §8.1・§8.4)。
  anomaly が出た候補は即 reject し理由を構造化して返す (規律 2・3)。検証は trace 有効 build、計測は trace 無効 build の別走 (規律 1)。新しい測定は旧判定を上書きせず、
  当時のコードとの同一性で拘束もしない (規律 7)。
- 旧 `linux-baremetal` 機の測定 (fig1・fig2・fig2b・fig4) を Pegasus で R2 すると別環境の新しい測定になる。Pegasus の値を旧機の図へ混ぜない
  (`docs/paper-story/figures/README.md` の fig2b 節、見積り稿 §8.4)。**旧機の所要は Pegasus の node 時間ではなく、D2212 項 4 の線と同列に比べない。**

## 2. 図ごとの経路と node 時間

経路の欄: **必須** = 論文の主張を再現パッケージで再現するのに要る最小の経路、**R2** = 測り直す場合、**G** = 独立探索のやり直し。
「確認」は、その図 1 本を 1 タスクとして投げる場合に D2212 項 4 の確認が要るか。

### 2.1 旧 linux-baremetal 機の図 (fig1・fig2・fig2b・fig3・fig4)

| 図 | 何を描くか / 論文での位置 | 入力の所在 | 必須 | R2 | G | 所要 (出所) | 確認 |
|---|---|---|---|---|---|---|---|
| fig1 `phase2_negative` | P2-5 の否定的結果 (誘導探索の探索コスト)。版の本文に掲載 | 値の出所 `output/campaigns/p2-5-summary.json` と P2-2 の 3 campaign (追跡下・現存)。**生成器は repo に無い** | 描き直し (**生成器が要る**、§3.1) | 下地の P2-2 fitness 表 (固定 genome 8 点 × 5 反復 × 3 workload) を測り直す場合だけ | 要らない。P2-5 は保存評価の再生で新規計測 0 (D21)。再生のやり直しは node 時間 0・LLM の直列時間だけ (未記録) | P2-2 の旧機: 1,016.7 s (WAL 時刻差 369.9 / 345.8 / 301.0 s、旧機の値)。Pegasus なら fig2b と同規模の試算 0.27 node 時間 | 暫定で不要 (Elapse の単価が無い。投入形を決めて (a) で見積もり、確定する) |
| fig2 `backoff_mechanism` | 凍結物。基準線の label が誤り、perf record 下の診断系列 (D20 で headline 非使用) | 一次資料 `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json` (追跡下)。生成器なし | **対象外** (後継 fig2b を使う) | しない | — | — | — |
| fig2b `backoff_sweep_3workload` (ComSys) | P2-4 の静的 backoff sweep (記述的、D496 以前、論文の利得率の出所ではない) | 3 campaign の WAL・`.dat`・lock (追跡下・現存)。再現コマンドは図 README の「後継図の再現」 | 描き直し | 可 (固定 genome 8 variant × 5 反復 × 3 workload、各 variant に `verify_done` あり) | — | 旧機: 1,214.0 s (WAL 時刻差 605.6 / 314.8 / 293.6 s、旧機の値)。Pegasus: 0.27 node 時間 (試算、fig2c の WAL 時刻差から 1 variant あたり 41.2 s × 24 variant) | 暫定で不要 (Elapse の単価が無い。投入形を決めて (a) で見積もり、確定する) |
| fig3 `arc_status` | 凍結物。2026-07-10 版の現況図 (fig1・fig2 の数値を転記した文字を含む) | 生成器なし | **対象外** (後継 fig3c) | — | — | — | — |
| fig4 `s1a_9pair_direct_comparison` (ComSys) | S-1a の 9 対の直接比較 (縮小主張 S' の失敗報告図) | 凍結 report `output/reports/s1_direct_comparison/report.json`・`output/s1-freeze/measurement_freeze.json`・4 campaign (追跡下・現存) | 描き直し | 可。4 構成の genome・gate 述語は `measurement_freeze.json` に凍結済みで、LLM 候補ではない。選定は構成ごとに異なる — system_gate は D50 の機械偵察の勝ち gate、`p2_2_flag_opt`・`backoff_fixed_best` は全列挙・sweep の argmax、`sort_best` は balanced が本走の argmax、**read-heavy は sweep 未実施の事前固定値** (結果稿の限定 9) | — | 旧機の時間台帳 spent 22,943.7 s = 6.37 h (記録、`docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md` §1.4、legacy + s2 の検証 324 件を含む)。**Pegasus の node 時間ではない。Pegasus での投入形は未定で、所要は未見積り** | 未判定 (投入形を決めた時点で (a) が無ければ (e) で見積もって判定) |

### 2.2 Pegasus の固定 genome の図 (fig2c・fig5〜fig11・fig13)

| 図 | 何を描くか / 論文での位置 | 入力の所在 | 必須 | R2 | G | 所要 (出所) | 確認 |
|---|---|---|---|---|---|---|---|
| fig2c `b10_extended_backoff` | B-10 拡張格子の記述図 (既定定数の adaptive の状態を覆う静的点、1000 µs は F718 で除外) | repo 外 `/work/1/SFC/tanab/b10-backoff-grid-runs5/` (現存、写し稿の写しに無い) | 描き直し | 可 (固定 genome、3 job、各 31 variant に `verify_done` あり) | — | 3,831.8 s = 1.06 node 時間 ((c) WAL 時刻差 1,276.3 / 1,276.2 / 1,279.3 s × 3 job × 1 node。Elapse は未記録) | 暫定で不要 (Elapse の単価が無い。投入形を決めて (a) で見積もり、確定する) |
| fig5 `a2_certification_reject` | A-2 正式 certification (attempt `t2022-20260828c`)。**測ったのは `BACK_OFF` の有効/無効で、採用静的 backoff の結論・図に使わない** (D1645、期限なし) | `output/insights/2026-08-24_paper-story-a2-certification/` (追跡下) と repo 外 `izanagi-measurements/.../t2022-20260828c` (現存) | 描き直し | **推奨しない** (測り直しても同じ用途制限が残る。静的 backoff の結論は fig6 の取り直しが担う) | — | 3,671 + 3,594 = 7,265 s = 2.02 node 時間 ((a) Elapse、結果稿 `2026-09-04-a2-certification-reject.md`、1 node × 2 job) | 要 (投げる場合) |
| fig6 `a2_certification_observed_positive` | A-2 の取り直し (attempt `t2364-20260907b`)。write-heavy +63.5485%・balanced +14.4213%、outer `observed-positive`。ComSys は表で掲載 | `output/insights/2026-09-07_t2364-paper-story-a2-certification/` (追跡下) と repo 外 `izanagi-measurements/.../t2364-20260907b` (現存) | 描き直し | 可 (固定 genome: stock `BACK_OFF=0` 対 fixed 10 / 5 µs) | — | 元の走: 3,020 + 3,037 = 6,057 s = 1.68 node 時間 ((a) Elapse、job.stderr の会計、`verbatim/wal-span.log` に抜粋。1 node 時代の走)。**現行 policy は 5 node** (2026-09-19 `eda92f107`)。同じ 5 node 形の B-7 の Elapse (rr5 386 s・rr50 841 s) で 5 × 1,227 = 6,135 s = 1.70 node 時間 (試算) | 不要 |
| fig7 `a2_builtin_backoff_onoff_reject` | fig5 と同じ attempt・同じ値を、効いた条件 (内蔵 adaptive の on/off) の記述へ訂正した図。静的 backoff の結論に使わない (D1936 項 21・D1993 決定 5) | fig5 と同じ | 描き直し | 推奨しない (fig5 と同じ) | — | fig5 と同じ測定: 2.02 node 時間 ((a) Elapse) | 要 (投げる場合) |
| fig8 `b10_static_tail_not_observed` | B-10 静的右 tail の 09-15 正式 cohort (8 点 × 3 workload × 5 反復、`performance_certified: false`) | repo 外 `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/` (現存、写しに無い) | 描き直し | 可 (固定 genome、legacy の正しさ検査 120 記録を job 内で実施) | — | 836.44 + 833.08 + 837.47 = 2,507.0 s = 0.70 node 時間 ((b) driver 記録の `job_elapsed_s`、`output/insights/2026-09-16/b10-tail-formal-submit/README.md`。後始末の前の値) | 暫定で不要 (Elapse の単価が無い。投入形を決めて (a) で見積もり、確定する) |
| fig8b `b10_static_tail_cohort2` | fig8 の後継 (cohort 1 と独立再現 cohort 2 を併記、合成しない) | 同上 dir の cohort 1・cohort 2 (現存、写しに無い) | 描き直し | 可 (2 cohort を測り直すなら fig8 を含む) | — | cohort 1 の 0.70 ((b)) と、cohort 2 の 3 job × 839 s = 2,517 s (換算。insight `output/insights/2026-09-19/b10-tail-cohort2/README.md` が 3 job 並行の走について「Elapse 839 秒」と記す (a) で、job ごとの内訳は無い) → 計 5,024 s = 1.40 node 時間 | 暫定で不要 (Elapse の単価が無い。投入形を決めて (a) で見積もり、確定する) |
| fig10 `b7_fixed5_three_workload_regression` | B-7 の材料 (fixed 5 µs を 3 workload で同一 attempt、read-heavy は床値超の退行)。ComSys は表で掲載 | `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/` ほか (追跡下) と repo 外 raw-cell 6 file (現存) | 描き直し | 可 (固定 genome) | — | 5 node × (386 + 841 + 1,218 s) = 12,225 s = 3.40 node 時間 ((a) Elapse × 記録の確保 node 数、結果稿 `2026-09-19-b7-fixed5-three-workload-regression.md` §1) | **要** |
| fig11 `a6_certification_reject` | A-6 read-heavy 正式 certification (fixed 2 µs、median 比 −5.7841%、outer `reject`)。ComSys は表で掲載 | `output/insights/2026-09-08_t2411-paper-story-a6-certification/` (追跡下) と repo 外 `izanagi-measurements/.../a6-20260908b` (現存) | 描き直し | 可 (固定 genome) | — | 元の走: 4,382 s = 1.22 node 時間 ((a) Elapse、結果稿 `2026-09-18-a6-certification-reject.md`、1 node)。**現行 policy は 5 node** (2026-09-08 09:10 `2a9ba783f`、元の走の開始 01:29 より後)。B-7 の rr95 の Elapse で 5 × 1,218 = 6,090 s = 1.69 node 時間 (試算) | 不要 |
| fig13 `b10_waiting_grid_forest` | B-10 待ち方 grid 正式走 (`constant` 対 `symmetric-modulo`、36 cell、3 族とも `different`、`official_certification: false`) | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/` (追跡下) と repo 外 `izanagi-job-evidence/b10-backoff-shape/submissions/23409962…/` (現存、写しに無い) | 描き直し | 可 (固定の待ち方 2 種 × μ 6 点 × 3 block × 5 反復、正しさ検証と計測を同一 job で行う相) | — | **(a) は無い** (結果稿 `2026-09-20-b10-waiting-grid-formal.md` §1.3 は投入と完了の時刻だけで、job 結果にも開始時刻が無い)。(e) walltime 上限: 43,200 + 43,200 + 86,400 s = 48 h (3 workload job、各 1 node。集約 job は測定なし)。参考: (d) 投入〜完了 14,615 + 13,200 + 39,022 + 集約 403 s = 67,240 s = 18.68 h (queue の待ちを含む)。どちらも実消費の見積りではない | 未判定 (単価の無いまま投げるなら確保枠 48 h を示して確認を取る) |

### 2.3 Pegasus のその他の図 (fig3b・fig3c・fig9・fig12・fig14・fig15)

| 図 | 何を描くか / 論文での位置 | 入力の所在 | 必須 | 測り直し | G | 所要 (出所) | 確認 |
|---|---|---|---|---|---|---|---|
| fig3b / fig3c `arc_status_*` | 版ごとの 3 幕と A・B 項目の状態だけを描く模式図 (数値なし) | 状態 JSON と版本文 (追跡下・現存) | 描き直し | 該当なし (値なし) | — | 0 | 不要 |
| fig9 `a1_balanced5_sized_attempt1` (ComSys) | A-1 attempt-0001 の記述図 (非認証 lane) | `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (追跡下)。背後の durable authority は repo 外で**写しあり** (写し稿 §2.3 `a1-durable-authority`) | 描き直し | **今は走らせない** (新しい attempt は D2211 項 10・D2212 項 5 で保留、走らせるなら attempt 間比較の事前登録を作ってから諮る) | — | 参考: 553.96 + 755.30 + 323.80 = 1,633.06 s = 0.45 node 時間 (結果稿 `2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` の elapsed 列) | (走らせるなら認可が先) |
| fig14 `a1_balanced5_sized_attempt2` (ComSys) | A-1 attempt-0002 の記述図 (fig9 の兄弟、プールしない) | `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` (追跡下)。durable authority と wave 記録は**写しあり** | 描き直し | 今は走らせない (同上) | — | 参考: 2,218.79 s = 0.62 node 時間 (写し稿 §4.5) | (同上) |
| fig12 `k2_manual_loop_dataflow` | K2 手動 loop 3 巡のデータフローの説明図 (性能値を描かない) | 流れ JSON・結果稿・role 定義 3 本 (すべて追跡下) | 描き直し | 図には該当なし。背景の候補 (20 / 25 / 10、4 巡目の 5) の提案 JSON は追跡下に残り技術的には R2 可 | 背景の K2 loop は LLM 生成。**論文の必須経路の外** (D2211 項 1) なので計画に入れない | 参考: 3 巡の job 82 + 432 + 69 = 583 s = 0.16 node 時間 (結果稿 `2026-09-20-k2-manual-loop-three-rounds.md`)。4 巡目と pair は 207 s (写し稿 §4.4) | — |
| fig15 `mocc_witlight_four_arm` (ComSys) | stock mocc の軽量 witness 4 arm × 60 走の非 certifying 観測 (TRACE=1、G2 signal の検出率) | 生成器の入力は repo 外 5 file `dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/` (現存、写し稿の写しに無い)。**同じ SHA-256 の逐語写しが追跡下の `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/` にある** (図 README の fig15 節。生成器はそれを入力にしない) | 描き直し | **R2 ではなく固定条件の観測の再実施** (固定 build、実行時 env の差だけ)。元の認可は 60 走 / arm の 1 回限りで、再実施には改めて認可が要る (結果稿 §1.1) | — | 再実施の所要: 本走 4 job 1,471 + 1,468 + 1,461 + 1,466 = 5,866 s と smoke 148 s = 6,014 s = 1.67 node 時間 ((a) Elapse、結果稿 `2026-09-20-mocc-witlight-four-arm.md` §2) | 不要 (認可は別に要る) |

### 2.4 共通の注記

- **検証の費用は各行の値に含まれる。** 元の走はどれも正しさ検査を同じ job の中で行っている (fig2b・fig2c は各 variant の `verify_done` を WAL で確認、fig8・fig8b・fig13 は結果稿・insight の記述、
  A-2・A-6・B-7 は legacy 1 + performance 5 の検証)。現行 policy の 5 node は正しさ検査を兄弟 node へ分ける経路 (`2a9ba783f`) のためで、確保した 5 node を占有時間として数えた。
- **試算の射程:** fig6・fig11 の 5 node 形の値は、同じ policy 形・同じ cell 構成 (stock 対 採用 1 本 × 5 標本) の B-7 の Elapse を当てたもので、別の日の別の job である。
  fig2b の Pegasus 値は fig2c の WAL 時刻差から出した 1 variant あたりの時間を当てた試算で、旧機の値とは別物である。
- **LLM の直列時間は node 時間と別に数える** (D2212 項 4)。R2 と観測の再実施は LLM を呼ばないので 0。G を行う場合は見積り稿 §9 の「1 巡 10〜13 分」を併記し、
  作り直した候補ごとに R2 の単価 (1 session 217〜509 s、見積り稿 §9) を足す。
- **受入などの開発の検査も同じ線で数える** (D2219 項 1)。R2 を投げる wave が実装を伴えば、受入 1 回 ≈ 0.25 node 時間を足す。

## 3. 描き直しの前提 (計算ではない)

### 3.1 生成器が無い図

| 図 | 状態 | 描き直しに要るもの |
|---|---|---|
| fig1 | 値の出所 `output/campaigns/p2-5-summary.json` (追跡下) は残る。生成器は repo に無い | 生成器 (探索コストの図を `p2-5-summary.json` から描く) を新しく作る。図の bytes の一致ではなく値の一致で再現とする (同 README の「再現できるのは値であってバイト列ではない」)。作成は実装面なので Codex author の別 wave で、本稿の scope 外 |
| fig2・fig3 | 凍結物で、後継図 (fig2b・fig3c) がある | 論文で使わないので要らない |

### 3.2 生成器の入力が repo 外にあり写し稿の写しに入っていない図

写し稿 §2 は job dir の論文根拠データ 12 組を写した (12 manifest の範囲)。次の入力はその範囲に入っていない。

| 図 | 生成器が読む repo 外の入力 | 置き場の種類 | 元が失われたとき |
|---|---|---|---|
| fig15 | `dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/` の `summary.json`・`W1〜W4/result.json` | dev-wave の job dir (写し稿 §2.1 のとおり worktree の撤去で失われる型がある) | 同じ SHA-256 の逐語写しが追跡下の `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/` にあるので値は失われない。生成器の既定の入力 path は使えなくなる |
| fig12 の背景 (K2 巡 1〜3) | `dev-wave-jobs/` の `dev-wave-t2588-k2-loop-roundtrip`・`dev-wave-t2746-k2-loop-round2`・`dev-wave-k2-loop-round3` | 同上 | 図自体は追跡下の入力だけで描けるので、図の再現には要らない |
| fig2c | `/work/1/SFC/tanab/b10-backoff-grid-runs5/` | job dir の外の plain dir | repo に写しがあるかは本 wave では確かめていない |
| fig8・fig8b | `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` | 同上 | 同上 |
| fig13 | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962…/` | 同上 | 同上 (report の provenance と `.md` は追跡下) |
| fig5・fig6・fig7・fig10・fig11 | `/work/1/SFC/tanab/izanagi-measurements/...` | official の durable authority (写し稿 §0 項 2 で写しとは別の dir にした場所) | 同上 (`certification.json`・`raw-manifest.json` は追跡下) |

いずれも本 wave では写していない (依頼は計画だけ)。公開パッケージを組むとき (残り (6)) に同梱の対象になる。

## 4. 積み上げ

D2212 項 4 の単位は「1 つのタスク (1 本の実験、または 1 本の wave) で投げる job の合計」なので、投入の単位を決めた時点で該当行を合計し直す。
下の表は束ね方の例で、出所の種類が違う値を足した和は見積りの目安であって (a) の Elapse ではない。**どの行も受入などの開発の検査を含まない** — R2 を投げる wave が実装を伴えば、
受入 1 回 ≈ 0.25 node 時間を同じ線で足す (D2219 項 1、§2.4)。

| 束ね方 | 所要の和 (出所) | 確認 |
|---|---|---|
| 描き直しを全 17 図 | 0 (計測機の外、`tools/plotting/FIGURE_CONVENTIONS.md` §7) | 不要 |
| ComSys 原稿の図のうち今測り直せる fig2b (R2) と fig15 (観測の再実施) を 1 タスク (受入なし) | 0.27 (試算) + 1.67 ((a)) = 1.94 | 暫定で不要 (fig2b は (a) が無い試算。受入を足すと 2.19 で要。fig15 は認可が別に要る)。fig4 を加えるなら fig4 の見積りが決まってから判定する |
| 表で載る値の図 fig6・fig10・fig11 を 1 タスク | 1.70 (試算) + 3.40 ((a) × node 数) + 1.69 (試算) = 6.79 | **要** |
| B-10 の図 fig2c・fig8b を 1 タスク | 1.06 ((c)) + 1.40 ((b) と (a) の換算) = 2.46 | **要** |
| B-10 の図 fig2c・fig8b・fig13 を 1 タスク | 2.46 + fig13 (未見積り、確保枠 48 h) | **要** (fig13 を除いた 2.46 で越える) |
| R2 を推奨する 9 図から、Pegasus の単価の無い fig4・fig13 を除き、fig8 を後継 fig8b の費用に含めて重複計上しない 6 図 (fig2b・fig2c・fig6・fig8b・fig10・fig11) を 1 タスク | 0.27 + 1.06 + 1.70 + 1.40 + 3.40 + 1.69 = 9.52 | **要** |
| 上の 6 図に fig13 と fig4 を加える | 9.52 + fig13 (未見積り、確保枠 48 h) + fig4 (未見積り) | **要** (9.52 で越える) |

- **1 本ずつなら 2 node 時間未満の図 (fig2b・fig2c・fig6・fig8・fig8b・fig11・fig15) でも、1 タスクに束ねれば合計で線を越えうる。**
- 2 node 時間未満でも、fig15 は元の認可が 1 回限りのため、fig9・fig14 は保留の裁定のため、投げる前に認可が要る (node 時間とは別の理由)。
- 所要は元の設計を 1 回測り直すときの値で、retry・事前の校正・smoke の再走は含めない (fig15 の smoke は例外として含めた)。

## 5. 実行の順序 (推奨)

1. **描き直し (node 時間 0):** 生成器のある 17 図を、図 README の各節の再現コマンドで計測機の外から描き直し、provenance の論理値と一致することを確かめる。
   fig3b・fig3c・fig12 は追跡下の入力だけで描ける。fig1 は生成器を作る別 wave が要る (§3.1)。
2. **入力の写し:** fig15 の repo 外 5 file は job dir にあるので、写し稿と同じ手順で写しておくと生成器の既定の入力が残る (値は追跡下の逐語写しにもある)。
   他の plain dir は公開パッケージの組み立て時 (残り (6)) に同梱する。
3. **R2 (論文投稿前、図ごとに判断):** 投げる単位を決めたら §2 の該当行を合計した見積りを示し、2 node 時間以上ならユーザー確認を取ってから投入する (D2212 項 4)。
   確認が要る見込みは fig10 と束ねた場合 (§4)。(a) の無い図 (fig1・fig2b・fig2c・fig8・fig8b) の「不要」は暫定で、投入形を決めた段階で (a) で見積もって確定する。fig13 と fig4 は単価が無いので、投入形を決めて見積もってから判定する (fig13 を単価の無いまま投げるなら確保枠 48 h を示して確認を取る)。fig5・fig7 は R2 を推奨しない。fig9・fig14 は保留の裁定、fig15 は 1 回限りの認可に従う。
   R2 の trace を保全するかは残り (1') の範囲で、本稿では決めない。
   なお、本 wave の着手後に着地した第 33 回の裁定 D2235 は、T-2853 残り (5) を「投入前確認の予告 (今は諮らない)」の 1 つに挙げている。本稿はその確認に出す見積りの下地であり、確認そのものではない。
4. **G は計画に入れない。** fig1 の P2-5 の再生のやり直しは G ではなく、図の再現にも要らない。

## 6. 出所

- 図の母集合と各図の入力・状態: `docs/paper-story/figures/README.md` の「図の一覧」と各節、各図の `*.provenance.json`。
- 元の測定の所要: §2 の各行が引く結果稿・insight、`verbatim/wal-span.log` (本 wave が WAL の ts から計算した時刻差と、fig6 の会計行の抜粋、
  script は repo 外の job dir の `walspan.py`、sha256 `c6e0785707c0febb2ad57bf782a34ee2a5f7a07af3c9d353b7bbd8c6a0c24461`)。
- policy の node 数の変更: `orchestrator/campaign/paper_story_{a2_certification,a6_certification,b7_fixed5_regression}.v2.json` の `scheduler.nodes` (いずれも 5) と
  `git log -S'"nodes": 5'` (`eda92f107`・`2a9ba783f`)。
- 調査子 (Claude Explore、sonnet) 3 本 (図の群ごとに入力の所在・元の測定・所要) の報告は会話内のみ。本文に使った所要の値は、親が結果稿・insight・job 会計・WAL で照合した。
  調査子が「fig2c は perf なし・検証なし」と読んだ点は WAL の `verify_done` で訂正し、fig13 の「約 18.6 時間」は開始時刻の無い投入〜完了の和 (待ちを含む) であることを確かめた。

## 7. 段 6 レビュー

軽量版の dev-wave として段 2・3 は省いた (実装面の差分ゼロ、設計の択一なし)。一次資料から事実を再抽出した docs なので、段 6 の read-only レビューを 1 本残した。
review (Codex、read-only、20:22〜20:26 JST、rc=0、`tools/check_codex_output.py` 受理 rc=0、逐語 `verbatim/s6-review.md`) は NO-GO (must-fix 6・should 3・nit 1)。
親が各所見を現物で裏取りし (図 README の fig15 節と追跡下の逐語写し 6 file、S-1a 結果稿の限定 9、B-10 の結果稿 §1.3・insight の所要表)、9 件を real・scope 内と裁定して本文を直した。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| M1 | fig13 の 18.68 h は Elapse ではなく投入〜完了 (待ちを含む) | real | 出所を (d) とし参考値へ分離 (§0 項 4、§2.2、§4)。確認要否は焦点再レビュー FM1 を受けて未判定に直した (下) |
| M2 | fig4 の旧機の時間台帳を Pegasus の node 時間と同列に加算 | real | 別欄にし「Pegasus での投入形が未定で未見積り」、確認は未判定 (§0 項 4、§1、§2.1、§4) |
| M3 | fig15 は TRACE=1 の非 certifying 観測で、R2 の形ではない | real | 「固定条件の観測の再実施」として R2 と分けた (§0 項 2、§2.3、§4) |
| M4 | fig15 の入力は追跡下に同じ SHA-256 の逐語写しがある | real | §0・§2.3・§3.2・§5 に併記し、「描き直せなくなる」の断定を外した |
| M5 | 「全 20 図で描き直しが必須」は表と矛盾 | real | 17 図 / 生成器が要る fig1 / 対象外 2 図に分けた (§0 項 1) |
| M6 | fig1 の再生と G の費用の混同 | real | 再生 (node 時間 0) と G (候補ごとに R2 の単価) を分けた (§0 項 3、§2.1、§2.4、§5) |
| S1 | fig4 の「どれも全列挙の argmax」は過大 | real | 構成ごとの選定を書き、read-heavy の `sort_best` は事前固定値と明記 (§2.1) |
| S2 | fig8 の `job_elapsed_s` は driver 記録で Elapse ではない | real | 出所を (b) とした (§1、§2.2) |
| S3 | fig2c の値は WAL 時刻差で Elapse ではない | real | 出所を (c) とし、§4 の和は Elapse ではないと明記 |
| N1 | 算術の転記は一致 | 確認 | 対応不要 |

焦点再レビュー 1 巡目 (Codex、read-only、20:28〜20:31 JST、rc=0、受理 rc=0、逐語 `verbatim/s6-focus-1.md`) は NO-GO — 前回 10 件は closed 9 / partial 1 (M1) / regressed 0、
新規 must-fix 1・should 2・nit 1。件数 (20 = 17 + 1 + 2、R2 推奨 9 図)、walltime の和 172,800 s、§4 の和はレビュー子が一次資料から再計算して一致した。親は 4 件を real・scope 内と裁定して直した。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| FM1 (M1 の残り) | walltime 上限 48 h から確認「要」を導くのは Elapse 単価の見積りではない | real | fig13 の確認を未判定にし、単価の無いまま投げるなら確保枠 48 h を示して確認を取る (保守側の運用で線の判定ではない) と分けた (§0 項 4、§2.2、§4、§5) |
| FS1 | cohort 2 の 839 s は insight が「Elapse」と記す | real | (a) とし、job ごとの内訳が無いことを添えた (§2.2) |
| FS2 | 「Pegasus の単価がある 6 図」は fig8 を落とす量化 | real | 「fig4・fig13 を除き、fig8 を fig8b に含めて重複計上しない 6 図」と書いた (§4) |
| FN1 | §4 の 1.94 は受入を含まない | real | §4 の冒頭と行に受入を含まないこと、足すと 2.19 になることを書いた |

焦点再レビュー 2 巡目 (Codex、read-only、20:33〜20:35 JST、rc=0、受理 rc=0、逐語 `verbatim/s6-focus-2.md`) は NO-GO — 初回と 1 巡目の 14 件はすべて closed、
§4 の和 (6.79・2.46・9.52) と件数はレビュー子が再計算して一致、新規 must-fix 1 (should・nit 0)。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| GM1 | (a) の Elapse が無い図 (fig2b・fig2c・fig8・fig8b) の「確認不要」を代理値から確定している | real | fig1・fig2b・fig2c・fig8・fig8b の確認欄を「暫定で不要 (投入形を決めて (a) で見積もり、確定する)」にし、§0 項 4・§4・§5 を揃えた。fig1 も (a) が無いので同じ扱いにした |

DW-O16 の上限 (3 巡) に達したので、GM1 の修正は再レビュー子に回さず親が閉じた。根拠: 表の 5 行は行頭の図名で特定して末尾の欄だけを書き換える script で置換し
(置換 5 件を assert)、§0 項 4・§4 の fig2b 行・§5 の文言を Edit で揃えた。変更後に「| 不要 |」で終わる行は描き直しと模式図の行 (fig3b / fig3c、§4 の描き直しの行) と、
(a) から出した fig6・fig11・fig15 だけであることを grep で確かめた。
