## 既存 caller の全数点検

静的 AST 点検の結果、signature 変更で壊れる既存 caller はありません。

- `loop.run_campaign`: production は16ファイル・20呼出しです。`b10_backoff_shape_sweep`、`backoff_extended_sweep`、`backoff_repro`、`backoff_sweep`、`demo`×2、`p2_2`、`p3_kickoff`×2、`p3_s4_loop`、`p3_s4_loop_sort`、`p3_s4_loop_trigger_gating`、`p3_s4_red`×2、`paper_story_a1_paired`×2、`paper_story_a2_certification`、`s6_sort_sweep`、`s8a_trigger_sweep`、`sanity_silo`。[固定 inventory](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_campaign.py:5338)とも一致します。
- `pipeline.evaluate`: production は5ファイル・5呼出しです。`loop`、`screening_driver`、`s1_direct_comparison`、`s8b_oracle_driver`、`qualification/t126_driver`。
- テスト内の直接呼出し式は `run_campaign` 49件、`evaluate` 61件です。前者は `test_campaign` 41件ほか6ファイル、後者は `test_campaign` 38件ほか11ファイルです。
- caller inventory の合成 fixture は8 positive、8 unresolved、13 regression、3 out-of-scope、6 final-fixの計38件です。[test_campaign.py:4798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_campaign.py:4798)

`run_campaign` の新引数は既存の `*` より後なので keyword-only、`evaluate` は旧末尾の `dependency_prefix` より後へ追加されており旧 positional の対応を動かしていません。[loop.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:240) [pipeline.py:1865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1865)

must-fix / nit ともになし。

## 既定経路の非変更

既定経路は実装上も維持されています。

- presence は base が `bool()`、source dir 3本と receipt が `is not None` です。[pipeline.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:894)
- 5値が揃った場合だけ `evaluate_options` に追加されます。[loop.py:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:562)
- `evaluate` から `_prepare_evaluation_core` への kwargs も非既定時だけ作られます。[pipeline.py:1937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1937)
- `common` / `build_v2` kwargs も同じ条件内だけで増えます。[pipeline.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1298)
- `buildcache.py` と WAL payload 構築部には差分がなく、未指定時は configure define、cache pre-image、WAL key 語彙へ新値が入りません。
- 新設 spy も `evaluate_options` と `build_v2` kwargs の両境界を対象にしています。[test_p3_s4_loop.py:7980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7980)

must-fix / nit ともになし。

## pin の同期漏れ

既存 pin を静的に照合し、赤化する同期漏れは見つかりませんでした。

- job contract の旧3 source path は `*-src` へ更新され、copy destination/base equality と両分岐の復帰変異も追加済みです。[test_p3_s4_loop_job_contract.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:249)
- `test_hooks.py` golden と `admission_registry.json` は content hash ではなく既存の `dispatch-required` 分類を pin しており、現状と一致します。[test_hooks.py:2745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_hooks.py:2745) [admission_registry.json:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/admission_registry.json:106)
- materializer は新 entrypoint を増やさず、既登録の `p3_s4_loop.main` を使っています。[materializer_admission.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/materializer_admission.py:132)
- 変更テスト2ファイルの top-level test 名は静的 AST 上254件・21件で重複なし。新規 handwritten `xdist_group` もありません。
- B4 closure は `p3_s4_loop.py` 全体を含むため、同ファイルの entry hash は旧 `54fddf…` から `73ffcd…` へ変わります。[p3_b4_closed_critic.py:632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_b4_closed_critic.py:632) ただし事前登録の projection hash 欄は現在「未記入」で、同期すべき既存 hash はありません。[phase3-b4-reflux-ablation-preregistration.md:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/docs/phase3-b4-reflux-ablation-preregistration.md:166)

must-fix / nit ともになし。

## job body の実行面

heredoc と comment を除く実行面を静的に追跡しました。

- stage-order test が列挙する17 markerは、source上で各1回かつ同順序です。[test_p3_s4_loop_job_contract.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:350)
- `cp -a` は `$thirdparty_root/$source_name` から新しい `$prebuild_source_root/${source_name}-src` へコピーします。[p3_s4_loop_pegasus.sh:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:328)
- 3 source変数、base、`source_root` receipt は同じ `$prebuild_source_root` に収束しています。[p3_s4_loop_pegasus.sh:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:353)
- fresh `config.h` 検査、receipt の `"x"` create-only、file/evidence-root `sync` は新 path と整合します。[p3_s4_loop_pegasus.sh:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:356)
- receipt option は proposal/fixture の各分岐に1回ずつあります。[p3_s4_loop_pegasus.sh:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:433)

このレビューでは `bash -n` を実行していません。must-fix / nit ともになし。

## 揮発値の焼き込み

新設22 parametrized caseと契約 mutation追加4 caseを確認しました。

絶対 path は `tmp_path.resolve()` から実行時に作り、`config_h_sha256` もfixture bytesから実行時に計算しています。[test_p3_s4_loop.py:7719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7719) `pbs_jobid="fixture-job"`、40/64 hex、attempt名は合成固定値で、working-tree hash・実時刻・実job id・host固有絶対pathの期待値はありません。`L.PIN` は既存のCCBench pinで、作業ツリーHEADではありません。

must-fix / nit ともになし。

## 記録との整合

- `[must-fix・親担当]` [tools/pegasus/README.md:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/README.md:316) — 有効 receipt を渡したjobは5値を共有buildへ通す一方、READMEは「seamが無くproxy cloneへ依存」と記載したままです。同じ旧説明が未測定項目にも残ります。[README.md:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/README.md:341)  
  放置時の影響: 運用上の一次参照が、実際のlocal prebuild transportを外部network依存として誤表示します。

- `[must-fix・親担当]` [docs/pegasus-runbook.md:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/docs/pegasus-runbook.md:360) — 同じrepo/layoutで既にterminalなvariantへreceiptを渡すと、`evaluate`前にskipされprebuildを消費しません。[loop.py:544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:544) 裁定R1の運用注記が§7.0にまだありません。  
  放置時の影響: operatorが再投入をprebuild消費走行と解釈しても、実際には既存terminal WALを参照してbuild 0件になります。

- `[must-fix・親担当]` [docs/worklog.md:1152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/docs/worklog.md:1152) — T-2356が現在も「実装待ち」、seamが死んでいる状態として残っています。履歴を書き換える必要はありませんが、親の完了記録でsupersedeが必要です。  
  放置時の影響: 現行タスク参照がT-2356を未実装候補として再提示し、同じ作業を重複配車し得ます。

これらが差分に無いこと自体は、指定どおり親担当であり手順違反とは判定していません。

## 総括

実装6ファイルについて、既存caller、既定kwargs/argv/cache/WAL、pin、job実行面、揮発期待値を壊すコード上の欠陥は見つかりませんでした。commit前のmust-fixは親担当の記録同期3点です。

pytest、`bash -n`、`check_docs.py`は実行していません。静的には `git diff --check`、変更Python 5ファイルのAST parse、caller全数、test名重複を確認しました。