---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-acceptance-runtime-opt
seq: 3
title: 受入全走でtest_sort_swo_oracle.py 26件の赤を発見、自分の編集 (docs-onlyの2 fragment) に起因しないと判定した (D662 known-violation登録)
---

## 本文

- D662 (計算ノード混雑の恒常化を踏まえた受入・land運用簡素化) に従い、local main (acfb7616) を
  取り込んだ自分のbranchに対して受入全走 (`python3 tools/run_tests.py`,
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600`) を実行したところ、
  `orchestrator/tests/test_sort_swo_oracle.py` の26テストが失敗した
  (26 failed, 14242 passed, 96 skipped, 3 warnings in 203.57s)。
- **自分の編集に起因しないと判定した根拠**: `git diff --stat acfb7616...HEAD` は
  `docs/spool/decisions/*.md` と `docs/spool/worklog/*.md` の新規2ファイル・200行追加のみ
  (既存ファイルへの変更・削除はゼロ)。C++ SWO oracle テストへ影響しうる編集面が皆無であり、
  `tools/check_acceptance_reds.py` による個別再検証を要するまでもなく無関係と判断した。
- 失敗は全26件が同一ファイルに集中しており、代表的な1件 (`test_candidate_compile_failure_is_
  reject_not_unavailable`) の失敗詳細は `outcome='config-h-missing'` (masstree依存の
  config.h欠落と見られる) を示している。D591/D636で扱った同ファイルのmasstree依存解決
  (`IZANAGI_SORT_SWO_MASSTREE_ROOT`、`ccbench/build/_deps/masstree-src`) 周辺の
  環境依存問題である可能性が高いが、原因の完全な特定はこのwaveのscope外 (docs-onlyタスク) の
  ため行っていない。
- D662の運用 (項目4: 自分の編集に起因しない赤はknown-violation登録+裁定送付、項目6: 混雑や
  既知の不具合で開発全体を止めない) に従い、修正を試みずに次の一手として起票し、
  自分のwave自体はこのままlandする。

## 次の一手差分

### 新規

- {{T:sort-swo-oracle-masstree-config-h-missing}} **P1・新規**:
  `orchestrator/tests/test_sort_swo_oracle.py` の26テストが受入全走で一括失敗する
  (`OracleStatus.UNAVAILABLE` を返し `outcome='config-h-missing'`、masstree依存の
  config.h欠落と見られる)。2026-08-22 20:22頃の受入全走 (dev-wave-acceptance-runtime-opt、
  tested main acfb7616) で実測。原因調査・恒久対応が必要。詳細は本entry参照。
