# T-180 段 4 裁定 + plan v2 + 変異事前登録

段 3 は A (正しさ境界) / B (整合・層) とも NO-GO。所見を real/refuted、採用/不採用、scope 内/外に
裁定し、plan v2 を確定する。親自身の brief の過大表現も是正対象に含めた。

## 1. 親が独立に裏取りした事実

- **A-3 は real (親が実コードで再現)**: `_validated_usage` は `cached_input_tokens > input_tokens`
  を通し、`_billable({input:100, cached:200, output:1})` = **-99**。負の消費を報告する job を
  上限判定に使うと token cap は自明に破れる。T-179 から継承した欠陥であり本 wave で塞ぐ。
- **`docs/dev-wave/**` = 23,962 / 24,000 bytes (残 38)** を親が実測。DW-O01 の書き換えは
  予算的にも一度しか許されない。
- T-179 は 10 session_id と stage の独立 oracle を凍結済み
  (`2026-07-29_t179-worker-ledger-verbatim/README.md`)。実データ受入に使える。

## 2. 裁定表

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A-1, A-2, B-6 | rollout tail は post-hoc 観測で、buffer/欠落時に token・model_calls を強制できない。usage 0 の accepted 経路が残る | **real / 採用** | R1, R2, R3 |
| A-3 | `cli_reported` が負になりうる | **real / 採用** | R4 |
| A-4 | thread ID の遅延・変化・複数 session。brief の「起動直後」は 2 秒 poll からの過大表現 | **real / 採用** | R5, R13 |
| A-5 前半 | `setsid()` で group を逃れた孫を殺せない | **real / 部分採用** | R6 (残存を証拠化)、完全封じ込めは scope 外 |
| A-5 後半 | workspace-write の retry が半端な変異を次 attempt へ持ち込む | **real / 採用** | R7 |
| A-6 | latch 後に SIGTERM handler が正常出力を書けば accepted になりうる | **real / 採用** | R8 |
| A-7, B-4 | manifest に wave identity がなく別 wave が混入。既存 `WaveManifest` と同名二義化 | **real / 採用** | R9 |
| A-8, B-2 一部 | manifest の完全性検査が `--strict` 依存 (T-179 F54 と同型の「0 件で健全」) | **real / 採用** | R10 |
| A-9 | 「既存値不変」は unchanged invocation にしか成立しない | **real / 採用** (親 brief の是正) | R11 |
| A-10 | receipt を `O_EXCL` で作った直後の crash が恒久 DoS | **real / 採用** | R12 |
| A-12, B-9 | 変異帰属が弱い。truth table が閉じていない | **real / 採用** | R14, R15 |
| B-3 | manifest の job/attempt を ledger が捨て、job 数・retry lineage が衝突 | **real / 採用** | R16 |
| B-5 | 「全非採用を retry」は `all retryable` という分類であり T-183 越境 | **real / 部分採用** | R7 (read-only 限定) + 分類は T-183 |
| B-7 | 凍結 10 session を使う実データ受入がない | **real / 採用** | R17 |
| B-8, A-末尾 | probe package が監査不能 (rollout 未参照・hash なし・TSV 破れ) | **real / 採用** | R18 |
| B-10 | CLI version / executable identity / group 残存が receipt にない | **real / 採用** | R6, R19 |
| B-12 | 低層 primitive は再利用すべき | **real / 採用** | R20 |
| B-1, B-11(A-11) | DW-O01 の結線と上限値の policy | **real / scope 外** | R21 (T-184 へ) + 本 wave 内 dogfood |
| B-11 | stdout/artifact bytes の上限 | **real / scope 外** | 裁定パッケージ (T-185 類似) |
| A-5 完全封じ込め (cgroup/bwrap) | — | **scope 外** | 裁定パッケージ |
| manifest の seal ceremony | — | **scope 外** | header 不変 + wave_id 束縛で代替 (R9) |

## 3. plan v2 (実装する内容)

### R1 二重 metering と正直な射程

- **wall-clock だけが hard cap**である。`model_calls` と token は
  「観測可能な proxy による best-effort 停止 + 事後 fail-closed 判定」と receipt・docs で明記し、
  `hard cap` と名乗らない。
- metering source を 2 系統持つ: **live = rollout tail** (停止に使う)、
  **terminal = stdout `turn.completed.usage`** (判定に使う)。
  両者が揃い矛盾しないことを accepted の必要条件にする。
  片方しか無い場合は「停止はできなかったが判定はできる」経路として非採用にする。

### R2 metering evidence 必須

- accepted の必要条件に「`info` が object の `token_count` を 1 件以上観測」かつ
  「stdout の最終 `turn.completed.usage` が存在」を加える。
- 観測 0 件は `metering_status="missing"` として **非採用**。0 として受理しない。
- rollout と stdout の最終累積が不一致なら `metering_status="inconsistent"` で非採用。

### R3 名称の是正

- `--max-billable-tokens` → **`--max-cli-reported-tokens`** (T-179 の "CLI reported" と同義)。
- receipt の該当 field は `cli_reported`。`billable` の語は使わない。
- `model_calls` は「観測済み `token_count` event 数」であり admission counter ではない旨を
  receipt の `model_calls_semantics: "observed_token_count_events"` として明示する。
- 最大 1 call 分の不可視 overshoot がありうることを receipt の
  `possible_unobserved_overshoot: true|false` で表出する。

### R4 usage 整合検査

- `cached_input_tokens > input_tokens` を **malformed** として扱う (launcher・ledger の両方)。
- ledger 側は既存 `_validated_usage` に検査を追加し、issue に `usage_cached_exceeds_input` を出す。
  これは**受理集合の縮小**であり、事前登録変異 M13 と正例 P2 で両方向を固定する。

### R5 session lineage を配列で持つ

- Attempt は `session_ids: [uuid, ...]` を持つ (0 件以上)。単一 ID 前提を捨てる。
- 観測した全 session を manifest へ記録する。非採用 attempt の session も削除しない
  (費消した資源を台帳から消さない)。
- brief の「起動直後に出る」は「本 probe では 2 秒の poll 粒度で観測」に是正する。

### R6 終了の検証と残存の証拠化

- `tools/dev_waves/worker.py` の `read_pid_identity` / `terminate_verified_group` を再利用する
  (B-12, B-10)。PID 再利用を跨いだ誤 kill を避ける。
- TERM → grace → KILL → reap。receipt に `process_group_residual: int` と
  `termination_verified: bool` を残す。残存があれば **accepted にしない**。
- `setsid()` で逃れた孫は killpg の射程外である。これを「封じ込めた」と主張せず、
  receipt の `escaped_process_containment: "not_attempted"` として正直に記録する。

### R7 retry の境界

- `--max-attempts` 既定 1。**`> 1` は `--sandbox read-only` の job でだけ許す**。
  workspace-write で `> 1` を渡したら引数エラー (rc=2) とする。
  理由 = 非採用 attempt の filesystem 変異が次 attempt の入力を変え、retry 同一性が壊れるため。
- 失敗型の分類・safety-filter 判定・backoff・escalation は**実装しない** (T-183 所有)。
  receipt には `retry_classification: "none"` を記録し、分類していない事実を残す。

### R8 上限停止は無条件に非採用

- `limit_trigger != null` の attempt は、Codex rc・validator rc・出力内容にかかわらず
  **決して accepted にしない**。
- receipt 作成時に証拠を封じる: stdout・rollout・output の
  `sha256` と `bytes` (rollout は読んだ byte offset) を記録する。
  receipt 後に追記された event は receipt の主張に影響しない。

### R9 manifest の identity と改名

- 型名を **`CodexWorkerSessionManifest`** とする (`tools/dev_waves/schema.py` の
  `WaveManifest` と別物であることを名前で分離、D75)。
- create-only header: `schema_version`, `wave_id`, `repo_root`, `base_commit`。
  header は最初の append で確定し、以後不変。`--wave-id` が header と異なる append は rc=2。
- receipt は `manifest_path` と **`manifest_wave_id`** の両方を持つ。
  `check-receipt` は membership と wave_id 一致の両方を検査する。

### R10 完全性は無条件

- `--manifest` 指定時、**`--strict` の有無にかかわらず** 次を rc=2 とする:
  structural error、file 欠損、`sessions` 空、manifest にあるのに rollout に無い session。
- rollout file の選択は filename・`session_meta.session_id`・manifest の**三者一致**を要求する。
  file 内に複数 `session_meta` がある場合は既存どおり issue に残しつつ、
  manifest 選択では exact 一致した ID の record だけを採る。

### R11 受理集合変更の明示

- `--manifest` は既存 `--cwd-contains` と**同時指定不可** (argparse rc=2)。
- 「既存値不変」の主張は **`--manifest` を指定しない invocation に限る**と brief・worklog に書く。
  manifest 選択は意図的な受理集合の縮小であり、R17 の実データ受入で意図どおりかを確認する。

### R12 receipt の原子的書き込み

- 同一 directory の temp file を `O_EXCL` で作り、write → fsync → `os.replace` → parent fsync。
  最終 path は「不在」か「完全」のどちらかにしかならない。
- 既存の**完全な** receipt がある場合だけ上書きを拒否する (部分 receipt による恒久 DoS を作らない)。

### R13 race の扱い

- thread ID 未到来: wall-clock 監視は継続し、`--evidence-grace-s` 到達で group 終了、
  `evidence_status="missing"` で非採用。
- rollout 未作成: grace 内は再探索。作成後は byte 0 から読む。
- process 先行終了: 最終 drain を一度行い、stdout 最終 usage で判定する。
- 上限到達と自然終了が同一 poll: 終了を先に確定し、`actual <= limit` のときだけ正常完了を許す。

### R14 receipt truth table を閉じる

- `outcome` / `stop_reason` / `launcher_rc` / `limit_trigger` / `accepted` の相互拘束を
  全組合せの表として実装し、writer と checker が**独立の実装**で同じ表を検査する。
- `check-receipt` は receipt の自己申告を信じず、output hash・validator 再実行・manifest membership・
  metering 整合を再計算する。

### R15 変異帰属の設計

- 各上限テストは**他の上限を十分高く**設定し、`stop_reason` の exact 値・最初の失敗・
  attempt 数・PID 消滅を assert する。rc だけを見ない。
- fake codex は次を再現できること: 正常、no-token (metering 欠落)、
  ID 遅延 / ID 変化 / 複数 session、`setsid()` 脱出子、latch 後に正常出力を書く SIGTERM handler、
  receipt 後に追記する late writer、rollout 未作成。
- 並列 manifest テストは barrier を置き、lock 除去変異が偶然直列化で生き残らないようにする。

### R16 ledger の job/attempt 公開

- `--manifest` 指定時、各 record に `job_id` / `attempt_index` を公開する。
- worklog 比較の job 数は **distinct `job_id`** とする。
- retry lineage は manifest の対応から取り、prompt hash 推測を `--manifest` 経路では使わない。
- `--manifest` 未指定時は既存挙動 (prompt hash 推測) をそのまま残す。

### R17 実データ受入 (親が実施、F54 の要素単位照合)

T-179 が凍結した 10 session_id で manifest を作り、次を親が実測する。

```
codex_worker_ledger.py --manifest <t179-10-sessions.json> --json --strict
expected: issues={} / sessions=10 / model_calls=434 / cli_reported=2757982
```

stage 別 6 値 (plan 1/39/224,150、consult 2/62/392,185、author 1/47/171,736、
review 2/87/544,553、fix 2/100/605,734、focus 2/99/819,624) を**逐件**照合する。
集約一致だけを根拠にしない (F54)。

### R18 probe package の監査可能化 (親が実施)

- `probe/` に再現 script、CLI version、`session_meta` の bounded 抜粋、
  全 `token_count` の時刻と usage、rollout の sha256 を保存する。
- `liveness.tsv` の単独 `0` 行 (grep fallback の混入) と末尾 1 列行を除去し、4 列契約を守る。
- 「唯一の seam」は「本 probe で観測できた唯一の live seam (CLI 0.146.0、1 実走)」に縮小する。

### R19 実行 identity

- receipt に `codex_version`、resolved executable の絶対 path と sha256 を記録する。
- retry 間で binary が変わったら非採用にする。

### R20 primitive 再利用

- `orchestrator/codex_roles/events.py` の `strict_json_loads` / `parse_jsonl`、
  `tools/dev_waves/schema.py` の `strict_loads` / `canonical_bytes`、
  `tools/dev_waves/worker.py` の group 終了 helper を再利用する。
  exact な `Receipt` / `WaveManifest` 型は意味が違うので共用しない (B-12 の裁定どおり)。

### R21 DW-O01 結線は scope 外 (T-184 へ)

- 理由 1: `docs/phase3.md` の T-184 が「model/reasoning/resource/retry の stage matrix を
  **DW-O01 と worker 契約へ一度だけ反映する**」と明示所有している。
- 理由 2: 上限の**数値**は stage policy であり T-184 の所有。T-180 が数値を決めるのは越境
  (B-1 自身がそう指摘している)。
- 理由 3: 残 38 bytes の予算で DW-O01 を二度書き換えるのは不経済。
- **死蔵回避**: 本 wave の**段 6 レビュー worker を新 launcher 経由で起動**して dogfood し、
  実 receipt と manifest を生成する。生成物は R17 と同じ ledger で検証する。
  これにより「誰も使わない機構」ではなく、実運用 1 件の証拠を持って T-184 へ渡す。
  launcher が失敗した場合は raw DW-O01 形へ退避し、その事実を worklog に書く。
- 本 wave は「dev-wave worker が全件 launcher を通る」とは**主張しない** (A-11 の縮小要求を採用)。

## 4. 実装単位 (DW-S05-A、所有素集合)

| 単位 | 所有ファイル | 内容 |
|---|---|---|
| A | `tools/codex_worker_launch.py` (新規)、`orchestrator/tests/test_codex_worker_launch.py` (新規) | R1〜R3, R5〜R9, R12〜R15, R19, R20 |
| B | `tools/codex_worker_ledger.py`、`orchestrator/tests/test_codex_worker_ledger.py` | R4, R9 の manifest parser (独立実装)、R10, R11, R16 |

manifest schema は本書で凍結し、A と B が**独立に**strict parser を実装する
(同一 spec の 2 実装 = 相互の独立 oracle)。

### 凍結 manifest schema

```text
CodexWorkerSessionManifest = {
  schema_version: 1,
  wave_id: string (1-128 ASCII, [A-Za-z0-9._-]+),
  repo_root: absolute-path,
  base_commit: lowercase-hex40,
  sessions: [
    { job_id: string (1-128, 同 charset),
      attempt_index: int >= 1,
      session_id: canonical lowercase UUID },
    ...   // 1..1024 件、(job_id, attempt_index) 一意、session_id 一意
  ]
}
```

未知 field 禁止、duplicate key 禁止、bool-as-int 禁止。

## 5. 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由で赤くなること、当該位置より前に同じ入力を拒否する検査が
ないことを実装後 anchor 再検証時に確認する (DW-M07)。

| ID | 変異 (単一箇所) | 期待 kill node |
|---|---|---|
| M1 | `limit_trigger != null` でも accepted を許す | `test_limit_stop_is_never_accepted` |
| M2 | metering 観測 0 件を 0 として受理 | `test_missing_metering_evidence_is_not_accepted` |
| M3 | token 上限に `input_tokens` を使う (cli_reported 定義を捨てる) | `test_token_cap_uses_cli_reported_definition` |
| M4 | SIGKILL 昇格を削除し TERM だけにする | `test_sigterm_ignoring_child_is_killed` |
| M5 | attempt 間で累積カウンタを reset | `test_cumulative_limits_do_not_reset_between_attempts` |
| M6 | `max_attempts` の off-by-one (N+1 を起動) | `test_max_attempts_never_spawns_extra_attempt` |
| M7 | workspace-write でも `--max-attempts>1` を許す | `test_workspace_write_retry_is_refused` |
| M8 | manifest append の lock を外す | `test_parallel_jobs_preserve_both_manifest_entries` |
| M9 | receipt を temp+rename でなく最終 path へ直書き | `test_partial_receipt_never_visible_at_final_path` |
| M10 | `check-receipt` の output hash 再計算を省く | `test_check_receipt_detects_output_tampering` |
| M11 | append 時の header `wave_id` 照合を外す | `test_manifest_refuses_foreign_wave_id` |
| M12 | manifest 欠損 session を `--strict` 時だけ rc=2 にする | `test_manifest_missing_session_fails_without_strict` |
| M13 | `cached > input` の検査を外す | `test_cached_exceeding_input_is_malformed` |
| M14 | 空 `sessions` の manifest を rc=0 で通す | `test_empty_manifest_is_rc2` |
| M15 | `--manifest` 時も job 数を `len(records)` で数える | `test_job_count_is_distinct_job_id_under_manifest` |
| M16 | rollout と stdout の最終 usage 不一致を無視 | `test_inconsistent_metering_is_not_accepted` |

**正例 (過剰拒否の検出、DW-M01 後段)**

| ID | 正例 | 期待 |
|---|---|---|
| P1 | 上限内・metering 完備・validator rc=0 の job | accepted、rc=0 |
| P2 | `--manifest` 未指定で T-179 の凍結 10 session を再現 | 10 / 434 / 2,757,982 が不変 |
| P3 | actual == limit ちょうどで自然終了 | accepted (境界で過剰拒否しない) |

## 6. scope 外として裁定パッケージへ返すもの

1. DW-O01 の結線と stage 別上限値の採用 (T-184 所有)。
2. stdout / artifact bytes の上限 (`max_artifact_bytes`)。「resource envelope」の射程を
   compute-usage (wall / model_calls / token / attempts) に限定し、disk は別 ID へ。
3. `setsid()` 脱出子の完全封じ込め (cgroup / bwrap)。本 wave は残存の証拠化まで。
4. manifest の seal ceremony と最終 digest の台帳束縛。
5. 「全 worker が launcher を通る」ことの機械強制 (dispatcher gate)。
