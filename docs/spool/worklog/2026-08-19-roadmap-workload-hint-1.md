---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: roadmap-workload-hint
seq: 1
title: workload descriptor に人間の自由記述ヒントを任意で許すよう roadmap §1 を協議改訂した (docsのみ、branch worktree-roadmap-workload-hint)
---

## 本文

- ユーザーとの協議で、izanagi の完全自律合成 (人間ヒント無し) が現状の LLM には難しすぎる懸念から、
  workload input に人間の自由記述ヒントを任意で添えられるようにする方針が決まった。「AI 側は受け
  取ったヒントをそのまま判断材料に使ってよい」までユーザーが明確化した — 人間が直接与える workload
  入力は規律6 (信頼境界) が言う「外部由来の未信頼入力」ではなく「ユーザーの直接メッセージ」と同枠の
  信頼される側であるため、leak 判定などの追加機構は不要という整理。
- 境界は {{D:workload-policy-hint}} に確定: ヒントは workload の傾向・重視目的を指す自由記述に限り、
  hole や具体実装そのもの (勝ち筋) は roadmap.md §2 D44 の要件 (人間が毎回 hole と勝ち筋を手渡さ
  ない) により含めない。ヒント使用の有無と内容は材料レポートへの記録を必須にした。
- 本 wave は roadmap.md §1 のこの一文の協議改訂のみ (docs のみ)。descriptor へのフィールド追加と
  planner/coder 側 prompt への配線は次の一手 (新規 T) へ分離した。

## 次の一手差分

### 新規

- {{T:workload-policy-hint-impl}} **P1・新規**: workload descriptor に任意の自由記述方針ヒント
  フィールドを追加し、少なくとも1段 (planner-v4 または axis-proposer) の入力プロンプトへ配線する。
  ヒントを与えた場合は材料レポートへその旨と内容を記録する。設計境界は {{D:workload-policy-hint}}。
  継承 branch: worktree-roadmap-workload-hint (roadmap.md §1 協議改訂 commit 済み・未 land、この
  branch の上に実装してよい)。
