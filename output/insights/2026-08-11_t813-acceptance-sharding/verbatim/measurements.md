# [T-813] probe 実測 (2026-08-11、本 wave が計算ノードで実走)

tree = worktree `dev-wave-t813-shard-eval` (main `1da73f2b`)、collection 8725 item / 163 file。
argv は全 arm とも **file 列挙形** (= `_is_acceptance_run` False、受入 lease を取らない部分走)。

## M-1. arm 一覧と生値

| arm | shard | rc | PBS Elapse | pytest wall | 結果 | node |
|---|---|---|---|---|---|---|
| base (k=1) | 0 | **1** | 546s | **539.83s** | 8 failed, 8697 passed, 20 skipped | bnode014 |
| k4count | 0 | 0 | 444s | **437.78s** | 2169 passed, 13 skipped | bnode015 |
| k4count | 1 | 0 | 233s | 227.31s | 2181 passed | bnode022 |
| k4count | 2 | **1** | 59s | 53.40s | 8 failed, 2171 passed, 2 skipped | bnode023 |
| k4count | 3 | **1** | 22s | 16.46s | 1 failed, 2165 passed, 5 skipped, **1 error** | bnode024 |

- 分割規則 = file 単位・group-atomic・件数均等 (LPT)。件数は 2182/2181/2181/2181 と**完全に均等**。
- それでも実時間は **437.8 / 227.3 / 53.4 / 16.5 秒**。**件数による均等化は無意味**である。

## M-1b. arm k4time (実測時間で重み付けした分割)

base の junit を重みにして LPT で割り直した (`make_shards.py --weights junit-base-0.xml`)。

| arm | shard | file | test | rc | PBS Elapse | pytest wall | node |
|---|---|---|---|---|---|---|---|
| k4time | 0 (real-repo 束) | 13 | 1037 | **1** | 277s | **271.87s** | bnode016 |
| k4time | 1 (`test_codex_reasoning_ab.py` 単独) | 1 | 139 | 0 | 188s | 182.39s | bnode017 |
| k4time | 2 | 74 | 3631 | 0 | 67s | 61.29s | bnode020 |
| k4time | 3 | 75 | 3895 | **1** | 102s | 97.08s | bnode022 |

## M-2. wall とポイント (核心。**k4count だけを見ると誤る**)

| 指標 | base (1 ノード) | k4count (件数均等) | **k4time (時間均等)** |
|---|---|---|---|
| makespan (pytest wall の最大) | 539.83s | 437.78s (1.23×) | **271.87s (1.99×)** |
| ノード秒 (PBS Elapse 合計) | 546s | 758s (1.39×) | **634s (1.16×)** |
| 直列総和 (junit time 合計) | 10320.53s | 7941.05s | 7827.51s |

- **正しい重みで割れば、4 ノードで wall はほぼ半分 (1.99×)、ポイントは +16% で済む。**
  裁定パッケージの「ポイントほぼ不変で wall を縮められる」は、**性能面では実測で支持された**。
  ただし後述のとおり **k=4 で既に下界に達しており、k を増やしてもこれ以上は縮まない**。
- **件数均等 (k4count) は失敗する** — 件数を完全に均等 (2182/2181/2181/2181) にしても
  実時間は 437.8 / 227.3 / 53.4 / 16.5 秒とばらけた。均衡化は実測時間の重みでしか行えない。
- ノード秒が k 倍にならないのは、軽いシャードが早く終わってノードを返すため。
- 直列総和が base より 24% 少ない = **base は同一ノード内の競合で個々のテストが遅くなっている**
  (最長テスト: base 303.96s → k4time 263.08s)。分割の利得の一部はこの競合緩和である。

## M-3. critical path (分割の理論下界)

base junit (8725 case) の解析:

- 直列総和 **10320.5s** / 48 worker = 215.0s
- **単体最長テスト = 303.96s** (`test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`)
- 200 秒超のテストが 9 本、すべて `test_s8b_oracle_driver.py` と `test_codex_reasoning_ab.py`
- file 直列和: `test_s8b_oracle_driver.py` **4103.9s** / `test_codex_reasoning_ab.py` 2436.8s
  → 2 file で直列総和の **63%**
- xdist group 直列和: `real-repo` 290.2s / `s8c-preregistration-candidate` 154.7s / `dev-waves-runtime` 17.5s
  (2026-08-09 に 1388.8s あった `real-repo` の巨大テストは解消済み)

**下界 = 最長テストの非競合時の所要 ≒ 263s。この値は k に依存しない。**
さらに `test_s8b_oracle_driver.py` は `real-repo` group を含むため **group-atomic 分割では割れない**。

**k4time の実測がこの下界に到達している**: シャード 0 の wall 271.87s に対し、
同シャードの最長テストは 263.08s。**つまり k=4 で既に飽和しており、k=8 でも 16 でも
271 秒より速くならない。** 「wall を 1/k」は k=4 までしか成り立たない。

## M-4. CPU 利用率 (「足りないのはコアではない」)

走行中の `qstat` 実測: base = CPU 2168.12s / Elapse 496s → **平均 4.4 コア**。
シャード 0 = CPU 2605.16s / Elapse 433s → **平均 6.0 コア**。いずれも 48 コア中である。
**suite は subprocess・git・待ちで律速されており、コアは既に 40 以上余っている。**
ノードを足すことは、余っているコアをさらに足す行為にあたる。

## M-5. 受理集合の和 (分割の正しさ)

`diff_union.py` で junit の和と collection を突き合わせた。

- **k4count: 和 = 8716 / collection = 8725 — 9 件足りない。**
  内訳は `test_s8b_approved.py` の 10 テストが**収集エラーで 1 件も走らなかった**こと (junit には
  collection error の 1 entry だけが残る)。→ **「和 = 既定 target」の検査はこの欠落を検出できる。**
- base: 和 = 8725 = collection (完全一致)。
- **測定側の注意 (親の artifact):** `--dist loadgroup` は junit の `testcase/@name` を
  `<name>@<group>` にする。`test_compile_argv_gate_rejects_bypass_channels[@args.rsp]` のように
  **id 自体に `@` を含むテスト**があるため、`@` で単純に切る併合器は id を壊す (base でも 1 件ずれた)。
  結果併合を実装するなら、この曖昧さを解かねばならない。

## M-6. 分割由来の赤 (fail 帰属)

| 症状 | 出た場所 | 原因 | 全走では |
|---|---|---|---|
| 収集 ImportError `No module named 'tests'` (10 テスト消失) | k4count-3 `test_s8b_approved.py:31` (`from tests.skiputil import`) | 同一シャードに `sys.path` を用意する file が居ない | 緑 |
| `No module named 'codex_roles'` | k4count-3 `test_profiler_directive.py::…role_policy_check` | 同上 | 緑 |
| 収集 ImportError `No module named 'tests'` (**24 テスト消失**) | **k4time-0** `test_s8b_protocol_builder.py:37` (`from tests import repo_tree_util`) | 同上 | 緑 |
| 上の巻き添え 2 件 | k4time-0 `test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root@real-repo` ほか | 収集できなかった module への横断整合検査が赤 | 緑 |
| `assert repo_before == _real_output_snapshot()` × 8 | k4count-2 / **base** `test_s8b_floor_campaign.py` | **他 job の dispatch receipt** が `output/pegasus-dispatch/` に書かれた | 単独走なら緑 |

**分割ごとに壊れる file が違う。** k4count は `test_s8b_approved.py` と `test_profiler_directive.py`、
k4time は `test_s8b_protocol_builder.py` を壊した。試した 2 通りの分割の**両方**が (F) を破った。

### M-6b. 根本原因 (実測で特定)

- repo には `orchestrator/__init__.py` も `orchestrator/tests/__init__.py` も**無い**。
  pytest の既定 (`prepend`) では各 test file の basedir = `orchestrator/tests/` が `sys.path` に入るだけで、
  **`orchestrator/` は入らない**。
- しかし `from tests import repo_tree_util` (`test_s8b_protocol_builder.py:37`)、
  `from tests.skiputil import Skip` (`test_s8b_approved.py:31`)、
  `from codex_roles import policy` (`test_profiler_directive.py:341`、**実行時 import**) は
  いずれも **`orchestrator/` が `sys.path` にあること**を要求する。
- それを入れているのは **`orchestrator/tests/test_reflux_ir.py:122` の module 直下の
  `sys.path.insert(0, str(_ORCH))`** という**副作用**である (同型の insert は多数あるが、
  多くは repo root を入れており `orchestrator/` を入れるのはこれと `test_campaign.py:7856` ほか)。
- **全走で必ず緑になる理由:** xdist の各 worker は**全 test file を収集する** (collection は
  worker ごとに全体を回す) ため、`test_reflux_ir.py` の import が必ず走り、path が整う。
- **分割で壊れる理由:** シャードの worker は自分のシャードの file しか収集しないので、
  `test_reflux_ir.py` が同じシャードに無ければ path が整わない。

→ **M0 は小さく閉じられる。** conftest で `orchestrator/` を明示的に `sys.path` へ入れ、
「偶然の module 副作用」への依存を断てばよい。ただし検査は**収集だけでは足りない**
(`codex_roles` の 1 件は `when=call` の実行時 import であり、`--collect-only` では捕まらない)。

### M-6c. 単独収集検査 (163 file、`probe_solo_collect.sh`)

各 test file を単独で `--collect-only` した結果、**収集エラーは 2 file だけ**
(`test_s8b_approved.py`、`test_s8b_protocol_builder.py`、いずれも `No module named 'tests'`)。
残りは全て rc=0。**破れは広範ではなく、少数の file に限局している。**

- 前 2 者は **分割不変性の破れ**。「どの nodeid が緑か」が分割の取り方に依存する。
- 3 つ目は **同時投入の副作用**で、base 側でも出た (base は 4 シャードと並走していた)。
  `_real_output_snapshot()` は実 repo の `output/` を byte 単位で固定する関数で、同 file 内に
  **19 箇所**の呼び出しがある。`test_s8b_floor_campaign.py` は `real-repo` group に**入っていない**
  ため、排他 group を group-atomic に保っても守られない。
- k シャードを 1 checkout から投入する設計は、この副作用を**必ず**生む
  (receipt の書き先は `<repo>/output/pegasus-dispatch/` 固定)。

## M-7. queue 待ちと固定費

- 5 job 同時投入で shard 0 の dispatch wall 791s に対し PBS Elapse 444s → **queue 待ち約 350 秒**。
  base は 565s vs 546s で待ち 19 秒。**k 本同時投入は queue 待ちを生む** (今日の gen_S は空だったにもかかわらず)。
- 固定費: collection 13.56 秒 + job 起動。k 分割は collection を k 回払う。

## M-8. wall-clock gate を持つテスト ([T-810] 条件付き)

- `orchestrator/tests/test_dev_waves_protocol.py:312` — `assert elapsed < 0.15` (timeout_s=0.04 の 3.75 倍余裕)
- `orchestrator/tests/test_dev_wave_land.py:1244` — `assert elapsed < 2.0` (lock-busy の即時性)
- `orchestrator/tests/test_dev_waves_worker.py:198` — `assert elapsed < 5.0` (timeout_s=0.05 の 100 倍余裕)

いずれも「有界であること」を検査する上界であり、**どのノードに載るかで余裕が変わる**。
本 wave の probe は 5 ノード (bnode014/015/022/023/024) に散ったが、これらの gate は全 arm で緑だった。
ノード間差の大きさは [T-810] が測定 protocol を設計中で未 land のため、**「余裕が十分か」は本 wave では結論できない**。
