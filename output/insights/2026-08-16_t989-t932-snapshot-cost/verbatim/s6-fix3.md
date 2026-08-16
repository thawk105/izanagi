## 総括

**NO-GO（検証未完了）**  
修正内容と exact oracle は整合し、standalone import は rc=0。  
ただし collect-only は規定 wrapper が rc=16 で停止し、親による実走確認が必要。

変更内容:

- [growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t989-t932-snapshot-cost/orchestrator/tests/growth_test_holds.py:406): 旧 407–421 行の対象保留を削除。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t989-t932-snapshot-cost/orchestrator/tests/test_s8b_floor_campaign.py:55): guard import と旧 8295–8297 行の呼出しのみ削除。
- [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t989-t932-snapshot-cost/orchestrator/tests/test_growth_test_holds_contract.py:39): count、digest、collateral、held module 集合を更新。
- [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t989-t932-snapshot-cost/orchestrator/tests/test_hold_inventory.py:185): reason / axis / node / collateral の対象 oracle を削除。

期待値の新旧:

- 登録件数: `57` → `56`
- key digest: `e0d35a319d7409310e14d1e471226ce0ebc046d637100825be41c4036f5e4c83` → `922510c85e7439818e224d64652b0357b3965bae842c4fe72edda33846ee8408`
- row digest: `dd941ebd14d1da2b36ea9faf03649ca2b6f442b69cc88281326e91071281d402` → `cfc9ba15bcbad25e3f9d5fc2031f96b76c96ef7f44b7f4a142df0cad9ecba11c`

検証結果:

1. 指定の standalone import: `ok`、rc=0。
2. 指定の直接 `python3 -m pytest --collect-only ...`: リポジトリ規律が直接 pytest を禁止するため未実行。代替の `python3 tools/run_tests.py --collect-only ...` は queue preflight 失敗で rc=16。
3. count・digest・held module・exact inventory oracle の直接 assert: `contract-oracles-ok`、rc=0。
4. `git diff --check`: rc=0。

他の 26 件は、導入 commit `59606f29` の追加 27 件を抽出し、対象 1 件を除いた全 26 件について、現在の登録存在と全 dataclass field が修正前 HEAD と同一であることを照合しました。結果は `introduced=27 removed=1 remaining-identical=26`、rc=0 です。

所有外への波及はありません。変更は許可された 4 ファイルだけで、docs 編集・commit・新規保留・他保留の解除は行っていません。