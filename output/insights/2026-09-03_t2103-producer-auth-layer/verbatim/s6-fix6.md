## 総括

F18 は closed、F19 は実装済みですが 201-block 実測未完了のため partial です。

変更したのは次の 2 file だけです。

- [p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/campaign/p3_b4_producer_auth_experiment.py:1987)
- [test_p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:304)

rogue support と prereg は本巡では変更していません。commit、git add、stash、branch 操作、docs 編集も行っていません。

期待 matrix、採否規則、13 mutation、39 組、201 block、floor=0、base-commit anchor、fail-closed は維持しています。D-P / D-T / D-C は全候補 SURVIVED のままです。

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F18 | closed | abort reason を `case_aborted:<phase>:<type>:message=<例外メッセージ全文>` に変更。複数行メッセージが shard JSON の serialize / parse 往復と diagnostic log の双方に残ることを補助検証しました。 |
| F19 | partial | D の再構築を `dataclasses.replace` に変更し、新 producer の `rejection_history` を含む全 metadata を保持。raw bytes と対応 SHA だけを変更します。ただし 201-block の実経路は dispatch failure で未実走です。 |
| 非後退 | regressed なしを静的確認 | C0 / C1 / R / POS-1 の分岐、mutation registry、prereg、期待 matrix は変更していません。実測による非後退確認は未完了です。 |

## D 系が当たっていた assertion

旧 D 経路は `B4RawAnalysisAssembly` を古い 5-field 形で組み直していました。新 producer が必須 field `rejection_history` を追加したため、実際の根因は次です。

```text
TypeError: B4RawAnalysisAssembly.__init__() missing 1 required positional argument: 'rejection_history'
```

同じ `_subprocess_probe` wrapper と旧 constructor 形で再現した AssertionError のメッセージ全文は次でした。

```text
case subprocess rc=1
stdout:

stderr:
Traceback (most recent call last):
  File "<string>", line 2, in <module>
TypeError: B4RawAnalysisAssembly.__init__() missing 1 required positional argument: 'rejection_history'
```

親 shard は F18 前のためこの本文を捨て、外側の型名 `AssertionError` だけを記録していました。修正後は上記 stdout / stderr / traceback を含む AssertionError メッセージ全体が reason に入ります。

## 再照準の内容

[post-assembly helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:304) で既存 assembly に対して次の 2 field だけを置換します。

- `canonical_bytes = made.raw_analysis_bytes`
- `sha256 = sha256(made.raw_analysis_bytes)`

`schema_version`、元の `source_artifact_bytes`、`planned_attempt_artifact_paths`、新しい `rejection_history` はそのまま保持します。実 route からの呼出しは [D の post-assembly 位置](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:455) にあります。

これが D の意味を保つ理由は次のとおりです。

- 正規 assembly が成功した後にだけ実行される。
- 別 module の rogue producer が作った raw-analysis bytes を使用する。
- D では planned attempt artifact を差し替えない。
- source artifact bytes と source binding は書き換えない。
- raw analysis の P / T / C 判断値と、その raw bytes に対応する SHA だけが変わる。

補助検証では `rejection_history` を含む metadata の同一性を確認しました。ただし実測で SURVIVED に到達したことは未確認なので、期待値は変更せず partial としています。

## 6 shard の起動 command

前巡から変更ありません。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json
```

combine argv も変更ありません。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py combine \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json \
  --output output/insights/2026-09-03_t2103-producer-auth-layer/comparison.json
```

## 実走した node と結果

pytest で実走できた node はありません。以下を `tools/run_tests.py` へ投入しましたが、すべて起動前に rc=16、`qstat -Q preflight rc=1`、`child_started=false` となりました。

```text
test_expected_matrix_has_twelve_negative_cases_and_pos_1
test_real_rogue_producer_writes_attempt_raw_and_source_bytes[P/T/C]
test_measurement_harness_routes_cases_through_real_probe
test_case_failure_records_aborted_and_remaining_cases_continue
test_abort_message_is_preserved_in_shard_json_and_diagnostic_log
test_post_assembly_raw_rewrite_preserves_new_producer_metadata
test_w08_preregistration_is_rederived_from_content
test_candidate_shards_require_all_39_pairs_before_decision
```

単一 node `test_post_assembly_raw_rewrite_preserves_new_producer_metadata` も個別再試行しましたが、同じ dispatch failure でした。以上は実装済み・未実走です。6 shard の 201-block 本走も実装済み・未実走です。

非 pytest の補助検証は通過しました。

- source の AST parse
- prereg canonical 完全一致
- 13 mutation、39 組
- D 系全候補 SURVIVED の期待維持
- 201 block、floor=0
- abort 全文の shard serialize / parse と log 保持
- raw bytes と SHA 以外の assembly metadata 保持
- `git diff --check`
- U+0300〜U+036F なし

## 従えなかった項目

- pytest node と D 系 201-block 実測は、Pegasus dispatch infrastructure failure のため実行できませんでした。性能測定をログインノードへ直接迂回していません。
- 「既存テストの期待値を変更しない」は、F18 と直接衝突する type-only abort reason の assertion 1 箇所だけ文字列を全文形式へ強化しました。domain outcome、期待 matrix、採否規則は変更していません。