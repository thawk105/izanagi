# 段 4 裁定 — [T-1396] 判定器 C04 の到達対象へ reject_started_trial を足す

## 親が追加で実測した事実

- `orchestrator/tests/test_s8c_preregistration_invariant.py` の
  `MACHINE_CONTRACT_FUNCTION_CHECKS` は
  `("C04", "orchestrator/campaign/trial_registry.py", "reject_started_trial")` を**既に含む**。
  契約側の exact-set は 5 名を pin 済みで、欠けているのは判定器だけである。この file の
  期待値は変更不要。
- `_snapshot_current_commit` (`test_s8c_preregistration_predicates.py:153`) は現 HEAD の
  evidence path を `git archive` で一時 repo へ展開し、**実 production の bytes** を評価する。
  したがって `current_commit_snapshot` 系は stub ではない実 repo 正例である。
- `orchestrator/tests/` で判定器 module 名を参照する test file は 4 件:
  `test_s8c_preregistration_predicates.py`、`test_s8c_preregistration_core.py`、
  `test_artifact_admission.py`、`test_t671_source_binding.py`。
  間接 consumer は `test_campaign_lock_codec.py` (path 一覧を parametrize)、
  `test_s8c_preregistration_invariant.py` (契約 exact-set)。
- `acceptance_duration_ledger.json` に無い node は unknown 扱いで許容される
  (`test_acceptance_schedule_order.py:439`)。新 node の登録は不要。

## 所見の裁定

| # | 所見 (出所) | 判定 | 採否 |
|---|---|---|---|
| A1 | 到達判定は may-reach 集合で、契約の "preflight" という**位置**を見ない。呼出しを移動しても死コードでも target が残る | **real** | **scope 外**。裁定パッケージへ |
| A2 | 実 HEAD 正例は callee 本体を見ない。`reject_started_trial` を `pass` にしても通る | **partially real** | **狭めて採用** (下記 R3) |
| A3 / B3 | 追加予定の `_functions(registry)` 存在検査は先行する `_declared_call` から含意され冗長 | **real** | **採用 (足さない)** |
| B1 | 焦点走を 1 file とする列挙は不完全。実際は 4 file + 間接 2 | **real** | **採用** |
| B2 | 広義 reader / metadata の取り残し | **refuted (無影響)** | 不採用。invariant は既に正しく、ledger は unknown 許容 |
| B4 | 変異は owner node 単独なら帰属するが、repo-wide では drift mask 候補がある | **real** | **採用** (probe 先行) |
| B5 | 親 probe の一般化限界 | **real** | **採用** (記録を限定する) |
| B6 | brief に 2-file scope 外の記録 (spool fragment) が混ざる | **refuted** | 不採用。spool fragment は `DW-S07` の義務であり scope 逸脱ではない |

### A1 を scope 外とする理由

契約の `reachable_from` は 3 件とも「どこから到達するか」の文言を持つが、`_evaluate_c04` は
既存の 2 件についても位置を検査していない (`forbid_trial_restart` が except 節の中にある
ことを見ていない)。位置・支配関係の検査は新しい解析機構であり、D1292 が決めた
「reachable target へ 1 件足す」を超える。契約自身の `static_only_note` も
「実際の crash や terminal report を要求しない」と静的検査に限定している。
`DW-G05` に従い、確定主目的の本体実装を優先し、A1 は裁定パッケージへ返す。
**この wave の変更は受理集合を狭める向きにしか動かないので、A1 を残しても規律 2 に反しない。**

### A2 を狭めて採用する理由

「callee 本体まで検査せよ」は A1 と同じく契約が静的検査に限定している範囲を超える。
一方、ユーザー引数は「production の呼び先を**実体として名指し**し、性質だけの正例に
しないこと」を明示要求している。`current_commit_snapshot` は実 bytes を評価するので
両層 stub では通らないが、**production の呼び先を名指ししていない** (12 条件の reason
snapshot の 1 行でしかない)。そこで、実 repo の bytes から `reject_started_trial` の
呼出しだけを消すと C04 が UNSATISFIED になる負例を足す (R3)。これは明示要求の範囲内であり、
恒真でなくなったことを**実コード上で**示す。

## プラン v2 (確定)

- **R1 判定器**: `_evaluate_c04` の `_declared_call` 対象へ
  `(registry_path, "reject_started_trial")` を足す。**これだけ**。
  `_functions(registry)` 側の存在検査は足さない (A3/B3。冗長で単一理由性を壊す)。
  reason code は新設しない。
- **R2 共有 fixture**: `TOKEN_ONLY_C04` に `reject_started_trial` の import と
  `run_trial` 冒頭 (try の前) の呼出しを足す。`_negative_control_case` の C04 branch の
  registry stub にも `def reject_started_trial(): pass` を足す。既存 baseline が
  `EVIDENCE_UNDEFINED` のままになるようにする。既存の期待値は変えない。
- **R3 実 repo 負例 (実体を名指しする)**: 現 HEAD の bytes を一時 repo へ展開し、
  `p3_autonomous_workload_trial.py` の `trial_registry.reject_started_trial(` 呼出しだけを
  取り除いて C04 が `UNSATISFIED / crash-policy-cell-partial` になることを示すテストを足す。
  取り除く前後で `mark_experiment_indeterminate` と `forbid_trial_restart` の到達、および
  registry の両定義が残ることを occurrence count で assert し、単一理由にする。
- **R4 token-only 負例**: `TOKEN_ONLY_C04` から 3 件目の呼出しだけを消して
  `UNSATISFIED / crash-policy-cell-partial` になることを示すテストを足す
  (段 6 変異 matrix の owner node)。`NEGATIVE_CONTROL_CASES` に新 ID は足さない。
- 契約 JSON は編集しない。`test_s8c_preregistration_invariant.py` も編集しない。

## 焦点走の集合 (統合 commit 後に走らせる)

`orchestrator/tests/test_s8c_preregistration_predicates.py`、
`orchestrator/tests/test_s8c_preregistration_core.py`、
`orchestrator/tests/test_artifact_admission.py`、
`orchestrator/tests/test_t671_source_binding.py`、
`orchestrator/tests/test_campaign_lock_codec.py`、
`orchestrator/tests/test_s8c_preregistration_invariant.py`。

判定器は HEAD blob 束縛なので、**未 commit のまま走らせない** (contract-loader-drift の偽赤)。

## 変異事前登録 (DW-M01、実装前)

対象 file は `orchestrator/campaign/s8c_preregistration_evidence.py` (contract loader 束縛)。
`DW-M07` に従い **probe を先に全件 SURVIVED で走らせて観測 node を集め**、本走 spec は
その観測集合を完全一致の期待 node として登録する。drift mask 込みの KILLED として登録し、
owner 単独証拠には数えない (B4)。

- **MU-1**: `_evaluate_c04` の対象 tuple から `(registry_path, "reject_started_trial")` の
  1 行を削除する。期待 = KILLED。単一理由性: 削除しても `main -> run_trial` の検査、
  先行 2 target、registry 定義検査はすべて通るので、最初に変わる判定は 3 件目の
  `_declared_call` だけである。owner 候補は R4 の token-only 負例と R3 の実 repo 負例。
- **MU-2**: 同 tuple の 3 件目を `(registry_path, "forbid_trial_restart")` へ書き換える
  (重複させて 3 件目の検査を恒真化する)。期待 = KILLED。単一理由性: MU-1 と同じ経路で、
  「対象が増えたように見えて実は増えていない」形を殺せるかを見る。
- 両変異とも `--runner-mode dispatch`、`--force-dispatch`、`--attempt-out` と
  `--wrapper-attempt` の対を使う。spec と `--out` は checkout 外に置く。

## scope 外の real 所見 (裁定パッケージ候補)

1. **A1 — C04 が契約の呼出し位置を検査しない。** 到達集合だけを見るので、
   `reject_started_trial()` を preflight から重複拒否の後ろへ移しても、
   `False and reject_started_trial()` のような短絡死コードにしても target は残る。
   既存の 2 件 (`mark_experiment_indeterminate` / `forbid_trial_restart` が crash handler の
   中にあること) も同じく未検査である。争点は「C04 の machine-checkable claim を
   到達可能性に限定するのか、呼出し位置・支配関係まで含むのか」。
2. **A2 の残り — callee 本体を検査しない。** `trial_registry.reject_started_trial` の本体を
   `pass` にしても、判定器・正例・負例はすべて同じ結果になる。
3. **契約の `field_paths` (`trial_lifecycle.started_once` / `trial_lifecycle.restart_forbidden`)
   を判定器が一切読まない。** 実体は `trial_registry.py` の state 定義と更新に存在するので、
   架空の懸念ではなく現行の契約不一致である。争点は 1 と同じ軸。

いずれも D1292 の「reachable target を 1 件足す」を超えるので、この wave では実装しない。
