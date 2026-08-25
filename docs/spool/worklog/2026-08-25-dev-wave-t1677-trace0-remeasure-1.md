---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1677-trace0-remeasure
seq: 1
title: [T-1677] TRACE=0 の材料値を束縛済み script で測り直した。証拠の鎖は走らせて初めて存在する (docs のみ、branch worktree-dev-wave-t1677-trace0-remeasure、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- **ユーザー裁定 ([T-1677] 2026-08-25 /rulings 全件、択 (a)) の実行。** 既存 TRACE=0 観測値を、
  D779 の束縛を実装した script で測り直して材料へ上げた。択 (b) (D779 を改めて append-only の
  事後 attestation を認める) は採らなかった。
- 本走: request `947072.nqsv`、Pegasus `gen_S`、`bnode024`、Intel Xeon Platinum 8468、
  48 physical cores、Elapse 55S。trace-disabled build (`CCBENCH_TRACE=0`、target `ycsb_mocc.exe`)。
  値は throughput 341,200.0296181694 txns/s (1,056,016 txns / 3.095005593 s)。
  実測値と証拠の所在は `output/insights/2026-08-25_t1677-trace0-remeasure.md`。
- **D779 の 4 項目が実 run で初めて埋まった。** pilot receipt は `mocc-trace-pilot-receipt/v2`、
  job-result は `mocc-trace-pilot-job-result/v2` で、checker report の path・SHA-256・schema・
  guarantee を束縛している。[T-1641] が実装した invocation identity 照合 (report の名乗りを
  producer の実引数と照合する経路) は、この run が最初の実発火である。
- **実装面の差分はゼロである。** 裁定の内容が「既存 script で測り直す」であり、script を触れば
  測り直した対象が裁定時の機構と別物になる。worktree の `mocc_trace_pilot.sh` /
  `submit_mocc_trace.sh` は main の blob と byte 一致 (`cb9004fa…` / `5ac577fb…`) で、投入 receipt の
  `source_commit` は wave 起点の main tip と同一である。**変異 matrix は登録しなかった** —
  本 wave が変更した実装面が無く、未変更の main コードへ変異を登録しても測るのは [T-1641] の
  検出力であって本 wave のものではない。受入全走は免除していない。
- **旧観測 (`942177.nqsv`、v1 受領証) との差 0.93% について優劣を主張しない。** 両者とも
  単一観測で、この構成の within-run noise floor は未実測である。本走の値は旧値を否定する材料では
  なく、束縛を備えた材料として旧値を置き換えるものである。compiler は 2 走とも g++-11 11.4.0 で
  同一だった。binary SHA-256 の相違は build directory が job ごとの `/scr/<jobid>` 配下にあり
  path が成果物へ入るためで、意味的な差ではない。
- **本走で見つけた非対称:** pilot は CPU model 不一致で fail-closed し、gflags / glog は policy の
  pin と照合するのに、**compiler は path と version を記録するだけで policy 側に期待値が無い。**
  計測の比較可能性を支える build 入力のうち、compiler だけが記録止まりである。
  新規項として起票した ({{T:mocc-pilot-compiler-pin}})。
- **昇格側の gate はまだ無い。** 本レポートの 4 項目は親が退避済み証拠に対して手で再計算して
  確かめたものであり、機械 gate が発火した結果ではない。これは [T-1678] の scope である。

## 次の一手差分

### 完了

- [T-1677] 束縛を実装した script で TRACE=0 を測り直し、4 項目を束縛した v2 受領証付きの
  観測値を材料へ上げた。事後 attestation の経路は作らなかった。
  remaining: none
  base: c3fa6db89885f75983fb0613ae33b32c9303901ac9c8c2402cdf4835f84b0a0e

- [T-1641] 昇格の道筋 (測り直し) を実行し、producer 側実装の出力が実 run で 1 件得られた。
  旧受領証は書き換えていない。
  remaining: none
  base: eaab8ab7652557c7d2641e3bce0ef0000e3a6b9e00d249d111df5d275e581153

### 新規

- {{T:mocc-pilot-compiler-pin}} **P2・新規**: mocc trace pilot の compiler を policy の期待値と
  照合する。現行は CPU model が不一致で fail-closed し gflags / glog も pin と照合するのに、
  compiler だけは path と version を記録するだけで期待値が無い。計測ノードの既定 toolchain が
  変われば、同じ policy・同じ source pair の観測値が黙って別条件のものになる。
  着手条件 = 期待値を policy へ足す形が、床値 campaign 側の toolchain 束縛 (D293 / D601) と
  同じ設計を二度書く形にならないかを先に確かめる。
