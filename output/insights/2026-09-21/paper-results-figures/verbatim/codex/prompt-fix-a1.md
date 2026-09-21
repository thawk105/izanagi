単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (本 fix の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s6-ruling.md
- 段 4 裁定 (設計の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s4-ruling.md
- 段 5 の実装子の最終報告 (本単位): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/author-a1.md
- 焦点走の log (計算ノードの pytest。赤 4 件の本文は `IZANAGI_FAILURE` の excerpt): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/focus-1.log
- 対象 test (全文): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/orchestrator/tests/test_plot_a1_sized_paired.py
- 生成器 (読むだけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/tools/plotting/plot_a1_sized_paired.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。

## 前置き

対象は研究用 repo の論文図の生成器の単体 test の修正である。セキュリティでも攻撃でもない。この worktree の HEAD は wave の統合 commit `f2d146cd55523946408eaaf569bdbe31dad61b51` で、
生成器・test・図 (fig14 / fig9) と README が揃っているので、着地 test も緑になるはずの木である。

# 依頼 — `test_plot_a1_sized_paired.py` の pytest 下の赤 2 件を直す

赤 2 件 (`test_landed_fig14_rejects_missing_or_partial_bundle`、`test_attempt2_visible_text_forbidden_claims_and_negative_control`) は plain runner では緑、pytest (受入と同じ) では赤である。
原因は親が特定済み: `assert cond, msg` の `AssertionError` を捕まえて `str(exc) == msg` と**完全一致**で比べているが、pytest の assert 書き換えが例外文に説明を足すため pytest 下だけ偽になる。
既存の fig9 用 test (`_reject_missing_landed_bundle`) は `str(exc).startswith(...)` で比べていて pytest でも緑である。同じ比べ方 (先頭行の完全一致、または `startswith`) に直す。
判定の強さ (欠落 bundle を拒否すること、禁止句の負例が意図した句で落ちること) は弱めない — 別の理由の AssertionError を取り違えて通さないよう、期待する文言は先頭で照合する。

## 所有 path (これ以外は編集禁止)

- `orchestrator/tests/test_plot_a1_sized_paired.py` だけ。

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` / `git rm` を一度も実行しない。
- 生成器 `tools/plotting/plot_a1_sized_paired.py`、docs、図の成果物 (`docs/paper-story/figures/`)、他の test file、台帳を編集しない。
- **既存テストの期待値を変更しない。** ここでの既存テスト = base `36fb14a3d` にある 28 本 (tracked)。本 wave で足した test (fig14 / attempt-0002 系) は編集対象だが、
  反転・緩和・skip・xfail・削除をしない。赤なら実装側の誤りとして報告する。
- `tools/run_tests.py` と `python -m pytest` は sandbox では使わない。

## 検査 (実走した nodeid と件数を報告する)

1. `python3 orchestrator/tests/test_plot_a1_sized_paired.py` (self-run harness) が全件 passed (着地 test を含む、skip 0)。
2. pytest の assert 書き換えを再現する代わりに、修正した 2 箇所で「pytest が付け足す説明付きの例外文」(例: `"fig14 integration bundle is incomplete\nassert False\n +  where False = all(...)"`) を
   受けても期待どおり判定されること、別の文言の AssertionError は通らないことを、関数を直接呼ぶ小さな確認で示す (確認用 code は test file に残さない)。

## 出力形式 (最後の節は必ず `## 総括`)

## 変更した物
## 実走した検査
## 既存テストへの影響
(base の 28 本の本文・期待値を変えていないことの確認方法と結果)
## 総括
