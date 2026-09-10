## 総括

**real 1件。新規 caller 検査の修正が必要です。** 製品実装の受理挙動を誤らせる差分は静的レビューでは見つかりませんでした。

### real

- **[orchestrator/tests/test_backoff_sweep.py:140](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/tests/test_backoff_sweep.py:140)**
  `prepare` の模擬実装が admission policy を束縛せず、返した cfg の identity 計算で停止します。focus-1.log:195–197 は該当2ケース失敗、117 passedを記録しています。
  **影響:** 候補 raw3000/physical1000 の意味照合へ到達せず、候補宣言欠落の変異 M5 を検出する検証根拠が成立しません。
  **最小修正:** 模擬 `prepare` 内で、既存 `ident.bind_admission_policy(cfg, kwargs["build_context"].policy)` により cfg を束縛してから使用・返却する。意味検査の期待値は維持する。

### refuted

- **期待値の循環参照:** `backoff_sweep.py:120` は要求 mapping の `float(physical)` から期待bitsを生成。観測や decoder からの逆算はありません。修正不要。
- **stock・乱択の静的化:** `screening_driver.py:228,270,278` は宣言を両分岐で転送し、BACKOFF_FIXED のみに適用。無宣言は既存 gate の未確立扱いを維持します。追加の宣言case拒否は不要です。
- **旧成果物への遡及:** `backoff_extended_sweep.py:675,1026,1265` は v2 slug で探索し、その campaign 配下へ出力します。旧v1 fallback・既存writerの変更はありません。追補 `docs/b10-backoff-static-tail-preregistration.md:1092` も全macro・性能認証への一般化を明示的に限定しています。修正不要。
- **author無し実装ハンク:** code/tests 6ファイルの全差分は `author.patch` とbytes一致。親の差分は事前登録の末尾追補のみです。

HEAD基準で旧 `output`、共通gate、s1・paper A2 に差分はありません。既存literalも s1 は5/10/2、paper A2 は10/5のままです。今回の確認は静的検査と既存ログの読取りであり、baseline 108 passedを変更後の成功や変異検証済みへ一般化していません。