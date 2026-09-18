## 総括

[build/t2686_ab_compare.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/build/t2686_ab_compare.py)のみ修正。全140行、追加24／削除1行です。

- **closed（関数検査範囲）**：両reviewの正常完了未確認。既存の一致・同main・process減に、4payloadすべての正常完了を追加。timeout／error／parse失敗／truncatedを拒否し、正常なindeterminateと不要処理を許容します。
- **検査成功**：正常例、負例11ケース、最終成功式5ケース、構文・空白検査。
- **partial**：旧新4走の実測確認は親待ち。pytest・性能測定・CLI全体は未実走です。検査範囲内でregressedなし。
- **波及**：共有fixture・production・既存テストは変更なし。tools／orchestrator/tests内にdriver参照は見つかりませんでした。親が置換するrepo外driverとsummaryの利用側には正常完了情報が追加されます。

argv説明の非阻害所見は所有外のため未変更。docs編集・add・commit・子起動は行っていません。