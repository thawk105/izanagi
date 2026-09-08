## 所見

- **A-01 / 高** — 対象: [s2-plan-out.md:33](</home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md:33>)、[t316_sandbox_backend_probe.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:310)、[condition_meaning_gate.py:2515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:2515)。プランは summary と `supply_pair` の両方で `supply.evidence["comparison"]` を直接参照する。ところが gate は production-issued の赤 supply も正当な record として扱い、例えば stock root 不在なら `stock-tree-unavailable` と `{"detail": ...}` を発行する。`require_condition_gate_family` はこれを例外にせず `admitted=False` として返すため、再 admission 後でも `comparison` は存在しない。現行コードなら `.get()` と `observed.admitted is True` により `False` となる入力が、変更後は `KeyError` で `verdict_s6` 全体を脱出する。S6 verdict 呼出し自体は [t316_sandbox_backend_probe.py:2556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:2556) で保護されておらず、final receipt を失いうる。具体例は、`BACKOFF_FIXED=-1/default=None/stock_comparison=True`、`stock_root=None` の genuine supply、undeclared meaning、そこから得た genuine `admitted=False` admission の三つ組。

受理集合そのものには過剰拡張を認めない。提案された値は「tuple 二つの `frozenset`」なので交叉を許さず、第 3 reason も含まない。gate は [condition_meaning_gate.py:3691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3691) で交叉を先に拒否する一方、第 3 reason は admit するため、probe の述語は恒真ではない。root-location-only 正例と第 3 reason 負例が、それぞれ独立に述語を効かせる実在入力になる。`comparison=None` の green record は gate で拒否され、tuple membership でも受理されない。

summary への `comparison` 追加は、それ自体では既存の equality 検査を弱めない。比較対象の field が一つ増えるだけである。issuer capability は [condition_meaning_gate.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:663) で canonical 対象外かつ `init=False` であり、scalar comparison から復元できない。公開される evidence は comparison 一項だけで、D1625 が要求した組の記録そのものに相当する。

## 親 brief への反証

- [s1-brief.md:31](</home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md:31>) の「root-location-only 環境では S6 が `S6_CONDITION_GATE_UNPROVEN` に固定」は条件不足。S6 は gate より先に attempted、walltime、toolchain、source identity を判定するため、例えば `attempted=False` なら `S6_BUILD_NOT_ATTEMPTED` になる。正しく言えるのは「それら先行条件を通過した root-location-only 観測では固定」まで。

- [s1-brief.md:38](</home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md:38>) の実測主張は、射影内では参照先の一行を挙げるだけで検算不能。また probe 自身が [t316_sandbox_backend_probe.py:2606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:2606) で「単一 PBS allocation を全 gen_S node へ一般化しない」と明記している。仮に引用された一例が正しくても、証明できるのは存在性だけで環境族への一般化ではない。

- 成果物影響は「go への到達阻害」だけではない。`condition_gates` の永続化形が変わるため、同じ v1 schema の observable receipt surface も変化する。旧 identity summary は新しい summary equality を通らず、関数全体の入力集合は単純な上位集合ではない。

- 「pin 閉包は空」という主張または根拠は、検査対象の brief 44 行には存在しない。空であるとの親実測として数えることはできない。

## 裁定パッケージ候補

- **既存問題:** [t316_sandbox_backend_probe.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:365) の Python equality は JSON scalar の exact type を検査しない。例えば receipt の `"admitted": 1` は生成値 `True` と等価になる。今回追加する文字列 `comparison` の境界は破らないため、本 wave の修正対象ではない。

## 総括

tuple 集合は D1625 の二組だけを正確に表し、交叉・第 3 reason・`None` の過剰受理はない。  
gate が交叉を mask する範囲はあるが、root-location-only と第 3 reason により probe 述語の独立効果は実在する。  
ただし `comparison` の直接添字参照は genuine な赤 family で `KeyError` を起こし、fail-closed verdict をプロセス失敗へ変える。  
したがって、段 2 プランは現状のままでは受理不可。