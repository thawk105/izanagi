---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1283-launch-authority-design
seq: 2
title: [T-1283] 残余(i)の設計insightのみを記録した (D569は維持、実装しない、branch worktree-dev-wave-t1283-launch-authority-design)
---

## 本文

- [T-1283] 残余(i)「tip側待ち手がlauncherを経由せず受領証を自作できる」の**設計insightのみ**を
  記録した (実装しない)。着手前に、この残余には専任ticket [T-1373] が既に存在し、本日
  2026-08-20 付で D569 (ユーザー裁定、(c) 現状維持・新規実装なし) が下りていたことを確認した。
  D569 は「(a) (bootstrap 層新設) の将来的な価値を否定しない」と明記しており、本 wave は
  D569 を覆さずその再訪用 insight を残す位置づけとした。
- 段2 codex plan (1本) が P2 仮説 (launcher 起動権だけを tested_main 起点の最小 gate へ
  抽出する案) を具体化。段3 敵対相談2レンズ (D403整合性・起動権実効性 / 検証法健全性・
  D569整合性) が計7所見・real 5件を発見: (i) gate 自身の bootstrap 例外が導入期間中に
  wave tip 起動権を再導入する (無条件の「常に tested_main」ではない)、(ii) completion
  protocol の positive control 主張が誤り (exact field 検査は整形式性のみで執行実在を
  証明しない)、(iii) gate が tip 側待ち手をどう起動するか (bytes/path/loader) 未定義、
  (iv) 記録案の文体が実装承認と誤読されうる、(v) decisions.md の実 D 番号は fold 前に
  確定しないため plan 内の仮番号表記は placeholder 化が必要 (spool 形式で構造的に解消)。
- 親の追加実測: launcher の receipt 生成は `pre_fingerprint`/`post_fingerprint`/
  `effective_scheduler`/checker 系 field を待ち手からの completion protocol 経由の
  自己申告のままにしており (`acceptance_launcher.py:82-86,461-463`)、gate 設計は
  この経路までは閉じない。
- 設計 insight は {{D:acceptance-gate-launch-authority-insight}} へ記録し、「D569 は
  変更しない・実装は承認しない」を明記した。

## 次の一手差分

### 更新

- [T-1283] **P1・残余(i)の設計insightを{{D:acceptance-gate-launch-authority-insight}}へ
  記録した (実装しない、D569は維持)。残余(i)(ii)(iii)はいずれも未実装のままT-696の協調境界に
  残る**: 将来 (a) を外部露出運用への移行時に再訪する場合、決定本文が挙げる未解決点
  (gate の tip 待ち手起動方法・gate 自身の trust root・completion protocol/fingerprint
  経路の自己申告面) を先に設計する必要がある。
  base: d2b4757abb9c858277a1a7df83788cb548a89ce1b4e5a41f33176db908c3158c
