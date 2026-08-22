---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1458-noncertifying-consumer
seq: 1
title: '[T-1458] acceptance の lease claim 待ちスキップを実装した (コード+テスト)'
---

## 本文

- D662 に従い `tools/dev_wave_wait.py acceptance` へ `--lease-optional` を追加した。
  held/queued claim は待たずに疑似 context で受入を継続し、receipt の holder は wave の SHA-256 先頭12桁に束縛する。通常経路は既定値のまま維持した。
- `orchestrator/tests/test_dev_wave_wait.py` の最終全走は `tools/run_tests.py` の local execution 経由で **401 passed**。Pegasus login からの通常 dispatch は queue 観測不能により rc=16 だったため、available memory 十分を確認して同 runner の site override を使った。
- optional held/queued の生成 receipt を実ファイルに書き出し、`dev_wave_land.py` の `_release_authority_digest` を通して digest 検証に成功した。追加 targeted は 7 passed。
- 追加で走らせた land 側全走は 214 passed / 2 failed。失敗は本変更外の既存 land/layout テストで、`test_exploration_external_root_keeps_wave_clean` は `/tmp` 配下を repository 外として扱う判定で再現し、`test_merge_child_inherits_lock_fd_if_helper_is_killed` は並列実行時の wrapper race だった。後者は直列再走で通過した。

## 次の一手差分

### 完了

- [T-1458] D662 の acceptance lease optional 経路を実装し、既存経路を含む対象テスト全走を完了した。
  remaining: none
  base: 44a31e2b08dcd7da13a578eafa2d2710915db2518596c3bd699a8997bdcb9289
