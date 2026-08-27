[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_certification.py:1463) の stub のみ修正しました。

変更前: 生の `cfg` で campaign identity を計算し、必須 admission policy がなく失敗。  
変更後: `kwargs["build_context"].policy` を `ident.bind_admission_policy()` で束縛してから identity を計算。layout assert は維持。

`git diff --check` は成功。実装済み・未実走です。親で次の nodeid の再実走が必要です。

`orchestrator/tests/test_paper_story_a2_certification.py::test_official_run_observes_and_passes_current_toolchain_manifest`

## 総括

赤 1 件の原因を正例 stub 側で修正しました。  
production、既存 assert、受理集合は変更していません。  
最大の残存リスクは親による実走が未完了である点です。