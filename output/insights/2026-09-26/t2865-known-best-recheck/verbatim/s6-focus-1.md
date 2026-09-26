## 対応表

| 前巡の所見 | 判定 | 根拠 |
|---|---|---|
| 1. 選択による上振れを「含まない」と断定 | **closed** | [README §3](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:102) は、新しい値を元の選択に使っていないことに限定し、選択全体の補正や統計的優位は示さないと明記した。 |
| 2. 元 throughput 3 値の丸めが不揃い | **closed** | 元 JSON の 5 rep 中央値を再計算すると、job 0 の fixed10 は **3,972,631 → 3,973**、1110 は **4,215,854 → 4,216**、1001 は **4,229,830 → 4,230**（千 txn/s、最近接丸め）。[README §2.3–2.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:76) の修正値と一致し、旧表示の 3,972・4,215・4,229 が切り捨て値であるとの注記も計算と整合する。 |
| 3. スクリプトに事前規則より強い束縛 | **closed** | [README §2.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/README.md:74) は追加条件を明記した。[スクリプト本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-26/t2865-known-best-recheck/verbatim/recheck-aggregate-script.md:56) は全 IR 行の本文 sha256・因子を照合し、新 3 job の toolchain 一致も要求する。JSON 上、相方 3 点の本文 sha256・因子はそれぞれ元 job と一致し、新 3 job の toolchain も一致する。 |

## 新規所見

なし。修正箇所の周辺に、新たな過大主張や誤った量化は見当たらない。

## 総括

**GO。残る must-fix はなし。** 修正後の記述と数値は、指定された一次資料および集計スクリプトと整合する。