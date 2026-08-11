# 段 6 レビュー所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| LUNA-01 変異 spec が段 4 事前登録と別物 | **real** | **採用 (親の手番)**。spec を段 4 の ID 体系 M1〜M6 へ戻し、M3 の期待変更は erratum として台帳へ残す (`DW-M02`)。discovery spec で node 集合を実測してから確定する |
| LUNA-02 M3 は SURVIVED にならない (二重 masking + 理由文字列 oracle) | **real** | **採用**。段 4 の「enum 縮小に独立検出力が無い」という判断自体は正しいが、**期待 status が誤り**だった。docs 照合が先に拒否するため KILLED になる。erratum に両方を書く |
| LUNA-03 HTML comment に旧表・旧宣言を隠すと緑のまま破れる | **real・blocker** | **採用 (fix)**。`_read_design` の段階で HTML comment を除去し、可視部分だけを抽出対象にする。既存抽出器 (`_extract_ruling_ids` / `_extract_design_row_ids`) も同じ弱点を持つため、1 箇所で塞ぐ。負例 node を 1 件追加する |
| LUNA-04 独立 pin の陽性 node は production 比較を検査しない | **real** | **採用 (部分)**。node は「fixture・manifest・module 定数の三者一致の snapshot」であって validator の拒否能力ではない。**docstring を実態に合わせる**。M2 の期待 node は並べ替え負例 1 件へ確定 (実測どおり) |
| LUNA-05 projection node は snapshot assertion | real | **採用 (nit)**。docstring を実態に合わせる |
| SOL6-01 既存 node の docstring が中立な再照準を「受理集合縮小」と表示 | real | **採用 (nit)**。中立なものは中立と書く |

**受理集合は広げない。production の緩和で辻褄を合わせない。** 既存テストの期待値
(拒否理由の逐語・件数) を変更しない。

## fix 単位

1 単位 (編集面が同一ファイル対で素集合にならないため一枚岩)。
`orchestrator/tests/calibration_freeze_authority_contract.py` と
`orchestrator/tests/test_calibration_freeze_authority_contract.py` のみ。
