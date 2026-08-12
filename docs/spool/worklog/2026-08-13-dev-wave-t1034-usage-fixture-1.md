---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t1034-usage-fixture
seq: 1
title: usage dominance の fixture 過剰決定を是正し、変異検出力の純増を実測する (テストのみ、branch worktree-dev-wave-t1034-usage-fixture)
---

## 本文

- 択一 (a) 単一理由 fixture へ差し替え / (b) 冗長 gate と明記 は、ユーザーが段 1 の実測で親が
  決めてよいと裁定していた (運用系の可逆判断)。実測が単一の犯人 gate を特定したため **(a) を採った**。
- 段 1 の実測は tracked file の一時変異 + 即時復元で行い、計算ノードへ 3 回 dispatch した。
  dominance を常に真にしても対象テストは 4 param すべて通過し、正規形チェックも併せて
  無効化したときだけ 4 件とも落ちた。正規形チェックだけを無効化しても通過した。
  この 3 点で dominance だけが残る唯一の理由であることを挟み込んだ。
- 犯人は本番相 2a の短絡連鎖の先頭にある message.id の正規形検査だった。fixture の
  msg-incomparable は本番が要求する msg_ + 英数字に合致せず、dominance は一度も評価されていなかった。
- **同型の過剰決定を隣接テストでも発見した。**
  test_same_message_and_usage_with_different_request_ids_remains_fatal も
  requestId 集合の相違を無効化して生存する。同一欠陥・同一修正のため本 wave で併せて直した
  (親の裁定。ユーザー指示は 1 テストを名指しするが、編集面はどちらも指示範囲内)。
- 変異 matrix は新旧両走を回した。wave 前 (734c03a1) と wave 後 (7ad74525) の差分:
  MUT-A (dominance 常に真) の失敗 node は 1 件から 5 件へ、MUT-B (requestId 集合検査の無効化) は
  SURVIVED から KILLED へ。**純増は対象 4 param + 隣接 1 件の計 5 node。**
- 段 2・3 と段 6 の review 子は軽量版として省いた。production 無編集で受理集合が動かず、
  検出力の証明は変異 matrix が直接与えるため。実装子は codex 1 本 (author、gpt-5.6-sol、
  reasoning=high、model calls 10、wall clock 131 秒、rc=0)。
- **起動検査の残 1 件は main 側の残置が原因。** check_wave_startup.py は
  docs/handoff に README 以外が残っていると赤にするが、そこにあるのは land 済みの別 wave の
  handoff であり、land は docs/handoff の削除を機械拒否する。どの wave も撤去できない状態で、
  新規 wave の起動検査を全件止める。本 wave は DW-O20 本文 (untracked handoff を残さない) を
  満たしているため続行し、構造の問題として {{T:orphan-landed-handoff-blocks-startup}} へ起票した。
- 放置した場合、usage dominance の判定が退行しても両テストは緑のままとなり、
  台帳の model_calls と token 集計が replica を 1 回に畳む保証を失う。

## 次の一手差分

### 完了

- [T-1034] fixture が dominance 以外の gate で過剰決定されていた原因を実測で特定し、
  message.id を正規形へ差し替えて単一理由にした。拒否理由を診断文で pin する assertion も足した。
  隣接テストの同型欠陥も併せて是正した。新旧両走で検出力の純増 5 node を実証した。
  remaining: none
  base: f08db5ff6f33273780e6455b9b0dc24952962c468a261935143762b8ff9c3822

### 新規

- {{T:orphan-landed-handoff-blocks-startup}} **P2・新規**: land 済みで撤去不能な
  docs/handoff の残置が、全 wave の check_wave_startup.py を赤にする。
  land が docs/handoff の削除を機械拒否するため wave 側からは解けない。
  main 直接の 1 回限りの撤去か、起動検査が自 wave 由来だけを見るようにするかを決める。
