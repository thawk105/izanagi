## 総括

- 2箇所の競合を両 branch の意図を保つ形で合成しました。
- conflict marker は0件、AST 構文検査は成功しました。
- `_open_dir` の rc 意味論と、post-provenance の lease 解放判定を維持しています。
- 既存テストや docs は編集していません。
- pytest は dispatch infrastructure failure の rc=16 により未実走です。緑とは報告しません。
- commit は作成していません。
- `git add` は Git 管理領域が read-only のため実行できず、親による staging が必要です。

### 競合1

[`tools/dev_wave_land.py:429`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:429) の例外経路を次の合成にしました。

- rc は固定せず、引数 `rc` を使用
- `retryable_same_request=True` を維持

全8 caller の調査結果:

- `RC_IDENTITY` の既定値を使う6箇所:
  - [541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:541)
  - [873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:873)
  - [875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:875)
  - [898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:898)
  - [1778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1778)
  - [1786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1786)
- `RC_CONTROL_PLANE` を明示する2箇所:
  - [1148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1148)
  - [1780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1780)

したがって `RC_IDENTITY` 固定は受理集合を変えるため採用していません。

### 競合2

[post-provenance 合成箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2958) は以下を両立しています。

- target-aware な `_control_snapshot(repository, preflight.control.worktree_targets)`
- `_surviving_worktree_bindings_unchanged()` を含む main 側の判定
- 条件成立時だけ active plan を再観測
- 読み込み失敗は `RC_FOLD_RECOVERY_FAILED`、同一 request で再試行可能
- rc=21 の `release_safe` は `refreshed_active_plan is None` で決定

head・collision fingerprint の変化は従来の rc=29 と指定 reason を維持し、その後にだけ全 `_locked_preflight()` へ進む順序です。

### `_control_snapshot` 呼び出し

全5箇所を新しい signature に揃えました。

- [1311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1311): `repository, targets`
- [1313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1313): `repository, targets`
- [2958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2958): `repository, preflight.control.worktree_targets`
- [3266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3266): `repository, control.worktree_targets`
- [3275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3275): `repository, control.worktree_targets`

検査結果は `syntax-ok`、conflict marker 0件です。pytest は指定コマンドで実走を要求しましたが、`qstat -Q preflight rc=1` により wrapper rc=16となり、pytest本体は未実走です。受理 rc、status、reason、テスト期待値はいずれも変更していません。