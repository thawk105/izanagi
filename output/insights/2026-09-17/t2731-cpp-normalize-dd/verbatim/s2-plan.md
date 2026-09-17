## `_cpp_normalize` の変更 (file:line と擬似 diff)

**P1 の空入力 prefix 除去を採用する。実装は再帰呼出し＋内部 keyword-only flag とし、subprocess の静的 spawn site を既存の 1 箇所に保つ。** 以下は起草であり、実装・pytest・変異走行は未実施。

変更位置は `orchestrator/campaign/source_digest.py:404` と `:1646-1676`。

```diff
 _BUILTIN_MACRO_CACHE: Dict[tuple, frozenset] = {}
+_CPP_ENV_PREFIX_CACHE: Dict[tuple, str] = {}

-def _cpp_normalize(source_text: str, defines: Dict[str, str], cxx: str) -> str:
+def _cpp_normalize(
+    source_text: str, defines: Dict[str, str], cxx: str,
+    *, _environment_only: bool = False,
+) -> str:
     """...下記の説明へ更新..."""
+    prefix = ""
+    if not _environment_only:
+        key = (cxx, tuple(sorted(defines.items())))
+        if key not in _CPP_ENV_PREFIX_CACHE:
+            _CPP_ENV_PREFIX_CACHE[key] = _cpp_normalize(
+                "", defines, cxx, _environment_only=True,
+            )
+        prefix = _CPP_ENV_PREFIX_CACHE[key]
+
     stripped = _INCLUDE_RE.sub("", source_text)
-    args = [cxx, "-E", "-P", "-nostdinc", "-Werror=undef", *BUILD_FLAGS]
+    args = [cxx, "-E", "-P", "-dD", "-nostdinc", "-Werror=undef", *BUILD_FLAGS]
     for k in sorted(defines):
         args.append(f"-D{k}={defines[k]}")
     args += ["-x", "c++", "-"]
     try:
         r = subprocess.run(args, input=stripped, capture_output=True, text=True)
     except (OSError, subprocess.SubprocessError) as e:
         ...既存の RuntimeError...
     if r.returncode != 0:
         ...既存の RuntimeError...
-    return r.stdout
+    if _environment_only:
+        return r.stdout
+    if not r.stdout.startswith(prefix):
+        raise RuntimeError(
+            "source_digest: preprocess 出力が空入力の環境 prefix と不一致"
+            " — identity を確定できないため fails-closed"
+        )
+    return r.stdout.removeprefix(prefix)
```

空入力を先に取得する。失敗結果は cache に入らず、実入力の失敗も従来どおり停止する。空文字も cache の値として区別できるよう、truthiness でなく key の存在を見る。内部 flag を使うのはこの関数内だけで、既存 consumer の呼出し形は変わらない。

供給差は現物で確認した。

- `:2071` の `_worktree_defines` は working-tree の Options / source owner の protocol CMake を読む。
- `:2085` の `_head_defines` は指定 commit の同じ資料を読む。
- `:902` の `_merge_defines` は既定値と genome を合わせ、実供給集合で絞り、cache 名の写像・裸 option・platform 定義を反映する。
- `patches/silo-backoff-fixed.patch:12` と `:25` 付近は `BACKOFF_FIXED` に加えて `BACKOFF_NOINLINE` も working-tree の供給に追加する。素の `-dD` では、この両方が baseline に無い出力差を作る。

helper に subprocess を移す案も同じ argv を共有できるが、spawn registry の owner を変更する必要がある。今回は小さい内部 flag で足りるため採らない。`orchestrator/tests/test_ccbench_spawn_sites.py:289` の登録は変更不要。

代案を採らない理由：

| 案 | 現物に即した欠点 |
|---|---|
| `-P` を外し linemarker で境界を取る | 行位置・入力名を含む出力になる。既存のコメント・空行に不感な正規化を保つには別の除去処理が必要 |
| 環境マクロ名で行 filter | source 自身の `#undef Linux` や、command-line と同名同値の再 `#define` まで落とす。今回残すべき操作を消してしまう |

docstring は D34 案 A の説明を維持し、次を明記する。

> builtin は定義済みのまま条件評価する。`-dD` により有効枝の source の `#define` / `#undef` を正規化出力に残す。対象 GCC の実測では predefined と command-line 定義も出力されるため、同じ argv の空入力出力だけを先頭から除去する。これは builtin の評価を無効化する処理ではなく、source が参照しない追加供給によって inert identity が変わることを防ぐ処理である。prefix 不一致は RuntimeError。skipped 枝の指令は出力されない。

## 不変条件の保持

**F-4 の指令数は現物と一致した。** `git show 511c953:<path>` で確認した結果：

| 対象 | `#define` / `#undef` 行 |
|---|---:|
| `include/backoff.hh` | 0 |
| `cc/silo/transaction.cc` | 0 |
| `cc/mocc/transaction.cc` | 0 |
| template patch の追加・文脈行 | 0 |

`backoff.hh:1` には既存の `#pragma once` があるが、macro stack 操作は無い。

同一 compiler・同一 defines で、環境 prefix 除去後に新たに残る source 指令が無いため、対象 stock・inert template・既存 template variant の本文出力は従来と同じになる見込みである。`_normalize_contexts:1686` の文脈タグ・順序、および pre-image の NUL 区切り・UTF-8 化は変更しない。

したがって、次を変更する理由は無い。

- `_GOLDEN_VID` (`test_campaign.py:11051` 付近)。
- `test_source_digest_stock_roundtrip:11250` 付近。
- `test_source_digest_fixed_variant_distinct:11264` 付近。
- `_digest(parts)` 自体の固定入力 golden。

厳密には `_GOLDEN_VID` は stock token 時の canonical genome の ID、pre-refactor golden は固定文字列の結合ハッシュであり、いずれも compiler 出力の byte 同一性を単独で証明する test ではない。**byte 同一は今回の静的予測であり、実測済みとはしない。**

`_trace_pair_diff:2150` は TRACE ごとの prefix を除去するので、command-line の `#define TRACE 0/1` が差分に入らない。除去しなければ通常は HEAD と working tree の双方へ同じ人工差分が入るが、それに依存しない。M6 の source 指令は両 TRACE 文脈で同じ出力となるため、file 単独の diff-of-diffs は引き続き通過する。

`tools/check_trace0_preprocess_identity.py:560-596` は old/new それぞれの defines を導出し、TRACE=0 を最後に固定する。policy の mocc pair：

```text
base = 511c9538e4e8efa54b45cda62e72389ed3b706ec
new  = e9e477ca1b55348ab4530de0b1cf663ce4555290
```

では Options / mocc CMake に差分が無く、両側の環境 prefix は同じ。mocc source の追加には `#if TRACE` / `#endif` と trace include があり、`#define` / `#undef` は無い。TRACE=0 の比較と include activity marker の比較を変更する必要は無い。

`test_source_digest_failsclosed_on_missing_define:11301` 付近は、BACKOFF_FIXED を除いた defines でも空入力の取得は成功し、本体の `#ifndef BACKOFF_FIXED` → `#error` で従来どおり RuntimeError になる。

`buildcache.py:3761` の `_assert_no_trace_symbols` と `diff_quarantine.py:492` 付近の `HOLE_ESCAPE` は変更しない。

## 回帰 test の設計 (node 名・主張・修正前の赤)

追加位置は `orchestrator/tests/test_campaign.py:11832` 付近、既存 builtin 回帰の後。実 compiler を使う node は先頭で `_any_cxx()` を一度選び、全 consumer に渡す。fake repo は `:11541`、backoff 本文は `:11470` の既存 fixture を使う。

以下の node はすべて同ファイル所属。A〜H は次節の期待集合の略号である。

**A — `test_source_digest_toplevel_macro_directives_change_identity`**

```python
"""本文が参照しない top-level の define/undef も別 identity にする。"""
```

`Genome("silo", {"BACK_OFF": 1})`。既存 include 直後へ次を挿入する。

```c
#undef T2731_LEAK
#define T2731_LEAK 1
```

挿入前の fixture に `T2731_LEAK` が無いことも確認する。

```python
assert token != source_digest.STOCK, "top-level 指令が STOCK に化けた"
assert current != baseline, "source 指令が digest の pre-image に入っていない"
```

`token=resolve(...)`、`current=compute(...)`。修正前は最初の assert が赤。

**B — `test_source_digest_toplevel_trace_directives_change_identity`**

```python
"""TRACE 漏れを別 identity にし、file 単独の trace 差分検査の境界も固定する。"""
```

A の名前を TRACE に置き換える。fake backoff 本文は TRACE を参照しない。

```python
assert token != source_digest.STOCK, "TRACE 指令が STOCK に化けた"
assert current != baseline, "TRACE 指令が digest に入っていない"
source_digest.assert_trace_diff_matches_head(g, head, sub, cxx=cxx)
```

修正前は identity assert が赤。修正後の trace 検査は通過する予測。docstring に「実 M6 の最終層は `buildcache._assert_no_trace_symbols`。この fake test は binary 検査を実行しない」と併記する。

**C — `test_source_digest_comment_only_preserves_stock`**

```python
"""include 直後のコメント追加は STOCK と baseline 一致を保つ。"""
assert token == source_digest.STOCK, "コメントだけで STOCK が変わった"
assert current == baseline, "コメントだけで digest が変わった"
```

A と同じ位置へコメントのみ追加。修正前も通る負例。

**D — `test_source_digest_unused_universal_supply_preserves_stock`**

```python
"""本文が参照しない universal 供給の追加は STOCK を変えない。"""
```

working-tree Options.cmake にだけ、既定値と供給行を追加する。

```cmake
set(CCBENCH_T2731_UNUSED 1 CACHE STRING "unused fixture")
# ccbench_universal_definitions の set 内
T2731_UNUSED=${CCBENCH_T2731_UNUSED}
```

`_worktree_defines` に当該 key が入り、`_head_defines` には無いことを確認したうえで：

```python
assert token == source_digest.STOCK, "未参照の universal 供給で STOCK が変わった"
assert current == baseline, "環境 prefix が identity に混入した"
```

Options.cmake は `source_digest.py:97` の allowlist 内なので `resolve` を使える。修正前は通り、prefix を剥がさない実装で赤。

**E — `test_source_digest_unused_protocol_supply_preserves_digest`**

```python
"""本文が参照しない protocol 供給は compute と baseline の一致を保つ。"""
```

別の fake repo で Options に同じ既定値、`cc/silo/CMakeLists.txt` の OPTIONS に供給行を追加する。protocol CMakeLists は allowlist 外なので `resolve` は呼ばない。silo source の実効 defines が増えたことを確認する。

```python
assert current == baseline, "未参照の protocol 供給が digest を変えた"
```

修正前は通り、prefix 除去を外すと赤。

**F — `test_source_digest_skipped_macro_directives_affect_only_live_variant`**

```python
"""dead 枝の指令は stock を保ち、live な兄弟 variant の identity だけを変える。"""
```

fake backoff の `#if BACK_OFF` 枝で `return 1` を `return 2` にした sibling variant を作る。stock genome は BACK_OFF=0、variant genome は BACK_OFF=1。指令挿入前の両 token / digest を記録し、その live 枝内だけへ A の 2 行を追加する。

```python
assert stock_after == stock_before == source_digest.STOCK, \
    "skipped 枝の指令が stock identity を変えた"
assert stock_digest_after == stock_digest_before, \
    "skipped 枝の指令が stock pre-image を変えた"
assert variant_after != variant_before, \
    "live 枝の指令が兄弟 variant と alias した"
assert variant_digest_after != variant_digest_before, \
    "live 枝の指令が variant pre-image に入っていない"
```

修正前は variant 側が赤。既存の BACK_OFF 供給を使うので、未知条件マクロ拒否による別理由の赤を作らない。

**G — `test_source_digest_cpp_environment_prefix_mismatch_fails_closed`**

```python
"""空入力と本体の prefix 不一致は、正規化結果を返さず停止する。"""
```

この node だけは compiler 不要。新 cache を `patch.object(..., {}, create=True)` で隔離し、`source_digest.subprocess.run` を模擬する。

- `input == ""`：rc=0、stdout=`"#define ENV 1\n"`。
- 本体：rc=0、stdout=`"#define DIFFERENT 1\nint x;\n"`。
- stderr は両方空。

```python
with pytest.raises(RuntimeError):
    source_digest._cpp_normalize("int x;\n", {}, "t2731-fake-cxx")
```

診断文言ではなく停止の有無を検査する。修正前は例外が出ず赤。`startswith` 判定を恒真化した実装も赤。mock と cache は必ず復元する。

**H — `test_source_digest_same_value_source_redefine_changes_identity`**

```python
"""command-line と同名同値の source 再定義も環境 prefix と一緒に消さない。"""
```

BACK_OFF=1 の fake repo で include 直後へ `#define BACK_OFF 1` を追加する。本文の展開結果は変わらない。

```python
assert token != source_digest.STOCK, "同名同値の source 再定義を消してしまった"
assert current != baseline, "source 再定義が環境 prefix と混同された"
```

修正前は赤。親の `dup_cmdline_define` 実測を永続回帰へ落とす。

`test_skip_classification.py:37` の `_SELECTED_CXX_CONSUMERS` は選定された既存 9 関数の静的 call 数を検査しており、全 consumer の自動列挙ではない。既存関数の呼出し数を変えない今回の追加では、登録簿と `len == 9` を変更する必要は無い。

## 変異登録の素材 (source-level と recipe v2 の期待署名)

source-level は**上記 A〜H の 8 node だけを runner に指定する**。この限定 runner に対する完全集合は次のとおり。

| 変異 | 一意な置換対象 | `expected_nodes` | `expected_status` |
|---|---|---|---|
| `-dD` を外す | `_cpp_normalize` の argv 内の `"-dD",` | A, B, F, H | `KILLED` |
| prefix 除去を外す | `return r.stdout.removeprefix(prefix)` → `return r.stdout` | D, E | `KILLED` |
| prefix 一致判定を恒真化 | `if not r.stdout.startswith(prefix):` → `if not True:` | G | `KILLED` |
| comment-only 対照 | 新 docstring の説明語だけ変更 | 空集合 | `SURVIVED` |

spec では略号を `orchestrator/tests/test_campaign.py::<上記の完全な関数名>` に展開する。全 test_campaign を走らせる場合、この集合をそのまま流用してはならない。

修正前 HEAD に新 tests だけを載せたときの静的予測は **A, B, F, G, H が赤**、C, D, E が通過。G は新しい停止契約、残る 4 node は指令の identity 被覆を検出する。

recipe v2 の node 対応は：

```text
N1a = orchestrator/tests/test_t2630_scan_boundary_reach.py::test_stock_identity
N1b = orchestrator/tests/test_t2630_scan_boundary_reach.py::test_variant_identity
N2a = orchestrator/tests/test_t2630_scan_boundary_reach.py::test_stock_owner_tu
N2b = orchestrator/tests/test_t2630_scan_boundary_reach.py::test_variant_owner_tu
```

| 変異 ID | v2 `expected_nodes` | `expected_status` | 導出 |
|---|---|---|---|
| `M0-comment-only-cmake` | `[]` | `SURVIVED` | CMake コメントのみ |
| `M1-synthetic-branch-code-edit` | `[N1b,N2b]` | `KILLED` | live variant の本文と TU のみ変化 |
| `M2-include-line-added` | `[N1a,N1b,N2a,N2b]` | `KILLED` | include 一致拒否。TU node も resolve 成功を要求 |
| `M3a-hole-leak-sleep-read-phase` | `[N1b,N2b]` | `KILLED` | stock では skipped、variant では指令と TU が変化 |
| `M3b-toplevel-leak-sleep-read-phase` | `[N1a,N1b,N2a,N2b]` | `KILLED` | 両 genome の指令 identity と TU が変化 |
| `M4-transaction-sandwich-desired-expected` | `[N1a,N1b,N2a,N2b]` | `KILLED` | include 除去後も define/undef が残る。TU 差・compile 失敗は既記録どおり |
| `M4b-transaction-sandwich-cas-relaxed` | `[N1a,N1b,N2a,N2b]` | `KILLED` | 同上。object の実行差を期待条件にしない |
| `M6-toplevel-leak-trace` | `[N1a,N1b,N2a,N2b]` | `KILLED` | 両 genome の指令 identity と TU が変化。trace gate 通過は追加観測 |

親の予測と一致する。probe 本文の `_pair` は TU node でも resolve 成功を要求する一方、token の等値は要求しない。このため M3b 等では identity 差と TU 差がそれぞれ赤になり、M2 は拒否が全 node に伝播する。

段 4 で作る `mutation-spec-v2.json` は**文書の第 2 版**であり、schema は既存の `izanagi-dev-wave-mutation-spec/v1` のままにする。`tools/mutation_harness.py:481,532` は exact keys を要求するため、説明・略号・独自 version key を JSON に足さない。既存の carrier 置換を保持し、上表の完全 node 名へ更新する。

親が行う再走手順：

1. 実装を commit した wave tip から、別の probe branch / worktree を作る。
2. `a519a7560`、`e35fb7c4e` の順で cherry-pick する。後者の実 site detector 修正も必要。
3. **harness の `--repo` はその clean な別木**。spec と出力は checkout 外に置き、最終 HEAD に対して置換 anchor の一意性を確認する。
4. §9 の dispatch recipe を使う。`--expected-spec-sha256` は新 spec の値へ更新し、旧 hash を流用しない。
5. `--runner-mode dispatch --detached`、新しい `--attempt-out` / `--wrapper-attempt`、runner の `--force-dispatch` を維持する。出力と scratch の device 条件も DW-M07 に従う。
6. probe は独立 clone 内の pin worktree に carrier を適用する。共有 `external/ccbench` に patch を当てない。

既存実測は約 8 分 34 秒。追加 prefix 呼出し分を含む所要見積りを登録し、既存の dispatch envelope より短い timeout にしない。期待集合から外れた初回結果は消さず、DW-M08 に従って理由を確認して再登録する。

## 親 brief への反論

**P1・P2 の採用を覆す食い違いは無い。以下は主張の限定・訂正が必要。**

1. **F-3 は BACKOFF_FIXED だけではない。** template は BACKOFF_NOINLINE も追加供給する。提案する prefix 除去は両方を処理する。

2. **mocc pair の「指令差分は include 1 行のみ」は文字どおりには誤り。** 現物には複数の `#if TRACE` / `#endif` 追加もある。正しくは「define/undef の追加は無く、追加 include は trace.hh の 1 行」。今回の結論への影響は無い。

3. **「golden は動かない」は対象を限定すれば妥当。** pin・現行 template・既存 variant の静的予測として支持する。ただし F-4 の指令数ゼロだけを一般的な compiler 出力の byte 同一証明にはしない。また `compute == baseline ⇔ 同一 pre-image` は SHA-256 衝突を無視する通常の前提を含む。

4. **`-dD` は任意の前処理状態操作を記録する保証ではない。** `push_macro` は macro stack へ保存し、`pop_macro` は復元する。したがって、pragma による後続 file への影響まで今回の有限 matrix で閉じたとは言えない。対象 pin / template にこの操作は無く、golden 不変の反例にはならない。GCC の当該操作の出力 bytes は今回未実測であり、`-dD` だけで完全被覆したと断言しない。[GCC の pragma 定義](https://gcc.gnu.org/onlinedocs/gcc/Push_002fPop-Macro-Pragmas.html)

5. **`-imacros` は現行 argv に無い。** GCC では読み込んだ出力を捨て、定義状態を保持するオプションである。現物の BUILD_FLAGS と argv はこれを供給していないため、今回の prefix/golden を壊す現行経路は確認できない。将来その入力を追加した場合まで `(cxx, defines)` cache の十分性を主張しない。[GCC のオプション定義](https://gcc.gnu.org/onlinedocs/gcc/Preprocessor-Options.html)

6. **同名同値の再定義は残す。** 親の実測では command-line と同文の source `#define` も prefix 後に出る。`removeprefix` は先頭の環境部分だけを一度除去するため保持できる。これは既存 golden の変更要因ではなく、新たな source 指令を別 identity にする意図した挙動であり、H で固定する。

新しい gate・台帳機構・一般化は提案しない。既存測定の無効化も、この静的検査からは導かない。

## 総括

`-dD`、同一 argv の空入力 prefix cache、prefix 不一致時の停止を採用する。spawn registry と consumer は変更不要。新規 8 node と source-level 4 変異、recipe 8 変異の期待集合を上記のとおり起草した。

全必読資料を読み、静的照合を完了した。ファイル変更・commit・pytest・変異走行は行っていない。