## 総括

親案 P1 は採らない。内容 witness を fd に先行出力しても、候補は `observation_fd` へ残りの正規列を直接追記して `_Exit(0)` でき、broker は長さと値域しか検査しないため、真の comparator 呼出し列を証明できない。
代わりに D825 が許した broker 側 `ptrace` 方式を採る。各呼出しの引数 witness と戻り値を broker が停止中の worker から採取し、候補には観測 fd を一切持たせない。
単位 2 は `s6_sort_sweep.CANDIDATES` と `STOCK_NAME` から exact な名前と comparator の権威集合を一度だけ機械導出し、freeze の生成側と検証側の双方へ束縛を入れる。
凍結済み 3 entry は静的照合で balanced=`sp_dd`、write-heavy/read-heavy=`sk_ad` が全て現行 `CANDIDATES` と byte exact 一致した。freeze SHA-256 も manifest の `354f...f516` と一致しており、bytes は変えない。
現行 v4 contract ID は repo 全域の `rg --no-ignore` で生きた成果物が 0 件だった。現れたのは独立 test golden だけなので legacy-v4 loader は追加しない。
この dispatch では実装も pytest 実走も行っていない。

## 単位 1 のプラン

- `orchestrator/campaign/sort_swo_oracle.py:47-57`
  - `PROTOCOL_VERSION=4`、`CONTRACT_VERSION=5`、`_MAGIC=b"IZSWO4\0\0"` に上げる。
  - `_HEADER` は `=8sIIIIIIIII` のまま、`_RECORD_SIZE = _HEADER.size + N*N` も維持する。最終 frame の形は変えず、新しい reject detail を既存の `witness_lhs`、`witness_rhs`、`detail_value` に載せる。
  - なぜそこか: wire identity と contract ID の機械導出元であり、旧 broker と新 broker の取り違えを header で閉じるため。

- `orchestrator/campaign/sort_swo_oracle.py:89-93`
  - `SORT_SWO_GUARANTEE_BOUNDARY` を次の意味へ変更する。
    - `guarantees[...]` に `reported-relation-matrix-is-comparator-true-relation` を移す。
    - `does-not-guarantee[...]` には有限 corpus PASS が任意入力上の SWO 証明ではない点だけを残す。
  - なぜそこか: D1271 で閉じる exact field であり、この文字列の SHA-256 が contract components に含まれるため。

- `orchestrator/campaign/sort_swo_oracle.py:764-891`
  - worker TU に、候補実行前の calibration と各比較直前・直後の trap helper を追加する。
  - logical witness は lhs/rhs それぞれについて:
    - `canonical_id: uint8_t`: `_CORPUS_MANIFEST` と `_TUPLE_BODY_MANIFEST` が表す全 semantic field の exact 比較から得る 0..17、非一致は 255。
    - `object_address: uintptr_t`: calibration 時に broker が保存した実 `WriteElement<Tuple>` address と照合する。
    - `sequence: uint16_t`: 0..647。
  - 比較前 witness の論理幅は 20 bytes、すなわち address 8 bytes x 2、canonical ID 1 byte x 2、sequence 2 bytes。これは fd へ書かず、x86-64 ABI register に載せて `int3` trap で broker に採取させる。
  - 戻り値は comparator の直後に bool 1 byte相当と sequence 2 bytes相当を別 trap で採取する。
  - なぜそこか: candidate TU 内の writable snapshot を信頼せず、候補実行前に broker が取得した address表と親の canonical corpus を基準にできるため。

- `orchestrator/campaign/sort_swo_oracle.py:892-959`
  - `active_order`、`relation`、`observation_fd`、`observation_count`、`emit_bool` を関係行列経路から除く。
  - `sort(...)` は各要素参照を取得した直後、comparator 呼出し前に before-trap、戻った直後に after-trapを通す。
  - `active_write_set` と `sort_called` は既存 call contract 用に残せるが、正しさの根拠には数えない。
  - なぜそこか: P1 の致命点は候補が `observation_fd` を直接使えることにある。観測 bytes の producer を broker だけへ限定する必要がある。

- `orchestrator/campaign/sort_swo_oracle.py:961-977,1149-1240`
  - corpus construction の順序は writable global ではなく `main` の local valueで決める。
  - candidate statement の直前に canonical 18 element の calibration trap を発火させ、broker が `canonical_id -> actual address` を保存する。
  - `_TU_SUFFIX` の observation count 判定は削除し、exact 648 comparison の判定を broker trace stateへ移す。
  - なぜそこか: calibration が候補より先なら、基準表は broker memory にコピーされた後は候補から変更できない。

- `orchestrator/campaign/sort_swo_oracle.py:1058-1135`
  - worker の seccomp から `SYS_write` 許可を除く。候補実行時 worker は観測 fd も final fd も所有しない。
  - `SYS_ptrace` は引き続き worker で禁止する。trace 関係は broker parent が worker の exec 前後に設定する。
  - なぜそこか: candidate 自身による正規 frame の偽造を構造的に消すため。

- `orchestrator/campaign/sort_swo_oracle.py:1250-1267`
  - `_BROKER_DETAIL_INPUT_WITNESS_MISMATCH` と `_BROKER_DETAIL_TRACE_PROTOCOL` を追加する。
  - input mismatch の `detail_value` は bit 0=lhs mismatch、bit 1=rhs mismatch とし、header の witness fields は親が期待した canonical pair を保持する。
  - なぜそこか: mismatch と trap順序異常を別理由にし、必須負例が単一理由で赤くなるようにするため。

- `orchestrator/campaign/sort_swo_oracle.py:1269-1387`
  - worker fd boundary は「worker の fd 集合が空」であることを正常条件に変更する。
  - `PTRACE_TRACEME`、exec stop、calibration trap、before/after trap の閉じた状態機械を broker helper として追加する。
  - trap RIP、trusted callsite の return address、sequence、before/after交互性、合計 648 回を exact 検査する。余分、欠落、順序逆転は trace protocol reject。
  - なぜそこか: candidate が trap helper を直接呼ぶだけでは正規呼出しとして受理されないようにするため。

- `orchestrator/campaign/sort_swo_oracle.py:1388-1464`
  - `_broker_frame` は worker の raw observation bytes ではなく、broker-owned の bool列と trace findingを入力にする。
  - witness が全件一致した場合だけ、現行と同じ first/second pass の repeat 検査と canonical matrix 組立を行う。
  - mismatch があれば matrix を受理せず、最初の pair と mismatch bitを final frame に載せる。
  - なぜそこか: comparator が出した bytes ではなく、broker が採取した結果だけから関係行列を作る信頼境界になるため。

- `orchestrator/campaign/sort_swo_oracle.py:1467-1603`
  - `_broker_main` の observation pipe 作成、read loop、workerへの observation fd 継承を削除する。
  - worker を完全に reap した後だけ final frame を `_broker_write_all` する既存順序は維持する。
  - なぜそこか: 条件 2「候補が出た bytes を取り消せない」を、より強い「候補は出力 bytes を一度も所有しない」に置き換えるため。

- `orchestrator/campaign/sort_swo_oracle.py:1606-1669`
  - 新しい ptrace、calibration、trace state helperを `_BROKER_SOURCE_FUNCTIONS` と broker semantics digest に全列挙する。
  - なぜそこか: helper を contract digest 外へ逃がさないため。

- `orchestrator/campaign/sort_swo_oracle.py:2122-2332`
  - `_run_matrix` は final frame の新 detail を `OracleRejectKind.MUTATION`、reason code `comparison-input-witness-mismatch` へ変換する。
  - `input_pairs` に期待 pair、`observations` に `broker-ptrace-input-witness`、lhs/rhs の ID/address match boolを載せる。
  - trace順序異常は別の `EXECUTION` finding にする。
  - なぜそこか: 規律 3 の「なぜ壊れたか」を、fault signalではなく比較入力の不一致として返すため。

- `orchestrator/campaign/sort_swo_oracle.py:47-64,893,1237-1239,1565-1577,2122-2249`
  - `_RUN_TIMEOUT_S=2.0`、CPU/AS/FSIZE/NOFILE limit は緩めない。
  - worker observation bytes は 648 bytesから 0 bytesになる。broker は 18 calibrationと before/after 648組を exact countする。
  - ptrace overhead を理由に wall timeout を上げない。正例が2秒内に通らなければ実装効率を直し、受理集合を広げない。
  - なぜそこか: timeout/resource gateの緩和を混ぜないため。

- `orchestrator/tests/test_sort_swo_oracle.py:32-169,202-248,285-313`
  - `sk_ad` を `s6_sort_sweep.CANDIDATES` の実値から取り、実 compileと `check_materialized_sort_swo` で PASS を確認する正例を追加する。
  - compile artifact 数の golden `6` は追加した実 TU 数へ更新する。
  - なぜそこか: stubではなく現行の正当 comparator が新境界を通ることを確認するため。

- `orchestrator/tests/test_sort_swo_oracle.py:379-510,682-700`
  - 負例は単一 sort 文の lambda captureで writableな shadow `OracleWriteSet` を事前構築し、初回 comparator 呼出しで `active_write_set` を shadowへ差し替え、次呼出しで元へ戻す形にする。
  - shadowは element順を入れ替えておき、faultやcall-count異常を起こさず、次の before-trapだけが input witness mismatchになるようにする。
  - `O._validate_single_sort_statement(statement) is None` を先に assertし、その後実 `_compile_verified`、`_evaluate_executable` を通して `MUTATION/comparison-input-witness-mismatch` を確認する。
  - なぜそこか: outer syntax gate、execution fault、observation countが先に赤くならない必須負例にするため。

- `orchestrator/tests/test_sort_swo_oracle.py:1780-2056,2080-2136,2200-2244`
  - broker source bundle、protocol semantics、contract literal、version tuple、TU文字列 assertを新構造へ更新する。
  - `observation_fd`、`emit_bool`、`Known residual` の旧 assertを除き、calibrationが candidate statementより前、trapが comparator前後、workerに `SYS_write`許可がないことを assertする。
  - なぜそこか: TUやcontractの大変更を独立再導出 goldenで固定するため。

## 単位 2 のプラン

- `orchestrator/campaign/sort_comparator_authority.py:1-110` 新規
  - `s6_sort_sweep.CANDIDATES` と `STOCK_NAME` だけから module import時に indexを構築する。comparator literalは再掲しない。
  - `name -> comparator | None` と `comparator -> name` の双方を作り、exact str型、空文字、名前重複、実装重複、stock名衝突を起動時に fail-closedにする。
  - 公開 API は `is_authorized_sort_comparator(value)`、`require_sort_comparator_binding(name, comparator)`、read-only mappingとする。
  - stockだけは comparator=`None` を正規形とする。`STOCK_IMPL_NOTE` は説明文であって実装ではないため、権威集合へ入れず、同文字列を comparatorとして渡したら拒否する。
  - なぜそこか: trigger軸と同じ「閉集合 membership + name/value束縛」を一箇所で機械導出するため。

- `orchestrator/campaign/s1_known_axes_freeze.py:27-30,82-177`
  - authority moduleをimportし、authority errorを `FreezeError` に変換する `_require_sort_name_comparator_binding` を追加する。
  - exact bytes一致とし、外側 whitespaceの同値化はしない。
  - なぜそこか: provenanceに記録された comparator bytesそのものを権威値に束縛するため。

- `orchestrator/campaign/s1_known_axes_freeze.py:483-505`
  - read-heavy経路で write-heavy provenanceの `entries.sk_ad.implementation` を得た直後、`("sk_ad", comparator)` の束縛を要求する。
  - なぜそこか: read-heavyの流用元が正しい文字列型でも、別候補または集合外文字列に差し替わる穴を閉じるため。

- `orchestrator/campaign/s1_known_axes_freeze.py:507-552`
  - balanced/write-heavyの main provenanceから comparatorを得た直後、`(best["name"], comparator)` の束縛を要求する。
  - なぜそこか: argmaxの nameと provenance implementationを同じ権威 indexに結ぶ生成側 gateだから。

- `orchestrator/campaign/s1_known_axes_freeze.py:803-830`
  - `_validate_schema` の workload loopで `sort_best` が Mappingであることを確認し、`record["name"]` と `record["comparator"]` を同じ helperへ渡す。
  - triggerの `system_gate`/`ident_all` 検査と並ぶ検証側 gateにする。
  - なぜそこか: 生成時だけ正しくても、保存済み freezeの coordinated tamperを検出できないため。

- `orchestrator/tests/test_s1_known_axes_freeze.py:40-65,85-109`
  - frozen 3 entry全てを `_validate_schema` と authority APIへ通し、balanced=`sp_dd`、write-heavy/read-heavy=`sk_ad` の exact comparator一致を確認する。
  - なぜそこか: 凍結 bytesを再発行せず、新検証層だけで現物が通ることを示すため。

- `orchestrator/tests/test_s1_known_axes_freeze.py:101-396` の同種 trigger testsの後
  - comparatorを集合外の有効な sort文へ置換した documentが拒否される負例を追加する。
  - balancedの name=`sp_dd` を維持したまま comparatorを正準 `sk_ad` へ置換し、membershipは通るが name束縛で拒否される負例を追加する。
  - read-heavy生成経路をmock provenanceで呼び、集合外文字列と `sk_ad`/別正準実装不一致が output組立前に拒否されることも確認する。
  - なぜそこか: verificationだけでなく `_sort_entry` 生成側が実際にloadした provenanceを検査することを固定するため。

- `orchestrator/tests/test_sort_comparator_authority.py:1-180` 新規
  - 15 comparatorとstockの正例、名前重複、実装重複、stock名衝突、`STOCK_IMPL_NOTE`拒否を検査する。
  - なぜそこか: import時 fail-closedとstock特例を freeze統合テストから独立して固定するため。

- `orchestrator/tests/test_frozen_artifacts.py:41-45,162-198`
  - manifest literalも freezeも編集しない。既存 `test_frozen_artifacts_match_manifest` を bytes不変の関門として使う。
  - なぜそこか: T-493は検証層追加であり、freeze migrationではないため。

## 波及と追随

編集 pathの所有は素集合に分けられる。

- 単位 1: `sort_swo_oracle.py`、`critic/digest.py`、`s8b_sort_swo_receipt.py` とその tests/fixture。
- 単位 2: 新 authority module、`s1_known_axes_freeze.py` とその tests。
- `s6_sort_sweep.py`、freeze JSON、`test_frozen_artifacts.py` は参照または検証対象で、編集しない。
- 同一 wave、同一受入枠にはまとめるが、実編集 fileの跨りはない。

contract consumerの追随は次の全件。

- `orchestrator/campaign/sort_swo_oracle.py:421-439,2610-2630`
  - result/receiptの current ID、TU hash、guarantee boundary exact一致は自動的に新値へ追随する。

- `orchestrator/campaign/s8b_sort_swo_receipt.py:1-10,114-130,140-177,219-231`
  - exact current ID/TU/boundary検査はimport定数で自動追随する。
  - 3箇所の docstringを「真の関係を保証しない」から新保証へ直す。field shape不変なので receipt schema v2は据え置く。

- `orchestrator/critic/digest.py:205-270,313-409,455-469,858-1048,1461-1526`
  - current loaderは新 IDへ自動追随。
  - current finding schemaへ `mutation/comparison-input-witness-mismatch` と `broker-ptrace-input-witness` を追加する。
  - v3/v2 legacy loaderは不変。v4 live成果物が無いので legacy-v4 generation、loader、rendererは追加しない。

- `orchestrator/campaign/s1_direct_comparison.py:279-290,673-710`
  - campaign identityと result exact checkは新 IDへ自動追随する。実コード変更は不要だがテストする。

- `orchestrator/campaign/p3_s4_loop_sort.py:175-229,267-274`
  - sort loopの exact result checkと campaign identityも自動追随。実コード変更は不要。

- `orchestrator/tests/s8b_floor_evidence_fixture.py:16-24,40-70`
  - fixtureはcurrent定数をimportしているため literal変更不要。新 receiptのID/boundaryを使うことを再確認する。

追随する既存 test/golden は以下。

- `orchestrator/tests/test_sort_swo_oracle.py:1780-2056`: source bundle、TU hash、contract ID、versionの独立 golden。
- 同 `:2080-2136`: TU文字列 assert群。
- 同 `:2200-2244`: broker/専用 fd境界と final frame検査。
- `orchestrator/tests/test_critic.py:98-114,126-232,1595-1650,1851-2070`: current contract golden、新 mutation finding、current/legacy世代分離。
- `orchestrator/tests/test_s8b_sort_swo_receipt.py:55-139,195-204`: exact boundaryとdocstring。
- `orchestrator/tests/test_p3_s4_loop_sort.py:344-394,688-689`: reject receiptとcampaign identity。
- `orchestrator/tests/test_s1_direct_comparison.py:499-564,979-1028,1126-1129`: receipt/result/config identity。
- `orchestrator/tests/test_p3_exploration_namespace.py:437-439`: current receipt stub。
- `orchestrator/tests/test_s8b_materialization.py:27-54,668`: portable receipt fixture。
- `orchestrator/tests/s8b_floor_evidence_fixture.py:16-70`: current ID/boundary fixture。
- `orchestrator/tests/test_s1_known_axes_freeze.py:85-109,277-443`: frozen documentの新 sort authority検査。
- `orchestrator/tests/test_frozen_artifacts.py:41-45,162-198`: known_axes freeze bytes不変。

現行 v4 IDの live artifact判定:

- 現行 ID exact検索と `sort-swo-v4-corpus2-protocol3-checker3-grammar1` prefix検索を、ignored fileを含む repo全域で実施した。
- live campaign、WAL、receipt、freezeは 0 件。
- hitは `test_sort_swo_oracle.py` と `test_critic.py` の独立 golden、およびproducer定義だけだった。
- よって legacy-v4 reader追加は不要。追加すると使われない新機構になりscope外でもある。

検証手順への D669 の影響:

- `test_sort_swo_oracle.py` は受入全走から恒久除外なので、acceptance成功だけでは単位 1を緑と判定しない。
- 実装者は `tools/run_tests.py` 経由の当該ファイル焦点走を別に実施し、その結果と「acceptance除外」を記録する。
- その後に関連 consumer tests、通常 acceptance、`check_codex_agents.py`、`check_docs.py`、commit後 provenance検査を行う。
- この plan dispatchではどれも実走していない。

## 変異事前登録の候補

1. `orchestrator/campaign/sort_swo_oracle.py:1388-1464` の新 input witness一致分岐
   - 無効化: lhs/rhs addressとcanonical IDの比較結果を常に一致へ固定する。
   - 期待して赤くなる node: `orchestrator/tests/test_sort_swo_oracle.py::test_cpp_e2e_rejects_active_write_set_redirect_with_parent_witness`
   - 単一理由性: 候補文は outer syntax、compile、SWO、call countを通り、witness mismatchだけが失われて誤PASSする。

2. `orchestrator/campaign/sort_comparator_authority.py:70-85` の comparator membership gate
   - 無効化: 集合外 comparatorの membership拒否だけを削る。name/value equalityは残す。
   - 期待して赤くなる node: `orchestrator/tests/test_s1_known_axes_freeze.py::test_validate_schema_rejects_out_of_authority_sort_comparator`
   - 単一理由性: document key、型、nameは正しいままで、集合所属だけを変異させる。

3. `orchestrator/campaign/sort_comparator_authority.py:86-100` の name/comparator equality gate
   - 無効化: 正準 comparatorの membershipは残し、nameに対応する値とのexact比較だけを削る。
   - 期待して赤くなる node: `orchestrator/tests/test_s1_known_axes_freeze.py::test_validate_schema_rejects_sort_name_comparator_mismatch`
   - 単一理由性: `sp_dd` と `sk_ad` は双方が権威集合内なので、赤の理由は束縛不一致だけになる。

## 未解決・親の裁定が要る点

- P1を撤回し、D825が既に示した broker `ptrace` 経路へ切り替える裁定が必要。P1のままでは fdへの正規 tail偽造を防げず、保証境界を「保証する」側へ移せない。
- 上記 ptrace設計を本 waveの「最小実装」と認めない場合、単位 1は実装へ進めない。P1を縮小実装して非保証fieldだけ消す案は採れない。
- guarantee boundaryの `does-not-guarantee` に有限 corpusの非普遍性を残す exact文言だけは親が固定してよい。protocolの保証内容と legacy-v4不要の判断には択一はない。