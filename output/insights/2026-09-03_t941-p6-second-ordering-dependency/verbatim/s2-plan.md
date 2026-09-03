## 変更面の実アンカー表

| 実アンカー | 今そこにあるもの | 何に変えるか |
|---|---|---|
| `orchestrator/campaign/reflux_p6_witness.py`（新規、想定 1–450） | 存在しない | ordered WAL の attempt 束縛、4 kind discriminator、cycle/permutation adapter、正規化、class-set、`P6NotDerived` / `P6NotApplicable` / `P6ContractError` 相当の witness 評価結果を持つ純粋 evaluator。`P6Derived` と `derive_p6_cut` は置かない |
| [reflux_result_evidence.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_result_evidence.py:594) | 各 projection record から `build_attempt_id` を取り出す | field が存在する record の明示的不一致だけを resolver で拒否し、`verify_done` に ID が無い場合を許容する。attempt の意味的束縛は新 evaluator に一元化 |
| [reflux_result_evidence.py:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_result_evidence.py:629) | `_resolve_ordered_wal()` が全 record の attempt ID 一致を要求する | ordered record 列と物理 byte 区間の一致だけを維持し、`build_start`/`abort` 区間一意性を後段 evaluator に渡す |
| [reflux_formal_consumer.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_formal_consumer.py:50) | result-evidence resolver の import | 新 witness evaluator の型と `evaluate_ordered_wal_evidence()` を追加 import |
| [reflux_formal_consumer.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_formal_consumer.py:812) | terminal の `candidate_attributable` / `truncated` / `witness_class_sha256s` を自己申告値として読む | ordered WAL の stage-qualified record から再導出し、3 field を導出値との完全一致検査へ変更。positive class-set 以外は FC07 |
| [reflux_formal_consumer.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/reflux_formal_consumer.py:1003) | `_validate_wal_outcomes()` 呼出し | expected attempt、workload、physical constraint を evaluator へ渡す結線に変更 |
| [reflux_origin_fixture_builder.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/reflux_origin_fixture_builder.py:39) | class digest を説明文字列の hash で固定 | 独立に作った cycle witness 正規形の literal golden digest に置換。production normalizer を期待値計算に使わない |
| [reflux_origin_fixture_builder.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/reflux_origin_fixture_builder.py:347) | `TriggerGateBinding` と自己申告だけの synthetic abort | `build_start` → `verify_done` → `abort` の stage-qualified record、実 `verify` 形状、構造化 G2 witness を生成。`verify_done.payload.anomalies` は整数のまま |
| [reflux_origin_fixture_baseline.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/reflux_origin_fixture_baseline.json:1) | 現 fixture の canonical hash/byte length | fixture 形状変更後の独立再計算値に機械更新 |
| [test_reflux_result_evidence.py:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_reflux_result_evidence.py:338) | 全 record が attempt ID を持つ順序検査 | `verify_done` の ID 欠落を resolver が許し、明示された異なる ID は拒否する境界を追加 |
| `orchestrator/tests/test_reflux_p6_witness.py`（新規、想定 1–500） | 存在しない | 8 正規化規則、4 kind dispatch、C-02 系、C-06〜C-10P の witness 層 calibration を独立 golden で検査 |
| [test_reflux_formal_consumer.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_reflux_formal_consumer.py:284) | helper が全 WAL record に attempt ID を注入 | stage/payload の実形状を維持し、`verify_done` 欠落・複数 interval を構成できる helper に変更 |
| [test_reflux_formal_consumer.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_reflux_formal_consumer.py:605) | 自己申告 class list が空なら FC07 という 1 ケース | 3 field 各々の虚偽、無効 witness、切詰め、ambiguous interval、lock/write fail-closed、derived class 不一致を FC07 で検査 |
| [test_reflux_formal_consumer.py:911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_reflux_formal_consumer.py:911) | consumer 内に `P6Derived` / `derive_p6_cut` が無いことを pin | 一切弱めず維持。新定義は別 module |
| `orchestrator/campaign/reflux_layer3_material.py`（新規、想定 1–280） | 存在しない | capability-bound ledger reader と result-evidence resolver を組み合わせ、Layer3 用の検証済み projection を返す独立 reader/verifier |
| [layer3_report.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/layer3_report.py:203) | WAL/whiteboard だけを一次配置として再走査 | 検証済み reflux projection が存在するときだけ、その `reflux:` refs も一次配置へ加える |
| [layer3_report.py:681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/layer3_report.py:681) | `build_report()` に reflux 入力が無い | optional な issued capability/client を追加し、新 verifier を呼ぶ。evidence が無い既定経路では既存出力 bytes を変えない |
| [layer3_report.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/layer3_report.py:788) | report に reflux 区画が無い | origin-bound のときだけ `reflux_origin_material` を追加。absence 時は `null` も出さず key 自体を省略 |
| [layer3_report.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/layer3_report.py:827) | accepted report が既存 `build_report()` だけを forward | 同じ optional capability/client を forward。ledger terminal を `certifying_input` の根拠にはしない |
| [layer3_schema.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/layer3_schema.json:22) | reflux 区画なし | historical v3 の読取互換を守る optional `reflux_origin_material` schema を追加 |
| [layer3_schema.json:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/layer3_schema.json:193) | `source_refs` が `wal|wb` のみ | origin-bound report に限り `reflux:<sha256>` を許可 |
| [test_layer3_report.py:1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_layer3_report.py:1367) | schema v3 と run required key の構造 pin | v3/run pin は維持し、reflux property が optional であることを追加 pin |
| [test_layer3_report.py:1408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/tests/test_layer3_report.py:1408) | originless report の形を検査 | reflux key 不在・既存 `source_refs` 不変を明示検査 |
| `orchestrator/tests/test_reflux_layer3_material.py`（新規、想定 1–350） | 存在しない | ledger/result-evidence の双方向対応、scope 三つ組、V-10 限界、Layer3 projection、evidence-present/no-capability 拒否を検査 |

`reflux_source_closure.py`、`reflux_ir.py`、`reflux_origin_ledger.py`、`reflux_origin_client.py`、`verifier/model.py`、`verifier/report.py` は reader/adapter の入力として使うだけで変更しない。指定された編集禁止 6 ファイルも変更面に含めない。

## 単位 1 の実装プラン

新 module の出力は P6 全体の実行結果ではなく、次の witness 評価結果とする。

- `WitnessDisposition.CLASS_SET`
- `WitnessDisposition.NOT_DERIVED` + `witness-truncated` / `witness-invalid` / `candidate-unbound` / `ambiguous-wal-binding`
- `WitnessDisposition.NOT_APPLICABLE` + `non-candidate-failure`
- `WitnessDisposition.CONTRACT_ERROR` + `unknown-witness-kind` / provisional `witness-kind-unavailable`

`P6Derived` は定義しない。negative disposition は外部的には契約の `P6NotDerived` / `P6NotApplicable` / `P6ContractError` に対応するが、`derive_p6_cut` が無い以上、P6 の4値結果そのものを名乗らない。

| 条項 | 新 module の想定位置 | 機械化 |
|---|---|---|
| SC-01 | `reflux_p6_witness.py:80–155` `bind_abort_attempt()` | ordered list を index 順に走査し、`build_start`/terminal `abort` の一意な区間、variant、env、workload、attempt を束縛 |
| SC-02 | `:156–245` `adapt_abort_evidence()` / `dispatch_witness_kind()` | discriminator の閉集合を `cycle` / `lock_coverage` / `write_intent` / `permutation` に固定。enum 変換不能は `P6ContractError(unknown-witness-kind)` |
| SC-03a | `:246–305` `_validate_cycle_shape()` | length、cycle txid 一意性、辺隣接、reason 非空、reason type/version shape、phenomenon、declared types を検査 |
| SC-03b | `:306–345` `_forward_rotations()` / `_choose_min_rotation()` | forward rotation だけを列挙し、canonical bytes の辞書式最小を選ぶ。reverse は候補に入れない |
| SC-03c | `:346–405` `_canonicalize_key_partition()` / `_canonicalize_versions_for_key()` | key 分割、version の存在、genesis、同値類、同一 key 内順序を保存 |
| SC-03d | `:406–450` `_derive_truncation()` / `_class_set()` | 全 anomaly を処理して sorted unique class-set を返し、cycle/permutation の切詰めを class 計算前に拒否 |

**構造化 witness と discriminator**

- wire/adapter seam の discriminator は exact `kind` とし、値は4種だけ。
- `cycle` は terminal `abort.payload.verify.anomalies[]` を `CycleWitness` に変換する。
- `permutation` は `integrity.permutation_violations` と `permutation_violation_details` から `PermutationWitness` を作る。
- `lock_coverage` / `write_intent` は counter の存在を検出するが、count-only object を「構造化 witness」とは名乗らない。既知 kind として dispatch した直後に `P6ContractError(witness-kind-unavailable)` とする。
- 未知 kind は enum 変換失敗を握りつぶさず `P6ContractError(unknown-witness-kind)`。
- build error、timeout、parse errorなど、`payload.verify` を持たない環境失敗は kind dispatch に入れず `P6NotApplicable(non-candidate-failure)`。

**lock/write の実経路**

1. `adapt_abort_evidence()` が `verify.integrity.lock_coverage_violations > 0` または `write_intent_violations > 0` を先に検出する。
2. closed discriminator でそれぞれ既知 kind に分類する。
3. 構造化 detail が無いため `witness-kind-unavailable` を返す。
4. `_validate_wal_outcomes()` は `CLASS_SET` 以外を FC07 にする。
5. したがって自己申告 `candidate_attributable=true` と class digest があっても通らず、cycle channel から integrity channel への移動で回避できない。

これは回避阻止を実装するが、4 adapter 各々の `P6Derived` 正例要件は満たさない。P6 は引き続き `NOT_IMPLEMENTED` である。

**permutation adapter と sample 上限**

`_adapt_permutation()` で以下の順に判定する。

1. `counts` の exact key、非負整数、合計が `permutation_violations` と一致することを検査。
2. `sample[].observation` の exact shapeを検査。
3. `permutation_violations > len(sample)` なら `witness-truncated`。単に `len(sample) == 5` では切詰めとしないため、ちょうど5件は受理可能、6件目が存在する場合だけ拒否する。
4. 非切詰め時は observation object を正準ソートし、重複を残す。`source_thread_hint` と `source_thread_hint_basis` は [report.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/verifier/report.py:58) が non-authoritative と明記するため class entropy から除外する。
5. canonical JSON bytes の SHA-256 を permutation class とする。

**設計 §3.3 の8規則**

| 規則 | 関数 | 実装内容 |
|---|---|---|
| 1 内部整合 | `_validate_cycle_shape()` | `length == len(cycle) == len(edges) >= 2`、隣接、reason 非空、type 値域 |
| 2 rotation | `_forward_rotations()` / `_choose_min_rotation()` | forward rotation のみの辞書式最小。逆向きを列挙しない |
| 3 txid | `_relabel_txids_by_position()` | concrete txid を捨て、rotation 後の位置 `0..n-1` を残す |
| 4 key | `_canonicalize_key_partition()` | traversal の first occurrence で `k0,k1,...`。同一/別 key の分割を保存 |
| 5 version | `_canonicalize_versions_for_key()` | absent、genesis `[1,0]`、同値類、同一 key 内の順序 rank を別々に符号化 |
| 6 reason | `_canonicalize_reasons()` | 正準ソートするが `set` 化せず重複件数を保存 |
| 7 phenomenon | `_derive_phenomenon()` | reason type から G0/G1c/G2 を再導出し、申告値と不一致なら `witness-invalid` |
| 8 `edges[].types` | `_validate_declared_edge_types()` | 元 reason 順の重複除去 type 列と照合するが、canonical class bytesには含めない |

C-02d は2-cycleの偶然対称を避け、3-node・辺ごとに異なる reason を持つ fixture で方向非同一性を pin する。

**`_validate_wal_outcomes()` の正確な差分**

現在は rejected branch で次を行う。

- terminal 自己申告が `candidate_attributable is True`
- terminal 自己申告が `truncated is False`
- terminal 自己申告 class list が `[physical_result.constraint_sha256]`

変更後は次の順になる。

1. terminal 自己申告を一切 evaluator 入力に渡さない。
2. ordered stage record、expected attempt、result-evidence の workload だけから `WitnessEvaluation` を導出。
3. 自己申告3 fieldについて、型を exact 検査したうえで導出 projection と個別に完全一致させる。
4. 一致しても、導出 disposition が `CLASS_SET`、`candidate_attributable=true`、`truncated=false` でなければ FC07。
5. 導出 class-set がちょうど `[physical_result.constraint_sha256]` でなければ FC07。
6. 複数 anomaly は全件正規化後の class-setを比較し、先頭1件へ畳まない。

**SC-01 attempt 束縛**

- `bind_abort_attempt()` は `enumerate(records)` で順序を保ち、expected attempt を持つ `build_start` と terminal `abort` の候補区間を列挙する。
- 0区間は `candidate-unbound`、2区間以上、nested start、別 attempt の terminal 混入は `ambiguous-wal-binding`。
- 区間内の stage record について variant/env が一意で、terminal abort の workload と対応する最後の `verify_done.payload.workload` が一致することを要求する。
- `verify_done.payload.anomalies` は整数としてのみ読み、対応する `abort.payload.verify.anomaly_count` と照合する。
- 現在の [pipeline.py:1485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t941-p6-mechanization/orchestrator/campaign/pipeline.py:1485) では `verify_done` に `build_attempt_id` が存在するが、これは補助的整合検査にだけ使い、束縛の根拠にはしない。
- `records_by_stage()` は stage ごとの last-wins により、先行 attempt、先行 verifier pass、区間境界を消すため使わない。

## 単位 2 (V-12) の実装プラン

結線は次の一方向にする。

`layer3_report.py` → 新規 `reflux_layer3_material.py` → capability-bound `OriginLedgerClient` + `reflux_result_evidence` resolver

Layer3 本体は ledger の意味検査を持たず、新 verifier が返した exact dataclass を投影するだけにする。

**reader/verifier の動作**

- `campaign_dir/reports/reflux-result-evidence/` が無く、capability/client も無ければ `None` を返す。既定 report bytes は不変。
- evidence があるのに issued capability が無ければ拒否する。
- capability がある場合は `require_origin_ledger_client()` を通し、raw `origin_id` や caller-selected store を受け取らない。
- `read_origin()` と `read_sealed_batches()` で ledger を読む。
- evidence file を canonical parseし、deterministic path、raw digest、ordered WAL/provenance referenceを `resolve_result_evidence_batch()` で検査。
- `(authority_blob_sha256, origin_id, cell_key)` を全 record と capability で一致させる。
- ledger の non-tombstone member と evidence recordを digest、batch/query/replicate、wire、outcome、constraint で一対一対応させる。tombstone は record 不在を要求する。
- reportへ渡す値は、scope三つ組、ledger state/counters、batch/member行、evidence ref、V-10保証限界だけ。

origin-bound report にだけ以下を追加する。

```text
reflux_origin_material = {
  scope,
  ledger_state,
  batches,
  assurance_limits: {
    ledger: "commitment-and-structure-only",
    content_addressing: "claimed-byte-equality-only",
    writer_authentication: "not-provided",
    physical_execution: "conditional-on-trusted-harness-sole-writer"
  }
}
```

ledger の `terminal_status="certifiable"` は表示可能だが、`certifying_input`、acceptance receipt、certified selection の判定には一切使わない。

**[T-326] 裁定 (b) との両立**

両立すると判断する。

- 既存 `variants` / `runs` / `verifications` / `rejects` / `aborts` の深い一致条件は変更しない。
- ledger/result-evidence の意味検査はすべて新 verifier に置く。
- `layer3_report.py` は exact 型の検査済み projection を一次配置と `source_refs` に含めるだけ。
- originless 経路では field 自体を出さず、既存 report bytes と受理集合を維持する。
- evidence-present 経路を以前どおり無視することは V-12 未結線の継続なので、そこだけ新 verifier 必須に狭める。

裁定 (b) を「本体から新 verifier を呼ぶこと自体も禁止」と読む場合は両立しない。その場合の代案は別 renderer entrypoint だが、既存 renderer が evidence を無視し続けるため V-12 を満たさない。親の provisional 読みを採るのが妥当である。

## 受理集合の変化 (D96 手続)

| 新たに拒否する群 | 今日通る具体例 | 実装後 |
|---|---|---|
| stage/verify のない自己申告 projection | 現 fixture の `records=[TriggerGateBinding, {"kind":"abort","candidate_attributable":true,"truncated":false,"witness_class_sha256s":[constraint]}]` | attempt/source witnessを導出できず FC07 |
| class digest の協調改変 | terminalと `physical_result.constraint_sha256`、ledger memberをすべて `"e"*64` に揃える一方、実 G2 witnessは不変 | 正規化 classが `"e"*64` と異なり FC07 |
| cycle 切詰めの虚偽 | `total_cycles=2`, `anomaly_count=1`, `len(anomalies)=1`, 自己申告 `truncated=false` | 導出 `truncated=true` と不一致、FC07 |
| permutation sample 切詰めの虚偽 | `permutation_violations=6`, `sum(counts)=6`, `len(sample)=5`, 自己申告 `truncated=false` | `witness-truncated`、FC07 |
| invalid cycle の自己認証 | anomaly の `length=3`, `cycle=[10,20]`、自己申告 classとphysical constraintを一致 | `witness-invalid`、FC07 |
| ambiguous attempt | 同一 expected ID の `build_start` を2区間置き、最後の abort自己申告を整合させる | `ambiguous-wal-binding`、FC07 |
| lock/write の素通り | `verify.integrity.lock_coverage_violations=1` または `write_intent_violations=1`、自己申告 `candidate_attributable=true` と任意 class | 既知 unavailable kindとして FC07 |
| evidenceを置いただけのLayer3 campaign | `reports/reflux-result-evidence/.../*.json` があるが issued capability/clientなし。現在は `artifact_refs` に載るだけ | V-12 readerが拒否 |
| ledger/evidence 不一致のLayer3 campaign | evidence の `query_ordinal=0` を ledger member 1 に対応させる、または scope の `cell_key` だけ変更 | 新 verifierが拒否 |
| digestの通る偽 referent | record自身はcanonicalだが `ordered_wal_ref.sha256` と取得bytesが不一致 | content-addressed resolverで拒否 |

有効な構造化 witnessから導出した3 fieldと自己申告が一致する既存入力は引き続き `P6Unavailable` まで到達する。`derive_p6_cut` が無いため non-aborted terminal が新たに受理されることはない。

## calibration corpus の設計

| case | 本 wave での到達性 | 入力と期待 |
|---|---|---|
| C-01 | **full caseは到達不能** | 有効G2から class-setを得てformal consumerが `P6Unavailable` に到達する witness 部分だけ実施。`P6Derived`、`B`、`marginal_keys` は scope 外 |
| C-02 | **witness部分のみ到達** | C-01のcycle/edgesを同方向rotationし、同じ class SHA。禁止集合一致は `derive_p6_cut` 不在で検査しない |
| C-02b | 到達可能 | 同一keyを2keyへ分割し、C-01と異なる class SHA |
| C-02c | 到達可能 | version等値、genesis、presence、順序のいずれか1つだけを変え、異なる class SHA |
| C-02d | 到達可能 | 3-node非対称 witness の辺方向だけを反転し、異なる class SHA |
| C-02e | 到達可能 | 同一reasonを1件増やし、重複度保存により異なる class SHA |
| C-06 | 到達可能 | cycle: `total_cycles=2/anomaly_count=1/len=1`、または permutation: count 6/sample 5。`P6NotDerived(witness-truncated)` |
| C-07 | 到達可能 | length不一致、辺隣接不一致、空reason、不正type、phenomenon/types不一致の各単独変異。`P6NotDerived(witness-invalid)` |
| C-08 | 到達可能 | dispatcher seamへ `kind="future-kind"`。`P6ContractError(unknown-witness-kind)` |
| C-09 | 到達可能 | `abort.payload.reason="trace-timeout"`、`payload.verify`なし。`P6NotApplicable(non-candidate-failure)` |
| C-10L | 到達不能 | raw counterしかなく構造化正例が無い。known unavailableとして fail-closed |
| C-10W | 到達不能 | C-10Lと同じ |
| C-10P | **witness部分のみ到達** | count 1〜5かつsample全件の permutation witnessは class-setまで到達。`P6Derived` と nonempty marginal setup は scope 外 |

**偽物の最低棄却集合**

| 偽物 | 本 wave の対応 |
|---|---|
| 空 handler | C-06〜C-09 の exact resultを返せず落ちる |
| 常に同じ verdict | C-06/C-07/C-08/C-09 の kind/code差で落ちる |
| blanket `P6ContractError` | C-06/C-07/C-09 で落ちる |
| 未知 kind を無視 | C-08 で落ちる |
| 常時 `NOT_CLAIMED` | 状態分類・C-11がscope外なので本 wave単独では棄却不能 |
| 全 integrity kindを一律エラー | C-10Pのwitness正例では部分的に落とせるが、C-10L/Wの`P6Derived`正例が無いため契約全体としては棄却不能 |
| case ID暗記 | evaluatorへcase IDを渡さず、C-02変形で固定表暗記を検出。ただし独立検査者hidden caseは認定手続scope外 |
| enforcer no-op | C-13/admissionがscope外なので棄却不能 |
| 形状射影の表駆動 | C-02b〜C-02eで落ちる |

したがって、この corpus は witness 層の機械検査には使えるが、D156 の accreditation corpus 完了を名乗れない。

## 変異事前登録の候補

| 条項ID | 変異対象 | 破壊変異 | 対応case | 無変異期待 | 変異後観測 | KILLED判定 |
|---|---|---|---|---|---|---|
| SC-01/stage | stage-qualified reader | `verify_done`整数をwitness listとして読む | C-01/C-07 | case PASS | shape/error不一致でFAIL | PASS→FAILのみ |
| SC-01/variant | interval binding | variant一致検査を削除 | C-01派生 | mixed variantを拒否 | class-setへ進みFAIL | PASS→FAILのみ |
| SC-01/env | interval binding | env一致検査を削除 | C-01派生 | mixed envを拒否 | class-setへ進みFAIL | PASS→FAILのみ |
| SC-01/workload | interval binding | abort/verify workload照合を削除 | C-01派生 | mismatchを拒否 | class-setへ進みFAIL | PASS→FAILのみ |
| SC-01/attempt | interval binding | `records_by_stage()` last-winsへ置換 | ambiguous C-01派生 | `ambiguous-wal-binding` | 末尾attemptを選びFAIL | PASS→FAILのみ |
| SC-02/cycle | cycle adapter | cycle branchを空にする | C-01 witness部 | class-set | error/empty | PASS→FAILのみ |
| SC-02/lock | lock discriminator | counterを無視する | C-10L | known unavailable | non-candidate扱い | full case不在のため現waveでKILLED不可 |
| SC-02/write | write discriminator | counterを無視する | C-10W | known unavailable | non-candidate扱い | full case不在のため現waveでKILLED不可 |
| SC-02/permutation | permutation adapter | details branchを空にする | C-10P | class-set | error/empty | witness部分PASS→FAIL。full caseでは保留 |
| SC-02/unknown | discriminator | defaultをignoreにする | C-08 | ContractError | 別結果/無出力 | PASS→FAILのみ |
| SC-03a/length | shape validator | length比較を恒真化 | C-07 | NotDerived invalid | class-setへ進む | PASS→FAILのみ |
| SC-03a/adjacency | shape validator | from/to照合を削除 | C-07 | NotDerived invalid | class-setへ進む | PASS→FAILのみ |
| SC-03a/reason-count | shape validator | 空reasonを許す | C-07 | NotDerived invalid | class-setへ進む | PASS→FAILのみ |
| SC-03a/reason-type | shape validator | type allowlistを削除 | C-07 | NotDerived invalid | class-set/unknown値 | PASS→FAILのみ |
| SC-03a/phenomenon | phenomenon check | 申告値をそのまま採用 | C-07 | NotDerived invalid | class-setへ進む | PASS→FAILのみ |
| SC-03a/edge-types | types check | `edges[].types`を検査しない | C-07 | NotDerived invalid | class-setへ進む | PASS→FAILのみ |
| SC-03b/rotation | rotation chooser | rotation正規化を削除 | C-02 | 同じclass | 異なるclass | PASS→FAILのみ |
| SC-03b/direction | rotation chooser | reverseも候補へ加える | C-02d | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03b/txid-discard | txid relabel | concrete txidをclassへ残す | C-02 txid-renaming | 同じclass | 異なるclass | PASS→FAILのみ |
| SC-03b/position | txid relabel | 全positionを同一値へ畳む | C-02d | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03c/key | key partition | 全keyを`k0`へ畳む | C-02b | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03c/version-presence | version normalizer | absent/presentを同一視 | C-02c | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03c/genesis | version normalizer | `[1,0]`を通常rankへ畳む | C-02c | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03c/version-equality | version normalizer | 同値類を各出現別rankにする | C-02c | 同値関係に応じたclass | 誤分離 | PASS→FAILのみ |
| SC-03c/version-order | version normalizer | version順序を捨てる | C-02c | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03b/reason-sort | reason canonicalizer | 入力順を残す | C-02 reason-permutation | 同じclass | 異なるclass | PASS→FAILのみ |
| SC-03b/reason-multiplicity | reason canonicalizer | `set`化する | C-02e | 異なるclass | 同じclass | PASS→FAILのみ |
| SC-03d/class-set | class-set builder | anomalies先頭1件だけ処理 | multi-anomaly C-01派生 | 全class集合 | 1class欠落 | PASS→FAILのみ |
| SC-03d/cycle-truncation | truncation detector | total/count比較を恒真化 | C-06 cycle | NotDerived truncated | class-setへ進む | PASS→FAILのみ |
| SC-03d/permutation-truncation | permutation adapter | count/sample比較を削除 | C-06 permutation | NotDerived truncated | 部分sampleをclass化 | PASS→FAILのみ |

§6規則4を accreditation に今適用すると、C-10L/W の positive mutationは確実に除外対象になる。さらに C-01/C-02/C-10P の full `P6Derived` verdictを必要とする行は、本 waveだけでは accreditation用KILLEDを確定できない。一般条項を削って認定するのではなく、認定を保留し `NOT_IMPLEMENTED` を維持する。SC-08a/b・SC-12はscope外であり、実装・変異とも本表へ入れない。

## 分割案

| 子 | 排他所有ファイル |
|---|---|
| 子 A — 単位1 | 新規 `reflux_p6_witness.py`、`reflux_formal_consumer.py`、`reflux_result_evidence.py`、`reflux_origin_fixture_builder.py`、`reflux_origin_fixture_baseline.json`、`test_reflux_p6_witness.py`、`test_reflux_result_evidence.py`、`test_reflux_formal_consumer.py` |
| 子 B — 単位2 | 新規 `reflux_layer3_material.py`、`layer3_report.py`、`layer3_schema.json`、新規 `test_reflux_layer3_material.py`、`test_layer3_report.py` |

producer/consumer 契約は次のように寄せる。

- witness型・normalizer・result-evidence attempt projection・formal consumerはすべて子A。
- Layer3用のledger/result-evidence照合・report projection・schemaはすべて子B。
- `result-evidence/v1` の9-key schema自体は変更しない。子Bは既存public parse/resolve APIを読むだけなので、単位間でschema編集を分担しない。
- fixture builderは子A所有。子Bはimportしてよいが編集しない。
- `reflux_origin_ledger.py` / `reflux_origin_client.py` は両子ともread-only。
- insightとworklogは子に分けず、親が統合後に1本ずつ記録する。

## 総括

実装・テスト差分はおよそ `10^3` 行、概算1,300〜1,800行である。内訳は単位1が900〜1,150行、V-12が400〜650行。子A/Bを並列化し、先に `result-evidence/v1` 非変更と report projection interface を固定すれば1 waveに収まるが、上限寄りである。

落とせるのは非規範的なtest helper共通化やreport表示上の重複fieldだけで、SC条項、3 field再導出、V-12、V-10限界、originless bytes不変は落とせない。それでも収まらなければ機能を削るのではなく、親wave内を2 commitへ分ける。V-12を別waveへ送るには[T-942]再裁定が要る。

| 前提 | 結論 |
|---|---|
| P1 | **狭い意味で支持**。`_validate_wal_outcomes()` の受理集合は実際に狭まり、自己申告だけで通るfixture群をFC07へ移せる。ただし帰納段/admission不在なのでP6の実効的generalized cutや認定は生まれない |
| P2 | **支持**。深い照合を新 verifierへ隔離し、Layer3本体をshallow projectionに限定すれば裁定(b)と両立する |
| P3 | **回避阻止について支持、SC-02充足について否定**。lock/writeを既知kindとしてFC07へ落とすため素通りは塞げるが、positive adapter要件は満たせない |
| P4 | **弱く支持**。約1.5千行を2子に排他分割すれば可能だが、単位1の正規化goldenとV-12 fixtureが膨らむと2 commit化が必要 |

親が段4で決める裁定パッケージ候補は次の3件である。

1. lock/write の既知未実装 codeを、推奨の `P6ContractError(witness-kind-unavailable)` とするか、別codeにするか。`unknown-witness-kind`へ偽装してはならない。
2. permutation classを、推奨の「authoritative observation multisetだけを正準化し、thread hintを除外」とするか。設計本文にはsort witness同値関係が未確定という記録があるため、採らない場合はpermutationもknown unavailableへ落とす。
3. [T-326] (b) を「新 verifierをLayer3本体から呼ぶshallow wiringは許す」と確定するか。許さない場合、V-12を満たす代案がなく[T-942]再裁定が必要。

帰納段、admission結線、全入口inventory、認定手続、`derive_p6_cut`、cap-lift、規律2の変更は本プランに含めない。テストは実走しておらず、緑は主張しない。