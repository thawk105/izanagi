# [T-2804] land の provenance 監査 timeout (480 秒) と dispatcher の queue 待ち上限 (900 秒) の両立契約 — 外側を固定し内側の締切を絶対 monotonic 期限から導く (契約 C-2804)

作成 2026-09-20。wave branch `worktree-dev-wave-t2804-provenance-timeout-contract`、起点 local main `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad`。
実装 commit `aa81e3c64445055dbf8088b47c47f22b39a63571` (Codex author)、fix1 commit `62ed683aba12dd98e17f040d701fe5390cbab4cc` (Codex author)。
job dir (repo 外、生ログ・script・独立 clone): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2804-provenance-timeout-contract/`。

## 1. 何をしたか (要約)

- land (`tools/dev_wave_land.py`) は取り込み前に checker (`tools/check_ai_provenance.py`) を `subprocess.run(timeout=480)` で走らせる。checker が計算ノードへ
  dispatch すると、dispatcher の queue 待ち既定 900 秒だけで外側 480 秒を超えうる。480 秒で親が SIGKILL すると dispatcher の回収 (qdel・orphan hold の昇格・
  receipt 保存) が走らず、投入後・pending 解除前なら job と pending hold が残る。
- 契約 C-2804 を決めて実装した: **外側 480 秒は不変 (延長は裁定なしに行わない)。land は spawn 直前に絶対 monotonic 期限
  (`IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC = time.monotonic() + 480`) を env で渡し、checker は dispatch 直前にそこから dispatcher の `deadline_at` と
  `queue_wait_timeout_s` を導く。導出 queue 予算が 16 秒未満なら qsub せずに rc=16 で返す。** env 未設定時の挙動 (直叩き・他の呼び手) は不変。
- これは **D2148 項 8 (外側 timeout が全区間を覆う = 外側が内側へ追随する) の実装ではなく、land 固有の限定契約**である (段 3 相談 A5 / B2)。項 8 型
  (外側を区間和 5,130 秒等へ延ばす) は §7 の裁定パッケージへ返す。
- 検証: 焦点走 2 回 (計算ノード、対象 2 file + consumer 13 file) 3,893 passed / 7 skipped / 0 failed。commit 後の全史監査 2 回 (12,061 / 12,062 件、新規違反なし)。
  Pegasus 実走 3 本 (§5)。変異 matrix は §6。

## 2. 起点と scope

起点は worklog entry 1722 の次の一手 [T-2804] (逐語 `verbatim/T-2804-origin.md`) と D2170 の「却下した選択肢」(land の 480 秒延長は scope 外)。
既裁定の逐語は `verbatim/` (D2148 項 8、D2170、D612、F975 抜粋、entry 1685 = T-2484 の実装、T-2484 の裁定パッケージ)。
scope 外 (記録のみ): 480 秒の延長 (§7)、D2170 の CPU 判定、T-2803 (受領証 fingerprint)、T-2805 (混雑時観測)、login 経路 (bounded scope 子) の orphan、
dispatcher の cleanup 予算の意味論、land の理由文面の拡張。

## 3. 段 1 の実測 (改善前)

### 3.1 provenance task の dispatch 受領証 85 件 (`measurements/dispatch-stats-1.txt`、T-2609 の probe を read-only で再走)

母集団: 残存する worktree / job dir の `output/pegasus-dispatch` にある provenance task の受領証。撤去済み wave の記録を含まない。全史 (`args=[]`、68 件) と
`--range` (17 件)、旧 checker と新 checker、child rc 0/1/2 と infra rc=16 が混在する。**land 呼出しの無作為標本ではない** (相談 A7 / B1)。

| 区間 | n | 中央値 | p90 | 最大 |
|---|---:|---:|---:|---:|
| queue 待ち `queue_wait_s` | 85 | 5.2 秒 | 7.3 秒 | 716.5 秒 (2026-09-20 20:09、gen_S QUE 47 / HLD 104 / RUN 46 の混雑時) |
| 監査本体 (RUN 初観測 → 最終観測) | 85 | 30.7 秒 | — | 475.9 秒 (09-08 14:53、旧 checker) |
| 合計 (qsub → 最終観測) | 85 | 37.1 秒 | — | 758.6 秒 |

合計の閾値別件数 (親が受領証の `state_history` 末尾から集計): > 300 秒 = 5、> 375 秒 = 2、> 480 秒 = 2 (482.3 秒 = 旧 checker の RUN 476 秒、758.6 秒 = 本日の
queue 716 秒)。375〜480 秒の帯は 0 件。本日の 716 秒の件は child rc=2 (`HEAD が監査中に変化した`) で land からの呼出しではない。
相談 A7 の指摘どおり、probe の出力だけでは全件の合計を再計算できないので、上の閾値別件数は親の集計 (job dir に残さず、`dispatch-stats-1.txt` の
非 child-0 明細と直近 15 件から下限だけ検算できる: 5.2 + 475.9 = 481.1 秒、716.5 + 41.0 = 757.5 秒)。

### 3.2 構造 (実装前のコード)

- land: `_run_provenance_checker` は `subprocess.run(..., timeout=480)`。timeout は SIGKILL (grace 無し)。checker は in-process で dispatcher を呼ぶので、
  `DispatchError` 経路 (qdel、orphan hold の昇格、receipt 保存、`_return_infra`) が一切走らない。**投入後・pending hold 解除前の kill** では pending hold と
  PBS job が残る (qsub 前・終端後の kill では残らない — 相談 A7 の限定)。stderr は捨てる。
- checker: dispatch 入口は 3 箇所 (`--force-dispatch`、headroom 不足 ∧ queue 可、bounded local の cap_oom 後)。いずれも `_default_dispatch` →
  `dispatch_compute.dispatch(argv, task="provenance", repo_root=REPO, **D612 上書き)`。外側予算を受け取る入力は無く `deadline_at` も渡していない。
- dispatcher (不変): queue 待ち 900 / walltime 3,600 / grace 300 / accounting 60 / cleanup 90 秒。既存 kwarg `deadline_at` は `total_deadline`・RUN 再基準・
  collection 締切・`claim_cleanup_once` の cleanup 予算 (`min(90, deadline_at − now)`)・scheduler command の timeout を覆う。**`deadline_at` ちょうどで
  overall-timeout が立つと cleanup 予算は 0 になり、qdel は `cleanup-budget-exhausted` で走らず `job_may_remain` → orphan hold latch** になる。
  queue 待ちの締切 `queue_wait_timeout_s` の超過は `queue-wait-timeout` で、cleanup 予算が残っていれば QUE の job を qdel できる (T-2484 §3.1: 0.3 秒)。
- 先例: 受入 shard は `_ACCEPTANCE_SHARD_DEADLINE_S = 5100` を `deadline_at` に渡す (外側 = 区間和 + 余裕)。変異 harness の `_effective_timeout` は
  max(spec, P180 + Q + W + G + A60 + C90) (T-2484 = D2148 項 8 の実装、外側が内側へ追随)。
- 既存テストの pin: land の `timeout` 実引数を AST で literal 定数と要求、subprocess.run の kwargs と env を exact 一致、`TimeoutExpired(…, 480)` の写像。

### 3.3 F975 (2026-09-14) の記録

land 40 回のうち rc=29 が 8 回、内訳は rc=16 × 5・`TimeoutExpired after 480 seconds` × 2 (load 75)・head 移動 × 1。login 経路の全史監査は load と強く相関し
(load 36 → 269 秒、70 → 419 秒、127 → 574 秒、旧 checker)、480 秒超は login 経路でも起きている。本 wave は dispatch 経路の契約だけを扱う。

## 4. 段 2〜4 (plan・相談・裁定)

- 段 2 plan (`reviews/s2-plan.md`): 外側 480 固定、env で予算を渡し `deadline_at = now + remaining − R_post(32)`、`Q = min(Q_existing, remaining − 32 − 90 − M_pre(180))`、
  `Q < Q_min(16.6)` なら qsub 前拒否、不正 env は rc=16、注入 seam を `**kwargs` 受けへ改訂。
- 段 3 相談 2 本 (`reviews/s3-consult-A.md` = 契約の穴、`reviews/s3-consult-B.md` = 受理集合・fail-closed・過剰)。両者が一致した must-fix:
  (1) (P1)「外側固定・内側導出」は D2148 項 8 の実装ではなく land 固有の限定契約で、成功集合が (導出 queue 締切, 480] の帯で縮む → 明示して記録する、
  (2) land と checker の時計の起点差 s が式に無い (`s + h < R_post` が要る) → 絶対 monotonic 期限を渡す、(3) M_pre=180 (harness の値の写し) は過大で
  queue 278.7 秒の既知成功例を落とす → 60 秒、(4) Q_min=16.6 (qsub 後合計の最小値) を queue 締切の下限に流用するのは区間違い → queue 待ちの観測 min 5.1 秒 × 3 ≈ 16 秒、
  (5) 注入 seam の全面変更は不要 (既存 fake は argv だけ、新規テストは末端 `dispatch_compute.dispatch` を monkeypatch)。refuted: 不正 env を無視して 900 へ戻す懸念、
  D612 の自動選択との同型 (呼び手が本 invocation の外側期限を明示する契約であり、argv の形から推測しない)、pin 改訂の弱体化、rc=1 の分類変更。
- 段 4 裁定 (`s4-ruling.md`): 契約 C-2804 (§1)、plan v2 (file:line)、変異 13 件 (M1〜M12 + 等価 E0) と実走 L1〜L3 の事前登録、延長の裁定パッケージ (§7)、brief の訂正
  (§8)。

## 5. 実装と検証

### 5.1 実装 (`aa81e3c64`、Codex author、+299/−9、4 file)

- `tools/dev_wave_land.py`: `_PROVENANCE_AUDIT_TIMEOUT_S = 480`、`_PROVENANCE_OUTER_DEADLINE_ENV`。`_run_provenance_checker` で `env[...] = repr(time.monotonic() + 480)`
  (継承値は上書き)、`timeout=` と `TimeoutExpired` の文面を定数から。reject reason・`_Reject` 分類・stderr の扱いは不変。
- `tools/check_ai_provenance.py`: 定数 (`_PROVENANCE_DEADLINE_POST_RESERVE_S = 32.0`、`_PROVENANCE_DISPATCH_PRE_RESERVE_S = 60.0`、`_PROVENANCE_MIN_QUEUE_BUDGET_S = 16.0`、
  各 1 行の根拠コメント)、`_outer_deadline_monotonic` (未設定 → None、有限数以外 → ValueError)、`_default_dispatch` (signature 不変、env 未設定なら現行と同一の kwargs、
  設定時は `deadline_at = K − 32`、`queue_wait_timeout_s = min(D612 明示値または既定 900, remaining − 32 − cleanup 90 − 60)`、`< 16.0` なら qsub せず理由行 1 本 + rc=16、
  dispatcher を呼んだ経路の終端で観測可能値 (`remaining_at_dispatch_s` / `queue_wait_timeout_s` / `deadline_margin_s` / `remaining_at_return_s` / rc) を stderr に 1 行)。
  `_dispatch_timeout_overrides`・`_invoke_dispatch`・3 箇所の呼出し・login bounded scope 経路・dispatcher は不変。
- テスト: checker 側 10 種 31 case (`test_outer_deadline_*`: 恒等 / 導出 / 3 経路 / 投入前拒否 / D612 との min / 不正値 / 予約区間の算術 / dispatcher 定数追随 /
  終端行と main の返却 rc / login 経路不変)。land 側: AST pin を `ast.Name` + `id` + `== 480` へ、env exact 一致に 1 key (値は monotonic の範囲検査)、`TimeoutExpired` の
  写像を定数参照、`_assert_non_authoritative_provenance_rc_retains` の fake stderr に予算行を入れて reason exact 一致と stderr 非転送、継承値上書きの新規テスト。
- 定数の根拠と母集団 (DW-O13): 60 秒 = 2.87 × (前段 max 15.9 秒 + poll 5.0 秒)、母集団は T-2484 の receipt 3,849 件 (主に tests task の harness regime)、poll 5 秒は既定間隔で
  qstat 遅延の上限証明ではない。16 秒 = 3 × queue 待ち観測 min 5.1 秒 (n=85、運用閾値であって必要時間の証明ではない)。32 秒 = 後段 (dispatcher return → checker 終了) の
  代理値 (実測なし、前段 max の 2 倍)。L1 で後段 h ≈ 0.03 秒を実測 (§5.4)。

### 5.2 焦点走 (計算ノード dispatch、`measurements/focus-runs.txt`)

対象 2 file + consumer 13 file (`test_t2337_dispatch_timeout_overrides`、`test_dev_wave_wait`、`test_pegasus_dispatch_compute`、`test_hooks`、`test_check_docs`、
`test_codex_reasoning_ab`、`test_dev_waves_git_state`、`test_resume_gate_acceptance_boundary`、`test_run_tests_shards`、`test_s8b_ratified_freeze`、
`test_t139_approval_payload`、`test_t793_approval_d291`、`test_flaky_test_holds_contract`)。実装後 3,893 passed / 7 skipped / 0 failed (85.5 秒、request 13607)、
fix1 後 3,893 passed / 7 skipped / 0 failed (85.9 秒、request 13640)。

### 5.3 段 6 レビューと fix1 (`reviews/s6-review-{A,B}.md`、`reviews/s6-fix1.md`)

- レビュー A (契約の穴・算術・dispatcher との噛み合わせ): GO。所見 1 (should): 終端行の field 名が裁定 §2 項 5 (`deadline_margin_s`) と違う (`deadline_at_margin_s`)。
  refuted: 締切算術・投入前拒否・恒等の穴、時計の起点差 (絶対期限で自動控除、`repr(float)`→`float` は無損失)、dispatcher との接続 (queue 超過検出時の残余
  `≥ C + 60 − p − δ`、`p + δ ≤ 60` なら cleanup 90 秒を確保)、land の pin と分類、終端行 (例外時も 1 本、rc=16)。判定不能: 後段 h < 32 の実測 (→ §5.4)。
- レビュー B (過剰・削除・受理集合・テスト帰属): NO-GO。must-fix 1: 同じ field 名の不一致 (段 5 の prompt を親が裁定と食い違う名前で書いたのが原因)。
  should: (2) DW-O13 の「内側予算の和 + 終了余裕 < 外側」は C-2804 の予約算術 (`D + 32 = K`、`Q + 90 + 60 + 32 ≤ remaining`) の検査であって後段 h の実時間保証ではない
  (→ §5.4 で h を実測)、(3) `test_t2337_*` の provenance 2 本が新 env を消していない、(7) M12 の単一理由は `==480` の assert を代表証拠にし他の赤は別分類、
  (8) 延長案 (b) の 5,130 秒は provenance 予算であって land 全体の最長時間ではない (§7 に反映)。refuted: 裁定外の gate・一般化・互換層、fail-closed の向き、テスト帰属、
  受理集合の表 (§5.5)。
- fix1 (`62ed683ab`、Codex author、+5/−3、4 file): 終端行を `deadline_margin_s=` へ改名 (値・順序・他 field は不変)、テスト期待行と land テストの fake stderr も同名へ、
  `test_t2337_dispatch_timeout_overrides.py` の provenance 2 本の先頭に `monkeypatch.delenv(新 env)` (期待値は不変)。所見対応: B must-fix 1 closed、B should 3 closed、
  A should 1 closed。fix1 は field 名の改名と env 隔離だけで実装不変のため焦点再レビューは省略した (DW-O16 の対応表は fix1 報告に含む)。

### 5.4 Pegasus 実走 (unit worktree `t2804-unit-impl` = fix1 と同内容、`measurements/live-*`)

期限 = 実行直前の `time.monotonic()` + offset。checker を `--force-dispatch` で走らせ、D612 上書きは解除。受入の wave 木から hold を隔離するため unit 木で行った。

| 走 | offset | 結果 | 区間 (receipt) | checker 終端行 |
|---|---:|---|---|---|
| L1 正例 | 480 | rc=0、`12062 件、新規違反なし`、checker 全体 52.6 秒 (22:10:18〜22:11:11 JST)、request 13650 | queue 待ち 5.17 秒、RUN 初観測 6.33 秒 → 終端 47.31 秒、Elapse 36 秒、qdel 無し、hold 無し | `remaining_at_dispatch_s=479.82 queue_wait_timeout_s=297.82 deadline_margin_s=32.0 remaining_at_return_s=427.37 rc=0` |
| L2 負例 (投入前拒否) | 30 | rc=16、0.14 秒、新規 submission dir 無し、hold 無し | (投入なし) | `provenance dispatch budget insufficient: remaining_s=29.86 queue_budget_s=-152.14 min_queue_s=16.0 rc=16` |
| L3 負例 (queue 取消) | 199 | **発火せず = 負例未観測。** queue が空いていて 5.23 秒で RUN へ入り、rc=0 で完走 (37.2 秒、request 13654) | queue 待ち 5.23 秒、RUN 6.39 → 31.99 秒 | `remaining_at_dispatch_s=198.88 queue_wait_timeout_s=16.88 deadline_margin_s=32.0 remaining_at_return_s=161.80 rc=0` |

- L1 から: 前段 (checker 起動 → dispatch 直前) 0.18 秒、dispatcher 区間 52.45 秒、**後段 h (dispatcher return → checker 終了) = 427.374 − (K − monotonic_at_exit) = 0.03 秒**
  (代理値 32 秒に対し 3 桁小さい。1 走の値であり上限ではない)。
- L3 は queue 締切 16.88 秒を渡したが混雑していないため queue-wait-timeout 経路は実走で観測できていない。この経路の発火・qdel・hold 無しは dispatcher の既存テストと
  T-2484 の実測 (hang_timeout 4 秒の派生 spec) に依る。**本 wave では「queue 超過時に cleanup 余裕付きで取消される」を実走で示していない。**

### 5.5 受理集合の変化 (段 4 §2 とレビュー B の表)

| 条件 | 現行 (480 秒 SIGKILL) | C-2804 後 |
|---|---|---|
| env 未設定 / login bounded scope | 不変 | 不変 |
| dispatch で queue ≤ Q、監査・回収が deadline_at 前に完了 | 成功 | 成功 (通常終端、残留なし) |
| queue > Q だが全体は 480 秒以内で完了しえた | 成功 | queue-wait-timeout → rc=16 → land rc=29 retryable (取消成功なら残留なし) |
| queue ≤ Q だが完了が (deadline_at, K] = 最後の 32 秒 | 成功 | 内側期限で rc=16 → rc=29 retryable、cleanup 予算 0 の hold latch が生じうる |
| queue 待ちだけで 480 秒超 | TimeoutExpired → rc=29 retryable、投入後なら job と pending hold が残る | Q で取消 → rc=16 → rc=29 retryable、取消成功なら残留なし |
| RUN / collection 中に deadline_at へ到達 | 480 秒まで待つ | 先に rc=16 側へ終端、hold latch は残る (dispatcher 不変の限界) |
| 不正 env・残余不足・D612 の Q=0 明示 + 新 env | (新 env は無視) | 投入前 rc=16、新規 job / hold を作らない |
| 返却 rc=1 (違反) | rc=29、release_safe、lease 解放 | 同じ (同じ返却 rc に対する land の写像は不変) |

段 1 の 85 件では、成功集合の 2 帯 (queue 待ちが (Q, 480 − RUN − 回収) / 完了が (K − 32, K]) に当たる既知成功例は 0 件 (queue 278.7 秒の例は前段 e ≤ 19.3 秒なら通る)。
母集団の限界 (§3.1) から「縮小ゼロ」の証明にはならない。

## 6. 変異 matrix (独立 clone `mutation-source` = fix1 commit `62ed683ab`、計算ノード dispatch、runner = `tools/run_tests.py --force-dispatch test_check_ai_provenance.py test_dev_wave_land.py -k "outer_deadline or provenance or cumulative_wait_budget or default_dispatch" -q -rf`)

事前登録 (段 4 §4): M1 R_post 欠落 / M2 C 欠落 / M3 M_pre 欠落 / M4 min→max / M5 拒否条件 `<`→`>=` / M6 `<`→`<=` / M7 env 未設定でも導出 / M8 `deadline_at` を渡さない /
M9 不正値を未設定扱い / M10 land の env 設定削除 / M11 land の `setdefault` / M12 land の 480→481 / E0 min の引数交換 (等価、SURVIVED 期待)。

結果 (`mutation/results-{probe,final}.summary.json`、原本 JSON は job dir に sha256 束縛):

| 走 | baseline | 結果 | 備考 |
|---|---|---|---|
| probe (`spec-probe.json`、全件 SURVIVED 期待で観測 node を集める) | PASSED (44.0 秒) | 12 件が MISMATCH (= 赤 node を観測)、E0 は SURVIVED | 観測 node 数: M1 13 / M2 17 / M3 17 / M4 20 / M5 21 / M6 1 / M7 2 / M8 8 / M9 3 / M10 2 / M11 1 / M12 4 |
| final (`spec-final.json`、観測 node を完全集合として KILLED 期待、E0 は SURVIVED 期待) | PASSED (47.7 秒) | **M1〜M12 = 12/12 KILLED (期待 node 完全一致、matching 13/13)、E0 = SURVIVED、MISMATCH 0、PARSE_ERROR 0、TIMEOUT 0、rc=0** | 1 run 42.7〜57.8 秒、M12 だけ queue 待ちで 713.6 秒。probe の M2 も 376.0 秒 (queue 待ち) |

単一理由性 (レビュー A / B の静的判定と一致): M1〜M5・M8 は導出値の exact 比較 (`derives` / `all_entries` / `composes_d612` / `reserved_intervals` / `terminal_line`) で
赤、M6 は境界 16.0 の正例 1 node だけ、M7 は env 未設定の恒等 2 node だけ、M9 は不正値の rc=16・未呼出し 3 node だけ、M10 / M11 は land の env 伝播・継承値上書き、
M12 は `test_cumulative_wait_budget_arithmetic_uses_production_timeouts` の `== 480` を代表証拠とし、残る 3 node (env の期限範囲・timeout の実引数・
`after 480 seconds`) は同じ値の pin であって別理由ではない (レビュー B 所見 7 のとおり診断だけの赤は kill に数えない)。M7 と M12 は既存テスト
(`test_provenance_dispatch_omits_both_overrides_when_unset`、実 timeout==480 の pin) でも落ちるので新規検出力ではない (レビュー B)。
E0 は `min` の引数順の交換 (両引数は有限) で等価変異の正例として SURVIVED。

## 7. 裁定パッケージ — land の provenance 監査の外側予算を D2148 項 8 型へ延ばすか (本 wave は実装しない)

| 択 | 契約 | 帰結 |
|---|---|---|
| (a) 480 維持 + 内側導出 (本 wave の C-2804) | 内側の締切を外側から導く land 固有の限定契約 | 成功集合は §5.5 の 2 帯で縮む、RUN / collection の hold latch は残る、land の累積 lock 待機 180 秒 (D1996) と検査 harness の 1,280 秒算術は不変 |
| (b) 区間和 P180 + Q900 + W3,600 + G300 + A60 + C90 = 5,130 秒へ延長 | 項 8 の形 (内側維持、外側が追随) | provenance 監査 1 回の予算が 85 分 30 秒 (lock 待ち・他検査を含む land 全体の最長時間ではない)。厳密な終了余裕は別途要る。`test_cumulative_wait_budget_arithmetic` の 1,280 秒算術を再設計。lock 外なので lock 保持は延びない |
| (c) 中間値 (例 480 + 900 = 1,380 秒) | 480 秒超の一部を救う | 全区間は覆えず内側短縮か残留が残る。1,280 秒算術の改訂が要る |
| (d) dispatch 時だけ延長 | login の成功集合を保ち dispatch 側だけ拡大 | checker から経路通知が要り、`subprocess.run(timeout=固定)` の構造変更 (段階 timeout) が要る |

親の推奨: (a) を今 land し、(b)〜(d) は改善後 checker の混雑時観測 (T-2805、D2170 の再訪条件) と本 wave の実走 (h ≈ 0.03 秒、L3 未観測) が揃ってから決める。
材料: §3.1 (母集団限定)、§3.3 (旧 checker の login 6 点)、§5.4。起点 task の「timeout の延長は裁定なしに行わない」が延長を裁定へ返す直接の根拠であり、1,280 秒の算術は
変更時の検査制約、F975 の 6 点は旧 regime の参考材料である (レビュー B)。

## 8. brief の訂正 (段 3 相談で判明、`s1-brief.md` は原文のまま残す)

- (P1)「内側の全締切 ≤ 外側 − 終了余裕なら項 8 を保つ」→ 撤回。C-2804 は項 8 の実装ではない (§1)。
- §(c)「`_dispatch_timeout_overrides` の bytes 同値を meta-test で pin」→ 実体は列挙入力に対する受理・拒否結果と値の比較 (bytes 比較ではない)。
- §(b)「SIGKILL で pending hold と job が残る」→ 投入後・pending 解除前の kill に限る。
- §(b) の 1,280 秒は検査 harness の watchdog であり production の watchdog ではない。
- (P4) checker が出せるのは予算・経過・rc まで。queue 待ち・RUN 区間の権威は dispatcher の receipt (checker は receipt を読み戻さない)。
- §(a) の閾値別件数は probe 出力だけでは検算できず、母集団は残存受領証 85 件に限る (§3.1)。

## 9. 限界と次の一手

### 限界
- queue-wait-timeout 経路 (queue 超過 → cleanup 余裕付き qdel → hold 無し) は実走で観測できていない (L3 は混雑無しで完走)。
- RUN / collection 中に `deadline_at` へ達すると cleanup 予算 0 で hold latch になる。dispatcher を変えずに防ぐ策は無い (相談 A2、レビュー A4)。
- receipt の永続化・checker の return が期限内に完了することは保証しない。後段 h は 1 走 (0.03 秒) の実測。
- 32 / 60 / 16 秒の根拠の母集団は harness regime (T-2484) と残存受領証 85 件で、provenance の land 呼出しと同一 regime とは証明していない。
- 成功集合は 2 帯で縮む (§5.5)。85 件では該当 0 件だが、母集団の限界から「縮小ゼロ」とは言えない。
- login 経路 (bounded scope 子) は変えていない。480 秒超の login 監査 (F975) は T-2805 と §7 の材料。

### 次の一手 (起票候補、本 wave では実装しない)
- 改善後 checker の混雑時 (load 100 超・queue 混雑) の観測を集め、queue-wait-timeout 経路の実走証拠 (qdel・hold 無し) と login 全史の 480 秒超の有無を記録する (T-2805 と同じ活動)。
- §7 の延長の裁定。

## 10. 再現資料 (job dir)

| 用途 | file |
|---|---|
| 段 1 の受領証集計 | `probe/dispatch-stats-1.txt` (T-2609 の `probe/provenance_dispatch_stats.py` を再走) |
| codex 子の prompt / 出力 | `codex/prompt-*.md`、`codex/s2-plan.md`、`codex/s3-consult-{A,B}.md`、`codex/s5-author.md` (+ `.patch`)、`codex/s6-review-{A,B}.md`、`codex/s6-fix1.md` (+ `.patch`) |
| 焦点走 | `run-focus.sh`、`focus-{1,2}.log` |
| commit 後の全史監査 | `run-full-audit.sh`、`audit-{impl,fix1}.log` |
| Pegasus 実走 | `run-live.sh`、`live/L{1,2,3}.*` (meta / stdout / stderr / receipt / dirs / holds) |
| 変異 | `make-mutation-source.sh`、`init-mutation-source-submodules.sh`、`advance-mutation-source.sh`、`run-mutation.sh`、`mutation-spec-*.json`、`mutation-*-results.json` |

本 insight dir 内の写し: `reviews/` (codex 出力 7 本、`s6-review-A.md` は行末空白を可逆正規化 — 原本 sha256 / bytes は `verbatim-normalization.json`)、
`measurements/` (受領証集計、焦点走・全史監査の抜粋、実走 L1〜L3 の meta / stderr / receipt。stderr 2 本は同じ正規化)、`verbatim/` (起点・既裁定の逐語)、
`s1-brief.md`、`s4-ruling.md`。probe / launcher の `.py` / `.sh` と author の `.patch` は実装面なので repo へ写さず job dir を指す。
