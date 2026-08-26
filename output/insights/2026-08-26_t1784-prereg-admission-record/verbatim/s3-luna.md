## 総括

最も危険なのは、admission record と receipt があっても、それらを B-4 の proposal、次 synthesis、最終台帳へ因果的に束縛する層が無いことである。現 plan の gate は critic query を止めるが、段 4 実走そのものを支配しない。  
併走 wave の receipt 必須化を足しても、receipt を未使用の通行証として渡すだけで任意 proposal を走らせられる。  
さらに test-only receipt、複数 record の選択、旧 §5 blob の再利用が合流後の抜け道になる。  
`/v3` 昇格は必須ではなく、併走 wave との三面衝突を増やす。v2 receipt と record の独立再検証で同じ gate を構成できる。  
親の現在値 3 件は実測どおりだが、projection 値と entry 数は両 wave の実装直後に必ず変わる。

## 所見

### F1 — production factory は B-4 実走の支配点ではない

- **自己判定: real。** repository 内の production caller は `p3_b4_closed_critic.py:1456` とテストだけで、3 driver からの import/call は 0 件だった。CLI 自身も「stage-4 driver を wire しない」と明記する (`p3_b4_closed_critic.py:1443-1448`)。一方、実 build/verify/bench は admission 無しの `run_one_iteration()` と `drive_iteration()` から起動できる (`p3_s4_loop.py:1044-1160,1213-1285`)。
- **具体的な破り方または不成立の筋道:** `p3_s4_loop --reflux on|off --run-iteration`、または Python API の `run_one_iteration()` を直接使えば、record も closed critic も通らず certified campaign を生成できる。現状はそれを後から B-4 と呼ばないという文書規律しかない。併走 wave が `drive_iteration()` だけを閉じても、fixture main は `run_one_iteration()` を直接呼ぶ (`p3_s4_loop.py:1398-1401`)。
- **成果物影響:** record 無しの variant が通常の certified 集合へ入り、材料レポートや台帳が後から B-4 標本として参照すると、B-4 受理集合が非登録 run を含む。
- **修正案:** B-4 専用の支配点を `drive_b4_block(*, launch_admission: B4LaunchAdmission, precursor_receipt: B4ClosedCriticReceipt, proposal: B4BoundProposal) -> B4BlockReceipt` として新設し、B-4 report/ledger は `B4BlockReceipt` のみ受理する。**通る正例:** committed record R、certified receipt、R と receipt に束縛された proposal を渡した 1 block だけが B-4 台帳へ入る。

### F2 — 併走 wave の receipt gate は順序が循環し、proposal への因果束縛も無い

- **自己判定: real。** driver は iteration を増やして実走した後に digest を生成する (`p3_s4_loop.py:1255-1275`)。closed controller はその保存済み state/WAL から digest を再構成して receipt を作る (`p3_b4_closed_critic.py:695-704`)。したがって iteration N の terminal receipt は driver N の開始前には存在しない。proposal schema が運ぶ critic 由来値は束縛されていない `prior_critic_reverse` だけである (`p3_s4_loop.py:1178-1210`)。
- **具体的な破り方または不成立の筋道:** receipt N を driver N の必須入力にすれば循環する。検査を driver N の末尾へ置けば build/bench は既に終了している。receipt N を次の driver N+1 に渡す形なら、receipt の decision を無視して任意の proposal を供給しても、campaign/arm/iteration/digest 検査だけは通る。
- **成果物影響:** 任意 proposal が次 synthesis と certified 選択を変えられ、台帳には正しい record/receipt が並ぶのに、B-4 効果量は treatment を消費していない標本から計算される。
- **修正案:** `B4NextSynthesisContext` に `precursor_iteration`、terminal receipt hash、decision/envelope hash、proposal canonical hash を持たせ、driver 入口で `receipt.iteration == state.iteration`、実走側を `state.iteration + 1` に固定する。**通る正例:** precursor iteration 4 の on receipt から生成・hash 束縛した proposal だけが iteration 5 を起動する。

### F3 — test-only factory が合流後の admission bypass になる

- **自己判定: real。** test-only factory は admission 無しのまま残す計画である (`s2-plan.md:21,143,147`)。現 reader は `certified` と `test-only` の双方を受理し (`p3_b4_closed_critic.py:1139-1144`)、pair gate も evidence class の一致しか要求しない (`p3_b4_closed_critic.py:1402-1405`)。併走 brief の P3 は campaign/arm/iteration/digest を列挙するが、`evidence_class == certified` を列挙していない。
- **具体的な破り方または不成立の筋道:** `create_b4_closed_critic_pair_for_test()` で matching receipt を作り、併走 gate へ渡す。fake runner でも実 Claude でも evidence class は test-only で、admission fields は `None` だが、reader と pair gate は通る。
- **成果物影響:** admission record 無しの critic decision が次 synthesis を変え、test-only 標本が B-4 certified 受理集合と台帳へ昇格する。
- **修正案:** driver 向けに `read_certified_b4_terminal_receipt(path) -> B4ClosedCriticReceipt` を公開し、`evidence_class != "certified"` と admission 不在を無条件拒否する。**通る正例:** production factory の certified receipt は通り、同じ bytes を test-only とした receipt は driver 入口で止まる。

### F4 — receipt `/v3` 昇格の必要性は refuted、衝突リスクは real

- **自己判定: schema 昇格の必要性は refuted、合流被害は real。** v2 receipt は既に実測 3 値を持つ (`p3_b4_closed_critic.py:195-199`)。projection は controller module 自身を含み (`p3_b4_closed_critic.py:501-537`)、reader は現在の closure と receipt を再照合する (`p3_b4_closed_critic.py:1315-1316`)。admission 実装後の certified v2 receipt は、必須 factory gate を通ったことを code closure から判定できる。
- **具体的な破り方または不成立の筋道:** `/v3` にすると、併走 wave の v2 exact-key fixture と reader が全滅する。後方互換として v2 も受理すると、admission 実装前 receipt の受理枝を残す。両 wave が別々の追加 field を同じ `/v3` 名で実装すると、同じ version に二つの exact schema が存在する。
- **成果物影響:** fail-closed 合流なら B-4 受理集合が空になり、互換枝を足すと旧 receipt が受理され、台帳の admission 参照が欠落する。
- **修正案:** receipt は v2 のまま、`verify_b4_admitted_receipt(*, admission_record_path, terminal_receipt_path, expected_arm, expected_campaign_id, expected_precursor_iteration) -> VerifiedB4Admission` を追加する。record の期待 3 値と v2 receipt の実測 3 値を比較し、record hash/commit は後段の `B4BlockReceipt` に保存する。**通る正例:** current certified v2 receipt と committed R の 3 値が一致すれば通る。

### F5 — 親の現在値は正しいが、実走手順への一般化は成立しない

- **自己判定: 現在値は real、一般化は部分 refuted。** 静的再計算結果は次のとおりだった。

  ```text
  projection_sha256 df37ca0d1e98b4fb2346db751fed0ddf7fc169dd9b863a7ce9ff3b1d87efff46
  entry_count 10
  effective_prompt_sha256 1b5006f6cde3c05d8b9b935ff590632074ed87ac876a264d7953e07e0435f0cf
  frontmatter_model opus
  model_is_runtime_slug False
  ```

  prompt は body に固定 separator/header と contract を加えた bytes なので LLM 無しで計算できる (`claude_projected_provider.py:162-169`)。model は alias `opus` しか repo に無く、exact snapshot は応答の `modelUsage` 後に決まる (`claude_projected_provider.py:317-353`)。また runtime 側は prefix しか検査せず、plan の「閉じた ASCII slug」より値域が広い。

- **具体的な破り方または不成立の筋道:** admission 実装は validator entry を追加し、両 wave が `p3_b4_closed_critic.py`、併走 wave が `p3_s4_loop.py` を変更する。したがって `df37...` と entry 10 件は合流直後に必ず失効する。さらに誤った model を宣言すると、provider は critic query と envelope 保存を終えてから mismatch を検出する (`claude_projected_provider.py:292-353`)。実出力と実 slug を見て record を更新し再試行できる。
- **成果物影響:** post-output で model 欄を修正した再試行が通ると、台帳上は precommitted でも critic 出力観測後に設定を選んだ B-4 標本になる。
- **修正案:** exact model snapshot を payload 送信前に transport が pin または attest できることを launch 条件にし、応答後 mismatch は record 再発行ではなく experiment abort とする。**通る正例:** launch attestation が `claude-opus-X` を返し、その同値を含む R を commit した後だけ最初の critic payload を送る。

### F6 — record の複数化と旧 §5 blob の再利用を拒否できない

- **自己判定: real。** plan は admission record path を任意 CLI 引数にし (`s2-plan.md:20,23`)、historical `content_commit` が record 検証 HEAD の祖先であることだけを要求する (`s2-plan.md:60-72`)。検証 HEAD にある現在の事前登録文書が `content_commit` の blob と同一であることや、active record が一つだけであることは要求しない。
- **具体的な破り方または不成立の筋道:** §5 の異なる版 D1、D2 と record R1、R2 を別 path で順次 commit する。closure code が同じなら最新 HEAD で両 record が有効であり、実走時に都合のよい母集合、outcome 定義、model を持つ方を選べる。現在の文書を D2 に変えても、R1 は historical D1 blob を検証して通る。
- **成果物影響:** record 選択によって primary outcome、母集合、期待 model と B-4 受理集合が変わり、材料レポートと台帳が現在の発効版とは異なる版を黙って参照する。
- **修正案:** active record を固定 repository path 一つに限定し、launch manifest がその path、record hash、prereg commit を一回だけ束縛する。旧版を許す場合も report は launch manifest が指す版以外を拒否する。**通る正例:** HEAD の canonical active record R と launch manifest L が同じ prereg D を指す場合だけ通り、別 path の R1 は拒否される。

### F7 — 「毎実走ごと作り直し」は refuted だが、合流前作成は無効

- **自己判定: 毎回再作成が必要という一般化は refuted、closure 変更時の失効は real。** record 自身は closure 外なので、code、prompt、model、§5 が固定なら複数 block で再利用できる。無関係な main の前進だけでも必ず失効する、とは plan からは言えない。一方、closure entry の変更は正しく失効する。
- **具体的な破り方または不成立の筋道:** 併走 wave が現在値を §5 へ commit しても、両 wave の code merge によって projection が変わるため、その §5 と record は実走に使えない。model rollout は Git 変更無しでも mismatch を起こす。実走後に作り直して同じ実験を継続することは、単なる保守ではなく protocol amendment になる。
- **成果物影響:** fail-closed なら受理集合が空になり、摩擦回避で古い record を許すと台帳の projection 参照が実 code と食い違う。
- **修正案:** 順序を「両 wave 合流と closure freeze → projection/prompt 計算 → §5 commit → canonical record commit → launch seal → 全 block」に固定する。生成関数 `build_b4_admission_record(...) -> bytes` も用意する。**通る正例:** final tree から一度作った Rを、同じ model と closure の n block で再利用する。

## scope 外だが real な層

裁定パッケージ候補は次である。

- **B-4 block 専用 orchestrator と B-4 identity:** 通常の `reflux=on/off` run と B-4 標本を機械的に分ける支配点。
- **closed decision → planner/coder proposal の因果束縛:** envelope/decision hash と次 proposal hash の chain。receipt 所持だけでは不足する。
- **B-4 report・材料レポート・試行台帳の acceptance consumer:** `B4BlockReceipt`、active record、launch manifest が無い block を参照不能にする層。
- **API 直呼びと fixture main の扱い:** 3 driver の `run_one_iteration()`、`drive_iteration()`、fixture main を物理的に止めるか、B-4 名乗りだけを downstream で拒否するかの裁定。
- **append-only launch ledger / one-shot token:** 複数 record、別経路の先行 query、失敗後 record 選択を repository-local Git だけで防げない。
- **§6 全前提の experiment launch gate:** plan が機械検査するのは主に §5 であり、§6 の 2、4〜8 は別 receipt 群が必要 (`prereg-s5-s6.md:44-76`)。
- **model snapshot の pre-payload attestation:** alias `opus` から exact deployment snapshot を query 出力無しに固定する層。

## 併走 wave との合流で壊れる組み合わせ

- **本 wave `/v3` reader + 併走 wave `/v2` fixture/validator:** positive path が全件拒否される。v2 fallback を足すと admission 前 receipt の抜け道になる。
- **両 wave が別内容で `/v3` を名乗る:** admission fields だけの v3 と driver-binding fields だけの v3 が同名になり、双方の exact-key reader が相手を拒否する。union を採るなら新しい単一 schema として再設計が必要。
- **本 wave の test-only admission None + 併走 wave の receipt binding:** evidence class を certified に固定しなければ、test-only receipt が record gate を完全に迂回する。
- **現在の projection 値を §5 へ書く併走変更 + 両 wave の code merge:** module 自身と `p3_s4_loop.py` の bytes が変わるため、`df37...` と entry 10 件が合流後に初めて stale になる。
- **receipt iteration N を driver N の必須入力にする実装:** receipt の生成には driver N の state/digest が必要で循環する。末尾検査なら実走停止 gate にならない。
- **`main` の独立 merge:** 本 wave が `--admission-record` を parse して factory へ渡す変更と、併走 wave の receipt 引数・公開 verifier 配線の片方だけが残ると、option は存在するが gate へ届かない、または必須 factory 引数欠落で全実走停止になる。

## 攻撃できなかった面

- 併走 wave の段 2 plan、実 patch、tests は射影されておらず、brief の P3 以上の具体実装は見ていない。
- 実 Claude query、model rollout、pytest は実行していない。model mismatch 後の漏洩評価はコード順序による静的判定である。
- 実際に採用される driver と sanctioned CLI は未確定なので、3候補すべてを同じ経路として検査した。
- B-4 専用 report/ledger consumer は repository 検索で見つからなかったため、未実装層として評価した。将来別 wave に存在する未起動の設計は見ていない。