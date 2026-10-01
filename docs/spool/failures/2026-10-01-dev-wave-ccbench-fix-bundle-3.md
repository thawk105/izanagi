---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-ccbench-fix-bundle
seq: 3
---

## 新規

### {{F:pass-on-instrumentation-violating-verifier-premise}}. 正しさ合格として数えた判定が、判定器の前提 (D1464) を満たさない計装の上で出ていた [テスト代表性] [手順漏れ]

- 事象: repo の Cicada の計装 `patches/instr-cicada-trace.patch` は、promotion の内部 write を workload の write と区別できないので、INLINE_VERSION_OPT ∧ INLINE_VERSION_PROMOTION ∧ TRACE を `#error` で止めている (根拠 D1464)。2026-09-29 の ccbench-cicada-bugfix wave は、この `#error` 1 行だけを消した repo 外の診断 patch (job dir `instr-cicada-trace-promotion-diag.patch`、sha256 `feaab9b6…`) で promotion 有効 genome を走らせ、K・R の巡回を根拠に 8 genome を失格にした (W・P の巡回 0 は合格に数えていない)。2026-09-30 の ccbench-cicada-promotion-uaf-fix wave は同じ patch の上で、修理後の promotion 有効 8 genome × YCSB 32 走行・TPC-C 16 走行の「巡回 0」を修理の確認 (正しさの確認) として数えた。2026-10-01 の ccbench-fix-bundle wave も同じ patch を当てて条件 (3) の取り直しに使う寸前だった (land 調整役の確認で投入前に停止)。
- 根本原因: 判定器の結果 (巡回 0・integrity 0) だけを見て、その入力の計装が判定器の前提 (D1464 の区別) を満たしているかを確かめなかった。`#error` が D1464 に基づく fails-closed の検査であることが計装 patch の commit message にしか書かれておらず、診断 patch を作った側は「当時 promotion が compile できなかった」ための止めと読んでいた。
- 恒久対応: D1464 に沿って promotion の write を内部処理として印を付ける計装と、それを読む verifier の拡張、および上の 2 wave の promotion genome の判定の再確認を {{T:cicada-promotion-trace-d1464}} として起票した。それまでは repo の計装 patch の `#error` (fails-closed) を外した変種の上の判定を正しさ合格に数えない (`output/insights/2026-09-30/ccbench-fix-bundle/README.md` §5。前例 2 wave の記録は書き換えず、同資料へ追記として残した)。
- 再発検知: 計装 patch を repo 外の変種に差し替えた判定は、変種と repo の patch の差分 (特に `#error`・`static_assert` の除去) を一次資料に書き、その止めの根拠となる D を引いてから合格・失格に数える。差分が止めの除去を含むなら合格に数えない。

## 再発

### F810

- **再発: 2026-09-30** — ccbench-fix-bundle wave の開始時、`tools/dev_wave_submodule_init.py` が `update-no-fetch` で 2 回続けて rc=1 になった。2 回目は何も変えずに再実行したが、1 回目の後で `git submodule status --recursive` を見れば 3 段とも初期化済みで、2 回目は不要だった (同 wave の子木 7 本は 1 回目で rc=0)。次から先に確かめること: rc=1 の後、再実行の前に submodule status と木の中身を見て、揃っていれば再実行しない。
