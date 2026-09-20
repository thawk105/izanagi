# K2 手動 loop 3 巡のデータフロー図 `fig12_k2_manual_loop_dataflow` (稿 2026-09-20 の説明図、値なし) と生成器 (Codex author) を着地させた

authority: none / default_effect: no-state-change (プロセス監査用の凍結記録。可変状態の正本は worklog 末尾と現行 phase doc)。

一次資料 (wave `dev-wave-k2-loop-fig12`、基準 HEAD = local main `947fd160ab44e6ae82b6eab56ee8d70813fda31d`、2026-09-20 13:32〜 JST、台帳 ID 未起票)。
段 1 brief / 段 4 裁定 / 段 6 裁定 (2 巡) は同 dir の `s1-brief.md` / `s4-adjudication.md` / `s6-adjudication.md` / `s6-adjudication-2.md`、
段 5 author・段 6 レビュー 2 本・fix 2 本・焦点再レビューの逐語と投げ文は `verbatim/`、変異の spec / 結果 / 観測 node は同 dir の `mutation-*.json`。
図の正本は `docs/paper-story/figures/README.md` の fig12 節。job dir (repo 外) は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/`。

## 1. 依頼・不変条件・結論

依頼 (command 引数、2026-09-20): 論文ストーリー 2026-09-20 §8 B-6 の材料稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` の 3 巡
(提案 → 評価 → critic × 3、実測の還流 2 回・診断の還流 1 回) のデータフロー図 fig12 を、役割 (tool なしの構造遮断)、親が射影する入力
(whiteboard・current_perf・leading indicators・knowledge manifest・critic 診断の exact 6 field)、評価経路 (Pegasus 計算ノード job → verifier
certified → 実測)、還流の矢印、規律 6 の検査点を 1 枚の schematic (fig2 系と同じ扱いの説明図、性能値を載せない) にし、FIGURE_CONVENTIONS
(生成器 + provenance、caption_source は稿を SHA-256 束縛、F36) に従って figures/README へ登録、図が言わないことを caption に明記、Codex author (D95)、
着手直前の local main から fresh worktree。scope 外 = loop の実走・稿の改訂・一般化した作図 framework。

**依頼文との差 (新事実、段 4 で確定):** 「役割 (planner-v4 / coder-v4-autonomous-k2 / critic、tool なしの構造遮断)」のうち **critic は tool なしではない**
(`.claude/agents/critic.md` frontmatter `tools: ["Read","Grep","Glob","Bash"]`、稿 §1.4・限定 3、B-4 非適格の理由)。図は planner / coder の 2 role を
「no tool access (structural blockade of tool use)」、critic を「legacy role with Bash; not B-4 material」と区別して描き、生成器が role 定義の frontmatter
を読んで JSON の宣言と一致することを検査する。

不変条件を守った: 生成器は判定・値・認証を再計算せず、稿から人が写した流れ JSON を描くだけ (稿は anchor の一意性検査と SHA-256 の記録にだけ使う)。
性能値 (tps / abort 率 / CV / latency / 秒 / %) は図に 1 つも無い (自由文の数量混入は生成器が拒否)。3 走を比較しない (規律 7)。`certified` は正しさ
gate の意味だけ (規律 2)。規律 6 の検査点は role の自己申告として描き、機械 gate と読める描き方をしない。稿・既存図 (fig1〜fig11) の bytes は不変。
F36: provenance が稿の SHA-256 を `caption_source` として持ち、稿は provenance の hash を持たない。

結論: 3 成果物 `docs/paper-story/figures/fig12_k2_manual_loop_dataflow.{png,pdf,provenance.json}` を login node (pegasus02) で生成 (rc=0、2026-09-20
15:02 JST、fix2 後の生成器 commit `d3b8b06ab`)。着地 bytes の SHA-256 は PNG `a6f2b550bd67ddfd05db193493736ef388b2a9f24d60916cb8964607dc3df991`、
PDF `c280037fe72fb60c4420864f1de1df1b28bbf5a7b5ed1c104d13244f2493cfcf`、provenance `76c03b92cb106fa0d73417c1f6357d5b0ded1a6e915ca210013fdb509dd1aaea`。
表示文字列 50 件・矢印 label 7 件・caption 全文は段 6 レビュー B の逐語照合で稿と一致 (不一致 1 件 = 提案日の「記録による」留保の脱落は fix1 で是正)。
README 2 本 (figures / paper-story) に節・行を足し、`tools/plotting/README.md` は受入直前に local main を取り込んでから足した。
**図が言わないこと** (caption の固定文 8 つ): 性能値なし・3 走を比較しない、certified は正しさ gate の意味だけ、planner / coder は tool なし・critic は
legacy で B-4 の材料でない、規律 6 の marker は自己申告で機械 gate でない、知識・診断の因果効果を主張しない (各条件 1 回の別起動)、同 job stock 対照は
未達で裁定待ち・提案値は literal であって結果でない、手続きは各巡の記録による・保存 prompt は送達証明でない、B-6 を判定しない・遮断は tool access に限る。

## 2. 設計 (段 1 brief → 段 4 裁定、軽量版で段 2・3 省略)

- 図: 横 = 4 列 (Round 1 / Round 2 / 「After round 2 (not a round)」= 未評価の proposal-3 / Round 3)、縦 = 6 lane (親の射影 → planner-v4 → coder-v4-autonomous-k2
  → 提案 → Pegasus 計算ノード job の評価 → critic)、上に K2 知識源の帯 (3 巡とも同一 bytes)。列内の縦の流れは細い矢印、巡をまたぐ矢印は実測の還流
  (実線、m1 / m2a / m2b)・診断の還流 (破線、d1)・不在 (点線 + ×、a1 / a2 / a3)。矢印 label は格子下の label bank。巡 3 の評価 lane に破線枠
  「same-job stock control not achieved; ruling pending (T-2795)」。各 role cell に規律 6 の marker (盾 = none detected / 赤 × = detected) と
  「instruction-like content: none detected (self-report)」の 1 行。16 × 11 in、200 dpi、軸なし (figure 座標の Rectangle / Text / Line2D)。
- 流れ JSON `tools/plotting/k2_loop_flow_2026-09-20.json` (schema `izanagi-k2-loop-flow/v1`): roles 3 (`tools_none` bool、definition_path)、lanes 6、
  knowledge、diagnosis_fields (6 field 名の完全一致)、planner_keys 4 / coder_keys 5 (完全一致)、columns 4 (typed `number` / `kind` / 日付 / cells)、
  arrows 7 (生成器の定数 `EXPECTED_ARROWS` と完全一致)、stock_control、discipline6。各要素の `source_anchor` (`§1.4` / `§2.2 巡 1`) は稿の見出し行が
  ちょうど 1 行あることだけを検査 (意味の一致はレビュー B)。自由文は `=`・`%`・単位語・数詞・宣言外の数字入り token を拒否 (token の両端の `()[].:` は剥ぐ)。
  提案 literal・job id・日付・key・6 field・規律 6 の bool は typed field から固定 template で描く。
- (P1) 提案の backoff literal (20 / 25 / 20 / 10) と job id は識別子として描く。レビュー A の判定は (b) 「値は proposal cell に 1 度だけ `backoff literal <v>`
  として出し、caption / 凡例で結果でないことを言う」で、fix1 で採用 (coder cell から値を外した)。
- (P4) role の遮断は生成器が frontmatter を読んで検査し、3 file の SHA-256 を provenance に記録 (生成時点の記録。着地後の一致は要求しない)。
- FIGURE_CONVENTIONS §1 (入力は WAL/dat) との関係は fig3b と同型の「値なし模式図に限った限定」(README 節に明記)。

## 3. 実装 (Codex author `85b463655` → fix1 `7debd680c` → fix2 `d3b8b06ab`、docs `4e6e10ac1`)

- `tools/plotting/plot_k2_loop_flow.py` (自己完結): `load_flow` (key 集合完全一致・重複 key・NaN/Infinity・enum・value 範囲と coder/proposal 一致・
  `evaluated` ⇔ evaluation/critic/評価日・not-a-round の制約・巡 3 だけ diagnosis・key 配列の完全一致・矢印の端点と定数の完全一致・anchor・role frontmatter・
  自由文検査、入力 5 file を bytes で 1 回読み SHA-256 を保持)、`_display_items` (全表示文字列を typed field から組む)、`make_figure` (固定幾何、
  単語境界で折返し、縮小・切捨てなし)、`check_figure_layout` (全可視 Text の figure 内包・所属領域内包・相互非交差 ≤ 1 px²・兄弟領域非交差・marker 非交差・
  **矢印の全線分 × Text bbox の非交差** (slab clipping)、違反は `FigureLayoutError` で保存前に落とす)、`_drawn_items` / `_drawn_arrows` (描いた artist と
  JSON の照合)、`build_provenance` (`izanagi-k2-loop-flow-figure-provenance/v1`)、`_publish_outputs` (layout check → 一時 file → hash → 0644 → `os.link` の
  no-clobber 公開)、`main` (rc 0 / 2)。
- `orchestrator/tests/test_plot_k2_loop_flow.py` (fix2 後 110 ケース): T1 実 JSON の実寸描画 + 構造数 + 全 instance / job の表示、T2 role 束縛 (反転 3 + frontmatter
  異常 5)、T3 異常系 (enum 6 / 未知 key 15 / その他 44 / parser 4 / 凍結矢印 3 / 非一意 anchor 1)、T4 自由文契約 (拒否 11 + 受理 1)、T5 overlap / escape /
  arrow-crossing (実 Figure の座標移動)、T6 publisher を 3 種の衝突で (座標移動、文字列不変)、T7 CLI 3 出力 + 独立 hashlib 照合 + caption_source + drawn_items
  の独立期待 + caption 固定文 + 矢印の独立表 (`RECORDED_PATHS`、稿から手で確定) + 規律 6 反転 (coder / planner / critic)、T8 不正 prefix、T9 着地 bundle
  (未着地は失敗)。自走 harness (`pytest.main`)、subprocess env に `PYTHONDONTWRITEBYTECODE`。
- 親の自走 harness (login): author 後 76 passed / 1 failed (未着地 T9) 7.77 s、fix1 後 104 / 1 13.07 s、fix2 後 109 / 1 16.23 s。
- 焦点走 (計算ノード dispatch、新 test + plain_runner + bytecode guard + collection_config [+ fig 系 README consumer test 2 本]): focus-1 (author 後)
  161 passed / 1 failed (期待赤 T9) 106.6 s、focus-2 (fix1 後、job `12722`) 194 / 1 107.0 s、focus-3b (fix2 + docs 着地後、job `12833`) **309 passed / 0 failed** 106.1 s。
  focus-3 は login の bounded local 試行中に親が insight dir を作って作業木 digest が変わり、fallback を拒否して rc=16 (再投入 1 回、下の §6)。

## 4. 段 6 レビューと fix

- レビュー A (過剰・削除 + P1、GO/NO-GO = NO-GO): must-fix 1 = 規律 6 の自己申告 field が表示にも検査にも使われず反転しても図が不変。should 4 = 限定 6
  (手続きは記録による) が caption に無い / B-6 非判定と遮断の範囲 / 提案値の二重表示 (P1 → (b)) / provenance の arrows が入力の写し。nit 2。
- レビュー B (逐語照合 + 正しさ境界、NO-GO): drawn_items 50 件・arrow label 7 件・caption 全文の照合表 — 値・判定・還流先・role 遮断・正しさ境界はすべて
  稿と一致、不一致 1 = 提案日の「記録による」留保の脱落。must-fix 3 = 提案日の留保 / not-a-round 固有制約の独立負例 / M7 fixture の単一理由。should 3。
- 裁定 (`s6-adjudication.md`): 全所見 real・採用 (refuted 0)、親の目視 8 項 (列見出し「Round N」・括弧の空白・a3 の経路・marker の大きさ・副題・
  `bnode host`・parent lane の文言・lane の空白) を追加。fix1 (Codex、3 file、+319/−134): 23 行の対応表で closed 21 / partial 1 (実測還流の
  「2 回」と描画 3 本の差)。
- 焦点再レビュー (NO-GO): closed 20 / partial 3 / regressed 0。must-fix 2 = caption の `drawn three times` が「還流 3 回」と読める /
  typed bool true を受理するのに caption は「検出なし」を断定し凡例の coder 集約が全 role の any。should 4。裁定 2 巡目 (`s6-adjudication-2.md`): 全採用。
  fix2 (Codex、3 file、+92/−45): caption の還流の文を固定文に (実施回数 2 / 1 と描画本数 3 / 3 を別文)、`EXPECTED_ARROWS` 定数、規律 6 の文と凡例を
  bool に束縛、cell 文言 `instruction-like content: none detected (self-report)`、`in / outside the run-card known set`。6 項目 closed。3 巡目の fix はしない
  (DW-O16 の上限)。残る所見 (なし) は無く、親は変異と受入で裏取りした。

## 5. 変異 (登録 worktree `mut-k2fig12`、DW-M05 正本経路、11 群 14 変異 + positive 1)

- 事前登録: 段 4 で 10 群 (M1〜M10)、段 6 裁定で M11 群 (a / b) を追加、positive control m0 (docstring だけの等価変異)。位置は fix1 / fix2 後も
  anchor 文字列が一意に残ることを `grep -c` で実測 (14 件とも 1)。spec は `mutation-spec-probe.json` (期待 node 空、probe 用) →
  `mutation-spec-final.json` (期待 node 完全集合、sha256 `3b4f83f13ed7c68c6ea961f77a61f474074901ad8943c544c7acd1d6eda335af`)。
- probe (login、fix2 anchor `d3b8b06ab`、`mutation-probe-login-results.json`): 14 負例すべてに kill node あり、m0 は着地 test 以外 0 件。M7 の kill は
  `test_t6_publish_runs_layout_check[overlap/escape/arrow-crossing]` の 3 つだけ (段 6 レビュー B が指摘した文字列不一致の二重理由は fix1 で解消)。
  M1 は `[direction]` を含む enum 6 種 (column-kind も落ちるが、それは後段整合検査の文言差で赤になる型。単一理由の根拠は direction)。
- final (`mutation-final-results.json`、harness `tools/mutation_harness.py --runner-mode dispatch --detached`、変異 worktree は docs 着地 commit
  `4e6e10ac1` に再 anchor して着地 test を baseline で緑にした): **baseline PASSED、m0 SURVIVED、M1〜M11b 14/14 KILLED、期待 node 完全一致 14/14、
  MISMATCH / PARSE_ERROR / TIMEOUT 0** (summary `registered 15 / completed 15 / matching 15`)。計算ノード job `12855`〜`12958` の 17 本
  (collection 1 + baseline 1 + 変異 15)、2026-09-20 15:15〜15:43 JST。final 1 回目 (`mutation-spec-v1-final.json`、job dir) は非 ASCII param の
  nodeid escape で preflight 中止 (計算ノード割当てなし、§6)。
- 等価変異 0。診断文字列だけの赤は無い (kill は全件 receipt / 拒否 / layout の受理集合の変化)。

## 6. 逸脱・near miss

- 段 5 の prompt に「実データ実走の検査欄」として measurement-reflux を「2」と書いたが、JSON の矢印は 3 本 (m2a / m2b で還流 2 回目が 2 宛先へ分岐)。
  author は経路と T1 を維持して報告に差を書き、caption の回数語の扱いは焦点再レビューの must-fix → fix2 で固定文にした。
- 変異 probe の 1 回目 (login) は node 抽出の regex が pytest 標準の `FAILED` 行を前提にしており、この repo の failure digest 形式
  (`IZANAGI_FAILURE rank=… nodeid="…"`) を拾えず 0 件だった。regex を直して fix2 anchor で再 probe した (`mutation-probe-login-2.json`)。
- 焦点走 focus-3 (15:06) は `run_tests.py` の login bounded local 試行中に親が `output/insights/` へ untracked file を作り、試行前後で作業木 digest が
  変わったため dispatch fallback を拒否 (rc=16)。走行中に作業木へ触れずに focus-3b を再投入して緑。
- 段 5 author の投入時、dry-run が作る空 artifact dir を rmdir してから本投入した (memory 既載の罠、実害なし)。

## 7. 工数

codex 6 本 (author 1、review 2、fix 2、focus 1)、計算ノード job = 焦点走 3 (focus-1 / focus-2 / focus-3b) + 変異 16 走 + 受入。login = 自走 harness 3 回、
図の生成 1 回、変異 probe 2 回。
