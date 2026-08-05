結論は **NO-GO** です。現 HEAD に gate が存在する点は段2プランが正しい一方、gate の前倒しは、公開された注入 seam では accepted publish 集合を変え、通常経路でも rejection proof chain を変えます。また benchmark 後 clock、loader／activation、変異帰属が未閉鎖です。

### F-00 — 親 brief の「現 HEAD には取得時 self-pass がない」は誤り

- 根拠: `_acquisition_reasons` 自体が clock を見ないのは事実です（[cli.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:400)）。しかし canonical 述語を呼ぶ helper は既に存在し（[cli.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:380)）、benchmark 後に適用されています（[cli.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:611)）。既存テストも全 outlier 位置の拒否と非 publish を固定しています（[test_calibrator_certify.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:533)、[同:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:564)）。したがって brief の「現 HEAD で accepted publish 可能」という結論（[stage1-brief.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:47)）は誤りで、段2の補正（[plan-out.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:5)）が正しいです。
- 自己判定: **real**
- 成果物影響: 新規防壁追加ではなく既存防壁の移動なのに「純増」と記録すると、変異台帳・材料レポート・裁定理由の baseline が虚偽になります。
- 推奨対応: **scope 内で直す**。brief／plan／変異表を「既存 late gate の early 化」に統一する。

### F-01 — gate 移動で accepted publish 集合が変わる静的反例がある

- 根拠: profile へ tolerance を書くのは benchmark 前の一度だけです（[cli.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:550)）。一方、canonical predicate は呼出し時点の module 属性と等値比較します（[execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)）。`Final` は実行時 seal ではありません（[effective_clock_policy.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/effective_clock_policy.py:1)）。`main()` は benchmark 本体を注入可能で（[cli.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:688)）、既存テストも policy 属性を再束縛しています（[test_calibrator_certify.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:663)）。
  
  静的反例は「開始時 policy=2.0、early gate 通過後に注入 `calibrate_fn` が policy=3.0 へ再束縛」です。現行 late gate は artifact の 2.0 と現 policy 3.0 の不一致を拒否します。early-only 案は再検査せず、schema は単に `0 < tolerance < 100` しか課さないため（[schema_v2.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:227)）、そのまま publish へ進みます（[cli.py:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:615)）。よってプランの無条件な集合不変主張（[plan-out.md:106](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:106)）は偽です。
- 自己判定: **real**（公開 Python 注入 seam における反例。既定 shell 経路での再束縛元は見つからない）
- 成果物影響: 現行なら rejected となる policy 不整合 artifact が `registered/` に accepted publish され、直後の loader では current policy 不一致になる可能性があります。
- 推奨対応: **scope 内で直す**。early gate は追加してよいが late gate を残すか、publish 直前に「attempt 開始時 policy が不変」を独立検査する。

### F-02 — accepted 集合が同じ場合でも rejection 成果物と reason 集合は不変ではない

- 根拠: 現行 self-failure は benchmark、quality 計算後に `calibration.json`、`calibration.md`、`window-probes.json` を生成します（[cli.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:590)、[同:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:615)）。テストも「`rejection.json` は無い」ことまで固定しています（[test_calibrator_certify.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:595)）。early acquisition rejection は逆に `rejection.json` だけを残し、benchmark／report／window artifact を残しません（[同:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:448)、[plan-out.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:85)）。
  
  したがって self-failure と同時に成立した `within-run-cv-invalid`、`post-attestation-mismatch` 等（[report.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/report.py:87)）は消えます。逆に後段 window probe が例外になる入力では、現行はその例外理由へ先に到達しますが、early 案は self 理由だけになります。collector は両 staging の全 path／size／SHA を final receipt へ束縛するため（[collect_receipt.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:76)、[同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:153)）、proof chain も変わります。
- 自己判定: **real**
- 成果物影響: certified publish は両者とも拒否でも、材料レポート、rejection の reason 集合、final-receipt の manifest／SHA／参照 path が変わります。試行台帳が reason を意味解釈する直接 consumer は見つかりませんでした。
- 推奨対応: **scope 内で直す**。`skipped_checks`／`not_evaluated` を明示し、artifact 種別変更を仕様化する。単に「拒否時点と診断だけ」とは記録しない。

### F-03 — benchmark 後の clock は未検査で、外側 post probe は publish より遅い

- 根拠: `_static_profile_bytes()` は `effective_clock` と `tsc` を明示的に除外します（[cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:373)）。benchmark 後に再 probe はしますが、比較対象はその static projection だけです（[cli.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:602)）。現行 late self-gate も保存済みの pre `profile` を自己比較するだけで、post clock を使いません。
  
  さらに shell の `attestation-post.json` は calibrator が rc=0、すなわち CLI 内で publish を完了した後に取得されます（[certify_calibration.sh:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:742)、CLI publish は [cli.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:633)）。その post probe 値を比較して publish を取り消す処理もありません。別 job の liveness はこの時間窓を束縛しません。
- 自己判定: **real**
- 成果物影響: benchmark 中または直後に clock が帯外へ移動しても accepted calibration と publish receipt が残り、登録後の certified 選択・材料レポートが不適切な計測を参照できます。
- 推奨対応: **裁定へ返す**。early gate は節約用として残し、publish 前に frozen pre profile 対 post observed clock の canonical 比較、method／governor equality を課すか裁定する。外側 post probe を proof にするなら publish transaction 自体を後ろへ移す必要があります。

### F-04 — evaluator 抽出は「band math」と「canonical policy」を一軸にできない

- 根拠: 現行 public predicate は exact shape と current policy equality を検査し、その後 private band math を呼びます（[execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)）。private math は任意幅で、境界は包含です（[同:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:198)）。既存 golden 自身が次の非同値を固定しています。

  - `tolerance=0`、完全一致: private=true、canonical=false。
  - `tolerance=100`、観測 `[0, 200]`: private=true、canonical=false。
  - 非 policy 10% の等号境界: private=true、canonical=false。
  - 空列: 両方 false。

  根拠は [test_execution_guard.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:424) です。したがって `out_of_band_count == 0` は canonical pass と同値ではありません。ところが予定診断 field には policy eligibility／input validity がありません（[plan-out.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:36)）。
  
  非 float も未固定です。現行 math は `float(sample)` を使うため、expected `[100.0]`／observed `["100"]`／2% は public predicate でも true になります。receipt の JSON validator も文字列・bool を許します（[execution_guard.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:222)）。NaN は calibration schema と receipt validator では拒否されますが、pure evaluator 自体には finite 検査がありません（[schema_v2.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:79)）。つまり integration test では schema preflight に mask されます。
- 自己判定: **real**（プランの同値性仕様が不足。実装前なので実際の bit drift が既に起きたとは主張しない）
- 成果物影響: diagnostics の帯外数を canonical verdict とみなすと tolerance 0/100 を誤受理できます。逆に文字列や bool を evaluator 抽出時に厳格化すると execution-receipt consumer の受理集合が未裁定で縮みます。
- 推奨対応: **scope 内で直す**。評価結果を `input_valid`、`policy_matches`、`band_pass` に分け、canonical は三者の conjunction、private math は `band_pass` のみにする。2% の上下等号／`nextafter`、NaN、numeric string、bool、空列、0、100を直接 unit vector に追加する。

### F-05 — predicate spy と複合 negative は変異の帰属を証明しない

- 根拠:

  - Unit 1／2 の「predicate を呼ばず diagnostics で判定」を predicate spy で kill する案（[plan-out.md:267](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:267)、[同:280](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:280)）は不成立です。mutant が predicate を呼んで戻り値を捨て、`out_of_band_count` で拒否すれば、通常の outlier では spy も結果も通ります。
  - profile の tolerance=100／空列／NaNを CLI 経由で試すと schema preflight が先に拒否します（[cli.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:556)、[schema_v2.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:227)）。これは evaluator gate の kill になりません。
  - Unit 2 は physical cores、affinity count、sample count、hostname を独立 gate として列挙する一方（[plan-out.md:134](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:134)）、テスト／変異表では「non-48 CPU shape」「hostname/48 CPU gate」に畳んでいます（[同:168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:168)、[同:283](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:283)）。一つの fixture で affinity と sample count の両方を壊すと、片方の gate を削除しても他方が拒否します。
  - isolation の call-count は片側削除だけは捕らえますが、「pre を2回呼んで post を使わない」変異を捕らえません。
  - Unit 3 の missing-key schema mask はプラン自身が認識しています（[plan-out.md:289](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/plan-out.md:289)）。ここは exact shape を保った一不一致 fixture が実装されるまで帰属未成立です。

  一方、Unit 1 の基本的な gate 削除／benchmark 後戻しについては、clock 以外が valid で `calibrate_fn` 未呼出しを固定する fixture があり（[test_calibrator_certify.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:231)、[同:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:448)）、別 gate による mask は反証できませんでした。`certification_quality_reasons` も benchmark 未呼出し assertion があるため、この基本変異は mask しません。
- 自己判定: **real**
- 成果物影響: mutation ledger が KILL と記録しても、canonical predicate が admission authority であることや各 liveness gate の存在を証明できず、誤った防壁保証が材料レポートへ入ります。
- 推奨対応: **scope 内で直す**。predicate=false／diagnostics 帯外0、predicate=true／diagnostics 帯外ありを意図的に作る矛盾 oracleを置く。hostname、physical、affinity、sample count、method、pre isolation、post isolation は一項だけ不正な fixture に分割する。

### F-06 — acquisition gate だけでは同じ自己不整合 artifact を別入口から受理できる

- 根拠: 各層の現状は次のとおりです。

  1. calibration schema は有限・正値・tolerance 範囲を検査しますが、samples の自己 band-pass は検査しません（[schema_v2.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:218)、[同:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:485)）。
  2. `load_verified_calibration()` は path、SHA、schema、env、TSC、policy tolerance を検査しますが self-pass はありません（[env_attestation.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:1060)）。
  3. `VerifiedCalibration` の「自己矛盾」は profile SHA 一致だけです（[env_attestation.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:110)）。
  4. issuer／consumer は frozen expected の中央値に対して live observed を比較するだけです（[env_attestation.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:970)、[execution_guard.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:159)）。expected 自身に outlier があっても、live observed が中央値帯内なら receipt を発行できます。
  5. registry self-pass は production gate ではなくテスト内 allowlist です（[test_env_contract.py:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:834)）。
  6. 一部の材料経路は loader を通さず JSON を直接読みます。例として silo binding は `quality.status` 等をそのまま転記します（[silo_ladder_rung1.py:4432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:4432)）。T419 causality driver も hash 後に直接 JSON と band を読みます（[t419_probe_causality.py:3388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/probes/t419_probe_causality.py:3388)）。

- 自己判定: **real**（プランも T-506 として defer している既知の未閉鎖層）
- 成果物影響: CLI 以外で作った schema-valid 自己不整合 artifact を registry／contract へ結び付ければ、loader・execution receipt・campaign admission・材料 report まで到達できます。
- 推奨対応: **裁定へ返す**。T-506／T-529 の登録時に、世代別 loader predicate と activation gate の両方へ canonical self-pass を置く。g1 互換は exact path+SHA 例外に限定し、直接 reader は admission 用途と historical report 用途を分離する。

### F-07 — D176 は source fuse であり、runtime の `REGISTRY` 再束縛を防がない

- 根拠: `validate_generations()` は確かに長さ≠1を拒否します（[env_contract.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_contract.py:316)）。しかし検査は import 時の `GENERATIONS` に一度だけ適用され、`lookup()` はその後も module global `REGISTRY` を動的参照します（[env_contract.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_contract.py:342)、[同:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_contract.py:383)）。従って `env_contract.REGISTRY = MappingProxyType({...g2...})` の再束縛には fuse が発火しません。reverse index も再束縛可能で、既存テストがその経路を使っています（[test_env_contract.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:618)）。
  
  D176 自身も「source bootstrap の防壁であって runtime 活性化権限ではない」「index は再束縛可能」と明記しています（[decisions.md:8691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:8691)）。明示的な production `register` API や環境変数経路は見つからず、テストも API 不在を固定しています（[test_env_contract.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:674)）。穴は in-process module rebinding です。
- 自己判定: **real**（ただし D176 が明記した保証範囲外）
- 成果物影響: 同一 process 内で current contract を activation receipt なしに差し替え、lookup を使う campaign receipt／contract hash／較正参照を切り替えられます。
- 推奨対応: **裁定へ返す**。親 brief の「迂回不能」を「source bootstrap では不能」に修正し、runtime authority は T-529 の未実装事項として明記する。

### F-08 — pin 閉包は直接参照でも1ファイル不足し、間接／歴史 pin の分類も不足

- 根拠: 旧 calibration path／SHA の direct literal を独立に数えると、source/docs は親列挙の4ファイル＋docs 3箇所です。docs は runbook（[pegasus-runbook.md:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/pegasus-runbook.md:556)）、failures（[failures.md:2235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/failures.md:2235)）、archive worklog（[worklog-phase3-0719.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/archive/worklog-phase3-0719.md:40)）の3つで、「docs 2」は archive を落としています。加えて tracked historical output は13ファイルあります（certify 3、silo 2、T419 causality manifest/result 8）。
  
  間接 pin もあります。旧 contract SHA は frozen floor protocol に入り（[floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/s8b-freeze/floor_protocol.json:1)）、その protocol SHA は `FROZEN_MANIFEST`（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_frozen_artifacts.py:38)）、builder golden（[test_s8b_protocol_builder.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_s8b_protocol_builder.py:108)）、selector journal（[journal.jsonl:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/output/s8b-freeze/selector-runs/journal.jsonl:1)）へ連鎖します。patch ledger も旧較正を含む silo evidence を path 参照します（[patches/ledger.json:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/patches/ledger.json:35)）。role review ledger の hash は role source／manifest 用であり（[review_ledger.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/codex_roles/review_ledger.py:15)）、較正 pin は見つかりませんでした。
  
  `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` が1件という数は確認できました（[test_env_contract.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:62)、[同:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:840)）。
- 自己判定: **real**
- 成果物影響: 閉包不足なら新世代の current 参照が旧 SHA のまま残ります。逆に歴史／frozen pin を一括更新すると、過去の材料レポート・試行台帳・23件 frozen manifest の proof chain を遡及改変します。
- 推奨対応: **裁定へ返す**。`current authority pin`、`historical retain`、`frozen transitive retain` の三群へ分類する。g2 は旧 frozen bytes の貼替えではなく、新 namespace／activation record を作る。

### F-09 — login node の1回測定は compute node 帯内化の根拠にならない

- 根拠: probe は実行 process の現 affinity と現在の `/proc/cpuinfo` を読み（[env_attestation.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:300)、[同:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:403)）、その host の全 CPU 値を成果へ入れます（[同:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:669)）。login の96 CPU と計算ノード policy の48 physical cores（[policy.json:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/policy.json:12)）は母集団も負荷条件も異なります。D181 も別時間窓の 9/9 を本番手続きの根拠にしないと明記しています（[decisions.md:8893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/docs/decisions.md:8893)）。brief 自身も compute 帯内化は未実証と認めています（[stage1-brief.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/stage1-brief.md:33)）。
- 自己判定: **real**
- 成果物影響: login 測定を liveness receipt の代用にすると、試行台帳の compute admission が虚偽になります。段2が別 compute job を要求している限り、直接の certified 集合影響はありません。
- 推奨対応: **不要**。段2の compute liveness 方針は正しい。login 値は sampler identity の smoke に限定する。

### 反証できなかった点

- module state が固定される通常経路では、early／late の両方が同じ deep-copy 済み `profile` を検査します。物理 clock の時間変化だけを理由に「移動で別 snapshot を検査する」という反証はできませんでした。これは F-03 の共通残存穴であり、移動差ではありません。
- liveness がプラン記載どおり `pegasus-effective-clock-liveness/v1` で calibration/v2 の必須 top-level key を持たないなら、loader の exact schema（[schema_v2.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:563)）で拒否されます。通常の publish／registry 登録経路も見つからず、「non-certifying」の構造保証は反証できませんでした。loader に実際に食わせて拒否する negative test は追加すべきです。
- Unit 1 の基本 gate 削除、全位置→一部位置、端 index 欠落、benchmark 後戻しについては別 gate の mask を確認できませんでした。
- pytest は一件も実行しておらず、緑は主張しません。

## 総括

- 最重 F-03: post-benchmark clock は検査されず、外側 post probe は publish 後なので較正の時間窓を防御できない。
- 次点 F-06: schema／loader／registry／receipt issuer に self-pass がなく、CLI 以外の入口から同じ穴へ到達できる。
- 次点 F-01: policy の実行中再束縛で、late 拒否・early-only publish となる accepted-set 反例がある。
- rejection proof chain、evaluator の policy/math 分離、mutation 帰属も実装前に修正が必要。
- certify は加えて T-443/T-444 の未束縛 FetchContent 問題があり、プラン自身の NO-GO 判定どおり投入不可。
- **NO-GO — F-01/F-03/F-04/F-05 を plan へ反映し、F-06/F-07/F-08 を明示的な裁定パッケージへ戻すまで実装開始不可。**