```text
## 判定 (NO-GO)

現 brief / plan のままの g2 単独活性化は認められない。

停止理由は、(1) g1 の自己不整合を historical resolver が検証済み扱いする、(2) g1/g2 混在 trial を許す結合欠落、(3) 既裁定の上位 authority-bundle / lockstep と commit 順序・実行主体が衝突する、(4) protocol path seam が caller-selected authority になりうる、の 4 件である。

### A-01 / g1 の自己不整合が historical 経路で検証済み扱いになる

主張:
g2 活性化後も g1 は `ever_active` に残り、`resolve_by_contract_sha256` から `_ensure_calibration_verified` を通る。しかし loader は clock self-pass を再計算せず、`quality.status == accepted` だけで受理する。g1 の 3080.935 MHz 外れ値は残ったままである。

証拠:
- `orchestrator/campaign/env_contract.py:486-516`
- `orchestrator/campaign/env_contract.py:601-612`
- `orchestrator/campaign/env_contract.py:671-703`
- `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484,1599-1601`
- `orchestrator/tests/test_env_contract.py:846-869`
- `s2-plan.md:102-116,219-221`

成果物影響: g1 歴史成果物を generic な「較正検証済み」として受理しつつ、current `REGISTRY` だけを走査するテストは「例外なし」を偽装する。

推奨:
`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を単純に空にしない。current-active の self-pass と historical grandfather を別型・別 gate にし、historical g1 を live 入力へ流せないことを固定する。全 `ever_active` entry を走査する検査を置き、g1 の扱いは新 D で明示裁定する。

### A-02 / g1 origin と g2 campaign を混在できる

主張:
活性化後は g1/g2 がともに `ever_active` になる。source closure は origin 側 hash が単独で解決できれば受理し、campaign は別に current g2 を選ぶ。origin-binding issuer は `prepared_origin` の hash を同じ origin 自身と比較するだけで、`prepared_campaign.campaign.bound_environment_contract` との一致を検査しない。

証拠:
- `orchestrator/campaign/env_contract_activation.py:360-394,417-422`
- `orchestrator/campaign/reflux_source_closure.py:471-508`
- `orchestrator/campaign/p3_autonomous_workload_trial.py:849-885`
- `orchestrator/campaign/reflux_origin_binding.py:530-568`
- `orchestrator/campaign/autonomous_trial_completeness.py:856-911,942-963`
- `orchestrator/campaign/model.py:73-84`
- production 発行は現状拒否され、fixture/non-certifying に限定: `reflux_origin_binding.py:569-575`

成果物影響: fixture trial ledger / report で g1 authority-origin と g2 campaign、または逆の世代混在が新たに受理される。

推奨:
issuer と completeness の双方で、origin の `environment_contract_sha256` を campaign の bound contract および campaign.lock authority と exact 比較する。g1-origin/g2-campaign と逆向きの負例を追加する。

### A-03 / 活性化単独は既裁定の上位 authority-bundle に反する

主張:
2026-08-10 の裁定は環境活性化と freeze 世代を上位束で lockstep にし、承認 A と発効 X を人間手番に固定している。g2 は `registered-inactive` のままと明記されている。8月16日裁定は「同一 wave / chain で世代移行を実装」としたが、この actor、lockstep、上位束を明示的に supersede していない。

証拠:
- `docs/decisions.md:12507-12530`
- `docs/calibration-freeze-authority-bundle-design.md:10-28,70-72,76-97,114-125`
- 同 `:154-179,211-220`
- `docs/archive/worklog-phase3-0810-367-368.md:407-414`
- `ruling.md:92-94,127-128`
- Codex author の単独 activation: `brief.md:101-105`
- activation 後に human protocol を置く順序: `s2-plan.md:245-260`

成果物影響: 人間が承認していない environment g2 × freeze g1 の直積を production authority として一時的に生成する。

推奨:
新裁定が T-657/D272 を破棄するのか明示裁定を取る。破棄しないなら、上位 E/G_f/A_f/Q/A/X を実装し、activation record・head literal・上位 pointer を人間 X の exact commit として lockstep 発効する。

### A-04 / g2 の clock self-pass は再計算できるが、取得 provenance は成果物だけでは立証できない

主張:
g2 の file SHA、48 標本がすべて 2101 MHzであること、2% 帯への self-pass は成果物から再計算できた。CLI に early、late、policy equality、publish 後再読の gate があることも確認できた。一方、host、qstat assignment、source head、`pinned_clean` は artifact 内の自己申告であり、runtime loader は job-result、publish receipt、published-self-comparison を束縛しない。

証拠:
- clock 標本: `calibration-94a4b79fa31bba3c.json:1440-1465`
- host / quality: 同 `:1570-1575,1599-1601`
- acquisition receipt: 同 `:2-55`
- CLI gate: `orchestrator/calibrator/cli.py:536-578,719-731,762-810,835-845`
- schema の構造・自己申告検査: `orchestrator/calibrator/schema_v2.py:345-482,504-544`
- runtime loader の検査範囲: `orchestrator/campaign/calibration_verify.py:81-142`
- source acquisition proof 非束縛の既決定: `docs/decisions.md:9310-9315`

成果物影響: D143(b) の clock 条件は支持されるが、「この artifact 単独で正規 active g2 を証明できる」という主張までは支持されない。

推奨:
上位 Q/A が job-result、source witness、publish receipt、published-self-comparison の対象同一性を束縛するか、source acquisition proof の残余を人間が明示受容する。`accepted` 文字列だけを activation 根拠にしない。

### A-05 / 親の対案 (X) の「移行前は何も走らない」は偽

主張:
g1 calibration の自己比較失敗は runtime の必然的失敗ではない。runtime predicate は期待列の中央値を中心に観測列だけを検査し、期待列自身の 3080.935 を検査しない。method 名も非空性しか見ない。g2 取得 profile を observed 側へ投影し g1 expected と静的再計算したところ、21 comparison は全件 pass だった。

さらに g1 active 期間中、Pegasus 計算ノードで attestation を要求しない非 study probe が実際に完走し、両 build が returncode 0 になっている。

証拠:
- runtime clock predicate: `orchestrator/campaign/execution_guard.py:295-337,340-445`
- current rotating-min probe: `orchestrator/campaign/env_attestation.py:35-42,639-682`
- method を判定に使わない issuer: 同 `:933-982`
- g1 outlier: `calibration-753f535a8d024727.json:1442,1484`
- 両世代 2101 MHz の既決定: `docs/decisions.md:14821-14827`
- 実 Pegasus 成功経路: `docs/archive/worklog-phase3-0809-335.md:3-8`
- 成果物: `output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/receipt.json:286-301,825-851`

成果物影響: 「活性化は能力を失わない厳密な改善」という (X) の前提が崩れる。

推奨:
(X) を採用しない。現行 code で certified campaign が常に失敗するとの主張には、新しい実機走が必要である。本レビューは campaign E2E 成功を実走確認していない。

### A-06 / 活性化で閉じる経路と、すでに閉じている経路が混同されている

主張:
次の三つは current-contract gate が g1一致からg2不一致へ変わるため、新たに閉じる。
- fixed floor static admission: `certified_writer_admission.py:177-214`
- ratified live launch: `s8b_ratified_freeze.py:2802-2813,3272-3279`
- holdout candidate producer: `s8b_holdout_freeze.py:1275-1303`

一方、次は活性化前から別理由で閉じている。
- silo current binding: snapshot の module hash が現在 bytes と異なり、独自に method exact 一致も要求する。`silo_ladder_rung1.json:63-68`、`silo_ladder_rung1.py:1956-2012,3541-3572`
- prediction seal: committed protocol は `d706…`、現 approved pin は `511c…`。`output/s8b-freeze/floor_protocol.json:1`、`s8b_approved.py:65-67`、`s8b_prediction_runner.py:1438-1451,1542-1549`
- live resume: tracked campaign.lock 30 件はすべて legacy で、certified lane では既に read-only。`ident.py:327-373`

historical ratified verificationは g1 のまま生存する: `s8b_ratified_freeze.py:2816-2833,3282-3292`。

成果物影響: 活性化後に閉じるのは floor 発行経路 1 本だけではなく、少なくとも三つの current gate である。一方、plan は silo/prediction/resume の喪失を過大帰属している。

推奨:
各経路を「移行で新規拒否」「既存拒否」「historical read-only 生存」に分け、replacement の positive fixture が揃うまで activation を発効しない。

### A-07 / versioned protocol seam は caller-selected path にすると受理集合を広げる

主張:
現行の固定 path は暗黙の trust root である。plan の receipt v2 が `protocol_path` と hash を選び、admission がその commit blobを確認するだけなら、検証対象を submitter が選べる。Git blob/hash 一致は「その protocol が人間承認済み」であることを証明しない。

さらに共通 validator は `ccbench_pin`、`stock_configuration`、`master_seed`、freeze path/hash を非空・形式だけで受理する。approved 値を焼くのは builder 側であり、admission は builder 由来性を再計算していない。

証拠:
- plan の caller-provided path/hash: `s2-plan.md:206-217`
- 現行固定 path: `orchestrator/campaign/certified_writer_admission.py:206-210`
- source blob 検査: 同 `:118-128`
- validator の自由 field: `orchestrator/campaign/s8b_floor_contract.py:140-168,194-227`
- approved builder: `orchestrator/campaign/s8b_floor_campaign.py:621-659`

成果物影響: safe な committed path であっても、未承認の別 protocol を floor admission 対象として選択できる受理拡大になる。

推奨:
path/hash/source commit は receipt で選ばせず、human-approved authority-bundle の generation record から resolver が決定する。receipt はその値を反復するだけにする。v2 seam は dormant に land し、承認済み束が無い間は v2 receipt を全拒否する。

### A-08 / テスト変更のうち一件は「緑にするための検査対象縮小」である

主張:
xfail 化、tolerance 緩和、3080 synthetic 負例の削除は plan にない。g2 never-active 負例を positive に反転し、別 synthetic generation で never-active 拒否を維持する方針も妥当である。

ただし self-consistency test は `ec.REGISTRY`、すなわち active view だけを走査する。活性化によって g1 が loop から消えるため、例外集合の空化は historical resolver の受理対象を検査から落として緑にする変更である。

証拠:
- 現 test: `orchestrator/tests/test_env_contract.py:839-881`
- plan の空化: `s2-plan.md:98-116`
- active view: `orchestrator/campaign/env_contract.py:615-625`
- historical resolver: 同 `:671-703`
- plan の他 negative 維持: `s2-plan.md:270-291`

成果物影響: current g2 の正例は守るが、ever-active g1 の実在負例と g1/g2 mixed vector がテスト網から脱落する。

推奨:
self-consistency の走査領域を active と ever-active に分ける。g1 historical exception、mixed trial、alternate protocol path を独立負例にする。`:885` の冗長 count assertion 削除自体は問題ない。

## 親 brief の誤り

1. 前提実測 1: lower-level `GENERATIONS` / activation chain の実在は正しい。しかし「世代機構は実装済み、移行実行だけ」は、未完成の上位 authority-bundle と protocol generation authority を無視した一般化である。`brief.md:21-27`、`docs/calibration-freeze-authority-bundle-design.md:1-28`。
2. 前提実測 2: g2 が registered-inactive なのは正しい。ただし `quality.status=accepted` を official activation 根拠へ一般化できない。`brief.md:28-31`。
3. 前提実測 3: g2 self-pass / g1 self-fail の算術は正しい。そこから「g1 runtime は必ず失敗」を導くのは誤り。runtime は expected 自身の外れ値を検査しない。`brief.md:32-35`、`execution_guard.py:324-337`。
4. 前提実測 4: D143 の全要素 acquisition gate は確かに land 済み。しかし「未実施は activation だけ」は loader、source proof、上位束を落としている。`brief.md:36-39`。
5. 前提実測 5: 一時変異は lower loader の遷移だけを支持する。human X、lockstep、mixed-generation consumer、downstream replacement は検証していない。`brief.md:40-43`。
6. 前提実測 6: g2 後の旧 floor live 拒否は正しい。この実測は activation 単独の安全性ではなく、replacement authority を先に要することを示す。`brief.md:44-51`。
7. 前提実測 7: D143「裁定待ち」という docs は stale である。ただし更新先は「g2 active」ではなく「D143 解決済み、T-657 bundle 未完成」でなければならない。`brief.md:52-53`。
8. 前提実測 8: 焦点走の赤 9 件は指定 3 test file 内の結果であり、blast radius 全体を証明しない。trial-origin mix、authority-bundle、current consumer の喪失を検出していない。`brief.md:54-69`。
9. 一時変異の復元状態は現 status と整合したが、正しさ主張の根拠にはならない。`brief.md:70-71`。

## プランの誤り

- P2 は不成立。g1 は active view から消えるだけで、ever-active resolver の受理対象からは消えない。`s2-plan.md:219-221`。
- P1 の「seam を activation より前に」は正しいが、receipt が path authority を持つ設計は不十分。既存上位束から path/hash を解決すべきである。
- §7 の seam → activation → human artifact は lockstep と逆で、Codex activation commit は human X の actor 契約にも反する。`s2-plan.md:245-262`。
- 「production 編集は head 定数 2 件だけ」は lower authority の説明に限れば正しいが、本 wave の sanctioned transition 全体としては偽。`s2-plan.md:74-96`。
- §5 は新規喪失と既存 drift を混同している。floor、ratified launch、holdout gate は新規拒否だが、silo と prediction は既に拒否状態である。
- §8 は g1/g2 mixed trial、ever-active g1 self-fail、caller-selected alternate protocol の負例を欠く。
- P4 の狭い主張、すなわち「D143 の全要素 acquisition gate を再実装しない」は成立する。

## 攻撃したが崩せなかったもの (反証できた項目を明記する)

- [崩せず] CLI の acquisition gate は early、late、policy equality、published bytes reread の四箇所に実在し、全要素 predicate を共有している。
- [崩せず] g2 artifact の file SHA は content address と一致し、48 clock samples は全件 2101 MHz で self-pass する。
- [崩せず] 一つの WAL 内では campaign.lock の exact contract hash と各 COMMIT が一致必須であり、g1/g2 COMMIT 混在は拒否される。`orchestrator/campaign/wal.py:1040-1085`。
- [崩せず] floor と ratified freeze の historical/current resolver 分離は、旧成果物を read-only 再検証しつつ live predecessor を拒否する。
- [崩せず] plan は xfail、tolerance 緩和、synthetic 3080 負例削除を提案していない。
- [崩せず] Pegasus login node は正規 campaign の反例にならない。site 分類と measurement admission が login を拒否する。`site_policy.py:30-46`、`p3_s4_loop_trigger_gating.py:319-330`。
- [反証] (X) の「g1 active では何も走らない」は、実 Pegasus 非 study probe の成功と、g2 acquisition profile が g1 の全21比較を通る静的再計算で反証した。
- [反証] brief P2 の「g1 の既知例外対象が消える」は historical resolver の存在により反証した。
- [反証] 「移行機構は完成し activation だけ」は、未完成の上位 bundle と path authority により反証した。
- [反証] silo/prediction/resume の拒否を activation の新規影響とする一般化は、既存 drift / legacy 状態により反証した。
```

## 総括

- 現 brief / plan は NO-GO である。
- D143(b) の全要素 clock gate と g2 の self-pass 自体は確認できた。
- g1 historical calibration を generic verified とする穴が残る。
- g1 origin と g2 campaign の混在受理も閉じていない。
- 親の対案 (X) の「移行前は何も走らない」は成立しない。
- seam-first は必要だが、protocol path を receipt に選ばせてはならない。
- T-657/D272 の human lockstep authority-bundle を先に整合させる必要がある。
- read-only 静的検査のみで、pytest、build、実機 campaign、Web 検索は実行していない。