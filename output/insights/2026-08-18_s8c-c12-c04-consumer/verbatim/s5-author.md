## 変更

- `trial_registry.py:217,1812,1908,1946` に lifecycle 状態、重複起動拒否、再起動禁止を追加。JSON key 集合は不変。
- `p3_autonomous_workload_trial.py:2229,3661` に isolation policy 条件付き予約 gate を追加。job、boot、残時間判定は既存 `reservation` に委譲。
- `p3_autonomous_workload_trial.py:3406,3768,3877` に failure-atomic な indeterminate 記録と元例外の再送出を追加。
- `conftest.py:95` に共有 valid reservation fixture を追加。
- C04/C12 predicate と invariant の反転テストを更新。
- 予約拒否3種、no-read、正例、重複起動、failure-atomic、例外順序のテストを追加。

## 現行挙動と変更後の受理集合

- 予約経路: 変更前は `run_trial` が予約 binding を読まず、Pegasus でも起動後処理へ進み得た。変更後は予約不要な OTHER/Linux は従来どおり read せず、必要な isolation policy では起動前に検査し、job不一致・boot不一致・残時間不足を拒否する。
- lifecycle 経路: 変更前は `record_trial_start_once` の内部拒否だけだった。変更後は `reject_started_trial` が start row を先に読み、重複起動を start 記録前に拒否する。
- crash 経路: 変更前は terminal 記録失敗時に包装例外が元例外を隠した。変更後は再起動禁止と indeterminate terminal を独立に試行し、失敗を note に集約して元例外を再送出する。通常の `Exception -> partial` は変更していない。
- site 呼び出し列、`_finish_trial` / `_run_workload` signature、generation budget 3境界は維持。

## 実走

- 構文検査: 変更8ファイルを `compile()` で確認し `syntax-ok 8`。
- 静的検査: C12 reachable call に `read_binding` / `check_reservation` が存在し、verdict は `None`。
- `git diff --check`: 成功。禁止対象ファイルの変更なし。
- pytest nodeid: 未実走。`python3 tools/run_tests.py -q` は exit 16、login headroom の台帳が read-only、`qstat -Q` preflight rc=1 で dispatch 前に停止。
- 既知の意図的赤候補 `test_candidate_freeze_matches_contract_and_generation_chain` は、親側の freeze/docs 未着地のため未確認。回帰赤は観測していない。

## 停止・未達

- commit は作成していない。
- docs、判定器、契約 JSON、凍結 record は編集していない。
- pytest の緑判定は未達。親が commit 後、runner 経由で再実走する必要がある。

## 波及

- `main` は `run_trial` 経由で新 gate の対象となる。
- Pegasus の既存 transport test と transport error test に共有 fixtureを適用。OTHER/Linux の no-read 経路は別テストで固定。
- `p3_s4_loop_trigger_gating` など `run_trial` 外の直接 launch 経路は scope 外。
- lifecycle の永続的な再起動拒否は既存 start row と indeterminate terminal rowで表現し、形式は変更していない。

## 総括

V2-1〜V2-5を実装した。  
M1〜M11を殺す負の対照と正例を追加した。  
コード・テスト以外は変更していない。  
実走だけPegasusのdispatch基盤障害で未達。