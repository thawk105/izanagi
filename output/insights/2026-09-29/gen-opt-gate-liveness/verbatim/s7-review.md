## 所見

- **F1・must-fix** — [README §0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/output/insights/2026-09-29/gen-opt-gate-liveness/README.md:14) の「発生条件はどれも 0 でない」は生出力と食い違う。[stock result.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/output/insights/2026-09-29/gen-opt-gate-liveness/raw/s1-stock-result.json) の `runs.W-rmw.gate.occurrence.W_R_occurrences` と `W_W_occurrences`、`runs.W-blind.gate.occurrence.M_M_occurrences` はいずれも **0**。**直し方:** 「D2b (i)(ii) に必要な発生条件は両 workload で 0 でない」と限定する。

## 照合して一致を確かめた数値

README の §0 結論表、§2.1〜§2.3 の **6 run 行**と発生条件、job 表の **4 行**、CI build の **2 構成**、format の **2 構成**、[fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/docs/spool/worklog/2026-09-29-dev-wave-gen-opt-gate-liveness-1.md:10) の本文・次の一手差分を照合した。commit・abort・違反件数・B1 計数・判定器の verdict と取引数・Elapse・rc と秒・format 件数・sha256 は、F1 を除き該当する raw field と一致した。Elapse 合計は **420 秒 = 約 0.12 node 時間**。事前登録の判定と `not-exercised` の扱いにも取り違えは見つからなかった。

## 総括

**NO-GO。** F1 の事実と異なる量化を直せば、指定資料の範囲では記録してよい。