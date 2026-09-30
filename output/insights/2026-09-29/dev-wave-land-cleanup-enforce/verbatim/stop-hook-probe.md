# Stop hook 入力の実測 (DW-O13、2026-09-29 21:45 JST、login node、claude -p サブスク経路、ANTHROPIC env 空)

probe: repo 外の一時 dir で `claude -p ... --settings settings.json` (Stop hook = stop_probe.py が stdin を log し、stop_hook_active=false なら block)。

1. 素の session (run.sh): Stop 入力 field = session_id, transcript_path, cwd, prompt_id, permission_mode, effort, hook_event_name="Stop",
   stop_hook_active, last_assistant_message, background_tasks (list), session_crons (list)。
   1 回目 stop_hook_active=false → `{"decision":"block","reason":...}` で継続、モデルは reason に従い応答 "SECOND"、2 回目 stop_hook_active=true → 通過。num_turns=2。
2. EnterWorktree 後 (run2.sh、一時 git repo): Stop 入力の cwd = `<repo>/.claude/worktrees/probewt` (入場後の worktree path)。同じく 2 回で終了。

生 log: stop-input.log (run2 分で上書き済み、run1 分は親 transcript に逐語)。
