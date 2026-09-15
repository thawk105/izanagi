# 段 1 brief — [T-2496] `run_trial` 経路の hard timeout

- wave: `dev-wave-t2496-git-timeout` / branch `worktree-dev-wave-t2496-git-timeout` / 起点 main `7dc4ecc39`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2496-git-timeout`

## 研究前進

論文の主張を直接進める wave ではなく土台である。止めている研究は「`run_trial` の 1 node が
git 呼び出しで無期限に止まると、試行台帳が埋まらず certified 選択の材料収集が止まる」こと。
最小差分は `trial_registry._git` の `subprocess.run` へ hard timeout を渡し、超過を fail-closed の
拒否へ写すこと。完了判定 = timeout が確実に発火する正例と正常完了を落とさない負例が同じ commit にあり、
焦点走と受入全走が緑。

## scope

- 変更面 (アンカー): `orchestrator/campaign/trial_registry.py` の `_git` (967〜977 行、`subprocess.run` は 971 行)。
  呼び出しは 16 箇所 (987 / 1151 / 1168 / 1180 / 1189 / 1205 / 1229 / 1294 / 1330 / 1349 / 2543 / 2560 / 2606 / 4583 / 5303 / 5342 行) で、
  すべてこの 1 関数を通る単一 choke point。
- テスト: 既存 `orchestrator/tests/test_trial_registry.py` へ正例・負例を追加する。**新規 test file を作らない。**
- scope 外: 他 campaign module の git helper、`executor` (D1847 却下項)、汎用 watchdog、監視 framework、
  `max_wall_s` の意味変更、新しい gate / 検査 / 台帳 / 一般化。

## 確定済みユーザー裁定 (引数)

局所修正だけ。仮想リスク向けの追加を作らない。規律 2 を緩めない。fresh worktree は作成済み。

## 不変条件

1. `test_ccbench_spawn_sites.py:284` の `("campaign/trial_registry.py", "<module>._git"): 1` を変えない。
2. 事前登録 evidence 契約 (`s8c_preregistration_evidence_contract.v1.json`) が束縛する関数名と call edge を変えない。
3. **timeout は受理を広げない。** 必ず例外で拒否へ写す。`except TrialRegistryError` は同 file に 10 箇所あり、
   握り潰すのは 2578 行 `_looks_like_attempt_genesis` だけで、そこは `_git` から到達しない (実装子とレビュー子が再確認する)。
4. `trial_registry.py` は A-1 paired campaign の source closure member (`paper_story_a1_paired.py:179`、
   `tools/pegasus/paper_story_a1_paired.sh:67`)。凍結 sha256 定数での pin は見つかっていない (digest は走行時計算)。
   land 直前に A-1 job の投入中有無を確認する。

## 親の provisional 裁定 (攻撃対象)

- **(P1-a) 予算値 = 300.0 秒の固定定数。** 実測 (この worktree、login node、load 57〜81、
  10,369 commit / 24,757 tracked file): 単一呼び出しの最大は `rev-list --all --topo-order --reverse` の
  6.954 秒 (4 回で 5.031 / 5.868 / 6.954 / 4.015)、`ls-tree -r -z --full-tree HEAD` 1.653 秒、
  path 限定 `log` 3.185〜3.709 秒、`cat-file blob` 0.440 秒。CPU 時間はいずれも 0.2 秒未満で I/O 待ち支配。
  300.0 は観測最大の約 43 倍で、D265 が ruleops へ定めた「1 回の git 呼び出しの絶対上限 CAP = 300.0 秒」と同じ値。
  観測 regime は login node の load 57〜81 で、適用対象の走行と同じ共有 FS だが load 147 の実測 (worklog 1483) がある。
- **(P1-b) 例外の形** = `subprocess.TimeoutExpired` を捕え `TrialRegistryError("[git-operational] ...")` を送出。
  新しい例外型・retry・部分結果は作らない。D265 の「timeout 以外の validation predicate は変えない」に揃える。
- **(P1-c) 正例・負例** = `_GIT_ENV_ALLOW` に PATH があるので tmp の PATH shim (sleep する偽 git) を使う。
  正例は予算を小さくして超過させ拒否を確認、負例は即座に返す shim と実 repo 呼び出しで通ることを確認。
  注入 seam を先に探し、monkeypatch は最後の手段とする (DW-O14)。

## per-call timeout が保証しないこと (誇張しない)

`_assert_attempt_registry_history` (2600 行台) は `rev-list --all` の 10,369 commit を回し、
各 commit で全 tree の `ls-tree -r` + blob ごとの `cat-file` を行う。1 呼び出しごとの timeout では
この loop 全体の終端は縛れない。**「run_trial の全経路が有界になった」とは書かない。**
縛るのは 1 回の git 呼び出しであり、集約の終端は協調的な `max_wall_s` のままである。

## 成果物と分割

コード 1 file + テスト 1 file の同一 commit、変異事前登録と matrix、焦点走、受入全走、
worklog / decisions fragment。受理集合が変わる (新しい拒否が増える) ので DW-C00 により敵対検証子を省かない。
段 2 plan 1 本、段 3 consult 2 本 (sol / luna)、段 5 実装子 1 本、段 6 review 2 本。
