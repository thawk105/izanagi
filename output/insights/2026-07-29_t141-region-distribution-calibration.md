# T-141 閾値校正 — pegasus 実測の region 分布と DEFAULT_MIN_* の裁定

- **日付**: 2026-07-29
- **担当**: dev-wave [T-141] (branch `worktree-dev-wave-t141-directive-ops`)
- **一次データ**: `output/env/pegasus/profile/t141-directive-calibration/0_873859.nqsv/`
  (region-totals-*.json ×12、report-symbol-*.txt ×12、attestation.txt、build ログ全文、
  会計痕跡 .e/.o)。失敗 attempt の forensic は同階層の `0_873732 / 0_873737 / 0_873759 /
  0_873846 / 0_873855` (経緯は §4)
- **採取系**: `tools/pegasus/t141_region_profile.sh` (gen_S 1 node、Xeon Platinum 8468
  48 物理コア照合済み、単独性検査付き)

## 1. 位置づけ

`profiler_directive.py` の暫定閾値 `DEFAULT_MIN_REGION_PCT=10.0` /
`DEFAULT_MIN_MARGIN_PCT=5.0` は導入時 (2026-07-27) に「実 perf 出力での校正は未了」と
明記されていた。本 insight はその校正の一次資料 — **既定値を動かす前に実測分布を残す**
(モジュール docstring の契約) を果たし、裁定を記録する。

## 2. 実験

- **build**: 現 pin d706650 の silo、trace-disabled (`CCBENCH_TRACE=0`)、Release +
  `-gdwarf-4 -fno-pie/-no-pie` (診断用。§5 の限界参照)。2 構成 =
  S (`CCBENCH_BACK_OFF=0`) / V (`CCBENCH_BACK_OFF=1` = stock 適応 backoff)
- **workload**: write-heavy (zipf 0.9 / rr5) と balanced (rr50)、
  RECORDS=1M / THREADS=48 / extime=3 / clocks_per_us=2100 (確定 calibration 値、規律 4)
- **採取**: perf record `-F 400` `cycles:u,instructions:u`、計時 run 先行 +
  `perf record -D` (マージン 1.0 秒) で makeDB 相を除外。サンプル窓 ≈ 2 秒/セル、
  cycles サンプル ≥1000 gate。reps=3
- **file 帰属**: perf script で cycles:u の IP を集計 → unique IP を addr2line 一括
  バッチで file:line 化 → **本番の `srcline_region_mapper` + `region_totals`**
  (orchestrator を node 上で import) で N1 provenance の 17 領域へ写像し
  region-totals JSON を in-job 算出。mapped 合計 0 は fail-closed

## 3. 結果 — 実測分布

| セル (build-workload) | top 領域 | top % (r1/r2/r3) | 2 位 % | margin | dropped % |
|---|---|---|---|---|---|
| S-write-heavy | cc/silo/transaction.cc | 32.6 / 33.6 / 33.7 | ≤0.4 (silo_op_element.hh) | 32.2〜33.3 | 66〜67 |
| S-balanced | cc/silo/transaction.cc | 27.9 / 27.7 / 28.7 | ≤0.2 (silo_op_element.hh) | 27.6〜28.6 | 71〜72 |
| V-write-heavy | include/backoff.hh | 46.7 / 46.8 / 46.3 | ≤0.8 (transaction.cc) | 45.6〜46.1 | 52〜53 |
| V-balanced | include/backoff.hh | 46.5 / 46.0 / 45.6 | ≤1.6 (transaction.cc) | 44.1〜45.0 | 52〜53 |

- n ≈ 38.4k〜39.6k cycles サンプル/セル。rep 間変動 ≤1.5 点 — 計時 run + `-D` の
  makeDB 除外が機能している傍証 (混入すれば rep 間で数点動く)
- symbol 対照 (report-symbol): S は `TxExecutor::read_internal` 23% /
  `MasstreeWrapper::get_value` 17〜23% / `_int_free` ~10%、V は `TxExecutor::abort` 87%
  (適応 backoff の spin が abort 経路に内在し、srcline では backoff.hh へ帰属)
- dropped の内訳は編集面外の正当な消費 (masstree 本体・allocator・libc)。regime 6 の
  fails-closed が値として記録に残る設計どおり
- **既定閾値での derive 帰結 (12/12 セル)**: S → `cc/silo/transaction.cc`、
  V → `include/backoff.hh`、すべて dominant_region。機序として正しい帰属
  (backoff off = validation/read 経路、backoff on = spin) であり、build×workload で
  一貫、rep 間で不変

## 4. 裁定 — **既定値据え置き** (MIN_REGION_PCT=10.0 / MIN_MARGIN_PCT=5.0)

1. 実測の支配領域は 27.7〜46.8%、margin は 27.6〜46.1 — 既定閾値から大きく離れており、
   判定は閾値の細部に依存していない (頑健)
2. 2 位領域は最大でも 1.6% — 現実の分布では region floor 単独でも判別でき、margin 閾値は
   将来の平坦な分布への備えとして機能する
3. 閾値を動かす根拠となる境界事例 (10% 付近の top、5% 付近の margin) は観測されていない。
   観測なしに動かすのは根拠のない変更であり、恒真化の検査 (None 分岐) はテストが担保済み

## 5. 既知の限界

- **非 PIE + DWARF4 の診断 build**: 帰属のための構成であり headline 計測には使わない。
  perf record 下の tps (S-write-heavy ≈ 2.27〜2.37M) は sampling 込みの参考値
- **`perf report --sort=srcline` は pegasus で使えない**: 巨大 static debug info に対し
  サンプル数非依存で 300 秒 stdout 0 バイトのままハング (873737/873759/873846 で実測、
  小バイナリでは再現しない)。pegasus での file 帰属は本 job の IP バッチ経路を使うこと
  (機械固有の作法として runbook §7.1 にも記載)。CLI `derive` の srcline report 直読み
  経路は、srcline が健全な環境 (linux-baremetal 等) 用として残る
- **cycles:u 限定**: カーネル時間は分布に含まれない (観測対象 = ユーザ空間の CC コード)
- walltime SIGKILL 時に failure.json が残らない縁は残存 (内部 deadline + reserve 600 秒で
  実質回避)。単独性検査の最終セル run 後は次セル検査が無い (probe 相応の割切り)
- 転移 (roadmap §5): 分布の**形** (どの領域が支配的か) は環境非束縛の知見として扱い、
  値 (%) は pegasus 束縛。他環境での再校正は不要 — 再取得するのは環境束縛量のみ

## 6. 経緯 (attempts、fail-closed の実証)

1. 873732 (25 秒): `git archive` が `.gitattributes` の `oze* export-ignore` で cc/oze を
   落とし configure 失敗 → tracked 限定 tar へ (commit 167c9b9)
2. 873737: srcline report timeout 120 秒 → -F 400 + timeout 300 へ (a1e5c31)
3. 873759: 同 timeout (0 バイト) — サンプル数非依存と判明 → DWARF4 + debuginfod 遮断 +
   :u + report smoke (448c6b2)
4. 873846: smoke 通過・実バイナリで依然ハング → srcline 撤去、IP バッチ経路へ (54e5faf)
5. 873855: 全段完走するも PIE の runtime IP で addr2line 全滅 (dropped=100%) → 非 PIE 化 +
   mapped 合計 0 の fail-closed 昇格 (次 commit)
6. **873859: 成功** (本データ)。全 attempt で failure.json / 部分成果物 / 会計痕跡が残り、
   fail-closed 経路が 5 種の実障害で発火したこと自体が採取系の負の試験になっている
