---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-codex-astra-ultra
seq: 1
---

## {{D:codex-astra-ultra}}. dev-wave・rulings・next-tasks の Codex 子を gpt-6-astra・reasoning=ultra へ改訂し (D2229 を supersede)、ultra の委任 (spawn_agent) をした attempt は起動器が受理しない

**決定 (2026-09-30 ユーザー指示「dev-wave, rulings, next-tasks で codex を gpt-6-astra・reasoning=ultra で使う」):**

1. model: `docs/dev-wave/operations.md` DW-O01 の権威行を `` `<model>`: 全段 `gpt-6-astra` (段 3 の 2 本も同じ)。 `` とする。V2 書式と `tools/dev_waves/launch_authority.py` の導出経路は D2229 決定 1 と同じで、slug だけを替える。`tools/check_docs.py` の literal とそれを pin するテストを揃える (D2229 決定 2 と同じ列挙)。
2. effort: `docs/dev-wave/workers.md` の DW-S02 / DW-S03 / DW-S05-A / DW-S06-A / DW-S06-C を `reasoning=ultra` とし、check_docs の effort pin・負例 (旧 medium を拒否)・テストを揃える。rulings の相談は `tools/dev_wave_codex.py --stage consult` が `--reasoning` を呼び手の必須入力とし DW-S03 から自動導出しないため、`.claude/commands/rulings.md` の起動例に `--reasoning ultra` と DW-S03 参照を書く。
3. 受理集合: `tools/dev_waves/effort_levels.py` の `CODEX_REASONING_EFFORTS` に `ultra` を足す。`CLAUDE_EFFORTS` は変えない。docstring に「ultra は luna 系が非対応 (依頼が指定した事実で独立実測ではない)、本 module は model×reasoning の互換を保証しない」と書く。
4. **委任の受理規則:** ultra の Codex は委任 (collaboration namespace の `spawn_agent`) を自動で試みる。prompt で委任を禁じ、root rollout に `spawn_agent` の function_call が 1 件でもある attempt は、起動器 (`tools/codex_worker_launch.py`) が致命 evidence reason `delegation_detected` を記録して accepted にしない。online の tail と sealed 再検証は同じ消費関数を通る。receipt schema は V5 のまま、拒否は終了時。`wait_agent` など spawn 以外の collaboration 呼び出しだけでは拒否しない。DW-O01 に「ultraの委任(spawn_agent)はpromptで禁じ、委任したattemptは起動器が拒否する。」を 1 文足し、L1.5 予算 (9,696 bytes) は既存 3 文の意味等価な縮約で収めた (D782 の手順で、上限は引き上げていない)。
5. next-tasks: repo 外の `/work/1/SFC/tanab/scripts/next_tasks_consult.sh` の codex 分岐に `-m gpt-6-astra` を明示し (利用者の `~/.codex/config.toml` の既定に依存させない)、`CONSULT_EFFORT` 既定を high → ultra、相談 prompt の前置きに「sub-agent を spawn しない」を足す。この script は起動器を通らないので委任の検出は無い (prompt の禁止と、read-only sandbox が委任先に継承されることだけに依る)。
6. 切り替わりの時点は D2229 決定 4 と同じ: 起動器は投入時点の `--repo-root` の docs から model と effort を導出するので、本決定が local main へ着地した後に作られる wave (と、その wave が切る子 worktree) から astra・ultra になり、着地前に始まった wave は自分の木の docs どおり走り終える。next-tasks は script の設置時点 (2026-09-30 17:00 JST 前後) から切り替わった。
7. 過去記録の gpt-6-sol / medium / high 表記 (output/insights、worklog、FOLDED、decisions 本文、受領証) は測定・実行時点の事実として残す (規律 7)。`test_s8b_ratified_freeze.py` の例示値、`.codex/role-adapters`、利用者の `~/.codex/config.toml`、`tools/codex_reasoning_ab.py`・`tools/t189_*` の許可リスト、Claude 側 effort は対象外。

**理由:**
- 生死確認: `codex exec -m gpt-6-astra -c model_reasoning_effort=ultra --sandbox read-only` をサブスク (ChatGPT) ログインで打ち rc=0・header `model: gpt-6-astra` / `reasoning effort: ultra`。改訂後の docs から導出した起動器実走 (段 6 の review 2 本) の受領証が requested / recorded とも astra・ultra、`outcome=accepted`、委任 issue なし。next-tasks の改訂版も rc=0・header astra / ultra・所要 119 秒 (締切 1,800 秒)・委任 0。
- 委任を受理しない理由: ultra は developer message で proactive な委任を有効化し (medium は無効化を注入)、委任先は別 rollout file に記録され (`session_meta.session_id` は root の id)、`--json` の stdout には root の id しか出ない。このため改訂前の起動器は委任先の model call・token・model/effort/cwd を見ずに attempt を受理していた (検査は落ちずに素通り)。委任先を会計する案は、全履歴 fork で子 rollout に親の meta/context が複製される、manifest が 1 attempt 1 session を強制する、子の完了と seal 後追記が閉じない、という実物の障害を抱え、receipt・manifest の新世代と ledger まで波及する。さらに委任先に `.codex/hooks.json` の guard が効くことは未確認である (root では exec 経由の guard 拒否を本番 rollout で観測済み、委任先では拒否記録 0 件で有効とも無効とも言えない)。未確認の面で走った仕事を受理しないのが規律 6 に沿い、依頼の「検査を黙って緩めず、受理規則を明文化して直す」も満たす。
- 設定で委任を止める手段は、この CLI (0.159.2)・exec 経路・明示 spawn 依頼で試した 3 設定 (`--disable multi_agent`、`agents.max_threads=1`、`agents.max_depth=0`) ではいずれも止まらなかった。

**却下した選択肢:**
- 委任を許して委任先を会計する — 上の障害で差分が 700〜1,100 行規模になり、委任先の guard 未確認のまま受理することになる。
- 権威段だけ effort を max に留める — 全段 ultra のユーザー指示と非同値で、max が委任しない証拠も無い。
- prompt で禁じるだけにする — 素通りが残る。
- L1.5 予算を 9,788 bytes へ引き上げる — 既存 3 文の意味等価な縮約で収容できた (段 6 レビューの指摘)。

**残る限界:** 事後拒否は委任先の実行・書込みを防ぐ機構ではない (workspace-write の author / fix で委任が起きると、子 worktree に guard 未確認の書込みが残りうる)。拒否された attempt の委任先 token は会計されない。委任先での guard 発火は未確認のまま (直接 probe は trust bypass flag の手打ちが auto mode に拒否され、未実施)。
