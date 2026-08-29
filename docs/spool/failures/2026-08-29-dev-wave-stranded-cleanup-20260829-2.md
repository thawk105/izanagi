---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-stranded-cleanup-20260829
seq: 2
---

## 再発

### F633

- **再発: 2026-08-29** — 掃除側で踏んだ。棚卸しで作った撤去リスト 56 本のうち **24 本が、
  実行が対象へ到達する前に別 session の撤去で消えていた** (`git worktree list` は走行中に
  116 → 61 本へ動き、私自身の撤去は 32 本、branch 削除は 0 件)。本件は F633 の未実施対応が
  挙げる「生きた登録でなく走行開始時の snapshot を読む形へ変えれば構造的に閉じる」を反証する。
  snapshot は列挙時点の一貫性を与えるだけで、列挙から個々の対象へ着手するまでの窓
  (本件は数十分) を閉じない。閉じたのは対象ごとの実行直前検査
  `tools/check_worktree_occupancy.py` で、消えた対象に `status=invalid-target` (rc=2) を返し、
  detach と削除の前で fail-closed した。裁定に要るのは snapshot 化ではなく、
  一括操作の各要素へ実行直前の再検査を義務づける形である。
