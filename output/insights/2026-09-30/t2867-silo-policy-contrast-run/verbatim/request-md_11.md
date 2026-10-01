md_11: 関数方策の軸の生成器対照を発効させ、本走を回す ([T-2867]、D2305 項 1)

最初に同じ directory の common-4.txt を読むこと。

■ 対象 item
[T-2867] (見出し「実装着地、生死確認 3 本成立 → 発効を承認 … → 発効の決定と本走 (AI)」)。

■ 目的
LLM×C++・LLM×IR・random×IR・進化×IR の 4 arm を、同じ評価の口で n = 12 系列ずつ回し、「フィードバックを使う非 LLM の探索 (進化) と比べて
LLM に何が言えるか」を事前登録どおりに測る。ユーザーは規模と計算を D2305 項 1 で承認済み。これは母集団型の探索 ([T-2892]) と段 A・B の比較の土台にもなる。

■ やること
1. 発効: docs/silo-policy-generator-contrast-preregistration.md §12 (発効束と確認事項、§12.1 の実値の案) を、生死確認の実測
   (output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md §4・§5) で埋め、日付付きの決定として spool の decisions fragment に書く。
   事前登録の本文の修正が要るなら、同文書の改訂規則 (凍結後は erratum) に従う。CCBench の pin は C `68106660` に固定し、本走の途中で変えない (D2305 項 1)。
2. 本走の最初の単位で、まだ計算ノードで回していない部品を確かめる: score job、参照 job (stock・静的 10 µs)、進化×IR の実走。
   ここで欠陥が出たら直してから次へ進む (最小の修正、Codex author)。
3. 本走: 48 系列を別ノードへ割って投げる。LLM の親は同時 4 (D2216・B-5 の運用)、LLM の待ちは login に置き (D2258 項 1)、週上限 (429) に当たったら
   系列を保留して待つ (D2258 項 2)。待ち手は完了通知で終わる 1 本にし、無変化の周期報告をしない。
4. 系列が揃ったら report を実台帳で 1 通し回し、事前登録の判定規則どおりに結果を出す。欠測・判定不能は欠測として書く。

■ 成果物
- 発効の決定 (decisions fragment)、本走の記録 output/insights/<着手日>/t2867-silo-policy-contrast-run/README.md (投入の一覧、Elapse、欠測、report の結果、限界)。
- spool worklog fragment ([T-2867] を更新または完了)。

■ scope 外
方策 driver の機能追加。探索の独立反復の本比較 ([T-2850]、D2305 項 2 で見送り)。Silo 修正後の Silo での測定。
