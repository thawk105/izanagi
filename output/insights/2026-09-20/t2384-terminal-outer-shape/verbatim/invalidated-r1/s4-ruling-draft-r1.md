# 段 4 裁定 — [T-2384] terminal record の外枠 exact gate (D1730)

裁定日時: 2026-09-20 07:46 JST。入力: s1-brief、s2-plan、s3-consult-A (must-fix 0 / nit 3)、s3-consult-B (must-fix 1 / nit 3)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) に本 wave 関連の未記録裁定なし (T-2384 / D1730 / FC07 で hit 0)。

## 1. 所見の裁定

| id | 判定 | 採否 | scope | 処置 |
|---|---|---|---|---|
| A1 / B2 (brief P3 の説明が逆) | real | 採用 | 内 | brief の (P3) は「`stage` の fallback だけが死に、`build_attempt_id` / `verify` 等は payload fallback が必須で残る」に訂正。実装は plan どおり `_wal_field` を保存 |
| A2 / B2 (brief P4 の理由) | real | 採用 | 内 | 非 dict payload は「root attempt 無し → resolver で落ちる / root attempt 有り → exact keys で落ちる」の二分で記録。M7 相当の等価性は維持 |
| A3 (P1 の根拠) | real | 採用 | 内 | insight に producer の return 経路 (`pipeline.py` 1912〜1932、2185〜2188、2304〜2321、2435〜2437、2529〜2531) と recovery の対象選択 (`wal.py` 2560〜2586) を根拠として書く。gate は変えない |
| **B1 (M4 / M8 の anchor 非一意)** | **real (must-fix)** | 採用 | 内 | M8 は登録しない (下記)。M4 と過剰拒否正例 M7 の anchor は `ts = terminal["ts"]` から始まる複数行 block にし、累積後の一意性を harness の `--plan-only` で確認 |
| B3 (焦点走 12 file) | real | 採用 | 内 | `test_reflux_campaign_issuer.py` を足して 12 file |
| B4 (docs:893、研究前進の文) | real | 採用 | 内 | 研究前進の行は B の文案を採用: 「terminal 外枠が不正な projection を FC07 で拒否し、fixture 由来の形が後続判定と receipt 発行へ進む経路を閉じる。certified 選択集合は変えず、変わるのは拒否 reason と receipt / evidence-root 参照」 |
| 親 (plan の末尾性項と `test_fc07_rejects_terminal_before_last_record`) | real | 採用 | 内 | helper の `terminal.get("stage") in (...)` 項は既存 outcome 別 stage 判定と過剰決定 (DW-M03)。件数 1 だけにし、同 test は作らない (両層が同じ入力を拒否し単一理由にならない) |
| 親 (等価変異の登録) | real | 採用 | 内 | DW-M01 に従い到達不能述語の変異 M7 (payload dict) / M8 (ts 有限) は spec に載せず insight に「到達不能・等価」と記す。逐語 B-057-M5 は `positive` / SURVIVED 期待で 1 件だけ載せ、harness の SURVIVED 検出の正例と「gate 後は等価」の実測を兼ねる。再照準は合成変異 M2 |

scope 外の real 所見: なし。裁定パッケージへ返す項目: なし。

## 2. plan v2 (実装子への確定仕様)

**consumer (`orchestrator/campaign/reflux_formal_consumer.py`)**

- `_validate_wal_outcomes` (1133 行) の直前に helper を置く:

```python
def _wal_terminal_outer_shape(records: Sequence[dict]) -> bool:
    terminal = records[-1]
    if set(terminal) != {"variant", "stage", "env_tag", "ts", "payload"}:
        return False
    if type(terminal["variant"]) is not str or type(terminal["env_tag"]) is not str:
        return False
    ts = terminal["ts"]
    if type(ts) not in (int, float) or (
        type(ts) is float and not math.isfinite(ts)
    ):
        return False
    if type(terminal["payload"]) is not dict:
        return False
    return sum(
        record.get("stage") in (STAGE_COMMIT, STAGE_ABORT) for record in records
    ) == 1
```

- `terminal = wal_records[-1]` (1142 行) の直後、`attempt = ...` の前に `_require(FormalReasonCode.FC07, _wal_terminal_outer_shape(wal_records))` を 1 行足す。
- `_wal_trigger` / `_wal_field` / 既存の commit・abort 判定式 / reason code / import は 1 byte も変えない (`math`、`STAGE_COMMIT`、`STAGE_ABORT`、`Sequence` は既に import 済み — 実装子が確認)。
- 定数の共有はしない (`_wal_trigger` の bytes を変えないため)。

**test (`orchestrator/tests/test_reflux_formal_consumer.py`)** — 1680 行付近 (既存 terminal 形状 test の隣) に追加。共通手順 R = `_projection_records(case, 0)` → 改変 → `_rewrite_wal(case, 0, wal)` → 負例は `_assert_reason(case, C.FormalReasonCode.FC07)`、正例は `_evaluate(case)` が `C.P6Unavailable` かつ `reason_code is C.FormalReasonCode.P6_UNAVAILABLE`。parametrize id は ASCII のみ。

| # | test | 組み立て | 期待 |
|---|---|---|---|
| 1 | `test_fc07_rejects_terminal_root_attempt_shadow` | 末尾 root `build_attempt_id` = 正しい attempt、payload 同名 = `"fixture-shadow-attempt"` | FC07 |
| 2 | `test_fc07_rejects_terminal_extra_root_key` | 末尾に `extra = 1` | FC07 |
| 3 | `test_fc07_rejects_terminal_missing_root_key[env_tag|ts|variant]` | 末尾から該当 key を削除 | FC07 ×3 |
| 4 | `test_fc07_rejects_terminal_outer_value_type[ts-bool|ts-str|variant-int|env_tag-null]` | `ts=True` / `ts="1788580082.583126"` / `variant=1` / `env_tag=None` | FC07 ×4 |
| 5 | `test_fc07_rejects_payload_only_terminal_stage` | `terminal["payload"]["stage"] = terminal.pop("stage")` | FC07 (B-057-M5 の直接 witness) |
| 6 | `test_fc07_rejects_duplicate_terminal_stages[abort-abort|commit-abort]` | `[trigger, abort, abort]` / `[trigger, commit 形 (exact 外枠、payload `{build_attempt_id, verify_configs: ["legacy","s2"]}`), abort]` | FC07 ×2 |
| 7 | `test_fc07_accepts_float_timestamp_abort_terminal_shape` | 末尾 abort の `ts = 1788580082.583126` | P6Unavailable |
| 8 | `test_fc07_accepts_nonterminal_record_without_exact_outer_shape` | trigger と abort の間に `{"stage": "build_start", "payload": {"build_attempt_id": attempt}}` | P6Unavailable |

8 関数 / 14 node (負例 12、正例 2)。既存正例 `test_exact_fixture_contract_reaches_only_p6_unavailable` / `test_fc07_accepts_production_commit_terminal_shape` は無変更で P6Unavailable のまま。既存 test の期待値は変えない。

**焦点走 (12 file、`tools/run_tests.py --force-dispatch`):** test_reflux_formal_consumer、test_reflux_origin_fixture_builder、test_reflux_result_evidence、test_reflux_origin_client、test_reflux_origin_artifacts、test_reflux_origin_binding、test_reflux_origin_topology、test_reflux_source_closure、test_trial_registry、test_p3_autonomous_workload_trial、test_reflux_originless_compatibility、test_reflux_campaign_issuer (すべて `orchestrator/tests/`)。

## 3. 変異の事前登録 (DW-M01、実装前)

runner: `python3 tools/run_tests.py --force-dispatch <12 file> -q -rf`。source は D1009 の独立 clone (`make-mutation-source.sh`、T-2766 と同形) を `tools/mutation_worktree.py --source-repo` へ渡す。clone の submodule 初期化が `nonlocal-url` で拒否された場合は、主 repo の登録 worktree (`git worktree add -b mut-t2384 ... <commit>` + `dev_wave_submodule_init.py`) に `mutation_harness.py --repo` を直接当てる経路へ切り替え、その差を README に erratum として書く (DW-O12)。probe 走 (全件 SURVIVED 登録で観測 node を集める) → final 走 (期待 node 完全集合) の 2 段。old は実装後の実物で再検証する (DW-M07)。

| id | category | 置換 (old → new、consumer 内) | 期待 | 殺す test の予測 (完全集合は probe で確定) |
|---|---|---|---|---|
| M1 逐語 B-057-M5 | positive | `_require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)` → `_require(FormalReasonCode.FC07, _wal_field(terminal, "stage") == STAGE_ABORT)` | **SURVIVED (等価)** | — (gate が root `stage` を必須にするため `_wal_field` は常に root を返す。注入実在は mutated diff で確認) |
| M2 gate 無効化 + M5 | both-layers | 2 置換: `_require(FormalReasonCode.FC07, _wal_terminal_outer_shape(wal_records))` → `_require(FormalReasonCode.FC07, True)` と M1 の置換 | KILLED | #5 payload-only-stage + M6 の集合 |
| M3 superset 許容 | negative | `if set(terminal) != {"variant", "stage", "env_tag", "ts", "payload"}:` → `if not {"variant", "stage", "env_tag", "ts", "payload"} <= set(terminal):` | KILLED | #1 root shadow、#2 extra key |
| M4 ts bool 許容 | negative | block `    ts = terminal["ts"]\n    if type(ts) not in (int, float) or (` → `    ts = terminal["ts"]\n    if type(ts) not in (int, float, bool) or (` | KILLED | #4 ts-bool |
| M5 件数検査除去 | negative | `    ) == 1` (helper 末尾の return 式の終端; 実装後の実物で一意性を確認し、非一意なら return 全体を anchor にする) → `    ) >= 1` | KILLED | #6 abort-abort、commit-abort |
| M6 gate 無効化 | negative | `_require(FormalReasonCode.FC07, _wal_terminal_outer_shape(wal_records))` → `_require(FormalReasonCode.FC07, True)` | KILLED | #1、#2、#3 ×3、#4 ×4、#6 ×2 (= 11 node)。#5 は旧 stage 判定が拒否するので数えない |
| M7 過剰拒否 (ts を int 限定) | positive | block `    ts = terminal["ts"]\n    if type(ts) not in (int, float) or (` → `    ts = terminal["ts"]\n    if type(ts) is not int or (` | KILLED | #7 float ts 正例 |
| M8 str 型検査除去 | negative | `    if type(terminal["variant"]) is not str or type(terminal["env_tag"]) is not str:` → `    if False:` | KILLED | #4 variant-int、env_tag-null |

登録しない (到達不能・等価、insight に記録): payload dict 述語の無効化 (root attempt 無しは resolver、有りは exact keys が先に拒否)、ts 有限性述語の無効化 (canonical JSON に非有限値は乗らない)。

## 4. DW-G05 (成果物影響)

放置時: fixture 由来の flat / root-shadow / 重複 terminal を持つ projection が FC07 を通り、後続判定と receipt 発行 (`P6Unavailable` の receipt / evidence-root 参照) へ進む。実装後: FC07 で拒否され reason が FC07 になる。certified 選択集合は不変 (D1730 限界節)。

## 5. 実装単位と権限

- Codex author 1 本 (D95)、unit worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2384-unit-impl` (base = local main `b7f970dfa507558f7fb669a5ab38958d6c76b57c`)、所有 path = 上記 2 file。fixture builder・producer・docs は所有外。
- 実装子は commit しない。親が patch を取り出し wave worktree へ適用、焦点走 12 file (計算ノード) → 実装 commit (Codex author trailer)。
- 段 6: 敵対レビュー 2 本 (1 本は過剰・削除レンズ)、fix は同 unit worktree で branch を切る。変異は実装 commit 後、独立 clone で probe → final。
