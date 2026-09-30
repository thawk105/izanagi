# 段 2 plan の未確定 1〜4 への親の追加実測 (2026-09-30 16:01 JST 前後、repo 外 scratch、read-only、astra・ultra)

1. root の stdout usage は root 単独。deleg1 の stdout `turn.completed.usage` = input 87,656 / output 415 は、root rollout の最終
   total_token_usage (input 87,656・output 415・total 88,071) と一致し、子 (61,473) を含まない。
2. root rollout の spawn 結果は子 id を返さない。`function_call_output` (spawn_agent) = `{"task_name":"/root/sandbox_probe"}`。
   子 rollout の `session_meta.agent_path` = `/root/sandbox_probe`、`agent_nickname` は別名。したがって「期待する子の集合」は
   root rollout の spawn 出力の task_name と、子の session_meta.agent_path + parent_thread_id で突き合わせられる (id ではない)。
   spawn の message 引数は暗号化文字列 (`gAAAA…`) で、子へ渡した指示を root rollout から読めない。
3. 全履歴 fork (fork_turns 省略): 子 rollout の token_count event は 1 件、total 15,241 (root 43,001 とは別)。親の token_count は
   子 rollout に複製されていない。ただし子の履歴 (response_item) は複製される。証跡 = liveness/forkall/、token-summary.txt 末尾。
4. sessions_root (`~/.codex/sessions`) の rollout は全体 788 file、2026/09/30 の日付 dir に 248 file (16:00 時点)。
5. 孫 (depth 2) は未実測。子 rollout の `source.subagent.thread_spawn.depth` = 1 の field があることだけ確認済み。
6. 過去の subagent rollout は全履歴で 6 件 (すべて本日、うち 4 件は親の probe、2 件はユーザーの対話 TUI)。子での guard 拒否記録は 0 件。
   子への guard 直接 probe は trust bypass flag の手打ちが auto mode 分類器に拒否されたため未実施 (brief L8)。
