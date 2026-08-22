---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-lease-cmd-entry-sync
seq: 3
---

## 新規

### {{F:waiter-consumer-pin-hardening-gap}}. dev-wave waiter-consumer pinのdisclaimer検出が英語語彙とH2内重複配置を防げない [恒真ゲート]

- 事象: `tools/check_docs.py`の`_check_dev_wave_waiter_consumer_pins`が持つ
  `DEV_WAVE_WAITER_DISCLAIMER_RE` (日本語の「参考例・任意・手動投入・してよい・使わない・
  実行しない・必須でない・省略可」を検出する正規表現) は、英語の同義語 (例:
  "This command is optional.", "do not use", "manual only") を検出しない。段3敵対相談
  (レンズA) がこの穴を指摘した。
- 事象2: `sequence_count()`はH2セクション全体から対象の連続行を数えるだけで、「項6という
  特定の位置」に紐付いていない。項6自体を破壊しつつ、同じH2内の別の可視箇所に正しい
  canonical文言を複製して配置すると、`sequence_count()==1`を満たしたままpinを回避できる。
  段6敵対レビュー (review2) がこれを実際に再現し、`findings=[]`になることを実演した
  (2026-08-23、dev-wave-lease-cmd-entry-sync wave)。
- 根本原因: `_check_dev_wave_waiter_consumer_pins`は正規表現による語彙検出と、H2全体を
  対象とした連続行カウントという2つの構造的に浅い検査で構成されており、「項6という位置に
  紐付いた、意味を保った本文か」までは検証しない。
- 恒久対応: 未着手。修正候補は (a) disclaimer正規表現へ英語語彙を追加する、
  (b) `sequence_count()`を項6見出し直下の連続行だけに限定するよう構造を絞る、の2方向。
  専用waveで、既存9件のnegative controlを壊さない設計を段2 codex planから起こす必要がある
  ({{T:waiter-consumer-pin-hardening}}参照)。
- 再発検知: 修正後、英語disclaimer語彙のnegative controlと、H2内重複配置のnegative
  controlを`orchestrator/tests/test_check_docs.py`へ追加する。
