---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-t810-test-isolation
seq: 3
---

## 再発

### F633

- **再発: 2026-09-29** — land 調整役が、撤去途中で `gitdir` を欠き `modules` だけが残る管理 dir が数分続く間に受入全走が走ると `test_t810_coordinator.py` の live 3 node が `cannot read worktree registration: file is absent` で決定的に赤になると報告し (t-2288 wave)、撤去と受入を窓で分けて land を遅らせていた。{{D:t810-skip-unlocked-absent-registration}} で本番の走査が gitdir も locked も無い管理 dir を飛ばすよう改めた。

## supersede 追記

- F633 **supersede: 2026-09-29** — 恒久対応「未実施」は古い。{{D:t810-skip-unlocked-absent-registration}} (ユーザー裁定) が本番の走査で gitdir 不在かつ locked 不在の管理 dir を飛ばす形で撤去途中の不在を閉じた。add 途中 (locked あり・gitdir 無し) と読み中変化は従来どおり拒否し、テストは既存の再試行で吸収、本番の coordinator は止まりうる。land 側の同型走査は未変更。
- F670 **supersede: 2026-09-29** — 「production は未変更」は古い。{{D:t810-skip-unlocked-absent-registration}} が消滅のうち locked の無いものだけを吸収した。読み中変化と locked 付きの消滅は従来どおり拒否で、本件の指摘 (消滅だけを名指しする修理は残差を取り残す) は有効のまま。
