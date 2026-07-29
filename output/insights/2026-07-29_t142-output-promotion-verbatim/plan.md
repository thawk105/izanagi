## 現物確認

指定された4資料はすべて全文読了できた。関連コード・テスト・schema も静的に確認した。read-only 指示どおり、ファイル編集・テスト実走・既存 WAL の変更はしていない。親 brief 記載の「325 passed / 9 skipped」は親の測定値であり、本回答の実測ではない。

V/A/O の現物は次のとおり。

| 集合 | 現在の実体 | 問題 |
|---|---|---|
| V: correctness verified | 実行中は [`EvalResult.certified`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:126)、永続側は `verify_done.payload.certified` と `workload.tag` ([pipeline.py:583](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:583)) | 試行単位で全 required tag を AND する型がない |
| A: atomic adoption | `STAGE_COMMIT` と [`EvalState.committed`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/model.py:112) | `wal.replay()` は COMMIT の存在しか見ず、verify/bench との同一試行束縛を検査しない |
| O: output-certified claims | 一級型は存在しない。layer3 の `runs` が事実上の性能出力 | 現在は全 `bench_done` を射影し、COMMIT/S2 を要求しない ([layer3_report.py:356](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:356)) |

promotion frontier に使える実在 field は以下だけで十分である。

- 候補分布: `bench_done.payload.tps`、`median_tps`、`unstable`、`cv` ([pipeline.py:330](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:330))。元の型は `ScalePoint.throughputs` ([model.py:54](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/model.py:54))。
- incumbent 認証: 同一試行の `commit.payload.fitness_tps`、`verify_configs` ([pipeline.py:729](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:729)) と、`workload.tag=="s2" && certified==true` の `verify_done`。
- 比較器: 既存 `stability.compare()` の `faster/slower/no-difference/indeterminate` と `near_floor` ([stability.py:209](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/stability.py:209))。
- 採否床: 動作点が完全一致する calibration の `between_run.cv`。within-run CV や D58 の `k`、abort rate を promotion 入力へ流用してはならない。

重要な現物差が2件ある。

1. 現行 sort/trigger driver は 100,000 records / 4 threads / reps 2 ([p3_s4_loop.py:509](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:509))。既存 between-run 記録は 1,000,000 / 48 threads なので、現行動作点に完全一致する floor は存在しない。`screening_driver.load_between_run_floor()` は workload しか照合せず ([screening_driver.py:34](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/screening_driver.py:34))、この用途には不足している。
2. final O の tie 規則は未凍結である。`p2_2_report` は winner と各候補を直接比較する ([p2_2_report.py:149](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p2_2_report.py:149)) 一方、`winner_tied_set()` は no-difference の推移閉包である ([replay.py:176](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/replay.py:176))。後者では 100–98–96 の橋渡しが起こるため、100 と有意に遅い 96 を先に落とす online promotion は tie 集合を保存できない。

## 設計

採用推奨は「direct-winner O を新 D で凍結し、明確な劣位だけ S2 未実行にする保守側 promotion」である。direct-winner を凍結できない場合は、全候補を S2 へ送る以外に O 保存を証明できない。

試行 `q` は `build_start` から次の `build_start` または最初の terminal record までとする。variant 単位の最後勝ちではなく、必ずこの試行境界で判定する。

- `V(q)`: campaign.lock が要求する全 verify tag に対し、同一試行に `certified=true` の `verify_done` がある。
- `A(q)`: 同一試行に COMMIT がある。
- `O_run(q)`: `V(q) ∧ A(q) ∧ bench_done(q)` に加え、COMMIT の `verify_configs` が要求 tag と一致し、`fitness_tps/cv/unstable` が同じ bench と一致する。adaptive campaign では S2 が必須。
- `O_select(q)`: `O_run(q)` のうち `unstable=false`。selected/stock/tie はこの集合だけから生成する。
- `do_bench=False` は V/A になり得るが O_run には入れない。

比較規則は次に固定する。

| 状態・`compare(incumbent.tps, candidate.tps)` | 処置 |
|---|---|
| O_select incumbent 不在 | S2へ promote |
| exact floor 不在、分布欠損、incumbent/candidate unstable、indeterminate | S2へ promote |
| faster | S2へ promote |
| no-difference（floor 以下または非有意） | tie 保存のため S2へ promote |
| slower かつ `near_floor=true` | 既存規律が再現要求帯としているため S2へ promote |
| slower かつ `near_floor=false` | `not_promoted` terminal outcome。S2未実行 |

raw median の「new-best」だけを gate にしてはならない。no-difference と near-floor を落とし、tie を破るためである。D58 の `baseline_tps × (1-k×floor)` や abort-rate 条件も使わない。

状態機械は以下とする。

- 初回候補: legacy緑 → bench → incumbent不在なのでS2。S2緑ならCOMMIT、S2赤ならABORT。S2赤なら incumbent は生まれない。
- 通常候補: legacy緑 → bench → promotion 判定。明確な劣位だけ `STAGE_NOT_PROMOTED`。それ以外はS2へ進み、全緑のみCOMMIT。
- legacy/S2赤: 従来どおりABORT。adaptive 経路のS2赤では bench が先に存在するが、Oとcritic性能入力から遮断する。
- retryable abort: `identity-error` / `bench-probe-error` / `verify-probe-error` は従来どおり新試行として再評価する。過去試行の bench を新試行のCOMMITへ結び付けない。
- crash: terminal 前なら全評価を再実行。bench 後・promotion outcome 前の crash も再実行する。
- S2未実行: `not_promoted` は aborted でも retryable でもない第三の terminal outcome。resumeでは再実行しない。
- duplicate: COMMIT先なら既存 `duplicate`、ABORT先なら `aborted`、`not_promoted` 先なら `duplicate-not-promoted`。最後だけ whiteboard/critic 上も `not-promoted` とし、fitness/verifier-red を持たせない。

WAL payload には比較監査用の候補・incumbent分布、floor、`Comparison` 結果を残してよい。ただし consumer は以下の射影に限定する。

- critic: `S2NotRun{variant,genome,reason,certification_state="s2-not-run"}` のみ。bench値・比較値・leading indicators・fitness を読まない。
- layer3 `runs`: `O_run` のみ。
- layer3 `variants.events`: O未認証 bench と `not_promoted` の数値 payload は埋め込まず、元WALの `source_ref`、stage、時刻、`projection="wal-only"` だけを置く。これにより WAL hash の双射を保ちながら、数値自体はWAL外へ出さない。
- layer3 に `promotion_outcomes` を追加し、S2未実行の identity/reason/state だけを正式表示する。
- `runs` には `commit_source_ref`、S2を含む `verification_source_refs`、`certification_state` を必須化し、単なるCOMMIT tagではなく実 record を束縛する。

schema は `layer3-material-report/v3` を推奨する。既存 v1/v2 JSON は再生成せず、freeze/manifest/trust root は変更しない。v3 が機序仮説配線用に予約されていた点は、新 D と [`phase3.md:411`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:411) で「v3を認証射影へ使用、機序仮説は次版へ」と明示訂正する必要がある。

## file:line 実装順

1. [`model.py:20–32, 104–150`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/model.py:20)

   `STAGE_NOT_PROMOTED` を generic stage に追加し、`EvalState.not_promoted` と三値 terminal outcome を追加する。`retryable_abort` はABORTだけに限定したままにする。

2. [`wal.py:566–611`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/wal.py:566) と新規 `orchestrator/campaign/promotion.py`

   `replay()` に第三 terminal を実装する。新ファイルに `EvalAttempt`、`OutputCertifiedAttempt`、試行分割、同一試行V/A/O検査、strict floor探索、`PromotionPolicy`、純粋な `decide_promotion()` を置く。`records_by_stage()` は promotion/O 判定に使用しない。

3. [`ident.py:26–74`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/ident.py:26)

   D58と同型に、opt-in時だけ `s2_output_promotion` を search_config へ追加する。policy version、PerfConfig全座標、既存 `compare` の alpha/near-floor margin、floor値とsource hashを焼く。off時はキー自体を返さず、既存campaign IDを保存する。runtime policyとcampaign.lockの不一致はWAL書込み前に拒否する。

4. [`pipeline.py:197–204, 363–434, 604–737`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:197)

   `_BenchResult` に生 `tps` と `bench_completed` を保持する。既定・D58経路は現行順をそのまま残し、promotion指定時だけ `legacy → bench → decision → S2 → COMMIT` とする。promotion+screening、promotion+do_bench=False、S2以外のextra構成はWAL前に拒否する。`EvalResult.fitness_tps` はS2緑後まで設定しない。

5. [`loop.py:26–40, 54–60, 76–161`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/loop.py:26)

   identityから policy を復元して `evaluate()` へ渡す。summaryに `not_promoted` を追加し、成功bench後はCOMMIT/S2赤/not-promotedの別を問わず `first_bench=False` にする。

6. p3 driver

   - 共通 outcome/duplicate処理: [`p3_s4_loop.py:558–664`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:558)
   - sort opt-in: [`p3_s4_loop_sort.py:165–242, 338–376`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop_sort.py:165)
   - trigger opt-in: [`p3_s4_loop_trigger_gating.py:324–397, 501–547`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop_trigger_gating.py:324)

   sort/trigger に明示CLI flagを追加するが既定false。base driverの [`default_cfg()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:493) にはverify/promotionを追加しない。

7. [`critic/digest.py:38–153, 192–219, 257–322, 544–680`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/critic/digest.py:38)

   `S2NotRun` 専用型・loader・rendererを追加する。性能digestとverify abort signalは試行単位O適格性を使い、not-promoted variantを除外する。

8. [`layer3_report.py:38–40, 149–205, 314–389`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:38) と [`layer3_schema.json:6–22`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_schema.json:6)

   v3、試行単位認証、未認証payloadのWAL-only射影、promotion outcome、複数proof ref検査を実装する。

所有は逐次2 unitが現実的である。

- Unit A: model/wal/promotion/ident/pipeline/loop/3 driver と対応テスト。
- Unit B: critic/layer3/schema と対応テスト。O判定を再実装せずUnit Aの共通helperだけを使う。
- manager専有: 新D98、phase完了、worklog、設計・変異・受入台帳。workerにはコードとテスト以外を持たせない。

## テスト

D96の境界テストは次を同じ変更単位に入れる。

- promotion比較行列: 初回、faster、floor等号、no-difference、非有意、near-floor、明確なslower、unstable、floor不在。
- 状態行列: 初回COMMIT、resume、同run duplicate、duplicate-not-promoted、retryable abort再試行、S2-red永久skip、not-promoted永久skip、bench後crash再試行。
- V/A/O境界: S2緑だけ、COMMITだけ、別試行のbench+COMMIT、`verify_configs`だけを偽装、同一試行legacy+S2+bench+COMMITの各ケース。
- identity: sort/trigger既定ID `3be89e0d` / `3f72ecd5` とbase `0b53a387`を保存し、opt-in時だけ別IDになること。
- D58: 既存 [`test_pipeline_screening_boundary_and_fails_safe_matrix`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_campaign.py:1915) を無変更で通し、promotionとの同時指定拒否を追加する。
- criticの非恒真control: raw WALの未認証benchに一意な sentinel数値が存在することを先に正対照で確認し、その後 `build_digest`・render文字列にsentinelも性能キーも無いことを否定対照で確認する。
- layer3の非恒真control: 認証済みbenchは `runs` に1件入り、同じsentinelを持つnot-promoted/S2-red benchは `runs`にもJSON全体にも現れず、`source_ref`だけ残ることを一つのfixtureで確認する。
- 既存 [`test_variant_without_commit_is_reject_with_primary_reference`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_layer3_report.py:413) は `runs == []` とWAL-only射影まで強化する。
- [`test_s8b_oracle_driver.py:3182`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_s8b_oracle_driver.py:3182) は編集しない。`bench_wall_s`の型・optional・closed schemaという独立goldenを既存のまま回帰として通す。
- S1とs8b oracleの順序・受理述語を直接確認する既存suiteを回すが、該当実装ファイルは変更しない。

## 変異

最低限、次の変異を対象とする。

| 変異 | KILLする境界 |
|---|---|
| `slower` と `faster` を反転 | promotion比較行列 |
| `no-difference` をnot-promotedへ変更 | tie正対照 |
| `near_floor` を無視 | near-floor正対照 |
| floor不在をskip扱い | floor不在はS2へ送るテスト |
| `not_promoted` をresumable/abort扱い | resume・duplicate状態行列 |
| 過去試行COMMITと新benchを結合 | retryable/mixed-attempt境界 |
| `verify_configs`文字列だけでO認証 | 実S2 `verify_done`欠落のnegative control |
| layer3を全bench射影へ戻す | WAL sentinel正対照＋report否定対照 |
| criticを全bench読みに戻す | 同じsentinel control |
| 未認証benchを`variants.events.payload`へ戻す | JSON全体のsentinel否定対照 |
| opt-in keyをidentityから除く |既定ID/opt-in別IDテスト |
| certified runまでredactする | layer3認証済みrun正対照 |

## リスク/未決点

- 最大の未決点は、Oのtie意味論が未凍結なこと。既存の推移閉包 `winner_tied_set()` をOとするなら、候補順序に依存せず安全に落とせる非空領域は証明できない。新Dで direct-winner 比較をO規則にするか、promotionを全件S2へ退避させる必要がある。
- 現行100k/t4動作点には exact between-run floor がない。1m/t48の0.03や1.07%を流用してはならない。安全実装は `floorなし→promote` なので、別途calibrationまたは動作点変更が承認されるまで短縮効果はゼロになり得る。
- current p3 campaign内に認証済みstock baselineがない。stock/tieを正式主張する場合は、stockがO_selectに存在するまで `selection_status="unavailable"` とし、外部WALからbaselineを発明しない。
- v3予約と、D12の「完全射影」をhash完全・payload redactionへ変える点は新Dで明記が必要。
- 過去WALからの「88%」はraw new-best集計であり、tie/near-floorを安全側へpromoteする本規則や将来分布へは外挿できない。

## 総括

採用推奨は、試行単位のV/A/O型を新設し、direct-winner Oを新Dで凍結した上で、既存 `compare()` が「明確なslowerかつnear-floor外」と判定した候補だけを `not_promoted` terminalへ送る案である。criticとlayer3は同じO認証helperを共有し、未認証数値はWAL外へ出さない。

最大の未決点はOのtie規則である。推移閉包tieを維持するならadaptive skipは安全に成立せず、direct-winner規則の裁定がない限り全候補S2が唯一の保守解になる。