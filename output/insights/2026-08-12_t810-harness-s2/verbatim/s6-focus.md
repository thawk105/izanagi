# 判定: **NO-GO**

静的検査のみ実施した。pytest は未実走。fix 後も production 正例経路が成立せず、未認証 wrapper 実行、偽 admission receipt、repo 内書込みが残る。

## 所見対応表

| 所見 | fix 申告 | 独立判定 | 差分・根拠 |
|---|---|---|---|
| A-1 | closed | **partial** | coordinator は guard/budget receipt の形式だけを検査し、guard 実行結果や ledger 実 bytes と照合しない。[t810_coordinator.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:356)、[t810_coordinator.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:387) |
| A-2 | closed | **partial** | qsub spelling と生成後 script 改変は閉じたが、caller 指定 `wrapper_path/wrapper_argv` をそのまま script 化し、`wrapper_sha256` の実 bytes 照合がない。[t810_coordinator.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:542)、[t810_harness_schema.py:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_harness_schema.py:351) |
| A-3 | closed | closed | config 埋込み event は廃止され、file-backed receipt と coordinator monotonic 受領時刻を使用。[t810_coordinator.py:886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:886) |
| A-4 | closed | closed | sequence、previous digest、順序、実 bytes SHA-256を検査。[t810_coordinator.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:851) |
| A-5 | closed | closed | state 1/2/3 が completion count より先に集約される。[t810_coordinator.py:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:1261) |
| A-6 | closed | closed | 成功 state は全13 slot の exact presence が必須。[t810_harness_schema.py:802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_harness_schema.py:802) |
| A-7 | closed | **partial** | roots は live git ではなく effect 前の caller 提供 `approved_git_identity` から導出。偽 identity で実 repo 内 root を外部扱いできる。[t810_coordinator.py:1434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:1434)、[t810_coordinator.py:1593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:1593) |
| A-8 | closed | **partial** | argv/name は prereg 由来だが、executable path/hash は caller の slot 値。正規名を持つ任意 binary と自己申告 hash が通る。[t810_pbs_wrapper.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:269) |
| A-9 | closed | closed | typed witness、outcome、reservation/job identity を検査。[t810_budget.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_budget.py:597) |
| A-10 | closed | closed | 列挙された低水準 effect は `AuthorizationToken` 型必須。approval trust root 不在は limitation に残る。 |
| B-1 | closed | closed | sentinel 構成 token と effect 境界の型 gate が存在。 |
| B-2 | closed | closed | 全 ratifiable status を receipt 読取前に deny。[t810_coordinator.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:340) |
| B-3 | partial | **regressed** | 未結線に加え、coordinator 生成 script と wrapper CLI が非互換。後述。 |
| B-4 | closed | **partial** | argv は閉じたが executable identity の caller 自己申告が残る。 |
| B-5 | closed | closed | node receipt chain/digest を実ファイルから検査。 |
| B-6 | closed | closed | release 後全再検査の成功後にだけ ack。ack 後 cancel fixture も有効。 |
| B-7 | closed | closed | filesystem lstat と専用 measurements JSONL を使用。 |
| B-8 | closed | closed | dependency/module/trace/NUMA/argv 等を coordinator が再評価。 |
| B-9 | closed | **regressed** | node の false 固定と coordinator の期待が矛盾し、正規 wrapper preflight が必ず拒否される。 |
| B-10 | closed | closed | exact decoder と Path/GitIdentity 復元が存在。 |
| B-11 | closed | closed | 6 ID は統一され、global policy の `execution_mediation_incomplete` が未結線を宣言。 |
| B-12 | closed | closed | `ready` surface は削除され、`release_is_still_active` は production caller を持つ。 |

## 回帰所見

### 1. coordinator が生成する PBS script は wrapper を起動できない — blocker

coordinator は `exec python3.10 …/wrapper.py` を生成するが、wrapper CLI は `--request` 必須である。

- 生成元: [t810_coordinator.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:542)
- 現在の正例 fixture: [test_t810_coordinator.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:120)
- CLI 要求: [t810_pbs_wrapper.py:1132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:1132)

具体入力は現行 coordinator 正例そのもの。全 PBS job が argparse error で終了し、preflight は一件も生成されない。

さらに `publish_wrapper_request()` は `pbs_request_id`、hostname、CPU allocation を要求するため qsub 前に呼べず、coordinator からの caller も存在しない。[t810_pbs_wrapper.py:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:338)

### 2. node repo-absence 誠実化が ready barrier と非互換 — blocker

wrapper は全4 booleanを false 固定する。[t810_pbs_wrapper.py:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:385)

一方 coordinator は `package_repo_free`、`git_ancestor_absent`、`pbs_workdir_repo_external` が true でなければ `preflight_failed` にする。[t810_coordinator.py:996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:996)

したがって production wrapper が生成した正常 preflight は必ず cancel される。`test_node_repo_absence_never_claims_unprovable_positive` は false 固定だけを直接検査し、barrier へ渡していない。

### 3. caller 指定の任意 wrapper を qsub できる — blocker

具体入力:

```text
wrapper_path=/tmp/evil.py
wrapper_argv=["python3.10", "/tmp/evil.py"]
wrapper_sha256=<任意64桁>
```

schema を通り、coordinator はその argv から正規 script を作る。effect 直前再検査も同じ caller 値との比較なので恒真となる。`wrapper_sha256` の実ファイル照合はない。

### 4. repo 外判定は effect 前に偽 identity で迂回可能 — blocker

`approved_git_identity` を実 repository と無関係な `/tmp/fake-repo` にし、`work_root/output_root` を実 repository 内に指定すると、fake roots に対する external 判定を通過して directory/file effect が起きる。live identity の validator は `prepare_group()` より後である。

## テスト実効性

受理を広げる方向の期待値変更、skip、xfail 追加は見つからなかった。node absence と ack 順序の変更は厳格化である。

ただし production を通らない正例が残る。

- [test_intent_manifest_producer_binds_prereg_policy_request_and_publication](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_pbs_wrapper.py:104) は producer を直接呼び、coordinator/qsub を通らない。
- [test_authorized_production_core_uses_same_validator_twice_and_dormant_prereg](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:788) はテスト自身が node JSONL を書き、wrapper CLI を通らない。
- [test_modified_pbs_script_is_rejected_at_scheduler_effect](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_coordinator.py:724) は生成後改変だけを検査し、intent 段階からの任意 wrapper を検査しない。
- executable forbidden-name coverageは従来の複数 parameter から `trace-benchmark` 一例へ縮小した。実装は現状全 fragment を拒否するが、`calibration/floor/oracle` の退行を単独で殺せない。

limitations は概ね誠実で、policy/guard/budget/terminal に `execution_mediation_incomplete` が残る。wrapper producer の coordinator 未結線を「結線済み」とする production caller は見つからなかった。ただしテスト名の “producer” は統合経路を保証しない。

## 変異耐性表

| 変異 | 判定 | 単独で殺すテスト |
|---|---|---|
| (a) hostname 異なり数検査の除去 | KILLED | `test_ready_barrier_recomputes_raw_evidence[duplicate_host]` |
| (b) spread 上限の緩和 | KILLED | `test_start_spread_boundary_uses_only_coordinator_receipt_times` |
| (c) 測定直前 cancel 再確認の除去 | KILLED | `test_second_cancel_check_observes_cancel_created_after_ack` |
| (d) argv exact を部分一致化 | KILLED | `test_prefix_suffix_reordering_and_options_are_denied` |
| (e) 未知 job_state の無害化 | KILLED | `test_unknown_state_has_dedicated_deny_reason` |
| (f) unratified を ratified 扱い | KILLED | `test_prepare_group_dag_is_create_only_and_policy_hosts_are_ratified` |
| (g) ledger genesis 照合の除去 | KILLED | `test_different_genesis_ledger_is_rejected` |
| (h) node receipt hash chain 検証の除去 | KILLED | `test_node_receipt_hash_chain_and_actual_bytes_digest_are_enforced` |
| (i) state 2 を無視し完了数だけで判定 | KILLED | `test_terminal_state_two_precedes_twelve_completion_reduction` |
| (j) witness 内容検証を64桁hex存在だけへ戻す | KILLED | `test_qdel_release_requires_typed_witness_content_and_reservation_identity` |

## Must-fix 優先順

1. qsub 前 static request と node 側 runtime identity を分離し、coordinator→script→wrapper CLI の一本の正例経路を完成させる。
2. node false 固定と ready barrier の判定を整合させ、false を理由に自動拒否しない契約へ直す。
3. wrapper path/hash を凍結 package の実 bytes に束縛し、任意 wrapper 実行を拒否する。
4. guard/budget producerを production に結線し、budget receipt の ledger-after を実 ledger bytes と照合する。
5. repository roots を caller config ではなく effect 前に取得した live git common-dir/worktree 集合へ束縛する。
6. executable hash/path を validator/build identity と intent/runner-policy間で同一に束縛する。
7. coordinator から実 wrapper CLI を通る positive integration testを追加する。

## 総括

- **NO-GO**。production 正例経路が成立しない。
- wrapper request producer は依然未結線で、申告どおり partial。
- coordinator script は wrapper の必須 `--request` を渡さない。
- node repo-absence false 固定は coordinator に必ず拒否される。
- 任意 wrapper と自己申告 executable identity が残る。
- guard/budget receipt は形式検査のみで実 producer・ledgerへ未束縛。
- repo 外判定は effect 前の偽 git identity で迂回可能。
- 指定された10変異はすべて現テストで KILLED と判定した。