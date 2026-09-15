## 実測設計

**真偽の対照表と、実ガードの拒否結果を別々に採取して結合する。** 真偽差だけで欠陥とは判定せず、拒否が発火した範囲まで示す。本段では静的確認のみ実施した。

以下、`R` は指定 worktree、`S=R/external/ccbench`、`B` は probe 専用 configure directory とする。

**1. compiler と列の構成**

`g++`、`g++-9`、`g++-11`、`g++-12`、`g++-13` を requested name のまま列挙し、各 compiler について次の列を作る。同じ realpath でも requested name は残す。

| 列 | 再現する環境 |
|---|---|
| `checker-normalize` | `_cpp_normalize` の exact argv、stdin 入力 |
| `checker-dM` | `_dump_macros` の exact argv、stdin 入力 |
| `build-search` | 実 compile command から派生した preprocess argv、stdin 入力 |
| `build-header` | 同じ build flags・探索順を使い、header 内で式を評価する補助列 |

各列に hostname、cwd、compiler の探索結果・realpath・full version・実体 SHA-256、関連環境変数を記録する。`PATH`、`CPATH`、`CPLUS_INCLUDE_PATH`、`C_INCLUDE_PATH`、`GCC_EXEC_PREFIX`、`COMPILER_PATH` 等を勝手に消さない。checker は cwd/env を指定していないため、それらも再現条件である。

**2. checker の exact argv**

```text
[cxx, "-E", "-P", "-nostdinc", "-Werror=undef",
 "-std=c++20", "-O3", "-DNDEBUG",
 *sorted_define_arguments, "-x", "c++", "-"]
```

```text
[cxx, "-dM", "-E", "-nostdinc",
 "-std=c++20", "-O3", "-DNDEBUG",
 *sorted_define_arguments, "-x", "c++", "-"]
```

`sorted_define_arguments` は、キー順の `-D{k}={value}`。対象 genome を JSON に保存し、`_worktree_defines(S, genome, source_rel)` で実効定義を取得する。`source_rel` はまず `include/backoff.hh` とし、`TRACE=0/1`、`GLOBAL_VALUE_DEFINE` 未追加／`1` の組合せを明示する。異なる文脈は列 ID を分ける。

両経路とも stdin は実装と同じ `_INCLUDE_RE.sub("", source_text)` を適用する。主表の式には通常の `#include` を置かない。

**3. 実 build の compile command 取得**

第一選択は、対象 admission の configure 条件を引き継いだ `compile_commands.json`。今回の検索では `S` 配下に既存ファイルを発見できなかったため、取得済みとは扱わない。

段 5 の probe／親の実行手順は次とする。

1. 対象 genome、TRACE、toolchain、dependency prefix、FetchContent source/base directory、binary-path policy を採取する。
2. v2 なら `buildcache._v2_commands(...)` が返す configure argv を基に、専用 `B` と `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` を指定する。legacy なら同実装の configure 条件を使う。Makefiles／Ninja 系 generator を使い、選択を記録する。
3. configure は親側の既存実行規律に従う。依存物を取得できず configure が失敗した場合、その rc・診断を保存する。別の依存 prefix に無言で変更しない。
4. `ycsb_silo.exe` の `cc/silo/transaction.cc` の entry を選ぶ。compiler ごとに configure を分ける。ほかの compiler の entry から executable だけを交換したものは「実 compile command 取得」と呼ばない。
5. 元 command と `directory` を保存し、`-c`、元 source、`-o` と出力先、依存ファイル出力オプションを除き、`-E -P -x c++ -` を加える。`-I`、`-isystem`、`-iquote`、sysroot、`-D/-U`、警告・言語・最適化フラグと順序は保存する。response file があれば内容も保存する。

これは **生成された compile command の探索環境を測る列**であり、stdin に置き換えた時点で元 TU 全体の再現ではない。

configure 不可時は、後述の CMake 根拠から判明する探索 path を再構成して実測を続ける。ただし列を `build-search-reconstructed` とし、未解決の推移的 include、順序、暗黙 system path、生成 header の有無を記録する。**再構成だけを admission の実 build 実測と認定しない。**

**4. 行として測る式**

各行は独立 subprocess で測る。`H` は probe が作った存在確認済みの空 header の絶対パス、`M` は存在しない絶対パスとする。

| 行群 | 式／前置定義 |
|---|---|
| system | `__has_include(<vector>)`、`__has_include("vector")` |
| project・root 相対 | `__has_include(<include/tsc.hh>)`、`__has_include("include/tsc.hh")` |
| project・header 相対 | `__has_include(<tsc.hh>)`、`__has_include("tsc.hh")` |
| 正の対照 | `__has_include("H")`、`__has_include(<H>)` |
| 負の対照 | `__has_include("M")`、`__has_include(<M>)` |
| literal 間接形 | `#define IZ_H __has_include` → `IZ_H(<include/tsc.hh>)` |
| 関数形 | `#define IZ_H(x) __has_include(x)` → `IZ_H(<vector>)` |
| operand 間接形 | `#define IZ_HEADER <include/tsc.hh>` → `__has_include(IZ_HEADER)` |
| 貼り合わせ | `#define IZ_H __has_inc##lude` → `IZ_H("tsc.hh")` |
| next | `__has_include_next(<vector>)`、`__has_include_next("tsc.hh")`、`__has_include_next(<include/tsc.hh>)` |
| next 間接形 | `#define IZ_H __has_include_next` → `IZ_H(<vector>)` |

貼り合わせの既測式は比較用アンカーとし、それ単体を純増に数えない。

各 fixture は次の形にする。

```cpp
/* 行固有の前置定義 */
#if 式
#define IZ_T1643_RESULT 1
IZ_T1643_VALUE_1
#else
#define IZ_T1643_RESULT 0
IZ_T1643_VALUE_0
#endif
```

通常 preprocess は sentinel、`-dM` は `IZ_T1643_RESULT` の定義値を読む。`rc=0` かつ結果が一意な場合だけ正式な `value=0/1` を入れる。エラー時の部分 stdout は `observed_marker` として保存しても、正式な真偽にはしない。

`__has_include_next` は探索開始位置に依存するため、stdin の結果だけで header 内の挙動を結論しない。`build-header` では一時 fixture を `S/include/` に置き、一時 driver から、実コードと対応する相対 include 経路で取り込む。`cc/silo/include/transaction.hh` 相当の位置から `../../../include/<fixture>` を使う。実 build の探索 flags は追加・変更しない。

この補助列では `tsc.hh` の quote 探索と next の診断を観測する。fixture の include 経路を JSON に残し、完全な実 TU 実走とは区別する。実 build の `-Werror` によって next が失敗した場合もそのまま記録し、警告を消して成功値へ置き換えない。

**5. (P1-d) の実関数による確認**

各 compiler・文脈・式について、表とは別に次を直接呼ぶ。

```python
source_digest._assert_conditional_macros_covered(
    source_text, defines, cxx, "include/backoff.hh"
)
```

`_lex_normalize`、`_dump_macros`、`_environment_macros`、subprocess を stub にしない。compiler ごとに新しい Python process を使い、環境マクロ cache の共有による観測省略を避ける。

結果は少なくとも次に分類する。

- `reject_condition_operator`
- `reject_define_operator`
- `reject_token_paste`
- `other_error`
- `accepted`

例外型・全文・traceback の発生位置を保存する。compiler 起動失敗や別の未知マクロエラーを、目的の reject 発火に数えない。通常の `#if 1` と、`#define IZ_OK 1`／`#if IZ_OK` も呼び、常時例外を出す壊れた harness を検出する。

`_cpp_normalize` と `_dump_macros` も実関数として呼び、前者の出力／例外、後者のマクロ名集合／例外を記録する。生 subprocess の真偽表と突き合わせる。`_dump_macros` 自体は**値を返さず名前集合を返す**ため、真偽は raw `-dM` 出力から読む。

この実測は実ガード関数の発火確認である。`resolve`／`resolve_evidence` の全経路を実走したという主張はしない。その駆動配線は下記の静的根拠と合わせて示す。

**6. probe 配置と JSON schema**

配置先：

```text
/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1643-has-include-pair/tools/t1643_has_include_pair_probe.py
```

probe、fixture、configure directory は一時物とし、親が実行後に probe と raw JSON を指定 job directory へ退避する。repo に恒久 script・gate・台帳を追加しない。

JSON は次の構造とする。下表の型・列挙値を schema として実装する。

| field | 型・内容 |
|---|---|
| `schema_version` | integer、`1` |
| `run` | hostname、時刻、cwd、repo/CCBench commit、genome、関連 env |
| `compilers[]` | requested、found、realpath、version、sha256、探索／起動の結果 |
| `environments[]` | ID、compiler ID、kind、argv、cwd、defines、TRACE/context、探索 path、入力方式 |
| `build_provenance[]` | configure argv/rc/診断、compile entry、派生操作、`compile_commands`／`reconstructed`、未解決事項 |
| `cases[]` | ID、式、前置定義、source 全文と SHA-256、control 種別、header context |
| `cells[]` | case ID、environment ID、status、value、rc、stdout、stderr、diagnostic 有無、launch error |
| `guards[]` | case ID、compiler/context、実関数名、結果分類、例外型・本文・traceback |
| `controls[]` | 対照の期待値、観測値、成立／不成立 |
| `limitations[]` | compute 未測、再構成の限界、未取得 pair 等 |

`cells.status` は `measured`、`compiler_missing`、`launch_error`、`preprocess_error`、`parse_error`、`environment_unavailable`。`value` は `0 | 1 | null`、`rc` は `integer | null`。未測を `0` で埋めない。

## file:line の根拠

以下の path は `R` 相対。

| 根拠 | 確認内容 |
|---|---|
| `orchestrator/campaign/source_digest.py:370` | `BUILD_FLAGS` は `-std=c++20 -O3 -DNDEBUG` |
| `source_digest.py:1662`、`:1663`、`:1666` | include 除去、normalize argv、stdin 指定。cwd/env の上書きなし |
| `source_digest.py:1707`、`:1710`、`:1722` | `-dM` argv。`-P` と `-Werror=undef` はなく、返すのは名前集合 |
| `source_digest.py:1695`、`:2163` | 文脈 overlay、TRACE 両値の normalize |
| `source_digest.py:2071` | source 所有 protocol に応じた実効 defines の取得 |
| `source_digest.py:1842`、`:1845`、`:1851` | 字句正規化後、define の貼り合わせ／operator を拒否 |
| `source_digest.py:1858`、`:1861`、`:1866` | live `-dM` と環境照会、その後の条件指令 operator 拒否 |
| `source_digest.py:1895` | 公開 guard が対象 source ごとに実内部関数を呼ぶ |
| `source_digest.py:2408`、`:2447` | `resolve_evidence`／`resolve` が guard を駆動する |
| `orchestrator/campaign/buildcache.py:621`、`:1838` | 既定 gcc-13/g++-13、compute の場合だけ gcc/g++ |
| `buildcache.py:1174`、`:1287` | PATH 実体解決、expected manifest からの requested compiler 取得 |
| `buildcache.py:1935`、`:1965` | v2 の対象 target と configure argv |
| `buildcache.py:3190` | legacy configure argv |
| `orchestrator/campaign/pipeline.py:1789`、`:1805`、`:1944` | site 選択または manifest 選択を checker／build に渡す |

CMake の include path は次の経路で決まる。

| 根拠 | compile command へ伝わる内容 |
|---|---|
| `external/ccbench/cc/silo/CMakeLists.txt:1` | `ycsb_silo.exe` に `transaction.cc` を含める |
| `external/ccbench/cmake/ProtocolHelpers.cmake:36` | common、masstree、mimalloc の usage requirements を継承 |
| `external/ccbench/CMakeLists.txt:68` | common の PUBLIC include は **`S`**。`S/include` ではない |
| 同 `:71` | Threads、Boost、gflags、glog の requirements も PUBLIC に伝播 |
| `external/ccbench/cmake/ThirdParty.cmake:85` | masstree source root を INTERFACE include として伝播 |
| 同 `:112`、`:116` | mimalloc upstream target の requirements を継承。include path の詳細は upstream 側で決まる |
| `external/ccbench/cmake/Findgflags.cmake:18`、`Findglog.cmake:18` | 検出した include directory を imported target から伝播 |
| `external/ccbench/cmake/CompileOptions.cmake:1`、`:30` | C++20、extensions off、`-Wall -Wextra -Werror` |
| `external/ccbench/cc/silo/include/transaction.hh:9` | backoff を `../../../include/backoff.hh` で取り込む |
| `external/ccbench/include/backoff.hh:11` | header 内の `"tsc.hh"` は隣接 header の探索を伴う |

したがって、**`-I S/include` を便宜的に追加する再構成は不適切**。確定できる直接要素は `-I S` と masstree source root であり、推移的要素の順序・`-isystem` 化・暗黙 path の省略は生成 command で確認する必要がある。

## 恒真回避 (正の対照・負の対照)

- **checker の正の対照**：存在する空 header の絶対パスを quote／angle で照会する。`-nostdinc` でも明示 path の存在照会がどうなるかを実測し、期待値 `1` を検査する。
- **両側の負の対照**：一時 directory 内の確実に存在しない絶対 header path を照会し、期待値 `0` を検査する。
- **反転対照**：同じ path の空 header を作成した状態と除去した状態で同じ式を測り、`1→0` を確認する。両試行の存在状態を記録する。
- **抽出系の対照**：同じ parser に `#if 1`／`#if 0` を通す。sentinel の欠落・重複、空 stdout を成功にしない。
- **guard の対照**：安全な条件式が受理され、目的の式が該当拒否箇所へ到達したことを別々に確認する。

対照不成立時は raw 表を残し、「全偽」「真偽一致」といった結論を出さない。これは一時 probe の成立確認であり、恒久検査の新設ではない。

## 測れない pair の扱い

`g++-13` は各環境の列を残し、各セルを次のように記録する。

```json
{
  "status": "compiler_missing",
  "value": null,
  "rc": null,
  "diagnostic_present": false,
  "launch_error": {
    "kind": "FileNotFoundError",
    "errno": 2
  }
}
```

実際の探索結果と起動試行の例外を保存する。プロセスが開始していなければ rc を `127` と創作しない。表では `未測：compiler 不在（探索・起動試行済み）` と表示する。不在の実測記録と、式の真偽実測を区別する。

実在 compiler の全行は引き続き測る。`g++-9` 等で言語オプションや operator が通らなければ、その rc・診断を保存し、オプションを勝手に緩めない。

compute 未実行なら、compute の `g++`／`g++-13` は `environment_unavailable` と理由を残す。login `g++` の結果を admission compute 実測に読み替えない。(P1-a)〜(P1-c) を実測で確定するには、compute 上で同じ探索・version／hash 採取と probe が必要になる。

## 親 brief への反論

- **(P1-a)：条件の省略がある。** manifest 未指定の compute では読解どおり system `g++`。ただし `pipeline.py:1792`、`:1947` は expected manifest を優先するため、admission toolchain 全般を無条件に system `g++` と断定できない。今回対象の manifest 有無を記録する必要がある。
- **(P1-b)：同一性は未確認。** ソースから login／compute の実体一致は導けない。version 一致だけでも十分ではなく、実体と探索環境を比較する。
- **(P1-c)：現在の compute 不在は未確認。** 台帳の過去観測と、今回の compute 探索結果は別に扱う。
- **(P1-d)：実装の方向は一致するが、駆動点と拒否理由を限定すべき。** normalize 自体は blanket reject しない。実ガードが拒否し、resolver がそれを駆動する。また define の literal／貼り合わせは `-dM` より前に拒否される一方、条件指令の拒否より先に環境照会が走る。任意の例外を blanket reject 成功に数えてはならない。
- **(P1-e)：提示 argv は接頭部分にとどまる。** sorted `-D`、`-x c++ -`、stdin の include 除去、cwd/env が必要。受理ガードに関わる `-dM` 経路も欠けている。`BUILD_FLAGS` の現物は `:370`。
- **scope：恒久対応を除外する設定に反論はない。** ただし「login のみで実行」と「admission toolchain の実 pair 実測を完了」は、そのままでは両立しない。compute を測らない場合、成果物には admission 実測未完を明記する必要がある。

## 総括

設計は **exact checker argv、生成 build command 由来の探索環境、header 文脈の補助観測、実ガードの拒否確認**を分けて記録する。正負・反転対照で probe の不成立を検出し、不在 compiler も欠落させない。

本段で実装・書き込み・configure・compiler probe・pytest は実行していない。欠陥の有無と admission pair の結論は、親の実測結果に委ねる。