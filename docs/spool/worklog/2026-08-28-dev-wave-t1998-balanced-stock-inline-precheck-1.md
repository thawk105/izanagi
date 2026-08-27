---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t1998-balanced-stock-inline-precheck
seq: 1
title: [T-1998] balanced stock-inline 正式測定の実装差分ゼロ precheck は既存 closure 不成立で停止した
---

## 本文

- ユーザー指示どおり、T-1998 の専用 prereg、同一 source/env の stock-inline build、launcher、
  result consumer、正式測定認可を、landed code と既存 artifact だけで先に棚卸しした。
- exact headline pair は balanced の no-backoff (`BACK_OFF=0`) と fixed-5us
  (`BACK_OFF=1, BACKOFF_FIXED=5`) で、診断ノブ `BACKOFF_NOINLINE` は inert default 0。
  `BACKOFF_NOINLINE=1` の balanced profile と perf 下 tps は D20 に従い headline へ流用しない。
- producer 部品は実在した。`backoff_sweep` は exact pair を含み、pipeline は trace-enabled verifier build と
  trace-disabled performance build を別 build・別 run にし、verifier 通過前の COMMIT を許さない。
- formal closure は不成立だった。T-1998 専用 prereg と sanctioned compute launcher は不在。
  既存 `backoff_sweep_report.py` は certified view を読むが、結果後の static argmax、選択バイアス未補正、
  `linux-baremetal` 固定であり、prereg-fixed pair の headline consumer ではない。
- runtime `AuthorizedContract` は環境 admission として実在するが、人間による正式測定認可の代用ではない。
  2026-08-27 rulings 控えは T-1998 を含まず、自身を裁定証拠でないと明記していた。
- 稼働 T-1905 の既知所有2 pathと本 precheck のコード編集面は衝突 0。ただし将来 launcher/consumer の
  path、registry key、campaign/output identity、測定資源を含む重複は予定面未確定のため未証明とした。
- 実装面の差分は 0。prereg、build、campaign、正式測定は起動していない。実装が必要と判明したため、
  本 precheck waveへ膨らませず別 D95 Codex author change unitへ戻す。
- Codex plan は初回、自前の 120,000 CLI token cap に達して output 0 となり不受理。canonical 抜粋と
  source 行範囲へ射影を狭めた再試行は出力検査を通過した。敵対 consult 2 本も出力検査を通過し、
  prereg を作らず停止する結論を支持しつつ、親の「全重複ゼロ」「human auth 不在」の過大断定を狭めた。
- エージェント工数: Codex subprocess 4 本 (plan 2、うち1本不受理 / consult 2)。実装 worker は 0。
- 記録 commit 後の受入 attempt 1 は `tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py` で
  `child-green` (raw/normalized rc=0)。tested main `5b6a5ec4f`、tested tip `37d10391b`、
  effective scheduler `loadgroup`。lease は未取得で release 対象なし。性能 build / benchmark は未実走。

## 次の一手差分

### 更新

- [T-1998] **P2・precheck 完了、別変更単位待ち**: 新しい汎用 driver は作らず、(1) pair consumerまで届く
  producer evidence の read-only 監査と不足時だけの限定 schema 拡張、(2) 既存 non-screening official
  `backoff_sweep` を呼ぶ薄い sanctioned launcher、(3) post-result argmaxを使わない prereg-fixed pair consumerを、
  別 D95 Codex author change unitで扱う。全 landed 後に fresh precheckを再実行し、成立時だけ prospective
  preregまで進めて停止する。正式測定はその後の人間認可を待つ。
  base: 1d623e6108c07bad2b2ec7bdff628aadb697525d3d7b153422db780ee084d253
