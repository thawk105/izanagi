## 総括

親確定済みの import 不発とは別に、D724 の admission 契約を破る must-fix がある。
自動注入された `"3"` は runner 上で明示指定となり、local admission を常に迂回して計算ノードへ dispatch する。
また、空文字環境では K=3 にならず、追加テストも `"3"` を literal に固定していない。
receipt は shard 数を記録しないため、誤って K=2 で走っても land は検出できない。

## 所見

### 1. 自動的な明示 K=3 は D724 の配置契約を破る

- `重大度`: must-fix
- `根拠 (file:line)`:
  - 注入値は runner に明示指定として渡る: [tools/dev_wave_wait.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:817)
  - runner は明示 2/3 を `explicit_shard_mode` とし、admission 条件から除外する: [tools/run_tests.py:2490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/run_tests.py:2490)
  - その後 `shard_mode` だけで直接 dispatch する: [tools/run_tests.py:2620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/run_tests.py:2620)
  - D724 は「既定の K=2 は login admission が dispatch を選んだ場合だけ」とする: [docs/decisions.md:28363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/decisions.md:28363)
  - 矛盾する本文は「本決定が変えるのは『dispatch される走行を何本に割るか』だけで、『どこで走るか』は変えない」: [docs/decisions.md:28371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/decisions.md:28371)
  - さらに「admission を迂回したまま既定化する」を明示的に却下している: [docs/decisions.md:28392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/decisions.md:28392)
- `失敗する具体シナリオ`: Pegasus LOGIN で local memory admission がローカル実行を選べる状況でも、waiter が `"3"` を自動注入すると admission を一度も評価せず 3 request を投入する。queue 停止時には、従来ローカル実行できた受入が rc=16 で終了し得る。
- `成果物影響`: rc=16 は receiptable でなく acceptance receipt が発行されないため land 不能。成功した場合も receipt は K や admission 通過を証明しない。
- `判定`: D724 が許す「明示 2/3」という字面には入るが、運用者の明示指定ではなく wrapper が既定で設定するため、実質は D724 が却下した「admission 迂回の既定化」である。D724 を明示的に supersede する裁定か、admission を保つ別設計が必要。

### 2. 空文字の環境変数では K=3 が注入されない

- `重大度`: 高
- `根拠 (file:line)`:
  - waiter は値でなく key の存在だけを見て注入を中止する: [tools/dev_wave_wait.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:820)
  - runner と D724 は未設定と空文字を同じ「指定なし」と扱う: [tools/run_tests.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/run_tests.py:253), [docs/decisions.md:28349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/decisions.md:28349)
  - 追加テストは未設定と `"1"` しか覆わず、空文字を覆わない: [orchestrator/tests/test_dev_wave_wait.py:3353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3353), [orchestrator/tests/test_dev_wave_wait.py:3389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3389)
- `失敗する具体シナリオ`: shell や scheduler 環境に `IZANAGI_ACCEPTANCE_SHARDS=` が export されている。Pegasus LOGIN でも waiter は環境を変更せず、runner は request を `None` と解釈して従来の K=2/admission 経路へ入る。
- `成果物影響`: K=2 走でも通常の v5 receipt が作られ、shard 数を持たない land はそのまま受理する。要求した K=3 が実現していないことを成果物から検出できない。

### 3. 定数と runner 受理集合の機械照合がなく、追加テストも `"3"` を固定していない

- `重大度`: 高
- `根拠 (file:line)`:
  - waiter の選択値: [tools/dev_wave_wait.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:313)
  - runner の受理閉集合: [tools/run_tests.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/run_tests.py:253)
  - 新テストは期待値にも production 定数を使うため、定数を `"2"` または `"4"` に変えても assertion 自体は成立する: [orchestrator/tests/test_dev_wave_wait.py:3367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3367)
  - `run_tests` と waiter を既に同時 import する consumer があるが、今回の consumer 列挙から漏れている: [orchestrator/tests/test_run_tests_shards.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_run_tests_shards.py:16)
- `失敗する具体シナリオ`:
  - waiter 定数だけ `"2"` になると K=2 へ静かに退行し、追加テストも通る。
  - waiter 定数が `"4"`、または将来 runner が `"3"` を受理集合から外すと、runner が suite 起動前に rc=16 を返す。
- `成果物影響`: `"2"` への退行は receipt と land で不可視。受理外値では receipt が発行されず land 不能。
- `推奨`: 権威は shard request の構文と admission を所有する `tools/run_tests.py` に置く。共有 runtime 定数へ移すと D838 の tested-main runner が tip 側依存を import する問題を作るため、`test_run_tests_shards.py` に cross-contract 検査を置くのが安全。少なくとも literal `"3"`、runner parser がそれを 3 と受理すること、eligible 条件で effective K=3 になることを同時に固定する。

### 4. receipt と env projection は形式上変わらず、land は K=2/K=3 を区別しない

- `重大度`: 情報
- `根拠 (file:line)`:
  - env projection は 4 field だけ: [tools/dev_wave_wait.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:454)
  - launcher も exact 4 field を要求する: [tools/acceptance_launcher.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/acceptance_launcher.py:36), [tools/acceptance_launcher.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/acceptance_launcher.py:159)
  - 注入は projection 作成後、launcher process の実環境にだけ行う: [tools/dev_wave_wait.py:3103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:3103), [tools/dev_wave_wait.py:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:844)
  - land も同じ exact 4 field だけを照合する: [tools/dev_wave_land.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_land.py:138), [tools/dev_wave_land.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_land.py:967)
- `失敗する具体シナリオ`: 所見 2 の空文字経路で K=2 が走っても、projection は正しい 4 field のままで land は拒否しない。
- `成果物影響`:
  - `argv`、`resolved_runner_path`、`launcher_*`、`runner_executed_sha256` は本変更では不変。
  - `waiter_blob_sha` と `waiter_executed_sha256` は waiter の変更に伴って変わるが、land は tested tip の blob から再計算するため正常に受理する: [tools/dev_wave_land.py:1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_land.py:1054)
  - `log_sha256` は K=3 のログ内容に応じて変わり得る。waiter は launcher 観測値との一致を確認するが、land は 64 桁形式だけを検査する: [tools/dev_wave_wait.py:3845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:3845), [tools/dev_wave_land.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_land.py:963)
  - D724 自身が receipt は K と gate 通過を証明しないと明記している: [docs/decisions.md:28397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/decisions.md:28397)

D838 の凍結対象は `tools/run_tests.py` だけである。launcher は通常 tested-main blobから実行されるが、main/tip launcher の等値は要求されない: [docs/decisions.md:31681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/decisions.md:31681), [tools/dev_wave_wait.py:2544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:2544), [tools/dev_wave_land.py:1021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_land.py:1021)。したがって `acceptance_launcher.py` は main 版で実行される束縛は持つが、「変更した wave は受入不能」という runner と同じ凍結ではない。

### 5. K=3 で増える具体的な故障面

- `重大度`: 運用上の高リスク
- `根拠 (file:line)`:
  - 3 shard をすべて先に起動する: [tools/acceptance_shards.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/acceptance_shards.py:1243)
  - 1 shard でも rc が 0/1 以外なら兄弟を終了させ aggregate rc=16 にする: [tools/acceptance_shards.py:1313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/acceptance_shards.py:1313)
  - queue timeout は各 request 900 秒: [tools/pegasus/dispatch_compute.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/pegasus/dispatch_compute.py:65)
  - 全 shard の共有 deadline は 5100 秒: [tools/run_tests.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/run_tests.py:79)
  - orphan hold は後続投入を rc=16 で止め、source/worktree の保全を要求する: [tools/pegasus/dispatch_compute.py:1461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/pegasus/dispatch_compute.py:1461), [tools/pegasus/dispatch_compute.py:2817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/pegasus/dispatch_compute.py:2817)
- `失敗する具体シナリオ`:
  - 3 本中 1 本だけが 900 秒以内に RUN へ入らないと全体が rc=16。残り 2 本が完走可能でも receipt は出ない。
  - 1 本が infra failure になると親が兄弟を terminate/qdel する。どれかの終端を証明できなければ request ごとの orphan hold が残り、後続受入も停止する。
  - 3 本が同じ 5100 秒 deadline を共有するため、1 本の queue skew、実行遅延、結果回収遅延だけで全体 deadline を消費する。
  - hold 発生時は acceptance receipt が発行されず、保全された worktree/evidence は人手処理まで残る: [docs/pegasus-runbook.md:1470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/pegasus-runbook.md:1470)
- `成果物影響`: 失敗確率は「3 本すべてが receiptable」に依存する。全 shard 未起動の queue timeout だけは全体再試行の候補になるが、1 本でも起動済みなら再試行されず receipt 無しで終わる。

## 赤になる既存テストの列挙

無し。pytest は未実走であり、以下は静的な赤予測である。

`tools/dev_wave_wait.py` を参照する test は次の 7 file だった。

- `orchestrator/tests/test_dev_wave_wait.py`: canonical waiter の直接テスト。変更前には `_default_launch_launcher` の `Popen` kwargs 集合や `env` 不在を固定するテストは無い。今回追加された捕捉テストだけが `env` を検査する: [test_dev_wave_wait.py:3297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3297)
- `orchestrator/tests/test_run_tests_shards.py`: waiter の dispatch marker consumer を参照するだけで、launcher 環境は参照しない: [test_run_tests_shards.py:991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_run_tests_shards.py:991)
- `orchestrator/tests/test_dev_wave_land.py`: waiter blob hashを fixture repository から動的に計算し、real waiter E2E も synthetic runner が追加 env を検査しない: [test_dev_wave_land.py:2041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_land.py:2041)
- `orchestrator/tests/test_resume_gate_acceptance_boundary.py`: waiter を複製し、receipt hash を複製した blob から動的に照合する: [test_resume_gate_acceptance_boundary.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_resume_gate_acceptance_boundary.py:258)
- `orchestrator/tests/test_fold_gate_nodes_contract.py`: AST 上の起動 payload 禁止検査であり、追加された環境 helper は対象外: [test_fold_gate_nodes_contract.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_fold_gate_nodes_contract.py:240)
- `orchestrator/tests/test_check_docs.py`: docs consumer の文字列契約だけを検査する: [test_check_docs.py:7451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_check_docs.py:7451)
- `orchestrator/tests/test_check_wave_startup.py`: startup guidance の文字列だけを参照する: [test_check_wave_startup.py:988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_check_wave_startup.py:988)

なお、author の consumer 列挙は `test_run_tests_shards.py` を落としている。また新規 Popen テストは `**kwargs` で受けるため、kwargs 追加そのものによる既存テスト赤は無い。

## docs 陳腐化箇所の列挙

無し。

`docs/dev-wave/` と `docs/pegasus-runbook.md` には、受入を K=2 または K=3 と固定する記述は見つからなかった。runbook の fan-out/orphan-hold 記述は shard 数に依存しないため陳腐化しない: [docs/pegasus-runbook.md:1470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/docs/pegasus-runbook.md:1470)。

数値 K=2 を持つのは指定範囲外の D724 であり、これは単なる docs 更新ではなく所見 1 の裁定衝突として扱う必要がある。

## 未確認事項

- pytest、受入全走、Pegasus live dispatch は依頼どおり未実走。
- queue 停止時や local admission 時のシナリオは実装分岐からの静的結論で、実機再現はしていない。
- 親確定済みの `site_policy` import 不発は再所見化せず、評価対象から除外した。
- Web 検索は行っていない。