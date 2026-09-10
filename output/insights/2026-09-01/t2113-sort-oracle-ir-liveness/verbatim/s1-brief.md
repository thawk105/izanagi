# [T-2113] 段 1 brief — sort SWO oracle の受理言語を検証済み IR へ縮める方向の生死確認

基準 main = `08a17b3b3271dc6e0db575a7c15afbbbb91f6328`。wave branch =
`worktree-dev-wave-t2113-sort-oracle-ir-liveness`。

## scope

問い 3 点だけを 100 行以内の使い捨て driver (`DW-G01`) で実測して答える。

- Q1 表現性: 現行の権威集合 15 件を、小さい型付き whitelist IR へ**全件**表現できるか。
- Q2 再現性: その IR の trusted evaluator が、現行 2 corpus の 18x18 関係行列を再現できるか。
- Q3 拒否: 未知 opcode・型不一致・任意 C++ 文字列を、評価前に fail-closed で拒否できるか。

**縮小そのものの実装は scope 外。** parser・receipt・合成エージェント・凍結成果物・
`sort_swo_oracle.py` 本体・`test_sort_swo_oracle.py` を変更しない。仮想リスク向けの gate・検査・
台帳・一般化を追加しない (`DW-G05`)。答えが否なら否と記録して実装差分ゼロで返す。

## 確定済みユーザー裁定

- D1355 (ユーザー指示): 関係行列の出所の非保証は「受理言語を検証済み IR へ縮め trusted evaluator で
  評価する」向きで閉じる。本 task は実装せず生死確認だけを置く。偽なら parser・receipt・
  合成エージェントの変更へ進まない。
- D1357: 権威集合は `sort_best.comparator` の name/comparator exact binding 一本。
- 規律 2 を緩めない。anomaly 検出時の即 reject は不変。

## 不変条件

- 実装面の repo 差分ゼロ。driver は repo 外 (`dev-wave-jobs/` 配下) に置く (T-317 裁定)。
- `orchestrator/tests/test_sort_swo_oracle.py` に触れない — 稼働中の [T-1999] が所有する
  (段 1・段 2 の重複検査で実測。下記)。
- 権威集合・corpus・TU template・compile flags の bytes を変えない。よって
  `CORPUS_SHA256` / `TU_TEMPLATE_SHA256` / `DEPENDENCY_MANIFEST_SHA256` の pin 閉包は不動。
- driver の出力は仮説であり、確定は既存 fail-closed 機構が担う (F29)。模擬と実の差を明記する。

## 実アンカー表

| 対象 | 実アンカー |
|---|---|
| 権威集合 15 件 | `orchestrator/campaign/s6_sort_sweep.py:143` `CANDIDATES` (生成器 `_single:122` / `_two:127` / `_NOSORT_IMPL:133`) |
| exact binding | `orchestrator/campaign/sort_comparator_authority.py:58` |
| 2 corpus | `orchestrator/campaign/sort_swo_oracle.py:629` `_CORPUS_TOPOLOGY`、`:659` `_CORPUS_MANIFEST` |
| 関係行列の生成 | 同 `:2442` `_evaluate_executable` (2 corpus x 3 order、order 間不一致は NONDETERMINISTIC) |
| 公理検査 | 同 `:588` `check_relation_matrix` (irreflexive / asymmetric / transitive / transitive-equivalence) |
| 現行の受理言語 | 同 `:523` `_validate_single_sort_statement` (単一の非修飾 `sort(...)` 文という形だけ) |
| 非保証の明文 | 同 `:89` `SORT_SWO_GUARANTEE_BOUNDARY` = `does-not-guarantee[reported-relation-matrix-is-comparator-true-relation]` |
| 比較対象 field の実型 | `external/ccbench/include/op_element.hh:19-21` `Storage storage_` / `std::string key_` / `T* rcdptr_`、`external/ccbench/include/ycsb.hh:35` `enum class Storage : std::uint32_t` |
| 決定的 allocator | `sort_swo_oracle.py:817` `oracle_arena_allocate`、`:842` `operator new` override、`:1183-1184` `aliases = new Tuple[4]` → `separate[0..5] = new Tuple()` |

## 成果物の形

- repo 内: `output/insights/2026-09-01_t2113-sort-oracle-ir-liveness/` の README + `verbatim/`、
  worklog / decisions fragment (`docs/spool/`)。実装面の差分ゼロ。
- repo 外: driver 本体と実行 log。

## 分割方針

実装面の差分ゼロなので段 5・6 と変異 matrix は `DW-S04` の免除に当たる。段 2 (プラン)・
段 3 (敵対 2 レンズ) は省かない — 本 wave の成果物は「正しさ防壁の設計の生死判定」そのもので、
親の単独主張にしてはならない。段 4 で裁定し、driver を親が書いて実測する。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1a) Q1 は真。** 15 件は既に生成器 `_single` / `_two` / `_NOSORT_IMPL` から機械導出されており、
  IR は `(kind, field, asc)` / `(kind, field2, asc1, asc2)` / `const_false` の 3 opcode で足りる。
  検証は「IR → render した文字列が権威集合の literal と byte 一致する」往復で行う。
- **(P1b) Q2 は真。ただし条件つき。** `rcdptr_` を比較する 6 件 (p_asc, p_desc, sp_aa, sp_ad,
  sp_da, sp_dd) はポインタ値に依存するが、TU は `operator new` を arena の bump allocator へ
  差し替えており、`aliases[0..3]` → `separate[0..5]` の割当順が固定なのでポインタの**順位**は
  corpus から導出できる。ただしこの順位は TU の C++ の記述順に暗黙に依存し、
  データとして宣言されていない。evaluator がこれを埋め込むなら、TU 変更で黙って壊れる。
- **(P1c) Q3 は真だが退屈。** whitelist parser は定義上これを拒否する。
- **(P1d) 本当の争点は Q1 の裏側にある。** 15 件だけを表現する IR は「事前 allowlist からの選択」で
  あり、**D344 が typed IR / AST allowlist を却下したときの理由そのもの** — raw C++ comparator の
  独立合成という実証点 (D39) が別実験に化ける。D1355 はこの却下理由に触れていない。
  生死確認は「15 件を表現できるか」ではなく「**15 件を真に含む、合成の余地が残る最小の IR**が
  trusted に評価できるか」で測らなければ、恒真な yes を返す。

## `DW-G05` 成果物影響

否と判定すべきものを真と返すと、後続 wave が parser・receipt・合成エージェントの interface 変更へ
進み、certified な選択結果の受理集合を、根拠のない保証つきで置き換える。逆に真を否と返すと、
`SORT_SWO_GUARANTEE_BOUNDARY` の非保証が恒久化し、この oracle を敵対的合成候補に対する
正しさ関門として使えないままになる。

## 編集面重複検査 (実測)

- 段 1 branch tip: scanned=42 unreadable=0 hits=1 →
  `worktree-dev-wave-t1999-define-gate-family` が `orchestrator/tests/test_sort_swo_oracle.py` を変更。
- 段 2 作業ツリー: total=28 scanned=28 unreadable=0 hits=2 →
  `.codex/worktrees/t1999-unit2b` / `t1999-unit2c` が同 file を未 commit で `M`。
- `orchestrator/campaign/sort_swo_oracle.py` は両段とも hit 0 件。

## 実測環境

Pegasus login node 上の read-only 検査と、driver の局所 compile / run のみ。ベンチマークも
正式測定も行わない。実 oracle の end-to-end 実行は `IZANAGI_SORT_SWO_MASSTREE_ROOT` 未設定のため
不可 — driver は同一 corpus データと同一 allocator 順序を使う独立 C++ 実行で ground truth を取り、
実 TU との差 (ccbench `Tuple` / `TupleBody` の実型を持たないので arena 内 offset が異なる。
ポインタの**順序**は割当順が同じなので保存される) を明記する。
