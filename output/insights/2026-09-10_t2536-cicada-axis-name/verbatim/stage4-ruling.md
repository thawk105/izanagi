# 段 4 裁定 — [T-2536]

親が段 3 の 2 レンズを real / refuted / scope で裁定し、plan v2 を確定する。

## 実測で切り分けた事実 (親が probe を走らせて得た)

probe は repo 外 (`probe_parser_limits.py`) に置いて実行した。対象は
`source_digest._parse_supplied_macro_details` の実挙動である。

| 入力 | 実測結果 |
|---|---|
| 素の CCBench 実体 | `INLINE_VERSION_OPT -> INLINE_VERSION_OPT_CICADA`、他は恒等 |
| 同じ左辺を別 RHS で 2 度供給 | `RuntimeError` で fails-closed (cache 名が衝突) |
| 2 軸が同じ cache 変数を読む | **通る** (両方が同じ cache 名へ写る) |
| `if(FALSE)` 内に旧 mapping を残す | **通る** (制御フローを解釈しない) |

さらに:
- `buildcache.cache_key()` の pre-image は `genome.canonical()|ccbench_commit|trace|src|toolchain|adm`
  で、configure argv を含まない。`derive_build_admission` の body にも argv は無い。
- `find output -name 'cicada_*'` は 0 件。canonical `cicada|` を含む tracked file は insight 逐語 1 本のみ。
- silo の genome は patch 供給の `BACKOFF_FIXED` / `BACKOFF_INCR_MILLI` / `BACKOFF_MAX_US` /
  `BACKOFF_UPDATE_US` を持ち、`test_campaign.py:11583` と
  `test_t2187_adaptive_const_probe.py:1448` が現行 argv を固定している。
- cicada の `cmake_defines()` を期待する既存テストは 0 件。

## 裁定表

| 所見 | 判定 | 採否 | 理由 |
|---|---|---|---|
| A-1 逆写像は D1864 の alias ではない | refuted | — | 親の (P1) を支持。旧汎用名は往復不一致で拒否される |
| A-2 / B-4 protocol 内 cache 名の単射性が未検査 | **real** | **採用** | 実測で parser は 2 軸→同一 cache 名を通す。新設する写像自身の性質なので scope 内 |
| A-3 軸集合が SPACES 由来で独立実体でない | real | 不採用 (scope 外) | 本 wave の主張は「宣言表が CCBench の cache 名と一致する」であって「軸集合が正しい」ではない。軸集合の独立 pin は SPACES の二重化になり、依頼の「仮想リスク向けの gate 追加は scope 外」に当たる。裁定パッケージへ |
| A-4 新 parser が重複左辺を拒否するか不明 | 判定不能 → refuted | — | 既存 parser は実測で fails-closed。**既存 parser を使う**ことで解決する |
| A-5 値取り違え検査が軸間 swap を捕えない | **real** | **採用** | 非対称な値の genome を使うだけで閉じる。安い |
| A-6 既存 4 拒否は維持される | refuted | — | — |
| A-7 compile command 層は検査対象外 | **real** | **採用 (主張の限定のみ)** | 検査は CMake source 上の cache 名契約に限る。compile command まで証明するのは別 wave。レンズ自身も scope 外と書いている |
| A-8 P3 の完了主張が強すぎる | **real** | **採用 (文言)** | 「認定の対象にできる」ではなく「前提を 1 つ除去した」と書く |
| A-9 P2 / P4 と高位 API 制約の認識は正しい | refuted | — | — |
| A-10 / B-10 他 3 protocol 恒等写像は親実測のみ | 判定不能 | — | 新設する drift 検査が 4 protocol 全部を毎回機械照合するので、本 wave 後は機械検証になる |
| B-1 build cache identity が写像を束縛しない | **real (機構)** | **不採用 (scope 外)** | 機構は正しい。しかし発火前提の cicada cache 項目は実測 0 件。将来の写像変更は CCBench 側なら `ccbench_commit` が key に入り、izanagi 側なら新設 drift 検査が赤にする。cache identity は全 protocol 共有の同一性コードで、依頼が除外した一般化に当たる。裁定パッケージへ |
| B-2 「cicada の live build 経路なし」は過剰一般化 | **real** | **採用 (親 brief の訂正)** | 専用 driver が無いだけで generic caller から到達可能。欠陥は現存する |
| B-3 test 側に新 parser を書くのは二重化 | **real** | **採用** | 既存 parser を使う。ただし `if(FALSE)` 非解釈は既存 parser の性質であり、本 wave では直さず限界として明記する |
| B-5 import 循環 | refuted | — | — |
| B-6 site 棚卸し | 判定不能 | 部分採用 | 親が実測で補った (下記 plan v2 の波及節) |
| B-7 source_digest 内の Genome 二義性 | **real** | **採用 (使い方の限定)** | 高位 API の実効値を oracle にしない。`macro -> cache 名` だけを使う |
| B-8 射影内既存テストへの波及なし | refuted | — | — |
| B-9 未射影テスト・golden | 判定不能 → 親が実測 | — | cicada の `cmake_defines()` 期待は 0 件 |

## plan v2 (確定)

1. `orchestrator/campaign/model.py` に静的表
   `GENOME_AXIS_CMAKE_CACHE_VARIABLES: Dict[tuple[str, str], str]` を literal で宣言する。
   4 protocol の `SPACES` 軸 17 本を網羅し、非恒等は cicada の `INLINE_VERSION_OPT` だけとする。
2. 同 module に `cmake_cache_variable_for_axis(protocol, axis)` と
   `genome_axis_from_cmake_cache_variable(protocol, cache_variable)` を置く。
   表に無い名前は恒等写像へ落とす (**この fallback は必須**。silo の patch 供給 define
   `BACKOFF_FIXED` 等の現行 argv を既存テストが固定している)。
3. **単射性**: 同一 protocol の表の値は一意でなければならない。重複があれば
   forward / inverse とも fails-closed で拒否する。逆引きで複数一致した場合も拒否する。
4. `Genome.cmake_defines()` を forward 関数経由にする。`canonical()` は変えない。
   `screening_driver.py:143,162` の局所組み立ても同じ forward 関数へ寄せる。
5. `orchestrator/calibrator/cli.py` の受領証復元は inverse 関数を通す。cicada の汎用名
   `-DCCBENCH_INLINE_VERSION_OPT=<v>` は `receipt-genome-invalid` で拒否する (alias にしない)。
6. drift 検査は `orchestrator/tests/test_pegasus_calibration_workload.py` に置き、
   **既存 parser `source_digest._parse_supplied_macro_details` を使って** CCBench 実体
   (`external/ccbench/cmake/Options.cmake` と `cc/<protocol>/CMakeLists.txt`) から表を作り、
   宣言表と exact 比較する。宣言表から CCBench 側の期待値を生成してはならない。
   負例は tmp 複製で CCBench 側 rename と izanagi 側 rename の両方向。submodule は編集しない。
7. 値の検査は**非対称な値の genome** (軸ごとに異なる値) で行い、軸間 swap を捕える。
8. 新規 test file を作らない (受入所要台帳の更新を発生させない)。

## scope 外 (実装しない・裁定パッケージへ返す)

- build cache identity への写像 fingerprint 追加 (B-1)。
- 意図軸集合の独立 pin (A-3)。
- emitted compile command 層までの証明 (A-7)。
- cicada を `certify_calibration.sh` / `submit_certify.sh` の受理集合へ入れること。
- `if(FALSE)` など CMake 制御フローを解釈する parser 強化 (B-3 の限界)。

## 完了主張の限定 (A-7 / A-8 を反映)

本 wave が主張してよいのは次だけである。

- 「genome 軸 → CMake cache 変数名の対応を CCBench 実体と一致させ、崩れたら落ちる検査を置いた」
- 「cicada を認定の対象にするための前提を 1 つ除去した」

主張してはならないもの: 「cicada を認定できるようになった」「コンパイラへ値が届くことを証明した」。

## 変異事前登録 (DW-M01、実装前)

実装後に anchor 逐語と期待 node を確定する (DW-M07)。位置と単一理由性は次のとおり。

| ID | 位置 | 変異 | 期待 KILLED の理由 |
|---|---|---|---|
| M1 | `model.py` 静的表 | cicada の `INLINE_VERSION_OPT` entry を削除し恒等へ落とす | drift 検査 (宣言表 vs CCBench 実体) と producer 値検査 |
| M2 | `model.py` inverse | 往復照合を外し汎用名を受理する | 受け手の汎用名拒否検査 |
| M3 | `model.py` 単射性検査 | 一意性の拒否を外す | 単射性検査 |
| M4 | `model.py` forward | cache 名は正しく値を別軸から取る | 非対称値の producer 検査 |
| M5 | 新 drift 検査 | CCBench 実体 parse を宣言表からの生成へ置換する (恒真化) | 両側 rename の負例 |

各変異は実装後に「同じ入力を拒否する層が前後にも内側にも無い」ことを確認する。確認できないものは
登録せず実効 gate へ再照準する。
