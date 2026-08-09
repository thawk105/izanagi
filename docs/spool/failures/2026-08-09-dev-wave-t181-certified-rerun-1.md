---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t181-certified-rerun
seq: 1
---

## 新規

### {{F:frozen-scorer-decision-regex}}. 実走前に凍結した採点器の decision 抽出が、正例 1 run を誤って post-treatment に落とした [テスト代表性] [計測汚染]

- 事象: [T-181] 認証再走 (2026-08-09) の 10 run のうち s03 (POS / max) だけが
  `score_run` で rc=23 `score: summary does not start with one GO/NO-GO decision` になり、
  `failure_class="post-treatment"` として primary の k 計上から外れた。結果、認証済み
  `aggregate.decision` は `max=2/3, high=3/3` により
  `quality_decision="benchmarkまたはmax基準が不安定"` を返した。
  **両読者 (親 + 独立第二読者) は s03 の R-1 を true と裁定しており、10/10 一致している。**
  s03 の総括は完結し 500 bytes を超え、結論も一意 (`NO-GO`) である
- 根本原因: decision 検査が二段構えで、第 1 段 `decision_match` (総括の最初の一文が単一
  GO/NO-GO) は**通過**したが、第 2 段の本文全体抽出
  `(?<![A-Za-z-])(NO-GO|GO)(?![A-Za-z一-龯ぁ-んァ-ヶ-])` が `GO` 直後のひらがなを除外するため、
  総括を「**NO-GO です。**」で始めた s03 は抽出 0 件となり `len(distinct)!=1` に該当した。
  第 2 段の意図は「GO と NO-GO の併記による曖昧さ」の検出であり、**抽出 0 件は曖昧さではない**。
  事前登録が義務づけた採点器 control は歴史 `focus1.md` (正例) / `focus2.md` (負例) の 2 本だけで、
  どちらも「`NO-GO。`」表記だったため、この分岐は control を通っていなかった。
  2026-07-30 の 10 run も全て「`NO-GO。`」「`GO。`」で、欠陥は 1 年分の運用で潜在したまま初発火した
- 恒久対応: 未実施。**実走後に採点器を直すと F61 が再発する** (凍結装置が変わり本走の replay 認証が
  失われる) ため、本 wave では直していない。是正と再走要否は
  {{T:score-decision-extraction-defect}} でユーザー裁定へ返す。
  暫定の防壁は `output/insights/2026-08-09_t181-certified-rerun/README.md` の
  「機械 `decision` 行は採点器の欠陥を含んでいる」節であり、当該行の実質的引用を禁じている
- 再発検知: 是正時に、同義だが表記の異なる決定文
  (`NO-GO。` / `NO-GO です。` / `**NO-GO**です。` / `結論は NO-GO です。`) を采点器の正例 control へ
  追加し、抽出 0 件を「曖昧」と誤判定しないことを単独 kill 可能にする。
  F60 と同型 (control が実運用の表記多様性を覆っていない) であり、**独立 2 例目**である
