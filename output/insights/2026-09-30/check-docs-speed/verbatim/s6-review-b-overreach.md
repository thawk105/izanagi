1. **should-fix** — [check_docs.py:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1106)、[同:3137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3137)。`entry_ids` は全 archive の全 entry 分を保持しますが、archive 間の遷移で後から使うのは各 archive の先頭分だけです。**推奨:** archive 内の遷移を検査した後は先頭 entry の ID だけを保持する。併せて不要になる `field(default_factory=list)` と import を削れるか確認する。

2. **should-fix** — [check_docs.py:1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1384)。LRU は4文書に制限されていますが、文字列と全改行位置を保持するため、常駐量は大きい文書4件の長さに比例します。**推奨:** 親の E3 で peak RSS を旧版と比較し、増分が大きければ件数・寿命を縮める。

3. **nit** — [test_check_docs.py:12965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:12965)、[同:12975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:12975)。T1 は59,048対照、T2 は436,698対照で、T2 には約11.2万回の例外経路が含まれます。数秒という裁定上の目安は静的検査だけでは確認できません。**推奨:** 親の実走で追加テストの所要を記録し、長ければ網羅範囲を変える前に裁定を見直す。旧実装の複製は CR・CRLF と assert 経路を広く守るため、現段階で削る根拠はありません。

## 総括

**GO（静的レビュー）。must-fix: なし。** 差分に検査項目の削除、閾値の緩和、対象の除外、既存期待値・exact pin・既存 helper の変更は見当たりません。既知の hold 契約違反は予定どおり修正が必要です。テストと新旧比較はこのレビューでは実行していません。