## 対応表

| 元の所見 | 判定 | 根拠 |
|---|---|---|
| A-1 | closed | runner 結果を受けた後、[orphan 判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2400)を先に行う。hold 時は[復元せず M の状態を検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2466)する。 |
| B-1 | closed | A-1 と同じ。[残存 job と bytes 変更が重なる試験](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3614)も追加された。 |
| B-2 | partial | [HEAD と bytes の負例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3489)は追加されたが、`[head]` は両方を同時に変える。 |
| B-3 | closed | [T5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3522)は runner 内で例外を出し、runner 後の検査を経ずに[復元直前の detached 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:766)へ到達する。 |
| B-4 | not-fixed-by-ruling | [policy の選択式](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2578)と[復旧文言](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:3030)の重複は残る。裁定は nit として修正対象外。 |
| B-5 | not-fixed-by-ruling | [T9 の８組](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3654)は残る。裁定は nit として修正対象外。 |
| B-6 | closed | 削ってはならない[注入後の照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:748)と[復元前の照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:763)は維持されている。 |

## 新規所見

| 重大度 | 根拠 | 何が起きるか・推奨 |
|---|---|---|
| should | [test_mutation_harness.py:3497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3497) | `[head]` の `reset --hard H` は HEAD と touched bytes を同時に変える。HEAD 照合だけを欠く場合も blob 照合で拒否されるため、B-2 の HEAD 単独検出は示せない。reset 後に touched bytes を M blob に戻し、HEAD だけが異なる試験にすることを推奨する。 |

hold でない経路では、[orphan 判定が `None` を返す](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:410)と[再検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2409)へ進む。file-swap 経路はこの commit 専用再検査を通らず、fix 差分による変更は見当たらない。静的検査では、この順序変更による新たな実装欠陥は見つからなかった。

## anchor 判定

[M1〜M9 の置換前 anchor](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1418-closure-mutation/out/s6-fix-1.md:21)は、現行 harness 内でそれぞれ１箇所と確認した。以下の赤は**静的な見込み**であり、実走結果ではない。

| ID | 期待 test の判定 |
|---|---|
| M1〜M4 | 報告された各 T2・T3 の期待 test が赤になる見込み。 |
| M5 | [T5 の runner 例外](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3527)により runner 後再検査には先取りされない。復元直前の検査を外すと branch ref 不変の期待が崩れる見込み。 |
| M6 | [T7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3564)と[新しい F1 試験](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3614)の**２ test**が、M を復元してしまうことを検出する見込み。 |
| M7〜M8 | 報告された T9・T8 が赤になる見込み。 |
| M9 | hold なしの[再検査ブロック](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/tools/mutation_harness.py:2409)だけを無効化する。[`[head]` と `[bytes]`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1418-closure-mutation/orchestrator/tests/test_mutation_harness.py:3489)が赤になる見込み。ただし `[head]` の単一理由性は上記のとおり不足。 |

## 総括

**NO-GO。** F1 と F3 の根本原因は静的に閉じているが、B-2 の HEAD 単独検出は未完成。`[head]` fixture を修正したうえで、親が行う実走結果を確認する必要がある。こちらではテストを実行していない。