# 段 4 裁定 — md_20 (dev-wave-md20-lock-order-loop)、2026-09-30 22:45 JST

入力: s1-brief.md、plan.md (条件付き GO)、consult-a.md (NO-GO)、consult-b.md (条件付き GO)。
親の実測: loop.py:884-895 (終端済み variant の評価 skip) 実在、pipeline.py:2772-2783 (fan-out は BACKOFF_REPRO 限定) 実在、tools/cc_model_checker/search.py:36 (`stop_reason ∈ {exhausted,max_states,max_seconds}`、完了 = exhausted) 実在。

## 所見の裁定

| 所見 | 裁定 | 処置 |
|---|---|---|
| A1 小モデルの完了が被覆に結び付かない | real (scope 内、最小形) | 登録簿 (repo 内、結果 file と独立) に場面ごとの期待を置き、結果と照合する (下の U-B)。結果 file が実際の checker 実行から来たことの束縛 (replay・生成元) は md_19 と本番登録の判断点へ返す (scope 外、限界に書く) |
| A2 終端済み variant の skip で要求つき判定に届かない | real | 新 driver は専用の campaign identity (spec / search tag が方策軸と別) を使い、skip された variant は history に `skipped` と書いて certified 行を作らない (A3 の照合で自然に塞がる) |
| A3 driver が要求の実効値を再確認しない | real | driver の certified 行は、各 verify 結果の gate 節で `required=True`・意味の版 ≥ 2・D5 pass・`certified=True` をすべて確かめたときだけ。欠ければ閉じた拒否コード |
| A4 fan-out 計画が実行条件と合わない | real | fan-out は変えない・試験しない。新軸の remote fan-out は scope 外 (backoff 専用の分岐で到達しない) |
| A5 U-D の直 build は build 境界の再照合を通らない | real | U-D の結果は「要求つき判定の配線確認 (fixture 付き)」と記録し、certified を主張しない |
| A6 総量・語彙の上限 | real (最小形) | 結果の場面数・反例数・history 1 行の反例数に上限、gate 違反は列挙コード + 件数で投影、自由文なし。語彙は登録簿が持てば `validate_counterexample(vocabulary=)` へ渡す |
| A7 loop.py が所有外 | real | 単位 1 に loop.py を入れる |
| A8 要求なし bytes 不変の範囲 | real (変えた面に限る) | snapshot serialize・capability 結果・verify_payload・receipt 入力の bytes 同一を既存 fixture で照合。lock/WAL は触らない |
| A9 生死確認の表現 | real (nit) | A5 と同じ |
| B1 fixture が certified へ流れうる | real | 小モデル関門の登録簿は production 定数だけを driver の反復関数が使う (引数で差し替えられない)。fixture 登録簿は関門関数の単体 (test・起動器) でだけ渡せる。起動器の outcome は `fixture-liveness` |
| B2 U-D は driver の 1 周を実証しない | real | 起動器は driver の関数 (intake・order_gate・関門・verify 結果の history 投影) を import して使い、build と判定だけを自前で行う。「standalone 判定」と「driver 関数の配線」を分けて記録。完全な 1 周は md_15・md_19 の後 |
| B3 完了条件の固定し過ぎ・stop_reason の食い違い | real | 最小の受け口: 完了 = `complete=True かつ stop_reason="exhausted"`。詳細形は md_19 が合わせる/再交渉する |
| B4 U-A は 3 file と include 解決事実に絞れる | real | 要求時だけ optional な D5 証拠束を capture。要求なしの v1 serialization は byte 同一 |
| B5 driver は薄い接続層 | real | intake・モデル関門・要求つき campaign 呼出し・閉じた history 投影・coder 入力の出力だけ |
| B6 反例 schema 通過 ≠ 反例の真偽 | 一部 refuted | 反例ありは build 前に拒否 (`model-counterexample`) する。拒否は安全側なので replay を待たない。反例の真偽確定 (モデル欠陥の判別) は md_19 の責務 |
| B7 inventory は実装後の実数だけ | real | 実装した call site 数だけ追記 |
| B8 生死確認の最小形 | 一部採用 | 1 job・build 2 本 (X = U1+修正+骨格、S = U1+骨格で修正なし)・各 RMW あり/なし 2 run。S は「出せない理由を構造化して返す」経路の実例 (D2b 赤) として要る。見積り 1 job 5 分前後 |

## (P) の確定

P1 採用 (flag 強制は caller の False で外せない)。P2 修正採用 (最小の受け口、`cc-model-result/1`)。P3 採用。P4 採用 (被覆は登録簿の場面ごと)。P5 採用 (名前つき対照を proposal として通す。LLM 候補の本評価とは書かない)。P6 採用。P7 採用 (MEANING_VERSION 2 据え置き、述語不変・取得元だけ snapshot)。P8 採用。

## plan v2 (実装単位、所有は素集合)

### 単位 1 (U-A) — 所有: orchestrator/verifier/core.py、orchestrator/verifier/model.py、orchestrator/campaign/source_digest.py、orchestrator/campaign/pipeline.py、orchestrator/campaign/loop.py、新 test `orchestrator/tests/test_verifier_capability_gate_witness.py`・`orchestrator/tests/test_pipeline_gate_witness.py`
1. `verify_trace_dir_with_capability(..., require_gate_witness: bool = False)` keyword-only (bool 型を厳密検査)。True のとき snapshot の D5 証拠束で D5 を評価。証拠束が無ければ D5 は unavailable (= certified にならない)。要求なしの capability 値・結果投影・receipt 入力は 1 byte も変えない。
2. D5 証拠束: `include/ycsb.hh`・`cc/silo/transaction.cc`・`cc/silo/ycsb_silo.cc` の text と、`ycsb_silo.cc` の引用 include が `include/ycsb.hh` に解決したかの capture 時の事実。要求時だけ capture し serialize する (要求なしの snapshot v1 JSON は byte 同一)。capture は `source_digest.resolve_evidence` と pipeline の再 capture の両方で同じ条件。disk 版 `_gate_d5(ccbench_root)` は CLI 用に残す。述語 (literal な `#if TRACE` 内の emitter 3 種と include 解決) は変えない。
3. 要求の運搬: `loop.run_campaign(..., require_gate_witness: bool = False)` keyword-only → 2 つの `evaluate` 呼出し → `pipeline.evaluate` → local の `_execute_verification_repetition`。実効値 = 明示要求 or (protocol silo かつ genome の `SILO_ORDER_VARIANT` ≠ 0)。既存 caller には keyword を送らない分岐を保つ。fan-out は変えない。
4. 既存 test は編集しない (test_campaign.py を含む)。新 test: 要求なしの bytes 同一、capability に要求が届く/届かない、flag=1・明示なしで強制、flag=0・明示 True で要求、snapshot の D5 が disk を読まない (snapshot と disk を意図的に分ける)。

### 単位 2 (U-B + U-C) — 所有: 新 `orchestrator/campaign/silo_lock_order_model_gate.py`、新 `orchestrator/campaign/p3_s4_loop_lock_order.py`、`orchestrator/campaign/axis_silo_lock_order.py` (登録簿の定数の追記だけ)、新 test `orchestrator/tests/test_silo_lock_order_model_gate.py`・`orchestrator/tests/test_p3_s4_loop_lock_order.py`、inventory test (`test_p3_exploration_namespace.py`・`test_campaign.py` の certified-writer inventory 節だけ・`test_p3_build_authority_cli.py`・`test_official_perf_closure.py`) への追記
- U-B `cc-model-result/1` (最小): top = {schema, axis, specification_digest, scenarios}。scenario = {scenario_id, complete, stop_reason, explored_configurations, witness_reached, counterexamples}。stop_reason ∈ {exhausted, max_states, max_seconds}。witness_reached は bool|null。counterexamples は `validate_counterexample` 済み (外側の digest・scenario_id と一致)。重複 key・余分 field・場面重複を拒否。上限: 場面 4096・反例は結果全体 64。
- 登録簿 (axis module の定数): `MODEL_SPECIFICATION_DIGEST = None`、`MODEL_SCENARIOS = None` (場面 ID → {expected_configurations: int|None, witness_required: bool})、`MODEL_VOCABULARY = None`。None なら関門は常に拒否 (`model-unregistered`)。
- 関門の判定 (build 前、拒否は別々の理由コード): 結果欠落 `model-result-missing`・schema 不正 `model-result-invalid`・axis/digest 不一致 `model-digest-mismatch`・登録場面の欠落 `model-scenario-missing`・未完了 (complete 偽か stop_reason ≠ exhausted) `model-incomplete`・構成数不一致 `model-coverage-mismatch`・witness 未到達 `model-witness-missing`・反例あり `model-counterexample`。登録外の場面は無視せず拒否しない (記録だけ)。
- U-C driver: 反復関数は production 登録簿だけを使う。順は intake (閉じた proposal、axis `silo-lock-order-policy`、重複 key 禁止) → `order_gate(write=False)` → 小モデル関門 → 合格時だけ骨格 patch 適用・`order_gate(write=True)`・`run_campaign(..., require_gate_witness=True)` → 各 verify 結果の gate 節で A3 を照合 → 閉じた history 行 (`lock_order_history.jsonl`) → coder 入力の出力。history 行の key は plan の案から自由文を除いた閉じた集合。反例は結果 1 行あたり最大 2 件を validated dataclass から投影。gate 違反は D1a/D1b1/D1b2/D1c/D2a/D2b_i/D2b_ii/unreachable の件数と D5 状態の列挙で投影。`p3_s4_loop_policy.py` は import して部品を使うだけで編集しない。
- 起動器 (単位 3) が使う公開関数: `load_lock_order_proposal`、`check_model_result(result_bytes, registry)`、`history_row_from_verification(...)` (名前は実装が決めてよいが、起動器と driver が同じ関数を使うこと)。

### 単位 3 (U-D) — 段 6 の後に別 author 子。repo 外 (job dir) の起動器。

## 規模上限 (段 5・6)

単位 1 production 追加 ≤ 350 行、単位 2 production ≤ 600 行 (test は別)。超えたら差し戻す。

## gate の禁止 (署名) と通る正例

- 禁止: 登録簿が None・digest 不一致・未完了・場面欠落・反例ありのいずれかで build に進むこと。正例: 登録簿と一致し、全登録場面が complete かつ exhausted、構成数一致、witness 到達、反例 0 の fixture 結果は通る。
- 禁止: gate 節の required が偽・版 < 2・D5 非 pass の verify 結果から certified 行を作ること。正例: required・版 2・D5 pass・certified の結果は certified 行になる。

## 変異の事前登録 (実装前、赤になるべき test は実装後に nodeid を確定)

| id | 変異 | 赤になるべき test (単一理由の置き方) |
|---|---|---|
| M1 | pipeline の flag 由来の要求強制を削る | flag=1・明示要求なしの evaluate で capability に required が届く test |
| M2 | loop.run_campaign が要求 keyword を evaluate へ渡さない | flag=0・明示 True の run_campaign で required が届く test |
| M3 | capability が require_gate_witness を verify_trace_dir へ渡さない | 要求ありで gate file 無しの trace が certified にならない test |
| M4 | 要求時の D5 を disk (ccbench_root) から読む | snapshot は emitter 欠落・disk は正常の組で D5 が fail になる test |
| M5 | 要求なしでも D5 証拠束を serialize する | 要求なしの snapshot JSON が既存 bytes と同一の test |
| M6 | 関門が登録簿 None を受理する | `model-unregistered` の test |
| M7 | 期待 digest を結果 file から取る | 別 digest の結果が `model-digest-mismatch` の test |
| M8 | stop_reason を見ない (complete だけ見る) | complete=True・stop_reason=max_states が `model-incomplete` の test |
| M9 | 登録場面の欠落を受理 | `model-scenario-missing` の test |
| M10 | 反例ありを受理 | `model-counterexample` の test |
| M11 | history 投影が反例の余分 field を通す (validated 入力から投影部だけ変異) | 投影 key 集合の完全一致 test |
| M12 | driver の certified 行が gate 節の required を見ない | required 偽・certified 真の結果が certified 行にならない test |

単一理由性は段 6 で実装後に確認する (M1/M2 は互いに遮らない入力を使う。M4 は再照合が先に拒否しない層で分ける)。

## 計算

生死確認 1 job ≈ 5 分、変異・焦点走・受入は land 用。合計 2 node 時間未満の見込み (相談不要)。
