# 結論

親 brief の **P1 は偽**です。したがって、この wave の現時点の scope は不変条件どおり「設計凍結 + ユーザー裁定パッケージ」へ落とすべきです。実装は、producer 契約を狭める明示承認を得た後に限ります。

根拠は次の2点です。

- `.claude/agents/coder-v4-autonomous.md:23,60` が禁止するのはコメントと継続行で、`<式>` 内の関数呼び出し、共有状態参照、算術式を禁止していません。
- `patches/silo-backoff-fixed.patch:66-68` はむしろ「既存 silo API を呼ぶ straight-line code」を許す宣言です。全関数呼び出しを拒否する P3 は明確な契約縮小です。

以下は、その裁定後に使える条件付き実装プランです。pytest は実走しておらず、緑とは報告しません。

## P1〜P4 の判定

| 前提 | 判定 | 根拠 |
|---|---|---|
| P1: 既存契約を狭めない | **反対** | role の `<式>` は未限定で、骨格コメントは既存 API 呼び出しも許している。call-free DSL または literal-only DSL は producer 契約を狭める。 |
| P2: 単一宣言文だけ | **賛成** | role の出力テンプレート `.claude/agents/coder-v4-autonomous.md:54-63` と一致し、複文、追加宣言、制御フローを閉じられる。 |
| P3: `clocks_per_us` を含む算術・比較・三項 | **反対** | `CoderProposal.value`、`BACKOFF_FIXED=int(value)`、実際の `now_backoff` の一対一帰属を壊す。現行 `assert_value_literal_consistent()` は式を評価せず、式中に value と同じ数があれば通し得る。 |
| P4: type→raw size→character→token→parse→semantic | **賛成** | trigger v1 の既存設計と揃い、拒否優先順位と資源消費を固定できる。ただし、この新 gate 自体は既存拒否理由を守るため構造検疫と denylist の後に置く。 |

推奨する v1 は **正の十進 literal 1個だけ**です。`clocks_per_us` は骨格から参照可能でも、候補値を実行時関数へ変えてしまうため v1 では受理しません。

親 P3 を採る場合は、先に `CoderProposal.value` と genome の意味を「実際の backoff 値」から別の policy ID へ変更し、帰属整合、campaign identity、WAL を再設計する必要があります。これは本 scope を超えます。

## 新 module と公開 API

新規配置は `orchestrator/campaign/backoff_hole_grammar.py` とします。

予定する file:line 構成は次のとおりです。

- `backoff_hole_grammar.py:1-35`: module docstring、`__all__`、文法 version、資源上限。
- `backoff_hole_grammar.py:37-70`: 固定 rule ID と `BackoffGrammarDecision`。
- `backoff_hole_grammar.py:72-135`: ASCII character gate と有限 lexer。
- `backoff_hole_grammar.py:137-185`: exact-statement parser。
- `backoff_hole_grammar.py:187-225`: decimal semantic 検査と公開入口。

公開 API は次に固定します。

```python
@dataclass(frozen=True)
class BackoffGrammarDecision:
    accepted: bool
    stage: str | None
    rule_id: str | None

def validate_backoff_implementation(
    implementation: object,
) -> BackoffGrammarDecision:
    ...
```

戻り値に候補文字列、token text、literal、例外文は含めません。拒否 rule ID は次の固定集合だけです。

```text
backoff-grammar.type.v1
backoff-grammar.raw-size.v1
backoff-grammar.character.v1
backoff-grammar.token-count.v1
backoff-grammar.parse.v1
backoff-grammar.semantic.v1
```

### 判定順と資源上限

| 順位 | 検査 | 上限・規則 | 根拠 |
|---:|---|---|---|
| 1 | type | `type(value) is str` | bool、bytes、str subclass を暗黙変換しない。 |
| 2 | raw size | Unicode code point 数と UTF-8 byte 数の双方が最大 **4096** | trigger v1 の凍結値 `README.md:46-49` を再利用。既存 denylist の 256 KiB より先に小さく閉じる。 |
| 3 | character | ASCII `[A-Za-z0-9_.=; \t]` のみ | 改行、backslash、コメント delimiter、括弧、演算子、Unicode homoglyph を parser 前に拒否。 |
| 4 | token | 空白を除き最大 **5 token** | 受理文は `double`, `now_backoff`, `=`, literal, `;` の厳密5 token。6個目は必ず受理言語外。 |
| 5 | parse | exact sequence、EOF 必須、最大深度 **0** | v1 は括弧も再帰構文も持たない。prefix-only acceptance を禁止。 |
| 6 | semantic | decimal が有限で `1 <= value <= 1000` | role の `value` 契約 `.claude/agents/coder-v4-autonomous.md:58` に一致。指数、suffix、octal風 leading zero を拒否。 |

## BNF

P2 は採用し、P3 は採用しません。

```bnf
<implementation> ::= H* "double" H+ "now_backoff" H* "=" H*
                     <decimal> H* ";" H*

<decimal>        ::= <integer>
                   | <integer> "." <digits>

<integer>        ::= "0"
                   | <nonzero-digit> <digits-opt>

<digits>         ::= <digit> <digits-opt>
<digits-opt>     ::= <digit>*
<digit>          ::= "0" | "1" | "2" | "3" | "4"
                   | "5" | "6" | "7" | "8" | "9"
<nonzero-digit>  ::= "1" | "2" | "3" | "4" | "5"
                   | "6" | "7" | "8" | "9"

H                ::= " " | "\t"
```

semantic 段で `0`、`1000` 超、非有限化する表記を拒否します。`001`、`20.`、`1e2`、suffix 付き literal は受理しません。

- `clocks_per_us`: v1 では拒否。runtime-dependent な式となり、単一 `coder.value` へ帰属できないため。
- `Backoff_`: 共有 atomic なので拒否。
- `rdtscp()`: 非決定ソースかつ関数呼び出しなので拒否。
- 算術、比較、三項: v1 では拒否。定数式でも現行帰属検査は式の評価値を照合しないため。

## `quarantine()` への配線

### 編集点

- `orchestrator/campaign/p3_s4_loop.py:59`: `backoff_hole_grammar` を import。
- `orchestrator/campaign/diff_quarantine.py:41-49`: `DiffRejectSubtype.BACKOFF_GRAMMAR = "backoff-grammar"` を追加。
- **唯一の執行点**: `orchestrator/campaign/p3_s4_loop.py:278`、現在の host-effect block の直後かつ `if write:` の直前。

概念上の順序は次です。

```text
run_one_iteration
  帰属整合 : p3_s4_loop.py:967-971
    ↓
quarantine
  構造 diff 検疫 : p3_s4_loop.py:245-247
    ↓ pass のみ
  coder_effect_gate denylist : p3_s4_loop.py:248-277
    ↓ pass のみ
  backoff grammar : p3_s4_loop.py:278 に新設
    ↓ pass のみ
  write : 現 p3_s4_loop.py:278-281
```

これにより、同じ候補が複数 gate に抵触しても既存理由が先に残ります。

- value 不一致は従来どおり `AttributionMismatch`。
- `#define`、コメント、marker 偽装などは従来どおり `HOLE_ESCAPE`。
- `system`、`read`、無条件 loop などは従来どおり `HOST_EFFECT`。
- 上記を通った意味逸脱だけが `BACKOFF_GRAMMAR`。

trigger は `p3_s4_loop.py:218-230` で正準化が必要なため構造検疫前にあります。backoff は入力を書き換えないので、**exact marker membership という軸分岐は対称、適用位置は意図的に非対称**とします。同じ pre-structure 位置へ置くと、既存 `HOLE_ESCAPE` を grammar reject に置換して親不変条件1に違反します。

新しい digest は固定値だけで構成します。

```python
{
    "rejection_type": "diff-quarantine",
    "subtype": "backoff-grammar",
    "reason": "backoff hole が閉じた受理文法 v1 外",
    "diff_region": source_rel,
    "template_diff_id": marker_id,
    "evidence": "rule_id=backoff-grammar.parse.v1 stage=parse",
    "rule_id": "backoff-grammar.parse.v1",
}
```

## 明示負例

「実測1の6形」は、基準正例を除く表の6行として数えました。

| 出所 | 形 | 推奨 v1 の判定 | 落とす規則 |
|---|---|---|---|
| 親1 | `Backoff_.store(0, ...)` の追加 | reject | comma、括弧などを `character.v1`。表記差で文字段を抜けても EOF 必須の `parse.v1`。 |
| 親2 | `static double s; s = s * 0.9;` | reject | `*` を `character.v1`。複文自体も5 token超。 |
| 親3 | `50 + (rdtscp() & 1)` | reject | `+`, `(`, `)`, `&` を `character.v1`。 |
| 親4 | `now_backoff_unused = 50; now_backoff = 0;` | reject | 5 token超の `token-count.v1`。 |
| 親5 | `goto izanagi_skip;` | reject | exact declaration sequence 不一致の `parse.v1`。 |
| 親6 | `(clocks_per_us > 1000) ? 50 : 25` | reject | 比較・括弧・三項文字を `character.v1`。 |

落とせない形は推奨 v1 にはありません。一方、**親 P3 をそのまま採れば親6は落ちません**。これは `p3_s4_loop.py` の敵対形というより、親自身が受理すると決めた境界正例です。brief の「6形が意味を壊す実例」という記述とは整合していません。

追加する敵対形は次です。

| 追加敵対形 | 狙い | 落とす規則 |
|---|---|---|
| `double now_backoff = Backoff_.load(std::memory_order_acquire);` | 共有状態の読出し | `character.v1` |
| `double now_backoff = rdtscp();` | 非決定関数 | `character.v1` |
| `double now_backoff = __LINE__;` | builtin風識別子 | `parse.v1` |
| `double now_backoff = 1e2;` | 現行 regex が部分 literal と誤認し得る指数表記 | `semantic.v1` |
| `double now_backoff = 001;` | C++ octal風 spelling | `semantic.v1` |
| `double now_backoff = 0;` | role 値域外 | `semantic.v1` |
| `double now_backoff = 1000.0001;` | 上限超過 | `semantic.v1` |
| `double now_backoff = 20;\ngoto x;` | 改行による複文 | `character.v1` |
| `double now_backoff = 20; // tail` | コメントで後続を隠す | `character.v1` |
| `double now_backoff = сlocks_per_us;` | ASCII `c` でない homoglyph | `character.v1` |

## 恒真性の反証設計

段4の mutation 事前登録は次の対応で固定します。

| 変異 | 殺す負例 |
|---|---|
| validator を無条件 `accepted=True` にする | 親1〜6と追加負例すべて |
| parser の EOF 確認を削除する | 親4、`20; goto x;` |
| character gate を削除する | rdtscp、コメント、改行、Unicode homoglyph |
| decimal semantic を削除する | `1e2`、`001`、`0`、`1000.0001` |
| marker 条件を削除または全 marker へ拡張する | trigger 32正準集合と sort comparator の非影響テスト |
| grammar を構造検疫より前へ移す | `#define` が `HOLE_ESCAPE` でなく grammar reject になる precedence テスト |
| raw/token cap を無効化する | 4097 byte、6 token の境界負例 |

少なくとも1件の正例と複数の負例を同じ mutation run に含め、単に「全部 reject」する実装も緑にしません。

## Disclosure-free 化

具体策は次です。

- `BackoffGrammarDecision` へ token text、identifier、literal、入力長、入力断片を持たせない。
- lexer/parser の内部例外を外へ出さず、全例外を固定 rule ID へ射影する。
- `reason` と `evidence` は固定 allowlist からだけ構成し、`repr(exception)` や受領 token を連結しない。
- `DiffQuarantineResult.digest` へ候補由来文字列を入れない。
- `record_diff_reject()` は現在 `p3_s4_loop.py:287-316` で implementation を variant ID の SHA-256 入力にだけ使い、WAL payload へ原文を保存していない。この性質を維持する。
- WAL の `genome.BACKOFF_FIXED` は宣言済み scalar で、候補 literal の字句 bytes ではない。`020.0` のような生 spelling は保存しない。
- critic へは固定 subtype、固定 reason、固定 rule ID だけを渡す。未知 rule ID は表示せず固定 general rejection へ落とす。
- sentinel を identifier、literal、後続文へ埋め込み、`res.digest`、WAL payload、`load_diff_rejections()`、`render_rejections()` の全射影に sentinel が無いことを1本の回帰で検査する。

## テスト計画

追加先は `orchestrator/tests/test_p3_s4_loop.py` のみとし、既存 assertion の期待値は変更しません。

予定 nodeid は次です。

- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_accepts_canonical_decimal_literals`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_rejects_measured_six_forms`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_rejects_additional_adversarial_forms`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_rejection_stage_precedence`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_raw_size_boundary_4096_4097`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_token_boundary_5_6`
- `orchestrator/tests/test_p3_s4_loop.py::test_quarantine_preserves_structural_reject_before_backoff_grammar`
- `orchestrator/tests/test_p3_s4_loop.py::test_quarantine_preserves_host_effect_reject_before_backoff_grammar`
- `orchestrator/tests/test_p3_s4_loop.py::test_quarantine_rejects_backoff_grammar_before_write`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_reject_is_disclosure_free_through_wal_and_critic`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_grammar_dispatch_is_exact_marker_only`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_allowlist_mutation_preregistration_has_positive_and_negative_controls`

既存 pin 回帰として次をそのまま走らせます。

- `test_trigger_quarantine_accepts_exact_32_canonical_predicates_with_outer_space`
- `test_trigger_quarantine_materializes_all_outer_whitespace_identically`
- `test_trigger_quarantine_rejects_noncanonical_text_before_structure_inspection`
- `test_sort_quarantine_preserves_outer_whitespace_bytes`
- `test_trigger_membership_does_not_change_sort_or_backoff_markers`
- `test_value_literal_consistency_accepts_match`
- `test_value_literal_consistency_rejects_mismatch`
- `test_candidate_value_literal_and_implementation_bytes_never_reflect_to_projections`

ただし `test_effect_scanner_runs_only_after_structure_and_sees_exact_written_hole_bytes` (`test_p3_s4_loop.py:230-286`) は現在、backoff marker で複文を `passed=True` と期待しています。P2 と同時には成立しません。

既存 assertion を変えずに維持するには、このテストの fixture marker だけを sort marker へ移し、軸共通の「構造検疫後に exact bytes を denylist へ渡す」テストとして残します。fixture 変更すら不可なら、P2 と「現行期待値を変更しない」は論理的に両立しません。

親が実走する場合の対象コマンドは `python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop.py::<nodeid>` とし、本プランでは実行していません。

## `quarantine()` 呼び手の静的波及

現行 production source を数え直すと、定義元を含め **8 module、14 call site** です。親 brief の「4 module」は現行 tree では不足しています。

| 呼び手 | call site | marker | 受理集合 |
|---|---:|---|---|
| `p3_s4_loop.py` | 991 | default backoff、dry | **縮小** |
| `p3_s4_loop.py` | 999 | default backoff、write | **縮小** |
| `p3_s4_loop_sort.py` | 156 | sort | 不変 |
| `p3_s4_loop_sort.py` | 456 | sort preview | 不変 |
| `p3_s4_loop_sort.py` | 564 | sort fixture | 不変 |
| `p3_s4_loop_trigger_gating.py` | 421 | trigger | 不変 |
| `p3_s4_loop_trigger_gating.py` | 890 | trigger preview | 不変 |
| `p3_s4_loop_trigger_gating.py` | 1007 | trigger fixture | 不変 |
| `p3_autonomous_workload_trial.py` | 1595 | trigger preview | 不変 |
| `s1_verify_extime_calibration.py` | 342 | trigger | 不変 |
| `s1_direct_comparison.py` | 666 | trigger または sort のみ | 不変 |
| `s6_sort_sweep.py` | 333 | sort candidate ref | 不変 |
| `s6_sort_sweep.py` | 354 | sort evaluation | 不変 |
| `s8a_trigger_sweep.py` | 434, 456 | trigger | 不変 |

`s1_direct_comparison.py:651-659` の `backoff_fixed_best` は patch を適用するだけで `quarantine()` を呼ばないため不変です。

したがって、親の「backoff marker の live consumer は `run_one_iteration` の2箇所だけ」は現行 tree でも正しい一方、「呼び手は4 module」は誤りです。テスト側の直接 caller は7 moduleありますが、exact marker guard により sort/trigger 系の受理集合は変わりません。

## 裁定パッケージ

実装へ進むには、次の択一をユーザーへ返す必要があります。

1. **推奨:** backoff role の `<式>` を「1〜1000の正準十進 literal」へ狭めることを明示承認し、role、review ledger、adapter、manifest を同一変更単位で更新した後、上記 v1 を実装する。
2. P3 の動的式を維持する代わりに、`CoderProposal.value`、genome identity、帰属整合を policy-expression 対応へ再設計する。別 wave 相当。
3. role 契約を維持し、本 wave は設計凍結だけで終了する。

現在の no-touch 条件下では `.claude/agents/coder-v4-autonomous.md:23,60` を変更してはならず、1を暗黙採用できません。

## 総括

- **プランの要点**
  - P2 を採り、P3 は退け、`orchestrator/campaign/backoff_hole_grammar.py` に literal-only v1 を置く。
  - 執行点は `p3_s4_loop.py:278` の1箇所。順序は帰属整合 → 構造検疫 → denylist → backoff grammar → write。
  - trigger と sort は exact marker guard と既存回帰で1 bitも変えない。
  - 実走はしておらず、静的検査のみ。

- **未解決の設計択一**
  - producer 契約を literal-only へ狭める明示承認を出すか。
  - あるいは P3 の動的式を残し、scalar value と campaign identity を再設計するか。

- **親 brief で誤っていると判断した点**
  - P1「既存契約を狭めない」は偽。
  - 親 P3 のもとでは `clocks_per_us` 三項形は拒否できず、敵対負例扱いと受理方針が矛盾する。
  - `quarantine()` の production 呼び手は現行 tree では4 moduleでなく8 module、14 call site。
  - 現行 `test_effect_scanner_runs_only_after_structure_and_sees_exact_written_hole_bytes` の backoff 複文受理期待はP2と両立せず、fixture の軸移動が必要。