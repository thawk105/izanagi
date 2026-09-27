---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: dev-wave-t2104-flock-scope
seq: 2
---

## {{D:held-campaign-lock-handoff}}. campaign 実行 lock は driver が外側で取り、run_campaign へ保持 handle を明示的に渡す

**決定:** D1346 の保持区間の拡大は、base driver (`p3_s4_loop.drive_iteration`) と `main()` の B-4 経路が
`campaign_lock` を非ブロッキングで外側から取り、`campaign_lock` が yield する保持 handle (path・取得 PID・保持中フラグ) を
`run_campaign(held_campaign_lock=...)` へ渡す形で実装する。`run_campaign` は handle の exact 型・保持中・PID・自分が計算する
lock path との一致を WAL より前に確かめて取得を省き、不一致は fail-closed にする。引数を渡さない caller は従来どおり自分で取る。
対象は B-4 事前登録の対象 driver である base だけとし、sort / trigger / policy driver は変えない。

**理由:**
- 同一 process の再入を CampaignBusy で拒否する既存契約 (`test_campaign_lock_reentry_rejected_in_same_process`) を保ったまま、
  外側と内側で同じ lock を二重に取らずに済む形がこれだけだった。
- PID を束縛するのは、fork で継承した handle を別 process が渡して並走するのを塞ぐため。fd・inode の照合は区間の保証に要らないので入れない。
- 本番の main は layout を注入しないので、driver と run_campaign と producer の lock path は同じ式で同じ値になる。
  test の注入 layout で食い違う場合は run_campaign の照合が WAL 前に止める。

**却下した選択肢:**
- `campaign_lock` を同一 process 内で再入可能にする — 既存の再入拒否契約を壊す。
- B-4 認可の消費より前に driver が path 一致を追加で照合する — 本番経路で起きない不一致に対する仮想リスク向けの検査になる。
- sort / trigger driver へも同時に広げる — 今回の B-4 の記録に効かない一般化になる。対象 driver を変えるときに同じ変更を行う。
