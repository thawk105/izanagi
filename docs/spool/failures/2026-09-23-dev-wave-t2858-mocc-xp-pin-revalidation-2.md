---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-23
wave: dev-wave-t2858-mocc-xp-pin-revalidation
seq: 2
---

## 再発

### F638

- **再発: 2026-09-23** — [T-2858] の段 9 land が `status=fold-failed` (rc=26、main 不動) で止まった。worklog fragment の `見送り追記` で見送り台帳 [T-167] へ足した 1 行に現行 pin の値の短縮形を書いたため、生成後の `docs/phase3.md` が `tools/check_docs.py` の「`pin.CURRENT_PIN` の値の literal 再掲」規則に当たった。`spool_fold.py --dry-run` と作業木の `check_docs.py` はどちらも緑で (fragment の段階では phase3.md に入っていない)、受入全走 (child-green) の後に lock 内で初めて赤になり、受入を取り直すことになった。追記行を `pin.CURRENT_PIN` への記号参照に直し、受入の前に使い捨て worktree で fold を実走して生成後の検査を通した。
