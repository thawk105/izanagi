## 総括

[対象テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2778-author/orchestrator/tests/test_dev_wave_cleanup.py:313) の313〜325行のみ修正しました。

- `tr a-z A-Z` と再正規化を使用。wildcard filter が他の fixture ファイルにも効くため、`git add --renormalize .` としています。
- blob＝大文字、作業木＝小文字、status＝clean を確認。
- 直接呼出し：負例2ケース・既存正例とも成功。
- 反実仮想：変換検査をメモリ上で外すと通過し、後段の `rc20 / integration` に到達。
- `git diff --check` 成功。pytest 全走は未実走です。

実装・docs の変更、commit、報告ファイル作成はしていません。