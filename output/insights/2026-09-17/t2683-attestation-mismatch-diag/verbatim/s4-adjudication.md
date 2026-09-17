# 段 4 裁定 — [T-2683] (2026-09-17、親)

裁定の正本 = main の **D2104 項 14** (局所修正・新 gate なし・受理集合不変) と **項 15** (成功時の receipt は書かない)。
wave 開始後に main が b4631a92e へ進み (docs のみ)、wave branch は ff-only で揃えた。

## 所見の裁定 (real / refuted、採否、scope)

| 所見 | 裁定 | 採否 / 扱い |
|---|---|---|
| A1 型変更で受理集合が動く | refuted | plan の配置 (typed raise は try/except の外、`except BaseException` で 31) を維持 |
| A2 fsync stall で timeout 文言に化ける・親の同期読取りも stall しうる | real、**scope 外 (限界として記録)** | `create_json` を維持。理由: 同じ子が accepted payload を同じ `create_json` (fsync) で書いており、mismatch 経路の I/O 特性は accepted 経路と同じ。D474 の「fsync しない」は launcher の監視ループ (test harness timeout へ stall を持ち込まない) 向けで、ここは `attestation_cap_s` の timeout 内。親の `load_json_strict` も成功経路 L1259 と同じ形。「通常の例外では rc=31 不変」と「stall・外側 timeout (`t126_qualification.sh` rc=124) は保証外」を分けて decisions fragment に書く |
| A3 sidecar が authority 化・全行が過剰 | refuted | P2 維持。主張は「比較時の全行と判定値の保存」に限定し、凍結 profile・policy まで含む自己完結再計算 (D2056 決定 5 相当) は主張しない |
| A4 create-only 衝突・再試行上書き | refuted | 衝突時は別名を作らず rc=31 (plan どおり) |
| A5 P1 の根拠 (非 JSON 型 TypeError) | refuted | **P1 維持: `execution_guard.py` 無変更。** 記録の文言は「message の伝播は維持されており、floor test は `out_root` の pin (全 FS の副作用ゼロ証明ではない)」に限定 |
| A6 P4 空 comparisons の sidecar | refuted | P4 維持 (`comparisons: []`、`failed_fields: []`、probe 例外の「sidecar なし」と区別できる) |
| A7 E1 の等価の射程 | real、nit | E1 は「helper 挙動の等価対照」と限定 (driver bytes は変わるので live identity は同一でない) |
| A8 brief「live 比較なし」の一般化 | real、**must-fix (brief 訂正、コード影響なし)** | 訂正文: literal hash 検索では更新対象 pin を発見しなかった。live identity 照合 (`_identity_files` L354-376 の HEAD blob 比較、prologue hash L896-897、wrapper `t126_qualification.sh:798-799`) は存在し、新規実走は変更を含む commit・source stage を要する (通常運用)。過去 attempt の `verify()` は記録 commit の blob で照合するので今回の変更で無効化されない。歴史 manifest の再発行は不要 |
| B-1 読み手不在 | refuted | 採用: 所有 test file に collector `_manifest` の consumer 正例 (sidecar が closure に列挙される) を 1 本足す。wrapper・receipt schema は変えない |
| B-2 P1 の一般化 (永続保存) | 部分 real | P1 は「message 伝播は維持、構造化 sidecar の永続保存は未対応、今回の変更対象は T126」に限定。裁定パッケージ候補 2 として記録 (推奨: 開始前・副作用ゼロの拒否は stdout/stderr で足りる、行動なし) |
| B1 helper 緑が production 配線を証明しない | real、**must-fix** | 採用: (a) AST 配線 pin test (同 file の `test_m10_driver_binds_prologue_observation_at_every_member_callsite` と同型) — `run()` 内 `attest` の子分岐が `os._exit(_run_attestation_child(...))` を呼び、親の非ゼロ分岐が `AttestationError(_attestation_rejection_message(...))` を上げることを AST で固定。(b) 実 `os.fork()` で helper を子として走らせ `waitpid` の exit code 31・sidecar 実在・親 message helper の出力を検査する test。`run()` 全体の E2E は attempt bootstrap 全体を要し局所修正を超えるので作らない (記録する)。配線変異 M10・M11 を登録 |
| B-4 親 message の replay 影響 | refuted | plan の実 FSM/replay test を維持 |
| B-5 構造 pin | refuted | 焦点走に consumer 6 file を含める |
| B-6 M8 の帰属 | real | M8 の対象を message helper に exact 指定、M10 (production raise の固定文言化) を別登録 |
| B2 SIGKILL 後の staging 残留で failure receipt が阻害 | real、**scope 外 (限界として記録)** | accepted payload の `create_json` にも同じ SIGKILL 窓が既にあり、mismatch 経路の露出は accepted 経路と同数 (0→1) になるだけで新しい型ではない。collector の staging 拒否は緩めない。裁定パッケージ候補 1 (非 fsync writer / staging 回収の共通層) として記録、推奨 = 現状維持・実害観測時に再検討 (D2104「gate の新設は実害の観測に限り」) |

## plan v2 (plan-out.md からの差分)

- D1〜D7、T1〜T2 は plan どおり。
- 追加 T3: AST 配線 pin test `test_t2683_run_attest_closure_wires_child_helper_and_rejection_message`。
- 追加 T4: 実 fork test `test_t2683_forked_child_writes_sidecar_visible_to_parent` (governor 不一致、`os.fork` → 子は `os._exit(_run_attestation_child(...))`、親は `waitpid` で exit code 31、sidecar 実在、`_attestation_rejection_message` が相対 path と `effective_clock.governor` を返す)。
- 追加 T5: consumer 正例 `test_t2683_mismatch_sidecar_is_listed_in_collector_closure` — `orchestrator/qualification/collector._manifest(attempt_dir, exclude=set())` に sidecar が `attestation/pre-round-1.mismatch.json` として列挙される。
- 焦点走 file 集合: `test_t126_qualification_driver.py`、`test_t126_pegasus_tools.py`、`test_t126_qualification_artifacts.py`、`test_campaign.py`、`test_official_perf_closure.py`、`test_artifact_admission.py`。
- sidecar 相対 path = accepted path の `.json` → `.mismatch.json` (`Path(relative).with_suffix(".mismatch.json")`)。schema_version = `t126-qualification-attestation-mismatch/v1`。exact 9 keys は plan §1。
- `execution_guard.py` 無変更。`run_series`・`verify()`・`attestation_records`・`V2_ENV_NEUTRAL_MODULES` 非接触。

## 変異事前登録 (B-057、実装前に固定)

各変異は独立適用。「期待 killer」は主 killer (他 test も赤になりうる)。構文破壊・import 失敗は kill に数えない。

| ID | 位置 | 変異 | 期待 killer |
|---|---|---|---|
| M1 | `_run_attestation_child` mismatch 分岐 | sidecar の `create_json` 呼出しを削除し rc=31 だけ返す | `test_t2683_mismatch_preserves_all_comparison_rows` |
| M2 | 同 成功分岐 | 成功時にも mismatch sidecar を書く | `test_t2683_match_preserves_accepted_bytes_without_sidecar` |
| M3 | 同 diagnostic 構築 | `failed_fields` を常に `[]` | `test_t2683_mismatch_preserves_all_comparison_rows` |
| M4 | 同 | `comparisons` を非 pass 行だけに絞る | `test_t2683_mismatch_preserves_all_comparison_rows` |
| M5 | 同 | 空 comparisons では sidecar を書かず rc=31 | `test_t2683_empty_comparisons_writes_rejected_sidecar` |
| M6 | 同 `except BaseException` | 書込み例外時の return を RC_INFRASTRUCTURE (34) に変える | `test_t2683_sidecar_write_failure_preserves_rc` |
| M7 | 同 | probe 等の汎用失敗にも空 sidecar を書く | `test_t2683_probe_failure_has_no_sidecar` |
| M8 | `_attestation_rejection_message` | 常に固定文言 `attestation child rejected` を返す | `test_t2683_parent_message_names_sidecar_and_failed_fields` |
| M9 | 同 | reader の例外を再 raise | `test_t2683_parent_message_unreadable_sidecar_is_best_effort` |
| M10 | `run()` 内 `attest` 親分岐 | `raise AttestationError(_attestation_rejection_message(...))` → `raise AttestationError("attestation child rejected")` | `test_t2683_run_attest_closure_wires_child_helper_and_rejection_message` |
| M11 | `run()` 内 `attest` 子分岐 | helper 委譲を現行のインライン処理 (`_attest`→`create_json`→`os._exit(0)` / `except BaseException: os._exit(RC_ATTESTATION)`) に戻す | 同上 (AST pin) |
| E1 | `_run_attestation_child` の docstring/comment | comment のみ変更 | 等価対照 (helper 挙動)。全 test 生存を期待 |

単一理由性は実装後 (段 6、変異走行前) に各変異の赤理由が 1 つに絞れることを確認する (DW-M01)。

### 事前登録の追記 (2026-09-17 07:08 JST、author 稼働中・変異走行前、DW-M03/M08 の読了に伴う分類の明示)

変異の一覧・期待 killer は上表のまま変えない。報告枠だけを DW-M08 に従い 2 つに分ける:

- **受理集合 / fail-closed 境界 (KILLED を数える):** M2 (成功 attempt の成果物集合が変わる)、M6 (書込み失敗時の rc 31→34)、M9 (reader 例外の再 raise で親の例外型と rc が変わる)。
- **診断感度 pin (kill でなく「診断 pin 赤」として別枠記録):** M1、M3、M4、M5、M7、M8、M10、M11 — 受理集合は変えず sidecar / message の構造化シグナルだけを pin する。
- E1 は等価対照 (helper 挙動)。

## 裁定パッケージ候補 (worklog fragment の次の一手へ記録、実装しない)

1. 診断 writer の fsync と強制終了後の staging 回収 (共通層 `artifacts.py` / `collector.py`): 推奨 = 現状維持 (accepted 経路と同じ露出、実害未観測)。
2. execution_guard 開始前拒否の比較行の永続保存: 推奨 = 行動なし (副作用ゼロ契約と stdout/stderr 伝播で足りる)。
