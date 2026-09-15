## 赤の原因と選んだ直し方

**(b) fixture 側の配置修正を選択しました。**

`SandboxProfile.argv` は `/tmp` を隠してから各 root を bind します。fixture では requested だけでなく依存 source・cache・scratch も `/tmp` 配下だったため、実 build 用 fixture 全体を作業 root 下の一時領域へ移しました。requested は引き続き scratch 外です。

変更前の wrong HEAD／dirty 拒否、scratch 内 requested 拒否、条件関門の受理集合は維持しています。

## 変異 M6 の帰属

既存 wrong-head ケースには harness の拒否による mask がありました。

新規検査では、実 identity 検査が wrong HEAD を観測した直後に木を正しい pin へ戻し、実 `assert_pinned_clean` の成功を確認します。それでも probe が `source-identity` で拒否することを検証しました。

拒否を無効化した場合は、最初の `apply_patch` 呼出し入口で assertion が失敗する構造です。後続 gate／build に帰属しません。**変異注入による KILL は未実走です。**

## 実装した変更

編集は [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/tests/test_t316_sandbox_probe.py:1730) のみです。

- 一時領域を管理・撤去する fixture を追加。
- M6 の独立した拒否経路の検査を追加。
- inside 失敗時の診断に build 内訳を表示。成功 assertion は維持。

docs、production コード、schema は未変更。commit／push／Git 管理状態の操作は行っていません。

## 実走した nodeid と結果

自走 harness：`PYTHONPATH=. python3 orchestrator/tests/test_t316_sandbox_probe.py`

- ファイル全体：**160 passed、1 failed**。診断・M6 境界 assertion の最終追記前。
- 最終版で次の2 node を選択して再走：**1 passed、1 failed、159 deselected**。

共通 prefix：`orchestrator/tests/test_t316_sandbox_probe.py::`

| node | 結果 |
|---|---|
| `test_s6_requested_wrong_head_rejected_without_harness_mask` | PASS |
| `test_s6_live_requested_gate_and_both_build_roots_match` | FAIL。outside 成功、inside 失敗 |

inside は `gflags-configure` で次のエラーでした。

```text
bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted
```

`tools/run_tests.py` は `qstat -Q preflight rc=1`、終了コード16、`child_started=false` でした。

## 未実走・未解決

- 配置修正の計算ノード検証は **実装済み・未実走**。現在の sandbox では bind 成立まで確認できていません。
- 本番 `TMPDIR=/tmp` の配置制約は残ります。
- M6 変異走行、実 CCBench の受入走、consumer meta-test は未実走です。

## 追加テスト件数の内訳

- 段5：新規 **6関数・8 node**。
- 段5：既存 dirty parametrization に **4ケース**追加。
- 今回：新規 **1関数・1 node**。
- 合計：**7関数・13ケース追加**。関数集合は **62 → 68 → 69、削除ゼロ**。

## 総括

M6 専用検査は実走成功。配置修正は **closed と申告しません**。

静的な波及先は、同ファイルの実 S6 fixture を使う5関数・7 node と、その全体収集です。所有外 production caller・共有 `patchharness`・execution-binding fixture への変更はありません。外部 consumer の hooks／perf closure／real-repo inventory と、collection 件数に依存する duration 検査は未検証です。