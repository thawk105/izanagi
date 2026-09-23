# 段 1 brief — dev-wave Codex 子の model を gpt-6-astra → gpt-6-sol (2026-09-23)

- 研究前進 (土台): dev-wave の全 Codex 子 (plan/consult/author/review/fix/focus) が新しい model で走るようにする。完了判定 = 着地後の main で `tools/dev_wave_codex.py --dry-run` が `gpt-6-sol` を導出し、check_docs と焦点テストが緑。
- 確定済みユーザー裁定 (2026-09-23): 「gpt-6-sol が使えるようになったのでそちらへ移行したい、reasoning は medium」。model 権威の改訂として decisions fragment に記録 (2026-09-10 の astra 移行と同じ扱い、経緯は D2137 理由欄)。
- 生死確認 (DW-G01、実測済み): `codex exec -m gpt-6-sol -c model_reasoning_effort=medium --sandbox read-only` が rc=0、出力 `PONG`、log header `model: gpt-6-sol` / `reasoning effort: medium`。codex はサブスク (ChatGPT) ログイン、ANTHROPIC/OPENAI_API 系の env は 0 件。証跡 = 本 dir の sol-ping.log / sol-ping-out.md。
- 開始 gate: `check_wave_startup.py --mode fresh --external-handoff` rc=0 (startup-gate.log)。基準 = main 3886a1fd36657537af2b6c6ed389257363d92bef。

## scope (実アンカー)

| file | 箇所 | 変更 | 担当 |
|---|---|---|---|
| docs/dev-wave/operations.md | DW-O01 の `<model>` 行 (14 行) | `gpt-6-astra` → `gpt-6-sol` (V2 形式 `全段 ... (段 3 の 2 本も同じ)。` を保持) | 親 (docs) |
| tools/check_docs.py | `DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL` (368 行) | 同じ置換 | Codex author |
| orchestrator/tests/test_check_docs.py | 9126 行 (drift 負例の置換元) と 9412 行 (literal の期待値) | 置換元を `gpt-6-sol`、期待値を sol へ | Codex author |
| orchestrator/tests/test_dev_wave_launch_authority.py | 261 行・377 行の期待 model | `gpt-6-sol` へ | Codex author |

## scope 外 (判定済み)

- test_s8b_ratified_freeze.py の `model=gpt-6-astra`: AI-Agent trailer 文法の例示値 (同じ tuple に `claude-opus-5-1m` も並ぶ)。DW-O01 を読まず launch authority とも無関係。変えると parametrize id が変わり acceptance_duration_ledger.json の 30 key の付け替えまで波及するだけで、成果物・受理集合に影響なし (DW-G05) → 変更しない。
- D2137 の決定は「第 2 worktree の docs を現行 main へ同期」なので sol 移行後もそのまま成立、変更不要。
- 過去記録 (output/insights・paper-story・worklog・FOLDED・decisions 本文) の astra、.codex/role-adapters、~/.codex/config.toml は触らない (規律 7、依頼の scope 外)。
- effort pin (DW-S02/S03/S05-A/S06-A/S06-C = medium) は不変。

## 不変条件

- V2 行は launch_authority の `_MODEL_LINE_V2_RE` に一致し、DW-O01 の可視本文に `gpt-` slug はこの 1 件だけ (check_docs の単一権威検査)。
- 正しさゲート・verifier に触れない。受理集合は「DW-O01 が指す model 名」の値だけが変わる。

## 分割・段構成

- 軽量版 (DW-C00): 設計択一なし・正しさ防壁非該当 → 段 2・3・段 6 review 子を省く。実装面があるので段 5 Codex author 1 本 (所有 3 file) は必須。
- 受入・実測: 焦点走・変異・受入は計算ノード dispatch (Pegasus、先例 T-2797 の script 一式を写す)。
