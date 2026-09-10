静的読解の結論は **NO-GO**。U-4 は現状の入口では発火不能であり、入口を直しても、別測定経路・複数 manifest・worktree ごとの一回性・不完全な条件束縛により best-of-N を防げない。以下、blocker 8件。

## 所見

### A-1 / blocker / holdout workload は U-4 gate に到達せず、保証が恒真になる

- 根拠: `rr80` / `rr20` は `WORKLOADS` に存在しない（`orchestrator/campaign/p3_autonomous_workload_trial.py:171-175`）。`run_trial` は未知 workload を先に拒否する（同 `:1746-1751`）一方、プランの gate 挿入位置はその後の現行 `:1760` 相当（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s2-plan.md:102-119`）。テストも `WORKLOADS` を monkeypatch して初めて H1/H2 を通している（`orchestrator/tests/test_p3_autonomous_workload_trial.py:2105-2142`）。
- 失敗シナリオ: `run_trial(workloads=["rr80"], trial_manifest=...)` → U-4 判定ではなく `unknown workload` で誤拒否され、U-4 固有の検出力は常にゼロ。
- 成果物影響: 正しい H1/H2 でも正式 report / acceptance receipt / certified 選択が生成不能。
- 提案: holdout を正式な workload resolver に組み込み、未知 workload 判定より前に U-4 admission を行う。H1/H2 を monkeypatch なしで到達させる受入試験を必須にする。

### A-2 / blocker / trial registry の束縛が条件名と rratio だけで、別実験を H1/H2 として受理できる

- 根拠: registry の holdout 束縛は `{workload, ycsb_rratio}` のみ（`orchestrator/campaign/trial_registry.py:46-49`）、acceptance も主に workload と rratio しか照合しない（同 `:1399-1416`）。対して凍結条件は skew `0.9`、rmw `0`、records `1,000,000`、threads `48` を含む（`orchestrator/campaign/s8b_holdout_freeze.py:58-74`）。P3 は records `100,000`、threads `4` をハードコードする（`orchestrator/campaign/p3_autonomous_workload_trial.py:528-584`）。
- 失敗シナリオ: A-1だけ直して登録済み H1=`rr80` を起動 → 100k records / 4 threads の測定が、名称と rratio の一致だけで H1 として receipt 化される。
- 成果物影響: report の性能値と certified arm 選択が、凍結済み 1M/48 条件の結果ではなくなる。
- 提案: ratified freeze の完全な `HoldoutSpec` とその SHA を sealed binding とし、campaign identity・実行引数・run-start・terminal report・acceptance で全 field を再照合する。

### A-3 / blocker / 通常運用の `s8b_floor_campaign --mode pilot` が U-4 と台帳を通らず holdout を観測できる

- 根拠: floor campaign は `pilot` / `official` を受け付け（`orchestrator/campaign/s8b_floor_campaign.py:197-214,3420-3429`）、pilot は official gate の対象外で実行される（同 `:2670-2740,3470-3499`）。測定セルは freeze の完全な records / threads / workload を使い（同 `:610-628`）、そのまま measurement 関数へ渡す（同 `:2102-2108`）。
- 失敗シナリオ: `python -m orchestrator.campaign.s8b_floor_campaign --mode pilot ...` で H1/H2 を先に観測 → 新設 trial lifecycle に記録されないまま条件や候補を調整 → 後から一度だけ正式試行。
- 成果物影響: certified 選択は一回の preregistered 試行に見えるが、実質は先行 holdout 観測後の選択になる。
- 提案: U-4 を P3 の高位入口だけでなく、freeze-derived holdout を実測へ渡す共通下位境界に置く。既存 S8B 経路にも approved slot と共有の一回性台帳を要求する。

### A-4 / blocker / trial_id ごとの一回性と manifest SHA ごとの receipt は、複数 manifest による best-of-N を閉じない

- 根拠: registry は同一 hash / trial_id / campaign_id の重複だけを拒み、異なる manifest の併存を許す（`orchestrator/campaign/trial_registry.py:386-400`）。その挙動はテストでも肯定されている（`orchestrator/tests/test_trial_registry.py:462-479`）。各 API は caller 指定の manifest / registry / trial_id を受ける（`s2-plan.md:26-47`）。receipt の canonical path も manifest SHA ごと（同 `:395-407`）。
- 失敗シナリオ: 一意な trial_id / campaign_id を持つ manifest を N 個登録 → 各 trial は一回だけ実行 → N 個の正規 receipt から良いものだけを下流へ渡す。
- 成果物影響: certified report と選択値が、事前承認された一組ではなく N 回中の最良結果になる。
- 提案: manifest ではなく `(prereg_generation, holdout, arm, replicate_slot)` を安定した実験単位にし、承認 artifact が全 slot と個数を固定する。追加 manifest を certified 対象にできず、全 predeclared receipt の列挙・消費を下流で検査すること。

### A-5 / blocker / 一回性台帳が worktree / clone ローカルで、並行した同一 trial を防げない

- 根拠: プラン自身が project-global CAS を提供せず、worktree / clone 間の重複を防げないと認める（`s2-plan.md:355-393`）。予定する `record_trial_start_once` はローカル JSONL を trial_id で排他追記するだけ（同 `:389-391`）。
- 失敗シナリオ: 同じ manifest と trial_id を二つの通常 worktree で同時起動 → 両方のローカル台帳が未使用として受理 → 良い結果の worktree だけを commit・receipt 化。
- 成果物影響: lifecycle と receipt は一回性を示すが、採用された report の値は実際には複数回中の選択結果。
- 提案: artifact 作成前に project-global な atomic CAS / lease を取得する。利用不能時は fail-closed かつ永久に `certifying=false`。台帳履歴では削除・再追加も拒否する。

### A-6 / blocker / canonical manifest・registry・承認 authority が admission に束縛されていない

- 根拠: manifest / registry の任意 path を受ける API が維持される（`s2-plan.md:26-47,143-195`、現行 CLI は `orchestrator/campaign/trial_registry.py:1444-1452`）。planned admission fields に registry path / blob SHA / introduction commit がない（`s2-plan.md:50-60`）。一方、evidence contract は canonical manifest path を要求する（`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:75-115`）。プランも approval artifact が未成立であることを認める（`s2-plan.md:490-513`）。
- 失敗シナリオ: 任意 path の並行 registry / manifest で launch と acceptance を構成 → path 内では append-only・一意性を満たす → 正式 authority が承認していない trial に receipt を発行。
- 成果物影響: certified report の trial_id・arm・manifest SHA が、唯一承認された台帳ではなく caller 選択の台帳に由来する。
- 提案: canonical relative path、manifest SHA、registry path、registry blob SHA、unique introduction commit を approval artifact で固定し、launch admission と receipt に含めて acceptance 時に完全一致させる。T-468 未解決中は `certifying=true` を禁止する。

### A-7 / blocker / receipt を必須消費する実在の下流経路がなく、receipt-free report が正式成果物になり得る

- 根拠: プランは既存 `build_report` / `render` を receipt-free のまま残す（`s2-plan.md:272-300`）。新しい `build_accepted_report` は戻り値だけで、保存 path・schema・既存 CLI との排他関係がない（同 `:282-299`）。さらに「既存 certified-selection consumer はないため T-470 完了を主張しない」と明記している（同 `:300`）。
- 失敗シナリオ: pre-acceptance report を現行 `layer3_report` CLI で生成 → receipt 検証経路を呼ばず、その report を従来どおり選択・共有 → receipt が存在しても消費されない。
- 成果物影響: certified と見なされる report / 台帳選択に receipt SHA が拘束されず、良い report だけを流せる。
- 提案: material report と acceptance receipt を包む別 schema の accepted envelope を canonical path に保存し、`material_report_sha256` と `receipt_sha256` を必須化する。certified 選択の全 consumer は envelope 型だけを受理し、旧 CLI 出力は明示的に non-certified とする。

### A-8 / blocker / arm の実行時束縛が未証明で、`certifying=true` は恒真不能か既存拒否条件の緩和を迫られる

- 根拠: 現行 registry は宣言しか証明せず、実際の arm を certify しないと明記する（`orchestrator/campaign/trial_registry.py:2-6,124-130`）。C02 は run-start、terminal report、campaign identity、proposal path、invocation ID の injective binding を要求する（`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:46-72`）。プランも C02 は進まず declared-only のままと認める（`s2-plan.md:563-569`）一方、certifying 条件には non-declared-only arm binding を置く（同 `:467-478`）。
- 失敗シナリオ: on/off の実行内容または proposal path を取り違える → 宣言上の arm 名だけ一致 → C02を省略して receipt を certifying にすれば誤受理、厳守すれば全 receipt が永久に non-certifying。
- 成果物影響: certified arm 名と report 内の性能値の対応が反転し、選択された arm が実測内容と一致しなくなる。
- 提案: arm capability を campaign identity、proposal artifact、実行 invocation、run-start、terminal report まで一方向に伝播し、acceptance で同一 invocation を照合する。これが完成するまで certifying receipt を発行しない。

## 親 brief N1〜N6 の再検証

| 主張 | 判定 | 静的根拠・限定 |
|---|---|---|
| N1 | 確認 | `-m` 実行時の `__main__` と package module の二重 import により `isinstance(PredicateResult)` が失敗し（`s8c_preregistration.py:1444-1461`）、包括 catch が12件一律 ERROR を作る（同 `:1474-1521`）。ただし package API 直接利用まで壊れるという一般化は不可。 |
| N2 | 確認 | 新 registry API は未配線で、既存の近似 API は manifest 読み込み・宣言受理に留まる。 |
| N3 | 反証 | 束縛表を直接 helper に与えれば拒否ロジック自体は発火し得るが、production の `run_trial` では A-1 により holdout がその前で拒否される。さらに完全な条件束縛もない。 |
| N4 | 確認 | runbook の通常手順は manifestless（`docs/phase3-s8c-autonomous-trial-runbook.md:61-102`）。 |
| N5 | 限定付き確認 | T-470 型の acceptance receipt bytes は存在しない。ただし repository に receipt と呼ばれる別種 artifact / transport receipt はあるため、「receipt が一切存在しない」は過大一般化。 |
| N6 | 限定付き確認 | 新しい trial manifest / registry artifact は存在せず、現行 frozen-artifact manifest にもない（`orchestrator/tests/test_frozen_artifacts.py:38-85`）。ただし S8C の condition-freeze artifact 自体は既に存在する。 |

既存の拒否条件を明示的に削除・緩和する変更はプラン中に見つからなかった。ただし A-8 の矛盾を C02 の省略で解消して `certifying=true` にするなら、それ自体が blocker 級の正しさゲート緩和となる。

## 総括

**NO-GO — blocker 8件。**

最低限、完全な holdout 条件束縛、全測定入口を覆う共有 admission、project-global 一回性、承認済み canonical manifest の固定、arm の実行時証明、receipt 必須の実在 downstream envelope が揃うまで、certified 選択・正式 report・台帳による一回性を主張できない。