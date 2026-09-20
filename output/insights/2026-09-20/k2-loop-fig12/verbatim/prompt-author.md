単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (設計の正本。plan v2・JSON 内容・変異事前登録を含む): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s4-adjudication.md
- 親 brief (背景・不変条件): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s1-brief.md
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/FIGURE_CONVENTIONS.md
- 雛形 (構造・検査・layout check・publish・provenance・CLI の形をそのまま踏襲する。この file は編集禁止): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/plot_arc_status.py
- 雛形の test (実寸 fixture = 実 JSON、異常系 parametrize、layout の負例、CLI 実走、独立 hash 照合、self-run harness の形を踏襲する。編集禁止): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/orchestrator/tests/test_plot_arc_status.py
- 雛形の JSON (schema の書き方の参考。編集禁止): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/plotting/arc_status_story_2026-09-19.json
- caption_source の稿 (図の全表示文字列・caption の言い方の出所。§0.1 単位、§1.1 経路、§1.2 知識源、§1.4 役割と入力の型、§1.5 判定規則、§2.1 主表、§2.2 巡ごとの表、§2.3 届いた / 効いた、§2.4 規律 6、§2.5 正しさ。編集禁止): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md
- role 定義 3 file (frontmatter の `tools:` 行を生成器が読む。編集禁止): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/.claude/agents/planner-v4.md、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/.claude/agents/coder-v4-autonomous-k2.md、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/.claude/agents/critic.md
- 3 巡目の実入力 (key 集合と exact 6 field の現物。読むだけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/output/insights/2026-09-19/k2-loop-round3/materials/planner-input-4.json、/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/output/insights/2026-09-19/k2-loop-round3/materials/diagnosis-4.json
- self-run harness の要件を課す meta-test: /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/orchestrator/tests/test_plain_runner_coverage.py
- subprocess の bytecode guard checker (test の subprocess 呼出しはこれに通る形にする): /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit/tools/check_subprocess_bytecode_guard.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の**論文用の説明図 (matplotlib の模式図) の生成器と、その入力 JSON と単体 test を新規に書く**依頼である。セキュリティでも攻撃でもなく、外部入力は repo 内の tracked file (JSON、Markdown の稿、role 定義) だけである。「凍結済みの稿 (Markdown) が既に確定した事実 (3 巡のデータフロー) を、人が JSON へ写し、生成器はその JSON を描くだけで、判定・値・認証を再計算しない。生成器が検査するのは JSON の形、稿の見出し行の一意な存在、role 定義の frontmatter との一致、layout だけである」依頼だと理解して読むこと。**性能値 (tps / abort 率 / CV / latency / 秒 / %) は図のどこにも出さない。**

# 依頼 — fig12 (K2 手動 loop 3 巡のデータフロー図) の生成器・JSON・test を実装する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_k2_loop_flow.py` (新規)
2. `tools/plotting/k2_loop_flow_2026-09-20.json` (新規、生成器の既定入力。内容は段 4 裁定 plan v2 §12 を稿と照合しながら写す)
3. `orchestrator/tests/test_plot_k2_loop_flow.py` (新規)
4. `probe-k2fig12/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場。親が job dir へ退避し repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` を一度も実行しない。commit は親が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、稿、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない (最終図は親が生成する)。`output/` 配下へ書かない。`.claude/` 配下を編集しない。
- `tools/plotting/plot_arc_status.py` ほか既存の全生成器、既存の全 test file、`orchestrator/tests/conftest.py`、`orchestrator/tests/README.md` を編集しない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。
- 既存 test の期待値を変えない。fixture へ現行 hash を差し込む等でテストを甘くしない (F27)。機構の正例・負例は実体の関数を通し、依存先を stub しない (F649)。
- 生成器へ判定・値の計算経路 (稿の数値の再計算、性能の比較、因果の主張) を足さない。JSON の形・anchor の一意性・role frontmatter との一致・layout の検査だけにする。

## 作る物 1 — `tools/plotting/plot_k2_loop_flow.py`

段 4 裁定の「plan v2」§1〜§9 を正本とし、そこに書かれた schema・検査・図の形・layout check・provenance・caption・CLI を全部実装する。自己完結 (matplotlib / numpy / 標準 library のみ、既存生成器を import しない)。雛形 `plot_arc_status.py` の構造 (`FigureDataError` / `FigureLayoutError`、`_require`、`_keys`、`_pairs`、`_constant`、`check_display_text`、`_anchor`、`load_*`、`_figure_number`、`make_figure`、`check_figure_layout`、`_drawn_items`、`build_provenance`、`_destinations`、`_publish_outputs`、`main`、末尾の `CAPTION`) を踏襲し、plan v2 の差分 (role frontmatter 束縛、4 列 × 6 lane の格子、矢印 3 種と矢印線分 × Text の交差検査、`arrows` / `roles` / `caption_source` を持つ provenance) を足す。

矢印は `matplotlib.patches.FancyArrowPatch` (transform=fig.transFigure) か Line2D の polyline で描き、**layout check は矢印の各線分と全 Text の bbox の交差を検査して交差があれば `FigureLayoutError`** にする (線分 × 矩形の交差判定を自前で書く。曲線 connectionstyle を使うなら path を `Path.iter_segments` / `interpolated` で線分近似する)。矢印の label Text は矢印の所有領域 (region) に登録し、矢印線分は自分の label の bbox とも交差してはならない (label は線分の脇に置く)。

caption は英文で決定的に組み立て、plan v2 §8 の内容を全部含める。次の固定文を**逐語**で含めること (test でも逐語検査する):

1. `This is a schematic of recorded data flow; no performance values are drawn and the three runs are not compared.`
2. `Certified means only that the trace-enabled verify run found the observed trace serializable with no anomaly; it is not a performance certification and not a choice among candidates.`
3. `The planner and coder role definitions declare no tools (structural blockade); critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation.`
4. `Discipline-six marks are role self-reports that external inputs contained no instruction-like strings; their form differs by role and they are not a mechanical gate.`
5. `No causal effect of the knowledge source or of the diagnosis on the proposed values is claimed: each condition was launched once, without a control.`
6. `The same-job stock control was not achieved and awaits a ruling; proposal values are backoff literals, not results.`

caption の骨格 (構造 field から書式化。`Figure N.` の N は出力 prefix の `fig<N>_` から。`<basename>` は caption_source の file 名):
`Figure N. Data flow of the K2 manual synthesis loop over three recorded rounds, read from the frozen results note <basename>. In each round the parent session projects typed JSON inputs (planner: <planner_keys joined by ", ">; coder: <coder_keys joined by ", ">) to planner-v4 and coder-v4-autonomous-k2; the proposal is one backoff literal evaluated by one Pegasus compute-node job with separate trace-enabled verify and trace-disabled bench builds and a campaign WAL terminal record; critic reads the digest and the WAL. Measurement reflux occurred twice (the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round) and diagnosis reflux once (the second critic into the third-round inputs as the typed key <diagnosis_key> with fields <diagnosis_fields joined by ", ">, identical for planner and coder). The unevaluated proposal, generated without a diagnosis key, re-proposed a known value. [固定文 3] [固定文 2] [固定文 4] [固定文 5] [固定文 6] [固定文 1]`
caption に次を書かない: `improvement`、`better`、`faster`、`converge`、`optimal`、`performance certified`、`causal effect of the diagnosis was`、tps の値、% の値。

## 作る物 2 — `tools/plotting/k2_loop_flow_2026-09-20.json`

段 4 裁定 plan v2 §2 の schema と §12 の内容を、稿の該当節と突き合わせながら書く。§12 に「※」で示した数詞 (`one` / `two` / `third`) は自由文検査に通る言い換えへ直す (意味を変えない)。自由文 (label / sublabel / discipline6 / attribution / recommend / definition / arrow label) に数字を含む token を書くときは `reference_ids`・instance (`planner-1` 等)・job (`job 1216` の形) のいずれかに token 全体一致させる。`reference_ids` は実際に自由文で使うものだけを入れる。稿と食い違う記述を見つけたら JSON は稿に従い、報告に食い違いとして書く (裁定の §12 は親の下書きであり稿が正本)。

## 作る物 3 — `orchestrator/tests/test_plot_k2_loop_flow.py`

段 4 裁定の plan v2 §10 (T1〜T9) を正本とし、列挙された test を全部書く。雛形の test と同じく `importlib` で生成器を読み込み、実 JSON をそのまま実寸 fixture に使い、本物の Figure を `check_figure_layout` へ通す。異常系は実 JSON の deep copy を 1 か所だけ変えて parametrize し、描画せずに `load_flow` (相当) で拒否させる。非一意 anchor の負例は tmp に repo 相当 root (JSON・稿 copy・`.claude/agents/` の 3 file copy) を作り、稿 copy に見出し行を複製して作る。role 束縛の負例も同じ tmp root で frontmatter を書き換えて作る。
変異事前登録の表 (裁定末尾 M1〜M10) の各変異を殺す test を、表の「kill する test」欄と対応が分かる名前で置くこと (例: `test_t3_invalid_enum_is_rejected`、`test_t3_unknown_key_is_rejected`、`test_t4_free_text_rejects_quantities`、`test_t5_overlap_is_a_layout_error`、`test_t5_escape_is_a_layout_error`、`test_t5_arrow_crossing_text_is_a_layout_error`、`test_t7_caption_source_hash_is_independent`、`test_t2_tools_none_mismatch_is_rejected`、`test_t6_publish_runs_layout_check`、`test_t8_cli_rejects_invalid_prefix`、`test_t3_non_unique_anchor_is_rejected`、`test_t7_drawn_items_match_flow`)。
着地 test (`test_landed_fig12_bundle_when_present`) は plan v2 §10 T9 のとおり。**親が着地させるまでこの test は赤になる。それは期待赤であり、報告に「未着地のため赤」と書けばよい (xfail 化・skip 化しない)。**
末尾に `if __name__ == "__main__": sys.exit(pytest.main([__file__, "-x"]))` の self-run harness を付ける。subprocess で python を起動する箇所は env に `PYTHONDONTWRITEBYTECODE` を入れ、`tools/check_subprocess_bytecode_guard.py --repo <unit worktree>` が違反 0 で通る形にする。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_k2_loop_flow.py` (self-run harness)。着地 test 以外が全部 passed であること。所要秒も報告する (目安 20 秒以内、超えるなら描画回数を削る)。
2. 実データの実走 (FIGURE_CONVENTIONS §10): `python3 tools/plotting/plot_k2_loop_flow.py probe-k2fig12/fig12_k2_manual_loop_dataflow` が rc=0 で png / pdf / provenance.json の 3 成果物を出すこと。provenance の `caption_source.sha256` が `sha256sum docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` と一致すること、`roles[].tools_none` が role 定義の現物と一致することを `python3` で照合し、結果を報告に写す。PNG を自分で開けないので、drawn_items の全文字列を報告に列挙する (親が目視する)。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`、`python3 tools/check_subprocess_bytecode_guard.py --repo /work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit`、および test file の列挙・命名に制約を課す他の meta-test を自分で洗い出して走らせる (F42。親の名指しを網羅と見なさない)。
4. `python3 -m py_compile` 相当の構文確認。`pytest` の直接起動は guard で拒否されうる。拒否されたらその旨を書き、1 の自走結果を正とする。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は file に書かず、最終メッセージの本文に全文を書け — 親の launcher が保存する)

## 実装した物
file ごとの要点 (schema・検査・図の形・layout check・provenance の key・caption)。
## 実走した検査
nodeid と passed / failed / skipped 件数、所要秒。実データ実走の rc と 3 成果物の path、caption_source の sha256 照合、roles の照合結果、drawn_items の全文字列。
## 稿との食い違い
裁定 §12 の下書きと稿の間で直した点 (無ければ「無し」)。
## 未実走・期待赤
走らせられなかったもの、着地前に赤の test 名。
## 受理・拒否の含意
生成器が受理する入力の形と拒否する入力 (各 1 文)、通る正例 1 つ。
## 所有外への波及
所有外の caller・共有 fixture・consumer test・列挙型 meta-test への影響の静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
裁定の表の各 id (M1〜M10) について、どの test (nodeid) が殺すか、変異の位置 (関数名)。前後に同じ入力を拒否する層があって単一理由にならない変異があれば指摘。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
