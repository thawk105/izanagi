## 総括

事実表には誤り・過剰一般化がある。

- 成功 probe 903110 の実行ノードは bnode033 ではなく **bnode019**。原票は `probe/job-0-903110.nqsv/env.txt:1-2`。wall 値は `walls.txt:1-7` と一致する。
- 「workload 間で持ち越す状態は4つだけ」は誤り。launch admission、transport admission/receipt、run-scope、CCBench/cache も run 単位で共有される（`p3_autonomous_workload_trial.py:1389-1391,2090-2107,2180-2205`）。
- campaign ID は facts.md 記載の単純な `(trial_id, workload, policy, contract)` 関数ではない。execution contract 自体は identity から除外される（`model.py:67-84`, `ident.py:151-178`）。世代数・descriptor・base config 等も preimage に入る。
- 同一 `Genome` だけでは build-cache key は一致しない。`src_token` と完全な admission も入る（`buildcache.py:246-266`）。また claim 衝突は `BuildCacheError` だが、pipeline が `build-error` abort へ変換し得るため、process が必ず落ちるわけではない（`pipeline.py:748-804`）。手動回収が必須なのは stale claim 等であり、正常 owner は claim を除去する（`buildcache.py:563-572`）。
- `partial = fail-stop` は誤り。例外・wall 切れは fail-stop だが、`role-invalid` は partial にした後も次 workload へ進む（`p3_autonomous_workload_trial.py:1727-1733,1459-1472`; D106 決定4）。
- 「中断時の証拠は journal のみ」も registered では誤り。lifecycle に `indeterminate` terminal が残る（`p3_autonomous_workload_trial.py:1910-1925`; `trial_registry.py:1640-1665`）。ただし強制終了なら terminal 自体が残らない可能性はある。
- `s8b_prediction_runner.py:71` は timeout の行ではない。1200秒は同 `:53`、実使用は `:1214`。
- registered 再投入は「新 trial_id を manifest に追加」では足りない。manifest 自体が exact 6 trial であり、全 report が manifest hash に束縛されるため、clean な再試行系列を作るなら原則として新しい exact-six manifest と新しい6 IDが要る（`trial_registry.py:322-357,2259-2265`）。

推奨は **(a) 実装しない**。exploratory no-build pilot は既存 CLI の singleton 起動で既に分割でき、正式経路は singleton report と exact-six 受入を持つ。一方、実 build の fan-out には build-cache claim、wall semantics、node 割付 protocol が未解決で、fixture probe の 1.69倍はその面を測っていない。

親裁定は **P2を維持、P3を撤回**する。P1・P4・P5は registered と exploratory、また「独立 trial の運用束」と「一つの trial の代替」を分ける限定修正が必要である。

## 1. 分離設計

N process の起動自体は、各 process に singleton `--workloads`、一意な `--trial-id` と `--run-root` を渡せばよい。core loop の変更は不要である（CLI は `p3_autonomous_workload_trial.py:2242-2275`）。

| 資源 | 既存 CLI だけで足りる範囲 | 新規機構が要る範囲 |
|---|---|---|
| run root | 各 process に新規 sibling directory を与える。既存 root は拒否済み（`:2061-2066`）。no-build campaign もその配下で分離される（`:1655-1657`）。 | group 全体を一成果物として扱うなら、期待 run-root 集合を起動前 manifest に固定する。 |
| provider | claude-headless は `run_root/provider/<role>` ごとに生成される（`:1082-1105`）。process 間共有は不要。 | 逐次 multi-workload run と同じ保証を名乗るなら、全 leaf report の valid `child_id` 相異も上位で検査する。現 completeness の session 検査は1 report内だけ（`autonomous_trial_completeness.py:307-324,1000-1004`）。 |
| journal/report | process ごとに `attempts.jsonl` と `report.json` を保持し、連結・再採番しない。各 report は自分の journal hash と1対1束縛済み（`p3_autonomous_workload_trial.py:1551-1580`）。 | 上位成果物を作る場合は各 leaf の report/journal path と両 SHA-256 を参照するだけにし、journal の「合併版」を作らない。 |
| transport receipt | process ごとに transport admission を再取得し、journal先頭と reportへ投影する（`:2090-2107`; `autonomous_trial_completeness.py:342-400`）。 | 異なる job の receipt を1個へ代表させてはならない。上位 ledger が leafごとの request ID、PBS job ID、receipt hash を束縛する。 |
| cell admission | 各 process が従来どおり cell ごとに実行する。no-build は exact `not-applicable`、build は Layer-3 admission（`p3_autonomous_workload_trial.py:1181-1230`）。 | aggregate は欠落 admission を補完せず拒否する。build なら leafごとの `assert_campaign_layer3_chain` も維持する（`autonomous_trial_completeness.py:1123-1174`）。 |
| wall | N個を「独立 trial」と定義するなら、既存 `--max-wall-seconds` でN個の独立閾値になる。 | 一つの旧 multi-workload trial と同じ総 wall を主張するなら既存 CLI だけでは不足。同値な共有予算には原子的 group ledger または共通 absolute deadline が要る。単に同じ値をN本へ渡すと総枠がN倍になる（`p3_autonomous_workload_trial.py:1361-1371,1682-1694,2084-2086`）。 |

さらに build fan-out には別の blocker がある。CLI は cache root を `--ccbench-dir/build-variants` に固定する（`:2327-2328`）。同一 source/admission が同時 build されると create-only claim が競合する（`buildcache.py:658-679`）。既存 CLI だけで確実に分離するには process ごとに別の CCBench base を用意する必要があり、cache 再利用を失う。専用 `--cache-root` を足すなら本体変更になる。

したがって「既存 CLI だけで足りる」のは、確実には singleton の fixture/no-build exploratory と、既に manifest が leaf trial を定義する registered 起動である。N job の投入・待機・rc 回収は launcher または人手の責務で、現状は汎用 N-job verifier を持たない（`docs/pegasus-runbook.md:999-1021`）。

## 2. 集約

### Registered

`assert_trial_registry_acceptance` をそのまま上位集約として再利用できる。新しい trial aggregate を重ねるべきではない。

既存受入は既に以下を行う。

- report を exact 6 本要求し、manifest trial set と完全一致させる（`trial_registry.py:2178-2243`）。
- 各 report と sibling journal を snapshot 読取し、completeness と journal hash を再検査する（`:1755-1856`）。
- workload singleton、cell 0/1、campaign binding を検査する（`:2326-2343`）。
- 各 trial の lifecycle start/terminal がちょうど1本で、report/journal hash と一致することを検査する（`:1983-2070`）。
- 最終 receipt に6本すべての report/journal path と hash、status を記録する（`:2384-2427`）。

これは任意 N の aggregator ではなく、H1/H2 × on/off/swapped の exact-six 専用である（`:322-357`）。また `partial` report も受入対象で、status を receipt に正直に残す（`:2344-2347,2384-2397`）。「受入済み」は「全6本 complete」や「科学的成功」を意味しない。現実装の receipt は `certifying=false` である（`:2419-2421`）。

### Exploratory

任意 N の exploratory report には既存受入を流用できない。committed manifest、effective preregistration、registry、lifecycle が無く、holdout は exploratory admission自体が拒否するためである（`trial_registry.py:1126-1188`）。

将来、上位成果物を作るなら `report.json` と混同せず、例えば非認証の `launch-group receipt` とし、少なくとも次を検査する。

1. 起動前に固定した `group_manifest_sha256` と exact N slot。
2. `(slot, trial_id, workload, run_root, argv/input hash)` の一意性と singleton workload。
3. 全N本の report/journal bytes、path、SHA-256。成功した部分集合だけでは発行しない。
4. 各 leaf の `assert_autonomous_trial_completeness`、role 1 attempt、retry=false。
5. semantic equivalence を主張する場合の report 間 `child_id` 相異。
6. leafごとの transport/request receipt と scheduler terminal state/rc。
7. cell admission と、build時の Layer-3 chain・campaign root一意性。
8. wall配分、retry slot、node block/randomization の事前定義との一致。
9. 入力 snapshot が検査中に変わっていないことと、aggregate receipt の exclusive create。

現 waveではこの成果物を作らず、N本を独立 exploratory trial として扱うのが安全である。

## 3. 部分成功

現行 `status` は科学的成功ではなく、実行投影の完全性を表す。

- `complete`: 要求 workload 数と cell 数が一致し、fatal error がなく、各 stop reason が禁止3種でない（`p3_autonomous_workload_trial.py:1491-1501`）。
- `partial`: それ以外。build-cache由来の候補 `outcome="aborted"` でも、cell stop reason 次第では report 自体は `complete` になり得る。したがって `complete` を certified 選択と読んではならない。
- 例外・workload境界のwall切れは後続 suffix を作らない（`:1361-1371,1393-1458`）。
- `role-invalid` は当該 cell を止めるが、outer loop は次 workloadへ進む（`:1727-1733,1459-1472`）。

採るべき意味論は、leaf report の現行定義を変えず、将来 group を作る場合だけ次の投影にする形である。

- group `complete`: exact N report がすべて存在・検証済みで、全 leaf status が `complete`。
- group `partial`: exact N report はすべて存在・検証済みだが、1本以上が `partial`。
- group `indeterminate/incomplete`: process crash等で expected report が欠ける。成功 leafだけでは terminal groupを作らない。

exploratory の旧「1 report・prefix fail-stop」をこの group で置き換えるなら、後続 workload の成果物も残るため受理集合の変更に当たる（現 completeness は cell を要求 workload の prefix に限定する。`autonomous_trial_completeness.py:900-930`）。一方、N本を単に独立 trial の運用束とし、groupを正式入力にしなければ、既存 report の受理集合は変わらない。

registered はもともと6本の独立 reportを exact受入するため、投入時刻だけを並行化してもこの点の受理集合は変わらない。

## 4. 再投入

| 経路 | 定義 |
|---|---|
| registered | 同一 trial ID は start row ができた時点で消費され、再 start不可（`trial_registry.py:1526-1584`）。terminalも once（`:1667-1686`）。同一 manifest内の差替えは認めない。現 partial reportをそのまま exact-six受入へ含めるか、cleanな再実験なら新しい exact-six manifest・新しい6 trial IDで全系列を切る。旧5本は旧 manifest hashへ束縛されるため再利用できない（`:2259-2265`）。 |
| exploratory | lifecycleは使われない。no-buildなら技術上は fresh run rootで同じ trial IDも動き得るが、attempt識別が曖昧になる。buildは同一 trial/workloadが同じ campaign IDとなりfreshness gateで拒否される（`p3_autonomous_workload_trial.py:1639-1658`; runbook `:203-210`）。常に新 trial ID・新 run rootを推奨する。 |

どちらも旧 attempt を上書き・隠蔽しない。再投入を許すなら起動前 protocol に retry slot を固定し、元 request IDと新 request IDを両方残す。未定義なら、元 group は partial/indeterminate のまま閉じ、新しい groupとして開始する。role単位の再試行は引き続き禁止する。

## 5. 実装可否の択

| 択 | 良くなること | 失うもの・危険 | 成果物への影響 | 規模目安 |
|---|---|---|---|---|
| **(a) 実装しない** | 防壁・受理集合・CLI互換を維持。singleton CLIをN回呼べる。 | canonicalなgroup待機・集約がない。運用者がN本のrc/hashを照合する。 | コード既定では certified選択・report・registry/lifecycleすべて不変。手動fan-out時だけ1 multi-cell reportがN leaf reportへ分かれるが、exploratoryなのでcertified入力にはならない。 | 0 LOC |
| **(b) 薄い運用script** | no-build pilotの期待集合、N起動、PID/rc/request回収を再現可能にできる。 | validatorなしのledgerは正式成果物でない。build対応を入れるとcache分離・wall・node protocolが必要になり「薄い」範囲を越える。 | leaf report/hashは(a)の手動fan-outと同じ。外部group ledgerだけ増え、registry/lifecycle/certified選択は不変。 | 純launcher 80–200行程度。exact validatorを足すなら300–700行＋テストで別択 |
| **(c) 本体を1 process 1 workloadへ強制** | singleton invariantをAPI境界で保証できる。 | 既存multi-workload exploratory CLI、共有wall、report内session相異、fail-stop semanticsを失う。build-cache問題は解けない。 | exploratory reportが常に1 cell/N journalとなり、既存multi-cell受理集合を縮小。formal exact-six形は概ね不変。 | 中〜大: production 250–500行、test/docs 600–1200行程度（未確認見積り） |
| **(d) 二層group supervisorを新設** | leaf coreを維持したまま、期待集合・scheduler receipt・wall・aggregateを機械化できる。 | 新しい状態機械、group lifecycle、cache分離、node割付、retry裁定が必要。正式受理と二重化しやすい。 | 新group manifest/report/receipt/hashが増える。正式経路では既存acceptanceとの役割分担が必要。node配置次第で性能値・将来の選択値も変わり得る。 | 大: production 600–1200行以上＋同程度以上のテスト・protocol文書 |

結論は (a)。no-build fan-out が頻繁になり、人手照合が実害になった時点で、(b) を `--no-build --allow-unregistered-exploratory` 専用として再評価するのが妥当である。

## 6. 親の (P1)〜(P5)

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1 | **一部同意、文言修正** | registered が singleton workload/report なのは事実（`trial_registry.py:1018-1024,1264-1273`）。ただし「fan-out済み」は不正確で、N process/job launcher・group waiterは無い（runbook `:1001-1021`）。正しくは「leaf分解済み・並行投入可能、formal aggregateは既存」である。 |
| P2 | **同意** | buildはbench lockの外で先行する（`pipeline.py:748-799`）。lockと競合probeはbench開始時だけで（`:365-399`）、probe対象も `ycsb_*.exe` に限られcompilerを見ない（`calibrator/runner.py:171-203`）。さらにshared build-cache claimも競合し得る。同一ノードbuild+bench fan-outは採らない。 |
| P3 | **撤回** | 現A/B/Cは `scientific_claim=false` の wiring pilot（`p3_autonomous_workload_trial.py:1523-1531`; D106決定5）。no-build operational fan-outは性能値をjob間比較しないため、node交絡を理由に禁止できない。一方、将来のH1/H2×3 armを別nodeへ割り、arm性能を比較するなら、D289/runbookのblock・randomization要件が必要（`docs/pegasus-runbook.md:968-978`）。「8cすべてがworkload間比較」は広すぎる。 |
| P4 | **限定修正** | 一つのmulti-workload reportを独立完走groupへ置換するなら受理集合変更であり同意。ただしN本を独立trialとして束ねない運用、または既存registered six-report運用なら、leaf受理集合は変わらない。fan-outに必然の変更ではない。 |
| P5 | **registeredは同意、exploratoryは限定修正** | registeredのlifecycle retry追加は不可。ただし新trial ID 1本だけではexact-six acceptanceを作り直せない。exploratoryはlifecycle制約がなく、no-buildでは同ID再実行も技術上可能だが、新IDを使うべき。 |

静的読解と既存 probe 原票の確認のみを行った。sandboxがread-onlyのためテストは実行しておらず、pytest緑・build fan-out実測・node間性能差は主張しない。本番コード、テスト、文書はいずれも変更していない。