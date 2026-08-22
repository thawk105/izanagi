---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1484-floor-restart-registry
seq: 1
title: '[T-1484] 床値 (8b v1 freeze) crash 復帰救出経路の技術確認を完了し、R-5を更新して実装方針の推奨をユーザー裁定へ返した (docsのみ、branch worktree-dev-wave-t1484-floor-restart-registry)'
---

## 本文

- 段1 brief で `docs/phase3-8b-restart-runbook.md` §3.6/§5 R-5 の crash 復帰袋小路、
  D496 決定3・D510 決定4、`docs/phase3-8b-descriptor-design.md` §10.5/§10.6、D649 の
  一次資料を突き合わせ、「D496決定3と旧§9項8のどちらが優先するか」は D510決定4 が
  `8b §9項8` を名指しして既に決着していること、同日付の §10.5 が対応する設計文
  (freeze-wide 事前割当 attempt registry) を既に持つことを確認した。command 引数は
  §10.5 を直接名指ししていなかった (未発見のクロスリファレンス)。
- 段2 codex plan (read-only) が、brief 未発見の重要なギャップを2件追加発見した:
  (1) 8b の失敗分類が現行実装では性能出力 (`measure_fn`) 実行**後**に決まっており、
  D510決定4の「出力を読む前に分類」要件を満たさない。(2) `trial_registry.py` 自身も
  OS レベルの read-first を保証しないと docstring で明記しており、T-1337 のレビューでも
  scope 外のまま残っている。
- 段3 敵対2レンズ (sol=正しさ境界、luna=整合性・実効性・所有範囲) が独立に段2 plan の
  結論を裏取りした。**決定的な所見 (luna):** 親の当初の暫定判断
  「8b 専用の attempt registry を新規に複製する」は未検証だった。`trial_registry.py` の
  attempt 状態機械本体 (約1,738行) はほぼドメイン非依存で、8c 固有部分は acceptance
  (約123行) に集中するため、共通 core 抽出 + 8c 互換 facade + 8b adapter の方が保守面で
  有利な可能性がある。段2 plan はこの比較を行っていなかった。sol は crash 点4
  (観測開始後) の再抽選バイアスが §10.5 だけでは閉じないこと、novelty search と
  再抽選バイアスが別問題であることを独立に確認した。
- 段4 裁定 (親): 両レンズの全13所見を real として採用した。D496決定3/D510決定4の優先順位
  自体は決着だが、**実装形状 (8b専用複製 vs 共通core抽出) は未検証のためユーザー裁定へ
  返す**。実装着手前に閉じるべき4点 (reuse形状・既存admission機構との束縛・出力前分類の
  設計・crash点4の再抽選バイアス) を `docs/phase3-8b-restart-runbook.md` の R-5 節へ
  明記した。§10.6 (epoch境界) は8b registryの実装自体は妨げないが、正式測定authorization
  はD649が確認した8c側のgate (`judge()`にproduction callerなし) が閉じている間、
  引き続き認可しない、と実装許可/測定不許可を分離して記述した。
- 実装差分ゼロ (docsのみ) のため変異 matrix は対象外 ({{D:t1484-floor-restart-registry-recommendation}} の却下した選択肢参照)。
  一次資料・段2 plan・段3 敵対2レンズ逐語・段4 裁定は
  `output/insights/2026-08-22_t1484-floor-restart-registry/README.md` に保存した。

## 次の一手差分

### 完了

- [T-1484] docs-only の技術確認・R-5更新・推奨返却で完結。実装は未着手のまま次のユーザー
  裁定 (reuse 形状の択一) を待つ。実装着手そのものは新規裁定後に別途起票する。
  remaining: none
  base: fb96821f0bfca98981b3e7272afe3b320b5371f5766ac6ad4dba26b120685d45
