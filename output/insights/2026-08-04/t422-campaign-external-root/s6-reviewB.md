## 所見

### 1. process pin が二重 module identity 間で共有されない

- 種別: 波及・並列整合
- 深刻度: 高 / must-fix
- 根拠: pin は module global です。[layout.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:224) 一方、8c は `orchestrator.campaign.layout` を相対 import し、[p3_autonomous_workload_trial.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:94) trigger は別 identity の `campaign.layout` を import します。[p3_s4_loop_trigger_gating.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:67) conftest が両者を個別 reset していることも二重実体を示します。[conftest.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/conftest.py:128)
- 具体的な壊れ方: 8c が root A の layout を `ensure()`・lock 作成した後、env が B に変わると、trigger 内の別 alias は未 pin なので B を初回値として受理できます。trigger は A を先に materialize し、[p3_s4_loop_trigger_gating.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:475) その後 `output_root` 無指定の別 `run_campaign` を呼びます。[p3_s4_loop_trigger_gating.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:496)
- 成果物影響: marker・lock・provenance は A、build/verify/bench WAL は B、返却 `layout_root` と WAL reader は再び A、という分裂が可能です。
- 修正方向: layout state を両 import 名が共有する単一 module に置き、check-and-set を lock で原子的にする。`campaign.layout` で A を pin 後、`orchestrator.campaign.layout` で B/未設定を必ず拒否するテストを追加する。

### 2. 8c の env 未設定時 default は全 caller で旧文字列と同一ではない

- 種別: 既存 caller 回帰
- 深刻度: 中 / must-fix
- 根拠: 旧 base は symlink を解決する `ROOT = Path(__file__).resolve()` です。[p3_autonomous_workload_trial.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:134) 新 default は `Path(_resolve_exploration_output_root())` ですが、env 未設定時の `repo_output_root()` は `abspath` のみで symlink を保持します。[p3_autonomous_workload_trial.py:1758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1758) [layout.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:42)
- 具体的な壊れ方: repo を symlink 経由で import/起動した caller では、旧 default は実体 path、新 default は symlink path になります。型は双方 `Path`、通常 checkout と trailing 表現は同一ですが、文字列完全互換ではありません。
- 成果物影響: `attempt_journal` と `run-finish.report` に path 文字列が保存されるため、[p3_autonomous_workload_trial.py:1196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1196) launcher 用 symlink の撤去後に台帳参照が切れます。
- 修正方向: env 未設定時は resolver の pin 検査を通しつつ、base 値には従来の `ROOT / "output"` を返す。symlink 経由の回帰テストを追加する。

### 3. F98 正例の WAL は production replay 契約を満たさない

- 種別: テスト代表性
- 深刻度: 中 / must-fix
- 根拠: fake evaluator は `build_start` に `build_attempt_id` を入れず、`build_done`・admission receipt なしで `commit` を書いています。[test_dev_wave_land.py:2718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2718) 現行 replay は attempt id を必須とし、[wal.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:616) receiptless attempt の commit も拒否します。[wal.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:660)
- 具体的な壊れ方: 初回 `run_campaign()` は返りますが、同じ campaign の次回起動は冒頭の `wal.replay()` で `AttemptTopologyError` になります。[loop.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/loop.py:152)
- 成果物影響: 「campaign を1回起動し WAL が残った」という正例が、再開不能な台帳を正常成果物として通します。
- 修正方向: canonicalな `build_start→build_done→commit` を書くか、validな pre-build abort を使い、最後に `wal.replay(..., admission_policy=context.policy)` の成功を固定する。

### 4. worktree 拒否診断が修正方法を示さない

- 種別: 診断品質
- 深刻度: 低 / nit
- 根拠: message は worktree 配下不可としか述べず、env 名や base root の形を示しません。[layout.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:331)
- 具体的な壊れ方: env を渡し忘れた T-420 job は停止しますが、stderr だけでは `IZANAGI_EXPLORATION_OUTPUT_ROOT=/work/<job専用base>` が復旧策だと分かりません。
- 成果物影響: 拒否は安全側で certified 値を変えないため nit。再投入まで成果物が生成されません。
- 修正方向: env 名、「絶対 path」「job 専用」「base は `exploration/` 自体ではない」を message に含める。

### 5. 素の land-test runner が `sys.path` を復元しない

- 種別: テスト隔離
- 深刻度: 低 / nit
- 根拠: 新テスト2本が `sys.path` へ追加しますが、finally は env・factory・evaluate 等だけを復元します。[test_dev_wave_land.py:2687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2687) [test_dev_wave_land.py:2764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2764) 加えて import される pipeline も同 path を再挿入します。[pipeline.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/pipeline.py:28)
- 具体的な壊れ方: import 途中の失敗後も `_run()` は次の test へ進むため、後続の動的 import の解決順が変わります。[test_dev_wave_land.py:2841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2841)
- 成果物影響: 現行の後続 test に新たな動的 import はなく、成果物影響を書けないため nit。
- 修正方向: import 前に `sys.path[:]` を保存し、finally でリスト全体を復元する。

## 攻撃したが破れなかった面

- 単一 module identity 内では pin 代入は全 env 検査後だけで、env 未設定時に因果なく raise する別経路はありません。[layout.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:281)
- worktree gate は exact component 対だけを見るため、通常の `/tmp`、`/work`、main checkout の repo-local `output/exploration/autonomous-trials` は通り、wave container だけが拒否されます。[layout.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:326)
- consumer test に静的な赤は見つかりませんでした。namespace test は factory を `tmp_path` へ差し替え、[test_p3_exploration_namespace.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_p3_exploration_namespace.py:98) loop/sort は明示 tmp layout、trigger は factory spy、8c build test も factory と drive を fake 化しています。[test_p3_autonomous_workload_trial.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_p3_autonomous_workload_trial.py:1039) oracle の factory 利用箇所は明示 `output_root=tmp_path` です。[test_s8b_oracle_artifacts.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_s8b_oracle_artifacts.py:30)
- pytest-xdist は worker process 分離で、worker 内は逐次です。autouse fixture が env と両 module pin を前後で reset するため、env・pin・`os.geteuid` の現行テスト間漏洩窓はありません。二重 alias の production pin 不整合は所見1の別問題です。
- F98 正例は layout `ensure`、namespace marker、campaign lock、WAL path、synthetic worktree clean、`_verify_wave_clean` まで通ります。実 evaluator/build/verify/bench は通りません。現行 `run_campaign` に別の repo-local spec writerは見つからず、spec directory 自体は同じ external layout 配下です。
- T-420 は env 注入だけで外部化できます。job script は新 env を unset せず、driver は `layout=None` で trigger factoryへ到達します。ただし凍結済み再現コマンドは現在も progress env しか渡していません。[README.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/README.md:39) 再走時に `qsub -v` へ新 env を追加する必要があります。これは s4 裁定どおり次 wave の運用注入で、追加の shared-code 配線は不要です。

pytest は実走していません。静的検査のみで、`git diff --check` は通過しました。

## 総括

real 候補数は **5件**、must-fix は **3件**。最深刻は、二重 module identity により process pin が共有されず、env drift 時に marker・lock・WAL・report が別 root へ分裂し得る所見1です。