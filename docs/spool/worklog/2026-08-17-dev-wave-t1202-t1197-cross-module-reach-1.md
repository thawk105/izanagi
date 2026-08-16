---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1202-t1197-cross-module-reach
seq: 1
title: 8c 事前登録の到達判定を cross-module へ広げ条件 12 の誤報を閉じた (コード + docs、branch worktree-dev-wave-t1202-t1197-cross-module-reach)
---

## 本文

ユーザー裁定 2026-08-16 /rulings 全件 第 3 回 択 (ii) の実装。逐語正本は
`dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full3-28rulings.md` §4。
設計は {{D:cross-module-reachability}} と {{D:decider-version-v2}}、詳細と逐語は
`output/insights/2026-08-17_t1202-t1197-cross-module-reach/`。

**裁定前提の変化 (段 1 前実測)**: D441 決定 (3) は「12 条件すべて `machine_checkable: false` で
実 tree に対して一度も走っていない」としていたが、D438 / 凍結世代 g3 で 6 条件が既に true へ
反転済みだった。よって D441 決定 (4) が「反転すれば出る」と予告した誤報は仮定ではなく
**現に出ていた**。この事実を段 4 裁定へ持ち込んだ。

**成果物影響の訂正**: 段 1 brief は「certified 選択と台帳 reason_code が変わる」と書いたが
過大だった。実際に変わるのは ActivationReport の条件 12 の status / reason / evidence と
その digest だけで、certified 選択と正式 trial 台帳は変わらない (trial registry は個別
reason_code を保存せず発効時の digest だけを持つ)。段 6 レビューの指摘を採って訂正した。

**親裁定の改訂が 1 回**: 段 4 で `**kwargs` 経由を一律に非 witness としたが、実 production
chain が `dict(...)` + subscript 更新 + `**splat` を 2 段通ることを段 6 で実測した。字義どおり
では裁定が目的を達しないため、限定した不変 dict carrier だけを許す形へ改めた。

**親裁定の撤回が 2 回、いずれも実装子が止めた**: fix 第 2 巡で親は焦点走の赤を「実装が受理集合を
広げた」と裁定したが、真因は負例 fixture の文字列置換が一致せず変異が no-op になっていたこと
だった ({{F:noop-replace-mutation-fixture}})。fix 第 4 巡で親は変異 1 件の生存を「検出力の穴」と
裁定したが、真因は述語節が恒真であることによる等価変異だった。子は 2 回とも実装を変えずに
停止し、親が独立検証して裁定を撤回した ({{F:parent-misjudged-red-as-implementation-defect}})。
実装子契約の「期待値が誤りと判断したら実装を変えずに報告して止まれ」が現に効いた。

**敵対レビューは段 3・段 6 とも 2 レンズが独立に NO-GO**。段 3 は段 2 プランの推奨案
(callable 既定引数を witness にする) を却下させ、段 6 は 11 件の must-fix を出した。
既定引数案は、実配線を削っても述語が「到達」と報告する false positive を作る形だった。

**セッション異常**: 親が変異走行中に spool fragment を repo へ書き込み、harness が untracked
検出で中止した (rc=2)。fragment を先に commit して清潔な木で再投入した。走行中は tree へ
書かないという既知の規律を親が破った。あわせて、段 5 で子 2 本を 1 回の呼び出しでまとめて
detach したところ 2 本目が起動せず、pid file 実在を確認せずに張った待ち手が `rc=2` で落ちた。
以後は 1 子ずつ detach し、pid file を確認してから待ち手を張った。

**環境**: ログインノードの bounded local は cgroup attest 不能 (`memory.max` /
`memory.oom.group` を走行中に attest できない) で全 run が停止したため、テストと変異走は
すべて `--force-dispatch` で計算ノードへ投げた。codex 子は Pegasus dispatch preflight
`qstat -Q rc=1` で pytest を 1 度も実走できず、実測は全て親が引き受けた。

**工数**: codex 子 11 本 (plan 1 / consult 2 / author 2 / review 2 / fix 4)、すべて `accepted`。
model は plan と consult が `gpt-5.6-sol` / `gpt-5.6-luna` の reasoning=max、
author と fix と review が `gpt-5.6-sol` の reasoning=high。

## 次の一手差分

### 完了

- [T-1202] 環境契約 条件 12 の誤報を閉じた。到達判定を cross-module へ広げ、条件 12 は
  `environment-contract-consumer-absent` (誤報) から `allocation-enforcement-consumer-absent`
  (真の不在) へ変わった。他 11 条件の status / reason は不変。条件 12 は改修後も充足しないが、
  それが正しい終状態である (allocation 節の縮小は [T-1167] 択 (c) の所有)。
  remaining: none
  base: a80b3429729413fae56a40c1ee6feec7508561e0368e06fea0c5dc66cfdadeba
- [T-1197] 6 条件が共有する到達判定 helper の射程不足を閉じた。同一 module 内 top-level 定義
  だけを辿る形から、契約宣言 root を起点に実 import 束縛だけを辿る canonical `(path, 関数名)`
  graph へ置き換えた。受理規則は {{D:cross-module-reachability}} に 9 項として明文化した。
  remaining: none
  base: 6203300b5eaf55bf5970a3f5872c94ba3da046c81c9c81f9ddee854637a0c7d8

### 新規

- {{T:declared-path-clause-tautology}} **P3・新規**: `s8c_preregistration_evidence.py` の
  `_declared_call` にある `target[0] in probe.declared_paths` は全呼び出し点で恒真である
  (target は常に契約由来の宣言 path から構成される)。挙動は変わらないため成果物への影響はゼロ
  だが、読み手には効いている guard に見える。削除して構成による担保だけに寄せるか、
  防御的冗長として明記するかを決める。変異 matrix では等価変異として記録済み。
- {{T:absent-vs-indeterminate-status}} **P2・新規**: 到達判定で「解析不能」と「実 consumer 不在」
  が同じ `UNSATISFIED` に畳まれている。段 6 レビューが `PROVEN_ABSENT` と `INDETERMINATE` の
  分離を提案した。status 語彙の拡張は判定器・射影・凍結記録・ActivationReport の全 consumer へ
  波及するため本 wave では見送った。
- {{T:attribute-name-is-not-enforcement-proof}} **P2・新規**: 条件 12 の attribute 検査は
  `single_process` / `allow_resume` という**名前が到達関数内に現れること**しか見ておらず、
  拒否方向や契約との対応を検査しない。cross-module 化で偶然一致の範囲が広がった。
  条件の再定式化に当たるため [T-1167] 系の所有境界と併せて裁定する。
