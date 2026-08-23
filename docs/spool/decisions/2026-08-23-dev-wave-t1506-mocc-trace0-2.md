---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-t1506-mocc-trace0
seq: 2
---

## {{D:mocc-trace0-checker-wiring}}. TRACE=0 前処理同一性検査は source 所有 protocol の実供給 define と、比較対象 commit 由来の不在証明へ配線する

**決定:** `tools/check_trace0_preprocess_identity.py` は次の 2 点を満たす。

1. `_head_defines` へ `source_rel` を渡す。ただし `EVOLVE_BLOCK_SOURCE_PROTOCOLS` に
   登録済みの path のときだけで、未登録 path には `None` を渡して現行の genome protocol を
   維持する。登録済み path で owner 解決が失敗しても未登録扱いへフォールバックしない。
2. `_assert_conditional_macros_covered` へ `known_absent` を渡す。値は
   `_assert_proven_repo_absent_macros` を **old / new それぞれの commit について 1 回ずつ**
   呼んで得る。一方の結果を他方へ流用せず、和集合も共通部分も取らない。

`_repo_supply_files` には keyword-only の `commit` を足す。指定時は **作業 checkout の走査に
加えて** その commit tree も走査し、どちらかに供給源があれば停止する (現行より厳しい方向)。
`commit=None` の既存経路は挙動を変えない。

**理由:**
- mocc の `cc/mocc/CMakeLists.txt` は `RWLOCK` と `TEMPERATURE_RESET_OPT` を実際に供給する。
  mocc の source へ silo の定義表を当てていたため、これらが恒久的に未知マクロとなり、
  mocc の TRACE=0 検査は**構造的に一度も通らなかった**。実供給を digest 側にも入れるのは
  実ビルドの忠実な模写であって検査の緩和ではない。
- `MQLOCK` は `PROVEN_REPO_ABSENT_MACROS` に登録済みで、registry は使用時に再検証される。
  checker だけがこの registry へ繋がっていなかった。
- 切り分けの実測では、`source_rel` が `RWLOCK` と `TEMPERATURE_RESET_OPT` を、
  `known_absent` が `MQLOCK` を、それぞれ 1 対 1 で取り除く。片方だけでは閉じない。
  広く緩めているのではないことがこれで示される。
- checker は任意の 2 commit を比較する。作業 checkout で取った不在証明をその 2 commit へ
  流用すると、checkout には無いが比較対象 commit には供給源がある組を素通しできる。
  段 3 の敵対レンズが独立にこれを指摘した。

**却下した選択肢:**
- `CONTEXT_MACROS` へ `RWLOCK` / `TEMPERATURE_RESET_OPT` を登録する — これらは実 TU が
  無条件に供給するものであって両文脈を織る必要は無い。実供給表から引くのが正しい模写である。
- 全 diff path へ無条件に `source_rel` を渡す — `_source_protocol` が未登録 path で
  RuntimeError を投げるため、registry に無い C/C++ source の既存正例を壊す。
- commit tree 走査だけに切り替える — 作業 checkout は初期化済み submodule の中身も読むため、
  切り替えると走査対象が狭まる。加算にすることで従来以上の強さを保つ。

## {{D:mocc-trace0-gitlink-not-fatal}}. commit tree 走査は gitlink を停止条件にせず、証明できない限界を明記する

**決定:** commit tree 走査で `160000` (gitlink) entry に出会ったとき、submodule の中身が
走査で覆われていることを証明できなくても**停止しない**。coverage を確認できたときだけ確認し、
できないとき (未初期化、repository でない、HEAD が tree の OID と違う) は coverage を主張せずに
先へ進む。**submodule の中身が不在証明の対象外であるという限界は関数の docstring に明記する。**

submodule checkout の HEAD を解決する前に、**repository 境界を必ず確かめる**。
対象 directory 自身に `.git` marker が実在し (symlink は不可)、
`rev-parse --show-toplevel` の realpath がその directory と一致することを要求する。

`120000` (symlink) entry と、`160000` で object type が commit でない entry の
fail-closed は維持する。

**理由:**
- 未初期化の directory へ `git -C` を撃つと git は**親 repository まで遡って**解決する。
  submodule の HEAD のつもりで superproject の HEAD を得ていた。実測では
  `checkout='058d0c4e…'` (superproject の HEAD) が tree の `fb14e659…` と不一致になった。
- 計測 job は submodule を初期化せずに `git worktree add --detach` した tree を checker へ
  渡す。gitlink を停止条件にすると、その topology で checker が必ず rc=1 になり、
  **TRACE=0 の workload が毎回 skip される**。検査を強めた結果、計測経路を丸ごと塞いでいた。
- submodule の中身は本変更の前から、作業 checkout の走査が「初期化されていれば読む」だけで
  厳密な保証は無かった。証明できないことを理由に停止するのは、従来より強い要求を
  新たに課すことであり、過剰だった。黙って落とすのではなく限界として書くのが正しい。
- 段 6 の敵対レビュー 2 本が独立にこれを指摘し、親が実測で確認した。

**却下した選択肢:**
- gitlink で常に停止する — 計測経路が塞がる。実測で rc=1 を確認した。
- submodule の object store へ再帰して pin された OID の tree を走査する — nested submodule が
  未初期化のとき object が手元に無く、結局 fail-closed になる。同じ経路を塞ぐ。
- gitlink を黙って無視する — 限界を記録に残さないと、後から「覆っている」と誤読される。
