## 実装結果

段6 fix をコード／テストのみに投入しました。`docs/**` は編集せず、`git add` / `git commit` も実行していません。

主な変更:

- [`buildcache.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py) の `build()` / `build_v2()` に必須 keyword-only `admission` を追加し、materializer の最初で再検査。
- [`s6_sort_sweep.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py) と [`s8a_trigger_sweep.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py) の `_eval_one()` へ admission を明示伝播。
- sweep の stock を `STOCK_OR_PINNED`、決定論的候補を `MACHINE_SWEEP` に分離。
- `BuildAdmissionError` を広い `except Exception` より先に再送出し、`driver-error` 化を禁止。
- S1 direct comparison、S8b oracle/floor を `HUMAN_REVIEWED` に分類。
- T-126 code identity に `build_admission.py` を追加。
- coder driver 5本の flag 無し／有り parameterized test、materializer 境界 test、M1〜M5 の単一理由 control を追加。
- T080 fixture を、現在の作業ツリーではなく発行済み receipt の migration-basis commit から source closure を復元する形に修正。

## 所見対応表

### レビュー1

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 materializer 迂回 | closed | `build()` / `build_v2()` を admission 必須化し、全 production caller を分類 |
| F2 source由来 capability | out-of-scope | 実装せず、caller自己申告であり層が閉じていないことを docstring に明記 |
| F3 cache/replay class束縛 | out-of-scope | cache preimage、manifest、replayへは入れず、既知限界を明記 |
| F4 sweep未定義名 | closed | keyword-only伝播、全入口への明示引数、admission例外の再送出、実 `_eval_one` build-entry spy test |
| F5 caller分類 | partial | s6/s8a分離と direct materializer caller分類は完了。source bytesとの暗号学的束縛はF2として対象外 |
| F6 CLI authority/immutable | partial | coder CLI 5本の実入口を検査。plain boolがoperator capabilityではない限界を明記。capability化は未実装 |
| F7 mutation独立性 | closed | M1 policy拒否、M2 CLI既定拒否、M3必須signature、M4 sweep class、M5 stock正例を個別nodeに分離 |

### レビュー2

| 所見 | 状態 | 対応 |
|---|---|---|
| 1 resume historical receipt | out-of-scope | 実装なし |
| 2 receipt consumer化 | out-of-scope | 実装なし |
| 3 legacy-unclassified | out-of-scope | 実装なし |
| 4 runbookのflag不足 | out-of-scope | `docs/**` 編集禁止のため未変更。親側の別タスクが必要 |
| 5 T-126 identity漏れ | closed | `REQUIRED_CODE_IDENTITY_PATHS` と独立assertへ追加 |
| 6 coder driver negative test | closed | 5 driverをparameterizeし、flag無し到達0／有りexact CODER trueを検査 |
| 7 docstring過大・過小 | closed | 自己申告分類、機械的pre-build gate、意味/security上advisoryを区別 |

### 受入赤14本

| 範囲 | 状態 | 対応 |
|---|---|---|
| `test_screening_opt_in.py` 2本 | closed・未実走 | sweepの誤ったCODER既定拒否を廃止し、内部で正しいclassを選択 |
| `test_campaign.py` 2本 | closed・未実走 | fake evaluateへ必須admissionを受け渡し、exact stock値を検査 |
| `test_s8b_oracle_driver.py` T080 10本 | closed・未実走 | historical migration basisからclosure fixtureを復元。検査本体は変更なし |

## Materializer caller分類

### `buildcache.build()`

| caller | class | 根拠 |
|---|---|---|
| `pipeline.py` trace/perf | callerのadmissionを伝播 | 実 sourceの分類主体は上位driver |
| `p3_kickoff.py` seed | `STOCK_OR_PINNED` | `assert_pinned_clean()` 後の素のseed build |
| `s3_lock_coverage.py` | `STOCK_OR_PINNED` | no-patch stock control |
| `s5_permutation_coverage.py` | `STOCK_OR_PINNED` | no-patch stock control |
| `between_run_floor.py` | `STOCK_OR_PINNED` | pinned baseline genomeのnoise計測 |
| `s2_verify_calibration.py` | `STOCK_OR_PINNED` | pinned stock trace/perf対照 |
| `backoff_profile.py` | `MACHINE_SWEEP` | `_genome()`による決定論的backoff profile点 |
| `backoff_overthrottle.py` | `MACHINE_SWEEP` | `_points()`の固定・決定論的列挙 |
| `s1_verify_extime_calibration.py` | `MACHINE_SWEEP` | verified known-axes由来の固定`g_rl`を生成しquarantine後build |

### `buildcache.build_v2()`

| caller | class | 根拠 |
|---|---|---|
| `pipeline.py` | callerのadmissionを伝播 | legacy経路と同じ分類値をtrace/perfへ共有 |
| `s8b_floor_campaign.py` の `build_cells()` | `HUMAN_REVIEWED` | ratified/verified freezeのcellをmaterialize |

主な pipeline producer は、S1 direct comparisonとS8b oracleが `HUMAN_REVIEWED`、T-126とstock系が `STOCK_OR_PINNED`、backoff列挙が `MACHINE_SWEEP`、P3 coder driverが `CODER_DERIVED/true` です。判断不能callerはありませんでした。

テスト側の直接callerも、`test_campaign` / `test_build_site_gate` / `test_buildcache_v2` はstock、S8b実build canaryはhuman-reviewedへ更新しています。

## s6/s8a class分離

分離しました。

- `stock` → `STOCK_OR_PINNED`, opt-in false
- s6の固定 `CANDIDATES` → `MACHINE_SWEEP`, opt-in false
- s8aの決定論的部分集合、`ident_all` → `MACHINE_SWEEP`, opt-in false

根拠は、候補がLLM出力をその場で受け取る経路ではなく、module内の固定生成器・有限列挙から再現可能に作られることです。過去のskeleton由来だけを理由に、候補全体を `CODER_DERIVED` とする必要はないと判断しました。

## T080 source closure

検査本体の exact 条件、すなわち `changed=12 / unchanged=51` と期待pointer集合は変更していません。

赤の原因は、E2E fixtureが「一回限りのhistorical migration basis」として現在の作業ツリーをコピーしており、後続waveで変更された `backoff_sweep.py` の3参照を追加changedとして数えたことでした。

fixtureのknown-axes source closureだけを、発行済みT080 receiptの `migration_basis_commit` から `git show` で復元するよう変更しました。現行hashの焼き込み、期待件数の緩和、新しい許容pointerの追加はありません。

## 静的検査

実行済み:

- `python3 -m compileall -q orchestrator`
- 対象ファイル群の `python3 -m py_compile`
- production materializer callのAST全走査: admission欠落 `[]`
- signature静的確認: `build` / `build_v2` / `evaluate` / sweep `_eval_one` が必須keyword-only
- s6/s8a class receipt静的確認
- `git diff --check`
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git status` / docs差分確認: `docs/**` 変更なし

ホストは `pegasus02` です。指示どおり、pytest、build、mutation実走、受入全走は一切実行していません。したがって緑は主張しません。実走nodeidは0件です。

## 波及可能性

静的に確認・更新した共有面:

- `test_campaign.py` の共有 `_mock_pipeline` build/build_v2 fake
- `test_buildcache_v2.py`、`test_build_site_gate.py` の直接materializer caller
- `test_s8b_floor_campaign.py`、`test_s8b_freeze_io.py`、`test_s8b_ratified_freeze.py` の共有build fake
- `test_s1_direct_comparison.py`、`test_s8b_oracle_driver.py` のevaluate consumer
- `test_p3_exploration_namespace.py` のcoder driver public entry
- `test_t126_pegasus_tools.py` のidentity closure

所有外では、3本のrunbookが依然としてflag不足です。また、外部の未探索Python callerはrepo全域検索では見つかりませんでした。

## 親の裁定を仰ぐ点

- `build_admission.py` と新規 `test_build_admission.py` は、禁止に従い未stageです。T-126のtracked-path testは、親がstageする前の現在状態では `build_admission.py` をuntrackedとして拒否します。全走前に親側でstage可能な状態へ移す必要があります。
- runbook 3本の修正はdocs編集禁止のため親側の別作業が必要です。
- F2/F3、レビュー2所見1〜3、F6のrun-scoped capability化は別タスク裁定どおり未実装です。
- caller分類について追加裁定が必要な不明点はありません。

## 総括

閉じた所見: F1、F4、sweep側F5、F7、レビュー2所見5〜7、および赤14本へのコード上の対応を完了しました。

残る所見: F2/F3、historical receipt consumer化、legacy再分類、CLI capability化、runbook修正は射程外です。

懸念: pytest/buildは未実走であり、T-126 tracked-path検査には親による新規ファイルのstageが必要です。