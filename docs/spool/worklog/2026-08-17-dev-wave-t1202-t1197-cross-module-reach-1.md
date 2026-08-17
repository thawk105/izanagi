---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1202-t1197-cross-module-reach
seq: 1
title: 8c 事前登録の到達判定を cross-module へ広げて着地させる — 観測値は変わらず、変わるのは 6 条件が共有する判定の射程 (コード + docs、branch worktree-dev-wave-t1202-t1197-cross-module-reach)
---

## 本文

ユーザー裁定 2026-08-16 /rulings 全件 第 3 回 択 (ii) の実装。逐語正本は
`dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full3-28rulings.md` §4。
設計は {{D:cross-module-reachability}} と {{D:decider-version-hold}}、詳細と逐語は
`output/insights/2026-08-17_t1202-t1197-cross-module-reach/`。

**裁定前提の変化 (段 1 前実測)**: D441 決定 (3) は「12 条件すべて `machine_checkable: false` で
実 tree に対して一度も走っていない」としていたが、D438 / 凍結世代 g3 で 6 条件が既に true へ
反転済みだった。よって D441 決定 (4) が「反転すれば出る」と予告した誤報は仮定ではなく
**現に出ていた**。この事実を段 4 裁定へ持ち込んだ。

**成果物影響の訂正**: 段 1 brief は「certified 選択と台帳 reason_code が変わる」と書いたが
過大だった。さらに land 相の実測で、**実 tree の観測値は 1 つも変わらない**ことが確定した。
本 wave が着地させたのは 6 条件が共有する到達判定 helper の射程であって、今日の出力ではない。
判定が変わるのは、対になる [T-1167] が実現可能な形へ縮小した allocation 節が満たされた後の木である。

**親裁定の改訂が 1 回、撤回が 3 回。撤回のうち 3 回とも実装子が止めて子が正しかった。**
改訂は段 4 の「`**kwargs` 経由を一律に非 witness」で、実 production chain が `dict(...)` +
subscript 更新 + `**splat` を 2 段通ることを段 6 で実測し、限定した不変 dict carrier だけを
許す形へ改めた。撤回は (i) fix 第 2 巡で焦点走の赤を「実装が受理集合を広げた」と裁定したが
真因は負例 fixture の文字列置換が一致せず変異が no-op になっていたこと
({{F:noop-replace-mutation-fixture}})、(ii) fix 第 4 巡で変異 1 件の生存を「検出力の穴」と
裁定したが真因は述語節が恒真であることによる等価変異、(iii) land 相で終端 target の所有 path を
条件自身の宣言 path へ限定すると裁定したが、条件 9 の正規 target は条件 10 の宣言 path にあり
限定すると条件 9 の reason が変わることを子が実測して止めた
({{F:parent-misjudged-red-as-implementation-defect}})。実装子契約の「期待値が誤りと判断したら
実装を変えずに報告して止まれ」が 3 回とも効いた。

**land 保留とその解消**: 段 9 の受入で帰属赤 2 件が出て land を保留した。(i) 判定器の版と
凍結世代の衝突 — 本 wave の稼働中に [T-1250] が g4 を着地させ `decider_version` に v1 を束縛した。
(ii) ActivationReport の golden digest 変化。裁定パッケージを
`dev-wave-jobs/rulings-inbox/2026-08-17-t1202-t1197-decider-version-generation-collision.md` へ
返し、2026-08-17 のユーザー裁定 (worklog 622) が「第 5 世代を発行して完結する推奨 (a) は却下、
検証済みの改善の着地を優先」と定めた。その後 [T-1167] が先に着地し、本 branch と**同一 hunk** の
v1→v2 bump と g5 (v2 束縛) を main へ入れたため衝突は消滅した。裁定控えが付けていた条件
「着地順に依存するので着地直前に凍結記録の世代を再確認する」を実測で満たしている。
(ii) も allocation-first 復元で条件 12 が短絡するため解消し、golden 更新は不要になった。

**main 取り込みが意味的合成になった**: [T-1167] が同じ実装 file 4 本を触っており競合 11 hunk。
親は当初「gate 順序は本 wave 側を採る」「allocation gate の射程も cross-module にする」と
裁定したが、local main には `test_c12_allocation_binding_gate_precedes_environment_gate` と
`test_c12_allocation_binding_helper_rejects_check_without_read_binding` という [T-1167] の
専用テストが実在し、この 2 本を書き換えないと成立しなかった。しかも両裁定は実 tree の判定を
1 つも変えない。別タスクが着地させた設計判断を効果ゼロで反転させる裁定だったので撤回し、
[T-1167] の構造を保持したまま本 wave の機構を後段へ置いた。

**敵対レビューは段 3・段 6 (実装相)・段 6 (land 相) の 3 度、いずれも 2 レンズ並列**。
land 相はレンズ A が NO-GO (must-fix 4)、レンズ B が GO。所見 4 件のうち 2 件
(裸名照合による誤認、decorator 置換の無視) は local main の性質で本 wave は未変更のため
scope 外とし {{T:bare-name-and-decorator-reachability}} へ送った。1 件 (終端 target の所有固定) は
処方が反証されたので {{T:terminal-target-owner-binding}} へ送った。残る 2 件と
レンズ B の 2 件を実装した。

**恒久ルール違反を 1 件持ち込んでいた**: snapshot 補助が `orchestrator/campaign/` 配下の
tracked な `.py` を全件 archive して展開し、それを 5 箇所が呼んでいた (139 file x 5 = 695 file)。
改修前は契約宣言 path だけを写しており、成長比例コストは本 wave が入れたものである。
レンズ B が検出し、閉包 57 file の 1 回生成へ是正した。焦点走は 540 passed / 47.01s から
544 passed / 45.35s になった。実時間の短縮より、campaign module が増えても展開量が増えない
形に戻したことが本質である。

**セッション異常**: 実装相で親が変異走行中に spool fragment を repo へ書き込み harness を
rc=2 で止めた。段 5 で子 2 本を 1 回の呼び出しでまとめて detach したところ 2 本目が起動せず、
pid file 実在を確認せずに張った待ち手が rc=2 で落ちた。land 相では待ち手が 2 度、
出力ゼロのまま「完了」として戻った (子は pid で生存を確認して継続した)。
fix 第 2 巡の子は停止条件を発火項目以外にも適用して全項目を止めたため、
発火項目だけを止める運用を明記して再投入した。

**環境**: ログインノードの bounded local は cgroup attest 不能で、テストと変異走はすべて
`--force-dispatch` で計算ノードへ投げた。codex 子は pytest を 1 度も実走できず、
実測は全て親が引き受けた。

**工数**: codex 子 16 本 (plan 1 / consult 2 / author 3 / review 4 / fix 6)、すべて `accepted`。
model は plan と consult が `gpt-5.6-sol` / `gpt-5.6-luna` の reasoning=max、
author と fix と review が `gpt-5.6-sol` の reasoning=high。

## 次の一手差分

### 完了

- [T-1202] 8c 事前登録の条件 12 の誤診断を解消し、到達判定を cross-module へ広げて着地した。
  実 tree の 12 条件の status / reason は着地前後で 1 つも変わらない — 条件 12 が指す
  `allocation-enforcement-consumer-absent` は、対になる [T-1167] が先に着地して既に返していた
  値と同じである。本 wave が変えたのは判定の射程であって観測値ではない。
  焦点走 544 passed in 45.35s、変異 matrix は KILLED 7 / SURVIVED 1 (等価) / MISMATCH 0 で
  期待 node 完全集合 36 件が実測と完全一致。判定器の版は s8c-decider/v2 のまま据え置き、
  新しい凍結世代は発行していない (2026-08-17 ユーザー裁定)。
  remaining: none
  base: a80b3429729413fae56a40c1ee6feec7508561e0368e06fea0c5dc66cfdadeba
- [T-1197] 6 条件が共有する到達判定 helper の射程不足を閉じた。同一 module 内 top-level 定義
  だけを辿る形から、契約宣言 root を起点に実 import 束縛だけを辿る canonical
  `(path, 関数名)` graph へ置き換えた。受理規則は {{D:cross-module-reachability}} に明文化した。
  実 tree で cross-module 走査が現に走るのは条件 4 と条件 9 の 2 件で、条件 1 は手前の
  gate で、条件 12 は allocation gate で先に確定するため走らない。
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
- {{T:terminal-target-owner-binding}} **P2・新規**: 終端 target の定義 path を全 12 条件の
  宣言 evidence path の和で照合しているため、別条件が宣言した path に同名の no-op を置いて
  import・call すれば cross-wire できる。land 相の敵対レビューが検出した。ただし
  「条件自身の宣言 path へ限定する」処方は反証済みである — 条件 9 の正規 target
  `assert_campaign_layer3_chain` は条件 10 の宣言 path にあり、限定すると条件 9 の reason が
  `formal-acceptance-layer3-consumer-absent` から `layer3-producer-unreachable` へ変わる。
  契約は正当に別条件の宣言 path にある consumer を参照している。真の修正は
  「終端 target を契約が名指しする所有 path へ束縛する」設計であり、契約 JSON の読み方を変える。
- {{T:bare-name-and-decorator-reachability}} **P2・新規**: `_called_names` は canonical binding を
  見ず裸名と属性末尾名を採るため、未束縛名・dead 枝・未呼出し nested 配下の同名 call を
  到達済みと数える。`_functions` は decorator 付き関数を無条件に canonical 定義とするため、
  runtime に置換される wrapper でなく元 body を辿る。いずれも local main の性質で本 wave は
  変えておらず、条件 12 の allocation gate と条件 9 / 10 / 11 の裸名検査が該当する。
  [T-1167] 系の所有境界と併せて裁定する。
