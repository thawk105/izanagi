## (F1) 直した内容 (file:line)

[autonomous_trial_completeness.py:5115](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1232-impl/orchestrator/campaign/autonomous_trial_completeness.py:5115) で、診断経路の generation に `proposal` 宣言があれば構造化 `_fail` で拒否するよう変更しました。

受理集合から提案宣言付き入力を除外しました。該当入力が到達しなくなるため、この経路の `_cross_binding_proposals` 呼出しを削除しました。

[test_autonomous_trial_completeness.py:5781](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1232-impl/orchestrator/tests/test_autonomous_trial_completeness.py:5781) に、実 producer 正例へ提案参照だけを注入する負例を追加。拒否 gate とメッセージを指定した regex で確認します。

## (F2) の結論

**構成不能。テストは追加していません。**

先行 gate は同 verifier の以下です。

- `:3146`：非 Mapping decision を拒否。
- `:3150–3154`：positive decision は、外側の厳密 key 集合に必須の `pending_critic_disposition` があるため拒否。
- `:3165–3168`：positive でも厳密 failure でもない decision を拒否。

したがって、指定条件を満たしつつ M7 を単独で殺す入力は新述語まで到達しません。M7 は登録除外が妥当です。

## 実走結果

指定の自走 harness で対象ファイル全体を実行しました。

**283 passed／537.13 秒／終了コード 0。赤・skip なし。**

追加 nodeid も実走済みです。

`orchestrator/tests/test_autonomous_trial_completeness.py::test_failure_only_diagnostic_rejects_declared_proposal`

## 波及の静的列挙

- 変更経路：公開 API の opt-in 診断分岐 → 診断 helper。CLI も同 API を経由。
- 通常経路の `_cross_binding_proposals` 呼出しは維持。
- producer・既存 chain・cross-binding 本体は変更なし。
- 既存テスト・helper の AST は開始時と一致。
- 静的追跡範囲は指定ファイル内。

## 台帳

上記 nodeid を `0.0` 秒で追加しました。`nodeid_count` は **23141 → 23142**。登録キー数との一致も確認済みです。

## 総括

F1 は修正・実走済み。F2 は先行 gate により構成不能と確定しました。編集は所有 3 ファイルのみで、docs 編集・commit は行っていません。