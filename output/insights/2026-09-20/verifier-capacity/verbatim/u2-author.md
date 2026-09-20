## 総括

- **(a) 変更**：edge・parse とも破綻時は残 worker を SIGKILL 後に shutdown。部分結果・Future・executor の参照を解放して全件を逐次再計算します。packed 構造、判定、PID 集合の意味は維持しました。
- **(b) harness**：指定コマンドで **114 passed / 0 failed / 0 skipped**。赤の nodeid なし。`git diff --check` も成功。
- **(c) 直接実行・反実仮想**：追加3テスト成功。edge 約1.1秒、parse 約1.3秒で復帰し、逐次結果一致・親PIDのみ・残存子なしを確認。HEAD の修正前関数をメモリ上で復元すると、両破綻テストとも **120秒 timeout**。参照解放を外す変異は両側で赤化。部分結果採用の変異も既存テストで赤化しました。
- **(d) 所有外への波及**：変更は指定3ファイルのみ。静的には enforcement closure の digest が変わり、既存 campaign lock は `contract-loader-drift` の対象です。schema・CLI・core・docs は未変更。
- **(e) 判断・逸脱**：小さい trace では修正前も終了したため、結果配列が pipe 容量を超える合成 trace に拡張しました。禁止された Git 操作、報告ファイル作成は行っていません。
- **(f) 未実走**：計算ノードでの実 OOM、保全済み巨大 trace の容量・性能測定、pytest は未実施です。

差分は未コミットで残しています。