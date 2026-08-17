推奨は案 γです。ただし、親 brief の形をそのまま一度に有効化すると、導入 wave が現行 main の D403 実装へ再実行され、main bytes が tip blob と異なるため再び `restart-required` になる循環があります。したがって、γには一度だけの明示的な bootstrap-seed 遷移が必要です。この例外を認めない場合、現 wave で γ を原子的に land することはできません。

静的検査のみ実施しました。pytest は実走しておらず、緑とは記録しません。

## 3 案の判定

| 案 | child-green | non-attributable-only | 待ち手変更 wave | land の独立検証 | 判定 |
|---|---:|---:|---|---|---|
| α: `_verify_red_check_receipt` 内だけ等値 | 発火しない | 発火する | child-green なら land 可 | main/tip blob 等値を Git から再計算可能 | 不採用。実測 22/23 本を覆わない |
| β: main/tip 等値を全経路で要求 | 発火する | 発火する | 両経路とも恒久拒否 | 完全に Git 由来 | I2 違反で不採用 |
| γ: main source へ自己再実行 | 発火する | 発火する | main 版で受入を実行できる | 期待値は Git 由来、実行値は自己申告 | 推奨。ただし seed 遷移必須 |

案 α の挿入点は、待ち手側が [`_verify_red_check_receipt`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3310) 内、land 側が [`verdict == "non-attributable-only"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:762) 内です。呼出し自体が child rc=1 の分岐内にあるため、[`normalized_child_rc == 1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3769) を通らない child-green には効きません。

案 β は、待ち手の投入前共通点 [`tools/dev_wave_wait.py:3700`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3700) と land の verdict 分岐前 [`tools/dev_wave_land.py:743`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:743) に main/tip blob 等値を置けば実装できます。しかし待ち手を編集した tip は必ず main と異なり、child-green にも逃げ道がありません。これは brief I2 の恒久 land 不能そのものです。

## D403 と P1-5

親の P1-5 の読みは正しいです。

- D403 は [`16952-16953`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/decisions.md:16952) で、receipt の実行 source SHA が冗長な理由を「gate 通過が実行 bytes == tip blob を含意するから」と限定しています。
- main source を実行し tip source と異なる γ では、その SHA は `waiter_blob_sha` と同じ意味ではありません。したがって冗長ではなくなります。
- 一方、[`16943-16945`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/decisions.md:16943) は main 比較が待ち手変更 wave を永久拒否すると明記しています。self-bootstrap は定常状態ではこの理由を解消しますが、現行 main 自身は bootstrap protocol を知らないため、初回導入だけは別途解く必要があります。
- 新 field は land が期待 SHA を Git から再計算する材料にはなりますが、「実際にその bytes が実行された」という値は待ち手の自己申告です。I4 に従い、land 側の照合は防御深度であり、独立した narrowing とは数えられません。

## 推奨 γ の実装プラン

### 1. bootstrap-seed を一度だけ許す

[`tools/dev_wave_wait.py:24`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:24) 付近へ、source bytes 内に一意に現れる protocol sentinel を追加します。

新設する判定は次の署名にします。

```python
def _verified_waiter_authority_source(
    effects: _Effects,
    repo: Path,
    tested_main: str,
    tested_tip: str,
    stage: str,
) -> _WaiterAuthoritySource
```

`_WaiterAuthoritySource` は少なくとも main/tip の blob SHA、raw source、raw SHA-256、seed/active の区分を持ちます。

受理する protocol 状態は exact に二つだけです。

- seed: tested main source に sentinel がなく、tested tip source に exact 1 件ある。この導入 receipt に限り、実行 source == tip を要求する。
- active: main と tip の双方に sentinel が exact 1 件ある。実行 source == main を要求する。
- main に sentinel があるのに tip にない、重複、非 blob、両側なしは fail-closed。

これにより導入 wave は既存 D403 と同じ tip 権威で一度だけ land でき、land 後は main 自身が protocol を持つため seed 分岐へ戻れません。この例外は親の provisional plan にはないため、段 4 で明示裁定し、新 D で D403 を部分 supersede する必要があります。

### 2. main source の取得と自己再実行

[`_red_gate_blob_sha`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:2227) と checker の実装形を再利用し、main/tip waiter の object type が `blob` であること、`cat-file blob` の内容を `hash-object --stdin --no-filters` で再照合する helper を [`tools/dev_wave_wait.py:2270`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:2270) の前へ置きます。

実行 predicate は次の署名にします。

```python
def _ensure_waiter_main_authority(
    *,
    effects: _Effects,
    repo: Path,
    tested_main: str,
    tested_tip: str,
    waiter_argv: Sequence[str],
    bootstrap_attempted: bool,
) -> _WaiterAuthorityResult
```

- seed では running SHA == tip raw SHA を要求して返す。
- active かつ running SHA == main raw SHA なら返す。
- active で不一致なら、tested main の検証済み raw source を外部 temp fileへ fsync して `python3 -I <temp> <元の waiter argv>` で `os.execve` する。
- bootstrap 後も不一致なら二度目は実行せず `restart-required` rc=70。
- Git/source取得不能、非 blob、exec失敗も受入 command 投入前に fail-closed。

[`_WaiterSourceBinding`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:44) と [`_initialize_waiter_source_binding`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:196) は、canonical path に加えて bootstrap temp の exact path/inode を非追従で束縛できるよう拡張します。束縛後は temp pathname を unlink し、FD は process lifetime 保持します。保証は従来どおり bound source inode bytes までで、Python が compile した bytecode の証明とは書きません。

[`_Effects`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:500) に次を追加します。

```python
exec_waiter_source: Callable[[bytes, Sequence[str]], NoReturn] | None
```

default wiring は [`_default_effects`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:1401) に置きます。

### 3. gate の位置

既存の [`_verify_waiter_source_bytes`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:1860) は tip 照合のまま残さず、上記 predicate に置換します。両方を残すと main != tip の正当な bootstrap 実行が D403 に再拒否されます。

呼出し位置は現在と同じ、prerun fingerprint 確定後、child command より前の [`3694-3722`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3694) です。ここなら final tested tip と `claim_context.main_sha` が揃い、child-green/non-attributable の分岐前なので両経路を覆います。

exec 前には次を処理します。

- 内部 validated message temp を削除。
- `ACQUIRED` なら既存 `_cleanup_lifecycle` で lease を解放してから exec。
- `HELD_SELF` は現契約どおり release せず execし、外側の所有者へ終端 release を残す。
- cleanup が失敗したら exec せず rc=74。
- bootstrap 回数を内部環境値で 1 回に制限する。

元の waiter argv は [`main:4190-4223`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:4190) で parse 前に保存し、[`run_acceptance`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:4078) と `_run_acceptance_attempt` へ渡します。

### 4. receipt v5

[`_RECEIPT_SCHEMA_VERSION`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:232) を `dev-wave-acceptance-receipt/v5` に上げ、[`_acceptance_receipt_bytes`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:2820) に次を追加します。

```python
waiter_source_sha256: str
```

これは gate 時点の bound source raw SHA-256 です。既存 `waiter_blob_sha` は tested tip の Git blob object ID のまま維持し、意味を混ぜません。

[`_run_acceptance_attempt:3782-3805`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3782) は、authority predicate が返した tip blob ID と running source SHA を receipt builder へ渡します。

### 5. land の独立検証

[`_runner_tree_entry`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:619) を path 引数付きの汎用 `_tree_blob_entry(repository, revision, path)` にし、waiter と runner の双方で object type と object ID を取得します。

[`_verify_acceptance_receipt`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:649) の verdict 分岐より外側で、両経路共通に次を検証します。

- tested tip waiter が blob。
- receipt の `waiter_blob_sha` == Git 由来 tip object ID。
- main/tip source の protocol 状態が seed または active の exact 形。
- seed なら expected raw SHA = tested tip source。
- active なら expected raw SHA = tested main source。
- receipt の `waiter_source_sha256` == expected raw SHA。

Git から再計算できるのは object type、object ID、source内容、期待 SHA、protocol状態です。`waiter_source_sha256` が実際の実行体を観測したという部分だけは自己申告です。

## schema v5 の全波及先

- [`tools/dev_wave_wait.py:232`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:232): v5 定数。
- [`tools/dev_wave_wait.py:2820`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:2820): builder 引数、形式検査、field追加。
- [`tools/dev_wave_land.py:70-97`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:70): schema 定数と exact field 集合。
- [`tools/dev_wave_land.py:573-583`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:573): `_receipt_object` の exact field 検査。呼出し元は release digest と acceptance verification の2か所。
- `orchestrator/tests/test_dev_wave_wait.py`: exact set、v4 literal、receipt fixture。
- `orchestrator/tests/test_dev_wave_land.py`: receipt factory、tamper matrix、実 waiter E2E。
- `docs/pegasus-runbook.md` §7.3。
- 新 D を spool fragment から追加し、D403 の tip gate と D487 の v4 schema を部分 supersede。D403/D487 本文は書き換えない。
- 発行済み v4 receipt は変換・fallback受理せず撮り直す。

`tools/check_acceptance_reds.py`、`tools/run_tests.py`、`tools/check_docs.py` に schema consumer はありません。`check_docs.py` は canonical waiter が regular file であることだけを検査しているため変更不要です。

## 既存 exact 述語との整合

- `argv == ["python3","tools/run_tests.py"]` と `resolved_runner_path == "tools/run_tests.py"` は変更しません。自己再実行されるのは外側の waiter process で、receipt の child command はそのままです。
- v4 の field 集合へ新 field を黙って足すのは不可です。v5 が必須です。
- D403 の tip gate は置換対象です。併存させてはいけません。
- D487 の checker/runner main==tip gate は [`_verify_red_check_receipt:3358-3364`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3358) と land の非帰属分岐内に残します。
- child-green の runner 受理集合は変更しません。

## runner の child-green 束縛

直接の main runner 実行には実在する衝突があります。

- land は [`682-683`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_land.py:682) で argv と resolved path を exact pin しています。
- main blob を `python3 -c ...`、stdin、または抽出 temp pathで実行すれば、いずれかまたは両方が変わります。
- tip の `tools/run_tests.py` をそのまま起動すれば exact pin は保てますが、実行 bytes は tip 側です。
- main==tip を child-green にも広げると、D487 が既に非帰属経路を閉じているため、runner変更 wave は全経路で land 不能になります。
- runner 自身へ self-bootstrap を実装すれば表面 argv は維持できますが、待ち手と同じ初回 rollout、実行値の自己申告、source binding が新たに必要です。

したがって runner child-green 束縛は本 wave の scope 外とし、裁定パッケージへ返すのが妥当です。現状を pin する [`test_child_green_receipt_does_not_require_main_tip_runner_equality`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/orchestrator/tests/test_dev_wave_wait.py:4219) と [`test_child_green_accepts_different_main_and_tip_runner_blobs`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1002) は変更しません。

## テスト計画

### 改訂する既存テスト

`orchestrator/tests/test_dev_wave_wait.py`

- `test_success_receipt_binds_tip_argv_rc_fingerprints_holder_waiter_and_scheduler`: exact field 集合へ `waiter_source_sha256`、schema v5、gate が command 前であることを追加。
- `test_no_merge_waiter_bytes_mismatch_blocks_submission_and_releases`: active mismatch が拒否ではなく、lease cleanup 後に検証済み main source と元 argvで execへ移る期待へ変更・改名。
- `test_waiter_bytes_unverifiable_is_restart_required_before_submission`: tip lookup を main/tip authority source lookupへ変更し、再bootstrap不一致を追加。
- `test_waiter_binding_failure_detail_omits_exception_message_and_path`: observed revision を `tested_main` と authority mode に更新。
- `test_waiter_source_binding_accepts_regular_direct_source_and_inode_replacement`: canonical binding 自体の pin に限定。
- `test_tip_waiter_bytes_sha256_hashes_blob_without_text_decoding`: main/tip authority source が binary-safe に raw SHA を作り、object IDを再照合するテストへ置換。
- `test_flake_only_publishes_v4_receipt_with_separate_nodeids`: v5 へ改名・更新。
- `test_acceptance_held_self_waiter_bytes_mismatch_blocks_without_release`: held-self を releaseせず bootstrapする期待へ変更。
- `test_real_waiter_process_rejects_merged_tip_with_different_waiter_bytes`: main が waiter を更新した場合に main sourceへ再実行して成功する期待へ変更。
- `test_real_waiter_process_accepts_merged_tip_with_same_waiter_bytes`: v5 と source SHA を追加。
- `test_retry_success_uses_only_success_attempt_values_and_v4_schema`: v5 exact setへ変更。
- `test_acceptance_receipt_field_detail`:不正な `waiter_source_sha256` の case を追加。

補助 fixture の `_FakeEffects`、`_WAITER_GATE_EVENTS`、`_valid_receipt_arguments` も新 effect・新 field に合わせます。

`orchestrator/tests/test_dev_wave_land.py`

- `_Repo._acceptance_receipt`: v5 と Git 由来 expected source SHA を生成。
- `test_land_accepts_receipt_bound_to_wave_tip_and_emits_digest`: main source SHA の照合を追加。
- `test_land_rejects_tampered_acceptance_receipt`: `v4-schema`、missing/invalid/mismatching `waiter_source_sha256` を追加。
- `test_real_waiter_receipt_is_consumed_by_real_land_end_to_end`: child-green v5 と main source SHA を pin。
- `test_real_non_attributable_waiter_receipt_passes_real_land_end_to_end`:非帰属経路でも同じ global authority を pin。

### 新設するテスト

`orchestrator/tests/test_dev_wave_wait.py`

- `test_waiter_authority_allows_only_seed_main_without_protocol_tip_with_protocol`
- `test_waiter_authority_selects_tested_main_after_protocol_activation`
- `test_waiter_authority_rejects_protocol_removal_or_duplicate_marker`
- `test_active_waiter_mismatch_bootstraps_before_child_green_submission`
- `test_active_waiter_mismatch_bootstraps_before_non_attributable_submission`
- `test_waiter_bootstrap_is_single_shot`
- `test_waiter_bootstrap_exec_failure_is_fail_closed_after_owned_lease_cleanup`
- `test_waiter_bootstrap_binding_accepts_exact_regular_temp_inode`
- `test_waiter_bootstrap_binding_rejects_symlink_path_or_inode_race`
- `test_real_waiter_edit_executes_main_waiter_and_emits_distinct_tip_blob_and_main_source_hash`

`orchestrator/tests/test_dev_wave_land.py`

- `test_land_accepts_child_green_with_different_waiter_blobs_and_main_source_hash`
- `test_land_accepts_non_attributable_with_different_waiter_blobs_and_main_source_hash`
- `test_land_rejects_waiter_source_hash_mismatch_for_both_verdicts`
- `test_land_waiter_authority_uses_tested_main_not_current_main`
- `test_land_rejects_waiter_protocol_downgrade`
- `test_land_rejects_non_blob_main_or_tip_waiter`
- `test_land_accepts_seed_transition_only_when_main_lacks_protocol`

## 変異検査候補

- [`tools/dev_wave_wait.py:3700`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/tools/dev_wave_wait.py:3700) の global authority 呼出しを rc=1 分岐内へ移す。child-green bootstrap テストと real waiter-edit E2E が赤になる。
- 新 `_ensure_waiter_main_authority` で active の期待 revision を `tested_main` から `tested_tip` に変える。main/tip divergence の unit test と real E2E が赤になる。
- land の expected raw SHA を tested main ではなく tested tip から計算する。両 verdict の divergence 受理テストが赤になる。
- land の protocol downgrade 拒否を削る。`test_land_rejects_waiter_protocol_downgrade` が赤になる。
- schema を v4 のままにする、または新 field を exact 集合から外す。v4拒否・missing field tamper・exact set テストが赤になる。
- bootstrap 回数制限を削る。`test_waiter_bootstrap_is_single_shot` が赤になる。

## runbook §7.3 の改訂箇所

- [`840-845`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/pegasus-runbook.md:840) の現行文言  
  「`--log-file` が指す path には最後の内部 attempt の log が残る。受領証は成功 attempt の値だけを収録し、path も版 (`dev-wave-acceptance-receipt/v3`) も root field も変わらない。」  
  `v5` へ改め、`waiter_source_sha256` も成功 attempt の値だけを収録すると追記。

- [`858`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/pegasus-runbook.md:858) の現行文言  
  「outer receipt の schema は `dev-wave-acceptance-receipt/v4` で、v3 は受理しない。」  
  「v5で、v4以前は受理せず撮り直す」へ変更。

- [`865-872`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/pegasus-runbook.md:865) の現行文言  
  「`tools/run_tests.py` または `tools/check_acceptance_reds.py` を変更した wave は経路 (ii) を使えない。」および「この2つを触る wave は完全に緑の走行でしか land できない」  
  runner/checker の制約は維持しつつ、waiter変更 wave は tested main waiterへ自己再実行するため両経路を使える、と明確化。

- [`877-884`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/pegasus-runbook.md:877) の現行文言  
  「`stage=restart-required` (rc=70) は待ち手を再起動しろという意味である。」「束縛した自 source の bytes と、その走行が束縛する tip の blob 内容を照合」「新しい tip の木から待ち手を起動し直す」  
  tested main sourceとの照合、active mismatch時の自動再実行、一度だけのbootstrap、二度目/exec不能時だけ restart-required、という規範へ全面置換。

- [`885-888`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob/docs/pegasus-runbook.md:885) の現行文言  
  「canonical direct 起動、または origin が束縛 source と同一 inode を指す file loader経由」「gate を持たないコードで既に起動している待ち手は本契約の被覆外」  
  canonical sourceに加え、bootstrap temp の検証済み inode/FDも保証範囲へ追加し、compile bytesは依然保証外と明記。seed receipt 1本の限定条件もここへ記録。

## 総括

- 推奨案は γ であり、active 後は child-green と non-attributable-only の双方を覆います。
- β は land が完全に独立検証できますが、待ち手変更 wave を全経路で永久拒否するため I2 違反です。
- α は実装容易かつ独立検証可能でも、実測 22/23 本の child-green を覆わず T-1283 の中核を閉じません。
- γ の実行 SHA は land から見れば自己申告であり、防御深度です。Git 由来の期待値と混同してはいけません。
- D403 の「SHA field は冗長」という理由は tip 束縛に限定されており、main 束縛下では親 P1-5 の読みが正しいです。
- 現行 main は bootstrap protocol を持たないため、厳密な γ を例外なしで一度に land することはできません。
- 一度だけの seed 遷移を段 4 で明示裁定し、receipt v5 と protocol sentinel で再発不能にするのが実装可能な閉じ方です。