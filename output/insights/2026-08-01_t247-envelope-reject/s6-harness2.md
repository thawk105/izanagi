35 件の変異 spec を持つ harness を実装しました。全 anchor の一意性と累積置換を静的確認済みです。tracked file の差分は残っていません。

## 総括

- (a) Harness: [harness.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:1)

  起動例:
  ```bash
  python3 .mutation-harness-t247/harness.py \
    --all \
    --ledger .mutation-harness-t247/ledger.jsonl
  ```

- (b) 変異 spec: **35 件**
  - submit: 13
  - job: 17
  - contract.py: 4
  - fixture: 1

- (c) 試走: `M-C1`
  - 実結果: `INFRA_OR_HARNESS_ERROR`、rc=16
  - 期待 KILL: **未確認**
  - 原因: `qstat -Q` が `EACCTAUTH Unknown user-id (uid: 31609)` で dispatch 前に失敗
  - [試走台帳](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/trial-ledger.jsonl:1)
  - node 抽出・semantic/diagnostic 分離の合成自己検査は成功しましたが、KILL 実測には数えていません。

- (d) 復元根拠:
  - 実試走台帳で `restore_content_equal=true`
  - 元本文との `read_text()` 比較に成功
  - `git diff` は空で、`git status` は `.mutation-harness-t247/` のみ untracked
  - timeout・signal 時も subprocess 終了後に親 `finally` で復元

- (e) 全走所要時間: **35 dispatch × 1〜2 分 = 約35〜70分**（queue 待ちを除く）

- (f) 未了事項:
  - PBS ユーザー認証が有効な親環境で `M-C1` の再試走と全35件の本走が必要
  - `py_compile`、`check_codex_agents.py`、`check_docs.py`、全 anchor 検査は成功済み
  - commit、git add、`.gitignore` 変更は行っていません。