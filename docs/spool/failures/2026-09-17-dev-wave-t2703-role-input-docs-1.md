---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2703-role-input-docs
seq: 1
---

## 再発

### F106

- **再発: 2026-09-17** — 役割入力文書の wave。今回は受入全走でも変異本走でもなく、**計算ノードへ dispatch した
  焦点走 (skip 理由を取るための `-rs` 再走) の走行中**に、親が段 6 の must-fix を役割 .md へ適用した。dispatch job は
  worktree を共有 FS 越しに live で読むため、ledger 未更新の状態を計測して `test_codex_agents` / `test_codex_role_runtime`
  が adapter parity drift で 8 failed になった。単独再走 (fix + render 後) は 2084 passed / rc=0 で消えた。根本原因は
  F106 と同一で、「dispatch 済みの走行は起動時点の木を見る」と誤認して待ち時間に worktree を触ったこと。恒久対応は
  F106 のまま。**焦点走であっても、投入から結果取得までは tracked file を編集しない。** 汚染した走行は合否に使わず
  skip 理由の参考にだけ使い、権威の走行を取り直した。
