---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-land-knowhow-ops-docs
seq: 2
---

## 再発

### F219

- **再発: 2026-09-29** — docs-only の land 調整の知見の反映 wave で、節予算 1000 bytes の原資を作るため `docs/dev-wave/operations.md` の DW-O20 の「`DW-C01`に従い初期化して」を「`DW-C01`で初期化して」に詰めたところ、受入全走 1 回目 (1 failed / 28064 passed) で `orchestrator/tests/test_check_docs.py::test_dw_o20_points_to_dw_c01_and_drops_legacy_submodule_command` が赤になった。追加事実は、**この pin は `tools/check_docs.py` ではなく test 側の逐語 assert にあり、`check_docs.py` 緑でも捕まらない**こと。親は詰める語句を `tools/check_docs.py` だけで grep していた。語句を戻して受入を取り直した (受入 1 回分、約 14 分の損)。予防は、詰める前に wave 前の本文にあって新しい本文に無い文字列 literal を tools・orchestrator・hooks の Python から走査すること (本 wave は AST で全数走査し、他に文書へ掛かる pin が無いことを確かめた)。

### F225

- **再発: 2026-09-29** — docs-only の land 調整の知見の反映 wave で、親が `docs/dev-wave/operations.md` を編集した未 commit 状態のまま段 6 の read-only review 子を投げ、`NG: docs/dev-wave/operations.md: working tree が authority commit と異なる` の rc=2 で起動前に終わった (起動から約 3 秒)。2026-08-27・2026-09-18 の再発と同型で、「実装子がいない docs-only wave でも、review 子の前に docs/dev-wave の編集を commit する」が追加の確認点。commit してから新しい job-id・新しい `.done` で投げ直して通った。失ったのは数分で、計算資源の浪費は無い。
