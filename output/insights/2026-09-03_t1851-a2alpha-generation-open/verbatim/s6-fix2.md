## 対応結果

| Gap | 状態 | 対応 |
|---|---|---|
| G1 | partial（実装済み・未実走） | marker 専用 atomic update の hook を実 OS lock で検査 |
| G2 | partial（実装済み・未実走） | v2 ordinal 1 の exact 拒否と ordinal 0 の正例を同一 node に追加 |

変更は [test_s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-a2alpha-fix2/orchestrator/tests/test_s8b_attempt_registry.py:2709) のみです。production・docs は変更していません。

## 新設した test

- `orchestrator/tests/test_s8b_attempt_registry.py::test_atomic_update_with_consumption_marker_hook_precedes_root_lock`
- `orchestrator/tests/test_s8b_attempt_registry.py::test_v2_resume_rejects_recovery_ordinal_and_accepts_zero`

いずれも既存の大型複合 node とは別の独立 node です。

## 変異を検出する理由

G1 は `_atomic_update_with_consumption_marker()` を直接呼び、hook 内から admission の `ledger.lock` に `LOCK_EX | LOCK_NB` を試みます。

- 現行実装では lock 取得に成功し、`hook_saw_unlocked == [True]`。
- hook を root lock 内へ移すと非 blocking lock が失敗して append されず、最終 assertion `assert hook_saw_unlocked == [True]` が `[] != [True]` で破れます。
- 2回以上呼ばれてもリスト要素数が増え、同じ assertion が破れます。

G2 は実 core で ordinal 0 の recovery 後に ordinal 1 の durable start/seal を作り、`resume_attempt()` が次の exact 署名で拒否することを検査します。

`[s8b-attempt-registry-consume] v2 resume recovery ordinal is not capability-backed`

gate を削除すると次の start-only gateへ進み、`[s8b-attempt-registry-resume] v2 start-only resume is not marker-atomic` となるため、`pytest.raises(..., match=exact_signature)` の assertion が破れます。同じ test の前半では、ordinal 0 の実 capability-backed classified resume が `ClassifiedAttempt` として通ることも確認します。

## 検査結果

焦点走として上記2 nodeidを3回 runner に指定しましたが、すべて次の infra 失敗でした。

- runner rc: `16`
- `child_started=false`
- 理由: `qstat -Q preflight rc=1`
- 実走した pytest nodeid: なし
- pytest の緑・赤: 観測なし

`queue-wait-timeout` ではなかったため、指定された timeout override による再投入条件には該当しませんでした。

静的検査は以下が成功しています。

- test module の AST parse
- test module importと新設関数の存在確認
- `git diff --check`
- 変更ファイルが test file 1件だけであることの確認

## 変更量

- 追加: 117 LOC
- 削除: 3 LOC
- changed LOC: 120
- `git add`、commit、push、branch・remote 操作: 未実施

## 総括

- G1: `partial（実装済み・未実走）`
- G2: `partial（実装済み・未実走）`
- 新設 nodeid:
  - `test_atomic_update_with_consumption_marker_hook_precedes_root_lock`
  - `test_v2_resume_rejects_recovery_ordinal_and_accepts_zero`
- G1 変異: hook が lock 内なら `hook_saw_unlocked` が空になり、`== [True]` assertion が破れる。
- G2 変異: ordinal gate 削除後は別署名へ進み、exact `pytest.raises` assertion が破れる。
- 実走した pytest nodeid: なし。3回とも test child 起動前の infra rc=16。
- changed LOC: 120（117追加、3削除）。
- 読めなかった資料: なし。指定4資料を順番どおり全文読了。
- 確かめられなかった事実: 新設2 node の実行結果、既存 test file 回帰、consumer 閉包、mutation harness。