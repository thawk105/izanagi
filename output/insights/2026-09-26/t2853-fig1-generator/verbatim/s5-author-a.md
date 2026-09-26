## 変更

- [plot_p2_5_search_cost.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py): 317 行、上限 450 行以内。履歴 WAL からの再計算、凍結 summary との照合、3 panel の描画、レイアウト検査、provenance と closure を実装。
- [test_plot_p2_5_search_cost.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py): 124 行、上限 300 行以内。T1〜T6 を実装。

所有外のファイルは変更していません。図の着地と commit は親の担当です。

## 裁定との対応

| plan v2 の項目 | 実装箇所 |
|---|---|
| CLI、PNG・PDF・provenance | 生成器 [282 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:282) |
| HISTORICAL_RAW、WAL 全 frame 検査 | 生成器 [114 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:114) |
| committed landscape、8 構成・記録上 certified の検査 | 生成器 [53 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:53) |
| 既存関数による greedy 500 seed、random、oracle、A、p の再計算 | 生成器 [127 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:127) |
| 描く値と summary の照合、出力前の失敗 | 生成器 [88 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:88) |
| 旧図の視覚符号、artist からの値の読み戻し | 生成器 [218 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:218) |
| 保存前のレイアウト検査 | 生成器 [192 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:192) |
| E0 の provenance、測定条件、SHA256 | 生成器 [149 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:149)、[297 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:297) |
| closure と日本語 caption | 生成器 [268 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:268)、[174 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:174) |
| T1・T2・T3・T4・T5・T6 | test [14 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:14)、[28 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:28)、[61 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:61)、[69 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:69)、[91 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:91)、[105 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:105) |

裁定と違えた箇所: なし。

## 変異の位置

以下のアンカーはそれぞれ指定ファイル内で **1 回**だけ現れることを確認しました。M1〜M10 のアンカーは生成器、C0 は test ファイルです。

| ID | 置換アンカー → 置換後 | 赤になる test・assert |
|---|---|---|
| M1 | `for group in ('greedy', 'guided'):` → `for group in ('guided',):` | T2 `greedy`、`pytest.raises` |
| M2 | `if round(calc['A'], 4) != frozen:` → `if False:` | T2 `A`、`pytest.raises` |
| M3 | `if not math.isclose(calc['p'], frozen, rel_tol=1e-12):` → `if False:` | T2 `p`、`pytest.raises` |
| M4 | `if not all(x.certified for x in land.values()):` → `if False:` | T3 certified 負例、`pytest.raises` |
| M5 | `if set(land) != {g.canonical() for g in SILO_SPACE.enumerate()}:` → `if False:` | T3 7 構成負例、`pytest.raises` |
| M6 | `sb.greedy_reach(land, tied, 500, 0)` → `sb.greedy_reach(land, tied, 500, 1)` | T1 write-heavy 度数 assert |
| M7 | `purpose=CampaignReadPurpose.HISTORICAL_RAW` → `purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE` | T1 の実データ読み込み |
| M8 | `median = ax.hlines(d['guided']['median']` → `median = ax.hlines(d['guided']['mean']` | T4 `median_bar == guided['median']` |
| M9 | `if _sha256(path) != item['sha256']:` → `if False:` | T6 改変 PNG の `pytest.raises` |
| M10 | `    fig.canvas.draw()` → `    return` | T5 重複 text の `pytest.raises` |
| C0 | test 冒頭の `Figure 1b values, reconciliation, layout, and hash closure.` → `Figure 1b regression checks.` | 対照。期待は SURVIVED |

## 実データでの値

3 workload とも指定された summary 値との照合に成功しました。greedy は各 500 seed です。

| workload | k・tied | random_E / oracle_E | greedy 平均・中央値・25/75 分位 | A・p | guided 中央値・未到達 |
|---|---|---|---|---|---|
| read-heavy | 4・`B0-L-W0/W1`, `B0-T-W0/W1` | 1.8 / 1.5 | 1.756・1・1/2 | 対象外 | 1・0/6 |
| balanced | 1・`B0-L-W0` | 4.5 / 1.875 | 4.234・5・2/6 | 0.58125・対象外 | 4・0/12 |
| write-heavy | 1・`B0-L-W0` | 4.5 / 1.875 | 4.362・5・2/6 | 0.23041666666666666・0.00025210801850960543 | 8・8/12 |

write-heavy の greedy 度数は `{1:62, 2:66, 3:67, 4:35, 5:31, 6:182, 7:57}` でした。

## caption

> 旧 linux-baremetal 環境の Phase 2 探索コスト。P2-2 の silo 8 構成について、LLM-guided は中立 critic の 30 試行（read-heavy 6、balanced 12、write-heavy 12）の凍結値を示す。原試行 WAL は削除済みである。未到達は事前登録どおり予算上限 8 として算入した。greedy は P2-2 WAL の決定論的再生 500 seed、random は解析期待値、oracle は初手ランダム制約下の天井。A = P(誘導<貪欲)+0.5·P(=)、p は厳密 permutation 検定（片側）。P2-2 campaign は verifier epoch E0 の記録をそのまま使用し、現行 verifier では再検証していない。read-heavy は k=4 で到達判定が情報を持たないため、A の注記を付けない。

## 波及

所有外の caller・共有 fixture に変更はありません。[test_pytest_collection_config.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_pytest_collection_config.py:424) は test file を走査しますが、対象名は `verifier` / `oracle` に限られ、この新規 test 名は該当しません。静的調査で、新規 test file の追加だけで赤になる固定一覧テストは見つかりませんでした。

## 実走

`py_compile` は両ファイルで成功。指定の生成器コマンドは rc=0 で PNG・PDF・provenance を生成しました。pytest を起動しない自走では T1、T2 の 4 例、T3、T4、T5、T6 の PNG 改変検査が成功しました。T6 の着地 bundle 検査は、親がまだ bundle を置いていないため skip です。pytest 本走は未実施です。一時ディレクトリ `.scratch-fig1/` は削除済みです。

## 総括

生成器と T1〜T6 を所有 2 ファイルに実装しました。実データの再計算・照合・描画は成功しています。着地 bundle の確認と commit は親の作業です。