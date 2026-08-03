H2 の fixture 修正を working tree に残しました。docs・commit・git add・branch 操作は行っていません。

### 対応表

| 赤の型 | 状態 | 対応 |
|---|---|---|
| `test_critic.py` 17件 | closed（未実測） | policy-bound lock、canonical genome/source identity、正規の build admission receipt、attempt topology を共通 fixture 化 |
| `test_p3_s4_loop.py` 7件 | partial | 実 policy-bound lock と real validator を使用。receiptless pre-build quarantine を拒む担当外 H1 validator 修正待ち |
| `test_p3_s4_loop_sort.py` 4件 | partial | 同上 |
| `test_p3_s4_loop_trigger_gating.py` 3件 | partial | 同上 |
| `test_autonomous_trial_completeness.py` 5件 | closed（未実測） | `"g"` を canonical `fixture|` に変更し、canonical variant と stock receipt を使用 |
| `test_guided.py` 1件 | closed（未実測） | online digest fixture を policy-bound lock＋canonical stock receipts に変更 |
| `test_p3_exploration_namespace.py` 1件 | closed（未実測） | exploration layout の `.root` を real validator へ渡すよう修正 |
| `test_claude_transport.py` 2件 | closed（未実測） | direct helper 呼び出しにも共有 `BuildRunContext` を追加 |
| regressed | なし（静的確認範囲） | pytest 未実行のため実測判定ではない |

### Fixture と gate の根拠

- Critic fixture は [test_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_critic.py:49) で現行 policy を lock に束縛し、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_critic.py:84) で source evidence、generator/stock admission、canonical variant、attempt ID、receipt SHA を一括生成しています。dirty-source の表示用ラベルは決定論的 SHA-256 に変換し、揮発する working-tree hash は使用していません。
- Guided fixture は [test_guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_guided.py:90) で policy-bound lock と実 `derive_build_admission()` による receipt を使用しています。
- Autonomous Layer3 fixture は [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_autonomous_trial_completeness.py:1186) で同一 context の policy・receiptを使い、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_autonomous_trial_completeness.py:1220) で canonical genome/variant を生成しています。
- Loop fixture は [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_p3_s4_loop.py:80)、[test_p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_p3_s4_loop_sort.py:81)、[test_p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:103) で policy-bound lock を書き、実 `require_admitted_campaign()` を呼びます。
- 通常経路も [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/campaign/p3_s4_loop.py:263)、[p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/campaign/p3_s4_loop_sort.py:484)、[p3_s4_red.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h2/orchestrator/campaign/p3_s4_red.py:170) から real validator を通します。
- Validator の置換・無効化、assert の削除・緩和、skip・xfail 化は行っていません。loop テストの mock は real validator を `side_effect` で呼ぶ回数確認用であり、受理判定を潰していません。

### 検査

実行した pytest nodeidは0件です。`hostname=pegasus02` で、リポジトリ規律が login node 上の pytest を単一 nodeidも含め禁止しているためです。したがって緑は主張しません。

実行済み:

- 所有17ファイルの `python3 -m py_compile`: rc=0
- 所有17ファイルの `git diff --check`: rc=0

未実行:

- 所有9 test fileの全pytest/nodeid
- 受入全走
- mutation
- build・campaign実走
- 所有外テスト

### 直さず報告した項目

- Loop系14件は、正当な receiptless pre-build quarantineを `post-policy WAL record variant has no canonical BUILD_START identity` として拒む担当外 `artifact_admission.py` のH1修正に依存します。receiptを捏造して通すことはしていません。
- Guided通常経路の replay-only WAL は、post-policy lockに対して receipt付きbuild topologyを生成しません。正しく閉じるには replay/no-build専用の admission契約が必要であり、今回のfixture修正には含めていません。
- 共有working treeにある担当外差分には触れていません。

## 総括

合成campaign fixtureを、歴史成果物扱いへ逃がさず、policy-bound lockと正規receiptを持つpost-policy形へ移行しました。Critic 17件、autonomous 5件、guided 1件、exploration 1件、Claude transport 2件は静的には対応済みです。Loop系14件は正当なU2 pre-build rejectionを扱うH1 validator修正待ちで、現時点ではpartialです。