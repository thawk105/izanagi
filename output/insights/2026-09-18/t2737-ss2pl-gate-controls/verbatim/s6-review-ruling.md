# 段 6 レビューの裁定 (親、2026-09-18 07:50 JST)

レビュー A (`s6-revA.md`、正しさ境界 / receipt 整合 / 主張検算) と B (`s6-revB.md`、裁定充足 / runner 契約 / 運用 / F29 / 表 / scope) を読み、所見ごとに closed / partial / regressed を裁定した。**code fix と計算ノード再投入は 0 件** (両レビューとも「fix 不要・再投入不要」)。是正はすべて insight README の記述に反映した (`output/insights/2026-09-18/t2737-ss2pl-gate-controls/README.md`)。

| # | 所見 | 判定 | 対応 |
|---|---|---|---|
| A1 | S 復元に新しい lock 意味論なし、DLR 5 組は正規 define で分岐保存、`rwlock.hh` 囲いは d2pl を壊さない (実 build は未確認) | refuted (骨抜きでない) | README 1.1 に保証範囲 (正規 define / 検査した経路) の限定を維持 |
| A2 | 最終版 (fix1 後) の phase1 局所前処理は `insert()` の括弧 1 箇所で現行と不一致。「一致」とは書けない | real | closed: README §6 の (ii) 非 inert 行を「呼び出し保持の局所確認、完全一致は未達、射程は 6 file の個別前処理」に修正 |
| A3 | shadow 受理条件 (期待 bytes 全体一致) と identity 記録は実装済み、9 shadow とも独立再構成と一致 | refuted | — |
| A4 | reason 転記不整合 0。予測差は条件付き予測内 (job 2: 7 cell) と job 1 の warm-up 前提不成立 (17 cell)。job 1 の plain build 後は 16 でなく **20 cell** | real (件数) | closed: README 1.4 を 20 cell (16 完全一致 + revs/T+/S 3 cell 条件付き + KIND C) に訂正 |
| A5 | gate 緩和・`#line`・WFG TU 混入なし。S build の WFG 不在検査 accepted (3 TU) | refuted | 「WFG という文字列が一切ない」とは書かない (軸表示文字列は既存契約で許容) |
| A6 | revS は runner の abort 所有権契約に拒否される | real | closed: README 3.3 に既存の障害として明記、validator は緩めない |
| A7〜A11 | 予定主張 (i)〜(v) はすべて限定付きで real | real | closed: (ii) の「1 行」は receipt の行数、その内容 (`__LINE__`) は login diff が根拠、と証拠を分離 (README 3.2)。(iv) は「両版 red、1 対 218、反転対照は未成立」に修正。(v) は「KIND は C が先行」を明記 |
| B1 | D2120 の必要比較は未成立、shadow-T は機構診断 | real | closed: README §0 の先頭に置いた |
| B2 | 非 inert の対応表と KIND 固定 target 対は揃っている。各 hunk の独立した必要十分性は未実測 | refuted (欠落なし) + 注記 | closed: README 3.1 に注記追加 |
| B3 | plain build 成功・WFG 不在検査受理は runner 全契約の受理ではない。abort 所有権と S 復元の衝突を独立行に | real | closed: README 3.3 |
| B4 | job 2 の warm-up 対・診断・予算に欠落なし。config.h の一致は staging 全体の不変証明ではない。診断 configure は rc=0 で stderr に警告 | refuted + 注記 | closed: README §4 に注記追加 |
| B5 | job 1 の後段は 20 cell。PBS ID は候補として保持 | real | closed: README 1.4 |
| B6 | gate 3 呼び出し・configure_args は production と一致。運用差分は列挙どおり。`revs/O/phase1` は admitted=true | refuted | README 1.3 / §5 で一致部分と差分を明記 |
| B7 | 「`#line` でしか消えない」は証拠を超える (唯一性未検証) | real | closed: README 3.2 / 3.3 / §6 を「固定復元範囲では残った。`#line` 同期は未実施、唯一性は未検証」に修正 |
| B8 | 段 7 の commit は insight + spool に限定。逐語 `.md` には元名・版・sha256 を付け、job 1 の旧 probe (v1) は区別 | refuted (混入なし) + 注記 | closed: README 1.4 に v1 の所在 (job dir `probe-v1/`、sha `418448c9…`) を記載。逐語 `.md` の先頭に sha256 と bytes |

DW-O16: 親が書いた派生値 (残差行数 1 / 218 / 3,666、byte 長、cell 件数、所要) は receipt の原データ (`receipts/probe-result-2.json`、`cells-summary-2.json`) から再計算して照合した (レビュー A4 が独立に 90 cell の転記一致を確認)。
