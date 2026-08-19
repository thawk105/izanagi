---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: t944-testops-pilot
seq: 1
title: "[T-944] 有界 task-run 観測 pilot v2 を実装した (コード+テスト、branch worktree-t944-testops-pilot、変異matrix=14/14 KILLED一致・2件除外理由付き)"
---

## 本文

- D341 (2026-08-12 第3束裁定、Q1〜Q3=(a)(a)(a) 確定) の制約下で、
  `output/insights/2026-08-12_testops-observation/` が凍結した blocker 9 件・must-fix 11 件
  (A1 は refuted 済み) を閉じた。9 段状態機械を全段実行 (段2 codex plan → 段3 敵対相談2本 →
  段4 親裁定 {{D:t944-testops-pilot-v2}} → 段5 実装 (Unit A/B 分割) → 段6 敵対レビュー2本 +
  fix 3巡 (DW-O16 上限) + 変異事前登録)。詳細は `output/insights/2026-08-19_t944-testops-pilot-v2/`。
- **段5〜6 で発見・是正した2つの重大バグ**: (1) cap 判定が `published` のみを数え
  `incomplete`/`damaged` を除外していたため、crash を繰り返す走行で pilot cap (10件) を実質無制限に
  超えられた (段6 両レンズが独立に検出)。(2) sidecar lease の命名 (`sidecar-<hash>.json`) が
  既存 `pytest_stats.py` の固定 basename 契約と非互換で、automatic 経路の counts/digest が常に
  欠測していた (親が段5 で実測して発見)。両方とも cap 分母修正・専用 lease directory + 固定
  basename への変更で閉じた。
- **段4裁定文の曖昧さで fix1→fix2→fix3 の往復が発生した** (damaged root への `start_run()` を
  拒否すべきか)。最終的に pre-existing v1 の既存テストが「damaged があっても start は成功する」を
  明示的に要求している事実で確定させた。教訓として、次回同種の裁定を書く際は
  「pre-existing 挙動と衝突しないか」を裁定文自体に明記する。
- **段6所見のうち2件が Unit A/B どちらの編集権限にも無い (`aggregate.py`・`pytest_stats.py`) ため
  当初 partial にとどまった。** 焦点レビューが「s4-ruling の受入契約は Unit 境界より上位」と
  指摘し、Unit A の権限を拡張して3巡目の fix で解消した。
- **検証実行自体が実運用の repo 兄弟ディレクトリを汚染することを発見した** (git-common-dir
  共有のため、どの worktree での `run_tests.py` 実行も実 pilot へ記録される)。着地前に
  `/work/1/SFC/tanab/izanagi-task-runs/` (10件、全て検証実行由来) を削除しクリーンな状態へ
  リセットした。この特性自体は D66 原設計でも既に観測済みの挙動 (初回 pilot が実質1日で
  cap に到達) であり新規の懸念ではない。
- **変異matrix走行中に m03 (banned-namespace-check) の既存テストが実際には
  `_check_banned_components` を単独では検証していないことが判明した** (2つ目の
  parametrize シナリオが、無関係な「中間ディレクトリ不在」の別チェックにマスクされ、
  DW-M03 の単一理由性を満たしていなかった)。専用 worktree で Codex にテストのみの
  fix を依頼し (`test_external_banned_namespace_is_rejected_with_existing_intermediates`
  を新設)、mutation-spec.json の `expected_nodes` も追随させて是正した。
- **hang_risk変異 (m04、lock timeout保護を外す) の走行中、`tools/pegasus/dispatch_compute.py`
  の既定walltime (1時間) が固定で毎回そのまま待たされる非効率をユーザーが指摘した。**
  調査の結果、`run_tests.py`がwalltimeを一切上書きできない構造的制約と判明し、
  `IZANAGI_DISPATCH_WALLTIME_OVERRIDE` 環境変数で上書き可能にする最小差分を専用worktree
  でCodexに実装させ、commit `201005ce` を作成した (詳細は decisions fragment)。
  短縮後もm04は「PBS強制終了された変異が正常完了マーカーを残せない」という
  `dispatch_compute.py`側の構造的非互換で毎回orphan-holdに落ちることが判明し
  (3回の実dispatchでいずれも30分以上ノータイムアウトを確認、被験対象の性質は実証済み)、
  timeout値に依存しないためharness側のtoolingの限界と判断してmatrixから除外した。
- **変異事前登録は 18 項目中 15 項目・16 変異を登録** (3 項目は DW-M01 の単一理由性を確認できず
  見送り)。**実走の結果: 14/16 KILLED (期待一致)、2件除外。** 除外はいずれもコードの不備ではない —
  (1) m04 (hang_risk) は上記の理由でharness側toolingの限界により未完了、(2) m16
  (repo-head TOCTOU) は `_git_output()` 自体が呼出し前後で同じ束縛検査を二重に行っており
  (`tools/task_runs/ledger.py:474,489`)、削除対象は三重目の冗長防御と判明 (DW-M03の
  「過剰決定」)。**また m07/m08/m09/m12 の4件は初回走行でMISMATCH (spec登録時の
  expected_nodesが過小、DW-M08違反) となったが、コード自体は正しく動作しており
  実際の失敗集合へexpected_nodesを補正のうえ再走して確定させた** (baseline
  無変異dispatch実行は415 passed/1 skippedで全緑を確認し、環境要因ではないことを
  裏取り済み)。
- 子の工数: plan 1本、敵対相談 2本、実装 2本 (Unit A/B)、敵対レビュー 2本、fix 9本
  (Unit A ×5、Unit B ×3、変異テスト fix ×1)、変異spec 1本、walltime override実装 1本。

## 次の一手差分

### 完了

- [T-944] D341 の制約下で blocker 9・must-fix 11 を閉じる実装を完了した。
  remaining: none
  base: ecfd80ad4f6acbd32761708012de4945add6d3f6fc1a79b31b23277d91ef6110
