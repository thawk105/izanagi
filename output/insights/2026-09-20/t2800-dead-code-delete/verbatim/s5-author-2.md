## 変更

開始時の `git status --porcelain` は空。HEAD は `947fd160a`、branch は指定どおりでした。

変更後の `git status --porcelain`（逐語）:

```text
 D orchestrator/campaign/p2_5.py
 D orchestrator/campaign/s6_amendment_20260713_fence.py
 D orchestrator/campaign/s6_canary_rename.py
 D orchestrator/manual_probes/t1994_capdrop_probe.py
 D orchestrator/manual_probes/t1994_readonly_snapshot_liveness.py
 D orchestrator/manual_probes/t1994_rootview_probe.py
 D orchestrator/manual_probes/t1994_seccomp_probe.py
 M orchestrator/tests/test_ccbench_spawn_sites.py
 D orchestrator/tests/test_insights_date_layout.py
 D orchestrator/tests/test_migrate_output_gzip.py
 D orchestrator/tests/test_plot_t2266_tail_mechanism.py
 D tools/insights_date_layout.py
 D tools/migrate_output_gzip.py
 D tools/plotting/plot_t2266_tail_mechanism.py
```

`git diff --stat`（逐語）:

```text
 orchestrator/campaign/p2_5.py                      | 167 ----
 .../campaign/s6_amendment_20260713_fence.py        | 117 ---
 orchestrator/campaign/s6_canary_rename.py          | 312 --------
 orchestrator/manual_probes/t1994_capdrop_probe.py  |  99 ---
 .../t1994_readonly_snapshot_liveness.py            | 100 ---
 orchestrator/manual_probes/t1994_rootview_probe.py | 100 ---
 orchestrator/manual_probes/t1994_seccomp_probe.py  |  96 ---
 orchestrator/tests/test_ccbench_spawn_sites.py     |   4 -
 orchestrator/tests/test_insights_date_layout.py    | 447 -----------
 orchestrator/tests/test_migrate_output_gzip.py     | 473 -----------
 .../tests/test_plot_t2266_tail_mechanism.py        | 505 ------------
 tools/insights_date_layout.py                      | 411 ----------
 tools/migrate_output_gzip.py                       | 885 ---------------------
 tools/plotting/plot_t2266_tail_mechanism.py        | 625 ---------------
 14 files changed, 4341 deletions(-)
```

共有 test の diff は指定された canary 4 行の削除だけです。stage・commit はしていません。

## 実走

**実装済み・未実走**。指定の pytest コマンドを試みましたが、起動前に PreToolUse hook が拒否しました。実走 nodeid・pytest の終了コードはありません。

```text
[guard_bash] 拒否: interpreter の baseline 重量対象 (pytest) を拒否します: Pegasus ログインノードでは重い処理を実行できません。qsub または qlogin を使い、Pegasus 計算ノードで実行してください。
```

`python3 -m py_compile orchestrator/tests/test_ccbench_spawn_sites.py` と `git diff --check` は終了コード 0 でした。

## 所有外への波及

指定範囲を stem の固定文字列で検索しました（path の一致も包含）。指定された歴史記録を除外した結果は **97 hit** です。全 hit の所在を、連続行は範囲にまとめて列挙します。

| file | 行（範囲内の全行が hit） | 一致対象 | 件数 |
|---|---:|---|---:|
| `orchestrator/tests/README.md` | 138 | `- test_insights_date_layout.py` | 1 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 9667–9728 | `test_insights_date_layout.py` の nodeid | 62 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 10128–10139 | `test_migrate_output_gzip.py` の nodeid | 12 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 14137–14158 | `test_plot_t2266_tail_mechanism.py` の nodeid | 22 |

これ以外の hit はありません。削除後の spawn-site 表にも参照はありません。台帳の96件は段4で保持指定された stale entry です。

## 親への申し送り

- README の `PYTEST_ONLY_ALLOWLIST` は、138行目の `- test_insights_date_layout.py` を削除してください。他の削除 test 2本は掲載されていません。README は未編集です。
- 台帳は未編集です。「README 以外0件」という検索期待には、保持指定の台帳96件を例外として含める必要があります。
- 親側で staging、README 追随、計算ノードでの焦点走・受入をお願いします。
- 補助の Python 差分検証も hook の構文分類で拒否されたため、通常の `git diff`・`rg` で確認しました。

## 総括

削除13 file・共有 test の追随4行は完了しました。  
scope 外のソース・文書・台帳は変更していません。未stage・未commitです。  
構文検査は成功。pytest はログインノード拒否により未実走です。