単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage4-ruling.md — **段 4 裁定とプラン v2 の差分 (本作業の正本)。plan と食い違う箇所はこちらが優先**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md — 段 2 プラン (§1〜5・§7・§8・§9 のうち side channel 側が本作業。§6 と caller の test は別の実装子が担当)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage1-brief.md — 親 brief (不変条件・P1〜P7)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md — 裁定の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-reference.md — 凍結事前登録の共通参照点 (定義文の整合先)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s3-consult-A.md — 段 3 相談 A (must-fix の背景)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop.py — **所有 file 1 (編集対象)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py — **所有 file 2 (編集対象)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop_trigger_gating.py — 先例 (読むだけ、編集しない)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/agent_outputs.py — `canonical_sha256` (読むだけ)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/wal.py — `read_records` (読むだけ)。読めなければ即停止

## 作業 (プラン v2 の side channel 側)

所有 2 file だけを編集し、次を実装する。

1. base 専用の provenance report (`<campaign root>/reports/p3_s4_loop_provenance.json`) の loader / writer / merge / attempt 抽出 helper (plan §1・§4、裁定 §3.1)。
   先例 `p3_s4_loop_trigger_gating` は import しない。trigger 固有の header (情報源・firewall・gate record) は写さない。
2. `drive_iteration` での公開位置 (評価・whiteboard 射影の後、`save_loop_state` の前、B-5 早期 return より前。plan §2)。
3. **評価前の検証 (裁定 §3.2):** layout が決まった直後、B-4 認可の検査・消費と評価より前に既存 report を読み検証する (書かない)。
   破損なら退避して停止し、評価も認可消費もしない。入口停止の経路でも report を新設しない。
4. proposal の canonical hash の配管 (plan §3): `load_proposal_file` の capture に検証済み document を足し、`main()` の `--run-iteration` 経路で
   capture から `canonical_b4_proposal_sha256` を計算して `drive_iteration` の keyword-only 引数 (既定 None) へ渡す。
5. P4 の保証の限定と、参照点の定義文 (plan §5、裁定 §3.1) を helper の docstring に書く。「回復可能」「対応を失わない」とは書かない。
   中断後の経路別帰結 (非 B-4 certified → duplicate になり得る / 検疫 reject → 新 attempt で entry 上書き、旧 attempt は WAL にだけ残る /
   B-4 → 再実行拒否、公開済み entry が残る) を書く。
6. test (plan §7 のうち side channel 側と、裁定 §3.3 の変更): 裁定 §3.3 が「作らない」とした `test_pair_candidate_has_one_provenance_entry` は作らない。
   `test_base_provenance_inputs_do_not_read_report` を足す。duplicate の fixture は採用 commit と最新 start の attempt が異なる形にする。
   失敗 test は 2 回目の呼び出しまで検査する。破損 test は評価未呼出し (と B-4 mode なら認可未消費) を assert する。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/` 配下、`docs/handoff/`)。所有 2 file 以外の file を作成・編集しない。sort / trigger driver、`artifact_admission.py`、
  凍結事前登録、`p3_b4_prerun_caller.py` とその test には触れない。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、test file の自走 harness のいずれも使わない)。親が計算ノードで焦点走を行う。
  報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile` の 2 file) は行ってよい。
- `p3_s4_loop.py` は contract loader closure と B-4 projection closure に入る。未 commit の bytes で v2 campaign lock を作る test は、内容と無関係に
  contract-loader drift で落ちる。**drift を避けるために binding 検査を緩めたり、test fixture に現行 hash を差し込んだりしない。**
  新 test は、できる限り v2 lock を作らない小さい fixture (helper 単体・drive の既存 fixture) で組む。v2 lock が要る fixture は binding を module 単位で 1 回だけ作る。
- 新設・改名した test が既存の制約 meta-test に触れないかを**自分で洗い出して静的に確認する** (親の名指しを網羅と見なさない)。
  少なくとも: `test_p3_exploration_namespace.py` の `p3_s4_loop` DriverContract (`ast_layout_calls` / `ast_run_campaign_calls`)、
  `test_campaign.py` の certified-writer 目録、`test_p3_b4_wiring_probe.py` の static 数・inventory、`test_official_perf_closure.py` の perf 面目録、
  `test_p3_s4_loop.py` 内の AST 隔離検査 (`_assert_agent_input_ast_isolated`) と既存 capture test (`test_agent_loader_capture_only_after_validation`)。他にもあれば挙げる。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値 (tree hash・時刻・乱数 attempt ID) を焼き込まない —
  attempt ID は WAL から読んで比較する。機構の正例・負例は実体 (`drive_iteration`、実 writer) を通し、依存先を stub しない (評価本体の stub は既存 fixture の定型に限る)。
- 指示外の受理集合を変えない。certified / reject / abort の判定、whiteboard の 5 field、planner 射影、critic digest の内容を変えない。規律 2 を緩めない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の挙動 (drive_iteration の書き順、capture の条件、report が存在しないこと)
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と、それぞれが今回の変更で影響を受けるか (受けるなら更新が要るか、要るならなぜ所有外か)
5. 所有外の caller・共有 fixture・consumer test への波及の静的列挙 (sort / trigger の `drive_iteration`、`b5_generator_contrast`、pair CLI の fixture など)
6. 未実走であることの明記と、親が走らせるべき nodeid の候補 (新設 test の完全な nodeid)
7. 裁定 §4 の変異 S1〜S14・E1 について、実装後の位置 (関数名・一行) と、同じ入力を拒否する層が前後・内側に無いかの自己点検
最後に `## 総括` を置く。
