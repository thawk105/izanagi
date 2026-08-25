---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1156-post-oracle-refetch-ban
seq: 2
---

## {{D:post-oracle-refetch-ban}}. oracle 判定後の再取得禁止は明示 capability で表し、材料検査は oracle 自身の検証器を再利用する

**決定:** 床値の `sort_best` cell について、oracle 判定後の依存材料の再取得を禁止する。
禁止の発火条件と照合の権威を、`buildcache.build_v2` の新しい optional 引数
(post-oracle 材料束縛) 1 つへ統合する。**引数の存在**が post-oracle capability であり、
**引数の中身**が oracle receipt 由来の内容権威である。

- 束縛があるときだけ configure argv へ `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を exact 1 本足す。
  束縛が無い呼び出しの argv は 1 byte も変えない。
- 材料検査は独自実装を持たず、oracle が使う依存検証関数
  (`sort_swo_oracle._verify_dependency_root`) をそのまま呼ぶ。照合先は oracle receipt の
  `dependency_manifest_sha256` と `dependency_config_sha256`、および呼び手が渡した HEAD と
  archive sha256 である。
- 発火条件は fail-closed とする。dependency binding を持つ `sort_best` cell の build は、
  exact な `buildcache.build_v2` と束縛を伴うか、さもなくば build を 1 度も呼ばずに
  `FloorCampaignError` で拒否される。
- 束縛があるときだけ cache identity の preimage へ population policy を加える。

**理由:**

- **禁止の発火条件を「FetchContent base を渡したか」という構文条件にすると、oracle と無関係な
  base-only の呼び出しまで拒否する。** 3 依存のうち masstree だけが staged で他が未 populate の
  正当な呼び出しが、global な disconnected によって configure 不能になる。構文条件を意味条件
  (post-oracle である) と同値化する誤りであり、F325 と同型である。明示 capability にすれば
  この同値化が起きない。
- **照合先を oracle 前の binding にすると、oracle が判定した内容そのものを見ないことになる。**
  oracle は `SHA256SUMS` の全宣言 file を検証するが、build 境界へ渡る 2-key receipt は
  HEAD と `config.h` しか運ばない。tracked header だけを差し替えれば、HEAD と `config.h` と
  archive が同じまま build 側検査を通過する。oracle receipt の manifest 権威を運べば閉じる。
- **同じ規則を 2 箇所で実装すると、両方を通る入力が存在しなくなりうる。** 本 wave の初版は
  build 側に独自の inventory 規則を書き、`.git` を除外し未宣言 archive を特例受理した。
  oracle 側は `.git` を含み宣言集合と実在集合の exact 一致を要求する。この状態では
  「oracle を通る材料は build 側で拒否され、build 側を通る材料は oracle で拒否される」。
  同一関数を呼べば、「oracle が受理した直後の未変更の材料は build 側も必ず通る」が
  構造的に成立する。{{F:dual-rule-empty-intersection}}。
- **identity を変えないと、禁止前に作った binary を hit したうえで記録だけが禁止付きの
  configure を主張する。** cache hit の経路は保存済み argv を読まず現在の生成器から argv を
  再構成するため、依存 bytes が同じでも「禁止 policy を実行した」という provenance は同じでない。

**却下した選択肢:**

- **flag を全 build へ無条件に付ける** — A1 paired と A2 certification の configure argv
  exact 述語 (完全一致) を破壊する。実測でも 55 の test node が赤になる。
- **`CMAKE_TOOLCHAIN_FILE` を configure の環境から剥がす** — D425 が「実効値の照合が
  それを包含する。環境変数の有無で受理集合を不必要に縮めない」として却下済みである。
  本決定は同じ規律に従い、実効値照合で包含する ({{D:disconnected-effective-value}})。
- **build 側の inventory 規則から `.git` を除外したまま独自実装を残す** — oracle 側と
  食い違い、両方を通る入力が空になる。
- **capability の付与を builder の同一性で条件付ける** — 条件が偽になったとき拒否ではなく
  禁止そのものが黙って消える。fail-open であり、ユーザー裁定の fail-closed に反する。
- **prebuild の oracle 後再入を拒否する gate を置く** — 現行 call graph に late edge が無く、
  呼び手が定数を渡すだけの恒真な gate になる。実効的な排他は process 間 lock を要し、
  書込み権威の変更として別審査に属する。

## {{D:disconnected-effective-value}}. 再取得禁止の実効値は build 自身の成果物から読み、argv を証拠にしない

**決定:** post-oracle 束縛のある build では、configure 成功後・`cmake --build` 実行前に
`CMakeCache.txt` の `FETCHCONTENT_FULLY_DISCONNECTED` を読み、実効値が exact `ON` でなければ
拒否する。同じ位置で材料検査も再度行い、configure 中に材料が変わっていないことを要求する。
**argv に禁止 token が 1 本あることを、禁止が発火した証拠に数えない。**

**理由:**

- **実測で反証された。** `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を argv に置いても、ambient な
  `CMAKE_TOOLCHAIN_FILE` が `set(FETCHCONTENT_FULLY_DISCONNECTED OFF CACHE BOOL "" FORCE)` を
  実行すると実効値は `OFF` になり、**再 populate が実際に起きる**。
  `CMakeCache.txt` は実効値 `OFF` を正直に記録するため、実効値の照合はこの経路を検出できる。
  {{F:argv-token-is-not-effective-value}}。
- **flag 単独では fail-closed にならない。** 同じ実測で、source が不在でも
  `FETCHCONTENT_FULLY_DISCONNECTED=ON` の configure は rc=0 で成功し、source を再作成しない。
  「存在しない材料の上を素通りする」経路が残るため、izanagi 側の材料検査と対にして初めて
  fail-closed になる。
- **これは D786 と D425 が採った規律の同型適用である。** 実効 source root は
  「与えた入力」ではなく「build 自身が残した成果物」から読む、という形をそのまま
  禁止 flag へ適用した。新しい規律ではない。

**却下した選択肢:**

- **argv の token 数だけを検査する** — 恒真である。実測で反証された経路をそのまま通す。
- **build 後の内容再観測だけで足りるとする** — 検知であって禁止ではない。汚染された材料から
  binary を作ってから気づくことになり、`cmake --build` 前に止める本決定より受理集合が広い。
- **CMake の版を上げて flag の意味論を強くする** — 依存の版を計測環境ごと動かす変更であり、
  本 wave の scope 外。かつ実効値照合はどの版でも成立する。
