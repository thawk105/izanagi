# [T-2804] 段 4 裁定 — 所見の real/refuted、plan v2、変異と実走の事前登録

作成: 2026-09-20 (時刻は handoff の mtime)。入力: `s1-brief.md`、`codex/s2-plan.md`、`codex/s3-consult-A.md` (sol)、`codex/s3-consult-B.md` (luna)。
裁定 inbox の再走査: `docs/handoff/` は README + 08-28 の 1 file (無関係) のまま、peer 通知は t2766 の land 1 件 (対象 file 非接触)。

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| A1 | 全経路で「480 秒より前に receipt 保存・return」は保証されない (RUN/collection で deadline 到達時は cleanup 予算 0 → hold latch、receipt 永続化は予算外) | real / must-fix (記述) | 採用: 契約の保証範囲を 3 つに分けて書く — (i) queue 区間は cleanup 余裕付きで取消、(ii) RUN/collection の期限到達は hold latch (dispatcher 不変の限界)、(iii) receipt 永続化は非保証。「構造を閉じる」は「queue 待ちだけで SIGKILL される構造を閉じる」に限定 |
| A2 | RUN hold を dispatcher 不変で必ず防ぐ追加策は無い | refuted (plan の限定は正しい) | 限界として記録。確率は数値化しない |
| A3 | land と checker の時計の起点差 s が式に無い (`s + h < R_post` が必要) | real / must-fix | 採用: land は **絶対 monotonic 期限** `time.monotonic() + 480` を spawn 直前に env へ置き、checker は起点を持たず env の期限から残余を計算する (同一 host の CLOCK_MONOTONIC は process 間で共通)。s は自動的に吸収され、残るのは h (dispatcher return → checker exit) だけ。h は段 6 の実走で測る |
| A4 | D612 の自動選択 (2) とは別物、明示上書きは緩まない | refuted | 境界文を D fragment に書く: 「呼び手が本 invocation の外側期限を明示する契約であり、argv の形から既定値を推測しない。未設定時は既定不変」 |
| A5 / B2 | (P1) を D2148 項 8 の実装と呼ぶのは不整合 (項 8 = 外側 ≥ P+Q+W+G+A+C、内側維持。plan は内側短縮) | real / must-fix | 採用: 本 wave の契約は **項 8 の実装ではなく land 固有の限定契約** と明記。項 8 型 (外側追随 = 延長) は task 文「延長は裁定なし不可」により本 wave で実装せず、裁定パッケージ (§6) へ |
| A6 | helper 旧呼出し互換 (`_default_dispatch(argv)`、`_invoke_dispatch(None, argv)`) | real / should | 採用: 新引数を足さない設計 (env を `_default_dispatch` 内で読む) にすれば互換問題自体が消える |
| A7 | brief §(a) の閾値別件数は probe 出力だけでは検算不能、母集団の限界未記載、SIGKILL 残留の成立条件、meta-test は bytes 比較でない | real / should (brief 訂正) | 採用: 全 85 件の合計表を job dir へ出す (段 7、`probe/`)、母集団 (残存 worktree の受領証、撤去済み wave 非含、全史/range・旧新 checker 混在) を insight に明記、SIGKILL 残留は「投入後・pending 解除前の kill」に限定、meta-test は「列挙入力に対する受理・拒否結果の比較」に訂正 |
| A8 / B1 / B6 | M_pre=180 は過大で queue 278.7 秒の既知成功例を落とす。60 秒なら e ≤ 19.3 で通る。厳密な成功→失敗件数は判定不能 | real / must-fix | 採用: **M_pre = 60 秒** (= 2.87 × (前段 max 15.9 + poll 5.0)、母集団 T-2484 receipt 3,849 件 = 主に tests task の harness regime、poll は既定間隔で qstat 遅延の上限証明ではない)。成功集合の縮小 (queue 待ちが (Q, 480 − RUN) の帯、または完了が (D, K] の帯) は縮小として明記し、85 件では該当 0 (queue 278.7 秒は e ≤ 19.3 で通る) と限定付きで書く |
| A8 / B4 | Q_min=16.6 (qsub 後合計の観測最小値) を queue 締切の下限へ流用するのは区間違い | real / must-fix | 採用: 下限は **queue 待ちの観測 min 5.1 秒 (n=85) × 3 ≈ 16 秒** (`_PROVENANCE_MIN_QUEUE_BUDGET_S = 16.0`) とし、「この値未満の queue 予算では投入しない (運用閾値、必要時間の証明ではない)」と書く。D612 の Q=0 明示 + 新 env 併用時に投入前拒否へ変わることは受理集合の縮小として記録 |
| A9 / B9 | 注入 seam の全面変更は不要 | real / should | 採用: `dispatch_fn` 注入時は現行どおり argv だけ。導出は `_default_dispatch` 内。新規テストは `tools.pegasus.dispatch_compute.dispatch` を monkeypatch |
| B3 | 不正 env を無視して 900 へ戻す懸念 | refuted | 拒否 (rc=16) が fail-closed。維持 |
| B5 | DW-O13 の「内側予算の和 + 終了余裕 < 外側」の検査が別の算術になっている、後段 16 秒は代理値 | real / must-fix | 採用: 検査は `deadline_at + R_post ≤ outer_deadline` (等号は構成上) と `queue + C + M_pre ≤ deadline_at − now` と `R_post > 0`。R_post=32 は代理値 (後段 h の母集団なし) と明記し、段 6 実走で h を測って insight に書く。h > R_post なら値を裁定パッケージへ |
| B7 | AST/env/TimeoutExpired の pin 改訂が弱体化する懸念 | refuted | 定数名・値 480・実引数・env 一致・累積算術を維持 |
| B8 | rc=1 の分類は不変。ただし「現行では rc=1 到達、新期限では途中取消」は release_safe → retryable へ移る | refuted (緩和ではない) | 「同じ返却 rc に対する写像は不変」と限定して書く。checker テストは main の返却 rc 自体を assert |
| B10 | 負例の目的を分ける (投入前拒否 / queue 取消 / 特定時点まで進めて取消) | real / should | 採用: 実走 3 本 (§5) |
| B11 | scope 膨張 | refuted | env 名は `IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC` (既存の `IZANAGI_PROVENANCE_SCOPE_*`・`IZANAGI_DISPATCH_*` と非衝突、`git grep` で段 5 前に確認) |

## 2. 裁定 — 契約 (本 wave で実装する)

**契約 C-2804 (land 固有の限定契約、D2148 項 8 の実装ではない):**

1. land の `_run_provenance_checker` の外側 timeout は `_PROVENANCE_AUDIT_TIMEOUT_S = 480` (値不変)。spawn 直前に `env[IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC] = repr(time.monotonic() + 480)` を置く (継承値は上書き)。`TimeoutExpired` の文面は定数から生成 (`after 480 seconds` のまま)。reject reason・`_Reject` 分類・stderr の扱いは不変。
2. checker は dispatch 直前 (`_default_dispatch`) でだけ env を読む。未設定 → 現行と同一の kwargs (恒等)。設定済みで有限数でない (空・非数・NaN・±Inf) → `ValueError` → `_invoke_dispatch` の既存一義化で rc=16。
3. 導出 (env 設定時): `K = float(env)`、`now = time.monotonic()`、`remaining = K − now`、
   `deadline_at = K − R_post`、`queue_budget = remaining − R_post − C − M_pre`、
   `queue_wait_timeout_s = min(Q_existing, queue_budget)` (Q_existing = D612 明示値、無ければ `dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S`)。
   定数: `R_post = 32.0` (代理値、段 6 で h を実測)、`M_pre = 60.0`、`C = dispatch_compute.DEFAULT_CLEANUP_BUDGET_S` (数値を複製しない)、`Q_MIN = 16.0`。
4. `queue_wait_timeout_s < Q_MIN` なら dispatcher を呼ばず、stderr に 1 行 (`provenance dispatch budget insufficient: remaining_s=… queue_budget_s=… min_queue_s=… rc=16`) を出して `PEGASUS_DISPATCH_RC` を返す (qsub 無し、hold 無し)。
5. dispatcher を呼んだ経路の終端で stderr に 1 行 (`provenance dispatch budget: remaining_at_dispatch_s=… queue_wait_timeout_s=… deadline_margin_s=… remaining_at_return_s=… rc=…`) を出す。queue 待ち・RUN 区間の権威は dispatcher の receipt。
6. 保証範囲: (i) queue 待ち超過は `queue-wait-timeout` で dispatcher が cleanup 予算 (≤ 90 秒) を持って qdel へ進める (前段 + 観測遅延 ≤ M_pre の範囲)、(ii) RUN / collection 中に `deadline_at` へ達した場合は cleanup 予算 0 で hold latch (dispatcher 不変の限界、本 wave は解かない)、(iii) receipt 永続化・return の完了は予算内を保証しない (`h < R_post` は実測で示す)。
7. 変えないもの: dispatcher (`tools/pegasus/dispatch_compute.py`)、`_dispatch_timeout_overrides` (両実装)、login bounded scope 経路、land の 480 秒、D2170 の判定、受領証 (T-2803)。

**受理集合の変化 (明示):** 成功集合は (a) queue 待ちが `(queue_wait_timeout_s, 480 − 前段 − RUN − 回収)` の帯、(b) 完了が `(deadline_at, K]` の帯 (幅 R_post = 32 秒) で縮む。retryable (rc=29) 集合はその分増える。残留集合: queue 超過の pending hold + job 残留は減る (取消成功時)、RUN/collection 超過の hold latch は新たに生じうる (現行は SIGKILL で pending hold + job 残留)。段 1 の 85 件 (母集団の限界付き) では (a)(b) に該当する既知成功例は 0 件 (queue 278.7 秒は e ≤ 19.3 秒で通る)。

## 3. plan v2 (file:line、変更前の行番号)

`tools/dev_wave_land.py`
- 3555 直前: `_PROVENANCE_AUDIT_TIMEOUT_S = 480`、`_PROVENANCE_OUTER_DEADLINE_ENV = "IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC"`。
- 3560: `env.setdefault("PYTHONDONTWRITEBYTECODE", "1")` の後に `env[_PROVENANCE_OUTER_DEADLINE_ENV] = repr(time.monotonic() + _PROVENANCE_AUDIT_TIMEOUT_S)` (`setdefault` 不可)。`import time` の有無を確認。
- 3571: `timeout=_PROVENANCE_AUDIT_TIMEOUT_S`。3633: `detail = f" after {_PROVENANCE_AUDIT_TIMEOUT_S} seconds"`。

`tools/check_ai_provenance.py`
- 49〜56 付近: `_PROVENANCE_OUTER_DEADLINE_ENV`、`_PROVENANCE_DEADLINE_POST_RESERVE_S = 32.0`、`_PROVENANCE_DISPATCH_PRE_RESERVE_S = 60.0`、`_PROVENANCE_MIN_QUEUE_BUDGET_S = 16.0` を追加 (各定数に母集団・regime のコメント 1 行)。
- 2858〜2879 `_dispatch_timeout_overrides`: **不変**。
- 2882〜2892 `_default_dispatch(argv)`: signature 不変。`dispatch_compute` import の後に env を読み (`_outer_deadline_monotonic(environ) -> float | None`、有限でなければ ValueError)、None なら現行 kwargs のまま `dispatch_compute.dispatch(argv, **kwargs)`。設定時は §2 項 3〜5。
- 2895〜 `_invoke_dispatch`: 不変 (ValueError は既存の `except (Exception, KeyboardInterrupt)` で rc=16)。
- 3586 / 3597 / 3648 の 3 呼出し: 不変 (起点を渡さない)。

`orchestrator/tests/test_check_ai_provenance.py` (新規、`_default_dispatch` を直接 + `main` 経由の 3 経路)
- `test_outer_deadline_unset_preserves_dispatch_kwargs` — monkeypatch した `dispatch_compute.dispatch` が受ける kwargs が `{"task": "provenance", "repo_root": REPO}` と exact 一致 (D612 設定時はその 2 key だけ加わる)。
- `test_outer_deadline_derives_deadline_and_queue_wait` — fake monotonic (例 now=1000、K=1470) で `deadline_at == 1438.0`、`queue_wait_timeout_s == 470 − 32 − 90 − 60 == 288.0` (期待値はテスト側で独立に置く)。
- `test_outer_deadline_applies_to_all_dispatch_entries[force|headroom_short|cap_oom]` — `main` 経由、`site=PEGASUS_LOGIN`、admission / queue / scope を固定、末端 monkeypatch で kwargs を捕捉。cap_oom では scope 中に fake clock を進め、残余が減ることを固定。
- `test_outer_deadline_refuses_before_dispatch` — remaining 30 / queue_budget が 15.9 / 負値 → dispatcher 呼出し 0、rc=16、理由行の数値。境界 `queue_budget == 16.0` は呼ぶ。
- `test_outer_deadline_composes_d612_with_min` — Q 明示値が導出値より小 / 大 / 同値 / 0 (0 は投入前拒否)。G 明示値は不変で渡る。
- `test_outer_deadline_invalid_value_returns_infra` — 空、空白、文字列、NaN、±Inf → rc=16、dispatcher 未呼出し。負・過去の期限 (remaining < 0) は「不正」ではなく残余不足で拒否。
- `test_outer_deadline_reserved_intervals_fit_outer` — `R_post > 0`、`deadline_at + R_post == K`、`queue_wait_timeout_s + C + M_pre + R_post ≤ remaining`、`M_pre ≥ 2 × (15.9 + 5.0)`、`Q_MIN ≥ 3 × 5.1` を検査 (DW-O13)。
- `test_outer_deadline_uses_dispatcher_default_constants` — `dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S` / `DEFAULT_CLEANUP_BUDGET_S` を monkeypatch → 導出が追随。
- `test_outer_deadline_terminal_line_reports_observable_values` — rc=0/1/16 と例外時: main の返却 rc 自体を assert、終端行に `remaining_at_dispatch_s` / `remaining_at_return_s` / rc、queue/RUN の実測値を出していない。
- `test_outer_deadline_does_not_change_local_scope_path` — 正常/不正 env でも bounded scope の argv/cap/rc 不変、dispatcher 未呼出し。

`orchestrator/tests/test_dev_wave_land.py`
- 4820: `ast.Constant` → `ast.Name` かつ `id == "_PROVENANCE_AUDIT_TIMEOUT_S"`、`provenance = getattr(LAND, id)`、`assert provenance == 480`。1280 算術は不変。
- 5843〜5857: env exact 一致に 1 key 追加 (値は `monotonic_before + 480 ≤ float(v) ≤ monotonic_after + 480` の範囲検査、他 key は exact)、`timeout == LAND._PROVENANCE_AUDIT_TIMEOUT_S == 480`、TimeoutExpired の注入値を定数参照。
- 9997: 定数参照。reason が従来どおり `after 480 seconds` を含むことを維持。
- 新規 `test_provenance_outer_deadline_overwrites_inherited_value` (継承 env `"9999"` でも上書き)。
- `_assert_non_authoritative_provenance_rc_retains` (9942): fake stderr に予算行を入れ、land の reason が従来どおり (rc=16 の文面 exact) で stderr を転送しないことを固定。

## 4. 変異の事前登録 (DW-M01、段 6 の matrix、位置は実装後の行へ再照準)

| id | category | 変異 | 期待 |
|---|---|---|---|
| M1 | negative | `deadline_at = K − R_post` → `K` (R_post 欠落) | KILLED (reserved_intervals / derives) |
| M2 | negative | queue_budget から `C` を除く | KILLED (derives / reserved_intervals) |
| M3 | negative | queue_budget から `M_pre` を除く | KILLED (derives / reserved_intervals) |
| M4 | negative | `min(Q_existing, queue_budget)` → `max` | KILLED (composes_d612) |
| M5 | negative | 拒否条件 `<` → `>=` | KILLED (refuses / derives) |
| M6 | negative | 拒否条件 `<` → `<=` | KILLED (境界 16.0 の正例) |
| M7 | negative | env 未設定でも導出 kwargs を足す | KILLED (unset_preserves) |
| M8 | negative | `deadline_at` を kwargs から外す | KILLED (derives / all_entries) |
| M9 | negative | 不正値を未設定扱い (None) にする | KILLED (invalid_value) |
| M10 | negative | land: env 設定行を削除 | KILLED (land env exact / 範囲検査) |
| M11 | negative | land: `env[...] =` → `env.setdefault(...)` | KILLED (overwrites_inherited) |
| M12 | negative | land: `_PROVENANCE_AUDIT_TIMEOUT_S = 480` → `481` | KILLED (== 480 / 1280 算術は通る → == 480 が単一理由) |
| E0 | positive (等価) | `min(a, b)` → `min(b, a)` | SURVIVED |

matrix は独立 clone (D1009) で `tools/mutation_worktree.py` を dispatch 経路で走らせ、runner は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_check_ai_provenance.py orchestrator/tests/test_dev_wave_land.py -q -rf` (所要見積り: 2 file で 1 run 5〜8 分 → probe と final を分け、baseline + 13 変異)。期待 node は probe (全件 SURVIVED 期待) で集める。

## 5. Pegasus 実走の事前登録 (段 6、author 完了・親の焦点走緑の後、wave 木から、子の編集停止中)

| 走 | 設定 | 期待 | 記録 |
|---|---|---|---|
| L1 正例 | `IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC=$(monotonic+480)` `--force-dispatch` (D612 未設定) | rc=0、receipt に `queue_wait_s` / state_history、終端行の `remaining_at_return_s ≥ R_post`、h = return→exit を stderr の時刻から | job dir `live/L1.*` |
| L2 負例 (投入前拒否) | 期限 = monotonic + 30 | rc=16、拒否行、新規 submission dir 無し、hold 無し | `live/L2.*` |
| L3 負例 (queue 取消) | 期限 = monotonic + (32 + 90 + 60 + 30 + 前段見込 5) ≈ +217 → Q ≈ 30 秒 | 混雑時: `terminal_reason=queue-wait-timeout`、qdel 実行、rc=16、`orphan-hold.json` 無し。RUN へ進んで完走したら「発火せず = 負例未観測」と記録 (成功に数えない) | `live/L3.*` |

monotonic の取得は checker と同じ `python3 -c "import time; print(time.monotonic())"` を直前に叩く (同一 host)。

## 6. 裁定パッケージ (段 7 で insight / decisions fragment に載せる、本 wave は実装しない)

**択: land の provenance 監査の外側予算を D2148 項 8 型 (外側が全区間を覆う) へ延ばすか。**
- (a) 480 維持 + 内側導出 (本 wave の C-2804): 成功集合は上記 2 帯で縮む、RUN/collection hold は残る、land の累積 lock 待機 180 秒 (D1996) と検査 harness の 1280 秒算術は不変。
- (b) 区間和 (P180 + Q900 + W3600 + G300 + A60 + C90 = 5130 秒) へ延長: 内側維持 (項 8 の形)、検査 harness の 1280 秒算術を再設計、lock 外なので lock 保持は延びないが land 1 回の最長が 85 分。
- (c) 中間値 (例 1380 = 480 + 900): 480 秒超の一部を救うが全区間は覆えず内側短縮か残留が残る、1280 算術の改訂が要る。
- (d) dispatch 時だけ延長: checker から経路通知が要り、`subprocess.run(timeout=固定)` の構造変更 (段階 timeout) が要る。
- **親の推奨: (a) を今 land し、(b)〜(d) は改善後 checker の混雑時観測 (T-2805、D2170 再訪条件) と L1 の h 実測が揃ってから決める。** 材料: 段 1 の 85 件 (母集団限定)、F975 の login 6 点 (旧 checker)、本 wave の L1〜L3。

## 7. brief の訂正 (段 7 の insight に反映)
- (c) の「bytes 同値を meta-test で pin」→「列挙入力に対する受理・拒否結果と値の比較」。
- (b) の「pending orphan hold と PBS job が残る」→「投入後・pending 解除前の kill では残る (qsub 前・終端後は残らない)」。
- (b) の 1280 秒は「検査 harness の watchdog」であり production の watchdog ではない。
- (P1) の「項 8 を保つ」→ 撤回。本契約は項 8 の実装ではない (§2)。
- (P4) checker が出せるのは予算・経過・rc まで。区間の権威は receipt。
- (a) の母集団: 残存 worktree/job dir の受領証 85 件、撤去済み wave を含まない、全史/range・旧新 checker・rc 混在、land 呼出しの無作為標本ではない。
