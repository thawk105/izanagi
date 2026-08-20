---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1292-backoff-ipc-missing
seq: 3
title: '[T-1292] backoff_sweep_report.py の欠測IPC偽装を修正した — 段3敵対相談がplot_backoff.pyとの互換性問題を発見、変異5/5 KILLED (コード+テスト、branch worktree-dev-wave-t1292-backoff-ipc-missing)'
---

## 本文

依頼は worklog archive entry 618 ([T-1292] 項) の再訪で、`backoff_sweep_report.py` が
欠測IPCを `g.li.get("ipc") or 0` で literal `0`/`0.00` へ変換し「perfでIPC=0を測った」と
読める偽表示を出す件。DW-G03 (族一般化には独立2例) は自分でgrep再実測し他ファイルに
同型0件と確認、局所修復のまま進めた。

**段2 codexプラン (plan、1本) は `_format_ipc` ヘルパー案・`.dat`側を `"—"` にする設計を
提示。段3敵対相談2レンズ (consult、sol/luna各1本) のうちレンズB (luna) が実装コードで
未検証だった致命的な穴を発見した: `tools/plotting/plot_backoff.py:166` が `reports/*.dat`
を汎用的に読み `float(parts[3])` でIPC列を無条件パースしており、`"—"` を書くと
`ValueError` になる。** 親が直接コードを読んで裏取りした。段4裁定でplan v2へ修正
(`.dat`側は `float("nan")`、Markdown側は既存の `"—"` 慣習を維持) し、変異事前登録
(M-1〜M-5、M-4が `"—"` への回帰を検出する最重要変異) を確定した ({{D:g04-display-fix-not-new-capability}}
参照)。

段5実装 (author、1本) はplan v2に忠実な差分 (`_format_ipc`新設・型注釈修正含む) と
新規テスト5本 (ipc=None/0.0/実測値混在・全点欠測・キー欠落・`plot_backoff.load_campaign()`
のnan回帰) を書いたが、Pegasus dispatch認証エラーで実走できず「実装済み・未実走」と
正しく自己申告した。親が `python3 tools/run_tests.py orchestrator/tests/test_backoff_consumers.py -q`
で実測し12 passed (既存7件+新規5件、回帰なし)。

段6敵対レビュー2本 (review) はreal所見0件。レビューB (変異頑健性担当) がM-4の実際の
kill経路が登録した `ValueError` ではなく手前の `math.isnan("—")` によるassert不一致
だと指摘 (real・minor、fix不要)。変異matrix本走はbaseline PASSED・5/5 KILLED・
matches_expectation全件true・SURVIVED 0・MISMATCH 0 (probe走で実測したfailed_nodesを
そのままKILLED期待へ転記、DW-M08の「初回probe→完全集合再登録」どおり)。

変異harness投入は2回orphan-holdで空振りした (F383再発、詳細は同fragment参照)。いずれも
`dispatch_compute.py` の accounting-grace timing race で、テスト自体は正常終了していた
(job stdoutで`child_rc=0`確認)。既定復旧手順 (手動qdelせずqstat内容で不在確認→hold削除→
新パスで再投入) で解消した。

工数: codex子6本 (plan 1・consult 2・author 1・review 2)、全てcheck_codex_output.py rc=0。
統合commit = `4c6dc19a`。段8自己改善: 候補を検討したが、dev-wave入口・reference文書の
変更を要する候補は無かった (F383再発の記録のみ、上記)。

## 次の一手差分

### 完了

- [T-1292] `orchestrator/campaign/backoff_sweep_report.py` のIPC欠測偽装 (`or 0`による
  None/実測値0の混同) を `_format_ipc` ヘルパーで解消した。.dat側は `float("nan")`、
  Markdown側は既存の `"—"` 慣習、「読み」節はIPCの測定状況だけを条件にする文言へ改めた。
  新規テスト5本追加、既存7件+新規5件=12 passed。変異5/5 KILLED。scope外
  (throughput_tps/abort_rate、digest.pyのperf_observation欠落) は理由付きで見送った。
  remaining: none
  base: d5dab8874aea01788f4e788e02fbef2ce79e1a2fcf3f13007b01a7cfaf58d799
