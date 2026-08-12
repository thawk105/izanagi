実装は完了しましたが、Pegasus scheduler preflight が `qstat -Q rc=1` で停止したため、全所見を `partial（実装済み・未実走）` と判定します。docs・commit・所有外ファイルは変更していません。

### 所見ごとの対応

| 所見 | 判定 | 根拠 |
|---|---|---|
| F-7 | partial | assignment alias を固定点追跡し、binding のない `import_module(...build_admission)` と組立て `getattr` を検出。[test_p3_build_authority_cli.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:210)、[同:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:563)、[同:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:581) |
| F-8 | partial | file skip を廃止し、全 tracked Python を parse。10 file・11 call-site の exact allowlist と、2本目／別 function の負制御を追加。[同:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:84)、[同:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:462)、[同:532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:532) |
| F-9 | partial | site は「保存済み・未消費」で admission rejection gate ではないと明記。[build_admission.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:326) |
| F-10 | partial | 静的列挙可能な Python issuer だけが対象であること、未閉包面、下流拒否・成果物隔離が成立しないこと、T-841 境界を明記。[build_admission.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:2) |
| F-11 | partial | M10 を structural coverage のみと明記し、runtime 証拠を M9 に帰属。[test_p3_build_authority_cli.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:462)、[同:681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:681) |

### 受理・拒否挙動

変更前は、assignment alias と binding のない dynamic import/getattr が `calls=[] / dynamic=[]` となり、除外10 file は source 自体が走査されませんでした。

変更後は次の repository 状態が閉包テストで拒否されます。

- low-level helper の assignment alias 呼出し
- binding の有無に関係しない `importlib.import_module("...build_admission")`
- build-admission module に対する組立て `getattr`
- allowlisted function 内の2本目
- 同じ allowlisted file の別 function からの呼出し

既存 runtime の受理集合は広げていません。6 registered entrypoint、low-level fixture seam、red/kickoff の既存起動正例は維持しています。[red/kickoff 正例:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_exploration_namespace.py:369)

同一 process から private/low-level factory を直接呼べる限界、shell materializer、任意 binary path、`output/**` の runnable script、下流 artifact admission は閉じていません。

### Exact allowlist 最終形

すべて helper は `add_coder_build_authority_argument`、count は1です。

| path | enclosing function | helper | count |
|---|---|---|---:|
| `orchestrator/tests/test_artifact_admission.py` | `_new_schema_campaign` | low-level | 1 |
| `orchestrator/tests/test_build_admission.py` | `_parser_authority` | low-level | 1 |
| `orchestrator/tests/test_buildcache_v2.py` | `_all_class_admissions` | low-level | 1 |
| `orchestrator/tests/test_campaign.py` | `<module>` | low-level | 1 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py` | `_coder_authority` | low-level | 1 |
| `orchestrator/tests/test_p3_build_authority_cli.py` | `test_stock_machine_and_opted_in_coder_paths_remain_accepted` | low-level | 1 |
| `orchestrator/tests/test_p3_build_authority_cli.py` | `test_dirty_noop_stock_token_enters_coder_admission_namespace` | low-level | 1 |
| `orchestrator/tests/test_p3_exploration_namespace.py` | `<module>` | low-level | 1 |
| `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` | `<module>` | low-level | 1 |
| `orchestrator/tests/test_s1_direct_comparison.py` | `test_pipeline_bench_rounds_default_three_and_opt_in_one` | low-level | 1 |
| `output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py` | `main` | low-level | 1 |

### M9 / M10 / M11

- M9: runtime の単一理由候補。未登録 site が token生成・build・WAL より前に拒否される負例です。ただし未実走。
- M10: scan-root equality が殺す structural coverage のみ。未登録 issuer の runtime 拒否証拠には数えません。
- M11: exact call count／function の structural negative。smoke の2本目は `(actual=2, expected=1)`、別 function は `(actual=1, expected=0)` の単一差分として静的確認済みです。

### 検査状況

静的診断では以下を確認しました。

- tracked Python 474件を全走査
- exact allowlist が実コードと完全一致
- dynamic violation 0件、star import 0件
- production registered call 6件がすべて `main`
- alias/dynamic/smoke負制御が期待する違反を生成
- 所有4 file の AST parse 成功
- `git diff --check` 成功
- `ADMISSION_SCHEMA`、`_ADMISSION_KEYS`、`derive_build_admission()`、`validate_build_admission_receipt()` は HEAD と AST 同一
- WAL/cache/COMMIT/freeze producer は未編集

実走を試みた範囲は以下ですが、いずれも pytest 起動前に `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1` で停止しました。

- F-7/F-8/F-11 の焦点6 nodeid
- `test_p3_build_authority_cli.py` と `test_p3_exploration_namespace.py` の collection

したがって緑の nodeid はありません。

### 波及可能性

- allowlist対象10 fileは、function名変更・call追加で閉包テストが赤になります。
- production caller 6 driver は登録 helper の path/function/site literal 完全一致を要求されます。
- 共有 fixture では `test_build_admission.py`、`test_buildcache_v2.py`、`test_campaign.py`、`test_artifact_admission.py`、P3 driver tests、`test_s1_direct_comparison.py` が波及候補です。
- consumer側の receipt schemaや artifact admission判定は変更していません。
- `materializer_admission.py` と `test_p3_exploration_namespace.py` には、このfixでの追加編集はありません。

## 総括

F-7〜F-11 はすべて実装済みですが未実走のため `partial` です。dev-wave worker契約に従い、docs・commit・所有外変更・受入全走は行っていません。親側で scheduler 復旧後に焦点nodeidと両test file全体を実走する必要があります。