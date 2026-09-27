### 所見ごとの対応 (F1 / F2: closed / partial / 未確認)

- **F1: partial（修正済み・pytest 未実走）**。7 件に共通する `ValueError` の原因だった、旧 `Transaction::abort()` 内での `TxExecutor::abort()` 検索を除きました。private checkout のクラスと関数を丸ごと置き換え、BEGIN 直前を凍結形 `HEAD + PROLOGUE` にし、block・epilogue の後も `#endif` と `}` で閉じています。canonical head が使う `ADD_ANALYSIS` も、この checkout の CMake 定義に供給しました。このテストは `source_digest` と実 build admission を通った後、`original_run` の直前に観測例外で止まる構成です。source の compile はしません。
- **F2: partial（修正済み・pytest 未実走）**。合成 checkout の `Options.cmake` に、実 CCBench と同形の `CCBENCH_ADD_ANALYSIS=0` と `ADD_ANALYSIS=${CCBENCH_ADD_ANALYSIS}` を追加しました。ログでは探索ケースの `ResultEvidenceIssuanceRefused` は先行する未知マクロ例外の処理中に発生し、originless ケースも build 完了前に abort しています。同じ原因の下流と判断していますが、3 件の解消は実走での確認が必要です。

### 変更

[buildcache fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/tests/test_buildcache_v2.py:5693) と [reflux fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/tests/test_reflux_campaign_issuer.py:135) のみ変更しました。受理・拒否、例外 message、件数の期待値は変更していません。

変更行数（追加＋削除、**段5 / 今回 / 合算**）は、`axis_trigger_gating.py` 57 / 0 / 57、`build_admission.py` 38 / 0 / 38、`test_build_admission.py` 111 / 0 / 111、`test_campaign.py` 4 / 0 / 4、`test_buildcache_v2.py` 5 / 33 / 38、`test_reflux_campaign_issuer.py` 26 / 2 / 28 です。合計 **276 行**で、450 行以内です。

### 検査

`python3 -m py_compile orchestrator/tests/test_buildcache_v2.py orchestrator/tests/test_reflux_campaign_issuer.py` は成功しました。合成 reflux source は `g++ -std=c++17 -fsyntax-only -DBACK_OFF=1 -DADD_ANALYSIS=0` に `BACKOFF_TRIGGER_GATING=0/1`、`TRACE=0/1` を組み合わせた **4 通りすべて成功**しました。`git diff --check` も成功しました。pytest は今回実走していないため、結果は**実装済み・未実走**です。

### 波及

F1 の CMake 定義は当該テストの private checkout に限定されます。F2 の定義は `_synthetic_silo_checkout` を使う 3 件に共通です。所有外の fixture、`source_digest`、`CONTEXT_MACROS`、実装側の受理・拒否は変更していません。

## 総括

焦点走の赤 10 件に対し、fixture の形を修正しました。  
F1 は旧クラス由来の検索失敗を除き、canonical な凍結 bytes と閉じた関数形にしました。  
F1 の観測点は compile より前です。  
F2 は `ADD_ANALYSIS` を実 CCBench と同じ経路で供給しました。  
F2 の合成 source は指定された 4 条件で構文検査を通過しました。  
pytest による 10 件の解消確認は、親の計算ノードでの再走が必要です。