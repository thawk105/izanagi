# 段 1 brief — [T-244] P3 producer 結線

wave: dev-wave-t244-p3-producer-wiring / branch: worktree-dev-wave-t244-p3-producer-wiring
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring
起点 main: 55c2e84。受入環境 = この worktree の repo root で `python3 tools/run_tests.py` (login
ノードでは gen_S へ自動 dispatch。機体固有情報は `docs/pegasus-runbook.md`)。

## 目的 (command 引数)

prototype (D159) を production caller へ結線し、P7 (consumer が origin proof を要求) とは面を分ける。
D159 決定 (4) と s4-adjudication の U-G が「P3 の充足は producer 結線 + P7 まで含める」と裁定済み。

## 段 1 前提実測 (すべて本 worktree で実測。既存 docs は根拠にしていない)

- **M1** `orchestrator/campaign/reflux_origin_authority_v1.json` の実 bytes は
  `{"authority_schema":"izanagi-reflux-origin-authority/v1","origins":[]}` — production authority は空。
- **M2** `_store_for_repo` (reflux_origin_ledger.py:1160-1169) の runtime root は
  `<git-common-dir>/izanagi/reflux-origin-ledger/v1`。実 path は未作成 = production 実行歴ゼロ。
  **worktree をまたいで共有される** (git-common-dir は main repo の `.git`) ため、本 wave のテストは
  private test seam `_fixture_store_for_test` (同 2317) の temp Git repo だけを使う。
- **M3** `batch_cardinality_min` は `_integer(..., minimum=2)` で hard 強制 (同 292)。query floor は
  `required_queries >= max(2, batch_min)` かつ `<= qmax` (同 281)。**予算消費は batch commit 経由**の
  ため、cardinality 1 では 1 query も消費できない。
- **M4** 8c 自律 trial は `MAX_APPROVED_GENERATIONS = 1` (p3_autonomous_workload_trial.py:143)、
  `attempt_policy = {"attempts_per_role_generation": 1, "retry": False}` (同 1014) → 1 cell あたり候補 1 点。
- **M5** E 段 loop は 1 invocation = 1 iteration = 1 proposal
  (p3_s4_loop_trigger_gating.py:611 `run_one_iteration` / 688 `run_iteration_with_proposal`)。
- **M6** coder proposal schema は D160 決定 (1) で `{axis, wire}` の 1 点に閉じている。
- **M7** (DW-O09/O10 pin 閉包) ledger / authority path を bytes で pin する production 台帳・test・
  trust root は 0 件 (`grep -rn` の hit は `output/insights/` の設計逐語のみ)。`FROZEN_MANIFEST` は
  `orchestrator/tests/` の 3 file にあり対象は `output/` 配下だけ。role 名 key の review ledger 側でも
  `reflux_origin` を検索し 0 件。durable manifest の再発行は不要。
- **M8** (DW-O08) `git submodule update --init` 済み。`tools/check_wave_startup.py --external-handoff` = OK。
- **M9 (段 2 投入後に追加実測)** trial artifact の consumer `autonomous_trial_completeness` は
  `attempt` が厳密に 1、`retry` が false であることを要求し、既存境界テスト
  `orchestrator/tests/test_autonomous_trial_completeness.py:678-694`
  (`test_attempt_policy_requires_attempt_one_and_retry_false`) が `attempt=2` を拒否する側で pin して
  いる。したがって **provisional (P2) の「attempts_per_role_generation >= 2」は consumer の受理集合を
  変えずには実装できず、既存テストの期待値変更 (DW-S05-B が禁止) を強いる**。(P2) と (P4)
  (「本 wave は consumer に触れない」) は現状のままでは両立しない。この矛盾の解き方 —
  (a) D96 手続を踏んで consumer を同一変更単位で改訂する、(b) 結線先を変える、(c) 実装しないと裁定して
  裁定パッケージへ返す — は段 3 の攻撃対象とし、段 4 で裁定する。

- **M10 (段 2 の指摘を親が実測で裏取り)** ledger の runtime store を**作る経路は private test seam
  `_fixture_store_for_test` (reflux_origin_ledger.py:2317-2333) の `_locked(store, create=True)` 1 点だけ**で
  ある。公開 API 3 本 (`read_origin` 2780 / `commit_event` 2793 / `read_sealed_batch` 2807) はいずれも
  `_locked(store)` = `create=False` で呼び、`_locked` は `create` が偽なら `O_CREAT` を付けずに
  lock を開くため (同 1392-1399) 未初期化 repo では必ず `cannot open authority lock` で失敗する。
  親が production 経路で実行して確認した (`L.read_origin('0'*64)` →
  `RefluxOriginLedgerError: cannot open authority lock`、runtime dir は作られないまま)。
  **すなわち prototype は現状 production では起動できず、「結線」には leaf 側へ production bootstrap を
  足す必要がある。** 本 brief の不変条件「ledger leaf の公開 API は変えない」はここで発火する。
- **M11 (段 2 の指摘。親は未裁定)** authority registry の entry を読んで `AuthorityManifest` を得る
  公開 reader が無い (`_manifest_from_object` は private、同 344)。caller は 13 field を自力で
  再構築するしかなく、`axis_semantics_sha256` / `verifier_policy_sha256` などは preimage の定義自体が
  repo に存在しない。定義を置くことは origin 識別を恒久的に固定する設計判断であり、D121 P10
  (origin authority のユーザー裁定) の射程に入る。

**M3〜M6 の帰結 (本 wave の中心事実):** 現行 production caller はどれも cardinality >= 2 の batch を
形成できない。したがって「admission だけ結線する」形では予算を 1 も消費せず、同一 origin で trial を
何度でも回せる — 予算束縛 (D121 決定 5) の実体を持たない。

## provisional 裁定 (親の暫定。すべて攻撃対象)

- **(P1) 結線先は 8c 自律 trial (`p3_autonomous_workload_trial.run_trial`) 1 点**とし、E 段 loop は
  今 wave では触らない。理由 = 予算は generation budget を持つ層に束ねるのが D121 決定 (5) の形。
  成果物影響: 結線しなければ certified 選択・材料レポート・試行台帳・proof chain は現在値のまま不変で、
  P3 は FAIL のまま (D159 決定 4 の会計)。
- **(P2) batch は「1 iteration 内の複数 coder 呼び出し」で形成する。** coder の出力 schema (D160) は
  変えず、`attempts_per_role_generation >= batch_cardinality_min` の origin 束縛 trial だけを新設し、
  全候補を commit し終えるまで preview / build / verify を 1 件も走らせない。
  成果物影響: これを実装しないと予算消費が 0 のままで、origin 予算は受理集合にも台帳値にも一切効かない。
- **(P3) 既定挙動は byte 単位で不変。** 発火は `--reflux-origin <origin_id>` の明示 opt-in のみで、
  未指定なら ledger を import すらしない。authority への entry 登録は本 wave では**行わない**
  (予算値と origin authority は D121 P10 = ユーザー裁定待ち、D159 決定 4 の「捏造登録しない」)。
  成果物影響: 既存 artifact の受理集合・凍結 bytes・proof chain は不変。
- **(P4) P7 との面の切り方** = 「origin proof を *許す*」までが本 wave、「origin proof を *要求する*」は
  P7。formal report / proof chain / `layer3_report` / WAL stage 集合には触れない。
  成果物影響: 触れば材料レポートが control event を実在しない棄却候補として数える (設計本文 ⑥ の既知不具合)。
- **(P5) DW-G04 の発火 gate に関する自己申告:** authority registry が空である限り、opt-in path は
  **fail-closed で拒否する側だけが発火する**。「受理して予算を消費する」側の発火条件を満たす既存
  artifact path は書けない (P10 裁定待ち)。これを DW-G04 違反と読むか、拒否側の発火で足りると読むかは
  段 3 の攻撃対象とし、段 4 で裁定する。

- **(P1') 親が M9 の後に見つけた代案 — レンズはこれも攻撃すること。** 結線先を E 段 loop
  (`p3_s4_loop_trigger_gating.run_iteration_with_proposal`, 同 688) にすると、attempt_policy の pin
  (M9) を踏まない。E 段 loop は proposal を外部 JSON file から受けるため (`load_proposal_file`, 同 649)、
  **batch は「どちらも走らせる前に 2 本以上の proposal file を用意して commit する」だけで形成でき、
  coder の出力 schema (D160) も role 呼び出し回数の契約も変えずに済む**。origin session は loop の
  上位に置き、候補が committed batch に含まれないなら loop を fail-closed で拒否する。
  未検証の前提 = 「E 段 loop の artifact を受理集合で縛る consumer に、iteration / proposal の
  cardinality を pin するものが無い」。レンズはこれを実ファイルで検証すること。

## 不変条件

- 正しさゲートを緩めない。既存テストの期待値を変更しない。
- docs / commit は親のみ。実装面は Codex `role=author` が書く。
- `MAX_APPROVED_GENERATIONS = 1` と D114 の cap は変えない。
- ledger leaf (`reflux_origin_ledger.py`) の公開 API と受理集合は変えない (必要が出たら停止して裁定へ)。

## 成果物の形

`orchestrator/campaign/` の新 producer leaf + `orchestrator/tests/` の専用テスト + trial への opt-in 結線。
docs は spool fragment (worklog / decisions) と insights 逐語。

## 分割方針

段 5 は所有素集合で 2 単位を想定 — 単位 A = producer leaf + そのテスト、単位 B = trial 側 opt-in 結線 +
そのテスト。B は A に依存するため A 完了後に所有パス限定 patch を展開して投入する。
