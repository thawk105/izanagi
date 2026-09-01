## 総括

plan v2 項目 1〜4 は実装済み。実測は dispatch infrastructure failure のため未実走・緑未確認です。

## 変更

1. [orchestrator/tests/test_p3_b4_wiring_probe.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/test_p3_b4_wiring_probe.py:288)

変更前:

```python
baseline = _inventory_symbols(P._build_inventory(static, runtime.modules))
target = "orchestrator.campaign.pipeline.evaluate"
assert target in baseline
without_anchor = tuple(seed for seed in P._GENERATION_SEEDS if seed != P._GENERATION_SEEDS[0])
mutated = _inventory_symbols(
    P._build_inventory(static, runtime.modules, seeds=without_anchor)
)
assert target not in mutated
```

変更後:

```python
baseline = _inventory_symbols(P._build_inventory(static, runtime.modules))
anchor = P._GENERATION_SEEDS[0]
assert anchor in baseline
target = "orchestrator.campaign.pipeline.evaluate"
assert target in baseline
without_anchor = tuple(seed for seed in P._GENERATION_SEEDS if seed != anchor)
mutated = _inventory_symbols(
    P._build_inventory(static, runtime.modules, seeds=without_anchor)
)
assert anchor not in mutated
assert target not in mutated
```

2. [orchestrator/tests/test_p3_b4_wiring_probe.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/test_p3_b4_wiring_probe.py:152)

変更前:

```python
def test_static_preflight_covers_exact_runtime_import_closure(static_runtime):
```

変更後:

```python
def test_static_preflight_mapping_matches_runtime_import_targets(static_runtime):
    """_load_runtime imports each preflight mapping name into runtime.modules."""
```

assert 本体は一切変更していません。

3. [orchestrator/campaign/p3_b4_wiring_probe.py:2111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/campaign/p3_b4_wiring_probe.py:2111)

変更前:

```python
"generation_scope": (
    "within the exact analyzed module set, functions reaching at least "
    "one named seed are included by reverse closure"
),
"generation_scope_exclusion": (
    "modules outside the exact analyzed set and producers reaching none "
    "of the three seeds are not covered by this layer"
),
```

変更後:

```python
"generation_scope": (
    "within the exact analyzed module set, reverse closure over "
    "statically resolved call edges includes functions reaching at "
    "least one named seed"
),
"generation_scope_exclusion": (
    "modules outside the exact analyzed set and producers reaching none "
    "of the three seeds, plus callers inside the analyzed set whose "
    "call binding cannot be statically resolved, are not covered by "
    "this layer"
),
```

4. [orchestrator/campaign/p3_b4_wiring_probe.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/campaign/p3_b4_wiring_probe.py:4)

変更前:

```text
Generation interdiction is
the reverse closure of three named seeds within the exact analyzed-module
manifest recorded in evidence; modules outside that manifest and producers
that reach none of those seeds are not covered by that layer.
```

変更後:

```text
Generation interdiction is
the reverse closure over statically resolved call edges from three named seeds
within the exact analyzed-module manifest recorded in evidence.  Modules
outside that manifest, producers that reach none of those seeds, and callers
within the manifest whose call binding cannot be statically resolved are not
covered by that layer.
```

## 不変条件の確認

- `_reason_paths`、`_build_inventory`、`_ProcessGuard` は変更せず、遮断挙動・受理集合を維持しました。
- 静的に解決不能な caller を明示的な除外とし、閉包の完全性は主張していません。
- gate・検査・台帳・helper・一般化・新規 test 関数は追加していません。
- 既存 assert は削除・緩和せず、skip・xfail も追加していません。
- `docs/phase3-b4-reflux-ablation-preregistration.md` は変更していません。
- `docs/`、`docs/spool/` は変更していません。
- runner が生成した dispatch receipt は削除済みで、最終 status に `output/` 差分はありません。証拠 JSON は再生成していません。
- `CLAUDE.md`、`AGENTS.md`、`hooks/`、`tools/` は変更していません。
- commit、add、stash、checkout、merge、rebase、push、remote 操作は実行していません。
- 最終 `git status --short` は指定された 2 file の変更だけです。`git diff --check` も通過しました。

## 実測

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_wiring_probe.py -q
```

未実走です。Pegasus の `qstat -Q` preflight が rc=1 となり、runner は rc=16、`child_started=false` で終了しました。テスト件数は 0 件、runner 呼び出し所要は約 0.23 秒です。1 回だけという指定に従い再実行していません。

## 残した懸念

焦点走の緑が未確認です。コード由来の赤ではなく、dispatch infrastructure failure が原因です。