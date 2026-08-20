---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: t1371-official-run-root
seq: 2
title: '[T-1371] official run の run root/campaign root を repo 外へ強制し RatifiedFreeze v2 の repo scan 契約と非矛盾にした (コード+テスト、branch worktree-T-1371-official-run-root)'
---

## 本文

- ユーザー裁定 (2026-08-20、command 引数で直接指定): 正式 run の run root/campaign root を
  repo 外へ強制する択(a) を採用。一次資料は
  `docs/archive/worklog-phase3-0818-658.md:618-631` (entry 658)。設計判断は
  {{D:official-output-root-forced-external}}。
- 段2 codex プランが (P1)〜(P4) を支持しつつ、`default_durable_root_policy()` (repo output/
  のみ approved) を弱めずに official run を実際に repo 外で完走させる配線が未解決 (P5) と
  発見した。段3 敵対相談2レンズがこの (P5) 軽視は誤りと指摘し (s8b_oracle_driver.py は
  trial_registry の12述語gateを経由しない独自 admission を持つため)、`run_block()` の
  既存 `durable_root_policy` 引数を CLI から埋めるだけの狭い配線を段4 裁定で scope に追加した。
  同レンズは段2プランの「直接 `CampaignLayout` 構築はテスト専用」も反証したが、該当2箇所
  (`guided.py`・`p3_autonomous_workload_trial.py` の `--no-build` journal-local layout) は
  親が直接確認していずれも非 official (前者は declared_use_class 概念自体を持たない P2-5
  誘導アーム、後者は runbook が明示的に「正式 campaign ではない」と免責) と確定し scope 外にした。
- 段5 実装子は Codex sandbox 制約で pytest を実走できなかった (rc=16、Pegasus dispatch
  preflight 失敗)。親が実測で17件の red を発見: 15件は既存 test fixture が git 初期化済み
  fixture root の内側へ output_root を置いており新設の git-ancestor 拒否が正しく発火した
  ため (resolver のバグではなく fixture 側の修正で解消)、1件は新設 test の symlink 先
  ディレクトリ未作成、1件は AST 制約 meta-test
  (`test_gate_decision_is_built_only_by_factory_and_all_run_returns_propagate`) の期待件数
  更新漏れ。fix 1巡で解消し `tools/run_tests.py` (対象10ファイル) で 1057 passed・
  27 skipped・0 failed を確認した。
- 段6 敵対レビュー2本 (実装差分の正確性・回帰境界条件) が real 所見計4件を返した。うち1件
  (exploration 側の `_resolve_exploration_output_root` が worktree container 拒否の
  タイミングを resolve 時へ前倒しし D158 の既存契約と矛盾する回帰) を fix 2巡目で復元し、
  回帰防止テストを追加した。残り3件 (未実走 consumer test 2本の追加実走要・D158 陳腐化・
  運用 runbook 更新漏れ) のうち consumer test 追加実走は同 fix 後の親再実走に含め、
  D158 陳腐化は本エントリの決定 fragment で supersede し、運用 runbook 更新は本 commit の
  docs 側で対応した。fix 後、親が10ファイルで再実走し 1173 passed・27 skipped・0 failed を
  確認した。
- 変異事前登録6件 (`resolve_official_output_root` の fail-closed 化・explicit 引数検証・
  git 祖先拒否・CLI 既定値・`ValueError`→refused 変換・`durable_root_policy` 配線) を段4で
  登録し `tools/mutation_harness.py` で裏取りした。probe (`expected_status=SURVIVED` 仮登録)
  で baseline PASSED・6件全て KILLED を確認。実測値で正式登録した本走では m03/m04/m05 が
  `matches_expectation=true` (単一理由性を機械確認)。m01/m02/m06 は本走で追加の無関係な
  failed node が混入し機械判定が揺れたが、原因は同一アカウントで並行稼働中の他 dev-wave
  セッション (T-1403・T-1310 等、7〜8時間稼働中) との per-user cgroup memory 予算・Pegasus
  gen_S queue (85〜99件滞留) の共有、および他プロセスの一時的な `/tmp/.git` 生成による
  `_has_git_ancestor()` の誤検出であり、親の手動コード追跡 (呼び出し経路の直接確認) で
  3件とも single-reason 性を独立に確認した。実装コード自体への疑義ではないと判定した。

## 次の一手差分

### 完了

- [T-1371] official campaign の出力 root を repo 外へ強制し、RatifiedFreeze v2 発効時の
  repo scan 0-hit 契約との自己矛盾を解消した。設計は
  {{D:official-output-root-forced-external}} 参照。
  remaining: none
  base: 713e663d2dfecbad0b6f899ac798b875f4776924a5e657774daf39fc6431445b
