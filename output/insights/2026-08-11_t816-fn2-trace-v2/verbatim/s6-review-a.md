## 所見

### 1. **blocker** — exact-path gate が実装されていない

段 4 は `-r` を「exact-path gate」の前提として要求し、確定プランは差分集合を厳密に `{cc/silo/transaction.cc}` としています。[s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s4-ruling.md:20) [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:101)

しかし実装が検査するのは `M`、mode、regular file、C/C++ suffix だけで、path の一致検査がありません。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:156) そのため、追加の既存 `.cc` / `.hh` の `M` 差分も比較対象として受理されます。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:322)

テストにも「`transaction.cc` と別の既存 C++ file を同時に M」の負例はありません。A/D/R と non-C++ しか覆っていません。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:198)

**成果物影響:** 意図しない追加 C++ 変更を含む pin にも `result: pass` が付き、そのコードを使う certified 選択・レポート・台帳が承認対象へ入る。

### 2. **blocker** — macro/include の意味変化が preprocess 比較から消える

`_cpp_normalize()` は include 行を先に削除し、`-E -P` の出力だけを返します。[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:320) `-dD` 等はないため、展開されない `#define` 自体も出力には残りません。

checker の include 防壁は次だけです。

- include 行の生文字列比較。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:226)
- 同じ行を自己保存 marker に置換。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:199)
- marker の生死・順序比較。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:262)

したがって、include operand を決める macro の変更や、consumer TU で展開される header macro だけの変更は、include 行と marker 活性を保ったまま正規化出力から消え得ます。実装は header suffix も受理するため、この穴は到達可能です。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:39)

R2 の狭い攻撃、すなわち通常表記の同じ include 行を新側だけ `#if TRACE` 内へ移す形は捕捉できています。旧 marker は残り、新 marker は `TRACE=0` で消え、専用 fixture もその message を検査しています。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:191) ただし、これは include の意味全体の同一性ではありません。

加えて include 抽出 regex は空白を挟む通常の物理行だけを認識し、コメントを挟む directive、行継続、digraph を C++ の翻訳フェーズどおりには字句解析しません。[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:213)

**成果物影響:** 実 TRACE=0 build の取り込む宣言・macro・header が変化しても JSON は一致となり、異なる binary の throughput が規律 1 保証付きとしてレポート／台帳へ載り得る。

### 3. **blocker** — context 集合が空でも pass

`contexts` は空で初期化され、genome と overlay の loop 内だけで追加されますが、1 件以上・8 genome・2 overlay のいずれも checker 内で assert していません。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:238)

loop が空なら file は `"contexts":[],"result":"match"` のまま返ります。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:300) 最終 gate は file 数しか見ず、`result: pass` になります。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:327)

正例テストは現状の `len(contexts) == 16` を assert しますが、CLI 自体の fail-closed 性を保証する空-context 負例ではありません。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:154)

**成果物影響:** context 列挙の退行時に比較 0 件のまま `pass` が台帳へ入り、未検査 pin が certified 候補として残る。

### 4. **must-fix** — JSON の old/new digest は独立 evidence ではない

実際の判定では旧新を別々に preprocess し、bytes を比較しています。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:254) marker 活性も別々に算出して比較しています。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:268) よって現行判定そのものは恒真ではありません。

しかし成功後の JSON は、正規化 digest を旧 bytes だけから計算し、同じ値を `old_sha256` と `new_sha256` の両方へ書きます。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:276) include digest も旧活性列だけから同様に複製します。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:277)

テストもその複製値の一致しか見ていません。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:165) したがって JSON 単体では「新側 digest を本当に計算した」証拠になりません。

**成果物影響:** 比較分岐が将来退行しても proof-chain の old/new hash は常に一致して見え、レポート・台帳が検出力を過大表示する。

### 5. **must-fix** — 負例 fixture 3 件が過剰決定で、変異 kill の帰属を壊す

負例 helper は rc だけでなく、stdout 空、保証名、期待 message 断片まで検査しています。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:126) これは通常は良いものの、次の fixture では acceptance が変わらなくても message の変化だけで node が赤になります。

- `test_add_delete_and_rename_are_rejected_as_unsupported_status`: status gate を外しても、A/D の片側 blob を `_git_show()` できず別理由で非 0 になります。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:198) [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:597)
- `test_same_commit_empty_diff_is_rejected`: empty diff gate は `_validate_diff()` と最終 `files` gate の二重です。片方だけを変異してももう片方で拒否されます。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:245) [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:156) [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:327)
- `test_non_cpp_changed_path_is_rejected`: suffix gateを外しても fixture の `"old text"` / `"new text"` が preprocess 不一致となり、別 gate で拒否されます。[test_check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:222) [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:254)

特に事前登録 M5 と M7 は、受理集合が広がっていないのに期待 message の不一致だけで KILLED と数え得ます。

**成果物影響:** 変異台帳が M5/M7 を有効 kill と誤記し、checker の検出力を過大評価した状態で pin 承認レポートが閉じる。

## fail-open 個別確認

| 経路 | 判定 |
|---|---|
| preprocess 失敗 | `_cpp_normalize()` が例外、CLI 境界で rc=1。[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:347) |
| git object 不在 | `rev-parse --verify` の非 0 を例外化し、rc=1。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:60) |
| compiler 不在／version 失敗 | 例外化し、rc=1。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:174) |
| diff path decode 失敗 | `CheckError`、rc=1。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:100) |
| 予期しない diff status | `status != "M"` を拒否、rc=1。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:160) |
| defines 導出の明示的失敗 | `_head_defines()` 由来例外を握らず CLI 境界で rc=1。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:240) |
| context 集合が空 | **fail-open。blocker 3。** |
| その他の予期しない例外 | `except Exception` が rc=1 にするため pass へは倒れない。[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:351) |

## 実 pin 対の pass が示しているもの

実 JSON は「何も見ていない」結果とは区別できます。[g++-11 JSON](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/real-run-g11.json:1) [g++-12 JSON](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/real-run-g12.json:1)

見るべき field は次です。

- `old_oid` / `new_oid`
- `diff[0].status/path` と相異なる `old_blob/new_blob`
- `compiler.path/version` が g++-11 と g++-12 で別
- `files` が 1 件で `path == cc/silo/transaction.cc`
- `files[0].contexts` が 16 件、8 genome × `base` / `GLOBAL_VALUE_DEFINE=1`
- 各 `defines.old.TRACE` / `defines.new.TRACE` が `"0"`
- `include_line_count == 8`、各 context の active marker が 8 件

したがって今回の二つの実走は、非空の対象を全 16 context で処理した証拠です。ただし `old_sha256/new_sha256` は blocker ではないにせよ独立算出証拠ではなく、上記 blocker が一般的な checker の健全性を妨げています。

## 総括

blocker は、① exact-path gate 欠落、② macro/include 意味変化の死角、③空 context の pass の 3 件です。  
実 pin 対の実走が「何も見ていない」わけではありませんが、現状の checker の `pass` を規律 1 の最終証拠として採用するのは不可です。