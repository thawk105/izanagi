---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-paper-results-ja
seq: 1
title: 本体論文の日本語結果・考察を既存証拠から起草する（docsのみ、branch worktree-dev-wave-paper-results-ja）
---

## 本文

- 新規ユーザー執筆依頼。D1598・D1936、paper-storyのstale注記、既存results稿と一次資料、方法稿を照合した。
  素材: `output/insights/2026-09-10/paper-results-ja/results-discussion.md` に本文と3表を作成した。
- 起動時にinsights-date-layoutの所有と配置規約を確認。中断後に再開した同waveの資料移動・実装には触らず、
  新規資料の日付配下規約へ合わせた専用枠に保存した。旧凍結稿・方法稿は上書きしていない。
- A2の外部一次入力12件は実在とSHA256一致を確認。raw標本の中央値4値・利得2値と旧sweep利得3値を再計算した。
  P2-5は後発のp値訂正を採用し、S1bの成立とS1a/S2/S3の不成立を分離した。本文リンク不達は0。
- observed-positiveは標本中央値の比較に限り、別trace走の正しさ、有意性、LLMの必要性を区別した。
  K2はland済みの既存候補再評価として採用し、新規CCと呼ばない。B4の詳細診断効果は未取得のままにした。
- 起稿中にlandしたT2514は失敗detail保存だけとして反映し、性能実測へ数えなかった。
  未landの床値・policy対照等は進行中に分離した。新規実験・英訳・文書シリーズ・一般化は追加しなかった。
- DW-C00のdocs-only軽量版で子ゼロ。独立レビュー済みとは主張せず、実装面ゼロの変異matrix免除を適用した。
- checkout中にsubmodule初期化を先行した順序不適切を訂正。再帰初期化とclean確認後、前進したmainを監査して
  ff-onlyで取り込み、fresh startupを通過した。赤のままrepo本文編集へ進んでいない。
- 関連test_check_docs.pyはrun_tests.py経由で572 passed / 3 skipped、991436.nqsv、11.88秒、child rc0。
  初回bounded localは1600 MiB上限に達して判定未取得となり、runnerが計算ノードへ自動dispatchした。
  実repoのcheck_docs / check_codex_agents / git diff --checkはrc0。独自の検査機構やテストは新設していない。
- この記録時点で最終受入全走は未実施。専用job rootは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-ja/`。
- 専用handoffのdev-wave改善候補はなし。自身の起動順序の誤りは既存命令で防げるため規約を増やさない。
  自己改善実装・次wave起動・pushは行わない。

## 次の一手差分
