指定された 3 ファイルだけを変更し、commit は作成していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| R1 | closed（pytest 未実走） | landed commit 全件の parent を `rev-list --parents --no-walk=unsorted` 1 回で取得。件数・順序・未知 SHA・非 ASCII を fail-closed 化 |
| R2-1 | closed（pytest 未実走） | cutoff の proper ancestor が trusted parent になる正例を追加 |
| R2-2 | closed（pytest 未実走） | zero-trusted merge の第2 parent だけに署名が見える負例を追加 |
| R2-3 | closed（pytest 未実走） | trusted parent がちょうど1つの octopus 正例を追加 |
| R3 | closed（pytest 未実走） | main-side fold 作成→wave merge→no-fold/declared-fold land の両経路を通す E2E を追加 |

主な変更箇所は [git_state.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:634)、[test_dev_waves_git_state.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:444)、[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:2574) です。

subprocess 回数は、landed 区間の完全走査について次のとおりです。`p_i` は各 merge commit の parent 数、`t_i` は trusted parent 数です。

- cutoff なし: `1 + n_linear + Σ p_i`
- cutoff あり: `1 + n_linear + Σ [p_i + (1 if t_i == 1 else p_i)]`
- 全 `n` commit が非 merge: `n + 1`
- 全 `n` commit が `p`-parent merge:
  - cutoff なし: `1 + np`
  - trusted 一意: `1 + n(p + 1)`
  - trusted 0/複数: `1 + 2np`

先頭の `1` が全 landed commit 共通の parent 一括取得です。成功経路全体では、上記に head と no-fold pending 検査の `+2`、または head と declared-fold 形検査の `+3` が加わります。

検査結果:

- `python3 -m py_compile`：変更3ファイル成功
- `git diff --check`：成功
- `python3 tools/check_codex_agents.py`：rc=0
- `python3 tools/check_docs.py`：rc=0
- pytest：**未実走**。変更2 test file 全体と `test_plain_runner_coverage.py` を dispatch したものの、collection 前に `qstat -Q preflight rc=1`、infra rc=16 で停止。実走 nodeid は0件です
- `test_n31_landed_interval_cannot_hide_an_earlier_fold`、既存 test 関数・既存 assert の削除や期待値変更はありません

静的な波及可能性:

- 所有外 caller：`tools/dev_wave_land.py`、`checker.py`、`daemon.py`。checker/daemon は cutoff 未指定の全-parent意味論を維持し、parent subprocess だけが全件1回へ減ります。
- land consumer：declared-fold と no-fold の両 keyword 配線を新E2Eが直接通ります。
- 共有 fixture：既存 `_Repo`、`_seed_pending`、`_fold_commit`、`_FakeFoldModule` を利用。既存 fixture 本体は変更せず、main-side fold 用 helper のみ純増です。
- consumer test：integration の checker/daemon 経路と fake fixture は非 merge/no-cutoff のまま意味変更なし。ただし pytest 未実走のため実測確認は親側に残ります。
- scope 外の署名2条件、checker/daemon cutoff schema には触れていません。

## 総括

- R1〜R3 は指定編集面で実装済みです。
- parent 取得は landed commit 数にかかわらず1 subprocessです。
- cutoff 未指定時の差分集合は全-parent走査のままです。
- 追加した6 nodeは scheduler 障害により未実走です。
- 静的検査4種は成功し、docs変更・commitはありません。