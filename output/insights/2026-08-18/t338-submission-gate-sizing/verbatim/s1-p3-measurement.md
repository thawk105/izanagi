# (P3) を決める親の実測 (2026-08-18 13:20 JST) — B1 は schema 不変で閉じる

`external/ccbench/cmake/Options.cmake:59-67` の関数 `ccbench_universal_definitions` は
`ADD_ANALYSIS=${CCBENCH_ADD_ANALYSIS}` と `TRACE=${CCBENCH_TRACE}` を
target_compile_definitions として吐く (同 file の逐語コメント
「Emit the universal flag list as `KEY=VALUE` items (suitable for target_compile_definitions)」)。
cache entry の定義は同 file `:14` (`CCBENCH_ADD_ANALYSIS`) と `:19` (`CCBENCH_TRACE`)。

よって CMakeCache の 2 値は、各翻訳単位の compile argv (`-DADD_ANALYSIS=0` / `-DTRACE=0`) として
`compile_commands.json` に必ず現れる。

凍結済み受領証 schema 側の実測:

- `compile_commands` は `fileRecord` (`path` / `size` / `sha256`) であり、
  `performanceCompileStock` / `performanceCompileMode` / `correctnessCompile` の `required` に入る。
  **validator が bytes を再読できる実体である。**
- `translation_units` は `translationUnits` (patternProperties で path をキーにする) で、
  各値は `translationUnit` = `normalized_argv` (string 配列) + `sha256`。
  §7.1(11) は「`translation_units` の key の POSIX 再正規化一致、`base_tree_sha` の再導出」を
  validator の責務としている。
- 一方 `cmake_cache` は `performanceCmakeCache` / `correctnessCmakeCache` =
  `{trace, add_analysis}` の 2 integer を enum (`[0]` / `[1]`) で pin した**申告値 object** であり、
  raw `CMakeCache.txt` の `fileRecord` は schema に存在しない (実測。0 件)。

## したがって §6.3 の 3 者一致は次で成立する

1. `configure_argv[]` 中の `-DCCBENCH_TRACE=` / `-DCCBENCH_ADD_ANALYSIS=` (受領証内の申告)
2. **`compile_commands` 実体の再読**から導いた各 TU の `-DTRACE=` / `-DADD_ANALYSIS=`、
   および `translation_units[*].normalized_argv` / `sha256` の再導出一致 (実体)
3. `cmake_cache` の申告値 — **不一致なら拒否するためだけ**に使う

受理の根拠は 2 にあり、§8 が禁じる「受理条件の入力」として 3 を使わない。
§6.3 本文自身が「1 つでも食い違えば拒否する」と拒否規則の形で書かれている。

## 帰結

**schema 変更も新 exact-byte approval payload (T-139 V1 の イ) も要らない。**
T-139 V1 の「イを作らずに B1 を閉じる案は (a) semantic validator を常時拒否 (受理集合が空) か
(b) §7.1(12) の CMakeCache leg を落とす (弱化) の 2 つしかない」という実証は、
**第 3 の経路 (CMakeCache 値を compile_commands の実体から再導出する) を見落としている。**
本実測でこれを反証する。段 4 でこれを採り、段 3 の 2 レンズに攻撃させる。

## この実測が外れる条件 (段 3 で確認させる)

- `compile_commands.json` に universal definitions が現れない build 経路が在る場合
  (例: 一部 target が `ccbench_universal_definitions` を呼ばない)。
- `CMakeCache.txt` の値と compile definition の値が乖離しうる場合
  (cache を編集した後に再 configure せずビルドする経路)。
  この乖離こそ `cmake_cache` 申告値を**拒否条件**として残す理由である。
