si の裸マクロ 2 件を条件 gate に登録し、指定された 6 ファイルの固定表を更新しました。commit は作っていません。

| ファイル | 変更 |
|---|---|
| [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/campaign/condition_meaning_gate.py:79) | si の owner、2 件の `DefineSpec`、witness、site 数を追加。供給ドメインを 59→61、compile-time witness を 41→43 に更新。 |
| [screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/campaign/screening_driver.py:88) | 両マクロの既定値を `0` に登録。 |
| [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/tests/test_condition_meaning_gate.py:169) | patch・fixture・登録簿の期待値と総数を更新。 |
| [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/tests/test_p3_s4_loop.py:8481) | patch 別の裸マクロ許容表に追加。 |
| [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/tests/test_ccbench_spawn_sites.py:3571) | 在庫総数 59→61 に追随。追加 2 件が S1・certify sink では到達不能、s8b sink では covered となる分類に基づき、固定件数も更新。 |
| [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/tests/test_screening_driver.py:671) | 両マクロの既定値 `0` を固定。 |

patch 本文の追加 `#if` 行を数え、V29 は **7**、V28 は **5** で U-A 報告と一致しました。`git diff --check` は通過しました。

**検査:** 次の node 相当を test 関数の直接呼び出しで確認し、すべて PASS でした。`test_condition_meaning_gate.py` の登録簿・fixture、domain、docstring、`test_ccbench_spawn_sites.py` の patch 在庫、`test_p3_s4_loop.py` の裸マクロ許容表、`test_screening_driver.py` の request 表です。pytest の nodeid 実走ではありません。全 sink 分類の直接呼び出しは短時間枠を超えたため中断しました。compiler を使う分岐選択テストと各ファイル全体も**実装済み・未実走**です。

M1・M3 は `test_v1_domain_and_claim_boundaries_are_exact`、M2・M4 は `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` が赤になる見込みです。各誤りをメモリ上で模擬し、実際に赤化を確認しました。

**重ね当てと経路:** テスト fixture は pin C に壊し patch を単独適用せず、[fixture 構築箇所](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/tests/test_condition_meaning_gate.py:378)で追加 `#if` 行から一時 TU を作ります。実ソースを照合する gate は[宣言 site 数を厳密に数える](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/campaign/condition_meaning_gate.py:3209)ため、pin C や v2 だけでは通らず、**pin C → v2 → 対応する壊し patch** が必要です。U-A はこの順の適用を確認済みです。

既定引数の `make_define_request` は両 si マクロを `cc/si/transaction.cc`・`ycsb_si.exe` として生成・検証でき、target 照合にも `CMakeFiles/ycsb_si.exe.dir/` が含まれます。一方、明示的な `protocol="si"` は[現行の factory](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847si-uc/orchestrator/campaign/condition_meaning_gate.py:1121)で拒否されます。Genome の `CCBENCH_` 引数は CXX_FLAGS route を満たさず、両マクロとも `screening-build-route-mismatch` を直接確認しました。受理述語と供給経路は変更していません。

## 総括

登録と固定表の更新、軽量な直接検査、M1〜M4 の赤化確認は完了しました。全 sink 分類と compiler を使う焦点テストは親の計算ノード実走が必要です。