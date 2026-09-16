## 総括

**既存テストの期待値と B3 の要件が衝突するため、指示に従い編集前に停止しました。**

[test_pegasus_tools.py:487](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-f1-shell/orchestrator/tests/test_pegasus_tools.py:487) の `test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench` は、mocc にも次の解決式が **ちょうど 1 回存在すること**を要求しています。

```bash
THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"
```

B3 はこれを hydrate 出力の `.source_root` に接続する要件です。旧式を残して上書きすることで検査だけを通す変更は行っていません。「期待値が誤りだと判断したら実装を変えず、報告して止めよ」に従いました。

- **B1・B3・P-1:** 未修正。変更前後の受理・拒否に差はありません。
- **M1・M10・M11:** 期待 node は未新設。
- **M3:** 既存候補は `orchestrator/tests/test_pegasus_thirdparty_fetch.py::test_build_dependencies_reject_mutated_cache[shallow-shallow-verify-gflags]`。実 `tool.main` の verify 経路ですが、shallow 状態は `.git/shallow` の書込みで作っています。未実走。
- **実走 nodeid・rc:** なし。meta-test を含め未実走です。
- **削除した test 関数:** 0 件。
- **期待赤との突き合わせ:** 指定の evidence binding 赤は未実走。実際に観測した赤はありません。上記は静的に確認した契約衝突です。
- **波及候補:** silo の submit receipt／FetchContent 3 本の binding、凍結 evidence の shell binding、mocc の FetchContent source 参照、shell 起動箇所・行番号を扱う meta-test。共有 fixture は未変更です。
- **変更・commit:** なし。実 job 投入・計算ノード走行・clone・build も未実施です。

再開には、上記 node の **mocc 分岐を hydrate 出力の契約へ変更すること**を、既存期待値変更禁止の例外として明示する必要があります。