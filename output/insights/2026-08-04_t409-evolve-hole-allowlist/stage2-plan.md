## 結論

P1 に賛成し、依存なしの「ASCII 文字 prefilter → 固定語彙 lexer → 再帰下降 parser → `kUnset` 評価」の recognizer を新設する。P2 は却下し、5 識別子 blacklist は active gate から外す。受理可能な意味は「abort reason ごとの真偽」全体を維持しつつ、危険な C++ の別表記だけを閉じる。

編集・pytest 実測は行っていない。純粋な in-memory 静的確認では、指定の攻撃と後述する5変異が現行 blacklist で `[]`、DiffQuarantine で `passed=True` になった。

## 現物照合

確認済みの攻撃経路は次のとおり。

- hole は patch の単一代入行 [silo-backoff-trigger-gating-variant.patch:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:86)〜[106](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:106)、実置換対象は `izanagi_gate_pass = true;` の [102](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:102)。
- `parse_coder` は JSON/schema と軸を検査した後、`\n`/`\r` の不在しか source 形状へ課していない [p3_autonomous_workload_trial.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:324)〜[347](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:347)。
- 現 gate は5識別子の正規表現検索だけ [p3_s4_loop_trigger_gating.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:112)〜[139](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:139)。
- DiffQuarantine は構造的 containment を担い、内容については directive、marker、コメント delimiter、行末 backslash だけを拒否する [diff_quarantine.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/diff_quarantine.py:437)〜[497](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/diff_quarantine.py:497)。同 module 自身も C++ 意味 admission ではないと明記している [diff_quarantine.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/diff_quarantine.py:9)〜[22](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/diff_quarantine.py:22)。
- `pro_set_` は public member [transaction.hh:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/include/transaction.hh:33)〜[39](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/include/transaction.hh:39)。`abort()` は read/write/node を clear するが `pro_set_` は触らない [transaction.cc:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/transaction.cc:35)〜[47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/transaction.cc:47)。
- `makeProcedure` は retry の前 [ycsb.hh:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:102)、`RETRY` は [108](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:108)、再走査は [117](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:117)。abort 後は同じ vector のまま `goto RETRY` する [149](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:149)〜[164](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:164)。

したがって、例の変異は retry 中の論理トランザクションを段階的に短縮する。短くなった操作集合にも通常の CC がかかるため serializability verifier が緑のままになり得る、という部分はコードからの推論であり、本ターンでは verifier 実測をしていない。

親 brief との食い違いもある。

- brief の `ycsb.hh:101/:107/:114` は現在の現物では `:102/:108/:117`。
- 次の `YcsbWorkload::run` では `makeProcedure` が `pro.clear()` する [ycsb.hh:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:55)〜[59](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:59)。従って「恒久的」は同じ retry 中の論理トランザクションについては正しいが、executor の後続全トランザクションまで、という意味なら誤り。
- 正例26件は「trigger の代入式26件」ではない。実際は trigger 代入式9件、trigger stock の説明文字列1件、sort control 16件。[positive-controls.txt:1](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:1)〜[52](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:52)。
- trigger stock の説明文字列を除く9代入式は、すべて `kUnset` を含む等値比較の `||` 連鎖である。

## 受理文法

新規 module は `orchestrator/campaign/trigger_gate_language.py` とし、公開署名を次で固定する。

```python
class GateLanguageRejectCode(str, Enum):
    INVALID_TYPE = "invalid-type"
    RESOURCE_LIMIT = "resource-limit"
    INVALID_CHARACTER = "invalid-character"
    INVALID_TOKEN = "invalid-token"
    INVALID_GRAMMAR = "invalid-grammar"
    UNSET_NOT_TRUE = "unset-not-true"

@dataclass(frozen=True)
class GateLanguageResult:
    passed: bool
    reason_code: GateLanguageRejectCode | None

def check_trigger_gate_implementation(
    implementation: str,
) -> GateLanguageResult:
    ...
```

result に入力本文、未知 token、文字位置を保持・返却しない。parser 内部でも Python `eval` は使わない。

EBNF は次の閉集合とする。`H` は ASCII space または tab だけで、lexer は token 間の `H*` を捨てる。

```bnf
<implementation> ::= H* "izanagi_gate_pass" H* "=" H*
                     <or-expr> H* ";" H*

<or-expr>        ::= <and-expr> (H* "||" H* <and-expr>)*
<and-expr>       ::= <unary-expr> (H* "&&" H* <unary-expr>)*
<unary-expr>     ::= "!" H* <unary-expr>
                   | <primary>

<primary>        ::= "true"
                   | "false"
                   | <comparison>
                   | "(" H* <or-expr> H* ")"

<comparison>     ::= "izanagi_abort_reason_" H*
                     <compare-op> H*
                     "IzanagiAbortReason" H* "::" H* <member>

<compare-op>     ::= "==" | "!="

<member>         ::= "kUnset"
                   | "kLockConflict"
                   | "kUpdateAbsent"
                   | "kReadValiTid"
                   | "kReadValiLocked"
                   | "kNodeVali"
                   | "kInsertNode"
                   | "kScanNode"
```

許可 token は次だけ。

- word: `izanagi_gate_pass`, `izanagi_abort_reason_`, `IzanagiAbortReason`, 上記8 member、`true`, `false`
- punctuator: `=`, `==`, `!=`, `!`, `&&`, `||`, `::`, `(`, `)`, `;`
- horizontal whitespace: space、tab

enum の8 member は骨格現物 [patch:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:56)〜[67](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:67) と一致させる。

構文受理後、内部 AST を `reason=kUnset` で評価し、結果が `True` でなければ `UNSET_NOT_TRUE`。明示的な `kUnset` token の存在は要求しないため、既存 fixture の次も通る。

```cpp
izanagi_gate_pass = true;
```

既存テストの `izanagi_abort_reason_ != IzanagiAbortReason::kNodeVali` も通る [test_p3_s4_loop_trigger_gating.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:85)。

正例9件は [positive-controls.txt:1](/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:1)、`:3`、`:5`、`:41`、`:43`、`:45`、`:47`、`:49`、`:51`。各項が `<comparison>`、連結が `<or-expr>` で、必ず `kUnset` 項を持つため9件すべて受理される。

この文法は C++ の受理表記を狭めるが、意味上は狭めない。入力は8値 enum 一つなので、任意の reason→bool 写像は等値比較の論理式で表せる。`kUnset=True` を固定しても残る `2^7` 方策をすべて表現できる。

## 字句段の防御

最初に原文を正規化せず、そのまま次で検査する。

- ASCII のみ。
- 許可文字集合は `A-Z a-z _ : = ! & | ( ) ; space tab`。数字も許可しない。
- 最大4096 byte、最大512 token、括弧深度64。
- word は `[A-Za-z_]+` 相当を maximal-munch し、上記 word 集合との完全一致だけを認める。実装は regex 依存でなく逐次 scanner とする。
- punctuator は2文字 token を先に読む longest-match。単独 `&`、`|`、`:` は拒否する。

| 攻撃面 | 文法到達前の拒否 |
|---|---|
| `and/or/not/bitand/bitor/xor/compl/*_eq` | 文字は prefilter を通り得るが、固定 word 集合にないため lexer が `INVALID_TOKEN` |
| digraph `<:`, `:>`, `<%`, `%>`, `%:`, `%:%:` | `<`, `>`, `%` が許可文字外 |
| trigraph 9種 | `?` が許可文字外 |
| backslash-newline、CR/LF | `\`, CR, LF がすべて許可文字外 |
| `//`, `/*`, `*/` | `/`, `*` が許可文字外 |
| char/string/raw string | `'`, `"`, 数字が許可文字外 |
| UCN `\u...`, `\U...` | `\` と数字が許可文字外。Unicode normalization はしない |
| 数値区切り `1'000` | 数字と `'` が許可文字外。数値 literal 自体を受理しない |
| 属性 `[[...]]` | `[` と `]` が許可文字外 |
| `#`, `%:` 等の directive | `#`, `%` が許可文字外 |

## 配線プラン

1. `orchestrator/campaign/trigger_gate_language.py:1` を新設し、全 lexer/parser/AST/enum member/資源上限を置く。凍結 axis module から新定数を派生させない。

2. [p3_s4_loop_trigger_gating.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:42)〜[66](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:66) で新 module を import し、`re` と `SYNTAX_CONTRACT_FORBIDDEN` import を外す。

3. [同:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:112)〜[139](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:139) の `_FORBIDDEN_RE`／`check_syntax_contract` を削除する。`_syntax_contract_reject_result` は `GateLanguageResult` を受け、本文なしの `reason_code` だけを evidence に載せる形へ置換する。既存 consumer 互換のため rejection subtype は `"syntax-contract"` を維持する。

4. [同:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:358)〜[402](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:402) の順序を次へ変える。

   `allowlist → DiffQuarantine → auditor digest/verdict → build`

   allowlist は `L.quarantine(..., write=do_build)` より前に置く。現状は DiffQuarantine pass 時に source へ書いてから syntax gate が走るため [p3_s4_loop.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop.py:212)〜[218](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop.py:218)、拒否対象を一時 materialize してしまう。

5. build 停止経路は既存のまま利用できる。gate が reject dict を返すと [p3_s4_loop_trigger_gating.py:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:480)〜[486](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:486) で return し、`run_campaign` [496](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:496)〜[502](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:502) へ到達しない。

6. standalone preview [同:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:675)〜[687](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_s4_loop_trigger_gating.py:687) にも同 checker 結果を追加し、DiffQuarantine と allowlist のどちらかが失敗すれば CLI rc=1 とする。

7. `parse_coder` の一行チェック [p3_autonomous_workload_trial.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:337)〜[339](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:339) は transport/schema の早期診断として残す。ここだけを load-bearing にすると `load_proposal_file` や dataclass 直生成が迂回できるため、最終 gate は必ず `_quarantine_and_audit` に置く。

8. autonomous preview [同:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:560)〜[578](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:578) の `"forbidden_identifiers"` を安全な `"syntax_contract": {"passed", "reason_code"}` へ変更し、pre-audit 判定 [1377](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:1377)〜[1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:1384) を追随させる。

9. trigger materialization の既存別経路にも同じ checker を置く。

   - machine sweep の書込み前 [s8a_trigger_sweep.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:419)〜[425](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:425)、および build 前 [441](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:441)〜[459](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:459)。
   - freeze 直接比較の旧 checker 呼出 [s1_direct_comparison.py:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:516)〜[525](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:525)。

P2 を採らない理由は、blacklist が allowlist 後には到達不能で、しかも凍結 module 内の更新不能な別 authority になるため。可読な診断は blacklist ではなく閉じた `reason_code` で維持する。

## 境界テスト

新規 `orchestrator/tests/test_trigger_gate_language.py:1` に純粋な language boundary matrix を置く。

- 正例: `true`、既存 `!=` fixture、全8 enum member、`!`/`&&`/`||`/括弧、space/tab 変種、正例9式。
- semantic reject: `false`、`reason == kLockConflict`、`reason != kUnset`。
- lexical reject: alternative token 11種、digraph全種、trigraph全9種、LF/CR/CRLF、backslash、コメント、char/string/raw literal、UCN、numeric separator、属性、Unicode homoglyph、NUL。
- grammar reject: LHS違い、member typo、逆向き比較、欠落/重複 semicolon、複数文、単独 `&|:`、関数呼出、代入式、末尾 token。
- 資源境界: 4096/4097 byte、512/513 token、深度64/65。

既存 integration tests は [test_p3_s4_loop_trigger_gating.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1093) 以降を blacklist テストから allowlist テストへ置換する。既存 site admission matrix [同:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:446)〜[454](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:454) は別責務なので変更しない。

「現に通る」negative 5種を parameterize する。

| 系統 | 現行を通る変異 | 新 gate |
|---|---|---|
| `pro_set_` | `izanagi_gate_pass = true; pro_set_.pop_back();` | `.`／未知 word／複数文で reject |
| 副作用 | `izanagi_gate_pass = ((izanagi_abort_reason_ = IzanagiAbortReason::kUnset) == IzanagiAbortReason::kUnset);` | expression 内代入で grammar reject |
| ループ | `izanagi_gate_pass = true; while (true) {}` | `while` と `{}` で reject |
| 制御移譲 | `izanagi_gate_pass = true; return;` | 未知 word／複数文で reject |
| fitness 参照 | `izanagi_gate_pass = CCBenchResults[0].local_abort_counts_ != 0;` | `[`, digit, `.`、未知 word で reject |

最後の global と counter は実在する [result.hh:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/result.hh:14)〜[21](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/result.hh:21)、[258](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/result.hh:258)。

各ケースで以下を pin する。

- DiffQuarantine 単体は pass する。
- 新 checker は fail。
- auditor が `pass` でも `"syntax-contract"` reject。
- allowlist reject 時は `L.quarantine` と `run_campaign` が呼ばれない。
- evidence、log、critic digest に式本文が出ない。
- accepted input だけが既存 dry-pass test [test_p3_s4_loop_trigger_gating.py:1158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1158) を通る。

さらに次を更新する。

- machine sweep の旧 blacklist test [test_s8a_trigger_sweep.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_s8a_trigger_sweep.py:92)〜[104](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_s8a_trigger_sweep.py:104) を「全生成候補が新文法を通る」へ置換。
- S1 の改行付き synthetic positive [test_s1_direct_comparison.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_s1_direct_comparison.py:335)〜[418](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_s1_direct_comparison.py:418) は、canonical predicate は pass、LFを含む synthetic は reject へ境界を更新。
- autonomous preview fixture の `"forbidden_identifiers"` [test_p3_autonomous_workload_trial.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_autonomous_workload_trial.py:107)〜[115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_p3_autonomous_workload_trial.py:115) と completeness/transport fixtures を新 schema へ追随。

## Producer 側

[producer role:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/.claude/agents/coder-v4-autonomous-trigger-gating.md:62)〜[115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/.claude/agents/coder-v4-autonomous-trigger-gating.md:115) を次のように変える。

- 「enum と literals を読める」という開いた説明を、上記 word/operator/member の閉集合へ置換。
- 旧5識別子節は削除し、「列挙外の token はすべて reject」とする。
- `kUnset=True` を結果条件として維持。
- 数字、文字列、呼出、member access、assignment、comma、ternary、alternative token を明示的に対象外とする。
- pipeline 説明 [同:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/.claude/agents/coder-v4-autonomous-trigger-gating.md:146)〜[148](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/.claude/agents/coder-v4-autonomous-trigger-gating.md:148) を blacklist grep から allowlist recognizer へ変更。

runtime に inline される契約も同時更新する。

- `ROLE_CONTRACTS["coder"]` [p3_autonomous_workload_trial.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:188)〜[195](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:195)。
- `GATING_SPEC`／`DESIGNATED_SOURCE_CONTEXT` [同:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:221)〜[240](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/p3_autonomous_workload_trial.py:240)。
- runbook の preview/auditor/pre-build 説明 [phase3-s8a-trigger-runbook.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/phase3-s8a-trigger-runbook.md:63)〜[88](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/phase3-s8a-trigger-runbook.md:88)。

これは候補式の既知リストを producer に渡す設計ではない。全8理由に対する任意の Boolean 方策を合成でき、特定の勝ち筋・部分集合・順位は提示しないため、D127 の producer 非互換を解消しつつ合成自律性を維持する。sort 軸へは適用しない。

## 新 D の骨子

現行 `docs/decisions.md` は [6951](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/decisions.md:6951) が末尾。実装時は採番競合を避け、正規の spool 経路で同じ変更単位へ含める。

```markdown
## D<採番時>. [T-409] trigger-gating EVOLVE-BLOCK の受理集合を閉じた Boolean 文法へ移す

### 決定

### 理由

### 射程

### 却下案
```

これと境界テストを同じ変更単位に含めるのが D96 [decisions.md:4269](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/decisions.md:4269)〜[4292](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/decisions.md:4292) の要件である。

## 凍結境界

[axis_trigger_gating.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/axis_trigger_gating.py:53)〜[64](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/axis_trigger_gating.py:64) は編集しない。現 sha256 は `47507d9b936e...b50c04c` で、known-axes JSON では例として [46](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/output/s1-freeze/known_axes_freeze.json:46)〜[47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/output/s1-freeze/known_axes_freeze.json:47)、measurement JSON では [41](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/output/s1-freeze/measurement_freeze.json:41)〜[42](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/output/s1-freeze/measurement_freeze.json:42) に pin されている。

新しい語彙定数はすべて `trigger_gate_language.py` に置く。旧 `SYNTAX_CONTRACT_FORBIDDEN` は frozen bytes として残るが、active consumer からは import しない。

## 回帰確認手順

正例26件は次の matrix として検査する。

- 総数26を確認。
- `izanagi_gate_pass =` で始まる9件を新 checker に渡し、全件 `passed=True`。
- trigger stock 説明1件は `BACKOFF_TRIGGER_GATING=0` の metadata control と分類し、code gate へ渡さない。
- sort 16件は trigger gate の domain 外と分類し、誤って渡されないことを確認。

恒久境界テストには9式を逐語固定し、wave acceptance では提供された `positive-controls.txt` 全26件を上記分類で走査する。「26件すべてを trigger 文法で受理」は sort と stock 説明までコードとして認めるため、実施してはいけない。

親が計算ノード経路で実行する関連テスト案は次。

```text
python3 tools/run_tests.py \
  orchestrator/tests/test_trigger_gate_language.py \
  orchestrator/tests/test_p3_s4_loop_trigger_gating.py \
  orchestrator/tests/test_p3_autonomous_workload_trial.py \
  orchestrator/tests/test_autonomous_trial_completeness.py \
  orchestrator/tests/test_s8a_trigger_sweep.py \
  orchestrator/tests/test_s1_direct_comparison.py
```

続いて全 suite、`tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後の provenance 監査を行う。本ターンではこれらを実測しておらず、緑の主張はない。

## 総括

提案する実装方式 (P1 への賛否): P1 に賛成し、ASCII prefilter + 固定語彙 lexer + 手書き Boolean parser + `kUnset` 評価を採用する。  
最大の技術的リスク: 新規・将来の trigger materialization 経路が recognizer を呼ばず generic `quarantine()` へ直行する consumer 閉包漏れ。  
親 brief の記述で誤っていた点: YCSB 行番号、正例26件の内訳、ならびに `pro_set_` 縮小が後続の全論理トランザクションにも恒久化するとの読み方。