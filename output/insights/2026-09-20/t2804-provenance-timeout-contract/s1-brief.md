# [T-2804] 段 1 brief — land の provenance 監査 timeout (480 秒) と dispatcher の queue 待ち上限 (900 秒) の両立契約

作成: 2026-09-20 21:08 JST。起点 local main `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad` (fresh worktree、開始 gate rc=0)。

## 研究前進 (1 行)

land (`tools/dev_wave_land.py`) は local main を進める唯一の経路であり、F975 では lock 外の全史 provenance 監査が完走できず 6 wave が 1 時間 26 分 main を進められなかった
(land 40 回のうち rc=29 が 8 回、内訳 rc=16 × 5・`TimeoutExpired after 480 seconds` × 2)。本 wave は「dispatch へ倒れた監査が queue 待ちだけで land に SIGKILL され、
job と pending orphan hold が残る」構造を、外側予算を内側へ伝播する契約 1 つで閉じ、延長の要否を裁定できる区間別の実測を残す。研究の主張・図表・値は変えない。

## 段 1 実測 (改善前、本 wave 着手時点)

### (a) provenance task の dispatch 受領証 85 件 (`probe/dispatch-stats-1.txt`、T-2609 の probe を read-only で再走、走査 root は同じ 6 glob)

| 区間 | n | 中央値 | p90 | 最大 |
|---|---:|---:|---:|---:|
| queue 待ち `queue_wait_s` | 85 | 5.2 秒 | 7.3 秒 | **716.5 秒** (2026-09-20 20:09、`dev-wave-fig13-b10-waiting-grid`、gen_S QUE 47 / HLD 104 / RUN 46) |
| 監査本体 (RUN 初観測→最終観測) | 85 | 30.7 秒 | — | 475.9 秒 (09-08 14:53、旧 checker) |
| 合計 (qsub→最終観測) | 85 | 37.1 秒 | — | 758.6 秒 |

合計の閾値別件数: > 300 秒 = 5、> 375 秒 = 2、> 480 秒 = 2 (482.3 秒 = 旧 checker の RUN 476 秒、758.6 秒 = 本日 queue 716 秒)。**375〜480 秒の帯に 1 件も無い。**
本日の 716 秒の件は child rc=2 (`HEAD が監査中に変化した`、queue 待ち 12 分の間に呼び手 worktree の HEAD が動いた) で、land からの呼び出しではない
(land なら 480 秒で SIGKILL され受領証が終端まで書かれない)。

### (b) land 側の構造 (`tools/dev_wave_land.py`)
- `_run_provenance_checker` (3555–3573) は `subprocess.run(..., timeout=480)`。`subprocess.run` の timeout は **SIGKILL** (grace 無し) → checker = in-process dispatcher なので
  `DispatchError` 経路 (qdel、orphan hold 昇格、receipt 保存、`_return_infra`) が一切走らず、qsub 前に create-only で置いた pending orphan hold と PBS job が残る。
- `_audit_provenance_history` (3576–3641) は `TimeoutExpired` を `provenance audit failed: TimeoutExpired after 480 seconds` (rc=29、retryable_same_request) へ写す。stderr は捨てる。
- 既存テストの pin: `orchestrator/tests/test_dev_wave_land.py:4820` (AST で `timeout` 定数 1 個、`_LAND_LOCK_WAIT_SECONDS` 180 + 480 + fold 外側 + 30 < 検査 watchdog 1280 の算術)、
  `:5843–5853` (subprocess.run の kwargs を exact 一致、env は `{**_git_env(), "PYTHONDONTWRITEBYTECODE": "1"}` の exact 一致)、`:9997` (TimeoutExpired 480 の写像)。

### (c) checker 側の構造 (`tools/check_ai_provenance.py`)
- dispatch 入口は 3 箇所: `--force-dispatch` (3586)、headroom_short ∧ queue 可 (3593–3595)、bounded local の cap_oom 後 (3648)。いずれも `_invoke_dispatch` → `_default_dispatch` (2882–2892)
  → `dispatch_compute.dispatch(argv, task="provenance", repo_root=REPO, **D612 override)`。**外側予算を受け取る入力は無く、`deadline_at` も渡していない。**
- `_dispatch_timeout_overrides` (2858–2879) は `tools/mutation_harness.py` の同名実装と bytes 同値を `test_t2337_dispatch_timeout_overrides.py` の meta-test で pin。

### (d) dispatcher 側の既存機構 (`tools/pegasus/dispatch_compute.py`、変更しない)
- 既定: queue 待ち 900 / walltime 3600 / grace 300 / accounting 60 / cleanup 90 (69–78)。
- `deadline_at` (monotonic、3570) は既存 kwarg。`total_deadline = min(submitted + W + G, deadline_at)` (4156–4159、RUN 初観測で再基準 4207–4211)、collection の締切 (4245–4247)、
  `claim_cleanup_once` の cleanup 予算 `min(90, deadline_at − now)` (3916–3921) を覆う。**deadline_at ちょうどで overall-timeout が立つと cleanup 予算は 0 → `_fresh_qstat_gated_qdel` は
  `cleanup-budget-exhausted` で qdel せず (3103)、`job_may_remain=True` → orphan hold latch。** queue 待ちの締切 `queue_wait_timeout_s` (4215) は kwarg で、超過時は
  `queue-wait-timeout` → cleanup 予算 min(90, deadline_at − now) の qdel (QUE なら 0.3 秒で閉じる、T-2484 §3.1)。
- 先例: 受入 shard は `tools/run_tests.py:79` `_ACCEPTANCE_SHARD_DEADLINE_S = 5100` を `deadline_at` として渡す (外側 = 区間和 + 余裕)。変異 harness は
  `_effective_timeout` = max(spec, P180 + Q + W + G + A60 + C90) (T-2484、外側が内側へ追随)。

### (e) 前段 (checker 起動 → qsub) の所要
T-2484 §2 の receipt 3,849 件で前段 max 15.9 秒 (`_effective_timeout` の P=180 はその 10 倍余裕)。本 wave の (a) では qsub 後しか見えない。

## scope (本題だけ)

**契約 (親の provisional、段 3 の攻撃対象):**
- (P1) **外側 (land の 480 秒) を固定し、内側 (dispatcher の締切) を外側から導く。** 逆方向 (外側を区間和へ延ばす = T-2484 型・受入 shard 型) は「timeout の延長」であり
  裁定なしに行わない → 段 7 の裁定パッケージ項目とし、本 wave は実装しない。D2148 項 8 の「外側が前段・queue 待ち・walltime・grace・回収・cleanup を覆う」は
  「内側の全締切 ≤ 外側 − 終了余裕」として保つ。dispatcher の既定値・回収規則は 1 bit も変えない (項 8 の「内側 dispatcher の期限と回収規則は維持」)。
- (P2) **伝播手段は env 1 本** (案: `IZANAGI_PROVENANCE_OUTER_BUDGET_S`、land が `480` を秒で置く)。未設定なら checker は現行どおり (既定 900/3600/300) — 直叩き・他の呼び手の挙動不変。
  land の `timeout=480` は名前付き定数 (例 `_PROVENANCE_AUDIT_TIMEOUT_S`) にして env と同じ値を 1 源から出す (AST pin テストは定数参照でも `ast.Constant` を要求するので改訂が要る)。
- (P3) **導出:** checker は起動時刻 (`time.monotonic()`) を取り、dispatch 直前に `remaining = budget − elapsed` を計算。`deadline_at = now + remaining − R_post`、
  `queue_wait_timeout_s = min(900, remaining − R_post − C90 − M_pre)` を dispatcher に渡す。R_post (deadline 後の receipt 保存・checker return・land 側の読み) と M_pre
  (qsub までの前段、実測 max 15.9 秒) は実測 max への倍率で決める (DW-O13)。`queue_wait_timeout_s` が最小所要 (a) の合計 min 16.6 秒未満なら **qsub せず** rc=16 と理由行
  (`残余予算 X 秒 < 最小所要`) で返す — 投入しても外側に殺される job を作らない。既存の D612 override が明示されていれば、その値と導出値の **小さい方** を使う (明示上書きを緩めない)。
- (P4) **区間の計測:** 権威は dispatcher の receipt (`queue_wait_s`、`state_history`、`terminal_reason`)。checker は dispatch 経路の終端で 1 行 (`budget / queue_wait_s / RUN 区間 / 残余`) を
  stderr に出す。land の reject reason 文面・`_Reject` の分類・stderr の扱いは変えない (rc=16 → `did not complete authoritatively (rc=16)` retryable のまま)。
- (P5) **login 経路 (bounded scope 子) は変えない。** 480 秒超の login 監査 (F975、旧 checker、load 70 超) は T-2805 (混雑時観測) と延長裁定の材料であり本 wave の対象外。
- (P6) **変異 (正例・負例):** テスト変異 matrix (導出式・閾値・env 不在時の恒等・上書きの min) + Pegasus 実走 2 本 (正例: 通常 queue で budget 480 の `--force-dispatch` が完走し
  receipt に区間が残る / 負例: 小さい budget で qsub 前拒否 rc=16、または短い queue 締切で `queue-wait-timeout` → qdel → hold 無し・rc=16)。実走は子の編集完了後、wave 木から。

**scope 外 (起票・記録のみ):** 480 秒の延長 (裁定パッケージ、材料 = (a) の分布・F975 の login 6 点・`test_cumulative_wait_budget_arithmetic` の 1280 秒 watchdog 算術)、
D2170 の CPU 判定、T-2803 (受領証 fingerprint)、T-2805 (混雑時観測)、login 経路の scope 子の orphan、dispatcher の cleanup 予算の意味論変更、land の理由文面の拡張。
仮想リスク向けの gate・検査・台帳・一般化は足さない (DW-G05)。

## 不変条件
- 規律 2/3: provenance 監査の判定 (rc=1 = 違反、release_safe) と land の関門 (DW-O25) は不変。infra 失敗 (rc=16) は今までどおり retryable、成功に読み替えない。
- dispatcher (`tools/pegasus/dispatch_compute.py`) は変更しない。`_dispatch_timeout_overrides` の bytes 同値 (t2337 meta-test) を壊さない。
- env 未設定時の checker の挙動 (dispatch kwargs) は現行と同一 (恒等の正例をテストで固定)。
- land の外側 480 秒は変えない。`test_cumulative_wait_budget_arithmetic_uses_production_timeouts` の算術が通る。
- DW-O09: 変更 file を pin する台帳は無し (git grep: check_docs は land を「唯一の land 経路」文言で参照するだけ、freeze manifest 非該当)。D2045 受領証は checker sha を環境 digest に含むため改版で cold 化 (既知、T-2609 §限界)。

## 成果物
- 実装: `tools/check_ai_provenance.py` (env 読み取り・導出・qsub 前拒否・終端 1 行)、`tools/dev_wave_land.py` (定数化 + env 1 key)、テスト (`orchestrator/tests/test_check_ai_provenance.py`、`test_dev_wave_land.py`)。Codex author 1 本。
- 変異 matrix + Pegasus 実走 2 本の receipt。
- insight `output/insights/2026-09-20/t2804-provenance-timeout-contract/README.md` (実測表、契約、逐語、裁定パッケージ = 延長の要否)。decisions fragment (契約)、worklog fragment。

## 分割方針
段 2 plan 1 本 (read-only)、段 3 consult 2 本 (レンズ A: 契約の穴 = 締切の算術・SIGKILL 窓・hold の残り方・D612/D2148 項 8 との整合、レンズ B: 受理集合・fail-closed・
scope 膨張・テスト pin と meta-test)、段 5 author 1 本 (所有: 上記 4 file)、段 6 review 2 本 + fix。設計択一が割れる (P1/P3) ので軽量版にしない。
