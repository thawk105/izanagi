# [T-1677] TRACE=0 の材料値を、束縛を実装した script で測り直した — 証拠の鎖は走らせて初めて存在する

- 日付: 2026-08-25
- wave: dev-wave-t1677-trace0-remeasure (branch `worktree-dev-wave-t1677-trace0-remeasure`)
- 起点の裁定: [T-1677] (2026-08-25 ユーザー裁定、択 (a))。既存の TRACE=0 観測値は、束縛を実装した
  script で測り直して正式材料へ上げる。択 (b) (D779 を改めて append-only の事後 attestation を
  認める) は不採用 — 後から証明書を付ける経路は絶対規律 3 (正しさシグナルを後付けにしない) と
  同型の緩みである。
- 正本: D779 (束縛の要求)、D780 (射程の文言と別防壁の閉包)、D297 (TRACE=0 preprocess 同一性の保証)
- 一次資料: `output/insights/2026-08-24_t1582-mocc-trace0-pilot.md` (旧観測)、
  `output/insights/2026-08-25_t1641-report-binding.md` (producer 側実装)
- environment: Pegasus `gen_S`、`bnode024`、Intel Xeon Platinum 8468、48 physical cores、HT off

## 1. 結果 — 束縛付きの TRACE=0 観測値

| 項目 | 値 |
|---|---:|
| completed transactions | 1,056,016 |
| workload elapsed | 3.095005593 s |
| throughput | **341,200.0296181694 txns/s** |
| average latency | 2.930832101975728 us |

workload は records=10,000、threads=48、zipf skew=0.9、read ratio=50、RMW=0、max operations=10、
extime=3 秒である。値は stdout の一意な `commit_counts_` witness (`commit-count.json` の
`count=1056016`) と monotonic elapsed から独立に再計算し、`throughput.json`・pilot receipt の
`workload` 節と一致した。

- request: `947072.nqsv`、submission nonce `8b30d9e9a845185fc6eef24ad14c3af5`
- outer source: `b3c5085bc602cc6f871c6ab331e05523b295bb52`
- ccbench source: `511c9538e4e8efa54b45cda62e72389ed3b706ec` → `058d0c4e5f237d88ec1c2ebe0739113d82906e47`
- pilot receipt SHA-256: `6783baaeae997a70c70ba7a5bc4972d703a45a661a19b348763494ba9dd48fb5`
- binary SHA-256: `44e09683073b111fe6fe7644693fcc2512794eacf5b900cf9486cc40287868ec`
- job script SHA-256: `cb9004fa7bc72ba22d73c40e396f3d09bdc156a3ee2ab31b4c274f1322349352`

## 2. D779 の関門が実際に発火した — 4 項目は実 run で初めて埋まった

pilot receipt は `mocc-trace-pilot-receipt/v2`、job-result は `mocc-trace-pilot-job-result/v2` で、
両者が checker report の 4 項目を束縛している。

| 項目 | 値 |
|---|---|
| path | `trace0-preprocess-identity.json` |
| sha256 | `ec9d30fe7555751d11117ceb3d90bfea61f2f1fdc6b20d2a9c1ee46e260f8416` |
| schema | `izanagi-trace0-preprocess-identity/v2` |
| guarantee | 選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性 |

親は退避後の証拠に対して report 実体の SHA-256 を再計算し、受領証が束縛した値と一致することを
確かめた。report 本体は `result=pass`、`old_oid=511c9538…`、`new_oid=058d0c4e…`、
`expected_paths=["cc/mocc/transaction.cc"]`、`compiler.path=/usr/bin/x86_64-linux-gnu-g++-11`、
`context_matrix` は 8 genome × 2 overlay = 16 context/file である。

**[T-1641] が実装した invocation identity 照合 — report の名乗りを pilot の実引数と照合する経路 —
は、この run が最初の実発火である。** 照合が偽になれば job は
`trace0_preprocess_identity_report_binding` で fail-closed して受領証を書かない。受領証が存在して
値が採れたこと自体が、照合を通った証拠になっている。

## 3. なぜ再計測でしかこの状態に到達できなかったか

旧観測 (`942177.nqsv`) の受領証は `mocc-trace-pilot-receipt/v1` で、`trace0_preprocess_identity_report`
という key 自体を持たない。親は退避済みの旧受領証を読んで、この不在を実測で確認した。

script の改修は将来の run にしか効かない。旧受領証へ 4 項目を後から足せば、受領証の SHA-256 と
create-only の歴史性が同時に壊れる。**「後から証明書を付ける」経路を一度認めると、以後
「証拠は後で足せる」が前提になる** — これが裁定が択 (b) を却下した理由であり、絶対規律 3 が
禁じている形そのものである。

本 wave は script を 1 byte も変えていない。worktree の `mocc_trace_pilot.sh` /
`submit_mocc_trace.sh` は main の blob と byte 一致であり (`cb9004fa…` / `5ac577fb…`)、
投入 receipt の `source_commit` は wave 起点の main tip と同一である。**測り直した対象が裁定時の
機構と別物にならないこと**を、内容 hash で閉じている。

## 4. 旧観測との対照 — 値は並べるが優劣は言わない

| | T-1582 `942177` | 本走 `947072` |
|---|---|---|
| receipt schema | v1 (束縛なし) | **v2 (束縛あり)** |
| host | bnode033 | bnode024 |
| compiler | g++-11 11.4.0 | g++-11 11.4.0 (同一) |
| ccbench source pair | `511c9538…` → `058d0c4e…` | 同一 |
| workload tuple | 同一 | 同一 |
| completed txns | 1,060,263 | 1,056,016 |
| elapsed | 3.078599114 s | 3.095005593 s |
| throughput | 344,397.877326226 | 341,200.0296181694 |

差は 0.93% である。**両者とも単一観測であり、この構成の within-run noise floor は未実測なので、
回帰・改善・優劣を主張しない。** 本走の値は旧値を否定する材料ではなく、束縛を備えた材料として
旧値を置き換えるものである。

binary SHA-256 は 2 走で異なる (`3f5b48c2…` / `44e09683…`)。build directory が job ごとの
create-only な `/scr/<jobid>` 配下にあり、その path が成果物へ入るためである。source pair と
compiler version は同一なので、これを意味的な差と読んではならない。

## 5. 射程と留保

- **この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては
  必要条件の一つである** (D780 決定 1 の統一文言)。完全除去を証明したと読んではならない。
  実 compile command・全 TU・link object・trace symbol/data・build receipt を結合する別防壁は
  未実装であり、D780 決定 2 に従い静的に解決できない間接値の限界と同じ閉包でだけ設計する。
- 受領証は `pilot=true`、`official_certification=false`、`eligible_for_refreeze=false` である。
  本値は 1 回の pilot raw observation であり、official calibration・certified 選択・refreeze の
  入力ではない。
- TRACE=1 の既存 evidence は別 source (`ef9328a3`) である。**same-source pairing、TRACE=1/0 の
  speedup、両者の比較は行わない。**
- TRACE=0 run なので verifier は `not-run` であり、trace artifact を性能値の正しさ証明へ
  読み替えない。
- job 内 `qstat -x` は Pegasus で非対応のため `qstat_accounting_rc=1` である。job 成功判定は
  pilot receipt・job-result・外側 PBS terminal 記録 (`Ended Request Time` が同一 request ID) の
  積で行った。
- **昇格側の gate はまだ無い。** producer が 4 項目を出しても、材料レポートを書く経路が
  返り値だけを読めば D779 の関門は実効発火しない。これは [T-1678] の scope であり本 wave では
  閉じていない。本レポートの 4 項目は親が退避済み証拠に対して手で再計算して確かめたものである。

## 6. repo 外一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1677-trace0-remeasure/evidence/` に保全した。

- `947072/`: 93 files / 104,220 bytes、manifest SHA-256
  `9183ab032b6a1e2693a871afa38cd215f87b31664c6cd2c8fa2660f3102758d5`
- `dry-run/`: 投入前 dry-run (nonce `d017beec9740e2b53c4f9dcfa2dda04d`) の submit receipt

repo 内 source と repo 外 copy の path/size/SHA-256 の完全一致を確認してから、
`output/env/pegasus/mocc-trace` と当該 PBS stdout/stderr を repo から限定削除した。
