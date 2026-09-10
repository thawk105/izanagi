## 総括

**指定3ファイル・5 hunkの回収は妥当。実装を止める未見事実は見つからなかった。** 一方、旧commitの「同一workerへ寄せる」という説明と、briefのtimeout解消への期待は、現行schedulerからは保証できない。これは旧説明の誤り・効果の未実証であり、D1936のmodule fixture承認を覆すものではない。

負側変異は、test入力の改変から既存productionのdetached拒否gate無効化へ再照準できる。恒久production差分も新テストも不要。

以下、行番号は回収前HEAD `c68d08d9`。略記は次のとおり。

- T: `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py`
- C: `orchestrator/tests/conftest.py`
- R: `orchestrator/tests/test_real_repo_serialization.py`
- P: `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py`
- brief、plan、裁定: 必読指定の `brief.md`、`plan.md`、`d1936-43.md`

### real候補

| 型タグ | 指摘と根拠 | 扱い |
|---|---|---|
| ドリフト | 旧commit本文の「同一shard・同一worker」のうち、同一worker保証が成立しない。C:1993はprocess-memo以外のsuffixを除去し、C:2103でshard検証後に適用する。対象はC:570の例外集合に含まれない。 | 説明訂正はscope内。scheduler変更・process-memo追加はscope外。 |
| テスト代表性 | brief:2のtimeout解消は未証明。登録後もC:1156のread lockは共有ロックで、reader間の同時走査を排除しない。brief:16のgroupingも、読取り競合解消の保証にはならない。 | 「承認済み回収」と「解消の実測」を区別する。親の正式受入で確認。 |
| テスト代表性 | plan:71の負側変異はbad snapshotの注入を外すため、production拒否gateが退行した場合の検出力を証明しない。plan:83自身もこの限界を認めている。 | 下記の既存gate変異へ置換できる。 |
| 権限逸脱 | brief:12の親による全実走と、一時production変異の作業分担は明確化が必要。恒久差分3ファイルという境界と、変異試験の一時編集を混同すると、不要なscope拡張または試験断念になる。 | 親の既存変異実走として扱い、終了後のproduction差分ゼロを確認する。新しい所有者や機構は不要。 |

### refuted候補

- **「全worker合計1回でないため裁定違反」: refuted。** 裁定:5はmoduleごとの取得と独立copyを承認している。全worker合計1回という追加条件は書かれていない。plan:51のfixture実体ごとの説明が適切。
- **「P1の30関数・51nodeが現行で崩れている」: refuted。** 現行ASTと回収元4集合を独立照合し、対象集合の欠落・余分はゼロ。実collectionは未実施。
- **「4集合を同時更新すると恒真ゲートになる」: refuted。** R:52、R:163は独立リテラルで、R:1520がproduction側access mapと比較する。片側の登録退行を検出する構造は残る。ただし、4集合すべての同じ誤記まで独立goldenだけで保証するものではない。
- **「clean値への上書きでproduction拒否が恒真化する」: refuted。** T:621で正常snapshotから1フィールドを壊し、T:623で再注入する既存負例がある。上書き自体も今回新設する挙動ではない。
- **「site偽装の追加が必要」: refuted。** P:163の取得はGit状態とsource digest。site分類を読まない。ただしP:134、P:148は環境を継承するので、環境全般から独立とは言えない。
- **「旧差分が現行3ファイルの後続変更を巻き戻す」: 現HEADではrefuted。** 回収元の親と現HEADの対象3ファイルは差分ゼロ。統合時点のmainまで保証する結果ではない。

brief:13の他wave所有状況は、指定資料内の宣言以上には確認していない。現在の競合不存在を独立確認済みとは報告できない。

### 4集合と全consumer

| 集合 | 現行位置 | 全件数の変化 | 回収元の対象登録 |
|---|---:|---:|---:|
| `_REAL_REPO_NODE_INVENTORY` | C:260 | 99 → 129 | 30 |
| `_REAL_REPO_PARENT_ONLY_NODES` | C:402 | 34 → 64 | 30 |
| `_REAL_REPO_CLASSIFIED_NODES_GOLDEN` | R:52 | 99 → 129 | 30 |
| `_REAL_REPO_PARENT_ONLY_NODES_GOLDEN` | R:163 | 34 → 64 | 30 |

T:73がautouseなので、次の全30関数がconsumer。名称はすべて `test_` 接頭辞を省略した。

| T行 | 関数 | node数 |
|---:|---|---:|
| 221 | r1_binds_all_three_explicit_values_and_skips_real_driver | 1 |
| 256 | r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 1 |
| 306 | r3_records_only_the_observed_ambient_approval_condition | 2 |
| 337 | r1_projection_follows_observed_approval_not_request_identity | 2 |
| 367 | r2_unexpected_approval_presence_is_unbound_and_not_green | 1 |
| 401 | missing_r1_explicit_value_cannot_be_green | 3 |
| 432 | swapped_r2_hex_values_fail_exact_binding | 1 |
| 458 | repository_local_evidence_directory_is_rejected | 1 |
| 510 | submission_source_digests_are_bound_to_runtime_bytes | 3 |
| 540 | r1_manifest_rejects_approval_that_does_not_equal_nonce | 1 |
| 575 | r3_manifest_rejects_nonliteral_ambient_approval | 1 |
| 610 | job_start_requires_manifest_head_detached_and_clean_repository | 4 |
| 640 | repo_unchanged_claim_compares_target_content_digests | 1 |
| 675 | r2_timeout_is_not_accepted_as_refusal | 1 |
| 699 | r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 1 |
| 721 | r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 1 |
| 751 | r2_refusal_rejects_any_driver_argv_mutation | 3 |
| 791 | atomic_result_publish_is_create_only | 1 |
| 803 | main_emits_one_prefixed_stdout_line_and_auxiliary_result | 1 |
| 892 | pbs_contract_runs_observer_through_single_result_call_block | 1 |
| 926 | pbs_early_ulimit_failure_emits_one_prefixed_result | 1 |
| 954 | pbs_preserves_one_valid_negative_observer_result | 1 |
| 980 | pbs_replaces_invalid_observer_stdout_with_one_fallback | 3 |
| 995 | submitter_text_is_outside_execution_inventory | 1 |
| 1007 | submitter_has_exact_three_request_design_and_create_only_witnesses | 1 |
| 1077 | submitter_preflight_parses_gen_s_semantic_state | 3 |
| 1151 | request_receipt_binds_qstat_body_visibility | 5 |
| 1208 | request_receipt_accepts_measured_qstat_layout | 1 |
| 1281 | request_receipt_rejects_wrong_owner_or_non_active_state | 3 |
| 1337 | group_intent_is_create_only_and_has_no_completion_fields | 1 |

20単一node関数と、10パラメータ化関数の31nodeで計51。PBSやsubmitterのテキスト検査も除外できない。

### 負側変異の再照準

P:261の次の条件だけを、一時的に `if False:` へ変更する。

```python
if repo_snapshot["detached"] is not True:
    raise ProbeError("job repository HEAD is not detached")
```

対象は既存の以下のnode。param IDは親の実collectionで確定する。

```text
orchestrator/tests/test_t1259_qsub_env_delivery_probe.py::test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False]
```

単一理由が成立する静的根拠は次のとおり。

- T:605、T:622で壊す値はdetachedだけ。HEAD、clean値、source digestは維持される。
- T:623のsnapshot再注入を保持するので、負例入力は変えない。
- T:140のmanifestとP:163のsnapshotは、一時変異後のsource bytesをそれぞれ読む。新しいテストプロセスで開始すれば、production編集だけを理由とするdigest不一致は静的には予想されない。
- before/afterは同じbad snapshotなので、P:841の比較による別拒否も予想されない。
- detached拒否を外すとmanifest受理へ進み、P:849がevidenceを返すため、最初にT:635の `accepted_evidence is None` が失敗する見込み。

**KILLEDは期待であり未実測。** planの正側・分類登録側変異は静的には維持可能だが、3案ともcopy境界の検出力を証明しない。二段のdeep copyは指定差分どおり保持し、新テスト追加へ広げない。

### 未実測・scope境界

実施したのは読解、Git比較、AST照合のみ。pytest collection、baseline、変異、正式受入、timeout解消は未実測。親が既存経路で確認する。

恒久実装は指定commitの3ファイル差分回収だけ。scheduler変更、process-memo追加、新gate・検査・台帳・一般化はscope外。成果物・一時ファイルは書き込んでいない。