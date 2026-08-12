## 所見

### 1. provenance preflight の順序が実装と逆

- **[real の根拠]** runbook は「overlap 判定 → provenance checker → merge」とする一方、実装は「merge → provenance checker → dry-run」です。[runbook:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:829)、[dev_wave_wait.py:872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:872)。checker は `MERGE_HEAD` がある場合に merge parents と両親差分を検査するため、merge 前実行は意味も異なります。また runbook の「checker 非 0 なら merge を中止」も、その記載順では merge 自体がまだ始まっておらず内部矛盾です。
- **[成果物影響 1 行]** docs どおりの再実装では merge の実装面 path が provenance 判定から落ち、誤った author 受理が commit・台帳の監査列へ入ります。
- **[判定] must-fix**

### 2. `prerun-clean` の保証範囲を過剰主張している

- **[real の根拠]** runbook は「claim から投入までの窓を閉じる」「投入の瞬間に木と tip が一致」としますが、実装は status 終了後に診断を出し、その後 `run_unbounded()` で child を起動します。[runbook:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:848)、[dev_wave_wait.py:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:919)。status 後から process 起動までの write は検出不能です。段 4 裁定の「投入瞬間の一致を保証すると書かない」にも反します。
- **[成果物影響 1 行]** 検査直後の変更を含む受入が緑でも、レポート・台帳が「tested tip と投入時 tree が一致」と誤って証明します。
- **[判定] must-fix**

なお runbook §7.5 の「全走中は同じ木へ書かない」は operator 規律としては両立します。ただし機械保証ではありません。

### 3. F191 の採用済み erratum が正本へ反映されていない

- **[real の根拠]** runbook は second parent で点 1 を充足すると記載しましたが、F191 本文は今も「message template へ SHA を差し込む」、点 3 は option なしの `git status --porcelain` のままです。[runbook:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:838)、[failures.md:4975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/failures.md:4975)。段 4 plan v2 が要求した F191 erratum 3 点が未実装です。
- **[成果物影響 1 行]** F191 を参照するレポート・失敗台帳の proof chain が、実際の merge parent・untracked 込み述語と異なる契約を指します。
- **[判定] must-fix**

### 4. 既存 wave は最初の一走だけ旧 waiter で新 gate を迂回できる

- **[real の根拠]** `dev-wave-t748-pilot-path` は main より 11 commit behind で、branch 上の waiter は旧 `--untracked-files=no` のままです。この旧 Python process が claim 後に新 main を merge しても、ロード済みコードは差し替わらず、新 `preflight-clean` / `prerun-clean` はその走行では発火しません。runbook に rollout barrier や waiter 再起動条件はありません。
- **[成果物影響 1 行]** 新契約を含む tip が、旧 waiter による untracked 未検査の受入結果で land され、台帳へ「新 gate 済み」と誤認され得ます。
- **[判定] must-fix**

少なくとも「新 main を取り込んで waiter process を再起動してから、この契約下の受入と数える」という移行条件が必要です。

### 5. untracked を作る実在 producer と `.gitignore` が一致していない

- **[real の根拠]** 登録済み `dev-wave-t748-pilot-path` は現在、次を untracked で持ちます。

  - `output/env/pegasus/floor/attempts/submissions/**`
  - `output/env/pegasus/floor/job-staging/**`

  これらは floor の正式な生成物です。[Pegasus README:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/pegasus/README.md:216)。しかし root `.gitignore` は `silo_ladder_rung1/job-staging/` 等だけを覆い、floor の二経路は覆いません。[.gitignore:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/.gitignore:17)。新 waiter を使えば claim 前の `preflight-clean` / rc=2 で停止します。

  通常の Python cache、`output/runs/`、dispatch、root `build/`、CCBench の `build*/`・object 類は無視されます。一方、submodule の in-source `CMakeCache.txt`、`cmake_install.cmake`、任意 log は無視されず、`--ignore-submodules=none` で親を dirty にします。
- **[成果物影響 1 行]** floor 証拠を持つ wave の受入・land が止まり、床値レポート、試行台帳、そこからの certified 判断が未収録になります。
- **[判定] must-fix**

runbook の「commit するか `.gitignore`」だけでは不十分です。途中の証拠を盲目的に commit/ignore できない producer について、停止・repo 外退避・hash 固定・再実行の安全な復旧順が必要です。

### 6. 段 7 fragment と最終受入の順序が canonical docs で閉じていない

- **[real の根拠]** state machine は段 6 で受入、段 7 で記録 commit としています。[dev-wave.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/.claude/commands/dev-wave.md:51)。一方、land は wave HEAD と `tested_tip` の exact 一致を要求するため、段 7 commit 後には最終受入が必要です。[dev_wave_land.py:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_land.py:603)。`DW-S07` は fragment の commit を要求しますが、spool の例は `git add` までで、最終受入との順序を明記しません。[core.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/dev-wave/core.md:87)、[spool README:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/spool/README.md:65)。
- **[成果物影響 1 行]** fragment 未 commit なら rc=2、受入後に commit すれば land が tested-tip 不一致となり、worklog・decisions・failures fragment が台帳へ fold されません。
- **[判定] must-fix**

必要な順序は「fragment 作成 → check/dry-run → add/commit → 最終受入 → tested tip 固定 → land」です。runbook の一般論「待機前に commit」だけでは、段 7 の状態遷移が一意になりません。

### 7. merge message file の配置条件が欠けている

- **[real の根拠]** runbook は message file を待機前に用意するよう要求しますが、repo 外へ置くとは書いていません。[runbook:786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:786)。repo 内に新規作成すると、実装は message を読む前に `preflight-clean` で untracked として拒否します。[dev_wave_wait.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:552)。
- **[成果物影響 1 行]** docs の例どおり準備しただけで受入が claim 前に止まり、受入結果と台帳記録が生成されません。
- **[判定] must-fix**

`--merge-message-file` は `dev-wave-jobs/<wave>/` 等の repo 外 path と明記すべきです。

### 8. 新テストは production checker と submodule dirt を実 Git で通していない

- **[real の根拠]** 実 Git 負例は tracked file の claim 後変更だけです。submodule dirt の実 Git 負例はなく、merge integration は production `check_ai_provenance.py` ではなく一時 stub checkerを使います。[test_dev_wave_wait.py:2718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2718)、[test_dev_wave_wait.py:2800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2800)。
- **[成果物影響 1 行]** 現行値は直ちに変わりませんが、MERGE_HEAD-sensitive provenance や submodule 判定の将来回帰をこのファイル単独では検出できません。
- **[判定] nit**

## consumer pin・共有 fixture の確認

- `tools/check_docs.py` の pin は runbook §7.3 本文を読みません。固定対象は `.claude/commands/dev-wave.md` の段 6/9、`DW-C00`、`DW-O01` と canonical file 実在だけです。[check_docs.py:3918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/check_docs.py:3918)。したがって今回の §7.3 改稿で consumer pin は赤になりませんが、所見 1・2も検出しません。
- `test_dev_wave_waiter_consumer_pins_accept_current_docs_contract` は上記 3 文書しか渡しておらず、§7.3 は対象外です。[test_check_docs.py:5897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_check_docs.py:5897)。
- mutation fanout の test は `tools/mutation_fanout.py` に `dev_wave_wait` 等が混入しないことだけを見るため、今回の差分とは独立です。[test_mutation_fanout.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_mutation_fanout.py:875)。
- `_PREFLIGHT_EVENTS`、`_STATUS_ARGV`、`_RoutingAcceptanceEffects` は同一 test module 内だけの fixture です。所有外 test file への import 波及はありません。
- `git diff --check` は問題なし。pytest は指示どおり実行していません。

## 総括

### (a) must-fix: 7 件

1. provenance preflight の順序が実装と逆
2. `prerun-clean` の保証範囲を過剰主張
3. F191 erratum が正本未反映
4. 既存 wave の旧 waiter による一走限りの rollout bypass
5. 実在する floor 生成物と `.gitignore` の不一致
6. 段 7 fragment commit と最終受入の順序が未確定
7. merge message file の repo 外配置条件が欠落

### (b) docs と実装の不一致: 全 2 件

1. docs は provenance checker → merge、実装は merge → provenance checker。
2. docs は claim〜投入窓と投入瞬間の一致を保証、実装は status 時点しか観測しない。

述語文字列、stage 名、rc、ACQUIRED/HELD_SELF の release 帰結、poll range、second parent による main SHA 記録は一致しています。F191 の stale 本文は docs 対 docs の不一致なので、この 2 件には含めていません。

### (c) 他 wave を壊す risk

**real かつ rollout 方法に依存します。** 旧 waiter をロードした既存 wave は最初の一走だけ新 gate を迂回でき、その後、新 waiter を取り込んで再実行すると untracked producer artifact により rc=2 で止まります。特に未 land の `dev-wave-t748-pilot-path` は、実在 floor 生成物を untracked で保持しており、この両側の危険を同時に満たします。安全な移行 barrier と producer 別の clean 化手順なしで land すべきではありません。