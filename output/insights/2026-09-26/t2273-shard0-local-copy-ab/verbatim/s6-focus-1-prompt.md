単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s6-ruling.md — 段 6 裁定と erratum E1 / E2。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md — 段 4 裁定 (計測の事前登録)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s6-review-a-out.md、s6-review-b-out.md — 1 巡目の所見。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s6-fix-p1-out.md — fix 子の報告。
- fix 前後の集計器: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.v1.py.txt (前) と probe/t2273lc_ab_analyze.py (後)。同 dir の他 4 file は変更なし。
- 実装 (変更なし): wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy の `git show eb65d322f`。
- 変異 spec: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/mutation-spec-probe.json (M1〜M5 は段 4 登録 + E2)。

## 目的

段 6 fix 後の焦点再レビュー。1 巡目の所見 A1 / A2 / A3 / B1 / B2 / B3 ごとに closed / partial / regressed / (裁定で refuted・不変) を表で判定せよ。とくに:
- E1 の照合が erratum の文言どおりか (A 同士・B 同士の完全一致、A/B 差 = B のみ指定 1 件、共通 node の 3 shard 割付完全一致、それ以外の許容・一般化が無いか)。無効時に対・走が判定から外れ、land 条件の「有効 3 対」に数えられないか。
- 判定式・閾値・順序・門番・land 条件・5 分別判定が fix で変わっていないか。
- 変異 spec の置換が実装の現物と一致し、各変異の最初に落ちる assert が erratum E2 を含む登録理由と一致するか (静的に)。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 対応表` (所見 | 判定 | 根拠 file:line)
- `## 新規所見` (無ければ「なし」)
- `## 総括` (3〜6 行。GO / 修正後 GO / NO-GO)
