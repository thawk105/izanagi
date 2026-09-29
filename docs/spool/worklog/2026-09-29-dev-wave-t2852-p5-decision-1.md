---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t2852-p5-decision
seq: 1
title: [T-2852] P5 の進め方の択一を (c) に決めた — ユーザーの判断委任を受け codex 2 立場と相談、S1-wh の本走は今は投入せず S3 の後に別登録、2026-11-02 に再提示 (docs のみ、計算投入 0、branch dev-wave-t2852-p5-decision)
---

## 本文

- 判断 {{D:t2852-p5-defer-to-s3}}、記録 `output/insights/2026-09-29/t2852-p5-decision/README.md`。主体はユーザーの判断委任を受けた親で、ユーザー本人の裁定ではない。
- 経緯: 2026-09-29 未明にマネージャー session (e5405a2a) から「ユーザーは朝まで不在。T-2852 の (a)/(c) を codex と相談して決めよ」と中継。親は codex 2 立場に相談して (c)。
  記録用 worktree の作成が Claude Code の自動モード判定 (共有資源の変更) で拒否されたので迂回せず、記録と land をユーザーへ返した。
  ユーザー本人が「codexに相談して決めてください」と返答し、記録の仕方を codex 2 立場 (案・攻撃) で相談した。攻撃側は「記録してよい (直し方つき)」、
  must-fix 2 (T-2867 と独立の期限・判断主体と計算承認の境界) と should 2 (S1 の独立の価値と延期の損失・計画半幅は感度の目安) をすべて採用した。
- エージェント工数: Codex consult 4 (gpt-6-sol / medium / read-only)。

## 次の一手差分

### 更新

- [T-2852] **P1・S3 実測待ち、2026-11-02 に再提示 (VLDB 差分分析 P5: 介入による理由の説明)**: 進め方の択一は (c) に決めた ({{D:t2852-p5-defer-to-s3}}、
  ユーザーの判断委任による判断)。S1-wh の本走は今は投入しない。事前登録の草稿 `docs/workload-description-critic-intervention-preregistration.md` は未発効のまま。
  再提示の条件: (i) [T-2867] の段階 F の生死確認と実測単価が揃った時点で、P5 を S3 で別登録する案と費用を示す。(ii) それと独立に 2026-11-02 に /rulings が
  S3 の見通しと、表示と critic の効果に絞った S1 縮小案を並べて示す。(iii) どちらも 2027-03-01 から逆算して収まらなければ P5 を論文の未取得の限界として明記する。
  どの案も投入の前に node 時間と LLM の直列時間を示してユーザー確認を取る (D2212 項 4)。材料は `output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md` §5。
  base: d381713ab6cdcdc0672e599353798f0c82571d588ac337baec9841290de5e7ca
