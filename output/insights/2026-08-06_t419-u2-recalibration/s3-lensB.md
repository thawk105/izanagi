レビュー時点は `HEAD=18149bcf`、worktree は clean です。Pegasus login node 上の read-only レビューであり、pytest・build・実測は一切行っていません。緑は主張しません。

## 所見

### SCOPE-01 — D176 は「publish」を拒否しない。親は活性化不能を取得不能へ拡張し、確定済み所有を縮小している

根拠:

- 確定済み所有は accepted publish receipt、独立 self-comparison、例外集合空化、凍結 bytes と pin 更新までです（[stage1-brief.md:6–13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:6)）。一方、親は後半を次 wave へ送っています（[stage1-brief.md:17–27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:17)）。
- `validate_generations()` が拒否するのは `GENERATIONS` の複数世代です（[env_contract.py:316–326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_contract.py:316)）。D176 自身も fuse を「source bootstrap の防壁」であって runtime 活性化権限ではないと限定しています（[decisions.md:8691–8698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:8691)）。
- 正規 CLI の content-addressed publish は `registered/calibration-<sha>.json` を作るだけで、`env_contract` や `validate_generations()` を呼びません（[cli.py:633–659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:633)）。
- したがって「registered directory への accepted publish」と「`REGISTRY` current への g2 活性化」は別です。T-529 が必要なのは後者、pin switch、例外集合空化、loader self-pass です。この部分は反証できませんでした。
- g1 の同一 path 上書きは D176 が明示的に禁じています（[decisions.md:8687–8689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:8687)）。

自己判定: **real**

成果物影響: acquisition-only artifact は作れても、現計画を `[T-419] U-2 完了` と扱えば、固定されたユーザー所有の未達を完了扱いする。

推奨対応: **裁定へ返す。** 「T-529 を同 wave に含めて U-2 を完了」または「取得 prerequisite wave へ明示改名し、U-2 完了を主張しない」の二択にする。

---

### SCOPE-02 — T-443/T-444 の編集禁止は技術的制約ではなく、親 prompt が作った自己矛盾である

根拠:

- T-443/T-444 は同じ再発行サイクルへの同梱が確定済みです（[stage1-brief.md:10–13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:10)）。
- ところが段2 prompt が `certify_calibration.sh` と `submit_certify.sh` を新たに編集禁止としています（[plan-prompt.txt:13–20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-prompt.txt:13)）。この禁止は brief の不変条件にはありません。
- certification の CMake argv は source projection 3本も `FETCHCONTENT_FULLY_DISCONNECTED` も持ちません（[certify_calibration.sh:486–507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:486)）。receipt producer も source heads/cache/helperを記録しません（[certify_calibration.sh:553–637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:553)）。
- verified cache の取得・hydrate 機構自体は既にあります（[tools/pegasus/README.md:181–210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/README.md:181)）。不足は certification への結線と receipt 束縛です。
- プランはこの自己制約を理由に T-443/T-444 と certify を実装外へ送っています（[plan-out.md:307–314](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:307)）。

自己判定: **real**

成果物影響: 現 script で accepted になった artifact は source projection/proof chain を欠いたまま `quality.status=accepted` を名乗り、T-443/T-444 完了物と誤読されうる。

推奨対応: **scope 内で直す。** certification script、submit receipt、AcquisitionReceipt schema/writer の限定編集を許可する。禁止維持なら T-443/T-444「同梱済み」とは書かず裁定へ返す。

---

### CERT-01 — 過去 build が「compute-node Git transport」で成功したとの断定は実測を越えている。ただし現状の production certify NO-GO は反証できない

根拠:

実測で言えるのは次までです。

- job は bnode011・48 CPU でした（[qstat-f.stdout:50–61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/qstat-f.stdout:50)）。
- source worktree と build dir は fresh `/scr` です（[certify_calibration.sh:486–507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:486)）。
- configure は成功し（[configure.stdout:37–41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/configure.stdout:37)）、build は `_deps/mimalloc-build` と masstree を使っています（[build.stdout:1–22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/build.stdout:1)）。
- CMake は GitHub の masstree/mimalloc/googletest を宣言します（[ThirdParty.cmake:35–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/external/ccbench/cmake/ThirdParty.cmake:35)、[ThirdParty.cmake:106–136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/external/ccbench/cmake/ThirdParty.cmake:106)）。
- AcquisitionReceipt に proxy、Git config、CMake preload、第三者 source path/head はありません（[acquisition-receipt.json:1–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/calibration/job-staging/0:867876.nqsv/acquisition-receipt.json:1)）。

したがって fresh job-local `_deps` の事前 warm は否定できますが、live Git transport、proxy、URL rewrite、共有 source、CMake preloadのどれかは確定不能です。プランは「Git transport が必要だった」と書いた直後に「未記録の共有 source もありうる」としており内部矛盾しています（[plan-out.md:234–240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:234)）。runbook も Claude CLI の proxy 実測を Git/CMakeへ一般化するなと明記します（[pegasus-runbook.md:588–608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/pegasus-runbook.md:588)）。

今 certify した場合の予測は条件付きです。

- liveness 出力が同 worktree に未 stage なら、qsub 前に dirty gate で確定的に失敗します（[submit_certify.sh:71–79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:71)）。
- clean tree から投入した configure の成功/失敗は証拠不足で予測不能です。
- build 後の α profile が帯外なら、現 HEAD は benchmark 実行後に self-pass で rejected にし、publishしません（[cli.py:590–631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:590)）。
- 全 gate が通れば accepted artifact は publishされますが、T-443/T-444 proof は欠け、活性化・pin更新・例外空化は起きません。

「登録できないから取得は無駄」は反証できます。accepted inert artifact はT-529前でも取得証拠になります。一方「機会があるうちに取る」は、現 script が証拠不足 artifact を accepted として publishするため、production completion の根拠には使えません。

自己判定: **real**（configure 成功確率のみ **speculative**）

成果物影響: 現 certify は失敗、2時間後の正当な rejection、または source-proof 欠落 accepted のいずれかであり、どれも `[T-419] U-2 完了` を保証しない。

推奨対応: **scope 内で直す。** T-443/T-444を先に結線してから certify。現状で取るなら明示的な non-certifying diagnostic とし、正規 publish経路を使わない。

---

### LIVE-01 — 1 node・1時刻・1回の pass は後続 certify も「計算ノード一般」も許可しない

根拠:

- プランは別 PBS で `ea.probe()` を1回実行し、その後の certify 投入条件にします（[plan-out.md:110–178](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:110)）。
- Pegasus は allocation ごとに node が変わり、exclusive submit も保証されません（[pegasus-runbook.md:520–527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/pegasus-runbook.md:520)）。別 job の pass は後続 job の host、boot、cpuset、load、時刻を束縛しません。
- `composite_competing_probe()` が検査するのは canary の可視性と他の `ycsb_.*\.exe` だけです（[runner.py:221–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/runner.py:221)）。「他プロセスがいない」証明にはなりません。
- D181 は異なるプロトコルの9/9を本番手続きの妥当性根拠に使うことを明示的に禁止しています（[decisions.md:8893–8906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:8893)）。1/1を別 allocationへ外挿するのも同じ種類の射程超過です。

言える範囲は次です。

- 1回 pass: その job・host・boot・cpuset・時刻で、取得された1 profileが帯内だった。
- certify admission: 同じ allocation 内、buildより前の直近 preflight として走らせ、その job identityへ束縛する。
- sampled-population の failure rate: 独立 allocation、node/time/load strata、同じ source/profileを事前規定して測る。失敗0件の片側95%上限は `1 - 0.05^(1/n)`。`p<5%` を言うには最低59独立 job、`p<1%` なら299 jobが必要です。それでも全bnode・将来時刻の普遍命題にはなりません。
- out_of_band が1件: 全位置帯内述語により、その exact profile/job は不合格であり、「常に帯内」という普遍主張は反証されます。ただし α 全般や全計算ノードが失敗するとは言えません。

自己判定: **real**（59/299は独立Bernoulliを仮定した統計的例示）

成果物影響: 別 job の1/1 passを certify 許可証にすると、帯外の本番 jobを誤って開始し、2時間を費やした後に rejected となりうる。

推奨対応: **scope 内で直す。** livenessを certify jobの同一allocation・同一source receipt内の最初の gateへ統合する。別driverは局所診断に限定する。

---

### OPS-01 — 新出力先は freeze/lock とは直接衝突しないが、guard、dirty gate、output snapshot、file-set sealと衝突する

根拠:

- `FROZEN_MANIFEST` は23 exact pathのみで、新しい `output/env/.../t419-alpha-liveness` は直接対象外です（[test_frozen_artifacts.py:38–114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_frozen_artifacts.py:38)）。ここへの直接衝突は反証できました。逆に無裁定でmanifestへ追加すると独立keyset検査に当たります。
- campaign lock防護は `output/campaigns` と `output/exploration/campaigns` に限定されます（[guard_bash.py:76–102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/hooks/guard_bash.py:76)）。新pathとの直接衝突はありません。
- 新しい `.pbs` は execution inventory に自動出現しますが、guard registryと固定期待値へ追加する計画がありません（[test_hooks.py:1140–1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_hooks.py:1140)、[test_hooks.py:1223–1246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_hooks.py:1223)）。実装すればこの検査は確定的に赤です。
- acceptance中に `output/` が増えると全output snapshot検査を交絡します（[test_s8b_floor_campaign.py:432–446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_s8b_floor_campaign.py:432)）。既発事故はF62/F115です（[failures.md:1405–1422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/failures.md:1405)、[failures.md:2639–2653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/failures.md:2639)）。
- committedであっても新規fileは `clean_scan_digest.repository_files` を変えます（[s8b_floor_campaign.py:1628–1661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/s8b_floor_campaign.py:1628)）。これはF39の既知罠です（[failures.md:828–848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/failures.md:828)）。
- liveness後のuntracked成果物は certify submitter（上記）とlandの完全clean検査（[dev_wave_land.py:785–787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/dev_wave_land.py:785)）を止めます。
- `check_docs.py` が同期するのはrunbook §7.0と`dispatch_compute.py`のtask表だけです（[check_docs.py:1842–1873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/check_docs.py:1842)）。新pathの整合は検査せず、衝突も検出漏れも防ぎません。
- プランはsanctioned submit wrapper、`qsub -v`、repo外 `-o/-e` を規定していません。runbookはこれらを必須とします（[pegasus-runbook.md:620–624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/pegasus-runbook.md:620)、[pegasus-runbook.md:668–684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/pegasus-runbook.md:668)）。

自己判定: **real**

成果物影響: 現順序では certify が dirtyで停止し、並行テストは偽赤、guard inventory検査も赤になり、既存file-set sealもdriftする。

推奨対応: **scope 内で直す。** 同一certify jobへの統合を第一候補とする。別jobなら専用submitter、guard registry/test、repo外scheduler出力、source/script hash receipt、acceptanceとの非並行、commit/collect順を明記する。

---

### API-01 — `run_probe.py` の additive mode は互換にできるが、プランはconsumerとidentity閉包を列挙し切っていない

根拠:

現在の呼び出し元は以下です。

- PBS certification bodyから3回（[certify_calibration.sh:340–343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:340)、[certify_calibration.sh:548–551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:548)、[certify_calibration.sh:747–749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:747)）。
- smoke bodyから1回（[smoke_probe.sh:111–117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/smoke_probe.sh:111)）。
- silo ladder driverから1回。その直後にv2 parserへ渡します（[silo_ladder_rung1.py:1932–1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:1932)）。
- exact v2 shape、file/stdout一致、write collisionを固定するテスト群（[test_pegasus_tools.py:774–870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_pegasus_tools.py:774)）。
- hook registryとsilo runtime-module binding（[test_hooks.py:1156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_hooks.py:1156)、[silo_ladder_rung1.py:254–280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:254)）。
- runbookに直接CLI記述はなく、certification suite経由の間接consumerです（[pegasus-runbook.md:556–562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/pegasus-runbook.md:556)）。

現行defaultは `--output` のみで、常に`pegasus-probe-output/v2`を返します（[run_probe.py:30–102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/run_probe.py:30)）。`--alpha-liveness`未指定時をbyte-for-byte同形に保てば、CLI追加自体が既存consumerを壊すとの反証はできませんでした。

ただし次が未処置です。

- `composite_competing_probe()`には有効な`nonce`が必須ですが、提案signatureにnonce生成/注入がありません。
- canaryは全processの単独性を証明しません。
- `run_probe.py`のbytesは既存silo evidenceに旧SHAで束縛されています（[silo_ladder_rung1.json:111–113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:111)）。旧evidenceは変更してはならず、テストも現行bindingとの不一致を歴史として要求しています（[test_silo_ladder_rung1_evidence.py:1239–1240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1239)）。

自己判定: **real**（実際のdefault破壊は実装前なので **speculative**）

成果物影響: 分岐を誤るとcertify/smoke/siloの全probe receiptが壊れ、旧evidenceを新SHAへ貼り替えると虚偽の履歴になる。

推奨対応: **scope 内で直す。** 専用entry pointを新設するのが安全。共有fileを使うならdefault exact回帰、全caller列挙、nonce、runtime-module新旧分類を必須にし、旧evidenceは更新しない。

---

### PIN-01 — 親のpin閉包は「live更新」「歴史保持」「新規再発行」を混同し、凍結contract hashを見落としている

根拠:

親の列挙は [handoff:26–30](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t419-u2-recalibration.md:26) ですが、処置別の正しい閉包は次です。

- **live current更新対象:** `env_contract.py`のg2追加/current activation、`test_env_contract.py`のgeneration hashes・current golden・既知例外集合（[env_contract.py:256–275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_contract.py:256)、[test_env_contract.py:62–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:62)、[test_env_contract.py:267–279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:267)）、runbookのcurrent path。
- **新規versioned発行対象:** 新g2 activation bundle/receipt、g2用floor protocol・seal・current evidence。旧 `floor_protocol.json` は旧contract SHAを直接持ち（[floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/s8b-freeze/floor_protocol.json:1)）、そのbytes自体がFROZEN_MANIFESTにpinされています（[test_frozen_artifacts.py:43–46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_frozen_artifacts.py:43)）。「凍結文書は較正SHAを含まないので動かない」は、calibration_refから導出されるcontract SHAを無視しています。
- **歴史として保持:** 旧calibrationとattempt/job receipts、`docs/failures.md:2243`、silo ladder本体とraw gap receipt、T419 causalityの4 manifest＋4 result。例えば causality receipt は旧path/SHAと実行時HEADを明示的に束縛しています（[manifest.json:70–124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/env/pegasus/t419-probe-causality/0_889400.nqsv/manifest.json:70)）。これらを新SHAへ置換してはなりません。
- **resolverへ移行すべきtest:** silo evidence検査は歴史artifactを現在の`lookup("pegasus")`へ照合しており（[test_silo_ladder_rung1_evidence.py:1252–1262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1252)）、floor E2Eも旧定数とcurrent lookupを同一視します（[test_s8b_floor_campaign.py:3374–3381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_s8b_floor_campaign.py:3374)、[test_s8b_floor_campaign.py:3448–3452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_s8b_floor_campaign.py:3448)）。g2時にはliteral更新でなく旧contract hash resolverへ切り替える必要があります。
- D176のresolverは存在しますが、production consumerをまだ持ちません（[decisions.md:8694–8698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:8694)）。

`docs/failures.md:2243`と既存evidenceは更新対象ではありません。新g2で現在有効な同種主張が必要なら、旧物を保持したまま再実測・新pathで再発行します。versioned resolverは旧物をhistorically verifiedにするためのもので、current eligibleへ昇格させるものではありません。

自己判定: **real**

成果物影響: 単純置換は旧試行が新較正を使ったという虚偽の履歴を作り、逆に旧定数をcurrent lookupへ残すとg2 activation後に検査が破断する。

推奨対応: **裁定へ返す。** T-529で `historical/current` resolver、activation receipt、新しいfreeze generationを一体設計する。旧bytesは保持、新current claimだけ再発行する。

---

### SRC-01 — brief/planのsource snapshotが既にdriftしている

根拠:

- briefは起点を`cfda4abe`と固定しています（[stage1-brief.md:3–4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:3)）。
- 現在の実測は `HEAD=18149bcf99d166577a33c99d039f6aa0a4f1329e`、brief基準は `cfda4abec7ec22f21ef1cde97f651f4e39278167` です。
- 間の差分には今回の必読面である `docs/decisions.md`、`docs/pegasus-runbook.md`、`tools/check_docs.py`、`tools/pegasus/dispatch_compute.py`、probe群が含まれます。
- `plan-out.md`のmtimeは01:59、現HEAD commitは02:09です。clean worktreeは「同じsource snapshot」を意味しません。

自己判定: **real**

成果物影響: 段2のfile:line、運用規律、execution inventoryを別HEADのまま段4以降へ持ち込むと、レビュー済みでない変更を実装前提へ混入させる。

推奨対応: **scope 内で直す。** 現HEADに対してbrief前実測と段2差分を再確認し、source commitを更新してから裁定する。

---

### CLAIM-01 — 現成果物はU-2の調査・設計までで、U-2完了物ではない

| ユーザー依頼の構成要素 | 現時点の到達 | 未到達／別wave扱い |
|---|---|---|
| 方式αの本番結線 | 前waveで到達済み | 本wave成果ではない |
| 取得時self-pass | 現HEADにbenchmark後gateが既存 | プランは早期化・診断のみ。未実装 |
| 計算ノードliveness | driver設計のみ | job未実走、receiptなし |
| T-443 source projection | 必要性と既存helperを特定 | certificationへ未結線 |
| T-444 proof chain | 欠落fieldを特定 | schema/producer/receipt未実装 |
| accepted publish receipt | 過去g1 receiptのみ | αによる新receiptなし |
| 独立self-comparison | CLI内部の同一profile gateのみ | 独立実行・独立receiptなし |
| 新較正の登録／活性化 | なし | T-529へ送付 |
| loader self-pass | なし | 次waveへ送付 |
| 例外集合空化 | 1件のまま | 次waveへ送付 |
| 凍結bytes・pin更新 | なし | 次waveへ送付 |
| `[T-419] U-2 完了` | 未到達 | scope再裁定が必要 |

根拠:

- briefは「本wave=取得サイクル」「新artifact」を成果物として掲げます（[stage1-brief.md:26–34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:26)、[stage1-brief.md:64–68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:64)）。
- しかしプランは production certifyを行わず、registration/pin/exception/loader/scriptsを実装しないと明記します（[plan-out.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:1)、[plan-out.md:307–314](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:307)）。
- `plan-out.md`自身はread-onlyでpytest未実行と正直に記載しています（[plan-out.md:316–330](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:316)）。したがって「コードを実装済み、テスト緑」とする明示的な偽装は反証できました。
- 問題は成果物名とscopeです。`[T-419] U-2 較正の再取得`というwave名とbriefの成果物記述は、Unit1/2だけで停止してもU-2へ到達したように読めます。

自己判定: **real**

成果物影響: acquisition prerequisite設計だけをU-2完了として記録すると、accepted receipt・proof chain・activation・pin closureの欠落が台帳上から消える。

推奨対応: **裁定へ返す。** 到達表を段4裁定と最終READMEへそのまま載せ、未達を別task IDと依存関係付きで残す。現scopeならwaveを「U-2 pre-acquisition hardening」へ改名する。

## 総括

- 最重所見1: D176はaccepted publishを阻止しない一方、pin/current活性化にはT-529が必要であり、親は両者を混同して固定所有を縮小した。
- 最重所見2: 別jobの1/1 livenessは後続certifyを許可せず、同worktree出力によりcertify自身もdirty gateで停止する。
- 最重所見3: pin閉包は旧evidence・凍結contract hash・current resolverを混同しており、単純SHA置換は虚偽の履歴を作る。
- production certifyをT-443/T-444前に投入しない結論自体は反証できなかったが、その制約は親が追加した編集禁止による。
- pytest・build・計算ノード実測は行っておらず、緑は主張しない。

NO-GO — 現プランは取得・活性化・歴史検証の境界と運用順序を閉じておらず、固定された `[T-419] U-2` 所有を完了できない。