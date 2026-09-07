---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2411-a6-readheavy
seq: 3
---

## 新規

### {{F:a6-collect-publish-blockers}}. 測定は完走したのに認証成果物を公開できず 2 段で止まった [手順漏れ] [環境前提]

- 事象: A-6 read-heavy の実走が `driver_rc=0` で完走し受領証も揃ったのに、`collect` が
  2 回続けて非 0 で止まった。1 回目は
  `qsub -v is not bound to workload and current pin`、2 回目は
  `tracked destination is not a fresh exact leaf`。
- 根本原因: 独立な 2 件が重なっていた。(1) `collect` は投入時に記録した policy の
  **絶対 path** と、実行時に解決した policy の path を突き合わせる。投入は隔離した投入用
  checkout から行い、`collect` を記録用 worktree から実行したので不一致になった
  (**`collect` は投入した checkout から実行する**)。(2) policy の `tracked_destination` が、
  前走失敗時に手で書いた insight directory を指していた。`collect` は空の新しい leaf を
  要求するので、以後この policy では永久に公開できない状態だった。
- 恒久対応: (2) は `tracked_destination` を空の新しい leaf へ更新して解いた。この key は
  `_protocol_preimage` に含まれないので `protocol_sha256` は動かない (実計算で確認)。
  **公開先と手書き insight の置き場を同じにしない。**
- 再発検知: (1) は既存 A-2 受領証が現配置で再検証できない件と同じ族であり、
  投入 checkout の path が生きているかに依存する。撤去前に `collect` を済ませる。

### {{F:noreplace-fix-left-sibling-writer-behind}}. Lustre の EINVAL 対策が兄弟 writer 1 箇所だけ取り残されていた [consumer 取り残し]

- 事象: A-6 read-heavy の実走が、条件 gate を 2 cell とも通過した直後に
  `[Errno 22] Invalid argument` で 36 秒で終了した。
- 根本原因: Lustre に `renameat2(RENAME_NOREPLACE)` が無い (実測: /work・/home で EINVAL、
  ノード内蔵 /tmp で成功)。同じ file の materialize 経路は先行 commit で代替を得ていたが、
  regular file を publish する `_atomic_write_bytes_noreplace` は代替を持たないまま残っていた。
- 恒久対応: {{D:a2-noreplace-link-publish}}。
- 再発検知: 許可 errno・上書き禁止・非許可 errno の伝播・後始末失敗時の非失敗を、
  それぞれ 1 本のテストで固定し、変異 4 件で単独帰属を確認した。
- 併発: 同じ欠陥へ main 側の別 wave が独立に、より弱い修復を先に着地させていた。
  受入の post-claim merge が競合し、Codex `role=author` の合成子による合成が必要になった。
  **同一の欠陥へ複数 wave が同時に着手していることを、着手前の編集面重複検査は捕まえられない**
  — 検査は path の重なりを見るが、main 側 wave はその時点でまだ着地していなかった。
