## 総括

**静的レビューとして採用可。新規 must-fix 0件、nit 0件。** working diff は PBS 1行・既存 test module 66行の追加で、D1936項30の限定修正と一致します。pytest・M1・全PBS実機実走は未実施で、実測の KILLED／closed は主張しません。

- **real：修正前の import 前検査欠落。** [PBS:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54) の既存配列へ条件関門が追加され、dirty 拒否→blob/runtime 照合→probe 起動→条件関門 import の順序になっています。先行する Python 版確認は条件関門を import しません。成果物影響は、receipt が束縛対象として扱う条件関門について、実行後だった dirty 検査を import 前にも適用することです。
- **F28：全体出口だけでは mask される懸念は real、今回の局所テストへの指摘は refuted。** 抽出範囲は配列から dirty 拒否まで。前段の環境・hostname・HEAD 検査、後段の blob/runtime・Python 検査は入りません。内側は実 Git status と既存拒否だけで、M1後に条件関門を別経路で拒否する検査はありません。
- **F820：fixture／構造 assert による偽killは refuted。** fixture の clean 確認後に対象だけを変更し、fixture PBS は置換しません。実行する断片は実 PBS から読みます。M1 は抽出 anchor と順序 anchor を変えず、[結果 assert:1568](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/orchestrator/tests/test_t316_sandbox_probe.py:1568) で期待 `(3, "")` に対して `(0, "T2543_AFTER_DIRTY\n")` となる構造です。
- **独立性・既存 consumer：** 対象5 path は独立 literal。既存4 path の staged/unstaged 拒否8ケース、条件関門2ケース、clean・対象外dirtyの正例4ケースを維持します。Python の束縛集合、既存 runtime spool テスト、admission registry と hook期待値に不整合は見当たりません。追加15 node の duration ledger 未登録は未知node契約で扱えますが、収集・coverage の実測結果はありません。

M1 の**期待失敗 node 完全集合（静的予測・未実測）**は次の2件です。他の12挙動nodeと順序nodeは、この1行除去では変化しません。

```text
orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_shell_dirty_gate[condition-unstaged]
orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_shell_dirty_gate[condition-staged]
```

採否は**実装・テスト設計を採用**。実測受入では、この2件だけが rc/marker の挙動 assert で失敗することが未確認事項として残ります。