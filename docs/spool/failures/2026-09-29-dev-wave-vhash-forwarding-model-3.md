---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-model
seq: 3
---

## 新規

### {{F:model-checker-false-counterexample-from-duplicate-timestamps}}. 小モデル検査器が時刻の一意性を初期状態でしか検査せず、並行 forwarding の同時刻選択による偽の反例を出した [恒真ゲート]

- 事象: VHash の選択的 forwarding の小モデル (`tools/vhash_forwarding_model/`) で、v1+O1 が場面 S10 で閉路反例 (39 step) を出し、段 6 の fix 報告は「O1 は安全でない」と読める結果を返した。親が反例列を読むと、T と W が forwarding 後にともに時刻 26 を使っていた。一次資料に載せる前に発見した (near miss)。
- 根本原因: 空き時刻の計算が、他 txn が forwarding 候補として選んでまだ確定していない時刻を「使用中」に数えなかった。時刻の一意性 (仕様 R1) は `State` の生成時に初期版と開始時刻だけで assert しており、到達状態では検査していなかった。初期状態で成り立つ不変条件を、並行して値を選ぶ操作のあるモデルで全状態の保証と見なした。
- 恒久対応: 空き時刻の計算に候補時刻を含め、探索器が全到達状態で `check_timestamp_uniqueness` を実行して破れたら例外で止める (`tools/vhash_forwarding_model/model.py`)。旧挙動で発火することを `orchestrator/tests/test_vhash_forwarding_model.py::test_s10_old_target_allocation_violates_timestamp_uniqueness` が固定し、検査を外す変異 MU10b がこの test で KILLED になることを確かめた (`output/insights/2026-09-29/vhash-forwarding-model/README.md` §8・§9)。{{D:vhash-forwarding-model-spec}} の決定 5 (「反例なし」は範囲付きでのみ書く) と合わせ、反例は列の中身 (時刻と持ち主) を読んでから結論にする。
- 再発検知: 探索中の `TimestampCollisionError` (fail-closed)。モデル検査器を新設する wave は、仕様の不変条件を初期状態の assert でなく全到達状態の検査として実装しているかを段 6 レビューのレンズに入れる。

## 再発

### F242

- **再発: 2026-09-29** (dev-wave-vhash-forwarding-model)。`tools/` に新 package (production file) と新 test file を足したのに、親の焦点走を新 test file と `test_pytest_collection_config.py` だけにし、`DW-O26` が名指す inventory test (`test_official_perf_closure.py`) と file 集合列挙のメタテスト (`test_plain_runner_coverage.py`) を含めなかった。段 6 の静的レビュー 2 本・焦点再レビュー 2 巡・docs レビューはどれも気づかず、受入全走の初回で赤 2 件 (探索の打ち切り判定の `perf_counter` が性能計測の述語として検出、test file に自走 harness が無い) が出て、fix 1 巡と受入 1 回を余分に使った。恒久対応は既存の `DW-O26` のとおりで、親は焦点走の file 集合を作る前に同節の 4 群とメタテストを列挙する。
