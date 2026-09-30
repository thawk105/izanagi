---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-cicada-promotion-uaf-fix
seq: 2
---

## {{D:cicada-promotion-uaf-fix}}. Cicada の promotion・insert・abort の欠陥は、読み取り専用 tx の promotion をやめ、promotion の書き込みに後続の update を移し、inline 有効時の insert で渡された版を使い、abort の解放を writeSetClean の後へ回して直す。受理集合を変える直し方は採らず、G と gc 修理の merge を土台にした CCBench の local branch に 1 修理 1 commit で置く

**決定:**
1. 巡回の原因 (単位 D の診断で帰属、修理前の代表 witness 52 件の全部が該当): 読み取り専用 tx は rts で可視版を選び `later_ver_` を rts 基準で記録する。promotion がこの tx を読み書き tx に転換すると、validation の読み取り再検査は `later_ver_` から wts 未満まで下り、`later_ver_` が aborted でその手前に rts と wts の間の確定版が入るとそれを飛ばして古い読みを通す。修理 1 = 読み取り専用 tx では promotion しない (`inlineVersionPromotion` の条件に `!is_ronly_`)。読み書き tx の promotion は残す。
2. 修理 2 = promotion が積んだ書き込み要素にだけ目印を付け (要素が 1 つ増え tx が aborted でないときだけ)、同じ tx の後続 `update()` の body をその要素の新版へ移す。promotion 以外の二重 update (stock の素通り) は変えない。目印と分岐は INLINE_VERSION_OPT ∧ INLINE_VERSION_PROMOTION の内側だけ。
3. 修理 4 (TPC-C の `std::bad_alloc` の原因、一要因対照で帰属): INLINE_VERSION_OPT=1 の `Tuple::init(…, ver, …)` が渡された版を latest にし body をそこから取る (OPT=0 の分岐と同じ意味)。新しい Tuple の inline 版を insert で使えるようにする変更はしない。
4. 修理 3 = abort は INSERT の tuple を退避 → 索引から外す → `writeSetClean()` → 解放。`writeSetClean()` は変えない。既定 genome の abort 本文が変わる (意図した差分)。
5. 置き場: CCBench の local branch `izanagi-cicada-promotion-uaf-fix`。土台は `izanagi-cicada-build-fix` と `izanagi-cicada-gc-records-fix` の merge commit (コードの追加なし) で、両 branch の SHA を保つ。これは local 検証土台であって D2305 項 6 の「束ねた pin tip」ではない。修理は 1 修理 1 commit (D2305 項 10)。out-of-tree の修理 patch は作らない。正例は `patches/broken-cicada-promotion-ronly-stale-recheck.patch` (修理 1 の条件だけを外す無条件 patch、ledger.json には登録しない)。
6. D297: 検査器は修理後 tip を cicada の未知 macro で fails-closed に拒否する (pass と呼ばない)。修理後 tip の `cc/cicada` だけを pin C の tree に戻した probe で pin C → probe を判定し pass を得て、非 cicada の bytes の同一性を取り直した。検査器・受理条件は変えていない。

**理由:**
- 原論文 §3.1 は読み取り専用 tx を rts の snapshot で読み読み取り集合を検証しないと定め、§3.3 の promotion は「可視版として読んだ版の読みを RMW へ格上げ」で、rts で読む tx の格上げは書いていない。修理 1 は論文の規則に戻す最小の変更で、読み書き tx の promotion (`later_ver_` が wts 基準) にはこの穴が無い。
- 修理 2 は版の trace と判定器では見えない値の欠落で、TPC-C の注文 insert 失敗を promotion 無効の約 16〜22 倍にしていた (修理後は同水準)。比較相手の作業量そのものを変えるので直す。
- 修理 4 は promotion ではなく INLINE_VERSION_OPT=1 の insert の欠陥で、promotion 無効の OPT=1 genome でも TPC-C が落ちる。promotion の 8 genome を使うには必須。
- どの修理も validation・precheck・commit・install の判定式を変えないので、受理集合を緩めない (規律 2)。

**却下した選択肢:**
- 読み取り専用から転換した tx の読みを最新版から再検査する — 論文にない転換を残したまま検査を足す形で、変更と証明範囲が広い。修理 1 で巡回が消えたので採らない。
- 後続 update の素通りを一律にやめる (二重 update すべてで body を移す) — stock の既定の挙動を変える。
- `writeSetClean()` で INSERT 要素を飛ばす — install 済み版の status を pending のまま残す。
- abort した insert の tuple の遅延解放 — 並行の読み手の寿命を塞げるが epoch 相当の設計で最小修理を超える。新 item にした。
- G か gc 修理の一方の上に積む、2 本を cherry-pick する — 一方の修理が欠けるか、同じ内容の別 SHA を作る。
