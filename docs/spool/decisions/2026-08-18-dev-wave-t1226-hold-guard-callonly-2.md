---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1226-hold-guard-callonly
seq: 2
---

## {{D:call-only-hold-guard}}. 恒久保留 guard の call-only は D360 の狭い例外とし、pytest 駆動の読み込みは拒否し続ける

**決定:** `enforce_held_functions` に `guard_mode="call-only"` を置き、module の読み込みを許して
held function の呼出だけを拒否する形を D360 の**狭い例外**として認める。既定は
`"import-and-call"` で、D360 の二層防壁のままとする。call-only でも次の 2 つは拒否を残す。

- 読み込みを駆動しているのが pytest である場合 (enforcement を持たない session の
  `--noconftest` / `--confcutdir` 経路)。判定は import 時の call stack に `_pytest` 由来の frame が
  あるかで行い、判定不能 (frame 取得不能) は拒否へ倒す。
- `__name__ == "__main__"` かつ plain runner が pytest へ委譲しない場合。

**理由:**
- 恒久保留は自己読込を持つ file へ掛けられなかった。呼出時 wrapper は既にあったが、末尾の
  一律 import 拒否が、同 file を `spec_from_file_location` や package import で読み直す
  正規 consumer を巻き込んで受入で差し戻された (F351)。
- D360 が読み込み時拒否を置いた理由は費用である。呼出時のみの拒否では `--noconftest` 経路が
  38.01 秒かけて実 repository 全走査を完走してから拒否していた (読み込み時なら 2.33 秒)。
  無条件に import を許すとこの層を失う。
- 一方、救うべき自己読込 consumer は素の `python -c` サブプロセスであり pytest を通らない。
  よって「pytest 駆動なら拒否」と狭めても、call-only が救う経路は 1 つも壊れない (実測)。
- 委譲先の無い直接実行を許すと、テストを 1 件も走らせずに rc=0 で終わる偽緑になる。

**残余 (閉じないと明示するもの):**
- call-only で読み込みを許した後、`__wrapped__` や `inspect.getclosurevars` 経由で原関数を
  取り出せば、解除 token 無しに本体へ到達できる。`@wraps` は保留関数のソースを
  `inspect.getsource(inspect.unwrap(...))` で読む既存 consumer が依存しており除去できない。
  D347 の `bypass_surface` が扱う既知迂回と同じ系列として記録し、閉じない。
  **call-only を実際に使う file を登録するときは、この迂回を `bypass_surface` へ書く。**
- pytest の test / plugin が別 thread から import する経路と、`__name__` を `_pytest.*` に
  偽装する経路は stack 判定で捕まらない。同じく既知迂回として記録する。

**却下した選択肢:**
- helper 閉包の切り出し — 依存が 8 個あり contained でない (ユーザー裁定で不採用)。
- `plain_runner` の literal を増やす — 同 literal は AST から導出した runner 種別との一致検査を
  持ち、保留防壁の強さという別軸と衝突する。
- call-only で import を無条件に許す — D360 の費用層を pytest 経路でも失う。

## {{D:hold-candidate-guard-binding}}. 恒久保留の候補選別に「guard binding を持てるか」を加える

**決定:** 成長比例テストを恒久保留する候補を選ぶとき、実行コストの比例だけで選ばない。
**その file に guard binding を置けるか**を選別条件に加え、契約テストで機械化する。

- 判定の母集合は登録済み held file だけとし、全 test file の走査や repo 成長に比例する検査を作らない。
- 自己読込の判定は、最終 loader path または module 名が当該 file と同一かで行う。
  loader API 名の出現や `__file__` の出現では発火させない (他 path を読むだけの file が
  偽陽性になる)。nested な subprocess source は二段 parse する。
  静的に解決できない loader は「自己読込なし」へ倒さず binding error とする。
- 自己読込を持つ file は `guard_mode="call-only"` の宣言を要求し、持たない file には
  同宣言を許さない (不要な import 緩和を作らないため)。
- call-only を宣言する file では、guard 呼出行より前の**import 時に評価される位置**に
  held function 名が名前としても文字列としても現れてはならない。canonical 名の wrapper が
  唯一の防壁になるためである。関数本体の参照は対象外とする (global 解決は呼出時に起き、
  guard 後に呼ばれる限り必ず wrapper を引く)。
- 比例コストが module の import 時副作用にある file は call-only の候補にしない。
  call-only は import を通すため、その費用を止められない。

**理由:**
- 選別を実行コストの比例だけで行った結果、自己読込を持つ file を保留登録してしまい、受入全走で
  帰属赤になって差し戻された (F351)。検出は受入 lease を 1 本消費した後だった。
- 静的検査へ前倒しすれば、同じ型の差し戻しを受入の手前で止められる。
- 別名退避を列挙して塞ぐ形は、動的な `globals()` lookup を取りこぼし、同時に安全な関数内参照を
  過剰拒否した。import 時評価という 1 本の基準へ寄せると両方が閉じる。

**却下した選択肢:**
- docs に選別条件を書くだけ — 謳うだけで発火しない保証になる。
- 全 test file を走査する検出器 — 母集合が repo 成長に比例し、開発するほどテストが遅くなる。
- 実 consumer file を毎回まるごと parse する回帰検査 — 同じ理由で却下し、固定サイズの
  synthetic 複製へ置き換えた。実データに対する保証は既存の held file 走査が担う。
