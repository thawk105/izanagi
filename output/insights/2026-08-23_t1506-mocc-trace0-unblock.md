# [T-1506] mocc の TRACE=0 前処理同一性検査を通るまで — 塞いでいたのは 1 箇所ではなく 3 箇所だった

- 日付: 2026-08-23
- wave: dev-wave-t1506-mocc-trace0 (branch `worktree-dev-wave-t1506-mocc-trace0`)
- 起点の裁定: D673 (ccbench 側の trace 用 include 行の修正は AI が行ってよい)
- 成果物 commit: ccbench `058d0c4e5f237d88ec1c2ebe0739113d82906e47`、
  izanagi `caad852d84ea304838502ad41338835fc82e8064` と
  `be3977577d0aba95997fdaca6d9708e6d74acfbf`

## 1. 何が塞いでいたか

D673 は「trace ヘッダの include 行に残った旧版コメントが残る限り、TRACE=0 の性能計測が
前処理同一性の検査に弾かれて一度も走らない」と述べていた。**この主張は正しかったが、
必要条件であって十分条件ではなかった。** 実測すると、塞いでいた箇所は 3 つあった。

### 壁 1 — include 行の末尾コメント (D673 が指していたもの)

`external/ccbench` の commit `ef9328a3` (ユーザーが 2026-08-21 に適用) の
`cc/mocc/transaction.cc:14` は次だった。

```cpp
#include "../../include/trace.hh" // izanagi: #if TRACE-guarded correctness trace
```

`tools/check_trace0_preprocess_identity.py` の `_mocc_trace_include_addition_index` は
include 行の `line.strip()` が `_MOCC_TRACE_INCLUDE_LINE` (`#include "../../include/trace.hh"`、
コメント無し) と完全一致することを要求し、`source_digest._INCLUDE_RE`
(`(?m)^[ \t]*#[ \t]*include\b.*$`) は行末コメントごとマッチする。よって不一致になる。

実測 (wave 開始時):

```
error: … include 行文字列（順序込み）が不一致: cc/mocc/transaction.cc
```

前 wave (`dev-wave-t755-q2-mocc-trace`) の段 6 が確定させた修正形は**コメントの削除ではなく、
include 行の直前の独立行への移動**である。本 wave はその逐語をそのまま適用した。

### 壁 2 — checker が mocc の source に silo の定義表を当てていた

壁 1 を直した使い捨て commit で checker を回すと、拒否は解消せず**別の gate へ移った**。

```
source_digest: cc/mocc/transaction.cc の条件指令が未知マクロ
['MQLOCK', 'RWLOCK', 'TEMPERATURE_RESET_OPT'] を参照 … fails-closed で停止 (T-148)
```

原因は checker 側の配線漏れだった。

- `_head_defines(sub, genome, oid, source_rel)` は `source_rel` を渡せば
  `EVOLVE_BLOCK_SOURCE_PROTOCOLS["cc/mocc/transaction.cc"] = "mocc"` の owner protocol 経由で
  `cc/mocc/CMakeLists.txt` の実供給 (`RWLOCK`、`TEMPERATURE_RESET_OPT`) を定義集合に入れる。
  checker はこれを渡していなかった。
- `PROVEN_REPO_ABSENT_MACROS = {"MQLOCK"}` は既に存在し、公開 wrapper
  `assert_conditional_macros_covered` は `known_absent` として渡している。checker は渡していなかった。

つまり **正しい経路は既に `source_digest` 側にあり、checker だけが繋がっていなかった。**

切り分けの実測 (job dir の `probe-wiring.py`、SILO_SPACE の 8 genome x 2 commit):

| `source_rel` | `known_absent` | 結果 |
|---|---|---|
| 無 | 無 | `['MQLOCK', 'RWLOCK', 'TEMPERATURE_RESET_OPT']` で拒否 (現状) |
| 無 | 有 | `['RWLOCK', 'TEMPERATURE_RESET_OPT']` で拒否 |
| 有 | 無 | `['MQLOCK']` で拒否 |
| 有 | 有 | OK |

取り除かれる macro が 1 対 1 で対応する。片方だけでは閉じず、両方が要る。
**広く緩めたのではなく、それぞれの macro を正しい供給元から埋めている**ことがこれで示される。

### 壁 3 — 強めた検査が計測 job の実経路を塞いだ (本 wave 自身が作った壁)

段 3 の敵対相談が「checkout だけで取った不在証明を任意の 2 commit へ流用するのは不健全」と
指摘したため、走査元を commit tree へ広げた。その際 gitlink (submodule) の扱いを
「checkout の HEAD と OID が一致するときだけ通し、一致しなければ停止」とした。

段 6 の敵対レビュー 2 本が独立に、これが計測 job を塞ぐと指摘した。親が実測で確認した。

`tools/pegasus/mocc_trace_pilot.sh:602-604` は **submodule を初期化せずに**
`git worktree add --detach` した tree を checker へ渡す。その形を再現すると:

```
error: … source_digest: commit tree と checkout の gitlink OID が不一致:
path='third_party/shirakami' tree='fb14e6597ecf7cc206af8f3424ca22503bb1e17d'
checkout='058d0c4e5f237d88ec1c2ebe0739113d82906e47' …
```

`checkout=` の値は submodule の HEAD ではなく **superproject の HEAD** である。
未初期化の directory へ `git -C` を撃つと git は親 repository まで遡って解決する。

直し方は 2 つある。

1. repository 境界 (`.git` marker の実在と `rev-parse --show-toplevel` の realpath 一致) を
   先に確かめてからでなければ `git -C` を撃たない。
2. gitlink の coverage を証明できないときに**停止しない**。submodule の中身は本変更の前から
   checkout 走査が「初期化されていれば読む」だけで厳密な保証は元々無い。証明できないことを
   理由に停止すると計測経路が丸ごと塞がる。coverage を確認できたときだけ確認し、
   できないときは coverage を主張せずに進む。**この限界は関数の docstring に明記した。**

## 2. 最終状態の実測

| 実測 | 結果 |
|---|---|
| 実 checker (通常経路、`--repo external/ccbench`) | rc=0、`result=pass` |
| 実 checker (計測 job と同じ topology、submodule 未初期化の detached worktree) | rc=0 (fix 前は rc=1) |
| `test_check_trace0_preprocess_identity.py` + `test_mocc_trace_job_contract.py` | rc=0、58 passed |
| `source_digest` の consumer 3 nodeid | rc=0、3 passed |
| 変異 matrix (11 変異) | baseline PASSED、11 KILLED、SURVIVED 0、MISMATCH 0 |

checker の report は `context_matrix` に `genome_count=8`、`overlay_count=2`、
`expected_context_count_per_file=16` を記録する。**ただし 16 文脈の実効 define map は 4 種、
正規化 digest は 2 種である。「16 個の異なる macro 構成を検証した」とは書けない。**

## 3. 正直な留保

- **TRACE=0 の性能値はまだ 1 件も無い。** 本 wave が解いたのは「検査が拒否する」ことであって、
  計測そのものは land 後の投入に委ねる。計測 script は投入前に未追跡ファイルゼロを要求し、
  計算ノード側は job 開始時にも HEAD が投入時と一致することを要求し、かつ job 自身が repo 内へ
  未追跡ディレクトリを作る。この 3 つが「記録 commit → 受入 → land」の途中での投入と両立しない。
- **TRACE=1 の既存 evidence は `ef9328a3` を source とする過去の pilot である**
  (`output/insights/2026-08-22_t755-mocc-trace-v2-pilot-serializability.md`)。TRACE=0 は
  `058d0c4e` を source とする。両者の source commit は異なる。差はコメント 1 行の位置だけで
  前処理出力は同一だが、**「同じ source で正しさと性能を揃えた」とは書けない。**
  規律 1 の逐語要件 (別ビルド・別 run、variant も baseline も trace-disabled) は
  source commit の同一を求めていないため、規律 1 違反ではない。
- pilot の receipt は `"measurement_role": "pilot-only; not official calibration"`、
  `"eligible_for_refreeze": false`、`"official_certification": false` を立てる。
  得られる値は pilot evidence が 1 件増えるだけで、certified 選択結果は変わらない。
- 本 wave が新たに commit tree 走査を足したため、checker 1 回あたり `git show` の起動が
  488 回増える (tree あたり 244 supply file x 2 commit)。genome ループの外なので文脈数には
  比例しない。計算ノードの job は 1790 秒の内訳に対して 1810 秒の余白を持つ。

## 4. 未解決 (ユーザー裁定へ返す)

段 3 と段 6 の敵対レンズが挙げた、**本 wave が広げても狭めてもいない既存の穴**が 3 件ある。
いずれも今回の差分は該当しないが、mocc の TRACE=0 値がこれから生まれる以上、
依存する範囲が増える。

1. **不在証明の解析が間接展開と行継続を追わない。**
   `set(MODE MQLOCK)` + `target_compile_definitions(t PRIVATE ${MODE})` の間接供給と、
   `#defi` + 行継続 + `ne MQLOCK` は、現行の CMake literal token 照合と `#define` regex を
   すり抜ける。走査元を commit tree に広げてもこの穴は残る。
   限定的な裏付け: 511c9538 の tree で `MQLOCK` は 31 行に現れ、**すべて `#ifdef` /
   `#endif` / コメント**である。`#define` も CMake 供給も無い。初期化済みの
   `third_party/shirakami` にも `MQLOCK` を含む file は 0 件。
2. **checker は include を展開前に除去するため、`#define H "a.hh"` を `"b.hh"` に変えて
   不変な `#include H` を残す差分を false-green にしうる。** 今回の差分は該当しない。
3. **report が `old_active` / `new_active` を別々に hash 化しながら `"identical": True` を
   固定するため、hash 不一致と identical が同時に立つ証拠が出うる。**

## 5. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1506-mocc-trace0/` に次を保全した。

- `checker-postmerge.out` — main 取り込み後の実 checker 出力 (rc=0)
- `jobsim-checker.err` / `jobsim-checker-after-fix.err` — 計測 job topology の fix 前後
- `probe-wiring.py` / `probe-fullchecker.py` — 切り分け probe (repo 外、monkeypatch)
- `mutation-ledger-probe.json` — 変異 probe 回 (M6 が SURVIVED。erratum として保全)
- `mutation-ledger-final.json` — 変異最終回 (11/11 KILLED)
- `transfer-receipt.md` — ccbench object の移送 receipt (prepared / imported / reentered)
- `s6fix-tests.log` / `s6fix-consumers.log` / `postmerge-tests.log` — 親が実走したテスト
- 段 2 プラン、段 3 / 段 6 の敵対レビュー各 2 本、焦点再レビュー、段 4 裁定
