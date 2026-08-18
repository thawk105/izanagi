---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t816-negtxid-refute
seq: 1
title: parse.py:213 の負txid false-green 修正依頼を反証で棄却する (docsのみ、branch worktree-dev-wave-t816-negtxid-refute)
---

## 本文

- 依頼は `orchestrator/verifier/parse.py:213` の負txid false-green
  (`C -1 0 2 1 0 0`/`E -1` が `missing=-1`になり欠番検出をすり抜ける) の修正・
  回帰テスト新設。根拠は
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step4-blockers-summary.md`
  の段3 real所見1件目 (2026-08-12時点、[T-816]の大きい裁定待ちに巻き込まれ未起票)。
- **段1 brief前の前提実測 (DW-S01) で棄却 (refuted) と判明。** 現行main
  (HEAD `a31832d9`) へ実際に `C -1 0 2 1 0 0\nE -1\n` を通したところ
  `ParseError: txid must be a non-negative integer: -1` が即raiseされ、
  false-greenは再現しない。負txid拒否は commit `fb5e74a1` (2026-08-12,
  [T-816]手順4) で追加され、後続の是正commit `a80daf83` (同日) でも維持されたまま
  現main tipに至る。ruling-inboxの当該ファイルは「実装差分ゼロ」の2026-08-12時点
  スナップショットであり、同日中の後続実装で副作用的にこの穴が塞がれたとみられる。
- 既存回帰テスト `orchestrator/tests/test_verifier.py:269-282`
  `test_negative_txid_is_rejected_before_gap_math_can_cancel_it` が、ruling文と
  同じ機序を docstring で過去形にして既にpinしている。新規テストの追加は
  「純増検出力ゼロ」の重複になるため見送る (DW-S01 既存被覆確認原則)。
- 過去露出窓の確認: 密連番gap-checkロジック自体は commit `36a11936` (2026-07-02)
  から存在し、負txid guard (`fb5e74a1`, 2026-08-12) まで約6週間、構文レベルの穴は
  main に実在した。ただし実CCBench trace-hookはtxidを0始まりの単調atomic counter
  でのみ採番する (`patches/README.md:385`) ため、負txidが実trace に出現することは
  構造的にありえない。**過去のreal mutation/evaluation走行がこの穴を通過した実例は
  ない。**
- 独立敵対チェック (fresh subagent、general-purpose、opus、168997 tokens、
  tool_uses 54) が13手動variant+全数探索1554通りで追試し、負txidでの再現不可を
  追認した。同チェックが提示した副次所見 (「末尾txid丸ごと欠落」による別種
  false-green) は、`test_verifier.py:882-940`
  「既知偽陰性のcharacterization」節で既に文書化・pin済みの意図的挙動と判明。
  実本番呼び出し経路を全数確認 (`grep -rn "verify_trace_dir(" orchestrator/`) した
  結果、実在する2経路
  (`orchestrator/campaign/pipeline.py:1118` の `expected_commits=` 配線 + witness欠落
  時のfail-closed reject、`orchestrator/campaign/silo_ladder_rung1.py:828-839,855`
  の独立witness照合) がいずれも独立に緩和しており、対応不要と判定した。
  一次資料: `output/insights/2026-08-18_t816-negtxid-refute/README.md`。
- **段4裁定: 実装しない。** parse.pyの編集もテスト新設も行わない。scope外の副次所見
  (末尾txid欠落) も同様に対応不要と裁定し、ユーザー裁定へ差し戻す新規論点は無い
  (実本番経路で既に緩和済みのため)。稼働中5+1 wave
  (s8c-c12-c04-c11/t1352-c07-result-judge/t1353-c03-c08/t688-job-kill-evidence-r2/
  t1348-c09-c10-consumer/t1363-c06-budget-consumer) とのfile衝突なしを確認済み。
- 受入全走: green。verdict=child-green, raw_child_rc=0, red_nodeids=[],
  flake_nodeids=[], tested_main=tested_tip=`a31832d9a021a907907266647ea49b9b7f0b5de5`
  (実装差分ゼロを裏付け)。
- ユーザー依頼は「まずT番号を起票し」と明示したが、事後にT番号を新設して即座に
  `完了`とする経路はfragment形式が構造的に許さない (`完了`/`更新`は対象itemの
  現本文digestを要求するが、新規itemには折る前の現本文が存在しない)。本waveは
  「実装差分ゼロで反証」の precedent (worklog #663「受入全走のwallは...」、
  設計判断は {{D:t816-negtxid-refuted}}) に倣い、次の一手への新規T番号は追加せず
  本文とdecisions fragmentで完結させる。

## 次の一手差分
