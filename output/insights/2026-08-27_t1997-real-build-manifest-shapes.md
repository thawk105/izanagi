# [T-1997] 実 CMake build が出す形での manifest 採取 — 実測

計算ノードでの実 build 正例を 1 回取り、`DependInfo.cmake` と `.o.d` の実形で採取が通るかを
実測した記録である。前 wave までは模擬 fixture でしか確かめられていなかった。

## 発見

**通った形と通らなかった形が 1 つずつある。**

1. **compiler input manifest の採取は実物で通る。**
   `orchestrator/campaign/s8b_compiler_input.py` の `collect_compiler_input_manifest` は、
   実 CMake `Unix Makefiles` が出す `flags.make` / `link.txt` / `*.o.d` をそのまま受理した。
   snapshot 外の入力を hash 記録だけに留める policy
   (`snapshot-and-external-hashes/v1`、D1136) を使った場合に限る。
   snapshot 内在籍を全入力へ要求する strict policy は、実物では
   `compiler input is outside the source snapshot` で必ず拒否される。これは D1136 が
   予告したとおりの挙動であり、欠陥ではない。

2. **masstree source root の解決は実物で通らない。**
   `orchestrator/campaign/buildcache.py` の `_masstree_source_root_from_cmake_cache` は、
   実 CMake が出す `CMakeCache.txt` を
   `CMakeCache.txt の FETCHCONTENT_SOURCE_DIR_MASSTREE が NUL なし絶対 path でない`
   で拒否した。原因は次の 1 点である。

   - CCBench の `cmake/ThirdParty.cmake` は `FetchContent_Declare(masstree ...)` を使う。
     CMake は宣言の時点で `FETCHCONTENT_SOURCE_DIR_MASSTREE` を**空値の cache PATH entry**
     として必ず作る。したがって実 `CMakeCache.txt` には
     `FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=` の行が**常に 1 行在る**。
   - 実装は「当該行が在ること」だけを「SOURCE_DIR が指定されている」の条件にしていた。
     値が空なので直後の絶対 path 検査で必ず落ちる。
   - `<FETCHCONTENT_BASE_DIR>/masstree-src` を使う base-only 分岐は、
     「当該行が無い」ときだけ到達する。実物ではその状態が起きないので、
     この分岐は**実質的に到達不能**だった。
   - `transport_mode` の既定値は `base-only` である
     (`orchestrator/campaign/s8b_floor_campaign.py`)。したがって既定 regime の全 cell が
     build 段で拒否される。

   既存テストは `FETCHCONTENT_SOURCE_DIR_MASSTREE` の行が**無い** cache を base-only の
   正例としており、実 CMake が作らない形でだけ base-only を通していた。さらに
   `test_masstree_source_root_invalid_source_does_not_fallback` の `empty` parametrize は、
   実 CMake が必ず作る形を**拒否として固定**していた。模擬が実物と逆向きに固まっていた例である。

## 再現条件

| 項目 | 値 |
|---|---|
| 実行場所 | Pegasus 計算ノード `bnode009` (queue `gen_S`、job `951893.nqsv`)、48 core、他 user process なし |
| 日時 | 2026-08-27T10:10:47+09:00 開始、10:11:01 終了 |
| CMake | 3.25.0 (`/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/cmake`) |
| compiler | g++ 11.4.0 |
| CCBench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| generator | `Unix Makefiles` |
| target | `ycsb_silo.exe` |
| FetchContent | base-only (`-DFETCHCONTENT_SOURCE_DIR_*` を渡さない) + `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` |
| build dir | source snapshot の**外側** |
| configure / build | 両方 rc=0、`ycsb_silo.exe` 生成成功 |

ログインノード (CMake 3.22.1) でも configure だけを別途実施し、同じ cache 形と同じ拒否を確認した。
**版が違っても (3.22.1 / 3.25.0) 空値 cache entry の形は同じである。**

## 実測した逐語形

`CMakeCache.txt` の該当 3 行 (`FETCHCONTENT_SOURCE_DIR_MASSTREE` の出現行数は 1):

```
CMAKE_GENERATOR:INTERNAL=Unix Makefiles
FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=
FETCHCONTENT_BASE_DIR:PATH=<base>
```

`CMakeFiles/masstree_build.dir/DependInfo.cmake`:

```
set(CMAKE_MULTIPLE_OUTPUT_PAIRS
  "<base>/masstree-src/config.h" "<base>/masstree-src/libkohler_masstree_json.a"
  )
```

target dir (`cc/silo/CMakeFiles/ycsb_silo.exe.dir/`) の実在 file:

```
DependInfo.cmake  build.make  cmake_clean.cmake  compiler_depend.make
compiler_depend.ts  depend.make  flags.make  link.txt  progress.make
transaction.cc.o  transaction.cc.o.d  util.cc.o  util.cc.o.d
ycsb_silo.cc.o  ycsb_silo.cc.o.d
```

`flags.make` は「2 行の `#` header + 空行 + `# compile CXX with <絶対 path>` +
`CXX_DEFINES` / `CXX_INCLUDES` / `CXX_FLAGS` の 3 代入」形。
`link.txt` は 1 行で、object は target dir 相対、出力は `-o ycsb_silo.exe` の相対名、
`-Wl,-rpath,<絶対 path>` を含み `$` を含まない。
`*.o.d` は target が **build root 相対**、入力はすべて**絶対 path**、行末 `\` 継続、
`../` を含む非正規化 path を含む。

## 採取結果の数値

| 項目 | 値 |
|---|---|
| `depfile_count` | 3 |
| 入力総数 | 588 |
| snapshot 相対入力 | 39 |
| 絶対 path 入力 | 549 |
| `manifest_sha256` | `990abdffb2212d60f70acac19bcc79d5a6695de4d3a48ea44ba9ea5b68cac281` |

絶対 path 入力の帰属分類:

| 置き場 | 件数 |
|---|---|
| build dir (使い捨て staging に相当) | **0** |
| FetchContent base | 31 |
| 外部依存 prefix | 7 |
| `/usr/include` と `/usr/lib/gcc` | 511 |

**build dir 配下の入力は 0 件**だった。したがって「staging を破棄した後に receipt 再検証が
`external compiler input is unavailable` で落ちる」という懸念は、この regime では発火しない。
ただし根拠は測定 1 例であり、build 生成 header が include path に載る別 regime は排除していない。

## 該当コード

- `orchestrator/campaign/buildcache.py` の `_masstree_source_root_from_cmake_cache`
  (空値 cache entry を「指定あり」と判定する分岐)
- `orchestrator/tests/test_buildcache_v2.py` の
  `test_masstree_source_root_accepts_base_only_shape` (行が無い模擬)、
  `test_masstree_source_root_invalid_source_does_not_fallback` の `empty` parametrize
  (実形を拒否として固定)
- `external/ccbench/cmake/ThirdParty.cmake` の `FetchContent_Declare(masstree ...)`
  (空 cache entry の発生源。CCBench 側は改変しない)

## 仮説

模擬 fixture は「実装がこう読む」という理解から書かれており、「CMake が実際に何を書くか」から
書かれていなかった。`FetchContent_Declare` が宣言の副作用として空 cache entry を作ることは
CMake の仕様だが、fixture の作者はそれを再現していない。結果として、実物では起きない形
(行が無い) を正例に、実物では必ず起きる形 (空値行) を負例に据えた。
D786 の本文は「`FETCHCONTENT_SOURCE_DIR_MASSTREE`、無ければ `<FETCHCONTENT_BASE_DIR>/masstree-src`」
と書いており、規範としては空値を「無い」と読むのが自然である。実装がその読みを取らなかった。

## 副次の発見 — snapshot を `git archive` で作ってはならない

CCBench の `.gitattributes` は `oze* export-ignore` を持つ。`git archive HEAD` は
`cc/oze/` を丸ごと落とすため、root `CMakeLists.txt` の `add_subdirectory(cc/oze)` が
`not an existing directory` で configure を止める。本 wave の実 build 準備で実測した。
production の build 経路は実 checkout をそのまま source root に使う (`sub = ccbench_dir`) ため
この罠を踏まない。`orchestrator/campaign/s6_canary_rename.py` は
`git archive HEAD <PATCHED_FILES>` を使うが、対象 2 file は `oze*` に当たらないため現時点で実害はない。

## CCBench 論文 / insight との関係

CCBench 側の欠陥ではない。CCBench は CMake の標準的な `FetchContent` 利用をしているだけで、
食い違っているのは izanagi 側の cache 読み取りである。上流への還元事項はない。

## 還元判断

CCBench への還元は不要。izanagi 側の是正で閉じる。
