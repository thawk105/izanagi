---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-research-gate
seq: 1
title: dev-wave が土台へのゴミ流入を止めているかを実測し、段 1 brief に「研究前進」を必須化した (docs-only、branch worktree-dev-wave-research-gate)
---

## 本文

- ユーザーの問い「dev-wave は過剰実装・過剰ガードレールを避ける仕組みか。研究開発の遅滞を気にかけている。
  不十分なら強化する」「規律だけでなく CC 自動合成のための土台整備のやりすぎも含む。土台にゴミを入れたら
  掃除が要る」に対し、dev-wave 側の抑止機構 (`DW-C00` 軽量版、`DW-G01`〜`G05`、`DW-O13`、D205、D271、
  D730) と土台側の実測を突き合わせた。結論: 仕組みはあるが土台へのゴミ流入は止まっていない。
  実測 (製品 +67K/−2K 行・テスト +73K/−2K 行 / 週、直近 4 日の wave 61 本中 土台 ≈34)、構造的な穴 5 点、
  提案 P1〜P6 は `output/insights/2026-09-08_dev-wave-research-gate/RESULT.md`。
- ユーザー裁定 (2026-09-08): P1 (段 1 brief に研究前進を必須化) 採用、P3 / P5 は codex 相談後に親が統合判断、
  P2 / P4 / P6 は未選択 (記録のみ)、予算は D782 の手順を親が回す。設計判断は
  {{D:dev-wave-research-advancement-line}}。
- codex 相談 2 本 (read-only、lane sol / luna、reasoning xhigh): 所見 lens A 12 件・lens B 6 件、全件 real。
  両レンズが独立に P3 (生存者バイアスで効果を測れない) と P5 (削除は受理集合を広げうる、規律 2) を却下し、
  親も採らないと裁定した。最重要: 「何を進めるか」だけでは恒真化する (A-2)、段 1 の文だけでは段 4 の scope
  判定が変わらない (A-6)、G05 の「1 cycle 後へ送る」と二義化しないよう「後送せず」を明記 (B-3)。
  親 brief 自身が 73 行で `DW-S01` の 10〜30 行を破っていた (A-1)。
- 予算: L1 10,594 → 10,568 / 10,625 bytes (正味 −26)。原資は D227 の同一読点重複 3 件 (`DW-S08` 本文 −139、
  `DW-S04` の `DW-M01` pointer −56、`DW-STOP` の入口巻き戻し規則 pointer −105)。増枠なし。
- docs-only のため実装子・変異 matrix なし。`python3 tools/check_docs.py` 違反なし。pytest はログインノードで
  guard に拒否されるため、受入全走は本記録 commit 後の tip へ計算ノード dispatch で投入し、結果は受入 receipt
  と land 出力で束縛する (本文執筆時点では未実施)。
- 素材: 土台の伸び (tools 0 → 148K 行、orchestrator 6.8K → 267K 行、tests 2.2K → 524K 行、7/1 → 9/8) は
  「AI 開発ループが自己増殖する土台」の定量例として論文の議論節に使える。

## 次の一手差分

### 新規

- {{T:dev-wave-excess-lens-mutation-scope-finding-exit}} **P2・裁定候補**: P2 (段 3・6 のレンズ 1 本を過剰・削除
  レンズに固定)、P4 (変異 matrix の義務を防壁・台帳・受入判定の実装面に限定)、P6 (研究前進か実測欠陥の根拠が
  無い scope 外所見は起票せず記録のみ) をユーザー裁定へ。両レンズとも P1 単独では段内の土台増殖を止めないと
  指摘 (A-10)。根拠は `output/insights/2026-09-08_dev-wave-research-gate/RESULT.md`。
