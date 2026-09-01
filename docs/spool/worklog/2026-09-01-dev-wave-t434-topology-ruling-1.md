---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t434-topology-ruling
seq: 1
title: [T-434] 発効 topology を二段束縛に確定した — 認定記録を置ける commit が無いという循環を codex が見つけた (docs のみ、branch worktree-dev-wave-t434-topology-ruling)
---

## 本文

- 直前の実装 wave が返した 3 択について、ユーザーが「codex に相談して決めて」と委任した。
  read-only の codex へ独立評価を依頼したところ、**3 択のいずれでもない第 4 の道**が返り、
  親が現物で追認して採用した。決定は {{D:cap-lift-two-stage-binding}}。
- **codex が見つけた循環 (前 wave の段 2 プラン・段 3 の 2 レンズ・段 4 裁定のいずれも見ていない):**
  P6 の認定記録は `subject_revision_sha` に束縛されるが、対象 revision は実装を含む内容 commit が
  確定するまで決まらない。一方で先行設計 v2 は発効 commit が受領証 1 ファイルだけを追加すると
  書いていた。両方を満たす commit が存在せず、認定記録を置ける場所が無い。
- 親が独立に確かめた 4 点。(i) 認定記録の revision 束縛と失効規則
  (`output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md` §8)。
  (ii) 条件評価の実装が `P6Unavailable` で無条件停止すること
  (`orchestrator/campaign/reflux_formal_consumer.py`)。
  (iii) 発効 commit の追加可能 path 数を固定した既裁定は台帳に存在せず、先行設計 v2 の
  当該一文は裁定済み択一 1〜10 の外にあること。(iv) D438 決定 (4) が同型の循環を
  二段束縛で解いた先例であること。**採用した形は新機構ではなくその適用である。**
- 直前 wave が推奨した択 A は順序が自己矛盾だった。P6 の認定を先に済ませても、後続の実装で
  対象 revision が変わり認定が失効する。認定は内容 commit の確定後に行う。
- 現行 manifest の exact 世代数 2 と 8c 事前登録は変更しない方針も同時に確定した。
  受領証で開く上限は新しい manifest 版へ隔離する。D882 が予約した条件 11 の locus と
  凍結済みの事前登録本文に触れずに拡張できる。
- codex 子 1 本 (consult、read-only、reasoning=xhigh)。rc=0、`check_codex_output.py` rc=0。
  逐語は `output/insights/2026-09-01_t434-topology-ruling/codex-recommendation.md`。
- 実装面の差分はゼロ。機械受理集合・凍結 bytes・proof chain・certified 選択はいずれも不変。
  変異 matrix は免除、受入全走は免除せず本エントリの記録 commit の tip を land gate として投入する。

## 次の一手差分

### 更新

- [T-434] **P1・発効 topology 確定済み ({{D:cap-lift-two-stage-binding}}) → 実装待ち**:
  2026-09-01 に 3 択へ決着をつけた。採ったのは 3 択の外の第 4 の道で、発効を
  内容 commit `G` + 発効 commit `A` (親集合が exact `{G}`、認定記録と受領証の 2 件だけを
  create-only 追加) の二段束縛にする。D438 決定 (4) の適用であり新機構ではない。
  D121 決定 (7) / D150 決定 (4) / D156 のいずれも supersede しない。
  現行 manifest の exact 世代数 2 と 8c 事前登録は変更せず、受領証で開く上限は
  新しい manifest 版へ隔離する。**残る blocker は P6 の意味的充足契約の本体実装**であり、
  それが `G` に入るまで受領証は発行できない。実装時の consumer 閉包・設計の穴 5 件・
  再利用すべき既存機構・変異事前登録の候補は
  `output/insights/2026-09-01_t434-cap-lift-receipt-v3/design-v3.md` §3 / §4 / §5 / §6 が正本。
  base: 6de4e53b0cca244d2cdc0d4b171a4d57894f5ec5f9e9ada3dec890fb20c91a59
