実装 U3 を working tree に残しました。docs・git index・commit・branch は操作していません。

## 変更前の受理・拒否挙動

- stock caller: U1 適用後は旧 fixed constructor が封印され実行不能。旧仕様上は source evidence や repo pin を検査せず stock を自己申告できました。
- machine caller: 同様に旧 constructor は実行不能。旧仕様上は registered generator receipt なしで machine class を自己申告できました。
- coder driver: plain bool を constructor に渡す旧配線で、flag なしを拒否していたものの run-scoped capability ではありませんでした。kickoff の dirty no-op は stock/cache hit 扱いでした。
- review caller: S1 は source-bound review receipt なしの fixed human-reviewed class でした。
- 手動 materializer: build admission を経由せず、成果物にも統一された拒否分類がありませんでした。
- T126: fixed stock admission と full source digest を `src_token` として渡し、live `SourceEvidence` と capability を分離していませんでした。

## caller 配線表

| caller | 変更後の導出根拠 |
|---|---|
| [backoff_overthrottle.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/backoff_overthrottle.py:69) | `BACKOFF_OVERTHROTTLE` generator receipt |
| [backoff_profile.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/backoff_profile.py:136) | `BACKOFF_PROFILE` generator receipt |
| [backoff_repro.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/backoff_repro.py:97) | `BACKOFF_REPRO` per-source generator receipt |
| [backoff_sweep.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/backoff_sweep.py:145) | `BACKOFF_SWEEP` per-source generator receipt |
| [between_run_floor.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/between_run_floor.py:161) | 実 evidence の clean + STOCK |
| [demo.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/demo.py:42) | pipeline が実 evidence から stock 導出 |
| [p2_2.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/p2_2.py:136) | pipeline が実 evidence から stock 導出 |
| [p3_kickoff.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/p3_kickoff.py:87) | parser-issued token。同一 context 内で evidence により分岐 |
| [p3_s4_red.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/p3_s4_red.py:132) | parser-issued token |
| [p3_s4_loop.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/p3_s4_loop.py:812) | parser-issued token を campaign ID 計算前に context 化 |
| [p3_s4_loop_sort.py:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/p3_s4_loop_sort.py:377) | parser-issued token。auditor verdict は advisory のまま |
| [p3_s4_loop_trigger_gating.py:700](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/p3_s4_loop_trigger_gating.py:700) | parser-issued token。auditor を review receipt に昇格しない |
| [s1_direct_comparison.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s1_direct_comparison.py:627) | `S1_KNOWN_AXES` の source-bound review receipt |
| [s1_verify_extime_calibration.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s1_verify_extime_calibration.py:342) | `S1_EXTIME_CALIBRATION` generator receipt |
| [s2_verify_calibration.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s2_verify_calibration.py:299) | stock build は実 evidence、broken build は non-admissible |
| [s3_lock_coverage.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s3_lock_coverage.py:193) | stock build は実 evidence、broken build は non-admissible |
| [s5_permutation_coverage.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s5_permutation_coverage.py:189) | stock build は実 evidence、broken build は non-admissible |
| [sanity_silo.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/sanity_silo.py:34) | pipeline が実 evidence から stock 導出 |
| [s8a_trigger_coverage.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s8a_trigger_coverage.py:134) | patched source + generator input を `S8A_TRIGGER_SWEEP` receipt に束縛 |
| [s8a_trigger_freq.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/s8a_trigger_freq.py:135) | coverage の admitted build を再利用し receipt を成果物へ保存 |
| [t152_write_intent_coverage.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/t152_write_intent_coverage.py:704) | non-admissible 診断専用 |
| [silo_ladder_rung1.py:4685](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/silo_ladder_rung1.py:4685) | non-admissible ability probe |
| [t126_driver.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/qualification/t126_driver.py:515) | live member build の context。pipeline が live evidence から導出 |

`p3_kickoff.py` の stock seed と dirty no-op/cache-hit 分岐は削除し、dirty no-op を coder-authored namespace の cache miss として検査するよう変更しました。

## NON_ADMISSIBLE_MATERIALIZERS

Registry は [materializer_admission.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u3/orchestrator/campaign/materializer_admission.py:20) に置きました。

- `s2_verify_calibration._broken_build_and_verify`: buildcache allowlist が通常拒否する negative control
- `s3_lock_coverage._build_broken`: verifier 感度確認用 trace mutation
- `s5_permutation_coverage._build_broken`: permutation verifier の negative control
- `t152_write_intent_coverage._build`: correctness-only mutation matrix
- `silo_ladder_rung1._build_variant`: research selection 不適格の ability probe
- `silo_ladder_rung1._correctness_command`: campaign buildcache 外の correctness build

各 producer は `admission_status: non-admissible` を成果物へ明示します。S8a coverage/frequency は registry へ落とさず、registered generator receipt を build 直前に再検証する経路にしました。

Registry docstring には、`tools/pegasus/*.sh` と calibrator の arbitrary binary path を閉じていないことを明記しています。

## 検証

pytest nodeid の完走結果はありません。

実行を試みたコマンド:

```text
python3 tools/run_tests.py \
  orchestrator/tests/test_p3_build_authority_cli.py \
  orchestrator/tests/test_p3_exploration_namespace.py \
  orchestrator/tests/test_p3_s4_loop_trigger_gating.py -x -q
```

結果は `qstat -Q preflight rc=1` による Pegasus dispatch infrastructure failure で、pytest は開始されませんでした。

実施済みの静的検査:

- 変更した production/test 全ファイルの `python3 -m py_compile`: 成功
- `git diff --check`: 成功
- docs 差分確認: なし

未実行:

- pytest 全 nodeid
- その他 driver 固有 test
- full suite
- CCBench build
- campaign 実走
- mutation test

## 期待して赤くなる finding

静的に既知の集合は次です。pytest 未実行のため、実際に観測した test failure ではありません。

- U4 未適用: `s6_sort_sweep.py`、`s8a_trigger_sweep.py` の旧 constructor、overlay/consumer/replay 群
- U5 未適用: `s8b_floor_campaign.py`、`s8b_oracle_driver.py` の旧 constructor
- 共有 test の旧 API fixture: `test_build_site_gate.py`、`test_screening_driver.py`、S6/S8a/S8b 関連 test
- `test_s1_verify_extime_calibration.py` は U4 所有の `s8a_trigger_sweep.py` import により collection へ波及可能
- 歴史的 `dff0f1e` stock driver は、新しい repo 正本 pin 条件では stock admission を取得せず fail-closed になる

この集合以外の赤は回帰として扱う必要があります。現時点ではテスト実行不能のため「それ以外の赤がない」とは主張しません。

既存期待値を変えた理由は、直接 constructor が正規 capability でなくなったこと、campaign identity が admission policy を含むこと、dirty no-op が tracked-clean stock ではないことです。歴史的 S8a campaign ID sentinel は旧導出値として残しています。

## 所有外への静的波及

- U4/U5 caller の旧 constructor は、新 API では import または呼出時に拒否されます。
- admission policy が campaign ID に入るため、5 coder driver と S1 の新規 campaign namespace は従来値から変わります。
- stock を含む旧 cache namespace は再利用されません。
- S8a coverage/frequency の成果物 schema に canonical `build_admissions` が追加されました。consumer は receipt を positive validationする必要があります。
- non-admissible producer の成果物 schema に refusal classification が追加されました。
- T126 の series identity・preimage・protocol・control pin は意図的に変更していません。
- `s1_known_axes_freeze.py` と `output/` は未変更です。

## 総括

1. build class は caller の enum ではなく、実 `SourceEvidence`、registered generator/review receipt、parser-issued tokenから導出する配線に統一しました。
2. dirty no-op を stock namespace へ戻さず、coder token と新 admission namespaceを要求するようにしました。
3. admission 外の Python materializer は明示 registry と downstream-visible refusalで閉じ、S8a machine characterization は実 source-bound receipt を要求しました。

既知限界は、pytest dispatch が失敗して動的検証できていないこと、U4/U5 caller・consumer が未適用であること、shell materializer・任意 binary path・推移的 provenance が未閉包であることです。