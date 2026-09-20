---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-paper-methods-ja-2026-09-20
seq: 1
title: 本体論文 (日本語) の方法節と実装対応メモを 09-10 以後の手順 (A-1 sized の投入経路と認可 record、A-2 / A-6 certification の受領証束縛、B-10 事前登録 2 本と driver、採用候補 2 genome の検証相、K2 型付き critic 診断と stock 対照口、mocc trace-hook と witness、床値 pair protocol v3、ccbench pin 前進) を反映して再導出し、実装済みと使用を分けた — read-only レビュー 1 本 (must-fix 4 / should-fix 3、全件反映) + 焦点再レビュー 1 本 (closed 9 / GO) (docs のみ、branch worktree-dev-wave-paper-methods-ja-2026-09-20、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数。逐語は insight README 冒頭) は「本体論文 (日本語) の方法節と実装対応メモを再導出する (docs-only、
  軽量版 DW-C00、台帳 ID 未起票の新規執筆依頼)。前稿 `output/insights/2026-09-10/paper-methods-ja/{methods,implementation}.md` (entry 1430) は
  09-10 以後の手順 (A-1 sized policy v3 と 1 attempt 認可の投入経路、A-2 / A-6 certification の receipt 束縛、B-10 静的右 tail・待ち方 grid の
  事前登録と driver、採用候補 2 genome の検証相、K2 手動 loop の型付き critic 診断 D2155、mocc の trace-hook と witness、床値 pair protocol v3)
  を反映していない。… 実装済みの機構と各実験で実際に使った機構を区別し、certified の意味を story §6 に揃える。英訳・新規実験は scope 外。
  仮想リスク向けの gate・検査・台帳の追加は scope 外」。
- **閉じた。** 成果物は `output/insights/2026-09-20/paper-methods-ja/methods.md` (方法節草稿、6 節。性能値・図は転載しない) と同
  `implementation.md` (実装対応メモ: 前稿の対応表 19 行を現行 main で再照合、09-10 以後の機構 15 行を「実装アンカー / 使用した走行 /
  実装済みだが未使用・上限」で分け、読み分け表 13 行、実走・契約・未了の境界)、同 `README.md` (wave 記録、brief・レビュー・検算の逐語は
  `verbatim/`)。前稿 2 本・story・README・results 稿・実装は 1 byte も変えていない。**新しい測定・合成・判定は 1 件も行っていない。**
- 起点 local main `fec4a8187` (fresh worktree、開始 gate rc=0)。段 6 レビューの後、peer 通知を契機に local main を読み直し
  ([T-2304] pin 前進 `511c9538` → `e9e477ca` の着地 `482f19b88`) を自 commit 0 で `--ff-only` 取り込み、submodule を揃え、pin に触れる記述を
  再照合した (基準 SHA、pin が動かす identity の層と動かさない層、旧系列は固定 checkout から走ること、X / P 計装は pin の tree に無く patch で
  当てること、G2 witness は `e9e477ca` の `#if TRACE` 内にあり軽量 witness は hook branch にあること)。
- certified の定義は story 2026-09-20 版 §6 の 2 文 (固定条件で certified な correctness の観測 = 性能の判定ではない、build された bytes に
  ついての判定で要求構成の build を含意しない) に揃え、限定 (i)〜(v) のうち (ii) (実 argv の独立記録なし、束縛は campaign lock と pipeline
  constructor) と (v) (`src_token` の限界) を本文に書いた。
- 前稿から一次資料で直した点: critic の拒否還流 3 関数の所在は `orchestrator/critic/digest.py` (前稿は `p3_s4_loop.py` 帰属)、層3 の
  機序仮説層は v3 が K2 2 巡目で適用済み (前稿「未実装」)、Silo 固定は D2114 で解除、凍結 v2 g1 は entry 1742 (D2180) で発効済み
  (story 2026-09-20 版の「未発効」は古い)。執筆中に一次資料で確かめた点: verify fan-out は policy 3 本の `scheduler.nodes` が 5 だが
  A-2 / A-6 の取得済み attempt は 1 node、検証相は条件関門を通していない (identity 束縛のみ)、certification の outer status の判定順は
  `collect_results` の分岐順、K2 の両 role 組立ては `k2_next_generation_inputs`。
- 段構成: 軽量版 (段 2・3 省略、段 5 は親の執筆)。段 6 は D2148 項 11 の read-only 独立レビュー 1 本 (2 レンズ、`gpt-6-astra` / medium、
  33 call、accepted): **NO-GO、must-fix 4 / should-fix 3 / refuted 2**。must-fix = (1) K2 stock 対照を「無 backoff」と誤記 (実装は内蔵の適応
  backoff `BACK_OFF=1, BACKOFF_FIXED=-1`、D2183)、(2) 成果物に残る admission record (`admitted` / `use_class` / `unestablished_meaning_macros` /
  `record_ids`) と残らない元 record 本体の取り違え、(3) 前稿の B-4 実装限界 3 点 (writer create-only、report §7.1 の 4 分類未実効、launcher
  単一 arm) の根拠なき削除、(4) MoCC pin 前進を「未解禁」と書いた (D2150 項 1 で承認済み)。should-fix = B-10 report の実行日 (09-05) と
  裁定日 (09-07) の混同、「使用欄に無い機能は走っていない」の全称、限定 (ii) の未明示。全件 real として反映し、現行 code
  (`p3_b4_raw_record_producer.py` の `O_EXCL`、`p3_b4_material_report.py` の `section_7_1_four_classifications_operationalized: False`、
  `p3_b4_launcher.py` の `--arm`、`_CONDITION_ADMISSION_KEYS`、`certification.json` の `workload_argv_observation`) で確認した。
  焦点再レビュー 1 本 (11 call): **closed 7 / partial 0 / regressed 0、refuted 2 維持、pin 前進の反映 9 項目すべて一致、GO**。nit 2 件
  (旧基準表示の残り、README のメタデータ) は親が直した。
- 検査: `check_docs.py` rc=0 (3 回)、稿が引く D 39 種・entry 19 種の見出し実在、repo 内 path の実在、hex の現物照合。三軸語走査は本 wave では
  走らせていない (稿は holdout の識別子・値を持たない)。変異 matrix は実装面差分ゼロで免除 (`DW-S04`)。受入全走は記録 commit の tip で
  門番 loop から投入する (結果は job dir の受領証と land の記録が持つ。child-green でなければ land しない)。
- 限界・言わないこと: 本稿の「実装済み」は静的照合であり、その機構を使った正式実験の完走ではない。A-1 attempt-0002 の投入、K2 の pair 投入、
  B-4 の w2 / finalize、mocc の探索、新 pin の main からの旧系列の再開はいずれも本 wave の外で、稿はそれらを数えない。
- 専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-2026-09-20/HANDOFF.md`。「dev-wave 改善候補」はなし。
- 工数: codex 子 2 本 (review 1 = 33 call / 約 11 分、focus 1 = 11 call / 約 4 分、すべて `outcome=accepted`)。計算ノード job は受入のみ。
  親の読み込み: story 2026-09-20 版の §2 第 3 幕・§5・§6・§8、worklog entry 20 本、D 約 15 本、insight README 12 本、campaign / verifier の
  該当 module。

## 次の一手差分

### carry

- [T-2792]
- [T-2795]
