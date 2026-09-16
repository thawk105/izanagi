---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2731-cpp-normalize-dd
seq: 1
---

## {{D:cpp-normalize-dd-env-prefix}}. `-dD` の predefined / command-line 出力は同じ argv の空入力 prefix として剥がす — 指令を持つ variant だけが別 identity になり、既存 identity は動かさない

**背景:** D2104 項 2 は F1016 (file 間へ漏れる `#define` / `#undef` を identity が見ない) の修正に (a) `_cpp_normalize` への
`-dD` を裁定した。裁定文と T-2630 insight §8 は「`-dD` は predefined を含まない」を前提にし「golden digest が動く」と
書いていたが、段 1 の前提実測 (login pegasus02、g++ 11.4.0 / g++-12 12.3.0) で **predefined (419〜437 行) と command-line
`-D` も `#define` 行として出力される**ことが分かった。template patch は CMake 供給に `BACKOFF_FIXED` / `BACKOFF_NOINLINE` を
足すので、素の `-dD` では `compute()` (working-tree 供給) の出力にだけそれらの `#define` が現れ `baseline()` (HEAD 供給) には
現れず、**inert template ≠ stock** になる (完了条件 1 の破壊。受入 suite は template を当てないので検出されない)。

**決定 (段 4、[T-2731]):**
1. `_cpp_normalize` は `-dD` を足したうえで、**同じ argv の空入力出力を環境 prefix として `removeprefix`** する。prefix は
   `(cxx, sorted defines)` ごとに module cache に取り、取得は同関数の再帰呼出し (`_environment_only=True`) で行って
   `subprocess.run` の call site を 1 箇所に保つ。実入力の出力が prefix で始まらなければ RuntimeError (fails-closed)。
2. EVOLVE_BLOCK_SOURCES 3 file (pin 511c953) と template に指令が無いため、**既存の stock / template variant の pre-image は
   byte 一致**する (実 submodule の silo 8 genome で旧版 / 新版 8/8 一致を実測)。identity が変わるのは指令を持つ variant だけで、
   記録済み測定の無効化・再認証は行わない (規律 7)。裁定文の「golden が動く」はこの実装形では起きない。
3. 再検証の発火条件は結果を見る前に登録した (M3b / M6 が 4 node 赤で別 identity、M0 は SURVIVED、baseline の variant token は
   T-2630 と同値)。実測は `output/insights/2026-09-17/t2731-cpp-normalize-dd/README.md` §6–§7。

**却下した実装形:** `-P` を外して linemarker で `<built-in>` / `<command-line>` を切る (正規化の意味が変わり、comment /
空行不感を別処理で再現する必要がある)。環境マクロ名で行 filter (source 自身の `#undef linux` や command-line と同名同値の
再 `#define` まで落とす)。

**受理集合の変化 (狭まる向き):** `_trace_pair_diff` (diff-of-diffs) の比較式 `D_variant == D_stock` は不変だが、`#if TRACE` 内の
未使用 `#define` / `#undef` も差分素材になるため、HEAD に無いそれを template が足すと拒否される。除外処理は足さない (規律 2)。

**残る限界 (scope 外、裁定パッケージ、実装しない):** (i) include 行を除去するため「指令と include の相対位置」は識別せず、
`#define X … / #include … / #undef X` と `#include … / #define X … / #undef X` は同 identity (前者だけが header を書き換える)。
(ii) `#pragma push_macro` / `pop_macro` の復元値は `-dD` に現れず、保存時点が違う 2 形が同 identity。いずれも修正前から同じで
pin / template にこの形は無い。解消は identity の設計変更 (相対位置の保存、macro stack の可視化、TU 単位 digest) を要するため
本裁定の scope 外とし、{{T:directive-position-and-macro-stack}} として起票する。選択肢は (α) 現状維持 + 限界明記、(β) include 行を
除去せず `-nostdinc` + `-MG` 等で include を dead 化して相対位置を保つ、(γ) TU 単位 digest (D2104 項 2 (c) の環境依存が再燃)。
親の推奨は (α) — pin / template に該当形は無く、coder 面は `HOLE_ESCAPE` が生指令を拒否するため実害の観測が無い。
