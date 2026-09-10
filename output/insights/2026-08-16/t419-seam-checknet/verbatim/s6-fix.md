## 総括

- replay 用 3 面と発行専用 4 面を分離しました。
- artifact 失敗は 4 種類の面名を持つ例外連鎖になりました。
- `ident.py` の current chain／recorded prefix を検出する serial 2 テストを追加しました。
- 既知 4 赤の fixture と 65 環境テストの隔離方法を修正しました。
- 較正 artifact の読込を successor ごとに 1 回へ統合しました。
- 編集は所有内のコード・テスト 3 ファイルだけです。docs、commit、activation は変更していません。
- pytest は実行基盤の rc=16 により本体 0 件で、実装済み・未実走です。

### 所見ごとの対応

| 所見 | 判定 | 根拠 |
|---|---|---|
| F1 | partial | replay 3 面と発行時 `clock-method` を分離し、serial 1／2 と発行拒否のテストを追加。未実走 |
| F2 | partial | `ActivationArtifactError` に4面名を保持し、発行 tool も cause chain を表示。未実走 |
| F3 | partial | `ident` の current chain と recorded prefix 各配線を壊す serial 2 負例を追加。未実走 |
| F4 | partial | 実在 g2 artifact を一時 root へコピーし、65環境は artifact-only seam に限定。未実走 |
| F5 | partial | shared `_verify_entry_calibration` は変更せず、activation admission を単一 load に統合。未実走 |
| F6 | partial | 65環境成功テストの composite 丸ごと置換を除去し、callback identity assertion を併置。未実走 |

主な実装は [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/campaign/env_contract.py:443)、発行配線は [issue_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/tools/issue_env_contract_activation.py:209)、回帰網は [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/tests/test_env_contract_activation.py:1614) です。

### 検査結果

pytest 緑: なし。次の既知4 nodeと追加8 nodeを `tools/run_tests.py` へ投入しましたが、pytest 起動前に停止しました。

- local: `/run/user/31609` の admission 台帳を sandbox から更新不能
- dispatch: `qstat -Q` が `EACCTAUTH Unknown user-id`、rc=16
- テスト本体実行数: 0
- 観測されたテスト赤: 0
- 未確認: 既知4赤の解消、および追加回帰全件

静的検査は以下が rc=0 です。

- 変更3ファイルの AST parse
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 結合文字検査 0 件

### 所有外への波及可能性

- 通常 authority loader、`ident` の current／recorded 経路は replay 3 面を利用します。
- `artifact_admission.py` と campaign resume は、`ident` 経由でより深い artifact cause を受け取ります。
- `calibration_freeze_authority_execution.py` の事前確認は replay composite のまま互換ですが未実走です。
- `_verify_entry_calibration` の active／historical consumer は変更していません。
- `env_contract.py` は contract-loader source closure 対象なので、将来作る v2 lock の blob hash は変わります。既存外部 lock の consumer test は未実走です。