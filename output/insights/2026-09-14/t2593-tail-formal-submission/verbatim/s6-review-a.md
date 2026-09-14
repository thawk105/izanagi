## 所見1 — 到達性テストが入力検査と driver の間を省略している

- **所見:** `test_job_formal_inputs_checked_before_work` は実装の離れた断片を直接接続するため、途中で新系列の入力を壊す変更を検出できない。
- **根拠（読解）:** `orchestrator/tests/test_b10_backoff_grid_job.py:139–148` は入力検査から `CURRENT_STAGE=allocation_reservation` の直前までを抜き、そこへ `_sweep(source)` を連結する。実際の `tools/pegasus/b10_backoff_grid.sh:287–596` は通らない。assert（同テスト:194–204）が証明するのは、この合成経路上の順序と argv である。
- **成果物影響:** 正常な投入が job 内で停止し、campaign・execution・完了印が生成されない変更でも、新設テストが緑のままになる。
- **最小の改変:** job script:287 の `CURRENT_STAGE=allocation_reservation` の直後へ `unset B10_PREREGISTRATION_COMMIT` を追加する。実 job は:619 の変数展開で停止するが、上記テストと `test_job_formal_command_uses_run_cli` はその行を抽出せず、fixture の正常値を使って緑のまま通る。`test_job_failed_sweep_cannot_reach_finalizer` も:597 以降だけなので検出しない。
- **深刻度:** **must-fix**。親裁定 (d) の接続保証に穴がある。入力検査から sweep までの連続した実装を通し、必要な外部操作を stub 化する検査が必要。

## 所見2 — group ID の日時・PID は形式しか検査していない

- **所見:** 旧系列不変性テストは、group ID を固定値に壊しても正規表現に合えば受け入れる。
- **根拠（読解）:** `orchestrator/tests/test_b10_backoff_grid_submit.py:98–100` は manifest から得た group ID の形式だけを検査し、:111–124 ではその値から期待 path を作る。`tools/pegasus/submit_b10_backoff_grid.sh:153` が生成する日時・PID と、実際の起動時刻・子プロセス PID の対応は観測していない。
- **成果物影響:** 投入台帳・出力 path の識別子が固定化され、同じ出力親への次回投入が receipt 衝突で拒否されても、不変性テストが通る。
- **最小の改変:** submit script:153 を `GROUP_ID="b10-backoff-grid-20000101T000000Z-1"` に置換する。`test_submit_legacy_qsub_argv_and_receipt_unchanged` の全パラメータは個別の出力ディレクトリを使うため緑のまま通る。新系列の転送テスト・文書投入テストも同様。
- **深刻度:** **must-fix**。親裁定 (a) の「日時・PID をその場で検証する」を満たしていない。起動前後の UTC 時刻と起動した shell の PID に照合すべき。

## 検査が効いていると判断した箇所

以下は静的読解による判断であり、テストや変異は実行していない。

- **SHA・receipt:** submit テスト:103 は `hashlib.sha256(JOB.read_bytes())` を計算する。shell が出した digest の自己申告ではない。:105–125 は manifest・submitted の schema、種別、run kind、argv・path の対応を比較する。
- **完走条件:** job テスト:353–369 は実際に8 commit と execution を用意し、driver stub を rc=0/1/23/124 にして、sweep から finalizer まで連続したコードを通す。finalizer 単体の負例へのすり替えではない。:626 の timeout 呼出しに `|| true` を付ける改変なら、非ゼロケースが赤になる。
- **負例の副作用:** submit テスト:79–83 は rc=2、全 stub 未呼出し、出力ディレクトリが空であることを検査する。queue 照会・receipt 作成を拒否前へ移す改変を検出する。
- **逐語:** 事前登録:1063–1065 の `t2500-tail-formal` / `t2500-backoff-static-tail-formal` は、shell の分岐・execution 名、テストの固定 literal、投入文書:7・32・51 と一致する。期待 literal を shell から逆算していない。
- **既存テスト:** 基底 `d895e90b2` との差分は、2つの `.count()` の期待値を2→3とする変更と説明コメントだけ。AST による静的比較でも関数名集合は一致し、追加・削除はゼロだった。
- **環境依存:** SHA・時刻・PID・実 host 名を期待値へ焼き込んだ箇所は見当たらない。ただし submit 正例は実際の `python3.10` を呼ぶため、その実行環境は必要。

## 総括

追加所見は **2件**。最も重いのは、到達性テストが実 job の中間区間を省略していること。次が、日時・PID の固定化を見逃す group ID 検査である。既知の `--help` 所見は重複報告していない。

親の実測では、上記の `unset` 追加と group ID 固定化を個別に適用し、指定テストが緑のままになることを裏取りしてほしい。対照として、timeout 行への `|| true` 追加が完走条件テストで赤になることも確認すると、検査範囲を明確にできる。