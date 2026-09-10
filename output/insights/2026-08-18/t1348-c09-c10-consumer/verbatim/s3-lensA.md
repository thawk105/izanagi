## 総括

必読の親 brief と段 2 plan は全文読了。静的 read-only 検査の結論は、現プランはそのまま採用不可です。

`cells=[]` の恒真経路は実在し、提案の先行拒否でその経路自体は塞げます。一方、C10 の受領証永続化、campaign root の権威、検証 CLI、build 正例 fixture に未解決の穴があります。

### 1. C10 aggregate digest が再検証不能 — 深刻度: blocker

再現:

- `s2-plan.md:99` は per-report receipt を返しますが、`s2-plan.md:103` 以降で永続化するのは 6 件の digest をまとめた `cross_binding_receipt_sha256` だけです。
- `s2-plan.md:120` の v3 検査は field の存在と SHA-256 形式だけです。
- 現行 `s8c_acceptance_receipt.py:843` の `verify_acceptance_receipt` に、C10 projection の再計算経路はありません。

v3 受領証の aggregate digest を別の 64 桁値に置換しても、受領証 verifier が preimage または C10 の 12 field を再計算しなければ形式上通ります。

影響: certified 選択は `False` のままですが、receipt と台帳が「C10 binding 済み」と主張する値を独立検証できません。

### 2. campaign root が自己参照で、古い成果物へ束縛できる — 深刻度: blocker

該当: `s2-plan.md:31`、`autonomous_trial_completeness.py:380`、`autonomous_trial_completeness.py:848`。

再現:

1. report の `cell["campaign_root"]` を、同じ campaign ID の古い campaign への symlink または別 run の root にする。
2. plan の `Path(...).resolve(strict=True)` がそれを実体へ解決する。
3. `assert_campaign_layer3_chain` は、その解決後の root から期待 `output_root` を作るため、期待値自体が攻撃対象 root になる。

build mode の既存 path 検査も `campaign_root.name == campaign_id` と親名 `campaigns` を見るだけで、現在の run root との束縛ではありません。

影響: report・WAL・bench・Layer3 は内部的に整合していても、古いまたは別 run の成果物を正式 proof chain として receipt に入れられます。

### 3. campaign root 付きの build failure cell は C09 を通過する — 深刻度: must-fix

該当: `autonomous_trial_completeness.py:2914`、`p3_autonomous_workload_trial.py:2057`。

再現:

- `do_build=True`
- `cells` に `campaign_root` 付きの exact failure decision を置く
- `reports/layer3_report.json` を欠落させる
- `require_admitted_campaign` が `ArtifactAdmissionError` になる状態にする

`assert_campaign_layer3_chain` は `autonomous_trial_completeness.py:2925` の `continue` で正常終了します。producer も `p3_autonomous_workload_trial.py:2165` でこの failure cell を実際に生成します。

campaignless fallback は plan の `campaign_root` 必須化で拒否できますが、root 付き failure cell は残ります。C10 がこの形を明示的に拒否しなければ fail-open です。

影響: C10 が欠落している場合、Layer3 のない build report が accepted list と receipt に入り、report と台帳に build proof があるように見えます。

### 4. 検証 CLI と lifecycle 台帳が C10 の consumer から外れている — 深刻度: must-fix

該当: `s2-plan.md:25`、`autonomous_trial_completeness.py:3008`、`autonomous_trial_completeness.py:3025`。

`verify_autonomous_trial_files` は completeness、execution digest、任意の C09 chain しか呼びません。C10 verifier の呼び出しはありません。さらに build でも fatal error かつ `cells=[]` なら `campaign_output_root` なしで通します。

producer 側も `p3_autonomous_workload_trial.py:2720` の `if do_build and cells` を維持します。

`registry` と `lifecycle` は現状 report/journal hash と run root を束縛するだけで、C10 projection は receipt top-level にしかありません。

影響: acceptance では拒否される raw response や build failure が、検証 CLI では成功 report になり、lifecycle 台帳には C10 未検査のまま残ります。

これは「acceptance receipt だけを正式 authority とするか、CLI と lifecycle も authority とするか」の裁定パッケージ候補です。

### 5. production acceptance の build 正例が repo にない — 深刻度: must-fix

該当: `orchestrator/tests/test_trial_registry.py:330`、`orchestrator/tests/test_trial_registry.py:360`、`orchestrator/tests/test_trial_registry.py:858`。

`test_trial_registry.py` の acceptance fixture は、`_base_start` と `_base_report` がともに `do_build=False` です。`_complete_report` もそこから継承し、6 件 acceptance の `test_p5_six_complete_terminal_reports_pass_acceptance` も no-build です。

実 build の Layer3 fixture は `test_p3_autonomous_workload_trial.py:2364` にありますが、unregistered exploratory run、3 workload、producer 側テストであり、6 件の `assert_trial_registry_acceptance` ではありません。

作るべき fixture:

- 6 trial 全件で run-start/report の `do_build=True`
- registered-effective launch admission
- 各 report に manifest と一致する 1 cell
- 実在する campaign.lock、WAL、loop state、Layer3 report
- role event の raw response、provider payload/envelope、proposal bytes
- supervisor harness と WAL bench record の一致
- acceptance を実際に通し、12 field と aggregate digest を検査

影響: 現状の acceptance テストは C09/C10 の build branch を一度も発火させず、no-build receipt の成功だけで実装を緑にできます。

### 6. P4 は `do_build` の自己申告を信頼しすぎる — 深刻度: must-fix

該当: `s2-plan.md:31`、`s2-plan.md:97`、`autonomous_trial_completeness.py:1753`、`p3_autonomous_workload_trial.py:3832`。

`do_build` は report と run-start の一致しか検査されず、manifest や launch admission に外部から固定された値ではありません。`--no-build` で no-build branch に入り、C09 と 12 個の C10 field を束縛せず受理できます。

これは現在の `certifying=False` により certified 選択を直接通す穴だとは refute できません。P4 は「no-build receipt を非 certifying のまま発行してよいか」という仕様裁定です。

影響: certified 選択は `False` のままですが、`AcceptanceSummary.trials` と receipt は6件受理を示し、reason を無視する consumer なら no-build report を成功扱いできます。

### 7. evaluator は dead code と未使用 literal を受理する — 深刻度: must-fix

該当: `s8c_preregistration_evidence.py:299`、`s8c_preregistration_evidence.py:312`、`s8c_preregistration_evidence.py:1645`、`s8c_preregistration_evidence.py:1680`。

`_called_names` は `ast.walk` で dead branch も拾い、C09/C10 は `_live_called_names` を使いません。既存の token-only fixture `test_s8c_preregistration_predicates.py:490` と `test_s8c_preregistration_predicates.py:506` は、実処理がなくても要求名と文字列だけで形状検査を通せます。

`if False:` 内の呼び出し、未使用の string literal、`pass` の wrapper でも evaluator は目標の `EVIDENCE_UNDEFINED` に到達します。

影響: certified 選択は変わらなくても、evaluator の条件 status だけが機械検査済みに変わり、実際の receipt・report・台帳が未束縛でも実装済みと報告されます。

### 8. no-build 変異テストは C09 を実際には検査しない可能性がある — 深刻度: nit

該当: `s2-plan.md:133`、`s2-plan.md:134`、`autonomous_trial_completeness.py:1775`。

report だけ `do_build=True` にすると、先に run-start/report の不一致で落ちます。両方を変更しなければ、C09 の `cells=[]` 拒否ではありません。

影響: receipt は作られないものの、テストが `run-envelope` の失敗を C09 の fail-closed と誤認し、C09 precheck を削除しても緑になる可能性があります。

### refute できなかった点

- `assert_campaign_layer3_chain` の `cells=[]` が内部 loop を空のまま戻るという主張は正しいです。`autonomous_trial_completeness.py:2874` が根拠です。`do_build=True and not cells` の先行拒否は、この経路には有効です。
- `campaign_id` と `campaign_root` がともに `None` の fallback は、plan の campaign root 必須化で受理前に拒否できます。
- C10 の意図された実装本文は、`s2-plan.md:54` と `s2-plan.md:63` に bytes 再読、hash 再計算、12 field の実値対応が明記されており、現時点で「薄い wrapper だ」とは断定できません。
- 呼び出し順は正しいです。`s2-plan.md:109`、現行 `trial_registry.py:2836` と `trial_registry.py:2843` の位置関係から、C09/C10 を `accepted.append` と receipt 作成より前に置けます。
- `certifying=True` の受領証経路は現行 parser `s8c_acceptance_receipt.py:335` で拒否され、plan も維持しています。
- P1 の「evaluator に SATISFIED 枝がない」というコード事実は正しいですが、それは runtime gate が実行された証明ではありません。

### 採用してよい部分

- C09/C10 を `accepted.append` と receipt issuance より前に置く順序。
- `do_build=True and cells=[]` の先行拒否。
- build mode の campaign root 欠落を fail-closed にすること。
- `read_and_verify_bytes` で実 bytes、hash、root 境界、symlink、path traversal を検査する設計。
- 12 field ごとに WAL、provider、proposal、Layer3、admission decision を実値で比較する方針。
- v3 receipt とし、v1/v2 の historical parser を保存する方針。
- `certifying=False` を反転させない不変条件。

採用前に、少なくとも「canonical campaign root の外部束縛」「C10 projection の再検証可能な永続化」「検証 CLI と lifecycle の authority 範囲」「6件の registered build 正例」「no-build の正式な意味」を裁定する必要があります。