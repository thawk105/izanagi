## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A1 | closed | 生成エラー、join エラー、削除エラーを個別に保持し、生成エラーを優先する。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py:2538) |
| A2 | closed | T1 の signature に `stat.S_IMODE` が加わった。[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1178) |
| A3 | partial | T1 は複写した conftest と別 import の module を使う。実装を変えず本番 controller の import と ROOT 一致を実走で確かめる裁定は妥当。ただし、その確認までは未完了。[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1137) |
| A4 | closed | A/B の事前 collection と追加 node 入力を必須化し、差集合を照合する。各走自身の collection への fallback も除去された。[t2273pi_ab_analyze.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/probe/t2273pi_ab_analyze.py:60) |
| B1 | closed | 同じ config・testrunuid を持つ別々の 2 node で hook を呼ぶ。[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1186) |

## 新たな所見

- **F1 — 中 — [test_s8b_oracle_driver.py:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1197)**：M4/E1 では 2 本の生成スレッドが同じ `output` と `result.json.pending` に書く。先に結果検査が失敗する、または後の終了処理で失敗する経路があり、期待する spy assert が最初に落ちるとは断定できない。**修正案**：2 回目の hook 直後に、config 上の job が 1 回目と同一であることを assert し、1 回性を競合の結果から独立して検査する。
- **F2 — 中 — [test_s8b_oracle_driver.py:1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1194)**：M6/E2 は 10 秒待った後、期待する assert ではなく 1197 行の `read_text()` が `FileNotFoundError` になる。**修正案**：待機直後に `assert (snapshot / "result.json").exists()` を置く。

fix L の差分は既存テストの期待値を変更していない。通常実装の受理集合や終了処理の例外優先順位に、裁定外の変更は見つからなかった。fix P の差分も、事前入力の必須化と fallback 除去に限られる。

## 変異の検証

old 文字列は、M4 の **2 文字列をそれぞれ数えて**、fix 後の対象 file 内で全て 1 件だった。

| ID | 落ちる箇所・理由 | 単一理由 |
|---|---|---|
| P0 | コメント変更のみ。SURVIVED | 該当なし |
| M1 | T2 の `visible_output.call_count == builder.call_count`（1128 行） | はい |
| M2 | T1 の変更後 `signature(second) == signature(expected)`（1205 行） | はい |
| M3 | T1 の signature の mtime 比較（1204 行）。元ファイルの時刻は固定済み | はい |
| M4/E1 | T1 の結果検査（1197 行）、spy（1198 行）、または終了処理に到達しうる | **いいえ。F1** |
| M5 | T1 の `copy_visible.assert_called_once_with(...)`（1198 行） | はい |
| M6/E2 | T1 は 10 秒待機後、1197 行の読取り例外 | **期待 assert ではない。F2** |
| M7 | T1 の `assert not snapshot.exists()`（1209 行） | はい |

## GO 判定

**条件付き NO GO。** 実装と probe の修正は裁定に沿うが、M4 と M6 の期待 kill 理由を満たす検査へ T1 を直してから、親の実走で判定する。

## 総括

静的検査のみで、テストは実走していない。fix P の A/B 差集合検査は段 6 裁定の記述と一致する。s4-ruling 原文は指定された必読射影に含まれないため、その原文との直接照合はしていない。