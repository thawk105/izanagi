単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s6-ruling.md — 段 6 裁定 (所見 8 件と fix の形)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s6-review-a-out.md、s6-review-b-out.md — 所見の原文。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s6-fix1-out.md — fix 子の報告 (closed の主張)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s4-ruling.md — 事前登録 §3。
- 対象: 作業木 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe の fix 後 commit `2a1b83339` (`git diff 2ebf25e24 2a1b83339 -- tools/` と、fix 後の 3 file 全体 `tools/t2273_replica_{runner,plugin,analyze}.py`)。計測される側は同作業木の `orchestrator/tests/test_s8b_oracle_driver.py`・`orchestrator/tests/conftest.py`。

## 焦点再レビュー

fix の主張を信じず、所見ごとに closed / partial / regressed を判定せよ。fix が新しく壊したもの (regression) も探せ。とくに:
- RA2: import を thread 内へ移した後、controller の hook が失敗・例外を握りつぶさず、thread 内の import 失敗が `failed.json` と P 無効へ届くか。worker 側の待ち上限 180 秒が、写し生成が遅いときに P を無効にする方向で働くこと (fallback しないこと)。
- RA3: file の digest と dir の path 集合 digest の両方が A/P 比較に使われているか。
- RA6: 「実際の memo 例外文」が conftest の実文と一致しているか (conftest を grep して照合)。
- RA5 / RB5: 有効 3 対未満で (b) を名指ししないこと、集計が有効対だけであること。事前登録 §3.3 の基準式 (3 対すべて Δ>0 ∧ r 中央値 ≥ 10 %) と §3.5 (pre 55〜80 秒の外は外れと明記) が出力にあること。
- 計算ノードで初回に落ちる型 (import・path・clean env・例外の握りつぶし) の残り。

read-only で書込可能 tmp が無いので静的検査でよい。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 対応表` (所見 ID ごとに closed / partial / regressed と根拠 file:line)
- `## 新規所見` (ID FN1..、重大度、根拠、放置時の結論への影響 1 行、推奨修正。無ければ「なし」)
- `## 総括` (3〜6 行、GO / 修正後 GO / NO-GO)
