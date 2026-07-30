# T-180 段 1 brief — job 単位 resource envelope と fail-closed receipt

対象 = dev-wave の **Codex worker job** (DW-O01 で起動する `codex exec`)。
`orchestrator/codex_roles/launcher.py` (Phase 3 role 用・activation BLOCKED の dormant 実行系) は
別層であり本 wave の対象外。

## 前提実測 (段 1 で実施、模擬でなく実走)

- `codex-cli 0.146.0` は turn / token / wall-clock / retry の**上限 flag を一切持たない**
  (`codex exec --help` 全文)。よって封筒は wrapper 側でしか強制できない。
- probe1 (`probe/events.jsonl`): stdout `--json` は `thread.started.thread_id` を**起動直後**に出す。
  この値は rollout の `session_meta.payload.session_id` およびファイル名と**一致**した
  (`019fadcd-a610-76e2-ab1e-57440d35d795`)。→ wave 受理集合を cwd 部分一致でなく session_id で
  決定的に束縛できる (T-179 が本 ID へ送った積み残し)。
- probe2 (`probe/liveness.tsv`、4 step の多 model call job): rollout JSONL は**実行中に逐次 flush**
  され、`token_count` event が t=12/20/29/37/39 秒で 1→5 と増えた。stdout 側は
  `turn.completed` まで usage を出さない (usage は最後に 1 回だけ)。
  → **live 強制の唯一の seam は rollout tail**。stdout は thread_id 取得と item 進行にだけ使う。
- probe2 の stdout `turn.completed.usage` は rollout 最終 `total_token_usage` と**完全一致**
  (input 84,667 / cached 64,512 / output 299)。T-179 の "CLI reported" 定義
  (`input - cached_input + output` = 20,454) がそのまま receipt に載る。
- 既存被覆の確認: `tools/dev_waves/` の上限は **Claude wave supervisor** のもの
  (`max_waves` / `per_wave_timeout_s` / `total_timeout_s`) で、Codex job 単位の封筒は無い。
  `orchestrator/codex_roles/events.py` の `validate_event_stream` は `_ALLOWED_ITEM_TYPES` が
  `reasoning`/`agent_message` のみで **command_execution を拒否**するため dev-wave worker には
  流用不可。流用するのは `parse_jsonl` / `strict_json_loads` の強化済み decode だけ。
  → 純増する検出力 = 「job 単位の上限到達停止」と「receipt 欠損拒否」。

## scope

1. 新規 `tools/codex_worker_launch.py`: DW-O01 形の起動を包み、job 単位で
   `--max-wall-clock-s` / `--max-model-calls` / `--max-billable-tokens` / `--max-attempts` を強制する。
   超過は process group ごと終了させ、**必ず receipt を書いてから** rc≠0 で fail-closed。
2. receipt (JSON): limits、actuals (wall_clock_s / model_calls / billable_tokens)、outcome、
   session_id、model、reasoning、validator rc、exit code、stop_reason。
3. wave manifest: job ごとに session_id を追記し、wave の受理集合を決定的に固定する。
4. `tools/codex_worker_ledger.py` に `--manifest` selector を追加 (`--cwd-contains` は残置)。
5. 受入テスト (fake codex bin を `--codex-bin` seam へ注入、実 inference なし):
   正常完了 / wall-clock 停止 / model-call 停止 / token 停止 / retry 上限 / receipt 欠損拒否 /
   manifest 選択。

## 不変条件

- model / reasoning の**既定値は変えない** (DW-O01 の値を引数として受け取るだけ)。
- テストは実 codex を呼ばない。注入は `--codex-bin` の正規 seam であり monkeypatch でない (DW-O14)。
- **T-183 の scope を持ち込まない**: 失敗型分類・safety-filter 判定・回復経路は T-183 の所有。
  本 wave の retry は分類なしの機械的上限のみ。
- ledger の既存出力・既存値は不変 (manifest は追加 selector であり既定を変えない)。
- 語彙: `turn` を使わず `model_calls` (T-179 の是正語彙、D75 の同名識別子二義化禁止の趣旨)。
  codex stdout の "turn" (exec 1 回 = 1 turn) と model call を混同しない。
- `--ephemeral` は使わない (rollout が消え live 強制と receipt の裏取りが不能になる)。

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- (P1) live 強制は rollout tail で行う。stdout に usage が来ないという実測に基づく。
- (P2) 実装は単一ファイル `tools/codex_worker_launch.py` (ledger と対称の書き味)。
- (P3) retry は同一 prompt の再実行を最大 N 回。分類は行わない (T-183 境界)。
- (P4) receipt 欠損拒否は launcher 自身の rc と、独立検査 mode の両方に置く。
- (P5) 上限到達時も既に得られた部分出力は破棄せず receipt に記録する (証拠保全)。

## 成果物影響 (DW-G05)

- 未実装なら wave 資源台帳は cwd 部分一致に依存し続け、worktree path 再利用・接尾辞衝突で
  別 wave の session を混入させる。worklog に載る session 数 / token 値が誤る。
- F43/F45 型の暴走 job (168k tokens 後に 194-byte 断片、243k tokens で safety 終了) が
  上限なしに費消し続ける。receipt が無いと「その job が存在し、なぜ止まったか」を
  受入で機械的に主張できない。

## 条件評価

- DW-O08 / O09 / O10: **不成立**。`FROZEN_MANIFEST` は `output/` 23 件のみで `tools/` を含まず、
  本 wave は凍結 bytes を変えない (grep で確認)。
- DW-O13: **成立** (新 gate)。入力 field の実在は上記 probe で実測済み。
- DW-O01 / O02 / O05 / O17 / O18 / O19 / O20: 成立。O11 (削除) は不成立。

## 環境・分割

- 受入全走・実測は本 worktree (ログインノード)。計算ノード不要。
- 受理集合が変わるため軽量版にせず、段 2 plan + 段 3 敵対相談 2 本 + 段 6 敵対レビュー 2 本を置く
  (DW-C00)。実装面は Codex `role=author` が書き、親は brief・裁定・統合・変異・受入・記録のみ。
