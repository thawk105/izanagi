## 対応表

| 裁定 1 の採用行 | 状態 | 実装箇所 |
|---|---|---|
| A-M1 | closed | [生成器:240](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:240)、[test:36](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:36) |
| A-M2 / B-M1 | closed | [生成器:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:54)、[test:41](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:41) |
| A-M3 | closed | [生成器:334](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:334)、[test:152](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:152) |
| A-S1 | closed | [生成器:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:216) |
| B-S1 | closed | [生成器:134](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:134) |
| P-M1 | closed | [test:171](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:171) |
| P-S1〜P-N1 | closed | [生成器:280](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:280) |

## 変更

[生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py) は **383/450 行**、[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py) は **206/300 行**。編集した追跡下ファイルはこの二つだけです。

## 変異の位置

以下のアンカーはすべて現在の生成器内で **各 1 回**と確認しました。赤は置換した場合の予想で、変異自体は実走していません。

| ID | 置換アンカー → 置換後 | 赤になるはずの test |
|---|---|---|
| M1 | `('greedy', GREEDY_KEYS)` → `('greedy', ())` | `test_reconciliation[greedy]` |
| M2 | `if round(calc['A'], 4) != frozen:` → `if False:` | `test_reconciliation[A]` |
| M3 | `if not math.isclose(calc['p'], frozen, rel_tol=1e-12):` → `if False:` | `test_reconciliation[p]` |
| M4 | `if not all(x.certified for x in land.values()):` → `if False:` | `test_landscape` |
| M5 | `if set(land) != {g.canonical() for g in SILO_SPACE.enumerate()}:` → `if False:` | `test_landscape` |
| M6 | `sb.greedy_reach(land, tied, 500, 0)` → `sb.greedy_reach(land, tied, 500, 1)` | `test_real_data` 等。**単一理由ではない**。度数 assert より先に照合の `FigureDataError` で落ちる想定 |
| M7 | `purpose=CampaignReadPurpose.HISTORICAL_RAW` → `purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE` | 実データを読む複数 test。**単一 test への帰属ではない** |
| M8 | `ax.hlines(d['guided']['median']` → `ax.hlines(d['guided']['mean']` | `test_end_to_end` |
| M9 | `refs.extend(provenance['outputs'].values())` → `pass` | `test_closure` |
| M10 | `def check_figure_layout(fig, axes):` の直後 → `return` を挿入 | `test_layout` |
| M11 | `format_p(d['p'])` → `format_p(d['A'])` | `test_end_to_end` |
| M12 | `refs = [provenance['summary']]` → `refs = [provenance['generator'], provenance['summary']]` | `test_closure_generator_history` |
| M13 | `測定条件は {c['threads']} スレッド、` → `測定条件は ` | `test_end_to_end` |
| C0 | `Recreate Phase 2 search cost from frozen guided trials and historical P2-2 records.` → `Recreate Phase 2 search cost figure.` | **SURVIVED** 想定。docstring だけの対照 |

## 実データでの値と条件

3 campaign とも `linux-baremetal`、48 スレッド、1,000,000 レコード、3 秒、`clocks_per_us=1800`、Zipf skew 0.9、`rmw=0`、`numactl --interleave=all`、`perf stat`、各構成 5 反復、ccbench commit `6656e93`。read 比だけが read-heavy **95%**、balanced **50%**、write-heavy **5%** と異なりました。

生成された caption の全文：

> 旧 linux-baremetal 環境の Phase 2 探索コスト。P2-2 の silo 8 構成。測定条件は 48 スレッド、1000000 レコード、3 秒、clocks_per_us=1800、Zipf skew=0.9、read-heavy: read 比 95%、balanced: read 比 50%、write-heavy: read 比 5%、rmw=0、numactl --interleave=all、perf stat、各構成 5 反復、ccbench commit 6656e93。LLM-guided は中立 critic の 30 試行（read-heavy 6、balanced 12、write-heavy 12）の凍結値を示す。原試行 WAL は削除済みである。未到達（read-heavy 0/6、balanced 0/12、write-heavy 8/12）は事前登録どおり予算上限 8 として算入した。点は誘導の各試行。横棒は誘導の中央値。四角は貪欲の平均。ひげは貪欲の 25/75 分位（search_baselines._summ の順位 n//4・3n//4 の標本値）。点線は random の解析期待値。破線は初手ランダム制約下の oracle 天井。greedy は P2-2 WAL の決定論的再生 500 seed。A = P(誘導<貪欲)+0.5·P(=)、p は厳密 permutation 検定（片側）。P2-2 campaign は verifier epoch E0 の記録をそのまま使用し、現行 verifier では再検証していない。read-heavy は k=4 で到達判定が情報を持たないため、A の注記を付けない。

## 実走

`py_compile`、指定の生成器実走、指定の自走 harness、`git diff --check` は成功しました。自走 harness は **12 passed、0 failed、1 skipped、0 errors**。skip は親の着地 bundle がまだない `test_landed_bundle` です。全体テストと変異実走は行っていません。`.scratch-fig1/` は削除済みです。

## 総括

裁定 1 の採用実装項目はすべて反映しました。着地 bundle の検査だけは親の配置後に実行されます。