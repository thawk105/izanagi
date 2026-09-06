# [T-1851] 実装単位 C1a — 起動層の raw facts 面: 副作用前の検査、v2 早期 gate、launcher 所有の分類 authority、二段 probe と私有 sink

2026-09-07。branch `worktree-dev-wave-t1851-unit-a`。**land していない (D1341)。**

- 継承 tip: `9f64a3d44` (B2 / D1 の記録 + 段 8)
- 本 wave の commit: `04f06d032` (local main `97ee3cd3a` の取り込み、integrator)、`35ba02e1a` (実装)、
  `6194d4840` (記録)、`6f2a89818` / `1780d360a` / `061ecb1b1` (受入 2 走の post-claim merge、local main
  `425060bab` → `9f093b612`)、受入結果の追記 commit
- 実装面の差分: 3 file、+827 / −78 (production 1 file +245 / −37、test 2 file +582 / −41)。codex 子: plan 1、レンズ 2、author 1、review 2、fix 3、再 review 2 = 11 本 (review 1 回目の 2 本は親の argv ミスで未起動、receipt なし)
- 逐語: `verbatim/s2-plan.md`、`verbatim/s3-lens-a.md`、`verbatim/s3-lens-b.md`、`verbatim/s5-launcher.md`、`verbatim/s6-review-a.md`、`verbatim/s6-review-b.md`、
  `verbatim/s6-fix1.md`、`verbatim/s6-fix2.md`、`verbatim/s6-rereview.md`、`verbatim/s6-fix3.md`、`verbatim/s6-rereview-2.md`。
  brief は `s1-brief.md`、裁定は `s4-adjudication.md`、親の実測は `parent-measurements.md`、変異は `mutation-spec-probe.json` /
  `mutation-probe-out.json` / `mutation-spec-final.json` / `mutation-final-out.json`

## 中身

台帳配線 3 task 閉包の 6 段分割 `B1 → A → B2 → D1 → C → D2` のうち、単位 C を **C1a (起動層 launcher の raw facts 面) / C1b (証拠 module、封印 API、E1 / E2、
core・profile・adapter) / C2 (campaign 配線、producer v5)** に割り、C1a を unlanded checkpoint として積んだ。terminal 証拠の契約 v2 (24 field + cross-field
不変条件 + 再導出 6 枝 + E2 の 4 語 + crash 後の権威) は段 4 裁定 (`s4-adjudication.md` 3 節) で固定し、実体化は C1b が持つ。

| file | 内容 |
|---|---|
| `s8b_floor_attempt_launcher.py` (+245 / −37) | `FloorAttemptReservation` に `protocol` / `mode` / `perf_preflight_receipt` / `consumption_marker`、`slot_id` 4 軸 \| 5 軸。副作用前の検査 `_checked_reservation_policy` (mode literal、`canonical_protocol_sha256(protocol) == binding.protocol_sha256`、`expected_use_perf = use_perf_from_receipt(receipt)`、official + receipt 非 null + True 拒否、capture kwargs の `use_perf` / `reps` 等値、callable 不在) と検査済み kwargs の 1 段 snapshot (`_snapshot_keyword_argument`)。v2 早期 gate `[s8b-launcher-v2-terminal]`。launcher 所有の分類 authority (`s8b-floor-attempt-launcher/pre-output-classification/v1`)、public API から `classification_authority` 引数を削除。流れ reserve → probe_before → (skip \| 私有 sink → capture → probe_after) → classify → open → snapshot → build → seal → observe → terminal。`failure{stage}`、`failure` ありの `observed` 申告を seal 前に拒否。`_external_evidence_sha256` は両 probe + launch_failures + capture failure、schema `s8b-floor-pre-output-evidence/v2`。`_post_probe` exact 4 key |
| `test_s8b_floor_attempt_launcher.py` (+567 / −41) | 31 node。fake token は sink 実体 (`calibrator/runner.py` の `open_measurement_point`) と同じ 6-key rep record を open 時に私有 sink へ書き、public `rep_observations` は別 list。実 adapter (`s8b_attempt_registry`) で reserve → classify → begin observation → terminal まで通す integration 正例。public API 経由で authority 定数を recorder が観測する node (M4)。D1522 の正例対照 (4 helper の直接 test、`_pre_observation_failure_reason` 5 枝、v2 payload の exact digest)。callable な dict subclass の負例。kwargs の nested container を pre-probe 中に変異させる TOCTOU 対照 |
| `test_official_perf_closure.py` (+15) | perf 参照 file 在庫へ launcher を登録 (file、predicate "A" = `_checked_reservation_policy` → `use_perf_from_receipt`、guard 2 本の ast.unparse 逐語)。検査の regex・意味・既存 entry は不変 |

## 1. 段 1 の brief の (P) 6 件と、plan・レンズの訂正

親の provisional 裁定 (P1)〜(P6) のうち (P2)(P3)(P4)(P6) を採用、**(P5) 「C1 を 1 wave 2 本で積む」は plan とレンズ 2 本が規模 (C1 = 1,600〜2,300 LOC) と到達可能性の
両面で棄却**し、C1 を C1a (launcher 単独、1 本) / C1b (証拠封印 + E1 / E2 + adapter) に割った。plan は親案 14 field に 5 field (protocol / perf_preflight_receipt /
open_failure / campaign_record / finished_at) を足し、段 4 裁定がさらに attempt_binding / mode / expected_use_perf / probe の前後 exact 組 / nonfinite_count /
rep_integrity_failures / session_cv_max / self_report を足して **24 field** に固定した。brief の anchor 行番号と test 件数 (関数数と parametrize 展開後の node 数の混同) は
両レンズが実測で訂正した (`s4-adjudication.md` 7 節)。

## 2. レンズ 2 本が独立に見つけた blocker と、段 4 裁定

レンズ A (blocker 7 / must-fix 4) とレンズ B (blocker 6 / must-fix 9) の収束点: 証拠の attempt 束縛の欠落、mode / receipt / authority の呼び手選択、seal の偽造可能性、
core 等値解除の受理拡大、policy の非網羅性、campaign_record の crash 順序、marker と pre-probe の順序、C1a の v2 半開き。段 4 裁定は契約 v2 を文書で固定し
(D 候補 `terminal-evidence-contract-v2-exact-fields`)、本 wave の実装を C1a に絞り (D 候補 `launcher-raw-facts-face-precedes-sealed-evidence`)、C1b / C2 / D2 の
境界を固定し、裁定パッケージ 5 件 (8 節) を返した。

## 3. codex の子は 1 本も pytest を走らせられず、赤は親の実走で 1 度だけ出た

実装子・fix 子 4 本とも Pegasus preflight (`qstat -Q`) 失敗で runner `rc=16`、自走 harness (direct call) だけ緑。親が統合 tree で DW-O26 の 2-hop consumer 集合
38 file を 4 回走らせた: baseline 4,717 → 段 5 統合後 **1 failed** / 4,733 → fix1 統合後は dispatch の queue-wait-timeout (infra、child 未起動) → fix2 統合後 4,736 →
fix3 統合後 4,736 passed / 16 skipped / rc=0。唯一の赤は `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact` の
`unreviewed: s8b_floor_attempt_launcher.py` で、launcher が `use_perf_from_receipt` を呼ぶようになったことによる在庫検査の設計どおりの発火 (fix1 が登録)。

## 4. 段 6 レビュー 2 本は NO-GO、fix 3 巡と再レビュー 2 回で GO

レビュー A (blocker 2 / must-fix 2) とレビュー B (must-fix 5) の所見 9 件はすべて real: A-1 検査済み kwargs の再読 (TOCTOU)、A-2 open 例外を `observed` として通せる、
A-3 D1522 の正例対照、A-4 = B-5 M5 の単一理由性、B-1 kwargs 期待値の弱体化、B-2 fake sink の別名、B-3 real adapter node が reserve 以降を通らない、B-4 authority node
が public API 未観測、M4 の再照準。fix2 が 9 件を閉じたが、再レビュー 1 回目は **NO-GO** (A-1 の浅い copy が nested container の別名を残す、A-3 の callable 負例が
後続 gate にも遮られる、fix2 で rep record の値 assertion が緩んだ = R-1、A-2 node の observed payload が実 core の null matrix に適合しない = R-2)。
親は A-1 / A-3 / R-1 を real (must-fix)、R-2 を nit、「M12 の terminal-failure が失敗理由なしで production-valid でない」は C1b 持ち越し (open 失敗の失敗理由は契約 v2
の `failure{stage}` が定める) と裁定した。fix3 (production +13 / −1、test +59 / −12) が 4 件を閉じ、再レビュー 2 回目は **closed 4 / partial 0 / regressed 0、新規所見 0、GO**。
再レビューは統合差分の sha256 が親の snapshot と一致すること、fix1 の guard 2 本の逐語と spawn-site pin の不変も静的に確認した。

## 5. 変異 matrix — 12 変異、本走 rc=0、**12/12 KILLED**、期待 node 集合と完全一致

checkout `35ba02e1a`、`tools/mutation_harness.py` (dispatch、`--detached`)、runner = `test_s8b_floor_attempt_launcher.py` +
`test_ccbench_spawn_sites.py` `-q -rf`。probe (全件 SURVIVED 登録) で観測 node の完全集合を集め、本走は KILLED 期待 = その集合
(DW-M08) で走らせた。baseline は両走とも PASSED (53.5 s)。

| ID | 変異 (launcher の 1 箇所) | 結果 | 観測 node (完全集合) |
|---|---|---|---|
| M1 | pre-probe 競合分岐で capture を呼ぶ | **KILLED** | `test_pre_probe_competition_terminalizes_without_capture` |
| M2 | sink snapshot を `open()` 前へ移す | **KILLED** | `test_private_rep_sink_snapshot_occurs_after_token_open` |
| M3 | v2 早期 gate を外す | **KILLED** | `test_v2_profile_is_rejected_before_any_registry_side_effect` |
| M4 | public API の forwarding を caller-selected authority へ差し替える | **KILLED** | `test_certified_api_owns_classification_authority` |
| M5 | protocol digest 等値検査を外す | **KILLED** | `test_reservation_rejects_protocol_not_bound_to_binding` |
| M6 | `expected_use_perf` を receipt でなく capture kwargs から取る | **KILLED** | `test_use_perf_must_be_derived_from_receipt` |
| M7 | `_pre_observation_failure_reason` が `probe_before.competing` を無視 | **KILLED** | `test_pre_probe_competition_classifies_as_competing`、`test_pre_probe_competition_terminalizes_without_capture` |
| M8 | `_external_evidence_sha256` の payload から `probe_before` を落とす | **KILLED** | `test_external_evidence_digest_binds_both_probes` |
| M9 | `_post_probe` の exact key 検査を緩める | **KILLED** | `test_probe_result_requires_exact_keys` |
| M10 | capture 例外を `failure` にせず伝播させる | **KILLED** | `test_capture_exception_terminalizes_with_stage_capture` |
| M11 | `reps` 等値検査を外す | **KILLED** | `test_reservation_rejects_reps_not_equal_to_protocol` |
| M12 | open 失敗時に sink snapshot を取る (空であるべき) | **KILLED** | `test_open_failure_yields_empty_repetition_evidence` |

- **M4 は fix2 の後に再照準した。** 段 4 の登録は分類 policy 定数の digest を変える形で、signature 検査と定数検査だけでは
  「public API が caller の authority を使う」退行を殺せなかった (段 6 レビュー B-4)。fix2 が public API を実際に呼ぶ node を
  足し、M4 を forwarding 行の差し替えへ変えた。`mutation-spec-probe.json` が再照準前、`mutation-spec-probe-2.json` が再照準後。
- **M7 だけが 2 node を殺す。** pre-probe 競合の分類を無視すると、分類語の node と「capture を呼ばない」node の両方が赤になる。
  期待集合は完全集合でなければならない (DW-M08) ので 2 node で登録した。
- 過剰拒否の正例 (DW-M01): M3 の node は v1 profile + marker None の正例を同じ test 内に持ち、M9 の node は valid な 4 key の
  正例対照を先に置く。M5 / M11 は他の入力を valid に保ち 1 値だけを変える形へ fix2 が直した (段 6 A-4 = B-5)。

## 6. 検査の実測

`parent-measurements.md` が一次資料。要点: 焦点走 38 file は fix3 統合後 4,736 passed / rc=0。
全史 provenance は実装 commit 後 8,272 件・新規違反なし。変異は 12/12 KILLED。
受入全走は 2 走した。**attempt 1 は子が緑 (21,039 passed / 68 skipped) だったが receipt が出なかった** —
shard 3 本の queue 待ちが 3,291 / 3,403 / 3,409 秒あり、走行が lease の TTL 2,400 秒を超えて
`receipt-lease-check` (`state=held`) で止まったためである。テストの赤ではない。D612 / D619 が予見していた
opt-in 上書きの latent risk の初回顕在化として台帳へ書いた。**attempt 2 は rc=0、`verdict: child-green`、
21,043 passed / 68 skipped**、receipt は `tested_main=9f093b612` / `tested_tip=061ecb1b1`、
red / flake 空、fingerprint 一致。lease は別 session が保持していたため未取得のまま publish された
(DW-O27 の疑似 holder 経路)。

## 7. 閉じていない窓

- **v2 台帳の terminal は依然として閉じている。** C1a は v1 terminal API のまま置き、v2 profile または consumption marker 非 None は早期 gate が副作用ゼロで拒否する。
  `launch_floor_attempt()` の production 呼び手は 0 件のまま (campaign `_Runner._run_session` は台帳を参照しない)。「効いている」と書いてはならない。
- **open 失敗の terminal は実 core では受理されない。** `failure{stage:"open"}` の attempt は launcher が `terminal-failure` で terminal を呼ぶが、v1 core は失敗理由なしの
  `terminal-failure` を null matrix で拒否する。失敗理由は契約 v2 (C1b) が `failure` field で定める。M12 node は fake registry で snapshot 空を固定するだけ。
- **証拠の封印は未実装。** `_external_evidence_sha256` は pre-output 証拠 (v2 schema) の digest で、terminal 証拠文書 (`s8b-floor-terminal-evidence/v1`) と
  `terminal_evidence_sha256` は C1b。
- **kwargs snapshot は 1 段。** Mapping は dict、sequence は tuple に固定するが、その中の可変 object (無いはず) は identity のまま。sealed capability は identity を保つ設計。
- 前 wave からの持ち越し: 他世代の予算超過は inspector が検査しない、D1533 の同一 bytes 再作成、journal の TOCTOU 窓、合成 2 段 v1 残骸、B1 の 5 件。

## 8. ユーザーへ返す裁定パッケージ

1. **pre-probe 除外 attempt でも admission ticket を消費する** (親裁定)。代案 = pre-probe 除外専用の非 consumption 予約権限を admission に新設。
2. **非有限 throughput は runner を触らず証拠側で null + `nonfinite_count` に正規化する** (親裁定)。代案 = `benchparse._num` を `math.isfinite` で閉じる。
3. **evidence file あり・terminal row なしは許容し非保証として明記する** (親裁定)。代案 = slot 宛 pending index で replay を止める。
4. **perf receipt の manifest 束縛は C2 (供給) + D2 (再検証)。** C1 は形と機械導出だけ。
5. 持ち越し: D1533 の非保証を result.md へ載せる所有 (C2 / D2)、D2 の動的 `RESULT_SCHEMA` fixture、B2 / D1 の裁定パッケージ 1・2・5、A2α / A1' / B1 の未裁定。

## 9. 次 wave の出発点

- **次段は C1b。** 最初に contract leaf `orchestrator/campaign/s8b_terminal_evidence.py` (3 節の exact dataclass、`seal_terminal_evidence(reservation, opened, terminal)` =
  launcher 私有 issuer、`require_sealed_terminal_evidence(value)`、projection の pure 関数) を固定し、その後 unit1 (launcher 側の発行 + launcher test) / unit2 (core の
  capability 経路、profile の E2 と validator、adapter の `record_sealed_attempt_terminal(observation, evidence)`、artifact 検査、load 面 7 箇所、その test) を並列にする。
  契約は `s4-adjudication.md` 3 節が正本で、C1b の brief はそれを再掲せず参照する。
- C1a が C1b に渡す raw facts: `OpenedFloorAttempt` の `failure` / `probe_before` / `probe_after` / `repetition_evidence` / `expected_use_perf` / `reps_expected`、
  `FloorAttemptReservation` の `protocol` / `mode` / `perf_preflight_receipt` / `consumption_marker`、`_ReservationPolicy` の検査済み kwargs snapshot。
- branch `worktree-dev-wave-t1851-unit-a` を継承し、main を取り込んでから着手する。継承元の状態は本 README が正本で、job dir handoff ではない。
- 6 段すべてを積んだ後に D1341 に従って 1 変更単位で land する。
