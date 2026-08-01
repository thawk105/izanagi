## 総括

- 現在の `whiteboard[].result` は既に `success|fail|rejected` を次世代へ渡しており、欠落は詳細な「なぜ」である。
- S1 は CLI 既定値を `1` にし、`parse_args()` 直後に拒否して競合検査・checkout より先に停止させる。
- 推奨は CLI だけでなく `run_trial()` も同じ validator で塞ぐ構成。P2 の CLI 限定には異議がある。
- 解除点は `MAX_APPROVED_GENERATIONS = 1` の 1 定数と、承認境界を固定するテスト 1 本に集約する。
- S2 は本 wave では実装せず、将来案として planner-only の閉じた失敗分類を第一候補とする。
- ただし同一 campaign state の再利用により、1 generation でも過去 whiteboard が届きうる別の残余がある。
- 指定資料はすべて読了した。pytest は実行しておらず、緑は主張しない。

## S1 実装プラン

### 推奨案: CLI と programmatic 経路を共通 validator で塞ぐ

1. `orchestrator/campaign/p3_autonomous_workload_trial.py:87-92`

   - 既存の絶対上限 `MAX_GENERATIONS = 10` は残す。
   - その隣に、裁定済み受理域だけを表す `MAX_APPROVED_GENERATIONS = 1` を追加する。
   - 将来の解除はこの値だけを新しい裁定値へ変える。環境変数、隠し flag、provider 別例外は作らない。
   - `MAX_GENERATIONS` は実装上の絶対上限、`MAX_APPROVED_GENERATIONS` は研究裁定上の上限、と役割を分離する。

2. `orchestrator/campaign/p3_autonomous_workload_trial.py:179-180` の `AutonomousTrialError` 直後

   - `_validate_generation_budget(generations: Any) -> None` を置く。
   - 判定順は次の二段にする。

     1. `bool`、非 `int`、`1..MAX_GENERATIONS` 外を既存の一般契約違反として拒否。
     2. `MAX_APPROVED_GENERATIONS` 超過を D106 残余 1 の未裁定運転として拒否。

   - 例外は既存と同じ `AutonomousTrialError`。
   - メッセージ案:

     ```text
     世代予算 {value!r} は裁定済み範囲 1..{MAX_APPROVED_GENERATIONS} 外です
     (D106 残余 1: cross-generation 還流設計は未裁定)
     ```

     上限を文面へ直書きせず定数から生成するため、解除時にメッセージが drift しない。

3. `orchestrator/campaign/p3_autonomous_workload_trial.py:857-860`

   - 現在の `run_trial()` 内の `1..MAX_GENERATIONS` 判定を共通 validator 呼び出しへ置換する。
   - これにより direct call も、`run_root.mkdir()` が起きる `:869-877` より前に拒否される。

4. `orchestrator/campaign/p3_autonomous_workload_trial.py:1017`

   - CLI 既定値を `default=2` からリテラル `default=1` へ変える。
   - `default=MAX_APPROVED_GENERATIONS` とはしない。将来上限を解除しても、明示 flag なしの運転を自動的に multi-generation へ変えないためである。
   - runbook の既存例 `docs/phase3-s8c-autonomous-trial-runbook.md:62-68`、`:75-81`、`:89-95` はすべて `--max-generations 1` を明示しており変更不要。

5. `orchestrator/campaign/p3_autonomous_workload_trial.py:1027-1028` の間

   - `args = parser.parse_args(argv)` の直後に共通 validator を呼ぶ。
   - これは次の全処理より前である。

     - fixture/build 組合せ判定 `:1028-1031`
     - no-build の pinned clean 検査 `:1037-1040`
     - 競合 process 検査 `:1043-1049`
     - checkout/build 準備 `:1050-1051`

   - `--max-generations 0` や負値も同じ位置で拒否し、無効入力が計測準備へ到達する既存の遅延拒否も閉じる。

### P2 の CLI 限定案を採る場合の差分

P2 を維持する場合は、上記から次だけを変える。

- `run_trial()` の `orchestrator/campaign/p3_autonomous_workload_trial.py:857-860` は従来の `1..10` のまま。
- `MAX_APPROVED_GENERATIONS` と新 validator は CLI 用とし、呼び出しは `:1027-1028` の間だけ。
- `run_trial(generations=2..10, do_build=True)` は引き続き build・COMMIT へ到達可能。

利点は既存 programmatic 契約を狭めないこと。ただし D106 残余 1 `docs/decisions.md:4863-4867` は「CLI invocation」ではなく「`>=2` の運転」を禁止しており、機械 gate としては迂回可能なままである。静的検索では production call site は `main()` の `:1053` だけで、他はテスト 3 件だったため、互換性コストより共通拒否のほうが妥当と判断する。

### docs の追随箇所

親が次を更新する。

- `docs/decisions.md:4269-4279`
  - D96 に従い、理由・射程・CLI/programmatic の採否・却下案を新しい D として記録する。
- `docs/decisions.md:4817-4819`
  - 「最大10世代」は実装上の絶対能力であり、現行の裁定済み受理域は1である、と新 D から限定する。
- `docs/decisions.md:4854-4867`
  - D106 の歴史的記述は消さず、「機械 gate は置いていない」を新 D により supersede されたと追記する。
- `docs/decisions.md:4896-4899`
  - 研究状態への影響に、新たな世代予算の受理集合変更を追記する。
- `docs/phase3-s8c-autonomous-trial-runbook.md:98-101`
  - 「機械 gate は無い」を、CLI/programmatic の実際の拒否範囲に置換する。
- 同 `:109-110`
  - 2世代以上は単なる運用禁止でなく `AutonomousTrialError` になることを明記する。
- 同 `:158-164`
  - 「運転者が守る規律」を機械 gate の説明へ置換し、解除には新裁定と境界テスト更新が必要と明記する。
- `docs/phase3.md:463-465`
  - 禁止が機械強制されたことと、programmatic 経路を塞いだか否かを明記する。

## S1 テストプラン

### 新規 nodeid 候補

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_generation_budget_boundary_at_ratified_launch`

  - `1` が受理され、`2` が `AutonomousTrialError` になることを一つのテストで固定する。
  - 値は意図的にハードコードする。裁定後は承認定数とこのテストだけを同じ変更単位で更新する。
  - D96 の「受理集合境界テスト」に当たる中心テスト。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_main_rejects_unapproved_generation_budget_before_build_preparation`

  - `claude-headless` の build 経路へ `MAX_APPROVED_GENERATIONS + 1` を渡す。
  - `competing_bench_pids`、`checkout`、`assert_pinned_clean` を「呼ばれたら失敗」に monkeypatch する。
  - 例外文面の `裁定済み範囲 1..1` を照合し、`run_root` と `ccbench_dir` が作られていないことも固定する。
  - gate の削除・下方移動・競合検査後への移動を検出する。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_run_trial_rejects_unapproved_generation_budget_before_artifact_creation`

  - 共通拒否案を採る場合に追加する。
  - `run_trial(generations=MAX_APPROVED_GENERATIONS + 1)` が provider 初期化や `run_root.mkdir()` より前に拒否されることを固定する。
  - P2 の CLI 限定案を採るなら、このテストは追加しない。

### 既存 nodeid の更新

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_main_accepts_fixture_no_build_at_cli_gate`
  (`orchestrator/tests/test_p3_autonomous_workload_trial.py:215-227`)

  - `--max-generations` を省略したまま残す。
  - pinned-clean sentinel まで到達することで、既定値が禁止側でないことを固定する。
  - 目的が分かる名前へ `test_main_default_generation_budget_is_accepted_at_cli_gate` と改名してもよい。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_invalid_role_is_single_attempt_and_stops_cell`
  (`:130-154`)

  - 共通拒否案では `generations=3` を `1` へ変更する。
  - このテストの不変条件は planner-invalid の一回停止であり、multi-generation 受理ではない。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_fixture_trial_runs_ycsb_abc_and_binds_descriptor`
  (`:69-120`)

  - 既に `generations=1` を明示しており、受理側の実経路回帰として維持する。

### 変異で固定すべき点

- gate 削除 → build-preparation テストが kill。
- `>` を `>=` に変更 → 1 の受理境界が kill。
- 既定値を 2 に戻す → default CLI sentinel テストが kill。
- gate を競合検査後へ移動 → unexpected preparation monkeypatch が kill。
- `run_trial()` 側の validator 呼び出し削除 → artifact-before-rejection テストが kill。

## S2 設計候補

共通の出発点は `WhiteboardEntry.result` が既に存在することだ。型は `orchestrator/campaign/p3_s4_loop.py:109-118`、planner 射影は `:273-286`、8c の planner/coder payload への投入は `p3_autonomous_workload_trial.py:667-676` と `:694-711` にある。

したがって以下は「失敗の有無」を新設する案ではなく、既存の `fail|rejected` をどこまで分解するかの選択肢である。

### 候補 A — 現状維持、1 generation/cell

- payload:
  - planner: 新規 field なし。
  - coder: 新規 field なし。
  - 既存 `whiteboard[].result: "success"|"fail"|"rejected"` のみ。
- D39/D45 との整合:
  - `WhiteboardEntry` の5 fieldを変えず、機序・理由・値を新規射影しない。
  - planner の Read 剥奪もそのまま。
- 最悪シナリオ:
  - `direction/magnitude/result` の組合せだけでも、反復できれば成功方向の粗い逆算は可能。
  - さらに `_whiteboard()` は既存 state を読む (`p3_autonomous_workload_trial.py:474-476`)。同じ campaign root を再利用すると、1 generation の新 run でも過去 result が最初の planner へ届きうる。
- 実装コスト:
  - S2 は0行。
  - S1 gate とテストのみ。
  - 「1 generation なら過去 feedback も無い」と強く保証するなら、`_run_workload()` の layout 確定後 `:631-666` に空 state 検査を追加し、コード約15–25行、テスト約30–50行が別途必要。
- 新しい機械 gate:
  - S1 の世代上限。
  - 厳密な無還流を主張するなら、generation 1 の planner 前に既存 `loop_state.json` を拒否する freshness gate。
- planner contract:
  - 現行文面と完全に両立する。変更不要。

これは本 wave の即時運用としては推奨するが、規律3を満たす設計解ではなく、次世代を作らないことで問題を発火させない停止案である。

### 候補 B — planner-only の閉じた失敗分類

- payload:
  - planner に次を追加する。

    ```json
    "prior_failure_v1": null
    ```

    または:

    ```json
    {
      "prior_failure_v1": {
        "class": "candidate-policy|correctness|liveness|infrastructure"
      }
    }
    ```

  - generation 1、成功、dry-pass は `null`。
  - coder には追加しない。引き続き `planner_direction` の `axis/direction/magnitude` だけを渡す。
- 値の生成元:
  - `rejected` は authoritative driver の diff/syntax/auditor rejection
    (`p3_s4_loop_trigger_gating.py:301-338`) から `candidate-policy`。
  - verify payload を持つ abort は `correctness`。
  - `LIVENESS_REASONS` に属する abort は `liveness`
    (`orchestrator/critic/digest.py:108-138`, `:257-298`)。
  - その他の abort は `infrastructure`。
  - payload shape が曖昧・未知なら生 reason を流さず、次世代開始前に停止する。
- D39/D45 との整合根拠:
  - whiteboard の5 fieldは変更しない。
  - raw digest、verdict、anomaly、abort reason、diff subtype、metrics、自由文を一切含めない。
  - coder は直接受けず、planner の抽象3 fieldだけを declassification 境界として維持する。
  - inline JSON なので Read 能力を戻さない。
  - ただし D39 の「機序経路を型で排除」という設計意図への明示的な例外であり、新しい D なしには採用できない。
- 最悪シナリオ:
  - planner は各 `direction/magnitude/result` と失敗 class を対応付け、one-factor probe を繰り返して「どの方向が correctness を避けるか」を逆算できる。
  - coderへ理由を直接渡さなくても、planner が次の direction を選ぶことで間接チャネルになる。
- 実装コスト:
  - `p3_autonomous_workload_trial.py:87-155`, `:474-501`, `:646-676`, `:783-837`: 約60–90行。
  - `test_p3_autonomous_workload_trial.py:59-120`: 約80–120行。
  - payload schema を変えるため `SCHEMA_VERSION` (`:88`) を更新。reportへ射影値を残すなら `REPORT_SCHEMA_VERSION` (`:89`) も更新。
  - `p3_s4_loop.py` の変更は不要。
- 必要な機械 gate:
  - exact-key・closed-enum 検査。
  - raw reason/digest/anomaly に canary を入れ、planner/coder payload bytes に存在しないことの否定テスト。
  - coder payload に `prior_failure_v1` が無いことの recipient separation テスト。
  - 未知分類時は次世代を開始しない。
  - generation 1 の既存 campaign state freshness 検査。
- planner contract:
  - 現行の「Do not name abort reasons...」だけでは、入力 field を justification にそのまま書く余地があるため追記が必要。

    ```text
    prior_failure_v1 is a closed coarse class for internal direction selection only.
    Do not echo, paraphrase, or expand it in justification or uncertainty.
    Do not name abort reasons, predicates, or a concrete gate design.
    ```

  - この文面は semantic lint ではないが、coder が planner justification を受けない構造が最終防壁になる。

将来 `>=2` を解禁するなら、この候補を第一候補とする。

### 候補 C — 非重複 window による遅延・集合還流

- payload:
  - planner のみに追加する。

    ```json
    "failure_window_v1": null
    ```

    または3件単位の非重複 window 完了時だけ:

    ```json
    {
      "failure_window_v1": {
        "window_size": 3,
        "classes_present": [
          "candidate-policy",
          "correctness",
          "liveness",
          "infrastructure"
        ]
      }
    }
    ```

  - `classes_present` はソート済み重複なし。件数、順序、iteration ID、direction との対応は渡さない。
  - coder には追加しない。
- D39/D45 との整合根拠:
  - per-attempt の理由対応を渡さず、whiteboard と別の集約 channel に限定する。
  - raw mechanism・性能値・ファイル参照を持たないため Read 剥奪を維持する。
  - ただし閉じた失敗分類自体は新情報なので、D39 の例外裁定は候補 B と同様に必要。
- 最悪シナリオ:
  - planner が同種の proposal だけで一つの window を構成すれば、集合でも実質的に一対一対応を得られる。
  - 複数 window の実験計画を操作し、集合差分から分類を復元できる。
  - 最初の feedback は4世代目以降となり、2〜3世代運転では規律3の狭まりを解消しない。
- 実装コスト:
  - `p3_autonomous_workload_trial.py:646-676`, `:783-837`: buffer・非重複消費を含め約90–140行。
  - テスト約120–180行。
  - crash resume 対応まで求めるなら、checkpoint schema
    (`p3_s4_loop.py:356-404`) も変わり、さらに約60–100行と既存 schema テスト
    (`test_p3_s4_loop.py:455-549`) の更新が必要。
- 必要な機械 gate:
  - window size固定、非重複、3件未満では絶対に emit しない。
  - counts/order/iteration IDを拒否する exact-key gate。
  - canary 非流出、coder 非配信、未知 class 停止。
  - window を跨いだ campaign state の origin binding。
- planner contract:
  - 候補 B と同じ追記が必要。
  - `classes_present` を justification に列挙しないことも明記する。

漏洩量は候補 B より小さいが、短い bounded trial では役に立たないため第二候補とする。

### 候補 D — planner と coder の双方へ閉じた分類を直接配信

- payload:
  - planner/coder 双方に候補 B と同じ `prior_failure_v1.class` を追加。
- D39/D45 との整合根拠:
  - raw reason、digest、anomaly、数値、Read は渡さない点では限定されている。
  - しかし coder が失敗 class と具体 predicate の双方を扱うため、D39 が排除した「棄却理由から勝ち筋を逆算する経路」を実質的に再現する。非再現とは言えない。
- 最悪シナリオ:
  - coder が `correctness` と知った直後に predicate の条件を一つずつ変え、accept/reject を oracle として具体 gate を探索する。
  - `candidate-policy` から禁止識別子や diff frame の境界を能動探索する。
- 実装コスト:
  - `p3_autonomous_workload_trial.py:110-131`, `:667-711`, `:783-837`: 約70–110行。
  - テスト約100–150行。
- 必要な機械 gate:
  - 候補 B の全 gate。
  - planner/coder が受け取る bytes の一致・閉集合検査。
  - ただし意味的な逆算そのものを機械的に禁止する gate は作れない。
- planner contract:
  - 候補 B の追記が必要。
  - coder contract `:124-131` にも非展開規則が必要だが、coder の職務自体が具体 predicate の生成なので、文面だけでは設計矛盾を解消できない。

実装効果は高いが、D39 の禁止経路を再開するため不採用を推奨する。

## 親 brief への異議

1. **P2「CLI だけ塞ぐ」には異議あり。**

   D106 決定6 `docs/decisions.md:4838-4847` は明示的に programmatic 経路を範囲外とした。一方、残余1 `:4863-4867` は `--max-generations` という表記を使いつつ、禁止理由を cross-generation の「運転」全体に置いており programmatic carve-out を持たない。

   `run_trial()` は公開名で、`do_build=True` と `generations=2..10` を直接受理し、台帳 COMMIT へ到達しうる。CLI-only gate は宣言済み禁止の完全な機械化ではない。production call site が `main()` 以外に無い現状では、共通 validator の互換性コストも小さい。

2. **「1 generation/cell は還流が起きない」は fresh campaign state を暗黙前提にしている。**

   - `_whiteboard()` は既存 state を読む: `p3_autonomous_workload_trial.py:474-476`
   - planner payload はその直後に whiteboard を受ける: `:666-676`
   - driver 自身も既存 state を load する: `p3_s4_loop_trigger_gating.py:487-490`
   - runbook も別 run-root で同一 campaign root を再利用しうると明記する:
     `docs/phase3-s8c-autonomous-trial-runbook.md:143-146`
   - D106 残余3も同じ事実を記録する: `docs/decisions.md:4876-4879`

   したがって S1 は宣言された `>=2` 禁止を機械化できるが、「還流を完全にゼロにした」とは記述できない。残余3を scope 外に維持するなら、docs でこの限定を明示すべきである。

3. **P1 の default=1 には賛成。ただし承認上限定数へ default を連動させない。**

   将来 `MAX_APPROVED_GENERATIONS` を2以上へ変えた際、flag 省略運転まで自動的に multi-generation 化するのは新たな受理変更になる。既定値はリテラル1のまま保持する。

4. **P3、P4 への異議は無し。**

   ただし P3 の「単一解除点」は、CLI限定より共通 validator のほうが明確に成立する。

## 確認できなかったこと

読めなかった指定ファイルは無い。read-only・書込み可能 tmp なしの条件に従い、pytest、py_compile、実 CLI 起動は行っていない。したがってテスト緑や実行時の拒否順序は未実測であり、上記は静的読解に基づくプランである。