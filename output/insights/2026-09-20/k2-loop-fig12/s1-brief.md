# 段 1 brief — K2 手動 loop 3 巡のデータフロー図 fig12 (schematic) (2026-09-20 13:55 JST)

- 研究前進: 論文ストーリー 2026-09-20 §8 B-6 の材料稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` (図は無い、
  paper-story README の results 行も「図は無い」) に対応する説明図 fig12 を足す。稿 §0.1 の「1 巡 = 提案 (planner + coder) → 評価 1 本 → critic」を
  3 巡、実測の還流 2 回 (巡 1 → 巡 2、巡 2 → 巡 3)、診断の還流 1 回 (critic-2 → 巡 3、`k2_critic_diagnosis` の exact 6 field) を 1 枚に描く。
  完了判定 = `docs/paper-story/figures/fig12_k2_manual_loop_dataflow.{png,pdf,provenance.json}` の 3 成果物が login で rc=0、figures/README の fig12 節
  (caption 正文・着地 SHA-256 3 行)、test 緑 (計算ノード dispatch)、変異 matrix 期待どおり、受入緑、land。
- scope (純増): 新 file `tools/plotting/plot_k2_loop_flow.py` (生成器)、`tools/plotting/k2_loop_flow_2026-09-20.json` (流れの射影 JSON、生成器の既定入力)、
  新 test `orchestrator/tests/test_plot_k2_loop_flow.py`、fig12 3 成果物、`docs/paper-story/figures/README.md` (一覧 1 行 + fig12 節)、
  `docs/paper-story/README.md` (results 行の「図は無い」→「図 12」+ 図の着地注記 1 項、fig10 の先例)、`tools/plotting/README.md` (command 例 1 節、
  **受入直前に local main を取り込んでから**足す — 稼働 3 wave が触る)、insight dir `output/insights/2026-09-20/k2-loop-fig12/`、worklog fragment。
  不変: 稿 (results/ 全 file)、既存図 (fig1〜10) と provenance、`plot_arc_status.py` ほか既存生成器、role 定義 `.claude/agents/*`、loop の経路
  (`p3_s4_loop.py` / job body)、正しさ gate。scope 外 = loop の実走、稿の改訂、一般化した作図 framework、fig11 (欠番は依頼どおり)。
- 確定済みユーザー裁定: 本 wave 引数 (fig2_backoff_mechanism と同じ扱いの説明図、性能値を載せない、図が言わないことを caption に明記、Codex author = D95、
  fresh worktree、plotting README は受入直前)、D2155 (診断 = exact 6 field を両 role へ同一に渡す)、D2148 項 2 (2 巡目の preflight 拒否は事後承認)、
  D2044 項 9 / D2120 項 1 (巡 1 / 2 の認可)、[T-2795] 裁定待ち (同 job stock 対照は未達 — 図は「未達」と描き裁定を先取りしない)。
- 不変条件: 規律 1 (verify = trace-enabled、bench = trace-disabled の別 build・別 run を図に分けて描く)、規律 2 (`certified` は正しさ gate の意味、
  性能認証と読める描き方をしない)、規律 6 (検査点は role の**自己申告**で形式が role ごとに違い、機械 gate ではない — 図と caption で言い切る)、
  規律 7 (3 走を比較しない)、F36 (稿に provenance hash を書かない = provenance が稿の SHA-256 を `caption_source` として持つ)、
  FIGURE_CONVENTIONS §5〜10 (図中ラベル短く、provenance、計測機の外、fail-closed layout check、実寸 fixture = 実 JSON、実データ実走)。
  §1〜4 は数値図の規約で、本図は fig3b 型の値なし模式図として「入力は凍結稿から人が写した射影」に限定する (fig3b 節と同型の限定)。
- 入力 (2026-09-20 13:5x JST 実測): caption_source = 稿 `1b0f6f568f17af4967362cb864a14c18ef9220f826e257c113da0065bb512758`。3 巡目
  `materials/planner-input-4.json` key = current_perf / k2_critic_diagnosis / knowledge_input / leading_indicators / whiteboard、`coder-input-4.json` key =
  baseline / k2_critic_diagnosis / knowledge_input / leakproof_context / planner_direction / whiteboard、`diagnosis-4.json` = attribution / avoid /
  data_boundary / recommend / source_sha256 / uncertainty (稿 §1.4 / §2.2 と一致)。role frontmatter: `planner-v4` と `coder-v4-autonomous-k2` は
  `tools: []`、`critic` は `tools: ["Read","Grep","Glob","Bash"]` (稿 §1.4 の「legacy」と一致)。login pegasus02 に matplotlib 3.10.9 / numpy 2.2.6。
  `docs/paper-story/figures/` に列挙型 pin は無い (test 検索で fig5/fig7 型の「着地していれば caption が README にある」検査のみ)。
- **依頼文との差 (新事実、段 4 で確定):** 依頼の「役割 (planner-v4 / coder-v4-autonomous-k2 / critic、tool なしの構造遮断)」のうち **critic は tool なしではない**
  (Bash 持ちの legacy role、稿 §1.4・限定 3、B-4 非適格の理由)。図は planner / coder だけを「tools: [] の構造遮断」と描き、critic は「legacy (Bash あり)」と
  区別して描く。依頼の意図 (遮断の所在を示す) はこれで満たす。
- (P1) 図に出す数: backoff の提案値 (20 / 25 / 20 / 10 = 提案の同一性、稿 §2.1 の `value` 列) と識別子 (job 1216 / 4947 / 4954 / 10761、role の巡番号) は出す。
  **性能値 (tps / abort 率 / CV / latency / 所要秒) は 1 つも出さない。** 生成器の自由文検査は fig3b 型 (単位語・`=`・`%`・宣言外の数字 token を拒否) とし、
  提案値と job id は typed field で宣言して固定 template で描く。
- (P2) 図の形: 横 = 巡 (巡 1 / 巡 2 / 巡 3)、縦 = 段 (親の射影 → planner-v4 → coder-v4-autonomous-k2 → 提案 → Pegasus 計算ノード job の評価
  [build trace / perf 別 → verify (trace-enabled) → bench (trace-disabled) → WAL] → critic)。巡をまたぐ矢印 = 実測の還流 2 本 (評価 → 次巡の親の射影:
  `current_perf` / `whiteboard`)、診断の還流 1 本 (critic-2 → 巡 3 の親の射影: `k2_critic_diagnosis` exact 6 field、planner / coder の両入力へ同一)。
  描くべき否定: critic-1 → 巡 2 の型付き入力は**無い** (経路未実装)、巡 2 の実測で作った proposal-3 (planner-3 / coder-3、診断 key 無し) は
  **既知値 20 の再提案で未評価**、巡 3 の評価・critic-3 の後の提案は**無い**、同 job の stock 対照は**未達**。巡 2 の job 4947 は preflight 拒否 (評価に未到達)。
  親の射影 = planner 入力 key 4 (+ 巡 3 で `k2_critic_diagnosis`)、coder 入力 key 5 (+ 同)、知識 manifest (K2、wal-only 1 source、受領証は job 内で verified)。
- (P3) 規律 6 の検査点: 各 role 出力に小さな marker を置き、凡例で「self-reported; form differs by role (coder: structured field
  `instruction_like_content_detected=false`; planner: `uncertainty` prose; critic: trust-boundary section); not a mechanical gate」と展開する。
  検出結果は 3 巡すべて「指示めいた文字列なし」(稿 §2.4) を marker の文言に写す。
- (P4) 生成器は稿を読んで値を再計算しない。JSON の各要素は `source_anchor` (稿の見出し、例 `§2.2 巡 1`、`§2.3`、`§2.4`) を持ち、生成器はその見出し行が稿に
  **ちょうど 1 行**あることだけ検査する (fig3b 型)。加えて role の遮断は `.claude/agents/{planner-v4,coder-v4-autonomous-k2,critic}.md` の frontmatter
  `tools:` を読んで JSON の宣言 (`tools_none: true/false`) と一致することを fail-closed で検査し、3 file の SHA-256 を provenance に記録する。
- 成果物の形: provenance schema `izanagi-k2-loop-flow-figure-provenance/v1`。`inputs` (flow JSON / caption_source 稿 / role 定義 3 file、path + SHA-256)、
  `generator` (path + SHA-256)、`outputs` (png / pdf)、`drawn_items` (id・kind・実表示文字列)、`arrows` (from / to / kind ∈ measurement-reflux /
  diagnosis-reflux / flow / absent)、`caption` (英文、`Figure {N}` は prefix から)、`argv`、`versions`。3 出力は既存があれば拒否 (上書きしない)。
- caption に明記する「言わないこと」: 性能値なし・3 走を比較しない、知識・診断の因果効果を主張しない (各条件 1 回の別起動)、同 job stock 対照は未達
  ([T-2795] 裁定待ち)、critic は legacy (Bash) で B-4 の材料ではない、`certified` は正しさ gate であって性能の判定・候補間の選択ではない、
  規律 6 の検査は自己申告で機械 gate ではない、診断が「届いた」「参照したと申告した」までで「効いた」ではない。
- 分割方針: 既定の軽量版 (DW-C00)。段 2・3 省略 (設計択一は fig3b / fig10 の先例で閉じ、正しさ防壁・受理集合に触れない)。段 5 = Codex author 1 本
  (生成器 + JSON + test、unit worktree)。段 6 = 親の焦点走 (計算ノード dispatch) → read-only レビュー 2 本 (A: 図の全表示文字列と caption を稿 §0.1〜§2.6 と
  逐語照合 = 一次資料からの事実再抽出、B: 生成器・test の正しさ境界・過剰・layout check の恒真) → fix 子 → 焦点再レビュー → 変異 matrix (段 4 で事前登録)
  → 受入。段 7〜9 親。
- 受入・実測環境: 作図は login (pegasus02、計測機の外)。焦点走・変異・受入は計算ノードへ dispatch。図の生成に計測は無い。
- DW-G05: 放置時 → B-6 材料稿に図が無いまま (結果節の図 12 欠落)。certified 選択・レポートの値・受理集合・参照は変わらない。
- 条件 dispatch: O08 / O09 / O10 不成立 (新規 file のみ、freeze・oracle・既存 proof chain・凍結 bytes に触れない)、O11 不成立 (削除なし)、O13 不成立
  (gate 新設なし。test は生成器の単体・着地検査で受理集合を変えない)、O20 成立 (背景 job、gate rc=0 済、worktree lock 済)。
