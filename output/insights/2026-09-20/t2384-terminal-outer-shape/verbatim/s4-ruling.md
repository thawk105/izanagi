# 段 4 裁定 (r2) — [T-2384] terminal record の外枠 exact gate (D1730)

裁定日時: 2026-09-20 08:01 JST。入力: s1-brief (+ 追補 07:53)、s2-plan (r2、07:55)、s3-consult-A (r2、must-fix 0 / nit 2)、s3-consult-B (r2、must-fix 0 / nit 3)。r1 の成果物 (`codex/invalidated-r1/`) は DW-O13 の期限超過で無効化し、流用していない。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) に本 wave 関連の未記録裁定なし (T-2384 / D1730 / FC07 で hit 0、08:00 再走査)。

## 1. 所見の裁定

| id | 判定 | 採否 | scope | 処置 |
|---|---|---|---|---|
| A01 (P1 の根拠が過大) | real | 採用 | 内 | insight に terminal 一意性の根拠を「pipeline の終了経路 (`pipeline.py` 1786 / 1932 / 2436〜2437 / 2530〜2531) + recovery が active attempt だけに追記 (`wal.py` 2627〜2671)」と書き、`wal.py` 2355〜2371 は「terminal を見たら active から除く処理」と限定する。DW-O13 の attempt 単位 16 件は全て commit で、abort の一意性は code 経路の確認に留まると明記 |
| A02 (M5 の等価性は配置に依らない) | real | 採用 | 内 | 等価理由を「exact keys の下で root `stage` が必ず存在し `_wal_field` は root を返す」だけにし、配置の因果は書かない |
| B1 (末尾性項と M09 は削除可) | real | 採用 | 内 | helper の末尾を `return terminal_count == 1` にし、末尾性項・M09・`test_fc07_rejects_nonterminal_after_abort` は作らない (既存 outcome 別 stage 判定と過剰決定、DW-M03) |
| B2 (両入力経路の説明) | real | 採用 | 内 | insight に「canonical-list 経路は `parse_line` を通らず外枠 gate が必要、frame 経路は外枠は上流で閉じるが projection 内の terminal 件数は上流が見ない」を書く。新 test は canonical-list 経路のみ (frame 経路の実測は主張しない) |
| B3 (brief の表記) | real | 採用 | 内 | brief 本文の「11 file」「行 17」は追補で訂正済み (行 893・表の項目 17)。研究前進は B の文案で insight に書く |
| 親: 等価変異の登録 | real | 採用 | 内 | 到達不能述語 (payload dict / ts 有限) の変異は spec に載せず insight に記す (DW-M01 / F28)。逐語 B-057-M5 は `positive` / SURVIVED / `expected_nodes` 空で 1 件だけ載せる — 依頼が名指しする変異の等価性を diff 付きで実測する目的と、harness の SURVIVED 検出の正例を兼ねる。再照準は合成変異 M02 |
| 親: 過剰拒否の正例 (DW-M01) | real | 採用 | 内 | 受理集合を縮小する wave なので、`ts` を int 限定へ狭める変異 M09 を `positive` / KILLED で登録し、float ts 正例が殺すことを実測する |

scope 外の real 所見: なし。裁定パッケージへ返す項目: なし。

## 2. plan v2 (実装子への確定仕様)

**consumer (`orchestrator/campaign/reflux_formal_consumer.py`)** — `_validate_wal_outcomes` (1133 行) の直前に helper を置く。行形は変異 anchor が `_wal_trigger` の同文と重ならないよう plan r2 のとおり (`terminal_ts`、variant / env_tag は別 `if`)。

```python
def _wal_terminal_shape_valid(records: Sequence[dict]) -> bool:
    terminal = records[-1]
    if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):
        return False
    if type(terminal["variant"]) is not str:
        return False
    if type(terminal["env_tag"]) is not str:
        return False
    terminal_ts = terminal["ts"]
    if type(terminal_ts) not in (int, float):
        return False
    if type(terminal_ts) is float and not math.isfinite(terminal_ts):
        return False
    if type(terminal["payload"]) is not dict:
        return False
    terminal_count = sum(
        record.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
        for record in records
    )
    return terminal_count == 1
```

- `terminal = wal_records[-1]` (1142 行) の直後、`attempt = ...` の前に `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))` を 1 行足す。
- `_wal_trigger` / `_wal_field` / 既存の commit・abort 判定式 / reason code / import は 1 byte も変えない (`math`、`STAGE_COMMIT`、`STAGE_ABORT`、`Sequence` の import 済みを実装子が確認)。定数は共有しない。payload の key 集合は閉じない。非 terminal record の外枠は検査しない。

**test (`orchestrator/tests/test_reflux_formal_consumer.py`)** — 1652 行付近 (既存 FC07 terminal 形状 test の隣)。共通手順 R = `wal = _projection_records(case, 0)` → 改変 → `_rewrite_wal(case, 0, wal)`。負例は `_assert_reason(case, C.FormalReasonCode.FC07)`、正例は `result = _evaluate(case)` が `type(result) is C.P6Unavailable` かつ `result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE`。parametrize id は ASCII のみ。既存 helper・既存 test の期待値は変えない。

| # | test | 組み立て | 期待 |
|---|---|---|---|
| 1 | `test_fc07_rejects_terminal_root_attempt_shadow` | 末尾 root `build_attempt_id` = 正しい attempt、payload 同名 = `"fixture-shadow-attempt"` | FC07 |
| 2 | `test_fc07_rejects_terminal_extra_root_key` | 末尾に `extra = 1` | FC07 |
| 3 | `test_fc07_rejects_terminal_missing_root_key[env_tag|ts|variant]` | 末尾から該当 key を `del` | FC07 ×3 |
| 4 | `test_fc07_rejects_terminal_invalid_outer_type[ts-bool|ts-str|variant-int|env-tag-none]` | `ts=True` / `ts="1788580082.583126"` / `variant=1` / `env_tag=None` | FC07 ×4 |
| 5 | `test_fc07_rejects_payload_only_terminal_stage` | `terminal["payload"]["stage"] = terminal.pop("stage")` | FC07 (B-057-M5 の直接 witness) |
| 6 | `test_fc07_rejects_duplicate_abort_terminals` | terminal を deepcopy して `[trigger, abort, abort]` | FC07 |
| 7 | `test_fc07_rejects_commit_before_abort_terminal` | `[trigger, commit 形 (exact 5 key、payload `{build_attempt_id: attempt, verify_configs: ["legacy","s2"]}`), abort]` | FC07 |
| 8 | `test_fc07_accepts_float_timestamp_abort_terminal_shape` | 末尾 abort の `ts = 1788580082.583126` | P6Unavailable |
| 9 | `test_fc07_accepts_nonterminal_extra_root_key` | `[trigger, build_start, abort]`、中間 record は `{"variant": "fixture-v", "stage": "build_start", "env_tag": "fixture-env", "ts": 0, "payload": {"build_attempt_id": attempt}, "extra": 1}` | P6Unavailable |

9 関数 / 14 node (負例 12、正例 2)。既存正例 `test_exact_fixture_contract_reaches_only_p6_unavailable` / `test_fc07_accepts_production_commit_terminal_shape` は無変更。

**焦点走 (12 file、`tools/run_tests.py --force-dispatch`、計算ノード):** `orchestrator/tests/` の test_reflux_formal_consumer、test_reflux_origin_fixture_builder、test_reflux_result_evidence、test_reflux_origin_client、test_reflux_origin_artifacts、test_reflux_origin_binding、test_reflux_origin_topology、test_reflux_source_closure、test_trial_registry、test_p3_autonomous_workload_trial、test_reflux_originless_compatibility、test_reflux_campaign_issuer。

## 3. 変異の事前登録 (DW-M01、実装前に凍結)

runner: `python3 tools/run_tests.py --force-dispatch <12 file> -q -rf`。source = D1009 の独立 clone (`make-mutation-source.sh`、`git clone --local --no-checkout` + main を実装 commit に固定 + `dev_wave_submodule_init.py`) を `tools/mutation_worktree.py --source-repo` へ渡す。clone の submodule 初期化が `nonlocal-url` で拒否されたときは、主 repo の登録 worktree (`git worktree add -b mut-t2384-… <path> <commit>` + 同 tool) に `tools/mutation_harness.py --repo` を直接当てる経路へ切り替え、README に erratum として書く (DW-O12)。probe 走 (全件 SURVIVED 登録・`expected_nodes` 空で観測 node を集める) → final 走 (完全集合) の 2 段。`old` は実装 commit の実物で一意性 (`--plan-only`) を再検証する (DW-M07)。

| id | category | 置換 (old → new、consumer 内 1 行、インデント維持) | 期待 | 殺す test の予測 (完全集合は probe で確定) |
|---|---|---|---|---|
| M01 逐語 B-057-M5 | positive | `_require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)` → `_require(FormalReasonCode.FC07, _wal_field(terminal, "stage") == STAGE_ABORT)` | **SURVIVED (等価)** | — (exact keys の下で root `stage` が必ず存在し `_wal_field` は root を返す。注入実在は mutated diff で確認) |
| M02 gate 無効化 + M5 | both-layers | 2 置換: `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))` → `_require(FormalReasonCode.FC07, True)`、および M01 と同じ置換 | KILLED | #5 payload-only-stage + M06 の集合 |
| M03 superset 許容 | negative | `if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):` → `if not {"variant", "stage", "env_tag", "ts", "payload"} <= set(terminal):` | KILLED | #1 root shadow、#2 extra key |
| M04 ts bool 許容 | negative | `if type(terminal_ts) not in (int, float):` → `if type(terminal_ts) not in (int, float, bool):` | KILLED | #4 ts-bool |
| M05 件数検査除去 | negative | `return terminal_count == 1` → `return True` | KILLED | #6、#7 |
| M06 gate 無効化 | negative | `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))` → `_require(FormalReasonCode.FC07, True)` | KILLED | #1、#2、#3 ×3、#4 ×4、#6、#7 (= 11 node)。#5 は既存 stage 判定が拒否するので数えない |
| M07 variant 型検査除去 | negative | `if type(terminal["variant"]) is not str:` → `if False:` | KILLED | #4 variant-int |
| M08 env_tag 型検査除去 | negative | `if type(terminal["env_tag"]) is not str:` → `if False:` | KILLED | #4 env-tag-none |
| M09 過剰拒否 (ts を int 限定) | positive | `if type(terminal_ts) not in (int, float):` → `if type(terminal_ts) is not int:` | KILLED | #8 float ts 正例 |

登録しない (到達不能・等価として insight に記録): payload dict 述語の無効化 (root attempt 無しは resolver `_projection_attempt_id`、有りは exact keys が先に拒否)、ts 有限性述語の無効化 (canonical JSON に非有限値は乗らない)。

## 4. DW-G05 (成果物影響)

放置時: canonical-list 経路で terminal 外枠が不正な projection (flat / root-shadow / 重複 terminal) が FC07 を通り、後続判定と receipt / evidence-root 参照の発行へ進む。実装後: FC07 で拒否され reason が FC07 になる。certified 選択集合は不変 (D1730 限界節、`P6Unavailable`)。

## 5. 実装単位と権限

- Codex author 1 本 (D95)、unit worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2384-unit-impl` (branch `dev-wave-t2384-unit-impl`、base = local main `b7f970dfa507558f7fb669a5ab38958d6c76b57c`、manifest `child-manifest.json` 登録済み)、所有 path = 上記 2 file。fixture builder・producer・docs は所有外。
- 実装子は commit しない。親が patch を取り出し wave worktree へ適用、焦点走 12 file (計算ノード) → 実装 commit (Codex author trailer、DW-O17)。
- 段 6: 敵対レビュー 2 本 (1 本は過剰・削除レンズ)、fix は同 unit worktree で branch を切る。変異は実装 commit 後、独立 clone で probe → final。
