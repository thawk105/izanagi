---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2437-record-issuer
seq: 1
title: [T-2437] result-evidence の producer を production の実行結果へ配線した — 依頼 4 項のうち 3 項を実装し、公開呼び手は発火経路が無いことを実測して裁定へ返した (コード + テスト + insight、branch worktree-dev-wave-t2437-record-issuer、変異 5/5 KILLED・期待 node 完全一致・登録 SURVIVED 1・閉包内 8 変異は帰属不能で不登録)
---

## 本文

- **当初の完了判定を取り下げた。** 段 1 brief は「formal consumer が受理し `P6Unavailable` へ到達する」を
  完了判定に置いたが、段 3 の 2 レンズが独立に到達不能を示し、親が現物で裏取りした。
  受理側は exact 33 record を要求し 1 campaign run は 1 件しか作らない。さらに ledger の
  evidence digest は seal 時に確定するのに、新しい record は attempt ID・nonce・timestamp という
  毎回変わる値を含む。**「先に答えを知っている fixture」でしか通らない循環**であり、
  自由生成 record の受理は原理的に示せない。差し替えた完了判定と名乗りの上限は
  {{D:result-evidence-production-issuer}} と insight §2 に置いた。
- **依頼 4 項のうち `run_origin_trial` の production 呼び手だけを裁定へ返した。**
  公開呼び手を置いても issuer へ到達する経路が 1 本も無いことを実測した (`main()` が fixture provider の
  real build を拒否、`--no-build` は `run_campaign()` の手前で戻る、registered manifest は
  exact `generations == 2` を要求)。発火しない機構を置くのは実装したふりなので DW-G04 で留めた。
- **段 6 で「緑だが守れていない」を 3 回続けて見つけた。**(1) 発行 context を渡さない既定経路でも
  引数が評価され既存 3 node が落ちる ({{F:early-return-does-not-guard-argument-evaluation}})。
  (2) 受領証の真正性を誰も検証せず、条件に合う任意の dict が通る。権威検証器は repo に既にあったのに
  参照 0 件で、中心正例も合成受領証で穴を通っていた。(3) それを直した後も検証の分岐を呼び手が
  自己申告できた ({{F:gate-checks-presence-not-authenticity}})。(1) は親の焦点走、(2) は段 6 の
  2 レンズが独立に、(3) は焦点再レビューが述語を実際に評価して見つけた。
- **変異事前登録の 14 件のうち 8 件を、実測に基づいて登録から外した。**
  `loop.py` と `pipeline.py` は campaign lock の enforcement source closure に含まれるため、
  変異を注入すると `contract-loader-drift` が狙った関門より先に発火し、campaign を構築する
  全 test が落ちる。probe の観測は閉包内 8〜10 node に対し閉包外 0〜4 node で、帰属が成立しない。
  期待 node に drift 由来の赤を含めれば形式上は完全一致するが、それは偽の KILLED を台帳へ残すことになる
  ({{F:mutation-blocked-by-source-closure}})。この制約は本 wave 固有ではなく同じ閉包に載る全 file に及ぶ。
- **子の実走は親の全走を代替しないことが再度実証された。** 実装子はどの段でも `tools/run_tests.py` を
  通せず (sandbox の `qstat -Q` preflight で rc=16)、単位 C の中心 3 node は子の環境で走らなかった。
  親が commit 後に走らせて初めて上記 (1) の回帰が出た。
- 親の手順ミス 2 件: 同一 worktree から dispatch を 2 本並行投入して一時 orphan hold を作った
  (後発が正しく拒否され、実害なし)。変異走行中に親が worktree へ insight ディレクトリを作り、
  共有木の事後検査を落とした (probe は全件完走済みで結果は有効)。どちらも DW-O26 / DW-M05 が
  明記していた禁止事項である。
- 工数: codex 子 11 本 (plan 1 / consult 2 / author 4 / review 3 / fix 2)。うち単位 C の初回は
  model call 上限 100 で無言死し、上限を上げた継続子が監査と修正と報告を引き継いだ。

## 次の一手差分

### 更新

- [T-2437] **P2**: record 層 producer core API (D1809) を production の実行結果へ配線した。
  `EvalResult` が local verifier 由来の rejected の typed `VerifyResult` を保持し、
  `run_campaign()` が per-result で issue を呼び、ordered WAL projection producer が
  terminal 時点の WAL prefix snapshot から証拠を作る。発行は解決済み契約から読んだ値で
  権威検証器に掛けた認証済み受領証がある場合だけ通る ({{D:result-evidence-production-issuer}})。
  **残るのは `run_origin_trial` の production 呼び手**で、置いても issuer へ到達する経路が
  無いことを実測したため裁定へ返した。到達させるには (a) `main()` の fixture provider real build
  拒否の解除、(b) `--no-build` 経路の変更、(c) `generations == 2` 制約との整合、
  (d) completeness の origin 分岐、の 4 件が要る。
  base: 973a0c59e2bc3b56cfa5a0ef63f41047dbb59b825754cad2557609661640c10a

### 新規

- {{T:origin-trial-public-caller}} **P2・新規**: `run_origin_trial` の production 呼び手を置く。
  [T-2437] の残余。現状は公開呼び手を置いても issuer へ到達しないので、上記 (a)〜(d) の
  どれをどこまで scope に含めるかをユーザー裁定で決めてから着手する。
- {{T:completeness-origin-branch}} **P2・新規**: completeness の origin 分岐を入れる。
  物理 search config の `origin_campaign_run` key を exact key gate が許さず、
  rejected build は `built_and_benched >= 1` を満たさないため、origin trial の report が完了しない。
  設計 §12 はこの層と材料レポート renderer に触れずに「結線した」と名乗ってはならないと明記する。
- {{T:issuer-failure-tombstone}} **P3・新規**: terminal 後の issuer 失敗を ledger tombstone へ接続するか
  裁定する。現状は terminal WAL と部分 content artifact が残り record が無く、
  受理側は fail-closed で拒否するが自動 tombstone 経路は無い。
- {{T:source-closure-mutation-method}} **P3・新規**: enforcement source closure に載る file の
  関門を変異で裏取りする方法を決める ({{F:mutation-blocked-by-source-closure}})。
  現行 harness では drift が先に発火して帰属できない。
