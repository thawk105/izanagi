# [T-2731] 既裁定と一次資料の逐語

## 第 20 回 rulings 項 2 (docs/spool/decisions/2026-09-17-rulings-all-20260917-1.md、main ad12ba35b、fold 前で D 番号未採番)

```
## {{D:rulings-full20-verdicts}}. 全 39 項の裁定 — 8b 再開と実測到達した identity の穴を前へ進め、gate の新設は実害の観測に限り、道具は受理述語を変えずに直す

**決定 (ユーザー裁定):** 索引 39 項の説明と推奨に対し、ユーザーは「推奨通りで」と回答した。
下の番号は会話の索引番号と一致する。本決定は裁定記録であり、実装・追補・測定が完了したことを
意味しない。各実装は名指しの変更に限定し、付随する gate・台帳・汎用化を足さない。

**提示から本記録までの間に main が entry 1579 から 1595 へ進んだ。** 項 1 の対象は entry 1591 が
候補生成まで消費し、新しい裁定パッケージ ((a) 打ち切り、(b) 世代導入 → 承認 → pointer、(c) 床の採否、
(d) growth hold の帰結) を起票した。**索引に出していないため本決定は触れない。** 項 11 の関連項
(floor セルの読取経路) は entry 1595 が実装済みで、本決定の「AI 対照実測先行」は消費された。
項 2 の対象は fold で採番され、状態語の更新は本 wave が行う。

**相談の採否:** 別系統モデル 2 本 (推奨の当否・索引漏れ) が起草推奨 28 件のうち 5 件を覆し (反対 1・根拠不足 4)、
既裁定の誤引用 4 件を訂正させ、索引漏れ 9 件のうち 8 件を親が現物照合で採用した。各項の理由に明記する。
...
### 項 2 — 実測到達した identity の穴は指令を pre-image に乗せて塞ぐ

対象: T-2731。

**決定:** `source_digest` の identity が `#define` / `#undef` の file 間効果を見ない欠陥に対し、
(a) `_cpp_normalize` に `-dD` を足して指令を pre-image に乗せる。golden digest が動く = identity 版の
変更なので、規律 7 の再検証発火条件 (変異 M3b / M6 が別 identity になり、M0 は同 identity のまま) を
**結果を見る前に**定めてから実装する。

**理由・採らない案:** 変異走行で到達が実測された正しさ欠陥 (規律 2 の一次防壁の穴、M6 は規律 1 も) であり、
仮想リスク向けの gate ではない。(a) は 1 箇所の変更で受理集合を狭める向きである。(b) 指令行の HEAD 一致検査は
将来の template の正当な `#define` を禁じる。(c) TU 単位 digest は依存供給と configure が identity の前提になり
環境依存が強い — **相談の指摘により、D34 が却下したのは別案 (`-dM` の builtin 注入) であって TU 単位 digest
そのものではないことを確認し、(c) の不採用理由を既裁定でなく環境依存に置く。** (d) 限界明記は一次防壁が
template 信頼に依存することを認めるため採らない。

```

## F1016 (docs/failures.md)

```
### F1016. 非再帰な走査境界を `#define` / `#undef` の漏れと include の挟み込みが抜け、別のプログラムが stock の identity を受け取った [恒真ゲート] [テスト代表性]

- 事象: 2026-09-16 [T-2630] の計算ノード実測 (bnode001、変異 harness 10 request) で、`include/backoff.hh` の
  include 直後に `#undef SLEEP_READ_PHASE` + `#define SLEEP_READ_PHASE 1` を置いた variant (M3b) が、実
  `source_digest.resolve()` で `src_token = "stock"`、pre-image と receipt の variant ID (`19d4249ef295`) も pure stock と
  一致したまま、実 configure 由来の compile command で前処理した `cc/silo/transaction.cc` に `sleepTics(1);` が入り、object
  も別物になった。同じ形で `TRACE 1` を漏らす M6 は `assert_trace_diff_matches_head` (規律 1 の diff-of-diffs) も通過し、
  object に `izanagi_trace` symbol が 8 個入った。synthetic 枝内に置く M3a は兄弟 variant と token 衝突、`#include` の前後で
  macro を定義・解除する挟み込み (M4 / M4b) も include 行一致検査を素通りした (M4 は compile 失敗、M4b は x86-64 で生成
  コード不変)。対照 M0 / M1 / M2 は登録どおり。
- 根本原因: identity は `EVOLVE_BLOCK_SOURCES` の 3 file を `#include` 除去のうえ**単独で** `-E -P` した出力しか見ない。
  `#define` / `#undef` は前処理器が消費して出力に現れず、file 自身の本文がそのマクロを使わなければ digest は動かない。
  一方、実 TU は 3 file と header を 1 つの翻訳単位として組むので、指令の効果は後続 header と別 file の本体へ届く。
  include 行の HEAD 一致検査は include 行そのものしか見ず、条件指令検査は `#define` 本体の `##` と `__has_include` しか
  見ない。T-148 (2026-07-28) の A-n2「`#undef` 未モデル」は file 内の条件枝の論点で、file 間の漏れは扱っていなかった。
- 恒久対応: 修正は [T-2731] として起票 (裁定待ち。選択肢は
  `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` §8、親推奨は `_cpp_normalize` への `-dD`)。現行で
  残る層は `build_admission.py:674-676` (STOCK_BASELINE は `tracked_clean` 必須、`tracked_diff_sha256` は変異ごとに別) と
  `buildcache._assert_no_trace_symbols` (M6 の symbol を binary で捕まえる対象)、coder 面は `diff_quarantine` の
  `HOLE_ESCAPE` (hole 内の生指令を拒否)。**identity 層 (loop の skip key) には無い。**
- 再発検知: 同 insight §9 の recipe で変異 harness を再走する (M3b / M6 が正例、M0 が負例)。修正後は M3b / M6 の
```

## D34 (docs/decisions.md、-undef 廃止と案 C 却下の逐語)

```
## D34. source_digest の -undef を廃止 — builtin definedness (#ifdef __x86_64__) の偽 cache hit を封鎖 (方針 A の一次防壁健全化)

**背景 (3 巡目敵対検証の critical):** 方針 A (D30/D33) は guard_write から payload 検査を削除し、identity の
正直さ (偽 cache hit 防止) を source_digest の preprocess 後ハッシュに委譲した。ところが 3 巡目検証で、その
委譲先自身が偽 cache hit を許すことが実 g++ ビルドで実証された。source_digest の digest は `g++ -E -undef` で
builtin (__x86_64__ 等) を全消しするため、EVOLVE-BLOCK に `#ifdef __x86_64__ / 別挙動 / #else / stock / #endif`
と書くと、digest 環境では stock 枝に落ち preprocess 出力が baseline と byte 一致 → src_token='stock' に化け、
別挙動の variant が verify を素通りして stock の certified 結果を継承する (規律2 直撃)。`#if __x86_64__` (値参照)
は -Werror=undef が捕えるが、`#ifdef`/`#ifndef`/`defined()` (definedness テスト) は -Wundef を発火させず素通る。
source_digest の docstring 自身 (道Y) が「-undef の乖離があるから EVOLVE-BLOCK 内の生 #ifdef を hook で禁止する」
ことを前提にしていたが、方針 A でその hook 検査を削除したため前提が崩れ、責務が一次防壁に移植されないまま宙に
浮いていた (coder 未実体化ゆえ攻撃は未 live だが、coder 投入前に塞ぐべき kickoff-blocking の穴)。

**決定 (案 A、ユーザー承認 2026-07-04):** `_cpp_normalize` の g++ フラグから `-undef` を外し、組込 builtin を
**実ビルドと同じく定義済みのまま** preprocess する。`-nostdinc` (系ヘッダ遮断) は維持。これで `#ifdef`/`defined()`
が digest に正直に反映され、別挙動の variant は別 digest = 別 cache_key = cache-miss で正しくビルド+verify される。
実 g++-13 で検証: `#ifdef __x86_64__` は -undef あり=stock枝(偽hit)・-undef なし=実枝(999、実ビルド一致)。
-Werror=undef の骨格 #if 供給漏れ検出は維持され、条件指令なしの stock digest は 2 回実行で同一 (STOCK 後方
互換保持)。回帰 `test_source_digest_builtin_ifdef_not_aliased_to_stock` + 変異検査 (-undef を戻すと赤) で固定。

**trade-off と却下案:**
- 代償 = digest 値が cxx/環境に依存する (別環境で別値) が、cache は env/<tag> 軸で環境別 (D13) ゆえ実害なし。
  計測層は単一実機に集約済み。非決定 builtin (__DATE__ 等) は churn するが偽 hit しない (毎回 cache-miss =
  新規ビルド+verify、正しさ不変)。旧 payload 検査が __DATE__ を禁じていた理由 (-undef 下の digest 非被覆) は
  -undef 廃止で消える (churn に格下げ)。
- 却下: 案 C (-dM で実 builtin を明示注入、-undef 維持) は環境非依存を保つが実装が重く規律5 と緊張。
  案 B (payload の生 #ifdef を検出 abort) は骨格 #if と payload #if の区別に skeleton 抽出が要り完了条件 1
  (inert=stock) と両立せず (docstring L34 が既に難しいと明言)。
- 残る穴: computed include (`#if __has_include`) は #include 行に現れず -nostdinc で dead 化 = 依然 identity に
  乗らない (known-limitation、auditor + 規律6 監査領域、恒久 fix は skeleton 抽出が要り却下済み)。

```

## insight §8 裁定パッケージ (output/insights/2026-09-16/t2630-scan-boundary-reach/README.md)

```
## 8. 裁定パッケージ (修正は本 wave では実装しない)

到達は実測で確認された正しさ欠陥 (規律 2 の一次防壁の穴、M6 は規律 1 も) なので、修正を起票して返す。
選択肢 (親の推奨は (a)):

- **(a) 指令を pre-image に乗せる。** `_cpp_normalize` に `-dD` を足す (`-dD` は前処理結果に加えて `#define` / `#undef` を
  出力し、predefined は含まない)。`#define` / `#undef` が 1 行でも増減すれば digest が動き、別 identity として自分の
  build・verify を受ける。変更は 1 箇所。**代償**: 既存の golden digest (`test_source_digest_preimage_join_has_pre_refactor_golden_digests`
  等の silo 8 golden id) が動く = identity 版の変更であり、規律 7 の「再検証の発火条件」を結果を見る前に決める必要がある。
  本 wave の M3b / M6 が正例、M0 が負例になる。
- **(b) 指令行の一致検査を足す。** `assert_includes_match_head` と同型で `#define` / `#undef` 行の列を HEAD と比較する。
  template patch 自体が `#define` を足していない (skeleton は `#if/#else/#endif`) ので template は通る。**代償**: 将来の
  template や coder 面が正当に `#define` を使えなくなる (現行の hole 契約は既に禁止しているので実害は小さい)。
- **(c) TU 単位の digest。** 実 include path で TU 全体を前処理して digest する。**代償**: 依存供給と configure が identity の
  前提になり、環境依存が強くなる。D34 が「skeleton 抽出が要る」と却下した方向に近い。
- **(d) 限界として明記し、template の信頼境界に委ねる。** coder 面は `HOLE_ESCAPE` が塞ぎ、template は人間が書く。
  **代償**: 規律 2 の一次防壁が「template を信頼する」前提を持つことを認める。

**還元判断: ユーザー確認待ち** (CCBench 本体のバグ報告ではない。izanagi の identity 層の欠陥)。

---

```

## 親の前提実測 (login pegasus02、2026-09-17、g++ 11.4.0 = /usr/bin/g++、g++-12)

### probe script (job tmp/s2probe.py)
```python
import subprocess, hashlib
ARGS = ["g++", "-E", "-P", "-dD", "-nostdinc", "-Werror=undef", "-std=c++20", "-O3", "-DNDEBUG", "-DFOO=0", "-DBAR=1", "-x", "c++", "-"]
def run(src):
    r = subprocess.run(ARGS, input=src, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout
prefix = run("")
print("prefix lines", prefix.count("\n"), "last:", repr(prefix.splitlines()[-3:]))
cases = {
 "plain": "int a;\n",
 "undef_builtin_first": "#undef linux\nint a;\n",
 "dup_cmdline_define": "#define BAR 1\nint a;\n",
 "comment_first": "// c\n/* x */\nint a;\n",
 "leading_blank": "\n\n\nint a;\n",
 "m3b": "#undef SLEEP_READ_PHASE\n#define SLEEP_READ_PHASE 1\nint a;\n",
 "m0_comment_only": "int a; // comment\n",
}
for k, src in cases.items():
    out = run(src)
    ok = out.startswith(prefix)
    body = out[len(prefix):] if ok else None
    print(f"{k:22s} startswith={ok} body={body!r}")
# prefix determinism across 3 runs
print("prefix stable:", len({hashlib.sha256(run('').encode()).hexdigest() for _ in range(3)}) == 1)
```
### 出力
```
prefix lines 440 last: ['#define NDEBUG 1', '#define FOO 0', '#define BAR 1']
plain                  startswith=True body='int a;\n'
undef_builtin_first    startswith=True body='#undef linux\nint a;\n'
dup_cmdline_define     startswith=True body='#define BAR 1\nint a;\n'
comment_first          startswith=True body='int a;\n'
leading_blank          startswith=True body='int a;\n'
m3b                    startswith=True body='#undef SLEEP_READ_PHASE\n#define SLEEP_READ_PHASE 1\nint a;\n'
m0_comment_only        startswith=True body='int a;\n'
prefix stable: True
```
### `-dD` の builtin 行数 (g++ / g++-12)
```
g++: builtin '#define __' lines = 419
g++-12: builtin '#define __' lines = 437
skipped 枝 (#ifdef BAR 内の #define INSIDE) は -DBAR 無しで 0 行、有りで 1 行
```
