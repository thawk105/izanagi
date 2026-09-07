## 実装した内容

- [t1998_stock_inline_pair.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-a/orchestrator/campaign/t1998_stock_inline_pair.py)
  - balanced の baseline／fixed-5 を immutable 定数化。
  - 共通 identity と arm 固有 identity を別 dataclass 化。
  - certified admission、WAL、lock、reservation、result、persisted receipt を検証。
  - 全拒否に `field / expected / actual / arm` を保持。
  - 不安定 arm は `inconclusive`。argmax は不使用。
  - gitlink prefix、job-body 限定 provenance、診断 marker 単独検査の限界を戻り値へ投影。
- [test_t1998_stock_inline_pair.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-a/orchestrator/tests/test_t1998_stock_inline_pair.py)
  - 実 admission／receipt 発行経路を使う自己整合 fixture と正負テストを追加。
  - `_run()` と `__main__` harness を追加。
- [test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-a/orchestrator/tests/test_official_perf_closure.py)
  - recorded performance evidence consumer として集合へ追加登録。

## 実走した検査

実走 nodeid は 0 件です。

- `python3 tools/run_tests.py orchestrator/tests/test_t1998_stock_inline_pair.py`
  - 対象範囲: 新規 test file 全体。
  - `qstat -Q` preflight rc=1、dispatcher rc=16。テスト本体へ未到達。
  - 実装済み・未実走。
- `python3 tools/run_tests.py --collect-only -q ...`
  - 対象範囲: 新規 test file と official perf closure 全体。
  - 同じ dispatcher rc=16 により collection 前に停止。
  - 実装済み・未実走。
- 実走済み静的検査:
  - 3 owned file の AST parse／import。
  - `git diff --check`。
  - 禁止 import、argmax、`admit_replay_evidence`、prereg 実値 literal の不在。
  - official perf file 集合完全一致。
  - U+0300〜U+036F 不在。
  - 変更 path が owned 3 path と完全一致。

build、benchmark、性能測定は実行していません。

## 所有外への波及可能性

- production caller: 現時点では無し。official perf 登録簿だけが新 module を参照。
- 共有 fixture:
  - `orchestrator/tests/commit_receipt_support.py`
  - `orchestrator/tests/campaign_lock_test_support.py`
- 関連する既存 consumer test:
  - `test_artifact_admission.py`
  - `test_t1286_commit_receipt.py`
  - `test_campaign_lock_codec.py`
  - `test_campaign_lock_wal_consumers.py`
  - `test_a5_second_boot_job_contract.py`
- `test_campaign.py` の実行 caller inventory、S1 freeze/golden、Pegasus registry／hooks は変更不要で、静的にも新 caller はありません。

## 現行の受理・拒否挙動

- 受理:
  - complete な balanced producer root。
  - baseline と fixed-5 が各 1 attempt。
  - preregistered commit、gitlink、environment、job-body digest、arm 別 genome／source digest が一致。
  - trace-disabled performance build、対応 executable、toolchain、samples／median／fitness／result projection が一致。
  - 両 arm が stable の場合のみ `accepted`。
- inconclusive:
  - 片方でも `unstable=True` なら `unstable-arm`、ratio／improvement は `None`。
- 拒否:
  - sibling failure receipt、成果物欠損・不正、hash／identity 不一致。
  - source digest 未束縛、診断 noinline、trace-enabled build、executable／toolchain／値の不一致。
  - admission が拒否した receipt・variant。
- 40 桁 gitlink は exact、短縮形は prefix 比較です。短縮一致は full identity ではないことを返します。
- `pair-cardinality` と `producer-rejected-variant` は「単独では発火しない冗長 gate」と明記して残しています。

## 残した赤とその理由

テスト由来の赤は確認されていません。テスト本体が未実走のため、緑とも報告しません。

残件は runner infrastructure の rc=16 です。sandbox から local 予約台帳を安全に更新できず、dispatch 先の `qstat -Q` も rc=1 となるため、規律に従い直接 pytest へ迂回していません。

## 総括

第 3 部品 consumer、実経路テスト、official perf 登録を owned 3 path だけに実装しました。commit／git add、docs、ledger、A-5 関連 file、Pegasus 配下への変更はありません。