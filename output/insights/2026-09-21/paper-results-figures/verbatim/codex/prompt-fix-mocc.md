単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (本 fix の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s6-ruling.md
- 段 4 裁定 (設計の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s4-ruling.md
- 段 5 の実装子の最終報告 (本単位): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/author-mocc.md
- 段 6 レビュー (所見 A#3・B#2・B#3 の根拠): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/review-A.md、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/review-B.md
- 焦点走の log (計算ノードの pytest。赤の本文は `IZANAGI_FAILURE` の excerpt): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/focus-1.log
- 対象 (全文): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/test_plot_mocc_witlight_four_arm.py と /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/tools/plotting/plot_mocc_witlight_four_arm.py
- import 形の手本 (冒頭 20 行だけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/test_plot_a1_sized_paired.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。

## 前置き

対象は研究用 repo の論文図の生成器と単体 test の修正である。セキュリティでも攻撃でもない。この worktree の HEAD は wave の統合 commit `f2d146cd55523946408eaaf569bdbe31dad61b51` で、
生成器・test・図 (fig15) と README が揃っているので、着地 test も緑になるはずの木である。

# 依頼 — 段 6 裁定の mocc 分 4 項目を直す

1. **pytest 下の赤 2 件** (`test_landed_fig15_rejects_missing_or_partial_bundle`、`test_caption_fixed_literals_and_forbidden_claims`): `assert cond, msg` の `AssertionError` を捕まえて
   `str(exc) == msg` と完全一致で比べているが、pytest の assert 書き換えが例外文に説明を足すので pytest 下だけ偽になる (plain runner では緑)。先頭行の完全一致または `startswith` で比べる。
   判定の強さ (欠落 bundle の拒否、禁止句の負例が意図した句で落ちること) は弱めず、別の理由の AssertionError を取り違えて通さない。
2. **A#3:** 図中の曝露比注記 2 行 (`BACK_OFF=0: on/off exposure ratio 0.8636`、`BACK_OFF=1: on/off exposure ratio 0.8450`) が実際に描かれていることを、`fig.findobj(Text)` の**可視 text** で検査する
   test を足す (既存の必須開示 test に足しても、別 test にしてもよい)。値は稿 §2.6 の独立 literal で照合し、生成器の関数から作らない。生成器の `make_figure` から
   曝露比注記の描画 (`for i, text in enumerate(series['exposure_notes']):` と次の `fig.text(...)`) を消すと、その test が赤になること (変異 M14 の kill 先) を直接確かめる。
3. **B#2:** test の `from orchestrator.tests.skiputil import Skip, skip` を、既存 `test_plot_a1_sized_paired.py` と同じ `sys.path.insert(0, str(HERE))` + `from skiputil import Skip, skip` に揃え、
   `python3 orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (PYTHONPATH 無し) で走るようにする。生成器の読み込み方は変えなくてよい (既に path で読んでいるなら)。
4. **B#3:** 生成器 `check_figure_layout` の「隣接 panel 侵入」検査 (`if text.axes is not None:` から `raise FigureLayoutError("text enters neighboring panel")` までの 4 行) を削除する。
   axes がちょうど 1 であることの検査、図外逸脱、text 重なりの検査は残す。

## 所有 path (これ以外は編集禁止)

- `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`
- `tools/plotting/plot_mocc_witlight_four_arm.py` (上の 4 の削除だけ。他の行は変えない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` / `git rm` を一度も実行しない。
- docs、図の成果物 (`docs/paper-story/figures/`)、他の生成器、他の test file、台帳を編集しない。生成器の描画・caption・provenance・閉包を変えない (4 の削除以外)。
- 本 wave で足した test は編集対象だが、判定の反転・緩和・skip・xfail・削除をしない。赤なら実装側の誤りとして報告する (既存 tracked test は本 file に無い)。
- `tools/run_tests.py` と `python -m pytest` は sandbox では使わない。

## 検査 (実走した nodeid と件数を報告する)

1. `python3 orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (PYTHONPATH 無し) が全件 passed (着地 test 2 本を含む、skip 0)。`PYTHONPATH=.` 付きでも同じ。
2. 1 の修正 2 箇所で「pytest が付け足す説明付きの例外文」を受けても期待どおり判定され、別の文言の AssertionError は通らないことを、関数を直接呼ぶ小さな確認で示す (確認用 code は test file に残さない)。
3. 2 の新検査について、生成器から曝露比注記の 2 行を一時的に消して赤になり、戻して緑になることを確かめ、戻した後の生成器の sha256 が変更前 (4 の削除後) と一致することを報告する。
4. 生成器を login で実走 (`python3 tools/plotting/plot_mocc_witlight_four_arm.py probe-fig15-fix/fig15_mocc_witlight_four_arm`、rc=0) し、4 の削除で layout 検査の結果・caption・provenance の値
   (`generated_utc` / `generator` / `outputs` / `reproduction` 以外) が着地 fig15 provenance (`docs/paper-story/figures/fig15_mocc_witlight_four_arm.provenance.json`) と一致することを報告する。
   `probe-fig15-fix/` は untracked のまま残す (親が退避する)。

## 出力形式 (最後の節は必ず `## 総括`)

## 変更した物
## 実走した検査
## 変異 M11〜M14 の kill 先
(nodeid)
## 総括
