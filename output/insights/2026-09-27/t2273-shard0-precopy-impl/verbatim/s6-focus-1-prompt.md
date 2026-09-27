単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s6-ruling.md — 段 6 裁定 (所見と扱い、変異 erratum E1・E2)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s6-review-a-out.md、s6-review-b-out.md — 元の所見。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s6-fix-l.patch — fix L の差分 (wave 木 commit `6041d2f28`)。wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy で `git show 6041d2f28`、全体は `git diff ad114fba0 6041d2f28`。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s6-fix-l-out.md、s6-fix-p-out.md — fix 子の報告 (変異の置換表を含む)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/probe-v1/ と probe/ — fix P の前後 (repo 外の計測 probe、`t2273pi_ab_analyze.py` だけ差分あり)。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## 焦点再レビュー

1. 所見 A1〜A4・B1 ごとに closed / partial / regressed を判定し、根拠 (file:line) を付けた対応表を作れ。A3 は「実装を変えず受入の実走で確かめる」裁定なので、その裁定が妥当かだけ見よ。
2. fix が新たに壊したもの (既存テストの期待値、受理集合、終了処理の例外順序、T1 の検査力) が無いか。
3. 変異の置換表 (fix 子報告) の old 文字列が fix 後の各 file で一意か、各変異が単一理由で期待 node の期待 assert に落ちるかを、実装の実際の行で検証せよ。特に E1 (M4 の 2 置換) で T1 のどの assert が先に落ちるか、E2 (M6) で T1 が 10 秒待った後どの assert で落ちるか。
4. fix P: A/B collection と追加 node 入力の必須化が、事前登録 (s4-ruling の計測の事前登録 3) と一致し、他の挙動を変えていないか。

## 出力形式

見出し「## 対応表」(所見 ID、判定、根拠)、「## 新たな所見」(ID F1〜、重大度、file:line、根拠、修正案、無ければ「なし」)、「## 変異の検証」(ID ごとに一意性・落ちる assert・単一理由か)、「## GO 判定」、「## 総括」(5 行以内)。
