# [T-189] 段 1 brief — 不正な reasoning / effort 値の拒否を許可リストで機械強制する

wave branch: `worktree-dev-wave-t189-reasoning-allowlist` / base `e0b9073`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist`

## scope

子起動 CLI の 3 面に reasoning / effort の値域検査を入れる。

1. `tools/codex_worker_launch.py:2475` の `--reasoning` (現在 `required=True` のみ、値域検査なし)
2. `tools/dev_waves/cli.py:92` の `--effort` (現在 `required=True` のみ、値域検査なし)
3. `tools/dev_waves/schema.py:832` の `_EFFORT_RE` (形検査のみ。呼び出しは `:801` の
   `parse_worker_spec` と `:853` の `validate_child_argv` の **2 箇所**)

`docs/dev-wave/`、`tools/check_docs.py`、`tools/spool_fold.py` には触らない (T-328 / T-313 /
fold-rotation が走行中)。docs の条文追加は T-328 の land 後に回す。

## 確定済みユーザー裁定

[T-189] は択 (a) — 不正な reasoning 値の拒否 (許可リスト検証) だけ先に実装し、served model の
attest 経路が無い点 (F56) は実験の限界として明記する。model routing の比較実験は本 wave の
scope 外であり着手しない。

## 不変条件

- 許可リストは 1 箇所に置き、3 面が同じ正本を参照する。
- **値域を広げる方向の変更を混ぜない。** 既存の正当な呼び出しを壊さない。
- `orchestrator/codex_roles/launcher.py:355` の `{low, medium, high, xhigh}` と
  `spec.py:610` の `{medium, high}` は **role manifest の policy 集合**であり、そのまま
  3 面へ流用してはならない (下記 M5)。
- `_EFFORT_RE` の形検査は残す (P2)。

## 成果物の形

3 面の値域検査 + 各面の負例テスト (不正値で rc≠0 / 例外)、通る正例を各面 1 つ、
および `max` の扱いと F56 の限界を記録した insight。

## 成果物影響 (DW-G05)

実装しない場合: 不正な reasoning / effort が silent に通り、resource ledger と insight の
`requested_*` が「その構成で実際に走った」証拠として読まれる。model×reasoning の台帳値が
誤った構成へ帰属し、certified 選択に至る材料レポートの根拠 receipt が汚染される
(F56 恒久対応 (c) の未実装分)。

## 段 1 実測 (前提の裏取り)

- **M1** `claude --help` → `--effort <level>  Effort level for the current session
  (low, medium, high, xhigh, max)`。**`max` は Claude 側でも正当**。
- **M2** `claude -p --effort bogus` は rc=0 で fail-open (警告のみ)。一次資料 =
  `output/insights/2026-08-01_token-hygiene-audit/probes/cli-effort-failopen.md`。
- **M3** codex 側の受理集合は **model 依存** (F56 (c))。`gpt-5.4-mini` は `max` を拒否し
  `none`/`low`/`medium`/`high`/`xhigh` のみ。`gpt-5.6-sol` は `max` を受理。
  `codex exec --help` は reasoning を列挙しない (`-c model_reasoning_effort=` は config 経路)。
- **M4** `max` は **live**。`docs/dev-wave/workers.md` の `DW-S02` / `DW-S03` が `reasoning=max` を
  規定し、本 wave の段 2・3 自身が使う。`DW-S05-A` は `high`。insight 逐語にも `max` 起動が多数。
- **M5** `launcher.py:355` の集合は role manifest の policy 検査であり CLI capability 集合ではない。
  `spec.py:610` はさらに狭い `{medium, high}`。brief の警告どおり、そのまま流用すると段 2・3 が落ちる。
- **M6** `tools/` → `orchestrator/` の import は既存 (`codex_worker_launch.py:35` が
  `orchestrator.codex_roles.events` を import)。正本を `orchestrator/codex_roles/` 配下に
  置く配線は既存依存方向と一貫する。
- **M7** brief 外の同型面を 2 つ発見 (scope 外候補、段 4 で裁定):
  (4) `tools/task_runs/cli.py:81` の `--reasoning` — 台帳 **記録** CLI、値域検査なし
  (`--role` には choices あり)。
  (5) `tools/codex_reasoning_ab.py` — 直接 `codex exec` 起動面。`collect-run` にだけ
  `max|high` の allowlist があり、arm 名として `max`/`high` が全体に硬く束縛されている。
- **M8** `tools/dev_waves` supervisor は **fake-only / real 未開放 (D74)**。面 2・3 は現時点で
  実 `claude` 子を駆動していない (機械検査としては純増、live 経路としては未開放)。
- **M9 (DW-O09 判定)** `receipt_schema_digest` は `schema_v{n}.json` を hash する
  (`tools/dev_waves/receipt.py:110,121`)。`schema.py` の source は digest 源ではないため、
  面 3 の編集で凍結 receipt schema digest の bytes は動かない。
- **M10 (純増検出力)** `orchestrator/tests/` に reasoning / effort の不正値拒否を検査する
  テストは 0 件。本 wave が足す検査はすべて純増。

## 親の provisional 裁定 (攻撃対象)

- **(P1改)** 元の P1「許可集合 = {low, medium, high, xhigh, max}、`max` を許すのは codex 経路だけ」
  は **M1 が反証**した — `max` は Claude `--effort` でも正当値である。改めて提案する:
  正本は 1 モジュールに置くが **単一の平坦集合ではなく製品別の定数**とし、
  `CLAUDE_EFFORTS = {low, medium, high, xhigh, max}` (M1 実測)、
  `CODEX_REASONING_EFFORTS = {low, medium, high, xhigh, max}` (sol 基準、M3/M4) を並置する。
  `none` は repo 内に呼び出し実績が無いため**含めない** (値域を広げない不変条件)。
  model 別の絞り込み (mini が `max` を拒む) は本 wave では実装せず限界として記録する。
  これは親の provisional 裁定であり攻撃対象。
- **(P2)** `_EFFORT_RE` の形検査は残し、その上に値域検査を重ねる (形が壊れた入力の診断を失わないため)。
  これは親の provisional 裁定であり攻撃対象。
- **(P3)** 正本の置き場所は `orchestrator/codex_roles/` 配下の新規小モジュール (M6)。
  `launcher.py:355` / `spec.py:610` の既存集合は **広げない** — 正本を参照するよう書き換えるかは
  段 2 の設計事項。これは親の provisional 裁定であり攻撃対象。

## 並列分割方針

許可リストの正本を先に 1 箇所へ確定してから 3 面を同時に配線する。実装単位の所有は素集合にする。

- 単位 A: 正本モジュール + `orchestrator/codex_roles/` 側の参照
- 単位 B: `tools/codex_worker_launch.py` (面 1) + その負例/正例テスト
- 単位 C: `tools/dev_waves/cli.py` + `tools/dev_waves/schema.py` (面 2・3) + その負例/正例テスト

単位 A は B・C の先行単位。A 完了後に所有パス限定 patch を B・C へ展開して並列投入する。

## 受入環境

Pegasus gen_S 計算ノード (`--runner-mode dispatch`)。所在は worklog、機体固有情報は
`docs/pegasus-runbook.md`。
