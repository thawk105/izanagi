---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t337-qualification-authority
seq: 1
---

## {{D:qualification-authority-boundary}}. 正例 artifact の適格性は producer が宣言せず、独立 validator の再計算だけを権威とする — 機械化は発火条件が揃うまで行わない

**背景:** D126 決定 (3) は「適格性宣言の権威境界は親が決めない」として裁定へ返し、
「これが解けるまで正例 artifact は成果物として発行できない」と記録した。ユーザーは択 (a)
(新 D で権威境界を定義し、種別軸を閉表で管理する。凍結 patch ledger の exact-one contract は
改訂しない) を採用した。本 D はその権威境界の条文である。RF 統計設計 11 問は全件裁定済みであり、
本 D はそのうち「状態は独立 validator が raw receipt から再計算する」という裁定を境界として条文化する。
一次資料 = `output/insights/2026-08-05_t337-qualification-authority/`。

**決定 (1): 宣言と判定を分離する。** producer が宣言できるのは、利用意図を示す閉集合の**種別**と、
raw な実行事実・証拠 pointer だけである。種別のうち qualification は「適格性審査へ提出する」という
意味であり、**合格宣言ではない**。適格性そのものは producer が宣言できる対象ではない。

**決定 (2): producer の raw receipt schema は適格性 field を未知 field として拒否する。** 適格性状態、
pairing の成否、受理状態、および validator の identity / 結果の混入を closed schema で reject する。
分類が caller の自己申告である限りそれは意味 gate ではない、という D127 の境界をここでも維持する。

**決定 (3): 適格性権威は独立 validator だけが持つ。** validator は producer から合否値や加工済み
object を受け取らず、永続化済み raw receipt の path を起点に bytes を自ら読み直し、schedule・
全 attempt・allocation / accounting・測定 checkout・correctness・raw throughput を再計算する。

**決定 (4): consumer は decision を入力として受け取らず、trusted validator を同一呼出し内で
再実行する。** validator の source hash が decision に載っていることは「その validator が実行された」
ことの証拠にならない — producer は予定 validator の hash を読み、正しい identity と空の理由列を持つ
合格 decision を直接書ける。既存 admission 境界が raw path から同一呼出し内で検査している形を先例とする。

**決定 (5): 検査は単一 fd / snapshot で読み、hash と parse を同一 byte buffer に対して行う。**
検査の前後で hash を取り直す方式は ABA (検査中だけ適格な bytes へ差し替える) を防がない。
symlink は拒否する。

**決定 (6): 状態は固定閉表とし、「少なくとも」という書き方をしない。** 弱い分母に対する
`weak_denominator_not_certifiable` は裁定済みの状態名であり、理由列へ落とさず状態として置く。
分母 screening は行わない。`RF > 1` は「回復」とも「新規改善」とも帰属させず、stock 超過とだけ述べる。

**決定 (7): 凍結 patch ledger の 3 つの適格性 field は entry-local な負制約として固定する。**
exact-one contract と exact 値要求はそのまま維持し、別 sidecar による実質上書きも作らない
(D120 決定 (2) の直接適用)。**これらの field は不活性な歴史的宣言ではない** — 静的契約と driver の
検証経路が実際に読み、不一致なら計測を止める。ただしそれは既存 entry に対する authoritative な
**負**制約であって、新 artifact を適格へ**昇格**させる権威ではない。昇格権威として読む consumer は
0 件である。

**決定 (8): 既存の環境適格性 receipt を遡及昇格しない。** 当該 protocol は subject / reference の
二者であり統計的主張を持たず、promotion API を持たない設計である。これを 3 arm の正例 artifact と
読み替えない。

**決定 (9): 適格性の統計 record を層 3 の calibration floor 閉表へ混載しない。** 別区画に置き、
`(試行 ID, 候補 ID, workload ID, contrast)` の composite key を持たせる。

**決定 (10): 機械化は発火条件が揃うまで行わない (`DW-G04`)。** 本 D と同じ変更単位で land するのは
docs だけであり、production code・schema・test・凍結 artifact は 1 byte も変更していない。
実装被覆は 0/9 層である。発火条件は (i) 3 arm を持ち事前登録を実走前に commit した計測が 1 本以上
存在すること、(ii) その計測が環境タグ・測定 checkout・pin・attestation を持つこと、
(iii) 判定を読む consumer の実 hook が実在すること、の 3 点とする。
唯一の 3 arm 計測は不成立かつ 1 allocation・J=1 であり、負例の存在が条件付き機能の発火を
正当化しないことは D120 決定 (3) が既に裁定している。

**決定 (11): 種別軸の field 名は本 D では確定させない。** 既裁定は literal な名前を指定しているが、
その名前は別軸 (探索 oracle の文書種別) として 2026-07-20 に land 済みであり、既裁定の記録は
この衝突に触れていない。同名で置けば D75 の二義化になり、改名すれば裁定済みの実装方向を
親が独断で非同値な択一へ戻すことになる。したがって本 D は権威境界だけを固定し、名前は
新事実を添えてユーザー再裁定へ返す。**名前が決まるまで、種別 field を持つ新しい producer を land しない。**

**却下した選択肢:**

- 種別 field を親の判断で改名して先へ進む — 実装方向まで裁定済みの項目を、代案の等価性を
  コードで確認しないまま非同値な択一へ戻すことになる。敵対 2 レンズが独立に blocker と判定した。
- 適格性を manifest の自己宣言で持つ — D126 決定 (3) の起点であり、恒真 gate の型そのものである。
- 凍結台帳の exact-one contract を改訂して新 entry を足す — 正しさ防壁の改訂であり独立の裁定が要る。
- 負例が実在することを根拠に機械 gate を先に作る — 拒否枝の存在は条件付き機能の発火を正当化しない。
- decision を成果物として持ち回り consumer がそれを読む — 決定 (4) の偽造経路が開く。

**研究状態への影響:** certified 選択の値、材料レポート、proof chain、凍結 bytes、既存 gate、
受理集合はいずれも**不変**である。実装差分がゼロのため変異 matrix と受入全走は射程外である。
変わるのは、正例 artifact の適格性を誰が宣言できるかという境界が条文として固定されたことと、
種別 field の名前がユーザー再裁定待ちとして分離されたことである。
