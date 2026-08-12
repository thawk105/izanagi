実装済み・未実走です。pytest と commit は親に残しています。`git diff --check` は通過しました。

### 変更箇所と述語

- [t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:524)
  - `repository_roots_from_git_identity()`
  - 変更後の述語:
    - `gitdir.is_symlink()` → 従来どおり拒否。
    - `gitdir` が空文字 → `continue`。
    - 登録先の `resolve(strict=True)` が `FileNotFoundError` → `continue`。
    - 非 regular file、読取異常、UTF-8 異常、その他の解決異常 → 拒否。
    - 解決できた登録だけ `roots.add(registered.parent)`。
    - `identity.repo_realpath` と common-dir の親は常に roots に残る。
- [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:1024)
  - `test_git_common_dir_skips_missing_registered_worktree()` を追加。
  - 存在しない worktree の `.git` を指す登録が例外にならず、roots にも含まれないことを固定。
- [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:905)
  - `test_generated_script_executes_staged_wrapper_cli()`
  - 子 process の `sitecustomize.py` に `time.sleep = lambda _seconds: None` を追加。
  - `time.monotonic_ns` は変更していない。

### 赤 1

消滅済み worktree の登録だけを無視するようにしました。実在する main repo、coordinator worktree、解決可能な linked worktree は引き続き roots に入り、symlink 登録や異常な registration は拒否されます。

したがって、並行 churn による過剰拒否 P1 は除去しますが、実在する repository 内への書込み受理は広げません。

### 赤 2

`os.getloadavg` の固定に加え、正規 seam へ注入される `time.sleep` だけを no-op にしました。

以下はすべて維持しています。

- 3 サンプル連続条件
- load 閾値
- deadline と実 `time.monotonic_ns`
- timeout 30 秒
- exit code `2`
- stdout `pre_release_invalid\n`
- receipt の PBS ID / hostname

production codeには変更がありません。

### 期待値と段 5 契約

- 既存テストの期待値は変更していません。
- 段 5 差分に残っていた slot-00 の exact argv assert 緩和は撤回し、全 slot の exact assertへ復元しました。
- skip、xfail、削除、timeout 延長はありません。
- M1〜M6および P1/P2 の既存テストは維持。今回追加した stale-registration 負例が赤1を直接固定します。
- authority、依存閉包、TOCTOU、guard、budget APIには触れていません。

### 所有外への波及可能性

- `prepare_group()`、`_coordinate_authorized()`、`coordinate()` は、共有 repo の消滅済み worktree 登録によって停止しなくなります。
- 解決可能な linked worktree の保護集合は変わりません。
- `sitecustomize.py` の sleep 置換は当該統合テストの子 process 全体へ効きますが、専用 `PYTHONPATH` 内に限定され、production processには波及しません。
- 新規 test node を固定参照する既存 meta-test は静的検索では見つかりませんでした。
- 作業ツリーの他の2変更ファイルは継承した段5成果物で、今回のfixでは編集していません。

## 総括

赤2件を指定どおり修正しました。状態は**実装済み・未実走**であり、計算ノードでの実測と受入判定は親待ちです。