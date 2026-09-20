## 変更一覧

**480 秒を固定し、env が設定された dispatch 経路だけに内側期限を導入する。queue timeout 後の回収余裕は確保するが、RUN 中の deadline 到達による hold latch までは解消できない。**

行番号は現 worktree の変更前を指す。

| file:line | 変更前 → 変更後 |
|---|---|
| `tools/dev_wave_land.py:3555` 直前 | `_PROVENANCE_AUDIT_TIMEOUT_S = 480` と env 名定数を追加する。 |
| `tools/dev_wave_land.py:3560` | `PYTHONDONTWRITEBYTECODE` の設定に続けて、`env["IZANAGI_PROVENANCE_OUTER_BUDGET_S"] = str(_PROVENANCE_AUDIT_TIMEOUT_S)` を追加する。`setdefault` は使わず、継承値を必ず上書きする。 |
| `tools/dev_wave_land.py:3571` | `timeout=480` → `timeout=_PROVENANCE_AUDIT_TIMEOUT_S`。 |
| `tools/dev_wave_land.py:3633` | `detail = " after 480 seconds"` → `detail = f" after {_PROVENANCE_AUDIT_TIMEOUT_S} seconds"`。現行の `: {exc}` を含む reason 全体は変更しない。 |
| `tools/check_ai_provenance.py:49` 付近 | env 名、前段余裕、終了余裕、最小所要の定数を追加する。既存の scope 用 env と衝突しない `IZANAGI_PROVENANCE_OUTER_BUDGET_S` を採用する。 |
| `tools/check_ai_provenance.py:2882` 付近 | 新 env 専用 parser を追加する。未設定は `None`、設定済みは有限の正数のみ受理する。 |
| `tools/check_ai_provenance.py:2884` | `_default_dispatch` に起動時刻を受け取る keyword 引数と、末端 dispatcher 注入用引数を追加する。既存 kwargs を作った後、新 env 設定時だけ期限の導出・投入前拒否・終端診断を行う。 |
| `tools/check_ai_provenance.py:2895` | `_invoke_dispatch` は `_default_dispatch` を介して注入先を呼び、既存の例外一義化を維持する。parser の `ValueError` もここで rc=16 へ写す。 |
| `tools/check_ai_provenance.py:3526` の直前 | `main` の最初の実行文を `started_at = time.monotonic()` とする。 |
| `tools/check_ai_provenance.py:3586,3597,3648` | 3 本すべての `_invoke_dispatch` 呼出しへ同じ `started_at` を渡す。cap_oom 後も時計を取り直さず、local scope に費やした時間を控除する。 |
| `orchestrator/tests/test_check_ai_provenance.py:6805` 周辺 | kwargs・予算・拒否・終端診断の新規テストを追加する。 |
| `orchestrator/tests/test_dev_wave_land.py:4814,5812,9986` | 下記の既存 pin を更新する。 |

`_dispatch_timeout_overrides`（checker:2858、harness:1395）は編集しない。dispatcher、`run_tests.py`、bounded local の実装・引数・admission 判断も変更しない。

**注入 seam は明示的に整理する。** 現在の `main(dispatch_fn=...)` は kwargs 構築を迂回するため、そのままでは要求された検査ができない。次の接続にする。

```python
main(...)
  -> _invoke_dispatch(dispatch_fn, argv, started_at=started_at)
  -> _default_dispatch(argv, started_at=started_at, dispatch_fn=dispatch_fn)
  -> selected_dispatch(argv, **dispatch_kwargs)
```

`selected_dispatch` は未注入なら `dispatch_compute.dispatch`。既存テストの argv 専用 fake は `**kwargs` を受ける形へ改訂する。これはテスト用 seam の変更であり、env 未設定時の本番 dispatcher kwargs は従来と同一にする。

## 導出式と定数

### 採用案

| 記号 | 値・定義 | 根拠と母集合 |
|---|---|---|
| `B` | 外側予算。land は **480 秒** | land の現行値を維持する。 |
| `t0` | `main` 先頭の monotonic 時刻 | admission・local scope・fallback の経過を含める。 |
| `e` | `now - t0` | dispatch 直前までの実経過。 |
| `M_pre` | **180 秒** | T-2484 の receipt 3,849 件について、brief が引用する前段 max **15.9 秒**の約 **11.3 倍**。harness の先例と同じ値。 |
| `R_post` | **32 秒** | `2 × ceil(15.9)`。終了処理実測がないため、前段 max を代理尺度にした暫定値。 |
| `Q_min` | **16.6 秒** | 段1の provenance receipt 85 件における qsub 後合計の最小値。 |
| `C` | `dispatch_compute.DEFAULT_CLEANUP_BUDGET_S` | 現行 **90 秒**。checker に数値を複製しない。 |
| `Q_existing` | D612 明示値、なければ `dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S` | 現行既定 **900 秒**。 |
| `W/G/A` | dispatcher の既存値 | 既定 walltime 3600、grace 300、accounting 60 秒。変更・再定義しない。 |

**`R_post` の根拠には限界がある。** 射影資料には receipt 保存から checker 終了までの実測 max がない。32 秒を「後段実測の2倍」と報告してはならない。代理尺度による暫定値として実装コメント・裁定資料に残し、段6で後段を観測する。DW-O13 が区間自身の実測 max を要求するなら、この部分は未充足である。

導出は dispatcher の遅延 import と env 検証の後、呼出し直前に行う。

```python
remaining = budget - (now - started_at)
deadline_at = now + remaining - R_post
queue_candidate = remaining - R_post - C - M_pre
queue_wait_timeout_s = min(Q_existing, queue_candidate)
```

`queue_wait_timeout_s < Q_min` なら dispatcher を呼ばない。負数をゼロへ丸めたり、最小値へ引き上げたりしない。

例として `B=480, t0=1000, now=1010` なら、

```text
elapsed = 10
remaining = 470
deadline_at = 1448
queue_wait_timeout_s = 168
```

### queue と cleanup の関係

dispatch 呼出しから qsub の基準時刻までを `p`、queue timeout の観測遅延を `δ` とすると、queue timeout 検出時刻は概ね、

```text
Tq = now + p + Q + δ
deadline_at - Tq ≥ C + M_pre - p - δ
```

したがって **`p + δ ≤ M_pre` の範囲では cleanup の90秒を残せる**。`M_pre` は前段だけでなく、poll・qstat による検出遅延を吸収する余裕でもある。無制限の遅延まで保証する式ではない。

前段が既観測 max の15.9秒、観測遅延が既定 poll の5秒だけなら、180秒の予約には十分な余裕がある。ただし、qstat 自体の遅延が5秒以内という証拠にはならない。

RUN 初観測後は queue timeout が無効になり、dispatcher:4207 の、

```text
total_deadline = min(run_observed_at + W + G, deadline_at)
```

が効く。**通常の長い queue を先に切る設計にはなるが、deadline に掛かる区間を RUN だけへ限定できるわけではない。** 前段の超過、状態観測の遅延、成果物回収の deadline 到達も残る。回収は dispatcher:4245 の `min(now + A, deadline_at)` に従う。

RUN 中に `deadline_at` へ達すると、

```text
effective_cleanup_budget = min(C, max(0, deadline_at - now)) = 0
```

となる。qdel は `cleanup-budget-exhausted` で実行されず、job が残り得るものとして hold が latch される。RUN 中央値30.7秒、新 checker の24〜42秒は通常完走の材料であり、上限保証ではない。

**dispatcher を変更せず、許可された予算伝播だけでこの hold latch を必ず防ぐ追加策は無い。** RUN を早く打ち切っても現行 fresh-qstat gate は RUN の qdel を許さない。deadline をさらに前倒しするだけでも、deadline と cleanup 締切が同時に動くため解決しない。

### 厳密な `<480` 検査の扱い

D612 値で制限されない場合、指定式の予約総和は、

```text
e + M_pre + Q + C + R_post = B
```

であり、**全予約の総和 `<480` は成立しない**。テストでこれを偽ってはならない。

32秒を「終了処理の代理所要16秒＋追加余裕16秒」と説明し、次を別々に検査する。

```text
e + M_pre + Q + C + R_post ≤ 480
(deadline_at - t0) + 16 < 480
```

後者は `448 + 16 = 464 < 480`。これは代理所要を置いた運用予算の検査であり、終了処理の実測保証ではない。

## fail-closed と受理集合

新 env は **dispatch 経路へ入った時点で検証する**。local、compute、message-file 免除などの経路は変更しない。

| 入力・状態 | 現行 | 変更後 |
|---|---|---|
| 新 env 未設定 | 既存 kwargs で dispatch | 完全に同じ kwargs。deadline・既定 Q を明示追加しない。 |
| 有限の正数、導出 Q が16.6以上 | env を参照しない | 導出期限を渡して継続。 |
| 有限の正数だが残余不足 | 同上 | qsub 前拒否、rc=16。 |
| 空文字・空白だけ・非数値 | 同上 | `ValueError` → `_invoke_dispatch` → rc=16。 |
| `0`, `+0`, `-0`, 負数、NaN、±Inf | 同上 | 同上。無視して無予算 dispatch へ戻さない。 |
| 正の小数・指数表記 | 同上 | `float` で有限の正数なら受理し、残余判定へ進む。 |
| D612 Q 明示値あり | 明示値を渡す | `min(明示値, queue_candidate)`。 |
| D612 Q が0、かつ新 env あり | Q=0を渡す | 合成後 Q が最小所要未満なので投入前拒否。 |
| D612 Q が0、新 env なし | Q=0を渡す | 現行維持。 |
| D612 G 明示値あり | 明示値を渡す | 同じ G を渡す。実効 overall deadline は dispatcher 内で `deadline_at` と min。 |
| D612 不正値 | rc=16 | 現行維持。 |
| bounded local を選択 | bounded scope 実行 | 新 env の正否を含め、この経路は不変。 |
| dispatcher が rc=1 / rc=16 を返す | 違反 / infra | 同じ rc を返す。成功へ読み替えない。 |

新 env の空文字は「未設定」と扱わない。D612 parser の空文字受理は変更せず、新しい外側予算契約では期限指定の誤りを拒否する。

投入前拒否の1行案：

```text
provenance dispatch budget insufficient: budget_s=30 elapsed_s=1 remaining_s=29 queue_budget_s=-273 minimum_queue_s=16.6 required_remaining_s=318.6 rc=16
```

ここで最小残余は `R_post + C + M_pre + Q_min = 318.6` 秒。16.6秒は「実行が必ず終わる最小時間」ではなく、brief が採用する経験的な投入閾値である。

これは `_no_execution_capacity`:3170 のメモリ・queue 可用性不足とは別原因なので、同じ文面へ畳まない。期待された残余不足は直接 rc=16 を返し、不正 env は既存の例外経路へ渡す。

**終端診断：** checker は dispatcher receipt を読み戻す経路を持たず、戻り値は rc のみ。checker 内の監査再利用 receipt は別物である。したがって実測 `queue_wait_s`・RUN 区間を checker が出す設計にはしない。

実際に dispatcher を呼んだ経路の終端には、例えば次を1行出す。

```text
provenance dispatch budget: budget_s=480 elapsed_s=47 remaining_s=433 rc=0
```

queue/RUN 区間の権威は dispatcher receipt とする。投入前拒否には専用行を使い、同じ拒否の要約を重複表示しない。env 未設定時は新しい予算診断を出さない。

## テスト計画

### checker の新規テスト

置き場は `orchestrator/tests/test_check_ai_provenance.py:6805` 周辺。共通 fixture は `monkeypatch`、`capsys`、可変値を返す fake monotonic clock、`capture_dispatch(argv, **kwargs)`。新規 main 呼出しには必ず `site=site_policy.PEGASUS_LOGIN` を明示する。

fixture は新 env と D612 の Q/G env を消去し、bounded membership・admission・queue 判定を固定する。実 scheduler、実履歴監査、実 scope は呼ばない。

| 新規 test 名 | 検査内容 |
|---|---|
| `test_outer_budget_unset_preserves_dispatch_kwargs` | main＋注入で、kwargs が `{"task": "provenance", "repo_root": REPO}` と exact 一致。D612 設定時は従来の2 keyだけが加わる。 |
| `test_outer_budget_derives_deadline_and_queue_wait` | `t0=1000, now=1010, B=480` で deadline=1448、Q=168。独立した期待値で検査する。 |
| `test_outer_budget_applies_to_all_dispatch_entries` | force、headroom_short、cap_oom の3経路をパラメータ化。cap_oom 前の scope 時間も elapsed に入る。 |
| `test_outer_budget_refuses_before_dispatch` | B=30、経過で枯渇したB、Q_min直下を拒否。注入 dispatcher の呼出し数0、rc=16、理由行の数値を確認。 |
| `test_outer_budget_queue_threshold_boundary` | Q=16.6は呼ぶ、直下は呼ばない。丸めた診断値で判断していないことも検査。 |
| `test_outer_budget_composes_d612_with_min` | Q明示値が導出値より小さい／大きい／同値／0。G明示値は不変。 |
| `test_outer_budget_invalid_value_returns_infra` | 空文字、空白、文字列、±0、負数、NaN、±Inf。rc=16、dispatcher未呼出し。 |
| `test_outer_budget_reserved_intervals_fit_land_timeout` | 上述の予約総和 `≤480` と、内側期限＋終了代理所要 `<480` を両方検査する。 |
| `test_outer_budget_queue_timeout_leaves_cleanup_reserve` | 捕捉 Q/D を使い、前段15.9秒＋既定poll遅延の時点で C が残ることを検査。 |
| `test_outer_budget_uses_dispatcher_default_constants` | dispatcher の Q/C 定数を別値へ monkeypatch し、導出が追随することを検査。 |
| `test_outer_budget_terminal_diagnostic_reports_observable_values` | rc=0/1/16、例外時の終端診断。elapsed・残余を確認し、未観測RUN値を出していないことを検査。 |
| `test_outer_budget_does_not_change_local_scope_path` | 正常値・不正値でも local scope の argv/cap、返却rc、dispatch未呼出しが不変。 |

新しい数値期待値は production の導出 helper を再利用せず、テスト側で独立に置く。

既存 `dispatch_fn` fake は `**kwargs` を受ける形へ改訂する。特に checker tests:5539、5656 の `assert_called_once_with(argv)` は、env未設定時の `task`・`repo_root` を含む exact call に更新する。argv 専用 lambda がある5579、5896、6524、6550なども同様。例外一義化テスト:6770付近は、kwargs を受けた後に意図した `OSError` を投げる形を維持する。

### land の既存 pin：変更前後

| test | 変更前 → 変更後 |
|---|---|
| `test_cumulative_wait_budget_arithmetic_uses_production_timeouts`:4814 | timeout AST が `ast.Constant` で、その `.value` を取得 → `ast.Name` かつ id が `_PROVENANCE_AUDIT_TIMEOUT_S` と確認し、`getattr(LAND, timeouts[0].id)` で値を取得する。`assert provenance == 480` を追加。既存1280秒 watchdog 算術はそのまま。 |
| `test_provenance_subprocess_contract_and_exception_mapping`:5812 | env exact一致:5843 に新 env 1 keyを追加。期待値は `str(LAND._PROVENANCE_AUDIT_TIMEOUT_S)`。subprocess kwargs のkey集合は不変。 |
| 同 test:5853 | `kwargs["timeout"] == 480` → `kwargs["timeout"] == LAND._PROVENANCE_AUDIT_TIMEOUT_S == 480`。さらに `float(kwargs["env"][ENV]) == kwargs["timeout"]`。 |
| 同 test:5857 | `TimeoutExpired(..., 480)` →定数参照。例外が `_Reject(RC_PROVENANCE)` へ写る既存検査を維持。 |
| `test_provenance_checker_timeout_is_retryable_and_retains`:9986 | 注入例外:9997の480を定数へ置換。reason に従来の `after 480 seconds` と例外文字列が保たれる検査を追加。release_safe=false、retryable=true、lease保持、stderr exact一致は維持。 |

AST pin の最小変更：

```python
assert len(timeouts) == 1
assert isinstance(timeouts[0], ast.Name)
assert timeouts[0].id == "_PROVENANCE_AUDIT_TIMEOUT_S"
provenance = getattr(LAND, timeouts[0].id)
assert provenance == 480
```

さらに `test_provenance_outer_budget_overwrites_inherited_value` を追加し、env に `"9999"` が入っていても subprocess へ `"480"` が渡ることを固定する。

**P4 の不変条件はテストで固定する。** 既存の infra/violation/timeout の分類テストを再利用する。`_assert_non_authoritative_provenance_rc_retains`:9942 の fake stderr に予算診断行を入れ、land の reason が従来どおりで、その診断が land stderr へ転送されないことを確認する。rc=16 の reason は部分一致から従来文面の exact一致へ強める。

`test_t2337_dispatch_timeout_overrides.py` の期待値は変更不要。実ファイルの meta-test は parser の受理・拒否結果を比較しており、文字列としての bytes 比較ではない。ただし本 wave では指定どおり両 parser 本体の bytes を変更しない。同 suite を含む検証環境では、新 env を明示的に未設定にする。

**今回の検証結果：** 指定された Python 8ファイルはメモリ上の `ast.parse` を通過した。提案算術も確認した。変更後コード、pytest、Pegasus 実走は未検証である。

## 変異候補

対象行は変更前の挿入アンカー。段6では完成後の行番号へ置き換える。

| 対象・変異 | 期待 | kill 理由 |
|---|---|---|
| checker:2884付近、deadline式から `R_post` を削除 | KILLED | deadline期待値と内側＋終了余裕の検査が失敗。 |
| 同、Q式から `R_post` を削除 | KILLED | Q期待値・予約総和が失敗。 |
| 同、Q式から `C` を削除 | KILLED | Q期待値とcleanup余裕が失敗。 |
| 同、Q式から `M_pre` を削除 | KILLED | Q期待値・前段込み算術が失敗。 |
| 同、`min` → `max` | KILLED | D612大小両ケースで失敗。 |
| 同、拒否条件 `<` → `>=` | KILLED | 小予算・正常予算の双方が逆転。 |
| 同、拒否条件 `<` → `<=` | KILLED | Q=16.6境界の正例が失敗。 |
| 同、env未設定でも導出Qを追加 | KILLED | kwargs恒等のexact一致が失敗。 |
| 同、`deadline_at` を渡さない | KILLED | kwargs検査が失敗。 |
| checker:3648付近、cap_oom後に起動時刻をリセット | KILLED | local消費時間を控除するテストが失敗。 |
| checker:2882付近、不正値を未設定扱いへ変更 | KILLED | 不正値でdispatcherが呼ばれる。 |
| land:3560付近、env追加を削除 | KILLED | env exact一致・予算一致が失敗。 |
| 同、envを`setdefault`で設定 | KILLED | 継承値上書きテストが失敗。 |
| land:3571付近、timeoutまたはenv値だけ変更 | KILLED | timeout=env=定数=480の検査が失敗。 |
| checker:2884付近、有限値検証後の `min(a, b)` → `min(b, a)` | **SURVIVED** | 両値が有限であり、等価変異。 |

## Pegasus 実走手順

親が段6で、実装済み wave 木から行う。各試行は開始HEAD、環境変数、開始・終了時刻、rc、stderr、対応する submission/request ID、receipt と hold 状態を保存する。HEAD は試行中に動かさない。

1. **正例：480秒**

   ```bash
   IZANAGI_PROVENANCE_OUTER_BUDGET_S=480 python3 tools/check_ai_provenance.py --force-dispatch
   ```

   D612 Q/G 上書きは解除した状態で実行する。期待はrc=0、終端receipt、`queue_wait_s`、`state_history` のRUN初観測から最終観測までの区間。checkerの予算診断と総経過も保存する。checkerの計測起点より前の起動時間、終了側の時間を可能な範囲で別計測する。

2. **負例：qsub前拒否**

   ```bash
   IZANAGI_PROVENANCE_OUTER_BUDGET_S=30 python3 tools/check_ai_provenance.py --force-dispatch
   ```

   期待はrc=16と専用理由行。試行前後を比較し、この invocation に対応する新規submission・job・holdがないことを確認する。共有領域全体が空であることは要求しない。

3. **負例：短いqueue timeout**

   例えば budget=340秒なら、導出Qは `38 − elapsed` 秒。実際のQが16.6秒以上になることを確認して使う。足りなければ、実測した前段に基づいて「R_post＋C＋M_pre＋約30秒＋経過見込み」となるbudgetを設定する。

   ```bash
   IZANAGI_PROVENANCE_OUTER_BUDGET_S=340 python3 tools/check_ai_provenance.py --force-dispatch
   ```

   混雑により未RUNのまま期限を超え、fresh snapshot が取消可能な状態なら、期待は `terminal_reason=queue-wait-timeout`、qdel実行、rc=16、対応する `orphan-hold.json` なし。qdelの結果とjob終端も確認する。

   **混雑していなければ発火しない。** 正常終了した試行は「発火せず＝負例未観測」と記録し、負例成功に数えない。RUNへ遷移してholdになった場合やqdel失敗も、その実際の結果を残し、hold無しの正例へ読み替えない。

## 見送りと理由

- **480秒の延長：** scope外。分布、F975、残存するRUN deadline問題を裁定パッケージへ渡す。
- **CPU・loadによるdispatch選択：** D2170により保留。変更しない。
- **dispatcherのcleanup期限分離、RUNのqdel規則変更：** dispatcher変更禁止により見送る。
- **walltime短縮、追加watchdog・signal制御：** 今回の予算伝播を超える。RUNのhold消滅も保証できない。
- **receipt探索をcheckerへ追加：** invocationへの束縛と読取り経路が別途必要。区間の権威は既存receiptに置く。
- **landのreason拡張・stderr転送：** P4に反するため行わない。
- **終了余裕32秒を実測保証とすること：** 後段の母集合がないため不可。代理尺度として明記する。
- **予約総和が厳密に480秒未満という主張：** 指定式は上限使用時に480秒と等しい。予約総和と終了処理の想定所要を分けて検査する。

## 総括

P1〜P6は、**env設定時だけ期限を導出し、短い残余を投入前拒否する契約**として実装可能である。提案値は `M_pre=180秒、R_post=32秒、Q_min=16.6秒`。

ただし、RUN deadline到達時のhold latch、前後処理の実測上限不足、予約総和の等号は残る。したがって「queue待ちによる親の先行打切りを抑える」と評価し、**全区間でjob・hold残留を解消したとは扱わない**。書込み・pytest・Pegasus実走は行っていない。