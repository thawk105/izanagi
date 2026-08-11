---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t766-t768-resume-diff
seq: 2
---

## supersede 追記

- F212 **supersede: 2026-08-11** — 恒久対応の dry-run は [T-768] 実装後 `python3 tools/spool_fold.py --dry-run --show-diff` とする。stale carry の露出は変わらず、加えて台帳へ挿入される bytes と削除される fragment を land 前に byte で確認できる。手順の正本は `docs/spool/README.md`。
