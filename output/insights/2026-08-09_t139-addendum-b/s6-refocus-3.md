| 出所 | # | 重み | 状態 | 根拠 file:line |
|---|---:|---|---|---|
| 第2巡残存 | 1 (`b03` receipt schema) | blocker | **closed** | 追加必須項目と validator 条件を明示的に否定し、producer 実装 wave／別 study へ戻した。`addendum-b.md:185-191,211-213`。core の既存 schema は `preregistration.md:278-297` |
| 第2巡残存 | 2 (`b02` 適用先なしのまま前進) | blocker | **partial** | 保留推奨と main 拒否は追加された。`package.md:13-17,210-216`。しかし B8(b) を「発効済み追補とは扱わない」とした直後、「発効した追補 B が存在する」状態と説明している。`:212-220` |
| A | 8 | must-fix | **partial** | 保留／設計入力／不採用の選択肢は揃ったが、B4 と B8 の発効状態・参照先が矛盾し、安全に裁定できない。`package.md:136-140,199-220` |
| B | 7 | must-fix | **partial** | 推奨は安全側へ差し替えられたが、上記の矛盾により「何を裁定すると何が発効するか」が非一意。`package.md:210-223` |
| B | 8 | nit | **closed** | 無限定の原文を残しつつ erratum で T-139 core 対象へ正しく限定した。`s4-adjudication.md:121-130`。package も同じ限定。`package.md:180-184` |

## 新規所見

### [blocker] B4／B8 が、追補 B の発効状態と新 study への接続を二通りに定義している

B8(b) は `b01`〜`b03` を「現 study の発効済み追補とは扱わない」と明記する一方、その成果物影響では同じ選択肢を「発効した追補 B が存在する」中間状態と説明している。`package.md:212-220`

さらに B4(a) は公表手続きを「新しい core を起こす別 study」で凍結するとしながら、現追補 B を「そのまま接続できる」と書く。`package.md:136-140`。しかし B8 自身は、別 study の新 core で現 study の空欄を後から埋めた扱いにはできないと正しく述べている。`:199-200`。core も別 study では新 core が必要と固定している。`preregistration.md:313-316`。現草案は旧 core の三つ組へ明示的に束縛されている。`addendum-b.md:20-27`

したがって、選択肢 (b) を裁定した際に、

- 非権威の設計入力だけが残るのか
- 現 study の追補 B が発効するのか
- 新 study が旧 core 向け追補 B を参照できるのか

が一意に決まらない。

**成果物影響:** resolver が旧 core に束縛された追補 B を新 study で拒否するか、誤って受理するかが分岐し、main admission の受理集合、材料レポートが参照する addendum digest、proof chain の core→addendum 辺が変わる。primary certified 判定式の値自体は変わらない。

最小修正は、B8(b) を「非発効・非権威の設計メモ」に一意化し、`:218-220` の「発効した追補 B」を削除すること。B4 は「新 study の新 core に束縛された新しい追補で、同じ提案値を再採用できる」と書くべきで、現追補をそのまま接続してはならない。閉集合外の公表手続きは引き続き**別 study へ**送る。

### [nit] README の「裁定 5 束をパッケージへ反映」は一件多い

README は Q-A〜Q-E の「5 束をパッケージへ反映した」とするが、列挙・package への反映は Q-A〜Q-D の4件だけである。`README.md:49-57`。Q-E は段8候補の処置であり、canonical 記録は `docs/worklog.md:2720-2722` にあるが package には現れない。

**成果物影響:** `b01`〜`b03`、certified 値、receipt の受理集合、proof chain は変わらないため nit。文言を「関連する Q-A〜Q-D を反映」に限定すれば足りる。

裁定内容そのものについては、次は正確だった。

- B7 は Q-B により裁定済み。`package.md:186-189`、`docs/worklog.md:2716-2717`
- Q-C は `a13` 台帳の方向であり、`b03` の実装契約として取り込んでいない。`package.md:229-233`、`docs/worklog.md:2718-2719`
- Q-D は B8 を裁定していないと明記されている。`package.md:205-208`、`docs/worklog.md:2720-2721`
- Q-A は schema 固定時期について「同じ向き」とする推論に留まり、`b03` 自体が裁定済みとは書いていない。`package.md:64-66`、`docs/worklog.md:2714-2716`

## 残存 blocker

**1件。**上記の B4／B8 の発効状態・cross-study 接続の矛盾である。

安全側の推奨自体は差し替えられたが、選択肢 (b) の意味が二重なので、第2巡 blocker 2 は完全には閉じていない。このままでは「設計入力を裁定しただけ」を「現 study の追補 B が発効した」と機械側または承認者が読み替えられる。

## 退行検査

- **`b03` の委任は空洞化していない。**root は literal から導出され、caller・receipt 申告・親系列 ID・試行 IDを入力にしない。`addendum-b.md:165-169`。公表台帳自身の create-only な `(root, ordinal)` 一意性で reset を防ぐ。`:171-183`
- **active gate 未実装との区別も維持されている。**台帳の実在・所有・操作は実装 wave の責務であり、現時点では規範だけだと明記する。`addendum-b.md:198-203`。schema 削除による宙づりの validator 参照はない。`:209-216`
- **時相境界は維持。**main 投入前の admission と、測定開始後の既存 §9 分類を分離している。`addendum-b.md:193-196`。core の既存分類は `preregistration.md:237-245`
- **閉集合外の規則を field として新設していない。**`b02` は配分値だけで、公表推論規則を明示的に除外する。`addendum-b.md:122-146`。`b03` は receipt schema／validator 条件を除外する。`:185-191`
- **exact-key:** fields 範囲は `addendum-b.md:62-206`（`## fields` は `:61`、次の `## ` は `:207`）。解決される key は `b01` (`:63`)、`b02` (`:94`)、`b03` (`:148`) のみで、集合は正確に `{b01, b02, b03}`。
- **fenced heading:** fields 内の fence は `:65-71`、`:96-108`、`:110-112`、`:150-163`。その内部に行頭 `## `／`### ` は **0件**。
- **core 不変:** 現在の core と指定 commit `88d68f9…` の blob はともに SHA-256 `ac939af4…` で、core 対象の `git diff` も空だった。草案が宣言する三つ組は `addendum-b.md:20-27`、core の不変・blob 束縛契約は `preregistration.md:29-37`。core 本文の書換えはない。
- **3成果物の主結論:** addendum は未発効かつ公表手続き未確定を認める。`addendum-b.md:15-17,144-146,214-216`。README は承認保留を推奨する。`README.md:44-48`。食い違いは package の B4／B8 内部に限定される。
- 実走・build・pytest は行っていない。以上は read-only の静的読解と字義走査であり、テストの緑は主張しない。

## 総括

- closed / partial / regressed: **2 / 3 / 0**（指定された5件の再判定）
- 残る blocker 件数: **1件**
- **NO-GO** — 保留推奨への修正は進んだが、「設計入力のみ」と「発効済み追補」、「別 study」と「現追補をそのまま接続」が同居している。意思決定材料としてまだ一意・正直ではなく、この草案と承認パッケージをそのままユーザー承認へ回してはならない。