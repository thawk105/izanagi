## 総括

HEAD `66e50e4b` は clean。敵対レビュー所見は、must-fix 1件、wave終了前の必須記録1件です。その他の指定項目に問題はありません。

### 所見1（must-fix）

`.claude/agents/auditor.md:67-71` → 型17〜21が、各機械検査の対象外となる具体的な構文・識別子・実行範囲を列挙している → D48/D511が禁じる「LLMが読める回避手順・境界条件」の開示になっている。

特に、lambda内部の未検査領域、未収載の非決定/副作用識別子、検出されるループ形と見逃されるループ形、有限corpusでのみ捕捉される例外、という形で回避方向が直接分かる。`docs/decisions.md:21296-21318` の「完全/部分/なしの分類に留め、境界条件を書かない」に反する。

段2案 `s2-plan.md:39-54` の抽象的な分類は安全だったため、機序を補う際もその粒度に留めるべきでした。型17〜21の分類と `working_diff` 監査指示は残し、具体的な検出/未検出形・識別子名・corpus境界は削除すべきです。

### 確認2：型17〜21の一貫性

問題なし。

- `.claude/agents/auditor.md:66-71,89`
- `manifest.json:119-123` → `maximum: 21`
- `auditor_gate.py:29` → `range(1, 22)`
- `test_auditor_gate.py:139-158`
- `test_p3_s4_loop_trigger_gating.py:1719-1725`
- `.codex/role-adapters/auditor.json:159`

全て5分割・17〜21で一致し、22は拒否されています。review ledgerの3 pinも更新済みです。

指定grepは履歴JSONの保存文字列も拾いましたが、現行の関連範囲に stale pin はありません。`tools/ruleops.py:2095` の `maximum=16` は文字列長上限で無関係です。

### 確認3：runbook追記

問題なし。`docs/phase3-s5-sort-runbook.md:94-110` で、JSON fenceは `97-104` に閉じており、追記はその後のauditor spawn文脈にあります。

`p3_s4_loop_sort.py:42-45` が示す通りspawn自体はメインセッション側なので、`designated_sources` へのAPI節追加という手動runbook指示は意味が通ります。機械検証ではない点は、段4裁定どおりです。

### 確認4：trigger-gatingへの影響

受理集合への影響はありません。

`p3_s4_loop_trigger_gating.py:421-439` と `auditor_gate.py:205-231` は型番号ごとに分岐せず、violationが空でなければrejectします。したがって型17〜21の誤引用は、passには転じず、trigger候補を許可しません。`p3_autonomous_workload_trial.py:298` の1〜21更新も共有schemaとの整合です。

ただし、以前の不正コードが「invalid」、現在は通常の `auditor-violation` rejectとして記録されるという状態/継続処理の差はあります。「実害なし」は、候補の許可/拒否集合に限った表現が正確です。

### 確認5：T-396 scope

問題なし。`git show 10f6d4f6 -- .claude/agents/coder-v4-autonomous-sort.md` は空で、commit差分にも同ファイルはありません。D344のraw C++方針も変更されていません。

### 所見2：新D記録は必要

`docs/decisions.md:4269-4279` のD96により、auditor出力schema/gateの受理範囲を16から21へ変更した今回の改修には、新しい設計判断と境界テストの記録が必要です。

D511（`21294-21318`）、D95（`4235`）、D344（`15206`）は制約を定めていますが、5分割、入力側runbook結線、共有gateのreject粒度、T-396非変更という今回固有の判断までは記録していません。段7で追加する判断は正しく、D511に反する具体的回避形は記録しないでください。