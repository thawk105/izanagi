## 総括

**NO-GO。must-fix 4 件。** 静的検査で、二重 runner、同一系列の親の二重起動、投入済み job の見失い、再起動後の系列欠測につながる経路を確認した。テストは依頼どおり実走していない。加えて、現時点の本走 config は指定 checkout の一部が存在せず、起動時検査を通らない。

## 所見

1. **must-fix — stale PID の除去が排他になっていない。** [contrast_runner.py:375](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:375)  
   古い PID を runner A・B がともに読む → A がファイルを消して自分の PID を作る → B がその新ファイルを消して自分の PID を作る → 両方が周回する。**影響:** 同じ系列の親や job が並行投入されうる。**最小修正:** 生存期間中保持する `flock` などで単一 runner を排他する。

2. **must-fix — 親起動から state 保存までに無記録の親が残る。** [contrast_runner.py:310](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:310)  
   `Popen` 成功 → 321 行の保存前に runner が異常終了 → 再起動時の state に親がいない → 同じ系列・同じ `a` の親をもう一つ起動する。**影響:** role と台帳更新が競合し、A の計上や結果を壊しうる。**最小修正:** 起動前に回復可能な起動記録を永続化し、再起動時に既存プロセスと出力を照合してから起動する。

3. **must-fix — `init`・`submit` の成功と state 保存の間を回復できない。** [contrast_runner.py:257](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:257)、[contrast_runner.py:344](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:344)  
   `qsub` 成功後、request ID 保存前に runner が終了 → 再起動して同じ単位を submit → 起動器は既存 evidence を理由に失敗 → attention。`init` 成功後の停止でも、既存 ledger への再 init が失敗する。**影響:** 実際には投入・開始済みの系列が欠測になる。**最小修正:** 起動器呼出し前の intent と結果を永続化し、再起動時に ledger・evidence・投入記録を照合して state を復元する。

4. **must-fix — qstat の遅延表示を job 終了と確定する。** [contrast_runner.py:196](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:196)  
   submit 直後、成功した qstat に新 request ID がまだ載らない → `job=None` にする → job が slot を書く前の status は同じ単位を返す → 再 submit が既存 evidence で失敗し attention。**影響:** 正常な job が動いていても系列を失う。**最小修正:** 不在を一度で確定せず、投入直後の確認期間と再照合を設ける。再投入前には同じ単位の evidence・台帳を確認する。

5. **should-fix — コピー先のテストは台帳の参照先が違う。** [test_contrast_runner.py:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/test_contrast_runner.py:15)  
   `HERE.parents[1]` は `/work/1/SFC/tanab/dev-wave-jobs` → 73 行の実物台帳コピー元が存在しない → 親によるコピー先でのテストが開始前に失敗する。**影響:** 本走用コピーの試験結果を確認できない。**最小修正:** repo path を明示的に渡すか、テストに必要な台帳を一緒に配置する。

6. **should-fix — 停止通知後も系列を開き続ける。** [contrast_runner.py:325](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:325)  
   `open_series()` の途中で SIGTERM → `STOP=True` → このループは再確認せず後続系列を init。**影響:** 停止要求後に登録 schedule の新系列が始まる。**最小修正:** 各 init の直前に `STOP` と pause を確認する。

7. **should-fix — 現在の本走 config は起動不可。** [config-v1.json:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/config-v1.json:11)  
   指定された `c03` と `c09`〜`c16` が現時点で存在しない → [起動時検査](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:56) が rc=2。**影響:** 本走は投入前に停止する。**最小修正:** 指定の 16 checkout を作成し、HEAD と状態を検査してから起動する。

8. **nit — 待ち列に `deque` は不要。** [contrast_runner.py:219](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:219)  
   末尾に追加して最後に `list(waiting)` として読むだけ。実害はない。**影響:** 本走結果への影響なし。**最小修正:** 通常の list にする。

## 確かめて問題が無かった点

- qstat の rc 非ゼロ・見出し欠落時は job を終了扱いしない。
- 記録済みの親が生きている間は、その系列の status・generate・submit を進めない。429 保留もこの経路に入る。
- 親の既知の非ゼロ終了は attention になり、`series-end` は台帳から読んでいる。
- 本走 schedule は、参照を各 batch の前に置き、各組を登録された巡回順で並べている。
- 通常の状態遷移では親 4・活動系列 16 の枠を計算し、attention 中の checkout は再利用しない。
- 親へ渡す環境から指定の `CLAUDE*`・`AI_AGENT`・`ANTHROPIC_*` を除外している。