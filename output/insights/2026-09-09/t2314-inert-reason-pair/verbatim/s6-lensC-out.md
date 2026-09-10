## 所見

なし（must-fix 0 / nit 0、静的検査）。

- exact 条件はすべて維持されている：`observed == expected`、receipt summary 一致、`observed.admitted is True`、`driver_id`、`macro`、supply green、meaning の status/reason は [t316_sandbox_backend_probe.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:375)–386 に残る。
- probe production 内の `evidence[...]` は 0 箇所。summary と述語はいずれも `.get("comparison")` を使う。[t316_sandbox_backend_probe.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:340)、[同:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:383)
- 具体例として `stock-tree-unavailable` の赤 supply は `comparison` を持たないが、gate は赤 evidence に green schema を要求せず admission=false を返す。summary は `comparison=None` となり、`verdict_s6` は例外ではなく `S6_CONDITION_GATE_UNPROVEN` を返す。[condition_meaning_gate.py:2514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:2514)、[同:4000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:4000)、[probe.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:390)

追加 test の層別到達性：

- `identity` 正例：production evaluator → gate admission=true → receipt 一致 → pair membership=true → go。
- `root-location-only` 正例：手書き `_arm_record` や依存 stub は使わず、実 CMake/C++ と production evaluator で record を発行している。[test_t316_sandbox_probe.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:185)
- 交叉負例 2 件：gate を [test:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1027) で中和し、交叉後 family から receipt を再生成しているため、receipt equality も通過し pair membership だけで拒否される。
- 第 3 reason 負例：`stock_comparison=False` の production record で、gate admission=true・receipt 一致の後に pair membership で拒否される。[test:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:233)
- 差分の削除行は既存 helper 呼出し 1 行と旧 production 述語 2 行だけ。既存 assert の反転・緩和・削除、skip/xfail、閾値変更はない。

## 受理集合の列挙

変更後に受理される完全集合は次の 2 組だけ：

```text
{
  (
    "stock-inert-preprocess-identical",
    "stock-inert-identity",
  ),
  (
    "stock-inert-preprocess-root-location-only",
    "stock-inert-root-location-only",
  ),
}
```

根拠は定数の 2 要素 [t316_sandbox_backend_probe.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:124)–133 と tuple membership [同:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:381)–384。gate が許す第 3 組は [condition_meaning_gate.py:3691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3691)–3707 にあるが、probe 集合との積集合から除外される。

`None`、missing、空文字、bytes、部分文字列はいずれも tuple の exact membership に一致しない。さらに reason は gate が exact `str` を要求し、green comparison は reason ごとの完全な文字列と照合される。[condition_meaning_gate.py:3991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3991)、[同:3702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3702)

## 変異 M1〜M4 の予測

- M1 — 期待どおり。赤くなる完全集合：
  `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`
- M2 — 期待どおり。赤くなる完全集合：
  `test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`、
  `test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]`
- M3 — 期待どおり。赤くなる完全集合：
  `test_s6_rejects_requested_default_preprocess_difference`
- M4 — 期待どおり。赤くなる完全集合：
  `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`
  （実 comparison を持つ test receipt と定数化された production summary が不一致になる。）

巻き添えで赤くなる node、または殺せない変異は予測されない。

## 裁定パッケージ候補

- 既登録：receipt の `"admitted": 1` は Python equality 上 `True` と等しく、summary equality を通過できる。[probe.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:352)、[同:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:376)
- scope 外の既存所見：`IZANAGI_T316_RUNTIME_PBS` は `_BOUND_RELATIVE_PATHS[1]`、すなわち `.py` と比較される。通常どおり `.pbs` を渡すと bytes 不一致で実行 binding が失敗する。[probe.py:2290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:2290)、[同:2337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:2337)

## 総括

GO。D1625 の 2 組と変更後の受理集合は完全一致する。  
旧 exact 条件の脱落と A-01 の例外回帰はない。  
追加 5 node はすべて目的の層へ到達し、M1〜M4 の期待 KILLED 集合も正しい。  
既存テストの期待値変更・緩和・skip・削除はない。  
scope 外の既存候補は別裁定として扱える。