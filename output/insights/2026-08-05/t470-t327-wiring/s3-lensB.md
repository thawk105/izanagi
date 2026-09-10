結論は **NO-GO**。静的監査で blocker 7 件を確認した。必須ファイルはすべて読めた。指示どおり編集・pytest・CLI 実行はしていない。

以下では、親資料を [brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/brief.md:1)、起草案を [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s2-plan.md:1) と表記する。

## 実際に効くまでの全層

正式成果物へ効く経路は次の 9 層である。

1. CLI / `run_trial()` / private worker の全入口
2. holdout 分類、manifest・registry・`effective_at(C)`・arm/campaign admission
3. trial 一回性 CAS と lifecycle start
4. provider input/raw/payload/envelope、proposal、WAL/build/bench の生成
5. run-start / journal / terminal report / completeness
6. pre-acceptance の generic Layer 3 生成と fresh rebuild
7. formal acceptance の exact-six、lifecycle、C02/C09/C10 検証
8. canonical receipt の exclusive-create、commit、tracked bytes 再検証
9. accepted Layer 3 → certified selector → canonical 台帳・正式レポート

最小 land 案は 1〜2 と 5 の launch marker までしか含まず、3、7〜9を後送する。6 は従来どおり acceptance 前に生成され、9 の selector は現 checkout に存在しない。これは `s2-plan.md:640`, `s2-plan.md:649`, `s2-plan.md:274`, `s2-plan.md:300` でプラン自身も認めている。

## 親 brief の前提・裁定検証

| 項目 | 判定 | 静的根拠 |
|---|---|---|
| N1 | 機構は確認。実測値は未再実行 | evidence module が package core を再 importする一方、`_normalize_predicate_results` は class identity を要求する。`s8c_preregistration_evidence.py:18`, `s8c_preregistration.py:1444`, `s8c_preregistration.py:1795` |
| N2 | 確認 | contract に指定名が実在。contract JSON `:46`, `:75`, `:118`, `:268`, `:304`, `:336` |
| N3 | 前半は正しいが結論は不正確 | rr80/rr20 は `HOLDOUT_BINDINGS` にあるが public runner は先に `WORKLOADS` で拒否する。`trial_registry.py:46`, `p3_autonomous_workload_trial.py:171`, `:1749`, `:1920` |
| N4 | 確認 | runbook 3 コマンドとも manifest 無し。runbook `:63`, `:76`, `:95` |
| N5 | 確認 | `AcceptanceSummary.certifying=False` 固定で、CLI は stdout のみ。`trial_registry.py:125`, `:1422`, `:1467` |
| N6 | 確認 | canonical registry は未追跡。コードには default path 定数のみ。`trial_registry.py:43` |
| P1 | launch gate 単体は妥当、成果物保証は未成立 | opt-in は holdout を拒否する設計だが、downstream consumer が後送される |
| P2 | 不採用 | 名前・文字列だけで readiness を昇格する恒真経路がある |
| P3 | 方向は妥当、実結線と参照経路が不足 | receipt/downstream は最小 land 外、C10 bytes の到達経路も不足 |
| P4 | 事実認識は妥当だが full scope と両立しない | authority 未解決中は `certifying=False` 固定になる |

## evidence contract 条件別照合

| 条件 | 照合結果 |
|---|---|
| C02 | **不一致**。`bind_trial_arm` への改名だけで、contract の run-start/report/campaign/proposal/invocation 全 sink に arm が到達しない |
| C03 | **不一致**。contract は `cells`、`admit_manifest_cell`、`history_prefix_sha256`、acceptance 後 registry append を要求するが、実装・プランは `trials` と receipt file を使う |
| C04 | **不一致**。提案 handler は `experiment_status` と `remaining_cells` を持たず、`_run_workload` 外の失敗を覆わない |
| C08 | **部分一致**。launch capability の exact 再計算は妥当だが、acceptance 側は最小 land 外。contract の manifest `manifest_sha256` field も実 schema にない |
| C09 | **full 案なら概ね一致、最小 land は不一致**。producer 検査は既存だが formal acceptance と downstream positive が後送 |
| C10 | **不一致**。contract の nested field 名と evaluator の flattened token が異なり、provider/proposal bytes の authoritative path・registry append も不足 |

## 所見

### B-1 / blocker / 最小 land は receipt.certifying・accepted Layer 3・certified 選択集合を一切変えず、親 brief の成果物を満たさない

**根拠:** `brief.md:15`, `brief.md:16`, `brief.md:78`, `s2-plan.md:640`, `s2-plan.md:649`, `s2-plan.md:300`。

**具体的な失敗シナリオ:** U-4 flag と report marker だけを land して wave 完了扱いにする。canonical receipt、tracked verifier、accepted Layer 3、selector、台帳はいずれも存在せず、certified 選択の受理集合は実装前と同じである。

**提案:** 親 brief を「U-4 launch-only」に正式に縮小するか、3、7〜9層を同じ wave に戻す。縮小する場合は lifecycle/receipt、C02/C10、accepted Layer 3、selector、T-468 をそれぞれ明示的な後続タスクにし、U-5/T-470 完了を主張しない。

### B-2 / blocker / T-468 未解決中は production receipt の certifying=True 集合が空であり、accepted Layer 3 の正例は生成不能である

**根拠:** `s2-plan.md:467`, `s2-plan.md:477`, `s2-plan.md:490`, `s2-plan.md:511`, `s2-plan.md:582`; `brief.md:19`。

**具体的な失敗シナリオ:** 六 trial が complete、全件 build、C02/C09/C10 が正常でも、canonical approval authority が無いため receipt は必ず `certifying=false` となる。`build_accepted_report` は全件拒否し、テストも negative しか land しないので「常に拒否する実装」が緑になる。

**提案:** T-468 authority の実在 artifact または人間裁定を full T-470 の開始条件にする。解決前は negative receipt 記録 wave として別タスク化し、架空の certifying fixture で production 正例を代用しない。

### B-3 / blocker / rr80・rr20 は public runner で admission より前に unknown workload となり、正式 holdout launch 集合が永久に空のままである

**根拠:** `trial_registry.py:46`, `trial_registry.py:933`; `p3_autonomous_workload_trial.py:171`, `:595`, `:1749`, `:1920`; `s2-plan.md:13`, `s2-plan.md:21`。

**具体的な失敗シナリオ:** `--workloads rr80` は argparse で拒否される。Python API でも `run_trial()` が line 1749 で拒否し、仮にそこを越えても `_prepare_campaign_identity()` が `WORKLOADS[workload]` で失敗する。admission 単体テストだけは holdout gate を通るため「配線済み」に見える。

**提案:** rr80/rr20 の実 projection を `WORKLOADS` と campaign/completeness consumer に追加するか、正式 holdout 専用 runner を設ける。scope 外なら後続タスクとし、public `main()` と `run_trial()` を通る正例ができるまで U-1 formal launch を完了扱いにしない。

### B-4 / blocker / exploratory の certifying=false は terminal report のラベルに留まり、generic Layer 3 材料集合から探索 run を除外しない

**根拠:** `s2-plan.md:121`, `s2-plan.md:274`, `s2-plan.md:298`, `s2-plan.md:593`, `s2-plan.md:649`; `p3_autonomous_workload_trial.py:1154`, `:1165`, `:1283`; `layer3_report.py:453`, `:468`。

**具体的な失敗シナリオ:** flag 付き non-holdout build は acceptance より前に通常の `layer3_report.json` を生成する。その `admission_decision` は campaign artifact admission であり、U-4 の `launch_admission.certifying=false` ではない。generic Layer 3 を読む側には探索 run を正式材料から外す機械情報も強制 consumer もない。

**提案:** accepted consumer が land するまで exploratory opt-in の build を隔離または禁止するか、generic Layer 3 に検証済み launch-admission marker を追加して全 consumer を fail-closed にする。selector 結線は別後続タスクとして明示するだけでなく、land まで T-470 未完とする。

### B-5 / must-fix / formal admission は「既 start を拒否」と書く一方、最小 land は lifecycle を除外しており、同一 trial の start 行数を 1 に固定できない

**根拠:** `s2-plan.md:72`, `s2-plan.md:229`, `s2-plan.md:389`, `s2-plan.md:393`, `s2-plan.md:640`, `s2-plan.md:649`; runbook `:198`。

**具体的な失敗シナリオ:** 同一 trial ID の二 supervisor が並行して admission と freshness を通過し、別 run root または別 worktree から複数 report を作る。lifecycle ledger が無いため receipt が参照すべき唯一の start/terminal 対応が定まらない。

**提案:** formal branch は lifecycle CAS と同時に land するか、lifecycle 実装まで無条件拒否する。別 clone/worktree を跨ぐ保証は T-469 後続タスクとして分離し、現 wave の保証を「単一 shared ledger 内」に限定する。

### B-6 / must-fix / rename 対象の caller 列挙が不足し、旧 acceptance CLI や旧 wrapper が残ると receipt を書かない経路が production に残る

**根拠（全 caller）:**

- `load_trial_manifest`: production `trial_registry.py:733,915,1310`; compatibility tests `test_trial_registry.py:131,360,534,550,560,571,581,594,601,704,727,762,858,885,1017,1018,1310,1376`。
- `load_launch_binding`: production `p3_autonomous_workload_trial.py:630`; `test_trial_registry.py:391,706,744,764,778,790,1143,1387`; `test_p3_autonomous_workload_trial.py:2181,2316,2367,2388,2412,2421,2439,2448`。
- `assert_unregistered_for_exploratory`: production `p3_autonomous_workload_trial.py:624,1368`; `test_trial_registry.py:486,1048,1192`。
- `assert_campaign_binding`: production `p3_autonomous_workload_trial.py:646`; `test_trial_registry.py:798`; `test_p3_autonomous_workload_trial.py:2368,2389`。
- `assert_trial_registry_acceptance`: production CLI `trial_registry.py:1467`; `test_trial_registry.py:415,435,453,473,845,866,904,918,940,961,982,1000,1037,1160,1178,1231,1287,1320,1531,1561`。
- `_trial_launch_binding`: production `p3_autonomous_workload_trial.py:1761,1981`; test `test_p3_autonomous_workload_trial.py:2269`。

**具体的な失敗シナリオ:** `accept_trial()` を新設しても `trial_registry.main()` の line 1467 を更新し忘れると、運用 CLI は旧 `AcceptanceSummary(certifying=False)` を stdout に出すだけで receipt を生成しない。一方、旧関数を削除すれば多数のテストが API 名変更だけで落ち、本来の意味検査に到達しない。

**提案:** production caller はすべて contract 名へ移し、旧 wrapper は明示した legacy/non-certifying テストだけに限定する。新旧両経路が同じ test fixture に紛れないよう、production source に旧名が残らない静的 assertion を追加する。

### B-7 / must-fix / 新 flag・capability・sealed scope・lifecycle token の全 caller が未整理で、既存テストが目的の gate より前で一斉に拒否される

**根拠（全 caller）:**

- `run_trial()`: production `p3_autonomous_workload_trial.py:2002`; `test_p3_autonomous_workload_trial.py:525,719,753,858,887,912,933,953,1373,1473,1517,1538,2211,2322,2346,2526,2616,2642,2737`; `test_autonomous_trial_completeness.py:949,1028,1622,1657,1699`; `test_campaign.py:4411`; `test_claude_transport.py:1412,1483`; `test_role_session_isolation.py:124,175,368,408,472,501`。
- direct `_run_workload()`: `test_p3_autonomous_workload_trial.py:980,1099,1116,1146,1174,1210,1239,1301,1403,2548,2574`; `test_claude_transport.py:2014`。
- direct `_finish_trial()`: `test_p3_autonomous_workload_trial.py:998`; `test_claude_transport.py:1641,1926,1974,2061,2099`。
- CLI `main()`: `test_p3_autonomous_workload_trial.py:672,1600,1625,1642,1665,1682,1702,1727,1739,2392,2469,2669`; `test_campaign.py:4371,4393`。
- runbook: `phase3-s8c-autonomous-trial-runbook.md:64,77,96`。

**具体的な失敗シナリオ:** direct worker の freshness、budget、transport を検査していたテストが、sealed scope 不在エラーだけを観測する。manifestless positive は flag 既定 false で admission に止まり、completeness や transport の回帰を検出しなくなる。

**提案:** 各 caller を「U-4 拒否を期待」「明示 exploratory」「formal」の三種に分類する。private worker positive には public admission から得た sealed scope/token を渡し、`None` やテスト専用 bypass default は作らない。

### B-8 / blocker / P2 の named readiness は token-only no-op を EVIDENCE_UNDEFINED に昇格させ、0 SAT 不変条件を保ったまま配線済みと誤認させる

**根拠:** `s2-plan.md:527`, `s2-plan.md:529`, `s2-plan.md:553`, `s2-plan.md:559`; `s8c_preregistration_evidence.py:439`, `:456`, `:475`; `test_s8c_preregistration_predicates.py:212`, `:226`, `:234`, `:242`, `:396`; `test_s8c_preregistration_invariant.py:191`。

**具体的な失敗シナリオ:** C04 は空の `mark_experiment_indeterminate()`、C09 は `"no-build"` / `"certifying"` 文字列、C10 は field 名 tuple と空の `read_and_verify_bytes()` だけで readiness 成功になる。値はすべて `EVIDENCE_UNDEFINED` なので「SATISFIED 0件」テストは緑のままである。

**提案:** 名前・文字列ではなく、要求 field が production entrypoint から検査・比較・拒否分岐・receipt sink へ流れることを検査する。token-only fixture は mutation 前から `UNSATISFIED` にする。readiness を別 ledger に分離できないなら、意味的 negative control が赤になるまで status を昇格させない。

### B-9 / blocker / C02/C03 は contract 名だけ揃えても field・sink・registry append が一致せず、arm_binding と exact trial 集合を証明できない

**根拠:** contract JSON `:52`, `:60`, `:83`, `:89`, `:100`, `:104`; `trial_registry.py:54`, `:56`, `:302`, `:1064`; `p3_autonomous_workload_trial.py:915`, `:1586`; `s2-plan.md:151`, `s2-plan.md:159`, `s2-plan.md:567`。

**具体的な失敗シナリオ:** manifest は `trials` なのに contract は `cells`、registry には `history_prefix_sha256` が無く、acceptance は receipt を別ファイルへ書くだけで registry append route がない。また proposal JSON と `rr80.g1.role` 形式の invocation ID に arm が無いため、on/off/swapped の injective sink binding を証明できない。`bind_trial_arm` という名前だけは存在する。

**提案:** C02 は arm を run-start、terminal、campaign identity、proposal、invocation ID の全 sink に実値として束縛し、acceptance で再導出する。C03 は `cells`/`trials`、history digest、acceptance append のどちらを正本にするか人間裁定で解決する。contract は protected なので、改名だけで済ませず必要なら正式 revision を行う。

### B-10 / must-fix / C04 の crash 範囲と C08 の exact field 経路が未定義で、lifecycle 状態または acceptance の prereg 参照が欠落する

**根拠:** contract JSON `:124`, `:125`, `:128`, `:283`, `:289`; `s2-plan.md:204`, `s2-plan.md:216`, `s2-plan.md:328`, `s2-plan.md:335`; `p3_autonomous_workload_trial.py:1231`, `:1280`, `:1316`, `:1840`。

**具体的な失敗シナリオ:** `_run_workload()` の後にある Layer 3 finalization や report/completeness 書込みが失敗すると、line 1231 の catch を通らず、`experiment_status` と `remaining_cells` が記録されない。C08 では `launch_admission` の nested object だけを追加して既存 top-level fields を落とすと、現 acceptance は全 formal report を拒否するか、新 acceptance が contract の経路を通らなくなる。

**提案:** lifecycle start 後の全処理を覆う top-level terminalization 境界を設け、status と remaining cell IDs を exact schema で残す。C08 は run-start/report の top-level field と launch admission の正規形を明記する。manifest 自身の `manifest_sha256` は自己参照 field にせず、contract を `manifest bytes digest` として正式に明確化する。

### B-11 / blocker / C09 は minimum 外、C10 は実 byte stream へ届かず、cross_binding_receipt_sha256 が実走と別の snapshot を認証できる

**根拠:** contract JSON `:318`, `:322`, `:342`, `:356`, `:362`, `:364`; `s8c_preregistration_evidence.py:475`; `p3_autonomous_workload_trial.py:925`, `:968`, `:1586`; `claude_projected_provider.py:341`; `p3_s4_loop_trigger_gating.py:736`; `s2-plan.md:252`, `s2-plan.md:261`, `s2-plan.md:467`, `s2-plan.md:649`。

**具体的な失敗シナリオ:** valid provider event は nested provenance に payload/envelope hash を持つが path を持たず、proposal path は campaign provenance にあるだけで proposal SHA がない。acceptance 前に proposal/provider artifact を一貫して差し替えると、verifier が「現在の bytes」を再 hash するだけでは生成時の bytes との相違を検出できない。さらに contract の registry append は receipt file 生成で代替されている。

**提案:** 生成時に canonical journal へ repo-relative path と hash を封印し、provider event・proposal内容・WAL・Layer 3 を相互比較する。symlink/out-of-root を拒否する。cross-binding receipt hash を contract が要求する registry append に到達させる。C09 は `accept_trial()` が全 build report を検査し、no-build を必ず non-certifying にする production positive/negative を同時に land する。

### B-12 / must-fix / runbook 更新案は最小 land に存在しない receipt 手順を記載し、formal crash 後の新 trial ID が manifest 集合を書き換える危険を残す

**根拠:** runbook `:57`, `:64`, `:77`, `:96`, `:173`, `:189`, `:195`; `s2-plan.md:593`, `s2-plan.md:597`, `s2-plan.md:649`。

**具体的な失敗シナリオ:** 最小 land 後、operator は flag 付き探索は実行できるが、runbook が指す receipt path/verifier は未実装である。正式 manifest の trial が crash した際に現行記述どおり新 ID にすると、その ID は manifest 外なので、manifest の差し替え・再登録による best-of-N 経路を誘発する。

**提案:** U-4-only wave では三コマンドへの flag と「常に非認証、正式入力禁止」だけを書く。receipt 段落は実装 wave まで追加しない。formal 手順は manifest/registry commit、effective capability、六 trial、accept、receipt commit、独立再検証、accepted Layer 3 の順をコマンド付きで別節にする。formal crash は manifest 全体 indeterminate で再走不可と明記する。

### B-13 / must-fix / 提案テストは常時拒否実装・現行 hash の自己一致・揮発値焼込みを排除できる仕様になっていない

**根拠:** `s2-plan.md:575`, `s2-plan.md:580`, `s2-plan.md:581`, `s2-plan.md:582`, `s2-plan.md:584`; `test_s8c_preregistration_predicates.py:396`; `test_s8c_preregistration_invariant.py:191`。

**具体的な失敗シナリオ:** `build_accepted_report` が常に例外を投げても positive は land しないため緑になる。`matching_tracked_bytes` fixture に現在の hash を埋めるだけなら、verifier が各 declared hash の自己一致しか見ず、manifest↔journal↔provider↔proposal↔WAL の意味的結合を無視しても通る。0 SAT テストも readiness の偽昇格を検出しない。

**提案:** authority 解決後に production 経路の certifying positive を必須化する。同一 receipt に対して manifest、registry、lifecycle、report、journal、raw、payload、envelope、proposal、WAL、Layer 3 を一種ずつ変更する mutation matrix を作る。HEAD、timestamp、現行 digest を期待値へ直書きせず、hermetic repo の既知 bytes から導出し、生成後改変で同じ public verifier が赤になることを確認する。

## 総括

**NO-GO — blocker 7 件**（B-1、B-2、B-3、B-4、B-8、B-9、B-11）。

U-4-only wave として brief を正式に縮小するなら再審査可能だが、その場合も formal holdout の production 到達、lifecycle 境界、全 caller、runbook、意味的 negative control を直し、U-5/T-470/T-468 と certified selector を明示的な後続タスクへ分離する必要がある。