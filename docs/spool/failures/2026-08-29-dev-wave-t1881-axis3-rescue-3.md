---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t1881-axis3-rescue
seq: 3
---

## 新規

### {{F:manifest-untouched-since-misread}}. 救出 manifest の分類語を一次資料と読み違え、着地可能な変更を破棄しかけた [捏造/幻覚] [手順漏れ]

- 事象: 救出 manifest が `docs/related-work/README.md` と `docs/related-work/claim-survey/README.md` に
  付けた `situation: UNTOUCHED_SINCE` を、親が「worktree はこの file を編集していない = 古い複製で
  あって着地対象ではない」と読み、段 1 brief に実測事実として書いた。実際には両 file とも worktree が
  編集した未着地の変更で、うち一方は着地済みの裁定 4 件を規則の正本へ書き下ろした 38 行だった。
  この読みのまま進んでいれば、本 wave で唯一着地できた変更を破棄していた。
- 根本原因: 道具が付けた**分類語の意味を、道具の定義に当たらずに文脈から推測した**。
  `UNTOUCHED_SINCE` は「main 側がその path を base 以降さわっていない」ことしか言わず、worktree が
  編集したかは言わない。manifest は sha256 も持っていたのに、親は blob 照合をせず語だけで判定した。
- 恒久対応: 救出物・棚卸し道具の出力にある分類語は、それ自体を一次資料として扱わない。
  「変更か否か」は worktree の bytes を **その worktree 自身の base commit の blob** と照合して決める。
  main との差だけでは、main が先に進んだのか worktree が編集したのかを区別できない。
- 再発検知: 本 wave では 2 経路で捕まえた。(i) 親が撤去前に `git status --porcelain` を 4 worktree で
  走らせ、両 file が `M` として現れたことに気づいて blob 照合へ進んだ。(ii) 独立コンテキストの段 3
  敵対検査が、同じ事実を独立に `REFUTED` として返した。分類語を根拠にした主張には、blob 照合か
  独立検査のどちらかを必ず付ける。
