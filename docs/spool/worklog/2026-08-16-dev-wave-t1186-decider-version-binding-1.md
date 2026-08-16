---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1186-decider-version-binding
seq: 1
title: 8c 事前登録の凍結記録へ判定器の版を 1 個記録し発効側に一致を要求した — 敵対 2 レンズが独立に「空改訂を許す例外」を止めた (コード + テスト、branch worktree-dev-wave-t1186-decider-version-binding、変異 matrix = 9/9 KILLED)
---

## 本文

- ユーザー裁定 (2026-08-16 /rulings 全件 第 2 回 #6、authority=user) は「判定器・評価器・射影の
  bytes 全体を凍結範囲へ入れない。凍結記録へ判定器の版を 1 個記録し、8c 事前登録の消費側が
  その一致を要求する」である。全 bytes 凍結は無関係な整形変更でも世代を上げる必要を生み、
  開発を止める型の検証機構になる。設計判断は {{D:s8c-decider-version-binding}}。
- 親が brief 前に実測した 3 点。(1) HEAD の 8c は NOT_EFFECTIVE (§5 が 9 欄 UNFILLED、
  C01〜C12 が evaluator-exception) であり、発効側を締めても動いている成果物は 1 つも無い。
  (2) `ActivationReport` は判定器・評価器の観測 hash を既に持つが、凍結記録側に対応 field が無く、
  一致を要求する consumer は 1 つも無い。(3) 凍結記録 path を pin する外部台帳・trust root は無く、
  参照は当 module と decisions 本文と正本 doc の改訂手続き節だけである。
- **段 3 の敵対 2 レンズが独立に同じ急所を突いた。** 段 2 プランは「保護 hash が同じでも版が違えば
  世代追加を許す」例外を `_assert_history_transition` へ入れる案だったが、正本 doc の
  **凍結範囲に含まれる保護ブロック自身**に「世代だけを増やす空改訂は機械検査で赤になる」と
  明記されている。実装だけが規範を無断で変えることになるため親は例外を却下した。
  代わりに、次世代 record を作る wave が同じ commit で正本 doc の改訂手続きを改訂すれば
  保護 hash が変わり、空改訂ではなくなるので例外自体が不要になる。
  副次的に履歴状態を触らずに済み、merge 遷移まわりの既存 fixture 更新 12 件級が消えた。
- レンズ A は「射影だけを更新した子孫 commit で、同じ世代・同じ版のまま旧 capability を
  再発行できる」を出した。判定器と評価器には「走っているコードが判定対象 commit の blob と
  一致すること」の検査があるのに、**射影モジュールにだけ無かった**。これは凍結範囲を広げる話ではなく
  既存契約の欠落なので採用し、同型の検査を足した。
- レンズ A の「版の bump 忘れを機械検出せよ」は**不採用**とした。bytes 凍結の再導入であり
  ユーザー裁定に反する。同日 18:xx の /rulings 第 3 回 #6 も凍結族について
  「束縛機構を増やさない」としており向きが一致する。限界は下記に明記する。
- 段 6 のレビューは 2 本合わせて blocker 4 件を出し、全件 fix で閉じた。とくに新設した射影検査が
  既存の `evaluator-blob-mismatch` を**先取り**して既存テスト 1 件を赤にしていた。
  期待値を変えず、3 つの同一性検査を core → evaluator → projection の順に連続させ、
  すべて通ったときだけ評価器を実行する形へ直した。焦点再レビューは所見ゼロで GO。
- 変異 matrix は使い捨て worktree (`tools/mutation_worktree.py`、runner=dispatch) で走らせ、
  権威は第 4 走の **9/9 KILLED、MISMATCH 0、baseline PASSED、wrapper rc=0**。
  台帳は `output/insights/2026-08-16_t1186-decider-version/`。
  probe (第 3 走) で 1 件が SURVIVED し、`str.__eq__` を直接呼ぶ層による mask だと分かったため
  両層同時変異へ再照準した経緯は同 README の erratum に残した。
- **親が production 経路で発火を実測した。** 最終 tip で
  `python3 -m orchestrator.campaign.s8c_preregistration check --repo-root .` を走らせ、
  実在する tip record (`condition-freeze.v1.g3.json`) に対して
  `decider_version decider-version-unbound` を返すことを確認した。gate は dormant ではない。
- **この wave が保証しないこと。** (1) 受理意味を変えたのに版を bump しなかった場合は検出しない。
  版の一致検査が止めるのは「明示的に bump した後で古い世代の記録を使い続けること」であり、
  bump 忘れは裁定が受け入れた手動 provenance の範囲に残る。(2) 3 者の同一性検査は検査時点の
  ファイル bytes と対象 commit の blob を比べるもので、既に import 済みのコードは束縛しない
  (判定器・評価器の既存契約と同じ性質)。(3) 版を束縛した世代 record はまだ存在しないため、
  **次世代が着地するまで 8c は発効できない**。これは意図した fail-closed である。

## 次の一手差分

### 完了

- [T-1186] 凍結記録 schema に版を持つ v2 を足し、発効判定が走っている判定器の版との一致を
  要求する形にした。legacy v1 記録は読めるまま残し、tip が v1 なら値を比較せず無条件に非発効とする。
  射影モジュールの同一性検査も足した。変異 9/9 KILLED。残余と保証しないことは本エントリ本文と
  {{D:s8c-decider-version-binding}} に明記した。
  remaining: none
  base: e54fecf9184152d1c972fe606c6ee42508bf5eaec7ed52d57483229d0f1c9727

### 新規

- {{T:s8c-decider-version-generation}} **P1・新規**: 版を束縛した次世代の条件契約 record を発行する。
  同じ commit で正本 doc の改訂手続きブロックへ「世代 record は判定器の版を持ち、判定器・評価器・
  射影の受理意味を変える変更は版を bump して新世代を要する」を書く。doc 改訂で保護 hash が変わるため
  空改訂にならず、`spurious-revision` の例外を必要としない。`ruling_reference` は
  {{D:s8c-decider-version-binding}} を指す。**これが着地するまで 8c は発効できない。**
- {{T:decider-identity-toctou}} **P2・新規**: 判定器・評価器・射影の同一性検査が、検査時点の
  ファイル bytes ではなく**既に import 済みのコード**を束縛するようにできるかを検討する。
  現状は 3 者とも同型の穴を持つ (射影を import してから disk を旧 bytes へ戻すと、報告は旧 commit を
  参照したまま実行意味だけが新しくなる)。3 者一括の設計変更になるため単独 wave とする。
- {{T:decider-version-in-certification-closure}} **P3・新規**: acceptance receipt と
  reflux の origin capability は活性化報告 digest を opaque な hash としてしか検査せず、
  判定器の版を独立に再導出しない。現状はどちらも non-certifying で Layer 3 が拒否するため
  受理集合は広がらないが、認証閉包を新設する wave (admission receipt / 全 certified sink) が
  判定器 module 群も対象に含めるべきかを裁定する。
