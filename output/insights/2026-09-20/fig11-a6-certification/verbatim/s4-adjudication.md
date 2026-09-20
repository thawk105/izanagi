# 段 4 裁定・plan v2・変異事前登録 — fig11 (A-6 read-heavy certification reject、attempt a6-20260908b) (2026-09-20 13:36 JST)

軽量版 (DW-C00) のため段 2・3 は省略した。ただし生成器の受理集合 (study) が広がる実装面なので、段 6 の独立敵対レビューは省かない。
裁定 inbox の再走査 (13:3x JST): `dev-wave-jobs/rulings-inbox/` の最新 3 本 (t750 W-4 / rulings-full25 / t2724 A-X) に本主題の項目は無い。
local main は着手時 `947fd160a` から不変、`docs/spool/` に未 fold fragment 無し。brief の前提を覆す新事実は無い。

## 裁定

- **(P1) 採用 — 単独稿の bytes は変えず、「限定 11 の更新」は `docs/paper-story/README.md` の results 表行と追補段落で行う。** 根拠: 稿冒頭と results 系列規則 (「append-only。書いた後は更新しない」)、fig11 provenance が稿の現 SHA-256 を caption_source として束縛する (稿を変えると closure が自壊)、同 README に凍結稿への追補の先例 (T-1998 単独稿の読解上の追補、C14a 追記) があり、fig8b / fig10 wave は稿 bytes を変えていない (git log で確認)。依頼文の「単独稿の限定 11 を更新」はこの形で満たす。
- **(P2) 採用 — 生成器は新 file でなく `plot_a2_certification.py` の in-place 一般化。** study → {表示名, caption_source} の exact 2 件の profile 表を持ち、workload 数は policy から導く (`6 × N` file 閉包、`N` 個の request / created_utc 一意、`2 × N` axes)。**A-2 (fig5/6/7) の caption・artist・provenance 射影は 1 byte も変えない** — fig5/6/7 の landed closure test が守り、変異 m9 で「A-2 caption を変えると赤になる」ことを実測する。
- **(P3) 採用 — fig11 caption の固定文は稿 §0 主判定文と §4 限定 1・3・4 (i)(ii)・5・6・7・9、§2.2 末文 (性能の reject は正しさ証拠を取り消さない) から英文化する** (下の plan v2 §1 に逐語で置く)。A-2 固有の末文 (older series / sign difference) と「Top-row y axes are scaled independently by workload」は 1 workload の A-6 に入れない。
- **figure 名は `fig11_a6_certification_reject`** (fig5 `fig5_a2_certification_reject` と同じ命名)。
- **scope 外 (実装しない):** B-10 3 block の併記・pool (caption で「履歴的照合・独立再現でない・pool しない」と 1 文触れるだけ)、A-2 との集計・前後比較、反復 attempt、certification の昇格、有意差・区間の効果への付与、稿の改訂・新稿、fig5/6/7 の再生成、新 gate・check_docs 規則・台帳、`plot_a2_certification.py` の他図種への一般化。
- **caption に書かない語:** `significant`、`superior`、`improvement`、`performance certified`、`reproduced`、`replicated`、`research failure`。

## plan v2 (親起草、file 粒度)

### 1. `tools/plotting/plot_a2_certification.py` (in-place 一般化。A-2 経路は挙動不変)

- 定数: `STUDY` は残す (legacy profile の受理 study、既存名)。新設 `STUDY_PROFILES` = `{"paper-story-a2-certification": {"label": "A-2", "caption_source": None}, "paper-story-a6-certification": {"label": "A-6", "caption_source": "docs/paper-story/results/2026-09-18-a6-certification-reject.md"}}` (exact 2 件、他 key 不可)。
- `CANONICAL_SHA256` に `"output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json": {"certification": "3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab", "raw_manifest": "8d17953575afc4594df052d5b5b778291c4d41a1564bb1fbc2d29e8d1df94ef9"}` を追加 (3 entry)。
- `_external_plan`: `expected_count = 10 if profile == "legacy" else 6 * len(workloads)`。message は `f"... exact {expected_count}-file closure ..."` のまま (A-2 は「12-file closure」で既存 test の match を維持、A-6 は「6-file closure」)。
- `load_measurements`: legacy profile は study == `STUDY` を要求 (不変)。current-full は study が `STUDY_PROFILES` に在ることを要求 (embedded policy の study 一致は既存検査のまま)。一意検査は `!= len(workloads)` (message 不変)。戻り値に top-level `"study": certification["study"]` を足す。既存 key の値は不変。
- `_study_label(data)`: `data.get("study")` が無ければ `STUDY` (fig5/6/7 の着地済み provenance は key を持たない — 互換の既定であり、新規生成は必ず `study` を書く)。
- `_caption`: current-full 枝を study で分岐。**A-2 は現行文字列と byte 一致** (共通部を関数化してよいが結果文字列は不変)。A-6 は次の骨格 (値は data から書式化、`Figure N.` の N は prefix から):
  `Figure N. A-6 formal certification attempt <attempt> (outer status: <status>). The single workload campaign was request <request> on <host> at <created_utc>; with one policy workload, the outer status is that workload's verdict itself. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. The median effect copied from certification is <label> (<workload>) fixed <BACKOFF_FIXED> us <effect:.4f>%. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. The displayed outer status is the protocol status based on the predefined median ratio: the adopted cell's median did not exceed the stock cell's median. This is one attempt of five samples per cell; it does not decide a between-run floor exceedance, repeated-attempt reproducibility, or research success or failure, and it does not show that stock is best for read-heavy or that static backoff is harmful for read-heavy in general. The bottom row is a descriptive leading indicator: one aggregate abort-rate point per cell, no confidence interval, and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all <n> cells were certified, but this is not a performance certification, and the performance reject does not withdraw that correctness evidence. L01 limits that evidence to point-key traces; under D1257 the correctness argv was not independently recorded. <gate_note> Conditions: <threads> threads, <records:,> records, Zipf <skew>, read-modify-write disabled, max operations <max_ope>, <extime> s, <reps> repetitions, CCBench pin <pin>, no perf, trace-disabled performance. The same-sign B-10 read-heavy blocks are a historical concordance under nearby conditions, not an independent reproduction, and are not pooled here; the A-2 attempts measured other workloads and are neither pooled nor compared as before/after.`
  「the adopted cell's median did not exceed the stock cell's median」は `outer_status == "reject"` かつ effect < 0 のときだけ書く (status が他の値なら書式化しない = 恒真化しない)。A-6 の固定文は test で逐語検査する。
- `_artist_series`: 不変 (workload 数に依存しない実装)。
- `make_figure`: `ncols = len(workloads)`; `plt.subplots(2, ncols, figsize=(11.8, 7.6) if ncols == 2 else (6.4, 7.6), squeeze=False)`; suptitle は `f"{label} {'four' if n==4 else 'two'}-cell certification — trace-disabled performance"` の形で A-2 は「A-2 four-cell …」不変、A-6 は「A-6 two-cell …」; 「correctness: … all <n> cells certified …」の n を data から; 脚注は A-2 不変、A-6 は「Single workload (read-heavy, rr95); abort axis is 0-1. Mean t95 CI is descriptive.」。x tick は既存の `("no backoff", f"fixed {BACKOFF_FIXED} us")`。
- `check_figure_layout`: 「four axes」固定を `rows == 2` かつ `len(fig.axes) == len(plot_axes) == 2 * ncols` (ncols = `len(axes[0])`、1 以上) に一般化。A-2 の 4 は同じ判定で通る。
- `build_provenance`: `STUDY_PROFILES[study]["caption_source"]` が非 None なら `tracked_inputs` に `{"kind": "caption_source", "path": <稿>, "sha256": <現 SHA-256>, "authority_scope": "fixed caption statements and limitation wording only; not measurement values or protocol status"}` を追加 (A-6 のみ。A-2 current-full は不変 = fig6 の landed provenance と同じ 2 行)。top-level に `"study"` を足す。
- `validate_repo_closure`: 不変 (caption_source 行は tracked_inputs として path + sha256 を既に検査する)。
- CLI / `main` / `_publish_outputs`: 不変。

### 2. `orchestrator/tests/test_plot_a2_certification.py`

- 既存 test の期待値は変えない。次の exact pin だけを A-6 を含む形へ更新する: `test_tracked_authority_literals_and_run_readme_record_agree` (`len == 3`、A-6 entry の 2 値。値は稿 §5.1 の表 (`docs/paper-story/results/2026-09-18-a6-certification-reject.md`) に逐語で現れることも検査)、`test_t2364_canonical_current_full_measurements_load_without_override` (A-6 entry を A-6 real root `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b` で同様に検査。root 全欠は skip、部分欠は失敗。期待 median `[10088796, 9505248]`、effect `-0.057841193339621455`)。
- 新設 `_a6_fixture(tmp_path)`: A-6 凍結 certification の embedded policy (rr95 1 workload、cell `rr95-stock` / `rr95-fixed2`) から `_current_fixture` と同じ機構で実寸 fixture を作る (5 標本、verify legacy 1 + performance 5、campaign lock / claim / WAL / receipt、manifest 6 file、study `paper-story-a6-certification`、request 1 件)。`_current_fixture` を policy 源で parametrize してよい (A-2 fixture の出力は不変)。
- 新設 test (名前で意図が分かる形): `test_a6_fixture_loads_as_current_full_with_six_file_closure`、`test_a6_rejects_six_file_closure_underflow_and_overflow`、`test_a6_provenance_tracks_caption_source_with_current_sha`、`test_a6_caption_contains_fixed_literals` (「not a performance certification」「does not withdraw that correctness evidence」「not an independent reproduction」「neither pooled nor compared」「with one policy workload」を逐語)、`test_a6_caption_excludes_forbidden_words`、`test_a6_real_size_figure_has_two_columns_and_passes_layout` (本物の Figure、`len(fig.axes) == 2`、artist 10 行)、`test_layout_rejects_wrong_axes_count` (3 axes の Figure を `check_figure_layout` へ → `FigureLayoutError`)、`test_unknown_study_is_rejected` (A-6 fixture の study を第 3 の値へ、policy 側も揃えて → 拒否)、`test_a2_current_full_caption_is_unchanged_for_landed_fig6` (fig6 の landed provenance から `_caption` を再構成し `caption` と一致 — 既存 `validate_repo_closure` 経由でもよい)、`test_a6_cli_writes_three_outputs` (`main` rc=0、3 file)、`test_landed_fig11_repo_closure_and_caption_when_present` (bundle 3 file 実在 → `validate_repo_closure` → caption が figures README に逐語 → README fig11 節「## 着地 bytes の SHA-256」の 3 行と現物一致。**bundle 未着地は skip でなく失敗**、`test_landed_fig11_rejects_all_missing_outputs` で全欠落が失敗になることを test)。
- 親が着地させるまで fig11 着地 test は赤 (期待赤、xfail / skip 化しない)。

### 3. docs (親、docs-only)

- `docs/paper-story/figures/README.md`: 一覧表に fig11 行、末尾に fig11 節 (何を示す図か / 既存図との関係 (fig5・fig6・fig7 の後継ではない、B-10・A-2 と pool しない) / 入力 / 再現 / 条件関門についてこの図が言えること / 作図規約への適合 / キャプション正文 / proof chain / 着地 bytes の SHA-256)。
- `docs/paper-story/README.md`: results 表 2026-09-18 A-6 行の「図は無い」→「図 11 (2026-09-20 追加、稿 bytes 不変)」、results 表直後に「A-6 単独稿の限定 11 への追補 (2026-09-20)」段落。
- `tools/plotting/README.md`: `plot_a2_certification.py` 節へ A-6 の再現 1 行 (受入直前、local main 取り込み後)。

## 変異事前登録 (DW-M01、位置は関数・述語で指定、`old`/`new` は実装後に spec へ写す)

| id | category | 位置 | 期待 |
|---|---|---|---|
| m0-equivalent-docstring | positive | 生成器 module docstring に 1 行追加 | SURVIVED (expected_nodes 空) |
| m1-a6-pin-drift-accepted | negative | `_load_tracked_authority` の certification SHA-256 一致検査を恒真化 | KILLED: 既存 m11/pin test + A-6 pin test |
| m2-closure-count-fixed-12 | negative | current-full の `expected_count` を 12 固定へ戻す | KILLED: A-6 6-file 閉包 test |
| m3-drop-a6-caption-source | negative | `build_provenance` の caption_source 追加を除く | KILLED: A-6 caption_source test |
| m4-layout-accept-any-axes | negative | `check_figure_layout` の axes 数検査を恒真化 | KILLED: wrong-axes-count test |
| m5-drop-a6-caption-literal | negative | A-6 caption の「but this is not a performance certification」を削除 | KILLED: A-6 caption literal test |
| m6-study-accept-any | negative | current-full の study 受理集合検査を恒真化 | KILLED: unknown-study test |
| m7-distinct-check-weakened | negative | `!= len(workloads)` → 常に偽 (検査消失) | KILLED: 既存の A-2 request/時刻一意 test (無ければ新設) |
| m8-landed-skip-on-missing | negative (test file) | fig11 着地 test を全欠落で skip に | KILLED: landed rejects all-missing test |
| m9-a2-caption-drift | negative | A-2 current-full caption に 1 語追加 | KILLED: fig6 landed closure test (A-2 不変の正例) |

単一理由性 (F820) は実装後に probe で確認し、前後に同じ入力を拒否する層があれば再照準する。runner は DW-M05 正本経路 = 主 repo に登録した固定 commit の worktree (`.codex/worktrees/mut-fig11-a6`) へ `tools/mutation_harness.py --runner-mode dispatch --detached` (計算ノード)。spec / out は job dir。baseline 緑必須。受理集合を広げる wave なので、A-2 (fig6 real root) と A-6 (real root) の両方が load できることを正例として test に持つ。
