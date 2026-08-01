# probe 一次資料 (2026-08-01, host pegasus02, worktree dev-wave-token-hygiene)

## P1: claude -p --effort bogus (不正 effort)
```
$ claude -p --model claude-haiku-4-5-20251001 --effort bogus "Reply with exactly: OK"
Warning: Unknown --effort value 'bogus' — ignoring it and using the default effort. Valid values: low, medium, high, xhigh, max.
OK
rc=0
```

## P2: claude -p --model not-a-real-model (不正 model)
```
$ claude -p --model not-a-real-model --effort low "Reply with exactly: OK"
There's an issue with the selected model (not-a-real-model). It may not exist or you may not have access to it. Run --model to pick a different model.
rc=1
```

## P3: claude --help の --effort 記述
```
  --effort <level>                      Effort level for the current session
                                        (low, medium, high, xhigh, max)
  --exclude-dynamic-system-prompt-sections
```

## 環境
```
claude_version=2.1.220 (Claude Code)
codex_version=codex-cli 0.146.0
date=2026-08-01T09:32:09+09:00
```
