---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2232-s4-loop-pegasus-job-script
seq: 1
title: [T-2232] 段 4 loop 用 Pegasus job body を新設し登録簿・手順書投影・README の qsub command を同期する (コード + docs、branch worktree-dev-wave-t2232-s4-loop-pegasus-job-script)
---

## 本文

- 軽量版 dev-wave (段 1〜9)。一次資料は `output/insights/2026-09-05_t2232-s4-loop-pegasus-job-script/README.md`。
  新規 Pegasus 実行体のため本 wave では投入せず (F660)、login node の stub harness 短走 (DW-G01) と
  登録簿の contract テストで止めた。設計判断は {{D:s4-loop-compute-only-job-body}}。
- ユーザー裁定 (起票時): job script と登録だけ。attestation の exact 照合など未実測の障害は先回りしない。
  F813 (PATH の CMake wrapper で third-party を注入しない) を守り、masstree `config.h` は job 内で
  A-2 と同じ FetchContent 準備で事前構築する。
- 段 3 で親 brief の前提 P1「事前構築は無害な死んだ経路」が誤りと判明 (hydrate 済み source を汚す)。
  scratch へ複製してから構築する形へ訂正 (C0/C4)。段 6 レビュー A/B は NO-GO (must-fix 計 7、うち 1 は
  段 7 で解消する README 参照の未存在)。fix 後の焦点再レビューは GO (D1〜D7 すべて closed、回帰なし)。
- 変異: 事前登録 16 件 (M1〜M16)。fix で M3 の anchor が消えたため fix 後の実効 gate へ再照準
  (spec v2、初回 spec は erratum として残置)。probe 1 回目は untracked な裁定追補 file で harness が
  起動前停止 (rc=2)、docs-only commit 後に再投入。本走 16/16 KILLED、期待 node と完全一致、baseline PASSED。
- 焦点走: 3 回 (1 回目は queue-wait-timeout rc=16 の infra、2 回目 1120 緑、fix 後 3 回目 1203 緑)。
  full provenance 監査 2 回 (8241 / 8242 件、新規違反なし)。受入全走は本記録 commit の後に投入し、
  結果は受入 receipt と land 報告に残す (記録 commit を tested tip の内側へ置くため)。
- 工数: codex 子 8 本 (plan 1、lens 2、author 1、review 2、fix 1、focus review 1)、いずれも rc=0。
- 段 8 スキル自己改善: 新規候補なし (変異 harness の untracked 拒否は既存記憶に含まれる)。

## 次の一手差分

### 完了

- [T-2232] 段 4 loop 用 Pegasus job body・登録簿・手順書投影・README の qsub command を同じ変更単位で
  同期した。初回投入と reservation / attestation の実効確認は後続 wave (投入時に割れうる点は
  insight README の保証範囲に列挙)。
  remaining: none
  base: 216200d164ebf7671cb1d65f4f34070e1b35eb85f6d85f6561e20f9cfe265174
