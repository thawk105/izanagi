```text
前提

必読資料はすべて読了した。読めなかった path はない。作業ツリーには変更を加えず、pytest も実行しない。実装後のテスト実測は親 wave が `tools/run_tests.py` 経由で行う。

今回の判断は、8b §10 が旧来の床値比較を置き換え、反復単位の対比を第3条件にしたことに基づく（docs/phase3-8b-descriptor-design.md:424、:441、:446）。8c 条件7も同じ3条件、3表、床 artifact の非入力を要求している（docs/phase3-8c-preregistration.md:231、:234、:237、:239）。

P1〜P4 の扱い

- P1 は維持する。C07 の `machine_checkable` は false であり（orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:300）、現在の `_MACHINE_EVALUATORS` にも C07 はない（orchestrator/campaign/s8c_preregistration_evidence.py:1806）。親 brief が報告した既存4テストの赤化と、契約に残る stale な `accept_trial` は、今 wave で契約や registry を反転させない根拠になる（s1-brief.md:29、s1-brief.md:45）。C07 は直接 evaluator を検査する静的準備段階に留める。
- P2 は維持する。床 artifact の検証は provenance のみとし、`judge` の引数または計算データに床値を渡さない（s1-brief.md:51、docs/phase3-8c-preregistration.md:239）。
- P3 は維持する。出力先は `publish_result_table` の caller が渡す。repo 内 path、condition-freeze の path、既定の出力ディレクトリを新規コードへ埋め込まない（s1-brief.md:55）。
- P4 は維持する。完全 block、schedule index、exact n、非有限値、パラメータ不正を判定不能にし、unpaired 退避や行削除を設けない（s1-brief.md:57、docs/phase3-8b-descriptor-design.md:446、:464）。

A. `orchestrator/campaign/s8c_result_judge.py` の新規設計

新規ファイルの予定 line anchor は次の通り。公開名は `__all__` と定義を検査し、`verify_floor_bytes`、`judge`、`publish_result_table` のちょうど3つに限定する（予定 `s8c_result_judge.py:1`、`:20`）。

1. 型と三値

- `_Status` を非公開 enum として定義し、値を `SATISFIED`、`UNSATISFIED`、`INDETERMINATE` の3つに固定する（予定 `s8c_result_judge.py:20`）。
- `None`、真偽値、例外の握り潰しを公式 status の代用にしない。
- `_JudgeResult` は、3要素だけの `conditions`、条件別 diagnostics、条件の連言から得た `conclusion` を保持する（予定 `s8c_result_judge.py:35`）。
- `conditions` の長さは常に3。`conclusion` は条件ではなく、3条件の結果から導出する値にする。`conclusion` を第4条件として表へ追加しない。

条件 ID は次の3つに固定する。

1. `on_off_prediction_difference`
2. `swapped_follow_through`
3. `paired_repeat_contrast`

2. `verify_floor_bytes`

予定 anchor は `s8c_result_judge.py:70`。

- caller が渡す `floor_refs` の各要素について、`path`、`sha256`、`env_tag`、`measurement_head` の4 field を必須にする。契約の対応 field は contract JSON に固定されている（orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:271、:274）。
- `path` は caller の入力として扱い、repo root や condition-freeze を補完しない。
- artifact の raw bytes を読み、一度の読み取り結果から SHA-256 を計算して参照値と比較する。
- `env_tag` と `measurement_head` は artifact の canonical metadata と参照値を比較する。ledger 側の field vocabulary は `_FLOOR_LEDGER_KEYS` に合わせる（orchestrator/campaign/s8b_holdout_admission.py:2072、:2079）。
- 参照の欠落、余剰、重複、型不正、hash 不一致、環境 tag 不一致、measurement head 不一致は検証失敗にする。
- 戻り値 `_VerifiedFloorEvidence` は path、hash、env tag、measurement head などの provenance だけを保持し、床値、floor score、floor threshold、raw measurement を含めない。
- `verify_floor_bytes` 内で bytes を読むこと自体は許可するが、その数値を `_JudgeResult` や `judge` の入力へ渡さない。

データフローは次の形に固定する。

    load_ratified_freeze()
        -> verify_floor_bytes(floor_refs)
        -> provenance receipt の保存または監査記録

    manifest + observations + prediction records + contrast params
        -> judge(...)
        -> 3条件の三値と diagnostics
        -> publish_result_table(...)

`judge` の引数には `floor_refs`、floor artifact の bytes、床値を含めない。したがって床値を変えても同一の manifest、observations、prediction records、params から得る judge 結果は不変になる。

3. 入力 binding と完全 block

予定 anchor は `s8c_result_judge.py:125` から `:245`。

- manifest の schedule row ごとに、holdout、cell、condition、replicate 添字を正規化する。
- observations 側の schedule index が manifest の row を指し、replicate 添字、cell identity、holdout identity が一致することを確認する。
- schedule index の欠落、重複、範囲外、非連続、別 cell への参照、manifest と observations の identity 不一致は判定不能にする。
- 各 holdout、各 cell、各 replicate の期待された組み合わせが全て存在することを確認する。完全 block でない場合は行を削除して対を作り直さない。
- manifest の宣言 `n` と observations の実測 replicate 数を exact 一致させる。`n` は各対象の count と一致しなければならない。
- on/off の pair は同一 holdout、同一 replicate、同一 block の schedule binding から作る。隣接行順や到着順で pair を作らない。
- unpaired fallback、欠測を別 replicate で補う処理、行削除後の再 pairing は実装しない。
- 欠測、重複、非有限値、complete block 不成立は、該当条件を `INDETERMINATE` にする。

4. パラメータ validator

予定 anchor は `s8c_result_judge.py:250`。

`_validate_contrast_params` を production の `judge` から必ず呼ぶ。

- `n` は bool を除く int、かつ `n >= 2`。
- `n` は manifest、observations、paired delta の全ての exact count と一致する。
- `delta_min` は指定された数値型で、有限、正、単位と向きが固定値に一致する。
- `sd_max` は指定された数値型で、有限、0以上、単位と向きが固定値に一致する。
- unit の空文字、未知の unit、符号反転、on-minus-off と異なる方向、NaN、正負 infinity は不受理にする。
- 不正な契約値を、個別の測定結果の不成立へ変換しない。validator の不成立は条件を判定不能にする。
- validator は private helper のままでもよいが、`judge` の実行経路から到達可能であることを単体テストで確認する。

これは §10.2 の n、delta_min、sd_max の要件に対応する（docs/phase3-8b-descriptor-design.md:464、:479）。

5. 3条件の評価

予定 anchor は `s8c_result_judge.py:285`。

- C1 は宣言された on/off prediction の差を、必要な holdout domain について評価する。完全な prediction record があり、差が宣言方向に存在すれば成立、完全で有効だが差がなければ不成立、入力不足や不整合なら判定不能にする。
- C2 は事前宣言された swapped mapping に対して、swap 後の prediction が対応する on/off の入れ替えに追従したかを評価する。swap mapping の欠落、余剰、identity 不一致は判定不能にする。
- C3 は同一 holdout、同一 replicate に結び付けた delta のベクトルだけで評価する。delta の向きは固定して `on - off` とする。
- 3条件の status を一つの条件 list に入れ、最後に `conclusion` を次で導出する。

  - 3条件が全て SATISFIED なら SATISFIED。
  - 1つでも UNSATISFIED があり、判定不能がなければ UNSATISFIED。
  - 判定不能があり、成立または不成立を確定できない場合は INDETERMINATE。

- 結論の導出を別の condition object、別の threshold、別の floor 条件にしない。

6. 反復単位の対比

予定 anchor は `s8c_result_judge.py:360`。

- 主量は有限な delta の平均と、有限な標本 SD の2つだけにする。
- 標本 SD は `n - 1` を分母にする。
- `mean_delta > delta_min` かつ `sample_sd <= sd_max` を成立条件とする。境界値はテストで固定する。
- 共分散、相関、相対差、散布比は diagnostics にのみ保存し、status の入力にしない。
- diagnostics が null または非有限でも、delta の平均と標本 SD が有効なら、それだけを理由に判定不能にしない。
- 走行内変動係数、個別 CV、session CV、個別 SD の合算を threshold にしない。既存 anomaly gate は measurement hygiene として扱い、performance evidence と混ぜない（docs/phase3-8b-descriptor-design.md:454、:462）。
- 同一 prediction が比較対象になる完全な入力は、C3 の不成立または成立を返し、判定不能にはしない。
- paired delta を作れない場合だけ判定不能にする。

7. `publish_result_table`

予定 anchor は `s8c_result_judge.py:475`。

caller から次の3出力先を受け取る。

- `descriptive_only`
- `official_status`
- `selection_evaluation`

各出力先は caller が渡す file-like object または path とし、repo 内の既定 path は定義しない。

各表は事前宣言された result cell 集合を共有する。

- manifest の predeclared cell set を読み、6 cell であることを確認する。
- 生成行の cell set と predeclared set を set equality で比較する。
- 欠落、余剰、重複、未知 cell、cell ID の正規化差は書き込み前に失敗させる。
- 欠落 cell を削除して表を完成扱いにしない。

表の意味を混ぜない。

- `descriptive_only` は6 cell 全ての raw values、within-config median、順位などを出す。性能成立の根拠には使わない。
- `official_status` は6 cell 全てについて三値の `official_status` を出す。公式性能は paired delta の平均と標本 SDだけに基づく。
- `selection_evaluation` は on/off、swapped、prediction と rank の対応を独立に出す。性能判定をこの表から再計算しない。
- 3表とも6 cell を保持し、表の有無や順位から公式 status を推測しない。

B. `_evaluate_c07` の設計

追加位置は既存 `_evaluate_c12` の後、`_MACHINE_EVALUATORS` の前（orchestrator/campaign/s8c_preregistration_evidence.py:1765、:1806）。

1. ReasonCode

既存の `FLOOR_JUDGE_CONSUMER_UNDEFINED` は、現在の非 machine-checkable C07 の fallback に使われている（orchestrator/campaign/s8c_preregistration_evidence.py:70、:1846）。これを変えず、新規 code を一つ追加する。

- `RESULT_JUDGE_CONSUMER_INCOMPLETE`
- 値は `result-judge-consumer-incomplete`
- 発火条件は、result judge の必須 entrypoint、floor ref field、3条件構造、3表の cell 構造のいずれかが静的に欠ける場合。
- ratified module または `load_ratified_freeze` 自体の欠落は既存 `RATIFIED_GENERATION_REFERENCE_ABSENT` とする（同ファイル:59）。

`REASON_CODES` は enum から生成されるため、enum 追加以外の登録は不要（同ファイル:89）。

2. 静的検査

`_ConditionProbe` の `python_kind`、`_functions`、AST node inspection、`PredicateResult` の既存骨格を使う（同ファイル:697、:739、:1461）。

C07 の契約から `consumer_requirement.entrypoints` を読み、3要素であることを確認する（contract JSON:294）。その3名について、result judge blob の top-level function が実在することを確認する。

- `verify_floor_bytes` が実在する。
- `judge` が実在する。
- `publish_result_table` が実在する。

`verify_floor_bytes` では live な AST 構造から `path`、`sha256`、`env_tag`、`measurement_head` の4 field が同時に扱われていることを確認する。死んだ token だけを有効な証拠にしない。

`judge` では次を確認する。

- `conditions` を表す mapping または record が存在する。
- condition 名の閉じた集合がちょうど3要素である。
- `conditions` の構造に床値比較用の第4条件がない。
- contrast parameter validator と complete-block validator に対応する live な呼び出し構造がある。

`publish_result_table` では次を確認する。

- `result_table.cells[*]` に対応する `cells` 構造がある。
- `descriptive_only`、`official_status`、`selection_evaluation` の3表 marker がある。
- exact cell-set validator に対応する live な呼び出し構造がある。

ratified reference blob について `s8b_ratified_freeze.py` を読み、top-level の `load_ratified_freeze` を確認する。契約の対応 field は `load_ratified_freeze().sha256` である（contract JSON:286、:291）。

3. reachability の扱い

`_ReachabilityExplorer`、`_reachable_calls`、`_declared_call` は既存 evaluator と同じ AST/reachability 境界を守るために使用可能だが、C07 では stale な `accept_trial` を実在する production entrypoint として証明しない（同ファイル:798、:420、:1474）。

理由は、親 brief が契約の `accept_trial` を現行 acceptance path と整合しない stale 名として確認しており、そこを根拠に C07 を machine evaluator へ昇格すると P1 と既存テストを破るためである（s1-brief.md:29、:43）。C07 は今回、entrypoint と構造の静的存在確認までとする。

4. 終端

- 必須構造が欠ける場合は `UNSATISFIED` と `RESULT_JUDGE_CONSUMER_INCOMPLETE`。
- ratified loader が欠ける場合は `UNSATISFIED` と `RATIFIED_GENERATION_REFERENCE_ABSENT`。
- 必須構造が揃っても、静的 evaluator は `SATISFIED` を返さず、`EVIDENCE_UNDEFINED` と `COMPLETION_PROOF_NOT_MACHINE_CHECKABLE` を返す。
- `_MACHINE_EVALUATORS` へ C07 を追加しない。現在の registry、machine id の bijection、C07 fallback の期待値を維持する（同ファイル:1806、:1815、:1821）。

C. テスト設計

1. `orchestrator/tests/test_s8c_preregistration_predicates.py`

既存の token-only fixture 群の近く（同ファイル:414、:548）に、`TOKEN_ONLY_C07` と ratified fixture を追加する。ただし `NEGATIVE_CONTROL_CASES` には追加しない（同ファイル:735）。

fixture は次の静的構造を持つ。

- 3公開関数の top-level definition。
- `verify_floor_bytes` 内の4 floor ref field。
- `judge` 内の3要素 condition 集合と `conditions` 構造。
- `publish_result_table` 内の `cells`、3表 marker、exact-set validator 呼び出し。
- `s8b_ratified_freeze.py` 内の `load_ratified_freeze` と `sha256`。

`_negative_control_case` にだけ `nc_c07_floor_or_result_cell_removed` 分岐を追加する（同ファイル:653）。変異版は、例えば `result_table.cells` 構造または3条件集合の一要素を除去する。既存の dict へ追加しない。

C07 用 probe helper は既存の `_walk_sources` と同様に `_ConditionProbe` を直接構築する（同ファイル:1757）。`evaluate_all` は呼ばず、次を直接検査する。

- token-only C07 を `_evaluate_c07` に渡すと `EVIDENCE_UNDEFINED` かつ `COMPLETION_PROOF_NOT_MACHINE_CHECKABLE`。
- `nc_c07_floor_or_result_cell_removed` の変異版を渡すと `UNSATISFIED` かつ `RESULT_JUDGE_CONSUMER_INCOMPLETE`。
- `_MACHINE_EVALUATORS` に7がない。
- `NEGATIVE_CONTROL_CASES` に C07 の key がない。
- 既存の snapshot で C07 が `FLOOR_JUDGE_CONSUMER_UNDEFINED` のままになることを壊さない（同ファイル:160）。

2. 新規 `orchestrator/tests/test_s8c_result_judge.py`

新規 judge module の公開 API が次だけであることを確認する。

    {"verify_floor_bytes", "judge", "publish_result_table"}

単体 fixture は、manifest の6 cell、各 replicate の schedule row、observations の schedule index、on/off prediction、swapped mapping、complete block を用意する。

必須境界テストは次の通り。

- manifest の `n` と observations の count の不一致は全該当条件が `INDETERMINATE`。
- 欠測 replicate、重複 replicate、非連続 replicate、wrong schedule index、cell identity 不一致は `INDETERMINATE`。
- 非有限 observation または delta は `INDETERMINATE`。
- `n=1`、bool の n、非有限 `delta_min`、0以下の `delta_min`、負の `sd_max`、未知 unit、逆向き direction は validator で拒否。
- `n=2` の SD が一つの差で計算され、分母が `n-1` になる。
- `mean_delta == delta_min` は、指定した strict direction では成立にしない。
- `sample_sd == sd_max` は、上限を含む仕様なら成立にする。
- covariance、correlation、relative difference、spread ratio を変えても status が不変。
- within-run CV を変えても status が不変。
- 行を削除した入力が別の valid pair として扱われない。
- 同一 prediction の完全 block は C3 の不成立となり、判定不能にならない。

3. floor 非入力の検証

同じ manifest、observations、prediction records、contrast params で `judge` を二度呼び、floor artifact の bytes または床値を変えても `_JudgeResult` が等しいことを確認する。

`verify_floor_bytes` の検証結果を呼び出し側で保持しても、それを `judge` に渡す経路が型または引数上存在しないことを確認する。floor の provenance は path、hash、env tag、measurement head のみで、judge の数値入力に変換されない。

4. result table の検証

- predeclared 6 cell と完全一致する入力は3表を生成する。
- cell 1つ欠落は失敗する。
- 未宣言 cell 1つ余剰は失敗する。
- 重複 cell は失敗する。
- 失敗時に3表の一部だけを書き残さない。
- `official_status` が3値以外を受け付けない。
- rank を変えても `official_status` は変わらない。
- `descriptive_only`、`official_status`、`selection_evaluation` が別出力である。
- output path を caller 側で変更でき、repo 内 path を参照しない。

D. 変更禁止と親 wave の受入確認

変更対象は新規 `s8c_result_judge.py`、`_evaluate_c07` と ReasonCode、C07 直接テスト、新規 judge/result table テストに限定する。

次は変更しない。

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の condition 7（:268、:300）。
- `output/s8c-preregistration/condition-freeze/`。
- `docs/phase3-8c-preregistration.md` §5 と §6。
- 既存テストの期待値、skip、削除、条件数。
- `_MACHINE_EVALUATORS` と `NEGATIVE_CONTROL_CASES` の C07 登録状態。

子では pytest を実行せず、緑とも記録しない。親 wave は実装後に `tools/run_tests.py` を通して関連テストを実測し、クラス3の完了検査として `python3 tools/check_codex_agents.py` と `python3 tools/check_docs.py` を実行する。実装と同じ commit 後に provenance 検査を行う。
```

## 総括

- 必読資料は全て読了し、ファイル変更と pytest 実行は行わない。
- `judge` は床値を入力にせず、3条件だけを三値評価する。
- 反復対比の主量は有限平均と標本 SD、SD の分母は `n-1` とする。
- floor 検証は path、hash、環境 tag、measurement head の provenance に限定する。
- C07 は直接静的検査するが `_MACHINE_EVALUATORS` へ登録しない。
- token-only は EVIDENCE_UNDEFINED、構造変異版は UNSATISFIED とする。
- result table は6 cellの完全一致と3表分離を検査する。