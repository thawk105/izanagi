## 検査した範囲

指定された親 brief、段 2 プラン、D1374、D1377、D19、および関連する production source、実 calibration、consumer test を静的検査した。編集・pytest・benchmark は実行していない。

層 3 から pin へ至る実在経路は次のとおり。

`build_report` の検証済み `DecodedCampaignLock`  
→ v2 authority の `environment_contract_sha256`  
→ `resolve_by_contract_sha256(..., expected_env_tag=...)`  
→ `GenerationEntry.contract.calibration_ref`  
→ `{path, sha256}` で pin された calibration

根拠は [layer3_report.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:541)、[campaign_lock.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/campaign_lock.py:84)、[env_contract.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:80)、[env_contract.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:881)。v2 lock の activation tuple も admission 中に真正性検査される [artifact_admission.py:1097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/artifact_admission.py:1097)、[ident.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/ident.py:310)。

## real 所見

1. **実装直後には、目的である非 silo の値は公式材料レポートへ入らない。**

   certified launcher は build flags と `ycsb_silo.exe` を固定している [certify_calibration.sh:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:527)、[certify_calibration.sh:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:536)。プランもこの不足を scope 外として認識している [stage2-plan.md:262](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:262)。

   さらに env contract は既存の legacy silo 2 件しか参照せず [env_contract.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:253)、activation head は g1 のみである [00000001.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract_activations/00000001.json:1)。

   影響: producer の能力と consumer の配線は増えるが、非 silo record の生産、pin、activation がないため、公式レポートの非 silo within-run 値は引き続き `null` になる。

2. **pin 限定案は linux-baremetal の既存値を消す。**

   プランは v2 campaign の within-run 候補を pin された 1 件だけに限定する [stage2-plan.md:90](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:90)。linux-baremetal の pin は skew=0.9 の record だけである [env_contract.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:291)。

   直下には別に skew=0、CV=0.004726... の実 record がある [calibration_t48_skew0_rr50_rmw0.json:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/linux-baremetal/calibration/calibration_t48_skew0_rr50_rmw0.json:3)、[同:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/linux-baremetal/calibration/calibration_t48_skew0_rr50_rmw0.json:66)。

   影響: v2・silo・threads=48・records=1,000,000・skew=0 の campaign は、現在ならこの値に一致するが、プラン後は `no-matching-env-record` へ後退する。D1374 の「記録形式変更で既存値を無効にしない」という理由 [D1374.md:12](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/refs/D1374.md:12) とも衝突する。

3. **提案された共通 fixture は、新しい env 照合を通れない。変異候補 8 は通常実装でも赤になる。**

   現行 fixture は v2 lock の authority を linux-baremetal にする [test_layer3_report.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_layer3_report.py:80) 一方、WAL は `test-env` を使う [test_layer3_report.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_layer3_report.py:476)。新 helper は `expected_env_tag` 不一致を fail closed にする計画である [stage2-plan.md:83](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:83)。

   また候補 8 の既存 test は任意の直下 `within.json` を使う [test_layer3_report.py:2948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_layer3_report.py:2948)。pin 限定後は、この file 自体が unpinned なので legacy 表示まで到達しない。

   影響: 候補 8 は D1374 表示を壊した場合にだけ落ちる試験ではなくなる。共通 `_campaign` を使う多数の既存 report test も、fixture を全面的に整合させない限り floor 処理前に停止する。

4. **非 certify producer を brief から黙示的に除外している。**

   親 brief は producer 全体と、certify・非 certify の両 write path を列挙している [handoff.md:55](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/handoff.md:55)、[handoff.md:73](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/handoff.md:73)。プランは非 certify 経路を genome 不在のまま残す [stage2-plan.md:49](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:49)。実際、この経路は `result_to_dict` を直接書く [cli.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:1064)。

   影響: 非 certify の mocc within-run record は genome 不在のままで、層 3 では legacy silo と解釈され、mocc campaign に一致できない。公式 certified 経路に限定するなら、親 brief 側も明示的に狭める必要がある。

5. **新 schema validator の仕様から `TRACE` 予約名検査が抜けている。**

   `Genome` は `TRACE` を明示的に禁止する [model.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/model.py:49)。consumer の canonical parser もこの API を通す [genome.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/genome.py:132)。しかしプランの stdlib validator と負例集合には `silo|TRACE=0` の拒否がない [stage2-plan.md:113](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:113)、[stage2-plan.md:234](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:234)。

   影響: 列挙された仕様どおりなら、schema・activation 側で受理できるのに layer3 consumer が拒否する genome が生じる。`TRACE` 明示拒否と負例を追加すべきである。

6. **consumer test 一覧は production file 別の閉包として不完全。**

   `cli.py` を内容走査する `test_env_contract.py` [test_env_contract.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_contract.py:97) と、全 calibrator/campaign Python を AST 走査する `test_ccbench_spawn_sites.py` [test_ccbench_spawn_sites.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_ccbench_spawn_sites.py:28) が `cli.py` 欄から抜けている。

   影響: 一覧の参照閉包という主張は不正確。ただし両 test は schema/layer3 側の一覧には現れるため、プランどおり全体を集合として走らせるなら焦点走の実害はない。

## refuted 所見

- **env contract への経路が存在しない、は refuted。** `AdmittedCampaign` 自身には ref がない [artifact_admission.py:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/artifact_admission.py:295) が、`build_report` は byte hash を admission decision と再照合した `DecodedCampaignLock` を持つ [layer3_report.py:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:571)、[layer3_report.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:609)。そこから pin へ到達可能である。

- **採用案でも pegasus の registered 2 件が衝突する、は refuted。** current activation は g1 のみで、pin 1 件だけなら g2 は候補にならない。衝突するのは registered 全 glob の場合だけである。

- **genome field 追加で既存 v2 bytes が必ず失効する、は refuted。** legacy/new の二つの exact shape に限る案は、任意 field の許可ではなく、凍結 2 件を保つための最小互換である。

- **変異候補 1〜7 は概ね帰属可能。** 1 は独立 literal、2 は実体名 `mocc`、3 は receipt のみを変え既存 `nm` stub を発火させない [test_calibrator_certify.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_calibrator_certify.py:391)、4 は現 schema が build argv の文字列 list しか検査しないため新 parser 固有 [schema_v2.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/schema_v2.py:403)、5 は schema unit、6 は実在 g1/g2 bytes、7 は temporary copy の SHA だけを変える。候補 8 だけが real 所見 3 の理由で不成立である。

- **要求外 framework の追加、は refuted。** production file 3 件内の局所 helper、二つの exact schema shape、既存 resolver 利用に留まり、新 module、registry、台帳、activation は追加していない。

- **T-2135 が必須 blocker、は refuted。** この checkout では mocc space は既に登録されている [genome.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/genome.py:87)、[genome.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/genome.py:108)。T-2137 の between-run 4 field 拡張も、D19 上の within-run 接続には不要である。

## 目的が果たされるか

**果たされない。**

プラン適用後の現データでの結果は次のとおり。

| 組合せ | プラン後の within-run |
|---|---|
| pegasus v2 g1、silo、48 threads、1M records、skew=0.9/rr50/rmw0 | g1 の CV `0.011705837968885854`、basis=`genome-absent-legacy-record` |
| pegasus v2 g1、非 silo | g1 は legacy silo 扱いなので `no-matching-env-record` |
| pegasus v1 | 直下 within-run が 0 件なので `no-matching-env-record` |
| pegasus g2 | current activation 上で never-active のため resolver が拒否 |
| linux-baremetal v2 g1、skew=0.9 | pin の CV `0.02280630204206476` |
| linux-baremetal v2 g1、skew=0 | pin 限定のため、実在 CV `0.004726195977018071` が消えて `no-matching-env-record` |
| linux-baremetal v1 | 直下 2 件を workload で分離し、skew=0 と 0.9 の各値が残る |

公式レポートへ非 silo 値を実際に入れるには、少なくとも次が残る。

1. certified launcher の protocol/flags/target 一般化。
2. 非 silo within-run floor の再取得と genome 付き registered artifact の生産。
3. その artifact を指す env contract generation の登録と、D1377 に沿った activation。
4. その contract hash を authority に持つ v2 campaign の実生産・admission。
5. 当該 campaign からの layer3 report 生成。

## 親 brief への所見

Codex author を 1 本にする判断は妥当である。production 編集は `cli.py`、`schema_v2.py`、`layer3_report.py` の 3 件に収まり、canonical genome の producer/schema/consumer 整合を同時に確認する価値がある。

ただし「同じ記録形式を直接跨ぐから不可分」という理由はやや強すぎる。layer3 は既に genome を解釈している [layer3_report.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:391) ため、producer/schema と pin 接続は file 面では分離可能である。それでも規模が小さく統合 test の比重が高いため、1 本で十分であり、分割必須ではない。

親 brief は「非 silo 値が公式材料へ入る」という目的と、「launcher、再測定、authority 新設は scope 外」という完了範囲を区別して記載すべきである。現状のまま T-2136 完了を目的達成と表現すると過大主張になる。

## 裁定パッケージ候補

1. **consumer は「直下候補を維持し、exact pin 1 件を追加して重複排除」を推奨。** registered 全 glob はせず、pin-only にもしない。これなら pegasus の 2 件衝突を避けつつ、linux-baremetal の既存 skew=0 値を失わない。

2. **T-2136 の完了文言を wiring-ready に限定する。** 非 silo の実値投入は launcher一般化、再測定、generation/activation を伴う後続 task と明記する。

3. **producer scope を明文化する。** certified producer のみを対象にするなら親 brief の「producer」をそう書き換える。非 certify まで対象なら、自己申告でない provenance 経路が別途必要である。

4. **test 計画を補正する。** v2 fixture の authority/env_tag を一致させ、D1374 回帰は実 pin bytesを使う形へ変更する。schema には `TRACE` 予約名負例を追加する。

## 総括

経路は実在し、content-addressed pin は pegasus の registered 2 件衝突を正しく回避できる。しかしプランは、非 silo record を実際に生産・activation しないため目的を直後には達成せず、pin-only 規則で linux-baremetal の既存値も一部消す。実装前に「直下 + exact pin」の併用、fixture 整合、`TRACE` 検査、完了主張の縮小を反映すべきである。