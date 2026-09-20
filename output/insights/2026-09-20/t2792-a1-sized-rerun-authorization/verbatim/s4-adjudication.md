# 段 4 裁定 — [T-2792] (2026-09-20 13:10 JST、親)

段 2 plan (`codex/s2-plan.md`、P1/P3/P4/P5 支持、P2/P6/P7 条件付き、Q1〜Q3) と段 3 consult (`codex/s3-consult.md`、must-fix 2 / should 3 / nit 3) を裁定する。裁定 inbox の再走査 (第 25 回控え 13:02、T-2724 A/X 12:50) に T-2792 への更新なし。

## 所見の裁定

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| A1 認可対象の attempt は限定されるが解除する先行証拠が限定されていない (must-fix) | real | 採用 | 定数に解除対象の先行 attempt `attempt-0001` を固定。gate は `authorized` かつ候補 `prior == base / "attempt-0001"` のときだけ末尾 2 箇所の拒否を skip。他の候補 (attempt-0003 等) は従来どおり拒否。負例「attempt-0001 と attempt-0003 の両方が bench 到達 + 一致 record → 拒否」を追加 (M10) |
| B1 配線 test の sentinel が intent 前で qsub 到達を検証しない (must-fix) | real | 採用 | 正例は job_contract の `_v3_submit_cli_fixture(study_id=sized, attempt_name="attempt-0002")` (3190 行、3294〜3321 行に sized の qsub 3 回到達 test が既存) を台に、attempt-0001 の先行証拠 + 一致 record で実 `run_submit` → 実 gate → 実 reader → 実 intent 作成 → `_run_qsub` 捕捉 (3 回) まで通す。負例 (record 不在 / 別 source / 一致 record + 既存 intent / 一致 record + 既存 attempt root) は qsub 未到達 + intent 非作成を確認。**変更面に `orchestrator/tests/test_paper_story_a1_job_contract.py` を加える (3 file)。** fixture が stub する層 (policy-ready、CCBench、git) は「scheduler 境界までの配線証明」と限定して報告 |
| A2 追補は §6.4 への例外追加を明記 (should) | real | 採用 | 追補 README に「D2172 項 2 に基づき将来の attempt-0002 一件に限って bench 後の同一配置反復を認可する。元の §6.4 本文は変更しない。attempt-0001 の判定・非認証 lane・限定 L-A1S-4 は遡及変更しない。本追補だけを根拠に L-A1S-4 を解除しない」を書く |
| A3 行番号と brief の表現の補正 (nit) | real | 採用 (記録) | `_revalidate_attempt_root` 呼出しは 8714、study differs の raise は 2805/2848/2898、`_v3_submit_cli_fixture` は job test 3190 で pilot 専用でない、probe log の `MATERIALIZATION_RELATIVE_PATH` は旧経路の定数 (sized の実効公開先は policy JSON 31 行) — insight に反映 |
| B2 保存条件の test は producer と consumer を分け、anomaly は既存 test を明示 (should) | real | 採用 | B1 の負例に「一致 record + 既存 intent」「一致 record + 既存 attempt root」を submit 側で置く。anomaly 即 reject は新 test を足さず、既存 (paired test 3888 collector gate / 3905 sidecar consumer、driver 6378〜6400・6632、materialize 8723〜8725 の observation consumer が destination gate より前) を「不変の根拠」として insight に列挙。認可による早期 return を導入しない |
| B3 変異の単位と kill 対象の明確化 (should) | real | 採用 | 下の事前登録に反映: (b)(c) は定数側と比較側を別変異、(i) は producer 内で再作成を実際に可能にする 2 hunk の意味的変異 (片側除去は登録しない) |
| B4 brief の実測を証明範囲に限定 (nit) | real | 採用 (記録) | 「intent が名指す実在 prior root は barrier が無くても候補になり 2735 で拒否」「別 study は受理 = gate 単体の実測」「live bytes pin 無し = 固定 hash に更新不能な形で束縛されていないの意味 (実行時は 4583〜4593 で記録し 7540〜7547 で照合)」「複製 gate 実走は qsub 到達 test の代替にならない」を insight に書く |
| B5 並行 wave の衝突は挿入位置だけでは判定できない (nit) | real | 採用 (実測済み) | 親の `scan_overlap.py`: driver / 2 test file を触る未 land branch は T-2724 chain の merge 1 件のみで tip は main と同 bytes。worktree の dirty 差分は無し (旧 commit の木の差分のみ) |
| consult の test 統合案 | real | 採用 | 不正 record 3 関数 (extra keys / corrupt JSON / bad shape) を 1 parametrized 関数に統合、`rejects_existing_exact_leaf` / `preserves_legacy_call` は既存 2485 行の公開先 test へ集約、producer の namespace 負例 (intent / attempt root / record 既存) は parametrize、`requires_parent` は独立関数にしない。bench-go / ready-triple の正例と A1 の負例は残す |
| 全層到達性 (consult は trial registry 内部を未確認) | — | 親が実測 | `trial_registry._validate_a1_projection_fields` (4135〜4165 行) と `issue_a1_registered_noncertifying_projection` (4167〜4197 行) は field 検査だけで履歴・study 単位の制約を持たない (親が読了)。`ident.py` の内部は未読だが output root は attempt 別 (consult が 2539〜2555・7098〜7103 で確認)。**残る拒否層は発見せず**。断定はせず insight に「読んだ層 / 読んでいない層」を書く |

## plan v2 (段 2 plan を次の点で改訂。他は plan のとおり)

- **定数:** `V3_SIZED_RERUN_AUTHORIZATIONS = frozenset({(V3_SIZED_STUDY_ID, "attempt-0002", "attempt-0001", "D2172", 2, "2026-09-20")})`。構造 `(study_id, attempt_name, prior_attempt_name, decision_id, decision_item, decided_on)`。record の key 集合は plan §1 のとおり 6 key (prior は record に持たせず定数で固定)。
- **reader `_exact_v3_rerun_authorization(base, *, study_id, current_attempt, source_commit) -> tuple | None`:** record 不在 → `None`。存在する record は unsafe / corrupt / differs を分けて raise。完全一致のとき定数 tuple を返す (呼び手は `prior_attempt_name` を使う)。self digest は新 helper `_rerun_authorization_digest` (`authorization_sha256` を除いて `_canonical_json_bytes` → `_sha256_bytes`)。
- **gate:** `_assert_no_prior_v3_bench_start(base, *, study_id, current_attempt, source_commit)`。走査前に reader を呼ぶ。候補 loop の末尾 2 箇所の拒否は `released = authorization is not None and prior == base / authorization[2]` のときだけ skip。2683〜2900 行の完全性検査と 2805 / 2848 / 2898 行の study differs は無条件で実行。
- **公開先:** plan §4 のとおり (`attempt` / `base` / `source_commit` の keyword 3 つ、全 None = 従来、一部指定 = 拒否、全指定 = `base == _durable_measurement_base(policy)` + `_validate_attempt_root(attempt, base)` + reader。record 一致時だけ `relative.with_name(f"{relative.name}-{attempt.name}")`、不一致 record は拒否、不在は従来 leaf)。create-only・親 dir 実在は不変。`_run_materialize_v3` 8732 行の呼出しに 3 引数を足す。
- **producer:** plan §5 のとおり `authorize-rerun` (全項目必須、定数 membership、intent / attempt root / record の不在、base は既存 dir を要求、`_exclusive_write` + `_fsync_directory`)。
- **test (3 file):** paired test = reader / gate / 公開先 / producer (統合後 目安 14〜16 関数、parametrize 可)。job_contract test = B1 の配線 (正例 1 + 負例 4、既存 sized qsub 到達 test の隣)。既存 gate test 3 本に `source_commit=` と docstring 2 文。
- **親 docs:** 追補 README (P7 v2 = A2 の文言)、insight README。
- **docstring:** 各新 test に「受理: … / 拒否: …」の 2 文 (DW-C01)。

## provisional 裁定の確定

| | v1 | v2 |
|---|---|---|
| P1 | 定数 1 件 (study, attempt-0002, D2172, 2, 2026-09-20) | **条件付き採用**: 定数に prior `attempt-0001` を加える (A1) |
| P2 | record 6 key + self digest | **採用**: digest helper は別設 (`_rerun_authorization_digest`) |
| P3 | 兄弟公開先 `…-sized-attempt-0002` | **採用** |
| P4 | producer subcommand | **採用** |
| P5 | 末尾 2 箇所だけ解除、完全性検査は無条件 | **条件付き採用**: 解除は候補 = 定数の prior に限定 (A1)。不一致 record は拒否 |
| P6 | materialize も record 一致時だけ兄弟 | **採用 (Q1)**: 不在 = 従来 leaf、不一致 = 拒否、base 直下検査を維持 |
| P7 | 追補は別 insight、source commit 束縛 | **条件付き採用 (Q2 / A2)**: 「将来の attempt-0002 一件」「§6.4 本文不変」「遡及なし」「L-A1S-4 は解除しない」「追補専用の実行時検査は無い」を明記 |

Q3: producer の変異は 2 hunk の意味的変異 (下 M13)。片側除去は登録しない。

## 変異の事前登録 (DW-M01、実装後に anchor と 1 理由性を再確認してから本走)

対象 file = driver。category は `negative` (KILLED 期待)、M0 だけ `positive` (SURVIVED 期待)。

| id | 変異 (位置) | 1 理由で kill する test (case) |
|---|---|---|
| M0 | 等価: reader 内の `set(record) != KEYS` の比較を意味を変えない書き方に置換 (SURVIVED 期待) | — |
| M1 | reader: record 不在で `None` の代わりに定数 tuple を返す (record 不在でも解除) | rejects_absent_record |
| M2 | 定数側 attempt: 定数 membership の照合から `current_attempt.name` を外す | rejects_other_attempt (current / record とも attempt-0003、file 名も attempt-0003) |
| M3 | 比較側 attempt: `record["attempt_root"] == os.fspath(current_attempt)` を除去 | rejects_other_attempt (file 名 attempt-0002 / field は attempt-0003) |
| M4 | 定数側 study: 定数 membership の照合から `record["study_id"]` を外す | rejects_other_study (caller / record とも pilot、pilot の先行証拠) |
| M5 | 比較側 study: `record["study_id"] == study_id` を除去 | rejects_other_study (caller = pilot、record = sized、pilot の先行証拠) |
| M6 | `record["source_commit"] == source_commit` を除去 | rejects_other_source |
| M7 | 定数 membership の照合から `decision["id"]` を外す | rejects_other_decision (id 単独変更) |
| M8 | self digest の照合を除去 | rejects_bad_digest |
| M9 | gate: `released` のとき候補 loop を検査前に `continue` (完全性検査 skip) | preserves_prior_integrity (一致 record + attempt-0001 の ready `recorded_epoch=0` → `prior ready evidence is corrupt`) |
| M10 | gate: `released` の条件から `prior == base / prior_name` を外す (全候補を解除) | rejects_other_prior_reached_bench (attempt-0001 + attempt-0003 が bench 到達 + 一致 record → 拒否) |
| M11 | 公開先: `os.path.lexists(destination)` の拒否を除去 | rejects_existing_sibling (一致 record + 兄弟 dir 既存) |
| M12 | 公開先: record 不一致 / 不在でも `attempt` 指定時は兄弟 path を expected にする | rejects_sibling_without_record |
| M13 | producer (2 hunk): record の `lexists` 事前検査を除去 + `_exclusive_write` を上書き書込に置換 | authorize_rerun_is_create_only (2 回目で拒否 + bytes 保持) |
| M14 | submit 配線: `_run_submit_v3` の gate 呼出しから `source_commit=expected_head` を外し固定値を渡す | job_contract 配線負例 (別 source の record で qsub 未到達) |

両層 stub: gate / 公開先 / reader は実関数、record は実 tmp file、配線 test は `_run_qsub` だけ捕捉。既存 test でも落ちる変異は新規検出力に数えない (登録時に確認)。
