# 段 1 brief — [T-360] 変異本走 transport を投入表の task として実装する

wave: dev-wave-t360-mutation-transport-task
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task
base main: 53c61414

## scope (確定済みユーザー裁定 = D842)

1. `tools/pegasus/dispatch_compute.py` の `TASKS` へ `mutation` task を足し、変異本走を
   計算ノードの 1 ジョブへ束ねる。専用の投入 script は不採用 (環境正規化の手写しを作らない)。
2. 同じ wave で「任意コマンドを計算ノードへ送る汎用 task が無い」を扱う。分けると 2 度設計になる。
3. D105 決定 3 (task enum を {tests, provenance} に固定) を supersede する。
4. D117 決定 4 の 4 契約を同時に満たす: (a) D105 supersede、(b) `_job_run` 側の
   `env_allowlist` 強制、(c) stdin / cwd / artifact 可視性、(d) 子 rc の意味の確定。

## 親の実測 (子はこれを裁定根拠にせず、自分で確かめてよい)

- **M1. `--runner-mode dispatch` は収集段だけ実在する。** `mutation_harness.py:1386-1397` が
  `dispatch_compute.py --task tests -- ... --collect-only` を組み立てる。一方**本走**は
  `mutation_harness.py:1871` の `subprocess.Popen(list(command))` で runner argv を直接起動し、
  その `command` は `_runner_identity` (`:786-794`) が `tools/run_tests.py` に限定している。
  ログインノードでは `run_tests.py` が自己 dispatch する (D103 決定 2) ので、
  **変異 1 件につき PBS job が 1 本立つ。** T-360 が束ねたいのはここである。
- **M2. `env_allowlist` の子側強制は実質存在しない。** `_job_run` (`:709-715`) は
  `child_env.update(requested_env)` で request の environment を無条件に適用し、
  allowlist と照合するのは `_TASK_RUN_SIDECAR_ENV` / `_TASK_RUN_AUTO_RECORD_ENV` の
  2 名だけである。親側 (`:2489-2492`) は allowlist で射影するので実運用では通るが、
  `task` にある二層 fail-closed が `environment` には無い。D117 (b) の指摘は今も生きている。
- **M3. 汎用 task と D103 決定 5 の関係は D105 の記述より狭い。** D103 決定 5 が退けたのは
  **hook の sanctioned path 列挙へ `tools/pegasus/*` の glob を許すこと**であり、理由は
  `exec_calibrate.py` が任意 argv を `os.execv` するからである。汎用 task はこれと同一ではないが、
  hook が sanctioned にしている `dispatch_compute.py` 経由で任意コマンドが計算ノードへ通るため、
  **同じ穴を別経路で開ける**。ここが本 wave 唯一の割れる設計択一である。
- **M4. drift 検査が実在する。** `check_docs.py:3292-3410` が dispatcher source を実行せず
  `TASKS[*].child_script` を AST 抽出し、`docs/pegasus-runbook.md:588` の exact task 表と
  `{task: child_script}` 写像として比較する。task 追加は同じ変更単位で runbook 表の更新を要する。
  `TASKS` の定義後書き込み・alias 再束縛も赤になる (D117 決定 6)。
- **M5. 凍結 bytes の pin は無い。** `tools/pegasus/admission_registry.json` の
  `dispatch_compute.py` 項は class/reason/gate/evidence だけで、sha 固定を持たない。
  `mutation_harness.py:803-814` は dispatch entrypoint を **live HEAD blob** と照合するので、
  変更後も HEAD 追随で整合する。凍結成果物の bytes は動かない (DW-O09/O10 不発火)。
- **M6. D131 前提 6 点の現状 (子は裏取りせよ)。** #6 の後半 (走行中 job への qdel 禁止) は
  `_fresh_qstat_gated_qdel` / `_QDEL_CLEANUP_POLICY="fresh-qstat-gate/v1"` として実在し、
  前半 (`total_deadline`) は D133 が入れた。#2 の permanent evidence は
  `mutation_fanout.py:604` の `.dispatch-evidence` と wrapper receipt が担う。
  #1 #3 #4 #5 の充足状況は**未確定**であり、plan で file:line で確定させること。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 汎用 task は「呼び手が任意 argv を渡せる」形にしない。** そう作ると
  `dispatch_compute.py` が hook の重量コマンド拒否を無効化する万能 escape hatch になり、
  D103 決定 5 が守った性質を別経路で失う。汎用性は「投入表に entry を足せば通る」側に置き、
  1 回の呼び出しで任意の実行対象を選べる形にしない、というのが親の暫定案である。
  **これが正しいか、代替があるかを攻撃せよ。** 汎用 task を安全に作れないなら、
  「作らない」も裁定の選択肢であり、その場合は D842 の当該部分を裁定へ返す候補になる。
- **(P2) 本走の束ね単位は fanout の shard 1 本 = 1 job とする。** `mutation_fanout.py` が
  既に shard へ割り、shard ごとに wrapper receipt と ledger を持つため、境界がここにある。
  mutation 1 件 = 1 job でも全 shard = 1 job でもない、というのが暫定案である。
- **(P3) M2 の子側強制は本 wave の同じ変更単位で入れる。** D117 (b) が
  `mutation` task 追加の同時条件として明記しているため、分離しない。
- **(P4) 研究状態は不変とする。** certified 選択、proof chain、campaign の受理集合、
  既存凍結 bytes は動かさない。変わるのは開発 harness の実行場所と受理する task 集合だけ。

## 不変条件 (緩めない)

- 変異 harness / runner の契約 (schema `izanagi-dev-wave-mutation-spec/v1`、baseline 緑必須) を
  変えない。transport を差し替えても内側の suite が別物になってはならない。
- 環境正規化を手で写さない。`_job_script` の正規化・interpreter probe・二層 fail-closed・
  receipt / 会計照合を再利用する (D842 の理由そのもの)。
- 閉集合の二層 fail-closed (親と `_job_run` の両方で照合) を弱めない。
- `TASKS` は literal 定義のままにする (M4 の検査が赤になる)。

## 成果物の形

- `TASKS` への `mutation` entry + `docs/pegasus-runbook.md` の exact task 表の行追加
- `_job_run` の `env_allowlist` 全キー強制 (二層 fail-closed の対称化)
- stdin / cwd / artifact 可視性と子 rc の意味を、契約として test で固定する
- 汎用 task: 実装するなら投入表側の一般化として。しないなら裁定パッケージ
- 上記を覆うテスト (`orchestrator/tests/test_pegasus_dispatch_compute.py` 他)

## 成果物影響 (DW-G05)

実装しない場合、変異本走は変異 1 件ごとに PBS job を立て続ける。queue 待ち 6〜86 秒 x 変異件数が
毎 wave の変異 matrix に乗り、長い matrix ほど右打切りされやすくなる。打切りは
worklog の変異 matrix 欄を「SURVIVED 0」でなく未実施にし、dev-wave の記録台帳に欠落を作る。

## 並列分割方針

段 2 プラン 1 本。段 3 敵対相談 2 本 (レンズ A = 正しさ境界と閉集合の穴、レンズ B = 汎用 task の
escape hatch 性と scope 整合)。設計が割れるので軽量版は採らない。
