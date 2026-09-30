単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt — ユーザー依頼の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s1-brief.md — 親の段 1 brief (実測 L1〜L9、scope 表、割れうる前提 P1〜P4)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra — 投入先 worktree (読むのはここ)。読めなければ即停止。

# 役割

あなたは dev-wave 段 2 のプラン起草子 (read-only) である。上の brief を実装できる file:line 粒度のプランを書く。
書込可能な tmp が無いのでテストは走らせず、静的検査でよい (テスト実測は親が行う)。予算が尽きそうなら
途中結論を下の出力形式どおり書いて終われ。**sub-agent を spawn しない (collaboration tool を使わない)。**

# 起草してほしいこと

1. 値の追随 (単位 A): `docs/dev-wave/workers.md` の 5 箇所の `reasoning=medium`→`ultra` (親が docs を編集する) に対し、
   `tools/check_docs.py` の `_check_dev_wave_reasoning_effort_pins` と関連 literal 定数、DW-O01 literal (372 行付近、既に docs は
   astra へ commit 済み 241f0c960)、`orchestrator/tests/test_check_docs.py`、`orchestrator/tests/test_dev_wave_launch_authority.py`
   で変える行を全部列挙する。D2229 決定 2 の列挙 (drift 負例の置換元、literal 期待値、全段導出 model、docs 独立照合) に漏れが無いか、
   effort 側で同型の pin (負例の置換元・期待値・合成 fixture の本文) を grep で洗って行番号つきで書く。
   `tools/dev_waves/effort_levels.py` に `ultra` を足す行と docstring の改訂案 (ultra は luna 系が非対応という事実の書き方)、
   `CODEX_REASONING_EFFORTS` を import する consumer (`tools/codex_worker_launch.py` 4857 行の argparse choices 等) と、
   その語彙を pin するテストがあれば列挙する。`tools/dev_waves/daemon.py` の `_supervisor_digest()` の閉包変化が
   既存テスト (digest の固定値を持つもの) を動かすかを確かめる。
2. 委任先会計 (単位 B、brief の P1): `tools/codex_worker_launch.py` で、stdout の root thread id から子 rollout
   (`session_meta.session_id == root id` かつ `source.subagent.thread_spawn.parent_thread_id` が既知 id、孫も連鎖) を発見し、
   turn_context の model/effort/cwd 照合、model call・token の合算 (既存 `max_model_calls` / `max_cli_reported_tokens` / 予算)、
   受領証への記録を足す最小設計を file:line で書く。現行の `_discover_rollouts` (1445 行)、`_consume_rollout_event` (1468 行、
   1497 行の `meta_id != rollout.session_id` 判定)、`_rollout_actuals` (1634 行)、受領証の field 定義 (83〜300 行付近)、
   evidence issue の集計 (470〜500 行付近) との接続を示す。子 rollout の発見方法 (sessions_root の走査範囲・時刻窓・
   ファイル数の実コスト) と、子の発見が root 終了後に遅れる競合 (evidence grace) の扱いを書く。受領証 schema を読む
   consumer (ledger・collect 系・テスト) を grep で列挙する。対案 P1' (委任を検出したら拒否) の差分量も併記し、
   どちらが小さく同等の安全性かを比較する。
3. rulings の effort (P2): `.claude/commands/rulings.md` 58 行と、plan/consult の `--reasoning` 値を書いている箇所を
   repo 全体で grep し、ultra にすべき記述箇所を全部列挙する (過去記録 output/・worklog・decisions 本文は除外)。
4. next-tasks (P3): `/work/1/SFC/tanab/scripts/next_tasks_consult.sh` の codex 分岐と `CONSULT_EFFORT` 既定の改訂案。

# 制約

- 過去記録の gpt-6-sol / medium / astra 表記、`.codex/role-adapters`、`~/.codex/config.toml`、`tools/codex_reasoning_ab.py`・`tools/t189_*`、
  Claude 側 effort、`test_s8b_ratified_freeze.py` の例示値は scope 外。
- 正しさゲート・verifier を緩める変更を提案しない。受理集合を広げるのは effort 語彙の `ultra` 1 語だけ。

# 出力形式

markdown。見出し「## 単位 A」「## 単位 B」「## P2 rulings」「## P3 next-tasks」「## 未確定・親への質問」「## 総括」。
各変更は `path:line` と変更前後の要旨。総括には単位ごとの変更行数見積もりと、brief の前提で誤っていたものを書く。
