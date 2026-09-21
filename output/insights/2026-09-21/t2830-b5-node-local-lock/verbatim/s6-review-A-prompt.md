単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/integrate-204eb77e6.diff — **レビュー対象** (統合 commit 204eb77e6 の全差分)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/s4-adjudication.md — 段 4 裁定・プラン v2・変異事前登録 M1〜M9 (実装が従うべき正本)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (追補 2 まで)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s5-author-A1.md — author A1 の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s5-author-A2.md — author A2 の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/focus-f1.log — **親が実走した焦点走の log** (consumer 回帰)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/p3_s4_loop_pegasus.sh — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_b5_contrast_launch.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/README.md — 統合後 (B-5 の節)。読めなければ即停止

## 親が実走したもの (この範囲だけが実測、他は未実走)

- 焦点走 f1 (計算ノード dispatch、request 15058.nqsv、統合 commit 204eb77e6 の木): 12 file — 変更 test 2 本、consumer 6 本
  (`test_hooks.py`、`test_pegasus_tools.py`、`test_pegasus_calibration_workload.py`、`test_check_docs.py`、`test_ccbench_spawn_sites.py`、
  `test_plain_runner_coverage.py`)、inventory 4 群 (`test_campaign.py`、`test_official_perf_closure.py`、`test_p3_exploration_namespace.py`、
  `test_p3_b4_wiring_probe.py`)。**結果: rc=0、2,074 passed / 9 skipped、失敗 0** (log は上記)。
- 統合後の `python3 tools/check_docs.py` = 違反なし、全史 provenance 監査 = rc 0。
- 変更 test 2 本の単独走 f2 は走行中。**変異 matrix (M1〜M9) は未実走。**

## レンズ A: 正しさ・実効性 (敵対レビュー)

実装を守らせず検査する。各項目を real / refuted で判定し、根拠 (file:line) を示す。real には must-fix / nit と、放置時に成果物
(B-5 本走の台帳・score・certified 判定) の値・受理集合・参照がどう変わるかを 1 行で添える。

1. **プラン v2 との一致:** 実装はプラン v2 の A1 / A2 から外れていないか (足りない・余計)。job body の差分は 1 行だけか。
2. **lock path の期待値:** `_assert_b5_driver_history` の期待値 (`scratch-base/<PBS_JOBID の ':' を '_' にした成分>`) は job body の
   `pbs_jobid_path_component` の実際の規則と一致するか。観測値から作られていないか。
3. **観測の汚染:** fake driver の環境記録 file は tmp_path ごとに 1 つ。同じ tmp_path で harness を 2 回以上呼ぶ test、または
   `_assert_b5_driver_history` を harness の複数回実行の後に呼ぶ test があれば、記録が積み上がって誤判定しないか。
   harness の `environment.pop("IZANAGI_BENCH_LOCK", None)` の位置 (k2_environment の更新後) は、観測の独立性を保つか。
4. **既存 3 経路の固定:** proposal 単独 / pair / fixture の argv 完全一致比較と「lock 未設定」の観測は、どの test のどの parametrize で
   覆われているか。覆われない組合せ (例: stock=0 と fixture) はあるか。
5. **launcher:** 各 job の env (`IZANAGI_S4_REPO_ROOT`) と qsub の cwd が同じ tree を指すことを、submit test の runner 内 assert と
   `calls` 比較が本当に検査しているか。`trees_by_arm` に arm が欠けたときの挙動 (KeyError) は fail-closed か、
   それとも main の except 節の外で traceback になるか (投入前に落ちるなら副作用は無いか)。
6. **[恒真ゲート] / [テスト代表性]:** 登録変異 M1〜M9 (s4-adjudication の表) それぞれについて、統合後の test のうちどれが**単一理由で**
   殺すかを静的に示す。殺せない・理由が 2 つ以上ある・メタ test でしか落ちない変異を挙げる。期待 node の完全集合 (nodeid) の候補も書く。
7. **README:** 統合後の README の B-5 節の記述は、コードの実挙動 (4 引数、cwd、lock の設定位置と非 B-5 の不設定、限定) と一致するか。
8. **9 skipped:** focus-f1.log の skip が本 wave の変更 test に由来しないか (由来するなら理由)。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** 実走していない事柄を「確認した」と書かない。
- 新しい gate・検査・台帳の提案は scope 外と明記し、裁定パッケージ候補として分けて返す。
- 予算が尽きそうなら、途中までの結論を出力形式どおりに書いて終える。

## 出力形式

項目 1〜8 を見出しで分け、各項目に判定と根拠。最後に `## 総括` (must-fix の一覧を先頭に)。
