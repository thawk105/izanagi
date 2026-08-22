## 結論

静的検証の結果、D510 の項目6は未実装です。項目1〜4は該当実装を確認でき、項目5は部分実装、項目7は受理ゲートによる fail-closed として確認できました。pytest は実行していません。

## P1 独立再検証

| 項目 | 判定 | file:line 根拠 |
|---|---|---|
| 1. paired contrast | 実装済み | `orchestrator/campaign/s8c_result_judge.py:763-893` で同一 holdout・replicate の on/off をペア化し、平均差と標本標準偏差で判定。`docs/phase3-8b-descriptor-design.md:439-462` と一致。 |
| 2. ルール・型・有限性・符号 | 実装済み | `s8c_result_judge.py:217-238` が `n`、`delta_min`、`sd_max`、unit、direction、source binding を fail-closed 検証。登録側にも `orchestrator/campaign/s8c_preregistration.py:874-945` がある。 |
| 3. 2層＋3表 | 実装済み | descriptive/official/selection の表名は `s8c_result_judge.py:39`、導出は `896-1000`、出力は `1340-1353,1437-1462`。テストも `orchestrator/tests/test_s8c_result_judge.py:774-816` で3表と役割分離を確認。 |
| 4. preallocated attempt registry | 実装済み | genesis 作成・固定 slot は `orchestrator/campaign/trial_registry.py:2672-2726`、append-only 検証は `2778-2837`、slot 予約は `2984-3005`。 |
| 5. 真の noninterference | 部分実装 | projection/digest 機構は `orchestrator/campaign/s8c_generation_projection.py:1-5,105-161,371-455` にある。しかし `docs/phase3-8c-preregistration.md:96-109,204-212` が示す通り、実 holdout 非干渉の証明は未成立。P2対象なので本 wave では触れない。 |
| 6. 測定近接性・主張強度 | 未実装 | `_ObservationContext` は `s8c_result_judge.py:150-155` の3 map のみ。`_build_observation_context` も `456-515` で medians、replicate values、blocks だけを構築する。timestamp、実行環境、implementation/toolchain identity、(a)〜(c) ラベルに相当する別名のフィールドや関数は確認できない。 |
| 7. epoch 境界・legacy 混合禁止 | システム上は fail-closed | `s8c_preregistration_evidence.py:3075` の `SATISFIABLE_CONDITION_IDS` は空で、`3185-3193` が SATISFIED を強制的に失敗化する。発効条件も `s8c_preregistration.py:1925-1971` にある。なお judge 自体は epoch を保持しない（`s8c_result_judge.py:1012-1070,1437-1452`）ため、将来ゲートを開く wave では別途確認が必要。 |

項目6について、隣接する旧8b経路も代替実装ではありません。`orchestrator/campaign/s8b_oracle_judge.py:27-38,122-224` は campaign/perf observation の検証に留まり、`s8b_oracle_artifacts.py:150-243` の verifier epoch も D510 の3区分ラベルではありません。`p3_autonomous_workload_trial.py:1703-1729` の timestamp 等は stable digest から意図的に除外される run-local metadata です。

## 項目6の最小実装プラン

### 1. `_ObservationContext` の拡張

`orchestrator/campaign/s8c_result_judge.py:141-155` に、次の private record を追加する案です。

```python
@dataclass(frozen=True, slots=True)
class _ObservationProvenance:
    measured_at: str
    environment_identity: str
    implementation_identity: str
    toolchain_identity: str
    relation_kind: Literal[
        "continuous",
        "recovered_gap",
        "intentional_past_comparison",
    ]
    relation_id: str
```

`_ObservationContext` には次を追加します。

```python
measurement_provenance: Mapping[tuple[str, int], _ObservationProvenance]
proximity_labels: Mapping[
    tuple[str, int],
    Literal["continuous", "recovered_gap", "intentional_past_comparison"],
]
proximity_time_delta_seconds: Mapping[tuple[str, int], float]
```

全フィールドを正式観測では必須とし、欠落・空文字・未知ラベルは `INDETERMINATE` にします。旧観測を黙って正式観測へ昇格させないため、optional の既定値は設けません。

検証規則:

- `measured_at`: timezone 付き UTC の canonical RFC3339 文字列。
- identity 3種と `relation_id`: 非空文字列。
- `relation_kind`: 上記3値以外を拒否。
- on/off のペアで `relation_kind` と `relation_id` を一致させる。
- (a)(b) では environment、implementation、toolchain identity もペア一致を要求。
- (c) は記録可能だが正式判定には使用しない。

### 2. `_build_observation_context` の変更位置

`orchestrator/campaign/s8c_result_judge.py:456-515` に以下を追加します。

- `464-467`: provenance、label、time-delta 用 map を初期化。
- `478-497`: raw/attestation 検証と同じ段階で observation provenance を厳格に parse。
- `501-506`: `(cell_id, replicate)` ごとの provenance を保存。
- `507-510` の coverage 検証後: holdout ごとに on/off を突合し、ペア単位のラベルを導出。
  - `continuous`: (a) として保存。
  - `recovered_gap`: (b) として保存し、timestamp 差を秒で保存。
  - `intentional_past_comparison`: (c) として保存するが、formal eligibility は false とする。
- `511-515`: 追加 map を返却。

時間差の閾値は新設しません。§10.4 は時間差の記録と主張の弱化を要求しており、任意の秒数を「連続」の境界として発明しない方が安全です。

### 3. 判定への接続

`orchestrator/campaign/s8c_result_judge.py:763-893` の `_evaluate_contrast` で、既存の差分計算 `816-873` は変更しません。

- (a): 既存判定を維持し、diagnostics に `proximity_label="continuous"` を追加。
- (b): 判定値は既存のまま、diagnostics に `recovered_gap` と実時間差を追加し、同時測定とは表現しない。
- (c): label と参照情報は diagnostics に記録するが、正式な条件判定の入力にはせず、その holdout の formal status は `INDETERMINATE`。
- ペア不一致、identity 不一致、時刻不正は既存の fail-closed 経路 `s8c_result_judge.py:1033-1046` に流す。

## テスト案

既存 helper `orchestrator/tests/test_s8c_result_judge.py:133-170` に deterministic な provenance を追加し、以下を追加します。

- `missing/malformed provenance`：context 欠落、非UTC timestamp、空 identity、未知 label を `INDETERMINATE` と確認。既存の `454-487` の fail-closed パターンを模写。
- `continuous label`：label と時間差が diagnostics に出るが、既存 status は変わらないことを確認。
- `recovered gap label`：時間差を保存し、同時測定を示す文字列が出ないことを確認。
- `intentional past comparison`：label は記録されるが、正式 status に使用されず `INDETERMINATE` になることを確認。
- `pair provenance mismatch`：on/off の relation、relation_id、identity 不一致を fail-closed 確認。
- 既存の3表テスト `774-816`、create-only/rollback テスト `904-1018` は維持する。

3表への影響はありません。`_table_bytes` は `s8c_result_judge.py:1340-1353` で cell/selection rows と floor provenance だけを直列化し、publish も `1453-1462` の既存3表を使用します。今回の label は judge diagnostics/context に限定すれば、`_TABLE_NAMES`、表のバイト構造、既存 pin の入力を変更しません。対象テストファイル内には表SHAの直接的な byte pin は確認できませんでした。

## P2 衝突面

handoff の「`s8c_result_judge.py` と `test_s8c_result_judge.py` の diff 衝突0件」は、指定どおり git diff の独立検証をしていないため、事実として保証できません。

一方、静的な参照調査では `p3_autonomous_workload_trial.py` から judge への実行時接続は確認できず、C07 の接続は `s8c_preregistration_evidence.py:2776-2800` の静的検査です。したがって、今回の「judge の入力契約を追加し、テストする」最小案だけなら、p3 や registry への変更は不要です。

ただし、現時点で実際に provenance を生成する8c producerも確認できません。正式な end-to-end artifact まで今回の受入条件に含めるなら、旧8b producerを流用せず、別 wave で producer・artifact schema・認証境界を決める必要があります。その場合は本 waveでは実装せず、段4へ差し戻すのが適切です。

## 規律5に沿った分割候補

1. **観測 provenance の型・厳格検証**  
   `_ObservationProvenance` と `_build_observation_context` の検証追加。単独では観測値を正式判定へ通さない基礎増分。

2. **ペア近接性ラベルと主張強度の導出**  
   `_evaluate_contrast` で (a)/(b)/(c) を扱い、(c) を正式入力から除外。1と分離可能ですが、検証だけ先に入れると実効的な挙動がないため、1と同一実装単位にすることを推奨します。

3. **3表・永続 artifact へのラベル出力**  
   今回は分離・延期。表バイト構造と pin を変更し、C07契約更新も必要になるため、最小増分ではありません。

4. **producer 側の provenance 生成**  
   今回は分離・延期。現行 no-touch 対象と旧8b経路の再設計を伴い、別 wave の所有者・信頼境界が必要です。

## 推奨

最小の独立実装単位は、`s8c_result_judge.py` と `test_s8c_result_judge.py` に限定した「provenance 必須化＋ペアラベル導出＋fail-closed テスト」です。項目5の projection/registry 系ファイル、3表の byte schema、旧8b producer には触れません。

## 総括

項目1〜4は既存実装を file:line で独立確認し、項目5は部分実装、項目6は欠落と判定した。  
項目7は空の受理集合による fail-closed 境界として成立するが、judge単体の epoch 保持はない。  
最小推奨は judge と対応テストだけで provenance と3区分ラベルを追加し、3表を不変に保つこと。  
producerを含む end-to-end が必須なら、衝突0を未検証のまま進めず、別 waveへ差し戻して「実装しない」とする。