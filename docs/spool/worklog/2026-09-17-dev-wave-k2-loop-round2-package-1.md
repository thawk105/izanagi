---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-k2-loop-round2-package
seq: 1
title: K2 ループ次巡 (保存済み proposal-2 value=25 の 1 評価 + proposal-3 への還流) の認可を求める裁定パッケージを起草した (docs のみ、branch worktree-dev-wave-k2-loop-round2-package、実装面の差分ゼロにつき DW-S04 により変異 matrix 免除・受入全走は実施)
---

## 本文

- ユーザー依頼は「[T-2588] の続き (台帳 ID 未起票)。K2 ループの次巡 (保存済み proposal-2 `value=25` の評価と、
  その実測を proposal-3 へ戻す 1 巡) の認可を求める裁定パッケージを起草する。実走はしない。1 巡目の結果・
  次巡の目的・範囲 (既存経路のみ・新機構なし)・予算・停止条件・critic 診断が型付き入力へ届かない既知限界を
  簡潔に書き、rulings-inbox の控えと spool fragment の形で /rulings が拾える状態にする。新しい承認管理機構は
  作らない。docs のみ、実装差分ゼロ」。
- **閉じた (起草として)。裁定は未着。** パッケージ本体は
  `output/insights/2026-09-17/k2-loop-round2-package/README.md` (`authority: none`)。控えは repo 外
  `dev-wave-jobs/rulings-inbox/2026-09-17-k2-loop-round2-authorization.md` (結果欄は空)。
  次の一手の新規項は本 fragment の {{T:k2-loop-round2-authorization}}。
- **認可の消費状況を段 1 で現物で確かめた。** D2044 項 9 の「1 回評価」は entry 1548 で消費済み。D1936 項 1 の
  1 本は T-2581 で消費済み (run-card 冒頭にも明記)。[T-2588] は worklog 末尾の次の一手に無い (carry 閉鎖)。
  D2044 以後の decisions に次巡の裁定は無い。依頼の「/rulings は拾わない」は一致した。
- **1 巡目以後の経路変更は 2 件だけと実測した。** `c79437d24` (driver 直起動で sources 非空なら `--coder-role`
  必須。job body は元々 `IZANAGI_S4_CODER_ROLE` で渡しており影響なし) と `106c0ec04` ([T-2702]、digest の
  集約是正、entry 1565 で着地済み)。PIN `511c9538…` = gitlink、verifier 無変更。[T-2703] は未了 (carry) で、
  2 巡目も 1 巡目と同じ射影側の回避 (`materials/leakproof-context-k2.md` 再利用) を範囲に書いた。
- 親の裁定 (子ゼロの軽量版、DW-C00): (P1) 推奨は「1 巡だけの追加認可 (D2044 項 9 と同形)」。N 巡の包括認可は、
  停止条件が harness の `check_stop` と予算しか無く、critic 診断が型付き入力へ届かない現状では推奨しない。
  (P2) 2 巡目の submit-tree は現行 main で新規に切る ([T-2702] 込み、campaign ID は 5 key 同一で `409e13f8`
  のまま、新規 WAL)。規律 7 により現行コードとの差は 1 巡目を無効にしない。
- 予算・停止条件は run-card `2026-09-10_cc-next-precheck` と同値で新設ではない (評価 job 1 本、critic 1 回、
  planner-3 / coder-3 各 1 回、再投入・再抽選・比較 arm なし。anomaly 即 reject、`continue` 以外で停止、
  proposal-3 保存で終了)。
- 主張しないこと: 本パッケージは認可ではない。2 巡目が閉じても合成による改善の実証ではない。
- 段 8 (自己改善): 入口の段 9 が「`tools/dev_wave_wait.py acceptance` で `release`」と書く点を再実測した
  (`acceptance release` は `cli-usage rc=2`、`release` / `message` は `tools/wave_land_window.py` の subcommand)。
  [T-1173] の見送り (D205、再訪条件 = 研究実走の blocker) に被覆され条件未成立のため是正せず記録のみ。
- 工数: codex 子 0 本。親の実測は grep / git log による前提照合のみ、計測なし。受入全走は land 前に
  `tools/dev_wave_wait.py acceptance` で 1 走 (receipt は job dir `dev-wave-jobs/dev-wave-k2-loop-round2-package/`)。

- K2 ループ次巡の認可を求める裁定パッケージを insight・spool 新規項・rulings-inbox 控えの 3 形で置いた。
  実走・実装なし。

## 次の一手差分

### 新規

- {{T:k2-loop-round2-authorization}} **P1・ユーザー裁定待ち**: K2 ループ次巡 — 保存済み proposal-2
  (`value=25`、`output/insights/2026-09-16/t2588-k2-loop-roundtrip/materials/proposal-2.json`) を既存経路で
  1 回評価し、その実測を planner-3 / coder-3 へ戻して proposal-3 を保存する 1 巡の認可。選択肢は
  A (1 巡だけ、推奨) / B (停止条件付き最大 N 巡) / C (不認可)。予算・停止条件・既知限界は
  `output/insights/2026-09-17/k2-loop-round2-package/README.md`。D2044 項 9 の認可は entry 1548 で
  消費済みで、本項の裁定が無い限り実走しない。
