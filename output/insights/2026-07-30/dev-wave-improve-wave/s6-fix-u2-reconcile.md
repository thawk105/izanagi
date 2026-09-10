唯一の must-fix は、current bytes の実装・静的契約上 **closed**、partial は **0件**です。実走未了のため live GO は主張しません。

変更ファイル:

- [tools/pegasus/test_dispatch.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:2871)
- [orchestrator/tests/test_pegasus_test_dispatch.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:1198)

実装内容:

- 実測済み NQSV `qstat -f` の `Request ID`／完全な `Request Name`／`Current State` を厳密解析。
- exact hash-bound job name が1件なら normalized ID を回収。
- rc0 ID解析失敗は monitor、timeout／signal／output-limit は qdel 補償後に終端 receipt を封印。
- 0件・transient は visibility grace／budget 内だけ再照合。多件・malformed・unknown state は即 fail-closed。
- lookup request、exact argv、job name、stdout/stderr/rc を bounded receipt と WAL hash chainへ束縛。
- resume は WALの既存照合結果を再利用でき、自動 qsub 経路を持たない。
- 通常の qsub stdout ID成功経路では lookup を呼ばない。
- 指定された期待赤ケースと、lookup出力上限・通常成功非回帰テストを追加。

静的確認はすべて通過しました。

- Python 3.10 AST parse
- Python 3.10 isolated import
- pyflakes
- exact `qstat -f` seam／resume no-qsub／必須test存在のAST検査
- `git diff --check`
- `tools/check_codex_agents.py`
- `tools/check_docs.py`
- policy canonical SHA-256確認: `c52c597531172b243e341f5086776112407d357f4d47d279c0296f50253e5917`

`test_dispatch_policy.json` は編集していません。docs、insight、freeze、provenance、他owner、submoduleも未編集です。commit／push／staging更新も行っていません。

未実走:

- pytest
- build
- qsub / qstat / qdel
- compute-node targeted/full/mutation/acceptance

## 総括

U2 #7 の unique job-name 自動照合を既存 NQSV CLIだけで実装し、scheduler orphanを残す timeout／signal 窓と resume再投入リスクを閉じました。must-fixは静的に closed、partial 0件です。ただし計算ノード受入が未実走のため、live投入判定は引き続き親の受入・再レビュー待ちです。
