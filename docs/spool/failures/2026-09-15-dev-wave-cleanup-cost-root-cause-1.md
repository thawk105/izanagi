---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-cleanup-cost-root-cause
seq: 1
---

## 再発

### F51

- **再発: 2026-09-15** — `/cleanup-branches` 実行中、撤去対象 worktree の追跡外ファイルを見るために
  `cd <worktree>` した時点で、背景セッションの作業ディレクトリが撤去対象の中へ移った。2026-07-20 の
  事例は cwd が最初から対象に固定されていたが、今回は**cwd が固定でないセッションが自分で入った**
  別経路である (harness が `cd` を追従して primary working directory を張り替える)。撤去前に
  main checkout へ戻して回避し、実害なし。判別 = 撤去対象へは `cd` せず `git -C` と絶対 path で
  扱う。撤去 step の cwd 検査 (対象配下なら停止) が本実行では機能した。§3 への明文化は
  {{T:cleanup-forbid-cd-into-retirement-target}} で起票済み。
