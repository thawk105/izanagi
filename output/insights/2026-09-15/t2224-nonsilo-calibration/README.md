# [T-2224] 非 silo (mocc / tictoc) の認定較正 record 取得

引数化済みの認定 launcher を使って、非 silo protocol の認定較正 record を実測で取った記録。
**較正であって性能選定ではない。** within-run floor の本走は embargo 中であり、本 wave は触っていない。

先行資料:
- `output/insights/2026-09-10/t2535-certify-offline-fetch/README.md` (offline 供給の配線と mocc/rr50 初取得)
- `output/insights/2026-09-13/t2515-t2534-backoff-withdraw/README.md` (BACKOFF_FIXED 撤回と silo rr95/rr5)

## 1. 何をしたか

コードもテストも 1 行も変えていない。既存の `tools/pegasus/submit_certify.sh` を
`--protocol` / `--rratio` で 3 通り呼び、3 条件を別ノードへ同時に流した。

| 条件 | request | node | 判定 | 成果物 |
|---|---|---|---|---|
| tictoc / rr50 | `998860.nqsv` | bnode093 | **accepted** | `calibration-9b49335d02ad4d2e.json` |
| tictoc / rr95 | `998863.nqsv` | bnode103 | **accepted** | `calibration-cb98513996e5ae35.json` |
| mocc / rr95 | `998864.nqsv` | bnode016 | **accepted** | `calibration-b3329d93417c76ad.json` |

**tictoc の測定は 0 件から 2 件になった。** mocc は rr50 の 1 件に rr95 が加わって 2 件になった。

共通条件: threads 48 / cpuset_size 48 / HT off、`ycsb_zipf_skew=0.9`、`ycsb_rmw=0`、
`clocks_per_us=2100`、CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` を `pinned_clean=true`、
L3 総量 110,100,480 bytes、`l3_multiple=4.0`、queue `gen_S`、`elapstim_req_s=7200`、
`job_script_sha256=08bbc498e36d1c9361d8f421d3dfce22cff1efc3c2553d22da6c773bc7e754ad`
(2026-09-14 の silo rr95 取得と同一 bytes の launcher)。

## 2. 測定値

| 条件 | records | 採用点の LLC miss | working set / L3 | within-run CV | 雑音床 mean (tps) | stdev | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| tictoc / rr50 | 1,000,000 | 7.969% | 4.934 | 2.2160% | 1,360,228.4 | 30,142.30 | 10 |
| tictoc / rr95 | 1,000,000 | 9.557% | 4.931 | 0.8336% | 4,585,960.8 | 38,227.24 | 10 |
| mocc / rr95 | 1,000,000 | 17.008% | 6.094 | 1.7204% | 2,382,335.7 | 40,985.06 | 10 |

3 条件とも `saturated=false` / `lower_bound_selected=true` で、D15 の下限基準
(`maxrss >= 4 x L3` を満たす最小 N) が働いて N=1,000,000 を選んだ。
採用点の miss 率はいずれも cache floor 0.50% を大きく上回り `cache_floor_warning=false`。
`high_variance=false`。`scale_sensitivity` は 3 件とも `not-measured`。

所要は job 側の `scheduler_started_epoch` から `completed_epoch` まで 184 / 177 / 238 秒。
要求枠 7200 秒に対する実所要であって、**時間式の最大経路を包含した証明ではない** (D1971 の限界を継承)。

## 3. genome が build の忠実な写像であること (D1864)

取得受領証 `acquisition_receipt.ccbench.build_argv` に載る `-DCCBENCH_*` の件数と中身を数えた。

- **tictoc = ちょうど 6 件**: `TRACE=0` / `BACK_OFF=1` / `NO_WAIT_LOCKING_IN_VALIDATION=1` /
  `NO_WAIT_OF_TICTOC=0` / `PREEMPTIVE_ABORTS=1` / `TIMESTAMP_HISTORY=1`。
  genome = `tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1`。
- **mocc = ちょうど 4 件**: `TRACE=0` / `BACK_OFF=1` / `KEY_SORT=0` / `TEMPERATURE_RESET_OPT=1`。
  genome = `mocc|BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`。
- 撤回済みの `BACKOFF_FIXED` は argv にも genome にも現れない。

投入前に静的にも確かめた。tictoc の 5 軸はすべてコンパイラへ届く:
`NO_WAIT_LOCKING_IN_VALIDATION` / `NO_WAIT_OF_TICTOC` / `PREEMPTIVE_ABORTS` / `TIMESTAMP_HISTORY` は
`external/ccbench/cc/tictoc/CMakeLists.txt` の `OPTIONS`、`BACK_OFF` は
`external/ccbench/cmake/Options.cmake:63` の universal definitions 経由。
`orchestrator/campaign/genome.py` の `TICTOC_SPACE.axes` はこの 5 軸と完全一致し、
制約 `_tictoc_no_wait_not_both` は (NWLIV=1, NWOT=0) で充足する。
cicada で起きた「軸名と cache 変数の食い違い」(D1864 決定 1) は tictoc では起きない。

正しさ側: job の trace 分離検査 (binary symbol table に `izanagi_trace` が無いこと) を 3 件とも通過し、
`calibrate_rc=0`。`CCBENCH_TRACE=0` は 3 条件すべての argv にある。

## 4. 依頼の前提が実測で覆ったこと

依頼文は「認定較正 record は 0 件のまま」としていたが、着手時点で **registered は 4 件**あった。

| 着手時点の registered | protocol | workload | 出所 |
|---|---|---|---|
| `calibration-753f535a8d024727.json` | genome 無記録 (legacy→silo 仮定、D1374) | rr50 | 2026-08-02 |
| `calibration-94a4b79fa31bba3c.json` | 同上 | rr50 | 2026-08-06 |
| `calibration-449d0ad22f13e366.json` | **mocc** | rr50 | 2026-09-10 ([T-2535]、989271) |
| `calibration-5c836a22eff9ab40.json` | silo | rr95 | 2026-09-14 ([T-2534]、995805) |

**0 件だったのは tictoc だけ**である。この差は本 wave の scope を変えた —
「非 silo を 0 から立ち上げる」ではなく「silo が既に持つ workload 点 (rr50 / rr95) に非 silo を追いつかせる」。

依頼が挙げた 2 つの blocker はどちらも着地済みだった ([T-2535] が offline FetchContent 供給、
[T-2534] が `BACKOFF_FIXED=-1` の取り下げ)。活動そのものを止める裁定も無い —
D1936 項39 の後置は cicada に限定されており、mocc / tictoc は射程外である。

## 5. 投入前に見つけた罠 — 同一キーの重複は layer3 を hard error にする

`orchestrator/campaign/layer3_report.py` の floor 照合は、一致キー
`(protocol, records, threads, workload)` で candidate を絞り、
**一致が 2 件以上あると `Layer3ReportError("一致する <kind> calibration floor が複数ある")` を投げる。**

したがって **mocc/rr50 をもう 1 本取ってはいけない**。本 wave が rr50 の再取得を避け、
mocc は rr95 だけにしたのはこのためである。取得した 3 件のキーは既存 4 件のいずれとも重複しない。

**既存の重複は本 wave が作ったものではない。** legacy 2 件 (753f / 94a4) は
`(silo, 1000000, 48, rr50)` が完全に同じである。この衝突は
`SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS` に載る 753f が contract pin のときだけ
within-run から除外されて解ける。**本 wave はこの機構に触れていないし、直してもいない。**

## 6. 運用上の実測

- **third-party staging は gitignore 対象で、主 checkout にも全 worktree にも存在しなかった。**
  `submit_certify.sh` は hydrate を起動しない (構造検査だけ) ので、投入前に
  `fetch_third_party.py hydrate --staging-root <worktree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src`
  を親が明示的に走らせる必要がある。永続 cache は `/work/1/SFC/tanab/izanagi-thirdparty-cache`。
  hydrate した 3 依存の pin は masstree `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` /
  mimalloc `02a2f5df9d7d46d30263b83832eebeeab62dc5fe` /
  googletest `f8d7d77c06936315286eb55f8de22cd23c188571`。
- **投入中は `output/` 配下以外を書けない。** job 冒頭が
  `git status --porcelain --untracked-files=all -- . ':(exclude)output'` を再照合し、
  dirty なら rc=2 `source_identity` で止まる。本 wave は 3 本の投入が終わるまで docs を書かなかった。
- **login node 負荷 173 (48 コア) で `tools/dev_wave_submodule_init.py` が rc=1 になった。**
  中身は `_GIT_TIMEOUT_S = 30` の deadline 超過で、submodule 側の欠陥ではない。
  同じ argv (`git -c protocol.file.allow=always submodule update --init --recursive --no-fetch`) を
  打ち切らずに走らせて rc=0。`git worktree add` も同じ負荷下で 13 分かかった。
- 3 条件は別ノード (bnode093 / bnode103 / bnode016) へ割れた。直列化していない。

## 7. 主張しないこと

- **性能を比較していない。** 取得したのは物差し (records 飽和点と within-run 雑音床) であって
  throughput の優劣ではない。3 protocol の雑音床 mean を横に並べても、
  それは別 workload・別ノードの単発測定であり性能比較ではない。
- **非 silo の within-run floor の embargo を解いていない。** 本 wave は較正取得だけに絞った。
  embargo の解除可否と floor の本走は本 wave の射程外である。
- **rr5 は取っていない。** silo/rr5 (995806) が `cache_floor_warning` 起因の `selection-invalid` で
  棄却された前例があり、本題 (非 silo の較正取得) の必要条件でもない。
- **cicada は取っていない。** D1936 項39 が Silo 合成再開の後に置いている。
- 所要 184 / 177 / 238 秒は 3 条件それぞれ 1 回の観測であって、分布でも再現性の主張でもない。

## 8. 一次資料

- registered record 3 件: `output/env/pegasus/calibration/registered/calibration-9b49335d02ad4d2e.json`、
  同 `calibration-cb98513996e5ae35.json`、同 `calibration-b3329d93417c76ad.json`
- 生証拠: `output/env/pegasus/calibration/job-staging/0:998860.nqsv/`、同 `0:998863.nqsv/`、同 `0:998864.nqsv/`
- attempt: `output/env/pegasus/calibration/attempts/0_998860.nqsv/`、同 `0_998863.nqsv/`、同 `0_998864.nqsv/`
- 投入受領証: `output/env/pegasus/calibration/attempts/submissions/<nonce>/submit-receipt.json`

binary sha256 は tictoc/rr50 = `fcde3d54ca2b7ba4540f59050343ac52f082fd1dab0c1a523df738a11f352467`、
tictoc/rr95 = `3aa47fc47c35e0f973203bd898b382b94af7f5ce898f5ab7540d3a42e0d3ab7c`、
mocc/rr95 = `c7fc2103dcaaac6e7ce26b09604aec8d7bfe6564fc1f679a80612781e1503001`。
record の sha256 は file 名の先頭 16 桁がそのまま先頭に一致する
(`9b49335d02ad4d2e...`、`cb98513996e5ae35...`、`b3329d93417c76ad...`)。
