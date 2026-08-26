静的検査の結論は NO-GO である。段 2 の停止判断は概ね正しいが、さらに manifest schema の設計不一致、`C` の singleton diff 未検証、legacy anchor `A` を発効点として再検証する production 経路、trial registration 不在が追加の停止条件になる。

pytest、evaluator、artifact 生成は実走していない。以下は source、Git 履歴、decision/worklog の静的追跡だけに基づく。

## 1. 3 artifact field の権威追跡

### Trial manifest

- **所見**: `schema_version` は設計文書から導出された値ではなく、実装が選んだ `"p3-8c-trial-manifest/v2"` である。
- **根拠**: `orchestrator/campaign/trial_registry.py:55,110-113,769-788`、`docs/phase3-8c-preregistration.md` §1・§4
- **成果物影響**: loader の受理集合はこの実装定数が決め、設計に適合しても別 schema の manifest は拒否される。
- **反証可能性**: 設計文書または批准済み freeze にこの literal と exact field 集合を定めた箇所があれば覆る。

- **所見**: `prereg_commit` は設計文書由来の値ではないが、D550 が認めた Git topology 由来の anchor `A` として機械確定できる。
- **根拠**: `docs/decisions.md:22436-22444`、`orchestrator/campaign/trial_registry.py:778-780,1468-1474`
- **成果物影響**: `A` の選択が変われば manifest bytes、campaign registration、履歴受理集合が変わる。
- **反証可能性**: 生成器導入前から一意な anchor を選ぶ設計規則、または `A` 以外を許さない既存 freeze があれば判断が変わる。

- **所見**: `trials` の 6 要素集合は設計で決まるが、配列順を H1/H2、次に on/off/swapped とする規則は実装側の選択である。
- **根拠**: `docs/phase3-8c-preregistration.md:139`、`orchestrator/campaign/trial_registry.py:73-74,754-766`
- **成果物影響**: 順序だけが異なる設計同値の manifest bytes と SHA-256 が拒否され、binding 参照も変わる。
- **反証可能性**: 設計または批准済み manifest 規約に配列の exact order が明記されていれば覆る。

- **所見**: `trials[*].trial_id` の `h1-on` 型命名は設計から一意に導けず、段 2 著者の命名規則である。
- **根拠**: `s2-plan.md:12`、`orchestrator/campaign/trial_registry.py:107,739-751`
- **成果物影響**: trial registry、attempt slot、report、receipt の全参照キーが任意の命名選択で変わる。
- **反証可能性**: 設計文書または既存凍結物に trial ID の生成式があれば覆る。

- **所見**: `trials[*].arm` の値集合は 8b 設計から正当に導出できる。
- **根拠**: `docs/phase3-8b-descriptor-design.md:156-170`、`docs/phase3-8c-preregistration.md:3`
- **成果物影響**: 値が違えば 6-cell universe、descriptor binding、選択評価表が変わる。
- **反証可能性**: 8b の再凍結で arm 集合が変更されていれば再導出が必要になる。

- **所見**: `trials[*].holdout` の H1/H2 は 8b 設計と既存 holdout freeze から正当に導出できる。
- **根拠**: `docs/phase3-8b-descriptor-design.md:6-12,113-118`、`orchestrator/campaign/s8b_holdout_freeze.py:80-104`
- **成果物影響**: 値が違えば正式 6-cell 集合と全件報告母集団が変わる。
- **反証可能性**: ratified freeze が別 holdout 集合を active としていれば覆る。

- **所見**: `trials[*].campaign_id` は site、environment contract、trial ID、arm binding を含む production preimage に依存し、現設計だけでは導出不能である。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:749-801,1143-1186,1267-1285`、`orchestrator/campaign/p3_s4_loop_trigger_gating.py:423-437`、`docs/phase3-8c-preregistration.md:157-158`
- **成果物影響**: 任意の ID を置けば production の `assert_campaign_binding` が拒否するか、別 campaign の report を参照する。
- **反証可能性**: 正式 site と environment contract を結果前に固定し、production identity 関数から 6 ID を再生成できれば覆る。

- **所見**: `trials[*].generations=2` は 8c 設計から一意に導出できる。
- **根拠**: `docs/phase3-8c-preregistration.md:91-95`、`orchestrator/campaign/trial_registry.py:747-748`
- **成果物影響**: 2 以外は loader と正式受入の generation binding が拒否する。
- **反証可能性**: 8c の再凍結が exact `G=2` を変更した場合だけ覆る。

- **所見**: manifest に cell ごとの `n` が無いことは 8b §10.2 と実 schema の実在する不一致である。
- **根拠**: `docs/phase3-8b-descriptor-design.md:464-484`、`orchestrator/campaign/trial_registry.py:110-113`、`orchestrator/campaign/s8c_result_judge.py:266-327`
- **成果物影響**: 現 manifest は完全 block と観測反復集合を certified judge へ束縛できず、正式性能表の受理根拠にならない。
- **反証可能性**: 同じ manifest SHA に束縛された別 artifact が cell ごとの `n` と完全 schedule を必須化し、judge がそれだけを読むなら影響を再評価できる。

### Effective binding

- **所見**: binding の `schema_version` は実装定数であり、設計文書が literal を一意に定めていない。
- **根拠**: `orchestrator/campaign/trial_registry.py:70,118-122,1341-1343`
- **成果物影響**: production loader の受理集合が設計でなくこの constant に支配される。
- **反証可能性**: 設計または批准済み schema record に `"p3-8c-prereg-effective-binding/v1"` が固定されていれば覆る。

- **所見**: `prereg_content_commit` は P 作成後に Git から一意に取得でき、自己参照を作らない。
- **根拠**: `docs/phase3-8c-preregistration.md:41-48`、`orchestrator/campaign/trial_registry.py:1344-1346,1412-1420`
- **成果物影響**: P が変われば binding bytes と、manifest/genesis を受理する履歴集合が変わる。
- **反証可能性**: binding が P 自身に含まれる構造へ変更されていれば循環になる。

- **所見**: `manifest_path` は凍結済み evidence contract が exact path を持つため導出可能である。
- **根拠**: `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:101-117`、`docs/phase3-8c-preregistration.md:285-287`
- **成果物影響**: 別 path は C03/C08 と binding loader の参照集合から外れる。
- **反証可能性**: condition-freeze tip が別 evidence contract path を束縛していれば覆る。

- **所見**: `manifest_sha256` は P の historical manifest bytes から一意に導出できる。
- **根拠**: `orchestrator/campaign/trial_registry.py:1412-1426`
- **成果物影響**: bytes が 1 bit 変われば binding と launch admission が拒否する。
- **反証可能性**: loader が historical blob でなく worktree bytes を権威にしていれば覆る。

- **所見**: `freeze_id` は設計が意味と生成式を定めず、任意の非空文字列を loader が受理するため導出不能である。
- **根拠**: `docs/phase3-8b-descriptor-design.md:538-543`、`orchestrator/campaign/trial_registry.py:1354-1356`
- **成果物影響**: 第二 registry の識別と全 attempt ledger の namespace が著者選択で変わる。
- **反証可能性**: condition-freeze digest、ratified 8b generation、P digest のどれを使うかを定めた批准済み規則があれば覆る。

- **所見**: `attempt_registry_path` の literal は実装定数であり、8b は canonical path の固定を要求するだけで文字列を定めていない。
- **根拠**: `docs/phase3-8b-descriptor-design.md:538-541`、`orchestrator/campaign/trial_registry.py:61-63,1357-1362`
- **成果物影響**: registry root の受理 path と全履歴走査対象が実装定数で変わる。
- **反証可能性**: 設計または凍結契約にこの exact path が明記されていれば覆る。

- **所見**: `attempt_registry_initial_sha256` は正しい genesis が存在すれば導出可能だが、現状は genesis の閉じた slot 集合が未確定なので値も未確定である。
- **根拠**: `orchestrator/campaign/trial_registry.py:1427-1438,2387-2434`、8b §10.2・§10.5
- **成果物影響**: 暫定 genesis を hash すると後から slot を足せず、不足反復が判定不能ではなく未登録として固定される。
- **反証可能性**: `n`、attempt 数、retry 理由、全 schedule-row digest が結果前に固定されれば導出できる。

### Schedule

- **所見**: schedule の `schema_version` は実装定数で、設計文書から literal を導出できない。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:51,340-345`
- **成果物影響**: artifact parser の受理集合が設計でなく module constant に依存する。
- **反証可能性**: 凍結契約に `"s8c-schedule/v1"` が明記されていれば覆る。

- **所見**: `generator_version` は実装著者が選んだ値で、設計が generator の版名やアルゴリズムを固定していない。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:52,286-314,340-345`、`docs/phase3-8c-preregistration.md:135-138`
- **成果物影響**: 同じ seed と設計でも別の正当なランダム化器が異なる schedule bytes を作り、受理集合が変わる。
- **反証可能性**: generator source/hash/domain を指定する批准済み schedule 規約があれば覆る。

- **所見**: `master_seed` を condition-freeze tip digest にする案は循環しないが、その選択規則自体は設計から導出できない。
- **根拠**: `docs/phase3-8c-preregistration.md:135-138,164-165`、`orchestrator/campaign/s8c_preregistration.py:1714-1720`、`s2-plan.md:26,58-68`
- **成果物影響**: seed と 6 cell の順序が、設計でなくプラン著者が選んだ hash source によって変わる。
- **反証可能性**: 設計またはユーザー裁定が tip record raw SHA-256 を seed とする式を確定すれば覆る。

- **所見**: `cells` の 6 座標集合は設計由来だが、配列順は `_order_key` の domain、preimage、tie-breaker という実装規則に依存する。
- **根拠**: `docs/phase3-8c-preregistration.md:135-139`、`orchestrator/campaign/s8c_schedule.py:88-90,286-314`
- **成果物影響**: 同じ seed でも generator 実装を替えると各 schedule index が別 cell を指す。
- **反証可能性**: この exact order algorithm が批准済み設計に固定されていれば覆る。

- **所見**: `cells[*].schedule_index` は実装上の列挙位置であり、設計から単独では導出できない。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:330-339`
- **成果物影響**: launch が index で cell を選ぶ場合、別 order は別 holdout/arm を実行させる。
- **反証可能性**: schedule generator の exact order が権威化されれば導出可能になる。

- **所見**: `cells[*].arm` と `holdout` の語彙と全積は設計由来だが、個々の index への割当は未権威の generator に依存する。
- **根拠**: 8b §3・§4、`orchestrator/campaign/s8c_schedule.py:299-314,330-338`
- **成果物影響**: 6-cell 被覆自体は維持できても実行順、slot 参照、report 行の対応が変わる。
- **反証可能性**: generator version と seed 規則が批准されれば個々の値まで決まる。

- **所見**: `cells[*].search_space_sha256` は 10-field projection が未定義なので現状導出不能である。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:59-70,252-272,328-337`
- **成果物影響**: arbitrary projection を自分で再生成すれば byte check は緑になるが、探索空間が設計に一致する証明にはならない。
- **反証可能性**: 10 field の exact source、JSON projection、historical commit を定めた authority contract があれば覆る。

- **所見**: `cells[*].initial_state_sha256` は 8-field projection が未定義か現実の値と型矛盾するため現状導出不能である。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:75-84,252-278,328-337`
- **成果物影響**: wrong initial state を全 cell で共有しても「共有 digest」の検査は通り、certified な比較の開始状態が変わる。
- **反証可能性**: 8 field の exact sourceと empty-state encoding を批准すれば覆る。

### Attempt-registry genesis

- **所見**: retryable reason の exact 集合は設計の凍結範囲に存在せず、現値は実装定数である。
- **根拠**: `docs/phase3-8b-descriptor-design.md:531-537`、`orchestrator/campaign/trial_registry.py:132-134`
- **成果物影響**: どの失敗に再測定 slot を使えるかという受理集合がコード著者の選択で変わる。
- **反証可能性**: exact 四理由が事前登録の凍結範囲へ追加・批准されれば覆る。

- **所見**: replicate と attempt の全 slot 数は `n` と attempt 上限が未確定なので導出不能である。
- **根拠**: 8b §10.2・§10.5、`orchestrator/campaign/trial_registry.py:1940-1977,2130-2133,2387-2434`
- **成果物影響**: genesis を早期発行すると不足 slot の後出し追加が禁止され、正式対比の観測集合が永久に不足する。
- **反証可能性**: cell ごとの `n` と各反復の attempt slot 数を固定する裁定があれば覆る。

- **所見**: cell-level `schedule.v1.json` は repetition row を持たないため、slot の `schedule_row_sha256` を導出できない。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:3-11,317-324`、`orchestrator/campaign/trial_registry.py:139-142,1965-1977`
- **成果物影響**: fixture digest を置けば attempt と正式 complete-block schedule の一対一束縛が偽になる。
- **反証可能性**: `n×6` 行の別 schedule を先に発行し、その各行を genesis が hash する規則があれば覆る。

## 2. Schedule authority 18 field

- **所見**: `arms` は on/off/swapped の値と順序を 8b §4 から導出できる。
- **根拠**: `docs/phase3-8b-descriptor-design.md:156-170`、`orchestrator/campaign/s8c_schedule.py:53`
- **成果物影響**: 誤値は search-space digest と 6-cell universe を変える。
- **反証可能性**: 8b の再凍結が arm 集合または表順を変えていれば再検討する。

- **所見**: `designated_source_context` の exact bytes は設計に存在せず、production module の文字列定数が実体である。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:357-369`
- **成果物影響**: source context の文言変更が search-space digest を変えるか否かを実装側だけが決める。
- **反証可能性**: 設計または凍結 artifact がこの文字列の bytes/hash を指していれば覆る。

- **所見**: `descriptor_bindings` の各 cell の実値は resolver から得られるが、6 値を一つの JSON object に射影する exact 規則が無い。
- **根拠**: `orchestrator/campaign/s8c_arm_inputs.py:409-493`、8c §3 の arm binding
- **成果物影響**: key、含める digest、descriptor bytes の選択で search-space digest が任意に変わる。
- **反証可能性**: cell key と含有 field を固定した批准済み projection があれば覆る。

- **所見**: `gating_spec` は production 定数として実在するが、設計由来の exact bytes ではない。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:322-326`、`docs/decisions.md:22401-22418`
- **成果物影響**: five-bit wire contract の文言変更が schedule hash を動かす authority をコードが握る。
- **反証可能性**: 設計がこの exact UTF-8 bytes または hash を固定していれば覆る。

- **所見**: `holdout_bindings` の意味値は既存 freeze にあるが、schedule field への exact projection は規定されていない。
- **根拠**: `orchestrator/campaign/s8b_holdout_freeze.py:80-104`、`orchestrator/campaign/trial_registry.py:77-102`
- **成果物影響**: workload 名、candidate ID、YCSB field のどれを含めるかで search-space digest が変わる。
- **反証可能性**: raw freeze object または `_holdout_bindings_from_freeze()` の出力をそのまま使う規則が批准されれば覆る。

- **所見**: `holdouts` の H1/H2 は設計と freeze から一意に導出できる。
- **根拠**: 8b §3、`orchestrator/campaign/s8b_holdout_freeze.py:100-104`
- **成果物影響**: 誤値は正式 cell 集合を変える。
- **反証可能性**: active holdout freeze が別候補を持てば覆る。

- **所見**: `role_contracts` の exact bytes は production 定数だけにあり、設計文書の権威ではない。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:271-320`
- **成果物影響**: role の受理出力や禁止事項を変えても、どの bytes が search-space authority かを実装者が選べる。
- **反証可能性**: role contract bytes/hash を指す批准済み freeze があれば覆る。

- **所見**: `role_files` は path と blob が実在するが、path、bytes、blob hash のどれを JSON に置くか設計が定めていない。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:261-269`、`docs/decisions.md:22401-22418`
- **成果物影響**: path だけなら同 path の改変を検出せず、bytes/hash を使えば別 digest になる。
- **反証可能性**: anchor commit の `{path,blob_sha256}` 集合とする批准済み規則があれば覆る。

- **所見**: `role_payload_allowlist` の exact mapping は implementation constant で、8c が凍結するのは閉包の意味だけである。
- **根拠**: `docs/phase3-8c-preregistration.md:96-116`、`orchestrator/campaign/p3_autonomous_workload_trial.py:328-355`
- **成果物影響**: payload key の追加・削除が search-space digest とリーク受理集合をコード側で変える。
- **反証可能性**: exact key mapping が evidence contract または freeze に含まれていれば覆る。

- **所見**: `workloads` の H1/H2 値は凍結物から得られるが、`FORMAL_WORKLOADS` の JSON projection を正本とする規則が無い。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:242-249`、`orchestrator/campaign/s8b_holdout_freeze.py:87-103`
- **成果物影響**: candidate ID や scale を含めるかで search-space digest が変わる。
- **反証可能性**: freeze の `HOLDOUTS` objectを exact authority value とする規則があれば覆る。

- **所見**: `attempt_policy` の production 値は実在するが、role attempt policy と実験 attempt registry policy のどちらを指すか設計が定めていない。
- **根拠**: `orchestrator/campaign/s8c_generation_projection.py:28-31`、8b §10.5
- **成果物影響**: retry 不可の role 呼出しと、障害時の再測定可能 slot を混同すると initial-state digest の意味が変わる。
- **反証可能性**: field の意味を role-attempt policy に限定する批准済み定義があれば覆る。

- **所見**: `baseline` は同じ開始状態という意味だけが設計にあり、exact mapping は production helper の選択である。
- **根拠**: 8b §4、`orchestrator/campaign/p3_autonomous_workload_trial.py:145-151,1684-1747`
- **成果物影響**: baseline の keyや null表現が initial-state digest と比較可能な開始状態を変える。
- **反証可能性**: baseline object の exact bytes/hash が凍結されていれば覆る。

- **所見**: `descriptor_binding` は cell ごとに異なる実行値なのに authority は全 cell 共通の単一 object を要求し、意味上も一意な値が存在しない。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:72-84`、`orchestrator/campaign/p3_autonomous_workload_trial.py:2585-2607`、`orchestrator/campaign/s8c_arm_inputs.py:434-493`
- **成果物影響**: 一つの cell の bindingを共有値にすると他の5 cellの initial-state claimが偽になる。
- **反証可能性**: この field が instance でなく binding schema/hash を表すと設計で明記されれば覆る。

- **所見**: `gating_snapshot` は dataclass として実在するが、JSON object への canonical projection が規定されていない。
- **根拠**: `orchestrator/campaign/s8c_generation_projection.py:173-212`、`orchestrator/campaign/s8c_schedule.py:91-105`
- **成果物影響**: `{text,sha256}`、`{wire}`、dataclass 全 field の選択で initial-state digest が変わる。
- **反証可能性**: exact object schema が批准されれば覆る。

- **所見**: `initial_role_metrics` は implementation constant であり、設計は exact key集合と null表現を定めていない。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:145-151`
- **成果物影響**: 初期未観測値の表現が initial-state digest と開始状態の同一性を変える。
- **反証可能性**: exact initial metrics object が凍結されていれば覆る。

- **所見**: `leakproof_context` は production では文字列だが schedule schema は JSON object を要求するため、そのままでは実在する矛盾である。
- **根拠**: `orchestrator/campaign/s8c_generation_projection.py:22-26`、`orchestrator/campaign/s8c_schedule.py:91-105,237-240`
- **成果物影響**: `{"text":...}` のような wrapper を発明すれば再生成検査は通るが、initial-state digest の権威が設計から実装へ移る。
- **反証可能性**: authority field は runtime value でなく metadata object だと定める既存規則があれば覆る。

- **所見**: `stop_policy` の意味は設計にあるが、exact JSON mapping は implementation constant である。
- **根拠**: `docs/phase3-8c-preregistration.md:140-143`、`orchestrator/campaign/s8c_generation_projection.py:32-35`
- **成果物影響**: policy keyや表現の選択が initial-state digest を変え、早期停止禁止の証明範囲を変える。
- **反証可能性**: exact mapping が凍結されていれば覆る。

- **所見**: `whiteboard` の正式初期意味は空で production も `[]` を返すが、schedule validator は空配列を拒否するため実在する矛盾である。
- **根拠**: `docs/phase3-8c-preregistration.md:110-116`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1650-1652`、`orchestrator/campaign/s8c_schedule.py:194-207`
- **成果物影響**: `[{"status":"initial"}]` のような sentinel は存在しない履歴を authority に加え、初期状態と future report を変える。
- **反証可能性**: 設計が非空 sentinel を初期 whiteboard と定めていれば覆る。

- **所見**: 18 field のうち完全に設計・凍結物から閉じるのは少なくとも `arms` と `holdouts` だけであり、他は projection 不在、実装定数、または型矛盾を持つため本 wave の停止条件である。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:57-115,210-249`、D1077
- **成果物影響**: 18-field mappingを埋めても「その mapping から再生成できる」ことしか証明せず、設計由来の certified schedule にはならない。
- **反証可能性**: 18 field 全件について source commit、path、JSON pointer、projection式を列挙した批准済み authority manifest があれば停止を解除できる。

## 3. Canonical projection で矛盾は消えるか

- **所見**: caller 側に projection 層を置く構造自体は D530/D549 が想定しているが、projection の内容規則は一つも批准されていない。
- **根拠**: `docs/decisions.md:21883-21906,22399-22418`、`orchestrator/campaign/s8c_schedule.py:13-15`
- **成果物影響**: 任意 projection と同じ projection を checker が再使用すれば恒真になり、保存 schedule の digestだけが変わる。
- **反証可能性**: producer と独立した設計権威から projection を再構築する verifier が既にあれば覆る。

- **所見**: `leakproof_context`、`whiteboard`、`descriptor_binding` を adapter で包めば型エラーは消えるが、現状その adapter 規則を本 wave が決めることは偽の権威に当たる。
- **根拠**: D1077、`orchestrator/campaign/s8c_schedule.py:91-109,167-207`、production 値は上記3所見
- **成果物影響**: wrapper の形が initial-state SHA-256 と、将来どの実行を同一開始状態として受理するかを決める。
- **反証可能性**: wrapper schema と empty-state semantics をユーザーが批准すれば偽の権威ではなくなる。

- **所見**: production 値に合わせて validator を緩和する案も、D530 の空配列拒否と C05 の受理意味を変えるため単純な修正ではない。
- **根拠**: `docs/decisions.md:21883-21899`、`docs/phase3-8c-preregistration.md:289-297`
- **成果物影響**: C05 の受理集合と拒否理由が変わり、`DECIDER_VERSION` bump と新 condition-freeze record が必要になりうる。
- **反証可能性**: semantic change でないと独立検査が示すか、新世代 record と裁定を同時発行すれば解除できる。

## 4. Authority schema の由来

- **所見**: 18-key schema は commit `542ab551...` で実装され、D530 は「caller供給、closed keys、型、非空性」だけを裁定し、18 field 名と型対応までは裁定していない。
- **根拠**: `docs/decisions.md:21883-21906`、`docs/archive/worklog-phase3-0818-662.md:15-20`、`orchestrator/campaign/s8c_schedule.py:57-115`
- **成果物影響**: field集合と型分類は実装著者の値規則であり、D1077 の設計権威として流用できない。
- **反証可能性**: D530 の一次裁定に18 field/typeの逐語承認が別途記録されていれば覆る。

- **所見**: schema 導入時のテスト authority は production と異なる fixture 値を使い、`leakproof_context` を object、`whiteboard` を非空 sentinel としていた。
- **根拠**: `orchestrator/tests/test_s8c_schedule.py:12-70`、`orchestrator/tests/test_s8c_preregistration_predicates.py:44-102`
- **成果物影響**: テストが緑でも正式 H1/H2 production authority を構成可能だとは示さない。
- **反証可能性**: 導入 commit の別検査が production constants 全18件を通していたと示せれば覆る。

- **所見**: 翌日の D549 と worklog は本物の production authority を構築不能と明記しており、schema が production 値を見て閉じたという一般化を否定する。
- **根拠**: `docs/decisions.md:22399-22427`、`docs/archive/worklog-phase3-0819-684.md:1-8`
- **成果物影響**: 現 schema は将来の interface stub であり、正式 schedule の値権威にはならない。
- **反証可能性**: D549 後に全18 fieldの実体供給と projectionを批准した決定があれば覆るが、検索では見つからなかった。

## 5. 自己参照

- **所見**: anchor `A` の condition-freeze tip record digestを seed にすること自体は循環しない。
- **根拠**: `orchestrator/campaign/s8c_preregistration.py:1666-1720`、condition-freeze records、`docs/phase3-8c-preregistration.md:285-301`
- **成果物影響**: Aを固定すれば schedule P、binding C、後続Rのどれも tip record bytesを変更せず、seedは安定する。
- **反証可能性**: 本 wave が規範本文、evidence contract、`DECIDER_VERSION`、condition-freeze recordを変更するなら再評価が必要になる。

- **所見**: 「発効中の record」という表現は誤りで、正確には A で履歴検証を通った condition-freeze tip recordである。
- **根拠**: `docs/phase3-8c-preregistration.md:303-317`、`orchestrator/campaign/s8c_preregistration.py:1714-1720`
- **成果物影響**: 誤表現のままだと全12条件が未充足でも発効済み authority と誤認されるが、artifact bytes自体は変わらない。
- **反証可能性**: `effective_at(A)` が全条件充足を返す実測があれば「発効中」と呼べる。

- **所見**: A→P→C の基本 derivation は、manifestがA、bindingがPを参照し、bindingがCを参照しないため循環しない。
- **根拠**: `docs/phase3-8c-preregistration.md:41-50`、`orchestrator/campaign/trial_registry.py:289-306,1331-1372`
- **成果物影響**: Pが変わればbindingだけ再生成すればよく、固定点探索は不要である。
- **反証可能性**: manifestにP、bindingにC、genesisにP/Cを埋める変更があれば循環する。

- **所見**: より深刻なのは legacy `prereg_commit=A` を production が発効 commit として再検証するため、Aに scheduleが無い限り registered-effective 経路が構造的に開かないことである。
- **根拠**: `orchestrator/campaign/trial_registry.py:3922-3940`、`orchestrator/campaign/s8c_preregistration_evidence.py:2082-2088`、D550
- **成果物影響**: HEADのC05が進んでも `effective_at(A)` は `schedule-schema-absent` のままで、certifying launch受理集合は増えない。
- **反証可能性**: launchがAでなくCを再検証する配線へ変わるか、A時点にscheduleを置ける非循環構造が示されれば覆る。

## 6. 二段束縛と land

- **所見**: 段2の A→P→C→R 順序は、CをPの通常直子として作る限り exact parent `{P}` を満たす。
- **根拠**: `s2-plan.md:86-94`、`orchestrator/campaign/trial_registry.py:1187-1245`
- **成果物影響**: merge/root/別親Cは拒否され、Pのmanifest/genesis以外をbindingできない。
- **反証可能性**: 実際の `git rev-list --parents -n 1 C` が `C P` の2 fieldでなければ所見は成立しない。

- **所見**: 現 production validator はCの親だけを検査し、Cがbinding pathだけを導入したことを検査しない。
- **根拠**: `orchestrator/campaign/trial_registry.py:1219-1245,1442-1487`
- **成果物影響**: bindingと同じCで別artifactや規範変更を導入してもlaunch/acceptanceが受理し、設計のsingleton変更集合が広がる。
- **反証可能性**: production到達可能な別helperがC対Pのdiff path集合をsingletonとして拒否していれば覆るが、検索では見つからなかった。

- **所見**: 新CLIの `--check` だけでsingleton diffを検査してもproduction launchが呼ばなければ§1・§7の強制にならない。
- **根拠**: `s2-plan.md:107-113`、`orchestrator/campaign/trial_registry.py:3624-3629,3922-3948`
- **成果物影響**: 開発時checkを省略した履歴もproductionが受理し、二段束縛の受理集合が設計より広い。
- **反証可能性**: `validate_preregistration_binding` 自身がdiff singleton検査を呼ぶ実装へ変われば解消する。

- **所見**: `dev_wave_land.py` の ff-only は既存Cの親集合を変更せず、mainをlanding tipへ前進させるだけである。
- **根拠**: `tools/dev_wave_land.py:5492-5506`
- **成果物影響**: land後もCのsole parentはPのままで、P/C binding bytesは変わらない。
- **反証可能性**: landがrebase、cherry-pick、非ff mergeを行った実履歴なら覆る。

- **所見**: spool fold commitはff-only後のlanding tipを親に持つ後続commitであり、PとCの間へ割り込まない。
- **根拠**: `tools/dev_wave_land.py:4481-4499,4570-4593`、同 `4434-4454`
- **成果物影響**: foldはcanonical docsを後続commitで変えるが、Cのparent集合とbinding blobを変えない。
- **反証可能性**: fold commitの親がlanding tipでない、またはwave側Cを再作成する経路があれば覆る。

- **所見**: main進行時にmerge/rebaseで既存Cを流用せずA/P/Cを再構成し、P変更時にbindingを再生成する段2方針は正しい。
- **根拠**: `s2-plan.md:94`
- **成果物影響**: 古いPを指すbindingを新履歴へ持ち込む受理を防ぐ。
- **反証可能性**: stale mainでもff-only可能でCのOIDが不変だった場合は再構成不要だが、害はない。

- **所見**: `AI-Agent:` trailerはcommit messageだけを変え、Cのtree diffを増やさず、bindingがCを記録しないため自己参照も作らない。
- **根拠**: `docs/ai-provenance.md:8-33,44-55`、`docs/phase3-8c-preregistration.md:46-48`
- **成果物影響**: CのOIDはtrailerで決まるが、artifactにCを焼かないためbinding bytesは不変である。
- **反証可能性**: 「bindingだけ」の意味がtree diffでなくcommit messageの無内容まで要求すると定めた規範があれば衝突する。

- **所見**: C後のR記録commitはCの親集合を変えないため二段束縛と両立する。
- **根拠**: `docs/phase3-8c-preregistration.md:49-50`、`s2-plan.md:91-92`
- **成果物影響**: worklogやhandoffを後続履歴に残してもCのidentityとsingleton tree diffは保持される。
- **反証可能性**: R作成時にCをamendまたはrebaseした実履歴なら覆る。

## 7. `n` と genesis に関する両面検査

- **所見**: 親の「n未記入なので完全slot集合を導出できない」という結論は8b §10.2・§10.5から強く支持される。
- **根拠**: `docs/phase3-8b-descriptor-design.md:464-484,518-543`
- **成果物影響**: `n` 未確定でgenesisを作ると、正式な全反復と全attemptの報告母集団を閉じられない。
- **反証可能性**: cellごとのnとは独立に全将来replicateを有限列挙できる別の批准済み上限があれば覆る。

- **所見**: 覆す候補は「manifestは6 trialの起動台帳で、nは後のjudge manifestで持つ」という二manifest解釈だが、同一pathをC03/C08とresult judgeが異なるschemaで期待しており現状は成立しない。
- **根拠**: `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:101-108,307-315`、`orchestrator/campaign/trial_registry.py:110-113`、`orchestrator/campaign/s8c_result_judge.py:266-327`
- **成果物影響**: launch用`trials` manifestを発行してもofficial性能表用`cells+n+schedule` manifestにはならず、certified選択を作れない。
- **反証可能性**: 2 manifestを別path/schemaとして分離し、互いのdigestをcross-bindする設計裁定があれば覆る。

- **所見**: productionの `PerfConfig.reps=2` はbench内部の反復で、8b §10.2のcell replicate `n` を確定する根拠にはならない。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:804-816`、`orchestrator/campaign/s8c_result_judge.py:341-366`
- **成果物影響**: `reps=2` をnとして流用すると1 trial内部の生値と複数trial replicateを混同し、標本SDと完全blockが変わる。
- **反証可能性**: report producerが各bench repを独立schedule row、attempt slot、run-startへ束縛していれば覆る。

- **所見**: productionが `replicate_index==0` だけを選ぶことは、n≥2の正式系列に未追随である。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:1299-1353`
- **成果物影響**: nをmanifestへ追加しても実行器がreplicate 1以降を消費せず、公式対比は判定不能になる。
- **反証可能性**: 全登録replicateを順に消費するproduction loopが追加されれば解消する。

## 8. 発行したふりと production consumer

- **所見**: `schedule.v1.json` を読むproduction経路は現在存在せず、`run_trial`は `s8c_schedule` をimportすらしていない。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:41-53,1799-1804`、`orchestrator/campaign/s8c_preregistration_evidence.py:2156-2185`
- **成果物影響**: schedule bytesを発行しても実行順、launch、report、certified選択は変わらない。
- **反証可能性**: `run_trial -> load_schedule -> verify_schedule -> consume_schedule` の実call graphが追加されれば覆る。

- **所見**: `_load_s8c_schedule_authority()` は18-field schedule authority builderではなく、現状raiseするbudget用の別shape入口である。
- **根拠**: `orchestrator/campaign/p3_autonomous_workload_trial.py:1799-1804,1837-1859`
- **成果物影響**: この関数を実装しただけでは `s8c_schedule.validate_authority` に渡す18 fieldもschedule cell消費も得られない。
- **反証可能性**: 同関数が18-field mappingとartifact bytesを返し、run_trialからconsumerへ渡す仕様へ変更されれば覆る。

- **所見**: manifestとbindingにはproduction loaderがあるが、launchには別の committed trial registrationが必須で、段2 planはそのartifactを発行しない。
- **根拠**: `orchestrator/campaign/trial_registry.py:57,3614-3629,3942-3948`、`s2-plan.md:217-230`
- **成果物影響**: 3 artifactとgenesisだけではregistered launchはregistry不在で止まり、production受理集合は増えない。
- **反証可能性**: 同waveの後続commitに `output/s8c-trial-registry/registry.jsonl` の正しいregistrationを追加するなら覆る。

- **所見**: 親の「C05の閂がartifact不在からconsumer未配線へ移る」は現在HEADのgap snapshotについてだけ正しい。
- **根拠**: `orchestrator/campaign/s8c_preregistration_evidence.py:2082-2088,2156-2185`
- **成果物影響**: gap reasonは変わるが、launch、report、certified選択、attempt ledgerはいずれも動かない。
- **反証可能性**: schedule注入後のcurrent-HEAD evaluatorが別reasonを返す実測があれば診断部分は覆る。

- **所見**: 実launchはmanifestのanchor Aを再評価するため、親のC05一般化はformal activationの進捗としては耐えない。
- **根拠**: `orchestrator/campaign/trial_registry.py:3922-3940`、AはPより前というD550
- **成果物影響**: C時点にartifactがあってもA時点では不在なので、registered-effective launchの閂は動かない。
- **反証可能性**: activation再計算のcommitをAからCへ変えるproduction修正があれば覆る。

- **所見**: 発行の実利は将来consumer向けbytes anchorとgap診断の精密化だけで、D1078の「休眠capabilityを残さない」という批判を満たすには不足する。
- **根拠**: D1078 `docs/decisions.md:36847-36858`、8c §6・§7
- **成果物影響**: certified値は不変で、formal path風のartifactだけが増え、実装済みという外観が強くなる。
- **反証可能性**: 3 artifact、trial registration、schedule consumerを同waveでproduction launchへ結線すれば価値判断は変わる。

## 9. D1077へ返す裁定パッケージ

- **所見**: 現状のまま値を補う選択肢は除外し、次の3択をユーザー裁定へ返すべきである。
- **根拠**: D1077、D1078、上記authority・schema・consumer所見
- **成果物影響**: 選択によりformal artifactの発行時期、schema互換性、certified受理集合が変わる。
- **反証可能性**: 未発見の批准済みauthority manifestが18 field、n、site、freeze、slotを全て閉じていれば裁定自体が不要になる。

|選択肢|内容|犠牲にするもの|機械照合|
|---|---|---|---|
|A. 設計権威を先に閉じる 推奨|8b再凍結と8c改訂で、manifest v3の`cells+n+complete schedule`、18-field projection、seed、freeze ID、campaign site、retry理由、attempt上限、C singleton検査を定義し、production consumerとregistrationを同じ変更単位で実装する|本waveの即時発行と小さい変更面|可能。source commit/path/JSON pointer/projection versionをauthority manifestへ固定できる|
|B. 現実装schemaを新たに批准する|現在の18-key/typeを正式仕様へ昇格し、production値のwrapperとempty-state sentinelをユーザー裁定・condition refreezeで確定する|「既存設計文書が既に権威」というD1077の前提と、runtime値の素直な型|可能だが、批准後の新仕様からの導出であり、現設計からの導出とは言えない|
|C. formal pathへは発行しない|draft fixtureを別namespaceに置くか、waveを停止してauthority決定を待つ|C05 gap reasonの移動と短期的なartifact可視化|provisionalであることは照合可能だが、D1077の3 formal artifact発行は未達のまま|
|D. 値ごとの人間確定へ戻す|site、n、seed、IDs、projectionをユーザーが直接批准する|D1077が狙った反復承認の削減|批准recordへdigestを持たせれば可能だが、D1077を明示的にsupersedeする必要がある|

## 総括

- **(a) 本 wave を進めてよいか**: 進めてはならない。A案のauthority/schema裁定を先に行うか、C案としてformal pathへの発行を止めるべきである。
- **(b) 停止条件に当たる所見**: あり。18-field projection不在、`campaign_id`/`freeze_id`不定、`n`/attempt集合不定、manifest `trials`対設計`cells+n+schedule`不一致、C singleton diff未強制、anchor A再評価の構造問題、trial registrationとschedule consumer不在が該当する。
- **(c) P1**: 条件付き反対。tip record digestは非循環で安定するが、そのseed導出式は設計に無く、批准前は偽の権威である。
- **(c) P2**: 反対。`trial_id`式は著者選択で、`campaign_id`はsite/environment未確定のためproduction値を導出できない。
- **(c) P3**: topology自体には賛成。ただしproductionのC singleton diff検査と、`effective_at(A)`ではなくCを評価する整合が欠ける。
- **(c) P4**: 反対。18 fieldは既存凍結物だけでは閉じず、特に`descriptor_binding`、`leakproof_context`、`whiteboard`は意味または型が矛盾する。
- **(c) P5**: 必要性には賛成、現waveでの発行には反対。正しいgenesisには`n`、attempt上限、retry理由、完全schedule rowが先に必要である。