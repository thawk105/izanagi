---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-test-failure-triage
seq: 1
title: 既知のテスト失敗を棚卸しし実測した — 登録済みの赤は間欠 flake 1 node のみで所有者は [T-476]、実測は 0 failed (docs のみ、branch worktree-dev-wave-test-failure-triage)
---

## 本文

- ユーザー依頼「既知のテスト失敗は今何件発生しているか、発生していれば解決せよ」に対する棚卸し
  wave。段 4 で **実装しないと裁定**したため段 5・6 を飛ばした (`DW-S04`)。実装差分が無いので
  変異 matrix は射程外だが、依頼そのものが実測であるため受入全走は行った。
- **実測 (main 241808e9 相当の wave worktree、計算ノード request 889825、535.52s):
  6182 passed / 19 skipped / 0 failed (rc=0)。** 赤は 1 件も無い。
- **登録済みの既知赤は 1 node のみ** =
  `test_reflux_origin_ledger.py::test_v04_global_flock_race_reentry_and_public_signature`
  (`:711` の `assert probe_state == "blocked"`)。並列受入全走の負荷下でだけ発火する間欠赤で、
  単独走行は緑。ユーザー裁定の既知赤 waiver **W2** が条件付きで許可しており、失効は [T-476] の land。
  機序は既に確定済み (子の `write_text` が生成と内容書込の 2 段であるのに親が `exists()` で待つため
  空ファイルを読む) で、修正は [T-476] の branch (main の 7 commit 先) に実装済み・受入緑。
  本 wave 実行中も同 wave が land 試行中であったため、**重複実装せず非接触とした**。
  もう一方の waiver W1 ([T-407] の ruleops 非 UTF-8 blob) は解消済み・失効済みで、対象 node も緑。
- xfail marker は repo 全体で 0 件、skip は 19 件 (busybox / bundled Codex runtime / submodule 条件)。
  「既知赤」を機械が保持する専用台帳は存在せず、正本は worklog の waiver 裁定文である。
- **手順違反 1 件 (自己申告)**: 別セッションの変異 harness
  (`dev-wave-t452-t453-clock-authority`、約 2 時間見込み) が走行中であることを確認せずに
  受入全走を投入した。結果が緑だったため観測自体は有効 (汚染は偽の赤を作る方向にしか働かない) だが、
  投入判断は誤りである。同じ罠は本日 3 例目 — worklog (210) の 79 failed、[T-476] 親の自己申告、
  そして本 wave。`DW-G03` の「独立 2 例」条件は既に満たしており、制度化は
  [T-476] 段 8 の改善候補 2 が所有する (本 wave では重複起票しない)。
- 段 8 自己改善: 候補 1 件を検討したが不採用。上記の禁止は既に [T-476] が所有しており、
  docs 予算の hard ceiling ([T-491] が同じ壁で停止済み) を消費する重複契約を足さない。

## 次の一手差分

### carry

- [T-476]
