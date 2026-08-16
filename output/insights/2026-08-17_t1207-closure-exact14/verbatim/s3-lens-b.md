~~~text
検査範囲: 必読の brief、s2-plan、D442、repo root を読了。全件検索と対象行の静的検査のみ実施し、pytest・build・親の実測は未実行。

編集面監査:
- `CONTRACT_LOADER_RELATIVE_PATHS`、blob key、scope constant の consumer を全件検索。production、ident、binding、codec、artifact、bench、env、layer3、S6/S8a、fixture は動的参照で、追加の未追随 consumer は見つからない。
- hard-code の exact 12 は T671、artifact fixture、S6/S8a の docstring、`test_artifact_admission.py:1077` に限定。freeze design の exact 12、S8b の exact 12/51、T080 の 12/51 は別契約で変更不要。
- 現行 verifier の加工後 hash pin は不在。Silo は `verifier.rglob("*.py")` と実ファイル hash を動的取得し、`e604...` は historical pin である。

B-01 / nit

主張: brief の M1 raw grep は現行 checkout の成果物確認には足りるが、任意形式の v2 lock 不存在を証明する測定ではない。

根拠:
`brief.md:44-48` は「`find output -name campaign.lock` = 32」「`grep -rlF 'campaign-lock/v2' --include=campaign.lock output/` = 0」と記録する。
`campaign_lock.py:209-223` は JSON decode 後に `schema_version`、v2 の exact key、canonical outer を検査する。
静的 inventory では exact `campaign.lock` が 32 本、圧縮ファイルが 0 本、別名の campaign lock が 0 本、exact lock 内の `schema_version` が 0 件だった。代表例も `output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e/campaign.lock:1` は v1 identity object である。

反例または検算: 将来 `campaign.lock.json`、`campaign.lock.gz`、別 layout を artifact loader が読むようになっても M1 の command は数えない。なお `schema_version` の別表記そのものは現行 codec の exact key と canonical 検査で v2 として拒否される。

成果物影響: 現行32成果物の certified 選択・report・受理集合は変わらないが、測定の一般化範囲を「この checkout の physical `output/**/campaign.lock`」に限定して記録すべきである。

B-02 / should-fix

主張: 新2 pathを既存の全 path parameterized testへ追加すると、closure の将来サイズに対して fixture 作成と Git hash 計算が O(N^2) で増える。

根拠:
`test_t671_source_binding.py:69-93` は各 test case で全 expected path を作成し、各 pathに `git cat-file` と hash計算を行う。
同じ helperを `:135-152`、`:183-194`、`:211-226`、`:312-326` の N 件 parameterized node が繰り返し呼ぶ。
`test_artifact_admission.py:326-345` も全 closure を作り、`:1127-1140` は verifier pathごとにそれを再作成する。
`s2-plan.md:189-196` は既存12 parameterを14へ増やし、drift testを4から6へ増やす。

反例または検算: closureをN=50へ拡張すると、N個のcaseがそれぞれN個の file、commit、blob hashを作る。F357の焦点走偽赤だけを記録しても、この比例費用は記録されない。

成果物影響: certified valueや受理集合は変わらないが、全 waveの受入時間、commit前の偽赤待ち時間、runner資源がclosure履歴に比例して増える。共有fixtureまたは新2 faceだけを個別検査する構成を裁定すべきである。

B-03 / should-fix

主張: phase3台帳のT819再訪条件がこのwaveで発火するのに、s2-planの文書編集面に入っていない。

根拠:
`docs/phase3.md:1215` はT819の再訪条件を「同一ファイルを触る wave への相乗り、または実害 1 件」とする。
`campaign_lock.py:27-42` が今回の対象であり、s2-planは `:10-13` と `:33-37` で worklog、decision、F357 fragmentだけを列挙する。

反例または検算: tupleを実際には編集せずwaveを中止するなら発火しないが、exact14実装を着地させる計画では同一ファイル編集が確定している。

成果物影響: certified選択やlock値は変わらないが、phase3の再訪台帳が「価値小」のまま残り、runner作法を再評価した参照と次タスク選定が古いままになる。

B-04 / should-fix

主張: P1のbrace shorthandは意味は正しいが、成果物に載るexcluded scopeの逐語としては実パスを列挙すべきである。

根拠:
`brief.md:134-136` と `s2-plan.md:23` は ``orchestrator/verifier/{__main__,cli}.py`` と wrapper の併記を提案する。
現行の `artifact_admission.py:69-72` は ``{__init__,__main__,cli,report}.py`` を束縛しないと記録し、`:114-118` でその文字列を exact compare する。
`docs/decisions.md:18535-18539` は wrapper、dispatch、reportの境界を別々に説明している。

反例または検算: `__init__.py` と `report.py` をtupleへ追加したのに、scope文字列が旧値または解釈不能な一つのbrace pathのままなら、E1 reportは実際の束縛範囲を誤記する。

成果物影響: E1の `identity_scope` / `excluded_scope` とoracle report・台帳の参照が不正確になる。受理集合そのものは変わらないが、certified証拠の境界説明が偽になる。

提案する逐語:
`verifier package のうち orchestrator/verifier/__main__.py と orchestrator/verifier/cli.py、および package 外の orchestrator/verify.py の implementation bytes は束縛しない`

B-05 / should-fix

主張: `test_exact_fourteen_clean_closure_capture_and_live_verify` と改名後のtuple test単体は、blob照合が壊れていても緑になるため、enforcementの発火保証として扱えない。

根拠:
`s2-plan.md:123` のclean nodeは未変更repoで capture、live verify、key集合、tuple順だけを確認する。
`test_t671_source_binding.py:123-132` はtuple一致とobject identityだけをassertする。
一方、実効 gateは `contract_loader_binding.py:324-337` の disk/blob比較と `:340-359` の commit blob/disk比較である。

反例または検算: captureがHEAD blobではなく現在diskをhashし、live verifyも現在diskを再hashする実装に壊れていても、clean nodeとtuple nodeは緑になる。独立した `git cat-file` digest assertと、計画済みの実disk mutation paired nodeが必要である。

成果物影響: 受理集合は直ちには変わらないが、mutation台帳が「検出済み」と誤認し、certified gateの実効性報告を過大評価する。

P1-P5判定:

- P1: 条件付き賛成。package内の `__main__.py`、`cli.py` と package外の wrapperを明示し、`__init__.py`、`report.py`をidentity側へ置く点は正しい。B-04の逐語修正が必要。
- P2: このwave限定で賛成。`artifact_admission.py:63` と `D442:18510-18513` の通り domain据置きは既存goldenへの影響を抑えるが、cross-version認証を意味しない。
- P3: 賛成。`campaign_lock.py:127-136` はwireをsort_keysで正規化し、`artifact_admission.py:742-745` はtuple順をepoch preimageへ使うため、旧12をprefixとして末尾appendする順序が必要。
- P4: 賛成。D442は `D442:18505-18516` の歴史記録として残し、新decisionでdispatch/reportの境界だけをsupersedeする。
- P5: briefの「全てT671」は不賛成。s2-planの `:200-206` の限定形、すなわちsource mutationはT671、旧exact12 wire拒否はcodec、epoch/scope/driftはartifact admissionへ置く構成を採用すべきである。

受理集合の検算（所見なし）:

`campaign_lock.py:171-184` は blob key集合を現在tupleとの完全一致で検査し、全tupleをchecked mapへ入れる。planned append後はexact14 mapを受理し、exact12 mapは集合不一致で拒否するため、subset化ではない。
`campaign_lock.py:209-223` はv2 marker、top-level exact key、canonical outerを検査し、`:232-239` のschemaなしv1経路は不変である。
現行outputの32 lockはv1でv2が0本なので、既存成果物の破壊は静的には確認されない。pytestは未実行。
循環importも所見なし。`campaign_lock.py:4-12` はcampaign model、identity、WALに依存せず、`pipeline.py:31`からverifierへ一方向に進む。`verifier/__init__.py:16-20` は内部verifierだけをimportする。
F358の共通driftは、s2-plan `:163-175` が単一nodeとfailed-node完全一致を要求しており、計画上は切り分けられている。

X-1208 / should-fix（scope外、裁定パッケージ候補）

主張: 旧12-path由来のE1を新14-path certified選択から排除するcross-version機構は、今回のexact14変更だけでは確定しない。

根拠:
`docs/decisions.md:18543-18545` はoracleがscope非空だけを見て、judgeが `state=E1` と `certified_eligible=true` だけを見ると記録する。
`brief.md:33` は[T-1208]を未裁定とし、`s2-plan.md:202-203` も未解決のまま継承する。

反例または検算: 旧仕様で生成されたE1 reportまたはselection recordが、current campaign.lockのdecodeを経ずにoracle/judgeへ渡る場合、同じE1文字列だけで新14-path成果物と同列に扱われる。

成果物影響: 将来のcertified選択集合に旧closure由来のrecordが混入し、report・台帳のepoch参照が世代を識別できない。実装せず、別裁定へ分離する。

X-1209 / should-fix（scope外、裁定パッケージ候補）

主張: T126 qualificationのcode identityは新closureへ追随せず、dsg/model/parseやdispatch/reportの変更を別のidentityとして検出しない。

根拠:
`docs/decisions.md:18546-18547` は「T126 qualificationのcode identityはcore.pyしか含まない」と明記する。

反例または検算: `dsg.py`、`model.py`、`parse.py`を変更してもT126のidentity値が不変なら、qualification reportは現行sourceと異なるbasisを参照し続ける。

成果物影響: certified値そのものより、qualification reportと台帳のsource identity参照が古くなる。実装せず、T126専用の裁定へ分離する。

X-DOMAIN / should-fix（scope外、裁定パッケージ候補）

主張: `campaign-verifier-epoch/v1`を維持するP2は今回の費用制約には妥当だが、12-path grammarと14-path grammarを同じdomain名で表す曖昧さを残す。

根拠:
`artifact_admission.py:63` はdomainを固定し、`D442:18510-18513` はdomain据置きの理由を既存goldenへの波及とする。
`D442:18562-18564` はdomain昇格とoracle exact scope gateを本wave外としている。

反例または検算: 外部consumerが `/v1` をgrammarの固定版と解釈し、旧E1と新E1を同じnamespaceで比較または選択する。

成果物影響: 据置きならE1 prefixと既存goldenは不変だが、cross-versionの受理集合がnamespace上分離されない。`/v2`昇格はlayer3、S1、S8bのgoldenとreport参照を変えるため、実装せず裁定へ返す。
~~~

## 総括

最も危険なのは、clean/tuple testを実効性の証拠と誤認し、blob照合の壊れた実装を見逃すことです。  
親はT819再訪、将来のO(N^2)テスト費用、P1の明示的scope文言を裁定してください。  
[T-1208]、[T-1209]、hash domain昇格は本waveへ混ぜず、別裁定に分離すべきです。