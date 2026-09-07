# 親の実測 (段 1 brief の後に取得。brief の数字を上書きする)

一次資料: `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/*/{junit.xml,report.json}`、直近 3 日。
計測機: login node (96 core) と Pegasus 計算ノード (dispatch 経由)。

## 1. wall の分解 (shard 別、約 77 走の中央値)

| shard | wall | 最も忙しい worker の実行時間合計 | 残差 (テスト以外) | W (全 test 所要和) | 最長排他鎖 C | W/48 |
|---|---|---|---|---|---|---|
| shard-0 | 306.6 | 191.6 | 102.0 | 7963 | 78.5 | 165.9 |
| shard-1 | 215.2 | 156.6 | 59.0 | 5757 | 16.7 | 119.9 |
| shard-2 | 220.6 | 161.6 | 58.6 | 4957 | 161.6 | 101.4 |

- 出所: `report.json` の `worker_occupancy[gwN].duration_s` と junit の `testsuite@time`。
- 全体 wall (3 shard の最大) 中央値 324.3 秒、p25 274.3、p75 378.0、p90 433.1、最大 663.4。
  300 秒超過 45/75 走。
- shard-0 が 70/75 走で最遅。2 位との差の中央値 61.7 秒。
- **wall = 最も忙しい worker の実行時間 + 残差** で説明できる。

## 2. collection の実測

| 条件 | 所要 |
|---|---|
| 単独・全 325 file (21,005 test) — cold | 36.83 秒 |
| 単独・全 325 file — warm (`__pycache__` 温) | 10.23 秒 |
| 単独・shard-0 の 113 file (7,012 test) | 8.06 秒 |
| 単独・shard-1 の 106 file (6,979 test) | 9.90 秒 |
| 単独・test file 1 本 (24 test) | 0.37 秒 |
| **48 プロセス同時・全 file** | **87.57 秒** |
| **48 プロセス同時・shard-0 scope** | **27.44 秒** |

- 48 並列にすると単独比 8.6 倍に劣化する。自 shard へ絞ると 3.2 倍速い。
- 受入は shard ごとに controller 1 + worker 48 が**同時に**全 collection を行う。

## 3. t080 fixture の内訳 (専有計算ノード、`-n 0`、同一 base key の 4 param 直列)

| 順 | nodeid の param | call 所要 |
|---|---|---|
| 1 | `known-artifact-known_axes.artifact_bytes` | **73.64 秒** |
| 2 | `ccbench-current-known_axes.ccbench_current` | 14.98 秒 |
| 3 | `holdout-artifact-holdout.artifact_bytes` | 3.70 秒 |
| 4 | `unknownness-layer2-holdout.unknownness_layer2` | 3.67 秒 |

- **base 構築が約 70 秒、テスト本体は約 4 秒。**
- process 内 cache は `_T080_E2E_BASE_CACHE` (`test_s8b_oracle_driver.py:898` 付近)。
- 受入では 48 worker に散るため base が worker ごとに再構築される。
  受入での同 param 群の中央値は 146〜158 秒 (競合込み)。
- **T-1933 の負結果の説明**: 「同一 worker へ寄せる」と 1 worker が 70 + 3x4 = 82 秒を直列に
  背負うだけで、最も忙しい worker は改善しない。必要なのは **worker を跨いだ共有**である。

## 4. 反実仮想 (D1019 と同じ方法論、75 走、各走自身の実測 duration)

- makespan 模型 `max(最長排他鎖, W/48)` を shard ごとに取り最大値。
- count 割付 180.1 秒 → duration 割付 161.6 秒。利得 中央値 11.6 秒 / 平均 23.5 秒 / 最大 167.8 秒。
- 75 走中 50 走で 1 秒超の利得。
- **D1020 の再検討引き金 `C < W/48` は shard-0 (78.5 < 165.9) と shard-1 (16.7 < 119.9) で成立。**
  8 月は全 shard で不成立だった。
- 模型は絶対値を 140 秒過小評価する (模型 184.6 対 実測 324.3)。D531 の警告どおり、
  絶対値には使わず相対比較にだけ使う。

## 5. 冗長テスト走査 (14,179 test function、AST body 一致)

- 完全一致 body の対は 11 組。10 組は所要 0.01 秒未満で wall に効かない。
- 意味があるのは 1 組だけ:
  `test_t080_output_snapshot_observes_git_visible_create_and_delete` が
  `orchestrator/tests/test_real_repo_serialization.py:804` (中央値 20.94 秒) と
  `orchestrator/tests/test_s8b_oracle_driver.py:642` (中央値 15.79 秒) に**同一 body で重複**。
- 定数のみ相違の群 (18 / 17 / 11 件) は別々の負例であり、削除は被覆を減らす。
- **結論: 削除で回収できるのは実質 15.8 秒 1 件。「不要テストの削除」は wall にほぼ効かない。**

## 6. 効果見積り (親の暫定。反証歓迎)

| lever | 内容 | 見積り |
|---|---|---|
| L2 | worker 跨ぎで t080 / floor の base を共有 | shard-0 の最忙 worker 191.6 → 約 120 秒 |
| L1 | worker の collection を自 shard へ絞る | shard あたり 40〜60 秒 |
| L3 | duration 重み割付 | 11.6 秒 |
| L4 | 冗長テスト 1 件削除 | 15.8 秒 |

## 7. xdist の collection 流路 (pytest-xdist 3.8.0、実 source で確認)

- `xdist/dsession.py:102-105` の `DSession.pytest_collection` は `return True` で
  **controller プロセスでの item collection を禁止している** (コメント: "prohibit collection of
  test items in controller process")。
- したがって全 collection を行うのは **48 worker だけ**である。controller は行わない。
- izanagi の plugin (`tools/acceptance_shards.py` の `pytest_collection_modifyitems`) は
  各 worker の中で全 collection から `allocate()` を再導出し、自 shard 分だけ retain する。
  つまり **1 受入走で 3 shard x 48 worker = 144 回の全 universe 導出**が行われている。
- 帰結: 「controller の全 collection が critical path に残るから worker を絞っても無駄」という
  反論は成立しない。**worker を絞れば 87.57 → 27.44 秒がそのまま効く。**
- 残る設計問題: 全 universe を観測する主体が 144 から減ることを、閉包 gate の検出力として
  どう補償するか。候補は「shard ごとに軽量な preflight collection を 1 回だけ行い、
  universe と割付を digest 付きで発行し、本走は自 shard の file だけを collect したうえで
  **collect した node 集合が割付と exact 一致すること**を検査する」。
  この案は universe 観測を 144 から 3 へ減らすが、shard 内の exact 一致検査を新設する。
  採否はレンズ A の判定に従う。

## 8. L4 の最終結論 (peer 照合と親の検算)

- 親の走査は正しかった: 現在の main (`dcf053f1c`) で
  `orchestrator/tests/test_real_repo_serialization.py` の `_t080_output_snapshot` と
  `orchestrator/tests/test_s8b_oracle_driver.py:565` の `_t080_output_snapshot` は
  **逐語で完全一致**しており、どちらも `rglob` + `lstat` 実装である。
  したがって main 時点では両 test は真の重複である。
- **しかし削除してはならない。** peer session (branch
  `worktree-dev-wave-acceptance-speedup-20260905`、受入通過済み `child-green`、
  tested_main=19f8ba3e7 / tested_tip=8b5da8352、land 直前) が
  `test_s8b_oracle_driver.py` 側を共有 module
  (`output_snapshot_ignores.git_visible_output_metadata_snapshot`) 実装へ移す。
  着地後は**同一入力を 2 実装で照合する独立オラクルの対**になる。
  片方を消すとこの独立性が消える。
- peer の裁定: 両方残す。速度を削るなら「共有実装だけを速くし、元実装をオラクルとして残す」向き。
  なお t080 の metadata snapshot は size / mtime / ctime を見るので内容不変の `touch` まで捉える。
  peer は git 索引経由化を**意図的に見送った** — 索引は内容の同一性しか言えず `touch` を
  見逃して受理集合が変わるため。高速化の対象外と裁定済み。
- **L4 の結論: 削除候補ゼロ。** 「不要なテストを消す」で回収できる wall は 0 秒である。
  14,179 test function の AST 走査で完全一致 body は 11 組しかなく、10 組は 0.01 秒未満、
  残る 1 組は上記の理由で残す。

## 9. peer 実測 (未 land、`worktree-dev-wave-acceptance-speedup-20260905`)

- snapshot を呼ぶ 12 node の合計が 1 走で 990.3 秒。改修前 63 走の中央値 1,384.8 秒、
  最小 1,017.8 秒なので**改修前の全範囲の外**に出た。1 本平均 115.4 → 82.5 秒。差 約 −394 秒/走。
  その走行は総作業 21,467 秒で改修前中央値 18,552 秒より 16% 混んでいた。
- ただし wall は n=1 では言えない。最遅 shard 264.5 秒に対し、改修前で 264.5 秒以下だった走が
  16/63 ある。peer 自身が「wall は他の帯で決まっている」と読んでおり、親の分解と整合する。
- **含意: 親の L2 / L1 は peer の変更と独立に効く。二重計上しない。**

## 10. floor_campaign の内訳 (専有計算ノード、`-n 0`、重い 5 test 直列)

| 順 | test | call 所要 |
|---|---|---|
| 1 | `test_official_fresh_issues_certificate_and_binds_wall_ledger` | 28.78 秒 |
| 2 | `test_official_resume_validates_certificate_and_completes` | 22.93 秒 |
| 3 | `test_pilot_path_has_no_launch_certificate_changes` | 22.46 秒 |
| 4 | `test_official_resume_rejects_renamed_run_dir` | 16.73 秒 |
| 5 | `test_official_resume_rejects_certificate_time_not_bound_to_run_id` | 16.61 秒 |

- **1 本目に大きな上乗せが無い。** t080 と違い、共有できる高価な前置きは存在しない。
  各テストの所要は実仕事 (`_run_campaign` を crash + resume で 2 回) である。
- ただし受入での中央値は同じ test で 123〜129 秒であり、**専有ノードの 5〜7 倍**に膨らむ。
  各 test は `_real_output_snapshot()` を前後 2 回呼び (例:
  `test_s8b_floor_campaign.py:12927` と `:12948`)、48 worker が同時に Lustre 上の
  478.7 MB / 18,126 file を hash するため競合で膨らむ。
- **これは peer の改修対象そのもの。親の L2 の対象からは外す。**
- **訂正: L2 の対象は t080 だけである。** 段 1 brief が floor_campaign を L2 対象に挙げたのは誤り。

## 11. t080 base key の多重度 (静的、`test_s8b_oracle_driver.py`)

`_t080_stub_free_e2e_repo(...)` の呼出し引数から、base key は 5 種類:

| key | 呼出し位置 |
|---|---|
| 既定 `(none, False, True, False)` | `:1476`, `:1564`, `:1822`, および `test_t080_stub_free_e2e_single_defects...` の 4 param、`..._remaining_section_1_4...`、`..._draft_finalize...`、`..._post_r_delete...` |
| `distinct_basis_blob=True` | `:1375` |
| `r_trailer="AI-Agent: codex"` | `:1797` (defect == "bad-trailer") |
| `extra_r_path=True` | `:1797` (defect == "extra-r-path") |
| `issue_receipt=False` | `:1370`, `:4379` |

- **既定 key を 8〜9 node が共有する。** ここが L2 の主戦場。
- `test_s8b_oracle_driver.py` は 1 file なので `_components` により **全 t080 node は同一 shard**
  (実測でも shard-0) に載る。48 worker へ散る。
- worker 跨ぎ共有なら、key ごとに 1 worker だけが 70 秒を払い (5 key は並行に組める)、
  残る node は約 4 秒になる。shard-0 の最忙 worker 191.6 秒 → 100〜120 秒の見込み。

## 12. 効果見積り (改訂)

| lever | 内容 | 見積り |
|---|---|---|
| L1 | worker の collection を自 shard へ絞る | 各 shard 約 −55 秒 |
| L2 | t080 の base を worker 跨ぎ共有 | shard-0 最忙 worker 191.6 → 100〜120 秒 |
| L3 | duration 重み割付 | −11.6 秒 |
| L4 | 冗長テスト削除 | 0 秒 (候補なし) |

合成見込み: wall 中央値 324.3 → 200〜230 秒。**peer の改修 (別 branch) とは独立で、二重計上しない。**

## 13. 閉包 gate の構造 (`tools/acceptance_shards.py` 実装で確認)

- `pytest_sessionfinish` (`:956-1024`) が shard の `report.json` を書く。
- `worker_occupancy[worker].duration_s` は `pytest_runtest_logreport` (`:862-877`) で
  per-test の `report.duration` を積算したもの = **その worker のテスト実行時間の合計**。
  親の wall 分解の前提はこれで裏が取れた。
- `observed_universe` は `raw_records` = **全 universe の record 列** (nodeid / file / group)。
  `merge_reports` が **shard 間**で照合する (3 者独立の相互検証)。
- `worker_collection_digests` は **shard 内**で 48 worker の collection 一致を照合する。
- **L1 の設計上の要点**: worker を自 shard へ絞ると、`worker_collection_digests` は
  「自 shard の collection について 48 者一致」に意味が変わり、`observed_universe` の
  producer を別に立てる必要がある。ここがレンズ A の判定対象。

## 14. 段 2 プラン後の追加実測 — collection 絞り込みの実現可能性 (親)

### 14.1 D711 の技術的障壁は再現する

- `python3 -m pytest --collect-only -q <shard-2 の 106 file>` は
  **`ModuleNotFoundError: No module named 'tests'`** で失敗する。D711 の記述どおり。
- 親が最初に測った shard-0 / shard-1 の絞り込み collection が成功したのは、
  問題の 2 file (`test_s8b_approved.py`、`test_profiler_directive.py`) が **shard-2 にある**ためで、
  D711 を反証していない。**親の当初の L1 見積りはこの点で不十分だった。**

### 14.2 `--ignore` 方式でも回避できない

- positional target を `orchestrator/tests` に保ったまま非対象 219 file を `--ignore` しても
  同じ `ModuleNotFoundError` になる (5.23 秒)。
- 原因は positional target ではなく **collect する file 集合が部分集合であること**そのもの。

### 14.3 原因は import 順序依存という直せる欠陥

- `orchestrator/tests/test_s8b_approved.py:31` の `from tests.skiputil import Skip, skip` と
  `orchestrator/tests/test_profiler_directive.py:341` の `from codex_roles import policy` は
  どちらも **`orchestrator/` が `sys.path` に載っていること**を要求する
  (`orchestrator/tests/skiputil.py`、`orchestrator/codex_roles/` が実体)。
- repo に `__init__.py` は無く、`pytest.ini` は `testpaths = orchestrator/tests` だけで
  `pythonpath` を設定していない。`orchestrator/` を `sys.path` へ載せているのは
  **他の多数の test module が import 時に行う `sys.path.insert`** である。
- したがって上記 2 file は「他のテストが先に import されていること」に暗黙依存している。
  これは DW-O18 が「file 選択走の偽赤」と呼ぶ型そのもので、**2 file を自己完結させれば直る**。
- **含意: D711 の技術的障壁は原理的な壁ではなく、テスト側の直せる欠陥である。**
  ただし D711 の gate 2 (shard 間の universe 一致) と gate 3 (login の独立 collect-only) が
  なす自己証明回避の対は別問題であり、絞り込みはこれを弱める。**ユーザー裁定が要る。**

### 14.4 D711 の費用前提は失効している

- D711 (2026-08-23) の理由文: 「固定費が実測 **12.86 秒** (48 worker 起動 + 全 collection + 集約、
  テスト 0 件) しかないので、全 collection を K 回払っても費用はほぼ増えない」。
- 現在の固定費は shard あたり **約 59 秒** (親の wall 分解)、うち collection が主。
  D1420 は worker 起動 3.2 秒 / collection 51.7 秒 / 終端 2.9 秒を確定している。
- 48 並列 collection の親実測は全 file 87.57 秒 対 絞り込み 27.44 秒。
- T-2298 の独立実測 (`2026-09-04_t2298-t2273-shard0-critical-path`): 全 suite 非 shard の
  M-A が `wall 487 = collection/起動 119 + test 361 + 7`、shard-0 の 111 file だけの M-C が
  `wall 250 = 56 + 190 + 5`。**collection/起動が 119 → 56 秒。**
- **3 者独立に同じ向きの数字が出ている。費用前提の失効は確実である。**

## 15. L2 の A/B 器 (焦点走、機序を直接測る)

command (両腕で同一):

```
IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600 IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600 \
python3 tools/run_tests.py orchestrator/tests/test_s8b_oracle_driver.py \
  -k "t080_stub_free or t080_full_valid or never_issued_generator_tamper" \
  -n 12 -p no:randomly --durations=0 -q
```

### pre 腕 (main + 単位 B、単位 A 未適用)

- rc=0、**13 passed、wall 99.80 秒**。
- **テスト所要の総和 909.6 秒。** 内訳 (call):
  93.77 / 89.62 / 84.75 / 83.78 / 82.29 / 82.15 / 82.05 / 81.81 / 80.95 / 79.64 (t080 系 10 node)、
  51.44 (never_issued)、17.23 (temp_roots)、0.09 (meta-test)。
- t080 の 10 node が 79.6〜93.8 秒。専有単独の 73 秒に対し、10 台が同時に自分の base を
  組むため膨らんでいる。**レンズ B が「build 時間は並列度に依らない」と仮定した点を、
  この腕自身が否定している。**
- 主指標は 2 つ: (a) 所要の総和 (worker 数に依らず「削れた仕事量」を直接表す)、
  (b) wall (critical path)。**(a) の方が機序に近い。**

## 16. L2 の A/B 結果 — 負結果 (効果なし)

### post 腕 (単位 A 適用、pre と同一 command)

- rc=0、**13 passed、wall 98.92 秒** (pre 99.80 秒、差 −0.88 秒)。
- **テスト所要の総和 932.6 秒** (pre 909.6 秒、差 **+23.0 秒**)。
- 個別 call: 96.81 / 92.01 / 87.86 / 86.86 / 85.47 / 85.46 / 85.40 / 85.37 / 84.61 / 82.69
  (t080 系 10 node、pre は 93.77〜79.64)、45.44 (never_issued、pre 51.44)、
  14.48 (temp_roots、pre 17.23)、0.09 (meta-test)。
- **wall も総和も改善しない。**

### 実装は正しく動いている (repo 外 probe で切り分け)

`host_tree_cache` を直接 import して 2 つの fail-closed 分岐を検査した。

- `xdist_session_cache_root(Path("/tmp/pytest-of-tanab/pytest-1/popen-gw3/test_foo0"), "gw3")`
  → `/tmp/pytest-of-tanab/pytest-1/.izanagi-host-tree-cache-v1` を正しく返す。
  `popen-` 祖先が無い path では `None` (fail-closed) を返す。
- `t080_live_repository_key(...)` は **None にならない** (0.47 秒で digest を返す)。
  HEAD・ccbench HEAD・3 blob・visible path 集合・live source status がすべて束縛されている。
- 実装子の制御テスト (11 passed) も「同時に複数 process が同じ key を要求しても
  builder 呼出しは 1 回」を確認している。

### 効果が出ない理由 (構造的。段 3 レンズ B の B-04 が正しかった)

**消費者が同時に miss すると、共有は「構築 70 秒」を「lock 待ち 70 秒」へ置き換えるだけである。**
待ち時間は test の `call` 所要に計上されるので、wall も所要総和も動かない。
しかも xdist の LPT (長いものから配る) は t080 系を必ず最初に固めて配るため、
本番の受入でも同時 miss になる。process 内 cache が既に「同一 worker 内の再利用」を
賄っているので、worker 数を下げても差は出ない。

**親は反証を試みたが、実測でレンズ B を覆せなかった。**

### 裁定

**単位 A を wave から落とす。** 効果を示せない 465 行の cache 機構と新規 module を
main へ入れることは規律 5 と DW-G05 に反する。設計・制御テスト・本負結果は insight に残す。
patch は `/home/SFC/tanab/.claude/jobs/98cb6669/tmp/unit-a.patch` に保全した
(59,465 bytes、`impl-dev-wave-accwall-unit-a` branch にも存在する)。

### 効果が出る形 (次の一手)

**base を collection 中に組む (prewarm)。** 固定費 59 秒の collection 窓に build 70 秒を
重ねれば、test 段から 85 秒がまるごと消える。lock 待ちにならないのは、
test が始まる前に完了しているからである。T-2333 (timeline 計装) とは独立に設計できるかを
検討する必要がある。
