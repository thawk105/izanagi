[must-fix] 共通自己改善契約の受理集合が 3 command のまま

根拠: next-tasks は共通契約へ dispatch する一方、契約本文は既存 3 command だけを対象としています（[next-tasks.md:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/.claude/commands/next-tasks.md:259)、[skill-self-improvement.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/skill-self-improvement.md:3)、[skill-self-improvement.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/skill-self-improvement.md:34)）。checker も H3 を 3 件に固定し、next-tasks 終端の追加を「孤児」として拒否します（[check_docs.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py:833)、[check_docs.py:6372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py:6372)）。docs 地図も同じ 3 件列挙です（[docs/README.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/README.md:49)）。

成果物影響: checker は next-tasks の自己改善先が未定義でも緑になり、逆に正しい第4終端を追加すると land を拒否します。

推奨: 移設ファイルの bytes は変えず、共通契約の対象・発火条件・routing・終端、docs 地図、対応する exact literal／合成 fixture を第4 commandへ追従させてから land する。

[should] 移設後も「本ファイルは repo 外」という命令が残る

根拠: tracked command 自身を「repo 外」と呼んでその場で直すよう命じ、直後には repo 内 command の変更を裁定送りにしています（[next-tasks.md:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/.claude/commands/next-tasks.md:261)）。また主要処理は `/work/1/SFC/tanab/scripts/` の絶対パスへ依存します（[next-tasks.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/.claude/commands/next-tasks.md:29)、[next-tasks.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/.claude/commands/next-tasks.md:72)）。

成果物影響: land 後の自己改善時に tracked file の直接編集と裁定送りが競合し、別環境では未管理の絶対パス依存により command が実行不能になります。

推奨: bytes 同一という明示条件（[brief-stage1.md:25](/home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md:25)）を優先し、d42f2bec5 では変更しない。「tracked command の編集境界」と「off-repo scripts を恒久依存として認めるか」を裁定へ返し、別 commit で直す。

[should] 現物 27,054 bytes の恒久 assertion が上限制約を exact-size 制約へ変える

根拠: test は予算 literal／plus-one に加えて、実 checkout の現物が常に 27,054 bytes であることを固定しています（[test_check_docs.py:2531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/orchestrator/tests/test_check_docs.py:2531)）。checker 本体の契約は 27,100 bytes 以下です（[check_docs.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py:287)）。

成果物影響: 27,055〜27,100 bytes の正当な将来編集は checker が受理しても test が落ちるため、46 bytes の予算余白が実質利用不能になります。

推奨: 27,054 assertion は今回の移設受入記録へ限定して恒久 test から外し、予算 literal と 27,101-byte 負例だけを残す。bytes 同一性は今回確認した SHA-256 一致で記録する。

所見外の確認:

- repo 側と元ファイルはともに 27,054 bytes、SHA-256 `10c6c0b4…9ee15` で一致しました。
- 予算余白は next-tasks が 46 bytes（0.170%）。既存 3 件の相対余白 0.032〜0.285% 内なので、`27_100 / 100` 自体は過大とは判定しません。
- command directory の閉包は `COMMAND_LIMITS` から導出されるため、第4 command は予算・存在検査へ入っています（[check_docs.py:5840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py:5840)）。`_ENUMERATED_DOCS` は living docs 用で、command の脱落ではありません。
- `arguments_count` は実装上 `$ARGUMENTS` の出現回数です（[check_docs.py:6088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py:6088)）。Claude Code の positional `$1` と矛盾せず、値 0 は正しいです。
- M1/M2 の報告された単一-node runnerでは、失敗集合はどちらも `test_next_tasks_command_budget_literal_is_exact` のみです。M1 は行2535の `KeyError`、M2 は同じ行の literal assertion で停止します。全 test file を mutation runner にする場合、M1 は共有 fixture の clean-positive nodes も広く赤にしますが、その走行は実装報告では主張されていません。
- `python3 tools/check_docs.py` は rc=0。48837186c は gitlink 110件削除＋既知違反1件追加で、レンズCの追加所見はありません。

## 総括

must-fix 1件、should 2件、nit 0件です。

確信のない点は、Claude Code 本体を live probe していないため `$1` の製品仕様を実環境では再確認していないこと、および M1 の全-file mutation failure 完全集合は実走されていないことです。