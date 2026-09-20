# 依頼文 (逐語、/dev-wave の引数、2026-09-21 07:3x JST)

wave 起動の固定費 (EnterWorktree → submodule 再帰初期化 → 開始 gate tools/check_wave_startup.py → 受入 fresh 木の +60 秒) を直近
  wave 12 本の startup-gate.log と HANDOFF.md の時刻から実測する (着手直前の local main から fresh worktree)。submodule
  初期化が固定費の大半なら、git submodule update --reference <主 checkout の module store> 等の既存 git 機構で初期化を短縮する局所修正 1
  件を、効果を同じ資料で見積もってから Codex author (D95) で実装する (worktree の登録・lock・開始 gate の受理条件・submodule の pin
  一致検査は変えない、alternates の参照先が消えると壊れる条件は runbook に 1 行で書く)。規律 2 を緩めない。本題だけ。gate・台帳・一般化の追加は
  scope 外。
