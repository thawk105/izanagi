静的監査のみ実施した。書込み、pytest、build、Web 検索は行っていない。

## 所見 1 — 残余経路は実在しない

**所見**

`pipeline.evaluate()`／`buildcache.build()` 自体は sort gate を再実行しない。しかし、現行 production caller を逆引きすると、LLM が合成した sort 断片を quarantine、auditor、SWO oracle なしで渡す到達可能経路はない。

### `pipeline.evaluate()` の全 production caller

1. [loop.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/loop.py:256)

   - (i) LLM 合成:
     - backoff 断片: [p3_s4_loop.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop.py:951)。sort ではなく、直前に quarantine／effect gate を通る [p3_s4_loop.py:941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop.py:941)。
     - sort 断片: [p3_s4_loop_sort.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_sort.py:325)。後述の全 gate を通過済み。
   - (ii) 列挙・有限構成:
     - [sanity_silo.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sanity_silo.py:59)
     - [backoff_repro.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/backoff_repro.py:113)
     - [backoff_sweep.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/backoff_sweep.py:173)
     - [s6_sort_sweep.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s6_sort_sweep.py:362)。候補は固定 15 件 [s6_sort_sweep.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s6_sort_sweep.py:136) で、D344 により SWO-by-construction の oracle 対象外 [decisions.md:15227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/docs/decisions.md:15227)。
     - [p2_2.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p2_2.py:144)
     - [s8a_trigger_sweep.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:464)
     - trigger の LLM 出力も C++ ではなく固定 5-bit wire なので (ii) 相当: [p3_s4_loop_trigger_gating.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:564)、[p3_s4_loop_trigger_gating.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:595)。
   - (iii) 固定 stock／patch:
     - [demo.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/demo.py:57)、[demo.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/demo.py:66)
     - [p3_s4_red.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_red.py:165)、[p3_s4_red.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_red.py:175)
     - [p3_kickoff.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_kickoff.py:111)、[p3_kickoff.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_kickoff.py:118)

2. [screening_driver.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/screening_driver.py:189)

   呼出元はすべて (ii): [backoff_sweep.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/backoff_sweep.py:100)、[backoff_sweep.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/backoff_sweep.py:119)、[s6_sort_sweep.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s6_sort_sweep.py:369)、[s8a_trigger_sweep.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:471)。

3. [s1_direct_comparison.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:970)、既定値は [s1_direct_comparison.py:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:782)

   (iii) verified freeze。sort は quarantine [s1_direct_comparison.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:663) と SWO oracle [s1_direct_comparison.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:671) を通る。

4. [s8b_oracle_driver.py:1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_oracle_driver.py:1490)、既定値は [s8b_oracle_driver.py:1299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_oracle_driver.py:1299)

   (iii) ratified freeze。共有 binding [s8b_oracle_driver.py:1462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_oracle_driver.py:1462) から S1 materializer [s8b_materialization.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_materialization.py:125) へ進むため、sort は同じ oracle を通る。

5. [t126_driver.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/qualification/t126_driver.py:537)

   (ii) 由来を凍結した (iii)。入力は P2-2 列挙 WAL の固定 member [t126_control_v1.json:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/qualification/t126_control_v1.json:15) で、sort hole ではない。

### `buildcache.build()`／`build_v2()` の全 production caller

- `pipeline.evaluate()` 内:
  - legacy: [pipeline.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/pipeline.py:851)、[pipeline.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/pipeline.py:857)
  - v2: [pipeline.py:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/pipeline.py:887)、[pipeline.py:890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/pipeline.py:890)
  - source 分類は上記 `evaluate()` と同じ。

- (ii) 列挙／有限構成からの直接 legacy build:
  - [s1_verify_extime_calibration.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:358)。finite trigger predicate を freeze と照合し quarantine 済み [s1_verify_extime_calibration.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:190)、[s1_verify_extime_calibration.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:341)。
  - [backoff_profile.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/backoff_profile.py:148)
  - [backoff_overthrottle.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/backoff_overthrottle.py:83)

- (iii) stock の直接 legacy build:
  - [s2_verify_calibration.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s2_verify_calibration.py:306)、[s2_verify_calibration.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s2_verify_calibration.py:307)
  - [s5_permutation_coverage.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s5_permutation_coverage.py:195)
  - [pegasus_floor_scoping.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/pegasus_floor_scoping.py:218)
  - [between_run_floor.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/between_run_floor.py:167)
  - [s3_lock_coverage.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s3_lock_coverage.py:199)

- (iii) freeze の直接 v2 build:
  - `build_fn` の production 既定 [s8b_floor_campaign.py:1949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_floor_campaign.py:1949)、呼出し [s8b_floor_campaign.py:2115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_floor_campaign.py:2115)。official 経路は既定関数を固定する [s8b_floor_campaign.py:4118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_floor_campaign.py:4118)。
  - S8B oracle の provenance wrapper [s8b_oracle_driver.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s8b_oracle_driver.py:1091) は同じ freeze source を中継するだけ。

LLM sort 断片の実際の呼出し列は次のとおりで、配線漏れではない。

`load_proposal_file` [p3_s4_loop_sort.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_sort.py:359)  
→ `drive_iteration` [p3_s4_loop_sort.py:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_sort.py:415)  
→ quarantine＋auditor [p3_s4_loop_sort.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_sort.py:152)  
→ SWO oracle [p3_s4_loop_sort.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_sort.py:162)  
→ `run_campaign` [p3_s4_loop_sort.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_sort.py:318)  
→ `evaluate` [loop.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/loop.py:256)  
→ build [pipeline.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/pipeline.py:851)。

`coder_effect_gate.py` は直接 build caller を scope 外と明記する [coder_effect_gate.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/coder_effect_gate.py:20) が、これは抽象 API の限界であり、現行 caller に (i) の bypass がある証拠ではない。

**深刻度**

残余欠陥は refuted。実装候補なし。

**提案**

段 2 §3 の `loop.py`／`pipeline.py`／`buildcache.py` への sort grammar 再配線は、この wave の到達可能欠陥修正としては実装しない。将来の caller 増加に備えた caller-closure 検査は別タスク候補に分離する。

`orchestrator/tests/` の直接呼出しは fixture であり production 到達性を作らないため、上の source 分類から除外した。

## 所見 2 — closed-region 契約は一部だけ機械執行される

**所見**

逐語契約は次のとおり。

> **Closed-region 制約 (D23 道Y、hook が機械執行する部分と auditor が目視する部分の併用):**  
> - 新しいヘッダ取り込み・型/関数/マクロ/グローバル変数の追加は禁止  
> - 生の前処理指令 (`#if`/`#ifdef`/`#define`/`#include` 等) は禁止  
> - `implementation` 内では `//`・`/*`・行末 backslash `\` を禁止する (文字列リテラル・raw string 内も禁止)。説明文はコード内に埋めず `justification` フィールドへ書く  
> - 非決定ビルトイン (現在時刻・乱数等) は禁止  
> - 既存 silo API を呼ぶ straight-line code のみ (副作用のある呼び出し・ループ・例外送出は不可)

出典: [coder-v4-autonomous-sort.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/.claude/agents/coder-v4-autonomous-sort.md:84)

| 契約項目 | 現に検査している実装 | 不要／未実装と影響 |
|---|---|---|
| 新しいヘッダ取り込み・マクロ追加 | 生指令を DiffQuarantine が拒否 [diff_quarantine.py:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/diff_quarantine.py:489)。hole 外変更も拒否 [diff_quarantine.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/diff_quarantine.py:443)。 | 実装済み。 |
| 型／関数追加 | oracle は外側が単一 `sort(...)` 文かだけを見る [sort_swo_oracle.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:486)。lambda 本体は raw C++ のまま compiler へ渡す [sort_swo_oracle.py:1529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:1529)。 | **未実装。** lambda 内の local type／補助 callable が compile と有限 oracle を通れば、宣言した三 field 能力より広い source が受理される。 |
| グローバル変数追加 | hole は `TxExecutor::validationPhase()` 内 [transaction.cc:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/external/ccbench/cc/silo/transaction.cc:383)。外側は単一文検査。 | namespace/global 定義は配置上**不要**。ただし static local や既存 global への到達は別項目として未閉鎖。 |
| 生の前処理指令 | `#`、`%:`、`??=` を行頭空白込みで検出 [diff_quarantine.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/diff_quarantine.py:51)、拒否 [diff_quarantine.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/diff_quarantine.py:491)。 | 実装済み。現行 (i) 経路は全て DiffQuarantine を通る。 |
| `//`、`/*`、行末 backslash | byte 一致で拒否 [diff_quarantine.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/diff_quarantine.py:503)、[diff_quarantine.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/diff_quarantine.py:517)。 | 実装済み。 |
| 非決定ビルトイン | `DENY_TABLE` には time／random の閉じた禁止集合がない [coder_effect_gate.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/coder_effect_gate.py:58)。oracle は同一 pair の再評価 [sort_swo_oracle.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:766) と別 process/order [sort_swo_oracle.py:1221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:1221) で観測分だけ拒否。 | **未実装。** 有限観測で変動しなかった非決定性は通り、実 workload で relation が変われば SWO と再現可能性が崩れる。 |
| 既存 silo API のみ／副作用なし | host-effect は有限 blacklist [coder_effect_gate.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/coder_effect_gate.py:58)。oracle は corpus bytes の mutation を snapshot で検出 [sort_swo_oracle.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:720)。 | **未実装。** blacklist 外で corpus を変えない call は受理されうるため、TxExecutor／process／host 状態を介して workload や fitness を変える余地が残る。実装自身も残余を明記 [coder_effect_gate.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/coder_effect_gate.py:12)。 |
| straight-line／ループ禁止 | 外側の複数文は拒否 [sort_swo_oracle.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:546)。effect gate は明示的な無条件 `while`／`for` だけ [coder_effect_gate.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/coder_effect_gate.py:527)。 | **未実装。** bounded／data-dependent loop は通り、oracle corpus では終了して実 workload だけで長時間化・非停止する source を契約違反のまま受理できる。 |
| 例外送出禁止 | oracle が有限 corpus 上で実際に送出された例外を捕捉 [sort_swo_oracle.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:775)、`candidate-comparator-threw` へ分類 [sort_swo_oracle.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:1051)。`throw` 自体の構文禁止はない。 | **未実装。** corpus で発火しない条件付き送出は通り、実入力で sort を中断し correctness／availability を失わせうる。 |

**深刻度**

副作用、非決定性、例外は重大。型追加と loop は中程度の契約不一致。ただし現行設計は auditor と有限 oracle を併用すると明記しており、機械的な完全閉鎖へ変えるには D344 の supersede 裁定が必要。

**提案**

この差分を「残余 caller の配線漏れ」として修正しない。ユーザー裁定では、raw C++ 合成を維持して machine-complete の主張を弱めるか、D344 を明示的に覆して typed grammar を導入するかを選ぶ。

## 所見 3 — reason code テストは契約差分を閉じていない

**所見**

`test_coder_effect_gate.py` が exact ID を固定する拒否コードは次の 6 件。

- `host-effect.process-shell.v1`
- `host-effect.file-stdio.v1`
- `host-effect.network.v1`
- `host-effect.sleep-block-thread.v1`
- `host-effect.escape-hatch.v1`

  出典: [test_coder_effect_gate.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_coder_effect_gate.py:67)

- `host-effect.lexer-malformed.v1`

  malformed、byte 上限、token 上限が同じ ID に畳まれる: [test_coder_effect_gate.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_coder_effect_gate.py:112)、[test_coder_effect_gate.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_coder_effect_gate.py:210)。

`host-effect.unconditional-loop.v1` は実装に存在する [coder_effect_gate.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/coder_effect_gate.py:108) が、テストが固定するのは `unconditional-loop` category だけで exact ID ではない [test_coder_effect_gate.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_coder_effect_gate.py:165)。

`test_sort_swo_oracle.py` が固定する REJECT reason は次のとおり。

- `qualified-or-non-sort-callee`
- `not-a-single-sort-statement`

  [test_sort_swo_oracle.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:297)

- `candidate-compile-failed`

  [test_sort_swo_oracle.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:471)、[test_sort_swo_oracle.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:606)

- `corpus-mutated-by-comparator`
- `relation-varies-within-process`

  [test_sort_swo_oracle.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:213)

- `relation-varies-across-process-order`

  [test_sort_swo_oracle.py:1104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:1104)

- `swo-irreflexive`
- `swo-asymmetric`
- `swo-transitive`
- `swo-transitive-equivalence`

  4 axiom は enum と exact witness の parameterization で固定 [test_sort_swo_oracle.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:178)、reason の生成は [sort_swo_oracle.py:1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/sort_swo_oracle.py:1253)。

§2 の未実装行との対応は以下。

| 未実装項目 | テスト固定状況 |
|---|---|
| local type／補助 callable の追加 | 拒否テストなし。 |
| 非決定 builtin 自体の禁止 | 観測された relation 変動だけ固定。builtin/capability の閉鎖テストなし。 |
| blacklist 外 API／corpus 外副作用 | 5 category と corpus mutation だけ固定。実装が明記する残余の拒否テストなし。 |
| bounded／data-dependent loop | 未固定ではなく、**通ることを明示的に固定済み** [test_coder_effect_gate.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_coder_effect_gate.py:151)。契約との不一致がテストで恒久化されている。 |
| 条件付き `throw` | `candidate-comparator-threw` の exact reason テストなし。有限 corpus で発火しない送出の境界テストもない。 |

**深刻度**

中。既存テストは現行有限 gate の挙動をよく固定するが、closed-region 契約全体の被覆証明にはなっていない。

**提案**

D344 裁定前に拒否テストだけを追加しない。まず受理集合を狭めるか、auditor-only 残余として契約を明記するかを裁定し、その結論と reason code テストを同じ変更単位にする。

## 所見 4 — 16 件中 1 件は文法入力ではなく、提案文法は D344 と衝突する

**所見**

段 2 文法は [positive-controls.txt:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/output/insights/2026-08-04_t409-evolve-hole-allowlist/positive-controls.txt:11) から [positive-controls.txt:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/output/insights/2026-08-04_t409-evolve-hole-allowlist/positive-controls.txt:39) までの実 C++ 15 件を受理できる。使用するのは固定 envelope、三 field、`<`、`!=`、条件演算子、`false` であり、BNF の production 内に収まる。

受理できない 1 件は次の stock メタデータ。

> `SORT_VARIANT=0 の #else 枝 (テンプレ骨格そのまま) = sort(write_set_.begin(), write_set_.end()) — WriteElement::operator< による (storage_, key_) 昇順 2 段辞書式 (silo_op_element.hh)`

出典: [positive-controls.txt:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/output/insights/2026-08-04_t409-evolve-hole-allowlist/positive-controls.txt:9)

これは `STOCK_IMPL_NOTE` であり、materialize される C++ ではない [s6_sort_sweep.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s6_sort_sweep.py:154)。したがって literal な「16 文字列を grammar が全受理」は達成不能で、正しい受入単位は「15 implementation＋1 stock system control」。

さらに、提案文法は既存 generic lambda 正例を落とす。[test_p3_s4_loop_sort.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_p3_s4_loop_sort.py:97) と [test_sort_swo_oracle.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:21) は `const auto&` を正例としており、実 oracle E2E も pass を要求する [test_sort_swo_oracle.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/tests/test_sort_swo_oracle.py:141)。段 2 自身も generic lambda を拒否するとする [s2-plan.md:347](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t396-hole-allowlist/s2-plan.md:347)。

D344 の却下対象は「完成 comparator の有限列挙」だけではなく、純粋 field 読取りと比較へ閉じる **typed IR／AST allowlist** そのもの [decisions.md:15245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/docs/decisions.md:15245)。提案文法が再帰的で受理集合が無限でも、field と operator の有限 production から選択・合成する DSL に変わるため、この批判に該当する。段 2 も supersede が必要と認めている [s2-plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t396-hole-allowlist/s2-plan.md:107)。

**深刻度**

ブロッカー。grammar 実装は D344 と実験設計を変更するユーザー裁定なしには進められない。

**提案**

正例要件を「15 C++ implementation＋stock materialization 1 件」に訂正する。その後も grammar を採るなら、D344 と generic lambda の受理をどう扱うかを明示裁定する。

## 所見 5 — 親 brief の残存 3 主張

**所見**

1. **trigger 軸へ LLM 任意テキストが入る経路はない — 正しい。**

   LLM coder のコード由来 field は exact 5-bit `wire` [p3_s4_loop_trigger_gating.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:114)。`parse_wire` は長さ 5 の `0/1` だけを受理 [reflux_ir.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/reflux_ir.py:113)、hole text は凍結 emitter が生成する [reflux_ir.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/reflux_ir.py:131)。

2. **`SYNTAX_CONTRACT_FORBIDDEN` が単独の受理関所である箇所はゼロ — 正しい。**

   - autonomous trigger は emitter drift 検査後 [p3_s4_loop_trigger_gating.py:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:410)、quarantine＋auditor へ進む [p3_s4_loop_trigger_gating.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:419)。
   - S1 は canonical membership [s1_direct_comparison.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:635) と quarantine [s1_direct_comparison.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:663) を併用。
   - workload trial preview も check 後に quarantine [p3_autonomous_workload_trial.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:889)。

   ただし brief の補助説明「使用は 2 箇所」は stale で、production の `check_syntax_contract` caller は上記 3 箇所。結論には影響しない nit。

3. **段 2 の編集面は `s1_known_axes_freeze` の live SHA pin を壊さない — 正しい。**

   verifier は generator 自身と全 `sources` の live bytes を再 hash する [s1_known_axes_freeze.py:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/orchestrator/campaign/s1_known_axes_freeze.py:832)。sort 関連で pin される production source は `s6_sort_sweep.py` と `p3_s4_loop_sort.py` [known_axes_freeze.json:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-hole-allowlist/output/s1-freeze/known_axes_freeze.json:200)。段 2 は両方を編集しないと明記する [s2-plan.md:250](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t396-hole-allowlist/s2-plan.md:250)。提案された `p3_s4_loop.py`、`loop.py`、`pipeline.py`、`buildcache.py` 等はこの freeze の source path 集合にない。

**深刻度**

3 主張の結論はいずれも正しい。「2 箇所」という件数だけ nit。

**提案**

親 brief の件数説明だけ 3 caller に訂正する。その他は段 4 の根拠として維持できる。

## 総括

残余経路としての (i)、すなわち LLM sort 断片を既存 gate なしで `evaluate`／`build` へ渡す経路は実在しない。  
LLM sort の唯一の production 列は quarantine → auditor → SWO oracle → evaluate → build である。  
直接 sink caller は列挙候補、finite emitter、凍結 patch、stock に限られ、本 wave の実装候補は消滅する。  
最も重い残余は closed-region 契約の機械未実装だが、段 2 grammar は D344 と衝突するためユーザー裁定が必要である。