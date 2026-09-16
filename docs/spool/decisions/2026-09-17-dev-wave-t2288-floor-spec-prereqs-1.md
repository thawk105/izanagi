---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2288-floor-spec-prereqs
seq: 1
---

## {{D:b4-floor-perf-config-approval}}. B-4 床値 spec の `perf_config` は `extime=3`・`ycsb_max_ope=10` を較正の取得構成から復元し、`reps=5` は較正出力に無い値として AI が委任の下で選んで承認する

**決定 (D1641 決定 3 の委任と [T-2288] 本 wave の依頼の下で AI が承認):** workload 別 3 spec
(`floor-pair-spec/v3`) の各 cell の `perf_config` のうち、較正成果物 (`calibration/v2`) に key が無い
3 項目を次の値で確定する。`records` は各 workload の採用較正の `saturation.records`、`threads` は 48、
`workload` は採用較正の `workload` 3 key と逐語一致させる (D1854 の exact 一致)。

- `extime = 3`。silo・t48・pegasus の accepted 較正 4 件は calibrator CLI の既定 `--extime 3`
  (`orchestrator/calibrator/cli.py` の既定値) で測られた。根拠は各 job の tracked な取得 argv
  `output/env/pegasus/calibration/job-staging/<pbs_jobid>/calibrate-argv.json` に `--extime` が無いこと。
  runner は渡された extime を `-extime=<値>` として bench へ渡す。
- `ycsb_max_ope = 10`。同じ 4 件の取得 argv の workload は 3 key (`ycsb_zipf_skew` / `ycsb_rratio` / `ycsb_rmw`)
  だけで `ycsb_max_ope` を含まず、runner の固定 flags にも無いので、較正は CCBench の既定
  `DEFINE_uint64(ycsb_max_ope, 10, …)` (`external/ccbench/include/ycsb.hh`) で走った。floor driver は
  `ycsb_max_ope` を workload に加えて明示で渡すため、較正と同じ動作点を指すには 10 を書く。
  (runner 一般がこの flag を渡せないという意味ではない — 今回の較正 argv に無い、という事実である。)
- `reps = 5`。**この値は較正出力からも取得構成からも導けない。** 較正 JSON に反復数の key は無く、calibrator は
  sweep の各点に 3 回、noise floor に 10 回を使うが、床値測定の 1 測定 (候補・参照) に採る反復数を一意に指定
  しない。`reps` は bench 1 回の flags を変えず、同じ flags の実行を繰り返す回数である (実行量・時間的標本化・
  session reducer `median/v1` に渡す標本の分布には効く)。値は、事前登録 §11.2 が 2026-09-02 から名目として置く
  「1 測定 = 5 反復 × 3 秒」、`PerfConfig` の既定 5 (`orchestrator/campaign/pipeline.py`)、D1640 の参照測定
  (5 反復) と揃え、median が実 rep を返す奇数を採る。**AI の選択であることを spec の非保証欄と本決定に残す。**
  spec 凍結前なら本決定への追記で改められる。凍結後は erratum に限る。

**理由:**
- floor driver は「校正済み動作点だけを測る」と逐語で宣言する。extime と max_ope は bench 1 回の構成そのもので、
  D1854 が rratio・rmw・max_ope を resident peak に効く key と確定しているとおり、較正時の構成を維持しないと
  同じ動作点と言えない。
- `reps` を calibrator の noise floor の 10 に合わせると名目 bench 時間が §11.2 の目安 (1 pair・1 セルあたり
  2 campaign 合計 7,440 秒) の 2 倍になり、§5 の総計測予算欄 (未記入) を圧迫する一方、bench 1 回の構成は
  変わらない。sweep の 3 は median が外れ値に弱い。
- D1536 は「既存機構または認可された人間手番で校正済み設定を用意できるかを先に確かめ、用意できるなら producer を
  作らない」と決めた。本決定はその確認の結果で、専用 producer は作らない。
- **本決定が保証しないこと:** admission 成功 (`load_verified_calibration`) は protocol・測定設定・対象集合の意味的
  一致も、選択規則の事前性も保証しない (D1696 が人手責任として残した 9 項目のまま)。現行 source と argv による
  構成の復元であって、取得当時の source bytes まで検証したものではない。

**却下した選択肢:**
- s8b official の `APPROVED_EXTIME_S = 5` / `APPROVED_REPS = 5` を流用する — 別実験の承認値で、較正は extime 3 で
  取られている。
- `reps = 10` (noise floor) または `3` (sweep) を自動転記する — 用途が違い、床値測定の反復数を導かない。
- `reps = 5` を「較正済みの出力値」と記す — artifact にその field は無い。
- CV や throughput を見て reps を調整する — 結果依存の設計変更になる。
- 較正 JSON へ 3 項目を足す producer を作る — D1536 の順序に反する。

## {{D:b4-floor-cell-set}}. B-4 床値のセル集合は 3 workload × 較正が支える 1 contention セル (t48・skew 0.9・rmw 0) の合計 3 cell に具体化し、各 spec は 1 cell を持つ

**決定 (D1641 決定 3 の委任と [T-2288] 本 wave の依頼「§5 の方針から具体列を起こす」の下で AI が具体化):**
事前登録 §5 は contention セルを列挙していない (2026-09-15 の [T-2288] wave と本 wave が現物で確認)。
**本決定は既裁定の転記ではなく、対象集合を具体化する新しい選択である。** 具体列は「対象 driver (silo、
`base (silo-backoff-magnitude)`)・Pegasus・3 workload について、accepted 較正が実在し binder
(`floor_pair_driver._bind_checkout_inputs`) の exact 一致を通る `threads` / `ycsb_zipf_skew` / `ycsb_rmw` の
条件」から起こし、`records` は {{D:calibration-record-selection-rule}} で選んだ較正の `saturation.records` を
そのまま採る。

| spec (workload) | cell の `workload` (逐語。`"0"` を `"false"` へ置換しない) | `records` | 束縛する較正 (path / sha256) |
|---|---|---|---|
| read-heavy (rr95) | `{"ycsb_rmw": "0", "ycsb_rratio": "95", "ycsb_zipf_skew": "0.9"}` | 1,000,000 | `output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json` / `5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc` |
| balanced (rr50) | `{"ycsb_rmw": "0", "ycsb_rratio": "50", "ycsb_zipf_skew": "0.9"}` | 1,000,000 | `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` / `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` |
| write-heavy (rr5) | `{"ycsb_rmw": "0", "ycsb_rratio": "5", "ycsb_zipf_skew": "0.9"}` | 2,000,000 | `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json` / `2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067` |

全 cell で `threads = 48`、`extime = 3`、`reps = 5`、`ycsb_max_ope = 10` ({{D:b4-floor-perf-config-approval}})、
`environment.env_tag = pegasus`、`clocks_per_us = 2100`。保守側の最大を取る対象集合 (D1641 決定 3) は
「この 3 cell × 各 spec の 2 時間窓」である。

**理由:**
- D15 は較正を (env, thread, 代表 workload) で key し、D1854 は cell と較正の workload exact 一致を正しい gate と
  確定した。よって cell の contention 軸 (skew) は accepted 較正が存在する値にしか置けず、silo・t48・pegasus の
  accepted 較正は skew 0.9 / rmw 0 の 3 workload にしか無い。
- skew を足すには新しい較正 (D15 の関門) が要り、それは D1641 決定 2 が認可した測定にも D1936 項 7 が認可済みと
  記す rr95 / rr5 の較正にも含まれない。無い較正を前提に cell を書けば spec は束縛できない
  (2026-09-15 の insight「未取得 artifact への前方参照 pin は凍結にならない」)。
- 1 spec 1 workload は D1855 / D1936 項 7 の確定事項である。3 件の較正の `env_tag` / `clocks_per_us` /
  `threads` / `workload` / `saturation.records` が上表と一致することは現物で照合した (段 3 レンズ B が独立に再現)。
- **本決定が主張しないこと:** この 3 cell が研究対象として十分 (contention 域を網羅) であること。binder 全体
  (binary・build receipt の束縛を含む) が成功すること — 較正側の照合が通ることまでしか確かめていない。

**却下した選択肢:**
- skew 0.5 / 0.99 等を足して contention セルを複数にする — 較正が無く束縛できず、AI が測定集合を広げることになる。
- rr50 だけで先に凍結する — 先行結果を見てから残りを選ぶ形は §5 追補 (b) の事前閉包に反する。
- §5 に具体列が既記載だったとする — 現物に無い。
- 観測した床値の大小でセルを間引く — 事後選択になる。

## {{D:calibration-record-selection-rule}}. 同条件の accepted 較正記録が複数あるときは、測定値を読まない 5 条件で適格集合を作り、取得申込が最早の記録を採る — 較正値は既知だが床値結果は存在しない時点で定めた

**決定 (D2044 項 11 の「別途定める」):** 凍結 spec の `provenance.calibration` に pin する較正記録は、次の規則で
1 件に決める。規則は spec を書く人手 (D1696) の選択規則であり、loader / binder / gate / schema の受理集合は変えない。

適格条件 (すべて満たす):
1. spec を凍結する checkout の `output/env/<env_tag>/calibration/registered/` 配下の tracked record である
   (registered 限定は本決定が新しく置く人手規則で、binder の要求は tracked bytes の束縛だけ)。候補集合は
   結果に応じて広げない。
2. `quality.status == "accepted"` で、floor driver と同じ入口 (`calibration_verify.load_verified_calibration`、
   `attestation_mode=required`、spec の `env_tag` / `clocks_per_us`) を通る。既存の品質条件を維持するだけで、
   accepted 同士を測定値の大小で順位付けしない。
3. protocol が spec の対象 driver の protocol (B-4 では silo) と一致する。判定は `genome` の先頭要素で行う。
   `genome` が無い record は、内容 sha256 が `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`
   または `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` の歴史的 2 件に限って silo と
   見なす。根拠は各 record の `acquisition_receipt.allocation.pbs_jobid` から辿る tracked な
   `output/env/pegasus/calibration/job-staging/<pbs_jobid>/calibrate-argv.json` の `--binary` が
   `cc/silo/ycsb_silo.exe` を指し、`--binary-sha256` が receipt の `ccbench.binary_sha256` と一致すること。
   **この例外を将来の genome 不在 record へ一般化しない** (D1538)。
4. `env_tag`・`clocks_per_us`・`threads`・`workload` (3 key の逐語) が cell と exact 一致する。`records` は
   選択後に採用較正から転記し、望む records で候補を先に選ばない。
5. 自分の attestation 述語 (effective-clock、現行 tolerance) を通らないと記録・裁定された記録でない。
   現時点でその記録は D1537 が自己不整合と裁定した `753f535a…` (Pegasus 世代 g1) の 1 件で、identity は
   消費側除外集合 `layer3_report.SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS` (path と sha256) が持つ。
   **effective-clock method の文字列が現行 (`env_attestation.EFFECTIVE_CLOCK_METHOD`) と違うことだけを拒否理由に
   しない** (規律 7)。較正 verifier が現行 policy と照合するのは tolerance だけで、method 一致は既存 gate ではない。

採用順序: 適格集合が 2 件以上なら `acquisition_receipt.qsub.submit_epoch` が最小の記録 (取得申込が最早)。
同値なら `acquisition_receipt.qsub` の `(project, queue, request_id)` の辞書順。同一の取得 identity に異なる内容が
あるとき、または順序の根拠が欠けるときは読み飛ばさず停止して人手確認へ戻す。内容 sha256 は束縛と重複確認にだけ
使い、順位には使わない (測定値を含む内容から決まるため)。

適用結果 (2026-09-17、registered 8 件):
- rr50 / silo: `753f535a…` (g1、method `proc-cpuinfo`) は条件 5 で不適格、`94a4b79f…` (g2) を採る。
  適格集合は 1 件になるので、採用順序は今回勝者を決めていない。
- rr95 / silo: `5c836a22…` のみ。rr5 / silo: `2b7ba072…` のみ。
- mocc / tictoc の record (rr50 2 件、rr95 2 件) は条件 3 で不適格。binder は protocol を照合しないので、
  この条件が無いと非 silo の較正で silo の cell を束縛できてしまう。

**時系列 (隠さず記録する):** 床値の結果は spec も測定も存在せず 1 件も無い。規則はその前に固定した。一方、
較正記録の測定値 (throughput・CV・miss 率) は 2026-07 以降 repo で公開されており、本 wave も閲覧した。
規則の条件のうち実際に候補を落としたのは条件 3 (protocol、`genome` という既存事実に本規則を当てたもの) と
条件 5 (D1537、2026-09-03 の既裁定 identity) だけで、**同条件 (rr50 / silo) の 2 件を分けたのは条件 5 の
既裁定 identity だけ**である。本 wave が新しく置いた条件 (registered 限定・最早順・同値処理) は 1 件も候補を
落としていない。D2044 項 11 の「結果を見る前に」は床値結果に対して満たす — 「結果」を床値結果と読むのは
本 wave の解釈であり、較正値の既知性は本文のとおり開示する。**admission 成功も本規則の適用も、選択規則の事前性を
機械的に保証するものではない。**

**理由:**
- 5 条件はいずれも record の測定値を読まない。条件 5 は「自分の述語で落ちた」という挙動基準であり、
  現行 method との差そのものではない。
- 「最早」は D1311 が床値 run に採った型 (起動時刻は結果より先に確定し、最新採用は望む記録が出るまで測り足して
  停止時刻を選べる) を較正へ類推した設計上の先例で、直接適用済みの裁定ではない。
- D2044 項 11 は D1986 項 1 (レコード数の選択規則) の流用を誤引用と判定した。本規則はレコード数を選ばず、
  同じレコード数の異なる記録を選ぶ。

**却下した選択肢:**
- 最新の accepted を採る — 事後に測り足す余地を残す。
- 環境契約の有効世代 (g1) の pin を採る — g1 は D1537 が自己不整合と裁定した記録で、rr95 / rr5 には世代 registry が
  無いので規則として閉じない。
- CV や miss 率が良い記録を採る — 値に依存する。
- method 文字列の不一致を拒否条件にする — 規律 7 に反する。
- 同値を内容 sha256 の昇順で決める — 測定値を含む内容に依存する。
- binder に protocol / 自己整合の照合を足す — gate の新設で D1696 と本 wave の scope 外。
