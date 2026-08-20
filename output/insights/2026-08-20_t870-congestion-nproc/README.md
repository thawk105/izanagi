# 受入全走ボトルネック分析 — [T-870] queue congestion時の並列度低減 (item (e)) の実装可否 (2026-08-20)

依頼: 「受入全走のボトルネック分析・改善。リワードハック禁止」

計測 checkout = `.claude/worktrees/dev-wave-t870-congestion-nproc`、起点
`595662be1804283331d0dfe4aff1ae65f2f903b1`。実行環境は Pegasus login node。**実装なし
(分析のみ、production コード変更ゼロ)**。

## 結論

`docs/worklog.md` の T-870 系列 (entry 769 commit `dd29fd9c`、進行中 wave
`dev-wave-t870-lease-timing`) が未着手のまま残していた (e) 「queue 混雑時は待つのでなく並列度を
下げる」(`IZANAGI_TEST_NPROC=4`、`docs/archive/worklog-phase3-0816-566-567.md:57-61` の単独 file
実例) を、**受入全走 (`orchestrator/tests` フルスイート) にも適用できるか**という問いに絞って
分析した。

**結果: 現時点の evidence は、受入全走への (e) の実装を支持しない。実装せず、記録に留める。**
段3 敵対相談2レンズがこの結論を支持したが、親の初期分析にあった2つの過大な補助的主張
(「local実行は永久に不可能」「実測した空き容量が典型値」) は棄却した。加えて、両レンズが独立に、
本 wave の scope 外にある新しい改善候補 (peak 履歴を無視する明示 opt-in の一回限り local retry) を
指摘した。これは次wave向けの具体的な次の一手として記録する (「## 次の一手」節)。

## 実測で確認した事実 (file:line 根拠つき)

### 1. 受入全走は is_acceptance 分岐なしで login admission を通る

`tools/run_tests.py:2003` で `is_acceptance = _is_acceptance_run(args)` を計算するが、
続く local admission 分岐 (`2046-2053`) はこの変数を一切参照しない。D612
(`docs/decisions.md:24540-24564`) が禁止した「`_is_acceptance_run` による自動分岐」は存在しない
(段2 codex プランが確認、段3 両レンズが独立に再確認)。

### 2. `IZANAGI_TEST_NPROC` は admission 判定の**入力に含まれない**

`login_headroom.grant_budget(operation=..., max_bytes=..., min_bytes=..., scope_cgroup=...)`
(`login_headroom.py:1043-1049`) の引数に nproc・worker 数は無い。実運用の呼出し
(`run_tests.py:2052-2053`) も `operation` しか渡さない。nproc は admission **後**にだけ読まれる
(`run_tests.py:227-241`、`2192-2206`)。段2プランが file:line で確認済み。

### 3. `tests-full` の peak 履歴に 4 GiB 上限ちょうどの記録が残っている

親の runtime ledger (`/run/user/<uid>/izanagi-admission/peak-tests-full.peak`) を read-only で
確認した:

```json
{"operation":"tests-full","peak_bytes":4294967296,"recorded_at":1786017539.2337587}
```

`peak_bytes` は `MAX_LOCAL_BUDGET_BYTES` (`login_headroom.py:29-31`) と bit-exact 一致。
`recorded_at` は 2026-08-06 20:58:59 JST。`run_tests.py:1755-1763` の CAP_OOM 経路
(`_safe_remember_peak(..., max(cap, samples.peak_current or 0))`) はこの値を生成しうる読み。
ただし段3 レンズ sol (`verbatim/s3-lensA-sol.md` §1) が指摘した通り、peak record 自体に
outcome/provenance が無い (`operation`・`peak_bytes`・`recorded_at` のみ、
`login_headroom.py:947-974`) ため、**この特定 record が実際に CAP_OOM 由来だと record 単体からは
確定できない**。「4GiBちょうど」という値と CAP_OOM 経路の読みが整合するというに留める。

### 4. peak 履歴に staleness/expiry/decay は無い (段3 レンズ sol が file:line で確認)

`_peak_name`/`_remember_peak_locked`/`_recall_peak_locked` (`login_headroom.py:941-976`) は
timestamp を保存・型検査するだけで、経過時間による無効化はしない。予約 record 用の
`STALE_RECORD_MAX_AGE_S` (`login_headroom.py:37`, `693-735`) は `.json` 予約 record だけを対象とし
`.peak` record には適用されない。

### 5. `grant_budget()` の恒常計算により、現行 peak 記録がある限り nproc の値に関わらず DISPATCH になる

`login_headroom.py:1097-1125`: `peak=4294967296` から `estimated = ceil(peak*1.25) = 5368709120`
(5 GiB)。実運用は `max_bytes` を渡さないため既定上限 4 GiB (`login_headroom.py:1043-1049`)。
`usable = min(4294967296, available)` は定義上 4 GiB 以下だから `estimated(5GiB) > usable` が
恒に成立し、`available` (現在の空き容量) にも nproc にも依存せず DISPATCH になる
(`login_headroom.py:1117-1125`)。

段3 レンズ sol の是正 (`verbatim/s3-lensA-sol.md` §3): これを「絶対に永久固定」と一般化するのは
過大である。同一 `operation` key・既定 `max_bytes`・ledger 継続の3条件が揃う場合の恒常挙動であり、
別 operation key (`tests-partial-<digest>`)・呼出し側が `max_bytes` を明示的に変える設計・ledger の
外部消失 (`/run/user/<uid>` はセッション終了等で消える可能性があるが、これはコードの外の事実で
確認できない) などの経路では成立しない。正確な主張は「**既定の呼出し経路には、この状態から
自然に回復する内部機構が無い**」である。

### 6. 今日時点で `grant_budget(operation="tests-full")` を実際に呼び、判定を確認した (ledger 変更なし)

新規 driver を書かず、既存 `login_headroom` モジュールを直接呼ぶ最小実測
(DW-G01 生死実験先行) を行った。DISPATCH 判定時はレジャーへ一切書き込まないことをコード
(`login_headroom.py` の全 DISPATCH 分岐は `lease=None`) で確認したうえで実施した。

```
admission: Admission.DISPATCH
budget_bytes: None
reason: 前回ピーク 4294967296 bytes の見積もり 5368709120 bytes は今の余裕 370070616 bytes に
収まらないため、計算ノードへ dispatch します（予約控除後の観測余裕=370070616 bytes、算出予算=
5368709120 bytes、現在使用量=16410726400 bytes、回収不能量=12514831272 bytes、実効天井=
15032385536 bytes、生存中の予約=0 bytes）。
no lease created (no ledger mutation)
```

段3 レンズ sol・luna の両方が独立に、この1点測定 (「今の余裕=370070616 bytes」) を
「典型的な混雑度」と一般化することはできないと指摘した (時系列データが読める資料内に無い)。
この測定は「今この瞬間、この login node で `tests-full` は DISPATCH になる」という事実を確認する
だけに留め、一般化の根拠にはしない。

## 段2 codex プラン・段3 敵対相談2レンズ (逐語)

- `verbatim/s2-plan.md` — 段2 (`--stage plan`, read-only, reasoning=max)。コールグラフ file:line
  特定、nproc と予算計算の非連動の確認、(P1)(P2) の当初判定。
- `verbatim/s3-lensA-sol.md` — 段3 レンズ sol (`--stage consult --lane sol`)。正しさ・一般化境界。
  親の実測・結論の過大な部分を是正 (上記4節・6節)。
- `verbatim/s3-lensB-luna.md` — 段3 レンズ luna (`--stage consult --lane luna`)。
  scope・整合性・reward-hack 回避。「実装しない」自体は支持したが、「改善余地なし」「記録だけで
  完結」は過大とし、次の一手として明記すべき具体的な安全改善候補 (下記) を独立に提示した。

両レンズは worklog の T-870 節の行番号 (親の brief 執筆時点の参照は取り込み並行 land で
ずれていた) も指摘した。現物は本 worktree 内 `docs/worklog.md:1971-1986`
(内容は entry 769 と同一、carry のみ ID 番号が進んでいる)。

## 段4 裁定

- **(P1)** 「566/567 の nproc=4 手法が受入全走 (フルスイート) にも適用できる」→ **不支持、実装しない**。
  理由: nproc=4 での full-suite peak が 4 GiB 以内に収まり CAP_OOM を避けられるという直接証拠が
  無い。加えて、既定の呼出し経路では現行 peak 履歴 (4GiB 上限相当) がある限り、nproc の値に
  関わらず恒常的に DISPATCH になる (上記5節)。
- **(P2)** 「実装するなら明示 opt-in、自動選択・is_acceptance 分岐を追加しない」→ **支持**
  (前提の P1 が不成立のため今 wave では適用機会なし)。
- **棄却した過大な補助主張**: 「local 実行は永久に不可能」(→「既定経路には内部回復機構が無い」に
  限定)、「実測した空き容量 370070616 bytes が典型的な混雑度」(→ 1点測定であり一般化不可)。
- **今wave で実装しない理由 (規律5 「盛らない」の適用)**: 段3 両レンズが独立に指摘した
  「peak 履歴を無視する明示 opt-in の一回限り local retry」は、本 wave の brief・段2・段3 が
  検証してきた「nproc」仮説とは別の、新しい設計対象である。対象が並行アクセス前提の
  safety-critical ledger (`login_headroom.py`) であり、専用の brief → plan → consult を経ずに
  同一 wave 内で実装へ進むのは段階導入の規律に反する。したがって次の一手として明記し、
  今wave では実装しない。

## 段9 受入全走の実施中に追加実測した事実

本 wave 自身の受入全走投入 (段9) で、queue congestion による dispatch 失敗を実地に観測した
(1回目試行: main 前進後の全史 provenance 再監査が 480 秒枠で `TimeoutExpired`。2回目試行:
merge・全史監査は通過したが `[Pegasus dispatch] request ... の状態: QUE` の後
`queue-wait-timeout` (900秒既定) で `child_started=false`)。投入時、`ps` で少なくとも 15 以上の
別 wave が同じ受入 lease・compute dispatch queue を同時に奪い合っていることを確認した。

この2回目試行の失敗を受け、T-870 が新設した opt-in override
(`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`) が使えるか検討し、**受入形の launcher には
そもそも届かないことをコードで確認した**:

- `tools/dev_wave_wait.py` の `_acceptance_environment_preflight`
  (`tools/dev_wave_wait.py:2423-2456`) は `_AcceptanceEnvironment` を
  `pytest_addopts`/`pytest_plugins`/`task_run_id`/`task_runs_root` の **4 field 固定**で構築する。
  `PYTEST_ADDOPTS`/`PYTEST_PLUGINS` が非空なら即座に `_StageFailure` で受入自体を拒否する
  (`:2432-2433`)。
- 実際に観測した子 process の起動引数にも
  `--env-projection-json {"IZANAGI_TASK_RUNS_ROOT":null,"IZANAGI_TASK_RUN_ID":null,
  "PYTEST_ADDOPTS":null,"PYTEST_PLUGINS":null}` という**閉じた4キーの射影**だけが現れ、
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/`IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`/
  `IZANAGI_TEST_NPROC` はいずれも含まれない。
- したがって、operator が受入投入前に自分のシェルでこれらの override 環境変数を export しても、
  `tools/acceptance_launcher.py` 経由で起動される受入形の `python3 tools/run_tests.py` 子
  プロセスには一切伝播しない。**T-870 (entry 769) が今日実装した opt-in override は、通常の
  受入・焦点走そのものには構造的に適用できない** (ad hoc な `--force-dispatch <target>` 手動実行
  にだけ効く)。これは entry 769 自身の文言「通常の受入・焦点走は queue 混雑時に引き続き rc=16 で
  落ちる」と整合する挙動であり、今回コードで直接確認できた点が新規である。

## 次の一手 (今wave では scope 外、次 wave 候補)

- **[T-870] 系列への追加候補 (h)**: `tests-full` の peak 台帳に一度 CAP_OOM 相当の値
  (`4294967296` bytes) が記録されると、既定の呼出し経路 (`operation="tests-full"`, 既定
  `max_bytes`) では内部から自然に回復しない (staleness/expiry/decay 機構が無い、`login_headroom.py`
  全体で確認済み)。**安全な改善候補**: operator が明示的に一回限り peak 履歴を無視して local
  admission を再試行できる opt-in 機構。既存の safety 機構 (lock・atomic write・
  `MIN_LOCAL_BUDGET_BYTES`・`MemoryMax`・CAP_OOM 時の dispatch fallback) はすべて維持し、
  失敗時 (再度 CAP_OOM) は既存の記録経路に委ねる (台帳を特別扱いで消さない)。D612 が禁止した
  「既定値の自動選択」「`is_acceptance` 分岐」のいずれにも該当しない (D612 の射程は既定 timeout
  値と受入形分岐に限られる、`docs/decisions.md:24540-24549`)。検証内容 (テスト件数・mutation
  matrix) は一切変えない。実装するなら専用の brief (段1) から着手し、`login_headroom.py` の
  ロック・並行アクセス契約を段3 で専用レンズを立てて検証すること。
  full-suite の nproc=4 実測 (peak bytes・route) も、このrecovery機構と併せて次 wave で行うのが
  効率的 (recovery が無いと local 試行自体が起こらないため、nproc 単独の実測は今のままでは無意味)。
- **[T-870] 系列への追加候補 (i)**: opt-in override (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`) を受入・焦点走の launcher 経路 (`tools/dev_wave_wait.py`
  の `_acceptance_environment_preflight`/`_AcceptanceEnvironment`) へ、明示 opt-in のまま
  (既定は不変・自動選択なし) 到達させる設計を検討する。現状は ad hoc な手動 dispatch にしか効かず、
  T-870 が意図した「operator が文脈を把握して上書きできる」対象に受入・焦点走自体が含まれていない。
  ただし `_acceptance_environment_preflight` が `PYTEST_ADDOPTS`/`PYTEST_PLUGINS` を拒否する設計
  (再現性の保証) と衝突しない形に限る必要があり、専用の brief→plan→consult を要する。
