---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2408-b10-lock-identity
seq: 1
title: [T-2408] B-10 限定受理の事前登録 identity を campaign lock の記録値から取る形へ 3 系列そろえて変えた — 裁定当時に見えていなかった 3 つ目の障害 (lock が 24 path 世代で現行 decoder が開けない) を実測で見つけた (コード + テスト + insight、branch worktree-dev-wave-t2408-b10-lock-identity、変異 8/8 KILLED・期待 node 完全一致)
---

## 本文

- **並行 wave との畳み込み判断。** 依頼文は「D1772 ([T-2409]) の実測結果しだいでは同じ変更単位へ
  畳めるので、担当が居るなら畳むか順番を譲るかを先に決めること」と指示していた。担当は稼働中の
  別 session であった。相手へ照会したところ「WAL の 3 field は block record 側に 1 件も無く
  (3 系列とも 0/45)、追加 exact 条件として重ねれば 135 個の literal は 1 byte も変わらない = 再発行 0 個」
  との実測が返った。よって D1772 が定める「再発行が要るなら同じ変更単位で一度に行う」条件は成立せず、
  **2 本を別単位のまま並行で進めた。** 編集面は相手が WAL 読取側の内部、本 wave が限定受理の
  identity 側で分け、共有 test file は行域で分けた。land は受入が緑になった順に 1 本ずつ譲る取り決めとした。
- **裁定の前提のうち 1 つが現行コードでは成立しないことを実測で確認した。** worklog 1324 の
  「現行 commit を指すと限定受理の binding が live prereg の値を使うため lock の旧値と exact 比較で落ちる」は、
  `_legacy_*_binding()` が commit `91a5bfca3` の時点で既に module literal を返す形へ変わっていたため
  成立しない。代わりに、**裁定当時に見えていなかった 3 つ目の障害**を見つけた — 3 系列の現物 lock は
  pre-T733 の 24 path grammar で、現行 `decode_campaign_lock` は 63 path を exact に要求するため
  そもそも開けない。これは D1771 の結論 (lock 記録値から取る) を覆さず、むしろ経路を 1 本に確定させた。
- **段 6 の敵対レビュー 2 レンズが独立に同じ穴を示した。** lock を歴史 decoder に通しただけでは
  identity の真正性に届かず、現物を土台に再 canonical 化した lock で偽の測定 identity を発行できた
  (calibration の 3 系列同時改変、space_version と trial の対改変、別系列の実在 authority との交換、
  未検査の search_config key)。親は個別の構造比較を足さず、系列ごとに lock 全体の内容 digest を
  pin する形を採った ({{D:b10-report-lock-digest-admission}})。
- **却下した所見。** 段 3 luna の「歴史成果物の report が live campaign identity の回転を伴う」は real だが
  コード変更はしない (実測で現に走っている B-10 campaign は無く、drain も resume 放棄も不要)。
  段 6 sol の「系列間の spec / ccbench_commit / formula / patch 比較は実質恒真」はそのとおりで、
  削除はせず診断として残し、変異防壁としては数えないことにした。
- **エージェント工数。** codex 子は plan 1・敵対相談 2・実装 1・敵対レビュー 2・fix 1・焦点再レビュー 1 の
  計 8 本 (すべて `gpt-5.6-sol`、reasoning=xhigh)。変異は probe と本走の 2 走で計 18 dispatch。
- 記録は `output/insights/2026-09-08_t2408-lock-identity/`。逐語 11 本と変異台帳 3 本を収めた。

## 次の一手差分

### 完了

- [T-2408] B-10 限定受理の事前登録 identity を campaign lock の記録値へ束縛し、3 系列そろえて閉じた。
  D1653 が必須とする記録 commit blob の 24 path 照合を既存 helper の再利用で満たし、
  系列ごとの lock 全体 digest を pin した。変異 8/8 KILLED。
  remaining: none
  base: 76ea31c51e715b48c39108e39d5b751c16861e91e81d906687533bb28fc4d2a2
