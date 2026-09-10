## 総括

**最小局所差分は成立します。計画を阻む欠陥は見つかりませんでした。** production 1ファイルと既存testへの追加で進められます。静的確認のみで、編集・pytest・変異実行はしていません。

- **P1の保存先は妥当です。** [受領証検証](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2514-a1-detail/orchestrator/campaign/paper_story_a1_paired.py:3482) がworkload別rootsを返し、[6840行](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2514-a1-detail/orchestrator/campaign/paper_story_a1_paired.py:6840) でCLIとの一致確認後に採用します。6935行の関門呼び出しへ、その `raw_root` を渡せます。保存helperへの新しい環境変数や検証gateは不要です。

- **全arm保存が必要です。** [admissionの定義](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2514-a1-detail/orchestrator/campaign/condition_meaning_gate.py:681) はrecordへの参照だけを持ち、detailを内包しません。拒否本文用の非green抽出を保存対象へ流用せず、両リスト全件とadmissionを保存する計画が正しいです。「全5件」は2値のfixtureに限り、実装では件数を固定しません。

- **D1912の局所適用で足ります。** [既存helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2514-a1-detail/orchestrator/campaign/p3_s4_loop.py:394) の一時file、file fsync、replace、directory fsyncを参照できます。原子性は各file単位です。directory fsync失敗時は完全な最終fileが既に存在し得るため、失敗テストで「必ず最終file不在」とは期待しません。

親へ返す修正・検証上の注意は次の3点です。

1. [briefのアンカー](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2514-a1-detail/handoff.md:21) にある `_v3_workload_paths` は存在しません。`_v3_job_roots:2485` に訂正し、関門6704行・production呼び出し6935行も明記してください。
2. 保存先引数の省略を許すため、直接関門を呼ぶテストだけではproductionの渡し忘れを検出できません。計画の配線テストは省略できません。
3. 変異で `could not run` に落ち、保存分岐へ到達しなかった場合は、保存要件の検出成功とは扱えません。保存欠落と拒否から受理への変化も別の結果です。`BaseException` 伝播はD1912どおり正常な挙動です。

所有分割は整合しています。`p3_s4_loop.py` とT-2581所有testは参照のみで足ります。今回確認したのはF855のdetail消失を防ぐ保存経路です。F580の依存供給不備やsource問題の解消、次回attemptの成功、実環境での耐久性まで確認済みとは一般化できません。