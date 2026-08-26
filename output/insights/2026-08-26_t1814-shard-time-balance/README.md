# 受入分割 (K=2) の時間不均衡 — 4 層実測と割付の反実仮想

- authority: none
- default_effect: no-state-change
- 計測 tip: `9463bcbcb1541625db59abb97cf6a76934b4c80c` (全 4 走で固定、clean tree)
- 参照走: tested_tip `4b40d17f27b3b8cf94ccaed1c0c07bc166b73244` (2026-08-24、land 済み)
- wave: `dev-wave-t1814-shard-time-balance`

可変状態の正本ではない。決定は `docs/decisions.md`、実績は `docs/worklog.md` を正本とする。

## 何を測ったか

受入 shard 分割 (`tools/acceptance_shards.py`) の `allocate()` が実行時間を見ずに
要素数で bin-packing していることが、受入全走の所要にどれだけ効いているかを測った。

同一 tip で `IZANAGI_ACCEPTANCE_SHARDS` を `2 / 1 / 1 / 2` と交互に切り替えて 4 走し、
D713 の 4 層 (queue 待ち / job Elapse / pytest wall / 外側 wall) を分けて記録した。

## 4 層の実測

| arm | K | queue 待ち | job Elapse | pytest wall | 外側 wall | rc | 計算ノード |
|---|---|---|---|---|---|---|---|
| a1k2 | 2 | 8 / 8 秒 | 318 / 226 秒 | 307.29 / 215.15 秒 | 339.09 秒 | 0 | bnode009, bnode001 |
| a2k1 | 1 | 249 秒 | 270 秒 | 261.45 秒 | 535.18 秒 | 0 | — |
| a3k1 | 1 | 564 秒 | 284 秒 | 275.05 秒 | 864.35 秒 | 0 | — |
| a4k2 | 2 | 8 / 8 秒 | 288 / 160 秒 | 275.02 / 148.99 秒 | 314.96 秒 | 1 | bnode016, bnode017 |

K=2 の値は 2 shard を `/` で区切って併記した。pytest wall と job Elapse は最遅 shard が全体を決める。
a4k2 の rc=1 は非帰属 (下記)。

- **K=2 が K=1 より速いとは言えなかった。** K=2 が 307.29 と 275.02 秒、K=1 が 261.45 と
  275.05 秒。各 2 走では勝敗を宣言できない。
- **queue 待ちは 8 秒から 564 秒まで動いた。** ユーザー裁定どおり所要目標からは除外している。
- **外側 wall と job Elapse の差はほぼ queue 待ちである。** D713 が 3 層を混ぜるなと言う理由が
  そのまま出ている。

## shard の内訳 (K=2、a1k2)

| | shard-0 | shard-1 |
|---|---|---|
| 選択 node 数 | 8580 | 8580 |
| 直列総仕事量 | 8981.5 秒 | 5880.5 秒 |
| 最遅 worker | gw0 222.68 秒 / 76 件 (`real-repo`) | gw1 156.17 秒 / 6 件 |
| 2 番目に遅い worker | gw7 191.4 秒 / 48 件 | gw3 154.9 秒 / 2 件 |
| 中央値 worker | 186.0 秒 | 121.0 秒 |
| 最速 worker | 185.71 秒 | 120.93 秒 |
| 残差 (wall − 最遅 worker) | 84.61 秒 | 58.98 秒 |

**選択 node 数は完全に均等なのに、仕事量は 34% 偏っている。** 控えの主張どおりである。
参照走 (2026-08-24) の偏りは 12.8% だったので拡大している。

**しかし偏りは wall を決めていない。** shard-0 では `real-repo` の排他 group が 1 worker を
222.68 秒占有し、残り 47 worker は 185.7〜191.4 秒に密集している。鎖が単独で最遅である。

`worker_occupancy` の `duration_s` は `report.duration` (setup + call + teardown) の合計であり、
worker ごとの collection・起動・idle を含まない (`tools/acceptance_shards.py:799-811`)。
「残差」はその差分で、走ごとに 39.2〜84.6 秒と動く。**定数として扱ってはならない。**

## 割付の反実仮想 — 完璧な予言者でも 0.0 秒

各走について、その走自身の実測 duration で 3 通りの割付を評価した。makespan 予測は
shard ごとに `max(最長排他鎖, 仕事量/48)` とし、割付で動かない残差は加えていない。

| 走 | 割付 | shard-0 予測 | shard-1 予測 | makespan 予測 |
|---|---|---|---|---|
| a1k2 | count (現行・要素数) | 222.7 秒 (鎖) | 156.2 秒 | **222.7 秒** |
| a1k2 | 台帳の重み | 222.7 秒 (鎖) | 156.2 秒 | **222.7 秒** (±0.0) |
| a1k2 | oracle (その走自身の実測) | 222.7 秒 (鎖) | 156.2 秒 | **222.7 秒** (±0.0) |
| a4k2 | count (現行・要素数) | 206.1 秒 (鎖) | 96.5 秒 | **206.1 秒** |
| a4k2 | 台帳の重み | 206.1 秒 (鎖) | 103.6 秒 | **206.1 秒** (±0.0) |
| a4k2 | oracle (その走自身の実測) | 206.1 秒 (鎖) | 110.1 秒 | **206.1 秒** (±0.0) |

oracle 割付は仕事量を完全に均衡させる (a4k2 で 5283.4 / 5283.4 秒、1 worker あたり 110.1 秒)。
それでも鎖は 1 worker に載り続ける。a4k2 では鎖 206.1 秒に対し shard-0 の仕事量/48 は
139.9 秒しかなく、鎖が 66 秒上回っている。

この結論は模型に依存しない部分を持つ。`xdist` の `loadgroup` は 1 group を 1 worker で直列に
実行するので、その shard の pytest wall は「鎖の所要 + その worker の開始時刻」を下回れない。

## 排他鎖の内訳 (a1k2、222.7 秒 / 76 件)

| 所要 | node |
|---|---|
| 42.77 秒 | `test_codex_reasoning_ab::test_verify_replays_complete_fake_codex_experiment` |
| 18.85 秒 | `test_codex_reasoning_ab::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_c...` |
| 18.57 秒 | `test_s8b_floor_campaign::test_real_seal_protocol_to_floor_official_core_e2e` |
| 13.58 秒 | `test_s8b_oracle_driver::test_v2_standalone_gate_check_requires_full_floor_validation` |
| 11.59 秒 | `test_codex_reasoning_ab::test_replay_forwards_only_successful_snapshot_evidence_to_adj...` |

上位 5 件で 105.4 秒、上位 10 件で 155.3 秒 (鎖全体の 70%)。
`test_codex_reasoning_ab` 群が支配的である。

同じ走の他 group は `s8c-preregistration-candidate` 156.2 秒 / 5 件、
`s8c-predicate-snapshot` 64.3 秒 / 3 件、`dev-waves-runtime` 18.3 秒 / 22 件だった。

## 走間ばらつき — 所要主張の前提を壊す

同一 tip・同一選択・同一割付の K=2 を 2 走した結果。

| | a1k2 | a4k2 | 比 |
|---|---|---|---|
| 直列総仕事量 | 14862.6 秒 | 10585.7 秒 | 1.40 倍 |
| pytest wall (最遅 shard) | 307.29 秒 | 275.02 秒 | 1.12 倍 |
| 排他鎖 | 222.68 秒 | 206.06 秒 | 1.08 倍 |
| 計算ノード | bnode009, bnode001 | bnode016, bnode017 | — |

**追おうとしている効果 0.0 秒に対し、ノイズが 32 秒ある。**

## 台帳の陳腐化 — 走の違いと suite の成長を分離する

commit 済み台帳 `orchestrator/tests/acceptance_duration_ledger.json` (15,909 nodeid) と、
各走の junit を同一 nodeid で突き合わせた。

| 走 | 台帳共通 node の実測比 | 倍率 p50 | 倍率 p95 |
|---|---|---|---|
| 参照走 4b40d17f (8/24) | 0.99 倍 | 0.91 | 2.12 |
| a1k2 9463bcbc (8/26) | 1.64 倍 | 1.01 | 4.75 |
| a4k2 9463bcbc (8/26) | 1.18 倍 | 0.90 | 2.24 |

- 台帳は参照走とほぼ一致する (0.99 倍)。台帳はその頃に採られたと見てよい。
- **a1k2 の 1.64 倍はノードの遅さである。** 同一 tip の a4k2 は 1.18 倍で、分布 (0.90 / 2.24) は
  参照走 (0.91 / 2.12) とほぼ同じ。
- 2 日ぶんの実際の増加は、共通テストで 1.24 倍、新規 2323 件を含めた総量で 1.42 倍
  (7472.5 → 10585.7 秒)。
- 台帳の被覆は 15,878 / 17,160 = **92.5%**。1282 node が台帳に無い。

## 非帰属の赤 (a4k2)

`orchestrator/tests/test_t810_coordinator.py::test_authorized_production_core_uses_same_validator_twice_and_dormant_prereg`
が a4k2 だけで落ちた。本走の実装差分はゼロ (tip = local main) である。

失敗は `FileNotFoundError` で、読もうとしたのは
`/work/1/SFC/tanab/izanagi/.git/worktrees/dev-wave-8b-b2-precheck/gitdir` だった。
走行中に別セッションがその worktree を撤去したと考えられる。この test は生きた worktree 登録を読む。
a1k2 と K=1 の 2 走では緑だった。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief (算術の訂正を含む)
- `verbatim/s1-anchors.md` — 実アンカー表と実測値
- `verbatim/s2-plan.md` — 段 2 codex plan
- `verbatim/s3-sol.md` — 段 3 敵対レンズ (正しさ境界)
- `verbatim/s3-luna.md` — 段 3 敵対レンズ (実効性・計測設計・運用)
- `verbatim/s4-adjudication.md` — 段 4 裁定

## 一次資料 (repo 外)

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1814-shard-time-balance/` —
  `arm-{a1k2,a2k1,a3k1,a4k2}.log` と `.meta`、`measure.sh`、および抽出・解析器
  `extract_layers.py` / `counterfactual.py` / `ledger_ratio.py` / `compare_runs.py` / `probe_alloc.py`
- `/work/1/SFC/tanab/.izanagi-acceptance-shards/e4a77eb86b3e8ad9c4855255307be11c/` — a1k2
- `/work/1/SFC/tanab/.izanagi-acceptance-shards/87fb18347fefb28dbbe2eb099604265e/` — a4k2
- `/work/1/SFC/tanab/.izanagi-acceptance-shards/e6887cb4d4059ee0ec0dbb6aea880485/` — 参照走

## land 待ちの相談 (2026-08-26、段 9)

受入全走が 2 走とも `test_dev_wave_cleanup.py` の別 node で rc=22 の占有不定になり land できず、
扱いを codex 2 レンズへ相談した。逐語は `verbatim/s9-consult-sol.md` と
`verbatim/s9-consult-luna.md`、相談材料は `verbatim/s9-situation.md`。

**両レンズが独立に (a) file 除外も (b) node hold も否定した。**

- **親の「脆弱な 15 node」は誤りだった。** 実 `/proc` に到達する成功経路は **6 node** だけである。
  `test_landed_attached_worktree_is_removed[locked|unlocked]`、
  `test_forward_merged_landing_tip_is_used_for_cleanup[derived|asserted]`、
  `test_reentry_states_run_only_remaining_cleanup[a|b]`。
  残りは `_occupancy_payload` を monkeypatch 済みか occupancy phase を持たない。
  親が現物で裏を取り直して確認した。観測された赤 2 件はどちらもこの 6 の中である。
- **同 file に隔離用ヘルパー `_stub_unoccupied` が既にある**
  (`orchestrator/tests/test_dev_wave_cleanup.py:128`、呼び出し 854 / 974 / 1018 / 1102)。
  上の 6 node だけがこれを使っていない。
- **今回の赤は D793 の射程外である。** 拒否本文が `attempts=1 retry_count=0` であり、
  `missing/{stat,cwd,cmdline}` だけなら最大 3 scan の再試行に入る
  (`tools/dev_wave_cleanup.py:29-30, 488-496`)。1 回で拒否された以上、
  `pid-reused` / permission / invalid / os-error / proc-root のような非 retryable な issue が
  少なくとも 1 件混じっている。D793 が閉じたのは deleted-cwd の 1 経路だけである
  (`tools/check_worktree_occupancy.py:427-445`)。
- **どの経路かは現状の出力からは特定できない。** 拒否 stderr が issue payload を捨てている。
  最初の一手は rc=22 の診断へ issue の `error` / `source` を出すことである。
- **(b) は現行契約では成立しない。** registry は row ごとに赤の実測を要求し、さらに canonical
  `docs/failures.md` の該当節が test 関数名と失敗署名を逐語で含むことを要求する
  (`orchestrator/tests/flaky_test_holds.py:105-112, 115-126, 146-161`)。
  赤を実測したのは 2 node だけで、その再発記録もまだ spool fragment のままである。
- **(a) は 94 node を受入から落とす。** 除外は実際には `--ignore=<file>` になる
  (`orchestrator/test_selection_contract.py:121-124`)。旧 entry の理由文
  「消滅 pid 型」も F489 の 2026-08-25 追記で誤りと判明している。
- luna は 1 走あたりの非帰属赤の確率を感度範囲 0.65〜1.0 と見積もった (観測 2 点であることの
  限界を明記した上で)。20 wave なら追加 25.8〜40 request、pytest wall 合計 59〜102 分になる。
- **前回の解除条件は再利用できない。** 「task が land し、明示 file 走が全緑」は 2026-08-25 に
  満たされ、翌日に再発した。
- **hold は受入だけでなく焦点走でも無条件に skip する。** 並行 job
  「dev-wave flake test correction」の指摘を親が現物で確認した。
  `orchestrator/tests/conftest.py:1335-1347` は collection 中の item の nodeid が registry に
  在れば無条件に `pytest.mark.skip` を付ける。growth hold と違って解除 env が無い。
  つまり一度登録した node はどこでも走らなくなる。(b) を採らなかったのはこの点でも正しい。
- **同 job から、登録行が修理より長生きする実例も来た。** 登録済み 3 件のうち 2 件は
  2026-08-26 09:17 の `639f2f28` (T-1719 の fix 子) でテスト側が既に直っていたのに、
  登録行だけが残っていた。修理と登録が別 wave に分かれると取り残しが起きる。

## 段 9 の帰結

- (c) の実装修理は並行 job「known-violation triage」が引き取った。
  編集面は `tools/check_worktree_occupancy.py` / `tools/dev_wave_cleanup.py` /
  `orchestrator/tests/test_dev_wave_cleanup.py` / `orchestrator/tests/test_check_worktree_occupancy.py`。
- 本 wave は受理集合を変えず、その修理が land するまで land を待つ。
- 親から先方へ渡した実測: 脆弱 6 node の名前、`_stub_unoccupied` の実在、
  `attempts=1` が D793 の射程外を意味すること、最初の一手は issue payload の可視化であること。
