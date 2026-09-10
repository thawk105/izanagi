## 直した内容

- MF1: [test_p3_b4_closed_critic.py:2674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2674)、[:2727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2727)、[:2786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2786)、[:2920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2920) の置換対象を `_run_one_iteration_resolved` へ変更。fixture は `layout, contract, resolved_site` の positional 呼出しに追随させました。
- MF2: [p3_s4_loop.py:1446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1446) の内部 boundary を `"base resolved run_one_iteration"`、[:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1577) の公開 boundary を `"base run_one_iteration"` にしました。
- MF3: [test_p3_s4_loop.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:191) に公開 `run_one_iteration` の負例を追加。`PEGASUS_LOGIN` と `PEGASUS_SUSPECT` の双方で、stub していない実の `_admit_env_contract` が `ExecutionGuardError` を出す契約です。
- MF4: [test_p3_s4_loop.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:179) で reflux=off の OTHER cfg も `_campaign_cfg_for_site` に通し、`95a32c3e` を検査します。既存の on arm も引き続き helper 経由です。

## 既存期待値を変えていないことの確認

- 元の `test_p3_s4_loop.py:4576` にあった regex は、追加行による移動後の [test_p3_s4_loop.py:4609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:4609) でも `match="base run_one_iteration"` のままです。
- 既存 golden ID `8ee68c0c` と `95a32c3e` の assert は [test_p3_s4_loop.py:4562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:4562) に無変更で残っています。
- 既存 assert の反転、緩和、skip、xfail、削除はありません。差分上の期待値削除検査も該当なしでした。

## 実走結果

実装済み・未実走です。

`tools/run_tests.py` で MF1〜MF4 の焦点 6 nodeid を dispatch しましたが、強制 dispatch と自動配置の双方が `qstat -Q preflight rc=1`、`rc=16`、child未起動で終了しました。したがって緑と申告できる nodeid はありません。

静的検査では、対象3ファイルの AST parse、MF1の署名、MF2のboundary、MF3の実呼出し形、`git diff --check` が通過しています。

## 所有外への波及

- [p3_b4_launcher.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:141) は base `main` を登録し、[:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:549) と [:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:602) から起動します。[:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:624) の gate が変更した boundary を診断へ反映します。
- [p3_b4_closed_critic.py:1984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_closed_critic.py:1984) は base cfg を供給し、launcherから `main`、`drive_iteration`、内部 resolved へ至る consumer です。
- [test_p3_exploration_namespace.py:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_exploration_namespace.py:1291) は公開 `run_one_iteration` を直接通す consumer test です。
- [test_p3_b4_launcher.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_launcher.py:42) は base on/off cfg と launcher context の consumer test です。
- [test_p3_b4_wiring_probe.py:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_wiring_probe.py:330) は公開 iteration/drive の静的 inventory と実 producer interception を検査します。
- [conftest.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/conftest.py:239) の autouse site fixture は追加負例にも適用されますが、テスト自身の `_current_site` 差し替えが後から優先されます。

## 総括

- MF1〜MF4を指定3ファイルだけに実装しました。
- MF5および裁定外の実装には触れていません。
- docs、output、既存golden、既存regexは変更しておらず、commitやindex操作もしていません。
- 焦点テストはdispatch基盤障害のため未実走で、親側の全走が必要です。