## 実装した内容

- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-b/tools/pegasus/p3_s4_loop_pegasus.sh:54) に K2 env の早期検査を追加。
  - manifest と coder role は all-or-none・非空。
  - K2 時は proposal path 必須。
  - 任意 2 宣言は設定時のみ非空検査・転送。
  - repository path 解決・`trap` より前に rc=2 で拒否。
- K2 argv は [proposal 分岐だけ](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-b/tools/pegasus/p3_s4_loop_pegasus.sh:585)へ転送。fixture 分岐は変更なし。
- [README §7](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-b/tools/pegasus/README.md:341) と単一行 qsub fence を更新。
- `orchestrator/campaign/` は変更していない。

## 新設したテストと実走結果

対象ファイル全体:

```text
PYTHONPATH=. python3 orchestrator/tests/test_p3_s4_loop_job_contract.py
80 passed in 4.08s
```

変異対応 nodeid を個別実走し、各 `1 passed, 79 deselected`:

- M4: `test_set_empty_manifest_alone_is_refused_by_actual_job_body`
- M5: `test_complete_k2_pair_without_proposal_is_refused_by_actual_job_body`
- M6: `test_complete_k2_environment_reaches_actual_job_driver_argv`

加えて、任意宣言の空拒否・省略時非転送・proposal-only 展開を新設。逐語 pin、段順、refusal、registry、README fence の meta-test 範囲も `5 passed, 75 deselected`。`git diff --check` も通過した。

## 受理・拒否の含意

拒否できるのは、K2 必須対の片側欠落・空値、設定済み任意宣言の空値、および K2 走行の proposal path 欠落です。

拒否できないのは、role・classification・de novo の値域、manifest 内容、proposal schema の不正であり、これらは driver の CLI・parser・K2 consumerへ委ねています。

通る正例は manifest、coder role、proposal path が非空の走行です。任意宣言を省けば driver へは必須 2 flag だけ、設定すれば対応する flag も渡ります。

## 波及可能性

- K2 の qsub caller/run card は必須対と proposal path の供給が必要。
- 非 K2 proposal caller と共有 fixture `--value` 経路は既存 argv のまま。
- consumer 側の `p3_s4_loop.py` とそのテストには新しい argv が到達するが、値域判定の所有権は移していない。
- shared fixture、policy、prebuild receipt schema は未変更。

## 総括

単位 B の env-to-argv 配線と契約防壁は実装・実走済みです。Pegasus 本投入や評価成立までは実施・主張していません。commit も作成していません。