## 総括

**GO（静的設計レビュー）**。must-fix **0件**、nit **1件**（追加変異の提案）。
pin 追随漏れ・テスト弱体化は見つからない。
両 literal・正本・統合後の本文はすべて **995 bytes、完全一致**。
author 報告の「check_docs 不一致1件」は統合後には該当しないが、報告自身が docs 適用待ちと明記しており、時点差として説明できる。
pytest・checker は未実走。以下の KILLED / SURVIVED は静的予測であり、親の変異実走結果とは区別する。

## 1

**pin 追随は完全。指摘なし。**

指定ディレクトリを隠しファイル・ignore 対象も含めて探索し、旧句「F不在は登録せず裁定送り」「hold登録後だけ投げ直し」「再赤/決定的赤はmain既存F」「field正本=同file」の残存はなかった。数値 `997` の残存は別用途で、DW-O18 の旧 byte 数に依存するものは見つからない。

更新箇所は次のとおり。

- `tools/check_docs.py:605`：production literal。
- `orchestrator/tests/test_check_docs.py:166`：独立した合成 literal。
- 同 `:9484`：byte assert。
- 同 `:9582` / `:9639`：M2 / M11 needle。

その他の DW-O18 参照は、見出し・dispatch 配線・定数参照であり、本文変更への追随は不要。

成果物影響：旧本文への依存によって新しい正本を拒否する箇所は残っていない。

## 2

**M2 / M11 の削除は、静的には `{o18_finding}` だけになる。M4 も一意。指摘なし。**

`orchestrator/tests/test_check_docs.py:1039` は独立 fixture を一度だけ描画する。M2、M11、M4 の needle はその節に各1回あり、他の合成節へ重複挿入する経路はない。

| case | 削除後の DW-O18 | finding |
|---|---:|---|
| M2 | 918 bytes | `o18_finding` のみ |
| M11 | 913 bytes | `o18_finding` のみ |

根拠：

- `tools/check_docs.py:1923`：削除は通常の本文内で、raw / 可視 slice の一致と見出し数1を保ち、期待本文との一致だけを壊す。
- 同 `:5983` / `:6022`：operations は最長行上限の適用対象ではない。
- 同 `:5675`：削除後の連結部分にも禁止語2種は生じない。
- 同 `:5398`：L2 上限は1000 bytes。削除で上限違反は生じず、byte 分類の保存則も保つ。
- 同 `:6190`：見出し・dispatch 表・参照先は変わらない。

`orchestrator/tests/test_check_docs.py:9596` の M4 needle「判定不能・原因未理解は除外せず共に停止。」も各1回を維持する。`:9653` の finding 集合の完全一致 assert は変更されていない。

成果物影響：M2 / M11 は別の検査違反に依存せず、DW-O18 exact 契約の欠落検出を検証する。

## 3

**テスト弱体化なし。995 への変更は、不適切な「現行 hash 差し込み」には当たらない。**

diff の test 変更は fixture 本文、byte 数、needle 2本だけ。期待 finding、rc、case 集合、assert の削除・緩和はない。

`orchestrator/tests/test_check_docs.py:9457` の目的は、独立 literal により production 定数との共謀的縮小を拒否すること。`:9484` の byte assert はその全文のサイズも固定する補助契約である。

今回はユーザー裁定と事前確定の正本が本文変更を要求しており、正本自体が995 bytes。production から期待値を動的導出したものではなく、独立 literal・全文一致・固定 byte assert は残る。旧997を維持すれば、裁定どおりの本文を誤って拒否する。

成果物影響：受理する本文は裁定済みの新全文へ切り替わるが、任意の短縮や別文言を許すようには緩まない。

## 4

**M0〜M3 の登録は妥当。追加提案のみ nit。**

M0 は `tools/check_docs.py:609` の「同一tipで各1回だけ。」直後に **`""" """`** を挿入する場合、隣接する triple-quoted literal の暗黙連結になる。メモリ内で変更したソースを AST 解析し、評価値が元の995 bytes と完全一致することを確認した。引用符間の空白は文字列値に入らない。

M0 の分割位置、M1 の置換前文字列、M2 / M3 の削除文字列は、いずれも `tools/check_docs.py:609` に各1回だけ存在する。

以下の nodeid はすべて `orchestrator/tests/test_check_docs.py::` を接頭辞とする。M1〜M3 共通の KILLED 予測は：

- `test_normative_exact_section_contract_is_handwritten_and_complete`
- `test_dw_o18_exact_section_pin_accepts_synthetic_fixture`
- `test_dw_o26_exact_section_pin_accepts_synthetic_fixture`
- `test_non_attributable_landing_general_terms_are_accepted`
- `test_real_repo_clean`
- `test_non_attributable_landing_contract_mutations_have_one_finding[M5]`
- `test_non_attributable_landing_contract_mutations_have_one_finding[M6]`
- `test_non_attributable_landing_contract_mutations_have_one_finding[M8]`

最後の3件は、各 case 本来の finding に O18 不一致が加わり、集合一致が失敗するため。

さらに登録 M2 は `test_non_attributable_landing_contract_mutations_have_one_finding[M2]`、登録 M3 は同 `[M11]` が KILLED。checker 側と合成本文側で同じ句を削除した結果、期待する O18 finding が消えるためである。

逆に、O18 を別の文言へ壊す case は、checker 変異後も同じ O18 finding を返して **SURVIVED し得る**。段4の候補表を「全 case が killer」と読んではならない。

**nit N1 — 追加変異の提案。** `tools/check_docs.py:609` の「同一tipで各1回だけ。」を「同一tipで各2回だけ。」へ変更する負例を追加候補とする。D2104 項30が明示した回数制限を直接狙え、anchor は一意、byte 数も変わらない。既存の全文一致テストが検出するため、必須修正ではない。

成果物影響：追加すれば回数制限の改変に対する検出実績が得られる。未追加でも現在の受理集合・land gate は変わらない。

## 5

**literal・needle の報告は一致。「不一致1件」は統合前後の時点差。**

AST で取得した定数とファイル bytes を照合した結果：

| 対象 | bytes | 正本との一致 |
|---|---:|---|
| `tools/check_docs.py:605` | 995 | 完全一致 |
| `orchestrator/tests/test_check_docs.py:166` | 995 | 完全一致 |
| `docs/dev-wave/operations.md:138` の節 | 995 | 完全一致 |
| `dw-o18-new.md:1` | 995 | 正本 |

`s5-author.md:32` が挙げる M1・M2・M3・M4・M7・M10・M11・M12 の対象文字列も各1回。M7 は needle 変数ではなく、`:9620` の置換対象見出しである。

`s5-author.md:19` の「check_docs rc=1、不一致1件」は、現在の `docs/dev-wave/operations.md:138` と `tools/check_docs.py:605` の組合せでは発生しない。報告の `:45` が「親による改訂適用待ち」と説明しており、統合後の実装不整合ではない。checker 全体の現在の rc は本レビューでは未検証。

成果物影響：統合前の赤を現在の残存不具合として扱う必要はない。現在の実走成否は親の検査結果で判断する。

## 6

**DW-G05：must-fix は0件。**

受理集合の意図しない変更、変異検出力の低下、land gate を壊す実装差分は見つからなかった。

唯一の **nit N1**（`tools/check_docs.py:609`）は回数制限を狙う追加変異の提案であり、放置しても現行の exact pin と gate は変わらない。採否は親に委ねる。

本 GO は静的設計レビューの結論であり、親がこれから行う変異 matrix の成功や land 完了を認定するものではない。