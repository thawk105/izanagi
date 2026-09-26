# 段 4 裁定 — [T-2853] (1') 保全口 inventory に R1 入力一式の残りを足す

- 作成: 2026-09-26 JST。基準 = local main 74e6d2f237d3cf6501731fc9fa06a7ce22d4e07e。brief = 同 dir の s1-brief.md。
- 段 2・3 は軽量版で省いた (brief §分割)。段 4 直前に裁定 inbox (`dev-wave-jobs/rulings-inbox/`) を再走査: 最新は 2026-09-23 で wave 開始後の新着なし。
- (5') の描き直しは段 1 の生死確認で成立 (実装面の差分なし)。本裁定は (1') だけを扱う。

## 1. 親の実測で確かめた前提

- 標準経路の verifier は in-process: `pipeline._execute_verification_repetition` (pipeline.py:493-) が
  `verify_trace_dir_with_capability(trace_dir, expected_commits=trace_result.commit_count_witness, genome, source_evidence, …)` を呼ぶ。
  同関数 (orchestrator/verifier/core.py:380-) は build に束縛した protocol source の snapshot (`source_evidence.proof_source_snapshot`) で `verify_trace_dir` を呼ぶ。
  CLI (orchestrator/verifier/cli.py) は `--protocol` と `--ccbench-root` から snapshot を作って同じ `verify_trace_dir` を呼ぶ。したがって同じ source root を渡した CLI argv は R1 の入口として成り立つ (brief P1 を採用)。
- runner v5 の組 (写し `izanagi-repro-archive/t2853-20260923/data/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py`):
  `verifier_argv` = `[realpath(sys.executable), '-B', '-m', 'orchestrator.verifier', <trace>, '--json', '--expected-commits', <witness>, '--protocol', 'silo', '--ccbench-root', <source>]` (222-227 行)、
  `repo_head` = `git -C <repo_root> rev-parse HEAD`、`ccbench_pin`、`patch_sha256`、`verifier_module_sha256` = `{p.name: sha256(p) for p in sorted((repo_root/'orchestrator/verifier').glob('*.py'))}` (610-613 行)。
- 標準経路の patch の実体は CCBench source root の `git diff --binary HEAD` で、その sha256 が `SourceEvidence.tracked_diff_sha256` (orchestrator/campaign/source_digest.py:2377-2398 `_tracked_diff_sha256`)。source root は `SourceEvidence.source_root`、pin は `SourceEvidence.ccbench_commit`。
- 保全口 (pipeline.py:2166-2208 の finally、2624-2690 の `_preserve_trace_directory`) は D2233 項 4 の不変条件で動く。

## 2. plan v2 (採用)

1. `_run_one_repetition` の finally で保全へ渡す入力を増やす: 反復の commit witness (trace が witness まで届いた反復だけ非 None) と、反復が使った `evidence` (`SourceEvidence`)。
   witness は `_execute_verification_repetition` の戻り値から取れないなら、戻り値の型へ witness を 1 field 足すか、`_project_repetition_outcome` に渡る前の outcome を finally から参照できる形にする (どちらでもよい。評価結果・verdict・WAL・受領証・例外の型と値は不変)。
2. `_preserve_trace_directory` の inventory に次を足す (名前は runner v5 と同じ。inventory の既存 key・配置・status 規則は不変):
   - `verifier_invocation`: 文字列 `"in-process"` (標準経路の判定は CLI でなかったことの明記。1 field だけ)。
   - `verifier_argv`: `[realpath(sys.executable), "-B", "-m", "orchestrator.verifier", <元の一時 dir の path>, "--json", "--expected-commits", str(<witness>), "--protocol", <genome.protocol>, "--ccbench-root", <evidence.source_root>]`。witness が None の反復は `null`。
   - `repo_head`: orchestrator を含む repo の `git rev-parse HEAD` (40 hex)。dirty は記録しない (D320)。
   - `ccbench_pin`: `evidence.ccbench_commit`。
   - `patch_sha256`: source root の `git diff --binary HEAD --` の bytes の sha256。bytes は archive 内の `patch/ccbench.diff.zst` に zstd で保全し、`patch_path` (archive からの相対 path)・`patch_bytes` を並べる。
   - `tracked_diff_sha256`: `evidence.tracked_diff_sha256` をそのまま記録 (patch_sha256 との一致を gate にしない。記録だけ)。
   - `verifier_module_sha256`: `{name: sha256}`、`orchestrator/verifier/*.py` の非再帰 glob を名前順 (runner と同じ)。
3. 取得はすべて保全処理の内側 (env が設定されたときだけ) で行う。env 未設定なら git・hash・zstd を一切呼ばない (D2233 項 4)。取得の失敗は既存の保全失敗と同じ経路 (inventory `failed`、原本を残す、stderr に 1 行、評価結果・例外は不変)。
   git の起動は `source_digest` と同じ sanitized 環境 (`_sanitized_git_env` 相当) で行う。
4. evidence が無い反復は無い前提だが、None が来たら R1 の 4 項目 (`verifier_argv`・`ccbench_pin`・`patch_*`・`tracked_diff_sha256`) を null にする (推測値を入れない)。
5. 変えないもの: `_execute_verification_repetition` の判定、verify fan-out (P5: remote 反復は現状も保全対象外、触れない)、job body の opt-in 配線 (P6)、WAL・proof chain・受領証・campaign lock の schema。

規模上限: production 120 行、test 200 行 (追加行)。

## 3. test (実装子が書く、この名前で。単一理由の入力で)

`orchestrator/tests/test_t2853_trace_preservation.py` に:
- `test_inventory_records_r1_inputs`: 実際の git repo (tmp に作り、1 commit + tracked file の変更を持つ) を source root にした evidence で評価を通し、inventory の 7 項目を exact に照合する — `verifier_invocation == "in-process"`、argv 全体 (witness・protocol・source root・元の一時 dir)、`repo_head == git rev-parse HEAD` (この repo)、`ccbench_pin == evidence.ccbench_commit`、`zstd -d` で戻した patch の bytes == source root の `git diff --binary HEAD --` の bytes かつ sha256 == `patch_sha256`、`tracked_diff_sha256 == evidence.tracked_diff_sha256`、`verifier_module_sha256` == この repo の `orchestrator/verifier/*.py` の名前→sha256。git・zstd・hash を stub しない (F649)。揮発値 (tmp path・sha) は実行時に計算して比べ、焼き込まない。
- `test_r1_argv_null_without_witness`: trace が witness に届かない反復 (既存 fixture の空 trace など、witness が None になる入力を 1 つ) で `verifier_argv is None`、他の項目は記録される。
- `test_unset_env_unchanged` の拡張: env 未設定で、R1 入力の取得 (git の起動・verifier module の hash) が一度も起きないこと。既存の assert は弱めない。
- `test_r1_input_failure_retains_original`: source root を git repo でない dir にした evidence で保全させ、inventory が `failed`、原本の一時 dir が残り、評価結果 (certified・verdict) が env 未設定時と同じであること。

既存 test の期待値は変えない。fixture の共有 helper (`test_campaign._eval` など) を変える必要があれば変えずに、この file の中で wrapper を書く。

## 4. 変異の事前登録 (DW-M01、意味で登録。位置は実装後に一意置換で確定し、単一理由を確認してから本走)

runner は `tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_t2853_trace_preservation.py` に限る (pipeline.py は campaign の contract loader 閉包にあり、全 test を走らせると drift 層が一律に殺すため。t2849 insight §6 と同じ理由)。

| ID | 変異 | 期待 | kill 点 |
|---|---|---|---|
| M1 | argv から `--expected-commits <N>` の 2 要素を落とす | KILLED | test_inventory_records_r1_inputs |
| M2 | argv の `--ccbench-root` の値を元の一時 dir にする | KILLED | test_inventory_records_r1_inputs |
| M3 | witness が None でも argv を作る (N に commit 行数などを入れる) | KILLED | test_r1_argv_null_without_witness |
| M4 | `repo_head` を source root 側の `rev-parse HEAD` にする | KILLED | test_inventory_records_r1_inputs |
| M5 | `ccbench_pin` を None にする | KILLED | test_inventory_records_r1_inputs |
| M6 | 保全する patch の bytes を空にする (sha256 は空 bytes の値) | KILLED | test_inventory_records_r1_inputs |
| M7 | `verifier_module_sha256` の対象から名前順の先頭 1 file を落とす | KILLED | test_inventory_records_r1_inputs |
| M8 | env 未設定でも R1 入力の取得 (verifier module の hash か git) を行う | KILLED | test_unset_env_unchanged |
| M9 | R1 入力の取得失敗を保全の境界の外 (評価へ) 送出する | KILLED | test_r1_input_failure_retains_original |
| C0 | `_preserve_trace_directory` の docstring だけを変える | SURVIVED | — |

単一理由: 各 KILLED は名指し test の 1 assert だけが赤になることを probe で確かめてから本走の期待 node に登録する。M4 は source root の HEAD と repo の HEAD が違う fixture でだけ意味を持つ (test がそうなっていなければ登録を外して再照準)。

## 5. 受入と費用

焦点走 → 変異 (単価を 1 job で実測してから) → 受入全走 (`tools/dev_wave_wait.py acceptance --lease-optional`)。合計 2 node 時間未満の見込み (受入 ≈ 0.25、焦点走・変異は数分単位)。
