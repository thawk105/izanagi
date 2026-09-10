## 総括

**partial：実装済み・未実走。** [所有ファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2273-resume-author/orchestrator/tests/test_codex_worker_launch.py:1475)のみ、HEAD 比で追加11行・削除4行です。

- signal mask を撤回。term_success のカウント対象 `token_count` を、output・terminal・rollout 準備と handler 登録の後に公開します。
- handler は `SystemExit(0)` のみ。I/O と terminal の重複出力を除去しました。M1 の変更先は `finish` 内の一意な箇所です。
- `max_model_calls`・子 exit0・validator0・`not_accepted` を同じ実経路で要求する既存 assertion は維持。期待値・timeout・production は未変更です。
- 波及：共有 fixture の他モードは従来順序を維持。`FAKE_EVIDENCE_READY` の既存 retry caller も不変。所有外 Python caller は検索で見つかりませんでした。
- closed：実走による確認なし。regressed：新たな回帰は未判定。親の既存赤を解消済みとは主張しません。

外側・生成 Python の構文、差分空白、禁止文字不在を静的確認済み。pytest・受入・変異は未実走。docs 更新・commit は行っていません。