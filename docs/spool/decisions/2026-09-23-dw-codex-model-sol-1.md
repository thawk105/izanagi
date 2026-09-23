---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: dw-codex-model-sol
seq: 1
---

## {{D:dev-wave-codex-model-sol}}. dev-wave の Codex 子の model 権威を gpt-6-sol へ改訂する (推論の深さは medium のまま)

**決定 (2026-09-23 ユーザー指示「gpt-6-sol が使えるようになったのでそちらへ移行したい、reasoning は medium」):**

1. `docs/dev-wave/operations.md` DW-O01 の model 権威行を `` `<model>`: 全段 `gpt-6-sol` (段 3 の 2 本も同じ)。 `` とする。書式は V2 (2026-09-10 の astra 移行で入った `全段 ... (段 3 の 2 本も同じ)。`) を保ち、slug だけを替える。`tools/dev_waves/launch_authority.py` の V2 正規表現と導出経路は変えない。
2. `tools/check_docs.py` の DW-O01 literal と、それを pin するテスト (`test_check_docs.py` の drift 負例・literal 期待値、`test_dev_wave_launch_authority.py` の全段導出 model・docs 独立照合) を同じ値へ揃える。
3. effort の pin (DW-S02 / DW-S03 / DW-S05-A / DW-S06-A / DW-S06-C の medium、plan / consult は呼び出し側指定) は変えない。
4. 切り替わりの時点: 起動器は投入時点の `--repo-root` の docs から model を導出する。したがって本決定が local main へ着地した後に作られる wave (と、その wave が切る子 worktree) から gpt-6-sol になり、着地前に始まった wave は自分の木の docs どおり gpt-6-astra のまま走り終える。遡って書き換えるものは無い。
5. 過去記録の `gpt-6-astra` (output/insights、paper-story、worklog、FOLDED、decisions 本文、受領証) は測定・実行時点の事実として残す (規律 7)。`test_s8b_ratified_freeze.py` の `model=gpt-6-astra` は AI-Agent trailer 文法の例示値で DW-O01 と結び付かないため変えない (変えると parametrize id と受入所要台帳の key だけが動く)。`.codex/role-adapters` (Phase 3 の役割子) と利用者の `~/.codex/config.toml` は本決定の対象外。

**理由:**
- model 権威は DW-O01 の 1 行だけにあり (check_docs が単一権威を検査)、起動器はそこから全段の model を導出する。1 行と、それを pin する literal・期待値を揃えれば移行が閉じる。D2137 の理由欄が記す 2026-09-10 の astra 移行と同じ扱いである。
- 移行前の生死確認として `codex exec -m gpt-6-sol -c model_reasoning_effort=medium --sandbox read-only` をサブスク (ChatGPT) ログインで 1 回打ち、rc=0・出力 `PONG`・log header `model: gpt-6-sol` / `reasoning effort: medium` を得た。さらに本決定の実装子 (Codex author) 自体が改訂後の docs から gpt-6-sol / medium を導出して走り、受領証が `recorded_model=gpt-6-sol`・`recorded_effort=medium`・`outcome=accepted` を記録した。
- D2137 (有効化前 commit の第 2 worktree は docs 入口を現行 main へ同期する) はそのまま成り立つ。同期先の現行 docs が sol を指すだけである。

**却下した選択肢:**
- V1 形式 (段 3 だけ別 model) へ戻して段ごとに model を分ける — ユーザー指示は全段の移行で、分ける根拠が無い。
- 過去記録の astra 表記を sol へ一括置換する — 当時その model で走った事実を消す (規律 7)。
- test_s8b の例示値も sol へ替える — 意味の無い parametrize id 変更で受入所要台帳の key 付け替えだけが生じる。
