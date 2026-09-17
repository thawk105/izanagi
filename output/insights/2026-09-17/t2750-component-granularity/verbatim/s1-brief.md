# 段 1 brief — [T-2273][T-2750] 受入 shard-0 の連結成分粒度 (file → node) を allocate で解く

wave: worktree-dev-wave-t2750-shard0-component-granularity / 基準 main 38353207f / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2750-shard0-component-granularity

## 研究前進 (土台)

受入全走 (毎 wave の land 前に必須、計算ノード 3 本 × 約 6 分) の最遅 shard wall を縮めることは、全 dev-wave の回転率を上げる土台作業。止めている研究は特定の論文主張ではなく wave 全体の throughput。完了判定 = 「最遅 shard wall の同時刻対照分布 (n≥20) に対して改善が示せる」か「算術と実測で利得 0 が示せて T-2750 を閉じる」のどちらか。

## ユーザー依頼 (逐語要約) と確定済み裁定

- 依頼: shard-0 の衝突成分 (campaign-repository-scan / real-repo / s8c-predicate-snapshot / s8c-preregistration-candidate、conftest の REAL_REPO_RESOURCE_NODES が real-repo を動的付与、台帳予測 7502 / 実測 8569 / 均等 6053 秒) を `tools/acceptance_shards.py::allocate` で解く。案 (a) 成分単位を file → node (順序依存の検査が先)、案 (b) 大 file の real-repo node を別 file へ分離。D358 と受理集合は変えない。採用条件 = 検出力維持 と D104 の効果実証 (同時刻対照つき、n=1 の前後比較で主張しない)。実装面は Codex author (D95)、変異事前登録要。規律 2 を緩めない。本題の分割改善だけ、追加 gate・検査・台帳は scope 外。
- 確定済み裁定: D358 (real-repo の排他は単一 worker 直列化のまま)、D1167 (衝突 group は同一 shard へ union、group は分けたまま)、D1618 (real-repo の shard affinity は全 node で保つ = 跨ホスト排他の防壁、規律 2)、D711 gate 4 (file と xdist_group の閉包)、D357 (wall の主張は反復走の中央値、10% 未満は変化なし)、D104 決定 3 (効果を示せない機構は land しない) / 決定 4 (一次証拠は duration でなく paired 比較 + 機構の実発火観測)、D1019 (割付を duration 重みへ変えても makespan = max(最長鎖, 仕事量/48) は動かない、完璧な予言者でも 0.0 秒)、D2067 (shard-0 の床は t080 e2e 群)、D2068 (t080 fixture 高速化 3 案は不採用)、D1714 (最長の単体 test 1 本を犯人と名指ししない)。

## brief 前の前提実測 — 覆す新事実

1. **最忙 worker は最長 node 1 本で決まっている。** 台帳 refresh 後の受入 20 走 (2026-09-17 09:34〜12:26、他 wave の受入 = 同時刻対照、`/work/1/SFC/tanab/.izanagi-acceptance-shards/*/shard-0/{report.json,junit.xml}`) で、shard-0 の最忙 worker は毎走 item 2 個 (`test_s8b_oracle_driver.py::…_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` 225.1〜499.7 秒、中央値 264.8 + 相方 約 20 秒)。最大占有 − 最長 node = 19.9 秒 (20 走中 17 走、min 7.5 / max 20.1)。wall − 最大占有 = 66.1 秒 (中央値、min 65.0 / max 88.2)。shard-0 wall 中央値 347.7 (min 310.8 / max 585.8)。
2. **平均 worker 負荷は最長 node より常に小さい。** shard-0 の直列和 ÷ 48 = 161〜221 秒 < 最長 node 225〜500 秒。shard-1/2 も同型 (最大占有 = 最長 node + 14〜24 秒)。48 worker では shard の wall は「最長 node + 固定費」で決まり、負荷の総和では決まらない。
3. **案 (a) の offline 割付 simulation (生死実験、DW-G01)**: collect-only 24660 node (login、`test_t316_sandbox_probe.py` は login の condition gate で collection error → 166 node 欠け) + 現行台帳で、現行 allocate = 7523 / 5372 / 5372 秒、案 (a) hybrid (group 付き node だけ group 成分、同 file の他 node は file 成分) = 6089 × 3 秒、案 (a) node 粒度 = 6089 × 3 秒。**D1019 の makespan 式 max(最長 node, 負荷/48) + 66.1 では、最遅 shard の予測は 3 通りとも 306.1 秒で不変** (最長 node 240.0 秒を持つ shard が最遅のまま)。衝突成分は 3929 node / 7523 秒 → 188 node / 1612 秒に縮む (均等化そのものは成立する)。
4. 一次資料 (T-2236 README) の「LPT はどう並べても shard-0 を軽くできない」は**負荷 (直列和) の命題としては真**、「これが shard-0 の床」は **wall の命題としては偽**。D2067 (床 = t080 e2e 群) が現行。

## (P) 親の provisional 裁定 — 攻撃対象

- (P1) 案 (a)/(b) とも最遅 shard wall の期待利得は 0 秒 (上記 1〜3)。D104 決定 3・D1019 により**実装しない**。docs-only で T-2750 を「wall を動かさない」と閉じ、T-2273 の次の律速を「最長 node (t080 e2e b5 群 5 本、233〜252 秒) の所要」と記録する。
- (P2) 相方 約 20 秒は xdist の初期 chunk 最小 2 item に由来する構造的な tail で、割付では消えない (未実測: 相方の identity は本 wave で 1 走の junit から同定する)。
- (P3) 「負荷が軽い shard では最長 node 自身が競合減で速くなる」効果は本 data では分離できない (外乱が両方を同時に膨らませる、相関は confound)。paired 実測 (同一 tip で旧/新割付を交互 n≥3) は実装後にしか測れず、期待値が 0 の機構へ払う費用 (Codex author + 変異 + 受入 6 走 ≈ 3〜4 時間の計算ノード) は研究最優先の観点で正当化できない。
- (P4) 案 (a) を実装するなら D711 gate 4 の file 閉包を変える (裁定改訂) ことになり、同 file の group 無し node が別 host へ行くとき module fixture 経由で実 repo に触る node (D358 が「正本リストの外に実在」と記録) の跨ホスト排他が失われうる。検出力維持の証明には REAL_REPO_RESOURCE_NODES の閉包が完全であることの実測が要る。これは (P1) が覆った場合の必須前提。

## scope / 不変条件 / 成果物

- scope: 本題 = 成分粒度の改善の採否。採用条件 (検出力維持 + D104 効果実証) を満たす見込みが実測で 0 なら docs-only で閉じる。追加 gate・検査・台帳は scope 外。
- 不変条件: 規律 2 (real-repo の跨ホスト排他 = D1618 の affinity、D358 の直列化) を緩めない。受理集合不変。凍結 bytes に触れない (pin 閉包: `tools/acceptance_shards.py` の source hash pin は git grep 0 件、参照 test は test_run_tests_shards.py / test_real_repo_serialization.py / test_acceptance_schedule_order.py、docs-only なら無関係)。
- 成果物 (docs-only 時): `output/insights/2026-09-17/t2750-component-granularity/README.md` (20 走の表、simulation、逐語)、spool fragment worklog (T-2750 完了 base 6fc28289…、T-2273 更新 base 937e28ec…) + decisions ({{D:shard0-component-granularity-no-wall-gain}})。受入全走は docs-only でも免除しない (DW-S04)。
- 変更面 (実装する場合の実アンカー): `tools/acceptance_shards.py:325-362 _components`, `:381-461 allocate`, `:464-494 assignment_closure_gate` (file 閉包 `file_shards`), `orchestrator/tests/conftest.py:662 REAL_REPO_RESOURCE_NODES`, `:2139-2206 _validate_real_repo_shard_state`, `orchestrator/tests/test_run_tests_shards.py:729-908`, `orchestrator/tests/test_real_repo_serialization.py:1735-1819`, `orchestrator/tests/README.md:272`。
- 分割方針: 段 2 plan 1 本 (案 (a) の file:line plan + 順序依存・閉包の検査設計 + D104 paired 測定設計)、段 3 レンズ A (正しさ境界: (P4) の跨ホスト排他と閉包、D711/D1618 との整合)、レンズ B (実効性: (P1)〜(P3) の実測と一般化を攻撃、「実装すべき」の最強の形)。段 4 で裁定。
- 実測環境: 受入 = Pegasus 計算ノード (`dev_wave_wait.py acceptance`)、対照 = 同時刻の他 wave の受入 session (repo 外 `.izanagi-acceptance-shards`)。
