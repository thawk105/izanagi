## 対応表

判定は指定された `a9cc7dbe3` までの静的差分に対するものです。3 回目の焦点走は結果を確認していません。

| 所見 | 状態 | 根拠 |
|---|---|---|
| A1 依存 prefix の区切り | closed | CLI は環境変数を明示引数へ写していない。[driver:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:319)、[test:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_policy.py:524) |
| A2 stock の source identity | closed | 同一 attempt の `BUILD_START.src_token` と stock variant を確認する。payload の実際の key も `src_token`。[driver:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:337)、[pipeline:1989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/pipeline.py:1989) |
| A3 stock 不成立の rc | closed | 単独 stock と pair の stock 不成立は rc=1。[driver:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:614)、[driver:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:669) |
| A4 compiler 固定による skip | closed | `find_compiler()` に変更。[test:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_policy.py:489) |
| B1 候補未実走の pair | closed | `ran=False` なら stock を起動せず rc=1。[driver:655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:655) |
| B2 方策 PIN の準備手順 | closed | 方策 PIN の読み替えを明記。[README:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/README.md:479) |
| B3 完全な pair 投入例 | partial | `qsub` 行は追加されたが、そこで使う `ARCHIVE_ROOT` の設定がない。[README:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/README.md:493) |
| B4 重複 env 検査 | 不採用のまま | 裁定どおり保持。[job body:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/p3_s4_loop_pegasus.sh:237) |
| 親の所見: 計測 log の破棄 | closed | stderr へ出す。[driver:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:613) |
| 焦点走 1 回目 R1 | closed | resolver の未定義 `policy_mode` 参照を修正。[job body:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/p3_s4_loop_pegasus.sh:358) |
| R2 | closed | 共有偽 driver の環境記録は既存の 2 key に戻した。[test:1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_job_contract.py:1324) |
| R3 | closed | 保全 root の拒否テストを実際の rc=2・driver 未起動に合わせた。[test:1510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_job_contract.py:1510) |
| R4 | closed | `run_campaign` を stock・候補の関数内へ戻した。[driver:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:378)、[driver:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:419) |
| 焦点走 2 回目の 2 件 | closed（静的） | 登録簿と raw AST の期待件数を実際の 2 呼出しへ追随。実行時の 1 呼出し期待値は維持。[test_campaign:5439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_campaign.py:5439)、[namespace test:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_exploration_namespace.py:463) |

## 新しい所見

- **should-fix — pair 投入例の `ARCHIVE_ROOT` が未設定。** [README:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/README.md:462) の変数設定にこの値がなく、[README:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/README.md:493) で初めて参照する。**成果物への影響:** 例をそのまま使うと空値が渡り、[job body:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/p3_s4_loop_pegasus.sh:287) で rc=2 となって E2E と trace 保全に到達しない。**修正案:** 方策用の例の直前に、repository 外の絶対 path を `ARCHIVE_ROOT=...` として設定する行を加える。

分割後の計測引数は、stock・候補とも共通の `_measurement_options` を使い、同じ環境契約、認可 session、fetchcontent 受領証を渡す。stock だけに capability resolver を付ける差は意図どおり。[driver:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:319)、[driver:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:374)、[driver:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:415)。job body も driver の rc を伝播する。[job body:799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/p3_s4_loop_pegasus.sh:799)

保全 root の方策テストは、偽 driver が受け取った環境値を別記録して照合するため恒真ではない。ただし検査対象は root の到達までで、trace の実保存は親の実測で確認する必要がある。[test:1329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_job_contract.py:1329)、[test:1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_job_contract.py:1496)

規律 1・2 を損なう差分は見つからなかった。方策の compile gate と auditor gate、verify 構成は維持されている。[driver:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:178)、[driver:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:134)

## 総括

NO-GO。B3 の投入例を完成させ、並行中だった 3 回目の焦点走の結果を確認してから E2E に進む判断が妥当です。静的レビューでは、計測引数・stock identity・rc・登録簿・規律 1・2 に追加の欠陥は見つかりませんでした。