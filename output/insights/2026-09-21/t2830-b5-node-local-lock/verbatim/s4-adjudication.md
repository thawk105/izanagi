# [T-2830] 段 4 裁定 + プラン v2 + 変異事前登録 (2026-09-21、base d99c556df)

入力: `brief.md` (追補 2 まで)、`codex/s2-plan.md`、`codex/s3-consult-A.md` (正しさ境界)、`codex/s3-consult-B.md` (過剰・削除)。
段 4 直前の裁定 inbox 再走査: D2200 項 1 (09:10 land) が T-2830 の範囲と「job ごとに submit-tree を分ける」を確定 (brief 追補 2)。

## 所見の裁定

| # | 所見 | 判定 | 採否・処置 |
|---|---|---|---|
| A1 | B-5 分岐内の export で B-5 の全 bench lock 取得を覆うか | refuted | slot 起動は `env={**os.environ,...}` で継承 (`b5_generator_contrast.py`)、fanout 上書きは `BACKOFF_REPRO` 限定で B-5 は通らない |
| A2 | 規律 2 | refuted | verify pass の critical section・判定手順に触れない |
| A3 | job 固有 lock は同一ノードの別 process と排他しない (machine-wide 排他からの縮小)。probe は原子的な代替保証でない | real (記述) | コード不変。insight・README の B-5 lock 行に「排他は同一 job 内、ノード単独性は gen_S 割当て前提で専有は保証外 (B-10 / A-5 と同じ)」と限定を書く |
| A3' | 59% は flock 待ちの直接測定でない | real (nit) | insight で「台帳区間とコードからの推定」と書く (D2199 の記述どおり) |
| A4 | 既存 3 経路の argv は完全一致比較済みか | refuted | proposal / fixture (stock 未設定・0)、pair、K2 空白 manifest の 3 test が完全一致 |
| A5 / B2 | `previous_trees` (path 重複・common repo 不一致の拒否) | real (過剰) | **入れない**。依頼の「検査の追加は scope 外」、実測欠陥なし → 裁定パッケージにせず insight に記録 (DW-S04) |
| A6 | D2205 の維持 | refuted | pair・認可 session・結合検査に触れない |
| A7 | 変異の帰属 (メタ test を kill に数えない、cwd 変異は rc=0 ケースでだけ検出、export 脱落は入力に lock が無いときだけ検出) | real (nit) | 変異登録に反映 (下記) |
| B1 | (P2) の根拠「lock 変更で build の同時性が上がる」 | real (brief の誤り) | 根拠を差し替え: **D2200 項 1 (6) の確定裁定** + 既存の共有 cache の claim が待機・retry なしで失敗する機序 (`buildcache.py` `_acquire_v2_claim`、cache root は submit-tree 内)。job ごとの tree は残す |
| B3 | NUL 区切り bytes の別 file 記録 | real (冗長) | 入れない。既存の argv 完全一致比較を「既存 3 経路の argv 固定」の証拠にする |
| B4 | 継承値専用 test | real (冗長) | 入れない。harness で外部の `IZANAGI_BENCH_LOCK` を除去し、既存 test に観測を足すだけ |
| B5 | `launch` に git 検証を移す | real (責務移設) | 入れない。`launch(jobs, trees_by_arm, *, submit, runner=None)`、検証は呼出し側 (`main`) が既存 `validate_submit_tree` + `replace` で行う |
| B5' | README の実行例が単一 `--repo-root` | real | 親が README の現行例だけ更新 (過去の submit_pilot 記録は変えない) |
| B6 | lock literal の新しい静的 pin・順序 assertion | real (冗長) | 入れない (`B5_PINS` と stage order marker は変更しない)。挙動観測で固定 |
| B6' | 「本走全体が投入可能」と書かない (launcher は試走形 write-heavy / series 1 / block 1 に固定) | real | insight・worklog の完了表現を「本走前に要る lock と tree 配置の実装」に限る |

**(P1) 確定:** B-5 mode 限定 (B-5 分岐内、driver 起動直前)。両レンズとも支持。
**(P2) 確定 (ユーザー裁定):** job ごとの submit-tree。**(P3) 確定:** 親 (呼出し側) が 4 本を用意・検証し、launcher は arm→tree の対応だけを配線する。

## プラン v2 (実装子への指示の正本)

### A1 — job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) と `orchestrator/tests/test_p3_s4_loop_job_contract.py`

1. job body: B-5 分岐内の `b5_rc=0` と B-5 driver 起動行の間に 1 行 `  export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を足す。
   他の行は変えない (非 B-5 経路・prebuild・trap・`B5_PINS` / `STOCK_PINS` 対象の literal はすべて不変)。
2. test harness `_run_actual_job_body_through_driver`: harness の環境から `IZANAGI_BENCH_LOCK` を除去する。fake driver (`python3.10` stub の `-m` 分岐)
   が driver 起動ごとに `{"TMPDIR": ..., "IZANAGI_BENCH_LOCK": <値 or null>}` を別 file (例: harness が env で渡す path、JSON lines) に追記する。
   **harness の戻り値の形 (3 要素) と既存の driver-evidence の辞書比較は変えない。**
3. 既存 test へ観測を足す:
   - B-5 の実 shell test (`test_b5_actual_shell_one_driver_and_trap_rc` 等、B-5 driver を実際に通る test): driver が観測した `IZANAGI_BENCH_LOCK` が
     `<scratch-base>/<pbs_jobid_path_component>/bench.lock` と完全一致し、`TMPDIR` がその親と一致する (期待値は job body の path 規則から独立に組む)。
   - 非 B-5 の `test_default_job_invokes_driver_once` (proposal / fixture、stock 未設定・0) と `test_pair_job_invokes_one_driver_with_both_modes`:
     driver が観測した `IZANAGI_BENCH_LOCK` が null (未設定)。
4. 新しい静的 pin・継承値 test・NUL bytes 記録は足さない。

### A2 — launcher (`tools/pegasus/b5_contrast_launch.py`) と `orchestrator/tests/test_b5_contrast_launch.py`

1. `launch(jobs, trees_by_arm, *, submit, runner=None)`: `trees_by_arm` は arm → 検証済み `SubmitTree`。各 job で `tree = trees_by_arm[job.arm]` を
   `build_job_environment` と `runner(argv, cwd=tree.repo)` の**両方**に使う (command ごとに tree を保持)。検証 (`validate_pilot_cap`・全 job の env / argv 組立て・
   freshness) を最初の mkdir / runner より前に終える既存の順序は維持。`SubmitTree` / `validate_submit_tree` / `pilot_jobs` / `build_job_environment` /
   `qsub_argv` / `_qsub_argv` は変更しない。
2. `main`: `--repo-root` を `--repo-root-random` / `--repo-root-sweep-matched` / `--repo-root-llm` / `--repo-root-stock` の 4 必須引数へ置換。
   共通の `--expected-head` で各 path を `PILOT_ARMS` 順に既存 `validate_submit_tree` → `replace(..., thirdparty_source_root=...)` し、mapping を `launch` に渡す。
   単一 `--repo-root` の fallback・互換層は作らない。path 重複・common repo の比較は**足さない**。
3. docstring (module 冒頭) を「4 job をそれぞれ専用の clean checkout から投入する」に合わせる。
4. test: `_pilot` fixture と `_expected_environment` を arm ごとの tree (`submit-tree-<arm>`) に対応。qsub argv exact test は各 job を自分の tree で比較。
   submit test の fake runner は `(argv, cwd)` を記録し、**rc=0 のケースで**全 4 件の cwd が各 arm の tree であることを検査 (rc 非零で後続を呼ばない既存検査は維持)。
   main の dry-run test は 4 CLI 引数を渡し、validator spy が `PILOT_ARMS` 順に 4 回・共通 HEAD で呼ばれ、出力 4 件の `IZANAGI_S4_REPO_ROOT` が各 arm の tree であることを検査。
   既存の validator 単体 test (単一 tree fixture) はそのまま。

### 親 (docs)
- `tools/pegasus/README.md` の B-5 launcher 実行例を 4 引数へ更新し、B-5 mode の lock 行と A3 の限定を 1〜2 行で書く (README を読む test を焦点走に含める)。

## 変異事前登録 (DW-M01、実装前。期待 node の完全集合は実装後に login self-run で観測して確定する — DW-M08)

| id | 位置 | 変異 | kill を期待する test (単一理由) |
|---|---|---|---|
| M1 | job body B-5 分岐 | 追加した export 行を削除 | B-5 実 shell test の lock 観測 (harness が外部値を除去するので null になる)。`test_b5_fragment_mutants_have_one_static_failure` 等のメタ test は kill に数えない (A7) |
| M2 | 同 | 値を `"$HOME/.izanagi/bench.lock"` | B-5 lock path 完全一致 |
| M3 | 同 | export を `export TMPDIR=$scratch` の直後 (job 全体) へ移動 | 非 B-5 (default / pair) の lock 不在観測。B-5 側は緑のまま |
| M4 | 同 | `export` を外し shell 変数代入だけにする | B-5 lock 観測 (null) |
| M5 | launcher `launch` | env 側の tree 参照を `trees_by_arm["random"]` 固定にする | qsub argv / env exact (random 以外 3 件) と dry-run 出力の repo root |
| M6 | launcher `launch` | runner の `cwd` を先頭 arm の tree 固定にする (env は正しいまま) | submit test (rc=0 ケース) の cwd 照合 |
| M7 | job body 非 B-5 | `pair_argv=(--stock-control)` を空配列 | 既存 `test_pair_job_invokes_one_driver_with_both_modes` の argv 完全一致 (既存 3 経路の固定の実証) |
| M8 | job body 非 B-5 | fixture 既定 `${IZANAGI_S4_FIXTURE_VALUE:-20}` を `:-21` | 既存 `test_default_job_invokes_driver_once[fixture…]` の argv 完全一致 |
| M9 | job body 非 B-5 | proposal 経路の `--isolate-worktree` を削除 | 既存 `test_default_job_invokes_driver_once[proposal…]` と pair test の argv 完全一致 (proposal 行は pair と共有) |

各変異は実装後に「同じ入力を拒否する層が前後・内側に無く赤理由が 1 つ」かを確認し、できなければ登録から外して再照準する (F820 / F28)。
M3 は B-5 側が緑、非 B-5 側だけ赤になることで単一理由を示す。M9 は proposal / pair の両 test に効く (同一行を共有) — 期待 node は両方を含む完全集合で登録する。

## scope 外の記録 (起票しない、insight に書く)
- launcher 自身による path 重複の拒否 (同じ path を 4 回渡すと共有 cache に戻る) — 実測欠陥なし、依頼が検査の追加を除外。
- 本走 (108 系列) 用 launcher への一般化 — 現 launcher は試走形に固定。D2200 項 1 の他の AI 手番 (全 arm 同一 walltime、Tier0、§12) も別手番。
