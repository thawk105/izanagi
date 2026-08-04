## 総括

- **判定: closed（実装済み、実走は親待ち）**
- 変更ファイル: [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:333)
- 変更した関数:
  - `_invoke`: tolerance を任意指定可能に変更。既存呼出しの既定値 `"5"` は維持。
  - `test_cli_artifact_preserves_effective_clock_tolerance_argument`
- 新規 node:
  - `orchestrator/tests/test_calibrator_certify.py::test_cli_artifact_preserves_effective_clock_tolerance_argument[pegasus-2pct]`
  - `orchestrator/tests/test_calibrator_certify.py::test_cli_artifact_preserves_effective_clock_tolerance_argument[nondefault-7_5pct]`

`2.0` と `7.5` を CLI に渡し、各実行について attempt の `calibration.json` と registered artifact の双方に同値が保存されることを pin しました。

production を `tolerance_pct = 5.0` に固定化すると、`pegasus-2pct` node の [assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:631) が `5.0 != 2.0` で赤になります。`nondefault-7_5pct` でも同じ assert が `5.0 != 7.5` で赤になります。手前を除いても registered artifact の assert が同様に落ちます。

検査結果:

- `git diff --check -- orchestrator/tests/test_calibrator_certify.py`: 成功
- `python3 -m py_compile orchestrator/tests/test_calibrator_certify.py`: 成功
- pytest: **実走できていません**。現在地が Pegasus ログインノード `pegasus02` のため、単一 nodeid も実行禁止です。緑は主張しません。

波及可能性:

- 共有 helper `_invoke` の既存 caller 15 関数・23 node 相当へ署名変更が波及しますが、既定 argv は従来どおり `"5"` です。
- 既存 node 名、期待値、受理・拒否条件は変更していません。
- 静的検索では既存 node 名を参照する外部 caller/meta-test は見つかりませんでした。
- production、docs、output は編集せず、add・commit・stash も行っていません。