## 総括

F1・F2 を実装しました。**テストは未実走**です。`run_tests.py` がキュー照会失敗（`qstat -Q`、rc=16）で停止し、テスト本体は起動していません。

## 変更一覧

- [tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1988): 退避経路で子木削除前に wave の祖先条件を再確認。削除後の admin 再検査にも wave path を渡す。
- [test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_dev_wave_cleanup.py:376): 退避開始後に wave HEAD が非祖先へ動く負例を追加。
- [dev_wave_cleanup_stop_hook.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup_stop_hook.py:82): stdin を 1 MiB に制限し、超過・非 UTF-8・不正 JSON を出力なしで通過。
- [settings.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/.claude/settings.json:53)、[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_hooks.py:5258): Stop hook の timeout 10 秒を設定・固定し、入力の負例を追加。

## テスト実走

**実装済み・未実走。** 新旧の焦点 5 nodeid を `tools/run_tests.py` で 2 回試みましたが、いずれも dispatch 前に rc=16 で停止しました。構文、settings JSON、`git diff --check` は通過しました。

## 変異との対応

- M13：削除前の wave 再検査を外すと、新テストは子木が消された時点で失敗します。
- M14：stdin 上限を外すと、読めれば block される巨大 JSON を新テストが検出します。

## 未了・リスク

焦点テストの実走確認が残っています。静的に列挙した波及先は、退避経路の削除前・admin 再検査、Stop hook の入力処理と設定配線です。統合済み経路の判定条件は変更していません。