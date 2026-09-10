# 段 4 裁定 (プラン v2 差分) — [T-470] + [T-327] U-1/U-4/U-5 配線 wave

段 3 は 2 レンズとも NO-GO (A: blocker 8、B: blocker 7 + must-fix 5)。親が real/refuted と採否を
裁定し、scope を確定する。**本 wave の看板を確定する** — 「起動 admission と受入の必須配線を入れ、
出力が非認証であることを構造的に保証する」であり、「certified 選択を開通させる」ではない。

## 0. 親が独自に裏取りした事実

- **A-1 / B-3 は real (親が直接確認)**: `p3_autonomous_workload_trial.py:1749-1751` の
  unknown-workload 拒否は `:1760` の launch gate より前にある。`WORKLOADS` (`:171-175`) に
  rr80/rr20 は無い。したがって holdout 分岐は現状 production 到達不能。
- **A-3 は real (親が直接確認)**: `s8b_floor_campaign.py:199-214` は `--mode pilot` を受け、
  official だけが `_assert_official_permitted` (`:204-213`) で無条件拒否される。pilot は
  freeze 由来の holdout セルを実測でき、trial registry を通らない。
- **A-8 / B-2 は real**: C02 の arm injective binding も T-295 approval record も存在しない。
  したがって本 wave 後も `certifying=true` を正当化できない。

## 1. real 採用 — 本 wave で実装する

|#|所見|裁定|実装|
|---|---|---|---|
|A-1 / B-3|holdout が gate 到達前に unknown workload で落ち、U-4 の検出力が恒真ゼロ|**real・採用**|admission を unknown-workload 検査**より前**に置く。argparse は holdout 名を parse 段で殺さず gate へ渡す。rr80/rr20 の実 projection は**追加しない** (実走能力を増やさず、gate が拒否する)。public CLI から `--workloads rr80` が U-4 固有 reason code で拒否される負例を必須にする|
|A-4 (部分)|同一 trial_id の一回性だけでは複数 manifest の best-of-N を閉じない|**real・部分採用**|本 wave は単一 lifecycle ledger 内の一回性まで。receipt に registry introduction commit を刻み、複数 manifest 併存の検出可能性を残す。実験単位の再設計は scope 外 (§2 U-A)|
|A-8 / B-2|`certifying=true` は C02 と T-468 なしに正当化できない|**real・採用**|**本 wave は `certifying=true` を構造的に発行しない**。receipt は必ず non-certifying とし、reason list に `c02-arm-binding-unproven` と `t468-approval-authority-absent` を含める。下流はこれを拒否する|
|B-8|contract 名に揃えるだけで readiness が偽昇格する|**real・採用 ((P2) を撤回)**|**production 関数名を contract 名へ揃えない**。`s8c_preregistration_evidence.py` と contract JSON は**編集しない**。12 述語の status は本 wave で一切動かさない。既存 predicate テストの期待値変更も行わない|
|B-4|探索 run の非認証が terminal report のラベルに留まり generic Layer 3 から除外されない|**real・採用**|`launch_admission` を run-start と report の双方に exact 記録し、generic `build_report()` は探索 admission を検出したら `certifying_input: false` を必須 field として持つ。accepted 入口はそれを無条件拒否する|
|B-5|formal 分岐が「既 start を拒否」と書くのに lifecycle が後送|**real・採用**|lifecycle ledger を本 wave に含める。保証範囲は「単一 shared ledger 内」と明記し、worktree/clone 横断は主張しない|
|B-6 / B-7|rename と新引数の caller 列挙不足|**real・採用**|改名を最小化した上で、残る caller を三分類 (U-4 拒否期待 / 明示 exploratory / formal) して更新する。private worker への test 専用 bypass default を作らない|
|B-12|runbook 案が未実装手順を書く|**real・採用**|runbook には本 wave で実在する手順だけ書く。receipt 節は receipt を land する場合のみ|
|B-13|常に拒否する実装が緑になる|**real・部分採用**|下流の各機構 (schema parse / tracked / bytes 一致 / 参照 hash) に**機構単位の正例**を置く。合成条件 `certifying` の正例は作らない (作れば虚偽)。「正例が作れない」ことを worklog に明記する|

## 2. real だが scope 外 — 裁定パッケージ (U-A〜U-G) としてユーザーへ返す

|ID|所見|理由|
|---|---|---|
|U-A|A-4: 実験単位を `(prereg_generation, holdout, arm, replicate_slot)` に再設計し、承認 artifact が全 slot を固定する|受理集合の再設計。[T-295]/[T-327] の事前登録内容に踏み込む|
|U-B|A-3: `s8b_floor_campaign --mode pilot` が U-4 と台帳を通らず holdout を観測できる|**重大**。別 producer であり、共有下位境界の設計が要る。DW-G03 の独立 2 例が揃ったので族一般化の起票に足りる|
|U-C|A-2: holdout 束縛が workload 名と rratio だけで、freeze の skew/rmw/records/threads を含まない|C01 の面。測定条件の束縛設計|
|U-D|A-5: project-global な一回性 CAS|[T-469] が既に所有 (U-3 同梱で裁定済み)|
|U-E|A-6 / B-9: canonical manifest/registry authority と C02 arm injective binding|[T-468] は approval artifact 不在で実装不能 (DW-G04)。C02 は述語 green 化段|
|U-F|B-3 後半: rr80/rr20 の実 projection と formal holdout runner|測定能力の追加であり配線ではない|
|U-G|N1: `python -m ...s8c_preregistration check` が常に 12 述語 ERROR を返す二重 import 欠陥|fail-closed で誤受理を生まない。production 配線は API 経由にするため本 wave では直さない|

## 3. 不採用 / 降格

- (P2) 「contract 名へ揃える」= **撤回** (B-8 real 採用の帰結)。
- プランの evidence evaluator 改修 (`s8c_preregistration_evidence.py:409-511, 621-666`) = **不実装**。
- プランの `bind_trial_arm` 改名 = **不採用** (C02 を名前だけで進めたと誤認させる)。
- B-1 の「brief を U-4 launch-only へ縮小」= **部分不採用**。receipt 発行と下流の受入拒否までは
  本 wave に残す (T-470 の本体が「下流が rc でなく receipt bytes を消費する」ため)。
  certified selector の実結線だけを後続へ送る (現 checkout に consumer が存在しない = DW-G04)。

## 4. 実装契約 (プラン v2 の確定事項)

1. 編集面は `orchestrator/campaign/s8c_preregistration.py` (追加のみ)、
   `orchestrator/campaign/trial_registry.py`、`orchestrator/campaign/p3_autonomous_workload_trial.py`、
   新設 `orchestrator/campaign/s8c_acceptance_receipt.py`、`orchestrator/campaign/layer3_report.py`、
   および対応 test。**`s8c_preregistration_evidence.py` と contract JSON は編集しない。**
2. `certifying` が真になる経路を作らない。receipt schema に `certifying` と
   `non_certifying_reason_codes` を持ち、後者は常に非空である。
3. 保証範囲を過大主張しない: 一回性は単一 lifecycle ledger 内、authority は registry history の
   一意性まで。worktree/clone 横断と approval authority は主張しない。
4. 既存テストの期待値を緩めない。U-4 で受理集合が縮む既存 positive は、明示 opt-in を足して
   意味を保存する (autouse fixture で暗黙許可しない)。
5. 12 述語の status を動かさない。`test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
   はそのまま緑を維持する。

## 5. 変異事前登録 (`DW-M01`。実装前登録、単一理由性は段 6 anchor 再検証で確認)

|#|変異|期待赤 (kill 判定)|
|---|---|---|
|m01|`admit_unregistered_exploratory` の既定拒否を既定許可に戻す|U-4 既定拒否の負例|
|m02|holdout 交差検査 `set(workloads) & HOLDOUT_WORKLOADS` を落とす|holdout opt-in 拒否の負例|
|m03|`HOLDOUT_WORKLOADS` を `WORKLOADS` 由来に差し替える|holdout 名が gate を素通りする負例|
|m04|admission を unknown-workload 検査の**後ろ**へ戻す|public CLI からの holdout 拒否 reason code 負例|
|m05|`_run_workload` の sealed run scope 必須を外し fallback を復活させる|private worker 直呼び拒否の負例|
|m06|`require_effective_preregistration` の digest 照合を型検査だけにする|偽造 capability 拒否の負例|
|m07|capability の commit と manifest `prereg_commit` の一致検査を外す|祖先 commit capability 拒否の負例|
|m08|lifecycle start の重複検査を落とす|同一 trial_id 再走拒否の負例|
|m09|lifecycle の flock を外す|単一走行の負例 (hang_risk 指定)|
|m10|acceptance の terminal row 必須を外す|crash 後 acceptance 拒否の負例|
|m11|receipt の exclusive-create を上書き許可にする|receipt 置換拒否の負例|
|m12|receipt verifier の tracked 検査を外す|untracked receipt 拒否の負例|
|m13|receipt verifier の bytes 再 hash を宣言値の自己一致だけにする|report/journal 改変検出の負例|
|m14|下流 `build_accepted_report` の `certifying` 検査を外す|non-certifying receipt 拒否の負例|
|m15|`non_certifying_reason_codes` を空リストにできるようにする|reason 非空の負例|
|m16 (正例)|`--allow-unregistered-exploratory` 付き非 holdout 探索起動|**赤にならない**こと (過剰拒否の検出)|
|m17 (正例)|manifest 無し・flag 付き・ycsb-a の既存 report 形状|**赤にならない**こと|

## 6. 実装単位

|単位|所有|依存|
|---|---|---|
|A|`s8c_preregistration.py` (追加のみ) + `trial_registry.py` + `p3_autonomous_workload_trial.py` + `orchestrator/tests/test_trial_registry.py` + `orchestrator/tests/test_p3_autonomous_workload_trial.py` + `orchestrator/tests/test_s8c_preregistration_core.py`|なし|
|B|新設 `s8c_acceptance_receipt.py` + 新設 `orchestrator/tests/test_s8c_acceptance_receipt.py` + `layer3_report.py` + `orchestrator/tests/test_layer3_report.py` + A が触った acceptance 面|A|
|C (親)|`docs/phase3-s8c-autonomous-trial-runbook.md`、spool fragment|A→B|

順序 = A → B → C(親)。A と B は同一 worktree で直列 (trial_registry.py を共有するため)。
