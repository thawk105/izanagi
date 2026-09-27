## 対応表

| 段 6 の所見 | 判定 | 根拠 |
|---|---|---|
| レビュー A-1: preflight probe の到達回数を `1` に固定 | **closed** | [f1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2104-flock-scope/focus-f1.log:113) では実際に 6 回到達。修正後は [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/tests/test_p3_s4_loop.py:7212) の wrapper が各到達時に busy を要求し、7218 行で 0 回到達を拒否する。[f2.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2104-flock-scope/focus-f2.log:31) は対象 3 ファイルで 1146 passed / 3 skipped。 |
| レビュー B-1: 解放後の直接再取得が重複 | **未対応（nit、記録のみ）** | [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/tests/test_campaign.py:3178) に残る。fix 差分の対象外で、成果物の判定には影響しない。 |
| レビュー B-2: `is_file()` が直後の読込と重複 | **未対応（nit、記録のみ）** | [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/tests/test_p3_s4_loop.py:7235) に残る。fix 差分の対象外で、保持区間の検証には影響しない。 |
| f1 の赤: preflight `assert 6 == 1` | **closed** | [f1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2104-flock-scope/focus-f1.log:113) の失敗条件を `assert hits` に修正。各回の busy 検査は維持され、[f2.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2104-flock-scope/focus-f2.log:31) で通過。 |
| f1 の赤: `run_campaign` の末尾 2 引数 | **closed** | [f1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2104-flock-scope/focus-f1.log:123) の期待どおり、[loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/campaign/loop.py:555) では新引数を末尾 2 引数の前に移動。`*` の後にあり keyword-only、既定値は `None`。対象テストは f2 で通過。 |

## 新規所見

なし。fix の 2 行変更による signature・既定値の回帰は見当たらない。preflight probe は 0 回では通らず、到達した毎回 busy を検査する。

実装全体でも、B-4 の事前認可前に [main が取得](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/campaign/p3_s4_loop.py:3879)し、driver は[認可・消費から checkpoint 保存まで保持](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/campaign/p3_s4_loop.py:3143)する。`run_campaign` は受け取った handle の型・保持中・PID・path を [WAL 前に照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope/orchestrator/campaign/loop.py:729)する。静的検査では、この区間の窓や規律 2 の緩和は見つからなかった。

## 総括

**GO（fix 後の焦点再レビュー）。** 根拠となる実走は親の f2 の対象 3 ファイルの結果であり、この静的検査を追加の緑とは数えない。未対応は重複検査に関する nit 2 件のみ。