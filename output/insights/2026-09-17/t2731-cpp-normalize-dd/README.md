# [T-2731] `_cpp_normalize` に `-dD` を足し、`#define` / `#undef` を identity の pre-image に乗せた (F1016 の修復)

`authority: none` / `default_effect: no-state-change` — これは**実装と実測の記録**である。可変状態の正本
(worklog 末尾・現行 phase doc) ではない。

- 実装日: 2026-09-17 (JST 06:45〜)、wave branch `worktree-dev-wave-t2731-cpp-normalize-dd`、base = local main b4631a92e
- 裁定: D2104 項 2 (第 20 回 rulings 全件、決定 = (a) `_cpp_normalize` に `-dD`)
- 実装 commit: bd21bc501 (本体 + 回帰 test 8 node)、2cc661235 (段 6 fix: test の署名固定と docstring 注記)
- 依頼: 「`_cpp_normalize` に `-dD` を足し、`#define` / `#undef` の指令を pre-image に乗せる。golden digest が動く =
  identity 版の変更なので、規律 7 の再検証発火条件 (M3b / M6 が別 identity になり M0 は同 identity のまま) を結果を
  見る前に登録してから実装する。最終層 `_assert_no_trace_symbols` が残ることを併記。golden の更新だけで済ませず、
  記録済み測定は無効化しない。本題の 1 箇所と consumer の整合だけ。」

---

## 1. 結論を先に

- **F1016 で実測到達した衝突 (M3b / M6: file 間へ漏れる `#define` / `#undef` が stock の identity を受け取る) は、
  `_cpp_normalize` の 1 箇所の変更で塞がった。** 段 4 で結果を見る前に登録した予測 (§5) と、計算ノードでの recipe 再走
  (§6) および source-level 変異 (§7) の結果を突き合わせた。
- **既存の identity は動かない。** 実 submodule (pin 511c953、stock checkout) の silo 8 genome で、旧版と新版の
  `canonical_source_preimage_bytes` は 8/8 が byte 一致 (§6.3)。EVOLVE_BLOCK_SOURCES 3 file と template patch に
  `#define` / `#undef` が 0 行だからである。裁定文の「golden digest が動く」は、この実装形では**起きなかった**
  (identity が変わるのは指令を持つ variant だけ)。記録済み測定の無効化・再認証は要らない (規律 7)。
- **裁定文と insight §8 の前提「`-dD` は predefined を含まない」は、g++ 11.4 / 12 の実測で誤り**だった (§2)。
  素の `-dD` だと template の追加供給 (`BACKOFF_FIXED` / `BACKOFF_NOINLINE`) が compute 側にだけ `#define` 行として現れ、
  inert template ≠ stock になる。同じ argv の空入力出力 (環境 prefix) を剥がす形で実装した。
- **残る限界 (scope 外、裁定候補として起票):** include 行を除去するため「指令と include の相対位置」は識別しない
  (`define→include→undef` と `include→define→undef` は同 identity)。`#pragma push_macro` / `pop_macro` の復元値は
  `-dD` に現れない。いずれも修正前から同じで、本 wave が新しく作った穴ではない (§8)。

---

## 2. 前提実測 — `-dD` の出力形 (login pegasus02、g++ 11.4.0 と g++-12 12.3.0)

`g++ -E -P -dD -nostdinc -Werror=undef -std=c++20 -O3 -DNDEBUG -D… -x c++ -` の出力:

| 観測 | 結果 |
|---|---|
| predefined (`#define __GNUC__ 11` 等) | **出力される** (g++ 11.4: 419 行、g++-12: 437 行)。GCC 文書の「`-dD` は predefined を含まない」は当てはまらない |
| command-line `-D` (`#define FOO 0`) | 出力される (predefined の後) |
| skipped 枝内の `#define` | 出力されない |
| 空入力の出力 (= 環境 prefix) | 実入力の出力は 7 形 (plain / 先頭 `#undef linux` / command-line と同文の `#define` / comment 先頭 / 空行先頭 / M3b 形 / comment-only) すべてで prefix から始まる。3 走で決定的 |
| `__DATE__` / `__TIME__` / `__COUNTER__` | prefix には出ない (展開値は本文側) |

逐語: `verbatim/verbatim-rulings.md` (probe script と出力)、`verbatim/s3-a.md` (レンズ A の追加断片実測: push/pop、
`GCC system_header`、builtin の undef→再 define、未定義名の単独 undef)。

**なぜ剥がすか:** `compute()` は working-tree の CMake 供給、`baseline()` は HEAD (pin) の供給で defines を絞る
(`_worktree_defines` / `_head_defines`)。template patch は `cc/silo/CMakeLists.txt` の供給に `BACKOFF_FIXED` と
`BACKOFF_NOINLINE` を足すので、素の `-dD` では compute の出力にだけ `#define BACKOFF_FIXED -1` 等が現れ、
inert template (未変異の template を当てた木) が非 stock になる。受入 suite は共有 submodule に template を当てないので、
この破壊は受入では検出されない (`test_source_digest_stock_roundtrip` は stock checkout で走る)。

---

## 3. 実装 (`orchestrator/campaign/source_digest.py::_cpp_normalize`)

1. argv に `-dD` を足す。
2. 同じ argv の空入力出力を環境 prefix として `(cxx, sorted defines)` ごとに module cache (`_CPP_ENV_PREFIX_CACHE`) に取る。
   取得は `_cpp_normalize("", defines, cxx, _environment_only=True)` の再帰呼出しで、`subprocess.run` の call site は
   関数内の 1 箇所のまま (spawn site 登録簿 `test_ccbench_spawn_sites` は不変)。
3. 実入力の出力が prefix で始まらなければ `RuntimeError` (fails-closed)。始まれば `removeprefix` して返す。
4. docstring に、理由 (F1016)、prefix を剥がす理由、skipped 枝の指令は出ないこと、残る限界 (相対位置・macro stack)、
   `_trace_pair_diff` の受理集合が狭まる向きに変わること (比較式は不変) を明記。

変えていないもの: `_normalize_contexts` の文脈列・タグ・NUL 区切り、`_trace_pair_diff` の比較式、`_dump_macros`、
`assert_includes_match_head`、`buildcache._assert_no_trace_symbols` (nm)、`diff_quarantine` の `HOLE_ESCAPE`、
spawn site / 静的 call 数の登録簿、既存 test の期待値。

段 3 で不採用にした代案: `-P` を外して linemarker で `<built-in>` / `<command-line>` を切る (正規化の意味が変わり、
comment / 空行不感の性質を別処理で再現する必要がある)、環境マクロ名で行 filter (source 自身の `#undef linux` や
同名同値の再 `#define` まで落とす)。

---

## 4. 回帰 test (fake repo、`orchestrator/tests/test_campaign.py`、8 node)

| 略号 | node | 主張 | 修正前 HEAD での予測 |
|---|---|---|---|
| A | `test_source_digest_toplevel_macro_directives_change_identity` | include 直後の top-level `#undef X` + `#define X 1` (本文は X を使わない) → `resolve != "stock"` かつ `compute != baseline` | 赤 |
| B | `test_source_digest_toplevel_trace_directives_change_identity` | 同形で `TRACE` → 別 identity。`assert_trace_diff_matches_head` は通過 (fake backoff は TRACE を参照しない)。最終層 nm は本 test では走らない | 赤 |
| C | `test_source_digest_comment_only_preserves_stock` | comment-only → `"stock"` | 緑 |
| D | `test_source_digest_unused_universal_supply_preserves_stock` | working-tree の Options.cmake にだけ未参照の universal 供給 → `"stock"` (prefix 剥がしの負例) | 緑 |
| E | `test_source_digest_unused_protocol_supply_preserves_digest` | protocol CMake にだけ未参照の供給 → `compute == baseline` | 緑 |
| F | `test_source_digest_skipped_macro_directives_affect_only_live_variant` | dead 枝の指令は stock を保ち、live な兄弟 variant の identity だけ変える | 赤 |
| G | `test_source_digest_cpp_environment_prefix_mismatch_fails_closed` | `cxx` seam の偽 compiler (空入力と実入力で別の prefix) → `RuntimeError("… 環境 prefix と不一致 …")` | 赤 |
| H | `test_source_digest_same_value_source_redefine_changes_identity` | command-line と同名同値の source `#define BACK_OFF 1` も別 identity | 赤 |

G は monkeypatch を使わず、`_cpp_normalize` の正規注入 seam (`cxx` 引数) に実行可能 script を渡す (DW-O14)。

---

## 5. 規律 7 の再検証発火条件 (段 4、結果を見る前に登録: 2026-09-17 07:10 JST)

`verbatim/s4-ruling.md` §4 の表。要点: M3b / M6 は 4 node 赤 (N1a: stock token ≠ "stock"、N1b: variant token ≠ reference、
N2a / N2b: TU 差)、M0 は SURVIVED、M3a は N1b+N2b、M4 / M4b は 4 node、M1 / M2 は不変、baseline は PASSED で variant token =
`d8a4a10d163d14c391745b8e7c89322349e7ebe60f539c2913a340e94c0383cc` (T-2630 と同値)。
実 submodule の `test_source_digest_stock_roundtrip` は緑。記録済み測定は無効化しない。

---

## 6. 実測 — recipe v2 (T-2630 §9 の再走、計算ノード)

実走: 2026-09-17 JST 07:38〜08:04 (UTC 22:38〜23:04)、計算ノード bnode043 / bnode044 / bnode046、NQSV request 10 本
(collection 2796、baseline 2800、M0 2808、M1 2813、M2 2857、M3a 2863、M3b 2866、M4 2871、M4b 2874、M6 2878)。
runner = probe test 4 node (`test_stock_identity` N1a / `test_variant_identity` N1b / `test_stock_owner_tu` N2a /
`test_variant_owner_tu` N2b)、probe tip c5affb156、carrier `patches/silo-backoff-fixed.patch` (sha a5e0710c…、T-2630 と同一)、
spec v2 sha256 `17cc80de…`。compiler = `compilers_for_current_site()` → system g++ (T-2630 と同じ 11.4.0 実体、
`compiler-cxx.json` を evidence に保存)。台帳 `mutation-recipe-1.json` (schema `izanagi-dev-wave-mutation/v4`)。

### 6.1 台帳: baseline PASSED、7/7 KILLED (期待 node 完全一致)、M0 SURVIVED、MISMATCH 0

| 変異 | 登録 (v2) | 台帳 | 失敗 node | 修正前 (T-2630) |
|---|---|---|---|---|
| baseline (未変異 template) | PASSED | PASSED | — | PASSED |
| M0 cmake comment 1 行 | SURVIVED [] | SURVIVED | — | SURVIVED |
| M1 synthetic 枝に `now_backoff += 1.0;` | KILLED [N1b, N2b] | KILLED | N1b, N2b | 同じ |
| M2 backoff.hh に `#include <cstdint>` | KILLED [4 node] | KILLED | 4 node | 同じ |
| **M3a** hole 内 `SLEEP_READ_PHASE=1` | KILLED [N1b, N2b] | KILLED | N1b, N2b | N2b のみ |
| **M3b** top-level `SLEEP_READ_PHASE=1` | KILLED [4 node] | KILLED | 4 node | N2a, N2b のみ |
| **M4** `desired`/`expected` 挟み込み | KILLED [4 node] | KILLED | 4 node | N2a, N2b のみ |
| **M4b** CAS relaxed 挟み込み | KILLED [4 node] | KILLED | 4 node | N2a, N2b のみ |
| **M6** top-level `TRACE=1` | KILLED [4 node] | KILLED | 4 node | N2a, N2b のみ |

### 6.2 赤理由の照合 (段 4 の A-5: KILLED の集計でなく token で読む)

各 run の `{reference,current}/{stock,variant}/token.txt` と `observations.json` (先頭 12 桁):

| 変異 | reference stock / variant | current stock / variant | current の `assert_trace_diff_matches_head` | 読み |
|---|---|---|---|---|
| baseline | `stock` / `d8a4a10d163d` | `stock` / `d8a4a10d163d` | 通過 / 通過 | 修正後も inert template = stock。variant token は T-2630 と同値 (**予測どおり**)。stock の pre-image sha `6454d9f3…0a84` は T-2630 baseline (旧版、g++ 11.4) と同値 |
| M0 | 同上 | `stock` / `d8a4a10d163d` | 通過 | 同 identity (負例) |
| M1 | 同上 | `stock` / `efadd99f22fa` | 通過 | variant だけ別 identity。値は T-2630 の M1 と同じ (指令を持たない編集の pre-image は不変) |
| M2 | 同上 | (resolve RuntimeError) | 通過 | `assert_includes_match_head` 拒否 (不変) |
| M3a | 同上 | `stock` / `1141c39d70b6` | 通過 | stock は dead 枝で不変、variant は別 identity (**兄弟 variant との衝突が解消**) |
| M3b | 同上 | `18c983be826f` / `7801b035f3cc` | 通過 | **stock 側も別 identity** (F1016 の到達例が塞がった) |
| M4 | 同上 | `2ceef5ebf703` / `5a31c02d9ae7` | 通過 | 両 genome とも基準 template と別 identity (compile は依然失敗、object 比較は無し) |
| M4b | 同上 | `2805af0fed6d` / `2c9fb1c98efd` | 通過 | 同上 |
| M6 | 同上 | `1eac00817ea4` / `70afcf6b2b2b` | **通過** | 別 identity になり自分の build・verify を受ける。diff-of-diffs は backoff.hh に TRACE 参照が無いため通過し、最終層は buildcache の nm 検査 (`_assert_no_trace_symbols`) のまま |

M3b / M6 / M4 / M4b の N2a / N2b は T-2630 と同じ実 TU 差 (`*-tu.diff.txt`)。identity の赤理由はすべて「token が
`stock` でない / reference と一致しない」であり、一律の RuntimeError ではない (M2 だけが RuntimeError で、これは登録どおり)。

### 6.3 既存 pre-image の byte 一致 (login、g++-12、実 submodule stock checkout)

旧版 (bd21bc501~1) と新版の `canonical_source_preimage_bytes` を silo 8 genome で比較した
(`verbatim/preimage-oldnew-login-gpp12.log`、script `verbatim/preimage-oldnew.py`):

| genome (canonical) | 旧版 sha256 先頭 16 | 新版 sha256 先頭 16 | bytes | 一致 |
|---|---|---|---|---|
| `silo\|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0` | `365b67e03821c54e` | `365b67e03821c54e` | 63622 | yes |
| `silo\|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=1` | `91ae07b2782c24c0` | `91ae07b2782c24c0` | 63662 | yes |
| `silo\|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` | `2d691b45afd02a79` | `2d691b45afd02a79` | 63718 | yes |
| `silo\|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=1` | `30a97b5296b74a38` | `30a97b5296b74a38` | 63758 | yes |
| `silo\|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0` | `ddefb02013b61bbe` | `ddefb02013b61bbe` | 63974 | yes |
| `silo\|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=1` | `fe503236e45976ca` | `fe503236e45976ca` | 64014 | yes |
| `silo\|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` | `6454d9f34b04fdb1` | `6454d9f34b04fdb1` | 64070 | yes |
| `silo\|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=1` | `3790aa07e93ecb17` | `3790aa07e93ecb17` | 64110 | yes |

8/8 一致 (ALL_SAME)。`6454d9f34b04fdb1…` は §6.2 の計算ノード (g++ 11.4、template 適用木、旧版 / 新版) の stock pre-image
とも同値で、この pre-image は compiler 版 (11.4 / 12.3) にも依存していない (builtin を参照する枝が無いため)。
これは「指令を持たない source の pre-image は不変」の実測であり、`test_source_digest_stock_roundtrip` の緑
(token が `stock`) とは別の証拠である (段 6 レンズ B の B6-1)。

---

## 7. 実測 — source-level 変異 (計算ノード、runner = 新 8 node)

実走: 2026-09-17 JST 07:35〜08:00 (UTC 22:35〜23:00)、計算ノード、NQSV request 6 本 (collection 2791、baseline 2793、
S0 2804、S1 2819、S2 2865、S3 2869)。runner = `tools/run_tests.py orchestrator/tests/test_campaign.py -k "<8 node の名前>"
-q -rf --force-dispatch` (collect-only で 8/426 を確認)、repo = 変異 container `.codex/worktrees/t2731-mutcontainer`
(tip 2cc661235)、spec sha256 `b1fe1c12…`。台帳 `mutation-src-1.json`。

| 変異 | 置換 (一意) | 登録 | 台帳 | 失敗 node |
|---|---|---|---|---|
| baseline | — | PASSED | PASSED (8 passed) | — |
| S0 docstring 1 語 (対照) | `-dD で有効枝の …` の 1 行 | SURVIVED [] | SURVIVED | — |
| S1 `-dD` を外す | argv の `"-dD", ` | KILLED [A, B, F, H] | KILLED | A, B, F, H |
| S2 prefix 剥がしを外す | `return r.stdout.removeprefix(prefix)` → `return r.stdout` | KILLED [D, E] | KILLED | D, E |
| S3 `startswith` を恒真化 | `if not r.stdout.startswith(prefix):` → `if not True:` | KILLED [G] | KILLED | G |

MISMATCH 0、matching 4/4。S1 の 4 node が「指令の被覆」を、S2 の 2 node が「環境 prefix の分離 (inert = stock)」を、
S3 の 1 node が「fails-closed」を、それぞれ単独理由で検出する。

---

## 8. 限界 (書けないこと) と裁定候補

1. **include と指令の相対位置は識別しない** (段 3 レンズ A の A-1)。`#define X … / #include … / #undef X` と
   `#include … / #define X … / #undef X` は include 行列が同じで、include 除去後の `-dD` 出力も同じ。実 include では前者だけが
   header を書き換える。M4 / M4b は基準 template と区別できるようになったが、この 2 形同士は同 identity。修正前からの限界。
2. **`#pragma push_macro` / `pop_macro`** (A-2)。復元値は `-dD` に出ないため、保存時点が違う 2 形が同 identity になる
   (レンズ A の断片実測: `int later = SLEEP_READ_PHASE;` を末尾に足すと展開値が 0 / 1 に分かれる)。pin / template に
   この操作は無い。修正前からの限界。
3. **`_trace_pair_diff` の受理集合は不変ではない** (A-3)。比較式 `D_variant == D_stock` は不変だが、`#if TRACE` 内の
   未使用 `#define` / `#undef` も差分素材になり、HEAD に無いそれを template が足すと拒否される (狭まる向き、規律 2 と同方向)。
4. **compiler をまたぐ token の同一性は主張しない。** prefix は同じ `cxx` の空入力から取るので、compute / baseline の
   stock 判定は保たれるが、別 compiler では本文の空白・展開差が digest 差になりうる (D34 が受け入れた環境依存)。
5. **有限 matrix である。** 8 変異 + 4 変異 + 8 node。mocc、`#pragma`、computed 系の残存経路の不存在は言えない。
6. **`p3_s4_loop_trigger_gating.py` の pre-image artifact** は再利用時に bytes 一致を要求する (`:348`)。指令を持たない
   既存 proposal は一致するが、指令を含む proposal (現行の `HOLE_ESCAPE` が拒否する形) を同じ artifact path で
   再 materialize すると停止する。

裁定候補 (実装しない): 1 と 2 の解消は identity の設計変更 (相対位置の保存、macro stack の可視化、または TU 単位) を要し、
本裁定の scope 外。新 T として起票し、着手は裁定に委ねる。

**書いてよい:** 「登録済み M3b / M6 は stock と別 identity になった」「M4 / M4b を基準 template と区別した」「対象 stock /
template の token は維持された」「M6 は trace 差分検査を引き続き通過し nm 層が残る」「有限 matrix の期待署名が一致した」。
**書いてはいけない:** 「file 間のマクロ効果をすべて被覆した」「非再帰境界を全面的に閉じた」「include と指令の相対位置も
区別する」「全 compiler で token 不変」「mocc・pragma・computed 系に残存経路はない」「今回の probe が最終 binary の nm 拒否
まで確認した」。

---

## 9. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/` に全量を保全した。

| 場所 | 中身 |
|---|---|
| `evidence/bnode0NN-2026…-<pid>/` | recipe 再走の run ごとの証拠 (`observations.json`、`{reference,current}/{stock,variant}/token.txt`・`preimage.bin`・`owner.ii`・`*.diff.txt` 等)。EVIDENCE_ROOT は probe branch の commit c5affb156 で本 job dir へ向けた |
| `mutation-recipe-1.json` / `mutation-recipe-1-attempt-1.json` | recipe v2 の台帳と attempt 記録 |
| `mutation-src-1.json` / `mutation-src-1-attempt-1.json` | source-level 変異の台帳と attempt 記録 |
| `mutation-spec-src.json` (sha256 `b1fe1c12f7c5c18038b9f9f908d4bd22c2498691b9b9b13c0eeb3ac39f2c1f06`)、`recipe-spec-v2.json` (sha256 `17cc80de48526de8ebeaaf9ab05c1a53fbdb5324b3c33b9865b79e1cc22a46a3`) | 事前登録した spec |
| `s1-brief.md` / `verbatim-rulings.md` / `s2-plan-out.md` / `s3-a-out.md` / `s3-b-out.md` / `s4-ruling.md` / `s5-author-out.md` / `s6-a-out.md` / `s6-b-out.md` / `s6-fix-out.md` / `s6-probe-author-out.md` | 段 1〜6 の逐語 |
| `s5-focus-run.log` / `s5-focus-run-2.log` | 親の焦点走 (計算ノード dispatch: 2748.nqsv = `test_campaign.py -k "source_digest or trace_diff"` 38 passed 3 skipped / 第 2 組 835 passed 6 skipped)。compiler は test の `_any_cxx()` 選択 (計算ノードに g++-13 は無いので g++-12 か g++ 11.4、個別記録なし) |
| `preimage-oldnew-login-gpp12.log` / `preimage-oldnew.py` | §6.3 の実測 |

probe branch `probe-dev-wave-t2731-cpp-normalize-dd` (worktree `.codex/worktrees/t2731-probe`、tip c5affb156 = wave tip 2cc661235 +
T-2630 の probe test 2 commit の cherry-pick + EVIDENCE_ROOT 変更) は harness 用で **land しない**。probe test の逐語は
T-2630 の insight `verbatim/probe-test.md`、今回の差分は `verbatim/probe-evidence-root.diff.txt`。

本 dir の `verbatim/` に複製したもの: 段 1〜6 の逐語、両 spec、両台帳、attempt 記録、§6.3 の log と script。
逐語は可逆最小正規化を施していない (原文と byte 一致)。原文の sha256 は `verbatim/SHA256SUMS.txt`。

---

## 10. 親が踏んだこと

- 裁定文の前提 (`-dD` は predefined を含まない) は段 1 の前提実測 (DW-S01) で覆った。覆さずに素の `-dD` で実装していれば
  inert template ≠ stock になり、受入 suite (template 未適用) では検出されず、recipe 再走の baseline 赤で初めて気づく形だった
  ({{F:dd-predefined-assumption}} として failures へ)。
- 隔離 session では複合 shell と heredoc が guard に拒否されるので、job dir への file は Write tool で、他 worktree への git は
  `.sh` 経由で行った。`.codex/worktrees/` の新 worktree は `dev_wave_submodule_init.py` が 1 回目 rc=1 (update-no-fetch)、
  同じ引数の再実行で rc=0 (2 本とも)。
- 焦点走は login の headroom 判定で計算ノードへ dispatch された (§7.0.0)。
