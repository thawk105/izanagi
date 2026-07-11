# 段 8a 段階 D 偵察 — silo-backoff-trigger-gating 機械 sweep (2026-07-11)

## 位置づけ

- 段 8a 段階 D (axis-onboarding §3-D、D46 型偵察)。**報告カテゴリ = 偵察 (preliminary、
  事前登録外)**。断定 verdict なし。失敗条件 (c) の判定は出さない。
- 目的 = 軸の生死 (floor 超地形の有無) を E 段 (LLM ループ) 実装の固定費を払う前に安価に先取り。
- 出口 = 本 insight の凍結 + **継続/軸見直しは人間判断** (worklog「次の一手」の gate)。
- 本軸は 8a (post-coder) 由来 — **探索補助限定・段 6 headline 非対象** (D47 決定 5)。
- **firewall: E 段へ流してよいのは軸の生死二値のみ** (D48 必須条件 7)。本偵察の材料
  (勝ち構成・数値・機序考察) を段 6 正式 grid・E 段入力に流用しない。本 insight を見て
  E 段入力を起草する記憶汚染は既知残存リスク — E 段 campaign provenance に「偵察 insight を
  見た」の情報源記録を義務付ける (D46 (a) のループ版)。
- 敵対レビュー 2 巡・全反映: 設計 3 レンズ (workflow wf_a80f3f4e-22c、should 11 / nit 1)、
  実装 2 レンズ (wf_24065dcb-223、should 3 / nit 3)。一次資料 = 各 workflow の journal.jsonl。
  裁定台帳 (9 項) は下記に凍結。

## 実験

### D48 必須前提 3 点の消化
- **(a) 要因頻度実測** (s8a_trigger_freq.py、`output/env/linux-baremetal/calibration/
  s8a_trigger_freq_t48.json`): 実効 3 ビット **{lock-conflict (lc), readvali-tid (rt),
  readvali-locked (rl)}**。不感 {update-absent, node-vali} (全 workload カウント 0 —
  update-absent は YCSB (delete なし) の構造論拠、node-vali は経験的予想の側)。
  保存則 (A 行総数 == abort_counts_) 3/3 OK。分母 = 実測 abort 総数 149K (balanced) /
  156K (write-heavy) / 71K (read-heavy) (訂正 2026-07-11 監査: 初版は 3 ラベルとも
  取り違え — 正本 = s8a_trigger_freq_t48.json。数値自体は実在、示唆節の対応は初版から正)。
- **(b) read-heavy floor** = max(0.030, rr95 実測) = **0.030** (rr95 実測 within CV 0.19% /
  between CV 0.11% が保守性を裏付け。ただし genuine-between 未較正の残存リスク付き —
  fresh 実測は下限値)。
- **(c) 適応連成**: 主走 = adaptive (E 段と同条件で測るのが生死判定として正当)。
  BACKOFF_FIXED 追走は contingency (発火条件 = 全点平坦、workload = read-heavy 事前固定)
  — 今回は floor 超が出たため**不発火**。

### 器と動作点
- 器 = `s8a_trigger_sweep.py` (s6 の器の 2 軸目適用 = 器の汎用性の初実証)。列挙 =
  2^3 subset + ident_all (恒等 gate、フラグ 1) + 真 stock (フラグ 0) = **10 点/workload ×
  3 workload**。動作点 = p2_2 確定 (t48 / 1M records / skew0.9 / reps5 / extime3 /
  CLK1800 / numactl interleave)。全点 verify legacy+s2。
- **比較基準 = ident_all** (D49 申し送り a — フラグ 0 stock との比較は骨格常駐コスト
  (7 store + 1 分岐) を軸効果に混入させるため、恒等 gate を基準にして外す)。真 stock は
  骨格常駐コストの別掲用に 1 点。
- テスト 22 本 (述語生成の機械検査 / config identity 分離 / replay outcome / floor
  fails-closed 等)、全体 352 passed (buildcache 修正後 354)。

### レビュー裁定台帳 (設計 3 レンズ、9 項全反映 — 一次資料の凍結)
1. **F1 (prereg):** D47 決定 5 (探索補助限定) をレポート限定欄 (7) に転記。
2. **F2 (prereg):** E 段 provenance への情報源記録義務を限定欄 (6) と本 insight に明文化。
3. **F3 (prereg) + STAT-2:** read-heavy floor の within/between 混同を訂正 — 「0.030 ≥
   rr95 genuine-between」は未検証仮定であることを明示 (残存リスク欄)。
4. **MS-1 (mechanism):** BACKOFF_FIXED 追走は現在の器で実行不能 (2 パッチ合成未検証) —
   contingency のまま発火時の前提タスク 3 点を凍結。発火しない限り実装しない。
5. **MS-2 + STAT-3:** cross-run 再測の必須化 — 単一 campaign の floor 超は候補提示のみ。
   生死二値の確定は当該点 + ident_all の --remeasure (別 trial) 後。
6. **MS-3 + STAT-1:** 「構造的発生不能」の語を訂正 (node-vali の 0 は経験的)。freq JSON に
   実測 abort 総数を分母として記録。
7. **STAT-4:** 条件付き追走の workload は機序ベースの事前固定 (read-heavy) — 「主走で
   最大レンジ」は noise realization に基づく選定のため撤回。
8. **STAT-5:** 恒等 gate vs 実効全集合の一致検査を「structural-zero 仮定の低 power
   backstop」に格下げ (一次証拠は頻度実測の count=0)。不一致時の分岐を事前規定。
9. **MS-4 (nit):** A 行手組み tally の数え漏れは保存則が fails-closed に検査、を docstring
   に明記。

## 結果

campaign (本走):
- balanced = `p3-s8a-trigger-sweep-balanced-sweep-c2d838b8` (07-11 14:44 完了)
- write-heavy = `p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8` (17:36 完了)
- read-heavy = `p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c` (18:11 完了)

cross-run 再測 (trial=remeasure1、別 campaign):
- balanced = `...-balanced-sweep-b8f4a4e2` (18:27) / write-heavy = `...-write-heavy-sweep-dcd2bbfb`
  (18:40) / read-heavy = `...-read-heavy-sweep-654d5cd7` (18:48)

詳細表 (median tps / CV / abort率 / certified) は各 campaign の
`reports/s8a_trigger_sweep_report_*.md` が正本 — ここでは要約のみ。

### floor 超地形 (軸の生死材料)

| workload | best (floor 較正済み) | 本走 vs ident_all | 再測 vs ident_all | 再測点の本走比 |
|---|---|---:|---:|---:|
| balanced | g_rl | +84.5% | **+91.0%** | +0.04% |
| write-heavy | g_rt | +61.2% | **+61.3%** | -1.2% |
| read-heavy | g_rl | +98.9% | **+98.7%** | +0.75% |

- **3 workload すべてで floor (±3.0%) を 1 桁上回る利得が cross-run 再現。**
  要因選択に情報がある: gate の選び方で subset レンジは +61.8%〜+98.9% の幅。
- floor 地形の評価点 (subset/ident_all/退化点) は全 campaign で certified (legacy+s2 とも
  anomaly 0)。unstable なし。本走 stock 2 点 (balanced/write-heavy) は build-error で欠測
  (教訓節の kill 残骸毒) — 骨格常駐コストは再測 campaign で回復済み (訂正 2026-07-11 監査:
  初版の「全評価点 certified」は本走 stock 欠測を含めると無限定には成立しないため限定)。
- high-abort 判定不能 (fails-closed) に分離した点: 退化点 g_none (全 workload)、
  write-heavy の g_rl (abort 41.9%)、read-heavy の g_lc (abort 基準比 2 倍超)。
- 不感縮約 backstop (g_lc+rt+rl vs ident_all): -1.75% / -0.37% / +0.77% — 全 workload
  floor 内、頻度実測の不感判定と整合。
- 骨格常駐コスト (ident_all vs stock): +0.55% (read-heavy 本走) / -1.24% (balanced 再測) /
  -0.85% (write-heavy 再測) — 全て floor 内 = **軸の固定費は検出限界以下**。

## 示唆 (判断しない)

- **最適 gate が workload で入れ替わる**: balanced / read-heavy は rl (readvali-locked)
  が最良、write-heavy は rt (readvali-tid) が最良。頻度実測の支配要因 (balanced は
  lc 82K > rl 51K、write-heavy は lc 149K/156K) と勝ち gate が一致しない — **要因頻度と
  gate 利得の非比例**が workload 横断で再現。8b (workload 次元) の動機づけ材料。
- balanced の地形解釈: g_none (全素通し) が最速 = balanced では backoff 総量の削減自体が
  利得 (p2_2 の B0>B1 と整合)。その中で「どの要因で待つか」に +0.6%〜+84.5% の幅 =
  gate の質の信号。
- read-heavy では g_none 8.35M (abort 15.9%) — abort 率の絶対値は低く、退化点でも
  スループット倍増。ただし high-abort 判定不能 (基準比 2 倍超) のため floor 比較からは分離。

## 還元判断

- **人間判断待ち: 軸の生死 (E 段へ進むか、軸見直しか)。** 偵察としての観察は「floor 超
  地形が 3 workload で cross-run 再現 = 生の強い候補」。
- E 段へ流してよいのは生死二値のみ (D48 条件 7)。E 段 campaign provenance に本 insight を
  見た事実の情報源記録義務 (D46 (a) ループ版)。

## 残存リスク

- rr95 genuine-between 未較正 (read-heavy の生死判定が負う — fresh 実測は 0.030 内だが下限値)。
- D49 latent fragility 2 点の再訪条件 (非同期 scan 導入時 / cmake 非経由ビルド) — 本偵察
  では不発火。
- 素の sweep は適応 Backoff_ との連成地形 — gate 単独の帰属は曇る (magnitude 軸との直交性
  主張は adaptive-off 前提の限定付き)。
- write-heavy/read-heavy の S2 verify は rr50 固定 (off-workload 被覆)。
- 本 sweep は fairness 偏向 (D41 型 15) を検出しない。

## 教訓 (計測基盤): kill 残骸の永続毒 — stock build-error の根本原因と恒久封鎖

- **事象**: balanced の stock 欠測 (build-error) は当初「二重起動事故 (14:02:38) の一過性
  巻き添え」と解釈された。しかし write-heavy のクリーン起動 (17:03) でも stock だけ
  build_start から **0.107 秒**で build-error 再発 → 一過性説が崩れ調査。
- **根本原因 (WAL タイムスタンプ + build dir 実地検証で確定)**:
  1. 14:02 の kill が stock の perf ビルド (build-variants/silo_4ef3431bfe_t0) を
     「CMakeCache.txt あり・binary 無し」の中途状態で放置 — kill では Python の例外経路
     (_discard_build_dir) が走らない (buildcache の kill 耐性の構造穴)。
  2. 残骸 CMakeCache の CMAKE_HOME_DIRECTORY = 当時の一時 worktree
     (/home/tanab/tmp/izanagi_wt_6m01ti2n/wt、実行ごとランダム・既に消滅)。
  3. 以後の stock configure は毎回別の worktree パスから走るため、cmake がソース
     ディレクトリ不一致で即死 → build-error を**永続再発** (「remeasure すれば回復」は
     残骸を破棄しない限り誤りだった)。stock の trace ビルドは完成済みで無害 — 毒は
     perf 側 1 dir のみ。
- **恒久対処**: buildcache.build の configure 前に「binary 不在の既存 build dir を
  _discard_build_dir で破棄」(_clear_stale_build_dir)。破棄→再ビルドは fails-closed 側の
  回復で、正当な完成品 (binary あり = cache hit 経路) は触らない。回帰テスト 2 本、
  全体 354 passed。**read-heavy 本走の stock 建て直し成功 (trace cache hit・perf 新規
  ビルド・verify 通過) で実地検証済み。**
- **全数点検**: build-variants 147 dir 中 binary 不在の残骸 7 個 (今回の毒 1 +
  2026-06-19 15:50-16:00 の Phase 2 期 trace 残骸 6)。修正後は次回アクセス時に自動破棄・
  再ビルドされる。Bash からの手動 rm は guard_bash が正しく拒否 (防壁の意図どおり) —
  **迂回せず正規経路 (buildcache 自身の破棄関数) で対処した**。
- **検出の早道と診断改善候補**: WAL の build_start→abort の ts 差 0.107 秒 (configure
  所要時間として短すぎる) が「ビルド失敗」でなく「即死」を示した。abort payload に例外
  文言が乗らない (reason のみ) ことが調査を遅らせた — 改善候補: pipeline._abort の extra
  に例外要約を乗せる (**人間判断待ち**、今回は変更せず)。

## 一次資料ポインタ

- 本走 campaign 3 本 + 再測 campaign 3 本 (上記 id)。各 reports/ に sweep report と
  provenance.json。
- 頻度実測: `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json`
- floor 実測: between_run_floor.py の rr95 追加 (コミット 540b797)
- 敵対レビュー: wf_a80f3f4e-22c (設計) / wf_24065dcb-223 (実装) の journal.jsonl
- 偵察器: コミット 8c97b6a (s8a_trigger_sweep.py + s8a_trigger_freq.py + テスト)
