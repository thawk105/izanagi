## 総括

**GO（静的レビュー）。blocking real: 0、blocking refuted: 3。** 今回の15行差分に、採用を止める実在の回帰は見つかりませんでした。

- **refuted：カウント公開が handler 登録に先行する競合。** `term_success` は従来位置の append を通らず、terminal・出力ファイルの準備後、handler 登録、`token_count` 公開の順に進みます。上限観測による SIGTERM が登録を追い越す旧経路は閉じています。根拠：[1475行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1475)、[1545行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1545)。
- **refuted：flush/fsync の割込みで handler が I/O に再入する。** handler は `SystemExit(0)` のみです。公開後の割込みで fsync 完了前に抜ける可能性はありますが、永続化完了と親からの可視性は別です。`with` の巻き戻しによる close は残るものの、handler 自身が中断中の stream を操作する経路はありません。根拠：[1306行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1306)、[1358行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1358)、[1547行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1547)。
- **refuted：M1 が既存 assertion をすり抜ける。** `finish` 内の変更先は一意です。`SystemExit(7)` が実行されれば、既存の `codex_exit_code == 0` が拒否します。ただし M1 は終了コードへの感度を検証するもので、競合消失そのものの証明ではありません。根拠：[4259行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:4259)。

他の signal、I/O 停滞、終了猶予 **0.05秒**、外側 watchdog **10秒** による強制終了の余地は残ります。今回案が常に exit 0 を保証する、という説明なら過大です。ただし、これらを今回導入の回帰とする証拠はありません。根拠：[1676行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1676)、[1138行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_codex_worker_launch.py:1138)。

pytest・M1 は本レビューでは未実走です。親報告の単独 `1 passed / 1.67秒` は補助証拠として扱い、全実行順序の保証とはしていません。ファイル編集はしていません。