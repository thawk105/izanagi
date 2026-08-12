---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t816-step4-impl
seq: 2
title: dev-wave 段 8 — 段 4 再開型 wave と gitlink 前進の著者性を裁定へ送る
---

## 本文

段 8 の自己改善 gate を 1 度適用した。候補 2 件はいずれも段構成・実装子権限に触るため、
契約どおり本文編集をせず裁定パッケージとして起票する (実装しない)。

## 次の一手差分

### 新規

- {{T:dev-wave-resume-at-stage-4-contract}} **P2・新規 (裁定候補)**: 前 wave が段 4 で
  ユーザー裁定待ちのまま停止し、裁定後に**別の fresh context が段 4 から再開する**型の
  wave について、入口が契約を持っていない。読み込み契約の巻き戻し規則は「後発条件が期限後に
  成立した場合」を定めるだけで、「前 wave の段 2 プラン・段 3 敵対レンズを新 context が
  流用してよい条件」を導けない。本 wave では親が判断して流用し (裁定が Q1/Q2 の結論だけを
  変え、変更面の骨格は同一であることを確認したうえで)、変更面の再検査を段 6 のレビュー 2 本へ
  寄せた。結果として段 6 が親裁定を 1 件覆したので判断自体は妥当だったが、**契約として
  明文化されていない**。選択肢 = (a) 流用可の条件を入口へ明記、(b) 段 2 から必ずやり直す、
  (c) 前 wave の逐語を「攻撃対象の入力」として段 3 へ再投入する型を新設。
  正本 = `output/insights/2026-08-12_t816-step4-impl/README.md`

- {{T:gitlink-advance-authorship-gap}} **P2・新規 (裁定候補)**: **submodule gitlink の前進は
  Codex `role=author` が物理的に実行できない。** submodule の git dir は worktree の外
  (`.git/worktrees/<wt>/modules/...`) にあり、workspace-write の sandbox から書けない。一方
  `external/` は `tools/check_ai_provenance.py` の実装面 prefix なので、gitlink だけを進める
  commit は「実装面なのに role=author が無い」commit になる。本 wave は codex author が書いた
  実装と同じ統合 commit に含めて回避した (方針は `docs/ai-provenance.md` の
  「Git 操作の機械的代行は記録しない」に沿う) が、**gitlink だけを進める wave では回避できない**。
  選択肢 = (a) gitlink 前進は Git 操作の機械的代行であって著作ではないと明文化し、
  checker の実装面判定から submodule gitlink を除外、(b) D105 の waiver を毎回使う、
  (c) codex 子が submodule へ書ける配線を作る。
  正本 = `output/insights/2026-08-12_t816-step4-impl/README.md`
