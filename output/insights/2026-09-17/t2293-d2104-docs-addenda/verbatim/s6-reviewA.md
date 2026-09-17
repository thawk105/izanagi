## 総括

**GO（静的設計レビュー）。must-fix 0 件、nit 1 件。**
pin 追随の漏れ、needle の複数理由化、テスト弱体化は見つかりません。
両 literal・正本・統合後 DW-O18 は、末尾改行を含めて同一の 995 bytes です。
author 報告の「check_docs 不一致 1 件」は統合後には該当しません。統合前の結果との時点差です。
pytest・checker は実走していません。変異の KILLED / SURVIVED は静的予測です。

## 1

pin 追随は完全です。対象は次の箇所で一致しています。

- `tools/check_docs.py:605`：production literal。
- `orchestrator/tests/test_check_docs.py:166`：独立した合成 literal。
- `orchestrator/tests/test_check_docs.py:9484`：995 bytes の固定 assert。
- `orchestrator/tests/test_check_docs.py:9582`、`:9639`：M2 / M11 needle。

指定されたディレクトリ・ファイルを検索し、旧登録文、`F不在は登録せず裁定送り、`、`hold登録後だけ`、DW-O18 の旧 997 bytes に依存する箇所は残っていません。検索に現れる 997 は UID fixture・trace・描画座標など別用途です。

成果物影響：旧契約が残って新しい正本文書を拒否する経路は見つかりません。

## 2

合成 operations から M2 / M11 needle をそれぞれ削除した場合、finding 集合は **`{o18_finding}` のみになる**と静的に判断します。

| case | 削除後の節サイズ | 結果 |
|---|---:|---|
| M2 | 918 bytes | DW-O18 exact 不一致 1 件 |
| M11 | 913 bytes | DW-O18 exact 不一致 1 件 |

根拠は以下です。

- `tools/check_docs.py:1923`：削除は可視本文だけで、raw/visible slice の差は生まれません。見出しも残るため `sections=1`。
- `tools/check_docs.py:5983`、`:6022`：operations は最長行制約の対象外。
- `tools/check_docs.py:5675`：削除前後・接合箇所に禁止語 2 種はありません。
- `tools/check_docs.py:5397`：節は 1,000 bytes 以下。削除で予算超過は生じません。
- 見出し・dispatch 表・参照 edge は変わりません。
- `orchestrator/tests/test_check_docs.py:9653`：rc=1 と finding 集合の完全一致を維持しています。

既存テスト M4 の needle `判定不能・原因未理解は除外せず共に停止。` も新 literal 内にちょうど 1 回です（`:9597`）。合成描画はその literal を 1 回配置します（`:1040`）。

成果物影響：対象義務の欠落を、別検査の偶発的な失敗で代用する変更にはなっていません。

## 3

期待 finding の緩和、case 削除、assert 削除はありません。変更は literal 2 本、固定 byte 数、needle 2 本です。

997 → 995 は、禁止すべき「現行 hash を fixture に差し込んで緑にする操作」には当たりません。

`orchestrator/tests/test_check_docs.py:9457` の docstring は「production 定数と合成 fixture の共謀的縮小を独立 literal で拒否する」としています。今回も fixture は production から動的に取得せず、全文を独立に保持しています。995 は裁定済み正本の実測 byte 数であり、比較・固定長・registry 全体の assert は残っています。

固定長だけでは同じ長さの意味改変を防げませんが、これは既存の限界です。今回その検出力を下げた差分はありません。

成果物影響：裁定された契約更新を受理する一方、production literal だけの改変を拒否する能力は維持されます。

## 4

**M0 は等価です。** `tools/check_docs.py:609` の `同一tipで各1回だけ。` 直後に `""" """` を挿入して隣接する三重引用文字列へ分割した式を AST で評価し、元の UTF-8 bytes と完全一致しました。空白は文字列の外側です。

M0 の分割 anchor、M1・M2・M3 の各置換 anchor は、`tools/check_docs.py` 全体でそれぞれ 1 回です。

以下の nodeid はすべて `orchestrator/tests/test_check_docs.py::` を接頭辞とします。

| 変異 | 静的に予測できる killer node |
|---|---|
| M1・M2・M3 共通 | `test_normative_exact_section_contract_is_handwritten_and_complete` |
| M1・M2・M3 共通 | `test_dw_o18_exact_section_pin_accepts_synthetic_fixture` |
| M1・M2・M3 共通 | `test_dw_o26_exact_section_pin_accepts_synthetic_fixture` |
| M2 固有 | `test_non_attributable_landing_contract_mutations_have_one_finding[M2]` |
| M3 固有 | `test_non_attributable_landing_contract_mutations_have_one_finding[M11]` |

共通 node は literal 等値または baseline の rc=0 が崩れて失敗します。M2 / M3 固有 node は、文書側の削除結果が変異済み checker literal と一致し、期待する finding が消えて失敗します。

**M1 に対して既存テストの `[M2]` / `[M11]` を killer と予測するのは不適切です。** 双方とも DW-O18 不一致が残り、同じ finding 1 件で通る可能性があります。段 4 の候補列挙は変異ごとに区別して probe へ渡してください。

回数制限の `各1回` → `各2回` は適切な追加負例です。読んだ `s4-adjudication.md:43` には既に **M4 として登録済み**でした。追加提案はありません。

成果物影響：登録された負例には独立 fixture による検出経路があり、M0 は値不変を確認する対照として成立します。

## 5

author 報告の次の主張は現物と一致します。

- 両 literal と正本が 995 bytes：AST 抽出で確認。
- M1・M2・M3・M4・M7・M10・M11・M12 の needle が各 1 回：確認。
- 期待 finding・rc・case 集合が不変：統合 diff で確認。

**nit N1 — 統合前後の検査結果を区別する。**  
参照：[s5-author.md:19](/home/SFC/tanab/.claude/jobs/4aa46448/tmp/wave/s5-author.md:19)、`docs/dev-wave/operations.md:138`、`tools/check_docs.py:605`。

報告の「DW-O18 exact 不一致 1 件」は、統合後の現物には成立しません。現在の operations 節は checker literal と完全一致するため、その finding は発生しません。報告末尾は親による docs 適用待ちと明記しており、過去の実走報告が誤りだとは判断しません。最終報告では「統合前の author 環境の結果」と区別すると明確です。統合後 checker 全体の rc は今回実測していません。

成果物影響：受理集合・変異検出力・land gate への影響はなく、検証結果の時点を取り違える余地だけです。

## 6

**must-fix はありません。** 放置により check_docs の受理集合、変異検出力、land gate を意図せず変える不備は確認できませんでした。

N1 は報告上の時点整理だけなので nit とします。本レビューの GO は静的設計に対する判断であり、親が予定している変異 matrix と land 前の検証結果を代替しません。