## 選んだ機構と根拠

probe 内に `_s6_requested_checkout` を追加しました。`TMPDIR` が未設定または `/tmp` 配下なら、実在する `scratch.parent` に checkout を作ります。

生成先は `scratch.parent/izanagi_wt_*/wt`。scratch の兄弟なので writable bind に覆われません。checkout 生成時だけ `TMPDIR` を変更し、例外時も元へ戻します。`/scr` の固定値は追加していません。

## 他の呼び手への影響

- `patchharness` と他 driver の配置方針は変更していません。
- 本番の変更対象は `observe_s6` の checkout 配置です。
- 共有 fixture 本体は変更なし。観測 helper に任意引数を追加し、既存呼出しの既定動作を維持しました。
- execution-binding 関連検査は今回の全体実走に含まれます。
- 前回報告にある外部 consumer（hooks／perf closure／real-repo inventory／duration 検査）は未実走です。特に収集件数は161から165へ増えます。

## 実装した変更

編集したのは次の2ファイルです。

- [probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py:1985)：配置用 context manager と呼出し。
- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/tests/test_t316_sandbox_probe.py:2076)：2関数・4 node を追加。

既存69テスト関数は AST 比較で変更・削除ゼロです。scratch 内拒否、schema、condition gate は維持。docs 編集・commit・push・リポジトリの Git 管理操作は行っていません。

## 追加した正例・負例

両方に `unset` と `/tmp` のケースを追加しました。

- **負例**：実際に生成・patch 適用された木を観測し、`/tmp` 外・scratch 外・readonly roots 登録・終了後の撤去を検査。
- **正例**：実 checkout／gate／両 build を通り、S6 成功・trace-disabled を検査。

既存 scratch 内拒否も独立して通過しました。

## 実走した nodeid と結果

実行：`PYTHONPATH=. python3 orchestrator/tests/test_t316_sandbox_probe.py`

範囲：ファイル全体 **165 node、162 passed／3 failed、rc=1**。

共通 prefix：`orchestrator/tests/test_t316_sandbox_probe.py::`

| nodeid | 結果 |
|---|---|
| `test_s6_requested_checkout_avoids_masked_tmp[unset]` | PASS |
| `test_s6_requested_checkout_avoids_masked_tmp[/tmp]` | PASS |
| `test_s6_requested_checkout_inside_scratch_is_rejected_and_removed` | PASS |
| `test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir[unset]` | 環境制約・未検証 |
| `test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir[/tmp]` | 環境制約・未検証 |
| `test_s6_live_requested_gate_and_both_build_roots_match` | 環境制約・未検証 |

失敗3 node は outside 成功後、inside の `gflags-configure` で同じエラーです。

```text
bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted
```

[実走ログ](/tmp/t2607-s6-placement-tests.log)

## 未実走・未解決

計算ノードでの inside build 完遂と本番 CCBench の S6 終端到達は、**実装済み・未実走**です。上記3 node は環境制約として分類し、成功条件は変更していません。

## 総括

本番の配置修正と実パス検査は実装済みです。配置検査は通過しましたが、S6 終端到達は計算ノードでの再走待ちであり、**closed とは申告しません**。