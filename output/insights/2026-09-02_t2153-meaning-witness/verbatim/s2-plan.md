## 事実確認

- 供給 domain は 22 件、意味 witness 対応は `BACKOFF_FIXED` だけである。[condition_meaning_gate.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:63)、[condition_meaning_gate.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:157)
- `capture_define_inputs` は渡された `source_root` を実在解決し、`stock_root` と同一なら拒否する。[condition_meaning_gate.py:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:545)
- S1 は patch 適用または quarantine 実体化後に、その同じ `sub` を `source_root` として gate へ渡す。[s1_direct_comparison.py:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s1_direct_comparison.py:859)、[s1_direct_comparison.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s1_direct_comparison.py:909)、[s1_direct_comparison.py:912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s1_direct_comparison.py:912)。positive control の専用 driver も patch の `applied` 範囲内で gate を呼ぶ。[s2_verify_calibration.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s2_verify_calibration.py:127)、[s3_lock_coverage.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s3_lock_coverage.py:114)、[s5_permutation_coverage.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s5_permutation_coverage.py:111)、[t152_write_intent_coverage.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/t152_write_intent_coverage.py:211)、[s8a_trigger_coverage.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s8a_trigger_coverage.py:137)。従って、条件指令は gate 実行時に実在する。
- pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` の stock submodule に対象 macro は存在せず、静的 `rg` は 0 件だった。条件指令の根拠は適用済み patch である。
- 現行 `_instrument_materialized_branches` は対象断片全体で `#if`、`#else`、`#endif` が各 1 個、かつこの順であることを要求する。[condition_meaning_gate.py:1888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:1888)。従って `#else` の無い 8 件は拒否され、入れ子の `#if ADD_ANALYSIS` を持つ `NOREAD_VALIDATION` と `HIGHKEY_VALIDATION` も拒否される。
- 既存枝 witness は `BACKOFF_FIXED=-1`、`MARKER_ID`、`SOURCE_REL`、stock 文の逐語まで固定されている。[condition_meaning_gate.py:1927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:1927)。そのまま他 macro へ流用はできない。
- 意味宣言が無い場合は `unestablished`、宣言した witness が不一致なら `red` になり、admission は supply 全緑かつ meaning 非 red の場合だけ通る。[condition_meaning_gate.py:2044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:2044)、[condition_meaning_gate.py:2503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:2503)。witness 追加は受理集合を狭める向きだけである。
- `IZANAGI_BREAK_*` は patch 本文でも deliberately broken positive control、既定 OFF、baseline 混入禁止と明記される。例は [broken-silo-permutation-erase.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-permutation-erase.patch:9)、[broken-silo-norw-validation.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-norw-validation.patch:9)。meaning green の主張境界を「値が選ぶ前処理枝」に閉じれば、correctness green や baseline 適格性を意味せず、既存記述と矛盾しない。

親の P1 に対する結論は次の通り。

- **P1-a は条件付きで支持。** macro ごとの所有 file、完全一致する開始指令、witness kind、要求値、既定値を宣言する方式が最短。ただし既存 BACKOFF 固有関数の単純一般化ではなく、別の conditional-selection witness とする。
- **P1-b は支持。** 対象枝内 marker と対応する `#endif` 直後の完了 marker により、`#else` 無しでも選択有無を観測できる。ただし要求値と既定値の両方を前処理し、観測が異なることを green の必須条件にする。
- **P1-c は否定。** 11 件中 `IZANAGI_BREAK_TRIGGER_MISATTR` は `#ifdef` である。[broken-silo-trigger-misattr.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-trigger-misattr.patch:9)。`-D...=1` と `-D...=0` はどちらも defined なので同じ枝を選び、健全な witness にならない。また `BACKOFF_NOINLINE`、`SORT_VARIANT`、`IZANAGI_SILO_LADDER_RUNG1_REPORT` も同じ有界な枝 witness を構成できるため、実装第一群は 13 件が妥当。
- **P1-d は否定。** S1 の default 集合は 4 macro だけである。[s1_direct_comparison.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s1_direct_comparison.py:176)。10 件の positive control は専用 driver が `declaration=None` を渡しているため、S1 の 1 関数だけ変えてもそれらの成果物は縮まらない。例は [s5_permutation_coverage.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s5_permutation_coverage.py:92)、[t152_write_intent_coverage.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/t152_write_intent_coverage.py:192)。

## 設計

[condition_meaning_gate.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:49) から [condition_meaning_gate.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:181) の宣言群へ次を追加する。

```python
@dataclass(frozen=True, slots=True)
class ConditionalBranchWitnessSpec:
    witness_kind: str
    source_rel: str
    directive: str
    requested_value: int
    default_value: int
    companion_defines: tuple[tuple[str, int], ...] = ()

@dataclass(frozen=True, slots=True)
class ConditionalBranchMeaningDeclaration:
    macro: str
    witness_id: str
    requested_value: int
    default_value: int

CONDITIONAL_BRANCH_WITNESSES: Mapping[str, ConditionalBranchWitnessSpec]
```

`CONDITIONAL_BRANCH_WITNESSES` は 13 macro を個別 key で宣言する。`witness_kind` は少なくとも `attribute-presence`、`selector-branch`、`positive-control-branch`、`compound-report-branch` に分け、D1242 が却下した scalar decoder 一般化とはしない。

[condition_meaning_gate.py:1888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:1888) 付近へ次を置く。

```python
def declare_define_runtime_meaning(
    request: DefineRequest,
) -> MeaningWitnessDeclaration | ConditionalBranchMeaningDeclaration | None

def _extract_declared_conditional(
    source_text: str,
    spec: ConditionalBranchWitnessSpec,
) -> str

def _instrument_declared_selection(
    conditional: str,
) -> str

def _assert_conditional_branch_meaning(
    captured: CapturedDefineInputs,
    request: DefineRequest,
    declaration: ConditionalBranchMeaningDeclaration,
    *,
    cxx: str,
) -> ConditionalBranchMeaningEvidence
```

- `_extract_declared_conditional` は宣言された開始指令の完全一致が file 内にちょうど 1 件あることを要求し、preprocessor directive の深さを数えて対応する `#endif` を求める。対象深さより内側の `#if ADD_ANALYSIS` は許すが、重複する対象開始指令、未閉鎖、対象深さの `#elif` は red とする。
- `_instrument_declared_selection` は開始指令直後に selected marker、対応 `#endif` 直後に completed marker を挿入する。`#else` の有無には依存しない。
- `_assert_conditional_branch_meaning` は実体化 source を既存の no-follow 読み取り機構 [condition_meaning_gate.py:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:790) で捕捉し、要求値と既定値を別々に `-E -P` する。要求値では selected=1、completed=1、既定値では selected=0、completed=1を要求する。両観測が同じなら `conditional-meaning-not-discriminating` で red にする。
- compound report では `IZANAGI_SILO_LADDER_RUNG1=1` を companion として両ケースへ渡し、REPORT の値だけを 1 と 0 で変える。
- `ConditionalBranchMeaningEvidence` には `source_rel`、source/conditional/selected-body SHA-256、要求値と既定値の両 observation、両 preprocess argv、compiler identity を格納する。[condition_meaning_gate.py:2351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:2351) の green evidence 検査にも専用 schema を追加する。
- [condition_meaning_gate.py:2044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:2044) は declaration の exact type で既存 BACKOFF witness と新 witness を分岐する。witness 不一致は red、registry 外または要求値が対応外なら従来通り `unestablished` とする。admission 条件は変更しない。
- `MEANING_SUPPORTED_MACROS` は `{"BACKOFF_FIXED"} | set(CONDITIONAL_BRANCH_WITNESSES)` とし、[condition_meaning_gate.py:2765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/condition_meaning_gate.py:2765) の `__all__` に新しい定数、型、factory を追加する。
- [s1_direct_comparison.py:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s1_direct_comparison.py:229) は引数を `request: DefineRequest` にし、gate の factory へ委譲する。これで BACKOFF の既存宣言に加え、S1 が扱える `BACKOFF_NOINLINE` と `SORT_VARIANT` が配線される。
- positive control の実成果物を縮めるには、`s2_verify_calibration.py:108`、`s3_lock_coverage.py:95`、`s5_permutation_coverage.py:92`、`t152_write_intent_coverage.py:192`、`s8a_trigger_coverage.py:118` の `declaration=None` を同じ factory 呼び出しへ置換する。REPORT は [silo_ladder_rung1.py:2161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/silo_ladder_rung1.py:2161) を追随させる。
- patch、条件指令、configure/build 引数は一切変更しない。動かせない 8 macro の理由は既存 admission の名前一覧と完了時の worklog fragment に名前付きで残し、新しい台帳や admission schema は足さない。

## 第一群の選定

次の 13 件を新たに green へ動かす。全件で要求値は `1`、既定値は `0`。観測差は「要求値では宣言対象枝 marker が 1 件、既定値では 0 件、完了 marker は両方 1 件」である。

| macro | 所有 file と条件指令 | 補足 |
|---|---|---|
| `BACKOFF_NOINLINE` | [patches/silo-backoff-fixed.patch:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/silo-backoff-fixed.patch:55) `include/backoff.hh`, `#if BACKOFF_NOINLINE` | 要求値で `noinline` attribute を選択 |
| `SORT_VARIANT` | [patches/silo-sort-variant.patch:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/silo-sort-variant.patch:54) `cc/silo/transaction.cc`, `#if SORT_VARIANT` | 要求値で合成 comparator 枝、既定値で stock sort |
| `IZANAGI_BREAK_PERMUTATION` | [broken-silo-permutation-erase.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-permutation-erase.patch:9) | 要求値で erase positive control を compile-in |
| `IZANAGI_BREAK_PERMUTATION_SWAP` | [broken-silo-permutation-swap.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-permutation-swap.patch:9) | 要求値で swap positive control を compile-in |
| `IZANAGI_BREAK_LOCK_COVERAGE` | [broken-silo-lockskip-validation.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-lockskip-validation.patch:9) | `#else` 無し |
| `IZANAGI_BREAK_EARLY_UNLOCK` | [broken-silo-early-unlock-validation.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-early-unlock-validation.patch:9) | `#else` 無し |
| `IZANAGI_BREAK_NOREAD_VALIDATION` | [broken-silo-norw-validation.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-norw-validation.patch:9) | 対象 `#else` 内に `#if ADD_ANALYSIS` があるため深さ追跡が必要 |
| `IZANAGI_BREAK_HIGHKEY_VALIDATION` | [broken-silo-highkey-validation.patch:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-highkey-validation.patch:8) | 同じく入れ子あり |
| `IZANAGI_BREAK_WRITE_INTENT_ERASE` | [broken-silo-write-intent-erase.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-write-intent-erase.patch:9) | `#else` 無し |
| `IZANAGI_BREAK_WRITE_INTENT_FORGE` | [broken-silo-write-intent-forge.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-write-intent-forge.patch:9) | `#else` 無し |
| `IZANAGI_BREAK_WRITE_INTENT_OPSWAP` | [broken-silo-write-intent-opswap.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-write-intent-opswap.patch:9) | `#else` 無し |
| `IZANAGI_BREAK_WRITE_INTENT_PTRSWAP` | [broken-silo-write-intent-ptrswap.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/broken-silo-write-intent-ptrswap.patch:9) | `#else` 無し |
| `IZANAGI_SILO_LADDER_RUNG1_REPORT` | [patches/silo_ladder_rung1.patch:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/silo_ladder_rung1.patch:56) | companion `IZANAGI_SILO_LADDER_RUNG1=1` 固定下で REPORT だけを 1/0 比較 |

残す 8 件は次の理由で `unestablished` のままとする。

- **複数箇所を一体として証明する witness が必要:** `BACKOFF_REQUESTED_US` は header と TU の 4 条件箇所 [silo-backoff-requested-us.patch:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/silo-backoff-requested-us.patch:29)、`BACKOFF_TRIGGER_GATING` は約 12 箇所 [silo-backoff-trigger-gating-variant.patch:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/silo-backoff-trigger-gating-variant.patch:41)、`IZANAGI_SILO_LADDER_RUNG1` は 3 箇所 [silo_ladder_rung1.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/silo_ladder_rung1.patch:9)。代表 1 箇所だけを green にすると macro 全体の意味を過大主張する。
- **selector、template、診断が混在:** `SS2PL_LOCK_IMPL`、`SS2PL_LOCK_KIND`、`SS2PL_DLR`、`SS2PL_WFG_DIAG`。例えば `LOCK_KIND` は template 引数と条件枝の両方で使われる。[ss2pl-lock-protocol-study.patch:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/ss2pl-lock-protocol-study.patch:182)、[ss2pl-lock-protocol-study.patch:2304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/patches/ss2pl-lock-protocol-study.patch:2304)。単一枝 witness では意味を確立できない。
- **要求値と既定値で観測が変わらない:** `IZANAGI_BREAK_TRIGGER_MISATTR`。`#ifdef` は値 `1` と `0` の双方で真になる。defined/undefined 比較へ読み替えると request/default 契約を変えるため採らない。

## テスト計画

本段ではテストを実走していない。親が実装後に実測する。

- `orchestrator/tests/test_condition_meaning_gate.py::test_conditional_branch_witnesses_select_requested_and_omit_default`  
  13 macro を parameterize し、要求値で selected marker あり、既定値で無し、meaning green を確認する正例。
- `orchestrator/tests/test_condition_meaning_gate.py::test_conditional_branch_witness_rejects_non_discriminating_predicate`  
  条件を `#if 1` または `#if MACRO || 1` へ変え、要求値と既定値が同じ選択になる場合を red にする負例。恒真化を直接暴く。
- `orchestrator/tests/test_condition_meaning_gate.py::test_conditional_branch_witness_rejects_wrong_macro_directive`  
  宣言 macro と異なる macro の指令へ差し替え、unique directive 不在または非識別で red になる負例。
- `orchestrator/tests/test_condition_meaning_gate.py::test_nested_conditional_branch_witness_observes_outer_selection`  
  `NOREAD_VALIDATION` と `HIGHKEY_VALIDATION` の入れ子を受理する正例。
- `orchestrator/tests/test_condition_meaning_gate.py::test_nested_conditional_branch_witness_rejects_unbalanced_or_duplicate_target`  
  対応 `#endif` 欠落、対象開始指令重複を拒否する負例。
- `orchestrator/tests/test_condition_meaning_gate.py::test_ifdef_value_pair_is_not_a_meaning_witness`  
  `IZANAGI_BREAK_TRIGGER_MISATTR=1/0` が同じ枝を選ぶことを示し、factory が declaration を出さず `unestablished` を維持する。
- `orchestrator/tests/test_condition_meaning_gate.py::test_conditional_meaning_red_narrows_admission`  
  正しい枝では admission 正例、恒真化した枝では meaning red かつ admission 拒否という対を確認する。
- `orchestrator/tests/test_condition_meaning_gate.py::test_v1_domain_and_claim_boundaries_are_exact`  
  [test_condition_meaning_gate.py:1062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/tests/test_condition_meaning_gate.py:1062) の supported 集合を既存 1 件から 14 件へ、補集合を上記 8 件へ更新する。
- `orchestrator/tests/test_condition_meaning_gate.py::test_green_conditional_meaning_schema_rejects_missing_case_or_same_observation`  
  要求値または既定値 observation の欠落、同一観測、argv と macro の不一致を admission schema が拒否する負例。
- `orchestrator/tests/test_s1_direct_comparison.py::test_condition_meaning_declaration_delegates_supported_branch_witnesses`  
  `BACKOFF_NOINLINE=1` と `SORT_VARIANT=1` が gate factory の declaration を得る正例。
- `orchestrator/tests/test_s1_direct_comparison.py::test_promotion_contract_carries_only_remaining_unestablished_macro`  
  `SORT_VARIANT` は green、`BACKOFF_TRIGGER_GATING` は `unestablished` のままで、一覧から前者だけ消えることを確認する。
- `orchestrator/tests/test_s1_direct_comparison.py::test_branch_meaning_mismatch_rejects_prepared_cell`  
  materialized 指令を恒真化した S1 fixture が `DriverError` になる拒否側。
- `orchestrator/tests/condition_gate_test_support.py:38` 付近に、`#else` 無し、入れ子あり、compound companion の 3 fixture generator を追加する。production patch や実 build 引数は変更しない。
- 専用 driver については既存の gate-before-build テストへ「`declaration` が exact `ConditionalBranchMeaningDeclaration`」という assertion を追加する。少なくとも `test_s5_permutation_coverage.py::test_condition_gate_rejection_stops_s5_before_build` と `test_t152_write_intent_coverage.py` の preflight 検査を追随させる。

## 追随が要る pin と golden

- `condition_meaning_gate.py` 自体を bytes pin する repo 内 manifest は無い。[test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/tests/test_frozen_artifacts.py:41) の全 exact path を確認したが、campaign Python source は含まれない。
- `s1_direct_comparison.py` は [s8b_oracle_manifest.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/campaign/s8b_oracle_manifest.py:65) の `materializer` source として hash 対象になる。
- S1 編集後は [test_s8b_oracle_manifest.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/tests/test_s8b_oracle_manifest.py:87) の materializer SHA-256 literal を新しい実 bytes から更新する。
- 上の literal は `PIN_GATE_SPEC_RAW` の一部なので、その raw bytes の SHA-256 である `PIN_GATE_SPEC_SHA256` も [test_s8b_oracle_manifest.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/tests/test_s8b_oracle_manifest.py:61) で再計算する。schedule 内容は変わらないため `PIN_GATE_SCHEDULE_SHA256` は更新しない。
- 現在の materializer hash と reviewed-spec hashを repo と `output` の JSON、Markdown、JSONL、text から検索した結果、literal consumer は上記 2 箇所だけだった。
- `s2_verify_calibration.py`、`s3_lock_coverage.py`、`s5_permutation_coverage.py`、`s8a_trigger_coverage.py`、`t152_write_intent_coverage.py`、`silo_ladder_rung1.py`、指定された test/support filesを bytes pin する literal は見つからなかった。ladder の歴史 evidence は現行 bytes と不一致であることを意図的に検査しており、repin 対象ではない。[test_silo_ladder_rung1_evidence.py:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-meaning-witness/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1263)

## 危険と未解決

- 最大の brief 誤りは P1-d である。S1 だけを編集するなら、新たに green になるのは S1 が扱える `BACKOFF_NOINLINE` と `SORT_VARIANT` の 2 件だけで、10 positive control と REPORT の成果物は縮まらない。実成果物まで縮める要件を優先し、専用 driver 6 面を scope に含める裁定を推奨する。
- 枝 witness が確立するのは「要求値が実体化 source の宣言対象枝を選び、既定値が選ばない」という compile-time meaning までである。positive control が動的に期待 anomaly を起こすことや、その build が正しいことは主張しない。この境界を受け入れず dynamic semantics まで要求する場合、今回の 13 件は green にできないためユーザー裁定が要る。
- `IZANAGI_BREAK_TRIGGER_MISATTR` を green にするには `#ifdef` を `#if` に変えるか、既定値を undefined と読み替える必要がある。どちらも D1404/D1405 と要求値対既定値の制約に反するため提案しない。
- 残る複数箇所 macro には、全使用箇所を閉じた集合として宣言して全箇所の差を要求する別 witness が必要である。本 wave では実装しない。
- 新しい source hash は観測された materialized bytes を束縛するが、動的 reachability は証明しない。proof kind と成果物文言でこの限界を明記する。
- read-only の本段ではファイル変更、pytest、compiler witness の実走を行っていない。

## 総括

- macro 固有の conditional-selection witness を追加し、要求値と既定値の差を compiler 前処理で必須化する。
- 13 件を新たに green へ動かし、`BACKOFF_FIXED` と合わせて意味対応を 14/22 にする。
- 残る 8 件は macro 名と理由を保持し、`unestablished` を緩めない。
- S1 と実際の positive-control/ladder driver を配線し、S1 の hash golden 2 箇所を更新する。