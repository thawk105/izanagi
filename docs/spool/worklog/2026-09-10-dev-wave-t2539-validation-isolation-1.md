---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2539-validation-isolation
seq: 1
title: [T-2539] backoff patch と Silo validation 経路の静的非交差を機械検査にした — 既存 1 group 認証を広げる根拠にはならないと 2 レンズが独立に裁定した (コード + テスト + insight、branch worktree-dev-wave-t2539-validation-isolation、変異 9/9 KILLED・期待 node 完全一致)
---

## 本文

- 一次資料は `output/insights/2026-09-10_t2539-backoff-validation-isolation/`。逐語 12 本と
  変異 spec / result 各 3 本、全 patch 29 本の判定表を置いた。
- **依頼への答えは「補助根拠まで」である。** 依頼は「触れていなければ既存の 1 group 認証で
  足りる根拠になる」と書いていたが、段 3 と段 6 の敵対レンズが独立に同じ飛躍を指摘した。
  `Backoff::backoff()` は abort の後始末の後に呼ばれるので、待ち時間を変えれば次の
  transaction が読む版・lock 競合・validation の成功失敗の**系列**が変わる。
  コードが同一であることは、実行される判定の系列が同一であることを意味しない。
  示せるのは「backoff の patch は validation 実装そのものを編集していない」までである。
  この非保証は出力の `claim_boundary` へ機械可読に載せた。
- **散文の主張は既に D22 にあった。** 「純 timing は abort-path タイミングのみで
  lock/validation 論理に触れず」がそれで、本 wave の純増は機械検査と非恒真の witness である。
  親 brief はこれを D2 と誤記し、両レンズが独立に訂正した。D22 が引く
  `transaction.cc:517-540` と `:154-157` は現物とずれている (現在の validation は 383-493、
  no-wait 即 abort は 160-164)。**本 checker は D22 の逐語より強い断定をしない。**
  D22 の参照更新は scope 外とし裁定パッケージへ送った。
- **恒真化の罠を段 1 で実測して brief に書いた。** 負例 patch は `#if IZANAGI_BREAK_*` の
  guard を持ち、この macro は既定で未定義である。preprocess 出力で判定すると負例が
  「無害」と評価されて検査が恒真になる。全条件枝を残した raw-config union の source で
  判定する設計はこの 1 点のために選んだ。
- **段 3 の棄却 finding:** レンズ A は 1 件 (root 不在 test が現 interface で作れない件は
  real として採用)、レンズ B は sort comparator の閉包包含・patch 内容の指示解釈経路・
  既存策で足りる疑い・正例が validation を直接編集する疑いを自ら refuted と判定した。
- **段 3 が実装前に潰した real 所見:** 正例側の恒真化 (CMake leg だけで通せる)、
  過大閉包を排除する対照の不在、純 timing への昇格、共有 header の全 owner TU への一般化、
  静的非交差から認証転用への飛躍。11 件を採用し、閉包 V の拡張は scope 外に置いた。
- **段 6 は親の実測が 3 件の欠陥を確定させた。** 敵対レビュー 2 本の指摘を親が実 patch を
  機械生成して測り直した。(1) 交差が確定しているのに無関係な展開失敗が ERROR で上書きして
  いた — `validationPhase()` を直接編集する既存 patch 7 本が判定不能に落ちていた。
  (2) **既定引数で偽の「交差なし」を返していた** — 閉包の深さ 1 にある
  `ReadElement::get_tidword` に既定引数を足すと交差なしになる。対照 (arity 不変の本体編集) は
  交差ありなので、機構は働いていて arity 解決だけが穴だった。安全側の主張における
  実測できる偽陰性である。(3) patch のコメント本文が verdict を動かせた — header へ
  3 行のコメントを挿入するだけで macro 編集と解釈され 4 交差を作っていた (規律 6)。
- **交差判定の単調性を設計へ入れた。** 編集が既知の閉包要素へ落ちれば、閉包をそれ以上
  展開できなくても交差は確定する。展開の失敗は閉包へ要素を足せるだけで減らせない。
  したがって「交差あり」は不完全な閉包でも健全、「交差なし」は閉包が完全なときだけ
  主張できる。verdict の優先順位はこの非対称に従う。
- **親が refuted と判定した所見が 1 件ある。** レビュー A の
  「`Tidword::obj_/1` が symbol へ誤抽出される」は、正例の閉包 symbol 18 件を列挙して
  `obj_` を含む symbol 0 件を確認した。閉包レベルでは再現しない。constructor edge 不在は
  事実なので、実装せず機械可読な適用限界として記載させた。
- **境界が飾りでない具体例を test へ固定した。** `broken-silo-early-unlock-validation.patch` は
  「交差なし」を返す。lock を解放してから tuple を書く既知の正しさ破壊 positive control で、
  file 名に validation を含む。V の定義では判定は正しい — 編集するのが `writePhase()` だからである。
  **「交差なし」は正しさの保証ではない。**
- **変異事前登録の erratum (DW-M02):** 初回 probe で 9 件中 2 件が SURVIVED した。
  いずれもテスト側の検出力不足で実装の欠陥ではない。M6 (CMake macro leg 削除) は
  閉包内で参照される macro を変える test が 1 本も無かったため、M8 (arity 完全一致) は
  既定引数 node が「交差なしでないこと」しか assert せず ERROR でも通ったためである。
  実効 gate へ再照準し、`cmake/Options.cmake` の `CCBENCH_TRACE` 既定値を変える正例統制を
  足した (深さ 0/1/1/2 で macro 参照の交差)。初回結果は probe ledger に残してある。
- **セッション異常 1:** 変異本走の 1 回目が `rc=2` で中止した。親が insight の配置を
  本走の起動と重ねたため、harness が untracked 16 件を検出して正しく止めた。
  `DW-M05` の「変異中は親の編集を止める」は tool が検証不能な自己申告義務であり、
  **段 7 の記録作業を「待機中の独立作業」として並行させると必ず抵触する。**
  insight を repo 外へ退避して走らせ直し `rc=0` で完走した。
- **セッション異常 2:** 段 5 の投入が 1 回 `rc=2` で即死した。`--reasoning` を
  `--stage author` へ渡したためで、同 flag は plan / consult 専用である
  (段 5 / 6 の effort は docs 権威から導出される)。`.done` を再利用せず新 path で再投入した。
- **実測 (全 patch 29 本):** Silo validation 経路を触る既存 patch 10 本はすべて交差あり、
  backoff 族 5 本はすべて交差なし、`writePhase()` を触る 1 本は交差なし (定義どおり)、
  他 protocol・写像不能の 13 本は判定不能 (fail-closed)。
- **エージェント工数:** codex 子 8 本 (plan 1 / consult 2 / author 1 / review 2 / fix 2) と
  台帳生成 2 本。全子 `outcome=accepted`。receipt は job artifact 側にある。

## 次の一手差分

### 完了

- [T-2539] backoff の patch が Silo validation 経路と静的に交差しないことを機械検査にした。
  判定は preprocess 出力を使わず全条件枝を残した raw-config union の call closure で行い、
  既存の正しさ破壊 patch 10 本で非恒真を示した。ただし**既存 1 group 認証を未実行 schedule へ
  拡張する根拠にはならない** — 補助根拠までである。規律 2 は緩めていない。
  remaining: none
  base: 4fde1d63cd14efde77736119090ccc1d9633df39fb65210909d80a65f51b3722

### 新規

- {{T:validation-closure-consumer-boundary}} **P2・新規・ユーザー裁定待ち**: 閉包 V を
  validation 結果の consumer (`commit()` の control edge) と `writePhase()` へ広げるか。
  広げれば「correctness logic に触れない」というより強い主張が書けるが、
  「validation 経路」の定義が変わる。段 6 レンズ B が `if (validationPhase() || true)` を
  反例に挙げ、親の実測では `broken-silo-early-unlock-validation.patch` が実物にあたる。
- {{T:validation-closure-implicit-lifetime-edges}} **P3・新規**: 閉包へ implicit な
  constructor / destructor edge を張る。現在は張っておらず機械可読な適用限界としてある。
  `Tidword check;` のような宣言から呼ばれる constructor を編集しても交差にならない。
- {{T:validation-isolation-runtime-anomaly-consumer}} **P3・新規**: runtime anomaly evidence を
  静的 verdict と合成して reject する consumer を置く。現在 `claim_boundary` の
  `runtime_anomaly_policy` は宣言で、checker 自身は強制しない (`enforced_by_this_checker: false`)。
- {{T:d22-stale-line-references}} **P3・新規**: D22 が引く `transaction.cc:517-540` と
  `:154-157` が現物とずれている件を更新する。現在の validation は 383-493、
  no-wait 即 abort は 160-164。
- {{T:validation-isolation-other-protocols}} **P3・新規**: 本 checker を他 protocol の
  owner TU へ広げる。`Backoff::backoff` の明示呼出しは CCBench 全体に 10 箇所あり、
  現在は Silo の root TU だけを解析する (`owner_tus` に明記)。
