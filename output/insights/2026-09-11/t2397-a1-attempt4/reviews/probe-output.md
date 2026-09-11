## 総括

実装済み・未実走です。

変更範囲は `orchestrator/manual_probes/test_t2397_a1_source.py` の出力先設定のみ（2行→3行）。`source-probe/<PBS_JOBID>` を親とし、呼出しごとに `tempfile.mkdtemp` で新規子directoryを作成して `evidence` に割り当てます。

過去出力・判定コード・source契約・期待値は変更していません。`git diff --check` は正常終了しました。

所有外への波及は、親の証跡収集が `run-*` 子directoryを参照する必要がある点です。親側で同一jobの連続呼出しと、gate/build/verify失敗が引き続き失敗することを実走確認してください。