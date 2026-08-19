---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t755-q2-mocc-trace
seq: 2
---

## {{D:mocc-trace-hook-edit-surface}}. T-755 の mocc trace-hook は限定的に編集面へ開くが、変異探索面にはしない

**決定:** T-755 Q2 の mocc correctness-trace v2 実装・検証に限り、`cc/mocc/transaction.cc` を
`EVOLVE_BLOCK_SOURCES`、`ALLOWLIST`、および `hooks/guard_write.py` の写しへ追加する
(実装済み、`orchestrator/campaign/source_digest.py:81-88`)。これは D16 の「trace-hook は
`izanagi-trace` submodule branch (=commit) へ格納する」原則を mocc に適用するための
限定的な authoring authorization であり、mocc を Phase 3 の mutation axis・template driver・
auditor 面へ追加する決定ではない。4 driver ファイル・`mocc_op_element.hh`・
`transaction.hh`・`include/trace.hh` は編集対象にしない。

D16 内の「一回限りの試作例外」([T-109](a) 紐付け、2026-07-26 ユーザー裁定) は T-755 へ
自動適用しない — 紐付け先が別タスクであり、si の trace-hook が人間直接 commit だった
事実は「例外が消費されていない」ことの傍証にはなるが証明にはならないため、この条項を
再利用するにはユーザーの再裁定が要ると判断した (今回は再裁定を求めず、EBS 拡張を
正式な信頼境界拡張として選んだ)。

**理由:**
- 現行 write gate (`hooks/guard_write.py`、Codex も `.codex/hooks.json` 経由で同一 gate を
  通ることを実測確認済み) は EBS 外の mocc source を拒否するため、D16 の branch 格納方針を
  実装するには正式な編集面追加が要る。
- `orchestrator/tests/test_campaign.py:10394-10412`
  (`test_lock_path_edit_surface_requires_auditor_live`) は `cc/silo/transaction.cc` の
  リテラル比較であり EBS の新メンバへ汎用的に効かないことを実測確認した。mocc 追加で
  実際に赤くなるのは `test_edit_surface_constants_exact_relationship` の exact-pin
  tuple だけであり、auditor-live 前提とは無関係な機械的な値更新で足りる。
- EBS に追加することで mocc source も digest・include 検査・TRACE diff-of-diffs の対象になり、
  gate 回避ではなく EBS・ALLOWLIST・hook の三面を明示同期する信頼境界変更として扱える。

**採用した構造:** `orchestrator/campaign/source_digest.py` の `EVOLVE_BLOCK_SOURCES` タプルへ
`cc/mocc/transaction.cc` を末尾追加 (digest pre-image 順序保存)、`ALLOWLIST` も同期。
`orchestrator/tests/test_s6_proposal_rounds.py` の凍結面比較は `==` (完全一致) から
`<=` (frozen ⊆ live) へ変更し、mocc が S6 (LLM 変異提案ラウンド) の対象になったことがない
trace-hook 専用の live-only 面であることを許容しつつ、live 側の**縮小**は従来どおり検出する
(手動 mutation で実証済み、`docs/worklog.md` 本 wave のエントリ参照)。
hermetic CCBench fixture (`orchestrator/tests/test_campaign.py`) へ最小の fake
`cc/mocc/transaction.cc` を追加し、EBS 拡張後も `source_digest.py` の全走査ループが
fails-closed で落ちないようにした。

**却下した選択肢:**
- **`patches/` 経由の inert patch (D16 の一回限り試作例外の再利用)**: 実 submodule への
  最終適用 (実 TRACE=1 ビルド・実測) は結局どちらの経路でも人間手番かそれに準ずる
  git commit 操作が要り、gate 回避の実利が薄い。かつ [T-109](a) への紐付けを T-755 へ
  流用する根拠が弱い (段3 レンズB の分析)。
- **S6 凍結面比較を `==` のまま維持し mocc を凍結面へ追加すること**: mocc は実際には
  S6 proposal round の対象になったことが無く、凍結面へ追加すると「LLM 変異提案の
  対象だった」という事実と異なる記録になる。

**この決定が閉じないもの (正直に):** mocc の X/P/I (D38/D41/T-152 相当) 行、
TPC-C/BOMB workload での E行-counter一致 (D295 が YCSB のみ allowlist する既存設計を
継承、mocc 固有の追加検証はしていない)、mocc の温度依存ハイブリッドロック
(cold=OCC/hot=悲観ロック) が D38 相当の lock coverage 不変条件を満たすかどうかの
実証は、いずれも本決定では閉じない。**将来 `cc/mocc/transaction.cc` を Phase 3 の
変異探索対象 (EVOLVE_BLOCK hole) にする wave は、今回の trace-hook 許可を
safety net とみなさず、独立の auditor-live 相当の機械実証を別途用意すること。**
