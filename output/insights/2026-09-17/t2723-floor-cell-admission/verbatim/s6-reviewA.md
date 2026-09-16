## 受理集合の適合

以下、A＝`orchestrator/campaign/p3_b4_admission_record.py`、F＝`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`、R＝`orchestrator/campaign/p3_b4_material_report.py`、AT／FT＝対応する `orchestrator/tests/test_*.py`。判定は静的読解であり、pytest・変異実走は行っていない。

**所見**: 裁定 §3 の列挙外の受理拡大という疑いは、変更前との照合では成立しない。
**分類**: refuted
**重さ**: nit
**根拠**: A:650「`cell.strip()`」、F:1489「`verbatim_labels[...] != PREREGISTRATION_FLOOR_LABEL`」、F:1503「`return raw_values[...]`」と旧 F:1470–1517 を照合。完全表の ` 未記入 ` は拒否→None、sentinel の真正表＋外側の同 prefix 行は拒否→None。`ｆｌｏｏｒ`／外周空白付き floor label は row error、`artifact_path=artifacts/a|b.json; sha256=…` も2セル制約で row error。
**影響**: 列挙外の成果物値・参照先変更は見つからない。同一入力が両版で成功する場合、floor 値・参照先は変わらない。
**推奨**: 変更不要。見出し境界・fence/comment・12非空行・header・両端 `|`・2セル・label 重複／集合・全セル不可視文字・責任者述語による縮小は裁定の列挙に含まれる。

## sentinel の掛け先

**所見**: NFKC 互換異体が absence に化ける疑いは現物で反証できる。
**分類**: refuted
**重さ**: nit
**根拠**: A:650–656 は strip 済み raw と normalized を別保存し、F:1524 は「`raw_cell == PREREGISTRATION_ABSENT_SENTINEL`」。責任者が適合する完全表では `未記⼊`（U+2F0A）→grammar error、` 未記入 `→None、`未記入\u200b`→A:541 の不可視文字検査で row error、raw が異なる他の NFKC 互換異体も不可視文字違反がなければ grammar error。raw の `未記入` だけが None。
**影響**: NFKC のみで一致する値から floor absent の材料レポートが生成される追加経路はない。
**推奨**: 変更不要。

## 責任者行の述語

**所見**: 責任者述語の複製・緩和、または sentinel による先行 return という疑いは成立しない。
**分類**: refuted
**重さ**: nit
**根拠**: F:1496 と A:705 は同じ `_assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel` を呼ぶ。F:1523 の `_floor_cell(raw)` 完了後に sentinel 比較。指定5例は旧／新述語とも、`実行責任者 = alice、開始時刻 = 2026-09-17T10:00+09:00`＝受理、両値 `未記入`＝拒否、`hello`＝受理、行欠落＝parser 拒否、空値＝述語拒否。
**影響**: 責任者違反を floor absent として処理する経路はない。`hello` の受理は既存の意味検証非保証であり、今回の緩和ではない。
**推奨**: 変更不要。5例の比較は責任者検査についてであり、完全 admission 全体の成立とは区別する。

## admission 関数の不変性

**所見**: helper 抽出に伴う admission の条件・例外 signature・検査順の変更は見つからない。
**分類**: refuted
**重さ**: nit
**根拠**: 旧 A:617–701 と新 A:608–722 を行単位で照合。追加は `verbatim_labels` の生成・保存・返却、helper 呼出しへの置換、述語内 `continue`→`return`。`values`／`raw_values` の挿入順、decode の「`raise B4AdmissionRecordError(...) from exc`」、固定 message、raw→normalized expectation grammar、model→prompt 照合の順序は同じ。
**影響**: admission の受理集合・例外型・message bytes・明示的 cause に差分は見つからない。
**推奨**: 変更不要。関数分割に伴う traceback のフレーム増加を、error signature の変更と混同しない。

## F423 型 decoy

**所見**: 両見出しを壊して別所の canonical §5 を読ませる F423 型は残る。
**分類**: real
**重さ**: nit
**根拠**: A:621／628 は文書全体で raw 見出しを照合する。真正側を `## ５.`／`### ５.１` に変更し、block 外の別所に正常な両見出しと完全表を置くと、後者だけが探索対象になる。一方、fence/comment 内コピーは A:619–627 で除外され、floor label の homoglyph・重複・9データ行＋外側 pin は A:637／653／658 と F:1489 で拒否される。
**影響**: 真正側に見える表が未充足でも、別所の canonical 表にある有効 pin が材料レポートの floor 出所になりうる。
**推奨**: 裁定 §5 の既知限界として記録する。本 wave の must-fix には追加しない。

## error の写像

**所見**: decode 以外の UnicodeError を encoding error と誤分類する具体的経路は、現物には見つからない。
**分類**: refuted
**重さ**: nit
**根拠**: A:608–613 だけが UnicodeError を捕捉して admission error の明示的 cause にする。正規化・表形状・不可視文字違反にはこの cause が付かない。F:1482 は「`isinstance(exc.__cause__, UnicodeError)`」で encoding、その他は row に写し、責任者違反も F:1499–1502 で row。R:222–226 の「`authoritative_floor_rejected`」「`f"{exc.code}: {exc.detail}"`」「`cause=exc`」は変更されていない。
**影響**: 不正 UTF-8 は encoding error、構造・責任者違反は row error として材料レポート生成を停止する。BOM 除去以外の decode 受理差分はなく、先頭 BOM 付き完全表は旧経路でも受理できた。
**推奨**: 変更不要。encoding の cause chain に admission error が挟まるのは指定された写像どおり。

## test の検出力

**所見**: M1〜M11 に SURVIVED 見込みの穴は見つからないが、失敗集合と KILLED は未実測である。
**分類**: plausible
**重さ**: nit
**根拠**: FT:835–963、AT:667／731／762／1173 の入力と assertion から下表を予測する。
**影響**: nit。静的な killer 予測を実測済みの変異検出実績として扱うことはできない。
**推奨**: 親の probe で実際の失敗集合を固定する。M1、M5、M6、M7 の killer 専属性は主張しない。

| 変異 | 赤になる見込みの test |
|---|---|
| M1 旧全文 prefix 走査 | 新規(2) `ignores_pin_outside_section5`、(3) missing-floor、(4) unrecorded-owner、(5) missing-owner、(6) decoy 両種、(10) unknown-label。外側複製・decoy は旧 `exact 1` 違反でも赤になる |
| M2 責任者述語削除 | (4) `rejects_unrecorded_owner_before_loading_pin`。pin 側は loader 呼出しで AssertionError、sentinel 側は期待した row error が出ない |
| M3 label 集合検査削除 | (10) `rejects_unknown_label_at_fixed_row_count`。floor／owner は残るため None まで通り、期待例外が出ない |
| M4 strip 除去 | 既存 `exact_sentinel_is_the_only_absence`、(8) `preserves_raw_floor_pin`、AT の raw／normalized 分離 test |
| M5 normalized 値を raw に保存 | AT:1173 `parser_preserves_raw_and_normalized_values`、AT:667 `expectation_row_rejects_nfkc_only_ascii_grammar_matches`、(8) raw path、(12) NFKC sentinel |
| M6 fence 除外撤去 | (6)[fence]、AT:731 `commonmark_fence_openers_and_marker_lengths` 等 |
| M7 comment 除外撤去 | (6)[comment]、AT:762 `rejects_html_commented_region_but_accepts_comment_outside` |
| M8 normalized pin 使用 | (8) `preserves_raw_floor_pin`。`artifacts/Ａ.json` が別 path になり、全角構文の拒否にも差が出る |
| M9 exact floor label 検査削除 | (9) `keeps_exact_floor_label[padded/fullwidth]` |
| M10 normalized sentinel 比較 | (12) `rejects_nfkc_only_absent_sentinel` |
| M11 全 label に述語適用 | (1) 実文書、既存 sentinel test、(2)／(6) の sentinel 正例等。floor 自身の `未記入` も拒否される |

(7) label literal と集合所属、(11) encoding/BOM は独立した契約 pin。M0 は等価対照として SURVIVED 見込み。

**所見**: loader 未呼出し観測が resolver の検査機構を置換しているという疑いは成立しない。
**分類**: refuted
**重さ**: nit
**根拠**: FT:815–823 は loader 到達時に記録して AssertionError を投げるだけで、parser・責任者述語・resolver は現物のまま。FT:798–805 は先に実 issuer で pin を生成し、(8) FT:908–926 は実 loader を呼ぶ。ただし既存 `_synthetic_source` は FT:73–80 で Git／校正読込の fixture 差替えを含む。
**影響**: resolver の検査欠落が loader stub の正常戻りで隠れる経路はない。一方、これらの test は実校正の成立を証明しない。
**推奨**: 変更不要。「全依存先を無差替え」とは説明せず、resolver 境界の観測と既存 synthetic fixture の範囲を区別する。

既知所見：F:74 の絶対 sibling import は現存し、FT とは別の `test_campaign_import_invariant.py:1238` で赤になる見込み。親の予定どおり相対 import にして F:32–33 の import 群へ移す（未実走、成果物受理集合への影響を示せないため本レンズでは nit）。

## テスト弱体化

**所見**: 指定3件以外の期待値緩和は見つからないが、schema 負例の入力変更は明示して扱う必要がある。
**分類**: real
**重さ**: nit
**根拠**: 差分では padded sentinel、duplicate rows、m05/m06 code 固定に加え、FT:759 の schema 入力が `v2`→`v999`。F:39–40 は `v2` を有効な aggregate schema と定義する。AT は1 test 追加のみ、RT は3箇所の文書 fixture 変更のみで、既存 assertion・golden の変更はない。
**影響**: schema 負例は「有効な v2 名に不適合な形状」から「未対応 schema 名」の拒否へ対象が変わるが、resolver が row error だけで test を通す穴は code 固定で閉じる。
**推奨**: author 報告どおり入力補正を記録する。反転・skip・削除・現行 hash 差込み・揮発 payload 焼込みによる弱体化は見つからず、追加変更は不要。

## 裁定パッケージ候補

**所見**: 他欄未記入でも有効 floor pin が present になる既存仕様は、今回の接続後も残る。
**分類**: real
**重さ**: nit
**根拠**: F:1494–1503 は責任者セルだけに述語を適用し、F:1514–1515 も「`Other cells' sentinels and expectation declarations are not checked`」と明記する。
**影響**: 他欄や expectation 宣言が未充足でも、有効 pin の floor 値を材料レポートへ渡せる。ただし、それだけで certified になるとは言えない。
**推奨**: 見出し decoy と併せ、必要なら別裁定で扱う。本 wave に他欄 sentinel 検査や完全 admission gate を追加しない。

## 総括

must-fix 0 件 — GO（本レンズの静的レビュー範囲）。

列挙外の受理集合変更、admission の振る舞い変更、M1〜M11 の明白な検出漏れは見つからない。既知の import 修正と親の統合・変異実走は残る。author の「173 passed」は自己申告として読み、本レビューでは追認していない。
