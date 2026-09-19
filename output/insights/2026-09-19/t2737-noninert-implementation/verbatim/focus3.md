## 総括

**NO-GO。裁定の(a)(b)(c)は実装されていますが、同一ファイル内の外部供給macro参照まで除外する逃がし道を確認しました。**

原因は `orchestrator/tests/test_ccbench_spawn_sites.py:676` でファイルの全追加行に除外macroを割り当て、同`:704`で各条件式からそのmacroを落とすことです。末尾の `#endif` と先頭の `#ifndef` の対応は検査していません。

実関数と正規表現をASTから抽出し、メモリ上のpatchを入力して確認しました。ファイル変更・pytest・コンパイルは行っていません。

**攻撃例の結果**

以下のfile:lineは、メモリ上で構成したpatchの追加先ファイルの行番号です。

| 例 | 構成・参照箇所 | `X`の候補判定 |
|---|---|---|
| (1) 同一ファイル本文 | `one.hh:1` `#ifndef X`、`:2`値なしdefine、`:3` `#if X`、`:5–6`で閉じる | **落ちる**。本文参照も除外 |
| (2) 別ファイル参照 | `guard.hh:1–3`がguard、`use.cc:1`が`#if X` | **残る**。除外は別ファイルへ波及しない |
| (3) endifが末尾でない | `tail.hh:1–3`がguard、`:4`に`int tail;` | **残る** |
| (4) includeが先行 | `include.hh:1`が`#include <cstdint>`、`:2–4`がguard | **残る** |
| (5) 値付き既定値 | `default.hh:1`がifndef、`:2`が`#define X 0`、`:3`がendif | **残る** |
| (6) 変更ファイルのhunk | `changed.hh:1–3`にguardを追加、`new file mode`なし | **残る** |

(1)の入れ子の `#if X` は、未供給時に空macroとなるため、そのままでは有効な動作切替の証拠として不十分です。しかし、次の追加例でも候補は空になりました。

```c
// escape.hh（新規ファイル。コメントを除いて下記が1〜6行）
#ifndef X
#define X
#endif
#if X + 0
int enabled;
#endif
```

`escape.hh:4`は、未供給または`-DX=0`なら偽、`-DX=1`なら真です。**外部供給値で本文が変わるにもかかわらず、`X`が登録候補から消えます。** 最後のendifが別の条件式を閉じても(a)(b)(c)を通ることが、具体的な反例です。

**現行patchへの適用**

以下の行番号はすべて `patches/ss2pl-lock-protocol-study.patch` 内です。

| 対象 | 実物の位置 | 結果 |
|---|---|---|
| `ss2pl_lock.hh` | `:123` ifndef、`:124` define、`:173`末尾endif | `SS2PL_LOCK_HH`を除外 |
| `ss2pl_study_lock.hh` | `:179` ifndef、`:180` define、`:681`末尾endif | `SS2PL_STUDY_LOCK_HH`を除外 |
| `ss2pl_wfg.hh` | `:687` ifndef、`:688` define、`:713`末尾endif | `SS2PL_WFG_HH`を除外 |
| `study_lock_test.cpp` | 最初のdirectiveは`:955`のinclude | guard除外なし |
| `ycsb_ss2pl.cc` | 最初は`:2668`の`#define GLOBAL_VALUE_DEFINE` | guard除外なし |
| `wfg.cc` | 最初は`:2242`のinclude | guard除外なし |

現行`patches/`全体では、新設の除外条件を無効にした場合との差分は**上記guard 3個だけ**でした。修正後は39候補で`DEFINE_SPECS`と一致し、`SS2PL_LOCK_IMPL`、`SS2PL_LOCK_KIND`、`SS2PL_DLR`、`SS2PL_WFG_DIAG`は残ります。登録位置は `orchestrator/campaign/condition_meaning_gate.py:160`以降です。現物への適用は意図どおりです。

**裁定条件との対応**

| 条件 | 状態 | 実装対応 |
|---|---|---|
| (a) 新規file・最初のdirectiveがifndef | **closed** | `test_ccbench_spawn_sites.py:663`、`:665`、`:669` |
| (b) 直後の追加行が値なしdefine | **closed** | 同`:673`で全文一致 |
| (c) 最後の非空追加行がendif、末尾コメント許容 | **closed** | 同`:671`、`:675` |
| 外部供給候補を見落とさない性質 | **regressed** | 同`:676`、`:704`により`escape.hh:4`も除外 |

(c)のclosedは裁定の文言への適合です。先頭guardとの対応や、同じmacroの別用途がないことまでは証明しません。

追加unit testの正例は同`:2856`、負例2つは`:2861`と`:2865`、検査は`:2869–2871`です。(5)(6)の過剰除外は捕まえますが、**(1)と追加反例は捕まえません**。(2)(3)(4)もfixtureに含まれません。

親報告の **180 passed / 2 skipped** と現行候補集合の一致は、この反例と両立します。現物の修復は確認できましたが、指定された「受理集合の逃がし道」の観点ではNO-GOです。