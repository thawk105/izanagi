# 段 4 裁定 — fig12_k2_manual_loop_dataflow (plan v2 + 変異事前登録)

裁定時刻: 2026-09-20 14:10 JST。基準 HEAD `947fd160a` (= 着手時 local main)。軽量版のため段 2・3 は省略し、設計は brief の (P1)〜(P4) を
親が確定した (攻撃は段 6 のレビュー 2 本が担う)。裁定 inbox (`dev-wave-jobs/rulings-inbox/`) に本 wave 関連の未処理項目なし
([T-2795] は裁定待ちのまま — 図は「未達」と描くだけで先取りしない)。同名 wave の並走なし (ListAgents 13:58 JST、fig11 は別 wave `a-6 certification reject fig11`)。

## 依頼文との差の確定

- 依頼「役割 (planner-v4 / coder-v4-autonomous-k2 / critic、tool なしの構造遮断)」→ **critic は tools を持つ legacy role** (`.claude/agents/critic.md` frontmatter
  `tools: ["Read","Grep","Glob","Bash"]`、稿 §1.4・限定 3)。図は planner / coder の 2 role を「tools: [] (structural blockade)」、critic を
  「legacy role with Bash; not B-4 material」と区別して描く。生成器は role 定義 file の frontmatter を読んで JSON の宣言と一致することを検査する (P4)。
- 依頼「性能値は載せない」→ tps / abort 率 / CV / latency / 所要秒 / 差の % は描かない。**backoff の提案値 (20 / 25 / 20 / 10) と job id は識別子として描く** (P1)。
  レビュー A が「提案値の描画は性能主張に読めるか」を攻撃対象にする。

## plan v2

1. **file:** 生成器 `tools/plotting/plot_k2_loop_flow.py`、流れ JSON `tools/plotting/k2_loop_flow_2026-09-20.json` (生成器の既定入力)、
   test `orchestrator/tests/test_plot_k2_loop_flow.py`。出力 prefix `docs/paper-story/figures/fig12_k2_manual_loop_dataflow` (親が login で生成)。
   自己完結 (matplotlib / numpy / 標準 library のみ、既存生成器を import しない)。雛形 = `tools/plotting/plot_arc_status.py` と
   `orchestrator/tests/test_plot_arc_status.py` (構造・検査・publish・CLI・test の形を踏襲)。
2. **JSON schema `izanagi-k2-loop-flow/v1`** (top-level key は完全一致、未知・不足・重複 key と NaN / Infinity は拒否):
   - `schema`、`figure_created` (ISO 日付)、`caption_source` = `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` (path 固定、生成器は bytes を 1 回読み
     SHA-256 を provenance へ。稿には provenance hash を書かない = F36)、`reference_ids` (自由文で許す ID token の配列、各 `^[A-Za-z]+[0-9]*-?[0-9]+[a-z]?$`、重複不可)。
   - `roles` (3 件、順序固定 planner / coder / critic): `id`、`name` (`planner-v4` / `coder-v4-autonomous-k2` / `critic`)、`definition_path`
     (`.claude/agents/<name>.md`)、`tools_none` (bool)、`label`、`sublabel`、`source_anchor`。生成器は definition_path の frontmatter
     (先頭 `---` 〜 次の `---`) の `tools:` 行を読み、`tools: []` ⇔ `tools_none=true`、非空配列 ⇔ `false` を要求 (不一致・行不在・file 不在は拒否)。
     3 file の SHA-256 を provenance `inputs` (kind=`role_definition`) に記録する。
   - `lanes` (6 件、順序固定 `parent` / `planner` / `coder` / `proposal` / `evaluation` / `critic`): `id`、`label`、`sublabel`、`source_anchor`。
     `planner` / `coder` / `critic` の lane は `roles` の同 id と対応 (label に role name と遮断の有無を出す)。
   - `knowledge`: `label`、`sublabel`、`source_anchor` (§1.2)。全巡共通の帯として描く。
   - `diagnosis_fields`: 固定配列 `["attribution","recommend","avoid","uncertainty","data_boundary","source_sha256"]` (完全一致を要求。3 巡目 `diagnosis-4.json` の key 集合)。
   - `planner_keys` = `["current_perf","leading_indicators","whiteboard","knowledge_input"]`、`coder_keys` = `["baseline","planner_direction","whiteboard","knowledge_input","leakproof_context"]`
     (完全一致を要求。稿 §1.4)。巡 3 の列だけ `diagnosis_key: "k2_critic_diagnosis"` が両 role の key に加わる。
   - `columns` (4 件、順序固定): `id` ∈ {`round-1`, `round-2`, `after-round-2`, `round-3`}、`kind` ∈ {`round`, `not-a-round`}、`label`、`date_proposal`、`date_evaluation`
     (ISO 日付 or null)、`source_anchor`、`cells` = {`parent`, `planner`, `coder`, `proposal`, `evaluation`, `critic`}。
     - `parent`: `sublabel` (自由文)、`has_diagnosis` (bool)。
     - `planner`: `instance` (`planner-<n>`)、`direction` ∈ {`increase`,`decrease`,`explore_both`}、`magnitude` ∈ {`small`,`medium`,`large`}、`discipline6` (自由文)。
     - `coder`: `instance` (`coder-<n>`)、`value` (int 1..1000)、`discipline6` (自由文)。
     - `proposal`: `instance` (`proposal-<n>`)、`value` (int、coder.value と一致必須)、`known_value` (bool)、`evaluated` (bool)、`sublabel` (自由文)。
     - `evaluation`: null (kind=`not-a-round` のときだけ) または {`job` (数字列)、`refused_jobs` (数字列の配列)、`verdict` = `serializable`、`certified` = true、
       `anomalies_none` = true、`stop` = `continue`、`sublabel`}。`proposal.evaluated` ⇔ `evaluation` が非 null。
     - `critic`: null (同上) または {`instance` (`critic-<n>`)、`attribution` (自由文)、`recommend` (自由文)、`discipline6` (自由文)}。
   - `arrows` (配列): `id`、`kind` ∈ {`measurement-reflux`, `diagnosis-reflux`, `absent`}、`from` (`<column-id>.<lane-id>`)、`to` (同、または `absent` の一部で null)、`label` (自由文)。
     `from` / `to` は実在する列・lane の組でなければ拒否。列内の縦の流れ (`parent → planner → coder → proposal → evaluation → critic`) は生成器が固定で描き JSON に持たない。
   - `stock_control`: `label`、`sublabel`、`source_anchor` (§2.2 巡 3)。巡 3 の evaluation cell の脇に破線枠で描く。
   - `discipline6`: `label`、`definition` (凡例の展開文、自由文)。
3. **anchor 検査 (稿の見出し行の一意な存在だけ):** `§<n>` → `^## <n>\. ` がちょうど 1 行、`§<n>.<m>` → `^### <n>\.<m> ` がちょうど 1 行、`§2.2 巡 <k>` → `^#### 巡 <k> `
   がちょうど 1 行。意味の一致は段 6 レビュー A が担う。
4. **自由文検査 (fig3b 型の小さい表示契約):** JSON の label / sublabel / discipline6 / attribution / recommend / definition / arrow label に対し、NFKC 後に `=`、`%` / `％`、
   単位語 (`tps µs μs us ms ns sec seconds percent`)、数詞の固定小集合 (`zero one two three four five six seven eight nine ten eleven twelve twenty thirty hundred thousand million dozen once twice thrice`)
   を拒否し、数字を含む token は `reference_ids` ∪ 全 `instance` ∪ 全 job id (`job <id>` の形で描く) に token 全体一致するものだけ許す。値 (`value`)、日付、job id、
   diagnosis_fields、key 配列は typed field から生成器の固定 template で描く (`value 20`、`job 1216`、`refused at preflight: job 4947`)。生成器の固定文
   (lane 説明・脚注・凡例の骨格) は数字を含まない。
5. **図の形 (16 × 11 in、200 dpi、fig.text + Rectangle + Line2D/FancyArrowPatch、axes なし):**
   - 上: title `K2 manual loop: data flow over three recorded rounds (schematic; no performance values)`、副題は caption_source の basename と figure_created から組み立て。
   - 左端 lane header 列 (幅 ≈ 0.17): 6 lane の label + sublabel (role の遮断の有無は sublabel に `tools: [] (structural blockade)` / `legacy role with Bash; not B-4 material`)。
   - lane `parent` の上に全幅の帯 `knowledge`: K2 知識源 (別機体の測定 WAL 1 件、3 巡とも同一 bytes、受領証は job 内で verified、data boundary 宣言) → 各列の parent cell へ短い矢印。
   - 4 列 (幅比 ≈ round 0.25 / 0.25 / not-a-round 0.13 / 0.25): 列見出し = label + 日付 (proposal / evaluation)。`not-a-round` 列は破線枠・淡色で、evaluation / critic cell に
     `not evaluated` / `no critic` の固定文だけを置く。
   - cell の表示 (固定 template): parent = key 配列 (`planner: current_perf, leading_indicators, whiteboard, knowledge_input` / `coder: …`、`has_diagnosis` なら両方に
     `+ k2_critic_diagnosis`) + sublabel; planner = instance + `direction / magnitude` + R6 marker; coder = instance + `value <v>` + R6 marker; proposal = instance +
     `value <v>` + (`known value` / `outside the known set`) + (`evaluated` / `not evaluated`) + sublabel; evaluation = `job <id>` + (`refused at preflight: job <id>` があれば) +
     `verdict serializable; certified; no anomaly; stop: continue` + sublabel; critic = instance + attribution + recommend + R6 marker。
   - 矢印: 列内の縦の流れは実線細矢印 (固定)。`measurement-reflux` は太い実線で右上へ回り込む (評価 cell の右辺 → 次列 parent cell の左辺、label 付き)、
     `diagnosis-reflux` は太い破線 (critic cell → 巡 3 parent cell、label に `k2_critic_diagnosis` と 6 field 名を typed 配列から)、`absent` は灰色点線 + `×` marker
     (到達先が null なら列右端で止め label を置く)。矢印の label は矢印の所有領域に置き、他 Text と交差しない。
   - R6 marker: 小さな盾形 (marker `"p"` 等) を role cell の右上に置き、凡例で `discipline6.definition` を展開。marker 脇に短い固定語 `R6: no instruction-like content (self-reported)`
     は凡例側だけに置き、cell 内は marker のみ (cell の文字数を増やさない)。
   - 凡例 (下): 矢印 3 種 + R6 marker + `not-a-round` の破線枠。脚注 3 行 (生成器固定、構造参照は field から):
     `Read from the frozen results note <basename>; no performance values are drawn and the three runs are not compared.`
     `Certified means the trace-enabled verify run found the trace serializable with no anomaly; it is not a performance certification.`
     `Discipline-six marks are role self-reports, not a mechanical gate; causal effects of knowledge or diagnosis are not claimed.`
   - 単語境界で折返し、収まらなければ保存拒否 (縮小・切捨て禁止)。
6. **layout check (保存前、Agg 200 dpi、fail-closed):** 全可視 Text の figure 内包・所属領域内包・相互非交差 (交差 ≤ 1 px²)・兄弟領域の非交差 (親子包含は許す)・
   marker の非交差、**矢印の全線分 (FancyArrowPatch の path を線分近似、または自前 polyline) が Text bbox と交差しない**こと。違反で `FigureLayoutError` → 3 成果物を 1 つも出さない。
7. **provenance (`izanagi-k2-loop-flow-figure-provenance/v1`):** `generated_utc`、`figure_created`、`caption_source` ({path, sha256})、`inputs[]` ({kind ∈ flow|caption_source|role_definition,
   path, sha256})、`generator` ({path, sha256})、`outputs[]` (png / pdf の path, sha256)、`drawn_items[]` ({id, kind, text = 実表示文字列}、生成器は JSON から期待集合を組み立て
   保存前に照合)、`arrows[]` ({id, kind, from, to, label})、`roles[]` ({name, definition_path, tools_none, sha256})、`caption`、`argv`、`versions` ({matplotlib, numpy})。自己 hash なし。
8. **caption (英文、provenance と同一、生成器の固定 template + 構造 field。次の内容を必ず含む):** schematic であること、3 巡 / 実測の還流 2 回 / 診断の還流 1 回、
   親の射影 key、planner / coder は role 定義が tools を持たない構造遮断、critic は legacy (Bash) で B-4 の材料でない、評価 = Pegasus 計算ノード job 1 本
   (trace-enabled verify と trace-disabled bench は別 build・別 run、WAL terminal record)、`certified` は正しさ gate の意味だけ (性能認証でも候補間の選択でもない)、
   proposal-3 は診断 key 無しで既知値を再提案し未評価、規律 6 の検査は role の自己申告で形式が違い機械 gate ではない、**言わないこと** = 性能値なし・3 走を比較しない・
   知識と診断の因果効果を主張しない (各条件 1 回の別起動)・同 job stock 対照は未達で裁定待ち、提案値は backoff literal であって結果ではない、caption_source の basename。
   caption に次を書かない: `improvement`、`better`、`faster`、`converge`、`optimal`、`performance certified`、`causal effect of the diagnosis was`。
9. **CLI:** `python3 tools/plotting/plot_k2_loop_flow.py [--repo-root PATH] [--flow PATH] OUT_PREFIX`。prefix basename は `^fig[0-9]+[a-z]*_`。既存の 3 出力のいずれかが
   存在すれば拒否。layout check 通過前に出力 dir・一時 file を作らない。失敗時は新規 file を残さない。公開 file は 0644。
10. **test (実寸描画 ≤ 8 回、全体 20 秒目安):**
    - T1 実 JSON の実寸描画 + layout 通過 + 構造数 (lane 6 / column 4 / role 3 / arrows の件数と kind 別件数) + 全 instance と全 job id の表示。
    - T2 role 束縛: 実 3 file で受理; JSON の `tools_none` を反転 → 拒否; `tools:` 行を欠く frontmatter の tmp copy → 拒否; definition_path 不在 → 拒否。
    - T3 JSON 異常系 parametrize (描画なし): 未知 / 不足 / 重複 key、不正 enum (direction / magnitude / kind / verdict / stop)、value 非 int・範囲外・coder と proposal の不一致、
      `evaluated` と `evaluation` の矛盾、`not-a-round` に evaluation 非 null、arrow の from / to 不在、不正 anchor、非一意 anchor (稿 copy に見出しを複製)、
      diagnosis_fields / planner_keys / coder_keys の不一致、自由文の数量 4 例、caption_source path 不一致。
    - T4 自由文検査の関数単体 (宣言 ID / instance / job token 受理; `38%` `10 tps` `2 µs` `A=0.58` `three runs` `applied twice` 拒否)。
    - T5 layout: 同一 cell 内 2 Text を同座標 → overlap; Text を figure 外へ → escape; **Text を矢印線分上へ移動 → arrow crossing**; いずれも `FigureLayoutError`、file を残さない。
    - T6 `_publish_outputs` に衝突 Figure を直接渡す → 拒否、tmp に file が残らない (publisher が check を呼ぶことの正例)。
    - T7 CLI 実走 (tmp prefix): rc=0、3 file、0644、PNG / PDF magic、provenance の key 集合、`inputs` / `generator` / `outputs` / `roles[].sha256` を独立 hashlib で照合、
      `caption_source.sha256` = 稿の実 SHA-256、`drawn_items` = JSON から独立に組んだ期待、`arrows` = JSON の arrows、caption の固定句、再実行は rc=2 `output already exists` で bytes 不変。
    - T8 不正 prefix → rc=2、file なし。
    - T9 着地 test `test_landed_fig12_bundle_when_present`: `docs/paper-story/figures/fig12_k2_manual_loop_dataflow.{png,pdf,provenance.json}` の 3 file 実在 → provenance の
      `caption_source.sha256` が稿の現 SHA-256 と一致 (稿は凍結物) → `caption` が `docs/paper-story/figures/README.md` に逐語で含まれる → README の fig12 節
      「## 着地 bytes の SHA-256」の 3 行 (`- \`<basename>\` SHA-256: \`<64 hex>\``) と現物一致。role 定義の SHA-256 は**記録のみ**で現物一致を要求しない (role 定義は凍結物でない)。
      bundle 全欠落は skip でなく失敗 (fig10 型)。**親が着地させるまで赤 = 期待赤。**
    - 自走 harness (`if __name__ == "__main__": sys.exit(pytest.main([__file__, "-x"]))`)、subprocess の env に `PYTHONDONTWRITEBYTECODE` (F42 / F521)、`skiputil` は使わない
      (skip する test が無い) か使うなら `Skip`。
11. **README (親):** figures/README.md に一覧 1 行 + fig12 節 (何を示す図か / 既存図との関係 (fig2 系と同じ「説明図」扱い、fig3b と同じ値なし模式図、fig11 とは独立) /
    入力 / 再現 / 再現できるのは内容であってバイト列ではない / 作図規約への適合 / キャプション正文 / proof chain / 着地 bytes の SHA-256)。`docs/paper-story/README.md` の
    results 行「図は無い」→「図 12」+ 図の着地注記。`tools/plotting/README.md` は受入直前 (local main 取り込み後)。
12. **JSON 内容 (author が稿 §0.1 / §1.2 / §1.4 / §2.1〜§2.5 から写す。性能値・数量は書かない):**

`reference_ids`: 使うものだけ (候補 `K2`、`B-4`、`T-2795`、`R0`、`D2044`、`D2155`。未使用は入れない)。

roles:
- planner / `planner-v4` / `.claude/agents/planner-v4.md` / tools_none true / label `planner-v4` / sublabel `tools: [] (structural blockade); outputs direction and magnitude, no value, no mechanism` / anchor `§1.4`
- coder / `coder-v4-autonomous-k2` / `.claude/agents/coder-v4-autonomous-k2.md` / tools_none true / label `coder-v4-autonomous-k2` / sublabel `tools: [] (structural blockade); outputs a backoff literal and self-reports knowledge use and data boundary` / anchor `§1.4`
- critic / `critic` / `.claude/agents/critic.md` / tools_none false / label `critic` / sublabel `legacy role with Bash; reads digest and WAL; not B-4 material` / anchor `§1.4`

lanes (label / sublabel / anchor):
- parent / `Parent session: typed projection` / `builds the planner and coder input JSON, sends the full JSON inline, runs preflight checks on the login node` / `§1.4`
- planner / (role planner の label) / (role planner の sublabel) / `§1.4`
- coder / (role coder の label) / (role coder の sublabel) / `§1.4`
- proposal / `Proposal file` / `one backoff hole literal; known-value re-proposals are recorded, not counted as new values` / `§1.5`
- evaluation / `Evaluation: Pegasus compute-node job` / `separate trace-enabled verify build and trace-disabled bench build; campaign WAL terminal record` / `§1.1`
- critic / (role critic の label) / (role critic の sublabel) / `§1.4`

knowledge: label `K2 knowledge source (identical bytes in all rounds)` / sublabel `one measurement WAL from another machine; manifest receipt verified inside the job; declared as data, not instructions` / anchor `§1.2`

columns:
- round-1 / round / label `Round 1` / date_proposal 2026-09-16 / date_evaluation 2026-09-16 / anchor `§2.2 巡 1`
  - parent: has_diagnosis false; sublabel `current_perf taken from the knowledge source's last record; whiteboard empty`
  - planner: planner-1 / decrease / medium / discipline6 `uncertainty prose: no instruction-like strings`
  - coder: coder-1 / 20 / discipline6 `structured field: no instruction-like content`
  - proposal: proposal-1 / 20 / known_value true / evaluated true / sublabel `known value re-proposal, evaluated under the round authorization`
  - evaluation: job `1216` / refused_jobs [] / serializable / certified / anomalies_none / continue / sublabel `bnode host; legacy verify condition`
  - critic: critic-1 / attribution `not attributable to any design choice` / recommend `same-job stock control first (R0)` / discipline6 `trust-boundary section: no instruction-like strings`
- round-2 / round / `Round 2` / date_proposal 2026-09-16 / date_evaluation 2026-09-18 / anchor `§2.2 巡 2`
  - parent: has_diagnosis false; sublabel `current_perf and whiteboard from the round one measurement`  (※ `one` は数詞 → `from the previous evaluation` にする)
  - planner: planner-2 / decrease / small
  - coder: coder-2 / 25
  - proposal: proposal-2 / 25 / known_value false / evaluated true / sublabel `outside the known set`
  - evaluation: job `4954` / refused_jobs [`4947`] / … / sublabel `the refused submission did not reach the campaign`
  - critic: critic-2 / attribution `not attributable; runs are not contemporaneous` / recommend `decrease, large; same-job stock control first (R0)`
- after-round-2 / not-a-round / `After round 2 (not a round)` / date_proposal 2026-09-18 / date_evaluation null / anchor `§2.2 巡 2`
  - parent: has_diagnosis false; sublabel `same measurement as the next column; no diagnosis key (typed path not yet implemented)`
  - planner: planner-3 / decrease / medium
  - coder: coder-3 / 20
  - proposal: proposal-3 / 20 / known_value true / evaluated false / sublabel `known value re-proposal; not evaluated by ruling`
  - evaluation: null; critic: null
- round-3 / round / `Round 3` / date_proposal 2026-09-19 / date_evaluation 2026-09-19 / anchor `§2.2 巡 3`
  - parent: has_diagnosis true; sublabel `same measurement as the previous column, plus the diagnosis built from the critic verbatim of round two` (※ `two` は数詞 → `of the previous round`)
  - planner: planner-4 / decrease / large
  - coder: coder-4 / 10
  - proposal: proposal-4 / 10 / known_value false / evaluated true / sublabel `outside the known set; equals the diagnosis candidate (self-reported as advice, not causation)`
  - evaluation: job `10761` / refused_jobs [] / … / sublabel `same-job stock control not achieved`
  - critic: critic-3 / attribution `not attributable (third consecutive round)` (※ `third` は許容: 数詞集合に無い。ただし避けて `again`) / recommend `same-job stock control first (R0)`

arrows:
- m1 measurement-reflux round-1.evaluation → round-2.parent `measurement reflux: current_perf and whiteboard`
- m2a measurement-reflux round-2.evaluation → after-round-2.parent `measurement reflux`
- m2b measurement-reflux round-2.evaluation → round-3.parent `measurement reflux: current_perf and whiteboard`
- d1 diagnosis-reflux round-2.critic → round-3.parent `diagnosis reflux: k2_critic_diagnosis (typed path), identical for planner and coder`
- a1 absent round-1.critic → round-2.parent `no typed path: diagnosis not delivered`
- a2 absent round-2.critic → after-round-2.parent `no diagnosis key`
- a3 absent round-3.critic → null `no further proposal in the recorded scope`

stock_control: label `same-job stock control` / sublabel `not achieved; ruling pending (T-2795)` / anchor `§2.2 巡 3`
discipline6: label `discipline-six check` / definition `role self-report that external input contained no instruction-like strings; coder as a structured field, planner in uncertainty prose, critic in a trust-boundary section; not a mechanical gate`

(自由文の数詞・単位・`=` は author が検査に通る言い換えへ直す。意味を変えない。)

## 変異事前登録 (DW-M01、単一理由性。位置は実装後に関数名で確定)

| # | 位置 (関数) | 変異 | kill する test | 赤理由 (1 つ) |
|---|---|---|---|---|
| M1 | JSON 読込の enum 検査 (direction / magnitude / kind / verdict / stop) | membership を恒真 | T3 (不正 enum) | 不正 enum が受理される |
| M2 | JSON 読込の key 集合検査 | 完全一致 → 部分集合 | T3 (未知 key 注入) | 未知 key が受理される (key 集合検査は 1 か所) |
| M3 | 自由文検査関数 | 早期 return | T4 | 数量が受理される |
| M4a | layout の交差面積 `_intersection` | 常に 0 | T5-overlap | Text 交差が検出されない |
| M4b | layout の内包 `_contains` | 常に True | T5-escape | 逸脱が検出されない |
| M4c | layout の矢印線分 × Text 交差検査 | 常に False (交差なし) | T5-arrow | 矢印が Text を横切っても検出されない |
| M5 | provenance の `caption_source.sha256` | 別の 64-hex 定数 | T7 (独立 hashlib) | caption_source の hash 不一致 |
| M6 | role 束縛検査 (`tools_none` ⇔ frontmatter) | 常に一致扱い | T2 (反転 JSON) | 遮断の宣言が検査されない |
| M7 | `_publish_outputs` | `check_figure_layout` 呼出し削除 | T6 | 検査なしで公開される |
| M8 | prefix 検査述語 | 常に受理 | T8 | 不正 prefix が受理される |
| M9 | anchor 検査 | 「ちょうど 1 行」→「1 行以上」 | T3 (非一意 anchor) | 非一意 anchor が受理される |
| M10 | `drawn_items` の期待集合との照合 | 照合を削除 | T7 (JSON の 1 cell を描画後に別文字列へ差替える test、または provenance と JSON の独立照合) | 描いた文字列と JSON の不一致が通る |

登録 10 件。等価変異が実装後に判明したら除外して台帳に理由を書く。実装後 (段 6) に位置を実行番号へ確定して走らせる (probe → final)。

## scope の再確認

- 実装面 = 生成器 + JSON + test (Codex author、unit worktree `.codex/worktrees/k2fig12-unit`)。docs = 親。生成物 = 親が login で生成。
- 段 6: 親の焦点走 → read-only review 2 本 (A: 表示文字列・caption と稿の逐語照合、B: 生成器・test の正しさ境界・過剰・恒真) → fix 子 → 焦点再レビュー → 変異 10 件 → 受入。
- 「実装しない」裁定ではないので 5 → 6 → 7 → 8 → 9 の通常遷移。
