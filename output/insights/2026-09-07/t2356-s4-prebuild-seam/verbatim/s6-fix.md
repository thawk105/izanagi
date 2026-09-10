## 直した 4 件

1. [test_p3_s4_loop.py:7998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7998)
   - `evaluate_call_count` を追加し、production `evaluate` が 1 回以上呼ばれたことを [同:8026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:8026) で要求。

2. [test_p3_s4_loop.py:7795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7795)
   - 恒真な `assert len(volatile_nontransport_fields) == 3` を削除。
   - 揮発 field を変更しても loader の 5 値が変わらない実挙動の検査は維持。

3. [test_p3_s4_loop.py:7902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7902)
   - 実行に渡されていない `tmp_path` fixture と空 directory assert を削除。
   - authorization、layout、source identity の明示 mock が未到達である検査を維持。

4. [test_p3_s4_loop_job_contract.py:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:498)
   - `source.count(fragment) <= 1` を `== 1` に変更。
   - M1〜M4を含む全 parameter case で、実在する一意な fragment を変異したことを要求。

## 直す前と後で捕まる欠陥

1. 以前は全 genome が skip されても空の `observed` が disjoint 判定を通過。現在は呼出し回数 assert が赤化。
   - `default-loop-all-skipped-mutant: DIRECT_CALL_PASS (raised AssertionError)`

2. literal の要素数 assert は production の変異を一切検出しませんでした。現在は実挙動の比較だけが証人となり、loader が `pbs_jobid` を transport へ漏らす変異を検出。
   - `receipt-volatile-payload-mutant: DIRECT_CALL_PASS (raised AssertionError)`

3. 以前の空 directory assert は別 root への副作用を検出不能でした。現在はその誤った主張を除き、gate より先に authorization へ到達する変異を明示 mock が検出。
   - 両 parameter case とも `DIRECT_CALL_PASS (raised AssertionError: side effect reached)`

4. 以前は fragment が最初から 0 件でも、欠落エラーが期待 label と一致して緑になりました。現在は変異前の `count == 1` で即座に赤化。
   - M1〜M4すべて `DIRECT_CALL_PASS (raised AssertionError)`
   - `DID NOT RAISE` は 0 件。

## 波及可能性

- loop spy の変更は対象 test 内だけです。
- receipt loader test は不要な assert の削除のみで、fixture・helperへの波及はありません。
- gate test は `tmp_path` fixture を要求しなくなり、2 parameter caseへ適用されます。
- fragment helper の強化は全13 parameter caseへ波及します。全件を直接呼び出し、すべて `DIRECT_CALL_PASS` を確認しました。

## 実走した範囲・できなかった範囲

- 対象 pytest node を `tools/run_tests.py` で起動しましたが、`qstat -Q preflight rc=1`、`child_started=false`、runner `rc=16` でした。pytest は未実走です。
- fixture 代替による直接呼出し:
  - receipt loader: `DIRECT_CALL_PASS`
  - run_campaign gate 2 case: `DIRECT_CALL_PASS`
  - default loop spy: `DIRECT_CALL_PASS`
  - fragment helper 全13 case: `DIRECT_CALL_PASS`
- 上記4種類の一時変異はすべて期待どおり赤化し、作業ツリー上の production fileは変更していません。
- `git diff --check` は成功しました。
- 全 suite、関連 suite、docs checker は未実走です。

## 総括

指定された test 2ファイルだけに4件を実装しました。production、docsには触れず、`git add`／`git commit`／`git merge`も実行していません。状態は「修正実装済み・pytest未実走・直接呼出しと赤化確認済み」です。