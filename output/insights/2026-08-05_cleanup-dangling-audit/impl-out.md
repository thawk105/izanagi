## 総括

実装は完了しましたが、Pegasus の計算ノード dispatch が認証エラーで停止したため、受入検査は未閉鎖です。commit・`git add`・`docs/` 編集は行っていません。

- [tools/audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/tools/audit_dangling_commits.py)
  - 到達不能、main に path 不在、全 local branch tip に path 不在、の3条件を実装。
  - `docs/spool/`、`docs/archive/` を既定除外。`--include-fold-trees` で上書き可能。
  - 既定 repo はスクリプト位置から解決。
  - Git エラーは fail-closed の rc=2、検出時 rc=1、0件時 rc=0。
  - 実行する Git 操作は `fsck`、`diff-tree`、`ls-tree`、`for-each-ref`、`rev-parse`、`show` の読み取り専用操作のみ。

- [test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/orchestrator/tests/test_audit_dangling_commits.py)
  - positive control 1本。
  - negative control 4本：main 到達可能履歴、main に同 path が存在、生存 branch tip に同 path が存在、fold 管理木のみ。
  - 合成 repo はすべて `tmp_path` 配下。

- [cleanup-branches.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/.claude/commands/cleanup-branches.md)
  - §1 に実行・§5報告の1行を追加。
  - 最終サイズは **3,981 bytes**（実効上限3,983）。
  - 予算は、F26への「事象と原因の」という重複説明と、直前に列挙済みの手動手順および重複F26参照を縮約して確保。
  - §2、F26の復元・安全手順、F51、§5 push引き渡し義務は維持。

- [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/tools/check_docs.py) / [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/orchestrator/tests/test_check_docs.py)
  - 実ファイルから計算した SHA-256 `41cdaf95919eeb45bc930a394072979fc936a9f590723f6e1fd95c0eef9537cd` を独立2 pinへ反映。
  - テスト内 whole-file fixtureも実ファイルと同一内容へ更新。期待値の緩和はなし。

検査結果：

- `python3 tools/check_docs.py`: **rc=0、違反0件**
- `python3 tools/check_codex_agents.py`: **rc=0**
- `python3 -m py_compile`（新規2ファイル）: **rc=0**
- fixture SHA-256静的照合: **一致**
- `git diff --check`: **rc=0**
- `orchestrator/tests/test_audit_dangling_commits.py`（5 nodeid）: `tools/run_tests.py` 経由で計算ノードdispatchを試行したが、`qstat -Q` が `Unknown user-id (uid: 31609)`。**rc=16、pytest実行0件**
- `orchestrator/tests/test_check_docs.py`（ファイル全範囲）: 同じdispatch基盤エラー。**rc=16、pytest実行0件**
- 現行repoへの `python3 tools/audit_dangling_commits.py`: 入力依存で未分類のためPegasusログインノードでは実行せず、scheduler認証も失敗しているため **実装済み・未実走**。0件は未確認。

参照案との差異：

- 既定repoを cwd ではなく自身の位置から解決：今回の明示要件に合わせた。
- Git subprocess失敗を黙って空集合にせず実行不能へ倒した：見逃しを正常0件と誤認しないため。
- branchごとの `cat-file` 反復ではなく、各tipの`ls-tree`集合で判定：3条件をコード上で独立させ、subprocess数を抑えるため。
- main到達可能commitの専用負例を追加し、要求どおり positive 1 + negative 4 とした。
- cleanup呼び出しを `python3 ...` まで明記したため、参照案の3,973 bytesではなく3,981 bytes。
- 参照案の「2段判定」という説明は採用せず、裁定済みの3条件を明記した。

静的な波及可能性：

- caller は `.claude/commands/cleanup-branches.md` と、それを読む cleanup-branches Skill。
- consumer test は `test_check_docs.py` のwhole-file pin、byte/最長行、invalid-backtick負例群。
- 共有fixture変更はなし。新規監査テストは標準の `tmp_path` / `capsys` のみ使用。
- 新規ツールを直接参照する既存callerは、静的検索上cleanup command以外にない。
- 親の段6レビュー、変異matrix、計算ノードでの上記pytest、現行repo実走がやり残しです。