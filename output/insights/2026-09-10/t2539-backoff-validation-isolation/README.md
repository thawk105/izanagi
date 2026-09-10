# [T-2539] backoff patch と Silo validation 経路の静的非交差 — 一次資料

wave: `dev-wave-t2539-validation-isolation` / branch `worktree-dev-wave-t2539-validation-isolation`

## 何を作ったか

`tools/check_silo_validation_isolation.py` — patch を 1 本受け取り、その編集面が
Silo の validation 経路と静的に交差するかを判定する CLI。
`orchestrator/tests/test_silo_validation_isolation.py` — 20 node の test。

`docs/decisions.md` の D22 が散文で書いていた「純 timing は abort-path タイミングのみで
lock/validation 論理に触れず」を、恒真でない機械検査にした。機械検査は本 wave まで存在しなかった。

## 判定の定義

閉包 V は `TxExecutor::validationPhase` を根とする**下向き呼び先の推移閉包**である。
`std::sort` と `std::max` の implicit comparator edge を含む。`commit()` は呼び手なので含めず、
`writePhase()` は validation 成立後なので含めない。

編集面 E は patch の hunk が写す post-image の source region と、変更された TU macro である。
`I = E ∩ V` が空でなければ交差あり、空かつ閉包が完全かつ全編集が分類済みなら交差なし、
それ以外は判定不能とする。

## 恒真化を避けた設計上の理由

**preprocess 後の出力を一切使わず、全条件枝を残した raw-config union の source で判定する。**
負例 patch は `#if IZANAGI_BREAK_*` の guard を持ち、この macro は既定で未定義である。
preprocess 出力で判定すると負例が「無害」と評価されて検査が恒真になる。

## 交差判定の単調性 (段 6 で入れた設計)

編集が既知の閉包要素へ落ちれば、閉包をそれ以上展開できなくても交差は確定する。展開の失敗は
閉包へ要素を**足せる**だけで**減らせない**。したがって

- **「交差あり」は不完全な (過小近似の) 閉包でも健全**、
- **「交差なし」は閉包が完全なときだけ主張できる**。

verdict の優先順位はこの非対称に従う。交差 → 未消費編集または展開不完全 → 交差なし、の順である。

## 実測 — 全 patch 29 本の判定 (`evidence/all-patches-verdicts.txt`)

| 群 | 件数 | 判定 |
|---|---|---|
| Silo validation 経路を触る既存 patch | 10 | すべて交差あり |
| backoff 族の patch | 5 | すべて交差なし |
| `writePhase()` を触る early-unlock | 1 | 交差なし (V の定義では正しい) |
| 他 protocol・写像不能・未対応 diff | 13 | 判定不能 (fail-closed) |

交差ありの 10 本: `broken-silo-highkey-validation` (深さ 0)、`broken-silo-lockskip-validation`
(深さ 1)、`broken-silo-norw-validation` (深さ 0)、`broken-silo-permutation-erase`、
`broken-silo-permutation-swap`、`broken-silo-sort-nonswo`、`broken-silo-write-intent-erase`、
`broken-silo-write-intent-forge`、`broken-silo-write-intent-opswap`、
`broken-silo-write-intent-ptrswap`、`silo-sort-variant`。

交差なしの backoff 族 5 本: `silo-backoff-fixed`、`instr-silo-backoff-trigger-gating-tally`、
`variant-backoff-red-1e9`、`variant-backoff-static50`、`variant-noop-else-copy`。

## この結果が主張してよい範囲 (最重要)

段 3 と段 6 の敵対レンズが独立に同じ結論へ収束した。

**「交差なし」は、既存 1 group 認証を未実行 schedule へ拡張する licence にならない。**
`Backoff::backoff()` は abort の後始末の後に呼ばれるので、待ち時間を変えれば次の transaction が
読む版・lock 競合・validation の成功失敗の**系列**が変わる。コードが同一であることは、
実行される判定の系列が同一であることを意味しない。示せるのは
「backoff の patch は validation 実装そのものを編集していない」という**補助根拠**までである。

出力の `claim_boundary` はこの非保証を機械可読に載せている。証明しないのは
thread interleaving、validation 判定の系列、abort/retry lifecycle、`commit()` による判定の消費、
`writePhase()` の write/writeback の正しさ、純 timing 性・副作用の不在、serializability と
動的 anomaly の不在、他 protocol の正しさ、他 group・未実行 schedule への認証転用である。
**実走で anomaly を検出した variant は本結果にかかわらず即 reject する** (絶対規律 2)。
`claim_boundary` は `enforced_by_this_checker: false` も持つ — この checker は runtime anomaly を
入力に取らないので、宣言を恒真な保証にしないためである。

### 境界が飾りでないことの具体例

`patches/broken-silo-early-unlock-validation.patch` は「交差なし」を返す。この patch は
lock を解放してから tuple を書く torn-read 窓を開ける既知の正しさ破壊 positive control であり、
file 名に validation を含む。V の定義 (下向き閉包) では判定は正しい —
この patch が編集するのは `writePhase()` だからである。
**つまり「交差なし」は正しさの保証ではない。** これを test node
`test_early_unlock_is_outside_closure_and_claims_no_correctness` に固定した。

## 段 3 の敵対レンズが実装前に潰した所見

レンズ A (検出力・恒真化) が 5 件、レンズ B (主張の射程・正しさ境界) が 6 件の real 所見を出した。
両者が独立に、親 brief の誤記 (`docs/decisions.md:403` を D2 と書いたが正しくは D22) と、
静的非交差から認証転用への飛躍を指摘した。D22 が根拠に引く `transaction.cc:517-540` と
`:154-157` は現在の submodule 実体とずれている (現在の validation は 383-493、
no-wait 即 abort は 160-164)。**本 checker は D22 の逐語より強い断定をしない。**

## 段 6 が閉じた欠陥 — 親の実測が 3 件を確定させた

段 6 の敵対レビュー 2 本と、親が実 patch を機械生成して測った probe が、次を確定させた。

1. **交差が確定しているのに ERROR が上書きしていた。** `validationPhase()` を直接編集する
   既存 patch 7 本が、patch が持ち込んだ別の呼び先を解決できないという無関係な理由で
   判定不能へ落ちていた。単調性を使う優先順位へ直し、7 本すべてが交差ありになった。
2. **既定引数で偽の「交差なし」を返していた。** 閉包の深さ 1 にある
   `ReadElement::get_tidword` に既定引数を足すと (C++ 上は既存の引数なし呼び出しが
   この関数を呼び続ける) 交差なしになった。対照として arity 不変の本体編集は
   交差ありを返していたので、機構は働いていて arity 解決だけが穴だった。
   **安全側の主張における実測できる偽陰性である。** 既定引数を考慮した解決へ直した。
3. **patch のコメント本文が verdict を動かせた。** header へ `/* doc:` `#if TRACE` `*/` の
   3 行を挿入するだけで `TRACE` の macro 編集と解釈され、4 件の交差を作っていた。
   C++ 上はこれは丸ごとコメントである。規律 6 の信頼境界の欠陥であり、
   コメントと literal を除去してから directive を抽出する形へ直した。

親が refuted と判定した所見も 1 件ある。レビュー A の
「`Tidword::obj_/1` が symbol へ誤抽出される」は、正例の閉包 symbol 18 件を列挙して
`obj_` を含む symbol が 0 件であることを確認した。閉包レベルでは再現しない。
ただし `Tidword check;` のような宣言から constructor への edge を張っていないのは事実なので、
実装せず機械可読な適用限界として記載した。

## 変異事前登録と erratum (`mutation/`)

段 4 で 9 変異を位置と意図つきで登録し、DW-M07 に従って期待 node は probe で観測してから確定した。

**初回 probe (`mutation/probe1-*.json`) で 7 件が KILL、2 件が SURVIVED した。**
生存はいずれもテスト側の検出力不足であり、実装の欠陥ではない。DW-M02 に従い実効 gate へ再照準した。

- **M6 (CMake macro leg を落とす)** の生存理由は、閉包内で実際に参照される macro を変える
  test が 1 本も無かったことである。既存の正例が変える `BACKOFF_FIXED` /
  `BACKOFF_NOINLINE` はどちらも閉包参照が空なので、leg を落としても結果が変わらない。
  `cmake/Options.cmake` の `CCBENCH_TRACE` 既定値を変える patch を実体から機械生成する
  node を足した。これは深さ 0/1/1/2 で macro 参照の交差を作る。
  build 設定の変更が validation 経路のコード選択を変える型であり、統制として意味も正しい。
- **M8 (arity 完全一致のみ)** の生存理由は、既定引数の node が「交差なしでないこと」しか
  assert しておらず、変異後の ERROR でも通ってしまうことである。現行実装が実際に返す
  交差 symbol と深さを固定する形へ強めた。必須引数の不一致で判定不能になる統制は別に残した。

再照準後の probe2 (`mutation/probe2-*.json`) で 9 件すべてが node を出した。
本走 spec は probe2 の観測から機械生成した (期待 node 合計 20 件)。

**本走 (`mutation/main-*.json`) は 9/9 KILLED、MISMATCH 0、SURVIVED 0、期待 node 完全一致。**
anchor commit は `b826701c9`。

初回 probe の結果は消していない (`mutation/probe1-result.json`)。M6 / M8 の
初回 SURVIVED は erratum としてここに残る。

### 本走で親が踏んだ手順の失敗

本走の 1 回目は `rc=2` で中止した。理由は親が insight の配置
(`output/insights/.../` の untracked 16 件) を本走の起動と重ねたことで、harness が
「runner/test 実行前に untracked file を検出」と正しく止めた。
`DW-M05` の「変異中は親の編集と worktree へ書きうる子の起動を止める」は tool が検証不能な
親の自己申告義務であり、**段 7 の記録作業を「待機中の独立作業」として並行させると必ず抵触する。**
insight を repo 外へ退避して走らせ直し、`rc=0` で完走した。

## 一次資料

- `verbatim/` — 段 1 brief、段 2 プラン、段 3 レンズ 2 本、段 4 裁定、段 5 実装報告、
  段 6 レビュー 2 本、fix 2 本、台帳子 2 本の逐語。
- `mutation/` — 変異 spec と結果。
- `evidence/all-patches-verdicts.txt` — 全 patch 29 本の判定 (fix 後)。

## 裁定パッケージ候補 (本 wave では実装していない)

1. 閉包 V を validation 結果の consumer (`commit()` の control edge) と `writePhase()` へ
   広げるか。広げれば「correctness logic に触れない」というより強い主張が書けるが、
   「validation 経路」の定義が変わる。段 6 レンズ B が
   `if (validationPhase() || true)` を反例として挙げた。
2. implicit な constructor / destructor edge の実装。現在は張っておらず、
   機械可読な適用限界として記載してある。
3. runtime anomaly evidence を静的 verdict と合成して reject する consumer の新設。
4. D22 の行番号参照が現物とずれている件の更新。
5. 他 protocol への一般化。`Backoff::backoff` の明示呼出しは CCBench 全体に 10 箇所あり、
   本 checker は Silo の root TU しか解析しない (`owner_tus` に明記)。
