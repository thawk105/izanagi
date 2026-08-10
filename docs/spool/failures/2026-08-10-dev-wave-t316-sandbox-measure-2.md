---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t316-sandbox-measure
seq: 2
---

## 新規

### {{F:stale-checker-range-audit}}. 取り込み前の古い checker で incoming range を監査し、登録済みの既知違反を赤と誤認した [手順漏れ] [ドリフト]

- 事象: 受入直前の `check_ai_provenance.py --range HEAD..main` が 4 違反で赤になり、
  受入投入を 2 度止めた。実体は別 wave の merge commit 4 件で、**main 側の checker には
  既知違反として登録済み**だった。wave 側 worktree は取り込み前の古い checker を持つため、
  その登録を知らないまま赤を出していた。取り込み後の full 監査は同じ木で緑になる。
- 根本原因: `DW-O17` は「`OLD_HEAD..HEAD` は補助で、correction を含むときは両 commit を含む
  range か full 監査だけを権威とする」と定めている。既知違反台帳の更新は correction であり、
  それが incoming 側にあるとき、**取り込み前の checker で incoming range を測る手順自体**が誤り。
  他セッションの land 済み履歴を書き換えたくなる方向へ誘導する点で有害である。
- 恒久対応: 受入 script の incoming gate を廃し、**取り込み後の full 監査**を権威にした
  (本 wave の `acceptance.sh`)。`DW-O17` の既存規定で説明できる誤用なので新しい規則は足さない。
- 再発検知: 同じ形の赤が出たら、まず incoming 側 checker
  (`git show main:tools/check_ai_provenance.py`) に当該 SHA が登録されているかを見る。
  登録済みなら wave 側 checker の陳腐化であって、履歴の欠陥ではない。

## 再発

### F125

- **再発: 2026-08-10** — 受入 lease 取得直後の main 取り込み merge で再発した。競合なしの
  auto-merge だったが combined diff がテスト 2 件を含み、message が `role=integrator` 1 行
  だけだった。取り込み後の full 監査が 1 新規違反として検出。実装面を書いたのは本 wave の
  Codex 子なので `role=author` を併記して amend し、再走で全走 rc=0 を確認した。
  merge message 生成器 (wave の `write_merge_msg.py`) が integrator 行しか書かない形だったのが
  直接原因で、生成器側を直した。
