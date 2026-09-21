# 段 6 裁定 — レビュー A (codex/s6-review-A.md、NO-GO、照合 81 件 / 一致 80 件) の所見

裁定 2026-09-21 08:5x JST。全 must-fix real・採用。README / fragment は docs なので親が直す。出所不足 (A6 の main 履歴) は Codex author 4 巡目の probe `main_checker_history.py` で補う。

| # | 判定 | 採否 | 対応 |
|---|---|---|---|
| A1 | real | 採用 | §1 の着地後 main を `5733c0f08…` (land-3.json の main_after) に直し、65966f4d8 は監査・land した tip と書き分ける。 |
| A2 | real | 採用 | §4 の「実装と同じ候補選択」を「選択集合・ancestry・距離順・prefix / raw correction は現行実装、候補集合は残存受領証の mtime 順で近似、`_read_audit_receipt` の mode 等の検査は再現しない」に直す。§7 に author 報告の非同値 7 項を全部入れる。 |
| A3 | real | 採用 | §5 の表を probe の分岐どおりに書き直す (root `.gitattributes` の検査は旧形だけ、新形・中間形・系統不明の attributes 差、複合差の連結、代表候補との比較、replay 失敗・未判定)。「代表候補との差は単独原因の証明ではない」を添える。 |
| A4 | real | 採用 | 26 件は「probe の規約で参考区分に分類」、digest 差の内訳は復元していない、errno 等を個別に排除していない、と書く。§8 の errno 行も同じ限定。 |
| A5 | real | 採用 | unsupported 10 本 = file mtime が期間内の解析不能 log file。監査 attempt 数・受領証の有無は未確定。 |
| A6 | real | 採用 | dispatch 受領証本体 (`measurements/force-dispatch-{1,2}.dispatch-receipt.json`) と mtime (`force-dispatch-mtimes.txt`) を insight に置き、node・queue の出所を field 名で書く。nqsv の作成→開始 (9 / 7 秒) も併記。main の checker 遷移は probe の出力で置き換え、親の「2 回」「6 件中 5 件は main に入らなかった版」は撤回 (6305f2d05 の checker は `65476daf…`)。 |
| B1 | real | 採用 | 「P-4 実行前の凍結目録の M + R では」と範囲を付け、P-4 初回は別枠と書く。 |
| B2 | real | 採用 | §8 は「land 1 件と P-4 初回は partition 跨ぎの観測例。統一後の全 bindings 一致と lookup 前の利用可能性は未検証、救済可能件数は確定しない」に直す。 |
| B3 | real | 採用 | fragment の title を「事後診断」「対照測定」の語へ直す。 |
| nit | real | 採用 | load1 は 13 行観測・4 行欠測、「約 1/7」、1.7〜3.5 秒は T-2803 insight §8.3 への直接 link、§3 の時刻は file mtime / launcher 出力が出所と明記し、出所の無い分刻み・工数は削るか出所を付ける。重複 (§2・§9・§10 と fragment) を減らす。 |

焦点再レビュー (DW-O16) は README / fragment の改訂後に 1 本、所見ごとの closed / partial / regressed 表を要求する。
