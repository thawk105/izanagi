---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-wave-startup-cost
seq: 1
title: wave 起動の固定費を実測した — 本体は superproject 31,699 file の checkout (worktree add、混雑下の代理区間 18〜96 秒・中央値 75 秒) で、submodule 再帰初期化は直接計測 7.46 秒 = 3 処理の 7.5% → 依頼の条件「大半」は不成立、`--reference` / alternates による短縮は実装しない (docs のみ、branch worktree-dev-wave-wave-startup-cost)
---

## 本文

- 依頼 (台帳 ID 未起票、主題 slug) を軽量版 + 診断で処理した: 段 1 実測 → 段 3 相談 1 本 (codex read-only、sol) → 段 4 裁定 → insight 起草 → 段 6 独立 read-only レビュー 1 本 + 焦点再レビュー 1 本 → 記録。実装面の差分ゼロ (D95 の docs-only 例外、変異 matrix 免除)。設計判断 (却下案) は {{D:no-submodule-reference-alternates}}。
- 実測 (一次資料は insight `output/insights/2026-09-21/wave-startup-cost/`): 自 wave の直接計測は EnterWorktree 85 秒 (うち git 代理区間 65 秒) / submodule 再帰初期化 7.46 秒 / 開始 gate 6.70 秒 = 3 処理 99.2 秒、submodule は 7.5%。今朝 07:32〜07:39 に近接起動した 10 worktree の git 管理 file の mtime では worktree add の代理区間 18〜96 秒 (中央値 75)、submodule 3 段の代理区間 4〜21 秒 (中央値 8)。superproject は tracked 31,699 file (`output/insights` 24,420 = 77%)、872 MB、submodule 3 段は 1,440 file。主 store の pack は worktree の module と同 inode (hardlink 共有済み)。
- 段 3 相談の所見 13 件 (must-fix 6 / should 5 / 判定不能 1 / refuted 1) は「実装しない」を維持しつつ根拠を訂正させた: mtime は処理境界でなく代理区間、昨日の t2797 標本は 2 木が 48 秒並走、`--reference` は local path の clone で hardlink 複製を省かない (git 2.34 `clone.c` は `--shared` でない限り `copy_or_link_directory()`) ので正の短縮量は未実証、+60 秒の同定は未了。段 6 レビュー A は NO-GO (must-fix 5: 残差の親への帰属、木の本数と概算、CPU 比の断定、一次記録の欠落、HANDOFF 標本の要約) → 親が README を訂正 → 焦点再レビュー A の結果は insight §9。
- 裁定パッケージ (insight §7、実装せず): 次の局所候補は (a) git 既存機構 `checkout.workers` (並列 checkout) の local config 1 行、(b) sparse-checkout で `output/insights` を外す (設計変更)、(c) 木の本数を減らす運用。(a) は job dir の独立 clone で ABA 系列 1 回 (workers=1: 50.6 秒 / 8: 20.4 秒 / 1: 45.3 秒、混雑下) の予備診断だけがあり、採用効果にはしない。推奨は別 wave で n ≥ 3 の交互計測をしてから採否を判断する。
- ユーザーの「受入 fresh 木の +60 秒」は、受入が git の木を作らない (静的確認) ため、T-2817 の受入 `pre` 61.9 秒と test 内部の base copy 64.2 秒の 2 候補が残り、同定は未了として残した。
- 工数: codex 子 = consult 1 + review 1 + focus 1 の 3 本、親の probe 1 系列 (login、約 3.5 分)、焦点走 (login → 計算ノード dispatch) 1 回。wave の壁時計は起動 gate 07:40 JST (`startup-gate.log`) → 記録 commit まで。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定するため insight §9 に追記する)。

## 次の一手差分
