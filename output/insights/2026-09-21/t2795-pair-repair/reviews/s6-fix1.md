## 総括

既存テストと A-R3 の修正指示が衝突するため、指定の停止条件に従い、**実装を変更せず停止しました**。

[test_campaign.py:14451](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a1/orchestrator/tests/test_campaign.py:14451) の `test_authorization_session_new_session_cannot_inherit_claim` は、初回取得の失敗について次を要求しています。

- 最上位例外が `ExecutionGuardError`
- `__cause__` が `ClaimError`

A-R3 の「初回 `ClaimError` を透過」に直すと、この既存期待値は必ず失敗します。「期待値の方が誤りだと判断したら、実装を変えずに報告して止める」という今回の指示に該当します。継続には、このテストの例外期待値を変更対象に含める指示が必要です。

変更がないため、新たに受理する入力はありません。新たに拒否する入力もありません。維持する正例は、同一の有効な session で認可を 2 回行い、claim 取得が 1 回になるケースです。

赤 (a) の probe 確認、例外透過の修正、M4′ の構造変更、重複比較の削除はいずれも未実施です。**未実装・未実走**であり、pytest・構文検査・probe は実行していません。ファイル編集、git add／commit、docs 編集も行っていません。