## 総括

**採用推奨。D1936項30の本体1行追加と、既存test module内の局所契約更新で十分です。** planを覆す追加のmust-fixは確認できません。静的確認のみで、書込み・pytest・変異は未実走です。

- **real：既存テストだけでは欠落を検出できない。** [test_t316_sandbox_probe.py:1439](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/orchestrator/tests/test_t316_sandbox_probe.py:1439) のfixture PBSは `exit 0`、同ファイル:1533／:1557はPython関数の直接呼出しです。shell配列entryを除去しても、この契約では検出できません。検査前importを許す実装を受け入れる成果物影響があるため、planのshell契約追加は必要です。

- **real：F28型maskの経路はあるが、planは回避している。** [PBS:60](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:60) のdirty検査の後にはblob照合(:68)、runtime照合(:80)、さらに[Python:2331](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/tools/pegasus/probes/t316_sandbox_backend_probe.py:2331) のdirty検査があります。全体の「拒否した」だけでは、[同:36](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/tools/pegasus/probes/t316_sandbox_backend_probe.py:36) のimport前に拒否した証拠になりません。配列とdirty検査だけを実PBSから抽出する案を採用します。

- **refuted：fixtureが必ず先に落ちるという所見。** [テスト:1507](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/orchestrator/tests/test_t316_sandbox_probe.py:1507) は準備後のcleanを確認しています。fixture返却後に対象だけを変更し、fixture内PBSを上書きせず抽出コードを実行すれば、このassertでの偽killは避けられます。ただし未実装なので、実走での確認は残ります。

最小実装は、PBS配列への条件関門1行追加、独立literalの5pathを使う局所テスト、実PBS内の検査からprobe起動までの順序確認です。抽出は追加でずれる固定行番号に依存させません。Python側・receipt・汎用harnessの変更は不要です。[brief:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2543-preimport/brief.md:12) の局所拡張案は妥当で、100行上限を埋める追加検査も不要です。

正負例と変異期待nodeは、既存モジュール内で次のように明示することを推奨します（名称は提案）。

| node | 通常版 | 条件関門entryだけ除去 |
|---|---|---|
| `test_execution_binding_shell_clean` | rc=0、markerあり | 同じく成功 |
| `test_execution_binding_shell_dirty[condition-unstaged]` | rc=3、markerなし | rc=0、markerありとなり**結果assertで失敗** |
| `test_execution_binding_shell_dirty[condition-staged]` | rc=3、markerなし | 同上 |
| 同dirtyテストの既存4path各例 | 拒否契約を満たす | 同じく満たす |

F820型の偽killを排除するには、条件関門の両nodeが**fixture・抽出・配列一致assertではなく、実行結果assertで失敗したこと**を受入時に確認します。配列一致検査を置く場合も、それだけの失敗をdirty拒否契約の変異検出として数えません。これは既存検査の観測条件であり、新しいgateや台帳を作る提案ではありません。