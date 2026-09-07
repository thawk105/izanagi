## 総括

出力 prefix の `fig<N>_` から caption の図番号を導出するよう修正しました。  
不正な basename は既定値へ落とさず、出力前に拒否します。  
既存の凍結図5検査は変更せず緑を確認しました。  
親 provenance の caption と再生成値は UTF-8 1788 bytes で完全一致し、1 byte も変わっていません。

## 変更点

- [plot_a2_certification.py:579](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/tools/plotting/plot_a2_certification.py:579): basename から番号を抽出する fail-closed 処理を追加。
- [plot_a2_certification.py:594](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/tools/plotting/plot_a2_certification.py:594): 新旧両 caption の固定 `Figure 5.` を導出番号へ変更。
- [plot_a2_certification.py:751](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/tools/plotting/plot_a2_certification.py:751): provenance、publish、closure 再検証を同じ prefix 導出へ接続。
- [plot_a2_certification.py:846](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/tools/plotting/plot_a2_certification.py:846): CLI 出力前に不正 prefix を拒否。新しい CLI 引数は追加していません。
- [test_plot_a2_certification.py:917](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:917): `fig6_...` が `Figure 6.` になる正例を追加。
- [test_plot_a2_certification.py:927](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-pin/orchestrator/tests/test_plot_a2_certification.py:927): 不正 basename を拒否し、出力を残さない負例を追加。

## 実走した検査

自走 harness（`PYTHONPATH=.`、pytest runner 不使用）で以下を確認しました。

- `::test_caption_uses_figure_number_from_output_prefix` — 緑。
- `::test_output_prefix_without_figure_number_is_rejected` — 緑。
- `::test_landed_fig5_repo_closure_and_caption_when_present` — 既存 test を変更せず緑。
- caption 関連の既存4 node — 緑。
- 凍結 provenance caption の byte 完全一致 — 緑、1788 bytes。
- 正例変異: 抽出番号を `"5"` 固定 — 正例 node が赤。
- 負例変異: 不正 basename を `"5"` へフォールバック — 負例 node が赤。
- 両変異は復帰済み。`git diff --check` も成功。

## 所有外への波及

所有対象の2ファイル以外は編集していません。凍結済み docs・results・insights は未変更で、`git add`・commit も行っていません。bytes pin、schema、closure、token 照合、gate 文には変更ありません。

## 未了・申し送り

実物の新版認証成果物はこの worktree にないため、その実データを使った生成は未実走です。親側で通常の全体検査と新版成果物による統合実走をお願いします。