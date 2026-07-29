修正完了しました。変更は [test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:338) の対象テストのみです。

- HEAD blob を `git cat-file` で独立取得
- dirty bytes が HEAD blob と内容・長さとも異なることを、書換え前に assert
- production inventory は fixture 条件の導出に不使用
- before/after canonical inventory の同一性を維持

検査結果:

- 対象テスト: `1 passed`
- `test_ruleops.py` 全体: `83 passed`
- `git diff --check`: 成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功

HEAD は開始・終了とも `8976c14aa585bc47278ec5d6637edbb105bfe6e5`。staged 差分・commit はありません。開始時から存在した未追跡 output には触れず、新規変更は指定ファイルだけです。Codex hook の発火は主張していません。