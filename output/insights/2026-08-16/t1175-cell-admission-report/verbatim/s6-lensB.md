## 総括

- **NO-GO**。提示された状態を前提とする静的追跡では、走 a・走 b とも `report.json` writer へ到達する。
- ただし pending critic の accounting 確定は裁定 2-3 の禁止文と明確に衝突し、受理集合を追加で広げている。親の再裁定が必要である。
- 事前登録 P1 の「全 cell admitted の正常 3 workload build trial」が存在せず、正常系の過剰拒否を検出できない。
- D96 が要求する新しい decision 記録も未作成で、現行 D217 はなお report 非公開を正本としている。
- pytest・実走は行っていない。確認したのは未コミット差分、限定検索、`git diff --check`、4 ファイルの AST parse である。

## 走 a / 走 b の追跡結果

### 走 a

**到達する。静的な停止関門は見つからない。**

1. coder parse 失敗は `_invoke` が invalid role event に変換する。`p3_autonomous_workload_trial.py:1499-1528`
2. cell は `outcome="coder-invalid"`、`stop_reason="role-invalid"` となる。`p3_autonomous_workload_trial.py:2646-2665`
3. active accounting は既に `finally` で一度だけ `partial-generation` として append される。`p3_autonomous_workload_trial.py:2785-2791`
4. 正常復帰側の admission 呼び出しで `AutonomousTrialError` が exact failure decision へ変換される。pending は空なので、問題の accounting loop は一度も回らない。`p3_autonomous_workload_trial.py:2182-2188,1775-1846`
5. `status="partial"`、pending 無し、decision 有りを満たす。`p3_autonomous_workload_trial.py:2242-2267`
6. completeness では terminal 不在が role-invalid に対して許容され、role history、attempt bijection、payload receipt、既存 accounting pair を通る。`autonomous_trial_completeness.py:1265-1290,1457-1604,1780-1924,1997-2016`
7. 3 workload の未処理 suffix は最終 failure cell により説明される。`autonomous_trial_completeness.py:1713-1724`
8. Layer 3 chain は persisted report 不在と独立 admission 失敗を再導出して failure cell を免除する。`autonomous_trial_completeness.py:2243-2260`
9. journal hash 再検査後、`_write_json_atomic` の呼び出しへ到達する。`p3_autonomous_workload_trial.py:2370-2376`

診断原因は `report.cells[0].generations[0].roles.coder` に残る。具体的には `status="invalid"`、`error_type="AutonomousTrialError"`、`error=<JSON decode の診断文>`、`error_artifacts=<payload/envelope の path/hash>` である。`stop_reason="role-invalid"` と `outcome="coder-invalid"` も併存する。admission decision の `error` は後段の Layer 3 failure であり、coder 原因を見る場所ではない。

raw response は parse 前に保存されるが、invalid event にはその path/hash が無い。これは裁定済み scope 外の既知制約である。

### 走 b

**到達する。静的な停止関門は見つからない。**

1. planner/coder/auditor 後の `KeyError('build_start')` でも、active accounting は `_run_workload` の `finally` で一度だけ確定する。`p3_autonomous_workload_trial.py:2785-2791`
2. caller の except が `fatal_error={"type":"KeyError","message":"'build_start'"}` と `supervisor-error` event を作り、構築済み generation を cell に収める。`p3_autonomous_workload_trial.py:2114-2147`
3. except 内の admission 呼び出しが exact failure decision を作る。`p3_autonomous_workload_trial.py:2148-2153,1775-1846`
4. `supervisor-error` は accounting より後、`run-finish` より直前になるため terminal 配置を満たす。`autonomous_trial_completeness.py:1291-1321`
5. harness を持たない最終 generation は supervisor-error branch で許容される。`autonomous_trial_completeness.py:1620-1634`
6. suffix、accounting、bijection、payload receipt、Layer 3 chain、hash 再検査を経て writer 呼び出しへ到達する。`p3_autonomous_workload_trial.py:2376`

`_write_json_atomic` 自身には JSON serialization、exclusive tmp open、write、fsync、replace の既存例外点が残る。`p3_autonomous_workload_trial.py:1285-1295`。ただし両新設テストは実際の writer を通り、disk 実在と decode 後の返却値一致をそれぞれ固定している。`test_p3_autonomous_workload_trial.py:2999-3001,3082-3084`

## must-fix

### 1. pending accounting の処理が裁定 2-3 と一致しない

**主張:** admission failure 時に pending accounting を新規 append する経路があり、裁定の「failure 経路で追加 append しない」に反する。走 a・bでは pending が空なので重複しないが、成功 harness 後の finalizer failure という別の受理集合を追加している。

**根拠:** `ruling.md:80-86` は追加 append を禁止する一方、実装は pending ごとに state を `partial-generation` へ変え `_append_generation_accounting` を呼ぶ。`p3_autonomous_workload_trial.py:1800-1824`。二重確定拒否は `p3_autonomous_workload_trial.py:1154-1156` にあり、既に確定済みの走 a・bへ二重 append は発生しない。

**成果物への影響:** 現状では `pending_critic_disposition.count=1` の trial に新しい `generation-accounting(state=partial-generation)` が試行台帳へ増え、その report が裁定外に受理される。単純に append を削れば、同 shape は accounting bijection で report 非公開へ戻る。

**直し方:** 親が先に再裁定すること。現裁定を維持するなら回復対象を accounting 確定済みの cell に限定し、pending を持つ finalizer failure は fail-closed に戻す。count=1 も救うなら、2-3 を明示的に改裁定し、追加受理集合と変異期待を登録し直す。

### 2. 正常 3-workload build の positive control が無い

**主張:** 事前登録 P1「全 cell admitted の正常 3 workload build trial」が実装されていない。

**根拠:** P1 は `ruling.md:143-154`。既存の 3-cell positive fixture は `do_build=False` である。`test_autonomous_trial_completeness.py:477-486,635-688,886-891`。既存 build producer test は `["ycsb-a"]` 一件だけで、Layer 3 chain も stub 化している。`test_p3_autonomous_workload_trial.py:2290-2358`、特に `:2314,2341`。

**成果物への影響:** 新述語または chain が正常な複数 build cell を過剰拒否しても、`status="complete"` から `partial` または report 不在へ変わる回帰を検出できず、certified 選択と試行台帳の report 参照が欠落し得る。

**直し方:** `["ycsb-a","ycsb-b","ycsb-c"]`、`do_build=True`、全 decision positive の producer test を追加し、`status=="complete"`、disk report 実在、全 campaign の実 Layer 3 chain 通過を固定する。chain 全体を no-op にしてはならない。

### 3. D96 の新しい decision 記録が未了

**主張:** 受理集合変更と同じ変更単位に必要な新 D が無い。これは author の権限境界上は親作業だが、land 前の must-fix である。

**根拠:** 裁定要求は `ruling.md:111-116`。D96 は新 D と境界テストの同時更新を要求する。`docs/decisions.md:4269-4279`。現行 D217 はなお finalizer failure を伝播し report を公開しないと定める。`docs/decisions.md:10249-10254`。author も未了を明記している。`author.md:68-71`

**成果物への影響:** コードは partial report を受理する一方、decision 台帳の参照は「report 非公開」のままとなり、同じ試行台帳・report v3 の受理根拠が正本上で矛盾する。

**直し方:** 親が spool fragment で新 D を起こし、D217 の該当部分だけの supersede、維持する fail-closed 境界、v3 据え置き理由、pending accounting の再裁定結果を同じ変更単位へ入れる。

## 回帰リスク

静的には shared positive predicate は従来の schema/status/classification 条件と等価で、正常 admitted cell を直ちに拒否する差は見つからない。ただし未実走のため、直接影響を受ける既存 nodeid は少なくとも次である。

- `test_p3_autonomous_workload_trial.py::test_run_trial_build_public_entry_passes_exploration_layout_to_trigger`
- `test_p3_autonomous_workload_trial.py::test_build_cell_admission_precedes_critic_invocation`
- `test_p3_autonomous_workload_trial.py::test_build_post_admission_invalid_critic_keeps_positive_admission`
- `test_p3_autonomous_workload_trial.py::test_critic_invalid_cannot_drop_build_admission_decision`
- `test_p3_autonomous_workload_trial.py::test_cell_admission_failure_is_not_converted_to_supervisor_error`
- `test_autonomous_trial_completeness.py::test_build_file_verification_with_cells_still_requires_campaign_root`
- `test_autonomous_trial_completeness.py::test_campaign_identity_is_pinned_without_producer_helper_oracle`
- `test_autonomous_trial_completeness.py::test_campaign_chain_declares_certified_acceptance_purpose`
- `test_autonomous_trial_completeness.py::test_campaign_chain_reads_legacy_layer3_without_epoch`
- `test_autonomous_trial_completeness.py::test_t428_workload_campaign_epoch_and_old_root_nonwrite`
- `test_autonomous_trial_completeness.py::test_campaign_chain_rejects_missing_persisted_report`

## nit / backlog

- `_MalformedRecordingCritic` を coder fixture としても使っており、名前が実際の役割と一致しない。成果物値や受理集合への影響はない。
- `is_positive_cell_admission_decision` の docstring は “exact” と呼ぶが、未知 key の閉集合までは検査しない。現行の後段 exact receipt 検査が残るため、この差分による成果物変更は確認できない。

## 反証された懸念

- **走 a・bの二重 accounting:** 成立しない。両方とも active accounting が `_run_workload.finally` で確定し、pending entry を持たないため、finalizer 内の loop は回らない。
- **journal terminal 配置の破壊:** 成立しない。新しい admission failure event は作らず、既存 `run-finish.cell_admission_failures` へ投影している。
- **suffix 関門の残存:** 成立しない。exact failure cell が唯一の最終 cellで `partial` の場合に限り通る。
- **admitted campaign の failure 詐称:** 成立しない。persisted Layer 3 不在と独立 admission 失敗の両方を再導出する。
- **admitted peer までの免除:** 成立しない。mixed `[admitted, failed]` では admitted peer の chain 検査が維持される。
- **F332 の disk 実在未固定:** 成立しない。正常復帰側・supervisor-error 側の双方が 3 workload で `is_file()`、disk decode、返却 report 一致を固定する。
- **診断原因が report に無い:** 成立しない。coder の invalid role event に error type/message が残る。ただし raw response の直接参照欠落は既知の scope 外である。
- **scope 外 4 件への侵入:** 成立しない。差分は production 2 ファイルと test 2 ファイルだけで、`build_start`、raw response projection、`trial_registry` formal receipt、`verify_autonomous_trial_files` の root 要求は変更されていない。