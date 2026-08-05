# 段 1 brief — [T-244] P3 (1)(2)(3) 設計起草

wave: dev-wave-t244-p3-design / branch: `worktree-dev-wave-t244-p3-design`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design`
起点 main: `3075a8fd`。受入環境 = この worktree の repo root で `python3 tools/run_tests.py`
(login ノードでは計算ノードへ自動 dispatch。機体固有情報は `docs/pegasus-runbook.md`)。

## 目的 (command 引数)

worklog (200) のユーザー裁定で設計 wave へ委任された **(1) origin authority の実体化・
(2) production runtime bootstrap と authority 世代移行の主体・契約・(3) 結線先と batch 形状**
について、推奨付き裁定パッケージを起草して返す。**(4)** (origin proof の durable
cross-reference を producer 側で今出す) と **(5)** (複数候補を通すなら D96 手続) は裁定済みで、
本 wave は前提として使う。**D163 の「prototype が production で起動できない」の解消案まで含める**
(command 引数の明示要求)。scope 外 real 所見 8 件 (A-2 / A-5 / A-6 / A-7 / A-8 / A-13 / B-4 / B-6、
一次資料 = `output/insights/2026-08-05_t244-p3-producer-wiring/s4-adjudication.md`) は本 wave の入力。

## 段 1 前提実測 (すべて本 worktree・起点 3075a8fd で実測。既存 docs は根拠にしていない)

- **N1 (承認済み裁定の前提が動いた)** entry (198) / D163 が見た ledger は **v1**、現 main は
  **v2** である。`AUTHORITY_RELATIVE_PATH = orchestrator/campaign/reflux_origin_authority_v2.json`
  (`reflux_origin_ledger.py:74`)、実 bytes は
  `{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}` = **空のまま**。
  間に P4 wave (`61fc5202`、D166) が land した。**(198) の裁定パッケージの file:line はすべて stale。**
- **N2 (D163 決定 2 は現 main でも成立する)** 親が production 経路で `read_origin('0'*64)` を実行し
  `RefluxOriginLedgerError: cannot open authority lock` を確認した。runtime dir
  (`<git-common-dir>/izanagi/…`) は作られないまま。genesis は private test seam
  `_fixture_store_for_test` (`reflux_origin_ledger.py:2642-2655`) の `_locked(store, create=True)`
  1 点のみで、公開 API 3 本 (`read_origin` 3105 / `commit_event` 3112 / `read_sealed_batch` 3132)
  はいずれも `_locked(store)` = `create=False`。**prototype は現状 production で起動できない。**
- **N3 (本 wave の中心的新事実)** **batch の distinct 制約は「候補平文」でなく「commitment」に掛かる**
  (`reflux_origin_ledger.py:1102-1106`)。commitment の preimage は
  `(candidate_wire_b64, query_ordinal, replicate_ordinal)` (`同 608-619`) で、query ordinal は
  origin 連続を強制される (`同 1107-1109`)。したがって **同一候補 1 点の R 回反復測定だけで
  cardinality >= 2 の合法 batch が成立する**。D166 決定 1 が旧実装の候補平文 distinct 強制を撤回した
  ことの帰結であり、**(198) の「複数候補にしないと batch を作れない → D96 手続が要る」という
  中心的閉塞は弱まっている**。ただし後述 (P3) のとおり、これは予算束縛を実体化するだけで
  軸 (iii) の反 oracle 性は満たさない。
- **N4 (producer 結線はゼロのまま)** `reflux_origin_ledger` を import する production module は
  0 件 (自分自身のテストのみ)。receipt・snapshot・sealed batch を消費する consumer も 0 件。
- **N5 (公開 authority reader は無い)** `__all__` (`同 43-70`) が公開するのは型・
  `canonical_manifest_bytes` / `derive_origin_id` / `derive_cell_key` と API 3 本のみ。
  `_manifest_from_object` は private (`同 364`)。caller は 13 field を自力で再構築するしかない。
  `OriginSnapshot` (`同 539-551`) は manifest / cell key / budget policy / open batch のいずれも持たず、
  `SealedBatch` (`同 554-558`) は trial / campaign / report への参照を持たない (B-6 は現 main でも real)。
- **N6 (manifest 13 field の preimage 可用性 — (198) の「機械導出できるのは workload のみ」を訂正)**
  現 production に preimage 規則が**既に在る**のは 3 件 — `environment_contract_sha256` =
  `env_contract.ExecutionEnvironmentContract.contract_sha256` (全 field の canonical JSON の sha256、
  `env_contract.py:150-160`、`loop.py:91` が実使用)、`workload.descriptor_sha256` =
  `descriptor_record["output_sha256"]` (`p3_autonomous_workload_trial.py:541`)、`ccbench_commit_oid` =
  `pin.CURRENT_PIN` (`pin.py:28`)。**部品が在るが束ねられていない**のが 1 件 — `role_bundle_sha256`
  は 4 role の `role_file_sha256` / `effective_prompt_sha256` が既に計算されている
  (`p3_autonomous_workload_trial.py:426-427`) が bundle 化の正準規則が無い。**preimage 規則が
  repo に存在しない**のは 5 件 — `spec_content_sha256` / `axis_semantics_sha256` /
  `verifier_policy_sha256` / `candidate_ir.{schema_ref, canonical_emitter_sha256}` /
  `recipient_projection_schema_sha256`。**authority が値を入れるしかない**のが 4 件 —
  `authority_series_id` / `budget_policy` / `stock_certification_ref` / `structural_zero_evidence_ref`。
- **N7 (clocks 食い違いの根本原因を特定した)** 候補 artifact
  `output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json` の `env_tag` は
  `linux-baremetal`、`clocks_per_us` は `2100`。現 registry の linux-baremetal は **1800**、
  pegasus が 2100 (`env_contract.py:169-193`)。原因は artifact 破損ではなく **producer の
  hardcode** で、`s8a_trigger_coverage.py:63-64` が `ENV_TAG = "linux-baremetal"` と `CLK = 2100` を
  literal 保持している。2100 は `sweep.py:129` が「TSC を実測できないときの CCBench default
  fallback」として使う値と同一であり、**この artifact の clocks は linux-baremetal の実測値ではない**
  疑いが強い。したがって現状のままでは `structural_zero_evidence_ref` に採用できない。
- **N8 (世代交代機構の実装済み前例がある)** `s8b_ratified_freeze.py` が承認 record・active pointer
  連鎖・revocation / cancellation tombstone・**transition table (変わってよい JSON Pointer の完全列挙、
  列挙外は前世代と厳密一致)**・fail-closed「active なし」既定・導入 commit の provenance 検査・
  legacy 世代の型分離を実装している (`同 6-24, 113-141`)。[T-478] の較正 contract 世代移行 wave
  (worklog (219)) が「推奨機構は新発明でなく既存型の適用」と裁定済みで、同じ型が (2) にも効く。
  D165 (段 8c 事前登録の hash 世代台帳) も同型の第 2 例である。
- **N9 (結線先の制約は現 main でも不変)** 8c driver の `WORKLOADS` は `ycsb-a/b/c` の 3 点のみ
  (`p3_autonomous_workload_trial.py:171-175`)。正式系列の holdout は H1=rr80 / H2=rr20
  (`trial_registry.py:46-49`) で **driver が回せない** (B-4 は real)。`trial_registry` は
  `certifying=False` / `arm_binding="declared-only"` (`同 124-129`) のまま。
  `MAX_APPROVED_GENERATIONS = 1` (`p3_autonomous_workload_trial.py:143`)、
  `attempt_policy = {"attempts_per_role_generation": 1, "retry": False}` (`同 1014`)。
- **N10 (完全性 consumer の pin は現 main でも不変)** `autonomous_trial_completeness.py:192-195` が
  `attempt` 厳密 1 / `retry` false を要求し、境界テスト
  `test_autonomous_trial_completeness.py:682` が固定する。**ただしこの pin が縛るのは role-attempt
  (LLM 呼出し) であって bench 測定の反復ではない** — N3 の replicate 経路がこの pin を踏むかは
  段 2 が file:line で確定すること。
- **N13 (D163 決定 2 より強い事実。親が実測)** production runtime の初期化は「呼ばれていない」のではなく
  **実装が明示的に禁止している** — `_initialize_locked` の冒頭が
  `if not store.fixture: _fail("production runtime initialization is forbidden")`
  (`reflux_origin_ledger.py:2591-2592`) である。したがって D163 の起動不能は「公開 API に
  create=True の入口が無い」という**欠落**ではなく、**意図的な禁止**である。解消案は新しい入口を
  足すだけでは足りず、**この禁止を条件付きで解除する契約**を伴う (= 受理集合の変更)。
- **N14 (bootstrap の一回性。親が実測)** runtime genesis は authority registry の**全 entry を
  その場で列挙して**各 origin の genesis event を作り (`同 2596-2623`)、runtime head の opening
  record に `authority_blob_sha256` と `origin_heads` を焼く (`同 2624-2632`)。読み出し側は
  authority blob sha の一致 (`同 2293-2294` = `authority version mismatch`) と
  **origin_heads の件数が `len(authority.entries)` と厳密一致すること** (`同 2296-2297`) を要求する。
  origin を後から足す event 型は存在しない (`OriginEvent` = BatchCommitted / BatchResultsPrepared /
  BatchSealed / OriginSealed、`同 531-536`)。**すなわち最初の genesis が、その runtime で今後存在しうる
  origin 集合を永久に固定する。** authority file を 1 byte でも変えると (無関係な origin の追加でも)
  runtime 全体が読めなくなる。これは (2) が「あれば良い設計」ではなく **bootstrap の前提そのもの**で
  あることを意味する。
- **N11 (DW-O08)** `git submodule update --init` 済み (`external/ccbench` = `d706650`)。
  `tools/check_wave_startup.py --external-handoff` = OK (fresh、local main 乖離 0)。
- **N12 (DW-O09/O10 の再評価)** 本 wave は**実装差分を作らない設計起草**であり、凍結成果物の bytes を
  変えない。ただし起草する設計は `s8a_trigger_gating_coverage.json` を manifest の evidence ref に
  pin する案を含むため、**採用後の pin 閉包を設計本文に列挙する義務**を成果物要件に入れる。

## provisional 裁定 (親の暫定。すべて攻撃対象)

- **(P1) D163 の起動不能は「明示 provisioning operation の新設 + N13 の禁止の条件付き解除」で解く。**
  公開 API 3 本は `create=False` のまま据え置き、genesis は独立した冪等 provisioning 経路
  (authority registry に有効 entry が 1 件以上あることを前提条件とし、authority blob の sha を
  runtime genesis へ焼く) として分離する。**N13 の `production runtime initialization is forbidden` は
  削除でなく条件化する** — 解除条件 (誰が・何を確認して・どの世代で) を契約として書き、
  条件を満たさない呼出しは従来どおり fail-closed で拒否する。lazy-create は採らない —
  runtime root が git-common-dir 共有 (A-6) のため、迷い込んだ 1 呼出しが全 worktree 共有の
  ledger を無音で作る。**git-common-dir 束縛自体は維持を推奨** — worktree を切れば予算が新品に
  なる経路を塞ぐ反回避性質だからである。成果物影響: 解かなければ producer 結線は永久に
  起票できず、P3 は FAIL のまま、cap-lift 上限 1 (D114) も不変。
- **(P2) authority 世代移行は N8 の既存型 (s8b_ratified_freeze) を適用し、新機構を発明しない。**
  active pointer 連鎖 + transition table + revocation tombstone + fail-closed「active なし」。
  **既存 origin の予算は世代を跨いで再束縛しない** — 移行は seal-and-succeed のみとし、
  in-place の manifest 差し替えを禁じる (差し替えを許すと予算が新品になる)。
  **N14 により、これは「あれば良い」ではなく bootstrap の必須前提である** — 世代移行を決めずに
  最初の genesis を打つと、その時点の origin 集合が永久に固定される。
  成果物影響: 決めないと authority 更新のたびに「全拒否 (authority version mismatch) か、消して
  counter を失う」の二択が残り、実運用の origin を一度も追加・更新できない。
- **(P3) 結線は 2 段階にし、第 1 段は「単一候補 × R replicate」の生死実験とする (N3)。**
  第 1 段は予算束縛を実体化し DW-G04 の受理側発火証拠を得るが、**軸 (iii) の反 oracle 性は
  満たさないと正直に名乗る** (候補 1 点では accept/reject の 1 bit membership oracle が残る)。
  第 2 段 (複数候補) は裁定済みの (5) に従い D96 手続を同一変更単位で踏む。
  成果物影響: 第 1 段を欠くと生きた 1 例が無いまま抽象を固めることになり DW-G01 に反する。
- **(P4) 結線先は 8c 自律 trial を第 1 段の宿主とし、pilot 限定であることを名乗りに書き込む (N9)。**
  正式 holdout (H1/H2) は driver が回せないため、第 1 段の成果は certified 選択の前進として
  数えない (B-7 と同じ会計)。成果物影響: 宿主を決めないと (1)(2) の契約が宙に浮く。
- **(P5) 予算値は authority が入れる不変制約として受け取り、コードへ literal を置かない (D147 決定 4)。**
  本 wave は具体値を決めず、**値を決めるのに必要な入力の一覧と floor 制約の形**だけを起草する。
- **(P6) `s8a_trigger_gating_coverage.json` は現状のまま evidence ref に採用しない (N7)。**
  推奨は「producer の hardcode を env contract 由来へ直し、再測定した artifact を採用する」。
  再測定が不可能なら別 evidence を選ぶ。**親は再測定の可否を実測していない** — linux-baremetal 機の
  可用性は段 2/3 の検証事項とし、不明なら「測定タスクとして別途起票」を推奨に含める。
- **(P7) (4) の durable cross-reference は `SealedBatch` / event 層でなく producer 側 artifact に置く。**
  ledger は trial / campaign / report を知らない (N5) ままとし、producer が
  `origin_id` / authority blob hash / batch id / seal commitment を自分の成果物へ書く。
  成果物影響: 出さないと P7 (consumer が origin proof を要求) が遡って信用できない。

## 不変条件

- 正しさゲートを緩めない。既存テストの期待値を変更しない。
- **本 wave は実装しない (docs のみ)。** 未裁定の設計択一を実装で既成事実にしない
  (D147 却下案 (a)・D153 却下案 (a)・D163 却下案 (d) と同型)。
- `MAX_APPROVED_GENERATIONS = 1` と D114 の cap を変えない。ledger 公開 API と受理集合を変えない。
- 「P3 充足」「P3 の部分実装」を名乗らない。P3 は FAIL のまま、cap-lift も FAIL。
- docs / commit は親のみ。実装面は生じない見込みだが、生じたら Codex `role=author` が書く。

## 成果物の形

`output/insights/2026-08-05_t244-p3-design/` に本 brief・段 2 プラン・敵対 2 レンズ・段 4 裁定・
**推奨付き裁定パッケージ (README = 正本)** を置く。台帳は spool fragment (worklog / decisions)。
裁定パッケージは (1)(2)(3) の各択一に **推奨 + 却下理由 + 成果物影響 1 行**を必ず添える。

## 分割方針

段 2 = codex read-only 1 本 (file:line 粒度の設計案)。段 3 = 敵対 2 レンズ並列 —
レンズ A = 正しさ境界・恒真化 (とくに N3 replicate 経路が軸 (iii) を偽装しないか、(P1) の
provisioning が予算回避経路を作らないか)、レンズ B = 実効性・会計・段取り (11 層のうち何層が
埋まるか、(P3) 第 1 段の名乗りが誇大でないか、N7 の再測定可否)。**親の実測 N1〜N12 と
その一般化もレンズの攻撃対象に含める。**
