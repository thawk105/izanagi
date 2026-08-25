# [T-1156] oracle 判定後の依存材料の再取得を禁止する — 逐語と実測

wave: `dev-wave-t1156-post-oracle-refetch-ban`
base main: `53c61414`
実装 commit: `03594501`

## 何を作ったか

床値 (floor) の `sort_best` cell について、SWO oracle が依存材料を判定した後に cell build の
cmake configure がその材料を取り直す経路を、事前拒否で塞いだ。既存の防壁は build 後の内容
再観測だけで、判定と使用の間に材料が入れ替わる窓が開いていた。

禁止の実体は 3 枚である。

1. `buildcache.build_v2` の新しい optional 引数 (post-oracle 材料束縛)。**引数の存在**が
   post-oracle capability であり、**引数の中身**が oracle receipt 由来の内容権威である。
2. 束縛があるときだけ configure argv へ `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を exact 1 本足す。
3. configure の前と、configure 後・`cmake --build` 前の 2 時点で材料を検査し、後者では
   `CMakeCache.txt` の実効値が exact `ON` であることも要求する。

材料検査は独自実装を持たず、oracle 自身の依存検証関数を呼ぶ。設計の正本は同 wave の
decisions fragment (fold 後に採番)。

## 本 wave で閉じていないもの (誇張しないための明示)

- **本 wave の主張は「再取得の禁止」までであり「材料変更の全面禁止」ではない。**
  `masstree_build` の custom command が source tree 内で `config.h` と archive を再生成する
  経路は残る。閉じるには書込み権威の変更が要り、D425 が別審査とした面に当たる。
- **禁止は production では現在 dormant である。** oracle の依存検証が要求する `SHA256SUMS` を
  production 側で生成・配置する経路が存在しない。**これは本 wave が作った欠陥ではなく
  変更前から存在する。** 本 wave の fail-closed 化により、この状態では build が安全側に
  止まる (誤った数値が通るのではない)。
- mimalloc と googletest の内容は build 境界へ束縛していない。cross-base cache hit の
  configure 記録は historical execution ではない。共有 base の process 間排他は無い。
  resume 経路は禁止前の durable manifest を受理し続ける。いずれも別項として起票した。

## 親が実測したこと (probe は repo 外の使い捨て driver、cmake 3.22.1 / login node)

CCBench と同形の 1 引数 `FetchContent_Populate(name)` を使った最小 driver で測った。

| # | 状況 | 結果 |
|---|---|---|
| 1 | 材料あり + `FULLY_DISCONNECTED=ON` | configure rc=0、source tree は無改変 (目印 file が生存)。禁止は効く |
| 2 | 材料を削除 + flag なし | 再 populate が発火し tree が置き換わった。**穴は実在する** |
| 3 | 材料を削除 + flag ON | **configure が rc=0 で成功し、source を再作成しない。** flag は「材料が無いこと」を咎めない |
| 4 | 材料あり + flag ON + ambient `CMAKE_TOOLCHAIN_FILE` が `set(... OFF CACHE BOOL "" FORCE)` | **実効値が `OFF` になり再 populate が実際に起きた。** `CMakeCache.txt` は実効値 `OFF` を正直に記録する |

3 と 4 が設計を決めた。**argv に禁止 token が 1 本あることは、禁止が発火した証拠にならない。**

適用範囲の断り: 本 probe は login node の cmake 3.22.1 で測った。実際に床値が走る計算ノードは
cmake 3.25.0 であり、login node に 3.25 は存在しないため測り直せていない。ただし本 wave の
設計は版に依存しない — fail-closed の権威を izanagi 側の検査に置いているため、cmake が
どちらの挙動でも結論は変わらない。

## 逐語

| file | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief |
| `verbatim/s1-brief-addendum.md` | 段 2 走行中に親が追加調査した追補 (A3-6 先例、oracle の private copy) |
| `verbatim/s2-plan.md` | 段 2 プラン (file:line) |
| `verbatim/s3-lens-correctness.md` | 段 3 敵対相談 (正しさ防壁) |
| `verbatim/s3-lens-scope.md` | 段 3 敵対相談 (受理集合と exact 述語) |
| `verbatim/s4-adjudication.md` | 段 4 裁定と変異事前登録 |
| `verbatim/s5-author.md` | 段 5 実装子の完了報告 |
| `verbatim/s6-parent-hypothesis.md` | 段 6 レビューへ渡した親の仮説 (攻撃対象として提示) |
| `verbatim/s6-review-liveness.md` | 段 6 敵対レビュー (恒真性と fail-open) |
| `verbatim/s6-review-regression.md` | 段 6 敵対レビュー (受理集合の回帰と検出力) |
| `verbatim/s6-fix1-ruling.md` | 段 6 fix 第 1 巡の親裁定 |
| `verbatim/s6-fix1.md` | 段 6 fix 子の完了報告 |

## 変異

| file | 中身 |
|---|---|
| `mutation-spec.json` | 本走の事前登録 spec (probe 観測 node を期待値として完全一致判定) |
| `mutation-ledger.json` | 本走の結果 |
| `mutation-probe.json` | probe 巡の結果 (全件 SURVIVED 期待で観測 node を集めた) |

本走: baseline PASSED (629 passed / 2 skipped)、**6/6 KILLED、SURVIVED 0、MISMATCH 0**。

| ID | 変異 | 期待 node 数 |
|---|---|---|
| M01 | capability 束縛時に flag を出さない | 6 |
| M02 | manifest 権威照合を外し HEAD と config だけにする | 1 |
| M03 | configure 後の実効値検査を外す | 1 |
| M04 | post-oracle 束縛時に identity policy を入れない | 1 |
| M05 | flag を無条件に付ける | 55 |
| M06 | configure 前の材料検査を外す | 2 |

M05 は 55 node を赤にする**過剰決定**であり、原因を 1 つに絞れない。「対象でない build へ
禁止を付けると広範囲が壊れる」ことの裏返しとして読み、単独変異の証拠からは外す。

M02 と M04 は段 6 の敵対レビューが「現行テストでは殺せない」と名指しした 2 件である。
fix 後はいずれも 1 件のテストが完全一致で殺しており、**指摘 → 修正 → 実測での裏取り**が閉じた。

## 検査

- 焦点走 (fix 後): `test_buildcache_v2.py` 172 passed、`test_s8b_floor_campaign.py`
  457 passed / 2 skipped。
- consumer 焦点走 (fix 前): 7 file で 872 passed / 9 skipped。
- AI provenance: 全 5995 commit で新規違反なし。
- 受入全走の結果は worklog に書く。
