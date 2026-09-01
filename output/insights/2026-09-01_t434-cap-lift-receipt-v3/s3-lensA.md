判定は **REAL、ただし親の理由づけは一部 refuted** です。現状では P6 の実装・認定記録が確実に存在せず、実 evaluator を通る正例は作れません。一方、「P1〜P9 の評価器が全部ゼロ」は実測方法が弱く、依存関係を一般化しすぎています。

テストは実走していません。以下は静的検査です。

### 受理集合トレース

ここで「通る」は generation budget gate の通過を指します。registered 起動には後段の manifest gate があります。

| 入口 | receipt 無し 1 / 2 / 3 | plan の valid receipt 付き 1 / 2 / 3 | 後段 |
|---|---|---|---|
| `main` | 通る / 通る / 拒否 | 拒否 / 拒否 / 通る | `run_trial` を再通過。registered では manifest が exact 2 |
| `run_trial` | 通る / 通る / 拒否 | 拒否 / 拒否 / 通る | registered は runtime と manifest の exact 一致必須 |
| `_run_workload` | sealed scope 内で通る / 通る / 拒否 | 拒否 / 拒否 / 通る | scope 自体は generation と receipt を束縛していない |

根拠は `orchestrator/campaign/p3_autonomous_workload_trial.py:501-510,3717,4397,5064`、plan `:51-58`。registered の追加拒否は `orchestrator/campaign/trial_registry.py:771-772` と `orchestrator/campaign/p3_autonomous_workload_trial.py:1245-1262` です。

[severity: must-fix] [観点 1, 3, 5]
主張: `trial_registry` は plan が数えていない generation consumer であり、registered 系の generation 3 は valid receipt があっても拒否される。逆に direct `_run_workload` の scope は generation を束縛しないため、manifest 2 の admission と receipt-backed 3 を混在させる余地がある。
根拠: `orchestrator/campaign/trial_registry.py:743-773`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1245-1262`、同 `:477-482,3699-3717`、`orchestrator/campaign/trial_registry.py:5753-5762`
影響: registered trial の台帳受入・受領証・certified 系では generation 3 正例が永久に通らない。一方 private 入口では preregistration の exact G=2 と異なる運転を開始し得る。N3 の「第 7 consumer」という個数と provisional P3 は refuted。
提案: `trial_registry`、manifest schema、registry/report acceptance を結線面へ追加し、receipt が exact G=2 を supersede するのか、registered 外だけを支配するのかを先に裁定する。`_RunScopeBinding` に generation・receipt SHA・application binding を封印して下位入口で exact 比較する。

[severity: must-fix] [観点 1, 2, 6]
主張: receipt-free cap exact 2 は runtime invariant ではなく、可変な `MAX_APPROVED_GENERATIONS` と offline C11 に依存する。定数だけ 3 にすると manifestless exploratory 経路では receipt 無しの generation 3 が三入口を通り、C11 は実行時 gate にならない。
根拠: plan `:8,51-58,102-103`、`orchestrator/campaign/s8c_preregistration_evidence.py:2525-2569,3371-3444`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1209-1221`
影響: plan が塞いだと主張する constant-only lift が production 実行面に残る。completeness が後で拒否しても、role・build 側の副作用を開始済みになり得る。
提案: producer と独立 completeness の双方で receipt-free cap を literal 2 として実行時検査する。C11 は mutation detector とし、runtime authority に数えない。

[severity: must-fix] [観点 2, 3]
主張: `origin_binding_sha256` と `run_configuration_sha256` の canonical preimage が未定義で、現在の形では receipt raw SHA との循環が生じ得る。申請側の二つの hash を一致させるだけの恒真検査にもなり得る。
根拠: plan `:31,72`、`orchestrator/campaign/autonomous_trial_completeness.py:146-150`、`orchestrator/campaign/p3_autonomous_workload_trial.py:762-793,1461-1480`
影響: campaign ID は receipt SHA を含む一方、origin binding は campaign ID を含むため、origin hashをそのまま使うと receipt SHA の自己参照になる。除外方法を各 consumer が独自に選べば、同じ receipt が異なる run configuration を承認する。
提案: receipt 発行前に計算できる、domain-separated な application preimage を exact key 集合で定義する。receipt SHA、campaign ID、発行後 field を明示的に preimage から除外し、その除外自体を全 consumer で pin する。

[severity: must-fix] [観点 3, 4, 5]
主張: C11 の contract・field_paths・評価器改訂は D882 が予約・却下した locus と衝突し、plan は semantic hash pin、`DECIDER_VERSION`、次世代 condition-freeze を落としている。このままでは C11 面は発効しない。
根拠: `docs/decisions.md:32456-32464,32477-32492,32511-32513`、同 `:19101-19117`、`orchestrator/tests/test_s8c_preregistration_core.py:1195-1198`、`orchestrator/campaign/s8c_preregistration.py:1673-1680`、plan `:103,183-187`
影響: literal hash test が失敗し、凍結 tip と実 evaluator の版・意味がずれる。C11 の拒否理由を変更しても正式な事前登録 evidence には反映されず、材料レポートが参照する preregistration chain と実コードが分裂する。
提案: 先に独立裁定で D882 決定 (3) を supersede する。その後 `DECIDER_VERSION` bump、contract hash の全 literal、正本文書、次世代 condition-freeze、境界テストを D439/D458 に従う変更単位で更新する。

[severity: must-fix] [観点 2, 3]
主張: plan の topology 手順は `core.useReplaceRefs=false` を HEAD 捕捉にしか明記せず、後続の `rev-list`・`cat-file`・`diff-tree` を同じ hardened git 面へ閉じていない。git environment allowlist と config 無効化も欠落している。
根拠: plan `:80-85`、`orchestrator/campaign/s8b_ratified_freeze.py:303-315,340-359`、`orchestrator/campaign/s8c_acceptance_receipt.py:580-600`
影響: H の捕捉後に後続 query だけが replace/config/environment の影響を受ければ、親 G、導入 commit A、履歴 immutability の異なる像を組み合わせて偽 receipt を受理し得る。
提案: 全 git 呼出しを一つの hardened helper に限定し、`GIT_NO_REPLACE_OBJECTS`、global/system config 無効化、環境 allowlist、shallow/replace/grafts 拒否を共通適用する。

[severity: must-fix] [観点 2, 5, 6]
主張: topology と revision 束縛だけの v1 は実装可能だが、それで acceptance を開くのは D121/D150/D156 の前提条件を迂回する。閉じたままなら rejection-only の dead branch になる。
根拠: `excerpt-d121.md:62-70` の「多世代開放の前提条件を 10 件に固定」、`excerpt-d150.md:60-62` の「申請側の宣言は入力にすぎず状態語を申請側に選ばせない」、`excerpt-d156.md:5-11` の「admission 結線まで含めた end-to-end calibration」および認定記録要求
影響: 開けば P6 accreditation 無しで generation 3 が通り、正しさゲートを弱める。閉じれば receipt-backed な certified 選択・材料レポート・台帳の正例が存在せず、「あるが効かない保証」になる。
提案: topology-only object は admission capability を発行しない内部部品に限定する。cap を開く実装は、少なくとも P6 実装・実 accreditation record・実 evaluator-backed witness が存在するまで WAIT とする。

[severity: must-fix] [観点 1, 3]
主張: `layer3_report.py` を編集すると `meta.generator.sha256` が変わるが、fresh rebuild 比較はこの field を正規化しない。したがって plan が後方互換とする旧 v3 report は、schema readerでは読めても campaign-chain では過剰拒否される。
根拠: `orchestrator/campaign/layer3_report.py:643-677`、`orchestrator/campaign/autonomous_trial_completeness.py:4687-4721,5015-5032`、`excerpt-d828.md:3-6`
影響: T-434 直前に発行され現在 chain 検査を通る material report が、generator source の編集だけで fresh rebuild 不一致へ反転する。既存材料の参照可能性と plan の v2/v3 後方互換主張が食い違う。
提案: recorded generator hash をどう扱うかの versioned compatibility 規則を設計し、旧 v3 の schema 読取だけでなく campaign-chain 正例を追加する。単純に generator hash 比較を削除して弱めてはならない。

[severity: should-fix] [観点 2, 5]
主張: 親 P4 の「`D121` 参照実装 0 件だから P1〜P9 evaluator 0 件」という一般化は証明になっていない。P1 は後続 D160 が充足を記録しており、現時点の NO-GO は「全部無い」ではなく、P6 一件だけでも確実に塞がることから導くべきである。
根拠: `docs/decisions.md:7938-7948`、`output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md:208-212`
影響: 既に存在する機構まで先行依存として再起票し、必要な欠落である P6 handler・adapter・accreditation format の整備順を誤る。
提案: P1〜P9 を行ごとに「機構」「独立 evaluator」「実 witness」「認定」の四列で再棚卸しする。NO-GO の最小証明は P6 未実装・認定記録無しに置く。

[severity: should-fix] [観点 2, 5]
主張: dead branch が D841 に直接違反するという plan の引用は強すぎる。D841 の逐語は receipt と consumer の同時変更を要求するもので、A/B/C 同一 commit は形式上これを満たす。ただし実装しない WAIT は D841 と矛盾しない。
根拠: plan `:1,153,239-240`、`excerpt-d841.md:3-9`
影響: 正しい NO-GO を弱い裁定引用で支えると、consumer を同時追加しただけで dead branch が許されるという反論を招く。
提案: NO-GO の直接根拠を D156 の accreditation、D150 の fail-closed、実 positive control 不在へ置く。D841 は「実装する場合の不可分性」として引用する。

なお、既存 repo には到達不能枝を stub で正例化した先例が実在します。acceptance receipt parser は `certifying=true` を構造的に拒否しますが、Layer 3 の正例は `SimpleNamespace(certifying=True)` と verifier monkeypatch を使っています (`orchestrator/campaign/s8c_acceptance_receipt.py:420-423`、`orchestrator/tests/test_layer3_report.py:264-270,1824-1845,1911-1934`)。T-434 が明記する「実体を stub しない正例」は維持必須です。

観点 6について、plan 本文に anomaly verifier や correctness verdict を直接緩める提案はありません。ただし上記 topology-only 案や、trial manifest の exact 2 を無条件に 3..10 へ広げる修正は規律 2 違反になります。修正は必ず verified receipt 条件付きに限定する必要があります。

## 総括

must-fix は **7 件**です。

最大の懸念は、plan が数えていない `trial_registry` の exact G=2 gate により、valid receipt の generation 3 が registered・台帳・certified 系へ到達しない一方、direct `_run_workload` ではその束縛を失う非対称です。C11 改訂も D882/D458 の変更単位を外しており、現プランのままでは発効しません。

NO-GO / WAIT の結論自体は **REAL** です。P6 実装・実 accreditation record が無いだけで合接は閉じ、topology-only v1 で acceptance を開くことは D121/D150/D156 の迂回になります。実装しないことは D841 と矛盾しません。

親が段 4 で裁定すべき択一は次です。

- **推奨: WAIT** — P6 accreditation、P別 evaluator/witness、T-435、C11 改訂の独立裁定、trial registry の receipt-conditioned generation 契約が揃ってから単一変更単位で実装する。
- 非推奨: topology と revision だけを検査する human-only receipt で cap を開く。採るなら D121/D150/D156 を明示 supersede する別裁定が必要です。