単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s4-adjudication.md — **段 4 裁定とプラン v2 (本作業の正本)。D-1・D-2・D-7・「plan v2」・「変異事前登録」の MA1〜MA16 と M0 に従う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/brief.md — 親 brief (不変条件)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s2-plan.md — 段 2 プラン (参考。§1 が本単位。v2 と食い違う箇所は v2 が優先。§1.1 の registered 探索系列への block 算式の検査は v2 で削除、§4 の配置は v2 の D-2 に差し替え)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s3-consult-A.md と s3-consult-B.md — 段 3 相談 (参考)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/campaign/b5_generator_contrast.py — 所有 file (driver)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/tools/pegasus/b5_contrast_launch.py — 所有 file (launcher)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/tools/pegasus/p3_s4_loop_pegasus.sh — 所有 file (job body、B-5 分岐だけを触る)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/tools/pegasus/admission_registry.json — 所有 file (launcher の `reason` 文字列だけを更新)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/tests/test_b5_contrast_launch.py、test_b5_generator_contrast.py、test_p3_s4_loop_job_contract.py、test_ccbench_spawn_sites.py — 所有 file (test)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/campaign/b5_generator_contrast_report.py — 参照のみ (registered の受理条件 `_validate`・`build_report`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/docs/pegasus-runbook.md — 参照のみ (launcher 分類表。class・evidence を変えないこと)。読めなければ即停止

## 作業 (プラン v2 の実装単位 A)

**編集してよい file は次の 8 つだけ:** `orchestrator/campaign/b5_generator_contrast.py`、`tools/pegasus/b5_contrast_launch.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、
`tools/pegasus/admission_registry.json` (launcher の `reason` 文字列だけ)、`orchestrator/tests/test_b5_contrast_launch.py`、`orchestrator/tests/test_b5_generator_contrast.py`、
`orchestrator/tests/test_p3_s4_loop_job_contract.py`、`orchestrator/tests/test_ccbench_spawn_sites.py` (launcher に新しい process 起動箇所を足した場合の目録更新だけ。既存の `launch` の runner 経路を再利用して起動箇所を増やさないなら編集しない)。

**着手前に次の現行挙動を読んで報告に明記する:** (a) driver `_header` が書く cohort / purpose / limits と、`run_series` / `run_block_stock` / `main` の引数。(b) job body の B-5 env 検証
(必須 env 配列、mode が無いのに B-5 env がある場合の拒否) と driver argv の組立て。(c) launcher の pilot 経路 (`_validate_job`・`validate_pilot_cap`・`build_job_environment`・
`_qsub_argv` の walltime literal・`launch` の検査順)。(d) report の `_validate` が registered の header に要求する条件。

実装内容 (食い違えば s4-adjudication.md が正本):

1. **driver:** `COHORT_REGISTERED = "b5-registered-v1"` を足す。`run-series` / `run-block-stock` に `--purpose {pilot,registered}` (既定 pilot) を足し、`run_series` / `run_block_stock` / `_header` に
   keyword-only `purpose="pilot"` を通す。pilot の header は既存と同じ key・同じ値 (cohort `t2797-beta-v1`、purpose `pilot`、limits の 2 文を文字単位で保持)。registered のときだけ cohort /
   purpose と limits の第 2 文を変える (例 `"Registered producer; cohort activation and actual execution order require external approval and evidence."`)。**registered 探索系列に
   `block == (series-1)//4+1` の拒否を足さない** (v2 で削除)。module docstring を両 purpose の producer の説明にし、「registered を出力できることは発効・投入認可を意味しない」と書く。
   A/B 消費点・生成器・handshake・endpoint・分類は触らない。
2. **job body:** `IZANAGI_S4_B5_PURPOSE` は任意。未設定は pilot。設定済みなら `pilot|registered` だけを受け、空文字・未知値は既存の `refuse` で拒否する。B-5 mode が無いのに purpose だけある場合も
   既存の「B-5 env は mode を要する」検査に含める。**既存の必須 env 配列には足さない** (pilot が壊れる)。`registered` のときだけ `b5_argv+=(--purpose registered)`。未設定・明示 pilot は argv を増やさない。
   非 B-5 の既存 3 経路・K2 の受渡し・node-local lock・終了コード伝播は変えない。
3. **launcher:** pilot の既存関数・CLI は変えない (旧 CLI は先頭が新 subcommand の語でないとき従来 parser へ)。registered 用に次を足す (名前は目安):
   - `registered_schedule()` — 純粋・決定論的。s4-adjudication.md D-2 の逆順組配置 (組 A = {LRS, SRL}、B = {LSR, RSL}、C = {RLS, SLR}、除く組 e = (w + b − 1) mod 3、残る 2 組を昇順に X・Y、
     block 内 j = 1..4 に X 第 1・Y 第 1・X 第 2・Y 第 2) で 108 系列の (workload, series, block, 順序) と、117 job (探索 108 + block-stock 9) の (block, stage) 配置を返す。
     block-stock は各 block の stage 2、header 座標は series = block。
   - `registered_walltimes(k)` — `k` を文字列から `Decimal` で読み、有限な `0 < k ≤ 4.06` を要求、W = ceil(21259 × k)、W_stock = ceil(5447 × k) を秒と `HH:MM:SS` (24 時間で wrap しない) で返す。
   - registered job の env / argv 組立て (job ごとの submit-tree を `job id → 絶対 path` の map で受け、各 tree に既存 `validate_submit_tree` を通す。選んだ job 間で tree は distinct。
     ledger / evidence root は `<root>/b5-registered-v1/block-<b>/<workload>/r<NN>/<arm>/` と `<root>/b5-registered-v1/block-<b>/<workload>/block-stock/`、全 tree・common repo の外。
     K2 の 4 env は llm job だけ。`IZANAGI_S4_B5_PURPOSE=registered` を明示)。既存の freshness・出力分離の検査を registered にも適用する。**新しい承認 gate・schedule の runtime 検査は足さない。**
   - CLI: `registered-schedule` (schedule を JSON で標準出力) と `registered --block B --stage S --walltime-factor K --submit-trees MAP.json --expected-head FULL_OID --ledger-root ABS
     --evidence-root ABS --thirdparty-source-root ABS --knowledge-manifest ABS --knowledge-classification C --knowledge-de-novo-claim {true,false} (--dry-run | --submit)`。
     dry-run は env・argv・cwd・job id を出力し mkdir / qsub をしない。submit は選んだ stage 全件の構築と検査を終えてから投入し、途中失敗はその場で返す (retry・stage の自動進行なし)。
   - pilot の walltime literal `08:00:00` / `03:00:00` は変えない。
4. **登録簿:** `tools/pegasus/admission_registry.json` の launcher の `reason` を pilot と registered の両方を投入する login 側 submitter の説明に更新する。class・primary_gate・evidence は変えない
   (runbook の投影表を変えないため)。
5. **test:** s4-adjudication.md の MA1〜MA16 の各変異が、名指しした test node (その名前で作る) で**変更箇所を実際に通って**落ちるように書く。特に:
   MA1 は report の `build_report(..., purpose="registered")` を実物で呼び invalid と purpose 分岐を確かめる (「例外が出ない」では足りない)。MA10 は積が非整数になる k (例 2.5) で ceil と floor を区別する。
   MA6 / MA7 は schedule の性質 (各 (block, stage) の LLM 数 = 4、各 workload で 6 順序 × 2、各 (w, b) で LLM と各 baseline の先後が 2 対ずつ) を schedule 関数の出力から独立に数える
   (期待値を同じ算式で再計算しない。性質の数え上げで検査する)。MA3 は pilot header の bytes を同じ HEAD・host・環境・deadline に固定した比較で確かめる。job body の test は既存の実 shell 呼出し fixture を使う。
   既存 test の期待値は変えない (pilot 経路は不変のはず)。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/` 配下、`output/`、`tools/pegasus/README.md` を含む)。所有 8 file 以外の file を作成・編集しない。report (`b5_generator_contrast_report.py`)・子 (`p3_s4_loop.py`)・
  pipeline・事前登録・`.claude/agents/*` は編集しない。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、`pytest.main` の埋め込み、test file の自走 harness のいずれも使わない)。親が計算ノードで焦点走を行う。報告は「実装済み・未実走」と書く。
  静的検査 (`python3 -m py_compile <file>`、`bash -n <file>`) は行ってよい。
- 追加した関数・CLI・env が既存の制約 meta-test に触れないかを**自分で洗い出して静的に確認する** (親の名指しを網羅と見なさない)。少なくとも: `test_ccbench_spawn_sites.py` の process 起動目録、
  job body の env / argv 契約 test (`test_p3_s4_loop_job_contract.py` の既存 B-5 test と非 B-5 経路の bytes 不変 test)、admission registry と runbook 投影表の整合 test、
  test file の自走入口 (`test_plain_runner_coverage.py`)、login 側 tool の資源・起動規約 test。
- 機構の正例・負例は実体を名指しし、依存先を stub しない (report・`validate_submit_tree`・schedule 関数・walltime 関数そのものは stub しない。qsub は既存 test と同じ runner 注入で代える)。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値 (tree hash・時刻・path 名の hash) を焼き込まない。
- 指示外の受理集合を変えない (pilot の argv・env・header、非 B-5 経路を 1 byte も変えない)。規律 2 を緩めない (verify legacy 1 + 動作点 trace 5、anomaly 即 reject の経路に触れない)。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 着手前の現行挙動 (上記 (a)〜(d))
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と、それぞれが変更で影響を受けるか (受けるならどう対応したか)
5. 変異 MA1〜MA16 と、それぞれを落とすはずの test node 名 (変更箇所を通る根拠)
6. 所有外の caller・共有 fixture・consumer test への波及の静的列挙
7. 未実走であることの明記と、親が走らせるべき nodeid / file の候補
最後に `## 総括` を置く。
