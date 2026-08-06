判定は **NO-GO** です。必読ファイルはすべて読めました。ファイル変更・pytest 実行はしておらず、以下は静的読解だけに基づきます。`docs/failures.md` は指定の `grep -n "^## F"` では見出しが `### F` のため 0 hit だったので、同索引を `^### F` で補いました。

## (a) 拒否される順序と FSM

最初の event から受理されません。

| 計画上の操作 | 実際の拒否 |
|---|---|
| `R=1`、`BatchReserved(member_row_count=1)` | authority parser は `batch_member_row_count_min >= 2` を強制するため、`_fail("reservation member row count is below batch minimum")`。計画の R=1 は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-8c-wiring/s2/plan.md:58,127,262,313`、強制値は `orchestrator/campaign/reflux_origin_ledger.py:320-324`、拒否点は同 `:1333-1334`。 |
| reserve だけ `2` に直し、現行の単一 member を commit | member 数が予約数と合わず `_fail("committed batch does not match reservation")`、`reflux_origin_ledger.py:1398-1403`。同一 query ordinal を複製すれば `_fail("committed query ordinals do not match reservation")`、`:1392-1397`。同一 commitment を複製すれば `_fail("invalid batch candidate commitments")`、`:1390-1391`。 |
| `BatchCommitted` が durable になった後、receipt 返却前に例外となり、local phase=`reserved` のまま abandon | 古い state commitment のままなら `_fail("state commitment CAS mismatch")`、`reflux_origin_ledger.py:3214-3216`。snapshot を読み直して abandon しても `_fail("batch reservation abandon is not allowed in current phase")`、`:1352-1354`。 |
| crash 後に open な `BATCH_COMMITTED` / `RESULTS_PREPARED` のまま `OriginSealed` | `_fail("origin seal is not allowed in current phase")`、`reflux_origin_ledger.py:1598-1600`。 |

R を authority に適合させ、member ごとに連続 query ordinal・相異なる salted commitment を作れれば、通常の `reserve → commit → prepare → seal` という相順自体は正しいです。snapshot の `iterations_used` / `queries_used` を使い、receipt の `current_state_commitment` を連鎖させる方針も正しいです。

ただし現計画の `_OriginBatchState` は salt/commitment が単一 scalar です。R≥2 への修正は literal の変更だけでは足りず、member 配列への再設計が必要です。計画が「1→2」を変異として登録している点も期待が逆です。`plan.md:38-48,288-293`。親 N3 は最低行数の存在を記録しながら値 2 と P3 の R=1 を結合しておらず、N8 の生死実験は実際には R=2 です。`parent-measured.md:31-38,91-95`。これは F131 型の誤前提です。`docs/failures.md:3017-3029`。

さらに、commit は receipt より前に head/event を durable 化します。`reflux_origin_ledger.py:3239-3271,3313-3389`。計画の「成功を推測しない」だけでは、成功済みなのに local phase が古い場合を処理できません。

## (b) origin なし既定経路の bytes

計画本文どおり、

- `origin_binding is None` で snapshot・salt・ledger call を行わない
- report/journal/proposal/raw/namespace に field を追加しない
- drive/preview の引数・順序を変えない

を厳守する限り、**実装が直接変更すると特定できる既定 artifact field はありません**。`plan.md:241-250`。journal・proposal は canonical `sort_keys=True`、report も `sort_keys=True` なので、内部辞書の挿入順だけでは bytes は変わりません。`p3_autonomous_workload_trial.py:515-524,799-809`、`s8b_prediction_runner.py:214-221`。

ただし、提案された literal SHA golden は現状の記述では成立しません。

- 実 public no-build drive は `loop_state.json` に `start_wall=time.time()` を保存します。`p3_s4_loop.py:577-580,1001-1003`。
- 計画が固定すると書いているのは `_now_iso` だけです。`plan.md:250`。
- 実経路で `loop_state.json` が作られることは `test_fixture_no_build_cli_uses_public_drive_without_critic_digest` が pin しています。`test_p3_autonomous_workload_trial.py:757-808`。
- `_fake_drive` を使えばこの時刻問題は消えますが、campaign artifact 自体をほぼ生成しません。`test_p3_autonomous_workload_trial.py:79-97`。

したがって `campaigns/<campaign-id>/loop_state.json:start_wall` の bytes/SHA が baseline と post-run で変わるか、fake drive にすると campaign artifact の無変更を未検査にします。これは F81 型です。`docs/failures.md:1911-1924`。

## (c) 既存 pin / 防壁

静的に赤が予測される既存 nodeid は次の2本です。計画が `_finish_trial` に既定値なしの必須引数を追加するため、期待している build/run-scope gate より前に Python の `TypeError` になります。`plan.md:194-201`、`test_p3_autonomous_workload_trial.py:1517-1577`。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_finish_trial_direct_compute_build_rejects_before_provider`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_finish_trial_rejects_copied_seal_from_different_admission`

また、計画上の新設 nodeid

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_fixture_origin_binding_real_ledger_seals_one_tombstoned_member`

は R=1 の reserve で拒否されます。未実装・未実走ですが、reducer の受理規則上の必然です。

それ以外については、次の防壁を直接壊す差分は静的には見つかりませんでした。

- preregistration の reachability：`main → run_trial → _run_workload` は残るため、`test_current_repository_snapshot_has_zero_satisfied_predicates` と `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` を壊す理由は見つかりません。契約位置は `s8c_preregistration_evidence_contract.v1.json:8-22,307-329,381-428`。
- `MAX_APPROVED_GENERATIONS=1`：`p3_autonomous_workload_trial.py:142-150`。pin は `::test_generation_budget_boundary_at_ratified_launch` と `::test_cli_default_is_literal_one_by_ast`。
- `certifying=False` / `arm_binding="declared-only"`：`trial_registry.py:193-200,1186-1195,1237-1248,1251-1265`。
- `_RUN_SCOPE_SEAL` と build admission は ledger 挿入位置より前に実行されます。`p3_autonomous_workload_trial.py:1457-1497`。
- planner→coder の3 field は `p3_autonomous_workload_trial.py:1591-1608`、critic identity projection は `:1743-1780` のままで、計画上 payload field 追加はありません。

ただし新しい seam の負例は既存テストで覆われません。最低でも次の新規 nodeid 相当が必要です。

- `::test_fixture_origin_binding_requires_explicit_fixture_ledger_before_artifacts`
- `::test_origin_binding_rejects_campaign_or_workload_mismatch_before_reservation`
- `::test_origin_commit_receipt_loss_reconciles_without_abandon`

R=1 の先行拒否がこれらの穴を隠すので、現在の赤/緑だけを根拠にしてはいけません。F60・F126 型です。`docs/failures.md:1416-1427,2934-2948`。

## (d) 注入 seam の抜け道

1. **通常の explicit claude-headless 注入**

   非 sentinel の client や非 `None` binding は計画の identity guard で拒否されます。`plan.md:212-219`。`functools.partial` や wrapper を explicit client として渡す場合も、この経路では拒否されます。

2. **fixture → production ledger は現実の抜け道**

   `_run_workload` の既定 client は production、`run_trial` も sentinel を production 関数へ解決します。一方、拒否条件は claude-headless にしか掛かりません。`plan.md:185-219`。したがって、R問題を直した後は次が追加の module rebinding なしで成立します。

   ```python
   run_trial(
       provider_kind="fixture",
       origin_bindings={"ycsb-a": caller_created_binding},
       # origin_ledger は省略 → production
       ...
   )
   ```

   fixture caller が production origin の不可逆予算を消費・forfeit できます。現在 authority が空なことは一時的な mask にすぎません。production API が固定 store を使う位置は `reflux_origin_ledger.py:1747-1754,3454-3478`。

3. **origin と campaign/admission が束縛されていない**

   `OriginBinding` は caller が作る `origin_id` と R だけです。`plan.md:32-36`。authority manifest は workload、verifier、environment、candidate IR 等を持ちますが、`OriginSnapshot` はそれらを返しません。`reflux_origin_ledger.py:238-251,588-608`。既存 launch binding の workload/campaign 検証後に、別 origin ID を選べます。`p3_autonomous_workload_trial.py:1478-1487`。これは `_RUN_SCOPE_SEAL` を破るのではなく、正規 scope 内に未束縛の第二権限を持ち込む穴です。

4. **private sentinel 持込み・module 再束縛・同一 process 差替え**

   private sentinel 自体を渡せば「省略」と区別できません。さらに module の `_PRODUCTION_ORIGIN_LEDGER`、ledger 関数、keyword defaults を同一 process で再束縛すれば identity guard は capability 境界になりません。テスト自身も `_RUN_SCOPE_SEAL` を import して scope を作っています。`test_p3_autonomous_workload_trial.py:57-71`。

   ledger 正本も、in-process private call は capability 境界ではないと明記しています。`reflux_origin_ledger.py:11-18`。したがって、private sentinel 持込み、module monkeypatch、wrapper/partial、同一 interpreter 内差替えは**保証対象外と明記すべき**です。これらまで防ぐなら別 process/service 境界が必要です。

   ただし fixture→production default と unsealed OriginBinding は、module 改変なしで使える public seam なので、保証対象外へ追い出してはいけません。

## Must-fix（6件）

1. **R=1 を撤回し、authority に適合する member モデルへ再設計する。**

   R≥2 の member 配列、連続 query ordinal、member ごとの相異 salt/commitmentを実装するか、ledger policy 自体を変えるユーザー裁定が必要です。一 drive を二 replicate と名乗るだけの修正は不可です。

   **DW-G05:** 放置すると bound run は planner 前で拒否され、`report.json.status/fatal_error` は partial 系へ変わる一方、origin ledger の batch/counter は更新されず、sealed trial-ledger 参照も certified 選択も生成されない。

2. **durable recovery と receipt-loss reconciliation を設計する。**

   salt/event/base commitment を reserve/commit 前に fsync した recovery capsuleへ保存し、`BATCH_RESERVED` は正規 abandon、`BATCH_COMMITTED` / `RESULTS_PREPARED` は同一 event の idempotent replayで閉じる必要があります。sidecar を禁止したままでは後二相を回収できません。snapshot は committed/prepared member や salt を公開しません。`reflux_origin_ledger.py:3402-3434`。F92 型です。`docs/failures.md:2207-2224`。

   また `run_trial` は現在 workload 例外を捕捉して partial report を返すので、計画の「例外を伝播」は public caller までは成立しません。`p3_autonomous_workload_trial.py:1316-1350`、既存 pin `::test_supervisor_error_still_writes_partial_terminal_report` は `test_p3_autonomous_workload_trial.py:2038-2069`。この既存挙動を保ち、ledger failure を `fatal_error` として記録して後続 workload を止める public-path test が必要です。

   **DW-G05:** 放置すると origin は `BATCH_COMMITTED` / `RESULTS_PREPARED` のまま I/Q 消費済みで、新規予約と `OriginSealed` の受理集合から永久に外れ、材料 report は partial/欠落、trial lifecycle 参照も hard crash では未終端になる。

3. **fixture client と production authority を分離し、OriginBinding を launch/campaign に束縛する。**

   fixture binding では production client の省略を拒否し、完全な fixture-store client を明示必須にするべきです。production binding は caller dataclass ではなく、workload・campaign/descriptor・launch admission を照合した発行済み capability に限定してください。

   **DW-G05:** 放置すると別 campaign の origin の `iterations_used`、`queries_used`、tombstone/forfeit、最終 constraint class が変わる一方、`report.json.launch_admission` は元 campaign を指し、origin 参照は report に存在しないため trial-ledger と材料 report の参照が分裂する。

4. **candidate commitment の canonical bytes を修正する。**

   計画式は base64 の `bytes` を JSON 値に直接入れています。`plan.md:75`。ledger 正本は `.decode("ascii")` した文字列です。`reflux_origin_ledger.py:668-679`。literal 実装なら canonical JSON 構成で失敗し、別の文字列化なら seal 時に `_fail("salted commitment opening mismatch")`、`:1533-1538`。R=1 の拒否に隠されない単体 vector test が必要です。F28/F126 型です。

   **DW-G05:** 放置すると reserve 後に candidate commit が成立せず、正常に abandon できても origin の I/Q は forfeited へ移り、report は partial、sealed batch と certified 選択参照は生成されない。

5. **`_finish_trial` の追加引数を originless 既定値付きにする。**

   `origin_bindings=None` と、binding があるときだけ解決される ledger sentinel/default が必要です。既存の guard テストが Python 引数束縛で短絡されないようにしてください。

   **DW-G05:** 放置すると従来 `_finish_trial` 入力の受理集合が domain-specific build/run-scope rejection から一律 `TypeError` へ縮み、report・trial-ledger 行を作らないまま既存防壁 node 2本が静的に赤となる。

6. **byte golden を決定的な実 campaign artifact まで拡張する。**

   `_now_iso` だけでなく `time.time`、必要なら monotonic/random ID を固定し、real public no-build drive の `loop_state.json` と provenance を含めてください。fake drive だけの golden は不足です。

   **DW-G05:** 放置すると `campaigns/<id>/loop_state.json:start_wall` が実装差分なしでも変わって SHA-map の受理集合が揺れるか、campaign artifact が比較対象から消え、journal/reportだけ同じでも「全 artifact bytes 不変」と誤受理する。

なお、no-build tombstone 自体は reducer の三値 matrix上は合法です。ただし no-build は検疫 dry-runであり build/verify/benchを行わず、`ran=True` を返す経路です。`p3_s4_loop.py:843-844,884-893,1038-1040`。tombstone は未実行 member で、`sealed_queries` に寄与せず query floor を満たしません。`docs/decisions.md:9563-9569`。したがって「oracle query wiring」ではなく「全 tombstone の FSM liveness」までに名乗りを下げる必要があります。

## 総括

- **総合判定: NO-GO**
- **must-fix: 6件**
- 最重要3件:
  1. R=1 は authority 最低行数 2 により最初の reserve で拒否される。
  2. committed/prepared 相の crash・receipt-loss 回収がなく、origin が永久に seal 不能になる。
  3. fixture caller が production ledger を使え、OriginBinding も campaign/admission に束縛されていない。
- 親 brief で撤回すべきもの:
  - **P2**: seam は claude の explicit 注入だけを拒否し、fixture→production と origin misbinding を防がない。
  - **P3**: R=1 は `_apply_event` の受理集合外。
  - **P4**: event 位置だけは妥当だが、no-build tombstone は oracle-result wiring ではないため全面主張は撤回し、順序 liveness に限定すべき。
  - **P5**: commit 後 abandon は FSM 上不可能で、receipt-loss 時には stale phase がさらに誤作動する。
  - **P6**: 通常 CLI は binding/store を供給せず、計画自身も発火しないと認めている。
- **P1** は直ちに偽とは限りませんが、R≥2 の再設計と trusted binding/recovery を driver 側だけで完結できるか再裁定するまで「成立」とは置けません。P7 は手順上の問題を認めません。