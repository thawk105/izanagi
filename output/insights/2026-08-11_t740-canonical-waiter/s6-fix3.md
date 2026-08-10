`acceptance` の merge 前に、所有実装面 overlap 判定を追加しました。commit は作成していません。

- [tools/dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:255)
  - repeatable な `--owned-path`
  - path 正規化と component 境界での完全一致・配下判定
  - `git diff --name-only HEAD...main` の独立 rc 判定 (`owned-path-diff`)
  - overlap 時は `owned-path-overlap` / rc=70 で merge 前に停止・lease release
  - 未指定時は diff を省略し、stderr に縮退通知を1行出力
- [test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:731)
  - exact match / directory 配下の overlap
  - diff 非0
  - `docs/x.md` と `docs/xy.md` の負例
  - 未指定時の warning と merge→commit→投入
  - repeatable CLI contract
  - overlap 経路は `_Effects.events` の exact 比較で、merge 0回・受入0回・release を固定

テストは実装済み・未実走です。以下を `tools/run_tests.py` 経由で試しましたが、すべて pytest 起動前に `qstat -Q rc=1`、wrapper rc=16 で停止しました。

- `orchestrator/tests/test_dev_wave_wait.py` 全体
- 追加した6 nodeid
- 同ファイルの `--collect-only`

user slice の余裕は約1.73 GiBで、local実行基準未満でした。代わりに AST parse と `git diff --check` は成功していますが、テスト緑とは扱いません。

既存 CLI contract への波及は、acceptance の受理 option が1つ増え、未指定時にstderr通知が加わる点です。delimiter、poll範囲、既定値、producer CLI の受理集合は変更していません。

対応表: closed=overlap実装・回帰テスト追加 / partial=テスト実走（環境rc=16） / regressed=静的確認上なし・動的未確認

## 総括

指定された2ファイルだけを変更し、merge前のfail-closed判定と検出力のあるテストを実装しました。最終状態は「実装済み・未実走」です。