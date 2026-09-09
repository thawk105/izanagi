## 実装状況

R1〜R7 のコード変更を 3 ファイルへ実装しました。pytest は基盤障害により未実走のため、状態は「実装済み・未実走」です。docs 編集・commit は行っていません。

## 変更したファイル

- [t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:110)

  - 12 seed と既定 seed の閉表、cell 別 thread 閉表を追加: 110、362 行。
  - 検証済み `CertificationAxes` と claim builder を追加: 374、416 行。
  - row/group/published consumer を同一閉表へ束縛: 934、2394、2686、2907 行。
  - p2 の missing/mismatch 理由と非 p2 seed conflict を実装: 1543〜1599 行。
  - anomaly 非空を reject: 2069 行。
  - performance artifact を実 seedと対象 thread rowへ束縛: 2148〜2269 行。`expected_repo_head` 検査は維持。
  - group 内 `binary_sha256`、`build_cache_key` singleton を追加: 2745〜2746、3077〜3078 行。
  - build、payload、claimへ実 seed/threadを伝播: 3400、3445、3478、3570 行。

- [t2187_adaptive_const_probe.pbs](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:28)

  - p2 の 12+1 seed 閉表: 28 行。
  - 非 p2 seed conflict、p2 seed必須、cell別 thread 閉表: 189〜229 行。
  - seed 引数配列を分岐外へ移動し、performance/certify双方へforward: 448〜480 行。

- [test_t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_t2187_adaptive_const_probe.py:778)

  - M1〜M8 の負例を追加: 778、1864〜2243、3050、3155〜3254 行。
  - 旧 `c2-p1-a1` / `c2-p2-a1` claimのpublished再検証を追加: 2046 行。
  - group binary/cache singleton の正負例を追加: 989、1154〜1211 行。
  - testファイルの新設・改名はなく、file集合meta-testへの波及はありません。

## テスト

指定 runner に次の nodeid をまとめて要求しましたが、rc=16、`child_started=false` で実テストは開始されませんでした。

- `test_probe_seed_table_matches_cohort2_preregistered_seeds`
- `test_certification_contract_accepts_only_cell_closed_thread_seed_axes`
- `test_certification_contract_rejects_seed_and_thread_near_misses`
- `test_certification_claim_requires_validated_axes_and_binds_actual_identity`
- `test_published_claim_compatibility_is_exact_for_the_four_old_literals`
- `test_group_axes_reject_mixed_policy2_seed_or_thread`
- `test_target_validation_rejects_nonempty_anomalies_from_real_serial_fixture`
- `test_pbs_certification_seed_and_thread_closed_tables_are_exact`
- `test_dynamic_performance_artifact_rejects_certify_identity_drift`
- `test_cohort2_performance_binding_requires_extime_and_default_seed`
- `test_public_certification_accepts_each_exact_cell_and_rejects_widening`
- `test_cohort2_certification_is_exact_and_policy2_uses_default_seed`
- `test_public_certification_rejects_step_policy_seed_before_dispatch`
- `test_pbs_dynamic_output_and_plus_transport_are_fail_closed`
- `test_pbs_certify_mode_preserves_literal_performance_exec_and_exact_axes`

単一 nodeid `test_certification_claim_requires_validated_axes_and_binds_actual_identity` でも再試行しましたが、同じく rc=16でした。原因はいずれも `qstat -Q preflight rc=1` のdispatch基盤障害で、実装起因ではありません。queue確認は rc=0でしたが状態は「観測不能」でした。

補助検証として、Python AST・import smoke・M1〜M8関連関数の非pytest直接スモークは rc=0です。`bash -n` はログインノードhookがPBS実行と誤判定して拒否したため、sandbox由来の疑いがあります。親環境で runner 経由の再現が必要です。

## 受理・拒否挙動の変更

| 対象 | 変更前 | 変更後 |
|---|---|---|
| p2 seed | certifyでは全seed拒否 | 明示した13値のみ受理。省略は`certification-step-policy-seed-missing`、閉表外は`certification-step-policy-seed-mismatch` |
| 非p2 seed | conflict | 同じ`step-policy-seed-certification-conflict`を維持 |
| thread | 全cell 48のみ | tuned/dynamicは48のみ、p1/p2は24または48。複数指定・近傍値・非exact literalは拒否 |
| claim | cell固定の旧literal | 検証済み実thread/seedとR7 build条件から生成。旧4 literalはpublished互換だけで受理 |
| performance束縛 | p2を既定seedへ固定、thread row不問 | request実seedと一致し、認証対象thread rowが実在する場合だけ受理 |
| anomaly | certified結果内の非空anomalyを明示拒否しない | `anomalies == []` を必須化 |
| group build identity | binary/cacheのgroup内混在が可能 | 両fieldをsingleton必須化 |
| PBS seed | certifyへforwardしない | p2閉表検査後、certifyへexact forward |

既存テスト期待値で変更したのは、p2の既定seed固定前提、PBSのseed非forward前提、group内24個の異なるbinaryを許す前提です。いずれもR1、R3、R5、R6の裁定を直接実装するための変更で、既存拒否の緩和ではありません。

## 波及可能性

- `_certification_contract` のprivate戻り値は `(Cell, workload, threads)` から `(CertificationAxes, workload)` へ変更しました。射影内callerは更新済みですが、所有外private callerがあれば追随が必要です。
- dynamic performance fixtureは対象rowの`threads`と、p2では実seed/genomeが必要です。
- p2 certification producerはCLIと`driver_argv`へseedをexactly once記録する必要があります。
- synthetic group fixtureは24 rowで同一binary/cache keyを使う必要があります。
- 新receipt consumerは新claimを扱う必要があります。既発行4 claimと`c2-p1-a1` / `c2-p2-a1`はexact互換を残しています。

## 実装しなかった裁定項目

- R1の13 performance job生成、認証走行、receipt収集は親段階の実機作業であり未実施です。
- R6(b)の12 group間binary相異確認は裁定どおり段7の親記録へ残しました。
- R7の診断計装入りgenome認証は裁定どおり改修せず、claimの限定だけ実装しました。
- R8〜R16の投入運用、記録、docs更新は3ファイルのauthor scope外です。

## 総括

- R1〜R7の実装とM1〜M8負例を保存済みです。
- 既存拒否は維持し、追加受理はcell/thread/seed閉表内に限定しました。
- 補助スモークはrc=0ですが、pytestはdispatch基盤障害で未実走です。
- 親で指定runnerによるnodeid群とファイル全体の再走が必要です。