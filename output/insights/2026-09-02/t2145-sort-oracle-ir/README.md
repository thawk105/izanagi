# [T-2145] sort SWO oracle の受理言語を検証済み IR へ縮めた — 一次資料

wave branch `worktree-dev-wave-t2145-sort-oracle-ir`。着手時 main `82a259c0a`、
取り込んだ main `24b31d2a3`、実装 commit `23565ae55`、取り込み commit `6850282ef`。

**この変更は D39 の raw C++ 独立合成の実証点を別実験へ移す。** D344 が却下理由に挙げた
実験同一性の論点は D1451 で supersede されていない。本 wave は D344 を supersede したとは
記録せず、別実験になることを明示したうえで着手した (D1451 が許可した形)。

## 構成

- `s1-brief.md` — 段 1 brief (親)。scope・不変条件・実アンカー表・親の provisional 裁定。
- `s4-adjudication.md` — 段 4 裁定 (親)。R1〜R10、変異事前登録。
- `s6-review-adjudication.md` — 段 6 レビュー裁定 (親)。F1〜F10。
- `s6-fix2-adjudication.md` — 段 6 追加裁定 (親)。実走で判明した G1〜G4。
- `s5-agent-review.md` — **role file 2 枚と adapter 2 枚に対する親の独立レビュー証跡**
  (先例が pin 更新に要求するもの)。
- `mutation-spec-final.json` / `mutation-probe.json` — 変異の事前登録と probe。
- `mutation-summary.json` — probe と本走の集計、識別子 churn の分離。
- `verbatim/` — 子の成果物 (plan 1、相談 2、実装 1、レビュー 2、fix 5、merge 解消 1)。

## 何を変えたか

受理言語を **79 値の閉じた型付き IR** へ縮め、関係行列の出所を候補実行から
trusted evaluator へ移した。**受理集合を狭める変更である。**

- admission は候補テキストの token 列が 79 値のいずれかの正準 token 列と完全一致することだけを
  受ける。token 間の空白だけ自由で、コメント・行連結・UCN・raw string・代替トークンは受理しない。
- 受理後は正準形へ正準化し、backoff 軸と同じ形で**正準形を材へ再 materialize する**。
  build 対象・compile 対象・照合対象がすべて正準形で一致する。
- 実 TU の compile と実行は残し、全 corpus x 全 order の観測行列と byte exact で照合する。
  不一致は候補の `REJECT` ではなく `UNAVAILABLE` とする。

## 親が実測した事実

いずれも子の主張を鵜呑みにせず親が測ったものである。

| # | 事実 | 測り方 |
|---|---|---|
| 1 | 値域はちょうど 79、render は一意、全件が admission を round-trip する | 実装を直接呼ぶ (`probe_s5_verify.py`) |
| 2 | 79 値の render が変更前の `_validate_single_sort_statement` を全件通る | 同上、失敗 0 |
| 3 | 79 値の render が変更前の `coder_effect_gate.scan_host_effects` を全件通る | 同上、finding 0 |
| 4 | 権威集合 15 件が render 値集合に **byte exact** で含まれ、admission も全件通る | 同上、欠落 0 / 過剰拒否 0 |
| 5 | 正準化は冪等で、空白ゆらぎは正準形へ畳まれる | 同上 |
| 6 | 非 IR 8 例 (総称 lambda・無条件 loop・重複 field・未知 field・body call・コメント・JSON・追加文) を全件拒否 | 同上 |
| 7 | 焦点走 **766 passed / 2 skipped / rc=0** | 計算ノードで実走 |
| 8 | 変異 **11/11 KILLED**、baseline 緑 | `tools/mutation_harness.py`、dispatch |

## 主張してよいこと・いけないこと

**主張してよい:** 本変更後に build へ入りうる sort comparator の集合は 79 個の正準形に等しい。
その全件が変更前の 2 つの受理 gate を通る。現行の権威集合 15 件はその真部分集合である
(byte exact、欠落 0 を実測)。したがって **materialize 面での受理集合は真に縮んでいる。**

**主張してはいけない:**

- 全 consumer 経路を通した完全な包含証明である — 段 3 レンズ A が列挙した diff 検疫・auditor・
  依存検証・broker 実行・build・S1/floor consumer・receipt・台帳は親 probe の測定範囲外である。
  焦点走と変異走が届く範囲までしか測っていない。
- 候補の SWO 違反を動的に見つける gate が強くなった — **その gate は恒真化した。**
  79 値は構成上すべて SWO なので、`check_relation_matrix` は候補由来では発火しない。
  保証の種類が「動的な反例探索」から「構成的 SWO + 実 TU conformance」へ**変わった**のであって、
  単純な強化ではない。provenance 面では強く、任意 C++ に対する動的反例探索能力は失っている。
- D344 を supersede した — していない。実験同一性の論点は生きたままである。
- 合成子の実挙動がどう変わるかを測った — 測っていない。合成走を回すまで分からない。

## 変異の帰属 — 識別子 churn を差し引いた

F568 のとおり、oracle module を触ると contract identity が変わり、機構と無関係に落ちる node が出る。
本 wave では**ちょうど 2 件**だった。

- `test_sort_swo_oracle.py::test_contract_manifest_hashes_and_literal_are_exact_snapshot`
- `test_p3_s4_loop_sort.py::test_b4_sort_marker_is_opt_in_and_ordinary_contract_is_unchanged`

これを差し引いた「機構固有の落ち先」は次のとおりで、**11 件すべてが 1 件以上を持つ**。
機構固有 0 件の変異は無い。

| 変異 | 機構固有 node 数 |
|---|---|
| M1 重複 field の受理 | 1 |
| M2 受理経路の迂回 | 4 |
| M3 描画方向の反転 | 41 |
| M4 storage を符号付き | 1 |
| M5 pointer 順位の反転 | 2 |
| M6 key を NUL で切る | 2 |
| M7 実行結果との照合を外す | 1 |
| M8 契約から pointer 対応を削除 | 2 |
| M9 正準化の省略 | 1 |
| M10 **過剰拒否の正例対照** | 42 |
| M11 語彙外で例外を投げる旧実装 | 9 |

M10 は `DW-M01` が受理集合を縮小する wave へ課す**承認外の過剰拒否の正例**である
(単一 field の IR を拒否させ、権威集合 15 件のうち 6 件が通らなくなることを検出できるか)。

**この表から読める設計上の含意が 2 つある。**

- M9 (正準化の省略) を捕まえるのは
  `test_p3_s4_loop.py::test_sort_quarantine_canonicalizes_outer_whitespace_bytes` **1 本だけ**である。
  段 6 でこの test の期待値を正しい不変条件へ直していなければ、この防壁は誰も検査していない。
- M4 と M6 (evaluator の値取り出しの誤り) を捕まえるのは 79 値 x 153,576 セルの
  batch conformance node **だけ**である。実行コストを理由にこれを削ると、
  trusted evaluator の値取り出しの誤りは素通りする。

## 限界

- `acceptance_duration_ledger.json` は本 wave の新設・改名 node へ**未追随**である。
  少なくとも 26 node が ledger に無く、旧名も残る。値は実測 JUnit からしか作れないため
  合成していない。**ledger 未更新だけを理由に赤になる検査は現状 0 本**なので受入は通るが、
  scheduling は古い参照を使う。別 task へ送った。
- D901 条項 2 の三脚 (identity / WAL / cache) のうち、sort は cache key へ届かない。
  backoff 限定のまま維持することを推奨として裁定パッケージへ載せた
  (`DW-G03` の族一般化を満たさず、成果物が変わる具体例も未確認のため)。
- D669 は当該 test file の受入全走からの恒久除外を決めているが、実装側の除外表は空である。
  本 wave は**現行コードを事実として扱った**。不一致自体は追っていない。
