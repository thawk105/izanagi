結論として、親の provisional 裁定 (P1)〜(P4) はすべて採用する。ただし「JSON 拒否」は parser に渡された raw 値についての主張に限定し、「監査済み」は静的な byte 一致の射程に限定する。本回答ではコード編集・テスト実行・再実測を行っていない。

## 設計判断

- `(P1)` 長さ 5 の ASCII `'0'/'1'`、`GATEABLE_REASONS` 順 LSB-first を採用する。
- `(P2)` `s8a_trigger_sweep.predicate_for()` を呼ばない独立実装を採用する。
- `(P3)` 32 点の手書き literal 表を基礎 oracle とし、campaign 9 点・freeze 3 点を上位 anchor として重ねる。
- `(P4)` 親 brief の限定付き表現は妥当。ただしテスト実測後にだけ名乗れる。

根拠となる軸順は [`axis_trigger_gating.py:50`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/axis_trigger_gating.py:50)、既存の独立 emitter は [`s8a_trigger_sweep.py:117`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s8a_trigger_sweep.py:117) と [`s8a_trigger_sweep.py:215`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/s8a_trigger_sweep.py:215) にある。

## 新規 leaf の API

`orchestrator/campaign/reflux_ir.py` の公開 API は次に閉じる。

```python
@dataclass(frozen=True, slots=True)
class TriggerGateIR:
    mask: int

    def __post_init__(self) -> None: ...

def parse_wire(wire: str) -> TriggerGateIR: ...
def emit_wire(ir: TriggerGateIR) -> str: ...
def emit_predicate(ir: TriggerGateIR) -> str: ...
```

`__all__` もこの 4 名だけにする。

| API | 受理集合 | 拒否集合 |
|---|---|---|
| `TriggerGateIR(mask)` | `type(mask) is int` かつ `0 <= mask <= 31` の32値 | `bool`、`IntEnum`、int subclass、float、str、`-1`、`32` 以上。型違反は `TypeError`、範囲違反は `ValueError` |
| `parse_wire(wire)` | `type(wire) is str` かつ正規表現相当 `[01]{5}` の32文字列だけ | 空、長さ違い、前後・内部空白、tab/newline、`+`/`-`、`0b`/`0B` prefix、英字・大文字表記、underscore、全角数字、bytes、int、list/dict/JSON object・array、引用符込み JSON string |
| `emit_wire(ir)` | exact `TriggerGateIR` の32値だけ | raw int、duck type、subclass を含む他の全値。暗黙変換しない |
| `emit_predicate(ir)` | exact `TriggerGateIR` の32値だけ | 同上。reason 列・任意 C++ 文字列は受け取らない |

正例は次のとおり。

```python
parse_wire("10100") == TriggerGateIR(mask=5)
emit_wire(TriggerGateIR(mask=5)) == "10100"
```

`"10100"` の文字位置 0 と 2 が bit 0 と bit 2 を表すため、mask 5 は `lock-conflict + readvali-tid` になる。

注意点として、`parse_wire('"10100"')` や `parse_wire({"mask": 5})` は拒否できるが、上流で `json.loads('"10100"')` された後の値は通常の `"10100"` と識別不能である。「JSON 由来なら正準文字列でも拒否する」という provenance 要件まで意味するなら、typed transport/envelope が別途必要であり、本 wave の leaf だけでは実現できない。

## 正準 wire と bit 会計

| 文字位置 | mask bit | reason | C++ enum |
|---:|---:|---|---|
| 0 | 0 | `lock-conflict` | `kLockConflict` |
| 1 | 1 | `update-absent` | `kUpdateAbsent` |
| 2 | 2 | `readvali-tid` | `kReadValiTid` |
| 3 | 3 | `readvali-locked` | `kReadValiLocked` |
| 4 | 4 | `node-vali` | `kNodeVali` |

有効 wire の個数は厳密に 32 なので容量は `log2(32) = 5 bit`。各 mask に対する表記数は 1 なので、空白・順序・prefix・同義表現による追加 lexical channel は `log2(1) = 0 bit` である。ASCII では物理的に 5 byte だが、許された語彙の選択肢は32個に閉じている。

ただし、transport metadata、呼出時刻、JSON decode 前の framing などはこの leaf の監査対象外であり、「end-to-end で side channel がない」とは名乗れない。

## emitter 方針

`emit_predicate()` は次の規則を独自実装する。

1. 先頭項を常に `izanagi_abort_reason_ == IzanagiAbortReason::kUnset` とする。
2. bit 0 から bit 4 へ走査し、立っている bit の enum 等値項だけを上表順で追加する。
3. `" || "` で結合し、exact prefix `izanagi_gate_pass = ` と末尾 `;` を付ける。
4. 先頭・末尾空白、改行、コメント、directive は一切出さない。

`predicate_for()` を共有すると、新旧実装の全32点差分検査が同じ関数を左右から呼ぶ恒真検査になる。fitness 帰属を守る部品では独立性の方が drift risk より重い。したがって `(P2)` を採用する。

drift は次で fail-closed にする。

- 新 leaf は `GATEABLE_REASONS` だけを軸正本から import する。
- reason→enum の5組は leaf 内に literal で持ち、その reason 列が `GATEABLE_REASONS` と exact 一致しなければ import 時に `RuntimeError`。
- `assert` は `python -O` で消えるため使わない。
- `s8a_trigger_sweep`、その `_CPP_ENUM`、`predicate_for` は import しない。
- 全32点の literal・独立差分・artifact anchor で drift を検出する。

## file:line 実装プラン

新規ファイルなので、以下は実装時の予定行ブロックである。物理的な文字列折返しで多少移動しても、記載した symbol 境界を維持する。

### `orchestrator/campaign/reflux_ir.py`

- `new:L1-L15`: P1 の機械部品だけであり、production wiring・origin ledger・constraint/no-good cut を実装しない旨の module docstring。
- `new:L17-L38`: imports、`__all__`、固定幅 5、mask 上限 32、reason→enum literal 5 組、[`GATEABLE_REASONS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/axis_trigger_gating.py:50) との明示的 fail-closed 照合。
- `new:L41-L56`: `TriggerGateIR`。exact int と `[0,31]` を検査し、frozen/slots で余分な状態を持たせない。
- `new:L59-L68`: private exact-type guard。wire/predicate emitter の raw int coercion を禁止。
- `new:L71-L88`: `parse_wire()`。`.strip()`、`int()`、JSON decode は使わず、exact 5 ASCII chars を LSB-first で mask 化。
- `new:L91-L101`: `emit_wire()`。通常の `format(mask, "05b")` は MSB-first なので使わず、bit 0→4 を明示走査。
- `new:L104-L119`: `emit_predicate()`。独立 literal enum mapping から exact 1 行を構成。

### `orchestrator/tests/reflux_ir_expected_goldens.py`

[`s1_expected_goldens.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/s1_expected_goldens.py:1) の家の型を踏襲する。

- `new:L1-L20`: test-only、production import 禁止、runtime 導出禁止、変更契約を明記。
- `new:L22-L170`: `EXPECTED_ROWS` を mask 0〜31 順の32 literal rowとして手書きする。各 row は `(mask, wire, predicate)`。新旧いずれの emitter の出力から生成・貼付しない。
- `new:L172-L225`: 六つの既存 campaign provenance path・既存 SHA・entry→mask 対応を literal で置く。distinct mask は9点。
- `new:L228-L242`: freeze の六 record→mask 対応を literal で置く。distinct mask は3点。
- production module、artifact、freeze をこの台帳の import 時に読まない。

### `orchestrator/tests/test_reflux_ir.py`

- `new:L1-L35`: test path 設定、production leaf、独立 s8a emitter、執行側 syntax gate、test-local golden の import。
- `new:L38-L115`: 値型・wire parser・round-trip・拒否閉包。
- `new:L118-L180`: 32 literal byte 比較、旧 emitter 差分、全32点の現行 identifier gate 照合。
- `new:L183-L235`: campaign 9点、freeze 3点の実 artifact anchor。
- `new:L238-L275`: AST による golden literal 性と、新 leaf の旧 emitter 非依存検査。

## 独立 golden の層構造

| 層 | record 数 | distinct mask | 被覆集合 |
|---|---:|---:|---|
| 凍結 bytes | 6 record | 3 | `{4, 8, 31}` |
| campaign 記録 | 複数 campaign の重複 record | 9 | `{0,1,4,5,8,9,12,13,31}` |
| 手書き literal 表 | 32 row | 32 | `{0..31}` |
| 既存独立実装との差分 | 32 comparison | 32 | `{0..31}` |

これらは加算しない。freeze の3点は campaign 9点の部分集合で、campaign 9点は32点の部分集合である。union は32点のまま。

freeze は balanced/read-heavy の `g_rl`、write-heavy の `g_rt`、3 workload の `ident_all` という六 record だが、distinct mask は3点にすぎない。[`known_axes_freeze.json:18`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/s1-freeze/known_axes_freeze.json:18)、[`known_axes_freeze.json:244`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/s1-freeze/known_axes_freeze.json:244)、[`known_axes_freeze.json:470`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/s1-freeze/known_axes_freeze.json:470) を読む。

恒真化は次で防ぐ。

- `EXPECTED_ROWS` は `ast.literal_eval()` 可能な literal assignment に限定し、call/comprehension/import 導出を拒否する。
- golden module に `campaign` / production import がないことを静的検査する。
- production leaf が `s8a_trigger_sweep` / `predicate_for` を import・参照しないことを静的検査する。
- campaign/freeze tests は emitter が作った値ではなく、checked-in artifact を直接読む。
- emitter の1文字変更、golden の1セル変更、artifact entry の変更、旧 emitter 呼出への置換が、それぞれ少なくとも一つの異なる検査を落とす構造にする。

AST 検査は「実行時に emitter から導出していない」ことを保証するが、過去に誰が literal をどう転記したかまでは証明しない。その由来はレビューと記録契約で担保する。

## 新設テスト一覧

| テスト関数 | 落とす欠陥 |
|---|---|
| `test_trigger_gate_ir_accepts_exact_mask_domain` | 0/31 境界の欠落、32点未被覆 |
| `test_trigger_gate_ir_rejects_non_exact_int_or_out_of_range` | `bool` の int 扱い、負値、bit 5 以上、暗黙 coercion |
| `test_wire_round_trip_matches_all_32_literal_rows_lsb_first` | MSB/LSB 反転、bit位置交換、round-trip 非恒等 |
| `test_parse_wire_rejects_noncanonical_strings` | 空白・prefix・符号・長さ違い・Unicode・引用符付きJSONの受理 |
| `test_parse_wire_rejects_non_string_inputs` | int/bytes/list/dict/JSON object の受理 |
| `test_emitters_reject_non_ir_inputs` | raw int や duck type の暗黙受理 |
| `test_emitter_matches_32_literal_predicates_byte_for_byte` | enum、順序、空白、semicolon、`kUnset` の任意の drift |
| `test_emitter_matches_independent_s8a_predicate_for_all_32_masks` | 新旧実装の全32点差異 |
| `test_all_32_predicates_match_current_execution_gate_surface` | 将来の禁止識別子追加との不整合、改行・末尾空白 |
| `test_golden_ledger_is_literal_complete_unique_and_production_independent` | 欠落/重複 mask、同一 wire/predicate、runtime 導出、production import |
| `test_campaign_provenance_anchors_exact_nine_masks` | 9点集合の欠落、artifact bytes と literal の差異、誤った mask 名対応 |
| `test_known_axes_freeze_anchors_exact_three_masks` | 六 record を六点と誤認、freeze bytes と literal の差異 |
| `test_reflux_ir_does_not_depend_on_s8a_emitter` | `predicate_for` 再利用による差分テストの恒真化 |

既存 [`test_s8a_trigger_sweep.py:54`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_s8a_trigger_sweep.py:54) の EFF3 構造検査は再実装しない。具体的には、候補名/category、`2^N+ident_all` 点数、入力順正規化、quarantine、campaign identity、frequency、provenance merge、floor/replay のテストは追加しない。`_parse_predicate()` の複製もしない。新規検出力は canonical parser と全5-bit・全32点の byte oracle に限定する。

## 編集ファイルの所有集合

段5の実装子が編集してよい完全な集合は、次の新規3ファイルだけである。

- `orchestrator/campaign/reflux_ir.py`
- `orchestrator/tests/reflux_ir_expected_goldens.py`
- `orchestrator/tests/test_reflux_ir.py`

既存ファイルの変更はゼロ。特に次は1 byteも変更しない。

- `orchestrator/campaign/axis_trigger_gating.py`
- `orchestrator/campaign/s8a_trigger_sweep.py`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- `orchestrator/tests/test_s8a_trigger_sweep.py`
- `orchestrator/tests/s1_expected_goldens.py`
- `output/s1-freeze/known_axes_freeze.json`

実装子は docs、spool、insights、commit を扱わない。親 brief が要求する段7の insight と worklog/decisions spool fragment は親所有であり、実装子の edit set には含めない。

モジュール名は親 brief どおり `reflux_ir.py` とする。P1 の「表現・parse・emit」だけを所有し、並行 P3 wave が所有する `origin`、ledger、CAS、replay、永続化という語彙・ファイル面を一切持たないため、`wave-t244-p3-origin-ledger` と所有衝突しない。

## production 受理集合

本 wave では wiring しない。

現行 production は JSON の `coder.implementation` をそのまま値型へ入れる [`p3_s4_loop_trigger_gating.py:571`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_s4_loop_trigger_gating.py:571) 経路を維持し、identifier blacklist は [`p3_s4_loop_trigger_gating.py:118`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/p3_s4_loop_trigger_gating.py:118) のままである。新 leaf は production から import されず、テストだけが消費する。

したがって、新 parser 自身の受理集合は32値に閉じるが、production の受理集合は不変である。将来、`implementation` 経路を `parse_wire()` → `emit_predicate()` に差し替える変更は、自由な1行 C++ から32点への縮小であり、設計 §3.1 が明記する D96 手続の対象になる。[`README.md:110`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/insights/2026-08-01_t244-reflux-design/README.md:110)

constraint 集合、exact-mask no-good cut、anomaly 消費も本 leaf には入れない。設計 §3.2 の実装と誤認させない。

## A〜H の一般化限界

親実測は再実測せず出発点として採用するが、次は一般化しない。

- A/B: no-touch と独立 comparator の根拠には使える。ただし両 emitter は軸定数と同じ設計仕様を共有するので、「完全に独立な意味証明」ではない。
- C: freeze は六 record だが三 mask。六点被覆とは数えない。
- D: 9/32 は checked-in provenance の `implementation` 記録被覆であり、9点すべての certified・実走・採用を意味しない。
- E: 32/32 の相異性は injective の必要条件であり、bit 対応や意味の正しさを証明しない。
- F: `check_syntax_contract()` は禁止識別子 grep であり、C++ parse・compile・副作用なし・auditor 合格を証明しない。
- G: stub での3 passed は二つの指定検査に対する結果であり、最終 module body や全 suite の非干渉保証ではない。
- H: 一度の dispatch 成功は試験経路の利用可能性を示すだけで、新差分の緑や将来 dispatch 成功を示さない。

## 「監査済み」と名乗れる範囲

親が新旧関連テストを実測して通した後に限り、次の文言まで許容する。

> 新規 emitter は全32 mask で test-local literal golden および既存独立実装と byte 一致した。うち9 mask は checked-in campaign provenance の implementation 記録にも一致し、うち3 mask は known-axes freeze の gate predicate bytes にも一致した。

加えて「新規 leaf の wire parser は `[01]{5}` の32値だけを受理する」とは言える。

次は過大表現になる。

- 「D121 P1 を満たした」「候補表現を5-bit IRへ閉じた」
- 「production parser を正準化した」「D96 手続を完了した」
- 「32点すべてが campaign で実走・certified・compile 済み」
- 「全32 predicate が意味的に安全／auditor 済み」
- 「end-to-end side channel が0 bit」
- 「規律3の還流、exact-mask cut、origin ledgerを実装した」
- 「多世代 cap-lift の前提が満たされた」「`MAX_APPROVED_GENERATIONS` を上げられる」
- 「P1〜P10のいずれかを充足した」
- 「全 suite が緑」または「pytest 済み」

設計 §7 自身も P1 を「部分的」とし、現時点で無条件義務は未充足としている。[`README.md:421`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/output/insights/2026-08-01_t244-reflux-design/README.md:421) D121 も同じ限定を置く。[`decisions.md:5842`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/docs/decisions.md:5842)

## 総括

- プランの骨子:
  - `TriggerGateIR`、`parse_wire()`、`emit_wire()`、独立 `emit_predicate()` を新 leaf に閉じる。
  - LSB-first の32 wireと32 predicateを手書き literal で固定し、旧 emitter・campaign 9点・freeze 3点を重ねる。
  - production wiring と既存ファイル変更はゼロにする。
- 最大のリスク:
  - artifact のない残り23 maskは、手書き仕様と二つの実装の一致までしか裏付けがなく、実走・compile・certification の証拠はない。
  - 「JSON 拒否」や「side channel なし」を leaf 外の transport まで一般化すると過大主張になる。
- 親が裁定すべき択一:
  - `(P1)` と `(P2)` を上記限定付きで正式採用するか。
  - 「JSON 拒否」を raw parser 入力の拒否と解するか、JSON-origin provenance まで要求して別 wave の typed transport に送るか。前者を推奨する。
  - 「監査済み」の文言を上記 P4 の一文に厳密固定するか。固定を推奨する。