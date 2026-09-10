テスト fixture のみ修正し、production 判定は変更していません。

[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:1333) では `git add -f` を使い、次を明示的に検証します。

- main: `collision.txt` が `!!`、つまり ignored かつ untracked
- wave: `git ls-files` に存在し tracked
- checker: 監査中に main 側だけを削除
- 結果期待: fingerprint 不一致による `RC_PROVENANCE`

さらに[元から存在しない正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:1373)を追加しました。同じ `unlink(missing_ok=True)` checker でも、監査前後とも main に collision が無ければ land 成功を要求します。これにより「消えた」と「元から無かった」を区別しています。

| 所見 | 対応 | 根拠 |
|---|---|---|
| ignored collision fixture が wave 側で tracked 状態を作れない | partial | `add -f` と状態 assert で修正済み。実走不能のため closed とは申告しない |
| 「消えた」と「元から無かった」の区別 | partial | 負例と正例を同一 checker 条件で固定済み。実走待ち |
| 他の新設 fixture の同種欠陥 | closed | 新設差分を静的点検。別の exclude 使用は `.codex/worktrees/` のみで、commit 対象 `tools/...` と非衝突。既存 ignored-target fixture は既に `add -f` を使用 |
| pathname 一時差し替えの残余 risk 記述 | closed | [実装コメント](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:1471)どおり、実行は pathname、照合は前後の束縛 FD なので、実行中だけ差し替えて復元する窓は残る |
| regressed | なし（静的確認範囲） | production と既存期待値は未変更 |

波及可能性は以下です。

- `_Repo.commit` は変更していないため、共有 fixture の全 caller への強制 add 拡大はありません。
- `tools/dev_wave_land.py`、RC、受理・拒否集合は fix 2 では変更していません。
- 新規正例により収集数は 76 から 77 へ増えます。exact 件数を固定する consumer は静的検索では見つかりませんでした。ファイル内 `_run()` は動的収集です。
- linked worktree 共通の `.git/info/exclude` という性質は当該 2 テスト内に局所化されています。

## 総括

- 修正: ignored target を `git add -f` で wave に tracked 化し、main の ignored/untracked 状態を assert。元から absent の正例も追加した。
- 実走: 焦点 2 nodeidを `tools/run_tests.py` で投入したが、`qstat -Q preflight rc=1` の dispatch infrastructure failure、`rc=16`。collect-only も同理由で `rc=16`。したがって**実装済み・未実走**。全体も未実走。
- 静的検査: 両ファイル AST parse、`git diff --check`、`tools/check_codex_agents.py`、`tools/check_docs.py` はすべて rc=0。
- 残余 risk: checker pathname を実行中だけ差し替えて終了前に復元する race は、従来申告どおり未検出窓として残る。production の緩和・docs 編集・commit は行っていない。