---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2279-mutation-dispatch-override
seq: 2
---

## supersede 追記

- F762 **supersede: 2026-09-09** — 根本原因の記述のうち「本走の command 構築も dispatcher 直呼び」は誤りで、当時も baseline と mutation は `tools/run_tests.py` を実行していた。直呼びは collection だけである。collection への上書き転送は 2026-09-07 の commit 1e22c4cbd が実装済みで「恒久対応: 未実装」も stale。今日の HEAD で上書きが届かない経路は 0 件であることを [T-2279] wave が全経路で確認した (`output/insights/2026-09-09_t2279-mutation-dispatch-override/README.md`)。残る欠陥は伝播ではなく外側 watchdog と dispatcher 締切の不一致で、{{T:mutation-watchdog-dispatch-deadline-contract}} が引き継ぐ。
