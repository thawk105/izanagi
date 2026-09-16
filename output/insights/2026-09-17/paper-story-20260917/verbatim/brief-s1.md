# 段 1 brief — 論文ストーリー 2026-09-17 版の全面再導出

- wave: `dev-wave-paper-story-20260917` / branch `worktree-dev-wave-paper-story-20260917` / 起点 local main `bf4f91f51` (2026-09-17 00:33 JST、開始 gate rc=0)
- 依頼の分類: クラス 3 (Phase 作業)。**docs のみ。実装面 (D95 決定 2 = 非 Markdown) の差分ゼロを不変条件とする** — (P1) が維持される限り。

## 研究前進 (1 行)

論文の §8 (証拠の現在地) と §9 (実証状態の非対称表) を 2026-09-17 の正典へ揃え、論文執筆者が「あと何が要るか」を現物で読める最新版を 1 つ作る。完了判定 = `docs/paper-story/2026-09-17.md` の新規追加 + README 3 節の更新 + `check_docs.py` rc=0 + 三軸語走査 rc=0 + 受入全走 child-green + land。

## scope (純増だけ)

- **作る:** `docs/paper-story/2026-09-17.md` — 前版 (2026-09-14、2,310 行) と同じ §0〜§10 の骨格で、**全項目を正典から独立に導き直す** (README 契約・D1858。差分改訂ではない)。
- **更新:** `docs/paper-story/README.md` の 3 節 — (a) 版の履歴表へ 1 行、(b) 「最新 = 」と「2026-09-14 版が前版を訂正した箇所は 4 つ」節を 09-17 版の訂正一覧へ置換、(c) 「最新スナップショット以後に確定したこと」の 3 項目を本文へ吸収して空にする (「次に正典が動いたら積む」の形へ戻す)。
- **触らない:** 旧版 7 本・`results/` 6 稿・`figures/`・`claim-evidence/`・`docs/paper-story-backoff/` (1 byte も変えない)。
- **図 (T-2647 (1)):** (P1) を見よ。
- **scope 外 (依頼の明示):** 仮想リスク向けの gate・検査・台帳・一般化の追加。既存 docs の隣接訂正 (glossary 等) も本題外。

## 確定済みユーザー裁定 (本版が従うもの)

D1858 (項目数は版を強制しない・版は全面再導出)、README の凍結契約、D1993 (A-2/A-6 の解除・但し書き 2 は限定 4 つ付きで外れる)、D1936 項21 + D1993 決定 5 (旧 fig5 の用途制限は期限なし)、D1637 (2 本目の論文との境界: 数値・図は共有しない)、D2044 全 39 項 — 論文素材に直接効くのは 項3 (B-7 は要件充足へ昇格させない)・項8 (A-1 本走の認可は据え置き)・項9 (K2 1 巡の実走認可 → T-2588 で実施済)・項12 (非 silo within-run floor の用途限定解除 → D2083)・項13/D2080 (高域対照は見送り推奨で裁定パッケージ)・項14 (帯 901〜998 は現状維持)・項25 (T-2630 走査境界の到達実測 → 到達した)・項36 (著作権者表記は指定待ち)。D2016 (B-4 記述統計追補は人の主張上限のみ)、D2027 (帯は専用 RUN_KIND を要する)、D2049 (D1640 追補 H1=rr80/H2=rr20)、D2050 (2 本目 cohort の地位は結果前に決める)、D2053 (fig7 の caption 既定)、D2069 (B-4 binary 配置)、D2072 (schema 固定は §5 記入の前提工程)、D2077 (official 床値の退避・再配置は一方向)、D1992 (PolyForm Noncommercial 1.0.0)。

## brief 前に実測した前提 (引数 12 項目)

| # | 項目 | 実測結果 (一次資料) |
|---|---|---|
| 1 | B-10 静的右 tail 本走 | `results/2026-09-16-b10-static-tail-not-observed.md` 実在。group `b10-backoff-grid-20260915T061814Z-545445`、verdict `not-observed-in-any-workload`、18 区間すべて `declining`、`performance_certified: false`。**5 箇所の stale は insight `t2647-b10-tail-downstream.md` §5.1 と README 項目 3 で一致** (§0 前進 9 / §2(g) 項 7 / §8 B-10 ×2 / §9 運用欄)。「執筆時点では真」の分類 |
| 2 | B-7 三走行材料 | entry 1531、`results/2026-09-16-b7-three-run-materials.md` (3 走行・4 対比較・8 arm・限定 20 件)。**D2044 項3: B-7 の要件充足へ昇格させない** (T-2610 未了) |
| 3 | rr5 accepted 較正 | entry 1535、`output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json`、records 2,000,000 (D2026 の取りこぼし率下限で 100 万→200 万)、LLC miss 1.567%、within-run CV 0.97%。3 workload セルが揃った |
| 4 | B-4 binary record と配置 | T-2636 (entry 1544): portable binary record 1 件 (binary 701,760 bytes、admission human-reviewed / s8b-floor、D2057)。T-2697 (entry 1555): 配置規則 `output/env/<env_tag>/binaries/<sha256>` ignored 複写 (D2069)。B-4 の他: T-2547 記述統計追補 (D2016)、T-2632 適格赤 0 件のまま (供給側と適格性側の双方に未充足)、T-2545 publication root、T-2464 開始時刻欄 |
| 5 | official 床値の完走 | entry 1577 [T-2698]: request `1818.nqsv`、96 attempt 完走 `driver_rc=0`、**rr20 = 35,817.945 / rr80 = 46,065.78、両 holdout とも配線下限 0.03 × stock 中央値 (実測 noise 項 1.6〜2.9 万が下限を下回る)**、12 cell valid、`eligible_for_refreeze: true` は producer 自己申告 (D488) で未発効。前段: T-1851 3 走 (entry 1515、launch certificate 初通過・config.h で停止) → T-2650 供給修正 → 完走。次は [T-2724] (freeze v2 候補 document、D2077 の順序) |
| 6 | 非 silo 床値の保留解除 | entry 1576 [T-2634] / D2083: 4 対 (tictoc rr50・rr95、mocc rr50・rr95) の within-run CV を phase doc 8b 節へ登録。between-run は D1373 の関門で起動できず未実施 (mocc/tictoc とも)。前段 T-2224 (entry 1503): tictoc 2 件・mocc rr95 の accepted 較正 |
| 7 | 層 3 screening 射影 | entry 1539: 09-14 版の **6 箇所が執筆時点で既に偽** (§1/§2 第 3 幕/§3/§6/§7/§8 B-9)。対象拡張は 2026-08-25 [T-1291] 着地済 (schema 2 段)。6f169f90 の材料レポート保存 (`historical-not-reclassified`、`certifying_input=false`、E0)。B-9 の残 2 項は裁定停止 / 発効条件待ち。F1 再発 |
| 8 | fig7 | entry 1541 / D2053: `fig7_a2_builtin_backoff_onoff_reject` (旧 attempt と同値・条件記述訂正、fig5 bytes 不変、採用静的 backoff の結論には使えない・期限なし)。README の恒久 erratum 節は fig7 を指していない ([T-2685] 未了) |
| 9 | D2044 の 39 項 | 全文読了 (上記) |
| 10 | README stale 3 件 | B-2 追補 (D2049、2026-09-16 実施)・層 3 (項目 2)・B-10 (項目 3) — 3 件とも本文へ吸収する |
| 11 | §8 A/B 群の状態欄 | A-1: D2044 項8 据え置き継続、T-2590 (pilot 専用分岐の一式) が稼働中 wave (ListAgents 実測)。A-5: 動きなし (要確認)。A-4: 完走 (上記 5)。B-2: 追補実施、完了証明層は要再実測。B-3: T-1957 manifest n (D2071/D2072)。B-4: 上記 4。B-7: 項3。B-9: 上記 7。B-10: 上記 1 + D2027 + D2050。C-1: 非 silo 較正 (上記 6)。C-4: 変化なし (要確認) |
| 12 | 図 | 下記 (P1) |

## 引数に無く、導出で入れる候補 (plan 子が一次資料で検算する)

- **[T-2630] 走査境界の到達実測 (D2044 項25、main 着地 `bf4f91f51`、fold 未)**: `#define`/`#undef` が identity に乗らず、5 変異で **identity 同一のまま実 TU が別プログラム**になった (M3b/M6 は `src_token = "stock"`)。coder 面からは到達しない (`HOLE_ESCAPE`)。修正は裁定待ち。**規律 2 の面。§6「言えないこと」と §8 exact claim の限定に効く** → (P4)
- **[T-2588] K2 ループ 1 巡** (D2044 項9): 既存経路で新提案 1 回評価、`certified` / 719,324.5 tps (CV 1.70%)、proposal-2 (`value=25`) は保存のみ未評価。新機構ゼロ。B-4 非適格 (legacy critic)
- **[T-2224] / [T-2634]** 非 silo 較正 (C-1)、**[T-1907]** v1 patch の別名凍結 (D2075)、**[T-304]** throughput field 実体名 (D2064)、**[T-2600]** anatomy 空間の数え直し (≈234、§5 `ccbench-anatomy.md` の見積に触れる)、**[T-2583]/[T-2635]** 高域 (2 本目の論文側、D2020/D2021/D2080)、**D1992** ライセンス (§5 運用素材)、**D2000〜D2003** 受入の別系列化 (運用)、**[T-1957]** 8c manifest の n (B-3)、**[T-2374]/[T-2397]** A-1 pilot の重複閉鎖、**F1 再発** (層 3)、**[T-2213]** inert A+B+C 不到達、**D1994** t316 inert
- 完了証明層 (`SATISFIABLE_CONDITION_IDS`) と 8c 事前登録の現況、A-5 の状態、C-4 の状態は**現物で再実測**する (前版値を引き写さない)

## 不変条件

1. 凍結物 (旧版 7 本・results 6 稿・figures・claim-evidence・backoff 系列) は 1 byte も変えない (`git diff --stat` で検算)。
2. 数値・日付・判定の出所は一次資料 (権威 bytes・record・decisions 本文・事前登録) だけ。**前版の記述を出所にしない。**
3. B-10 の言い方は事前登録 §4.5 の固定表現に限る。「飽和しない」「飽和点が存在しない」は書かない。`performance_certified: false`。
4. B-7 は充足と書かない (D2044 項3)。3 走行を pool しない (D1993 項 6)。
5. official 床値の実値は floor 案 (未発効) として書き、`eligible_for_refreeze: true` を発効根拠にしない (D488)。床は配線下限で決まっている事実を明記。
6. 行番号参照禁止・basename 参照・`output/insights/` の path は 1 件ずつ実在確認。三軸語走査 (`s8b_holdout_freeze search`) rc=0。`check_docs.py` rc=0。`git diff --check` rc=0。
7. 実装面の差分ゼロ → 変異 matrix は DW-S04 で免除。**受入全走は免除しない。**

## 親の provisional 裁定 (攻撃対象)

- **(P1) 09-15 cohort の論文図は本 wave では作らず「未作成」と書く。** 置き場所は本版が定める: 本体系列 `docs/paper-story/figures/fig8_b10_static_tail_not_observed.{png,pdf,provenance.json}`、生成器 `tools/plotting/plot_b10_static_tail_formal.py` (新図種)、入力は repo 外 group report 3 file (SHA-256 束縛、fig6 の `external_inputs` と同型)、cohort を明示。根拠: FIGURE_CONVENTIONS §10 は実寸 fixture (3 workload × 8 点 × 5 反復 + 境界参照)・本物の Figure の検査・実データ全モード実走・3 成果物確認を要求し、`figures/README.md` の caption/proof chain と provenance pin test も要る = fig7 wave (Codex 子 6 本 + 変異 matrix) と同規模の実装面。依頼は「図を完了条件にしない」。
- **(P2) §9 の 4 文要約の第 4 文は書き換えない。** 前版以後に肯定的 headline 主張は 1 つも増えていない。増えたのは (i) official 床値の初の実値 (配線下限)、(ii) B-10 右 tail の集団判定 (not-observed)、(iii) B-7 の 3 走行材料、(iv) 非 silo 較正 3 件と用途限定解除、(v) B-4 の材料 (binary record・配置・追補)、(vi) 層 3 の screening 射影が対象内だったことの訂正。
- **(P3) 前版の訂正の分類:** 「執筆時点で偽」= 層 3 screening の 6 箇所 (訂正 1 件として冒頭に列挙)。「当時は真・現在地が古い」= B-10 の 5 箇所と official 床値・A-4 関連 (訂正ではなく前進として書く)。README の分類を踏襲。
- **(P4) T-2630 の扱い:** §3 項目 5 (運用方法論の素材)・§5・§6「言えないこと」・§9 運用欄へ入れ、**§8 exact claim の (正しさ) に限定 (v) として足す** — 「`src_token` の identity は `#define`/`#undef` の効果を pre-image に乗せない。A-2/A-6 の新 attempt は無変異の template patch で走っているので判定は動かないが、identity の証明力の上限として書く」。
- **(P5) README の「最新スナップショット以後に確定したこと」は 0 件へ戻す** (3 件とも本文へ吸収)。「2026-09-17 版が前版を訂正した箇所」節を新設し、旧「4 つ」節は履歴として 09-14 版自身の冒頭へ委ねる (README 契約「旧版が自分の前版をどこで訂正したかは、その旧版自身の冒頭が持つ」)。

## 成果物の形・分割

- 親が本文を執筆 (docs-only)。Codex 子: 段 2 plan 1 (read-only、`--reasoning`)、段 3 consult 2 (`--lane sol` / `--lane luna`、正しさ境界と引き写し / 主張の強さと非対称性)、段 6 review 2 (一次資料照合・母集合・射程 / 主張の強さ・分類の一貫性・二重計上・内部整合)。段 5 の実装子は (P1) が維持される限り起動しない。
- 記録: `output/insights/2026-09-17/paper-story-20260917/README.md` + `verbatim/`、spool fragment (worklog 1 本、decisions は設計判断があれば)。
- 受入環境: Pegasus 計算ノード、`tools/dev_wave_wait.py acceptance --lease-optional` (所在 = worklog 1579 の作法)。新規計測ゼロ。
