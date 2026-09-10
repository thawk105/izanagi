## 総括

7 site を共通 persisted COMMIT helper へ結線し、lock/WAL の同一 snapshot 契約も実装した。  
受理集合は、有効な verify・receipt・lock 束縛を保持する COMMIT のみに縮小した。  
指定負例 7 件と lock 差替え負例 1 件、S8B pin を追随した。  
pytest は dispatch 障害で未実走。静的検査は成功。commit は作成していない。

## 7 site それぞれの現行の受理・拒否挙動 (変更前)

1. `backoff_requested_us`
   - epoch、campaign classification、attempt topology、source identity は検査。
   - verify の `certified=True` と receipt の operation/variant/id の一部だけを独自確認。
   - anomalies、terminal payload、lock SHA、receipt evidence の不一致を受理し得た。

2. `s1_report`
   - session identity、一意 build/COMMIT、`verify_configs`、fitness を検査。
   - 保存済み verify record と receipt を検査せず sample 化し得た。

3. `s8b_oracle_report`
   - outcome、stage topology、attempt binding、`certified` を検査。
   - anomalies と durable receipt が不正でも completed row になり得た。

4. `s6_sort_sweep::_replay_outcome`
   - `wal.replay()` の `state.committed` だけで `replayed-certified` を返した。

5. `s8a_trigger_sweep::_replay_outcome`
   - S6 と同様に COMMIT の存在だけで `replayed-certified` を返した。

6. `backoff_repro::_bench_tps`
   - BENCH_DONE 後の COMMIT だけで TPS を certified 値へ昇格した。

7. `paper_story_a2_certification::_raw_cell_from_wal`
   - `certified=True` なら anomalies と receipt を見ず `pass` へ射影し、`observed-positive` の根拠にできた。

## 実装した内容 (file:line、site ごと)

- [backoff_requested_us.py:444](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/backoff_requested_us.py:444)
  - 全 COMMIT を helper へ通し、失敗を `RuntimeError` へ変換。
  - 弱い独自 certified/receipt 判定を削除。

- [s1_report.py:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s1_report.py:293)
  - 一意 COMMIT を helper へ通す。
  - 失敗を `persisted_certification_invalid` issue にして sample を不受理化。

- [s8b_oracle_report.py:1392](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:1392)
  - window の一意 COMMIT を helper へ通す。
  - 失敗を row の `protocol_violation` 理由へ追加。

- [s6_sort_sweep.py:402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s6_sort_sweep.py:402)
  - 同一 snapshot を既存 WAL validators と projector に渡し、最終 COMMIT を helper で検査。

- [s8a_trigger_sweep.py:501](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8a_trigger_sweep.py:501)
  - S6 と同じ結線を実装。

- [backoff_repro.py:82](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/backoff_repro.py:82)
  - TPS を昇格する各 COMMIT を helper で検査。

- [paper_story_a2_certification.py:2574](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/paper_story_a2_certification.py:2574)
  - COMMIT cell を correctness/performance へ射影する前に helper で検査。
  - 失敗を `CertificationError` に変換。

## 同一 snapshot 契約の実装

全 7 site で次の順序を実装した。

1. lock bytes を取得し SHA-256 を導出。
2. 同じ bytes から必要な epoch/lock identity を判定。
3. WAL records を一度取得。
4. lock を再取得して SHA-256 一致を要求。
5. 一致した場合だけ helper を呼ぶ。

不一致は helper より前に拒否する。S1 に lock 差替え負例を追加した。A2 の frozen mapping でも同じ lock entry を再取得する。

## 凍結 pin の追随内容

- `s8b_oracle_report.py` SHA-256:
  `6563483e13b7fa556cfbb743e86b9509c89c464dbef230addae506a783930de8`
- [test_s8b_oracle_manifest.py:61](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_manifest.py:61)
  - `PIN_GATE_SPEC_SHA256`:
    `c52ffcc6dc228d3462368b9f6ec7e050f8f818216a343f944e6a7591b9a4ceca`
- [test_s8b_oracle_manifest.py:90](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_manifest.py:90)
  - 独立 `PIN_GATE_SPEC_RAW` の report SHA を更新。

`s8b_oracle_manifest.py` は source bytes を実行時に計算する validator で、更新対象となる literal は存在しなかったため変更していない。

## 追加したテスト (node id 一覧)

- `test_s1_report.py::test_persisted_certification_invalidates_sample[s1]`
- `test_paper_story_a2_certification.py::test_raw_cell_requires_persisted_certification[a2]`
- `test_s6_sort_sweep.py::test_replay_outcome_requires_persisted_certification[s6]`
- `test_s8b_oracle_report.py::test_assess_window_requires_persisted_certification[s8b]`
- `test_s8a_trigger_sweep.py::test_replay_outcome_requires_persisted_certification[s8a]`
- `test_backoff_consumers.py::test_backoff_repro_requires_persisted_certification[backoff-repro]`
- `test_backoff_requested_us.py::test_reference_records_requires_persisted_certification[backoff-requested-us]`
- `test_s1_report.py::test_lock_replacement_during_wal_read_invalidates_persisted_samples`

## 変異の単一理由性の確認結果

- M7/S1: session、COMMIT、receipt は有効。anomalies を見るのは helper だけ。
- M8/A2: 既存 `_raw_verify_record` は `certified=True` を pass にするため、helper だけが anomalies を拒否。
- M9/S6: snapshot/projector は固定済みで、helper 呼び出しだけが anomalies を拒否。
- S8B: stage/outcome/attempt/receipt は有効で、既存 report 判定は anomalies を見ない。
- S8A: S6 と同じ単一理由。
- backoff repro: BENCH_DONE と receipt は有効で、helper 以外の certification 判定はない。
- backoff requested: upstream admission/topology を固定した入力で、helper だけが anomalies を拒否。
- snapshot 負例: lock SHA 不一致で helper 呼び出し前に拒否されることを検査。

M1〜M6、M10〜M13 は単位 1 の所有範囲であり変更していない。

## 実走した pytest の nodeid と結果

pytest の実走成功は 0 件。

次の二範囲を `tools/run_tests.py` で起動した。

- 上記新設 8 node
- 変更した全 test file、および `test_plain_runner_coverage.py`、`test_campaign_import_invariant.py`

両方とも `qstat -Q preflight rc=1`、child 未起動、runner rc=16。緑とは扱っていない。

静的検査は以下が成功した。

- 全変更 Python file の `py_compile`
- production/test module import
- `git diff --check`
- 変更 15 path がすべて所有範囲内であること
- report SHA、`PIN_GATE_SPEC_RAW`、`PIN_GATE_SPEC_SHA256` の相互一致
- `artifact_admission.py` が未変更であること

## 未実走・未完の範囲

実装上の未完はない。以下は実装済み・未実走。

- 変更した test file 8 件の全 node
- 新設 8 node
- `test_plain_runner_coverage.py`
- `test_campaign_import_invariant.py`
- S8B manifest の generator/pin 検査
- 波及先の `test_bench_first_real_wal.py`

## 所有外への波及可能性 (静的列挙)

- `test_bench_first_real_wal.py` は `backoff_repro._bench_tps()` を直接呼ぶ。単位 1 で receipt fixture は追随済みだが未実走。
- `test_s8b_oracle_driver.py` は report module と generator source hash を消費する。
- `commit_receipt_support.py` を S1、S8B、A2、backoff fixture が共有する。file 自体は未変更。
- S6/S8A の resume 呼出元は、receipt 不完全な保存 COMMIT で `replayed-certified` を返さなくなる。
- A2 の `_raw_cell_from_wal()` を呼ぶ再構築経路 2 箇所も同じ拒否を受ける。
- 既存保存成果物に verify/receipt/lock 束縛の欠落があれば、新しい certified 主張には使えない。これは意図した受理集合縮小。
- 新 test file は作っていないため plain-runner allowlist の追加は不要。