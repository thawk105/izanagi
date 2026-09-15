# [T-1643] `__has_include` 族を実 pair で実測した対照表

`authority: none` / `default_effect: no-state-change` — これは**実測記録**である。可変状態の正本
(worklog 末尾・現行 phase doc) ではなく、checker の受理集合も変えていない。

- 実測日: 2026-09-14
- 実測機: login node `pegasus02` と計算ノード `bnode009` (NQSV request `997000.nqsv`)
- 基準 commit: `c2a28d67d` (wave branch `worktree-dev-wave-t1643-has-include-pair`)
- 依頼: 「`__has_include` 族を g++-13 と admission toolchain の実 pair で実測する。結果を見る前に
  『欠陥がある』と決めず、実測した対照表そのものを成果物にする。checker の一般化へは広げない。」

---

## 1. 何を測ったか

`orchestrator/campaign/source_digest.py` の checker は、variant の identity (= `src_token`) を
決めるために対象ソースを preprocess する。checker は `#include` 行を除去して **stdin** から
`-nostdinc` で preprocess する (`:1662`-`:1666`) 一方、実 build は CCBench の実 include path で
compile する。`__has_include` は header 探索の結果に依存するので、**同じ式が両者で違う値を取りうる**。

本 wave はその真偽を、実在する compiler で実測して対照表にした。**checker の実装は変えていない。**

### 測った環境 (列)

| 列 | 中身 |
|---|---|
| `checker-normalize` | `_cpp_normalize` の exact argv。`[cxx, -E, -P, -nostdinc, -Werror=undef, -std=c++20, -O3, -DNDEBUG] + sorted(-D…) + [-x, c++, -]`、入力は stdin |
| `checker-dM` | `_dump_macros` の exact argv (`-P` と `-Werror=undef` を持たない) |
| `build-search-reconstructed` | 実 build の探索条件を **再構成**した列。configure は 10 回とも失敗したため `compile_commands.json` は取得できていない |
| `build-header` | header 文脈の補助列。`/tmp` の相対構造と symlink を使う。実 header 位置ではない |

文脈は `TRACE` × `GLOBAL_VALUE_DEFINE` の 4 通り。以下の表は `TRACE=0, GLOBAL_VALUE_DEFINE=0` である。

---

## 2. 対照表

**`g++` / `g++-11` / `g++-12` の 3 名称、および login `pegasus02` と compute `bnode009` の
両方で、下表は完全に一致した。** (`g++` と `g++-11` は同一実体への別名。§3 を見よ。)

| case | 式 (前置定義がある場合は併記) | `checker-normalize` | `build-search-reconstructed` | `build-header` |
|---|---|---|---|---|
| `system-angle` | `__has_include(<vector>)` | **error(rc=1)** | 1 | 1 |
| `system-quote` | `__has_include("vector")` | **0** | **1** | **1** |
| `root-angle` | `__has_include(<include/tsc.hh>)` | **error(rc=1)** | 1 | 1 |
| `root-quote` | `__has_include("include/tsc.hh")` | **0** | **1** | **1** |
| `header-angle` | `__has_include(<tsc.hh>)` | **error(rc=1)** | 0 | 0 |
| `header-quote` | `__has_include("tsc.hh")` | **0** | 0 | **1** |
| `atomic-angle` | `__has_include(<atomic>)` | **error(rc=1)** | 1 | 1 |
| `atomic-quote` | `__has_include("atomic")` | **0** | **1** | **1** |
| `literal` | `#define IZ_H __has_include` → `IZ_H(<include/tsc.hh>)` | **error(rc=1)** | 1 | 1 |
| `function` | `#define IZ_H(x) __has_include(x)` → `IZ_H(<vector>)` | **error(rc=1)** | 1 | 1 |
| `operand` | `#define IZ_HEADER <include/tsc.hh>` → `__has_include(IZ_HEADER)` | **error(rc=1)** | 1 | 1 |
| `paste` | `#define IZ_H __has_inc##lude` → `IZ_H("tsc.hh")` | **0** | 0 | **1** |
| `next-vector` | `__has_include_next(<vector>)` | **error(rc=1)** | 1 | 1 |
| `next-tsc` | `__has_include_next("tsc.hh")` | 0 | 0 | 0 |
| `next-root` | `__has_include_next(<include/tsc.hh>)` | **error(rc=1)** | 1 | 1 |
| `next-literal` | `#define IZ_H __has_include_next` → `IZ_H(<vector>)` | **error(rc=1)** | 1 | 1 |
| `positive-quote` (正の対照) | `__has_include("/tmp/…/present.hh")` | **1** | 1 | 1 |
| `positive-angle` (正の対照) | `__has_include(</tmp/…/present.hh>)` | **1** | 1 | 1 |
| `negative-quote` (負の対照) | `__has_include("/tmp/…/missing.hh")` | 0 | 0 | 0 |
| `negative-angle` (負の対照) | `__has_include(</tmp/…/missing.hh>)` | 0 | 0 | 0 |
| `flip-1` / `flip-0` (反転対照) | `__has_include("/tmp/…/flip.hh")` (存在 / 除去) | 1 / 0 | 1 / 0 | 1 / 0 |
| `extract-1` / `extract-0` (抽出対照) | `#if 1` / `#if 0` | 1 / 0 | 1 / 0 | 1 / 0 |
| `safe-define` (guard 対照) | `#define IZ_OK 1` → `#if IZ_OK` | 1 | 1 | 1 |

`error(rc=1)` の診断は次の形である (逐語):

```
<stdin>:2:19: error: no include path in which to search for vector
(null):0: confused by earlier errors, bailing out
```

### 表から読み取れること

1. **quote 形式は checker 列で 0、再構成探索列で 1 になった** (`system-quote` / `root-quote` /
   `atomic-quote`)。`header-quote` と `paste` は `build-header` 列だけが 1 である。
2. **angle 形式は 0 に倒れない。** `-nostdinc` 下では探索パスが 1 つも無いため、
   `__has_include(<X>)` は偽値ではなく **preprocess の失敗 (rc=1)** になる。
   `source_digest.py:372-373` のコメントは
   「`__has_include` 系だけは header 探索パスに依存し digest が `-nostdinc` で**常に 0 に倒れる**」
   と書いており、**angle 形式についてこの説明は今回の観測と一致しない**。
   guard の拒否診断本文にある「digest 環境は -nostdinc で header 未発見 = dead 枝」も同じである。
   **ただし preprocess の非ゼロ rc は `_cpp_normalize` で `RuntimeError` になる**ため、
   0 に倒れる場合も失敗する場合も**いずれも fails-closed 側**であり、受理集合が広がる向きではない。
3. **「`-nostdinc` だから全部偽」という結論は成立しない。** 正の対照 (絶対 path の照会) は
   checker 列でも 1 になった。probe が何も測らずに全偽を返しているのではないことの証拠である。
4. 負の対照は全列 0、反転対照と抽出対照は 0/1 に分かれた。

---

## 3. compiler の実測

| requested | login `pegasus02` | compute `bnode009` | 実体の SHA-256 (先頭 12) |
|---|---|---|---|
| `g++` | `/usr/bin/g++` 11.4.0 | `/usr/bin/g++` 11.4.0 | `2360901d864c` |
| `g++-11` | `/usr/bin/g++-11` 11.4.0 | `/usr/bin/g++-11` 11.4.0 | `2360901d864c` |
| `g++-12` | `/usr/bin/g++-12` 12.3.0 | `/usr/bin/g++-12` 12.3.0 | `88315fd2d961` |
| `g++-9` | `/usr/bin/g++-9` 9.5.0 | **不在** | — |
| `g++-13` | **不在** | **不在** | — |

- **`g++` と `g++-11` は realpath も SHA-256 も同一**である。表の 3 名称は **2 実体**であり、
  独立 2 例 (`DW-G03`) には数えない。
- **`g++-9` は今回の argv では真偽を取得していない。** checker の `BUILD_FLAGS` にある
  `-std=c++20` を認識せず、`error: unrecognized command line option '-std=c++20'; did you mean
  '-std=c++2a'?` で全 cell が失敗した。これは「差が無かった」ではなく「測っていない」である。
- **`g++-13` は login でも compute でも不在だった** (`found=None`、`FileNotFoundError`)。
  依頼が指定した「g++-13 との実 pair」は、この機体では実測できない。
  D293 は「固定要求のまま `g++-13` を Pegasus へ用意する」を却下済みである。
- `orchestrator/campaign/buildcache.py:1838` `compilers_for_current_site()` は Pegasus compute で
  `("gcc", "g++")` を返す。したがって **compute で実測した `/usr/bin/g++` 11.4.0 が、
  この site で `compilers_for_current_site()` が選ぶ compiler の実体**である。
  ただし §5 のとおり、これは本番 admission の呼出しに対応づけたものではない。

---

## 4. checker の実 guard 関数の発火

`source_digest._assert_conditional_macros_covered` を**実関数で**呼んだ (内部関数・subprocess を
stub にしていない)。**login と compute で件数は完全に一致した。**

| 分類 | 件数 | 発生箇所 |
|---|---|---|
| `reject_condition_operator` | 204 | `source_digest.py:1868` の専用 raise |
| `reject_define_operator` | 60 | 同 `:1853` |
| `reject_token_paste` | 20 | 同 `:1846` |
| `accepted` | 36 | 拒否されず通過 (`safe-define` 等) |
| `other_error` | 180 | `_dump_macros` 起因の前段失敗 (g++-9 が 84、g++-13 が 84、動作する 3 名称の `operand` 行が 12) |

**これは「渡した fixture に対する拒否箇所別の件数」である。** 実 variant が resolver でこの拒否点へ
到達したことの実測ではない。走査対象は `EVOLVE_BLOCK_SOURCES` の 3 file
(`include/backoff.hh`, `cc/silo/transaction.cc`, `cc/mocc/transaction.cc`) で**非再帰**であり、
`_cpp_normalize` と `_dump_macros` は `#include` 行を除去する。

`other_error` 180 件を include 演算子の専用拒否へ合算してはならない。

---

## 5. この表から言ってよいこと・言ってはいけないこと

| 書いてよい | 書いてはいけない |
|---|---|
| 記録した stdin fixture について、quote 3 ケースは checker 列で 0、再構成探索列で 1 だった | checker と実 build で真偽が食い違うことを実証した |
| angle ケースは checker 列で preprocess error になり、真偽値を取得しなかった | angle も checker では 0 になる |
| 「常に 0」というコメントは今回の angle 観測と一致しない。受理集合の破れは未証明である | コメントと違うので checker の欠陥が確定した |
| 実 guard 関数は、渡した fixture に対して条件演算子の拒否点で 204 件拒否した | resolver が実 variant 204 件をこの拒否点で遮断した |
| `g++` と `g++-11` は同一実体への別名だった | 独立した 2 compiler で再現した |
| `g++-9` は今回の argv では真偽未取得だった | g++-9 では食い違いが無かった |
| 成立列の限定観測を保存した。全体の対照は不成立で、結論は保留する | 不成立列を除けば全対照成立なので実 pair 検証は完了した |

**対照は 820 件中 508 件成立・312 件不成立で、`controls_passed = false`、`conclusion = null` である。**
不成立はすべて `g++-9` (各 156 件) と `g++-13` (各 156 件) に局在し、
`g++` / `g++-11` / `g++-12` は各 164 件すべて成立した。成立列の観測は事実として書けるが、
wave 全体の結論は保留する。

---

## 6. 実測の限界 (probe 自身が `limitations[]` に記録したものを含む)

1. **stdin 置換の限界。** checker 列も `build-search-reconstructed` 列も入力は stdin である。
   GCC の quoted 探索は「現在 file のディレクトリ → `-iquote` → 通常の探索列」の順だが、
   stdin には file 名が無く、その基点は cwd に帰着する。**両列の差は、記録した cwd・argv・env での
   人工 stdin の評価であり、実 TU の評価ではない。**
2. **configure は 10 回とも失敗した。** `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` と
   `FETCHCONTENT_FULLY_DISCONNECTED=ON` で試みたが依存物を取得できず、実 build 列は**再構成**である。
   推移的 include の順序・`-isystem` 化・暗黙 system path・生成 header の有無は未解決である。
   **再構成列を admission の実 build 実測と読んではならない。** 便宜的な
   `-I <ccbench root>/include` は追加していない (実 build の common target が公開するのは
   ccbench root 自身であり、`include/` ではない — `external/ccbench/CMakeLists.txt:68`)。
3. **`build-header` 列は `/tmp` の相対構造と symlink**であり、実 header 位置ではない。
   `__has_include_next` は探索開始位置に依存するため、この列から実 header 内の挙動は結論できない。
4. **guard 直呼びは resolver の全経路実走ではない。** 先行する allowlist / include 検査、
   repo 不在マクロ確認を通っていない。
5. **compute の観測は `generic` task 経由である。** dispatcher は `env_mode="clean"` で
   `CPATH` / `CPLUS_INCLUDE_PATH` 等を保持せず、cwd を repo root に固定する。
   本番 admission の呼出しと探索環境まで対応づけた実測ではない。
6. **2002 (login) / 2000 (compute) の cell は「記録」であって「真偽実測」ではない。**
   真偽取得は各 960 件で、残りは preprocess error・compiler 不在・未測 placeholder である。
7. `GLOBAL_VALUE_DEFINE=1` は合成した overlay であり、実 TU から抽出したものではない。

---

## 7. 既存記録との差分 (純増)

既存の T-148 レビュー記録には次がある。**今回が初被覆ではない。**

- `output/insights/2026-07-28/t148-review-verbatim/review-focus-claude-closed-partial-table.md:15`
  — 貼り合わせ形 (`#define IZ_H __has_inc##lude` + `#if IZ_H("tsc.hh")`) の明示的な 0/1 pair
  (逐語「実測: `-nostdinc` で 0、既定 path で 1」、g++-12)。
- 同 `review-B-codex-layers-and-test-teeth.md:59` — literal 間接形
  (`#define IZ_HAS_LOCAL __has_include("atomic_wrapper.hh")`)。
- 同 `:101` — 「g++12 では `-nostdinc` + `<atomic>` 自体が preprocess error になり、
  blanket guard 以外の理由でも赤」。**今回の angle 形式の観測はこれと同型である。**
- `docs/decisions.md:801` の g++-13 実測は `#ifdef __x86_64__` についてであり、
  `__has_include` 族の実測ではない。

**今回の純増は、式名や compiler 列数ではなく、次の exact な確定である。**

- checker の実 argv (`_cpp_normalize` / `_dump_macros` 双方) と cwd・env を記録した上での
  quote / angle / 間接形 / `__has_include_next` の値と診断。
- **angle 形式が 0 ではなく preprocess error になること**の、現行 checker argv 下での確認。
- 現行 guard の拒否箇所別件数 (`:1868` / `:1853` / `:1846`) の実測。
- **login と compute の compiler 実体の同一性** (SHA-256 一致) と、`g++-13` の両所での不在の、
  今日の確認。

---

## 8. 一次資料の所在

raw JSON は 36 MB / 20 MB あり、repo には入れていない (リポジトリ膨張の実測 = worklog entry 1483)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1643-has-include-pair/` に保全した。

| file | 中身 |
|---|---|
| `probe-login-parent.json` | login `pegasus02` の全 2002 cell (36 MB) |
| `probe-compute.json` | compute `bnode009` の全 2000 cell (20 MB) |
| `t1643_has_include_pair_probe.py` | probe 本体 (475 行、Codex `role=author` が作成、repo へは残さない) |
| `s1-brief.md` / `s2-plan-out.md` / `s3-sol-out.md` / `s3-luna-out.md` | 段 1〜3 |
| `s4-ruling.md` | 段 4 裁定 (所見の real/refuted、plan v2、主張範囲) |
| `s5-author-out.md` / `s5-implementation.diff` | 段 5 |
| `s6-sol-out.md` / `s6-luna-out.md` | 段 6 敵対レビュー 2 本 |

子の逐語は本 dir の `verbatim/` にも複製した。

**`verbatim/` は可逆最小正規化を施してある** (`DW-S07`)。Markdown の強制改行に使われていた
**行末空白だけ**を `sed -i 's/[ \t]*$//'` で除去した (可視文字は不変)。原文は job dir 側にあり、
下表の SHA-256 と byte 数で同定できる。

| verbatim/ の file | 原文 (job dir) | 原文の SHA-256 | 原文の bytes |
|---|---|---|---|
| `s1-brief.md` | `s1-brief.md` | `a226af2c3617ab51ec7d4174a1ca87a74f67dae7b2fbd97b5d90d98cb67b44b9` | 6084 |
| `s2-plan.md` | `s2-plan-out.md` | `2fac4a930dddaa1d532b70d233f8125d2fe476f23627c4c8c625817baf9a97ac` | 17003 |
| `s3-sol.md` | `s3-sol-out.md` | `5b3f17d633021e3bf16637de700b92eb4c3e06c9744a9b98eaf32965a079cb80` | 9919 |
| `s3-luna.md` | `s3-luna-out.md` | `5b1eac4b2318aea3f77fa2197f4a0c4786460a3add9dc2b1a354c5dba657c7bc` | 10518 |
| `s4-ruling.md` | `s4-ruling.md` | `dc221e079afbf09a656ed88b7ccb5c24b8891969041d42eeacfc7819791f1ca9` | 14562 |
| `s5-author.md` | `s5-author-out.md` | `6b4655ff7397465ed4fac7d87c6a796edf9d26c62eff4f42c7450eb9a0093c51` | 2725 |
| `s6-sol.md` | `s6-sol-out.md` | `b3173341f060d0c0bddde2045f0608d145e72fa4776513547b2033665b647087` | 4990 |
| `s6-luna.md` | `s6-luna-out.md` | `43aca52bbc2d0e6bf6257dc6abd2383a45aa51fe2ed771894e90c006015f5dc9` | 8701 |

compute 実測の再現:

```
python3 tools/pegasus/dispatch_compute.py --task generic \
  --queue-wait-timeout 240 --overall-grace 240 --walltime 00:10:00 \
  -- python3 -B tools/t1643_has_include_pair_probe.py --output <出力先>
```

`--walltime` は **HH:MM:SS 形式**でなければ rc=16 (setup-failure) になる。

---

## 9. 裁定パッケージ候補 (scope 外の real 所見)

本 wave では実装しない。

- **(R-1) legacy 分岐の compiler 引数の非対称。** `orchestrator/campaign/pipeline.py:1790` が
  site 選択した compiler を checker へ渡す一方、`common is None` の legacy 分岐 (`:2002`、
  `buildcache.py:3140`) は `cc/cxx` を渡さず既定 `g++-13` を使う。静的に確認できる非対称であり、
  到達可能性と既存防壁との関係の評価は別裁定。
- **(R-2) 走査範囲外の include 先の一般安全性。** `source_digest.py:85` / `:1895` / `:1662` の
  非再帰な走査境界は実在するが、そこから許可された variant が実際に別挙動・stock identity 継承へ
  到達するかは未証明である。今回は安全性主張の除外範囲として記載するに留める。
- **(R-3) コメントと観測の不一致。** `source_digest.py:372-373` と guard の拒否診断本文は
  `__has_include` が `-nostdinc` で「常に 0 に倒れる / dead 枝になる」と説明するが、
  angle 形式では preprocess error になる。**どちらも fails-closed 側なので受理集合は変わらない。**
  記述を実測に合わせるかは checker の変更にあたるため、本 wave の scope 外 (依頼が
  「checker の一般化へは広げない」と明示) であり、裁定に委ねる。

**還元判断: ユーザー確認待ち** (CCBench 本体のバグ報告ではないが、上記 3 件は人間の裁定を要する)。
