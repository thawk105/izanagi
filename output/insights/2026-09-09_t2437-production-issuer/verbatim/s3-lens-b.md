## 所見

### 1. originless の literal bytes 不変は成立しない

重大度: blocker

根拠: `orchestrator/campaign/campaign_lock.py:49-55` は `loop.py` と `pipeline.py` を enforcement source closure に含める。`contract_loader_binding.py:518-532` は HEAD の blob digest を採り、`ident.py:583-598` がそれを新規 `campaign.lock` に記録する。accepted 経路では `pipeline.py:2039-2045,2372-2381,2492-2502` が lock digest を commit receipt に入れる。Layer3 は `layer3_report.py:212-220,879-885` で lock と WAL を含む全 file digest と admission receipt を report に入れる。

影響: `result_evidence_context=None` でも、新しい HEAD で生成した originless campaign の accepted WAL frame と Layer3 report は旧実装と byte 一致しない。旧 lock の resume も `ident.py:388-396` の live closure 照合で拒否され、受理集合が変わる。

反証可能な主張: `pipeline.py` または `loop.py` を変更して commit した前後で、時刻と乱数を固定した同じ accepted campaign を新規生成すれば、少なくとも `campaign.lock`、commit receipt、Layer3 report の digest は異なる。プランの「非揮発入力比較」は親 brief の「1 byte も変えない」を証明しない。

### 2. `EvalResult` field 追加を自動 serialize する consumer は見つからないが、プランの consumer 棚卸しは不足

重大度: must-fix

根拠: `EvalResult` は `pipeline.py:300-310`、`CampaignSummary.results` は `loop.py:58-75`。production の field reader は少なくとも次である。

- `loop.py:660-667`
- `p2_2.py:384-391`
- `backoff_sweep.py:309-317,420-430`
- `sanity_silo.py:68`
- `p3_kickoff.py:171-173`
- `p3_s4_red.py:211-223`
- `s6_sort_sweep.py:419`
- `s8a_trigger_sweep.py:521`
- `p3_s4_loop.py:1709-1715`
- `p3_s4_loop_sort.py:419-425`
- `p3_s4_loop_trigger_gating.py:830-858`
- `paper_story_a2_certification.py:3237-3239,3430,3625-3630`
- `backoff_repro.py:175-182`
- `demo.py:62`
- 直接 consumer は `s1_direct_comparison.py:956-969` と `screening_driver.py:506-521,638`。

repository-wide の `asdict`、`vars`、`__dict__`、JSON 化の静的検索では `EvalResult` または `CampaignSummary.results` 全体を serialize する production 経路は見つからなかった。

影響: field 追加そのものによる report/WAL bytes 変更の反例はない。一方、プラン `s2-plan.md:514-520` の consumer 列挙だけでは回帰面を覆わない。

反証可能な主張: 上記 reader は新 field を参照せず、production serializer も存在しない。bytes 変更の実因は所見 1 の source closure である。

### 3. completeness は content file 自体ではなく、物理 campaign identity と rejected build を拒否する

重大度: blocker

根拠: 物理 cfg は `p3_autonomous_workload_trial.py:1271-1279` で `search_config.origin_campaign_run` を追加する。しかし completeness は `autonomous_trial_completeness.py:830-844` で search config の exact key 集合を固定し、この key を許さない。さらに qualifying rejection は bench 前に abort するため、`autonomous_trial_completeness.py:4130-4136` の `built_and_benched >= 1` を満たさない。

`_complete_origin_runtime()` は completeness より先に呼ばれ (`p3_autonomous_workload_trial.py:3788-3789`)、ledger terminal を commit する (`:1892-1897`)。その後に completeness と Layer3 chain が走る (`:3902-3927`)。

影響: formal consumer が一度 `P6Unavailable` に達して ledger を aborted terminal にしても、trial report は completeness で失敗して public caller は partial になる。台帳 terminal と report 完了状態が分離する。

反証可能な主張: 現行 gate のまま `origin_campaign_run` 付き r9 rejection を流すと、完成 report は発行できない。

補足: 設計 §12 の「新 record を exact key gate が拒否」は正確ではない。`docs/phase3-8c-wiring-design.md:828-830` 自身が後段で訂正しており、cell に `campaign_runs` を足す exact gate はない。実拒否点は上記 search config、単一 campaign 前提、generation 履歴、Layer3 chain である。

### 4. プランの `generations == 1` は registered origin 経路を全拒否する

重大度: blocker

根拠: プランは `/home/SFC/tanab/.claude/jobs/68d5cbca/tmp/t2437/s2-plan.md:293-300` で `generations == 1` を要求する。manifest loader は `trial_registry.py:765-784` で exact `generations == 2` を要求し、registry acceptance も report 値との一致を要求する (`:5925-5931`)。設計も `phase3-8c-wiring-design.md:811-813` で G=2 を論理 metadata のまま残すよう指定している。

影響: public 正例は issuer に達する前に preflight failure となり、record、report、ledger のいずれも計画どおり更新されない。

反証可能な主張: 現行 registered manifest を使い、プランの `generations == 1` gate を追加した `run_origin_trial()` が `OriginCompletedTrialReport` を返す例は作れない。

### 5. completeness と renderer を外したまま「8c を結線した」とは名乗れない

重大度: blocker

根拠: Layer3 の semantic source は WAL と whiteboard のみである (`layer3_report.py:234-248,251-266`)。新 content file は `artifact_refs` に opaque file digest として載るだけで、ledger、result-evidence、formal receipt は report の一次参照にならない。プランは completeness と renderer を scope 外のままにしている。

影響: 材料レポートの `source_refs` と証明内容は従来どおりで、record が発行されたことや ledger member と一致したことを示さない。certified 選択は変わらず、台帳と report の参照鎖も閉じない。

反証可能な主張: 変更後の Layer3 report から `result-evidence` の ledger member、physical result、formal receipt をたどる経路は存在しない。

許される名乗りは「`run_campaign()` への issuer hook と、fixture scope の単一 member 発火可能性」までである。「8c origin 結線」「formal end-to-end 完了」は不可。

### 6. B1: content-addressed path は formal consumer の受理集合を変えない

重大度: nit

根拠: resolver は evidence root 相対の任意 canonical pathを受ける (`reflux_result_evidence.py:920-1001`)。formal consumer は projection と source が計算済み physical root 配下にあることだけを要求する (`reflux_formal_consumer.py:974-982`)。固定名は test helper の `test_reflux_formal_consumer.py:282-300` にあるだけである。15-file pin は production source filename の閉集合 (`:32-48,2285-2309`) であり、runtime artifact path の pin ではない。

影響: 新 prefix を使っても consumer の受理集合は変わらず、既存固定名 test を書き換える必要もない。新 producer 用 test を追加すればよい。

反証可能な主張: basename が `runs/wal.jsonl` または `ordered-wal-projection.json` であることを要求する production 判定式はない。

凍結 gate、path pin、`check_docs.py` の住所 lintについても、新 prefix の fixed-string 検索は 0 件であり、変更対象となる定数は見つからなかった。反例なし。

### 7. B2: 3 content artifact と `artifact_refs` の生成順には反例なし

重大度: nit

根拠: プランは source、projection、provenance、record の順で issuer を完了させる (`s2-plan.md:209-213`)。その後 trigger 側が execution provenance と loop state を書く (`p3_s4_loop_trigger_gating.py:821-829,1136-1138`)。Layer3 render はさらに後 (`p3_autonomous_workload_trial.py:3045-3066`) で全 file を走査する (`layer3_report.py:208-220`)。completeness は Layer3 report 自身を除外して再走査し (`autonomous_trial_completeness.py:3317-3329`)、宣言集合との exact 一致を要求する (`:3379-3384`)。

record 本体の path は evidence root 相対 (`reflux_result_evidence.py:818-827`) で、既存 test も outer root に残す (`test_reflux_formal_consumer.py:304-316`)。

影響: 成功経路では 3 content artifact は Layer3 `artifact_refs` に入り、record 本体は入らない。この 3 file が原因で `:3384` が落ちることはない。

反証可能な主張: Layer3 render 後に physical campaign root へ別 file を追加した場合だけ、persisted refs と再走査が不一致になる。本プランの記載順にはその追加 write はない。

### 8. B3: fresh record と pre-sealed fixture ledger の循環は実在する

重大度: blocker

根拠: ledger の `EvidenceDigest` は dereference しない claimed digest である (`reflux_origin_ledger.py:203-205`)。seal 時には evidence digest を salted commitment と照合する (`:1505-1535`)。formal consumer は record raw bytes を SHA-256 化し (`reflux_formal_consumer.py:638-643`)、sealed member の digest と exact 一致させる (`:658-682`)。現在の trial は既に sealed 済みの batches を読み、その後 caller-supplied record bytes を渡すだけである (`p3_autonomous_workload_trial.py:1859-1883`)。

既存 public-path test でこの循環を回避しているのは、private monkeypatch 内で physical evidence を先に作り、次に ledger を seal する手順である (`test_p3_autonomous_workload_trial.py:10975-10993`)。これは public route ではない。

影響: 先に sealed fixture を用意する public 正例では、WAL timestamp、attempt ID、nonce、projection/provenance digestまで含む将来の record bytesを事前に一致させない限り FC01 になる。自由に生成された fresh record の受理は証明できない。

反証可能な主張: pre-sealed member digest と 1 byte 異なる fresh record を差し替えると `reflux_formal_consumer.py:668-670` で FC01 になる。

本 wave が正当に名乗れる 1 行: 「事前協調された fixture digest の下で、production package の issuer hook が fresh path に record を発行できる」までであり、「producer が自由に生成した record を ledger-bound consumer が受理した」ではない。

### 9. end-to-end 正例は前 wave より topology 面で弱い

重大度: must-fix

根拠: 前 wave の正例は 33 件すべてについて実 `derive_physical_result`、`assemble_result_evidence_record`、`issue_result_evidence_record` を呼ぶ (`test_reflux_formal_consumer.py:843-947`)。その 33 fresh bytes から ledger member を作り (`:952-957`)、実 `evaluate_formal_origin()` へ渡す (`:970-983`)。

新プランは active 1 件だけを disk record へ差し替え、残る 32 件は caller-supplied fixture record のままにする (`s2-plan.md:298-300,335-338`)。

また `r9_dense_cycle4` は verifier fixtureであり、前 wave は `verify_trace_dir()` を直接呼んでいる (`test_reflux_formal_consumer.py:824-831`)。プランには actual `run_campaign()` がその fixture trace を生成する実 seam が示されていない。

影響: `P6Unavailable` は 32 stub record に依存するため、33 physical run の producer 結線を証明しない。actual pipeline を stub 化すれば、`EvalResult` retention の実効性も証明しない。

反証可能な主張: 新正例で実 issuer 呼び出し件数を数えると 1、formal consumer 入力は 33 であり、32 件は新 issuer を通らない。

### 10. 実装 path の素集合性には反例なし

重大度: nit

根拠: A、B、C、D の所有 path は `s2-plan.md:3-38` のとおり相互に重複しない。production path だけでなく test path にも同一 file の二重所有はない。

影響: 段 5 の file-level 並列競合は起きない。ただし D は B/C の signature 確定後でなければ実装できず、完全並列ではない。

反証可能な主張: 列挙された所有 path の集合積は全て空。反例なし。insight、worklog、decision fragment の所有だけは未記載なので、親一元所有に固定すべきである。

### 11. 変異事前登録は実装前予測の形になっていない

重大度: must-fix

根拠: プランは変異の分野だけを列挙し、mutation ID、変更式、期待 node 集合を定めていない。具体的には次が mask または等価になる。

- truncated final frame は既存 `wal.ordered_attempt_frames()` が先に拒否する (`wal.py:1688-1694`)。新 producer の変異には帰属しない。
- 「全 frame の attempt 一致」は同 API が該当 attempt だけを選ぶ (`wal.py:1701-1708`) ため、通常入力では恒真。
- terminal、attempt、projection schema の検査は既存 `derive_physical_result()` の `reflux_result_evidence.py:515-533,549-570` と重複する。producer-only 変異は derive に mask される。
- producer と resolver を一続きで呼ぶ負例では、interval 一致を producer から外しても `_resolve_ordered_wal()` の `reflux_result_evidence.py:1127-1129` が落とす。例外だけを期待すると変異は生存する。write 前で落ちたことと file 集合 0 件まで node が検査する必要がある。
- positive attempt が最初なら `byte_start=0` 変異は等価。2 番目以降の attempt を正例にする必要がある。
- `res.verify_result=None` を `s2-plan.md:99-109` の 2 箇所で行う案は相互に mask する。成功 result を `res` に保存しない設計なので、両方とも実質 no-op になりうる。
- pre-build、identity-error、eval-exception の attempt ID 追加 (`s2-plan.md:83-84,240-245`) は、別の発行拒否理由で先に落ちるため過剰決定になる。
- 前 wave の M2-M4 は複合変異が必要、M5 は独立帰属不能だった (`verbatim-insight-README.md:113-126`)。同じ二層重複を単独変異へ戻してはならない。

影響: KILLED になっても狙った gate の実効性を示さず、台帳の mutation attribution が偽陽性になる。

反証可能な主張: 現プランだけから「各登録変異が落とす exact node 集合」を一意に書けない。実装前に `mutation ID / 変更箇所 / 無効化する述語 / 期待 node / 期待外 node 0` の表が必要である。

### 12. 単位 D には本題外または重複した surface がある

重大度: must-fix

根拠:

- `OriginProducerInputs.batch_id/query_ordinal` (`s2-plan.md:278-284`) は run plan member の `query_ordinal`、`evidence_path` と reserve attempt の batch ID から導ける。自己申告 field を増やす必要がない。
- `issued_result_record_paths` (`:286-291`) は deterministic `member.evidence_path` と `result_evidence_relative_path()` から再導出できる。mutable list は不要。
- `campaign_output_root` と `ResultEvidenceIssuanceContext.evidence_root` を signature chain 全体へ別々に渡す案 (`:315-317,340-358`) は同一 root を二重化する。context から導くべきである。
- `--origin-fixture-inputs` (`:361-369`) は fixture document schema と CLI 互換面を新設するが、現 main は fixture provider の real build を拒否する (`p3_autonomous_workload_trial.py:5406-5411`)。`--no-build` では trigger が `run_campaign()` 前に戻る (`p3_s4_loop_trigger_gating.py:788-794`)。
- `generations == 1` は所見 4 のとおり削除必須。
- accepted/repetition の二重 reset と非 verifier abort の attempt ID 保持も、所見 11 のとおり削除候補。

影響: 新 CLI、入力 schema、mutable runtime state、二重 root parameter が増える一方、actual issuer 発火実績は増えない。

反証可能な主張: 上記を削り、sealed capability、run plan member、単一 evidence root だけから issuance context を構成しても S1-S3 の issuer hook は実装できる。

## 親 brief の誤り

- `brief-t2437.md:92` の result-evidence path を `<campaign_root>` と書いた点は誤り。core API の root は outer evidence root である (`reflux_result_evidence.py:818-827`)。
- `brief-t2437.md:101-102` の「record 群が physical artifact_refs に載る」は過度な一般化。載るのは physical subtree に置く 3 content artifact だけで、record 本体は載らない。
- `brief-t2437.md:85-86` の whole-file literal hash pin 0 件は狭い意味では正しいが、「bytes pin の影響なし」への一般化は誤り。`pipeline.py` と `loop.py` は campaign lock の enforcement closure に pin される。
- `brief-t2437.md:71-81` の ownership/editing 面から `p3_s4_loop_trigger_gating.py` が欠落している。
- completeness と renderer を scope 外にしながら、冒頭で fixture trial の完了と formal consumer 到達を end-to-end 完了条件にした点が矛盾する。
- 非 test core caller 0 件、`run_origin_trial` 非 test caller 0 件、production authority 空、`_artifact_refs` 全走査、whole-file hash literal 0 件、HEAD `2143a49c0` については反例なし。

## プランの誤り

- originless literal bytes 不変を証明できない。
- `generations == 1` が registered origin を全拒否する。
- completeness の search-config gate と rejected build population gateを無視している。
- renderer を opaque artifact listing のままにしている。
- pre-sealed ledger と fresh record の循環を固定 fixture で覆い隠している。
- 33 record のうち実 issuer を通すのが 1 件だけで、前 wave の topology 正例より弱い。
- mutation の期待 node 集合が未定で、重複 gate、固定 0、過剰決定を除けていない。
- D の CLI、自己申告 batch/query、issued path list、二重 root parameter は削減可能。
- B1 の新 path prefixと B2 の file 生成順は妥当。所有 path の素集合性も反例なし。

## 裁定パッケージ候補 (scope 外の real な所見)

1. completeness と rendererを本 wave に入れるか、成果物名を「issuer hook + fixture single-member reachability」に制限するか。前者なら origin 専用 completion、physical search config、qualifying rejection、report schema/source refs を設計する必要がある。

2. fresh record の後に ledger の results-prepare/seal を行う実 topologyを入れるか、pre-coordinated fixture digest の循環を限界として明記するか。現 scope では後者しか名乗れない。

3. 33 physical run 全件を実 issuerへ通す正例を要求するか、1 member splice を配線 smoke test として明示するか。1 member splice から P6 topology 到達を主張してはならない。

4. originless 不変条件を literal bytes から「同一 committed closure 内で、context 非提示時の application projectionと追加 file 集合が不変」へ狭めるか。literal bytes を維持するなら本 wave の `pipeline.py` / `loop.py` 編集と両立しない。

## 総括

現プランの S1-S3 は issuer hook の実装案としては成立しうるが、S4 の public end-to-end 正例は成立しない。主因は G=1/G=2 衝突、completeness の物理 identity と rejected-build gate、pre-sealed ledger digest の循環、33 件中 1 件だけの実発行である。

静的検査のみ実施し、pytest は実行していない。