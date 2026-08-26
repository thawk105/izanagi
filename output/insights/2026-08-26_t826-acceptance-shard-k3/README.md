# 受入全走の shard 数 2 対 3 — 4 層実測と、律速が単体テストへ移ったことの確認

- authority: none
- default_effect: no-state-change
- 計測 tip: `b253e0b79609f74ce757a7fc11c609f21643a7b7` (= 計測時点の local main、実装差分ゼロ)
- wave: `dev-wave-t826-acceptance-closure-split`
- 実装 commit: `c05f389509e97488984ca2fcb31fa49596413d5e`

可変状態の正本ではない。決定は `docs/decisions.md`、実績は `docs/worklog.md` を正本とする。

## 何を測ったか

受入全走 (`tools/run_tests.py` の受入形) の所要が shard 数 K でどう変わるかを、同一 tip・
実装差分ゼロのまま `IZANAGI_ACCEPTANCE_SHARDS` だけを 2 と 3 に切り替えて測った。
受入 receipt を作る `tools/dev_wave_wait.py acceptance` 経路は claim 時に main を merge して
tip を動かすため、計測としては使わず `tools/run_tests.py --force-dispatch` を直接投入した。

D713 に従い queue 待ち / job Elapse / pytest wall / 外側 wall を混ぜない。ユーザー裁定により
queue 待ちは所要目標から除外する。

## 4 層の実測

| arm | K | pytest wall (最遅 shard) | 最遅 worker | `W_shard/48` | 残差 | 結果 |
|---|---|---|---|---|---|---|
| arm1 | 2 | **285.52 秒** | 211.99 秒 | 203.9 秒 | 73.53 秒 | 1 failed (非帰属) / 17390 passed / 64 skipped |
| arm2 | 3 | **160.92 秒** | 101.70 秒 | 94.7 秒 | 59.22 秒 | 17391 passed / 64 skipped |

shard 別の内訳。

| | arm1 shard-0 | arm1 shard-1 | arm2 shard-0 | arm2 shard-1 | arm2 shard-2 |
|---|---|---|---|---|---|
| 選択 node 数 | 8728 | 8727 | 5819 | 5818 | 5818 |
| 直列総仕事量 | 9786.3 秒 | 6823.1 秒 | 4544.9 秒 | 3441.5 秒 | 2843.2 秒 |
| pytest wall | 285.52 秒 | 225.13 秒 | 160.92 秒 | 123.22 秒 | 146.19 秒 |
| 最遅 worker | 211.99 秒 | 170.40 秒 | 101.70 秒 | 74.18 秒 | 96.64 秒 |
| 最速 worker | 202.73 秒 | 140.40 秒 | 92.28 秒 | 71.29 秒 | 57.70 秒 |
| 残差 | 73.53 秒 | 54.73 秒 | 59.22 秒 | 49.04 秒 | 49.56 秒 |

- **K=2 → K=3 で最遅 shard の pytest wall が 124.60 秒 (43.6%) 縮む。** D1019 が記録した
  同一 tip・同一割付の走間ばらつき 32.27 秒に対し 3.9 倍で、ノイズでは説明できない。
- **直列総仕事量そのものが 1.53 倍縮む** (16609.9 秒 対 10830.1 秒)。1 node あたりの worker 数は
  どちらも 48 で同じなので、これは容量の増加ではなく **node あたり総負荷の低下による競合の減少**
  である。K は容量を増やすだけでなく仕事量を減らす。
- **`real-repo` の排他鎖は既に消えている。** arm1 shard-0 の `group_to_workers` は `real-repo` を
  40 worker へ分散している。2026-08-26 13:19 の commit「受入の real-repo 排他鎖を資源別 RW lock へ
  細分化する」が効いており、a1k2 (2026-08-26 の前 wave) が測った鎖 222.68 秒は**その前**の値である。

## 律速はどこへ移ったか

**最長単体テストである。**

| | arm1 (K=2) | arm2 (K=3) |
|---|---|---|
| 最長単体 | 165.17 秒 `test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications` | 100.32 秒 `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` |
| 上位 15 node の合計 | 2133.6 秒 (総和の 12.8%) | 1302.9 秒 (総和の 12.0%) |

K=3 の wall 160.92 秒は **最長単体 100.32 秒 + 残差 59.22 秒 = 159.5 秒** でほぼ説明できる。
すなわち K=3 で既に単体の床に達しており、K を上げる余地は単体を速くしない限り無い。
`tools/run_tests.py` の受理値が `{1,2,3}` に閉じていることと物理的な頭打ちが一致している。

重い node の file 別合計 (arm1、上位 8)。

| 直列合計 | file |
|---|---|
| 1926.1 秒 | `orchestrator/tests/test_s8b_floor_campaign.py` |
| 1738.7 秒 | `orchestrator/tests/test_s8b_oracle_driver.py` |
| 1107.9 秒 | `orchestrator/tests/test_t126_pegasus_tools.py` |
| 954.8 秒 | `orchestrator/tests/test_trial_registry.py` |
| 842.5 秒 | `orchestrator/tests/test_autonomous_trial_completeness.py` |
| 791.8 秒 | `orchestrator/tests/test_s8b_oracle_report.py` |
| 734.0 秒 | `orchestrator/tests/test_s8b_ratified_verify.py` |
| 550.2 秒 | `orchestrator/tests/test_paper_story_a1_paired.py` |

## 残る直列 group

arm1 の `group_to_workers` から。`real-repo` を除く 3 group はいずれも 1 worker 直列のままである。

| group | arm1 の最遅 worker | arm2 の最遅 worker |
|---|---|---|
| `s8c-preregistration-candidate` | 170.40 秒 | 96.64 秒 |
| `s8c-predicate-snapshot` | 166.49 秒 | 74.18 秒 |
| `dev-waves-runtime` | 小さい | 小さい |

K=3 では `s8c-preregistration-candidate` の 96.64 秒が makespan を決める shard-0 の
最遅 worker 101.70 秒を下回るので、**この群を割っても wall は動かない**。

## 残差 (固定費) は定数ではない

残差 = pytest wall − 最遅 worker。worker ごとの collection・起動・idle と finalization を含む。

- arm1: 73.53 / 54.73 秒。arm2: 59.22 / 49.04 / 49.56 秒。
- 前 wave の観測は 84.61 / 58.98 秒、その前は 39.2 秒。**K でも走でも動く。**
- K=3 到達後は wall 160.92 秒の 36.8% を占め、K を上げても縮まないので次の支配項になる。

## 親の live 実測が捕まえた偽緑

段 5 の実装は `_acceptance_launcher_environment()` の中で
`from orchestrator.campaign import site_policy` を行っていた。しかし
`python3 <repo>/tools/dev_wave_wait.py` という実際の起動形では `sys.path[0]` が `<repo>/tools`
になり cwd は `sys.path` に入らないため、この import は解決しない。

親が同じ `sys.path` (cwd を除く) を再現して `_acceptance_launcher_environment()` を直接呼んだ
ところ `ModuleNotFoundError` で戻り値が `None` になり、**機構が一度も発火しない**ことが確定した。

追加テスト 5 本はいずれも `site_policy.current_site` を monkeypatch しており、pytest process では
repo root が `sys.path` にあるため production の解決経路を 1 度も通らない。すなわち
**production が壊れていてもテストは緑**だった。

修正は house 作法どおり `__file__` から repo root を解決して `sys.path` へ入れる 1 箇所と、
**script 実行と同じ `sys.path` を持つ subprocess を起動して注入を確かめる検査**の追加である。
変異 `m09` (その `sys.path` 追加を消す) を殺すのはこの検査 1 本だけで、他 8 本は素通りする。

## 変異 matrix

baseline = PASSED (rc=0、88.86 秒)。9 変異すべて KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0。対象 commit は `c05f389509e97488984ca2fcb31fa49596413d5e`、spec sha256 は `254214f27863d47dcb2e488fb895b775abf1795787eab5b7e46765fa59bd1c7b`。
probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本登録し直す DW-M07 の手順に従った。

| id | 変異 | 殺した node 数 |
|---|---|---|
| m01 | 注入を丸ごと落とす | 3 |
| m02 | 定数を `"3"` から `"2"` へ | 4 |
| m03 | 定数を受理外の `"4"` へ | 4 |
| m04 | site gate を恒真化 | 2 |
| m05 | site gate を恒偽化 | 3 |
| m06 | 既存環境の継承を落とす | 1 |
| m07 | queue gate を恒真化 | 3 |
| m08 | 空文字を未指定として扱わない | 1 |
| m09 | repo root の `sys.path` 追加を落とす | 1 |

m02 と m09 は段 6 の fix より前には 1 node も殺せなかった。前者はテストが期待値に production
定数を使っていたため、後者は monkeypatch が production の解決経路を迂回していたためである。

## 一次資料

- 計測 log: `arm1-k2.log` / `arm2-k3.log` (wave job directory)。
- shard session root: `/work/1/SFC/tanab/.izanagi-acceptance-shards/b18df44fd3a810ead112742e1de18a20`
  (K=2) と `/work/1/SFC/tanab/.izanagi-acceptance-shards/40fc419debb24c1345a03f83238d0d98` (K=3)。
  各 shard の `report.json` (`worker_occupancy` / `group_to_workers`) と `junit.xml`。
- 変異 matrix: `mutation-final-out.json` と `mutation-final-spec.json` (同ディレクトリ)。
- 逐語は `verbatim/`。
