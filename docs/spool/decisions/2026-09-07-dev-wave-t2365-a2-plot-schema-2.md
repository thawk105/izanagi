---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2365-a2-plot-schema
seq: 2
---

## {{D:a2-file-publish-hard-link-fallback}}. A-2 の file 公開は Lustre の EINVAL 時に create-only hard link へ退避する

**決定:** `_atomic_write_bytes_noreplace` が `renameat2` の no-replace フラグで `EINVAL` を受けたときだけ、
同一 directory 内の create-only な hard link による公開と staging の unlink へ退避する。
`EINVAL` 以外の errno は従来どおり送出する。退避後も宛先が既に在れば必ず失敗する。

**理由:**

- 計測領域も repo も Lustre であり、Lustre はこのフラグを実装せず `EINVAL` を返す。
  親が `stat -f` で両方 Lustre であることを実測し、attempt を実投入して 2 workload とも
  約 50 秒で `driver_rc=2` で落ちることを観測した。この経路は環境と混雑によらず決定的に落ちる。
- 親が Lustre 上で実測した結果、`ln` は成功し、既存名への `ln` は `EEXIST` で失敗する。
  したがって hard link は「既存なら失敗する不可分な公開」をこの FS で正確に満たす。
  受理集合を広げない。
- directory 公開側の既存退避を流用しない。あちらは directory が hard link できないため
  claim file で直列化しており、非協調 writer に対して不可分でないと docstring 自身が認めている。
  **file にはリンク方式の方が強い。**
- 変異試験で、退避を消す変異と「既存を置換する rename」へ変える変異の両方が KILLED になった。
  退避が恒真な保証になっていないことを実測で確かめている。

**却下した選択肢:**

- `flags=0` の rename へ退避する — 既存を黙って置換するため、no-replace の意味が失われる。
- directory 用の claim 方式を file にも流用する — 不可分性が落ちる。
- 族として一般化する — 同型欠陥は A-1 でも独立に再現しており `DW-G03` の条件は満たされているが、
  A-1 側は稼働中の別 wave の編集面であり、本 wave はユーザーが scope を明示的に絞っている。

## {{D:a2-figure-pin-table-repo-owned}}. A-2 図生成器の bytes pin は repo が所有し、呼び手は成果物を選ぶだけにする

**決定:** 図生成器の bytes pin を CLI 引数で受け取らない。certification の repo 相対 path を key に
した repo 所有の pin 表を引き、CLI が選べるのは「どの成果物か」だけとする。表に無い path は
fail-closed で拒否し、既定値へ落とさない。新しい attempt を図にするには repo へ entry を足す
commit を要する。

**理由:**

- 対象 file とその期待 hash を同じ呼び手が渡せる設計は、pin を「呼び手が言うとおり」を
  確かめる恒真判定へ落とす。凍結 certification の `status` を書き換えて自分で計算した hash を
  添えれば、偽の判定を載せた図を publish できる。段 3 の別系統レンズがこの具体例を示した。
- pin を repo 所有にすると、新しい成果物を図にする操作が査読を通る commit になる。
  これは凍結物の所定手続きと同じ形である。
- 変異試験で、pin 表を迂回する変異が KILLED になった。
- python の kwargs seam は test 専用として残すが、CLI からこの経路へ到達できないことを
  検査で押さえる。

**却下した選択肢:**

- CLI 引数で hash を渡す — 上記のとおり恒真化する。
- pin を省略可能にする — 未 pin の成果物から図を作れてしまう。
- 成果物自身が申告する hash を信じる — 権威が差し替え可能になる。

## {{D:a2-figure-number-derived-from-prefix}}. 図 caption の図番号は出力 prefix から導く

**決定:** A-2 図生成器の caption 先頭の図番号を、出力 prefix の basename `fig<N>_` から導く。
`fig<N>_` の形でない prefix は出力前に fail-closed で拒否し、出力を 1 file も残さない。
図番号を渡す CLI 引数は足さない。

**理由:**

- 決め打ちのままだと、新しい図が凍結済みの図と同じ番号を名乗る。論文素材に誤った相互参照が
  入るため、放置できない。
- 凍結図の prefix は `fig5_` なので導出結果は同じ文字列になり、**凍結図の caption は
  1 byte も変わらない。** 子が UTF-8 1788 bytes の完全一致を確認した。
- 引数で渡す形にすると、呼び手が任意の見出し文字列を caption へ注入できる。導出なら
  出力先の名前と caption が必ず一致する。

**却下した選択肢:**

- 図番号の CLI 引数を足す — 呼び手が caption へ任意文字列を注入できる。
- 新しい図の filename を `fig5` 系にする — 凍結図と衝突する。
- caption の番号を人手で直す — 生成器の決定的な組み立てと README 収録の一致検査が壊れる。
