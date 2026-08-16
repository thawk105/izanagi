# レンズ A 所見

## 0. 読んだファイルと確認した行

必読 3 ファイルは全文読了した。

- [brief.md](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-t1134-prereg-contract/brief.md:1): 1〜125 行
- [parent-measurements.md](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-t1134-prereg-contract/artifacts/parent-measurements.md:1): 1〜112 行
- [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t1132-t1134-prereg-contract/artifacts/s2-plan.md:1): 1〜303 行

静的に確認した主な実装・契約・テスト:

- [s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/campaign/s8c_preregistration_evidence.py:194): 契約 loader、6 evaluator、`_evaluate_undefined`、例外処理
- [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/campaign/s8c_preregistration.py:1243): freeze 履歴、ruling 照合、predicate 正規化、発効 conjunction
- [evidence contract](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:1): C01/C03/C04/C08〜C12 と全 negative-control ID
- [phase3-8c-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/docs/phase3-8c-preregistration.md:25): §1、§4、§6、発効・凍結・構造衝突、正式起動形
- [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/tests/test_s8c_preregistration_predicates.py:312): token-only fixture、negative control、恒真化対策
- [test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/tests/test_s8c_preregistration_invariant.py:124): candidate freeze と発効 snapshot
- [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/campaign/p3_autonomous_workload_trial.py:389): generation validator、3 入口、射影 consumer、CLI 既定
- [s8c_generation_projection.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/campaign/s8c_generation_projection.py:458): critic 射影と planner payload 検証
- [trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/orchestrator/campaign/trial_registry.py:59): manifest schema
- [D96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/docs/decisions.md:4269) と [D410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract/docs/decisions.md:17149)

確認時点は HEAD `108133382312`、未コミット差分なし。pytest は実行しておらず、緑とは記録しない。

## 1. 受理集合の拡大経路

前提として、親の M2 は単一入力 `HEAD` の評価である。`f_old(HEAD)=false` かつ `f_new(HEAD)=false` から、全 commit に対する集合 `{C | f_new(C)=true}` が広がらないとは導けない。

1. **`machine_checkable` 反転単独**

   判定: **refuted / 重大度なし（固定 HEAD に限る）**。現 HEAD で boolean だけを反転した場合、6 本は親実測どおりすべて `UNSATISFIED` であり、直ちに `SATISFIED` は増えない。

   ただし判定: **real / 重大度: 高（将来一般化）**。反転は dormant evaluator を将来の commit に対して有効化する。C11 は同 wave の終端変更と組み合わさり、以前は必ず `EVIDENCE_UNDEFINED` だった入力を受理する。他 5 条件も将来終端を変更した瞬間に同じ経路が開く。

   成果物影響: 現在の正式三成果物は生まれないが、残条件実装後には shallow evaluator を通る試行が試行台帳、材料レポート、certified 選択へ流入しうる。

2. **C11 の sample-plan / cap-lift 差し替え**

   判定: **real / 重大度: 致命的**。旧契約は両 artifact の不存在を拒否した。新契約はそれらが無い入力を明示的に受理するので、受理集合は確実に広がる。さらに両 artifact が持っていた `minimum_generations >= 2`、`sample_count`、`ruling_reference` を失う一方、現行 validator は `1` も受理する。

   成果物影響: `G=1` の manifest／試行が正式台帳へ入り、「ワークロード特化合成」の材料レポートと certified 選択を偽装しうる。

3. **C03/C08 の二段束縛**

   判定: **real / 重大度: 高**。旧契約では commit 自己参照により構成不能だった入力を、P/C 二段構成で構成可能にする。これは正当化可能な変更だが、明白な受理集合拡大であり、brief の「他 11 条件は不変」は契約意味論について偽である。

   現 evaluator では両条件が `machine_checkable:false` のままなので、wave land 直後の predicate 出力が増えない点だけは **refuted / 重大度なし**。

   またプランの「C は binding record だけを導入する」は説明文にあるだけで、提案された exact-parent 検査だけでは、C が manifest その他も同時変更する形を拒否できない。

   成果物影響: 将来 evaluator を追加した際、P の manifest と異なる C-tree の manifest や余分な変更を台帳・報告・選択が参照する危険がある。

4. **評価器終端の C11 `SATISFIED` 化**

   判定: **real / 重大度: 致命的**。これは直接の受理集合拡大である。現テスト自身が、token-only C11 が現在の全静的検査を通って終端へ到達することを示している。段 2 の AST 強化案も後述の `G=1` と D96 の制約を解けていない。

   成果物影響: 残条件が閉じた後、C11 の偽陽性だけで非準拠試行が正式三成果物へ混入する。

5. **境界テストの追随**

   判定: **real / 重大度: 高（開発受理集合）**。production の predicate 集合を直接変えないが、「C11 が SATISFIED になる patch」を land 可能にする開発ゲート変更である。特に zero-satisfied snapshot を `{"C11"}` へ変えると、現行の `G=1` 受理を含む実装を正例として固定する。

   成果物影響: 誤った正例を CI が承認し、後続の試行台帳・材料レポート・certified 選択へ欠陥を運ぶ。

6. **g3 世代記録**

   判定: **real / 重大度: 高**。g3 は、それまで `unrecorded-protected-change` で拒否された新契約を freeze-valid にするため、freeze 履歴の受理集合を意図的に広げる。

   さらに `ruling_reference=D96` は本改訂の内容裁定ではなく一般手続である。`_assert_rulings_exist` は見出しの存在しか見ず、revision と決定内容の対応を検査しない。新しい実体 D が無くても D96 だけで g3 は通る。提案された g3 テストはこの弱い値を固定する。

   成果物影響: 内容裁定に束縛されない契約改訂を有効と見なし、三成果物の正当化根拠を弱める。

7. **g3 が executable gate を凍結しない**

   判定: **real / 重大度: 致命的**。freeze が hash するのは文書と evidence JSON であり、core、evaluator、generation projection は含まれない。live bytes と対象 commit の一致検査は provenance であって意味の凍結ではない。将来 commit が evaluator の終端や `_evaluate_undefined` を変更しても g4 は不要で、g3 は有効なままである。

   成果物影響: 契約世代を上げずに全 predicate を `SATISFIED` へ変え、正式台帳・材料レポート・certified 選択を発行できる構造が残る。

## 2. 終端 SATISFIED 化の危険 (条件別)

共通欠陥として、契約の `field_paths`、`reachable_from`、`consumer_requirement.path`、`entrypoints`、`proof` は loader で保存されるだけで、6 evaluator は一切参照しない。実際に使う契約情報は主に artifact kind と path であり、「契約を完全 discharge」する一般機構は存在しない。

判定: **real / 重大度: 致命的**。

成果物影響: JSON の要求を強めても evaluator が旧 hard-code のまま受理し、三成果物が契約文面より弱い証拠で発行されうる。

1. **C01 — real / 重大度: 高**

   契約は同じ ratified hash と workload projection が三つの production sink へ届くことを要求する。評価器は各関数内に整数 `1_000_000` と `48` があること、関数名の到達、どこかに `.sha256` と `.holdouts` があることしか見ない。値の代入、引数、同一 hash、実行順を証明しない。

   成果物影響: 異なる workload 規模や freeze を使った試行が台帳へ入り、比較材料と certified 選択を無効にする。

2. **C04 — real / 重大度: 高**

   call 名の到達と registry 側の同名関数の存在だけである。catch 節内か、全実験を判定不能にするか、再起動拒否が return より前かを見ない。

   成果物影響: crash 後の生存 cell だけが報告・選択され、材料レポートに file-drawer bias が入る。

3. **C09 — real / 重大度: 致命的**

   `accept_trial` 内の関数名と `"no-build"`／`"certifying"` 文字列だけを見る。全 build report、publish／append 前、no-build 非認証を証明しない。

   成果物影響: Layer 3 を通していない材料レポートが正式台帳と certified 選択の根拠になりうる。

4. **C10 — real / 重大度: 致命的**

   12 文字列と `read_and_verify_bytes` という call 名、`accept_trial` 内の verifier 名だけを見る。どの bytes を読んだか、hash 比較結果を使ったか、registry append 前かを見ない。

   成果物影響: proposal、raw response、WAL、bench、Layer 3 が別試行由来でも同一 proof chain として発行されうる。

5. **C11 — real / 重大度: 致命的**

   現評価器は `MAX_APPROVED_GENERATIONS >= 2`、三入口の call 名、critic call 名、疎な artifact schema、二つの文字列を見るだけである。段 2 案は AST を増やすが、formal run が `generations=2` であることを検査しない。

   成果物影響: `G=1` または feedback が実際には消費されない試行を、正式合成結果として三成果物へ流せる。

6. **C12 — real / 重大度: 致命的**

   関数名、属性名、別 blob に同名関数があることだけを見る。lookup 結果の同一性、calibration／allocation receipt、launch 前拒否、例外握り潰しを証明しない。

   成果物影響: resume・multi-process・未登録環境の測定が台帳へ混ざり、材料値と certified 選択が比較不能になる。

以下は現 evaluator の検査を終端まで通す最小型の偽装である。必要な別 blob は同名関数だけの stub、C11 artifact は schema を満たす dummy JSON で足りる。既存テストの `TOKEN_ONLY_C*` も同じ事実を実証している。

```python
# C01
def load_ratified_freeze(): return object()  # ratified blob との同一性なし
def _campaign_for(): return (1_000_000, 48)
def _perf_for(): return (1_000_000, 48)
def _descriptor_for(): return (1_000_000, 48)
def _run_workload():
    x = load_ratified_freeze()
    x.sha256; x.holdouts
    _campaign_for(); _perf_for(); _descriptor_for()
def run_trial(): _run_workload()
def main(): run_trial()

# C04
def mark_experiment_indeterminate(): pass
def forbid_trial_restart(): pass
def run_trial():
    if False:
        mark_experiment_indeterminate()
        forbid_trial_restart()

# C09 registry
def assert_campaign_layer3_chain(): pass
def accept_trial():
    policy = ("no-build", "certifying")
    if False:
        assert_campaign_layer3_chain()
    return policy

# C10 verifier
def read_and_verify_bytes(): pass
def verify_s8c_cross_binding():
    fields = (
        "input_payload_sha256", "raw_response_path", "raw_response_sha256",
        "provider_payload_sha256", "provider_envelope_sha256", "proposal_path",
        "proposal_sha256", "build_records", "bench_records", "artifact_refs",
        "source_refs", "admission_decision",
    )
    if False:
        read_and_verify_bytes()
    return fields

# C11
MAX_APPROVED_GENERATIONS = 2
def _validate_generation_budget(): pass
def apply_critic_feedback(): pass
def _run_workload():
    _validate_generation_budget()
    if False:
        apply_critic_feedback()
    return ("sample_plan_sha256", "cap_lift_sha256")
def run_trial(): _validate_generation_budget(); return _run_workload()
def main(): _validate_generation_budget(); return run_trial()

# C12
def run_trial():
    if False:
        contract = lookup()
        attest_and_build_receipt(contract)
        single_process_required(contract)
        contract.single_process
        contract.allow_resume
```

D96 は AST 固定が `if False`、alias、`getattr`、例外握り潰しを見逃すため不採用と明記している。例えば次も、名前・順序だけの検査を満たしながら validation failure を launch へ通す。

```python
try:
    applied = apply_critic_feedback(critic, source_metrics=metrics, source_generation=1)
    feedback = applied.planner_projection
    receipt = validate_planner_payload(
        payload, expected_critic_feedback=feedback, **expected
    )
except Exception:
    receipt = None
_invoke(payload=payload, validation_receipt=receipt, **invoke_args)
```

`_invoke` は receipt が `None` なら検証を省く。ほかにも import 後の同名関数再束縛、恒真な `assert verify() or True`、dummy call と実 call の `getattr` 分離が成立する。未実装の AST checker がこれらを全拒否すると仮定して SATISFIED を事前決定してはならない。

## 3. 条件 11 の証拠の弱化

1. **exact `G=2` は存在しない — real / 重大度: 致命的**

   `MAX_APPROVED_GENERATIONS = 2` は上限である。`_validate_generation_budget` は `1 <= generations` を受理し、CLI 既定は明示的に `1` である。manifest schema にも generation field はなく、trial は `trial_id/arm/holdout/campaign_id` のみである。

   閉じた critic 射影は generation 2 以降でしか実行されないため、G1 なら射影コードが存在するだけで未使用となる。段 2 案の「定数が exact 2」「三入口で validator」を満たしても G1 は通る。

   成果物影響: G1 trial を台帳に束縛し、実質的に合成していない結果を材料レポートと certified 選択へ昇格できる。

2. **「既存 4 機構」は実質 4 つではない — real / 重大度: 高**

   - 定数と三入口 call は一つの「上限 validator」機構であり、独立な四証拠ではない。
   - generation projection と production wiring は実在する一つの機構。
   - negative control は開発テストであり、commit 証拠として `probe.evidence()` に入らない。
   - 現テストでは mutation も `EVIDENCE_UNDEFINED` のままで、現在は赤を出さない。

   したがって production 証拠は実質二系列の code blobであり、独立証拠を含めても三つ未満である。

   成果物影響: 単一系統の source-shape 誤判定が、そのまま三成果物すべての誤認証へ伝播する。

3. **閉じた射影の実在 — refuted / 重大度なし**

   `_CRITIC_KEYS`、固定 diagnostics、`apply_critic_feedback`、`_validate_critic_projection`、expected-tree 照合は実在し、現 production にも配線されている。

   ただし「完全に静的検査できる」は **real / 重大度: 高の欠陥**。D96 がその一般 AST 証明を否定しており、`prior_reverse` は planner projection とは別に proposal と generation driver へ渡る。D410 自身も injection seam と意味的非干渉を保証外にしている。

   成果物影響: 射影実装の存在自体は三成果物を傷つけないが、それだけを C11 全体の証明として使うと未検査チャネルを正当化する。

4. **sample-plan / cap-lift の証明力喪失 — real / 重大度: 高**

   sample-plan は少なくとも generation 下限、feedback 必須、sample count を表す。cap-lift は下限、入口集合、ruling reference を表す。現 evaluator の hash binding は文字列存在だけで弱かったが、削除すると下限と裁定 trace 自体が消える。新案の上限 validator はこれらの代替ではない。

   成果物影響: 何件・何世代をどの裁定で正式実行するかを台帳から再構成できず、材料レポートと certified 選択の preregistration 証明が弱くなる。

## 4. 恒真な保証

1. **現 `test_satisfiable_predicate_requires_negative_control` — real / 重大度: 高**

   `machine_checkable == SATISFIABLE_CONDITION_IDS == frozenset()` なので、後続 loop は 0 回である。negative control が実在・発火することを現在は一件も検査していない。

   成果物影響: negative control 不在でも開発ゲートが緑になり、将来の三成果物へ未検出の緩和を運ぶ。

2. **現 `test_noop_and_token_only_fixtures_never_satisfy` — real / 重大度: 高**

   六つの baseline と mutation の両方に同じ `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` を期待する。mutation が何も壊さなくてもテストは通るため、現在は KILL を証明しない。

   成果物影響: 「負例あり」という記録が実際の拒否能力を持たず、三成果物の信頼根拠にならない。

3. **C02/C03/C05/C06/C07/C08 の control — real / 重大度: 高**

   `nc_c02_*`、`nc_c03_*`、`nc_c05_*`、`nc_c06_*`、`nc_c07_*`、`nc_c08_*` は JSON 内の文字列としてしか存在しない。`test_s8c_preregistration*.py` に mutation case はない。loader も ID の正規表現と条件番号だけを検査する。

   成果物影響: 半数の条件は「negative control を持つ」という契約表示だけで、台帳・報告・選択の境界を守らない。

4. **提案後の C11 control も不十分 — real / 重大度: 致命的**

   cap を 2 から 1 へ戻す mutation は上限しか検査しない。保持すべき重要な反例は「cap=2 のまま、validator と CLI／manifest が G1 を受理する」である。プランの追加 mutation 群にも G1、同名 shadow、catch-and-continue、receipt=None、alternate invocation path がない。

   成果物影響: 提案テストが全部通っても、G1 の正式試行が三成果物へ混入できる。

5. **`SATISFIABLE_CONDITION_IDS` — real / 重大度: 中**

   production からは参照されず、テスト用の手書き metadata である。実際の発効は core が status を直接見る。集合定数を `{"C11"}` にしても、C11 の意味が証明されたことにはならない。

   成果物影響: 宣言と実 evaluator の意味がずれても、宣言自体は三成果物を防護しない。

6. **g3 の `ruling_reference=D96` テスト — real / 重大度: 高**

   一般手続 D の文字列を固定するだけで、本改訂固有の新 D の存在・内容対応・同時 land を検査しない。謳う「新しい設計判断との束縛」は発火しない。

   成果物影響: 内容裁定のない契約改訂を根拠に正式三成果物を発行しうる。

## 5. fail-closed の破れ

1. **現 HEAD の例外経路 — refuted / 重大度なし**

   - `_evaluate_undefined` の最後の `else` は `EvidenceContractError` を raise する。
   - それは `PredicateRegistry.evaluate_all` で `ERROR` に変換される。
   - `EvidenceContractError`、`PreregistrationError`、その他 `Exception` はすべて `ERROR` 側。
   - core の `all_satisfied` は 12 件すべてが exact enum identity `SATISFIED` の場合だけ真。

   読取不能、未定義、通常例外が現在のコードで充足側へ倒れる具体経路は見つからなかった。

   成果物影響: この限定面では、読取失敗だけで試行台帳・材料レポート・certified 選択が発行されることはない。

2. **例外分類の潰れ — real / 重大度: nit**

   missing evaluator の `contract-machine-evaluator` や artifact JSON 異常を含む多くの `EvidenceContractError` が `BLOB_READ_ERROR` に潰れる。`PreregistrationError` は `.reason` なのに catch 側は `.reason_code` を見る。

   成果物影響: 受理は広がらないが、正式三成果物が出ない原因の診断と次の修正判断を誤らせる。

3. **「静的 reject が無かった」を SATISFIED とする経路 — real / 重大度: 致命的**

   現在は検査漏れがあっても末尾 `EVIDENCE_UNDEFINED` なので閉じている。P2 はこの最後の fail-closed 層を外し、未検出の alias、dead branch、例外握り潰し、G1 を充足として扱う。これは例外処理の fail-open ではなく、証明不足の fail-open である。

   成果物影響: 残条件が実装された時点で、証明されていない正式試行が三成果物へ直結する。

4. **core/evaluator 非凍結 — real / 重大度: 致命的**

   将来 commit は protected hash を変えずに evaluator や core を変更できる。live-byte equality は変更後 commit と checkout が一致すれば通る。従って g3 後も、未記録の acceptance mutation を機械的には止めない。

   成果物影響: freeze-valid を保ったまま全条件を満足扱いにし、三成果物を無裁定で発行できる。

## 6. 親の実測とプランの誤り

1. **M1 — refuted / 重大度なし**

   全 12 条件 false、6 evaluator が production dispatch されない、という測定はコードと一致する。

   成果物影響: 現状は正式三成果物の発行を止めている。

2. **M2 — real / 重大度: 致命的**

   private evaluator を現 HEAD に直接当てた一点測定から「受理集合は広がらない」へ一般化している。測ったのは一つの status vector であり集合包含ではない。C11 の artifact 差し替えと終端変更を含む wave 全体については、親自身が後段で受理拡大を認めており、記述も自己矛盾する。

   成果物影響: 将来の偽陽性を「HEAD で 0 件だった」ことにより見逃し、三成果物へ持ち込む。

3. **M3 — refuted / 重大度なし（現構造）**

   六つの末尾が undefined である事実は正しい。ただし `SATISFIABLE_CONDITION_IDS` は production gate ではなく、この二層性は終端を変更した瞬間に消える。

   成果物影響: 現在は止めるが、永続的 backstop として三成果物を守らない。

4. **M4 — real / 重大度: 致命的**

   「既存 4 機構」と「exact G2」が誤り。validator は G1 を受理し、CLI default も G1。negative control は現在発火せず、閉じた射影は G2 に入らなければ動かない。

   成果物影響: G1 を正式合成と誤認し、台帳・材料レポート・certified 選択を汚染する。

5. **M5 — refuted / 重大度なし（時系列実測）**

   D410 が g2 より先に着地していること、導入 commit で ruling heading を要求することは再確認できた。

   一方 P1 の `D96` 代用は **real / 重大度: 高**。一般手続を内容裁定として使っており、新 D との機械的な対応を失う。

   成果物影響: 三成果物の契約改訂 provenance が、本改訂を承認した決定へ到達しない。

6. **M6 — real / 重大度: 高**

   行位置と六つの case 登録は事実だが、「D96 の境界テストがある」という結論は過大。現テストは空集合 loop と undefined 同士の比較で、negative control の検出力を証明しない。

   成果物影響: 境界テスト済みという誤認が unsafe land を許し、後続三成果物へ伝播する。

7. **M7 — real / 重大度: 中**

   文字列 hit の棚卸しとしては有用だが、意味的 pin 閉包の証明ではない。特に新たな live evidence となる generation projection、evaluator semantics、C11 の formal generation binding が freeze 保護外である。D96 も AST consumer 閉包では証明できないと明記する。

   成果物影響: pin 済みと誤認した可変コードが、台帳・報告・選択の受理意味を後から変える。

8. **M8 — real / 重大度: 低**

   08:25 時点の四 wave との path 重複ゼロは snapshot としてのみ有効で、実装・land 時の非重複や意味的 consumer 競合を保証しない。

   成果物影響: 直接の三成果物影響はないが、競合 land による検査期待値の上書きを防ぐ根拠にはならない。

9. **段 2 プランの AST discharge — real / 重大度: 致命的**

   D96:4281-4284 が不採用とした方式を、C11 の SATISFIED 根拠に再導入している。プラン自身の「証明できなければ undefined に戻す」という fallback は正しいが、現時点の事実に照らすと、その fallback を発動すべきである。

   成果物影響: D96 が既知とする偽陽性を正式三成果物の入口へ戻す。

## 7. must-fix / nit の仕分け

must-fix:

1. P2b を採り、C11 は `EVIDENCE_UNDEFINED` のままにする。少なくとも現 AST 案で SATISFIED 化しない。
2. formal manifest／binding に generation budget を明示し、effective 8c admission が exact `2` 以外を拒否する consumer を実装する。cap 上限 2 で代用しない。
3. C11 の負例に G1、CLI default 1、manifest G1、dead branch、同名 shadow、catch-and-continue、receipt `None`、alternate invocation を追加する。
4. g3 は本改訂固有の新 D を参照する。採番順序を解けないなら P1c の先行 D land を選び、D96 を内容裁定の代用にしない。
5. evaluator、core、generation projection の受理意味を freeze 世代へどう束縛するかを裁定へ返す。少なくとも現状を「g3 が受理集合を凍結する」とは記述しない。
6. C03/C08 は C の単一親だけでなく、P の manifest blob が C で不変であること、C の差分が binding record に限定されることを契約・consumer・負例で固定する。
7. C02/C03/C05/C06/C07/C08 の ID を active negative control と呼ばない。実 mutation を実装するか、未実装であることを明示する。

nit:

- `EvidenceContractError` の reason mapping を `BLOB_READ_ERROR` 一色にしない。
- M8 は「確認時点の path 重複ゼロ」と限定して記録する。
- C03 の `static_only_note` にある「registry module 不在」は現 HEAD と不一致なので追随させる。

## 総括

親の「M2 より受理集合は広がらない」という一般化は棄却する。単一 HEAD の全件不充足は集合包含の証明ではない。  
最大の欠陥は、上限 2 を exact G2 と誤認し、G1 を受理する現実装を C11 の正例にしようとしている点である。  
閉じた critic 射影は実在するが、G1 では動かず、D96 が否定した AST 検査で完全 discharge はできない。  
現 HEAD の例外・未定義経路は fail-closed であり、この面の直接 fail-open は refuted。  
g3 の D96 参照と executable gate 非凍結は、将来の無裁定な受理変更を止めない。  
must-fix は P2b への退避、exact G2 の formal binding、固有 D 参照、非恒真な mutation control である。  
pytest は未実走であり、緑とは記録しない。