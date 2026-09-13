# [T-2515] [T-2534] BACKOFF_FIXED=-1 の取り下げと rr95 / rr5 の較正取得

裁定 D1936 項 6 の実装と、その後に投入した認定較正 2 条件の実測記録。
先行資料は `output/insights/2026-09-10/t2515-rr95-rr5-calibration/README.md` (当時の拒否実測)。

## 何をしたか

`tools/pegasus/certify_calibration.sh` から、供給されていない `BACKOFF_FIXED=-1` の
configure argv と、その専用条件関門 (`run_condition_gate` の定義・呼び出し・付随コメント) を
**同時に**取り下げた。gate だけを消して宣言を残す形にはしていない。
shell の独立表 (D1863) を parse する test の該当期待値、`_protocol_shell_observation` と
`_calibrate_interpreter_fragment` の切り出し、`tools/pegasus/README.md` の説明を整合させた。
予約式コメントから `condition_gate(300)` を除き、合計を receipt 側と同じ 6610 へ揃えた。

実装 commit = `b3c62ee7fe46083a26209ddd0bf4318ee9da47c1`。
実測記録 commit = `931eee3c3b7b3122af020a96e675bdf3628b5644` (変異検査はこの commit へ束縛)。

## 裁定前提の実測

- pinned CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` に `BACKOFF_FIXED` は **0 件**
  (`external/ccbench` 全走、`third_party` と `.git` を除外、grep rc=1)。
  `CCBENCH_BACK_OFF` は `external/ccbench/cmake/Options.cmake:20` に実在する。
- 着手時点の registered calibration は 3 件ともに `workload.ycsb_rratio=50`。rr95 / rr5 は 0 件。
- `tools/pegasus/certify_calibration.sh` は main 側 `tools/pegasus/admission_registry.json`
  (blob `fcc032092ab686cbc06d255cc1395fcc4cf964f3`) に `class=dispatch-required` で登録済み。
  新規 Pegasus 実行体ではないので F660 は発火しない。
- submit / job 両 shell の rratio 許可集合は既に `{5,20,50,80,95}` であり、追加は不要だった。
- `SPACES['silo'].axes` は `{BACK_OFF, NO_WAIT_LOCKING_IN_VALIDATION, NO_WAIT_OF_TICTOC, WAL}` で
  `BACKOFF_FIXED` を含まない。撤去後は独立表の除外が `{"TRACE"}` だけになり mocc / tictoc と同形。

## 較正の実測 (2 条件を同時投入)

commit `b3c62ee7f` の worktree から `tools/pegasus/submit_certify.sh` で同時に投入した。
**両 job とも条件関門で止まらず configure / build / calibrate まで到達した。**
撤去前の 2 巡目 (988706 / 988708) は、どちらもここへ到達する前に専用 gate で停止していた。

| 条件 | request | node | 判定 | records | LLC miss | noise floor CV |
|---|---|---|---|---:|---:|---:|
| rr95 (read-heavy) | `995805.nqsv` | bnode027 | **accepted** | 1,000,000 | 6.023% | 0.425% |
| rr5 (write-heavy) | `995806.nqsv` | bnode028 | **rejected** | 1,000,000 | 0.364% | 1.353% |

共通条件: threads 48 / cpuset 48 / HT off、`ycsb_zipf_skew=0.9`、`ycsb_rmw=0`、
`clocks_per_us=2100` (TSC 実測)、CCBench `511c9538` を pinned-clean、
L3 総量 110,100,480 bytes、`l3_multiple=4.0`、`elapstim_req_s=7200`、queue `gen_S`。

### rr95 — accepted

成果物 = `output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json`。

- `quality.status = accepted`、`workload.ycsb_rratio = 95`
- `genome = silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`
- acquisition receipt の `ccbench.build_argv` に載る CCBENCH define は
  `-DCCBENCH_TRACE=0` / `-DCCBENCH_BACK_OFF=0` / `-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1` /
  `-DCCBENCH_NO_WAIT_OF_TICTOC=0` / `-DCCBENCH_WAL=0` の **5 件ちょうど**。
  撤回した `BACKOFF_FIXED` は argv にも genome にも無い。
- `binary_sha256 = ffba3dd6b5a8f188352c59e9a9c6f93d777d275bbb078a2403cbc2bbedaf7dc5`
- `job_script_sha256 = 08bbc498e36d1c9361d8f421d3dfce22cff1efc3c2553d22da6c773bc7e754ad`
- 飽和点なし → D15 の下限基準で N=1,000,000 を採用 (working set 518 MB = L3 の 4.93 倍)。
  採用点の miss 率 6.023% は cache floor 0.50% を大きく上回るため `cache_floor_warning=false`。

### rr5 — rejected (`selection-invalid`)

記録 = `output/env/pegasus/calibration/attempts/0_995806.nqsv/`。registered へは昇格していない。

拒否の連鎖は次のとおりで、**撤回した `BACKOFF_FIXED` とは無関係である**。

1. 飽和点が無いので D15 の下限基準が働き、`maxrss ≥ 4 × L3` を満たす最小 N = 1,000,000 を選ぶ
   (working set 517 MB = L3 の 4.93 倍)。
2. その採用点の LLC miss 率が **0.364%** で、`orchestrator/calibrator/analyze.py` の
   `DEFAULT_CACHE_FLOOR = 0.005` (0.50%) を下回る → `cache_floor_warning = true`。
3. `orchestrator/calibrator/report.py` が `cache_floor_warning` を `selection-invalid` に落とし、
   `quality.status = rejected` になる。

観測した sweep 系列 (rr5):

| records | miss_rate | Δ | maxrss |
|---:|---:|---:|---:|
| 1,000,000 | 0.364% | | 517 MB |
| 2,000,000 | 1.392% | +1.027pp | 1,023 MB |
| 4,000,000 | 4.762% | +3.370pp | 1,958 MB |

同じ node 世代の rr95 は同じ N で 6.023% だった。**書き込み主体 (rratio=5) では、
working set の代理指標 (maxrss) と実際の LLC miss 率が食い違う**というのが今回の新しい観測である。

この拒否は絶対規律 4 の「小さすぎると many-core の cache 競合が再現されず測定が楽観的に歪む」
側の防壁であり、**迂回していない**。`l3_multiple` を 4 から上げれば N=2,000,000 が選ばれて
miss 率 1.392% で通ることは上表から読めるが、**通る値を結果を見てから選ぶのは規律 2 が禁じる
正しさゲートの事後緩和**なので採らなかった。扱いはユーザー裁定へ返す (下記)。

## 共通の正しさ検査について

`orchestrator/tests/test_ccbench_spawn_sites.py` の `_shell_gate_coverage` と、それを使う
cross-product 検査は 1 文字も変更していない。この検査の責務は
「build sink の argv に patch 由来 macro があれば条件関門を要求する」ことである。

- define と gate を**同時に**撤去すると、当該 macro が source inventory から消えるため
  `proven-unreachable` として通る。検査が空集合になるのではなく、受理条件を満たす。
- **gate だけ消して define を残すと赤になる。** 裁定が禁じた向きは機械で捕まる。
  これは下の変異 M1 が実測した (`test_define_sink_cross_product_has_no_unreviewed_ungated_member`
  を含む 7 node で KILLED)。
- **define だけ消して gate を残しても赤にならない。** gate 内の macro token が inventory に残り
  先行呼び出しで `covered` になるためである。この非対称は穴ではなく責務の外であり、
  本 wave では現物レビュー 2 本と変異で整合を確かめた。新しい gate は足していない。

## 変異検査

`tools/mutation_harness.py` を固定 commit `931eee3c3` へ束縛して走らせた。
probe を全件 SURVIVED 期待で先に流し、観測 node から本走の期待 node 完全集合を機械生成した
(probe は 6 件すべて MISMATCH = 実際には KILLED。初回記録も `mutation-report.probe.json.gz` に残す)。

**本走: baseline PASSED (失敗 node 0)、6/6 KILLED、期待 node 完全一致、wrapper rc=0。**

| ID | 変異 | 失敗 node 数 | 単一理由性 |
|---|---|---:|---|
| M1 | silo の configure argv へ `-DCCBENCH_BACKOFF_FIXED=-1` を戻す | 7 | **過剰決定**。独立表 3 本 + spawn-sites 3 本 + configure argv が同時に拒否する。**冗長 gate として単独変異の証拠から外す** |
| M2 | `-DCCBENCH_BACK_OFF=0` → `=1` | 2 | 独立表の exact 値検査。`BACK_OFF=1` は `SPACES` 内なので軸検査は通る |
| M3 | `-DCCBENCH_WAL=0` を削除 | 4 | 軸の脱落 |
| M4 | test の exact 表から silo の `"BACK_OFF": "0"` を削除 | **1** | `test_certify_shell_protocol_defines_match_exact_values` が**この性質の唯一の歯**であることの実測 |
| M5 | `TMPDIR` の `${PBS_JOBID//:/_}` を `${PBS_JOBID}` へ | 2 | 逐語 pin を 1 行削った test の**残りに歯があること**の裏取り |
| M6 | README の撤回説明を旧文へ戻す | 1 | **diagnostic sensitivity pin として別枠記録**。受理集合を変えない |

生の spec と report は本 directory の `mutation-spec.*.json` / `mutation-report.*` を正本とする。

## 当時の拒否の読み方

2026-09-09〜10 の `supply-effectuation / configure-failed` と
`runtime-meaning / materialized-branch-invalid` は、「直った」のではなく「要求しなくなった」。
過去の拒否記録は拒否のまま残し、緑へ読み替えない。

## ユーザー裁定へ返す項目

1. **rr5 の cache floor 拒否。** D15 の下限基準 (`l3_multiple=4`) が選ぶ N と、
   `analyze.py` の cache floor 0.50% が、write-heavy では両立しない。
   選択規則を変える (例: 下限基準に miss 率の下限も課す) のは正しさゲートの受理集合の変更であり、
   結果を見た後で AI が決めてよいものではない。上の実測値を添えて裁定へ返す。
2. **予約式 6610 は完走保証ではない。** 段 3 のレンズ 2 が、shell 内の直列 timeout の総和が
   式中の build 見積り 1080 秒を大きく超えることを指摘した。本 wave の変更で生じた問題ではなく、
   既存の T-2563 の時間不整合と同じ面である。

## 検査

- 焦点走 (親の実走、実装 commit 時点): `test_pegasus_calibration_workload.py` 68 passed、
  `test_pegasus_tools.py` 69 passed。
  consumer 4 file (`test_ccbench_spawn_sites.py` / `test_official_perf_closure.py` /
  `test_pegasus_floor_tools.py` / `test_calibrator_certify.py`) は 276 passed / 1 failed。
  赤は `test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` で、
  `os.write` を 5 秒眠らせて割り込みを見る負荷依存の test。差分から到達できない面であり、
  単独再走で 3 passed と再現しなかったので変更に帰属しない。
- local main `29c5fb594` 取り込み後の焦点再走: 3 file で 184 passed。
  incoming 側が `test_ccbench_spawn_sites.py` を変えているため実走で確かめた。
- `tools/check_docs.py` rc=0、`tools/check_codex_agents.py` rc=0、
  `tools/check_ai_provenance.py` 全史 rc=0 (9,713 件、新規違反なし)。
- 段 3 敵対相談 2 本、段 6 敵対レビュー 2 本。実装への must-fix は 0 件。
  段 3 で見つかった最も重い取り残しは、削除する関門の**中身の 1 行**を逐語 pin していた
  `orchestrator/tests/test_pegasus_tools.py` の assert で、識別子検索には掛からないものだった。
- 受入全走の結果は worklog に記す。

## 所在

- 親 brief / 裁定 / 子成果物 / 変異 spec:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2515-t2534-backoff-withdraw/`
- 較正の生証拠: `output/env/pegasus/calibration/job-staging/0:995805.nqsv/`、同 `0:995806.nqsv/`
- 試行記録: `output/env/pegasus/calibration/attempts/0_995805.nqsv/`、同 `0_995806.nqsv/`
