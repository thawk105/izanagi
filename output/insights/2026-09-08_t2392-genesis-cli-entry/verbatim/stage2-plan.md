## 再導出した実測

- `create_attempt_registry_genesis` の識別子は、射影された production source 4 本では次の 3 箇所だけだった。

  1. 8c facade の定義：[trial_registry.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2471)
  2. facade から共有 core への呼出し：[trial_registry.py:2517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2517)
  3. 共有 core の定義：[attempt_registry_core.py:1431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/attempt_registry_core.py:1431)

  従って、射影内では facade `trial_registry.create_attempt_registry_genesis` の非テスト caller は **0 件**。別名代入、対象名を使う `getattr`、`globals` / `locals` / `__dict__`、`import_module`、`eval` / `exec`、文字列 dispatch も対象4本で検索したが、対象関数へ到達するものはなかった。production driver は `trial_registry` を module import しているが（[p3_autonomous_workload_trial.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/p3_autonomous_workload_trial.py:53)）、genesis は呼んでいない。

  ただし射影外の repo file は読めないため、**repo 全体の非テスト caller 数は判定不能**。上記の 0 件は射影4本に限定した結論である。計算で組み立てた関数名による未知の動的呼出しも、一般論として完全には否定できない。

- `trial_registry.main` の subcommand は **2 個**。

  - `register`：[trial_registry.py:6505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6505)
  - `accept`：[trial_registry.py:6510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6510)

  `add_subparsers(..., required=True)` は [trial_registry.py:6504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6504)、`parse_args(argv)` は [trial_registry.py:6522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6522)。第3入口はない。

- provisional 裁定の再導出結果：

  - **P1 は成立**。genesis 行自身に commit は入らないが、effective binding は `prereg_content_commit` と genesis 初期 hash を保持し（[trial_registry.py:1379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1379)）、P の blob と照合する（[trial_registry.py:1462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1462)）。P/C/H の親子・祖先関係も強制される（[trial_registry.py:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1477)）。v5 receipt は P/C を記録する（[trial_registry.py:6440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6440)）。
  - **P2 は成立**。genesis は `freeze_id`、manifest path/hash、canonical root path、retry reason の閉集合、全 slot を保存する（[attempt_registry_core.py:1506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/attempt_registry_core.py:1506)）。`prereg_generation` は全 slot と一致する正整数に制約される（[trial_registry.py:2497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2497)）。ただし絶対 `repository_root` は証跡 field ではなく、repository-relative path に正規化される。
  - **P3 は成立**。driver は登録済み走で slot を予約し（[p3_autonomous_workload_trial.py:4844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/p3_autonomous_workload_trial.py:4844)）、lifecycle start を記録する（[p3_autonomous_workload_trial.py:4923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/p3_autonomous_workload_trial.py:4923)）。正常 terminal は [p3_autonomous_workload_trial.py:5203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/p3_autonomous_workload_trial.py:5203)、例外時の indeterminate terminal は [p3_autonomous_workload_trial.py:5237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/p3_autonomous_workload_trial.py:5237) で記録される。
  - **P4 は成立**。raw argv は `parse_args` 後に捨てられ、`register` の出力は manifest hash・件数・commit-required のみ（[trial_registry.py:6531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6531)）、`accept` の summary にも argv field はない（[trial_registry.py:6490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6490)）。射影4本に `sys.argv` の保存先もない。
  - **P5 は逐語裁定からは導けない**。D1775 の例外は4項目が「記録されているなら足さない」である（[D1775-verbatim.md:4](/home/SFC/tanab/.claude/jobs/631b6865/tmp/t2392/D1775-verbatim.md:4)）一方、argv は記録されていない。「第3 subcommand も argv を記録しないので provenance が増えない」は妥当な設計評価だが、未記録を記録済みに変換せず、D1775 の停止条件そのものではない。

## 判定 (commit / argv / 入力 / lifecycle)

| 項目 | 判定 | 束縛と、赤になる具体例 |
|---|---|---|
| commit | **記録される** | receipt は `prereg_content_commit` / `prereg_effective_commit` を必須 field とする（[s8c_acceptance_receipt.py:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:819)）。検証時、それらを attempt row の expected binding として replay する（[s8c_acceptance_receipt.py:1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1620)）。例えば receipt の P と attempt event の P が異なれば [s8c_acceptance_receipt.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:550) で赤。P に genesis blob がない、または現在の prefix がその blob を継承しない入力も [s8c_acceptance_receipt.py:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1638) で赤。従って恒真ではない。 |
| argv | **記録されない** | `main(argv)` は parse するだけ（[trial_registry.py:6502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6502)）。receipt schema、registry row、CLI output のいずれにも raw argv field はない。従って argv を改変しても、それが最終的に同じ意味値を生成する限り、argv 自体を理由に赤にする条件式は存在しない。 |
| 入力 | **記録される** | genesis の exact slot keys は trial/arm/holdout/campaign、generation、replicate/attempt index、schedule hash を含む（[trial_registry.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:146)）。receipt verifier は genesis の manifest hash が receipt と違えば赤（[s8c_acceptance_receipt.py:1632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1632)）、slot projection が receipt と違えば赤（[s8c_acceptance_receipt.py:1660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1660)）、trial/arm/holdout/campaign 集合が receipt trials と違っても赤（[s8c_acceptance_receipt.py:1667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1667)）。 |
| lifecycle | **記録される** | acceptance は各 manifest trial に start と terminal がちょうど1行ずつあることを要求する（[trial_registry.py:5402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5402)）。start の manifest/P/C/head/admission が accepted bytes と違えば赤（[trial_registry.py:5449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5449)）、terminal status/report/journal hash が違えば赤（[trial_registry.py:5522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5522)）。外側 verifier も append-only history と receipt prefix hash を再検査する（[s8c_acceptance_receipt.py:1991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1991)）。 |

現在の v5 receipt については、attempt registry の再検証が必ず呼ばれる（[s8c_acceptance_receipt.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:2075)）。したがって commit・入力・lifecycle の束縛は単なる記載ではなく、具体的な不一致入力を落とす fail-closed 条件である。

## 「足す」場合の plan

最小差分は `trial_registry.py` の `main` と新規 CLI test だけに限定する。

1. [trial_registry.py:6522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6522) の `parse_args` 直前、既存 `accept` 引数定義の後に第3 subcommand **`genesis`** を追加する。既存 help 順 `register, accept` は保つ。

   引数は次の5個だけにする。

   - `--manifest PATH`：必須。`load_trial_manifest` で検証し、`manifest.sha256` を creator へ渡す。
   - `--repo-root PATH`：必須。
   - `--freeze-id TEXT`：必須。
   - `--prereg-generation INT`：必須、`type=int`。
   - `--slots-file PATH`：必須。strict UTF-8 JSON の top-level array。各要素は既存 `_ATTEMPT_SLOT_KEYS` の exact object。

   `--manifest-sha256` は足さず、manifest bytes から導出する。`--registry` も足さず、既存 canonical default を使う。`--retryable-failure-reasons` も足さず、既存の閉集合 default を使う。これにより自由度と新規契約を増やさない。

2. [trial_registry.py:6536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6536) の既存 `else` の前に `elif args.command == "genesis"` を挿入する。

   - `_read_regular_bytes`（[trial_registry.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:619)）と `_decode_json`（[trial_registry.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:606)）で slots を読む。
   - `create_attempt_registry_genesis` に上記の導出値を渡す。
   - 新 subcommand だけ、canonical JSON で `attempt_registry_path`、`manifest_sha256`、`slot_count` を出す。
   - 現在の `register` branch と `accept` branch の本体、引数、出力 dict は移動・変更しない。

3. test は既存 test を未読のまま推測して追記せず、新規 [tests/test_trial_registry_genesis_cli.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/tests/test_trial_registry_genesis_cli.py:1) として追加する。

   - 正例：一時 Git repo に妥当な6-cell manifest と、共通 `prereg_generation=1`、`replicate_index=0`、`attempt_index=0` の6 slot を置く。`main(["genesis", ...]) == 0`、canonical path に v3 freeze 行が1行だけ作られ、manifest digest・freeze ID・全 slot が一致することを確認する。
   - 拒否例1：同じ argv を再実行し、create-only 違反で `SystemExit(2)`、既存 bytes が不変であることを確認する。根拠となる既存 `O_EXCL` gate は [trial_registry.py:2444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2444)。
   - 拒否例2：CLI の `--prereg-generation=1` に対して slot の一つを `2` にし、作成前に拒否されることを確認する。条件は [trial_registry.py:2502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2502)。
   - 拒否例3：`--slots-file` が JSON object、重複 key、非 UTF-8、または非有限数なら strict decoder / slot parser で拒否し、artifact が作られないことを確認する。

影響範囲：

- **受入：触れない。** `assert_formal_attempt_registry_acceptance`（[trial_registry.py:3675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:3675)）および v5 verifier（[s8c_acceptance_receipt.py:1955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1955)）は無変更。
- **凍結成果物の tracked bytes：触れない。** wave 中に `output/s8c-preregistration/attempt-registry.jsonl` を作らない。将来の CLI 実行効果は既存 creator の canonical serializer と create-only pin（[trial_registry.py:2526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2526)）だけを通る。
- **enforcement closure：触れない。** production driver の予約・start・terminal 経路と、receipt の最終 consumption 検査（[s8c_acceptance_receipt.py:1576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/s8c_acceptance_receipt.py:1576)）は無変更。
- schema、argv 記録機構、8b、追加 gate、台帳、一般化は足さない。

## 総括

再導出結果は **commit=記録される、argv=記録されない、入力=記録される、lifecycle=記録される**。従って P1〜P4 は支持するが、4項目中 argv が欠けるため、D1775 の逐語的な「記録されているなら足さない」から P5 は導けない。逐語裁定をそのまま適用するなら判定は **「足す」** に傾く。

ただし追加する `genesis` も argv provenance を保存しないので、P4 自体は改善しない。これは本 wave で argv 記録機構を新設しないという scope と整合するが、「CLI 追加によって4項目がすべて記録される」という結論にはならない。

pytest は実行しておらず、緑の主張はない。静的確認のみ。