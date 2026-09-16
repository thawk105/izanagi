**[所見 1] A1 は D780 に適合するが、「保証対象が同じだから主張は強くならない」という説明は不十分**

**判定の根拠 (file:line)**  
`tools/check_trace0_preprocess_identity.py:3` の「検査する」は処理の説明であり、段 2 の「証明する」は保証の主張である。対象集合の不変だけでは、主張の強さの不変までは導けない。

ただし「D297 の保証」を留保込みで読む限り、D780 が直接指定した文言であり、誤った保証の追加とは断定しない。問題は、A1 が保証名を具体化する一方、`verbatim/d297.md:22–23` の compiler 依存・admission toolchain 非同一性を具体化していない点である。`orchestrator/campaign/source_digest.py:1295–1301` にも実 build の全 define 不在を保証しない限界が残る。

**この所見が誤りである場合の条件**  
A1 の読者が必ず D297 全文を参照し、その留保も含めて「保証」を読むことが担保されている場合。

**推奨対応 (scope 内)**  
A1 の既存文と D780 の逐語文を維持し、次を続ける。

> ここでいう保証は、使用した compiler と選定した macro context に依存する。admission toolchain と同一であるとは主張しない。この検査だけで計測ビルドからの trace 完全除去を証明したと解釈してはならない。

D774 の実装や拒否条件を変える必要はない。

**[所見 2] A6 の英訳自体に強弱のずれは認めない**

**判定の根拠 (file:line)**  
`tools/pegasus/mocc_trace_pilot.sh:1742` に追加予定の英文では、`proves` の目的語は D297 guarantee に限定され、`one necessary condition` は「必要条件の一つ」に対応する。末尾の `it does not prove that removal` も、`verbatim/d780.md:5–6` の完全除去を証明したと読ませない要求に合う。

既存の `hard gate` は失敗時の実行禁止であり、成功時の十分性を述べていない。したがって親の「A6 だけが実際に弱まる」という評価も成立しない。

**この所見が誤りである場合の条件**  
`D297 guarantee` を留保抜きの無条件保証として別途定義している場合。

**推奨対応 (scope 内)**  
英訳の訂正は必須ではない。A1 と同じ留保を入口にも明記するなら、追加文は次とする。

> `# The D297 guarantee is compiler-dependent and does not assert identity with the admission toolchain.`

**[所見 3] 親の pin 実測は不完全。checker に加えて pilot の source SHA と派生成果物が変わる**

**判定の根拠 (file:line)**  
`s1/anchors.md:41–48` の一覧では、次の束縛が落ちている。

| 束縛 | 根拠・波及 |
|---|---|
| checker 実 bytes | pilot `:1751` で SHA 採取、`:2673` で再読込・照合、`:2915` で receipt に格納 |
| pilot 実 bytes | submitter `tools/pegasus/submit_mocc_trace.sh:319` で SHA 採取、`:461,548` で pre-submit／submit receipt に転記 |
| submit 時と実行時の pilot 一致 | pilot `:999,1040`。編集前の submit receipt と編集後の script を組み合わせると拒否対象 |
| job-result と派生 SHA | pilot `:3370,3372` に receipt SHA と script SHA。receipt 変更は sidecar・job-result の bytes／digest に波及 |
| pair の同一 script 制約 | `orchestrator/campaign/mocc_trace_pair.py:915`。旧新 pilot の leg 混在は同一性検査に触れる |
| 過去の checker pin | `output/insights/2026-08-26_mocc-trace-pair-receipt.json:90,123` に現 checker の SHA `248b2c2e…fcf93` が記録されている |

現在の checker SHA を文字列として逆引きしても、この過去 receipt が見つかった。保証名と schema だけが pin ではない。

また、pilot `:3358–3364` は **report binding のキー集合と値型の検査**であり、checker source SHA の四項目照合ではない。report SHA と source SHA は別の束縛である。

**この所見が誤りである場合の条件**  
親の「凍結 pin」が「今回更新を要する固定 literal」だけを指し、動的束縛・過去成果物を明示的に除外している場合。ただし一覧の射程はそのように訂正する必要がある。

**推奨対応 (scope 内)**  
上表を影響記録へ追加する。過去 receipt は変更しない。将来の新しい実行では新 bytes に対応する束縛を生成する。今回の文言修正のために再計測する必要はない。

**[所見 4] AST・文字列アンカー・inventory の pin は存在するが、予定編集で壊れる固定行番号 pin は確認できなかった**

**判定の根拠 (file:line)**

- `orchestrator/tests/test_mocc_trace_job_contract.py:4909` は checker の実 AST を読み、`check()` の返却辞書を検査する。
- 同 `:2969` は pilot の文字列マーカーから finalization を抽出し、同 `:4191` はマーカー出現数を固定する。行番号ではない。
- 同 `:2993,3329,3339` は helper 経由で実 checker path を解決し、その時点の bytes から SHA を計算する。
- `orchestrator/tests/test_hooks.py:4392` の inventory は path 集合・拡張子・実行属性・先頭 shebang を見る。全文 SHA の pin ではない。
- `output/insights/2026-08-25_t1641-mutation-spec-final.json:27` などの過去変異仕様は、対象 path と置換前 literal を保持する。

指定文案はこれらの実行文・抽出マーカーを変えない。検索した freeze／preregistration、hooks、`.claude`、`.codex` では対象 path または現 SHA の追加一致を確認しなかった。`.github` は存在しなかった。これは未知の派生 digest を含む全 pin の不在証明ではない。

**この所見が誤りである場合の条件**  
未確認の consumer が行位置・全文 digest・docstring を契約として使っている場合。

**推奨対応 (scope 内)**  
「pin なし」ではなく、固定値・動的計算・構造アンカー・歴史記録を区別して報告する。過去変異台帳や行番号の遡及更新は不要。

**[所見 5] 非緩和確認は恒真ではない。ただし文言の妥当性を検査する仕組みではない**

**判定の根拠 (file:line)**  
`s2/plan.md:64–78` の手順は、固定基準と承認済み置換文から期待 bytes を作るなら有効である。例えば `GUARANTEE` の変更、拒否分岐の削除、heredoc 内の変更は全 bytes 比較で検出される。

一方、module docstring を除く `ast.dump(include_attributes=False)` は次を見落とす。

- 今回の保証文を「完全除去を証明する」に変える誤り。
- コメント、空白、同値の文字列表記。
- `lineno`・`col_offset`・終了位置、そこから生じる traceback／ソース位置の変化。
- module の `__doc__` の変化、外部 consumer によるソース読取りへの影響。

checker の JSON は `tools/check_trace0_preprocess_identity.py:703,748`、CLI 説明は `:724` で生成され、ここには module docstring 参照がない。この静的確認を伴うことで、通常の同一入力・依存条件での出力不変を支えられる。AST 一致だけからの無条件な観測同値は言えない。

**この所見が誤りである場合の条件**  
期待する新文を編集後ファイルから抽出して比較する実装なら、文言検査部分は自己確認となる。逆に承認文を変更したのに期待 literal を更新しなければ、正当な修正も赤になる。

**推奨対応 (scope 内)**  
承認済み文案を独立した期待値に固定し、全 bytes 比較を主検査、AST 比較を補助検査とする。意味の確認は D297・D780 との対照で別に行う。

**[所見 6] 四つの焦点 test file に具体的な追加漏れは確認できないが、検索一発では閉包の根拠にならない**

**判定の根拠 (file:line)**  
間接経路を引き直した結果、重要な二段経路は既存の四ファイル内に収まる。

- binding test → `_run_mocc_trace_finalization`（job contract `:3136`）→ `_mocc_trace_finalization_fragment`（`:2969`）→ pilot。
- 同 helper → `_production_selected_tool_path`（`:2993,3329`）→ 実 checker bytes の SHA（`:3339`）。
- hooks inventory（`test_hooks.py:4392`）→ `os.walk`／先頭 bytes 読取り → pilot。

別ファイルの `test_real_repo_serialization.py:2930` は `test_hooks` を import するが、使用先は `GW.decide` による別の編集対象の検査であり、今回の文言 consumer ではない。

また、`test_mocc_trace_pair.py:400–406` の preprocess checker SHA は合成値であり、同 `:123–150` の `_checker_pin` 系は **`mocc_trace_pair.py` 自身**の束縛である。名称だけで今回の checker pin と数えてはいけない。

**この所見が誤りである場合の条件**  
今回確認した経路以外に、対象 bytes／docstring を動的に選択して読む helper がある場合。

**推奨対応 (scope 内)**  
四ファイルを維持し、上記の間接経路を根拠へ追加する。焦点走を全 consumer の完全証明とは呼ばない。親が予定した受入全走は別途実施する。

**[所見 7] 実行ロジックの変異 matrix を今回新設する意味はない**

**判定の根拠 (file:line)**  
変更対象は checker `:3` と pilot `:1742` の説明だけであり、新しい受理・拒否分岐はない。既存の checker test `:219` は report の再現性などを検査するが、今回の保証文の意味は検査しない。

文言を「必要条件の一つ」から「十分条件」へ変えても、AST 比較と既存動作 test は通り得る。承認文との bytes 比較なら殺せるが、それは文案への一致確認であり、正しさゲートの変異耐性を新たに測ったことにはならない。

**この所見が誤りである場合の条件**  
後段で実行文・判定条件・report schema まで変更する場合。その場合は本 wave の前提自体が崩れる。

**推奨対応 (scope 内)**  
新しい変異 matrix は不要。承認文との一致、実行部分の不変、文言の意味の対照を記録する。既存ロジックへの変異投入は scope 外。

## 総括

実装修正を止める固定 pin の破損は確認しなかった。ただし、**親の pin 一覧には実際の漏れがあり、段 2 の「対象不変だから主張も非強化」という説明も補強が必要**である。

A1 に D297 の compiler 留保を添え、pilot SHA を含む束縛の波及を明記すれば、二ファイルの文言修正という scope を維持できる。ファイル変更・commit・テスト実行は行っていない。