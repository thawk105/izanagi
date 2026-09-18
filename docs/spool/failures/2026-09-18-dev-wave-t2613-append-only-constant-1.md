---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2613-append-only-constant
seq: 1
---

## 再発

### F43

- **再発: 2026-09-18** — [T-2613] wave の段 5 author 子 2 本 (発行側 / 受入側) が両方とも
  `failure_class=f43_fragment` で不受理 (`codex_exit_code=0`、`validator_rc=1`、報告 5,445 / 7,637 bytes)。
  原因は 2026-08-26 型と同じく**親の prompt 側の誤り** — plan / consult / review の prompt には
  `## 総括` を書いたが、author 2 本の「完了報告に必ず含める」節に `## 総括` 見出しを要求しなかった
  (`DW-O01` の「prompt に `## 総括` 必須」を author 段で落とした)。実装は両 worktree に正しく
  あり、親が未受理と明記して報告本文を段 6 レビュー 2 本の入力 (データ) に渡し、レビューが実装を
  監査した (`DW-O01` の「未受理は未完了と記し次の子に監査させる」)。fix 子の prompt には
  `## 総括` を最初の見出しとして明示し、2 本とも受理された。恒久対応は従来どおり親検収 +
  `check_codex_output.py` で、reference は編集しない。
