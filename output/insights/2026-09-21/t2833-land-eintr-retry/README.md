# [T-2833] land の登録 worktree path 解決を InterruptedError のときだけ最大 5 回呼び直す — F672 経路の局所修正 (2026-09-21)

`authority: none` / `default_effect: no-state-change`

**種別:** 実装 wave (軽量版、Codex author 1 単位、fix なし)。段 2・3 は省略、段 6 の敵対レビュー 2 本は **Codex の利用上限のため独立 context の Claude 子で代替した** (§5)。

- 日付: 2026-09-21 (JST)
- wave: `dev-wave-t2833-land-eintr-retry`、branch `worktree-dev-wave-t2833-land-eintr-retry`、着手時 local main `d99c556dfa23e446987ef3ccbb5c018986fe10b5` (開始 gate `--mode fresh` rc=0、乖離 0)
- 裁定: D2206 項 1 (第 29 回 /rulings、ユーザー「推奨通りで」)。一次資料: `output/insights/2026-09-21/land-roundtrip-diagnosis/README.md` の §3.2 / §5.1、F672、D2119
- job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2833-land-eintr-retry/` (brief、段 4 / 段 6 裁定、prompt、変異 spec と ledger、焦点走 log)

## 0. 一行で・主張すること・しないこと

**fold gate の `_registered_worktree_paths` で、登録 path の `Path.resolve(strict=True)` が `InterruptedError` を返したときだけ、1 path あたり呼び出し最大 5 回 (初回 + 再試行 4 回) まで sleep なしで呼び直すようにした。**
呼び出し位置 (outer watchdog の armed 区間内)、例外 class、`retryable_same_request`、D2119 の rc 分類、watchdog 本体は変えていない。

**主張する。**

1. 受理集合の変化は「登録 path の strict resolve の前に `InterruptedError` が 1〜4 回前置されても、後続の結果 (受理・拒否・拒否の分類) は前置が無い場合と同一」だけである。
   `InterruptedError` が 5 回続いたときだけ、従来と同じ `_FoldGateFailure("registered worktree path cannot be resolved: ...")` (非 retryable) で拒否する。
   具体的には、1〜4 回の EINTR の後に成功すれば解決済み path、`FileNotFoundError` なら従来どおり `path.absolute()` で受理される (従来は 1 回目の EINTR で拒否)。
   EINTR 以外の `OSError` / `UnicodeError` は 1 回目で従来どおり拒否し、呼び直さない。期限超過で watchdog handler が投げる `_FoldGateInfrastructureFailure` は捕まえず、呼び直さず、変換もしない。
2. 新設 test 5 関数 / 9 node はこの受理・拒否を実体 (`_registered_worktree_paths` 本体・実物の watchdog と handler) で検査し、事前登録した変異 7 本 (M1〜M7) を全て単一理由で赤にした (§4)。
3. consumer 回帰は焦点走で 0 赤 (§4.1)。

**主張しない。**

- **EINTR 型の rc=31 が無くなったとは言わない。効果は未実測である。** 一次資料 §5.1 の 6.4〜10.2 分は削減候補区間の割当てで、削減量ではない。
  §3.2 の仮説 (100 ms 周期の SIGALRM が Lustre 上の遅い metadata 呼び出しを中断する) が正しい場合、sleep なしの 5 回が吸収できるのはおよそ 0.4 秒の stall までで (段 6 レビュー B の観察)、
  それより長い stall では 5 回とも中断されうる。**使い切れば同じ文言 `registered worktree path cannot be resolved: [Errno 4] Interrupted system call` の rc=31 が残り、
  その扱いは F672 の再発検知と、是正済みの復旧 (同じ tested tip / landing tip / receipt で再投入すれば新規登録として検査を再実行する、一次資料 §3.2) のままである。**
- 他の strict resolve / `os.lstat` 経路 (object store・隔離 `/tmp`・`_open_dir`) へは広げていない (D2206 項 1、失敗は retryable 側へ流れる)。
- Codex の敵対レビューは受けていない (§5)。

## 1. 変更の実体

| commit | 内容 |
|---|---|
| `2a29a2381` | `tools/dev_wave_land.py` +10/−1 (定数 `_REGISTERED_WORKTREE_RESOLVE_ATTEMPTS = 5` と `_registered_worktree_paths` の resolve を囲む `for` / `try` / `except InterruptedError`)、`orchestrator/tests/test_dev_wave_land.py` +170 (新設 5 関数)。Codex author (gpt-6-astra / medium)、既存 test は不変 |

- production の呼び出し元は `_execute_fold_gate` の先頭 1 箇所で、`_run_fold_gate` の `with _FoldGateOuterWatchdog(budgets.outer_seconds):` の中にある (差分はこの区間に触れていない)。
- 段 4 の規模上限 (production 25 行、test 250 行) 内。所有外の変更 0。

## 2. test と裁定の対応

| 新設 test (node) | 要件 | 殺した変異 (観測) |
|---|---|---|
| `test_registered_worktree_paths_retry_interrupted_resolve[1]`、`[4]` | 1 回 / 4 回の EINTR の後に成功 → 戻り値が注入なしと完全一致、呼び出し k+1 回 | M1 (両方)、M2 (`[4]`) |
| `test_registered_worktree_paths_exhaust_interrupted_resolve` | 5 回連続の EINTR → `_FoldGateFailure`、型が厳密に一致、`retryable_same_request is False`、cause、呼び出し 5 回ちょうど (6 回目は番兵) | M1、M2、M3、M6、M7 |
| `test_registered_worktree_paths_do_not_retry_other_oserrors[permission]`、`[eagain]`、`[eio]`、`[eintr-then-permission]` | 他の `OSError` は呼び出し 1 回で拒否 (EINTR の後なら 2 回) | M1 (`[eintr-then-permission]`)、M4 (4 node) |
| `test_registered_worktree_paths_keep_absent_after_interruption` | EINTR → `FileNotFoundError` なら `path.absolute()` で受理、呼び出し 2 回 | M1、M4 |
| `test_registered_worktree_paths_propagate_watchdog_during_retry` | 実物の watchdog を armed にし、2 回目の中で時計を期限後へ進めて `signal.raise_signal(SIGALRM)` → 実 handler の `_FoldGateInfrastructureFailure` がそのまま上がる、呼び出し 2 回、itimer と handler が元に戻る | M1、M5 |

- **D2206 項 1 の「SIGALRM handler 下で `InterruptedError` を 1 回注入して成功する test」に 1 対 1 で当たる node は無い。** `T1[1]` (handler 無しで 1 回注入 → 成功) と
  `propagate_watchdog_during_retry` (armed 下で 1 回注入 → 2 回目へ到達) の組で満たす。期限前の `_alarm` は何もしないので (`tools/dev_wave_land.py` の `_FoldGateOuterWatchdog._alarm`、
  `_fold_gate_now() >= self.deadline` のときだけ raise)、armed か否かで分岐は変わらない。合成注入の `InterruptedError` は handler を通らない。この等価性はコードで確認した (段 6 レビュー A の A6)。
- 検出の仕方の注記: M4 (他の `OSError` も呼び直す) の検出は呼び出し回数 (5 ≠ 1 / 2) による。回数 = 1 は 2 回目を呼ばないことの証明なので、「1 回失敗して次は成功する」入力も拒否されることまで押さえる (段 6 レビュー B)。
  既存の `test_registered_worktree_paths_fail_closed_for_other_resolution_errors[permission]` は回数を見ないので M4 で緑のまま。

## 3. 段構成と逸脱

- 段 1 brief → 段 4 裁定 (段 2・3 は省略: 設計は D2206 と一次資料 §5.1 で確定、択一なし) → 段 5 Codex author 1 本 (14:13〜14:17 JST) → 段 6 (焦点走・変異・レビュー 2 本) → 段 7。
- **段 6 の敵対レビューは Codex review 子 2 本を起動したが、2 本とも Codex の利用上限 (`You've hit your usage limit ... try again at Sep 26th, 2026 7:35 PM`、14:40:51 JST) で rc=1・出力 0 だった。**
  D582 に従い自動再試行せずユーザーへ通知した。実装は Codex author commit で完了していたので、レビューは独立 context の Claude 子 2 本 (Plan / opus、同じ prompt・同じ 2 レンズ、read-only) で代替した。
  DW-S06-A / DW-O01 が指定する「codex」からの逸脱である (F818 の再発、failures fragment)。
- fix は無い (must-fix 0)。したがって Codex 不可用は実装差分に影響していない。

## 4. 検証

### 4.1 焦点走 (親、計算ノード、commit `2a29a2381`)

- 対象: 変更 test file `orchestrator/tests/test_dev_wave_land.py`、land tool の consumer test 7 本 (`test_dev_wave_wait.py`、`test_run_tests_shards.py`、`test_acceptance_schedule_order.py`、
  `test_flaky_test_holds_contract.py`、`test_check_docs.py`、`test_t139_approval_payload.py`、`test_t793_approval_d291.py`)、DW-O26 の inventory 4 群
  (`test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`、`test_official_perf_closure.py`、`test_p3_exploration_namespace.py`、`test_p3_b4_wiring_probe.py`)。
- 結果: rc=0、**1,824 passed / 4 skipped、赤 0** (request 15068.nqsv、Elapse 85 s、runner 報告 79.64 s)。
- 全史 provenance 監査 (統合 commit 後): rc=0、12,363 件、新規違反なし。

### 4.2 変異 (独立 clone、main = `2a29a2381`、`tools/mutation_worktree.py --runner-mode dispatch`、runner = `run_tests.py --force-dispatch orchestrator/tests/test_dev_wave_land.py -q -rf`)

- 事前登録 (段 4、実装前): M0〜M7 の 8 本。実行は probe (全件 SURVIVED 期待で観測 node を収集) → final (観測 node を KILLED 期待の完全集合として登録) の 2 段。
- probe (spec sha256 `16539f5ab3fe…`): baseline PASSED、M0 SURVIVED、M1〜M7 は新設 test だけを赤 (既存 test の赤 0)。各 node の赤理由を pytest の stdout で確認し、全て単一理由だった。
- **final (spec sha256 `4c4553acd321…`): rc=0、KILLED 7 / SURVIVED 1 (M0、期待どおり)、期待との一致 8 / 8、不一致 0、baseline PASSED。** 観測 node 集合は probe と完全一致。
- 等価対照 M0 が SURVIVED なので、runner 範囲 (`test_dev_wave_land.py` の全 node) に「source の bytes が HEAD と違うだけで落ちる」drift 層は無い。
- node 単位の表は `mutation-matrix.md`。段 4 の「殺すはずの test」列は下限で、観測はその超集合 (M1 = 6、M2 = 2、M4 = 5 node、超過分も新設 test かつ単一理由、段 6 レビュー B の B3)。

## 5. 段 6 レビュー (Claude 代替子 2 本、read-only)

逐語の転記は `reviews/`。

| ID | 重大度 | 裁定 | 1 行 |
|---|---|---|---|
| A1 | should | real・採用 (記録) | brief の「受入の取り直しまで着地が遅れる」は是正済みの F672 復旧 (同じ receipt で再投入) と矛盾する。記録には写さない |
| A2 | should | real・採用 (記録) | 効果は未実測。使い切れば同じ文言の rc=31 が残り、F672 の再発検知と復旧はそのまま (§0) |
| A3 | nit | real・採用 | 受理集合の拡大に「EINTR の後の `FileNotFoundError` を absolute で受理」を含める (§0) |
| A4 | nit | real・不採用 | T3 の permission と eio は M4 に対して同じ性質を 2 回 pin (eagain は残す)。成果物影響なし |
| A5 | nit | real・不採用 | 導出可能な assert (T2 の isinstance、T4 の expected と `in`)。影響なし |
| A6 | nit | real・採用 | D2206 項 1 の正例は T1[1] と T5 の組で満たす (§2) |
| B1 | nit | real・不採用 (記録) | T5 に約 0.6 µs の実時間窓 (1 走あたり約 6×10⁻⁶) があり、`raise_signal` 後・`__exit__` の disarm 前に実 tick が来ると itimer が残って同じ worker の後続 test に連鎖しうる。既存 `test_fold_gate_outer_watchdog_fires_when_injected_clock_advances` も同じ構造。test の後始末の強化は Codex author が要る |
| B2 | nit | real・採用 | 「EINTR の後に OSError 以外の例外 (3.10 の ELOOP → `RuntimeError`)」も前置が無い場合と同じ分類 (retryable Infra) になる。§0 の一般形で書いた |
| B3 | nit | real・採用 | 段 4 の kill 列は下限。final spec と §4.2 は観測集合を使う |
| B4 | nit | real・不採用 | T2 は同じ instance を 5 回投げるので `__cause__` が最後の EINTR かを区別できない。source は正しい |

- 親の自己懸念 (T3 が M4 を回数でしか見ない、DW-M03) は refuted (§2 の注記)。

## 6. 限界・言わないこと

- 効果は未実測 (§0)。次の混雑窓で rc=31 (EINTR 型) の件数を数えるのが実測の入口。
- Codex の敵対レビューは受けていない。独立 context の Claude 子 2 本は同じ prompt で実施したが、製品が違う。
- 受入全走は本記録 commit を含む tip に対して投入する (結果は本 README には書かない。worklog の次 entry か job dir の `acceptance-final-*.log`)。
- B1 の窓は既存 test と同じ構造で残る。

## 7. この dir の中身

- `README.md` — 本書
- `reviews/s6-review-A.md`、`reviews/s6-review-B.md` — 段 6 レビュー 2 本の転記
- `mutation-matrix.md` — 変異 final の node 単位の表
