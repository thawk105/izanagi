## 所見

以下、`brief.md`・`plan.md`・`inventory/`・`sibling-owned-files.txt` は指定された job directory 内を指す。静的検査のみ実施し、ファイル変更・pytest・変異実行は行っていない。

1. **real / should — scanner 外に、同じ入力・検査を繰り返す5件がある。**

   `plan.md:36` の「真の重複関数がない」は、B1 候補7組に限定すべき。次の5件は `inventory.json` で当該関数の分類が空だった。パスはすべて `orchestrator/tests/test_p3_s4_loop.py`。

   |削除を検討できる位置|残存側の位置|静的根拠|
   |---|---|---|
   |`:3238` の関数|`:3248` の `[middle-int]`・`[middle-float]`|`20` / `20.0`、implementation 文字列、`CoderProposal` 構築と `assert_value_literal_consistent` 呼出しが一致する。|
   |`:3271` の `nonintegral` row|`:1913`|同じ `20.5` と implementation を渡す。残存側は例外型・文言・rule_id に加え stage・reason も検査する。|
   |`:3272` の `bool` row|`:1911`|同じ `True` と `"double now_backoff = 1;"`。残存側の検査が包含する。|
   |`:3275` の `zero` row|`:1914`|同じ `0` と implementation、同じ range rule。残存側の検査が包含する。|
   |`:3277` の `above-upper` row|`:1915`|同じ `1001` と implementation、同じ range rule。残存側の検査が包含する。|

   原因は、関数全体の AST 比較では通常関数と parameterized test の包含関係を拾えず、row 比較も別 decorator 間の実効入力まで比較していないこと。**静的な重複候補として real であり、削除承認済みという意味ではない。** 共通 fixture は同 file の `:84`。親はこの局所5件を追加評価し、同一 file 内の意味的重複を今回の B に含めるか明記する。本文内ループの整理などには広げない。

2. **refuted / should — inventory の既存候補を大量に残した判断が、直ちに過少削除とはいえない。**

   - `orchestrator/tests/test_s6_sort_sweep.py:79` と `test_s8a_trigger_sweep.py:86` は別 production module の source を検査している。本文同一だけでは代替できない。
   - `test_env_contract.py:191` の `False` と `0`、`test_p3_s4_loop.py:3248` の int/float は型境界の異なる入力。Python の値比較による重複判定をそのまま採用できない。
   - `test_dev_waves_cli.py:312` は `Path.exists` を mock するが、実際の `supervisor.export` が既存 destination を拒否するか検査する。mock 自身の返値だけを assert する恒真テストではない。
   - `test_ruleops.py:2248` の `assert 1 == 1` は合成 source の内容。実際の検査は `:2271` の receipt 整合性拒否であり、削除根拠にならない。

   推奨は既存保持判断を維持し、所見1の取りこぼしだけを局所的に補うこと。恒真 mock テストの実例は今回確認できなかった。

3. **refuted / should — 現行削除案に D 混入・要求外の掃除はない。**

   `plan.md:13` の差分は、`test_s8b_holdout_freeze.py:2383` の重複 `True` と対応 id の除去だけ。`plan.md:367`・`:369` は変更 file を1本に限定し、本文・期待値・helper・fixture・import を変更しない。D は `:311` で全件保持している。

   `tools/update_acceptance_duration_ledger.py:21` の凍結8 suite に holdout-freeze は含まれない。台帳追随が必須なら候補を外す `plan.md:373` も scope に整合する。変異実験中の一時注入と、production の永続差分は区別すべきであり、前者だけを scope 逸脱とは数えない。

4. **real / should — P4 は有限の変異集合に対する証拠であり、検出力全体の保存証明ではない。**

   `brief.md:8` の「削除で消える検出力が無いこと」と、`:12` の module ごと負例2〜3件には論理的な隔たりがある。今回の M1/M2 は `orchestrator/campaign/s8b_holdout_freeze.py:1981`・`:1983` の同じ選択拒否を攻撃するため、module 全体の独立した挙動を代表するものではない。

   ただし今回の1 row は、`test_s8b_holdout_freeze.py:2381` の**同じ関数・同じ型の同じ入力**である。入力、fixture、id 依存の有無を確認した同値性の根拠と、`plan.md:303` の変異別 `S − {d}` 完全一致を組み合わせる形は妥当。

   推奨は、主張を「登録した変異に対する検出集合保存＋削除ケースの同値性確認」とすること。module 内に異質な削除を追加する場合、負例の個数だけで十分とは判定しない。

5. **real / should — 「module 数 × 3走」を job 数と読むと費用を過少評価する。**

   `plan.md:385` が所要未実測とする点は正直だが、見積単位の補足が必要。harness は次を別々に実行する。

   - collection：`tools/mutation_harness.py:3226`
   - baseline：`:3271`
   - 各 mutation：`:3307`

   dispatch mode の collection も `:1525` で dispatch command を構成する。M1・M2・E1 の fresh 本走は、通常 **collection 1＋baseline 1＋変異3＝5 job 相当**。pre/post で10 job、さらに probe が加わる。probe も同じ一式なら合計15 jobになる。「1走＝1 job」は個々の runner 実行には使えても、spec 全体には使えない。

   推奨は、20 runner file の実行費用、collection、投入待ち、probe を分けて見積もること。harness が既に行う同一 HEAD・同一 runner の baseline と別の重複確認を増やさない。未測定のため「400 call や所要上限を超える」とまでは断定しない。

6. **refuted / should — P1/P2 と現行所有分割は妥当。**

   `sibling-owned-files.txt:2`〜`:7` の6 file と、`plan.md:367` の変更 file は交差しない。author は1単位・編集2行であり、多数 file の削除が400 model call を圧迫する構成ではない。`d95.md:11` の Codex author 必須にも従っている。

   P1 は hold・golden・凍結台帳を変えずに済ませる局所境界として合理的。ただし「登録されているから永久に削除不能」という一般制度にはしない。P2 の一覧は時点付きなので、`brief.md:10` が要求する段4での再確認は維持する。runner に sibling file を含めること自体は編集所有の衝突ではないが、pre/post でその内容も固定する必要がある。

7. **real / must-fix〔最終成果物の完成条件〕— D 裁定パッケージはまだ確定一覧ではない。**

   `plan.md:311` の291関数は scanner 候補数であり、`:380` によれば246件は個別未確認。`:313` も代表からの一般化を明確に否定している。この留保は適切だが、`brief.md:6` が求める D の件数・file・pin 先の確定報告は未完了。

   推奨は、最終成果物で「D 確認済み」「D ではない」「未確認候補」を分け、確認済み D に pin 先を対応づけること。291件をそのまま D の確定件数として裁定に渡さない。放置すると裁定用レポートの件数・対象参照が不正確になるため、これは報告完成上の must-fix。テスト削除を増やす要求ではない。

## 裁定パッケージ候補

**対象 module ごと1 spec の例外化。** `brief.md:6` のユーザー裁定を変更するため、親判断だけでは採用できない。

選択肢は、現行の module ごとの pre/post を維持するか、同じ関数の同型同値 row に限り、fixture・mark・id 依存まで確認した同値性資料で個別の変異実走を代替するか。

**今回は現行維持を推奨する。** 対象は既に1 module なので「代表1 module に絞る」節約はない。AST 本文同一だけの一般免除は、所見2の別 binding 例で成立しない。将来、多 module の完全重複が実際に見つかった段階で、例外の費用効果を再提示するのが妥当。

## 親 brief への所見

- **real / should — 母数の整合が必要。** `brief.md:4` は391 file、`inventory/inventory.json:16` は363 file。今回の直接 glob も363だった。基準時点・glob・helper 込みなどの数え方を明記する。これだけから scanner が28 file を落としたとはいえない。

- **real / should — collection と wall の改善は未証明。** `brief.md:3` の動機から「node 減少に比例して collection や受入 wall が減る」とは導けない。`docs/decisions.md:62586` の D2046 は、pre が55.4〜59.1秒、wall が296.2〜604.5秒と別々に変動し、残差の成分配分も未確定としている。1 node を減らしても同 file の import・収集処理は残る。

- **refuted / should — plan の33秒表示は概ね適切。** `plan.md:384` は wall や setup が33秒減ると主張していない。台帳の当該 entry は `orchestrator/tests/acceptance_duration_ledger.json:17613` の33.0秒。ただし台帳は編集しないので、`:389` の17,925.8秒は**削除 node を除いた台帳換算値**であり、台帳ファイルの総和や実測 worker 秒が変わった値ではない。

- **P3 は候補生成として妥当、網羅性の根拠としては不足。** `inventory/inventory.md:311` は未評価 row 1,198件・container 133件を明示する。所見1も含め、scanner が挙げなかったものを「低価値なし」とは扱えない。汎用 scanner 拡張や新 gate は不要で、局所確認と限界記載でよい。DW-G03 の独立2例は制度一般化の条件であり、同じ file の重複5件だけで全 repo の新制度を作る根拠にはならない。

- **real / should — DW-G05 の1行は修正した方が正確。** `brief.md:16` は既存成果物への直接影響がない点では妥当だが、4.99時間を将来の維持値のように書き、誤削除の影響は抽象的。次の表現を推奨する。
  **「放置しても既存 certified 選択・レポート・台帳値は変わらず、重複1 node の台帳換算33 worker 秒が残る；誤削除は将来の earliest-eligible 選択違反を検出する回帰防壁を欠落させ得るため、残存ケースの同値性と登録変異の pre/post 検出集合を確認する。」**

  明示されたユーザー依頼の局所掃除として進める根拠はある。研究 blocker の解消や一般的な高速化制度としては位置づけない。

## 総括

現行の1 row 削除案に、過剰削除・D 混入・所有衝突は確認しなかった。一方、scanner 外に通常関数1件と parameter row 4件の重複候補を確認した。追加削除は同値性と変異費用を確認して親が判断する。

優先する修正は、D 裁定一覧の完成、spec 実行回数と job 数の区別、削減量を台帳換算 worker 秒に限定する記述。静的相談としての結論であり、pytest 緑・KILLED・実測 wall 短縮は未確認。