# 親が実走した結果と実測 — [T-2001]

**これが唯一の実走記録である。** 段 5 の実装子はいずれも sandbox から計算ノードへ
dispatch できず (`qstat -Q preflight rc=1` → `rc=16`)、実走 nodeid は 0 件だった。
**子の報告にある「検査した」は静的検査であり、緑ではない。**

## 親が実走したテスト (worktree = `.claude/worktrees/dev-wave-t2001-b4-analysis-path`)

| 対象 | 結果 | 所要 |
|---|---|---|
| `orchestrator/tests/test_p3_b4_analysis_contract.py` | **38 passed** | 3.74s |
| `orchestrator/tests/test_p3_b4_analysis_adapter.py` | **27 passed** | 4.54s |
| `orchestrator/tests/test_p3_b4_analysis_ledgers.py` | **13 passed** | 4.08s |
| `orchestrator/tests/test_plain_runner_coverage.py` + `test_pytest_collection_config.py` | **79 passed** | 84.35s |
| `orchestrator/tests/test_campaign_import_invariant.py` | **24 passed / 6 skipped** | 3.71s |

いずれも `python3 tools/run_tests.py <file> -q -rf` を repo root から実行し、
計算ノードへ dispatch された走行である。受入全走ではない。

## 実測 1 — 一覧検査の中核 6 件は通常走では skip される

`test_campaign_import_invariant.py` の real-repo 走査 6 node は
`IZANAGI_GROWTH_HOLD_V1` の下にある。

- `hold_axis = tracked_files`
- `release_condition = explicit-user-command-only`
- 出典: 2026-08-12 rulings 第 3 束
- 解除には exact token の環境変数**かつ** collection が suite root 全体であることが要る
  (`orchestrator/tests/conftest.py:1342` `_growth_holds_opted_in`、
  `同:1451` `_is_complete_growth_hold_collection`)

**したがってこの gate は受入全走でしか発火しない。** 迂回しない。

該当 node:
- `test_repository_scan_set_is_nonempty_and_contains_sentinels`
- `test_real_repository_legacy_namespace_matches_exception_ledger`
- `test_real_campaign_package_has_canonical_direct_bootstrap`
- `test_real_campaign_package_uses_relative_sibling_imports`
- `test_real_current_docs_have_no_legacy_module_command`
- `test_known_exception_ledger_is_unique_rationalized_and_commented`

## 実測 2 — 新 module の import 形 (親の静的確認)

- `p3_b4_analysis_contract.py`: stdlib のみ
  (`dataclasses` / `enum` / `fractions` / `math.comb` / `typing`)。
- `p3_b4_analysis_adapter.py`: stdlib + `from .p3_b4_analysis_contract import ...` の相対兄弟。
- どちらも `sys.path` 変異なし、`__main__` なし、`campaign.*` legacy 名なし。

## 実測 3 — 浮動小数点の tie 境界 (段 3 の所見を親が再現)

```
on=1.1, off=1.0, ref=1.0, floor=0.1
float 経路          -> tie でない (差 0.10000000000000009 > 0.1)
as_integer_ratio 経路 -> tie でない (超過 3/36028797018963968)
10 進 exact 経路      -> tie
```

`json.loads(data, parse_float=Fraction)` は十進 lexical から `Fraction(11, 10)` を作る。

## 実測 4 — 受入の 90% coverage 閾値の余裕

`orchestrator/tests/acceptance_duration_ledger.json` の `nodeid_count = 17630`。
90% を保てる collection 上限は 19588 なので **slack は 1958 node**。
本 wave が足す新 node は数十件で、閾値には掛からない。

## 実測 5 — main の進行

wave の base は `343b8f5a5`。段 3 時点で main は `aa8a7cd6a` (14 commit 先行) だったが、
変更面は `tools/codex_reasoning_ab.py` / `orchestrator/tests/test_codex_reasoning_ab.py` /
insights / docs のみで、**一覧検査と campaign module は 1 件も変わっていない**。

## 実測 6 — codex 子はテストを実走できない

`--sandbox workspace-write` の子が `tools/run_tests.py` を叩くと、
`qstat -Q preflight rc=1` により dispatch child が起動せず `rc=16` になる。
段 5 の全実装子 (A / B / C) で再現した。

## 段 5 完了時点の実走 (12:5x JST、fix2 適用後)

```
python3 tools/run_tests.py \
  orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py \
  orchestrator/tests/test_p3_b4_analysis_path.py \
  orchestrator/tests/test_p3_b4_analysis_contract.py \
  orchestrator/tests/test_p3_b4_analysis_adapter.py \
  orchestrator/tests/test_p3_b4_analysis_ledgers.py -q -rf
-> 121 passed in 4.87s
```

内訳 (個別走行の実測): contract 38 / adapter 27 / ledgers 13 / path 12 / prereg_consumer 31。

## 実測 7 — 単位 D が露出させた統合欠陥 (fix2 で解消済み)

単位 D の初回実走は **9 failed / 3 passed** だった。親が repo 外 probe で切り分けた真因:

- 単位 C の `build_contract_binding()` は `reference_tps` を `(100, 1)` (整数比 tuple) で作る
- 単位 A の `_as_exact_fraction((100, 1))` → `Fraction(100)` (受理)
- 単位 B の `_exact_fraction((100, 1))` → `binding_domain_error` (拒否)
- **同じ値域を 3 module が別々に実装していて食い違っていた**

fix2 で単位 A が `as_b4_exact_fraction()` / `b4_binding_domain_is_valid()` を公開正本にし、
B と D が委譲する形へ統一した。**単位 A の受理集合は 1 bit も変えていない。**

併せて `p3_b4_analysis_path.py` の一括 `except Exception` を段別境界へ分割した。
**期待値の変更は 1 件だけ** —
`test_loader_failure_is_returned_as_analysis_invalid_not_raised` の理由 enum を
`BINDING_DOMAIN_ERROR` → `FIELD_MISSING_OR_ILL_TYPED` (凍結文面の受け皿の定義に従う)。
他の assertion は完全一致比較のまま維持されている (親が現物で確認)。
