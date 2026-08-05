# 独立設計監査

**判定は NO-GO。** 指定資料はすべて読めた。以下はコード、テスト、Git object の静的検査結果であり、pytest は実行していない。既存 baseline の緑は主張しない。

## 所見

### 1. blocker — N3 のコード事実は真だが、「candidate batch」という意味は恒真化している

**主張:** 同一 wire の反復で ledger 上の合法 batch を作れる、という N3 は真。ただし D121 のいう batch cardinality は候補数であり、現在の `cardinality` は member row 数である。prose で「反 oracle 性は満たさない」と断るだけでは、機械的な誤認を防げない。

**静的確認:**

- ledger は commitment の distinct 性だけを検査する。[`reflux_origin_ledger.py:1102`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1102)
- commitment preimage は wire、query ordinal、replicate ordinalを含む。[`reflux_origin_ledger.py:608`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:608)
- 同一 wire 4 行が合法となる正例が存在する。[`test_reflux_origin_ledger.py:2247`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_reflux_origin_ledger.py:2247)
- 一方、D121 は「候補 batch」の下限がなければ batch サイズ 1 の逐次実行で恒真になると明記する。[`decisions.md:5794`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:5794)
- 提案 API が返すのは区別のない `cardinality` で、distinct candidate count はない。[`s2-plan.md:386`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:386)

**設計への効果:** `batch_cardinality >= 2` を将来の P4 consumer が見ると、候補 1 点を候補 2 点以上と誤認できる。最低でも `member_row_count` と `distinct_candidate_count` を別型・別 field にし、後者が 1 の記録を P4 証拠として受理不能にする必要がある。「ledger transaction batch」と呼ぶのは正確だが、「候補 batch を作った」という記録は誤導である。

---

### 2. blocker — P1 は別 clone・全削除・再 genesis による新品予算を塞がない

**主張:** `--runtime-root` を設けず git-common-dir に固定する案は同一 clone 内の worktree 回避だけを塞ぐ。D147 が要求した authority root の同一性と削除耐性は未達である。

**静的確認:**

- 現 ledger 自身が、別 clone、Git rollback、同一 UID による authority/runtime の協調再構築を検出しないと明記する。[`reflux_origin_ledger.py:11`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:11)
- runtime root は clone ごとの git-common-dir から導出される。[`reflux_origin_ledger.py:1432`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1432)
- 提案は「何もない」場合に新規 provision する。[`s2-plan.md:288`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:288)
- `pointer があるのに epoch がない` 場合だけ拒否するため、pointer と epoch を共に削除すれば「何もない」に戻る。[`s2-plan.md:298`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:298)
- 設計案自身も、外部 monotonic anchor がなければ同一 UID の全削除・履歴書換えを防げないと認める。[`s2-plan.md:633`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:633)
- これは D147 が停止理由とした「別 origin／別 root で新品予算」と同型である。[`decisions.md:7183`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:7183)

**経路別判定:**

| 経路 | 判定 |
|---|---|
| 別 runtime root | CLI 引数では阻止。ただし別 clone の別 common-dir では成立 |
| runtime 全削除→再作成 | pointer も含めて消せば成立 |
| 別 origin | authority 承認は必要だが、後述の semantic-equivalent cell で成立 |
| authority 差替え | in-place は拒否するが、履歴書換え／別 clone／全削除との組合せで成立 |

**設計への効果:** production 初期化を解禁した時点で、現在は不可能な「予算 root を作り直す」操作が可能になる。外部 append-only anchor、clone を跨ぐ repository identity、second-genesis 拒否のいずれかがない限り、budget-enforcing production runtime として land できない。

---

### 3. blocker — N14 は真だが、P2 の successor は新 origin に新品予算を発行する

**主張:** 旧 epoch を残すだけでは予算持越しにならない。successor の `added_origins` は、同じ科学的試行を byte-different な cell として再発行すれば使用量 0 の予算を得る。

**静的確認:**

- N14 の事実は真で、現 genesis は全 authority entry を焼き込み、authority blob と件数の完全一致を要求する。[`reflux_origin_ledger.py:2595`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2595) [`reflux_origin_ledger.py:2293`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2293)
- successor 案は新規 `added_origins` を受け、新 origin は誕生 epoch に route する。[`s2-plan.md:335`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:335)
- `derive_origin_id` は full manifest 依存だが、`derive_cell_key` は workload descriptor、axis、verifier、environment の4 digestだけである。[`reflux_origin_ledger.py:445`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:445)
- 現テストも series 変更で origin ID が変わり、cell は同一になることを固定する。duplicate cell 拒否は一つの authority blob の内部だけである。[`test_reflux_origin_ledger.py:749`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_reflux_origin_ledger.py:749)
- 提案の semantic artifact は blob hash なので、意味を変えない空白・表記変更でも axis/verifier digest を変え、新 cell を作れる。[`s2-plan.md:64`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:64)
- “seal-and-succeed” は predecessor が terminal であることしか要求せず、successor の予算を predecessor の消費量へ課金しない。[`s2-plan.md:348`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:348)

**transition table の問題:**

- s8b の allowlist は parent pointer 以下を subtree ごと許可する。[`s8b_ratified_freeze.py:650`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:650)
- 実際の s8b 世代遷移は `/budget` 全 subtree の変更を許す。[`s8b_ratified_freeze.py:128`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:128)
- origin authority 固有の exact pointer 表は提案されておらず、8項目の散文だけである。[`s2-plan.md:337`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:337)

列挙漏れが protected 側なら permanent no-active という可用性故障、過剰な parent pointer を許可すると既存 origin・budget・cell identity の改変という安全性故障になる。

**設計への効果:** 全世代・全 revoked/cancelled record を含む「ever-issued scientific cell」集合、semantic-equivalence の裁定、series 全体の累積予算割当が必要である。旧 epoch を保存するだけでは新品予算を防がない。

---

### 4. blocker — preimage 規則は `H` と bytes の所有者が二義的で、非自己参照 topology が定義されていない

**主張:** 名前付き Git blob を用いる方向は良いが、現案の共通規則はそのまま実装できない。

**静的確認:**

- 共通規則は「captured commit `H` の `H:<path>` blob bytes」とする。[`s2-plan.md:54`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:54)
- ところが workload descriptor と environment contract は path を持つ blob ではなく「既存 canonical bytes」とされている。[`s2-plan.md:64`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:64)
- provisioning は authority generation と approval が `activation-head` に存在することを要求するが、generation 導入 commit、preimage 基準 commit、approval commit、activation commit を区別しない。[`s2-plan.md:241`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:241) [`s2-plan.md:274`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:274)
- D75 はまさに検証時 HEAD と生成基準 `H` の同名混同を既知の設計誤りとし、`G / H_gen=G^ / A / X` の非自己参照 topology を要求した。[`decisions.md:3017`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:3017) [`decisions.md:3033`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:3033)

**推論:** 現案が実際に自己 hash を生成しているとは断定しない。しかし、generation 自身・approval・active pointer を preimage closure に含めない規則も、含めた場合の循環拒否もない。descriptor/env を「現在のコードで再直列化」する実装なら、serializer 改訂で同じ実験の origin ID が変わる。

**設計への効果:** `H_gen`、generation 導入 `G`、人間承認 `A`、発効 `X` を別識別子にし、各 hash の source blob を exact path 付きで列挙する必要がある。authority generation・approval・pointer・それら自身の hash は source preimage から明示的に除外すべきである。

---

### 5. blocker — A-2 の full-manifest sink binding は一文だけで、実行 sink まで閉じていない

**主張:** `AuthorityBinding` と prepared identity の比較だけでは、比較した値と実際に走らせた値が同一であることを保証しない。

**静的確認:**

- 提案は prepared identity で spec/full OID/workload/env/axis/verifier/IR/role/projection を比較するとだけ記す。[`s2-plan.md:427`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:427)
- 現 campaign identity の spec、records、threads、CCBench pin は別々に組み立てられる。[`p3_autonomous_workload_trial.py:528`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:528)
- 実 drive は `cfg`、`perf`、`sub` を受ける。[`p3_autonomous_workload_trial.py:1606`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1606)
- sink 側は site/environment を改めて解決し、`run_campaign` へ contract、clock、NUMA、CCBench directory を渡す。[`p3_s4_loop_trigger_gating.py:701`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:701) [`p3_s4_loop_trigger_gating.py:565`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:565)
- A-2 は「4 digest の cell 比較では別 spec/CCBench/role bundle が同じ origin に入る」と既に real 裁定されている。[`s4-adjudication.md:64`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-producer-wiring/s4-adjudication.md:64)

**設計への効果:** full manifest の各 field について、比較元、capture 時点、実 sink 引数、実行 receipt、sidecar field の対応表が必要である。同じ immutable `ExecutionBinding` から campaign identityと runner 引数を生成し、formal consumer が実 sink receipt まで再照合できなければ A-2 は閉じない。

---

### 6. blocker — commit-reveal は単一候補でも seal 前に多値を漏らす

**主張:** 候補選択 index がなくなるだけで、membership oracle、correctness、metrics、早期停止は残る。提案の「auditor を同じ shape で呼ぶか、staging」も未確定な択一である。

**seal 前に漏れる具体値:**

1. preview の pass/fail、subtype、reason、diff digest。[`p3_autonomous_workload_trial.py:1533`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1533)
2. auditor skip と実呼出しの分岐、skip reason、pre-audit evidence。[`p3_autonomous_workload_trial.py:1541`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1541)
3. 実呼出し時の raw auditor response と journal event。raw は即時 fsync される。[`p3_autonomous_workload_trial.py:904`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:904)
4. proposal artifact 内の coder wire と auditor verdict。[`p3_autonomous_workload_trial.py:1586`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1586)
5. campaign WAL/provenance の outcome、variant、binding commitment。[`p3_s4_loop_trigger_gating.py:736`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736)
6. 提案される `rep_evidence` の return code、metrics、stdout hash、environment receipt。[`s2-plan.md:450`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:450)
7. ledger 自身も seal event fsync 後・head commit 前は raw storage に plaintext が残ると明記する。[`reflux_origin_ledger.py:20`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:20) 実際に event frame は head commit より先に fsync される。[`reflux_origin_ledger.py:2993`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2993)

現 critic が outcome、variant、metrics を受けることも静的に確認できる。[`p3_autonomous_workload_trial.py:1647`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1647)

**設計への効果:** critic を seal 後へ移すのは必要だが十分でない。preview/auditor/runner/rep evidence/WAL を、seal まで同一 UID の観測者にも読めない staging に置く exact storage contract が必要である。D166 が projection から除外した実行依存 counter は、producer artifact 経由で完全に復活している。

---

### 7. major — create-only `rep_evidence` は物理 query の証明ではなく producer の自己申告である

**主張:** command hash、stdout hash、return code を JSON に書くだけでは、その process が一度だけ実行されたことを証明しない。

**静的確認:**

- ledger は sealed row 数を数えるだけで、物理 query を観測しない。[`reflux_origin_ledger.py:2`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2)
- D166 も「正しく番号付けた同一 evidence で counter が増える」と明記する。[`decisions.md:8286`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8286)
- 提案は runner が create-only artifact を書くことだけを規定し、process-issued capability、PID/start receipt、stdout inode、execution nonceとの不可分性を定義しない。[`s2-plan.md:454`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:454)
- A-13 は ledger commitment が実 query 由来か検査しないことを既に real と裁定している。[`s4-adjudication.md:75`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-producer-wiring/s4-adjudication.md:75)

**設計への効果:** この artifact は監査材料としては有用だが、「物理 R 回」の証明にはならない。trusted runner が実 process lifecycle と同じ操作で発行する nonce 付き receipt、build binary identity、stdout/perf artifact、ordinal の全単射を formal consumer が検証する必要がある。

---

### 8. blocker — reservation／seal／sidecar の crash recovery と namespace が閉じていない

**主張:** `seal → sidecar` の順序には、不可逆 seal 済みだが cross-reference が存在しない crash window がある。逆順にすると plaintext 先出しになる。

**静的確認:**

- 提案順序は Layer 3、ledger seal、sidecar fsync、report である。[`s2-plan.md:600`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:600)
- `EventReceipt` は event hash・state commitment・operation ID を持つが、`SealedBatch` は origin/batch/membersしか持たない。[`reflux_origin_ledger.py:554`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:554) [`reflux_origin_ledger.py:561`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:561)
- 提案 sidecar は seal event hashを要求する一方、operation IDを保存しない。[`s2-plan.md:566`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:566)
- recovery 用 `OpenBatchHandle` にも operation ID／prepared request hashがない。[`s2-plan.md:386`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:386)
- 現 ledger は durable prepared operation と異なる operation IDを拒否する。[`reflux_origin_ledger.py:2944`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2944)
- producer は既存 run root の resume を拒否する。[`p3_autonomous_workload_trial.py:1786`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1786)

また、sidecar の `generation` が LLM generation、authority generation、runtime epoch のどれか定義されておらず、`trial_id`、`campaign_id`、`batch_id` の正準 namespace・導出関係もない。[`s2-plan.md:570`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:570) これは既知 A-7 と同じ穴である。[`s4-adjudication.md:69`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-producer-wiring/s4-adjudication.md:69)

**設計への効果:** crash 後に event receipt を再取得できる deterministic operation ID、secret を含まない proof-intent commitment、sidecar の idempotent finalize が必要である。現順序では裁定済み (4) の「durable cross-reference を今出す」を満たさない。

---

### 9. blocker — 「現行 baseline で発火する検査」一覧の多くは対象条件に到達せず、schema 不在を赤と数えている

`s2-plan.md` の10検査を対象条件単位で静的評価した。[`s2-plan.md:616`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:616)

| # | 検査 | 現行 baseline での判定 |
|---|---|---|
| 1 | authority readiness | **対象条件で発火する。** authority は空。[`reflux_origin_authority_v2.json:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_authority_v2.json:1) ただし拒否証拠であって positive liveness ではない |
| 2 | full OID | **plan の主張は誤り。** `CURRENT_PIN` は7文字だが、plan 自身の規則は Gitlink full OIDを読む。[`pin.py:28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/pin.py:28) [`s2-plan.md:63`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:63) 静的 `git ls-tree HEAD external/ccbench` は full `d706650c…fb40969` を返した |
| 3 | evidence/environment | **直接検査なら発火する。** artifact 2100、registry 1800。[`s8a_trigger_coverage.json:2`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:2) [`env_contract.py:169`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/env_contract.py:169) ただし現 AST 対象一覧は producer を含まない。[`test_env_contract.py:71`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_env_contract.py:71) |
| 4 | provisioning | **positive branch は発火しない。** 現 public APIは createしない。[`reflux_origin_ledger.py:3105`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:3105) |
| 5 | physical query binding | **恒真化した代理赤。** v2 reportに field がないため schema で止まり、偽造 row と実 process の1対1条件は一度も評価されない |
| 6 | privacy readiness | **対象となる赤入力は実在。** conditional auditor と preseal critic がある。[`p3_autonomous_workload_trial.py:1533`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1533) ただし checker の exact predicate は未定義 |
| 7 | durable proof | **恒真化した代理赤。** report v2に ref がないという schema redだけで、sidecar/batch bijection は未到達 |
| 8 | reservation crash | **恒真化した代理赤。** 現 event union に reservation がない。[`reflux_origin_ledger.py:503`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:503) schema不在を拒否しても no-refund recovery は検査されない |
| 9 | same-wire positive/mutation | **非恒真。** 同一 wire 正例、ordinal reset/gap/duplicate commitment の負例がテスト source に実在する。[`test_reflux_origin_ledger.py:2247`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_reflux_origin_ledger.py:2247) |
| 10 | epoch reset | **恒真化した代理赤。** epoch schema自体がなく、旧 epoch 欠落時の router 分岐は発火不能 |

さらに、IR schema、emitter golden、role bundle、recipient projection の名前付き artifact は現 tree に存在しない。既存の32-wireテストは `expected` と実行側を同じ `emit_predicate()` から得ており、独立 golden 照合ではない。[`test_p3_s4_loop_trigger_gating.py:1187`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1187)

**設計への効果:** 10件中、対象条件の実 red があるのは 1・3・6、実 ledger positive/mutation があるのは9だけである。4・5・7・8・10を「発火証拠」と数えるのは D163 が却下した「空 authorityを拒否しただけ」の再演である。[`decisions.md:8102`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8102)

---

### 10. major — recipient schema validation は D164 型の恒真 tripwireになる

**主張:** field 名と JSON 型を schema 検査しても、許可された文字列値への secret 符号化を検出しない。

**静的確認:**

- proposal は全 role payload builder を schema validationするとする。[`s2-plan.md:103`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:103)
- 現 critic payload は candidate-dependent `variant` を含む。[`p3_autonomous_workload_trial.py:1649`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1649)
- diff reject の variant は candidate implementation を preimage にした hashである。[`p3_s4_loop.py:241`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop.py:241)
- D164 の静的32点列挙は、この ID が32/32一意で、字面 tripwireは0/32発火だったと確定している。[`decisions.md:8149`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8149)

**設計への効果:** schema validationだけなら、候補依存 ID が全32点で合法な string として通る。必要なのは D164 決定3どおり、公開入力を固定し secret wireだけを32点変えたときの **serialized sink bytes 同一性** である。[`decisions.md:8180`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8180) critic を seal 後へ移すなら、同じ検査を preseal auditor、staging、journal、WAL、rep evidence に適用すべきである。

---

### 11. major — global CAS 所見 A-6 が未処理で、別 origin の event が post-query commit を妨害できる

**主張:** reservation 後に別 origin が global state commitmentを動かすと、対象 origin 自身が不変でも後続 commit がCAS loserになる。再試行規則がない。

**静的確認:**

- state commitment は authority内の全 origin headとsemantic stateを含む。[`reflux_origin_ledger.py:2183`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2183)
- runtime/lock は git-common-dir 共有である。[`reflux_origin_ledger.py:1432`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1432)
- A-6 は既に real と裁定されている。[`s4-adjudication.md:68`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-producer-wiring/s4-adjudication.md:68)
- plan は reservation後に planner/coder/workload を実行するが、CAS loser時の「同じ候補・同じ予約を再 commitする」規則を定義しない。[`s2-plan.md:437`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:437)

**設計への効果:** seal 前漏洩と組み合わさると、不都合な結果の後だけ別 origin を動かして commitを失敗させる選択チャネルになり得る。per-origin CAS、または candidateを再生成せず current global baseへ同一 operationを安全に rebaseする exact retry契約が必要である。

---

### 12. minor — 既存期待値の変更はあるが、D96 手続自体は明示されている

**主張:** brief の「既存テスト期待値・公開 API・受理集合を変えない」は設計案と両立しない。ただし設計案はこの点を隠しておらず、D96を明示している。

**静的確認:**

- brief は既存期待値と受理集合を変えないとする。[`brief.md:144`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/brief.md:144)
- reservation event は現3-event uniform pathを変更するため新D対象だと明記される。[`s2-plan.md:481`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:481)
- report v3と新 `origin-proof` eventを追加する。[`s2-plan.md:600`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:600)
- 現 completeness は閉じた event 集合であり、未知 event を拒否する。[`autonomous_trial_completeness.py:40`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:40) [`test_autonomous_trial_completeness.py:984`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_autonomous_trial_completeness.py:984)
- report v2期待も固定されている。[`test_p3_autonomous_workload_trial.py:519`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_p3_autonomous_workload_trial.py:519)
- 設計案は新D、report/completeness/registry/境界テストの同一変更単位を明記する。[`s2-plan.md:616`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/insights/2026-08-05_t244-p3-design/s2-plan.md:616)

**設計への効果:** brief の不変条件を削除・訂正すべきだが、隠れた D96 違反ではない。複数候補を後続 wave に送ることも、現 wave が複数候補を受理しない限り裁定済み (5) に反しない。

## 総括

### (a) GO / NO-GO

**NO-GO — production bootstrap が予算 root の再生成を可能にする一方、successor の累積予算、full-manifest sink binding、seal 前 storage、crash recovery、対象条件まで到達する発火 gate が閉じていない。**

### (b) blocker

- #1 候補数と member row 数を同じ `batch cardinality` と記録する恒真化
- #2 別 clone／全 runtime 削除による新品予算
- #3 successor の semantic-equivalent 新 originによる新品予算と未定義 transition table
- #4 preimage commit topologyと bytes sourceの二義性
- #5 full manifestが実 execution sinkまで束縛されない A-2
- #6 seal 前 artifact／raw storageからの membership・metrics漏洩
- #8 reservation／seal／sidecarの回復不能・durability欠落
- #9 baseline gateの大半が前段停止または schema不在の代理赤

### (c) N1〜N14 / P1〜P7 のうち誤りと判定したもの

- **N6:** 誤り。s2-plan の訂正どおり、`CURRENT_PIN` はfull OID preimageではない。
- **N3:** コード事実は真。ただし「合法 ledger member batch」を「D121 の候補 batch」と一般化する意味付けは誤り。
- **P1:** D147 型の予算 root 回避を閉じる解としては誤り。
- **P2:** 旧 counterを保存するだけで successor の新品予算を防げる、という点が誤り。
- **P3:** proseで anti-oracle 非充足を名乗れば十分、という点が誤り。artifact型でも候補数1を固定する必要がある。
- **P7:** producer側 artifactという層選択は妥当だが、提案順序で「durable」とする部分は誤り。

N13・N14は実コード上で真。その他の N は今回の静的範囲では覆していない。

### (d) そのまま採ってよい部分

- 公開 ledger APIを `create=False` のまま保ち、lazy-createを禁止する判断。
- admin CLIに `--runtime-root`、`--fixture`、`--force`、`--reset` を設けない判断。
- コード自身の source hashを authority trust rootにせず、名前付き semantic artifactを用意する判断。
- 現 `s8a_trigger_gating_coverage.json` を evidenceに採用せず、environment contract由来で再測定する P6。
- 8cを非認定 pilotのまま保ち、`certifying=False`、cap=1、P3/P4未充足を維持する P4。
- 予算値を caller literalにせず authority不変値として受ける P5。
- candidate生成前の no-refund reservationという原則、および criticをLayer 3 admission・seal後へ移す判断。
- reservation/report v3/複数候補について新Dと境界テストを同一変更単位にする D96 方針。

pytest は実行しておらず、テスト成功は主張しない。