# 段 4 裁定 — [T-1156] oracle 判定後の材料再取得を禁止する

親が段 2 プランと段 3 敵対 2 レンズ (correctness / scope) の所見を real/refuted・採否・scope へ裁定し、
プラン v2 と変異事前登録を確定する。

## 0. 親が段 4 直前に追加実測した事実 (裁定の前提)

**実測 A (新規・決定的)。** 正しさレンズ所見 1 の攻撃を repo 外 probe で再現した。
`-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を argv に置いても、ambient な `CMAKE_TOOLCHAIN_FILE` が
`set(FETCHCONTENT_FULLY_DISCONNECTED OFF CACHE BOOL "" FORCE)` を実行すると:

- `CMakeCache.txt` の実効値は `FETCHCONTENT_FULLY_DISCONNECTED:BOOL=OFF` になる。
- **再 populate が実際に起きた** (削除した source tree が再作成された)。

すなわち **argv に flag が 1 本あることは禁止の発火を意味しない。** 一方、`CMakeCache.txt` は
実効値 `OFF` を正直に記録していたので、**実効値の照合はこの攻撃を検出できる。**

**実測 B。** `CMakeCache.txt` は正常時に `FETCHCONTENT_FULLY_DISCONNECTED:BOOL=ON` を記録する
(読み取り経路が実在する)。

**実測 C。** login node の cmake は `/usr/bin/cmake` の 3.22.1 のみ。3.25.0 は存在せず
(`/usr/share/cmake-*` は 3.22 のみ、module system なし)、login node では測り直せない。
**したがって scope レンズ所見 9 の「3.25 の `FetchContent.cmake` もローカルに存在する」は refuted。**

## 1. 所見の裁定

### real・採用 (本 wave で実装する)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | correctness 所見 1 | argv の flag は実効値を保証しない (ambient toolchain が FORCE で上書きできる) | **real・採用。** 実測 A で親が再現。configure 後・build 前に `CMakeCache.txt` の実効値を照合する |
| R2 | correctness 所見 7 | 「base 束縛 = post-oracle」の同値化は generic base-only 呼び出しを過剰拒否する (F325 型) | **real・採用。** flag と検査の発火条件を base の有無でなく **明示的な post-oracle capability 引数**にする |
| R3 | scope 所見 1 + correctness 所見 2 | 事前検査が oracle PASS の内容権威でなく oracle **前**の binding を見ている。HEAD と `config.h` だけでは tracked header の差替えを見逃す | **real・採用。** oracle receipt の `dependency_manifest_sha256` (= `SHA256SUMS` 全 file 権威) を build 境界まで持ち回り、事前検査の照合先にする |
| R4 | scope 所見 3 + correctness 所見 5 (前半) | (P4) は誤り。identity を変えないと旧 flag 無し entry を hit し、記録だけが flag 付きになる | **real・採用。** post-oracle build だけ identity preimage に population policy ID を入れる |
| R5 | scope 所見 4 | 「実行 argv と記録 argv の完全一致」テストは `-B` が staging と publish 先で必ず違うため常時赤 | **real・採用。** 完全一致テストは登録しない。正規化後の policy token 一致だけを検査する |
| R6 | scope 所見 7 | 負例 3 種のうち missing-source と archive mismatch は既存 gate と重複し純増でない | **real・採用。** 純増 vector (configure 前 config 不一致 / manifest 権威不一致 / flag 本数 / 実効値 / identity 分離 / 過剰拒否) だけを登録する |
| R7 | correctness 所見 8 | テストが production 定数を import すると綴り違いを共有して恒真化する | **real・採用。** flag token は test 側に literal で書く (独立 oracle) |

### real だが scope 外 (実装せず裁定パッケージへ返す)

| # | 出所 | 所見 | 理由 |
|---|---|---|---|
| X1 | 両レンズ (scope 所見 5 / correctness 所見 6) | `masstree_build` の custom command が source tree 内で `config.h` と archive を**再生成**しうる | **real。** これは fetch でなく書込みであり、D425 が「download / 書込み権威の変更は別審査」とした面そのもの。閉じるには依存 tree の書込み禁止か private snapshot build が要る。**本 wave は「再取得の禁止」であり「材料変更の全面禁止」ではない。残存経路として記録し、裁定へ返す** |
| X2 | correctness 所見 4 | mimalloc / googletest の内容が build 境界へ一度も束縛されていない | **real。** ただし本 wave が作った穴ではなく、flag はこれを悪化させない (欠落は安全側に拒否される)。別 wave |
| X3 | correctness 所見 5 (後半) | cross-base cache hit で記録 argv が historical execution を指さない | **real。** 既存テストが cross-base hit を明示的に許しており、変更は既存受理集合を狭める。R4 の policy ID とは別問題。別 wave |
| X4 | correctness 所見 3 | 共有 base を使う別 process の late prebuild を止める排他境界が無い | **real。** D424 は job 一意 `mkdtemp` base で排他が構造的に成立する設計を採っており、明示共有 base は別モード。process 間 lock は書込み権威の変更。別 wave |
| X5 | scope 所見 2 | resume 経路は `build_v2` を呼ばず、禁止前の durable manifest をそのまま受理する | **real。** 閉じると既存 floor manifest が一括で失効する migration になる。受理集合を大きく縮めるためユーザー裁定が要る |

### refuted

| # | 出所 | 所見 | 反証 |
|---|---|---|---|
| F1 | scope 所見 9 | 「CMake 3.22 と 3.25 の `FetchContent.cmake` がローカルに存在し静的に同形と確認できる」 | **refuted。** 実測 C — login node に 3.25 は存在しない。子は確認していない |
| F2 | 親 brief (P3) / scope 所見 8 / correctness 所見 3 の一部 | prebuild の oracle 後再入を拒否する gate を置く | **refuted (親自身の裁定を撤回)。** 現 call graph に late edge が無く、定数を渡す gate は恒真になる。実装しない。X4 として裁定へ返す |
| F3 | 親 brief (P5) の「別型だから無関係」という理由付け | 再生成経路は本 wave と無関係 | **理由付けは refuted。** X1 のとおり real な経路である。**scope 外という結論だけを維持し、理由を「別型だから」から「D425 が別審査とした書込み権威の変更だから」へ訂正する** |
| F4 | 親 brief 表 E | `_portable_argv` は exact 述語 consumer である | **refuted。** 位置・長さ・集合を固定しておらず、置換のみ。代わりに `_v2_commands` 自己検査と floor postflight の filtered exact 述語が該当する |
| F5 | 親 brief (P4) | cache identity は変えない | **refuted。** R4 のとおり |

## 2. プラン v2 (確定)

**中心となる設計変更: 発火条件と内容権威を 1 つの引数へ統合する。**

`buildcache.build_v2()` へ optional の post-oracle 材料束縛を 1 つ足す。この引数の**存在**が
post-oracle capability (R2) であり、その**中身**が oracle PASS 由来の内容権威 (R3) である。
base の有無を代理条件にしない。

実装は次の 5 点。file:line は段 2 プラン `## 実装プラン (file:line)` を土台とし、
下記の訂正を優先する。

1. **capability 引数の新設。** `build_v2()` に post-oracle 材料束縛を受け取る optional 引数を足す。
   束縛は最低限 (a) canonical な FetchContent base、(b) oracle receipt の
   `dependency_manifest_sha256`、(c) 期待 HEAD と `config.h` sha256、(d) 期待 archive sha256 を持つ。
   `s8b_floor_campaign.py` の `sort_best` 経路 (3979-4003 付近) が、`oracle_attempt` の receipt から
   この束縛を作って渡す。**oracle 前の binding だけから作ってはならない** (R3)。

2. **flag は capability 束縛時だけ付ける (R2)。** `_v2_commands()` で、post-oracle 束縛がある場合だけ
   `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を exact 1 本足す。無い場合は exact 0 本。
   `prepare_masstree_fetchcontent()` には足さない (oracle 前の populate 経路)。

3. **configure 前の材料検査 (R3)。** `_run(configure, ...)` の直前に fail-closed 検査を置く。
   照合先は oracle receipt の manifest 権威である。`SHA256SUMS` の sha256 が
   `dependency_manifest_sha256` と一致し、宣言された全 file が宣言どおりの sha256 を持ち、
   宣言外の regular file が無いことを要求する。HEAD と `config.h` と archive の一致も併せて要求する。

4. **configure 後・build 前の実効値検査 (R1)。** configure 成功後、`cmake --build` の前に
   `CMakeCache.txt` から `FETCHCONTENT_FULLY_DISCONNECTED` の実効値を読み、`ON` でなければ拒否する。
   同じ位置で 3 の材料検査をもう一度行い、configure 中に材料が変わっていないことを要求する。
   **これは D786 が採った「実効値を build 自身の成果物から読む」規律の同型適用である。**
   ambient な `CMAKE_TOOLCHAIN_FILE` を env から剥がす案は採らない — D425 が
   「実効値の照合がそれを包含する。環境変数の有無で受理集合を不必要に縮めない」と裁定済み。

5. **identity への policy ID (R4)。** post-oracle 束縛がある build だけ、`_v2_identity()` の preimage へ
   population policy ID を足す。束縛が無い build の preimage は 1 byte も変えない。

**既存の事後検知は 1 つも削らない・短絡しない・条件を緩めない。**
`buildcache.py` 1932-1939 / 2042-2053 / 2122-2151、`s8b_floor_campaign.py` 3379-3608 / 4048-4066。

### gate の署名 (受理と拒否を含意の向きで 2 文に分ける)

**受理:** post-oracle 束縛付きで `build_v2()` が binary を publish したなら、その binary を作った
configure は実効値 `ON` で走り、configure 前と build 前の両時点で、base 配下の masstree source は
oracle receipt が宣言した `SHA256SUMS` 権威・HEAD・`config.h`・archive とすべて一致していた。

**拒否:** 材料が oracle receipt の宣言と 1 file でも食い違う、`SHA256SUMS` が権威 hash と違う、
宣言外の file がある、または configure 後の実効値が `ON` でないなら、`cmake --build` より前に
`BuildCacheError` が raise され binary は publish されない。

**通る正例:** canonical base `B` の `B/masstree-src` が oracle receipt どおりの `SHA256SUMS`・
HEAD・`config.h`・archive を持ち、ambient に toolchain 上書きが無い floor `sort_best` build。
configure・build とも成功し、`configure_argv` に flag が exact 1 本入る。

**通る正例 2 (過剰拒否の検出用):** post-oracle 束縛を渡さない generic な base-only `build_v2` 呼び出しは、
flag 0 本で従来どおり configure でき、受理集合が縮まない。

## 3. 変異事前登録 (DW-M01)

各変異は、同じ入力を拒否する層が前後に無いこと (単一理由性) を確認して登録する。

| ID | 変異 | 期待 KILL 主体 | 単一理由性の確認 |
|---|---|---|---|
| M1 | capability 束縛時に flag を出さない | flag 本数テスト (束縛時 1 本 / 非束縛時 0 本) | 実効値検査は configure を実走しないテストでは発火しない。argv 生成層でのみ観測される |
| M2 | 事前・事後検査から `SHA256SUMS` 権威照合を外し HEAD + `config.h` だけにする | 「HEAD と `config.h` は不変のまま tracked header を書き換える」負例 | 既存層は HEAD / `config.h` / archive しか見ない (`buildcache.py` 2122-2151、floor postflight)。この vector を拒否する層は前後に無い |
| M3 | configure 後の実効値検査を外し argv の flag を信頼する | ambient 上書き負例 (`CMakeCache.txt` が `OFF`) | 実効値を読む層は他に無い。source root の実効値検査 (D786) は別 key を見る |
| M4 | post-oracle 束縛時に identity policy ID を入れない | identity 分離テスト (旧 entry を hit しないこと) | preimage を検査する層は `_v2_identity()` のみ |
| M5 | capability の有無を無視して flag を無条件に付ける | 過剰拒否の正例 2 + A1/A2 の exact argv 述語 | 非 base build の argv を固定する層は A1/A2 と `_v2_commands` 自己検査 |
| M6 | configure 前検査の raise を warning へ落とす | configure 前 config 不一致の負例 (`_run` 呼び出し数 0 を要求) | 既存層の config 照合は build **後**。configure 前に止める層は他に無い |

**変異 baseline は緑必須。** 登録は実装前に凍結し、段 6 で走らせる。

## 4. 恒真化しない根拠 (親の検算)

- M2 の vector は実測に基づく: oracle は `SHA256SUMS` で全 file を検証するのに、build 境界へ渡る
  `cache_receipt()` は HEAD と `config.h` しか運ばない (`s8b_sort_swo_receipt.py` 46-55 に
  `dependency_manifest_sha256` が実在することを親が確認済み)。権威は既にあり、運んでいないだけである。
- M3 の vector は実測 A そのものである。攻撃が成立し、かつ `CMakeCache.txt` が実効値 `OFF` を
  記録することを親が測った。検査は発火する。
- M6 の vector は `_run` の spy 呼び出し数で観測でき、「謳うだけ」にならない。

## 5. 成果物影響 (DW-G05)

実装しない場合、certified な床値の `sort_best` 数値が、oracle の判定した材料とは違う masstree で
作られた binary から出る経路が 2 本残る — configure による再 populate と、ambient 上書きによる
禁止の無効化である。床値は certified 選択の下限であるため、下限が別材料由来になると選択結果の
根拠が失われる。

**同時に、本 wave で閉じない残存経路 (X1) を記録へ明記する。** 本 wave の主張は
「oracle 判定後の**再取得**を禁止した」までであり、「材料変更を全面禁止した」ではない。
`masstree_build` の再生成は依然として oracle 判定済みの `config.h` と archive へ書きうる。

## 6. 実装子への境界

- 編集面は `orchestrator/campaign/buildcache.py`、`orchestrator/campaign/s8b_floor_campaign.py`、
  `orchestrator/tests/test_buildcache_v2.py` に限る。
- X1〜X5 は**実装しない**。
- 既存の事後検知を削らない・短絡しない・条件を緩めない。
- docs を編集しない。commit しない。
