結論として、現行プランはこのまま実装へ進めない。特に、binding 必須性を決める信頼済み lane がないこと、照合前に WAL repair が走ること、reader inventory が未閉包であることが must-fix である。

必須ファイルはすべて読めた。以下は read-only 静的検査であり、ファイル変更・pytest 実走・緑判定はしていない。

## 整合性・実効性

### B-01 — `_validate_attempt_topology` への `campaign_lock` 追加

- 対象: [wal.py:939](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:939>)
- 判定: **refuted**
- 根拠:

  ```python
  # recover
  campaign_lock = _campaign_lock_value(layout)       # 1243
  _validate_attempt_topology(records, ...)           # 1276

  # replay
  campaign_lock = _campaign_lock_value(layout)       # 1362
  _validate_attempt_topology(records, ...)           # 1369, 1381
  ```

  第4呼出し元の [artifact_admission.py:602](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:602>) も既に `lock` を decode 済みで、呼出しは同ファイル646行。全4呼出し元で引数追加は成立する。

- 成果物影響: なし。懸念は反証された。
- 修正案: 4箇所すべてを固定する callsite inventory は残す。ただし後述の early return と repair 順序は別問題。

### B-02 — writer 用 binder と planning 用 binder の引数契約が矛盾

- 対象: [s2-plan.md:32](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:32>)、[s2-plan.md:36](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:36>)、[s2-plan.md:211](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:211>)
- 判定: **real**
- 根拠: §1 は `bind_environment_contract(cfg, contract)` に exact `ExecutionEnvironmentContract` を要求し、「guard 戻り値以外から束縛しない」とする。一方 §7 は planning/report caller が明示的な文字列 `contract_sha256` を helper に渡すとしている。現物の reader API にその値の入口はない。

  ```python
  def layout_for(document: Mapping, role: str,
                 output_root: str = "") -> CampaignLayout:   # s1_direct_comparison.py:241
      ...
      return campaign_layout(str(ident.campaign_id(cfg)), ...) # :244

  def report(tag: str, trial: str = TRIAL_MAIN, log=print):   # s6_sort_sweep.py:456
      ...
      layout = campaign_layout(str(ident.campaign_id(cfg)))    # :463
  ```

  [autonomous_trial_completeness.py:1127-1139](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/autonomous_trial_completeness.py:1127>) も persisted contract hash を持たず producer config から ID を再計算する。

  直接 `ident.campaign_id` 呼出し一覧そのものは全件一致していたが、`ensure_resumable_wal` / `ensure_resumable_attempts` の全呼出し元は一覧外である。特に `guided.py:198` は actual contract を渡せない。

- 成果物影響: writer と report が別 ID を計算し、実在 directory・certified sample・manifest の `campaign_id` 参照が欠落または別 campaign を指す。
- 修正案: APIを分ける。

  - writer 専用: guard 戻り値の exact contract object だけを受ける。
  - read/planning 専用: persisted hash とその出所を受ける純粋な再計算 API。
  - writer が文字列版を直接呼べない型境界を置く。

### B-03 — `require_binding` を安全に決定できる lane がない

- 対象: [s2-plan.md:137-146](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:137>)、[guided.py:83-137](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/guided.py:83>)
- 判定: **real**
- 根拠:

  ```python
  # guided も post-policy lock
  return ident.bind_admission_policy(cfg, _NO_BUILD_POLICY)   # guided.py:104

  # しかし synthetic COMMIT は contract 無し
  wal.log(layout, v, STAGE_COMMIT, ENV_TAG,
          {"fitness_tps": res.fitness_tps})                   # :137
  ```

  `require_binding` を hash key の有無から決めれば、欠落した旧 writer が自動的に exempt される恒真 gate になる。`build_admission` の有無や `admission_policy` から決めると、guided も certified と同じ post-policy なので拒否される。

- 成果物影響: 選び方次第で、guided 台帳が全拒否になるか、旧無束縛 COMMIT が `committed=True` のまま受理集合へ残る。
- 修正案: hash の存在から必須性を推論しない。versioned lock kind または trusted entrypoint の exact enum で `CERTIFIED_BOUND / SYNTHETIC / FROZEN_HISTORICAL` を分ける。歴史 lane は exact byte ledger に限定する。

### B-04 — 照合前に WAL bytes が変更される

- 対象: [ident.py:185-202](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:185>)、[wal.py:526-590](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:526>)
- 判定: **real**
- 根拠:

  ```python
  ensure_campaign_identity(...)
  repair = wal.repair_truncated_tail(...)    # ident.py:195-198
  wal.recover_interrupted_attempts(...)      # :199

  receipt_path = _write_receipt(...)         # wal.py:584
  os.ftruncate(fd, final_size)                # :585
  ```

  contract validator は plan 上 recovery/replay に入るが、tail repair はそれより先に receipt を生成して WAL を truncate する。さらに recovery は attempt-schema key が無いと [wal.py:1259-1262](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1259>) で validator より前に return する。

- 成果物影響: `lock=H_A, valid-prefix COMMIT=H_B, truncated-tail` の directory が、拒否前に WAL bytes と repair receipt 参照を変更される。manual driver では no-attempt COMMIT の後へ新 record を追記し得る。
- 修正案: 同じ fd lock 内で valid prefix の contract 検証を完了してから receipt/truncate する。contract 検証は attempt-schema early return より前に置く。

### B-05 — 「全 selection reader が閉じる」は現物と不一致

- 対象: [s2-plan.md:158](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:158>)
- 判定: **real**
- 根拠:

  ```python
  # 最新 COMMIT を baseline 採否に使用
  commits = [rec for rec in wal.read_records(layout)
             if rec.stage == STAGE_COMMIT]              # screening_driver.py:117-123

  # certified report の Sample を COMMIT から生成
  commits = [record for record in segment
             if record.stage == "commit"]               # s1_report.py:274-325

  # official S8b report も raw collected reader
  records, line_issues, truncated_tail = \
      wal.read_records_collected(layout)                 # s8b_oracle_report.py:1292
  ```

  `backoff_repro.py` と `p2_2_report.py` は「公式判定に使わない」と明記されるため allowlist 化可能だが、screening と S1 report は実際に採否・certified sample を作る。§8の15 nodeidには reader inventory test 自体も存在しない。

- 成果物影響: replay が拒否する `H_A/H_B` 不一致 COMMIT が、screening baseline、S1 certified sample、S8b report から依然受理される。
- 修正案: parser-only API と semantic checked view を型で分離し、selection/report consumer を後者へ移す。raw reader は明示的 diagnostic allowlist のみ許可する。

### B-06 — historical artifact admission が無束縛 COMMIT を明示的に受理する

- 対象: [artifact_admission.py:600-635](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:600>)、[test_artifact_admission.py:90-112](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_artifact_admission.py:90>)
- 判定: **real**
- 根拠: `build_admission` のない lock は post-policy validator より前に返る。

  ```python
  if type(search) is not dict or "build_admission" not in search:
      ...
      return CampaignAdmissionDecision(
          classification="historical-pre-admission-schema",
          admission_status="historical-not-reclassified",
          ...
      ), tuple(records)
  ```

  `CampaignAdmissionDecision.admitted` は `legacy-unclassified` 以外を全受理する（[artifact_admission.py:95-97](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:95>)）。現行テストは21本について次を固定している。

  ```python
  admitted = A.require_admitted_campaign(ROOT / path)
  assert admitted.decision.admission_status == \
      "historical-not-reclassified"                    # test_artifact_admission.py:606-609
  ```

- 成果物影響: plan どおり post-policy の `_validate_attempt_topology` だけを直しても、21本の無束縛 historical COMMIT が `AdmittedCampaign` として critic・layer3 report・completeness の入力に残る。
- 修正案: 要裁定。少なくとも「歴史的記述用に読める」と「certified selection に admitted」を分ける。後者を維持するなら親 brief の scope 3 は成立しない。

### B-07 — hash 同値だけでは認可・env 整合を証明しない

- 対象: [s2-plan.md:146-156](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:146>)、[env_contract.py:627-659](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:627>)
- 判定: **real**
- 根拠: plan は `lock.H == COMMIT.H` と64 lower-hexだけを見る。しかし既存 resolver は、未知・非一意・ever-active でない hash を明示的に拒否できる。

  ```python
  candidates = _CONTRACT_SHA256_INDEX.get(contract_sha256)
  if candidates is None:
      raise EnvContractError("未知の contract_sha256")
  if contract_sha256 not in state.ever_active_contract_sha256s:
      raise EnvContractError("... ever-active でない ...")
  ```

  lock、COMMIT、directory suffixを同時に `H_X` へ再封すれば、単純な equality と campaign-id 再計算は通る。また `WalRecord.env_tag` は選択フィルタなのに、`H_linux` と `record.env_tag="pegasus"` の交差検査もない。

- 成果物影響: 任意の self-consistent `H_X` や別 env_tag の COMMIT が admitted/certified 集合へ入り、「どの契約に認可されたか」というレポート値が虚偽になる。
- 修正案: runtime は guard 戻り contract、offline reader は既存 historical resolver で H を一度解決し、COMMIT の `env_tag` も解決 contract と照合する。generation を入力へ束縛しないので T-627 の先取りではない。

### B-08 — S8b の1405行は「COMMIT reader」ではない

- 対象: [s8b_oracle_driver.py:1405](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:1405>)
- 判定: **real**
- 根拠:

  ```python
  new_records = wal.read_records(layout)[before:]
  abort_payload, bench_s = _trial_measurements(new_records)
  ```

  `_trial_measurements` は [s8b_oracle_driver.py:666-680](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:666>) で `abort` と `bench_done` しか見ない。`committed` outcome は COMMIT でなく in-memory `EvalResult` から決まる。offline report は別途 raw WAL を読む。

- 成果物影響: happy-path testでは同じ `plan.contract` 由来の lock/COMMIT が一致するだけで恒真的になり、後日改変された COMMIT を S8b report が検出しない。
- 修正案: private exact-4 lock は維持し、shared validator を driver の postcondition と `s8b_oracle_report` の双方で実行する。独立に COMMIT を H_B へ変える負例が必要。

## scope 判定

| ID | 対象 | 判定 | 根拠・成果物影響 | 修正 |
|---|---|---|---|---|
| B-09a | S8b private lock exact-4 | **refuted — scope内** | private lockは標準 identity lockでないが、S8b WALの期待Hをdirectory内へ置く唯一の場所。外すとS8bのscope 3が成立しない。 | keep。ただしB-08のoffline readerも配線する。 |
| B-09b | `artifact_admission` | **refuted — scope内** | `require_admitted_campaign` は sole raw-WAL admitted view（[artifact_admission.py:723-737](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:723>)）。外すとcertified consumerが迂回する。 | keep。historical laneは裁定へ返す。 |
| B-09c | `records_by_stage` | **refuted — scope内** | S6/S8a/P3 selector が `STAGE_COMMIT` を読む。外すとscope 3は成立しない。 | keep。ただしこれだけではB-05を閉じない。 |
| B-09d | caller inventory test | **refuted — scope内** | 実装機能ではないが、照合の全reader配線を証明する acceptance proof。 | §8に実在 nodeid と対象allowlistを追加する。 |
| B-09e | qualification event sink 2口 | **real — scope外** | [pipeline.py:1033-1042](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1033>) と1085-1087は WAL でなく、T126 evaluation event の canonical payload。T126 final receiptにも `contract_sha256` はない。 | このwaveからT06、T07のevent側、M4、ASTの4口化を外す。外してもcampaign WALのscope 3は成立する。必要なら別裁定。 |

## 同名識別子

### B-10 — `contract_sha256` の二義化

- 判定: **refuted**
- 根拠となる全分類:

| 現在地 | 意味 |
|---|---|
| [env_contract.py:151-166](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:151>) | `ExecutionEnvironmentContract` 全fieldの canonical fingerprint |
| `env_contract_activation` / `resolve_by_contract_sha256` | 同じfingerprintのactive・ever-active世代索引 |
| [execution_guard.py:204-215](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/execution_guard.py:204>)、v2の620-624 | execution receiptが指す同じ環境契約 |
| `buildcache.BuildResult` / cache manifest | buildに使用した同じ環境契約 |
| floor protocol、oracle `run_contract`、ratified freeze、silo ladder、trigger provenance | すべて同じ環境契約fingerprint |
| `reflux_origin_ledger.environment_contract_sha256` | 長い名前だが同じ fingerprint。設計文書も `_canonical_obj()` hash と明記 |
| T126 final receipt / attestation | bare `contract_sha256` は現在存在しない |
| build admission / artifact admission | `receipt_sha256`、`build_admission_receipt_sha256`、`attempt_receipt_sha256s` であり別名 |
| S8c | `evidence_contract_sha256` 等の修飾済みschema hash。bare名ではない |

- 成果物影響: proposed WAL field が同じ綴りで別物になる箇所はない。
- 修正案: 別名は不要。`contract_sha256` を維持できる。ただしB-07のresolver/env_tag交差検査は必要。

## 変異事前登録 8 件

`○` は要件を満たす、`×` は帰属証拠にならないことを示す。列順は `(a)単一target / (b)maskなし / (c)単一赤理由 / (d)期待node固有`。

| ID | planの置換 | a/b/c/d | 判定 | 成果物影響・修正 |
|---|---|---:|---|---|
| M1 | conflict `if ...` → `if False` | ○/○/○/○ | **refuted** | direct helper testなら上書きだけを観測できる。有効。 |
| M2 | `bind_environment_contract(...)` → `cfg = cfg` | ○/×/×/× | **real** | mandatory `canonical_preimage` が後段でmissingを拒否し、順序欠陥でなく別gateの赤になる。多数のrun testも赤。campaign IDをspyする孤立テストへ変更する。 |
| M3 | no-bench WAL hash → zero | ○/○/○/○ | **refuted（位置指定条件）** | raw WALを直接 exact H と比較すれば有効。位置をAST/spanで固定する。 |
| M4 | no-bench qualification hash → zero | ○/○/○/○ | **real（scope）** | 帰属自体は成立するが、変更対象がscope外。T126 event ledgerだけが変わるため本waveから除外。 |
| M5 | `.get(KEY)` → `.get(KEY, expected)` | ○/○/○/○ | **refuted** | missingだけを通す。valid topology fixtureなら単独理由になる。 |
| M6 | `actual != expected` → `actual != payload.get(KEY)` | ○/○/○/× | **real** | mismatch testだけでなく `records_by_stage` mismatch等も赤になる。期待node固有でない。consumer別ではなくcore validatorの1 nodeを期待赤にする。 |
| M7 | `actual != expected` → `actual == expected` | ○/○/○/× | **real** | 全matching WALを拒否し、mismatchを受理するため多数の既存・新nodeが同時に赤。局所帰属不能。validator単体の対向2例へ変更。 |
| M8 | `records_by_stage` validator → `None` | ○/○/○/× | **real** | T11はM6/M7でも赤になり得る。consumer call-presenceをspyする専用nodeと、core比較nodeを分離する。 |

## 新規15 nodeidの実効性

| ID | nodeid要旨 | 判定 | 甘くできる点・コード根拠 | 成果物影響 / 修正 |
|---|---|---|---|---|
| T01 | scalar hash only | **real** | typeが`str`だけを見れば、別keyへのfull contract混入を見逃す。 | ID preimageがreceipt/generationで揮発。exact search_config差分とH_A/H_B ID差を固定。 |
| T02 | conflicting prebind reject | **refuted（条件付）** | valid H_B入りcfgへH_A contractを直接渡せば後段maskがない。 | なし。helper direct・cfg不変もassertする。 |
| T03 | lock key stays nested | **real** | nested keyの存在だけならtop-level重複を見逃す。 | lock schemaとID参照が変わる。exact top-level 5とcanonical bytesをassert。 |
| T04 | authorization後にID計算 | **real** | binding削除はmandatory gateにmaskされる。現行順序は admission:123、auth:131、ID:135。 | 別contractが同じdirectoryを共有。`campaign_id` spyで受取cfgを直接観測。 |
| T05 | no-bench WAL writer | **refuted（条件付）** | replayせずraw recordのexact Hを見ればよい。 | なし。zero/foreign Hも負対照にする。 |
| T06 | no-bench qualification | **real** | test自体は作れるがscope外。 | T126 event bytesのみ変更。本waveから削除。 |
| T07 | bench both sinks | **real** | `if qualification_policy is None: ... else:` なので1実行で両sinkは発火しない。 | 片口漏れを見逃す。scopeを取るなら2独立実行が必要。 |
| T08 | commit-only | **real** | happy pathの1 WALだけではabort・qualification・no-benchを覆わない。 | 他stageのschema/ledger bytesが膨張。全発行stage集合を検査。 |
| T09 | independent H_A/H_B mismatch | **refuted** | §9のvalid admission/attempt fixtureなら比較だけが拒否理由。 | なし。resolver/env_tag負例を追加。 |
| T10 | missing field replay | **refuted** | M5を直接killできる。 | なし。format検査より後の例外文字列だけをassertしない。 |
| T11 | records_by_stage mismatch | **real** | 1 consumerだけの試験で、B-05のraw reader inventoryを証明したことにできる。 | S1/screeningが不一致を採る。別のinventory testが必要。 |
| T12 | matching resume/skip | **real** | `committed=True`だけなら実評価が走った後でも緑にできる。 | 重複計測・台帳追記。evaluate/buildの非呼出しspyを必須化。 |
| T13 | lockless legacy replay | **real** | testは有効だが、semantic `replay` が無束縛COMMITをterminal化する契約自体がscope 3と衝突。 | 旧COMMITがskip集合へ残る。diagnostic parser型へ分離するか裁定。 |
| T14 | S8b lock/commit same H | **real** | 同一`plan.contract`由来のhappy pathは恒真的。1405のreaderもCOMMITを使わない。 | S8b reportがtamperを見逃す。独立H_B改変とoffline report負例が必要。 |
| T15 | AST 4 mouths | **real** | 現行ASTは `wal.log` だけを数え `len==2`（[test_campaign.py:4071-4083](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:4071>)）。generic `.emit` まで数えると別emit/aliasで甘くでき、そもそも2口はscope外。 | gateがWALとT126を混同する。WAL 2口gateを維持。 |

追加で不足している試験は、少なくとも次の5種。

- contract mismatch では WAL tail repair receiptもtruncateも発生しない。
- `artifact_admission` の post-policy mismatch と historical 21本の裁定済み分類。
- selection raw-reader inventory。
- guided/certified lane の非推論分類。
- equal-but-unknown H、および H と `record.env_tag` の不一致。

dual runner 懸念は、plan §256を守る限り **refuted**。現物は [test_campaign.py:7568-7575](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:7568>) で各 `test_*` を引数なし `fn()` として呼ぶため、必須fixture/parametrizeは禁止のままにする必要がある。

一方、literal fixture の揮発性は **real**。[test_campaign.py:88-92](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:88>) は毎回 active head を `ec.authorize("linux-baremetal")` から取る。`_T530_*` golden の算出元は明示generationの reviewed contractに固定し、別テストでactive-head変化時の意図的ID変更を扱うべきである。

## 親 brief 自身

### P-01 — campaign 数の母集団混在

- 対象: [s1-brief.md:33](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:33>)、[s1-brief.md:78-80](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:78>)
- 判定: **real**
- 根拠: 現在の `output/campaigns` 直下は30 directory。repo全体の `campaign.lock` は32だが、残り2本は `output/insights/.../evidence/campaign-layout/campaigns`。3,086 WALは30本側だけ。
- 成果物影響: 「既存32 directoryが新IDで到達不能」という移行台帳の件数・参照先が誤る。
- 修正案: `30 official + 2 smoke evidence` と母集団を分ける。

### P-02 — WAL 3,086・単一env

- 判定: **refuted**
- 根拠: 30 official WALの行数合計は3,086、全行 `env_tag=linux-baremetal` だった。
- 成果物影響: なし。

### P-03 — `_T343_BACKOFF_CAMPAIGN_IDS` が実在dirに対応する

- 対象: [s1-brief.md:40-42](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:40>)
- 判定: **real**
- 根拠:

  ```python
  _T343_BACKOFF_CAMPAIGN_IDS = {
      "...-c7e53c07", "...-09c1364f", "...-adad17bc"
  }                                                     # test_campaign.py:284-288
  ```

  実在dirは `...-493813a7`、`...-484c663e`、read-heavyの`610004b9/6f169f90/8ff95955`で、一致は0件。

- 成果物影響: literal pinを更新して緑にしても、driver/reportが実在成果物を指す証拠にならない。
- 修正案: identity golden と実在artifact path pinを別契約として扱う。

### P-04 — 既存dirは「certified本走ではない」

- 対象: [s1-brief.md:54-56](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:54>)
- 判定: **real**
- 根拠: [phase3.md:408-410](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/phase3.md:408>) は `p3-s8a...3f72ecd5` を「最終成果物」と明記する。[freeze-permanent-design-s2.md:708-712](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/freeze-permanent-design-s2.md:708>) はS1 3本のWAL OID/hash/record数を凍結参照する。
- 成果物影響: old IDを到達不能・unboundとして一律拒否すると、最終成果物とS1 frozen reportの参照集合が失われる。
- 修正案: 既存30本を `admitted historical / denied overlay / legacy trigger / frozen final` に分類して受理差分を裁定する。

### P-05 — D13/D125 supersession の権限

- 対象: [s2-plan.md:48-57](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:48>)、[decisions.md:6098-6103](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/decisions.md:6098>)
- 判定: **real**
- 根拠: D125は「OTHER の campaign_id は1 bitも変えない」とし、理由に既存最終成果物を挙げる。T-530裁定は「campaign identity + WAL COMMIT」とは言うが、D125の明示supersessionや既存最終参照の廃止までは記録していない。
- 成果物影響: 全OTHER IDと既存最終成果物の参照先が変わる。
- 修正案: 「campaign identity」がcfg-hash変更を意味しD125をsupersedeするのか、lock隣接bindingでIDを維持するのかを裁定へ返す。

### P-06 — `attestation_mode="none"` receipt の扱いが brief と plan で不一致

- 対象: [s1-brief.md:19-22](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:19>)、[s2-plan.md:104](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s2-plan.md:104>)
- 判定: **real**
- 根拠: worklogは「receipt発行とresume変更を伴う」と裁定前提にした。一方planは `_authorize_measurement` を `(registered_contract, optional_receipt)` にするだけで、現行の

  ```python
  if contract.attestation_mode != "required":
      return None                                      # loop.py:75-76
  ```

  を変更する記述・テストがない。

- 成果物影響: mode-noneの `CampaignSummary.execution_receipt` はnullのままで、briefがいうproof chainのreceipt参照は完成しない。
- 修正案: receipt発行をT-530に含めるか、brief 21行の解釈を撤回するかを裁定する。T-658の「全書込み口配線」とは分けて扱う。

### P-07 — FROZEN_MANIFEST 23件

- 判定: **refuted**
- 根拠: [test_frozen_artifacts.py:139-153](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_frozen_artifacts.py:139>) がexact 23件とkey setを固定している。
- 成果物影響: なし。実装時に期待hashを更新しないという親条件は妥当。

## 作業量

### B-11 — 単一 Codex 実装単位という見積り

- 対象: [s1-brief.md:66-74](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t530-contract-hash-binding/s1-brief.md:66>)
- 判定: **real**
- 根拠: 親は `ident/wal/pipeline/loop` 近辺とするが、plan自身が direct ID caller 14 production files、artifact admission、S8b private driver/report、既存 fixture/literal群へ波及させる。さらにB-05/B-06のreader・historical分類が未計上。
- 成果物影響: 一単位で進めると、writerだけ新ID、reportは旧ID、または一部readerだけ旧COMMITを受ける混成状態をcommitしやすい。
- 修正案: interface確定後、所有を次の素集合に分ける。

  1. Core WAL: `model.py`、`pipeline.py`、`wal.py`、`artifact_admission.py`、専用WAL/admission tests。
  2. Standard identity: `ident.py`、`loop.py`、`guided.py`、全direct-ID callerとstandard report/reader、`test_campaign.py`等。
  3. S8b: `s8b_oracle_driver.py`、`s8b_oracle_report.py`、S8b tests。

  共有validator APIを1で固定してから2・3を進める。qualification filesは本waveから外す。

## 総括

- must-fix: `require_binding` をhash有無から推論せず、trusted/versioned laneを設ける。
- must-fix: writer exact-contract APIとplanning persisted-hash APIを分離する。
- must-fix: contract検証を同一fd lock内でtail repair・recovery appendより前に行う。
- must-fix: S1/screening/S8bを含むselection reader inventoryを閉じる。
- must-fix: equal Hだけでなくever-active解決とCOMMIT `env_tag`を照合する。
- 裁定へ: historical 21本のadmitted利用、lockless replay、guidedをどう分類するか。
- 裁定へ: T-530がD125をsupersedeしてOTHER IDを変えるか。
- 裁定へ: mode-none receipt発行とqualification event sinkをこのwaveに含めるか。
- nit/refuted: `_validate_attempt_topology` の全4呼出し元にはlockを渡せる。
- nit/refuted: bare `contract_sha256` の既存用途は同一環境契約hashで統一されている。
- nit/refuted: 3,086 WAL全行linux-baremetal、FROZEN_MANIFEST 23件は現物と一致する。