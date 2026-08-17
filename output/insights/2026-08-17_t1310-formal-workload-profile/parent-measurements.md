# 親の実測 — [T-1310] 正式 workload profile

測定環境: worktree `t1310-formal-workload-profile` (branch `worktree-t1310-formal-workload-profile`)、
起点 main `2a3b5055`、Pegasus login ノード、2026-08-17 22:45〜23:15 JST。
テスト実走は `python3 tools/run_tests.py` の bounded local (受入形ではない)。

## M1 — C01 の現在の判定

`orchestrator/tests/test_s8c_preregistration_predicates.py` を runner 経由で実走: **137 passed / 17.91s**。
この緑は snapshot が `C01 = (UNSATISFIED, "workload-projection-mismatch")` を記録していることを意味する
(`test_s8c_preregistration_predicates.py:151`, `:1869`)。

不成立の原因は `_evaluate_c01` の projection 検査
(`orchestrator/campaign/s8c_preregistration_evidence.py:1423`):

```
if any(not {1_000_000, 48} <= _integers(functions[name]) for name in sinks):
    return ... ReasonCode.WORKLOAD_PROJECTION_MISMATCH
```

`sinks = ("_campaign_for", "_perf_for", "_descriptor_for")`。

## M2 — `_integers` の正確な意味 (C01 の検出力の上限)

`s8c_preregistration_evidence.py:319-326`:

```
def _integers(node): return {c.value for c in ast.walk(node)
    if isinstance(c, ast.Constant) and isinstance(c.value, int) and not isinstance(c.value, bool)}
```

`_functions` (`:290-295`) は module 直下の `FunctionDef` だけを拾う。よって:

- 要求は「3 sink **関数本体の AST 内**に整数 literal `1000000` と `48` が現れること」。
  module 直下の定数や helper 関数へ出すと C01 は満たされない。
- 判定は**上位集合**であり、同じ関数に探索 scale (`100000` / `4`) が同居していてもよい。
- **C01 は literal の存在しか見ない。**その literal が実際に射影へ使われることは検査しない。
  したがって C01 を満たすことは正式 scale が本当に 3 sink へ流れる証拠にならない。
  この wave のテストは C01 に頼らず実射影を検査しなければならない (恒真回避)。

## M3 — ratified (v2) 経路は未発効

library 経路の probe:

```
orchestrator.campaign.s8b_ratified_freeze.load_ratified_freeze(root)
→ RatifiedFreezeError: [no-active] live active pointer が無い (v2 未発効)
  (s8b_ratified_freeze.py:1274 resolve_active_generation)
```

## M4 — v1 凍結には正式 holdout が実在

`output/s8b-freeze/holdout_freeze.json` (schema `8b-holdout-freeze/v1`、27942 bytes):

- `holdouts.rr80`: candidate_id = `H1`、skew = `0.9`、read 比率 = `80`、rmw = `0`、records = 1000000、threads = 48
- `holdouts.rr20`: candidate_id = `H2`、read 比率 = `20`、他は同じ

**この文書は三軸の鍵語を同居させている。** 値を JSON 正規形 (`"key": "value"`) で書くと
この文書自身が conjunction hit になる。以降の追記も並記で書く (D88 の defang 規律)。
- v1 loader = `orchestrator/campaign/s8b_freeze_io.py:41` `load_verified_freeze(path, expected_hash=None)`

## M5 — rr80 / rr20 は既に登録済みの workload 名である

`orchestrator/campaign/trial_registry.py:51-57`:

```
HOLDOUT_BINDINGS = {"H1": {"workload": "rr80", "ycsb_rratio": "80"},
                    "H2": {"workload": "rr20", "ycsb_rratio": "20"}}
HOLDOUT_WORKLOADS = frozenset(binding["workload"] for binding in HOLDOUT_BINDINGS.values())
```

producer の CLI は既にこの名前を受理する (`p3_autonomous_workload_trial.py:3302-3306` の
`_parse_workloads` が `set(WORKLOADS) | set(trial_registry.HOLDOUT_WORKLOADS)` を許す)。
一方 `WORKLOADS` (`:188-192`) に rr80 / rr20 の flags は無い。**CLI は受理するが producer は値を持たない**
という非対称が現状である。

## M6 — 登録簿は holdout の探索扱いを既に拒否している

`trial_registry.py:1268-1273`:

```
holdouts = sorted(set(selected) & HOLDOUT_WORKLOADS)
if holdouts: _fail("u4-holdout-workload", "holdout workloads cannot use exploratory admission: ...")
```

`:1407-1410` も `explicit-unregistered-exploratory` の admission に holdout workload が混ざることを拒否する。
producer 側は登録済み経路 (`trial_registry.admit_registered_launch`、`registered-effective`) を
既に呼んでいる (`p3_autonomous_workload_trial.py:731-800`)。

## M7 — `pilot_scope` / `scientific_claim` は 2 層で exact 照合されている

- `orchestrator/campaign/s8c_generation_projection.py:636-639` の `fixed` に
  `"pilot_scope": PILOT_SCOPE` (= `"exploratory-ycsb-abc"`, `:20`) と `"scientific_claim": False` があり、
  `_assert_expected_tree` で payload と exact 照合される。
- `orchestrator/campaign/autonomous_trial_completeness.py:544-552` の `expected_fixed` も同じ 2 field を
  exact 照合する (`_PILOT_SCOPE` = `:241`)。
- producer 側の literal は `p3_autonomous_workload_trial.py:654`, `:1595`。

→ 正式 profile をこの 2 field のまま走らせると、成果物が正式走行を
「探索 pilot・科学的主張なし」と記述する。M6 の拒否規則と論理的に矛盾する。

## M7b — 札の全出現と cross-binding の不在 (段 4 の scope 判定に直結)

`scientific_claim: False` の production 側出現は 5 箇所:

- `p3_autonomous_workload_trial.py:1596` (`_common_payload` = 全 role payload)、`:2312`、`:3088`
- `s8c_generation_projection.py:639`、`autonomous_trial_completeness.py:547`

`_common_payload` (`:1589-1605`) は role payload へ `pilot_scope="exploratory-ycsb-abc"` と
`scientific_claim=False` を無条件で焼き込む。`_campaign_for` の spec_content (`:658-663`) も
「T-178 exploratory ... no formal descriptor claim」と明記している。

**cross-binding は無い。** `autonomous_trial_completeness.py` は role payload の fixed literals を
自前の `_PILOT_SCOPE` と照合するだけで (`:544-552`)、campaign の `search_config["pilot_scope"]` とは
突き合わせない (同 file の `pilot_scope` 出現は `:116`, `:546` の 2 箇所のみ)。

→ 「campaign 側だけ正式札にし role payload は探索札のまま」という中間形は、どの検査にも
捕まらないまま成果物の内部が矛盾する。**この中間形を採ってはならない。**採れるのは次の 2 つだけ。

- **(A)** producer の 3 箇所 + verifier 2 層すべてを profile 由来にする。exact 照合契約が変わるため
  受理集合の変更を伴い、台帳項の scope を超える。
- **(B)** 札は一切触らず、規模と flags の束縛だけを実装する。正式 profile の走行は当面
  「探索・科学的主張なし」と自己記述したままになる。

## M8 — repo scan invariant を壊さない条件 (実測による特定)

三軸 conjunction は**同一 file 内**での `ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw` の同時一致で 1 hit
(`s8b_holdout_freeze.py:501-530`、除外は `output/s8b-freeze/` のみ)。file 内の出現数:

| file | rratio | zipf_skew | rmw | 判定 |
|---|---|---|---|---|
| `orchestrator/campaign/trial_registry.py` | 有 (`"80"` / `"20"`) | 0 | 0 | hit にならない (前例) |
| `orchestrator/campaign/p3_autonomous_workload_trial.py` | 3 (50/95/100) | 3 | 3 | **rratio に `"80"` / `"20"` を書き足せば hit になる** |

→ producer に holdout の read 比率を literal で書いてはならない。import か実行時読取で入れる。
新設するテスト file も同じ制約を受ける。

## M8b — 反実仮想による実証 (推論ではない)

`s8b_holdout_freeze.holdout_conjunction_hits(texts)` (`:630`) に実 file 本文を渡して測った。

| 入力 | rr80 | rr20 |
|---|---|---|
| 現状の `p3_autonomous_workload_trial.py` + `trial_registry.py` | `[]` | `[]` |
| producer に rr80 の read 比率を JSON 正規形で 1 行足した反実仮想 | `['orchestrator/campaign/p3_autonomous_workload_trial.py']` | `[]` |

→ M8 の判定は実測で確認された。producer への正式比率 literal は 1 行で invariant を破る。

## M10 — repo scan invariant テストは恒久保留で AI は実行できない

`orchestrator/tests/test_s8b_repo_scan_invariant.py` の契約は
`KNOWN_CONJUNCTION_HITS = {"rr80": [], "rr20": []}` (0 件) である (`:21-24`)。

- pytest 経由: **skip** (`enforce_held_functions(..., plain_runner="manual")`、`:54-55`)。
  runner 実走で `1 skipped in 2.12s`。
- plain runner 経由: 拒否される。
  `GrowthTestHoldBypassRefused ... {"release_env":"IZANAGI_RUN_GROWTH_HELD_TESTS","release_token":"explicit-user-command"}`
  → 解除はユーザーの明示命令のみ。**親は全 repo scan を実走できない。**

したがって台帳項が言う「repo scan invariant の既知 hit 0 件契約への波及」は、
(a) 正式比率 literal を入れないことで契約値を 0 のまま保ち、
(b) 変更した file 本文に対する `holdout_conjunction_hits` (M8b の経路、成長比例コストなし) で証明し、
(c) 全 repo の held テストは依然ユーザー解除待ちであると記録する、
の 3 点で閉じる。**held テストが緑になったとは書かない。**

## M9 — descriptor sink は正式規模を受理する

`orchestrator/campaign/s8b_descriptor.py:85-130` の `project_from_search_config` は
records / threads を正の int として受理し上限を持たない。skew は宣言済みラベル (`"0.9"` を含む) のみ、
rratio / rmw は canonical 整数文字列のみ。よって 1,000,000 / 48 と rratio `"80"` / `"20"` は素直に通る。
