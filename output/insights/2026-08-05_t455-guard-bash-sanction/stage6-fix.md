修正しました。[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:915) で以下を変更しています。

- `collect_receipt.py` を control から除外。
- `bash tools/pegasus/certify_calibration.sh` に差し替え。
- `python3 tools/pegasus/run_probe.py` は維持。
- 未裁定の login 手順を pin しない理由を docstring に記載。

静的確認では、`certify_calibration.sh` は現行 `_SANCTIONED_PATHS` に含まれず拒否されます。仮に `_is_sanctioned` を「`tools/pegasus/` 配下なら許可」へ退行させると sanctioned 早期許可へ入り、`assert not ok` が失敗するため、恒真 control ではありません。

テストは実行していません。ホストが `pegasus02` であり、上位規律がログインノード上の pytest を単一 nodeid も含め禁止しているためです。緑は主張しません。

- 未実行 nodeid: `orchestrator/tests/test_hooks.py::test_bash_login_fetch_third_party_does_not_sanction_siblings`
- 未実行の要求範囲: `python3 -m pytest orchestrator/tests/test_hooks.py -q -rf`
- 静的検査: `git diff --check -- orchestrator/tests/test_hooks.py` 成功

## 総括

- control を `collect_receipt.py` から `certify_calibration.sh` へ差し替えた。
- `run_probe.py` は維持し、理由を2行の docstring に記録した。
- control が directory 一律許可への退行を検出できることを静的確認した。
- この fix では `hooks/guard_bash.py` を編集せず、変更前後の受理集合は 1 bit も変わっていない。
- 残リスクは、ログインノード規律により pytest 実測が未完であること。