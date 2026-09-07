# 受入全走の wall を分解し、短縮候補を実測で 3 つに絞った (2 つは負結果)

- authority: none (可変状態の正本は worklog と decisions。本書は一次資料の置き場)
- default_effect: no-state-change
- wave: `dev-wave-acceptance-wall-20260907` / branch `worktree-dev-wave-acceptance-wall-20260907`
- base main: `d19d2182fbc324f67b47f600be70136d6503aa59`
- 実測日: 2026-09-07 (Pegasus login pegasus02、計算ノードは dispatch 経由)
- 一次資料: `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/*/{junit.xml,report.json}`

依頼は「受入全走が時間がかかりすぎている。不要なテストは消す、並列化・バッチ化・賢い論理での
短縮はやる、リワードハック禁止」。**本 wave が land したのはテスト 2 件の削除だけである。**
短縮を主張しない。主成果は wall の分解と、短縮候補 3 つの値付けである。

## 1. wall の分解

`report.json` の `worker_occupancy[gwN].duration_s` と junit の `testsuite@time` を join した。
直近 3 日の約 77 走の中央値。

| shard | wall | 最忙 worker のテスト実行時間 | 残差 | W (所要総和) | 最長排他鎖 C | W/48 |
|---|---|---|---|---|---|---|
| shard-0 | 306.6 | 191.6 | 102.0 | 7963 | 78.5 | 165.9 |
| shard-1 | 215.2 | 156.6 | 59.0 | 5757 | 16.7 | 119.9 |
| shard-2 | 220.6 | 161.6 | 58.6 | 4957 | 161.6 | 101.4 |

- 全体 wall (3 shard の最大) 中央値 **324.3 秒**、p25 274.3、p75 378.0、p90 433.1、最大 663.4。
  **300 秒超過 45/75 走。**
- **shard-0 が 75 走中 70 走で最遅。** 2 位との差の中央値 61.7 秒。
- **`wall = 最忙 worker のテスト実行時間 + 残差` で説明できる。** 残差は shard-1 / shard-2 で
  59 秒とほぼ一定、shard-0 だけ 102 秒。

`worker_occupancy.duration_s` は `pytest_runtest_logreport` で per-test の `report.duration`
(setup / call / teardown) を worker ごとに積算したものであり
(`tools/acceptance_shards.py` の `pytest_sessionfinish`)、
protocol 外の lock 待ち・scheduler gap・collection・起動は含まない。**残差を collection と
同一視してはならない。**

## 2. 残差の主因は collection の重複

| 条件 | 所要 |
|---|---|
| 単独・全 325 file (21,005 test)、cold | 36.83 秒 |
| 単独・全 325 file、warm | 10.23 秒 |
| 単独・shard-0 の 113 file (7,012 test) | 8.06 秒 |
| 単独・shard-1 の 106 file (6,979 test) | 9.90 秒 |
| 単独・test file 1 本 (24 test) | 0.37 秒 |
| **48 プロセス同時・全 file** | **87.57 秒** |
| **48 プロセス同時・shard-0 scope** | **27.44 秒** |

`xdist/dsession.py` の `DSession.pytest_collection` は `return True` で controller の item
collection を構造的に禁じている。したがって全 collection を行うのは **worker だけ**であり、
1 受入走で 3 shard x 48 worker の全 universe 導出が同時に走る。

独立な裏づけが 2 つある。

- D1420 は worker 起動 3.2 秒 / collection 51.7 秒 / 終端 2.9 秒を確定している。
- `output/insights/2026-09-04_t2298-t2273-shard0-critical-path/` の M-A (全 suite 非 shard) が
  `wall 487 = collection/起動 119 + test 361 + 7`、M-C (shard-0 の 111 file 非 shard) が
  `wall 250 = 56 + 190 + 5`。**collection/起動が 119 → 56 秒。**

**3 者独立に同じ向きの数字が出ている。**

## 3. 候補 1 — collection の絞り込み (実装せず、ユーザー裁定へ)

賞金は shard あたり約 55 秒。しかし **D711 が明示的に禁じている**。

D711 の 2 つの理由を個別に検査した。

- **「file を positional target へ渡す形は使えない」は再現した。** shard-2 の 106 file を
  positional target にすると `ModuleNotFoundError: No module named 'tests'` になる。
  `--ignore` で非対象 219 file を外しても同じ失敗になる (5.23 秒)。
  原因は positional target ではなく **collect する file 集合が部分集合であること**である。
  `orchestrator/tests/test_s8b_approved.py:31` の `from tests.skiputil import` と
  `orchestrator/tests/test_profiler_directive.py:341` の `from codex_roles import policy` は
  どちらも `orchestrator/` が `sys.path` に載っていることを要求し、それを載せているのは
  **他の多数の test module が import 時に行う `sys.path.insert`** である。
  repo に `__init__.py` は無く、`pytest.ini` も `pythonpath` を設定していない。
  **この 2 file を自己完結させれば直る。原理的な壁ではない。**
- **「固定費が実測 12.86 秒しかない」という費用前提は失効している。** 現在の固定費は
  shard あたり約 59 秒で、約 4.6 倍である。

**残る本質的な論点は 1 つだけ**である。D711 の gate 2 (全 shard の `observed_universe` 一致) は
「collection plugin が file を 1 件落としても全員が同じ縮小集合に同意して緑になる」経路を
断つためにある。絞り込みはこの二重化を弱める (gate 3 の login 独立 collect-only は残る)。
**正しさ防壁の変更であり、親の一存では決めない。**

なお、親は当初 shard-0 / shard-1 の絞り込み collection が成功したことを根拠に
「D711 の技術的障壁は無い」と考えたが、これは**問題の 2 file が shard-2 にあったための
偽陽性**だった。段 2 の子がこの誤りを指摘した。

## 4. 候補 2 — t080 base の worker 跨ぎ共有 (実装して A/B、負結果)

`orchestrator/tests/test_s8b_oracle_driver.py` の t080 base fixture は 1 回 70 秒かかり、
テスト本体は約 4 秒である (専有計算ノード、`-n 0`、同一 base key の 4 param 直列:
73.64 / 14.98 / 3.70 / 3.67 秒)。11 node が 11 worker へ散るため worker ごとに組み直される
(T-2298 が既に実測していた。本 wave の再発見である)。

Codex `role=author` が host 共有 cache を実装した (`orchestrator/tests/host_tree_cache.py`、
465 行 + 専用テスト、自走 harness 11 passed)。cache key は HEAD・ccbench submodule HEAD・
凍結 3 blob・git 可視 output 集合 digest・live source status を束縛し、束縛できなければ
fail-closed で再構築する。lock は publish 直前まで、copytree は lock 外、
返却は毎回独立実体、document は deepcopy。

### A/B (同一 command、`-n 12`、13 node)

| 腕 | wall | 所要総和 |
|---|---|---|
| pre (単位 A 未適用) | 99.80 秒 | 909.6 秒 |
| post (単位 A 適用) | 98.92 秒 | 932.6 秒 |

**wall も所要総和も改善しない。**

実装は正しく動いている。repo 外 probe で 2 つの fail-closed 分岐を直接検査し、
`xdist_session_cache_root` は標準の xdist 配置で正しい root を返し、
`t080_live_repository_key` は None にならない (0.47 秒で digest を返す) ことを確認した。

**効果が出ないのは構造的な理由である。** 消費者が同時に miss すると、共有は「構築 70 秒」を
「lock 待ち 70 秒」へ置き換えるだけで、待ち時間は test の `call` 所要に計上される。
xdist の LPT は t080 系を最初に固めて配るため、本番の受入でも同時 miss になる。
process 内 cache が既に「同一 worker 内の再利用」を賄っているので、worker 数を下げても差は出ない。

**段 3 のレンズ B (所見 B-04) がこれを事前に予告し、親は実測で覆せなかった。**
T-1933 が grouping で得た +0.897 秒 (変化なし) とも整合する。

**裁定: 効果を示せない 465 行の cache 機構と新規 module を main へ入れることは規律 5 と
DW-G05 に反するため、単位 A を wave から落とした。** patch は
`verbatim/unit-a-dropped.patch` に保全した (59,465 bytes)。

**効果が出る形の候補**: base を collection 中に組む (prewarm)。固定費 59 秒の窓に build 70 秒を
重ねれば、test 段から消える。lock 待ちにならないのは test が始まる前に完了しているからである。

## 5. 候補 3 — collection hook の重複評価除去 (実装して撤去)

`tools/acceptance_shards.py` の `pytest_collection_modifyitems` は `_canonical_item` を
item ごとに 2 回呼んでいた。1 回化する変更を実装したが、次の理由で撤去した。

- 旧測定では collection hook 全体が 0.375 秒であり、**効果は約 0.4 秒 = wall の 0.1%** である。
- 段 6 レンズ C が「形式的な受理集合が広がる」(アクセスごとに値を変える Item に対して
  二時点検査が消える) と指摘した。現 repo に custom Item は無く悪用不能だが、
  **0.1% のために受理集合を形式的にでも広げるのは規律 2 に反する。**
- 段 6 レンズ C が「report bytes 一致検査は両辺が同じ現行 renderer を呼ぶ恒真形」、
  レンズ D が「回帰検査が worker → controller の本番集約経路を通らない」と指摘した。
  どちらも証拠の質の欠陥である。

## 6. 候補 4 — 不要テストの削除 (land した唯一の変更)

14,179 個の test function を AST body で走査した。完全一致 body の対は 11 組。

- 10 組は所要 0.01 秒未満で wall に効かない。
- 1 組 (`test_t080_output_snapshot_observes_git_visible_create_and_delete` が
  `test_real_repo_serialization.py` と `test_s8b_oracle_driver.py` に重複) は
  **削除しない**。現 main では逐語一致だが、別 wave
  (`worktree-dev-wave-acceptance-speedup-20260905`) が片側を共有 module 実装へ移すため、
  着地後は同一入力を 2 実装で照合する独立オラクルの対になる。
- 「定数のみ相違」の群 (18 / 17 / 11 件) は別々の負例であり、削除は被覆を減らす。

実際に削除したのは 2 node である。

- `test_autonomous_trial_completeness.py::test_pre_raw_failure_allows_missing_raw_response_pointer`
  (残す側: 同 file の `test_p3_role_invalid_partial_passes`)
- `test_codex_reasoning_ab.py::test_f176_preserves_decision_mentions` の `go_condition` param
  (残す側: `test_f176_preserves_legitimate_opposite_mentions` の `go_condition_not_met` param)

`acceptance_duration_ledger.json` の対応 2 key を削除し `nodeid_count` を 19519 → 19517 とした。

**回収できる wall は約 1 秒である。「不要なテストを消す」は受入の所要にほぼ効かない。**

## 7. 変異

削除の positive control は「**残す側が、削除した側と同じ検出力を持つか**」である。
production を壊して残す側が赤になることで示した。

| 変異 | 内容 | 期待 node | 結果 |
|---|---|---|---|
| M1 | pre-raw 失敗でも raw response pointer を必須にする | `test_p3_role_invalid_partial_passes` | KILLED |
| M2 | 決定 token 先読みから CJK 範囲を落とす | `test_f176_preserves_legitimate_opposite_mentions[go_condition_not_met]` | KILLED |
| M3 | 台帳の `nodeid_count` を旧値へ戻す | `test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations` | KILLED |

**3/3 KILLED、期待 node 完全一致、MISMATCH 0 / SURVIVED 0 / TIMEOUT 0。**
spec と台帳は `mutation-spec.json` / `mutation-ledger.json`。

## 8. 親自身の訂正

- **D1020 の引き金は成立していない。** 親は `C < W/48` を shard ごとに当てたが、
  D1020 の式は `C > W/(48K)` で `W` は**走全体**の直列総仕事量、`K` は shard 数である。
  走全体で `W = 18,587 秒`、`K = 3` なので `W/(48K) = 129.1 秒`、`C = 161.6 秒`。
  `C > W/(48K)` であり成立側にない。段 3 レンズ B が指摘した。
- **反実仮想の利得は小さい。** D1019 と同じ方法論 (各走自身の実測 duration、
  makespan 模型 `max(C, W/48)`) で 75 走を評価すると、count 割付 180.1 秒 →
  duration 割付 161.6 秒、利得の中央値 11.6 秒。走間ばらつき (D1019 実測 32 秒) より小さい。
  **D1019 はそのまま有効である。**
- **中央値 324.3 秒は固定 tip の基準線ではない。** 75 走は複数 tip の混合であり
  (collection digest 40 種、universe 20,410〜21,111 件)、前後比較には使えない。
  「現状はこの帯にいる」という所在の記述にのみ使う。
- **「削除候補ゼロ」は誤りだった。** 親の AST 走査は body 120 文字未満を除外していたため
  短い重複を落としていた。段 2 の子が 2 件を見つけた。

## 9. 段 6 レビューの所見 (blocker 0)

レンズ C: `blocker` 0、`should-fix` 2 (どちらも撤去した単位 B の B1 について)。
レンズ D: `blocker` 0、`should-fix` 2 (B1 の検査経路、および未 commit 木での受入赤の警告)。
所見の逐語は `verbatim/s6-review-c.md` / `verbatim/s6-review-d.md`。

## 10. 非主張

- 本 wave は受入 wall の短縮を主張しない。land した変更の効果は約 1 秒である。
- 候補 1 の 55 秒は**未実装**であり、ユーザー裁定を要する。
- 候補 2 は実装したうえで**効果なしを実測**し、撤去した。
- D1184 により受入 gate 自身を編集する wave はその gate で捕捉できないが、
  本 wave は最終的に `tools/acceptance_shards.py` を変更していない。
