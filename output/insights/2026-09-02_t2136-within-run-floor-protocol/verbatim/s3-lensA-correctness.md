## 検査した範囲

指定された親 brief、段 2 plan、D1374、D1377、D19を全文確認し、リポジトリ内の producer、schema、env contract、campaign lock、WAL、層 3、既存成果物を静的に追跡した。pytest は実行しておらず、作業ツリーも変更していない。

凍結 2 件の実 SHA-256 はファイル名と一致する。

- g1: `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`
- g2: `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9`

content-address pin の主な実体は次のとおり。

- 権威 pin: [env_contract.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:261)、[env_contract.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:274)。g1 の契約 hash は activation record にも固定される。[00000001.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract_activations/00000001.json:1)
- 実 bytes と full SHA の固定試験: [test_env_attestation.py:1297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_attestation.py:1297)、[test_env_contract.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_contract.py:62)、[test_env_contract.py:1192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_contract.py:1192)、[test_s8b_floor_campaign.py:10165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_s8b_floor_campaign.py:10165)、[test_silo_ladder_rung1_evidence.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_silo_ladder_rung1_evidence.py:70)
- nodeid・操作 key pin: [acceptance_duration_ledger.json:8109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/acceptance_duration_ledger.json:8109)、[acceptance_duration_ledger.json:16539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/acceptance_duration_ledger.json:16539)
- 文書 pin: [b10-backoff-shape-preregistration.md:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/b10-backoff-shape-preregistration.md:213)、[decisions.md:10556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/decisions.md:10556)、[pegasus-runbook.md:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/pegasus-runbook.md:778)、[env-contract-activation-prerequisites.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/env-contract-activation-prerequisites.md:43)、[phase3-8b-restart-runbook.md:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/phase3-8b-restart-runbook.md:94)、[failures.md:4125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/failures.md:4125)
- 派生成果物 pin: [backoff profile:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/profile/backoff_profile_t48_skew0p9_rr50.json:12)、[silo ladder:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:11)、[gap receipt:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/gap-result-receipt.json:19)、4 組の `t419-probe-causality/*/{manifest,result}.json`、[g1 final receipt:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/calibration/attempts/0_867876.nqsv/final-receipt.json:8)、[g2 self comparison:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/calibration/attempts/0_892707.nqsv/published-self-comparison.json:2)
- path 以外の契約 hash pin: g2 の `1346c20b...` は [t810_preregistration.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/t810_preregistration.py:23) と [pegasus-node-variance-protocol.md:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/pegasus-node-variance-protocol.md:110) にも固定される。

## real 所見

1. **新しい層 3 接続は、既知の self-inconsistent な g1 を新規受理する。**

   計画は active な g1 pin を選ぶことを明記している。[stage2-plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:76) 一方、g1 は自分の effective-clock 述語を通らない既知例外である。[test_env_contract.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_contract.py:62)、[test_env_contract.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_contract.py:889)、[decisions.md:22342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/decisions.md:22342) `resolve_by_contract_sha256()` が使う通常検証は schema・hash・quality を見るだけで self-consistency を再検査しない。[env_contract.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:601)

   影響: 新しい v2 Pegasus silo campaign の balanced 条件で、現在の `no-matching-env-record` が g1 の `cv=0.011705837968885854` を持つ `env-record` へ変わる。[g1 calibration:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1577)

2. **acquisition receipt は calibrator 境界では caller の自己申告であり、build argv と binary の因果関係を証明していない。**

   `--receipt-json` は caller が指定でき、単に JSON として読む。[cli.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:154)、[cli.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:716) 現行検査は receipt 内 SHA と手渡し binary の SHA が同じことしか確認せず、記録された argv がその binary を生成したこと、`-B` と `--build` と binary path が同じ build tree であることを確認しない。[cli.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:617) 公式 shell が正しく build して receipt を作る経路は実在するが、calibrator はその経路から来た receipt であることを認証しない。[certify_calibration.sh:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:527)、[certify_calibration.sh:628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:628)

   影響: 任意の trace-disabled binary に、その SHA と別の protocol・flags を記した receipt を対応させると、新成果物がそれを `canonical-floor-genome` という確認済みの根拠で表示しうる。これは D1374 の「検査していないことを検査したと読ませない」と同型である。[D1374.md:9](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/refs/D1374.md:9)

3. **計画の genome 導出規則は親の 4 軸 canonical genome と矛盾し、完全な軸集合も検査しない。**

   計画は TRACE 以外の全 `CCBENCH_*` を回収し、期待値にも `BACKOFF_FIXED=-1` を含める。[stage2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:43)、[stage2-plan.md:216](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:216) しかし `SILO_SPACE` の軸は `BACK_OFF`、2 種の no-wait、`WAL` の 4 件だけである。[genome.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/genome.py:74) `Genome.canonical()` 自体は未知・不足 flags を拒否しない。[model.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/model.py:46)

   影響: 新規 artifact の genome、bytes SHA、content-address path が親の主張した 4 軸値と異なる。さらに軸不足や protocol 非対応の receipt も syntactic canonical として通り、将来の exact genome 照合を汚す。

4. **非 certify の新規 record を今後も「歴史的 legacy」として silo に仮定する穴が残る。**

   計画は非 certify 経路へ genome を書かず、従来の legacy 扱いに残す。[stage2-plan.md:51](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:51) CLI は任意の `ycsb_*.exe` を受け、直下へ genome 無しで書く。[cli.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:132)、[cli.py:1077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:1077) 層 3 は genome が無い全 within-run record を、作成時期に関係なく silo とする。[layer3_report.py:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:399)

   影響: 変更後に新規作成された mocc 等の非 certify record が、条件一致時には silo の `env-record` 値として受理されうる。D1374 の grandfathering 対象を「歴史的 record」へ限定できていない。

5. **親の pin 閉包は実際には閉じていない。**

   親の列挙は [handoff.md:69](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/handoff.md:69) の 7 面だが、上記の `env_contract_activations`、S8b、silo ladder、activation prerequisite、restart runbook、failure、派生成果物、契約 hash pin が欠落している。

   影響: 凍結 bytes 自体は今回変わらないが、その保全回帰を親の列挙だけで実行すると、歴史 evidence identity、契約 hash、派生成果物内の参照切断を見落とす。

## refuted 所見

- **凍結 2 件を変更する提案ではない。** 編集対象から既存 artifact、env contract、activation JSONを明示的に外している。[stage2-plan.md:168](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:168) 新規 publish も artifact bytes の digest から別名を作り、create-only rename を使う。[cli.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:925)

- **既存 2 件が schema 赤になる問題は、計画どおり二つの exact shape を実装すれば成立しない。** 現状 `_exact` は完全一致である。[schema_v2.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/schema_v2.py:43) 計画は旧 `_TOP_KEYS` と `_TOP_KEYS | {"genome"}` だけを受理し、既存 bytes の旧 shape を維持する。[stage2-plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2136-within-run-floor-protocol/artifacts/t2136-within-run-floor-protocol/stage2-plan.md:107) 集合としては「既存の有効集合」に「canonical genome を持つ新 shape」を加えるだけで、未知 field や既存必須 field を optional 化しない。

- **schema_version は上げないため、D1284 の世代付き移行を直接新設する案ではない。** D1284 は世代付き移行を段 0 権限束へ残す裁定である。[decisions.md:41454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/docs/decisions.md:41454) ただし同一 `calibration/v2` に二形状を持たせてよいかは、下記の裁定候補に残る。

- **規律 1・4・D19 の直接変更はない。** `nm` 検査は残り、receipt の TRACE=0 検査は追加方向である。[cli.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:187) records 選択、既定 sweep、CV、between-run の用途には触れない。性能 build と verifier build の配線も変更しない。

- **現在 `env-record` 値を持つ campaign が値を失う経路は見つからなかった。** 実在する該当 report は balanced 2 件、read-heavy 2 件、write-heavy 2 件で、全て linux-baremetal の schema 無し v1 lock である。例として [balanced report:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/layer3_report.json:1)。schema 無し lock は v1 と解釈される。[campaign_lock.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/campaign_lock.py:334) 計画は v1 の直下走査を維持するため、これらの within-run・between-run 値は維持される。

- **層 3 の集合変化は次のとおり。**

  - 新たに受理: authority 付き v2 campaign について、ever-active contract が pin した 1 件が protocol、records、threads、workload に完全一致する within-run record。現在の具体例は Pegasus g1 の silo、1M、48 thread、rratio 50、skew 0.9。
  - 新たに候補外: authority 付き v2 campaign の直下にある、pin されていない within-run record。
  - 新たに hard reject: pin の repo escape、env 不一致、SHA 不一致、unknown・never-active contract。
  - 不変: v1 の直下走査、between-run の直下走査、複数一致 fail-closed、D1374 の legacy 表示。
  - したがって集合は拡大するが、「registered 全件」ではなく active contract 1 件に限定される。無制限な glob 緩和は成立しない。

- `test_pegasus_tools.py` は凍結 digest pin ではない。任意の `calibration-*.json` を `next(glob)` で読むだけである。[test_pegasus_tools.py:712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_pegasus_tools.py:712) schema consumer としては関係するが、親閉包中の「bytes pin」という分類は不正確である。

## 親 brief への所見

- **4 軸 canonical genome:** 今ある 2 件を `SPACES["silo"].axes` へ射影する限り、親の  
  `silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`  
  は正しい。TRACE と BACKOFF_FIXED はその射影から除外される。一方、build argv だけから一般の canonical genome が自動的かつ一意に決まるという一般化は誤りである。軸集合の照合が別途必要で、`SPACES` 自体も現在は silo と mocc しか持たない。[genome.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/genome.py:108)

- **既存 2 件の 4 field match:** 正しい。両者は同じ target、4 軸、records=1M、threads=48、workload を持つ。[g1:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:20)、[g2:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:20) これは現在の 2 件についてだけ成立し、将来の record には一般化できない。

- **Pegasus calibration 直下の within-run 0 件:** 正しい。直下 3 件は A2 cost 2 件と between-run 1 件だけで、within-run block はない。[between-run file:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json:2) これは現在の Pegasus だけの事実であり、linux-baremetal、他 env_tag、将来の出力には一般化できない。

- **一般化限界:** 現行 env registry は linux-baremetal と Pegasusだけで、env ごとに calibration ref は 1 件である。[env_contract.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:291) 新しい protocol・workload の record を作るだけでは層 3 に接続されず、別の contract generation と activation が必要になる。

## 裁定パッケージ候補

- **receipt を確認済み事実としてよい条件:** caller 提供 JSON を process provenance と認定するか、producer 管理 build・実行済み build tree・binary を機械的に結ぶ追加証明を要求するか。推奨は後者。現計画のままなら表示 basis を `receipt-declared-build-argv` 程度へ弱め、`canonical-floor-genome` と呼ばない。

- **既知 self-inconsistent g1 の新規 consumer 利用:** active だから層 3 に新規投入してよいか、healthy だが never-active の g2 が発効するまで `no-matching-env-record` を維持するか。これは D1377 と段 0 activation の裁定面であり、本 wave 内で暗黙に決めるべきでない。

- **同一 `calibration/v2` の二形状:** backward-compatible な exact union として許すか、schema 世代を必要とみなして D1284 の段 0 権限束へ送るか。

- **非 certify の将来 record:** 新規 genome 不在 record を D1374 の歴史 allowlistへ混ぜ続けるか、既存 content hash だけを grandfather し、新規 genome 不在 record は層 3 で拒否するか。推奨は後者。

- **将来の multi-protocol registry:** env 単位 1 pin では protocol・workload 別 floor を同時に権威化できない。D1377 の activation 手続と合わせた別設計が必要で、本 wave の scope 外とするのが妥当。

## 総括

凍結 bytes の不変更、旧 schema の再検証、v1 campaign の既存値保全、trace・records・between-run 規律の維持は成立する。

ただし現プランは、このまま author へ渡せる状態ではない。少なくとも、既知 self-inconsistent g1 の新規受理、receipt の自己申告境界、`SPACES` と矛盾する genome 導出、非 certify 新規 record の誤った legacy 化、pin 閉包の不足を解消または裁定する必要がある。