## 所見

- **RB1 — must-fix** — [runner:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_runner.py:650), [analyzer:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:895): P には `T2273_PRECOPY=1` を渡す一方、`run.json` には記録せず、`T2273_LOCAL_OUTPUT_SOURCE` に文字列 `T2273_PRECOPY` を記録する。全対で `intervention_env` が偽となり、約 1,000 秒の job を完走しても有効対にならない。**P の実際の環境値を正しいキーで記録する。** smoke は analyzer を実行しないため捕まえない。
- **RB2 — must-fix** — [analyzer:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:857): P の `copy.digest` が欠けた key を内包条件で飛ばすため、A 側だけ digest があっても `stat_digest_equal=True` になりうる。写しの同一性を確認せず (a) を推奨しうる。**全 key に A/P 各 1 件の digest を要求する。**
- **RB3 — must-fix** — [analyzer:935](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:935), [analyzer:976](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:976): 3 対未満または無効対があっても「この基準では確認できない」「(b) の候補」を出す。測定失敗を効果不足と誤読させる。**有効 3 対が揃わない場合は「判定不能・取り直し」とし、(b) を名指ししない。**
- **RB4 — should** — [analyzer:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:897): 早期 memo 超過をログ内の英語 `early memo` と `timeout` 等の同一行だけで判定する。実際の超過表示が異なれば無効走を有効にし、条件別件数も過少になる。**計測した memo event または既存の構造化ログから明示的に超過を判定する。**
- **RB5 — should** — [analyzer:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:953): `next_publish_phase` は全 P 発行の phase 秒数の総和だけで選ぶ。無効対も含み、1 回の発行の律速とも限らず、(b) の対象を誤って名指ししうる。**有効対の key 別 phase 中央値を示し、対象の判断根拠を明記する。**

## 総括

**修正後 GO。** RB1 は smoke を通って本走後に初めて表面化する確定的な判定不能要因。RB2・RB3 は結論の向きを誤らせるため、本走前に修正が必要。指定資料と対象コード・差分による静的レビューであり、計算ノードでの実走は確認していない。