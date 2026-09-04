# 段 6 裁定 — レビュー所見の real / refuted と fix scope

## 0. 親が実測した決め手

`g++-12 -E -P` で相対 include 経由の `__FILE__` を実測した (repo 外 probe)。

- header: `"<root>/cc/silo/../../include/backoff.hh"` — **正規化されない**。
- owner TU: `"<root>/cc/silo/transaction.cc"`。
- `__FILE__` は「token を含む file」ではなく「macro が展開された file」の path になる。
  CCBench では `ERR` の定義は `include/debug.hh`、展開は `cc/silo/transaction.cc` なので、
  出力に出る path は **transaction.cc** であり、`root_dependent_builtin_paths` の要素
  (= debug.hh) とは**一致しない**。

この 2 点が下の裁定を決めた。

## 1. 両レビューが収束した中心の所見

A の must-fix 1 と B の must-fix 1 は同じものである。

> 閉包 membership は「その名前の依存 file がある」ことしか証明せず、
> 「この出力 span が `__FILE__` の展開である」ことを証明していない。
> 閉包内 path と同じ bytes を持つ普通の文字列リテラルでも置換が起きる。

**裁定: real (指摘は正しい)。しかし「意味の異なる個体が緑になる」という影響主張は成立しない。
fix は採らず、限界として明記する。**

理由:

1. 分類器が実際に保証しているのは「差のある行が、`<requested_root>` を `<control_root>` へ
   写すだけで control 行と byte 完全一致する」である。**この保証だけで、両出力は root 文字列を
   除いて同一である**。閉包 membership はそこからさらに狭めるための追加条件であり、
   健全性の根拠ではない。
2. 両レビューの反例は、いずれも requested 側が `<requested_root>/X`、control 側が
   `<control_root>/X` (X が同一) という形である。**X が同一である差は、定義上、
   同じものを別の場所に置いたことによる差**である。X が違えば残差が出て赤になる。
3. source に runtime の一時 directory の絶対 path を書き込むことはできない。出力へ絶対 root が
   入る経路は (a) compiler の `__FILE__` / `__BASE_FILE__`、(b) build system による
   source dir の埋め込み (`configure_file` 等) の 2 つだけで、**どちらも置き場所由来**である。
4. 反例を「意味の差」にするには stock 側 (素の CCBench) にも対応するリテラルが要る。
   patch を書ける側からは作れない。素の木を書き換えられる相手は本関門の防御対象ではない。
5. B の対案 (`-fmacro-prefix-map` で compiler に正規化させ、追加でもう 1 回 preprocess して
   完全一致を要求する) は採らない。
   - **生成時に畳む形であり、D1523 が却下した「比較の前に情報を捨てる」形に当たる。**
   - inert arm ごとに preprocess が 1 回増える。
   - compiler が未対応のときの fail-closed 枝を発火させる実在の成果物を名指しできない
     (DW-G04、DW-O13)。検査できない枝を足すことになる。
   - 裁定パッケージ候補として記録する。

## 2. 採用する fix (1 件だけ)

**A の must-fix 2 のうち「root の直前の token 境界」だけを採る。**

- 現行は行中の任意位置で `<requested_root>/` に一致すれば置換する。直前の byte が
  path 文字集合に含まれていても置換してしまう。
- 実際の `__FILE__` 展開は必ず `"` の直後に現れるので、**直前 byte が path 文字集合に
  含まれないことを要求しても、実運用の緑を 1 件も落とさない**。
- 受理集合を狭める方向 (規律 2 の向き) であり、負例で発火を確かめられる。

## 3. 採らない fix と理由

| 所見 | 裁定 | 理由 |
|---|---|---|
| A must-fix 1 / B must-fix 1 (builtin provenance の束縛) | real・不採用 | 1 節のとおり。限界として明記する |
| A must-fix 2 の「control 側閉包にも rel が実在すること」 | real・**不採用** | 発火条件を満たす入力を作れない。requested の閉包にあって control の閉包に無い file は、その file の中身が requested 出力にだけ現れるので必ず残差で赤になる。**検査できない述語は足さない (DW-G04)** |
| A must-fix 2 の「末尾空成分」「通常 file を跨ぐ `..`」 | real・不採用 | 0 節の実測どおり `..` は実在の展開形に必ず現れるので禁止できない。残る差は 1 節の理由で置き場所由来である |
| A must-fix 3 の負例追加 (`@policy`、`probe.hh/../other.hh`) | real・不採用 | 対応する述語を採らないので、負例だけ足しても機構を通らない |
| A must-fix 4 (M1 の単一理由性の記述訂正) | real・**採用 (記録の訂正)** | 4 節 |
| B の「空 root 検査は到達不能」 | real・nit | production の root は `resolve(strict=True)` 済み。fail-closed 側の冗長で害はない |
| B の「red record の digest / ID が旧版と変わる」 | real・nit | pin している consumer は 0 件 |
| B・A の「build root 除外は将来 false red になりうる」 | real・条件付き | 段 4 の判断どおり。発火したら実測として現れる。worklog に残す |

## 4. 変異事前登録の訂正と追加 (A must-fix 4 への対応)

- **訂正**: M1 (置換許可の述語を無条件許可へ) を kill する
  `test_inert_root_shaped_literal_outside_closure_is_red` は、membership 拒否が残差を生むという
  **単一の因果鎖**で赤になっている。membership と残差は独立した 2 層ではなく上流・下流である。
  A の「各条件を個別に無効化する」機械的基準では 2 件に見えるが、冗長 gate ではない。
  同じテストが M2 も kill するが、M2 には専用の負例 (`..._semantic_difference_on_root_line_is_red`)
  が別にある。
- **追加 M7**: 置換位置の左 token 境界検査を削除する変異。
  kill する node: `test_inert_root_prefixed_by_path_byte_is_red` (新設)。
  単一理由性: 左境界を外すと当該負例は置換されて残差が消え緑になる。他の条件
  (membership は満たす、builtin 非空、置換 1 件以上) はいずれも赤にしない。

## 5. 明記する限界 (成果物へ書く)

> 本関門は「差が置き場所だけで説明できる」ことを、requested 側の差分行に対する
> root 置換で control 行と byte 完全一致することによって判定する。
> **置換した span が compiler の `__FILE__` / `__BASE_FILE__` 展開であったことは証明していない。**
> 依存閉包にある file を指す絶対 path が、build system の埋め込み等、別の経路で出力に現れた
> 場合も同じ扱いになる。両側で suffix が同一である差だけを通すため、通す差は置き場所を
> 揃えれば消える差に限られるが、生成元までは束縛していない。
> 素の (stock) 木を書き換えられる相手はこの関門の防御対象ではない。
