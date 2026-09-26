---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: worktree-t2850-trace-concurrent-verify
seq: 1
---

## 新規

### {{F:settle-cap-from-different-order-probe}}. 同時検査の後の静定待ちの上限を、本番と違う順序で測った load の減衰から決め、計算ノードの smoke で品質欠測になった [テスト代表性] [誤前提]

- 事象: [T-2850] の案 (b) の決定 (親の裁定) は、同時検査の後に 1 分 load average が 4.0 以下に戻るまでの実測 3〜39 秒 (write-heavy) から上限を 60 秒にした。
  その実測は「trace 取得 → 直列検査 → 90 秒の減衰 → 同時検査 → 減衰」の順の測定 script で取った値で、本番の「5 本の連続取得の直後に同時検査」では
  取得の負荷 (48 thread × 約 3 秒 × 5 本) が上乗せされる。実装後の計算ノードの smoke (job 29777) で系列開始 stock が 60 秒を使い切って
  `settled=false` → 品質欠測 → `stock-unestablished` になった。本番順序で測り直すと 67 秒・77 秒だった。
- 根本原因: 時間予算の根拠にした実測の regime (直前の負荷の履歴) が適用対象と違うことを、決定の時点で確かめなかった。1 分 load average は
  直前 1〜2 分の負荷の履歴に依存するので、同じ検査でも前段の順序で閾値到達の秒数が変わる。
- 恒久対応: 測定 script に本番順序の mode (`--order production`) を足して測り直し、上限を実測の最大 77 秒の約 1.5 倍の 120 秒にした
  ({{D:concurrent-local-verify-fork-receipt}} 項 4)。規律は `docs/dev-wave/operations.md` の `DW-O13` (時間予算は観測 regime が適用対象と同じかを併記して
  実測の max への倍率で決める) — 既存の義務の適用漏れで、新しい手順は足さない。
- 再発検知: 静定・待ちの上限を決める実測は、測定 script の順序が本番の経路 (直前の負荷を含む) と同じかを記録に書く。実装後の smoke で
  `bench_done.settled` と harness の品質分類まで確かめる (certified だけで合格にしない)。

## 再発

### F1037

- **再発: 2026-09-26** — [T-2850] は `orchestrator/campaign/p3_s4_loop.py` (closure member) の変異 M8 (「`--verify-performance` だけでも同時検査の key を search_config に入れる」) を未 commit 注入の matrix に登録し、probe で狙いの 2 test が等価変異 M0p の drift 集合 (139 node) に含まれて値の層の kill を観測できなかった。本エントリの恒久対応どおり独立 clone の commit に焼いて 2 test だけを dispatch すると **2 passed (値の層で生存)** — 既定 identity の test が `--verify-performance` なしの呼び方だけで、B-5 や比較 harness の read-heavy / balanced が使う組を検査していなかった。test を足し (fix 6)、同じ commit 注入で再確認した (`output/insights/2026-09-26/t2850-trace-concurrent-verify/README.md` §5)。drift に覆われた変異を「drift 集合で KILLED」と数えると、この種の test の穴を見逃す。
