---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2766-pairing-adopt
seq: 3
---

## 再発

### F344

- **再発: 2026-09-20** — land を挟まない**同一 wave の連続受入** (採用効果の A/B 再確認で B 木の受入を 3 走) で起きた。02-B の成功後に lease が保持されたまま (記録済み main_sha `4fe49200e`) 他 wave の land で main が進み、03-B の claim が `stage=claim-self-unverified rc=70` で 1 回空振り (子は走らず、17 分の門番待ちを消費)。親が `wave_land_window.py release` で解放し、launcher へ「`lease is held` と告げた走だけ終端で release する」を加えて以後は通った。F344 の恒久対応 (land rc=0 直後の release) と 2026-09-07 の追記 (land 不成功時の release) は「land しない受入の反復」を覆っていない — 同 wave で受入を続けて投げるときは、各走の終端 (または次走の投入前の `status` 確認) で release する。逐語は `output/insights/2026-09-20/t2766-pairing-adopt/README.md` §5・§7。
