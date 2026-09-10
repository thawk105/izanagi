# [T-182] 段 1 brief — model routing の限定 shadow pilot

- **scope**: production の第二レンズは `gpt-5.6-sol` のまま従来どおり走らせ、同一凍結入力を
  軽量 model へ **追加 (shadow) 投入**して比較証拠と receipt を残す。置換はしない。
  既定 policy (`DW-O01` / `DW-S03` / `DW-S06-A` の model・reasoning) は変更しない。
- **確定済みユーザー裁定**: `docs/phase3.md` [T-182] — critical planning/受入判定は `gpt-5.6-sol`
  維持、低リスクな第二レンズ 1 箇所のみ、finding coverage・誤検出・token/turn/wall-clock と
  model identity receipt を残す、production 既定は変更しない。
- **前提を覆した実測 (DW-S01)**: 「利用可能な軽量 model」は単純には存在しない。
  同一 prompt (`prompt_hash=45a76772a5bd…`)・`reasoning=max` で
  sol=34,289 / luna=30,262 / terra=37,947 CLI reported token、wall 49s / 70s / 99s、
  model_calls 3 / 4 / 9。**luna も terra も sol より軽くない**。唯一の軽量 tier
  `gpt-5.4-mini` は `reasoning=max` を 400 で拒否し `xhigh` までしか使えない
  (未サポート: `gpt-5.4-nano`, `gpt-5.1-codex-mini`)。よって単一軸の「軽量 model 比較」は
  成立せず、段 4 で scope を裁定し直す。

## 成果物

1. `tools/codex_model_shadow.py` (新規・read-only・live inference なし)。arm manifest と
   rollout から arm 別 receipt を作り、次を fail-closed にする。
   (a) 全 arm の `prompt_hash` 一致、(b) 記録 `model`/`reasoning` が要求値と一致、
   (c) `model_calls>0` かつ成果物が `check_codex_output.py` rc=0、
   (d) authoritative arm がちょうど 1 本かつ production 既定 model、
   (e) 交絡タグ (計測時の同時 codex 実行数) の存在。
2. `orchestrator/tests/test_codex_model_shadow.py` (合成 fixture、正例 + 各 fail-closed 負例)。
3. pilot 実走証拠を `output/insights/2026-07-29_t182-model-routing-shadow-pilot*` へ凍結。

## 不変条件

- `tools/codex_worker_ledger.py` を変更しない (T-180 が `--manifest` を追加予定。import のみ)。
- `docs/dev-wave/*.md` の model/reasoning 契約を変更しない (policy 採用は T-184 所有)。
- shadow arm の finding を裁定・受入に使わない。テストで live inference を呼ばない。

## 成果物影響 (DW-G05)

- (b)(c) 欠如 → 未サポート model が rc=1 / `model_calls=0` のまま「finding 0 件」に化け、
  T-184 が「軽量 model は品質劣化」という誤った既定を採用する。**実測済み**:
  session `019fadd3-c15a-79e1-8783-f083061d4e3d` (nano)、
  `019fadd3-c19c-7a12-bbf0-ded998aed815` (codex-mini) は receipt に要求 slug を残したまま消費 0。
- (a) 欠如 → 異なる入力の比較を「同一凍結入力」として台帳に記録し、routing 判断の根拠が偽になる。
  実測 ID: `33beae9e…` / `45a76772…` / `53eae705…` の 3 prompt を機械識別できている。
- (d) 欠如 → shadow の finding が authoritative 台帳へ入り、production 既定を実質変更する。
- (e) 欠如 → 5 wave 並行 (`pgrep -c -f codex` = 28) 下の wall-clock を無条件比較値として記録する。

## provisional 裁定 (親の暫定。段 3 の攻撃対象)

- **(P1)** 第二レンズ = 本 wave の段 3 敵対相談 B を主、段 6 敵対レビュー B を従。
  いずれも sol arm を従来どおり走らせ shadow を**追加**する。
- **(P2)** shadow arm = `gpt-5.4-mini` @ `xhigh` (唯一の軽量 tier、model と reasoning の
  2 軸が同時に動くことを明記) + `gpt-5.6-luna` @ `max` (reasoning 固定の単一軸 control)。
  terra は実測で最も重いため除外。
- **(P3)** reasoning 軸の所有は T-181。本 wave は sol / luna を `max` に固定する。
- **(P4)** 主指標 = finding coverage / 誤検出 / token / model_calls。wall-clock は交絡タグ付き観測値。
- **(P5)** `prompt_hash` と token の定義は `codex_worker_ledger.py` の正本をそのまま使い再定義しない。
- **(P6)** receipt は**要求値の記録であり served model の attest ではない**。実測: mini の 400 が
  実体 `gpt-5.4-mini-codex-1p-codexswic-ev3` を露出する一方 receipt は `gpt-5.4-mini`。
  また不正値 `reasoning=ultra` は sol/luna/terra で **rc=0 のまま成功し receipt に `ultra` と残る**。
  この限界を receipt 出力へ明示する。
- **(P7)** 段 7 の全履歴 provenance は別 wave (`dev-wave-ai-provenance-forward-fix`、
  ユーザー裁定 = 履歴非改変・forward-only) の land 依存。本 wave 由来 commit は `--range` で
  緑を要求し、pre-existing 1 件 (`6b64d21`) は scope 外として記録する。

## 分割・環境

- 実装単位 1 (Codex `role=author`、所有 = 上記 2 ファイル)。docs・実走・変異・受入・記録は親。
- 受入環境 = 本 worktree・ログインノード。CCBench 実行なし。live inference は shadow arm のみ。
