---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1414-dispatch-latch
seq: 2
---

## {{D:dispatch-latch-narrow-safe-relax}}. dispatch orphan-hold latch は「積極的な不在確認」だけを安全側緩和の根拠にする

**決定:** `tools/pegasus/dispatch_compute.py` の `_fresh_qstat_gated_qdel()` 内 `denied()` は、
`reason=="request-absent"` かつメインループが既に `terminal_history_end=True` を確定済み
かつ `elapsed()` 取得に例外がない場合だけ `job_may_remain=False` にする。それ以外の全理由
(判定不能・エラー系・terminal_history_end 未確定の request-absent) は従来どおり
fail-closed (`job_may_remain=True`) を維持する。あわせて、メインループの END 判定
(`_scheduler_state()` の結果が `"END"` の場合) は `current.returncode == 0` のときだけ
有効とし、RUN/QUE/HLD の検出は rc を問わない元の挙動 (bookkeeping レベルの
fault-tolerance) を維持する。`_orphan_hold_required`/`_latch_orphan_hold`/
`_best_effort_qdel` の契約 (`job_may_remain=True` を受けたら create-only で必ず hold する)
は変更しない。

**理由:**
- `docs/failures.md` F383 が記録する非決定的 orphan-hold (受入 checker・変異 harness 双方で
  複数回再発、直近は本 wave 自身の変異 matrix 実行中にも別トリガーで2回観測) の根本原因
  ([T-1409] 診断) は、accounting-grace 超過後の後追い qstat が「対象 job が既に存在しない」
  ことを検出しても、これを一律 fail-closed に倒す設計にあった。
- 安全性を緩めてよいのは「対象が scheduler 上に存在しないと積極的に確認できた」場合だけに
  限定し、判定不能・エラー系は緩めない — 規律2 (正しさゲートを緩める変異を許さない) の
  精神を、CC variant の正しさ判定ではなくこの運用インフラ latch にも適用した。
- メインループの END 判定を rc=0 限定にする補正は、段3 敵対相談 (レンズA) が発見した
  「rc≠0 の qstat 応答に偶然 END 相当の状態文字列が含まれると偽陽性になりうる」という
  懸念を閉じるために必須だが、対象を END 判定だけに絞ることで、同じ関数が持つ
  既存の意図的な fault-tolerance 設計 (rc≠0 応答からの RUN 検出で queue-wait bookkeeping を
  進める) を壊さない。段5 の当初実装 (rc≠0 なら state 計算を一律抑制) はこれを壊し、
  親が実測 (pytest 焦点走) で回帰を発見した。

**却下した選択肢:**
- accounting-grace 窓の単純延長・probe 投入間隔の調整 — 原因箇所 (latch 条件自体) から遠く、
  同型の非決定性を別の閾値へ先送りするだけと判断した (ユーザー裁定原文どおり)。
- メインループの `_scheduler_state()` 呼び出しを一律 `current.returncode == 0` 限定にする
  (段5 当初実装) — 既存2テストが pin する RUN 検出の fault-tolerance 設計を破壊すると
  実測で判明したため不採用。
- `success-request-absent` の判定自体 (`_qstat_mentions_request`) を、空応答・無関係応答を
  除外するようさらに厳密化する — 段3 レンズA が理論的な残余懸念として指摘したが、
  `terminal_history_end` との組み合わせで十分保守的と判断し、対象追加によるスコープ
  拡大 (規律5) を避けた。
