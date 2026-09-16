## 受理集合と fail-closed への所見

以下はすべて**読解**による所見。テスト・変異は実行していない。位置表記では次の略称を使う。

- `driver` = `orchestrator/campaign/s1_direct_comparison.py`
- `test` = `orchestrator/tests/test_s1_direct_comparison.py`
- `gate` = `orchestrator/campaign/condition_meaning_gate.py`
- `brief` = `output/insights/2026-09-16_t2651-diag-detail-review/verbatim/s1-brief.md`
- `plan` = `/home/SFC/tanab/.claude/jobs/f3824ce9/wave/s2-plan.md`

**S1：通常の発行経路について、受理集合を広げる反例は確認できなかった。**

- **位置:** `driver:331–355`、`gate:4019–4059,4088–4103`。
- **成果物影響:** 確認した経路では、診断整形によって拒否された record が certified な選択材料として返ることはない。
- **根拠の種別:** 読解。
- **攻撃と結果:** admission は整形前に確定し、整形は `not admission.admitted` の枝だけで動く。その枝には正常 return がなく、通常例外を fallback にしても最後は `DriverError` になる。admitted の場合は整形せず record を返す。
- **限界:** 現行コードの制御フローについての結論であり、着地前後の全入力に対する bytes・rc 不変の実測証明ではない。

**S2：属性失敗・非 dict・二重の非 green 判定という攻撃は、現行の発行型契約で大部分が排除される。**

- **位置:** `driver:335–353`、`gate:655–667,1044,4019–4039,4088–4089`。
- **成果物影響:** 正常な発行 record では reason の対応と拒否を保持する。detail 欠落は本文上の代替表現になり、受理集合は変わらない。
- **根拠の種別:** 読解。
- **反例候補と結果:**
  - `evidence` が dict でないこと自体は異常ではない。実 factory は `MappingProxyType` を返し、`.get()` を使用できる。
  - `detail` 欠落なら `<detail unavailable>` を整形する。
  - 非 Mapping、異常な `macro` / `arm` / `reason_code` は admission 前の検証に抵触する。
  - `reasons` の `!= "green"` と detail ループの `== "green"` は、検証済みの exact `str` では相補的である。比較演算子を細工した subclass による齟齬は、その型検査を越えられない。
- **残る境界:** `reasons` と detail ループの status 取得は整形側の `try` 外。ただし、ここを破るには検証後の強制的な属性改変など追加条件が必要で、今回の変更による到達可能な欠陥とは確認できなかった。

**S3：「non-green はすべて拒否本文へ入る」という一般化は誤り。ただし既存 admission 契約どおりである。**

- **位置:** `gate:3335–3340,4098–4107`、`driver:334,342,355`。
- **成果物影響:** supply が green、meaning が unestablished の組は admission が受理し、拒否本文を作らず返る。今回の追加による受理集合変更ではない。
- **根拠の種別:** 読解。
- **具体例:** 正規発行された `supply=green / meaning=unestablished` → `admitted=True` → 整形なし。別の red によって family が拒否された場合には、その unestablished record も本文対象になる。
- **判断:** 「red 本文保持」と「全 non-green の拒否」を同一視してはいけない。gate 本体の変更要求ではない。

**S4：`Exception` 捕捉が fail-open を作る経路は確認できない。`BaseException` 非捕捉も成立する。**

- **位置:** `driver:272–295,344–354,1321–1327,1408–1415`、`test:200–232,328–342`。
- **成果物影響:** 通常の整形失敗は拒否理由を保った `DriverError` になる。終了割込みはそれを置換して伝播し、通常の拒否 rc を保証しない。
- **根拠の種別:** 読解。
- **具体例:** helper が `RuntimeError` を送出 → 外側が捕捉 → fallback を付加 → `DriverError`。helper が `SystemExit(0)` を送出 → 内外とも捕捉せず伝播 → プロセスは rc=0 になり得る。ただし record は返らず、certified な選択が成立する反例ではない。
- **判断:** 後者は「BaseException を捕捉しない」という明示契約の帰結であり、実際の helper が通常の文字列から `SystemExit(0)` を生成する経路は見つかっていない。「rc 不変」は終了割込みまで含む無条件の保証として記載できない。

## 親 brief への所見

**B1：完了条件の「全件 KILLED」は、契約上の kill と harness の分類を混同する危険がある。記録上の要修正候補。**

- **位置:** `brief:14–16,48–49`、`plan:165`、`docs/dev-wave/mutation.md:18–20,59–63`。
- **成果物影響:** 診断文字列への感度を正しさ防壁の検出力として試行台帳・変異 matrix に過大計上する。
- **根拠の種別:** 読解。
- **反例:** M5 で tail を空にする → tail assertion が失敗する一方、admission・拒否型・通常 rc は同じ → これを「正しさ弱体化を kill」と集計すると証拠の意味が変わる。
- **意見:** 6 変異の実施を維持しつつ、harness 判定と契約上の証拠分類を分けるべきである。P2 の変異固定は、その分類を固定する根拠にはならない。

**B2：P1 は対象6変異の診断検査として妥当だが、正しさ防壁全体の保証へ拡張できない。**

- **位置:** `brief:46–47`、`test:53,130–143,174–179,245–259,291`。
- **成果物影響:** この runner の結果だけを根拠に、実 materializer 接続や admission 全体まで検証済みと記載すると、材料レポートの保証範囲が実際より広くなる。
- **根拠の種別:** 読解。
- **反例候補:** 通常の driver テストでは `_condition_records_for_genome` が autouse fixture により置換される。一方、診断テストは保存した実関数を直接呼ぶ。この構造では「実関数の診断処理を検査した」と「通常の prepare 経路が実関数へ正しく接続することを検査した」は同値でない。API 名を残して呼出しを無効化しても、`test:140–143` の文字列 assertion 自体は成立する。
- **限定:** その追加変異がファイル内の全テストを生存するとは主張しない。今回6変異には実関数／実 helper への検出経路がある。

**B3：masking の記述は、読解と実測、および存在と網羅性を分ける必要がある。**

- **位置:** `brief:30–40`、`orchestrator/tests/test_s8b_oracle_manifest.py:88–89,1081–1096`、`orchestrator/tests/test_s8b_oracle_report.py:200–202,251–264`、`orchestrator/tests/test_s8b_oracle_driver.py:2650–2652,2687–2698`。
- **成果物影響:** 静的な依存関係を実測済みの失敗 node 集合として台帳に記録すると、変異の帰属根拠が不正確になる。
- **根拠の種別:** 読解。
- **確認できたこと:** manifest の固定 literal と、兄弟テストの動的 hash 構築箇所は実在する。
- **反例になり得る経路:** 動的 hash の自己整合性は、import／collection の失敗や、同じ変異に対する別の挙動 assertion の失敗を排除しない。構文を壊す変異なら hash 検査へ到達する前に停止し得る。「任意の変異が必ず同じ hash 理由で赤」は強すぎる。
- **補足:** brief の逐語は「masking 層が 1 つ実在する」であり、「それだけ」と明記してはいない。これを唯一性の証明として引用すべきではない。今回の literal 検索も、別形式の masking 不在を証明しない。親の baseline 実行報告自体を虚偽と判断する根拠はない。

**P3 / P4 への判断:** `brief:50–52` の P3 は real 所見に対する修正経路を明記しており、それ自体は修正拒否ではない。「差分ゼロ」を理由に B1 の記録上の問題まで refuted にするなら不適切である。P4 に従って着地実装を検査したが、実装の受理集合拡大という must-fix は確認できなかった。

## 変異の帰属への所見

以下の表もすべて**読解による予測**であり、失敗 node の実測ではない。

| 変異 | 実際の位置・反例 | 帰属の評価／成果物影響 |
|---|---|---|
| **M1** | `driver:341`、`test:189–197,209–232,259`。ループを空にすると detail 行と helper 呼出しが消える。 | 診断欠落と割込み注入点の消失を同時に検出する。拒否自体は残る。全失敗を同じ「正しさ kill」と集計できない。 |
| **M2** | `driver:341–343`、`test:184–197,224–230`。non-green を1件にすると2行目と2回目の helper 呼出しが消える。 | 複数診断の保持に帰属する。fixture は両 arm が同じ `compiler-failed`、同じ detail なので、arm 間で detail を取り違える欠陥はこの fixture では識別できない。 |
| **M3** | `driver:352–353`、`test:209–228`。捕捉を無効化すると注入した `RuntimeError` が外へ出る。 | 外側の例外境界には直接帰属する。helper 自体を差し替えるため内側捕捉に mask されない。ただし実証対象は拒否型・理由の保持であり、正常 return や受理への転倒ではない。 |
| **M5** | `driver:291`、`test:294–295`。tail を空にすると末尾 sentinel が消える。 | 末尾保持への有効な診断 pin。omitted は残存量から再計算されるため、omitted assertion が成立しても末尾保持の証拠にはならない。 |
| **M6** | `driver:290`、`test:292–293`。head を空にすると先頭 sentinel が消える。 | 先頭保持への有効な診断 pin。M5 と同様、admission や拒否経路の検出ではない。 |
| **M7** | `driver:283`、`test:296–307`。digest 表示を削除すると sha256 assertion に加え marker 正規表現が失敗する。 | omitted node は算術比較 `:303–305` より前の `:301` で止まる。したがって「省略数の誤りも検出した」とは数えられない。4 node は4つの独立した性質の証明ではない。 |

**恒真性・過剰決定についての追加所見**

- **位置:** `test:263–288`、`gate:1018,1035,1057–1072`。  
  **根拠:** 読解。`_diagnostic_record()` は `_arm_record()` を直接使うため、`:288` の exact type assertion は factory の構造からほぼ自明である。発行 capability を持つ実 evaluator record である保証にはならない。  
  **反例／成果物影響:** 未発行 record でも helper 検査へ進めるため、このテストを admission 統合検査として材料レポートに数えると保証範囲を誤る。helper 単体検査としては問題ない。

- **位置:** `test:184–188,200–230`。  
  **根拠:** 読解。absent compiler が両 arm を同時に red にするため、単一 arm の正しさゲートを試す fixture としては過剰決定である。  
  **反例／成果物影響:** 一方の arm の拒否を無効化しても他方が拒否を維持し得る。複数 detail 保持の fixture としては適切だが、各 arm の独立した fail-closed 証明には使えない。

- **位置:** `test:153–155,355–361`。  
  **根拠:** 読解。green bytes の比較相手は同じ実行で admission 時に観測した record である。  
  **反例／成果物影響:** 発行段階で bytes が変わっても、その変更後の record を無改変で返せば比較は成立する。「返却時に改変しない」は検査できるが、「着地前後で green bytes 不変」の独立 golden にはならない。

M2 の候補選別後に再び non-green を確認する条件は候補集合から含意される。ただし、2件の診断を要求する assertion まで恒真になるわけではない。今回の head・tail・digest assertion に、対象変異で発火しない恒真検査は見つからなかった。

## kill か diagnostic sensitivity pin か

`docs/dev-wave/mutation.md:18–20` の逐語：

> kill は受理集合か fail-closed 挙動が期待方向へ変わったときだけ数え、診断文字列だけの赤を kill に  
> しない。fixture が単一理由か確認し、過剰決定なら単一理由へ差し替えるか、冗長 gate と明記して  
> 単独変異の証拠から外す。

同 `:61–63` の逐語：

> 受理集合を変えず構造化シグナルだけを pin する変異は kill でなく diagnostic sensitivity pin へ  
> 別枠記録する。テスト強化だけの wave は新テストと変更前 HEAD 版の双方へ変異を走らせ、新テスト  
> だけが検出する差分を示す。

私の意見は次のとおり。親の最終裁定は代行しない。

- **M2 / M5 / M6 / M7:** diagnostic sensitivity pin に分類することに賛成。拒否が受理へ変わらず、主たる観測差は診断の内容である。
- **M1:** 診断保持の失敗と割込み伝播の失敗を分離して記録すべき。helper を呼ばないため注入した割込みが発生しなくなることは、red variant の受理を示さない。
- **M3:** 通常の診断文字列だけの変更より強く、拒否例外の型を守る検査である。ただし、今回の注入は cause/context のない `RuntimeError` で、`driver:1020–1031,1324–1327,1412–1415` を読む限り、変異後も retry に入らず CLI は `EXIT_REFUSED` に至る。したがって、これを correctness kill と数えるには「fail-closed 挙動」に拒否型の保持を含める根拠を親が明示する必要がある。現状のテストだけから fail-open 検出と呼ぶことには反対する。

## nit

- **`driver:274–276,1414`：短文の surrogate。** 読解。`detail="\udcff"` は byte 数判定では escape されるが、返却値には surrogate が残る。strict UTF-8 の出力先なら最終 print が失敗し、通常の拒否 rc を置換し得る。ただし通常の stderr 設定での発生は確認しておらず、今回の本番到達例・成果物影響を確定できないため must-fix にしない。
- **`test:345–361`：green 時に helper を呼ばないことの直接検査ではない。** 読解。副作用なく helper を呼んで戻り値を捨てても record 同一性と bytes 比較は成立する。現行実装は実際に呼ばないため、これは検査の射程の注記である。
- **`brief:50–51`：差分ゼロ方針そのものには欠陥を認めない。** real 所見を修正する例外が明記されている。

## scope 外の観察

兄弟 driver への横展開、condition gate の unestablished 受理契約変更、仮想入力向けの新規防壁追加は提案しない。

## 読めなかった射影 file

なし。

## 総括

静的検査では、今回の実装が通常の発行経路で受理集合を広げる反例は確認できなかった。主な指摘は**証拠の分類と保証範囲**であり、全6変異のテスト失敗を一括して正しさ防壁の kill と数えることには反対する。

実装 must-fix は未確認。親には、診断 pin・例外境界の検査・契約上の kill を分け、masking に関する読解を実測結果と区別して裁定することを推奨する。