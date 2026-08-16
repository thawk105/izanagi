## 総括

取り残しは既知の 1 箇所だけでした。[test_reflux_originless_compatibility.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_reflux_originless_compatibility.py:234) の acceptance digest pin を次へ更新しました。

```text
386492ad216ec0bef7d264188a9823359300080f4e095e1d2619ea474d54eb79
↓
3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170
```

pytest／`tools/run_tests.py` は指示どおり実走していません。docs、output、git、commit には触れていません。

### 1. 全件検索のコマンドと結果

#### SHA-256 literal の全母集団

```bash
rg -o --glob '*.py' '[0-9a-f]{64}' orchestrator tools hooks tests 2>/dev/null | wc -l
rg -l --glob '*.py' '[0-9a-f]{64}' orchestrator tools hooks tests 2>/dev/null | wc -l
```

結果は 805 literal、66 file でした。ここから、本 wave の入力面へ到達する producer を次の順で追跡しました。

- evidence contract の意味 hash: `evidence_contract_sha256()`  
  [s8c_preregistration.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:389)
- C12 判定結果: `_c12_allocation_binding_verdict()` → `_evaluate_c12()`  
  [s8c_preregistration_evidence.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence.py:564)
- 凍結 record と最新版: `validate_condition_freeze_at()`／`_record_document()`
- 判定器版を含む活性化報告: `_activation_report_at()`
- その全 field の digest: `_activation_report_digest()`  
  [s8c_preregistration.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:1932)

#### 活性化報告 digest の literal

```bash
rg -o -n --glob '*.py' \
  '386492ad216ec0bef7d264188a9823359300080f4e095e1d2619ea474d54eb79|3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170' \
  orchestrator tools hooks tests
```

更新後の全結果は同じ golden の 4 occurrence です。

- 新値 1 件: `acceptance/activation_report_digest_sha256`
- 旧値 3 件:
  - `journals/*/*/launch_admission/activation_report_digest_sha256`
  - `lifecycle/*/activation_report_digest_sha256`
  - `reports/*/launch_admission/activation_report_digest_sha256`

構造への復元確認には次を使いました。

```bash
python3 -c 'from orchestrator.tests import test_reflux_originless_compatibility as t; vals={"old":"386492ad216ec0bef7d264188a9823359300080f4e095e1d2619ea474d54eb79","new":"3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170"}; print("\n".join(f"{label} {k}: {v}" for label,digest in vals.items() for k,v in t._PRE_WAVE_ORIGINLESS_BASELINE.items() if any(run[0] == digest for run in v)))'
```

旧値 3 件は取り残しではありません。受入実測で変化した 354 項目中の唯一の差は acceptance 側であり、reports／journals／lifecycle は fixture capability が保持する既存値です。これらまで一括置換すると、実測差分に無い 3 項目を誤って変更します。

#### evidence contract の意味 hash と加工後 hash

```bash
rg -o -n --glob '*.py' \
  '6944a0b0eed75917c9d489dd43c3b58e637f3d85b97203d1dc60d2cf96fbdf29|8569c023aeb473fd4a02078ff392445af4174a70accd63efee70351460d0685c|8401901107438f127bc164bfe3fc754f108bcdc19cb2af198c93e1cec0a29768|8cec35e8879b6b611ee2c1afcf80cfca2f0095c203dc0b17eb6aba158d18998a' \
  orchestrator tools hooks tests
```

全結果は [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py) の 4 件です。

- 764、769、774 行: 現行 contract に NUL／CR／LF を非 path field へ加えた加工後 hash 3 件
- 1155 行: 現行 contract の意味 hash `6944a0...` 1 件

いずれも本 wave 後の値へ既に更新済みでした。追加の取り残しは 0 件です。

g5 が持つ他の意味 hash も検索しました。

```bash
rg -o -n --glob '*.py' \
  '5ae2a5f4997a358fba1b1068c7dd3b6d507b7477fc828f9e496ee7bb87d4085e|8602af63930e8c85395e15bf4b8c530b18f29ffa1e52baa6cbb90cce12056448|12d9e4dfe25e94a997f1dc615603f18c22ffbe697203b67acc809cf3a204a7fc|4b6100225bf92233b1fd4e1da1737829fc08094cf25a1b5ed47f0cac34c168cc' \
  orchestrator tools hooks tests
```

結果は 0 件です。これらは literal test pin ではなく、[test_s8c_preregistration_invariant.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:151) 以降で現行契約から動的に再導出・照合されています。

変更された core、evaluator、contract raw bytes、g5 raw bytes 自体の SHA-256 も全 Python file から検索し、literal pin は 0 件でした。

#### 判定器版と C12 理由コード

```bash
rg -n --glob '*.py' \
  's8c-decider/v2|s8c-decider/v1|allocation-enforcement-consumer-absent|environment-contract-consumer-absent' \
  orchestrator tools hooks tests
```

全件を分類した結果:

- `s8c-decider/v2`
  - production 定数 1 件: [s8c_preregistration.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:50)
  - 現行版テスト 3 件: `test_s8c_preregistration_core.py:2057,2075,2080`
- `s8c-decider/v1`
  - g4 の歴史不変 pin 1 件: [test_s8c_preregistration_invariant.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:237)
  - `v1/extra` は不正形式の負例 1 件
- 新 C12 理由
  - production enum 1 件
  - gap snapshot／現行 repository／precedence／negative-control の test literal 4 件  
    [test_s8c_preregistration_predicates.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:132)
- 旧 C12 理由
  - production enum 1 件のみ  
    [s8c_preregistration_evidence.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence.py:83)

旧理由は stale pin ではありません。allocation gate を通過した後、environment／execution guard が欠落する別の拒否段で現在も返される有効な理由です。[s8c_preregistration_evidence.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence.py:592)

#### 凍結世代数・最新世代の固定 literal

```bash
rg -n --glob '*.py' \
  'condition-freeze\.v1\.g5|generation_path\(5\)|freeze_generation\s*==\s*5' \
  orchestrator tools hooks tests
```

結果は 0 件です。最新世代を 5 と固定した consumer はありません。

```bash
find output/s8c-preregistration/condition-freeze -maxdepth 1 -type f -printf '%f\n' | sort
```

全結果は g1、g2、g3、g4、g5 の 5 file です。世代閉包は固定値 5 ではなく、[test_s8c_preregistration_invariant.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:136) で `1..validation.generation_number` の連続列として検査されています。

`generation_path(4)` は [test_s8c_preregistration_invariant.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:200) に 1 件ありますが、g3→g4 が「契約を変えず版束縛手続きを導入した」という歴史的遷移の専用検査であり、latest=4 の仮定ではありません。

#### pin 閉包のメタテスト

「この digest literal の参照箇所は N 件」と直接数えるメタテストは 0 件でした。

関連する閉包メタテストは次の 4 種です。

- evidence contract の全 path 入力を exact 39 件と束縛  
  [test_s8c_preregistration_core.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py:639)
- wave 必須 path の閉集合と全 freeze path の列挙  
  [test_s8c_preregistration_invariant.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:30)、同 297 行
- freeze 世代の連続閉包  
  同 136–142 行
- originless 出力の全 nonvolatile leaf と closed key set  
  [test_reflux_originless_compatibility.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_reflux_originless_compatibility.py:581)

### 2. 直した箇所と新値が正しい理由

変更は [test_reflux_originless_compatibility.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_reflux_originless_compatibility.py:234) の acceptance leaf 1 件だけです。

新値が正しい根拠は次の連鎖です。

1. acceptance receipt は実 repository から活性化報告を再導出する。
2. 活性化報告には freeze generation、protected hash、decider version、全 predicate、core/evaluator/projection blob hash が入る。
3. `_activation_report_digest()` はその全 field の canonical JSON を domain-separated SHA-256 にする。
4. 本 wave はその入力のうち C12 契約、C12 理由、版、freeze tip を意図的に変更した。
5. 受入全走の実測 actual が `3176f3...` で、354 項目中この acceptance leaf だけが旧 golden と異なった。

したがって pin の削除や緩和ではなく、同じ full-structure assertion の期待値を実 repository の正しい再導出値へ更新しています。

親が再計算する node と値の読取手順:

```bash
python3 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set \
  -vv -rf
```

stale pin の場合は失敗出力の `acceptance/activation_report_digest_sha256` に現れる actual 64-hex を読む。この turn では実走していません。

直さずに返す破損所見はありません。旧 digest 3 occurrence、旧理由 enum、g4/v1 literal は上記のとおり現役の別経路または歴史不変値です。

### 3. 親が走らせる焦点範囲

最低限の再計算 node:

```text
orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set
```

変更 production 3 file、evidence contract、freeze namespace、および activation digest の全 consumer 側を含む焦点 file 集合:

```text
orchestrator/tests/test_s8c_preregistration_core.py
orchestrator/tests/test_s8c_preregistration_predicates.py
orchestrator/tests/test_s8c_preregistration_invariant.py
orchestrator/tests/test_ccbench_spawn_sites.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_trial_registry.py
orchestrator/tests/test_reflux_origin_binding.py
orchestrator/tests/test_reflux_originless_compatibility.py
orchestrator/tests/test_s8b_ratified_freeze.py
orchestrator/tests/test_s8b_ratified_verify.py
orchestrator/tests/test_s8c_acceptance_receipt.py
orchestrator/tests/test_autonomous_trial_completeness.py
orchestrator/tests/test_layer3_report.py
```

この集合は、直接 import／path 参照する検査 9 fileに加え、digest の transitive consumer 4 fileを含みます。今回変更した test file だけでなく、production の `_activation_report_digest()` 出力を real-repository fixture 経由で pin する originless compatibility test を明示的に含めています。