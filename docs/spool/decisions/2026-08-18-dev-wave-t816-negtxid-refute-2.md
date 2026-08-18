---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t816-negtxid-refute
seq: 2
---

## {{D:t816-negtxid-refuted}}. 負txid false-green (ruling-inbox 2026-08-12 finding#1) は実装しないと裁定する

**決定:** `orchestrator/verifier/parse.py:213` 周りの負txid false-green
(`C -1 ...`/`E -1` が `missing=-1` になり欠番検出をすり抜ける) について、修正・
新規回帰テストのいずれも実装しない。

**理由:**
- 現行main (HEAD `a31832d9`) への直接実測で `C -1 0 2 1 0 0`/`E -1` を含むtraceを
  `parse_trace_dir()` に通すと `ParseError: txid must be a non-negative integer: -1`
  が即座に発生し、false-greenは再現しない。負txid拒否は commit `fb5e74a1`
  (2026-08-12, [T-816] 手順4) で既に追加され、後続の是正commit `a80daf83`
  (同日) でも維持されている。
- `orchestrator/tests/test_verifier.py:269-282`
  `test_negative_txid_is_rejected_before_gap_math_can_cancel_it` が同じ入力
  パターンを `verify_trace_dir()` 経由で既にpinしている (docstring:「{-1, 1} は旧
  max(txid)+1-len(txns) だと欠番を相殺できた。構文で拒否する。」)。
- 独立コンテキストの敵対チェック (fresh subagent, general-purpose, opus) が13通りの
  手動variantと1554通りの全数探索で追試し、反証できなかった。
- 密連番gap-checkロジック自体は commit `36a11936` (2026-07-02) から存在し、負txid
  guard (`fb5e74a1`, 2026-08-12) までの約6週間は構文レベルの穴が実在したが、
  実CCBench trace-hookはtxidを0始まりの単調atomic counterでのみ採番するため
  (`patches/README.md:385`)、負txidが実evaluation/mutationのtraceに出現することは
  構造的にありえない。過去のreal走行がこの穴を通過した実例はない。

**副次所見 (対応不要と裁定):** 同じ敵対チェックで、隣接するが別種のfalse-green
(「末尾txid丸ごと欠落」、witnessなしoptional APIパス) が見つかったが、これは既に
`orchestrator/tests/test_verifier.py:882-940` で「既知偽陰性のcharacterization」
として文書化・テスト済みの意図的挙動であり、実本番経路2つで独立に緩和されている
ことを確認した: `orchestrator/campaign/pipeline.py:1118`
(`expected_commits=trace_result.commit_count_witness` を渡し、witness欠落時は
fail-closed reject) と `orchestrator/campaign/silo_ladder_rung1.py:828-839,855`
(`_validate_correctness_commit_witness` がstdout witnessと記録txn数を独立照合)。
新規T番号・追加実装は不要と裁定する。一次資料:
`output/insights/2026-08-18_t816-negtxid-refute/README.md`。

**却下した選択肢:**
- 依頼どおり parse.py を編集し新規回帰テストを追加する — 既に同一シナリオをpinする
  テストが存在するため、追加は「純増検出力ゼロ」の重複になる (DW-S01 の既存被覆
  確認原則に反する)。
- 副次所見 (末尾txid欠落) を本waveのscopeへ繰り込んで実装まで行う — 依頼が明示
  した対象 (負txid) と異なるベクトルであり、段階導入/盛らない原則 (絶対規律5) と
  DW-S04 の「scope外のreal所見は実装せず裁定パッケージで返す」に従い見送る。
  実本番経路は既に保護されているため緊急性もない。
