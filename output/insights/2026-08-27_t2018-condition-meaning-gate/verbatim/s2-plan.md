## 総括

最小設計は、新規 `orchestrator/campaign/condition_meaning_gate.py` に次の三腕を閉じ込める。

1. `supply` — 適用後 worktree の CMake source を [`source_digest.parse_supplied_macros()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:739) で読み、対象 macro が実 TU 供給集合にあることを要求する。
2. `materialization` — 適用後 source から一意な EVOLVE-BLOCK 全体を抜く。式文字列の検索ではなく、条件骨格と代入文を含む block を評価 TU にそのまま組み込む。
3. `compiler-evaluated meaning` — 要求 define 値と明示 context を `-D<macro>=<value>` と整数変数として実 compiler に渡し、実行結果集合を独立な期待集合と exact 比較する。複数格子点では実現集合の単射性も検査する。

F707 fixture は「decoder source は存在するが CMake 供給集合だけ欠ける」形にして `macro-not-supplied` で落とす。F718 fixture は供給と compilation を通した上で、`BACKOFF_FIXED=1000` の観測 `{0}` と要求 `{1000}` の不一致で `decoded-meaning-mismatch` にする。これにより負例を別理由で kill できる。

証明種別は次の二つに限定する。

- `compiler-evaluated-applied-source-declared-context-meaning`
- `compiler-evaluated-applied-source-grid-injectivity-only`

「実 build の動的枝到達性を証明した」とは命名しない。

## 既存面と入力実在

| 入力 | 現在の実在場所 | 新 API / fixture field |
|---|---|---|
| 要求値 | [`_ordered_points()` の `Genome.flags["BACKOFF_FIXED"]`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:278)。格子本体は [33行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:33) | `cases[].define_value` |
| 宣言した意味 | 現 driver には無い | `proof_mode=declared-meaning` の `cases[].expected_values`。decoder から自動導出せず、独立 field にする |
| 評価 context | 現式の `start` は [`now_backoff` 式](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:70) が参照 | `contexts[].variables.start`。fixture は `1` と `2` を与え、乗算 hash の上位 bit 1/0 両向きを通す |
| decoder source | patch の [条件骨格と式](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:60)。本番入力は patch bytes ではなく適用後 `include/backoff.hh` | `contract.source_rel` と `contract.marker_id`。API の `ccbench_root` から解決 |
| 供給集合 | patch の CMake cache [12行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:12) と universal mapping [23行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:23) | `ccbench_root/cmake/Options.cmake` と `ccbench_root/cc/<protocol>/CMakeLists.txt` |
| compiler | 既存 source digest は [`_cpp_normalize()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1501) で preprocess だけを行う | `cxx=` keyword。新 gate は compile と生成 executable の実行まで行う |
| 出力型 | 現 backoff は `double now_backoff` | `result_identifier="now_backoff"`、`result_kind="float64"`。将来用に `int64` / `uint64` も閉じた列挙で許可 |

既存面について重要な境界がある。

- [`s8b_compiler_input.py:17`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/s8b_compiler_input.py:17) は動的 predicate reachability を証明しないと明記している。
- 同 module は [`flags.make` の `CXX_DEFINES` を構文検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/s8b_compiler_input.py:197)するが、返すのは compiler path だけで、[`CompilerInputManifest` には define 集合を保存しない](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/s8b_compiler_input.py:714)。したがって、この manifest を A2 の実値入力として扱ってはならない。
- 現在の materialization 検査は [marker の文字列存在](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:137)、供給検査は CMake source、binary 検査は [SHA-256 単射](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:161)までであり、F718 の意味一致には届かない。
- hole-literal 経路は [`assert_value_literal_consistent()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/p3_s4_loop.py:953) が scalar と実 literal を照合済みなので、新 module の対象外とする。

射程上の9 define は contract 候補として残すが、本 wave で具体 fixture を作るのは `BACKOFF_FIXED` のみとする。他の wire 1、enum 5、診断 0/1 2 は、実 source の result identifier と期待意味集合を別 wave で宣言するまで「対応済み」と数えない。

## file:line 実装 plan

`orchestrator/campaign/condition_meaning_gate.py` を新設し、次の順序で配置する。

- `:1-34` — module docstring と claim boundary。patch 適用、binary identity、動的枝到達性を証明しないことを固定する。
- `:36-70` — schema/proof mode/result kind 定数と `ConditionMeaningGateError`。例外に exact `reason_code`、`define_value`、`expected`、`observed` を保持する。
- `:72-125` — frozen dataclass:
  - `MeaningCase(define_value, expected_values | None)`
  - `EvaluationContext(variables)`
  - `DefineMeaningContract(protocol, source_rel, marker_id, macro, result_identifier, result_kind, proof_mode, contexts, cases)`
  - `MeaningEvidence(proof_kind, source_sha256, compiler, observed_by_define)`
- `:127-205` — `load_define_meaning_contract(path)`。JSON の未知・欠落 field、bool-as-int、空 context、重複 define、非有限 float、混在した expected 有無をすべて拒否する。`declared-meaning` は全 case に非空 `expected_values`、`grid-injectivity-only` は全 case で expected field 禁止とする。
- `:207-245` — `_read_ccbench_inputs(ccbench_root, contract)`。root、`source_rel`、Options、protocol CMake を strict resolve し、symlink traversal、root 外 path、read failure を拒否する。同じ source bytes を hash と TU 生成の両方へ使い、再読みによる mixed snapshot を作らない。
- `:247-270` — `_assert_macro_supplied(options_text, protocol_text, macro)`。既存 `source_digest.parse_supplied_macros()` を呼び、parser failure は `supply-set-unavailable`、対象不在は `macro-not-supplied` に正規化する。空集合を pass にしない。
- `:272-320` — `_extract_unique_decoder_block(source_text, marker_id)`。一意な BEGIN/END、順序、非空 body を要求し、`#if` から `#endif` を含む marker body 全体を返す。`double now_backoff = ...` という文字列検索結果だけを合格条件にしない。
- `:322-390` — `_render_evaluation_tu(contract, decoder_block)`。
  - case × context ごとに関数を生成。
  - 各関数の直前で `#define <macro> <define_value>`、直後で `#undef`。
  - context field は任意 C++ text でなく strict identifier と `uint64_t` literal だけから宣言。
  - 抽出 block 全体を関数本体へ挿入し、その後で strict identifier の `result_identifier` を読む。
  - `float64` は表示丸めを避け、`memcpy` した IEEE-754 bits を16桁 hexで出す。整数は exact decimal。
- `:392-445` — `_compile_and_execute(tu, cxx)`.
  - compiler は caller 指定を一度だけ resolve。
  - `source_digest.BUILD_FLAGS` と同じ `-std=c++20 -O3 -DNDEBUG` を使う。
  - compile rc 非0、compiler 不在、実行 rc 非0、stderr、出力行数・case index・token 形式の不一致をすべて拒否。
  - hard-coded timeout は置かない。親実測に compile/run 時間分布が無いため、未測定 timeout 述語を新設しない。
- `:447-520` — 公開 API:

```python
def assert_compiler_evaluated_define_meaning(
    contract: DefineMeaningContract,
    *,
    ccbench_root: PathLike[str] | str,
    cxx: str,
) -> MeaningEvidence:
    ...
```

処理順は schema → root/input read → supply → marker extraction → compile/run → declared meaning comparison → grid injectivity。意味不一致を先に判定するため、F718 は単射性エラーだけに縮退せず `decoded-meaning-mismatch` になる。期待宣言が無い mode では `grid-not-injective` だけを主張する。

既存 driver は編集しない。将来接続するなら、適用後 source が実在する [`patchharness.applied()` 内の materialization 後、prebuild 前](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:379)が唯一の候補だが、本 wave では呼び出しを追加しない。

## test / fixture plan

新規 fixture 配置:

```text
orchestrator/tests/fixtures/condition_meaning_gate/
├── supplied/
│   ├── cmake/Options.cmake
│   ├── cc/silo/CMakeLists.txt
│   └── include/backoff.hh
├── f707-missing-supply/
│   ├── cmake/Options.cmake
│   ├── cc/silo/CMakeLists.txt
│   └── include/backoff.hh
├── positive.json
├── f707.json
└── f718.json
```

`supplied/include/backoff.hh:1-15` と `f707-missing-supply/include/backoff.hh:1-15` は、現行 patch の marker、`#if/#else/#endif`、復号式を保持する。F707 側も decoder を保持し、CMake supply だけを欠かせる。

contract JSON の exact fields は以下とする。

```json
{
  "schema_version": "izanagi-condition-meaning-contract/v1",
  "proof_mode": "declared-meaning",
  "protocol": "silo",
  "source_rel": "include/backoff.hh",
  "marker_id": "silo-backoff-magnitude",
  "macro": "BACKOFF_FIXED",
  "result_identifier": "now_backoff",
  "result_kind": "float64",
  "contexts": [
    {"variables": {"start": 1}},
    {"variables": {"start": 2}}
  ],
  "cases": [
    {"define_value": 5, "expected_values": ["5"]}
  ]
}
```

予定 test file は `orchestrator/tests/test_condition_meaning_gate.py`。

- `:1-35` — fixture root resolver と `_any_cxx()`。既存慣例どおり `g++-13`、`g++-12`、`g++` の順で選び、全不在時だけ compiler-dependent node を skip。production API 自体は compiler 不在を error にする。
- `:38-66` — `test_positive_fixture_replays_current_decoder_with_declared_meaning`
  - 0、5、999を要求。
  - `start=1/2` の両 context で観測集合がそれぞれ `{0}`、`{5}`、`{999}`。
  - source hash、proof kind、格子単射性も確認。
- `:68-92` — `test_f707_fixture_rejects_macro_not_supplied`
  - decoder と期待意味は正例と同じ。
  - Options だけが `BACKOFF_FIXED` を供給しない。
  - `reason_code == "macro-not-supplied"` を要求。存在しない `cxx` を渡しても supply 理由が先に出ることを確認し、compiler failure との混同を防ぐ。
- `:94-128` — `test_f718_fixture_rejects_1000_decoded_as_zero`
  - case は 0→`{0}` と1000→`{1000}`。
  - supply、marker、compile は通る。
  - error evidence が `define_value=1000 / expected={1000} / observed={0}` であることを exact 確認。
- `:130-158` — `test_formula_text_in_comment_does_not_satisfy_gate`
  - 実代入を `now_backoff=0` に変え、元の909-byte式を comment に残した一時 source を使う。
  - 文字列が存在しても実行結果が違うため赤になることを固定。
- `:160-188` — `test_uniform_shift_is_rejected_even_when_grid_is_injective`
  - decoder を `BACKOFF_FIXED + 1` に変異。
  - 0、5、999の観測は相異なり単射性だけなら通るが、pointwise の期待意味比較で赤になる。
  - 「格子全体単射だけでは一様な意味ずれを捕らえない」限界の positive control。
- `:190-215` — `test_injectivity_only_mode_rejects_f718_collision`
  - `proof_mode=grid-injectivity-only`、期待値なしで0と1000を評価。
  - 両者が同じ観測集合 `{0}` なので `grid-not-injective`。
  - proof kind が meaning 一致を名乗らないことも確認。
- `:217-250` — malformed marker、compiler 不在、compile failure、出力 cardinality 不一致がすべて fail-closed になる node。

焦点検査 node は上記7本と test file 全体。read-only 段なので一切実走しておらず、緑とは報告しない。

## 変異 anchor 候補

| anchor | 変異 | kill する node |
|---|---|---|
| `condition_meaning_gate.py:247-270` `_assert_macro_supplied` | membership 検査を削除、または対象 macro を無条件追加 | `test_f707_fixture_rejects_macro_not_supplied` |
| `:272-320` marker extractor | marker 外の最初の代入や単なる substring を返す | `test_formula_text_in_comment_does_not_satisfy_gate`、malformed marker node |
| `:322-390` TU renderer | `-D<macro>=<define_value>` を固定0、または期待値から結果を生成 | positive と F718 の両方 |
| `:392-445` compile/run | compile rc、run rc、出力 cardinality のどれかを無視 | fail-closed node |
| `:447-485` declared meaning comparison | `observed != expected` を削除・反転 | F718 と uniform-shift node |
| `:486-510` grid injectivity | observed 集合の重複検査を削除 | injectivity-only F718 node |
| fixture `f707-missing-supply/cmake/Options.cmake` | `BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` を追加 | F707 node が期待した赤を失う |
| fixture `supplied/include/backoff.hh` の `/1000ULL` | divisor を1001等へ変更 | F718 evidenceまたは positive golden |
| `f718.json` の `expected_values=["1000"]` | decoder 観測から期待値を自動生成 | F718 negative が恒真化するため、closed-schema/expected field test で禁止 |

凍結 patch 自体は mutation 対象にせず、fixture の一時コピーまたは新 module の判定分岐だけを変異させる。

## scope 外と主張上限

- T-1999 は裁定待ちのまま。`backoff_extended_sweep.py`、`backoff_profile.py` その他 driver へ gate を義務化・配線しない。
- `patches/silo-backoff-fixed.patch`、`patches/ledger.json`、凍結 patch/ledger、`EXTENDED_SWEEP_US`、符号化式、格子定数は変更しない。
- 現 driver の1000点は依然として保護されない。新 module が存在するだけでは driver 実行時に発火しないため、「再発を閉じた」とは主張しない。
- 評価対象は、適用後 source から抽出した decoder block を standalone TU で実 compiler に通した結果である。ccbench 本体 TU の include、全 macro 環境、実行時の枝到達性までは証明しない。
- `contexts` は宣言された有限 witness のみ。`start` の全 `uint64_t` 値域や実 `rdtscp()` 分布を全称証明しない。F718 の1000→0はこの式では context 非依存だが、一般の乱択 mode の完全分布証明にはならない。
- `source_digest.parse_supplied_macros()` が示すのは CMake source 上の供給集合であり、完成 build の `flags.make` に現れた exact define 値ではない。後者を義務化するなら T-1999 または `s8b_compiler_input` 拡張の裁定が別途必要。
- 単射性のみの mode は一様な単位ずれ、offset、scale、別 enum 命名を捕らえない。期待意味を独立宣言した `declared-meaning` mode だけが、指定 context 上の pointwise 意味一致を主張できる。
- 他8 define は射程に残るが、具体的 result identifier、context、期待意味集合が未宣言なので本 wave の検証済み対象に含めない。
- docs、commit、全走、実 mutation、land は親担当。静的調査のみで、pytest は未実走。