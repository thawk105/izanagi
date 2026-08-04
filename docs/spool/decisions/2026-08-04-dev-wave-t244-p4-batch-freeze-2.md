---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t244-p4-batch-freeze
seq: 2
---

## {{D:t244-p4-batch-freeze-defer}}. D121 P4 の独立 leaf 実装は差し戻す — batch 第一級の裁定の下で batch freeze は origin ledger 実装と不可分であり、member identity ほか 5 件を裁定へ返す

**背景:** D121 決定 (7) の P4 (batch cardinality・全候補の事前 commit・seal までの結果非公開) は
D150 で無条件義務へ移り、未充足のまま残っていた。本 wave は P4 の機械部品を独立 leaf
(commitment codec + freeze→seal FSM) + 独立 golden として実装するために起票され、file:line 粒度の
実装プランを起草した (逐語 = `output/insights/2026-08-04_t244-p4-batch-freeze/`)。
段 3 の敵対 2 レンズが**独立に NO-GO** を返した (blocker 11 件・major 8 件・minor 2 件)。

**決定 (1): 本 wave では実装せず、プラン・所見・裁定を設計材料として凍結する。** 決め手は 3 点。

第一に、**batch を origin ledger の第一級にするというユーザー裁定の下で、ledger 外の独立 FSM
leaf は実装先として誤りになった。** 第一級 batch event が canonical bytes・digest・cardinality・
policy を格納する以上、独立 leaf の lifecycle・policy・result schema は将来の第一級実装との
二重実装か、どこからも発火しない prototype のどちらかになる。後者は D150 決定 (6)(a) が警告する
「実装のふりをした非適用」の温床である。

第二に、**batch member の identity が未裁定で、commitment preimage が決まらない。** プランは
member を distinct wire set (最大 32) とした。しかし採用済みの予算下限式は 32 候補 × R replicate の
全 query を数えるため、distinct set では反復測定を表現できず、cardinality と query 消費が
実 query 数より小さく写る。preimage が決まらない以上、正準 bytes の独立 golden 凍結も成立しない。

第三に、**条件付き機能の発火 gate (DW-G04) に対し、発火する既存 artifact path / 計測 ID を
1 件も書けない。** D149 (P1) の「機械部品 + 独立 golden 先行」は golden の独立性を監査する
順序の先例であって、発火 gate の一般例外を作らない。

**決定 (2): 設計択一 5 件を裁定パッケージとしてユーザーへ返す。** 推奨込みの一覧:
W1 実装先 = origin ledger 実装 wave の中で第一級 batch event / reducer として設計・実装する
(producer・ledger・driver・formal consumer・proof chain の結線順と各層の受理条件も同 wave の
設計に含める)。W2 member identity = query/replicate ordinal 込み (予算下限式の replicate を
表現するため)。W3 結果の evidence 束縛 = evidence digest 束縛 (二値 + 自己申告 class hash では
proof chain が未裏付け outcome を受理しうる)。W4 = 早期停止時は残 member を tombstone として
消費し公開 transcript 長を固定する (設計本文 §4③ の既定どおり)。W5 floor / Kmax の authority =
origin-total の計数は ledger、batch 層は authority receipt 由来の policy だけを受理し、
class referent の実在・完全性検証は formal consumer 側の義務とする。

**決定 (3): 名乗りの制限。** 本 wave が残すのは設計材料 (プラン + 敵対所見 + 裁定) だけである。
「P4 実装」「P4 充足」「P4 prototype」のいずれも名乗らない。P4 は未充足のまま、cap-lift は FAIL、
承認上限 1 (D114) は不変。

**却下した案:** (a) member identity 等を親の裁量で決めて実装する — D121 却下案 (b)
「未裁定設計の既成事実化」と同型で、D147 が P3 で却下したのと同じ理由。(b) commitment codec
だけ先行 leaf 化する — preimage が W2 に依存するため codec 単体でも既成事実化になる。
(c) レンズ A の「golden 凍結 = freeze 族接触で段 1 巻き戻し」— 当該節の義務 (freeze 族の
submodule 初期化と skip の正直な報告) は wave 開始時に履行済みで、新規 golden の新設は
凍結成果物・oracle gate・proof chain の機構に触れない。巻き戻しは成果物を捨てるだけで
判定を変えない。

**研究状態への影響:** なし。本 wave は docs のみで、production 挙動、受理集合、certified 選択、
材料レポート、proof chain、凍結 bytes はいずれも不変である。実装差分が無いため変異 matrix は対象外。
