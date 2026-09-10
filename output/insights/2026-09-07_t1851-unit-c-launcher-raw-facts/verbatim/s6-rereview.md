| 所見 | 修正の現物 | 検査 node と単一理由性 | 判定 |
|---|---|---|---|
| A-1 | [実測] `_ReservationPolicy.capture_keyword_arguments` は `s8b_floor_attempt_launcher.py:175-178`、copy 作成は `:475-493`、capture 利用は `:589-603,759-763`。 | [実測] `test_capture_uses_checked_kwargs_snapshot_after_source_mapping_mutates` (`test_s8b_floor_attempt_launcher.py:837-861`) は top-level の `reps` / `use_perf` 再代入を検出する。ただし nested mutable value の別名は検査しない。 | **partial / blocker** |
| A-2 | [実測] 矛盾拒否は `s8b_floor_attempt_launcher.py:823-827` で、`output.seal` `:828`、observation `:829`、terminal 記録 `:832` より前。 | [実測] `test_open_failure_cannot_be_reported_as_observed` (`:1113-1128`) は terminal / observation が呼ばれないことを検査する。ただし pre-seal 自体は観測せず、observed 用の他 field も valid でない。 | **partial / nit** |
| A-3 | [実測] 対象 helper は launcher `:257-275,414-452,496-586`。 | [実測] 正例対照は tests `:930-966,980-1042,1082-1092` に追加済み。ただし protocol / receipt の callable 負例は、その gate を外しても後続 canonicalization / receipt validation に拒否される。 | **partial / must-fix** |
| A-4 = B-5 | [実測] digest gate は launcher `:537-547`、reps gate は `:548-580`。 | [実測] `test_reservation_rejects_protocol_not_bound_to_binding` (`:930-939`) は `reps=3` を保って `session_cv_max` だけを追加するため、digest 不一致だけを踏む。 | **closed** |
| B-1 | [実測] tests `:368-377`。 | [実測] `extime=3`、`reps=3`、`use_perf=True` を exact に検査し、私有 sink が list で caller kwargs に無いことも検査する。 | **closed** |
| B-2 | [実測] fake sink は tests `:180-211,269-283`、snapshot 検査は `:807-834`。実体は `calibrator/runner.py:938-1005,1046-1049`。 | [実測] 6 key 集合と public list との非別名、private sink 由来を検査する。値の exact assertion が緩んだ点は新規所見 R-1。 | **closed** |
| B-3 | [実測] integration node は tests `:600-705`。 | [実測] registry には実 module `s8b_attempt_registry` を渡し、fake は capture / probe だけ。6 event の exact 列により reserve、classify、begin observation、terminal を実 adapter で通す。 | **closed** |
| B-4 | [実測] public forwarding は launcher `:843-864`、node は tests `:889-927`。 | [実測] monkeypatch 対象は launcher module の `_PRODUCTION_DEPENDENCIES` と `_owned_post_probe` だけ。public API と正式 capability を実際に呼ぶ。 | **closed** |
| M4 再照準 | [実測] 対象行は launcher `:860`。 | [実測] 別 `ClassificationAuthority` へ差し替えると recorder の `authority_id` / digest が `_CLASSIFICATION_AUTHORITY` と異なり、tests `:920-927` が失敗する。 | **closed** |

## blocker

### A-1 — 浅い copy では nested mutable value が固定されない

[実測] `_checked_measurement_keyword_arguments` の `dict(request.keyword_arguments)` (`s8b_floor_attempt_launcher.py:482`) は浅い copy である。`reps` と `use_perf` は immutable scalar なので今回の node では固定されるが、許可済みの `workload` / `extra_env` は mapping、`numactl` は sequence であり、元 object と同じ値 object を保持する。

[実測] grep 上、`measurement.keyword_arguments` の production 再読は `:482` の検査時だけで、`_capture` は `policy.capture_keyword_arguments` だけを使う (`:761`)。top-level TOCTOU は閉じている。

[推測] pre-probe 中に `workload`、`numactl`、`extra_env` の内容が変更されると、検査後に実行 argv / environment が変わり、throughput、raw output、repetition evidence、将来の certified 選択が変わり得る。

[推測] 所有 file `orchestrator/campaign/s8b_floor_attempt_launcher.py` で、少なくとも `workload` / `extra_env` を独立 dict、`numactl` を tuple として固定する。sealed capability 類の identity は copy しない。所有 test に nested container を pre-probe 中に変更する node を追加する。

## must-fix

### A-3 — callable 負例は正例対照を得たが、対象 gate 単独ではない

[実測] 4 helper の有効入力対照は追加され、`_external_evidence_sha256` は v2 payload の exact digest と probe / capture-failure 差を固定している (`test_s8b_floor_attempt_launcher.py:998-1028`)。

[実測] 一方、protocol 負例 `{"reps": 3, "x": lambda: None}` と receipt 負例 `{"x": lambda: None}` (`:957-958`) は `_contains_callable` を除去しても、それぞれ canonical JSON 化と receipt exact-shape validation に拒否される。message mismatch で test は赤になるが、callable gate 自体の単独証明ではない。

[推測] callable かつ downstream-valid な stateful mapping が受理される回帰を取り逃すと、policy bytes、receipt 由来値または計測引数の参照が検査間で変わり、台帳参照や測定値が変わり得る。

[推測] 所有 test file で、protocol は callable な `dict` subclassに valid 内容と一致 digest を持たせる。receipt も callable な `dict` subclass に valid receipt 全体を持たせ、measurement の `use_perf` を導出値へ合わせる。

### 所見 R-1 — B-2 更新時に repetition record の値 assertion が緩んだ

(a) [実測] fix2 前は `repetition_evidence` の各 record を throughput 値まで exact tuple で比較していた。現在は `rep_index` 列と key 集合だけを検査し、`returncode`、`counter_status`、`missing_perf_events`、`perf_raw`、`throughput` の値を検査しない。

(b) [実測] 現物は `test_s8b_floor_attempt_launcher.py:817-825`。fake が設定する値は `:201-207`。同じ値を検査する別 node は存在しない。

(c) [推測] snapshot が key を保ったまま throughput、returncode、counter facts を置換する回帰が緑になり、repetition evidence、除外理由、レポート値、certified 選択が変わり得る。

(d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_attempt_launcher.py` で、実体同形の 6 key を持つ 3 record 全体を exact tuple として比較する。

## nit

### 所見 R-2 — A-2 node は pre-seal 順序と fully-valid observed payloadを固定しない

(a) [実測] `replace(_terminal(opened), terminal_status="observed")` (`test_s8b_floor_attempt_launcher.py:1124`) は、`observation_sha256=None` と `primary_value=None` を残す。実 core の observed null matrixには適合しない。また node は terminal / observation の非実行だけを検査し、seal 前かを観測しない。

(b) [実測] production の順序自体は launcher `:823-832` で正しい。

(c) [実測] 現在の成果物値には影響しないため、DW-G05 に従い must-fix ではなく nit とする。

(d) [推測] 所有 test file で observed 用の non-null observation digest / primary value を明示し、保持した recorder の deferred reader が拒否後も未 seal であることを検査する。

## A-2 の逆向き

[実測] `terminal-failure` かつ `opened.failure is None` は launcher gateを通す。これは pre-probe competition や captured launch failureでは `failure=None` のまま classification reason が立つため、裁定 4 節 5 の classified-failure observation と整合する。

[実測] `failure=None` かつ classification reason も None の `terminal-failure` は launcherでは seal後まで進むが、実 core が `failure_reason=None` の terminal-failure null matrixを拒否する (`attempt_registry_core.py:1053-1064,2026-2036`)。terminal API は呼ばれるが terminal row は commit されない。

[実測] open failure + observed の対象組合せでは launcher `:823-827` で止まり、`record_attempt_terminal` `:832` は呼ばれない。

## B-2 / B-3 の実体同形性

[実測] fake record の key 集合は `{rep_index, returncode, counter_status, missing_perf_events, perf_raw, throughput}` (`test_s8b_floor_attempt_launcher.py:202-206`)。実 runner が sinkへ初期化・更新する集合 (`calibrator/runner.py:940-949,990-1002`) と一致する。

[実測] 実 runner は最後に sink から別 listを `ScalePoint.rep_observations` へ作る (`runner.py:1046-1049`)。fake も private `_rep_sink` と public `rep_observations` を分離し、public 側へ異なる内容を置いている (`test_s8b_floor_attempt_launcher.py:194-205`)。

[実測] real adapter nodeに adapter monkeypatch は無い。`registry=s8b_attempt_registry` (`:690`) により、launcher `:748-839` から実体 `reserve_attempt_slot`、`classify_attempt`、`begin_attempt_observation`、`record_attempt_terminal` が呼ばれ、event 列 `:702-705` が全段を固定する。

## B-4 / M4

[実測] M4 の新しい変異は public forwarding `classification_authority=_CLASSIFICATION_AUTHORITY` (`s8b_floor_attempt_launcher.py:860`) を caller-selected authorityへ差し替えるものとなる。

[実測] node は public `launch_floor_attempt` を呼び (`test_s8b_floor_attempt_launcher.py:904-909`)、recorder 実値を定数と比較する (`:920-927`)。指定変異ではこの比較が失敗するため KILLED となる。signature 検査だけへの依存ではない。

## 受理集合・所有外

[実測] `_CERTIFIED_MEASUREMENT_KEYWORDS` は launcher `:40-54` のままで、統合差分には集合要素の変更がない。

[実測] `_owned_post_probe` の関数名、argv `("pgrep", "-af", r"ycsb_.*\.exe")`、timeout `120.0`、単一 `subprocess.run` は launcher `:32-33,278-307` で不変。spawn-site pin は `test_ccbench_spawn_sites.py:212` の 1 件である。

[実測] `_checked_reservation_policy` の guard は AST unparse で次の逐語を維持している。

```text
reservation.mode == 'official' and reservation.perf_preflight_receipt is not None and expected_use_perf
type(capture_use_perf) is not bool or capture_use_perf is not expected_use_perf
```

[実測] 現物の `git diff 04f06d032` は統合 snapshot と同じ SHA-256 `7bba5874...1432e`。変更 file は launcher、launcher test、fix1 所有の `test_official_perf_closure.py` の3本だけで、adapter / core / profile / `s8b_floor_campaign.py` / calibrator は無変更。

## fix2 の新規持ち込み

[実測] 1巡目所見と無関係な production / test hunkは 0 件。test function の削除、skip 追加、新しい production fail-open、期待結果の反転もない。

[実測] 禁止された assertion 緩和は R-1 の1件。A-2 / M12 の terminal期待変更、B-3 integration拡張、B-4 public呼出し化、A-3正例追加は各修正指示に対応する。

[実測] marker の `_contains_callable` 行削除は指示どおり。callable を含む marker も `consumption_marker is not None` (`s8b_floor_attempt_launcher.py:509-516`) だけで callable 検査前に専用署名拒否される。node は object marker で同じ predicate を踏む (`test_s8b_floor_attempt_launcher.py:864-886`)。

## 変異 M1〜M12 観測 node

| ID | 観測 node | 静的判定 |
|---|---|---|
| M1 | `test_pre_probe_competition_terminalizes_without_capture` | [実測] capture callable 自体が `pytest.fail`。**KILLED**。 |
| M2 | `test_private_rep_sink_snapshot_occurs_after_token_open` | [実測] open前 sinkは空、open後は3件。前倒し変異は **KILLED**。R-1は値検査の別問題。 |
| M3 | `test_v2_profile_is_rejected_before_any_registry_side_effect` | [実測] profile / marker以外は validで、副作用件数0を検査。**KILLED**。 |
| M4 | `test_certified_api_owns_classification_authority` | [実測] node名は不変、対象を public forwarding差替えへ再照準。**KILLED**。 |
| M5 | `test_reservation_rejects_protocol_not_bound_to_binding` | [実測] `reps` は3のまま。旧 `reps=4` 入力から変更され、冗長 reps gateは解消。**KILLED**。 |
| M6 | `test_use_perf_must_be_derived_from_receipt` | [実測] unavailable receiptと `use_perf=True` の不一致だけ。**KILLED**。 |
| M7 | `test_pre_probe_competition_classifies_as_competing` | [実測] node名不変。5分岐へ拡張され、pre競合 caseは post非競合・failure空。**KILLED**。 |
| M8 | `test_external_evidence_digest_binds_both_probes` | [実測] node名不変。exact payloadと4 digestへ拡張。pre-probe削除変異は **KILLED**。 |
| M9 | `test_probe_result_requires_exact_keys` | [実測] valid対照後、extra keyが最初の負例。緩和変異は **KILLED**。 |
| M10 | `test_capture_exception_terminalizes_with_stage_capture` | [実測] capture伝播では結果・後続eventへ到達しない。**KILLED**。 |
| M11 | `test_reservation_rejects_reps_not_equal_to_protocol` | [実測] protocol / binding / receiptは validで、capture repsだけ2。**KILLED**。 |
| M12 | `test_open_failure_yields_empty_repetition_evidence` | [実測] snapshot前倒し変異自体は非空 sinkで **KILLED**。ただし classification reasonなしの terminal-failure は実 coreでは無効なので、単一理由の production-valid nodeとしては **partial**。 |

[実測] node の改名・分割はない。内容変更は M4 の再照準、M5 の入力修正、M7 / M8 の対照拡張、M12 の terminal status修正である。

## 総括

- [実測] 9所見は closed 6 / partial 3 / regressed 0。
- [実測] 残存 blocker 1件は A-1 の nested mutable alias。
- [実測] 新規所見は blocker 0 / must-fix 1 / nit 1。
- [実測] M1〜M11 の指定変異は静的に KILLED、M12 は変異を殺すが production-valid性が partial。
- [実測] pytestは制約どおり未実走。現物差分と guard / ownership / spawn pinのみ静的確認した。
- [推測] 判定は **NO-GO**。A-1、A-3、R-1を修正し、A-2 / M12 nodeを再固定してから再レビューが必要。