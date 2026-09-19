---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-19
wave: dev-wave-t2786-recovery
seq: 2
---

## 再発

### F649

- **再発: 2026-09-19** — T-2786 の replica probe で、analyzer の validity 述語 (production report の
  `group_to_workers` を 1 群 1 worker と要求) を合成 fixture `{'g': ['gw0']}` だけで緑にし、plugin の
  `check_prepare_order` (xdist remote hookimpl の `isinstance` 同定) には test が無いまま、段 6 レビュー 2 本 +
  焦点再レビューを通過した。本番 conftest は real-repo marker を 118/173 件で意図的に分割 (5ac638955) し、
  xdist worker の interactor は execnet の `__channelexec__` 名前空間の別 class なので、計算ノードの実機 1 走
  (block1、9492.nqsv) で A/L が却下・P が全 48 worker UsageError になった。実体 (本番 report の形、
  compile+exec した別 class) を名指しした正例・負例と block1 原本への実データ照合で fix2 を検証した
  (`output/insights/2026-09-19/t2786-base-decomposition-recovery/README.md` §2〜3)。
