## 対応表

指定原本を確認したところ、実在する見出しは `RA-1〜RA-8`、`RB-1〜RB-6` までである。`RA-9 / RB-7 / RB-8` は原本に存在せず、裁定もないため判定を捏造しない。

| 所見 | 判定 | file:line 根拠 | 残余 |
|---|---|---|---|
| RA-1 | closed | `p3_s4_loop_trigger_gating.py:520-540,583-604` | 公開入口から `site` は消え、実 site を各入口で一度だけ解決する。 |
| RA-2 | partial | `loop.py:54-110,120-121`; `pipeline.py:486-513,579-620` | `run_campaign` は attestation するが、Pegasus 用 cfg identity と `allow_resume=False` を強制しない。さらに `pipeline.evaluate` 直呼びは contract だけで attestation を迂回できる。 |
| RA-3 | closed | `p3_s4_loop_trigger_gating.py:309-326,532-540,599-606` | no-resume は lock/state/WAL/provenance、reject、入口 stop の書込み前に移った。単一 process の競合取得は親裁定で保留された S5 の範囲。 |
| RA-4 | partial | `p3_autonomous_workload_trial.py:651-677,769-777`; `s8a_trigger_coverage.py:108-143`; `screening_driver.py:128-155` | 裁定で列挙された多くの入口は閉じたが、wrapper/partial screening と未列挙 raw legacy driver が残る（RF-1、RF-2）。 |
| RA-5 | partial | `buildcache.py:347-379,506-530,581-595` | 配列化、空要素/cwd、明示相対 path は修正済み。しかし ambient 値は identity 時に正準化するだけで、subprocess には元の可変 env/symlink を継承するため snapshot が一致しない。 |
| RA-6 | 対象外 (裁定で保留) | `s4-adjudication.md:40`; `buildcache.py:527-530`; `pipeline.py:609-618` | 依存 bytes/content manifest の束縛は未実装。親裁定どおり path 束縛まで。 |
| RA-7 | closed | `p3_s4_loop_trigger_gating.py:444-452,724-728,760-765` | authoritative `layout_root` を返し、CLI は元 cfg から再計算しない。 |
| RA-8 | partial | `test_p3_s4_loop_trigger_gating.py:443-482`; `test_buildcache_v2.py:257-389,513-518` | exact manifest の M7/M8 重複は除去されたが、M5 は実 attestation sink を撃たず、M14 は無効入力の後段例外で赤になる。M2/M8にも帰属不成立が残る。 |
| RA-9 | 判定不能（原本欠番） | `s6-revA.md:158,201` | 原本最後の所見は RA-8。裁定対象も存在しない。 |
| RB-1 | closed | `p3_s4_loop_trigger_gating.py:444-452,724-728,760-765` | CLI・fixture とも返却された Pegasus layout のみ参照する。 |
| RB-2 | closed | `p3_autonomous_workload_trial.py:651-677,769-777,1017-1034,1122-1128` | `_run_workload`、`_finish_trial`、`run_trial`、CLI で actual OTHER 以外の build を provider/artifact より前に拒否する。 |
| RB-3 | closed | `p3_s4_loop_trigger_gating.py:520-540,583-604` | trigger 公開 API の caller 注入 `site` は消滅した。 |
| RB-4 | partial | `site_policy.py:74-81`; `buildcache.py:701-719,852-876`; `pipeline.py:208-235` | 標準 non-screening `run_campaign` は fresh/cache-hit とも止まるが、screening の bench-first と raw legacy subprocess は覆わない。 |
| RB-5 | 対象外 (裁定で保留) | `s4-adjudication.md:46`; `critic/digest.py:38-75,192-210,478-489` | critic schema は env を保持しないまま。RF-1 を閉じない限り「env 分離で混ざらない」という保留前提も成立しない。 |
| RB-6 | partial | `test_p3_s4_loop_trigger_gating.py:545-609`; `test_p3_autonomous_workload_trial.py:273-386`; `test_screening_driver.py:139-165` | exact ID、CLI layout、8c lower entry、OTHER build 正例は追加済み。一方 M14 fixture と `_REAL_EVALUATE` 逃げ道は実 sink を代表しない。 |
| RB-7 | 判定不能（原本欠番） | `s6-revB.md:93,133` | 原本最後の所見は RB-6。 |
| RB-8 | 判定不能（原本欠番） | `s6-revB.md:93,133` | 同上。 |

## 新規所見

### [RF-1] 関数 identity と contract dataclass が実行能力になっている

深刻度: **BLOCKER**

file:line: `screening_driver.py:128-155`、`pipeline.py:262-315,486-513,579-620,759-793`、`buildcache.py:701-719,852-876`、`test_screening_driver.py:139-165`

失敗シナリオ:

`evaluate is _REAL_EVALUATE` は wrapper、decorator、`functools.partial` の全てで偽になる。現テスト自身が COMPUTE を設定したうえで fake evaluator に差し替え、この逃げ道を正例として固定している。

- 単なる wrapper でも、legacy cache hit 後は build 防壁を通らず、screening の `_run_bench` が `_run_trace` 防壁より先に実行される。
- `partial(_REAL_EVALUATE, env_contract=lookup("pegasus"))` なら fresh build も通る。非 qualification の `pipeline.evaluate` は contract と `env_tag`・clock・NUMA・receipt を照合せず、`_run` / `_run_trace` は exact dataclass があるだけで防壁を解除する。
- `run_campaign` 直呼びも、登録 contract を渡せば任意の cfg で Pegasus 実測でき、campaign env 分離と no-resume を強制しない。

成果物影響: Pegasus throughput が `linux-baremetal` の `BENCH_DONE` / `COMMIT` に入り、screening の棄却集合、certified 選択、critic 入力を変更できる。

提案: legacy screening は evaluator identity に関係なく COMPUTE を拒否し、fake 配線テストは OTHER か副作用のない専用 seam で行う。`pipeline.evaluate` の COMPUTE 実行は、contract オブジェクトではなく attestation receipt・actual site・campaign identity・実行値に束縛された authorization を要求する。bench 防壁も `_run_bench` の subprocess 前へ置く。

### [RF-2] sink 方式が未列挙の legacy 実測 driver を覆っていない

深刻度: **BLOCKER**

file:line: `site_policy.py:74-86`、以下の各実行・出力箇所。

独立 grep で、防壁を通らず実計測へ到達できる呼び口は次のとおり。

- `s1_verify_extime_calibration.py:241-250,314-341,419-425` — legacy cache hit 後の trace run。
- `s2_verify_calibration.py:103-145,242-280,295-318,359-364` — cache hit と direct CMake の双方。
- `s3_lock_coverage.py:73-85,135-165,185-208,243-247` — 同上。
- `s5_permutation_coverage.py:69-81,131-161,181-203,233-237` — 同上。
- `between_run_floor.py:69-90,150-166` — cache hit 後に `measure_point`。
- `backoff_profile.py:97-139,183-219` — cache hit 後に `perf record`。
- `backoff_overthrottle.py:60-85` — cache hit 後に `run_once`。これは永続成果物を直接書かないため、単独なら backlog。

`refuses_heavy_work()` は COMPUTE を受理し、legacy `buildcache.build()` は cache hit なら `_run` を通らない。s2/s3/s5 の direct CMake は fresh でも通る。

成果物影響: Pegasus 値で `output/env/linux-baremetal` の calibration/profile を上書きでき、screening floor、verify extime、機械 gate、レポート参照値と受理集合が変わる。

提案: CCBench 実行の共通最下層に「legacy default は actual COMPUTE 拒否、Pegasus-aware caller は検証済み authorization 必須」の契約を置く。direct CMake/trace driver も同じ sink を使わせ、M14 対象へ追加する。

## 変異の単一理由性

ここでの「可」は静的に本走可能という意味であり、kill 実測済みではない。

| 変異 | 結果 | 確認 |
|---|---|---|
| M1 | 可 | `p3_s4_loop_trigger_gating.py:285-296`。先行拒否なし。縮小すれば compute admission 正例が同一理由で落ちる。 |
| M2 | **不可** | LOGIN を admission set に足しても `_SITE_ENV_TAGS` に key がなく、後段 `KeyError` で依然拒否される。受理集合が拡大しない等価変異。map を唯一の admission 正本にして LOGIN→contract を足す変異へ再照準する。 |
| M3 | partial | `p3_s4_loop_trigger_gating.py:77-80,299-306`。同じ map が contract tag と campaign ID の双方を変え、M3 と M11 の赤理由が重なる。二つを一つの「site→env binding」変異へ統合するか selector を分離する。 |
| M4 | 可 | `loop.py:78-92`; `test_campaign.py:2638-2692`。正しい contract は先行拒否されず、attestation 呼出し削除は順序検査に帰属する。 |
| M5 | **不可** | `test_p3_s4_loop_trigger_gating.py:637-652` は実 `attest_and_build_receipt` を raise させず、`T.run_campaign` 全体を偽物にしている。実 sink が例外を握り潰す mutant は生存する。`loop.execution_guard.attest_and_build_receipt` を raise させ、layout/evaluate poison 未到達を検査する node へ再照準する。 |
| M6 | **可** | `p3_s4_loop_trigger_gating.py:309-326,532-540,599-606`。state、全 reject、WAL-only tail、入口 stop を書込み前に捕える (`test_p3_s4_loop_trigger_gating.py:655-698,1350-1371`)。先行 freshness gate は call graph 上にない。 |
| M7 | 可 | `buildcache.py:506-530`; `test_buildcache_v2.py:257-268`。actual site 以外の先行拒否は fixture で neutral。専用 cache-miss 理由のみ。 |
| M8 | **不可** | `_v2_identity` から field を落とすと explicit M8 に加え ambient M9、injectivity、relative-prefix manifest も赤になる。explicit branch 固有 anchor へ再照準するか M8/M9 を一つの prefix-binding 変異へ統合する。 |
| M9 | 可 | `buildcache.py:513-516`; `test_buildcache_v2.py:289-328`。ambient 読取り削除は ambient identity 不変に帰属する。ただし実 env snapshot 不一致は RA-5 の残余。 |
| M10 | 可 | `buildcache.py:386-400,576-595`; `test_buildcache_v2.py:330-381`。argv 除去は明示 prefix の subprocess 条件だけを変える。 |
| M11 | 可 | `p3_s4_loop_trigger_gating.py:299-306`; `test_p3_s4_loop_trigger_gating.py:545-558`。env 分離削除で exact campaign ID が一致する。M3 と同時変異にはしないこと。 |
| M12 | 可 | `loop.py:163-170`、`pipeline.py:539-547,593-605`; `test_campaign.py:1439-1458,2584-2635`。二つの call site は別 mutant として各専用 node に照準できる。 |
| M13 | 可 | `buildcache.py:506-530`; `test_buildcache_v2.py:384-393`。caller `site` は identity 前の拒否に使われず、注入値使用で digest 差だけが出る。 |
| M14 | **不可** | `test_p3_s4_loop_trigger_gating.py:443-482` は `None` や不在 binary を渡す。防壁削除後の赤は実 subprocess poison ではなく `AttributeError` / `TypeError` / FileNotFound、または別の重複防壁である。fix3 が挙げる screening の `ensure_resumable_wal(None,None)` も同じ偽 kill。各 authoritative 最下層を valid fixture＋subprocess/provider/WAL poison で個別変異し、wrapper、partial、fresh、cache-hit、bench-first を含めて再登録する。 |

## GO / NO-GO

**NO-GO。変異本走にも commit にも進めない。**

- RF-1 は actual measurement と certified WAL まで到達可能な BLOCKER。
- RF-2 により B-f の「Pegasus 値を Linux 台帳へ入れない」が全 legacy caller では成立しない。
- RA-2 と RA-5 は依然 partial。
- M2、M5、M8、M14 は事前登録条件を満たさず、本走しても有効な mutation matrix にならない。
- 親提示の `450 passed / 9 skipped / rc=0` は回帰実測として受領したが、上記経路と mutation kill を証明しない。本レビューでは pytest を実行していない。

## 総括

- caller 注入 `site`、CLI layout、8c 下位入口、逐次 no-resume は修正された。
- 防壁を sink へ移した結果、標準 non-screening 経路は fresh/cache-hit とも閉じた。
- しかし screening は関数 identity に依存し、wrapper/partial と bench-first cache hit で抜ける。
- contract dataclass は authorization ではなく、直 `pipeline.evaluate` が attestation を迂回する。
- 未列挙 legacy driver は Pegasus 値を Linux calibration/profile へ書ける。
- M6 は本走可能だが、M14 は依然 behavioral mutation になっていない。
- 原本には RA-9 / RB-7 / RB-8 が存在しない。