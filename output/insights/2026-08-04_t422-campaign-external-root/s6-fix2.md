指定された FX-1〜FX-3 を実装しました。pytest・変異・受入試験は未実走のため、動的な緑は主張しません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| new-1 / FX-1 | closed | layout 固有の materialization admission を追加。official は no-op、exploration のみ container を拒否。WAL 4 経路を duck-typed policy 呼び出しへ変更 |
| new-2 / FX-2 | closed | resolver に `legacy_base` を追加し、8c の env 判定を lock transaction 内へ統合。pin 後の env 削除を reset なしで拒否するテストを追加 |
| A-5 partial / FX-3 | closed | `repair_truncated_tail` と `ensure_exploration_namespace` の残存 materialization 経路を gate |
| new-3 | 対象外 | 親所有の変異 matrix には未着手 |
| regressed | 静的にはなし | 動的回帰は未実測 |

### 差分要約

本巡で編集したのは所有範囲内の4ファイルです。

- [layout.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:201)
  - `CampaignLayout._admit_materialization()` は no-op
  - `ExplorationCampaignLayout._admit_materialization()` は container gate
  - resolver に keyword-only `legacy_base`
  - namespace helper の作成前 gate
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:310)
  - append、repair、write_lock、acquire_lock_atomic の4経路を `getattr(..., lambda: None)()` に統一
- [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1758)
  - `--run-root` 省略時は常に resolver を呼び、`ROOT/output` を `legacy_base` として渡す
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3774)
  - reset なし pin/env削除負例
  - official layout の4 materializer正例
  - exploration repair負例
  - namespace helper直呼び負例
  - legacy defaultの引数・文字列互換検査を強化

### 受理・拒否挙動の変化

- worktree container 内の official layout は WAL、両 lock、tail repair を受理します。
- exploration layout は従来どおり append・両 lockを拒否し、repairも拒否するようになりました。
- exploration namespace helperの直呼びも、directory/marker作成前に拒否します。
- admission methodを持たない疑似 layout は従来どおり受理されます。
- env未設定・pinなしでは、`legacy_base` があればそれを返し、なければ従来の `repo_output_root()` を返します。
- env由来rootをpinした後のenv削除は、legacy rootへfallbackせず `ValueError` になります。
- 8cのenv未設定時rootは従来の `ROOT/output/exploration/autonomous-trials/<trial-id>` と同一です。
- 明示 `--run-root` の挙動は不変です。

### 所有外への波及可能性

- official sweep・oracleなどのWAL callerは、worktree内での過剰拒否が解除されます。
- `ident.ensure_resumable_wal()` 経由のexploration repairにも新しいpolicy gateが適用されます。
- 8cのnamespace作成は公開helper側でもcontainerを拒否します。
- resolverの既存callerは、`legacy_base` が任意引数なので互換性を維持します。
- docs、hooks、`tools/dev_wave_land.py`、`durable_root.py`、spec/matrixは編集していません。既存の親由来docs・テスト差分は保持しています。
- git add/commitは実施せず、`git diff --cached` は空です。

### 静的検査

すべて独立実行で rc=0:

- `python3 -m py_compile`（所有6ファイル）
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

`pegasus02`ログインノードかつ明示禁止のため、pytest、`run_tests.py`、変異検査は実行していません。

## 総括

対象3所見はコードと追加テスト上で closed、regressed は静的には0件です。所有・禁止境界を維持し、必須静的検査は通過しました。動的合否は未判定であり、親による計算ノード上の関連pytest・変異・受入検査が必要です。