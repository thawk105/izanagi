---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1458-noncertifying-consumer
seq: 1
title: '[T-1458] acceptance の lease claim 待ちスキップ (--lease-optional) を実装しmainへ着地させた (コード+テスト、branch worktree-dev-wave-t1458-noncertifying-consumer)'
---

## 本文

- D662 に従い `tools/dev_wave_wait.py acceptance` へ `--lease-optional` を追加した (commit
  0c89ec77、Codex role=author)。held/queued claim は待たずに疑似 context (wave 名の
  SHA-256 先頭12桁を holder とする) で受入を継続し、reclaim確認・TTL十分性チェック・release
  処理は自動スキップする。既存経路 (フラグ未指定時) は無変更。`test_dev_wave_wait.py`
  401 passed (新規7件含む)。
- 実測背景: 15件以上の並行 wave が単一の `acceptance.lease` ファイルによる FIFO 直列化で
  同時に長時間 (最長63分超) ブロックされ、うち1件は holder プロセスが計算ジョブ完了後に
  異常終了し TTL (2400秒) 満了まで lease を保持し続ける事象も実測した。D662 (2026-08-22
  ユーザー裁定) は既に「lease claim 待ちは不要」としていたが、実行可能にするコード変更が
  誰も着手していなかった。
- 「今後の全 wave が自動的に使う」ためのユーザー裁定を受け、`docs/dev-wave/operations.md`
  へ DW-O27 を追加、`.claude/commands/dev-wave.md` 条件18 (「親がテスト・受入を走らせる
  直前」) へ DW-O27 を追記、`tools/check_docs.py` の `REQUIRED_REFERENCE_SECTIONS` /
  `CONDITION_DISPATCH_CONTRACT["18"]` へ登録した (commit 25614f86)。
- 上記 commit は manager (claude) が `tools/check_docs.py` を直接編集したため
  `missing-codex-author` を誘発し、ユーザー承認 (AskUserQuestion 経由) を得て
  `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` へ 3 commit
  (25614f86, 94815c57, 3a5e5feb) を登録した (commit 94815c57, 782c55f5)。
- DW-O27 追加が `orchestrator/tests/test_check_docs.py` の `_build_min_repo()` 合成
  fixture との整合性を壊し、320件のテストが新規違反 (`H2 見出し DW-O27 が 0 件`) で
  失敗した。過去に同種の理由で DW-O26 を追加した commit 461b600f を参考に、DW-O27 は
  exact pin 契約化していない点を踏まえて最小限の追従 (fixture の許可セクション集合・
  条件18の合成文字列・レイヤー予算契約リストへの追加) を Codex 子 2 回で行い、
  502 passed / 0 failed まで解消した (commit 8256ba0f)。
- 受入は計 16 回投入し、13回目は上記 test_check_docs.py 不整合、14回目は
  `check_acceptance_reds.py` の `git worktree add` 一時競合 (rc=128、手動再現では
  rc=0 で成功、15+ wave 同時活動下の一過性競合と判断)、15回目は同ツールの
  `git worktree remove` 失敗によるプローブディレクトリ残骸 (`git worktree list` には
  既に非登録、単純なファイルシステム残骸と確認し安全に削除) でそれぞれ再試行した。
  16回目で受入成功 (`status=non-attributable-only`、`acceptance succeeded; lease was
  not acquired`)。成功時の26件のテスト失敗 (`test_sort_swo_oracle.py` 系、担当外) は
  全て non-attributable と正しく判定された。ただしこの non-attributable 判定
  (`check_acceptance_reds.py` が26件を直列に `git worktree` 経由で再現検証) 自体に
  41分以上を要しており、これは T-1458 の変更とは独立した既存ツールの性能課題として
  ユーザーへ報告済み (別途調査要否をユーザー判断で保留)。
- 作業中、複数の並行セッションが「専用 lease-dir を使って検証を無効化する」迂回策を
  検討・実行していたのを技術的根拠を示して都度指摘し、大半は撤回された。一方で
  「main SHA 不変性チェック・tree fingerprint 照合は実際は lease-dir と独立に機能し、
  専用 lease-dir で実質的に失われるのは reclaim 確認 (他 wave との受入投入順番調整) だけ」
  という技術的な反論を受け、コード再検証の上で自分の当初説明の一部 (3点を一括りにした
  部分) を訂正した。また「acceptance.lease が free なのに ticket queue が滞留する」
  という別の実バグ (`wave_land_window.py` の `_queue_head()` 関連と推定) の報告を受け、
  T-1458 のスコープ外と判断して専門セッションへ転送した。

## 次の一手差分

### 完了

- [T-1458] D662 対応の acceptance lease-optional 経路 (`--lease-optional`) を実装し、
  今後の全 wave が使う運用 docs 登録 (DW-O27) まで含めて完了し、受入 (16回目) が
  `non-attributable-only` で成功した。
  remaining: none
  base: 44a31e2b08dcd7da13a578eafa2d2710915db2518596c3bd699a8997bdcb9289
