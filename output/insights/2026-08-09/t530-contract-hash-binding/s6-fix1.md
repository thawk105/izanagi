実装済み・未実走です。docs 編集、commit、pytest 実行はしていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | `default_cfg()` を未束縛化。site seam 経由で一度だけ束縛し、autonomous は contract を明示渡し。completeness は lock の hash を ever-active 解決 |
| F2 | closed | 既存 hash の削除・上書きを廃止。不一致を fail-closed。注入 layout を最終 campaign-id と照合 |
| F3 | closed | guided の2 callerへ `False` を追加。正例を `ensure_resumable_wal` に通し、repair・terminal readまで検査 |
| F4 | closed | 正しい topology の不一致 COMMIT＋active attemptで、recovery ABORT・repair receiptとも bytes 不変を固定 |
| F5 | closed | T343 admission-bound/no-H、T428 descriptor/no-H を明示再計算して exact 比較 |
| F6 | closed | 固定 vector は generation-1へ固定。writer testは実際に認可された contract hash と比較 |

Production の挙動変更:

- 同一 hash の事前束縛は従来どおり受理します。
- 異なる事前束縛 hash、最終 ID と異なる layout、lock の不正・未知・非 ever-active hash は書込み前に拒否します。
- offline completeness は current generation の変更ではなく、成果物自身の lock に束縛された世代を使用します。
- guided production、`s1_direct_comparison.config_for`、scope 外の reader・sink・private lockには触れていません。

波及を静的確認した caller/consumer は、autonomous の identity preparation・launch/workload、write-time completeness、trigger CLI、exploration namespace test、synthetic authority fixture、real-repo serialization 対象です。`test_campaign.py` の新規テストは引数なしで、素の Python runner の収集契約を維持しています。

変更ファイルは production 3件と tests 7件です。

- Production: `p3_s4_loop_trigger_gating.py`、`p3_autonomous_workload_trial.py`、`autonomous_trial_completeness.py`
- Tests: `test_guided.py`、`test_campaign.py`、`test_p3_autonomous_workload_trial.py`、`test_autonomous_trial_completeness.py`、`test_p3_s4_loop_trigger_gating.py`、`test_p3_exploration_namespace.py`、`test_s8a_trigger_sweep.py`

## 総括

- F1 closed / F2 closed / F3 closed
- F4 closed / F5 closed / F6 closed
- production 3ファイル、test 7ファイルを変更
- docs変更なし、commitなし
- AST parse と `git diff --check` は成功
- pytest・素Python runnerとも未実走
- 残存リスク: 動的な全 caller と mutation 6 の実測確認は親の計算ノード実走待ち