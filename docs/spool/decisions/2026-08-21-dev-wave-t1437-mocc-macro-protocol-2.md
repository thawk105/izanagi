---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1437-mocc-macro-protocol
seq: 2
---

## {{D:source-digest-supply-precision}}. source_digest の macro 供給表解析を source 単位・CMake 慣習非依存へ精密化する (D93 を緩めない)

**決定:** `orchestrator/campaign/source_digest.py` の実 TU 供給集合解析を3点精密化する。
いずれも D93 の fails-closed 閾値 (未知 macro は停止する) を変えず、検査が見る対象
(defines/供給集合) の精度だけを上げる。

1. **source 単位の protocol 分離。** `EVOLVE_BLOCK_SOURCES` は複数 protocol の source
   (`cc/silo/transaction.cc`、`cc/mocc/transaction.cc`) を一つの tuple に混在させるが、
   従来の defines 計算は genome 1 つが持つ protocol からしか作られておらず、tuple 内の
   他 protocol の source を検査する際に無関係な protocol の defines を誤って適用していた。
   `EVOLVE_BLOCK_SOURCE_PROTOCOLS` (各 source の owner protocol、`None` は genome 由来を意味する)
   を新設し、`_worktree_defines`/`_head_defines` に `source_rel` 引数を追加して file 単位で
   defines を作るよう変更した。registry と `EVOLVE_BLOCK_SOURCES` の exact-match は
   モジュール読み込み時と呼び出しごとの双方で自己検査し、drift や未知 source は `RuntimeError`
   にする (生の `KeyError` を伝播させない — 呼び手が `except RuntimeError` で variant 単位の
   abort に隔離する既存契約に合わせるため)。
2. **CMake `OPTIONS` の裸オプション・非対称 cache 名への対応。** 実 TU 供給表解析
   (`_SUPPLY_RE`) は `NAME=${CCBENCH_NAME}` 形しか認識せず、`=` を伴わない裸オプション
   (`ccbench_add_protocol` の `OPTIONS` に列挙される、CMake の `target_compile_definitions` で
   常時 `-DNAME` になる形) と、左辺 (TU macro 名) と右辺 cache 変数名が異なる非対称命名の
   両方を見落としていた。`ccbench_add_protocol(...)` を balanced paren scan で抽出し、
   `OPTIONS` から次の section keyword までの範囲だけを token 化して解析するよう拡張し、
   裸 token は `merged[name] = "1"` (CMake の `-DNAME` 相当) を明示反映、非対称命名は
   左辺→右辺 cache 名の対応を保持して転送する。
3. **universal definitions 関数本体の CMake 呼び出し形非依存化。** `ccbench_universal_definitions()`
   の中身から供給 token を抽出する処理が、当初 `set(${out_var} ... PARENT_SCOPE)` 形の
   呼び出ししか認識しなかった。`target_compile_definitions(${target} PRIVATE ...)` で同じ
   universal 供給を書くのも同等に正当な CMake の書き方であり、これを使う既存テスト
  (実装済み・別ツールの fixture) が新規に fails-closed してしまった。両方の呼び出し形から
   供給 token を抽出できるよう拡張した。

**理由:**
- fails-closed の閾値自体 (未知 macro を受理しない) は一切変更していない。変更したのは
  「どの macro が実 TU 供給集合に属するか」の判定精度であり、既存の正しい拒否は維持したまま
  誤った拒否 (実際には供給されている macro を未知と誤認する) を減らす。
- MQLOCK は repo 全体 (全 protocol の CMakeLists.txt・universal 定義・`#define`・
  `target_compile_definitions`/`add_definitions`/`add_compile_definitions`/
  `add_compile_options`/`target_compile_options`/`set_target_properties`・
  `CMAKE_CXX_FLAGS` 経由の `-D` 注入) を実走査して供給源ゼロと確認した上で、専用 registry
  (`PROVEN_REPO_ABSENT_MACROS`) に登録した。`CONTEXT_MACROS` (TU 注入で「時々供給されうる」
  macro を両文脈 digest 化する機構) とは意味が異なるため流用しなかった — MQLOCK は
  「一度も供給されない」ことが主張であり、両文脈を覆う必要がない。registry は毎回
  repo を再走査して自己検証し、供給源が出現すれば stale として fails-closed する
  (静的な信頼ではなく実行時の裏取りを維持する)。

**却下した選択肢:**
- 裸オプション・非対称命名を無視し mocc protocol だけ個別に許容する — 同型の裸オプションは
  ss2pl (`DLR1`) にも実在し、mocc 固有の特殊扱いにすると次に同じ壁に当たる protocol を
  未然に防げない。
- MQLOCK を `CONTEXT_MACROS` に追加する — 「TU から不可視に供給されうる」という
  `CONTEXT_MACROS` の意味と、「一度も供給されない」という MQLOCK の実態が食い違い、
  存在しない `MQLOCK=1` 枝を digest に取り込んで誤分類する。

**検証:** 変異事前登録5点 (source 単位 protocol 固定化・registry exact-match 無効化・
MQLOCK self-check 無効化・裸 option 代入削除・非対称 mapping 削除) を実測ベースの
expected_nodes で本登録し、baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0 を確認した。
受入全走は `verdict=child-green` (red_nodeids/flake_nodeids とも空)。
