---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-b2-descriptor-prereg
seq: 1
title: B-2 の判定規則には generation/search 固有の読み替えが凍結されていない — 実装差分ゼロ (docs のみ、branch worktree-dev-wave-b2-descriptor-prereg)
---

## 本文

- 依頼は「B-2 (descriptor を条件にした合成の因果証拠) の実験を設計し事前登録する。
  因子・セル・反復・判定規則を実走前に commit する。批准の閂が閉じているので実走は後続へ起票」。
  **成果物は実装差分ゼロの裁定パッケージ =
  `output/insights/2026-08-26_b2-descriptor-causal-evidence/`。**
- **依頼が求めた事前登録の大半は既に存在していた。** B-2 の器は 8b 設計 §7 段階 2 の
  generation/search 実験であり、その事前登録は `docs/phase3-8c-preregistration.md` である。
  因子 (3 arm × 2 holdout)・セル (6)・世代予算 (`G=2` 厳密)・判定規則の構造・全件報告・停止規則は
  凍結済みだった。**新規に書けば二重登録になる。**
- **本 wave の純増は 1 点である — 判定規則に generation/search 固有の穴がある。**
  8b §6 / §10.1 の 3 条件と `s8c_result_judge.py` の条件 ID は「予測構成」を入力に取る
  selector 語彙だが、generation/search arm の出力は合成された variant であり、
  しかも `G=2` で 2 世代ぶんの proposal が出る。**どれを arm の構成として判定表へ入れるかが
  一意でない。** judge は予測を構成 ID へ正規化するのに、supervisor は proposal と
  `harness.variant` を記録するだけで予測写像を作らない。decisions を主題で検索しても
  この読み替えを裁定した D は 0 件だった。これは 8b §8 の「判定基準」に当たるため、
  再凍結 + ユーザー承認が要る。**実装せず裁定へ送った。**
- **同日の先行 wave (エントリ 981) が既に B-2 の precheck を出していた。** 親は段 7 の記録中に
  worklog archive を主題で検索して気づき、**書き上げた成果物を差分へ書き直した。**
  先行 package が扱った実走入口の層 (a)〜(f) は本書で繰り返さず、再測して
  「再訪条件は 1 つも成立していない」ことだけを記した。
- **親の provisional 裁定 4 件のうち 2 件が覆り、1 件は自ら取り下げた。**
  (P2)「新規 pilot 事前登録を中心成果物にする」は取り下げ — 裁定 1 が決まるまで因子・セルが
  書けず、別文書で先取りすると 8b §8 の再凍結手続きの迂回になる。
  段 2 と段 3 の 2 レンズが、異なる経路から独立に同じ結論を出した。
  (P4)「実装面は `check_docs.py` の登録だけ」も、P2 の取り下げにより実装面ゼロへ変わった。
- **親の実測 2 件が段 2 に反証された。** (i) 「§5 の未記入は 7 欄」は誤りで、9 行中 8 行。
  (ii) 「判定パラメータの機械検証 consumer は既に実在する」は過大評価で、
  parser の違反が発効判定へ結線されておらず、judge には production の呼び手が無い。
  **どちらも親が brief に書いた実測の一般化しすぎだった。**
- **親は F369 / F631 の罠を一度踏んだ。** 最初に判定器を CLI 形式で測って全条件
  `evaluator-exception` を得た。library 経路で測り直し、後から先行 package が名指ししていた
  正しい入口 (`python3 -m orchestrator.campaign.s8c_gate_report`) を知って取り直し、
  両者が完全一致することを確認した。**その過程で、同じ欠陥に F369 と F631 の 2 件が
  登録されていることが分かった** (機序・道具・帰結が同一)。自己改善契約の routing 規則は
  同型再発を既存 F への追記に限っているので、F631 の新設はこれに反する。台帳は本 wave で
  直さず裁定へ送った。
- 段 2 のプラン起草 1 本 (read-only, xhigh)、段 3 の敵対検証 2 本 (sol / luna, read-only, xhigh)。
  段 4 で「実装しない」と裁定したため段 5・6 は飛ばした。
  実装面の差分ゼロのため変異 matrix は免除、受入全走は実施した。

## 次の一手差分

### 新規

- {{T:b2-generation-outcome-unit}} **P1・ユーザー裁定待ち**: generation/search arm の「出力単位」を
  3 案 (proposal sequence 全体 / 最終世代の canonical variant / 合成後の決定論的 selector) から
  裁定し、8b §8 の再凍結と 8c 条件契約世代の改訂で正本化する。親の推奨は proposal sequence 全体。
  裁定パッケージは `output/insights/2026-08-26_b2-descriptor-causal-evidence/` §4 裁定 1。
- {{T:s8c-section5-param-consumer}} **P2・新規**: 8c §5 の判定パラメータ欄に実効性のある
  consumer を作る。`section5_value_violations` を発効判定の連言へ入れ、発効版 §5 から
  `_ContrastParams` を構築する束縛と、supervisor から judge を経て 3 表を出す production 経路を
  実装する。受理集合を変えるため decider の版上げと 8c 世代 record を伴う。
- {{T:b2-pair-planning-pilot-prereg}} **P2・新規**: `n` / `delta_min` / `sd_max` を決める
  対計画用 pilot を事前登録する。{{T:b2-generation-outcome-unit}} と
  {{T:s8c-section5-param-consumer}} が land した後に着手する。導出関数の恒真化を防ぐため、
  `delta_min` は pilot と独立に固定し、pilot は `n` と `sd_max` の導出に限定する。
  既存の T-1142 n-pilot (oracle argmax 用・R=11・R>=32 未達) は既知結果台帳へ載せ、
  前向き導出から除外する。
- {{T:b2-pilot-role-rejection}} **P3・新規**: pilot 成果を B-2 の証拠に数えない保証を機械強制する。
  現在この非算入は全系列共通の `certifying=False` による恒真であり、pilot 固有の拒否経路が無い。
  pilot 専用 namespace と不変な `experiment_role` を設け、正式 manifest・result judge・受入が
  その role を拒否する結線と positive control を置く。
- {{T:failures-f369-f631-duplicate}} **P3・ユーザー裁定待ち**: `docs/failures.md` に同一欠陥が
  F369 と F631 の 2 件で登録されている問題を裁定する。台帳の既存 bytes を動かす操作なので
  統合の可否と手順を人間が決める。
