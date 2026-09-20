## 総括

単位1を実装し、差分を残しました。変更は指定の2ファイルのみです。commit は作成していません。

- **`orchestrator/verifier/dsg.py`**
  - `_build_compact`：範囲を事前検査し、範囲外 write は保存した `_build_compact_tuple` へ退避。
  - `_build_compact_packed`：鍵の初出順を保ち、版・producer を flat 配列化。安定整列で最初の writer を保存し、重複・genesis の notes を元の走査順で再生。
  - `_PackedVersions` / `_PackedProducer`：既存の Mapping 操作を提供。
  - `_edge_candidates_for_task`：packed 経路は配列から wr/rw/ww を生成。run 順序を維持。
  - `_build_compact_edges`：ww 重みを offsets から同値計算。task 分割・pool・完全性検査・fallback・set 再生・PID 記録は維持。
  - `_txn_for_id` / `_reasons`：変更せず、view 経由で既存の理由列を維持。
- **`orchestrator/tests/test_verifier.py`**：指定の5テストと比較 helper を追加。既存期待値は変更なし。

**検証結果**

- 指定の自走 harness：**111 PASS / 0 FAIL / 0 SKIP**。赤の nodeid なし。
- 追加5テストの直接呼出し：全件 PASS。
- 反実仮想：最後の writer 採用、Mapping 読取り、範囲外退避除去、rw の非 strict successor の **4件を検出**。退避除去は `OverflowError`、他は `AssertionError`。復元後も追加5件 PASS。
- 親スクリプト：**22/22 fixture、workers=1/2 の44個の sha256 が凍結値と一致**。一覧 JSON 全体も `cmp` 一致。
- 全 fixture の `VerifyResult` 全 field、境界 trace の隣接 tuple・root 順・SCC 列も保存した旧 builder と一致。
- `git diff --check`：問題なし。

**所有外への波及**

`core.py:186` の鍵数、既存 test の `_EdgeWorkerState` 直接構築・`tuple(versions)`・producer lookup を維持し、該当テストは通過しました。共有 fixture は未変更です。`commit_receipt.py` の結果 digest・親 PID 束縛、および `test_t1286_commit_receipt.py`、`test_campaign_lock_wal_consumers.py` は間接 consumer として静的確認しました。後二者の全走は未実施です。`dsg.py` は campaign lock の closure 対象なので、既存 lock の digest drift は発生します。

**裁定 §4 に対する判断**

- `array("q")` に32 bit×2の全域を収めるため、格納値は **`((epoch << 32) | tid) - 2**63`** としました。指定の生値からの逸脱ですが、全域・版順序を保存し、上端境界も検証済みです。
- ordinal 配列は保持せず、安定 scatter/sort と元入力の再走査で occurrence 順を保存しました。
- worker は file ごとの配列を選ぶ tuple/header 参照を残します。write 数に比例する親の Mapping・鍵・版 object は参照しません。
- §4(a)(5) の pool 破綻時の参照解放は、今回の明示的な範囲指定に従い単位2へ残しています。

大規模 trace の記憶量・CoW・所要は**未実走**です。容量目標の達成や性能改善は主張しません。