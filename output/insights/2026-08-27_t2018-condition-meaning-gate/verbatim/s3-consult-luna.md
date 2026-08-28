## 総括

段2 plan は現状のまま段5へ進めない。判定は **NO-GO**。blocker は 7 件。

最大の問題は次の4点。

- repo-wide の対象は9個ではなく **8個**。しかも同じ `result_identifier` 型ではなく、量、分岐 selector、依存 enum、診断 toggle が混在する。
- `parse_supplied_macros()` は名前集合しか返さないため、要求した CMake cache 値が対象 macro へ届くことを証明しない。F707 の別形を通す。
- `expected_values` を context 間の集合に潰すと、context ごとの結果を入れ替えた decoder が通る。
- driver 配線0なので、成果物は「gate」ではなく、明示的に呼ばれた時だけ効く **call-scoped standalone decoder oracle** である。

静的検査のみ実施した。pytest、compiler probe、mutation は未実走であり、緑とは報告しない。

## 数え上げ

母集合は repo 内の全 `patches/*.patch`。追加行だけから次を独立抽出した。

- Cache 集合
  `C = {X | +set(CCBENCH_X ...)}`
- TU 供給集合
  `S = {X | +X=${CCBENCH_Y}}`
- define-decode 候補
  `C ∩ S`

結果は8個だった。

| 分類 | macro | 現行の意味形 |
|---|---|---|
| 量 decoder | `BACKOFF_FIXED` | 整数を式で `now_backoff` へ復号 |
| behavior selector | `BACKOFF_TRIGGER_GATING` | 0/1で predicate scaffold を切替。5-bit値そのものではない |
| behavior selector | `SORT_VARIANT` | 0/1で comparator 枝を切替 |
| behavior selector | `SS2PL_LOCK_IMPL` | stock/study lock を切替 |
| 依存 enum | `SS2PL_LOCK_KIND` | `LOCK_IMPL=1` の時だけ lock 種を選択 |
| 依存 enum | `SS2PL_DLR` | 0/1/2と `DLR0/1/2` の組を選択 |
| 診断 toggle | `BACKOFF_NOINLINE` | symbol emission用の属性 |
| 診断 toggle | `SS2PL_WFG_DIAG` | source追加、計装、runtime出力を切替 |

したがって、親 brief の「量1・wire1・enum5・診断2 = 9」と、段2 plan の「他8 define」はともに誤り。[親実測:75](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/parent-measurements.md:75)、[段2 plan:37](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:37)。

別供給の `IZANAGI_BREAK_*` は現在11名あり、`CCBENCH_` cache/mapping は0件。`instr-*` は既存 `BACKOFF_TRIGGER_GATING` を参照するだけで、新しい供給 macro はない。これは上の8個と別 bucket にすべきである。

## Findings

### 1. 対象数と意味形の一般化が誤っている

- 判定: **real**
- severity: **high**
- scope: **内**
- blocker: **yes**
- file:line: [親実測:75-87](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/parent-measurements.md:75)、[段2 plan:37](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:37)
- 検索母集合/式: 全 `patches/*.patch` の追加行、`C ∩ S`。結果は上表の8個。
- 成果物影響: `BACKOFF_FIXED` fixtureだけで、分岐、comparator、複数TU、CMake source追加を持つ他7個まで族一般を閉じたように読める。特に `BACKOFF_TRIGGER_GATING` は5-bit wireではなく、その wire を含む coder生成 predicate を有効化する1-bit selector。
- 最小修正: v1 の production registry は `BACKOFF_FIXED` 1件だけに固定し、`SUPPORTED_MACROS == {"BACKOFF_FIXED"}` を明記する。repo-wide inventory testで8個と分類を固定し、残り7個を「未対応」ではなく「別 semantic shape」と記録する。

他7個は無防備でもない。例えば `BACKOFF_NOINLINE` は完成ELFの symbolを確認する [backoff_profile.py:663](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_profile.py:663)、sortは独立SWO oracleを持つ [sort_swo_oracle.py:2674](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/sort_swo_oracle.py:2674)、SS2PLは要求cache、実compile definition、runtime自己表示を三段照合する [run_ss2pl_lock_study.py:905](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/tools/pegasus/run_ss2pl_lock_study.py:905)、[同:2394](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/tools/pegasus/run_ss2pl_lock_study.py:2394)。ただし、これらを「意図した意味の独立再導出」と格上げしてはならない。

### 2. F707 腕が cache-to-macro 配線を証明しない

- 判定: **real**
- severity: **critical**
- scope: **内**
- blocker: **yes**
- file:line: [段2 plan:52](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:52)、[source_digest.py:739](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:739)、[同:1849](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1849)
- 検索母集合/式: `parse_supplied_macros()` の戻り値と `_parse_supplied_macro_details()`、`_worktree_defines()` の全経路。
- 成果物影響: 例えば `BACKOFF_FIXED=${CCBENCH_WRONG}` でも名前集合には `BACKOFF_FIXED` が入り、synthetic TUへ要求値5を直接注入すれば緑になる。一方、実driverは `Genome.cmake_defines()` から `-DCCBENCH_BACKOFF_FIXED=5` を渡すため [model.py:61](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/model.py:61)、実TUは別値を受けうる。
- 最小修正:
  - `source_digest` に source-owner-aware な effective define 解決を公開APIとして薄く出す。
  - `Genome("silo", {"BACKOFF_FIXED": v})` と `source_rel="include/backoff.hh"` から、各caseで `effective["BACKOFF_FIXED"] == str(v)` を要求する。
  - contract JSONが自由に `protocol` を選ぶ設計を廃止し、ownerは [source_digest.py:86](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:86) のregistryから取る。

F707 fixtureは cacheの `set(...)` だけでなく、`BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` mappingを欠かせる必要がある。他のuniversal mappingを1本残し、parser全体が空集合理由で落ちないようにする。

### 3. context を集合へ潰すと意味の入替を通す

- 判定: **real**
- severity: **critical**
- scope: **内**
- blocker: **yes**
- file:line: [親 brief:36-39](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s1-brief.md:36)、[段2 plan:46-59](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:46)
- 検索母集合/式: `cases[].expected_values` と `contexts[]` の直積。反例は
  `expected(c1)=0, expected(c2)=1`、`observed(c1)=1, observed(c2)=0`。両集合は `{0,1}` で一致する。
- 成果物影響: `declared-context-meaning` と名乗りながら、contextと結果の関係を証明しない恒真寄りのgateになる。
- 最小修正: `MeaningCase.expected_by_context` をcontext順と同数のtupleにし、case × contextをpointwise比較する。集合は観測表示としてのみ派生させる。

`grid-injectivity-only` modeもv1から外すべきである。独立期待値がある `BACKOFF_FIXED` ではpointwise一致が単射性を含み、別gateは重複する。独立期待値がない軸では一様shiftや単位違いを通すため、T-2018の意味関門にはならない。

### 4. JSON contract は実在production入力ではない

- 判定: **real**
- severity: **high**
- scope: **内**
- blocker: **yes**
- file:line: [段2 plan:50](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:50)、[同:102-122](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:102)
- 検索母集合/式: `orchestrator/campaign/` と `orchestrator/tests/` 全ファイルで予定schema、loader、consumerを検索。production consumerは0。
- 成果物影響: test専用JSONのためにdataclassとJSON schemaを二重化し、任意path、marker、macro、result identifier、result kindを新しい入力境界として増やす。将来用 `int64`/`uint64` も未使用。
- 最小修正: v1ではJSONを作らない。production-ownedな `BACKOFF_FIXED_CONTRACT` をPython定数として固定する。caller入力は `ccbench_root`、`cxx`、exact型のcases/contextsだけにする。
  - bool-as-intは `type(value) is int` で拒否。
  - context値は `0 <= value <= 2**64-1`。
  - duplicate define caseを拒否。
  - path、marker、macro、result identifier、result kindはcaller入力にしない。
  - float64出力はbitsで比較し、NaN/Infを専用理由で拒否。
  - unknown JSON fieldとduplicate JSON keyは、JSON自体を廃止することで入力面から消す。

### 5. `gate` という名称が配線0の実効範囲より強い

- 判定: **real**
- severity: **high**
- scope: **内**
- blocker: **yes**
- file:line: [段2 plan:41](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:41)、[同:172-175](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:172)
- 検索母集合/式: 新APIを呼ぶproduction site数 = 0、test siteのみ。
- 成果物影響: moduleが存在するだけでdriverが保護されたように誤読される。現行1000点は引き続き実行可能。
- 最小修正:
  - module名を `condition_meaning_oracle.py` とする。
  - APIを `evaluate_registered_decoder_meaning()` とする。
  - proof kindを `compiler-evaluated-extracted-decoder-standalone-tu-source-local-define-pointwise-declared-context` とする。
  - supply証拠は別fieldで `cmake-source-owner-resolved-cache-to-tu-define` とする。
  - `driver_integration="none"` をdocstringとD記録へ明記する。
  - `gate` と呼べるのはT-1999裁定後にdriverが必須呼出しを持った時だけとする。

### 6. 新規block parserは既存部品と重複する

- 判定: **real**
- severity: **high**
- scope: **内**
- blocker: **yes**
- file:line: [段2 plan:53](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:53)
- 検索母集合/式: `orchestrator/campaign/` 全域の `EVOLVE-BLOCK-BEGIN` parser/extractor。
- 既存部品:
  - file/line-number parser: [diff_quarantine.py:567](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/diff_quarantine.py:567)
  - text-based unique extractor: [sort_swo_oracle.py:493](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/sort_swo_oracle.py:493)
  - BACKOFF_FIXED exact-source/compiler oracle: [b10_backoff_shape_sweep.py:1662](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/b10_backoff_shape_sweep.py:1662)
- 成果物影響: 3本目のparserがmarker重複、directive数、CRLF、nested directiveの扱いを別実装し、oracle間で受理差が出る。
- 最小修正: `sort_swo_oracle.extract_materialized_hole()` の既存意味を小さい共有 `evolve_block.py` へ抽出し、full conditional blockとholeの両方を返す。sort側の公開wrapperは維持する。`diff_quarantine` はdiff行番号という別責務なので置換しない。

fixtureのdecoder lineは [b10_backoff_shape_sweep.py:122](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/b10_backoff_shape_sweep.py:122) の既存exact formulaと一致することをtestで固定する。

### 7. timeout無しは未測定述語を避けたのではなく無期限hangを許している

- 判定: **real**
- severity: **high**
- scope: **内**
- blocker: **yes**
- file:line: [段2 plan:60-64](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:60)、[D706](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2018-condition-meaning-gate-codex-resume/authority-s2.md:135)
- 検索母集合/式: compile/run subprocessの全終了辺。timeoutなしでは、compiler hang、生成実行物のloop、異常source増大が有限時間で拒否されない。
- 成果物影響: fail-closed oracleではなく、campaignを永久停止させる入力を持つ。
- 最小修正: author投入前に親が同じlogin-node/compiler/source-size regimeでcompile/run時間分布を実測し、N、max、倍率、外側watchdogとの不等式を記録する。その値からtimeoutを決める。既存B10の120秒を根拠なく流用しない。

新test nodeは受入実走後に [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/acceptance_duration_ledger.json:1) へ追加する。現在のcoverage gateは90%以上を要求する [test_acceptance_schedule_order.py:704](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_acceptance_schedule_order.py:704)。

### 8. scope外だが現行1000点は未保護のまま

- 判定: **real**
- severity: **critical**
- scope: **外**
- blocker: **no。ただし主張上限の記録必須**
- file:line: [backoff_extended_sweep.py:33](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:33)、[同:379](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:379)、[test_backoff_extended_sweep.py:121](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_backoff_extended_sweep.py:121)
- 検索母集合/式: `EXTENDED_SWEEP_US` の全29点。1000はdecoderで0へ写る。
- 成果物影響: 同driverを再走すれば、binary hashは異なるが意味は0 µsの1000 µs点を生成できる。
- 最小修正: 本waveでは編集しない。新oracleのtestで「現行29点を評価すると1000で拒否」を固定し、D/worklogへ「driver保護0」を残す。義務接続はT-1999へ返す。

## Refuted

1. **driver配線0自体は違反ではない。** 段2 planは現driverが未保護だと明記している [s2-plan:174](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:174)。名称と証拠種別をoracle相当に弱めれば、固定境界と整合する。

2. **`cc/silo/CMakeLists.txt` の選択はBACKOFF_FIXEDについては正しい。** `include/backoff.hh` のownerはgenome protocolで、silo caseならsilo CMakeへ到達する [source_digest.py:1849](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1849)。問題は自由なJSON `protocol` と、fixture内容、値mappingの未照合である。

3. **hole-literal経路のscope外判定は概ね正しい。** 実閉包は単独の `assert_value_literal_consistent()` だけでなく、exact single-literal grammar [backoff_hole_grammar.py:576](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_hole_grammar.py:576) と呼出順 [p3_s4_loop.py:998](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/p3_s4_loop.py:998) の合成で成立する。briefは単一関数へやや過剰帰属しているが、経路除外は維持できる。

4. **compiler flagsのC++20/O3/NDEBUG採用は既存source_digestと一致する。** [source_digest.py:225](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:225)。親probeのC++17/O2との差は現在式のF718再現を反証しない。ただし実TU同一性の証明には使えない。

5. **他live branchとの実装path重複は現時点で見つからない。** `main` のbase以降変更はS8b系、`dev-wave-b10-overthrottle-grid` はcleanで本baseへ既に含まれ、T-2018親worktreeはuntracked insightだけだった。current parent/Codex resumeの同一wave重複は想定内。

## 推奨 plan v2

1. 先に記録と実測を固める。

   - `docs/decisions.md`: 新Dを1件。8 macro inventory、v1はBACKOFF_FIXEDだけ、oracleであってdriver gateではないこと、proof kindを記録。
   - `docs/failures.md`: 新Fは不要。F718へ「現行1000は未保護」「T-2018 v1は未配線」のaddendumを付ける。
   - `docs/roadmap.md`: T-1999はそのまま裁定待ち。別の新Tを1件割り当て、残り7 macroを既存oracle込みでsemantic-shape別に設計する。
   - `docs/worklog.md`: 現行1000点の未保護、T-1999待ち、残り7の新Tを記録。
   - compile/run所要分布を親が実測し、timeout根拠を確定する。

2. exact実装pathを次へ変更する。

   - 新規 `orchestrator/campaign/evolve_block.py`
     既存sort extractorを共有化。unique BEGIN/END、exact 1組のif/else/endif、順序、full conditional block、hole bytesを返す。
   - 変更 `orchestrator/campaign/sort_swo_oracle.py`
     現公開 `extract_materialized_hole()` を共有parserへの互換wrapperにする。
   - 変更 `orchestrator/campaign/source_digest.py`
     source ownerとcache mappingを保ったeffective define解決の公開adapterを追加する。
   - 新規 `orchestrator/campaign/condition_meaning_oracle.py`
     code-owned `BACKOFF_FIXED` contractだけを持つ。JSON loader、任意path/marker/result kind、injectivity-only modeは置かない。
   - 新規 `orchestrator/tests/test_condition_meaning_oracle.py`
   - 変更 `orchestrator/tests/test_sort_swo_oracle.py`
   - 変更 `orchestrator/tests/test_campaign.py`
     公開effective-define adapterのowner/mapping境界を固定。
   - 実走後のみ `orchestrator/tests/acceptance_duration_ledger.json`
   - `tools/check_docs.py` 自体は編集不要。

3. fixtureは次の最小形にする。

```text
orchestrator/tests/fixtures/condition_meaning_oracle/
├── supplied/
│   ├── cmake/Options.cmake
│   ├── cc/silo/CMakeLists.txt
│   └── include/backoff.hh
└── f707-missing-supply/
    ├── cmake/Options.cmake
    ├── cc/silo/CMakeLists.txt
    └── include/backoff.hh
```

F707側はdecoderを維持し、`BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` mappingだけを欠かせる。他のmappingを残してparserを空集合エラーにしない。F718は`supplied` treeへ1000の独立期待を渡すため、別JSONも別source複製も不要。

4. contract/APIはpointwiseにする。

```python
MeaningCase(
    define_value=1000,
    expected_float64_bits_by_context=(bits_1000, bits_1000),
)
```

公開結果はsource hash、compiler identity、context順の観測bits、effective define mappingを持つ。F718は `define_value=1000 / context_index=0 / expected=1000 / observed=0` のように単一cellを示す。

5. 必須testを固定する。

   - repo-wide追加patch inventoryが8個である。
   - `SUPPORTED_MACROS == {"BACKOFF_FIXED"}`、他7個を対応済みに数えない。
   - positive 0、5、999をcontextごとに一致。
   - F707 mapping欠落はcompiler解決前に `macro-not-supplied`。
   - cache-to-macro誤配線は `supply-value-mismatch`。
   - F718の0/1000は1000 cellで `decoded-meaning-mismatch`。
   - context結果swapは集合一致でも拒否。
   - comment内の正しい式、uniform shift、非有限出力、marker重複、compiler/run失敗を拒否。
   - 現行 `EXTENDED_SWEEP_US` 全29点を入れると1000で拒否する。
   - fixture holeが既存B10 exact formulaと一致する。
   - timeoutは親実測由来値で発火testを持つ。

6. consumer閉包を正直に分ける。

   - 本waveのproduction consumer: **0**。
   - 共有parser consumer: 新oracleと既存sort oracle。
   - oracle consumer: 新testだけ。
   - `diff_quarantine.parse_template_file()` の既存consumerである `pipeline.py` と `p3_s4_loop.py` は変更しない。
   - 将来T-1999で接続する場合だけ、[backoff_extended_sweep.py:379](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:379) のmaterialization後、prebuild前へ置く。その際は `test_backoff_extended_sweep.py`、`test_campaign.py`、`test_official_perf_closure.py`、`test_p3_build_authority_cli.py`、`test_ccbench_spawn_sites.py` をconsumer closureに含める。

7. 親の検証段では関連node、test file全体、受入全走からJUnitを取り、duration ledgerを更新する。その後に `check_codex_agents`、`check_docs`、commit後provenanceを行う。本consultではいずれも未実走。

**NO-GO — blocker 7件。**
