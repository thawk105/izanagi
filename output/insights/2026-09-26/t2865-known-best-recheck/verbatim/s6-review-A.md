## 所見

1. **must-fix [捏造/幻覚] — 選択による上振れを「含まない」は言い過ぎ。** 根拠: [README §3](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:99) は、新しい r' が「16 点から最大を選んだ」上振れを含まないと断定する。新しい値を*選択に使っていない*ことは確かだが、選ばれた 3 点だけを再測しており、同じ job 内位置などの交絡も残る。**影響:** 論文で選択効果を除去した証拠として読まれる。**修正案:** 「新しい r' は元の選択に使っていない値である。選択全体の補正や統計的優位は示さない」に留める。

2. **should [手順漏れ] — 元の throughput 3 値だけ、千 txn/s の丸め方が新しい表と異なる。** 根拠: [README §2.3–2.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:77) の元 job 0 fixed10 `3,972` は元 JSON の中央値 `3,972,631` を最近接の千で丸めれば `3,973`。元対象 `1110` の `4,215` は `4,215,854` → `4,216`、`1001` の `4,229` は `4,229,830` → `4,230`。3 値とも[元の記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md:50)の表示とは一致する。**影響:** 元と新の throughput 差の表示が各 1 千 txn/s ずれる。比と再現判定は変わらない。**修正案:** 生 JSON から同じ丸め規則で再表示するか、元の表示値を転載した列だと明記する。

3. **should [ドリフト] — 集計スクリプトに事前規則より強い束縛がある。** 根拠: [README §1.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:33) は**対象点**の IR 本文と因子を指定するが、[スクリプト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/verbatim/recheck-aggregate-script.md:54) は相方 IR にも同じ照合を課す。また[同スクリプト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/verbatim/recheck-aggregate-script.md:230)は新 3 job 間の toolchain 一致も要求する。現データではいずれも成立しており判定は変わらない。**影響:** 別の入力では、事前規則で対象点を判定できてもスクリプトが「判定不能」にしうる。**修正案:** この差を実装上の追加条件として明示し、今回の判定根拠は §1.3 の条件に限定して説明する。一般向けの追加 gate は不要。

## 照合表

出典の「新 JSON」は `compare-recheck/compare-{0,1,6}.json`、「元 JSON」は `compare/compare-{0,1,6}.json`。判定規則は[README §1.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:31)、集計値は[recheck-aggregate.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/env/pegasus/calibration/silo_function_policy_recon/compare-recheck/recheck-aggregate.json)。

| README の値 | 照合結果と一次資料 |
|---|---|
| §0・§2.4 の r'、元 r' | **一致。** 新 `1.051405 / 1.065106 / 1.073415` → `1.051 / 1.065 / 1.073`。元 aggregate `1.068096 / 1.068802 / 1.061960` → `1.068 / 1.069 / 1.062`。 |
| §2.3 の新参照 throughput・abort 率 | **全 12 組一致。** job 0: `2,356,127 (.784934) / 1,366,946 (.124795) / 2,348,207 (.791293) / 3,948,709 (.385020)`。job 1: `2,332,424 (.786865) / 1,359,841 (.122327) / 2,311,357 (.793903) / 3,910,180 (.388492)`。job 6: `2,514,211 (.775198) / 1,371,927 (.123282) / 2,553,841 (.779708) / 4,006,572 (.381760)`。順序は abort0 / stock / B0-L-W0 / fixed10。新 JSON の各 `cases[].bench`。 |
| §2.4 の対象 throughput・abort 率 | **全 3 組一致。** `1111: 4,151,691 (.292312)`、`1110: 4,164,757 (.344119)`、`1001: 4,300,716 (.341431)`。新 JSON の 5 rep 中央値。 |
| §2.4 の ÷B0-L-W0・÷stock | **全 6 値一致。** `1111: 1.768026 / 3.037202`、`1110: 1.801867 / 3.062679`、`1001: 1.684019 / 3.134799`。新 JSON の中央値同士から計算。 |
| §2.3–2.4 の元 throughput | 元記録の表示には**一致**。生の元 JSON を最近接の千で丸めると、fixed10 job 0 は `3,973`、1110 は `4,216`、1001 は `4,230` となり、README の `3,972 / 4,215 / 4,229` と**不一致**。他の元表示値は一致。 |
| §2.4 の元 abort 率・相方比 | **一致。** 元 abort `0.289924 / 0.341514 / 0.346251` → `.290 / .342 / .346`。新相方 `0.973067 / 0.983128 / 0.989225`、元相方 `0.983436 / 0.984035 / 0.994127` は各 3 桁表示に一致。 |
| 5 rep 最小・fixed10 最大 | **全 3 組一致。** `4,120,369 > 3,969,689`、`4,066,636 > 4,002,940`、`4,274,436 > 4,048,053`。新 JSON の `bench[].throughput`。 |
| request・node・開始 JST・Elapse | **一致。** `29950.nqsv / bnode105 / 11:23:58 UTC→20:23:58 JST / 770秒`、`29951.nqsv / bnode107 / 11:16:19→20:16:19 / 774秒`、`29952.nqsv / bnode108 / 11:16:19→20:16:19 / 774秒`。node・時刻は新 JSON、request・Elapse は [job0](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/recon/job0-a.log:4)・[job1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/recon/job1-a.log:4)・[job6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/recon/job6-a.log:4) のログ。 |
| §0・§4 の計算合計 | **一致。** `770+774+774=2,318秒`、`2,318/3,600=0.6439` → `0.64 node 時間`。 |
| §0 の 18 方策、§2 の適格性 | **一致。** 3 job × 6 行すべて `complete`、両 verify certified、trace0 clean、5 rep 有効、前後 source evidence が非空で一致。対象 abort 中央値はいずれも同 job abort0 の 2 倍以下。 |
| §1.3 の束縛と判定 | 新 JSON の phase・job・case_order・role は[driver の `_cases`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/orchestrator/campaign/silo_policy_recon.py:35)の巡回と一致。対象の本文 SHA・因子は元 JSON と一致し、abort0 本文 SHA、対照 flags、fixed10 の両 trace の実効 define、workload も一致。新しい `(hostname, started_at)` は元 8 job と重複しない。中央値の最大参照は各 job とも fixed10 で、`r' > 1.03` より**3 点とも「再現」**。列挙実装そのものの本文は指定資料に含まれないため、列挙との一致についてはスクリプトの照合と元 JSON との一致までを確認した。 |
| 計測前固定の §1 | `git show 4175771006:…/README.md` と `git diff 4175771006 -- …/README.md` で、**§1 本文の変更なし**。commit 日時は `2026-09-26 20:15:46 JST`。 |

§0・§3 の限定は、1 回の再測、未較正の 3% 線、job 内位置の交絡、pin 差と依存 module の変化、診断 build の NON_ADMISSIBLE、段階 E/F への firewall を記している。§0 の論文用文も、これらを同じ段落に置くという条件付きなら §1.4 の範囲内である。

## 総括

**NO-GO。** 数値による「3 点とも再現」の判定は支持される。**must-fix は §3 の「選択の上振れを含まない」という断定の修正 1 件。** 元 throughput の丸め 3 値と、集計スクリプトが事前規則より強い点も記録を整えるべきである。