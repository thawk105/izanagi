---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2521-fig5-usage
seq: 1
title: [T-2521] 旧fig5の用途制限を期限なしとする追補 (docsのみ、branch worktree-dev-wave-t2521-fig5-usage)
---

## 本文

- D1936項21を適用。D1645の「正しい新attemptが出るまで」という期限を旧fig5について外す。
  旧図が測ったBACK_OFF有無は新attempt取得では変わらず、採用静的backoffの結論・図には使わない。
- 起動時に登録worktreeの論文図表README差分と関連handoffを照合した。同名READMEに差分表示が
  あったT-2515とt2417-recovery-authorは現mainとworking bytesが一致し、独自の競合変更は無かった。
- DW-C00軽量版、D95 docs-onlyで子0走。実装面差分0により変異matrix免除。新しいgate・検査・
  台帳・一般化、旧画像・provenance JSON・統計・凍結稿の変更、新fig6との前後比較・新規性主張は無し。
- 関連走はtools/run_tests.py経由でtest_check_docs.pyとtest_s1_9pair_figure_provenance.pyを実行し、
  601 passed / 3 skipped、113.74秒、rc0。skipは既存growth hold 3件で新設していない。
  pegasus02上のbounded local予算3427053536 bytes、観測ピーク3335876608 bytes。
  これは関連走であり、最終受入全走は記録commit固定後に行う。
- git diff --check、check_docs、check_codex_agentsはrc0。旧凍結captionを含む既存行は削除0。
- dev-wave改善候補は現時点なし。終端で自己改善契約を再読しhandoffへ確定記録する。
  改善実装・次wave起動・pushは行わない。

## 次の一手差分

### 完了

- [T-2521] D1936項21に従い旧fig5の用途制限から期限を外し、論文ストーリーと図表READMEへ追補した。
  remaining: none
  base: 8450bd0be4a4c2b1c284bdcbb32d40b3ae79d1d852e55feb11fae1dbf68d9f99
