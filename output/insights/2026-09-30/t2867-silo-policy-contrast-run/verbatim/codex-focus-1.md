## 総括

**NO-GO。静的検査で must-fix 2 件。** 再起動時に実際の親・job が動いていても `done.json` を書ける経路と、停止通知後に新しい job を投入できる経路がある。本走結果の欠測・規則逸脱に関わるため修正が必要。テストの実走は依頼どおり行っていない。

## 所見ごとの判定表

| 裁定 1 の所見 | 判定 | 根拠と残る失敗の筋書き |
|---|---|---|
| 1. stale PID の排他 | **closed** | [contrast_runner.py:418](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:418)–442。`flock` を周回終了まで保持し、取得失敗時は起動を拒否する。 |
| 2. 親起動の記録窓 | **partial** | [contrast_runner.py:341](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:341)–357、[同:154](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:154)–158。二重起動は fail-closed になったが、再起動時に生存しうる親の記録を消すため、完了を早計に宣言できる。 |
| 3. init・submit の記録窓 | **partial** | [contrast_runner.py:281](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:281)–295、[同:383](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:383)–393。intent により二重実行は防ぐが、submit の成否不明時は生存しうる job を state に記録せず、`done.json` の条件を満たせる。 |
| 4. qstat の遅延表示 | **closed** | [contrast_runner.py:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:211)–223。成功した qstat での不在を 2 回数え、投入後 120 秒まで終了扱いしない。失敗した qstat の周は計数もリセットもしない。 |
| 6. 停止後の init | **partial** | [contrast_runner.py:376](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:376) で各 init 前に確認する。ただし周の途中で通知を受けた場合、後述の submit・親起動には進みうる。 |

## 新しい所見

- **must-fix — 不明な親・job が残っていても完了を宣言する。** [contrast_runner.py:154](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:154)–160、[同:310](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:310)–315。`Popen` または `qsub` の成功後、結果保存前に終了 → 再起動で attention を付け、親は `None`、submit の job も `None` のまま → 他系列が終わると、生存中の処理を確認せず `done.json` を書く。**影響:** 未完の本走を完了と誤認し、系列の結果を欠測させうる。**最小修正:** 不明な実行を未解決状態として保持し、照合・手動解決まで done 判定を禁止する。
- **must-fix — STOP 判定が周の途中で古くなる。** [contrast_runner.py:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:242)、[同:273](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:273)–283、[同:305](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:305)–309。`paused=False` を記録した後、時間のかかる status 中に SIGTERM → 古い値で submit、または親起動へ進む。**影響:** 停止後に新規 job・親を動かし、停止規則から逸脱する。**最小修正:** 各 submit・generate・親起動の直前に `STOP` と pause を再確認する。

## 確かめて問題が無かった点

- 旧 state の `intent`・`job_missing`・親の `starting` 欠落は [既定値で補完](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:146)される。旧 job の `job_submitted` は読込時刻になり、終了判定が遅れるが二重投入には直結しない。
- init・submit 失敗時の attention は state を二度保存するが、[JSONL への追記は一度](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:175)。正常時は intent を消して保存する。
- lock fd は [外側の `finally` まで保持](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py:418)され、通常の子プロセス起動で継承されない。