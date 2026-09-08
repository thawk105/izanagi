## 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial | 現物 sink 4061 を確認し、4051 の pin 2 箇所を更新。3294 は不変。pytest 未実走。 |
| F2 | partial | 指定名の collector 負例を追加。90 record、tag 15/75、variant、45 block record、lock を維持し、1 record の `anomalies` だけを 1 に変更。pytest 未実走。 |
| F3 | partial | lock monkeypatch を削除し、3 個の production binding helper から実 lock を生成。validator stub の限界を docstring に明記。pytest 未実走。 |

regressed と判定した所見はありません。

## 変更した file と行

- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_ccbench_spawn_sites.py:885)
  - pin 2 箇所を 4061 へ同期。
- [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2997)
  - collector fixture を共有 helper 化。
  - [正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3119)を実 lock 通過へ変更。
  - [拒否側 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3142)を追加。

段 5 の production file は編集していません。

## 走らせた検査と結果

- 指定焦点走: rc=16、pytest child 未起動。
- collection と所要台帳 meta-test の追加走: rc=16、pytest child 未起動。
- 原因はいずれも `qstat -Q preflight rc=1`。
- `git diff --check`: rc=0。
- 変更 3 file の AST parse: rc=0。
- 保護定数・関数の HEAD 比較: rc=0。
  - frozen digest literal は各 45、計 135 で不変。
  - binding、validator、lock検査、collector の各関数は不変。
  - golden 2 個と `wal.py` も不変。
- `python3 tools/check_codex_agents.py`: rc=0。
- `python3 tools/check_docs.py`: rc=0。

pytest は実装済み・未実走で、緑の nodeid はありません。

## 赤の内訳と帰属

- pytest の赤はありません。2 回とも child 起動前の dispatch infrastructure failure です。
- 自作の静的確認は初回に `frozenset` の解析方法を誤り rc=1。checker を訂正して再実行し rc=0。製品・test の失敗ではありません。
- runner が生成した一時 dispatch receipt 2 組は、各 exact directory を確認後に除去済みです。

## 波及の静的列挙

- 4061 pin の consumer:
  - `test_define_sink_cross_product_has_no_unreviewed_ungated_member`
  - `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
  - `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- `_verification_source_disclosure` の production caller は `_collect_report_inputs` のみ。さらに `run_formal` の report 分岐から到達します。
- collector fixture helper の共有先は新しい正例と拒否例の 2 test のみです。
- `_collect_report_inputs` を静的検査する既存 4 test、および既存 collector test が consumer です。
- 新規 node に波及する meta-test は `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`。静的投影は約 91.604% ですが未実走です。

## 裁定から外れた点

実装上の逸脱はありません。docs、commit、push、branch、凍結成果物、repository 外、`wal.py` は変更していません。full `--phase report` も実行していません。

検査のみ、Pegasus dispatch 障害により未実走です。

## 総括

F1〜F3 は実装済みですが、権威ある pytest が起動していないため全件 partial です。親側で指定焦点走と所要台帳 meta-test の実走が必要です。