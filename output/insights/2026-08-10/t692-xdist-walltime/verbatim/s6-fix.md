## 総括

- F1: **直した**。kwargs 負例を positional 1個＋kwargs 非空、expected `{"real-repo"}` に変更。MT4 は kwargs 検査を消した場合だけ負例が通過する。
- F2: **直した**。missing-only と extra-only を独立追加。MT5 の各片側緩和は対応する一方の負例だけを通過させる。
- F3: **直した**。marker 付与を pre-yield、ソートを hookwrapper の post-yield に分離。`--ff`／`--nf` の cache 状態を注入した実 collection chain と、loadgroup FIFO sentinel を追加。MT6・MT7 は独立 literal と priority 定数の不一致だけで落ちる。
- F4: **直した**。全 CLI instance の最大 index と全 barrier instance の最小 indexを比較し、parameterized 正例も追加。対応する事前登録変異はなし。
- fix の未 stage 差分は tracked テストの [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:249) と [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:434) のみ。production・docs・tools・禁止ファイルは未編集、commit なし。
- 実走を試みた selector:
  - `orchestrator/tests/test_real_repo_serialization.py -n 0`
  - `...::test_xdist_group_audit_rejects_synthetic_negative_controls`
  - `...::test_real_repo_priority_order_is_literal_and_writers_follow_barrier`
  - `...::test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence`
- 結果はいずれも pytest 起動前に `qstat -Q preflight rc=1`、runner rc=16。実行 nodeid は **0件**で、**実装済み・未実走**。
- 静的検査は `git diff --check`、対象2ファイルの `py_compile`、`check_codex_agents.py`、`check_docs.py` がすべて rc=0。
- 変異の単一理由性はコード上で確認済み。ただし MT4〜MT7 の mutation harness と pytest による実証は未実走のため、実測確認はできていない。