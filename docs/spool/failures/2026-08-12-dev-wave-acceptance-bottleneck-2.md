---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-acceptance-bottleneck
seq: 2
---

## 新規

### {{F:fix-stage-role-name-collision}}. 段 6 fix 子の成果に `role=fix` と書いて provenance が赤 [手順漏れ]

- 事象: 段 6 の fix 子 2 本の成果を統合する commit へ
  `AI-Agent: ...; role=fix; scope=...` と書き、`check_ai_provenance.py` が rc=1 で
  「AI-Agent の形式違反」+「実装面に Codex role=author がない」を出した。
  `git commit --amend` で `role=author` へ直して rc=0。main は 1 bit も汚していない。
- 根本原因: **dev-wave の段名と provenance の role 名が衝突している。**
  段 6 の子は入口でも `tools/dev_wave_codex.py --stage fix` でも一貫して「fix 子」と呼ばれるが、
  `docs/ai-provenance.md` の role 許可値は `author`/`reviewer`/`researcher`/`manager`/`integrator`
  の 5 つで `fix` は無い。段名をそのまま role へ写すと必ず落ちる。
  dev-wave 側の reference (`DW-O17`) へ 1 行足す案は L1.5 予算超過 (9700 > 9566 bytes) で
  入らなかったため、台帳側へ記録する。
- 恒久対応: 段 6 fix 子の成果を commit する直前に、trailer の role が
  `docs/ai-provenance.md` の 5 値のいずれかであることを確認する。fix 子は実装面を書くので
  `role=author` が正しい (段名ではなく寄与の種類で選ぶ)。
- 再発検知: `check_ai_provenance.py` が commit 後に機械検出する (本件もこれで止まった)。
  ただし検出は commit 後なので、amend が必要になる点は変わらない。
