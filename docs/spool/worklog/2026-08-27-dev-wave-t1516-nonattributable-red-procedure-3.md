---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1516-nonattributable-red-procedure
seq: 3
title: 非帰属の受入赤で wave を止めない手順を DW-O18 へ収容する (docs + checker pin、branch worktree-dev-wave-t1516-nonattributable-red-procedure)
---

## 本文

- **着手時の実測で scope が縮んだ。** [T-1516] の裁定 (2026-08-24 /rulings 全件、択 (b) を先に) を
  受けた D873 が正式手順を既に `DW-O18` へ書いており、依頼の 3 要求のうち
  「assertion 本文で判定し署名一致で決めない」は着地済みだった。純増は 2 点だけである。
- **予算は D782 / D730 の手順 (a) 既存記述の削減だけで閉じた。** 節は 998 → 997 bytes、
  L2 単節上限 1000 は据え置き。(b) の例外収容にも (c) の上限引き上げにも進んでいないので、
  D961 / D1046 が禁じる「案件ごとの裁定送り」も発生していない。
  なお D961 が命じていた `docs/skill-self-improvement.md` の文面書き換えは、本 wave の走行中
  (2026-08-27 朝) に別 wave が main へ着地させた。D1046 が指していた滞留原因は解消している。
- **敵対検証が 3 段階とも別々の穴を出した。**段 3 → 段 6 レビュー → 段 6 焦点再レビューで、
  いずれも前段が見落とした所見が出ている。とくに受理集合に触れる 2 件は親も段 2 も
  見落としていた。省いていたら実効的な受理集合を広げたまま着地していた。
  - 段 3: 後置した「投げ直す」に回数上限が係らず**無界再投入**になっていた。
  - 段 6 レビュー: その修正でも「1 回だけ」が受入再走にしか係らず、**単独再走が無界**のまま
    残っていた。単独走を緑になるまで回してから受入再走へ進む経路が生きていた。
  - 段 6 焦点再レビュー: 停止条件を 1 文へ統合したことで D873 の分岐別述語を直積化し、
    判定不能・原因未理解へ「裁定へ送り」を足していた。D961 / D1046 と逆向きだった。
- **段 6 レビューの一方は must-fix 0 件だった。** レンズ B は「追加した変異 case が
  節全文 exact pin の下で恒真になっていないか」を問われて、needle の出現回数 assert が
  義務ごとの bytes を実際に押さえていると独立に結論した。親の見立てと一致した。
- **変異が想定を覆した。** 本文から義務を削る変異が SURVIVED した。実効 gate は
  test file ではなく `python3 tools/check_docs.py` の直接実行だった
  ({{F:doc-obligation-guard-is-bytes-only}})。実効 gate は user 裁定の growth hold で
  既定スイート外にあるため、**hold は解除せず**親が `DW-O19` の一時変異で直接測り、
  rc=1・finding 1 件ちょうどを確認した。
- **子の工数。** codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 2、focus 1 の計 9 起動)。
  段 5 / 段 6 の実装子はいずれも計算ノードの dispatch 障害で pytest を実走できず、
  緑は申告していない。テストの実走はすべて親が login node 経由で行った。

## 次の一手差分

### 完了

- [T-1516] 非帰属の赤が出た wave の着地手順を `DW-O18` へ収容した。純増は
  「N 走完全一致は flake でも非帰属の証拠でもない」と「停止条件外は治すか hold 登録後だけ
  投げ直し wave を止めない」の 2 点。予算は削減だけで閉じ、上限は据え置いた。
  設計判断は {{D:nonattributable-red-does-not-stop-the-wave}}。
  remaining: none
  base: 8964fc37caf782e36d4e4eefbf6eb2554a02c4f9e0504af975a4c293fdb7576e

### 新規

- {{T:real-repo-docs-pin-gate-is-held}} **P2・新規**: 実 repo の手順書 exact pin を照合する
  唯一の test が docs_bytes の growth hold で既定スイート外にある。
  解除条件はユーザーの明示コマンドのみで、現状この gate は
  `python3 tools/check_docs.py` の直接実行にだけ乗っている。
  安く回せる形 (対象節だけを照合する軽い test) を作れるかを見積もる。
