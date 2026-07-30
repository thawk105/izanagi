GO です。推奨は、既存の long-path roundtrip node を分割せず、実 `select` を roundtrip まで通した後だけ test-owned 同期で serve loop を制御する、1 テストファイル限定の test-only patch です。固定 `join(120)` は削除できます。

静的検査のみ実施し、pytest・mutation・受入コマンドは一切実走していません。緑は主張しません。ファイル編集も行っていません。

## 現行契約の確認

同名概念を次のように分離します。

| 概念 | 実体 | T-145 での扱い |
|---|---|---|
| production shutdown Event | [`Supervisor._shutdown`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:488) | `shutdown()` が set する停止入力 |
| shutdown operation | [`Supervisor.shutdown()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1643) | `_shutdown.set()` を維持 |
| serve loop 停止判定 | [`while not self._shutdown.is_set()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1613) | shutdown 後の再評価を同期で実証 |
| serve loop wake 根拠 | [`select(..., 0.25)`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1615) | exact 0.25 は固定せず、「有限 poll」を維持 |
| durable run state/reason | [`StatusResponse.state/reason`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/schema.py:206) | `COMPLETED` 期待を変更しない |
| durable side-effect event | [`side_effect_prepared/observed`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/ledger.py:56) | T-136 の期待集合を変更しない |
| test-owned 同期 | 新規 `roundtrip_selected`、`loop_parked`、`release_loop`、`serve_finished` | WAL event や `_shutdown` と呼び分ける |
| serve thread state | [`thread.is_alive()` と `serve_failures`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1193) | cleanup と例外回収の最終確認 |

T-136 の `ResourceLimits.per_wave_timeout_s/total_timeout_s` は [`ResourceLimits`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/schema.py:158)、テスト側の通常値は [`_profile()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:218) と [`_request()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:240) にあります。これらと `exchange(..., timeout_s=60)` は変更対象外です。

## 実装計画

変更対象は [`orchestrator/tests/test_dev_waves_integration.py:1193`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1193) から始まる既存 node 内だけとします。

1. `daemon_mod.select.select` の実関数を保存し、`mock.patch.object` で node 内だけ観測 wrapper を置く。

2. wrapper は roundtrip 前は実 `select` へ委譲する。timeout が `None` なら、既知の M-D 型停止退行として即例外にする。値の短縮・延長自体は判定根拠にしない。

3. listening socket が ready になった実 roundtrip を観測したら `roundtrip_selected=True` とする。その次の `select` 呼び出しで `loop_parked=True` を通知し、test-owned `release_loop` を条件変数で待つ。

4. `_serve()` の既存 `except BaseException` と `serve_failures.append()` を維持し、`finally` で `serve_finished=True` を通知する。主 thread は「`loop_parked` または `serve_finished`」を待つため、bind/serve 例外を待ち続けない。

5. [`daemon=True`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1208) は維持し、start 前に `assert thread.daemon is True` を追加する。

6. long-path 長検査、独立 capability skip、実 AF_UNIX exchange、`response.ok`、`RunState.COMPLETED` はそのまま通す。probe と正負 control は [`_sandbox_permits_short_alias_bind()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1093) から変更しない。

7. run terminal 後、serve thread が `loop_parked` へ到達済みであることを確認してから `supervisor.shutdown()` を呼ぶ。直後に production `_shutdown.is_set()` を保存し、`release_loop` を通知する。

8. `thread.join()` は timeout なしで行う。ただし、その前に thread は test-owned gate 内へ捕捉済みである。正常実装なら次の loop predicate で終了し、停止条件を無視する実装なら wrapper の二度目の post-release 呼び出しが sentinel 例外を投げて thread を終了させる。

9. join 後に、production shutdown Event が set、post-release `select` が一度だけ、thread 非生存、`serve_failures == []` を順に assert する。`join(120)` と `is_alive()` による wall-clock 判定は削除する。

production の [`tools/dev_waves/daemon.py`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1586)、protocol、schema は編集しません。したがって public request、state/reason、side-effect、製品 daemon の受理集合は不変です。

## 決定的な分類

| 観測 | 判定 |
|---|---|
| shutdown 前に `loop_parked`、Event set、release 後に thread 正常終了 | PASS |
| roundtrip 後、再反復せず `serve_finished` | one-shot/早期 exit 退行として赤 |
| `_shutdown.is_set()` が False | shutdown 停止入力欠落として赤 |
| release 後に wrapper が再度呼ばれる | loop が停止条件を無視した確定退行として sentinel 赤 |
| `select` timeout が `None` | periodic recheck 消失として即赤 |
| serve 内例外 | `serve_failures` 経由で主 thread の赤 |
| thread が一度も再 scheduling されない | pytest の機能赤にはしない。外部 ceiling の hang/infra timeout。緑にもならない |

最後の scheduler starvation を有限時間で機能退行と区別することは不可能です。新方式は、それを誤って assertion failure にせず、既知の確定退行は test-owned trap で終了させる設計です。

## P1/P2 の攻撃結果

- P1「production wakeup API なしで閉じる」: **支持**。既存の `daemon_mod` import、`mock.patch.object`、test-owned 条件変数で閉じます。production seam は不要です。

- P2「real roundtrip と shutdown-contract node を分離」: **不採用を推奨**。分離すると real node 自身の cleanup に、固定 join・daemon 放置による偽緑・同じ同期 helper のいずれかが再び必要です。同じ helper を両 node へ入れるなら重複であり、検出力は増えません。単一 node なら「実 long-path request を処理した同じ live loop が shutdown で止まった」ことまで束縛できます。

段3で process-wide mock が許容不能と反証された場合の最小代案だけは、[`SupervisorDependencies`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:289) に既定値 `select.select` の注入 seam を1 field追加し、serve loop の一箇所だけを差し替える案です。wakeup API 追加より小さいものの、現時点では不要です。

## Mutation 事前登録

現行 anchor は静的に一意であることを確認済みです。

| ID | 変異 | 変更前 / 修正後の期待 |
|---|---|---|
| T145-M1 | [`conn.shutdown()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1638) 後に loop を早期終了 | 変更前 SURVIVE、修正後は再反復未観測で KILL。純増検出力の主証拠 |
| T145-M2 | [`shutdown()` の `_shutdown.set()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1644) 削除 | 両版赤だが、修正後は wall-clock 非依存の Event assertion |
| T145-M3 | [`while not ...is_set()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1613) を `while True` | 修正後は二度目の post-release select sentinel で即 KILL |
| T145-M4 | [`select` timeout](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1615) を `None` | 有限 poll assertion で KILL。daemon thread の hang に依存しない |
| T145-M5 | test の `daemon=True` を `False` | start 前の daemon assertion で KILL。変更前は正常系で SURVIVE |
| PRES-MB | [`socket_path_alias`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/protocol.py:128) を実 long path に戻す | long-path node が SKIP でなく FAIL |
| PRES-ME1/E2 | capability probe を常時 False / True | probe 正例 node がそれぞれ KILL。既存 skip 契約を維持 |

T-136 preservation control も、PM1 timeout reason、PM2 deadline guard、PM3 log-limit reason、PM4 residual process state を既存台帳どおり再登録します。対象 anchor は [`worker.py:552`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/worker.py:552) と [`daemon.py:1011`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1011) です。これらは T-145 の新規検出力には数えず、同一 node・同一 state/reason 署名の preservation control と記録します。

test-only wave なので、T145-M1〜M5 は変更前 HEAD と修正後テストの双方へ適用し、`rc`、FAILED node、skip 数、外部 timeout の有無を記録します。

## 受入コマンド

repo root・ログインノードで、順に実施します。

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_dev_waves_integration.py::test_socket_roundtrip_works_beyond_108_byte_repository_path \
  orchestrator/tests/test_dev_waves_integration.py::test_short_alias_bind_probe_separates_capability_loss_from_regression \
  orchestrator/tests/test_dev_waves_isolation_contract.py::test_every_node_that_touches_process_external_resources_stays_serialised \
  -rf
```

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_dev_waves_integration.py::test_child_failure_injection_stops_before_next_wave \
  orchestrator/tests/test_dev_waves_integration.py::test_expired_deadline_prevents_next_real_artifact_side_effect \
  orchestrator/tests/test_dev_waves_integration.py::test_shutdown_running_child_uses_same_prepared_signal_path \
  -rf
```

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_dev_waves_integration.py \
  orchestrator/tests/test_dev_waves_isolation_contract.py \
  -rf
```

```bash
python3 tools/run_tests.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
git diff --check
```

commit 後に:

```bash
python3 tools/check_ai_provenance.py
```

Mutation は各変異を独立 subprocess・外部 ceiling 付きで実施し、tracked source の復元比較後に次へ進めます。性能値や wall 比較は成果物にしません。

## 記録対象とリスク

- [`docs/phase3.md:517`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/docs/phase3.md:517) の完了記録へ T-145 を追加。
- [`docs/worklog.md:1095`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/docs/worklog.md:1095) の次回エントリで T-145 を完了化。
- wave 専用 insight に mutation matrix、受入結果、非実施/timeout を実値で記録する。事前に結果欄を埋めない。

主なリスクは、`select.select` の patch が同一 pytest worker 内で process-wide になることです。ただし対象 node は既に `dev-waves-runtime` group で、meta-test は [`daemon_mod` を runtime 語彙として追跡](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_isolation_contract.py:35)しています。patch context は必ず serve thread の終了まで保持し、daemon thread を残したまま復元しません。

## 総括

- **GO**
- **推奨 scope:** `orchestrator/tests/test_dev_waves_integration.py` の既存 long-path node 1件だけを実装変更。production 0 byte。phase/worklog/insight は記録段で同期。
- **P1:** 採用。test-owned 同期で閉じる。
- **P2:** 不採用。node 分割は real node の cleanup 根拠を弱める。
- **残る裁定点:** process-wide `select` mock を許容するかだけ。拒否時は `SupervisorDependencies` への単一注入 seam が最小代案。