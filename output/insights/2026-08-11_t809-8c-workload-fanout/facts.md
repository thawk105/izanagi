# [T-809] 事実表 — 8c trial の workload 単位 fan-out

> **訂正 (段 2 の指摘を親が裏取りした結果、2026-08-11)。**
> 1. **probe 903110 の実行ノードは `bnode019`** である (`probe/job-0-903110.nqsv/env.txt`)。
>    `bnode033` は 1 本前の 903102。親が §E の見出しで取り違えていた。
> 2. **「部分成功 = fail-stop」は広すぎた。** 外側 loop を止めるのは例外 (`supervisor-error`) と
>    wall 切れだけで、**`role-invalid` は当該 cell を止めるが次の workload へ進む**
>    (`p3_autonomous_workload_trial.py:1727-1733` の `break` は generation loop、`:1459` で
>    cell を append して継続)。2026-07-29 dry-run の「他 cell は続行」と一致する。
> 3. **build cache の claim 衝突は process を落とさない。** `BuildCacheError` は `RuntimeError`
>    派生で (`buildcache.py:54`)、`pipeline.py:798` の `except (RuntimeError,
>    subprocess.SubprocessError)` が捕えて当該 variant を `build-error` abort へ隔離する。
>    失うのはその世代であって run 全体ではない。**恒久的な害は「build 途中で kill された
>    ときに残る stale claim」** で、これは以後その digest の build を全部止め手動回収を要する。
>    fan-out は kill 対象 process を N 倍にするのでこのリスクを増やす。
> 4. §C の「持ち越す状態は 4 つだけ」は**可変状態**についての主張である。run 単位で共有される
>    定数 (launch admission、transport admission / receipt、run-scope binding、CCBench base と
>    cache root) も存在する。
> 5. **未検証の段 2 指摘** (親は裏取りしていない): campaign identity の preimage に
>    execution contract が入らず世代数・descriptor 等が入ること、`s8b_prediction_runner.py` の
>    1200 秒定数の行番号、registered 再投入には新しい exact-six manifest が要ること。
>    段 3 のレンズはこれらも検証対象にしてよい。

一次資料は実コード (branch `worktree-dev-wave-t809-8c-fanout`、HEAD `856f4d4c`) と、
2026-08-11 に gen_S で取った probe (903102 = bnode033、903110 = bnode019) (request 903095 / 903102 / 903110)。
`docs/` の記述は一次資料と一致した範囲でだけ使う。

## A. 逐次 loop の実体

`orchestrator/campaign/p3_autonomous_workload_trial.py:1361` の
`for workload in selected:` が対象。1 反復で `_run_workload` → `_finalize_cell_admission` →
`_run_pending_critics` を回す。

**loop が workload 間で持ち越す「可変」状態は 4 つだけ** (run 単位で共有される定数 —
launch admission、transport admission / receipt、run-scope binding、CCBench base、cache root —
は別にある)。

| 持ち越す状態 | 実体 | 生成箇所 |
|---|---|---|
| journal | `AttemptJournal(run_root/"attempts.jsonl")` (単調 `seq`、fsync、`failed` sticky) | `:2083` |
| provider 集合 | `active_providers` (role 4 本、`CrossRoleSessionTracker` 共有) | `:2157`, `:1052` |
| build context | `build_run_context(...)` = process-local | `:2086` |
| wall 予算 | `started_monotonic` からの経過を `max_wall_s` と比較 | `:1362`, `:1683` |

**workload local (持ち越さない)**: `descriptor` / `cfg` / `campaign_id` / `layout` /
`current_metrics` / `prior_reverse` / cell の critic 待ち行列。`_run_workload:1659-1680` で毎回作り直す。
→ **workload 間に「合成の入力」としての依存は無い** (前 workload の結果は次 workload の
planner / coder payload に入らない)。ただし provider の session 相異検査、共有 wall、
fatal 時の break は workload を跨いで効く。**「独立」と言えるのは合成入力についてだけである。**

## B. 正式経路は既に 1 trial = 1 workload

- `trial_registry.py:1024` — `workloads != [holdout の workload]` を `workload-binding` で拒否。
- `trial_registry.py:1272` — `admission.workloads != (binding.workload,)` を拒否。
- `trial_registry.py:2189` — 受入は `report_paths` を**ちょうど 6 本**要求する
  (manifest の trial 集合と exact 一致、`trial-set`)。
- したがって `--workloads a,b,c` の複数指定が使えるのは
  `--allow-unregistered-exploratory` の探索 pilot だけである。
  **正式系列では「1 workload = 1 process = 1 report」が既に唯一の形。**

## C. 分離できるもの / できないもの

| 資源 | fan-out 時の状態 | 根拠 |
|---|---|---|
| run root | 完全分離可 (`run_root` は新規 dir 必須) | `:2061-2066` |
| journal | run root 配下なので分離される。`seq` は run 内で閉じる | `:2083`, `:470-501` |
| report | run root 配下。`attempt_journal_sha256` で journal と 1:1 に束縛 | `:1559-1563` |
| campaign root (`--no-build`) | `run_root/campaigns/<campaign_id>` = 分離 | `:1655-1657` |
| campaign root (build) | `exploration_campaign_layout(campaign_id)` = **共有 root 下の別 dir**。<br>`campaign_id` の preimage は `spec_content` / `ccbench_commit` / `search_tag` /<br>`search_config` (workload・ycsb flags・records・threads・descriptor sha・**generation_budget**・<br>stop_policy・admission policy 等) / `trial` (= `<trial_id>-<workload>`)。<br>**execution contract は identity に入らない** (runtime carrier)。process 由来の値も入らない | `ident.py:151-178`, `model.py:66-84`, `:504-541` |
| build context | process-local が仕様。1 process 1 個で足りる | `build_admission.py:148-170` |
| provider | `run_root/provider/<role>` 配下なので分離される | `:1092` |
| lifecycle 台帳 | `flock(LOCK_EX)` で直列化。start/terminal とも trial_id 単位で once | `trial_registry.py:1482`, `:1580` |
| wall 予算 | **共有**。1 process 1 予算なので fan-out すると N 個の独立予算になる | `:1362`, `:1683` |
| bench (計測) | **同一ノードでは排他**。`bench_lock()` 取得直後に `competing_bench_pids()` を再検査 | `pipeline.py:370-378` |
| session 相異検査 | `CrossRoleSessionTracker` は process-local と明記。逐次では 1 trial 内の全 workload ×<br>全 role を 1 集合として検査するが、fan-out すると process 内 4 role だけに縮む | `role_session_isolation.py:1-9`, `:53-66` |

## C-2. build cache — 衝突ではなく「再利用の喪失」が本当の制約 (段 3 で訂正済み)

**訂正前の本節は「別 workload が同じ genome を合成すると claim が衝突する」と書いていた。
標準 CLI の build 経路では成立しない。** 親が実コードで裏取りした結果は次のとおり。

- cache identity (`buildcache.py:246-266` `_v2_identity`) は `admission` を含み、
  `admission` の body は `SourceEvidence.as_receipt()` を含む (`build_admission.py:108-114`, `:470-481`)。
  その receipt には **`source_root`** が入る (`source_digest.py:149-160`)。
  `source_root` は `os.path.realpath(os.path.abspath(sub))` (`source_digest.py:851`) である。
- build 経路の `sub` は `checkout(trigger.PIN, base_dir=fixed_sub)` が作る
  **process ごとに一意な使い捨て worktree** (`p3_autonomous_workload_trial.py:2327`,
  `patchharness.py:288-306`) で、driver はこれを `ccbench_dir=sub` として build へ渡す
  (`p3_s4_loop_trigger_gating.py:599`)。
- したがって **2 process の build digest は必ず異なる。claim (`<digest>.building`) は衝突しない。**
- **代わりに失うのは run 内の cache 再利用である。** 1 process 内では全 workload・全世代が
  同じ `source_root` を共有するので、同一 genome の 2 度目は cache hit になる
  (WAL 実測で build は cache hit 込み p50 0.3 s、fresh は p90 45.2 s / max 46.7 s)。
  fan-out するとこの共有が消え、同じ genome でも作り直しになる。
  **同一 genome は現に起きている** — 2026-07-29 dry-run で workload B の提案は A と同一だった。
  1 世代あたり trace/perf の 2 build なので、失う量は (重複 genome 数 × 2 × fresh build 時間)。
- claim が問題になるのは、将来 process 間で `ccbench_dir` を共有して cache を再利用しようと
  した場合である。そのときは create-only claim (`buildcache.py:658-679`) が競合しうる。
  衝突しても process は落ちず、`BuildCacheError` (`RuntimeError` 派生) を `pipeline.py:798` が
  捕えて当該 variant を `build-error` abort へ隔離する。**恒久的な害は stale claim** で、
  kill だけでなく claim 取得後の configure / build / validation / publish の失敗でも残り
  (`buildcache.py:701-793`)、以後その digest の build を全部止めて手動回収を要求する。

## C-3. 共有 git metadata (残る実務上の結合)

`checkout` の使い捨て worktree は `git worktree add` / `remove` / `prune` を
**共有 base (`external/ccbench`) の worktree 登録簿**に対して行う (`patchharness.py:291-306`)。
fan-out 用の明示 lock は無い。並行実行の残骸は別問題として残る。

## D. 部分成功と再投入の現状

- **外側 loop を止めるのは例外と wall 切れだけ。** `role-invalid` (planner/coder/auditor の
  parse 失敗) は当該 cell の generation loop を止めるが、cell は通常どおり append され
  **次の workload へ進む** (`:1727-1733` の break は generation loop、`:1459`)。
  例外は `fatal_error` を立てて `break` し、k+1 以降は cell すら作られない (`:1393-1458`)。
  `status` は
  `len(cells) == len(selected)` かつ fatal 無し かつ全 cell の `stop_reason` が
  `{role-invalid, supervisor-error, supervisor-wall-budget}` の外、のときだけ `complete` (`:1491-1501`)。
- **wall 切れも同じ形。** workload 先頭で残 wall が尽きると `supervisor-wall-budget` で break (`:1362-1371`)。
- **resume は無い。** `run_root は新規 directory 必須 (resume は MVP 範囲外)` (`:2065`)。
- **同一 trial_id の再投入は構造的に不可。** registered mode は
  `record_trial_start_once` が `lifecycle-start-once` で拒否する (`trial_registry.py:1580-1584`)。
  **しかも新 trial_id を 1 本足すだけでは足りない** — manifest は exact 6 trial で
  (`trial_registry.py:322-357`)、受入は 6 report と manifest hash の一致を要求する (`:2189`)。
  clean な再実験は新しい exact-six manifest と新しい 6 ID を要する。
  **ただしこれは「やってよい」を意味しない** — 失敗系列を残したまま成功するまで新系列を作れば
  repeat-until-success になる。8b の裁定は crash 後の再走なし・実験全体を判定不能とする。
- 中断時の証拠保全は journal だけではない。registered では lifecycle に
  `terminal_status="indeterminate"` が残る (`:1910-1934`, `trial_registry.py:1640-1665`)。
  ただし強制 kill では terminal 行自体が残らない。

## E. 実測 (2026-08-11, gen_S bnode019, request 903110)

条件: `--provider fixture --no-build --max-generations 1 --allow-unregistered-exploratory`。
**LLM 4 役も build も bench も含まない supervisor 配線だけの計測である。**
`IZANAGI_EXPLORATION_OUTPUT_ROOT` は非 git base (`/work/1/SFC/tanab/izanagi-jobs`)。

| arm | 形 | wall (s) | rc | status |
|---|---|---:|---:|---|
| A | 1 process = 1 workload (ycsb-a) | 1.122 | 0 | complete |
| B | 1 process = 3 workload 逐次 (現行) | 2.006 | 0 | complete (3 cell) |
| B2 | 同上 再走 | 2.027 | 0 | complete (3 cell) |
| C | 3 process = 各 1 workload 同時 | **1.189** (個別 0.947 / 1.068 / 1.185) | 0,0,0 | 3 本とも complete |

- **3 process 同時実行は衝突ゼロ**。run root・journal・campaign root・provider・namespace marker の
  いずれも競合しなかった。
- process あたり固定費 ≈ 0.68 s、workload あたり限界費 ≈ 0.44 s (B と A の差から)。
  fan-out は wall を 2.006 → 1.189 s (1.69×) にする代わりに process 固定費を 2 本分足す。
- **この 1.69× を本番の期待値として使ってはいけない。** 本番 1 世代の内訳は
  role 4 呼び (各上限 1200 s、`s8b_prediction_runner.py:71`) と
  build+verify+bench (既存 WAL n=51 で p50 147.0 s / max 406.3 s、
  `output/insights/2026-08-01_8c-one-allocation-budget-design.md` §1.1) である。

## E-2. 既存 docs が既に書いている関連事実 (`docs/phase3-s8c-autonomous-trial-runbook.md` §既知の限界)

一次資料と突き合わせて一致を確認した範囲だけ引く。

- **build 経路では `--run-root` を変えても campaign 状態は同一。** campaign root は cfg の内容 hash で
  決まるので、同じ workload/config なら別 run root でも同じ campaign root になる。
  crash 後の再開は run root の変更でなく**新しい trial id** で行う (trial は campaign ID の preimage)。
  → 実コードと一致 (`ident.campaign_id(cfg)`、`cfg.trial = f"{trial_id}-{workload}"`)。
- **「freshness 検査と state 生成の並行 race は保証対象外であり、同じ trial/config の 2 supervisor が
  同時に検査を通過しうる」** と明記されている。**workload を分けた fan-out ではこの race は
  起きない** (campaign_id が workload を含むため) が、同一 workload を 2 本立てると起きる。
- 「1 cell が stale だと supervisor-error となり、**同 invocation の後続 workload も走らない**」 —
  fail-stop の記述と一致。
- `--max-wall-seconds` は **hard wall でも safety 上限でもない**。検査は workload と generation の
  先頭だけで、超過後も 1 世代分 (role 1 呼びで最大 1200 秒) 新規に開始しうる。
- 次の正式系列は **H1 rr80 / H2 rr20 × descriptor on/off/swapped**、同一 generation budget、
  同一 correctness gate、固定 stop、全 attempt 報告。A/B/C は operational pilot であり昇格させない。
- login node での build/bench は禁止、campaign の計算ノード dispatch 経路は未実装 (§3.3 注記)。

## F. 実測で判明した運用事実 (probe 2 本を空費した原因)

1. **`PBS_JOBID` はコロンを含む** (`0:903095.nqsv`)。これを `PATH` に載る directory 名へ
   使うとコロンが `PATH` の区切りとして働き、python3.10 shim が丸ごと無効になる。
   実測では全 arm が Intel python 3.9.13 で走り `dataclass(slots=True)` で落ちた (request 903095)。
2. **`IZANAGI_EXPLORATION_OUTPUT_ROOT` は git 配下を拒否する** (`layout.py:329-332` の
   `_has_git_ancestor`)。runbook §8 が指す「job 専用の /work 配下」として自然な
   `/work/1/SFC/tanab/dev-wave-jobs/` は `.git` を持つため拒否された (request 903102)。
3. **login ノードでは trial 自体が走らない** —
   `ExecutionGuardError: 計測用 env bytes は site='PEGASUS_LOGIN' では生成できない` (login 実測)。
