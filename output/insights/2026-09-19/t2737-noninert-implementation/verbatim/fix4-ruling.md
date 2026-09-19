# fix4 裁定 (focus3 の NO-GO 所見、2026-09-19 22:20 JST)

## 所見 (real)
focus3 (`artifacts/dev-wave-t2737-noninert-codex/focus3.md`) の反例 escape.hh:
新規 file が `#ifndef X` / 値なし `#define X` / 末尾 `#endif` の形を満たしつつ、本文に `#if X + 0` を持つと、
fix3 の実装 (`test_ccbench_spawn_sites.py:676` で file の全追加行に除外 macro を割り当て、`:704` で全条件式から落とす)
は本文の `#if X + 0` からも X を落とす。外部供給値 (`-DX=1`) で本文が変わるのに X が登録候補から消える = 受理集合の逃がし道。
現行 `patches/` の実物では guard 3 個以外に差は無い (焦点走 180 passed と両立) が、防壁としては閉じていない。

## 採る修正 (fix4、Codex author 1 単位、所有は同じ 1 file)
- 除外の射程を **guard 自身の `#ifndef X` 行 1 行だけ** に限る。file の他の条件行 (`#if X`, `#if X + 0`, `#elif X`, `#ifdef X` 等)
  に現れる X は従来どおり候補として発見する。実装上は index→macro の割当てを file 全行でなく
  `start + first` (その `#ifndef X` 行) だけにする。(a)(b)(c) の判定条件自体は変えない。
- 受理の含意: 新規 file の include guard の `#ifndef X` 行だけは外部供給 interface の証拠として数えない。
- 拒否の含意: 同じ file の本文で X を条件に使えば X は候補に残り、`DEFINE_SPECS` に無ければ赤。
  既定値慣用句 (値付き `#define X 0`) と変更 file 内の guard も従来どおり候補に残る。
- 負例を 1 つ追加: focus3 の escape.hh (guard 形 + 本文 `#if X + 0`) で X が `patch_sources` に残ること。
  既存の正例 1・負例 2 は保持。fixture に揮発値を焼き込まない。
- 既存 test の期待値 (25/35/14/39 等) は不変。`DEFINE_SPECS`・patch・production は触らない。
- 規模: 追加変更 25 行以内。新しい仕組みを足さない。

## 期待される結果
- 実物 patch では guard 3 個は引き続き除外され (guard の `#ifndef` 行以外に X を使う条件が無い)、
  define 目録 3 test と unit test は緑のまま。escape.hh 型は候補に残る。
- 親は fix4 統合後に焦点走を再走し、変異 M7/M8 に「除外を file 全行へ広げる (fix3 の挙動)」M9 を足して負例 test が赤になることを裏取りする。
