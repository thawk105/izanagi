## 総括

D291 の trust root 偽造経路を実装上は閉じました。ただし Pegasus の `qstat -Q` preflight 障害によりテスト本体は未実走です。このため全所見を `partial（実装済み・未実走）` と判定します。docs 編集・commit・所有外ファイルの編集は行っていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| C1 | partial | projection API の payload 引数を廃止し、固定 `F_p` bytes を毎回再読 |
| C4 | partial | 公開 renderer の report object 引数を廃止し、repository root から内部構築 |
| D3 | partial | C1 と同じ。caller 構築 payload を公開 API が受理しない |
| C5 | partial | 後続 decision に `D291` が現れれば無条件に `possible_supersession` |
| C6 | partial | fixture を literal `b13b7ea…` に固定し、実装定数との独立 assert を追加 |
| C7 | partial | canonical 桁合わせへ修正。両置換対象が `F_p` に各 1 件あることを静的確認 |

変更箕所は [approval_d291.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py)、[report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py)、[__init__.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/__init__.py) と対象テスト 2 本です。

公開 API の変更:

- `require_d291_projection_exact(payload, projection)`  
  → `require_d291_projection_exact(repository_root, projection)`
- `resolve_d291_approvals(repository_root, *, candidates=None)`  
  → `resolve_d291_approvals(repository_root)`
- `approval_report_to_dict(report)`  
  → `approval_report_to_dict(repository_root)`
- `build_approval_report(repository_root) -> ApprovalReport`  
  → `build_approval_report(repository_root) -> dict[str, object]`
- `D291ApprovalPayload` / `D291RoleResolution` / `ApprovalReport` / `SupersessionScan` は公開名から除去し、内部型へ変更

検査結果:

- 走らせた nodeid: なし
- 試行範囲:
  `orchestrator/tests/test_t793_approval_d291.py`
  `orchestrator/tests/test_t793_report.py`
- 結果: `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`。pytest の収集・実行前に停止
- `python3 -m py_compile` は対象 5 file すべて成功
- C7 の canonical literal は `pilot_submission`、`main_submission` とも `F_p` 内で各 1 件
- 両 test file の `__main__` self-runner は維持

所有外への波及可能性:

- リポジトリ内に旧署名を使う所有外 Python caller は見つかりませんでした。
- 将来、削除した公開型または旧引数を import する外部 consumer があれば追随変更が必要です。
- `test_plain_runner_coverage.py` は共有 meta-test として両 test file を走査しますが、self-runner は残しています。
- 親の mutation matrix は公開署名と supersession status の新しい anchor に再照準する必要があります。