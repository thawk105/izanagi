# 段 1 brief — [T-1275] 受入 lease の待ち札を同一 process 内で再試行させる

wave: dev-wave-t1275-lease-ticket-retry / base main = 699c9cae / 2026-08-17 09:10 JST

## 確定済みユーザー裁定 (前提。覆す新事実が無い限り再裁定しない)

- **[T-1275] 択 (a)**: 待ち札は**同一 process 内で再試行**させる。D253 の待ち札意味論には触れない。
  (b) heartbeat の別経路、(c) 待ち札 TTL 延長は不採用。
  ruling package `output/insights/2026-08-17_t650-lease-release/ruling-package.md` R-A が
  (a) を「待ち手を切らさず、attempt の切り替えを process 内で行う。
  `--receipt-file` / `--log-file` の attempt ごと別 path 必須と噛み合わせる設計が要る」と定義している。
- **[T-1172]**: land 直前の lease renew を入れる。660 秒 > 300 秒が確定値なので実測を待たない。
  外側 deadline は不採用。「[T-1275] と同じ作業で扱ってよい」。

## brief 前の実測 (裁定の前提が今も成立するか)

1. `tools/dev_wave_wait.py:2954 run_acceptance` は **1 attempt で必ず終わる**。失敗すると
   `_cleanup_lifecycle` が lease を release して process が終了する。再試行は親の再投入しかない。
2. 待ち札の heartbeat を出すのは `claim` 呼び出しだけ (`tools/wave_land_window.py:543 _ensure_ticket`)。
   `_WAITER_TTL_SECONDS = 300` (同 :29) を超えて途切れた札は unlink され、次の `claim` で
   **新しい `queued_at_ns`** になる。→ 裁定の前提は現行コードで成立している。
3. 実害の実測 (`docs/failures.md` F365 / ruling package R-A): t1180-pilot-approval が
   20:20 赤 → 20:50 再投入 → `queued_at_ns` 20:50:17 → 21:42:28 に書き換わり **52 分の先着順位を喪失**、
   後着 3 本に追い越されて通算 79 分待ち。
4. 判定を 1 つも産まずに attempt が死ぬ経路が実在する: 受入 command が
   `dispatch` の `DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900` に当たって rc=16 で終わる型
   (**テストは 1 件も走らない**)。現行コードでは `child_rc not in (0, 1)` として
   `_StageFailure("acceptance-command", source_rc=...)` になる (`dev_wave_wait.py:3167`)。
5. 受領証 schema は **land 側が exact に pin している** — `tools/dev_wave_land.py:70`
   `_ACCEPTANCE_RECEIPT_SCHEMA = "dev-wave-acceptance-receipt/v3"`、root field 集合も exact 一致検査。
6. 既存被覆 (性質で検索): 「同一 process 内で attempt を再試行する」性質を主張するテストは
   `orchestrator/tests/test_dev_wave_wait.py` に **0 件**。純増検出力 = この性質全体。
7. `_acceptance_receipt_preflight` / `_acceptance_log_preflight` は receipt / log / red-check receipt が
   **既存でないこと**を要求する (`_external_new_file_preflight`)。attempt ごとに別 path が要るのはこの制約から。
8. T-1172 の数値: `_RECEIPT_PUBLISH_MIN_TTL_SECONDS = _STAGE_TIMEOUT_SECONDS = 300`
   (`dev_wave_wait.py:227,230`)、lease TTL 2400。受領証発行時に保証される残 TTL は 300 秒しかない。

## scope

- **S1 (主)**: `tools/dev_wave_wait.py` の受入経路に、**同一 process 内の attempt 再試行**を入れる。
  待ち手 process を attempt 間で切らさないことで、待ち札の heartbeat を途切れさせない。
- **S2 (従)**: land 起動直後に自 lease を 1 回 renew する (`tools/dev_wave_land.py`)。
  lease は advisory なので renew 失敗は land を止めない。

## 不変条件 (破ったら停止)

- **I1**: D253 の待ち札意味論を変えない — 到着順 = payload `queued_at_ns`、生存 = mtime、
  `_WAITER_TTL_SECONDS = 300`、縮退の 3 発火条件、`status` は札を読まない。
- **I2**: 受領証 schema `dev-wave-acceptance-receipt/v3` の版と root field 集合を変えない。
  変えるなら land 側 exact 集合の同時改訂と版 bump が必須で、それは本 wave の scope 外。
- **I3 (規律 2)**: 受理集合を緩めない。再試行は**判定を上書きしない**。
  赤の attempt を無かったことにせず、緑になるまで回す形にしない。
- **I4**: 受入の caller argv (`python3 tools/run_tests.py` ちょうど) を変えない。
  dev-wave docs は 3 層とも予算満杯かつ exact pin なので、**docs 改訂を要さない形**にする。
  新 flag を足すなら既定値で従来と同一挙動になるものだけ。
- **I5**: 緑を得た attempt の lease を、記録の体裁のために自分から release して取り直さない。
- **I6**: lease の既存契約 (env export + 絶対パス + `--lease-dir` 必須、poll 30 秒) を壊さない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 再試行の発火条件は「**その attempt が受入判定を 1 つも産まなかった**」に限る。
  現行コードでは `child_rc not in (0, 1)` の `acceptance-command` 失敗が該当する。
  `child_rc == 0` (緑) と `child_rc == 1` (赤) は判定を産んでいるので再試行しない。
- **(P2)** [T-1172] を本 wave に含める。編集面が素集合で、受入窓 (希少資源) を 1 本で済ませられる。
- **(P3)** 受領証・log の扱い: 失敗 attempt は受領証を発行しない (現行どおり)。
  成功 attempt の受領証と log は caller が指定した path に置く。
  失敗 attempt の log は派生 path へ退避し、caller path を次 attempt のために空ける。
- **(P4)** 再試行は有界にする。試行回数上限と既存 `--max-wait-seconds` 由来の全体 deadline の
  両方で必ず止まる。無限ループにしない。
- **(P5)** claim 前 preflight で落ちる型 (argv 誤り・provenance 赤) は親の介入が要るので
  再試行しない。この型は claim へ到達しないので札も作られない (F365 の恒久対応どおり)。

## 成果物影響 (DW-G05)

- **S1 未実装**: インフラ由来の非判定失敗 1 件ごとに、certified 選択・材料レポート・試行台帳の
  確定が 40〜70 分遅れる (実測 52〜79 分)。値そのものは変わらないが確定時刻が遅れ、
  待たされた後続 wave の受入結果が古い main を基準に取られる確率が上がる。
- **S2 未実装**: land の 660 秒中に lease が失効し、別 wave が窓を奪う。
  受入結果と land の間に他 wave の main 前進が挟まり、tested_tip と land 対象の乖離が起きる。

## 成果物の形

- `tools/dev_wave_wait.py` の受入経路の変更 + `orchestrator/tests/test_dev_wave_wait.py` の新規テスト
- `tools/dev_wave_land.py` の renew + `orchestrator/tests/test_dev_wave_land.py` の新規テスト
- 変異 matrix、worklog / decisions fragment、insights

## 分割方針 (段 5)

所有素集合の 2 単位。

- **U1**: `tools/dev_wave_wait.py`, `orchestrator/tests/test_dev_wave_wait.py`
- **U2**: `tools/dev_wave_land.py`, `orchestrator/tests/test_dev_wave_land.py`

## 環境

- 実装・テストは repo root (worktree) の親環境。受入全走は `python3 tools/run_tests.py` を
  `tools/dev_wave_wait.py acceptance` 経由で、Pegasus 計算ノードへ dispatch。
- lease dir は既存の env `IZANAGI_WAVE_LEASE_DIR` (絶対パス、`--lease-dir` 明示)。
