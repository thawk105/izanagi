# 段 1 brief — [T-2228] screening 関門の生死確認 (正規入口 CLI から最小 screening を計算ノードで 1 走)

wave `dev-wave-t2228-screening-liveness` / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness` / 基点 main `1042a1bc95057fa03117d504cfa2b0fafaae60d0` / job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/`

## 研究前進 (1 行)
`backoff_sweep` (P2 case study、paper-story backoff の材料 driver) は 2026-09-01 の関門義務化以降、screening 段の関門 (`screening_driver._run_condition_gate_for_genome`) が `preprocess-failed` で赤のまま新しい値を 1 つも産めない (一次資料 §2)。D1784 で供給を入れたが「緑になった」とは名乗っていない。**完了判定: 現行の正規入口 (CLI `main`) から `--screening --screening-fixed-us 2` の最小 screening を計算ノードで走らせ、baseline (BACK_OFF=0 / BACKOFF_FIXED=-1 inert、stock 比較あり) が関門を通過した後にしか書けない WAL record (`bench-done` → `commit`) を official output root に得る。** これで T-2228 の残りが閉じ、sweep driver で新規測定を再開できる。

## scope
- **本題の 1 走だけ**: workload `write-heavy`、`--screening --screening-fixed-us 2` (baseline + fixed=2 の 2 genome)。全点 sweep・他 workload・`backoff_repro` / `s1` へ広げない。
- **実装差分は既定ゼロ**: repo へ入るのは `output/insights/2026-09-17/t2228-screening-gate-liveness/` (README + evidence の写し) と spool fragment (worklog / decisions) だけ。production 4 file の sha256 を実測時点で記録する。
- 赤なら止まった段 (driver 段関門 / screening 関門 / build / bench / attestation / infra) と reason code を一次資料 (`2026-09-07_t2228-driver-gate-liveness/README.md` §1) と同じ粒度で記録し、直す場合は Codex author (D95)。直さない赤も成果物にする。
- 仮想リスク向けの gate・検査・台帳・一般化 (例: arm record の永続化を backoff_sweep へ横展開) は scope 外。所見として記録するだけ。

## 確定済みユーザー裁定・依頼の制約
- D1733: 供給は screening 関門 1 箇所だけ。`backoff_repro` / `s1_direct_comparison`、pin 整合、freeze 再生成に触れない。
- D1784: 発火条件は `expected_toolchain_manifest is not None` (経路の代理)。本 wave まで「緑」と名乗らない。D1666: 実装 wave と実測 wave を分ける先例。D1785: prebuild の非対称は帰属しない。
- 依頼文: 着手直前の local main から fresh worktree (済: `1042a1bc9`)、計算ノードの単独性を確認してから投入、規律 2 を緩めない、scope 外の追加なし。
- D1912: `backoff_sweep` 系は関門の arm record を「作って捨てる」(evaluate_candidate が戻り値を捨て、赤は try/except の外で例外)。緑の直接 record は production 経路に無い。

## 不変条件
- production 無編集 (`backoff_sweep.py` / `screening_driver.py` / `condition_meaning_gate.py` / `buildcache.py` / `dispatch_compute.py`)。関門の判定式・受理集合に触れない。
- CCBench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` (worktree の submodule と一致、実測済み)。
- official output root は repo 外 (job dir 配下)、投入中の worktree へは `output/` 配下 (dispatch の request dir と buildcache の `external/ccbench/build-variants`) 以外を書かない。
- 待ち手は 1 条件 1 本 (`DW-C00`)。計測は増やさない。

## 段 1 で実測した前提 (模擬でなく実)
1. CLI: `python3 -I -B orchestrator/campaign/backoff_sweep.py write-heavy --screening --screening-fixed-us 2` (file 直起動の bootstrap あり、`main` → `run_workload` の薄い入口)。
2. A-5 job body (`tools/pegasus/a5_second_boot_backoff_sweep.sh`) は `--screening` を渡さず finalize が全 genome を前提 → 実装差分なしでは最小 screening を A-5 経由で走らせられない。
3. generic dispatch (`tools/pegasus/dispatch_compute.py --task generic`): clean env (HOME/LANG/LC_*/LOGNAME/PATH/TZ/USER)、cwd = 投入元 worktree、read-only は `output/pegasus-dispatch/<nonce>/` だけ、argv 規約は先頭非空のみ、job_run に clean-tree 検査なし、interpreter は python3.10 を PATH 先頭に置く。
4. CLI が環境に要求するもの (A-5 が export しているもの): `IZANAGI_OFFICIAL_OUTPUT_ROOT` (必須、repo 外・`.git` 祖先なし)、`CMAKE_PREFIX_PATH` (gflags/glog; buildcache は ambient を読み receipt の prefix roots に記録)、`http_proxy`/`https_proxy=http://10.120.96.1:8080` (FetchContent が masstree/mimalloc/googletest を GitHub から取る; 計算ノードは直の名前解決不可、proxy 経由は A-5/B-10 が実走)、`TMPDIR` (未設定なら /tmp; A-5 は /scr、/scr は job 終了時削除)、`IZANAGI_BENCH_LOCK` (既定 `~/.izanagi/bench.lock`)。
5. gflags/glog pin = v2.2.2 / v0.5.0。既存 prefix `/work/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install` (2026-08-25 作成、静的 lib あり) は同版。T-2213 / T-2630 で configure + preprocess に使用、link までの先例は repo 内に見つからず。
6. between-run floor (`between_run_noise_t48_skew0p9_rr5_rmw0.json`) tracked。較正は Pegasus contract の required attestation を `run_workload` が通す (前回 probe が同経路で driver 段まで到達済み)。
7. 関門 request: baseline → `[('BACKOFF_FIXED', -1, stock_comparison=True)]`、候補 → `[('BACKOFF_FIXED', 2, False)]` (login で純関数を実測)。関門は evaluate の前に無条件で走り、赤は process を止める。
8. 単独性: gen_S は `Exclusive submit = OFF` (runbook §1)。確認は割当ノード上で行う — production の `run_workload` 冒頭 `_assert_single_tenant()` (競合 ccbench bench の pgrep、検出時は PID を出して停止) が job 内で走る。queue は 00:33 JST で gen_S 18 RUN / 0 QUE。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- **(P1) 投入形**: generic dispatch + `/usr/bin/env <VAR=…> python3 -I -B orchestrator/campaign/backoff_sweep.py write-heavy --screening --screening-fixed-us 2`。script ゼロ・実装差分ゼロ。これを「現行の正規入口 (CLI) + tools/pegasus の投入 tool」と読む。対案: A-5 へ screening option を足す (実装差分、Codex author、sha 束縛の再計算、finalize 改修) / job dir の launcher script (Codex author、A-5 の env 段を写す)。
- **(P2) 緑 record の定義**: 関門の arm record は production が捨てるので、緑の record = 関門の直後にしか到達しない baseline の WAL `bench-done`/`commit` + process rc=0 + stdout。間接証拠であることを README に明記し、「関門が走った」ことは build/bench の前に `_require_condition_gate_before_evaluation` が無条件に呼ばれる構造 (前提 7) で支える。
- **(P3) gflags/glog**: 既存 prefix を `CMAKE_PREFIX_PATH` で渡す (A-5 は job 内で hydrate 済み source から build)。link 失敗なら build 段の infra 赤として記録。
- **(P4) TMPDIR**: `/scr` を直に指す (job 終了時に削除)。対案: 既定 /tmp。
- **(P5) walltime**: 01:30:00 (関門 ×2 各 ≤ 2 分 + build ×2 各 ≤ 5 分 + bench + legacy correctness)。`--queue-wait-timeout 3600 --overall-grace 3600`。

## 成果物の形
- `output/insights/2026-09-17/t2228-screening-gate-liveness/README.md` (要点 / 実行 identity / 段別結果 / 緑の意味の限定 / 限界 / scope 外所見)、`evidence/` に dispatch receipt・job stdout の写し・WAL 抜粋・production sha256。
- spool: worklog fragment 1、decisions fragment (緑 record の定義と限界を D として残す)。
- 変異 matrix: 実装面差分ゼロにつき免除。焦点走: 変更 file なし → 受入全走のみ。

## 並列分割方針
- 段 2 plan 1 本 (read-only codex): 投入 argv の exact 形・env 値・walltime・赤の分類表・README 骨格を file:line で起草。
- 段 3 consult 2 本 (並列、別レンズ): A = 正規入口・環境等価性 (P1/P3/P4、A-5 との差が結果の意味を変えるか)、B = 証拠の恒真性 (P2、関門を経ずに緑に見える経路が無いか、規律 2 / 7)。
- 段 5/6 は実装差分ゼロなら省略 (`4→7→8→9`)。赤で直す場合のみ Codex author。
