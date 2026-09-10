F1〜F7 の実装差分は完成していますが、pytest child が起動できなかったため全件 `partial（実装済み・未実走）` とします。

## 対応結果

| Finding | 状態 | 対応 |
|---|---|---|
| F1 | partial（実装済み・未実走） | v2 start-only resume を `[s8b-attempt-registry-resume] v2 start-only resume is not marker-atomic` で fail-closed。分類済み v2 の正例対照を追加 |
| F2 | partial（実装済み・未実走） | reserve / observation が marker-bound、classification claim / row と recovery row が非束縛であることを spy-through-real-call で exact pin |
| F3 | partial（実装済み・未実走） | 完全世代 symlink を使い、4下層の直接拒否・上流への例外写像と呼出 assertion・差し替えなし正例を独立 node に追加 |
| F4 | partial（実装済み・未実走） | `_atomic_update_locked()` の無効 lock 直接拒否、v1 上流経路での差し替え到達、実体正例を独立 node に追加 |
| F5 | partial（実装済み・未実走） | v2 reserve の防壁 assert 2件を明示的 `_fail()` に変更 |
| F6 | partial（実装済み・未実走） | M6/M13 を SURVIVED、M6b/M13b を KILLED と再登録する根拠を整備。M7b fixture と M8 fixture を補正 |
| F7 | partial（実装済み・未実走） | test 名を forged v2 の実態へ改名。create/read の profile・slot annotation を v1/v2 union 化 |

主要差分は [s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-fix1/orchestrator/campaign/s8b_attempt_registry.py:1582) と [test_s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-fix1/orchestrator/tests/test_s8b_attempt_registry.py:2410) です。

F2 で意図的に開いたままの範囲は、v2 の classification claim、classification row、recovery row です。分類・回復を marker 経路へ移していません。

## F5 assert の分類

防壁と判定して明示例外へ変更したもの:

- `reserve_attempt_slot()` の `assert consumption_marker is not None`
- 同じく `assert measurement_generation_claim_digest is not None`

どちらも現在は同一の明示的 `_fail()` 防壁です。

内部不変条件として残した adapter 内の全 `assert`:

- `expected_recovery is not None`
- 他世代 registry の `data is not None`
- prelock `snapshot is not None`
- locked update の `old_bytes is not None`
- public read の `payload is not None`
- v2 reserve codec 前の `snapshot is not None`
- classification の `claim_result is not None`
- classification receipt の `receipt_bytes is not None`
- legacy marker の `raw is not None`
- v2 observation codec 前の `snapshot is not None`
- resume の `payload is not None`
- resume の早期明示 gate 後にある `consumption_marker is not None`
- resume 分岐完了後の `resumed_handle is not None`

core 側では `parsed_binding is not None` を内部不変条件として維持しています。

レビューが名指しした codec 選択後の slot-type guard 4件も維持しました。現物では Python の `assert` 文ではなく、明示的な `if type(...) is not ...: _fail(...)` です。

- v2 reservation slot
- legacy observation slot
- v2 resume slot
- legacy resume slot

## 変異登録

| 変異 | 修正後期待 | kill する nodeid / 根拠 |
|---|---|---|
| M6 | SURVIVED | generation 早期拒否を単独除去しても `_publish_create_only` の拒否が残る |
| M6b | KILLED | `test_generation_publish_direct_barriers_adapter_mapping_and_positive` |
| M7b | KILLED | `test_generation_symlink_lower_layers_map_rejection_and_keep_positive`。完全世代を使い、不完全世代・existing destination・enumerator の mask を変異定義から除外 |
| M8 | KILLED | `test_v3_claim_address_separates_measurement_ordinals`。両 slot の `schedule_row_sha256` を同値化し、payload 差を `measurement_ordinal` だけと assertion |
| M13 | SURVIVED | 早期 gate を消しても新しい下流明示例外が残る |
| M13b | KILLED | `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed`。早期・下流拒否を同時除去し、marker-less を通常 update へ流す変異なら、期待拒否が消えて start row が追加される |

これらは静的 kill 根拠です。mutation harness は未実走です。

## 検査

runner へ指定した焦点範囲は次の8 nodeidです。

- `test_forged_v2_profile_is_rejected_but_slot_lookup_is_five_axis`
- `test_generation_publish_direct_barriers_adapter_mapping_and_positive`
- `test_generation_symlink_lower_layers_map_rejection_and_keep_positive`
- `test_atomic_update_locked_direct_guard_maps_upstream_and_keeps_positive`
- `test_v2_start_only_resume_fails_closed_and_classified_resume_stays_open`
- `test_v2_mutation_marker_binding_scope_is_exact`
- `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed`
- `test_v3_claim_address_separates_measurement_ordinals`

結果は2回とも `rc=16`、`child_started=false`、`qstat -Q preflight rc=1` でした。queue-wait-timeout ではないため、指定された timeout override は適用していません。実走した pytest nodeidと緑はありません。

静的検査結果:

- 両変更ファイルの AST parse: 成功
- test module import: 成功
- create/read の `get_type_hints()`: v1/v2 union を確認
- `git diff --check`: 成功
- 171 node 全走: 未実施

## 波及可能性

- `s8b_floor_attempt_launcher.py` は create/read/reserve の所有外 caller。現状はv1 profileと既定 `consumption_marker=None` を使うため、runtime は静的不変です。
- production の `resume_attempt()` caller は見つかりません。F1 は現状の test/API 面だけに作用します。
- F1 は v2 start-only resume だけを狭め、分類済み v2 resume と全v1 resumeを維持します。
- F2 により v2 classification/recovery の非束縛範囲は変わりません。
- F3/F4 の差し替えは test-local。production dependency は変更していません。
- 共有 fixture `test_s8b_holdout_admission._consumed_marker_capability_case` を F1/F2 で再利用しましたが、fixture 自体は未変更です。
- 改名前 nodeid の repo 内参照は0件でした。
- trial registry、holdout replay、scheduler accounting、launcher、既存89+82 node は未実走のため回帰可能性が残ります。

## 総括

- F1〜F7: 全件 `partial（実装済み・未実走）`。`closed` / `regressed` は0件。
- 実走した pytest nodeid: なし。焦点8 nodeは投入前 infra rc=16。
- 残る赤:
  - 期待赤: 観測なし
  - 回帰: 観測なし・未確認
  - infra: `qstat -Q preflight rc=1`
- 変異登録: M6/M13をSURVIVED、M6b/M7b/M8/M13bをKILLEDへ再照準。kill nodeidは上表のとおり。
- 波及可能性: launcher、共有 admission fixture、trial/holdout/scheduler consumer、既存171 node。
- 追加した changed LOC: 240（232追加、8削除）。
- 読めなかった資料: なし。指定5資料を順番どおり全文読了。
- 確かめられなかった事実: pytest焦点走、既存171 node、consumer閉包、mutation matrix。
- commit、git add、push、branch/remote操作は実施していません。