## 総括

**採用相当。新規の real な must-fix／nit はありません。** working diff は PBS 1行追加＋既存テストモジュール66行追加で、D1936項30の限定修正と一致します。静的レビューのみで、pytest・M1・全PBS実機実走は未実施です。

- **正しさ・scope：** `BOUND_PATHS` はトップレベルで定義され、同じ shell の dirty 検査と後続 blob 照合に展開されます。条件関門単独の staged／unstaged 変更は probe 起動前に `exit 3` となる構造です。Python の条件関門 import は `_execution_binding` より先なので、元の欠落は **real**、今回の追加は適切です。先行する Python 版確認は残るため、「全Python起動前」とは表現できません。
- **受理集合：** 既存4 pathの拒否は維持されます。clean と対象外 dirty は path 限定の検査を通過する構造です。対象外正例は untracked／staged の新規ファイルを扱っています。無条件拒否やリポジトリ全体への拒否拡大はありません。
- **成果物影響：** receipt が束縛対象として記録する条件関門について、import 後まで dirty 検査が遅れる欠落を埋めます。同じ配列を使う既存 blob 照合にも追加対象が入り、汎用機構の新設はありません。

M1 の mask を前後・内側で再確認しました。

- **前：** fixture は独立 literal から commit・clean 確認まで済ませ、その後に対象だけを変更します。実PBSの1行除去は fixture に影響せず、「fixture が先に落ちる」は **refuted** です。
- **後：** 抽出は dirty 判定で終わるため、実PBS前段の環境検査、後段の blob／runtime／Python検査は観測を隠しません。全PBSの最終拒否だけでは mask される懸念自体は **real** で、この局所テストが対応しています。
- **内側：** M1 は抽出 anchor・順序 assert を変えません。残る4 path が clean なら Git status は空となり、`rc=0` と marker 到達を返すため、[挙動 assert](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/orchestrator/tests/test_t316_sandbox_probe.py:1568) が失敗する想定です。Git／timeout の異常も `exit 3` に合流しますが、clean 正例が恒常的な実行障害による偽の拒否成功を検出します。

**M1 の期待失敗 node 完全集合（未実測）は次の2件です。**

```text
orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_shell_dirty_gate[condition-unstaged]
orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_shell_dirty_gate[condition-staged]
```

既存4 path、clean、対象外dirty、順序契約、既存runtime-spoolテストには、M1による追加失敗要因を認めません。採用判断は静的整合性に基づき、実測KILLEDや受入完了は主張しません。