---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t244-p4-batch-freeze
seq: 2
---

## {{D:p4-batch-freeze-ledger-conformance}}. D121 P4 の batch freeze は origin ledger 側の契約としてだけ適合させる — W2 は origin-wide ordinal、W4 は terminal event 形の統一で満たし、P4 充足は名乗らない

**背景:** D153 は P4 の独立 leaf 実装を差し戻し、設計択一 W1〜W5 を裁定へ返した。ユーザーは
2026-08-04 の /rulings で **W1〜W5 全件を D153 推奨どおり採用**し、「P3+P4 実装 wave を起票できる」
とした。D159 が land させた origin ledger prototype は第一級 batch event を持つが、W2 と W3 には
適合していなかった。本 D はその適合を実装した wave の設計判断である。

**決定 (1): W2 の member identity は origin-wide の ordinal で束縛する。** batch member の正準
preimage を `(candidate wire, origin-wide query ordinal, origin-wide replicate ordinal)` とし、
salted commitment はこの preimage に対して作る。replicate ordinal を batch-local にする案は、
W2 の目的節 (予算下限式の replicate を表現する) と設計本文の origin 単位予算が origin 全体を
数えることから不採用とした。同一 wire の反復測定が表現可能になり、旧実装が強制していた
候補平文の distinct 制約は撤回した。

**決定 (2): replicate ordinal は commitment preimage だけに置き、seal 前の公開面に出さない。**
`replicate_ordinal == 0` の member 数は distinct wire 数そのものなので、平文公開は
「seal までの結果非公開」を破る。query ordinal は連続で ledger の公開 counter から導出できるため
公開してよい。実行依存 counter (sealed / tombstoned) も seal 前 projection から除外し、
少数候補の列挙で prospective digest を照合する oracle を塞いだ。

**決定 (3): W4 の「公開 transcript 長を固定」は terminal event 形の統一まで要求する。**
全 terminal path を `committed → prepared → sealed` の 3 event に統一し、
専用の tombstone 終端 event を削除した。未実行 member は閉じた三値 outcome の `tombstoned` row として
seal に載せ、member row 数を committed cardinality に固定する。全 tombstone だけ 2 event で終わる
設計は、早期停止の有無を terminal 種別と event 数として公開してしまうため不採用とした。
**JSON byte 長の同一化は保証しない**。これは設計本文が「上界が未定義の面は明示的に受容残余とする」と
定めた枠に従い、受容残余として記録する。

**決定 (4): W3 は「outcome と evidence digest claim の commitment 束縛」までであり、そう名乗る。**
outcome と evidence digest を単一の salted preimage へまとめ、codec 層と reducer 層の二層で
三値 matrix (合法 3 セル・不正 9 セル) を検査する。referent の実在・完全性検証は W5 の分界どおり
formal consumer の義務であり、ledger は digest を dereference しない。この境界はテストで固定するが、
「consumer を実装した」とは数えない。

**決定 (5): ledger は物理 query を観測しないと明記する。** sealed query counter は
「evidence を伴う sealed member row 数」であって実 query 数の代理ではない。同一 wire・同一 evidence を
正しく番号付けて並べれば counter は増えるので、この counter だけで query floor が物理的に
満たされたとは言えない。恒真な「query 一対一」検査は**作らない**。物理 query と member row の束縛は
producer/driver 側の設計であり、裁定パッケージとして返す。

**決定 (6): schema を v2 へ分離する。** authority feasibility の意味 (partition 存在、
origin 横断の runtime-head 合算、cardinality の十進桁を含む byte 上界) が変わるため、
同一 schema ID のまま挙動を変えない。manifest / authority / event / head / runtime を v2 とし、
空の registry file も v2 名へ改名した。**実在 authority の世代移行の主体と契約は本 D で決めない** —
その裁定は別途起草中の設計パッケージが所有する。

**決定 (7): 名乗りの制限。** 本実装は「D153 W1〜W5 の ledger 側契約に適合する P4 batch-freeze
prototype」であり、**P4 は依然 FAIL、cap-lift も FAIL、承認上限 1 (D114) は不変**である。
充足の会計は D159 決定 4 の U-G と同型で、producer 結線・driver 結線・実 authority 登録・
seal 前漏洩を防ぐ storage 契約・formal consumer・proof chain 結線の 6 点が残る。
production caller ゼロ・authority registry 空も維持しており、受理集合の現在値は不変である。

**却下した選択肢:**
- salt の下限だけを保つ (上限なし) — 「最長 frame」が定義できず codec feasibility が成立しない。
  exactly 32 lowercase hex へ固定した。
- 予算の origin-total を単一 batch として直列化して feasibility を測る — 分割すれば合法な
  authority を過剰に拒否する。per-batch 上限と origin-total の partition 可能性を分離した。
- member 列の順序を別の commitment で二重に固定する — 外側の event hash と重複し、
  単一理由で kill できる検査が作れない (恒真な保証を増やす)。削除した。
- 敵対レビューが求めた「evidence digest の origin 内 distinct 強制」— 正当な同一 artifact を
  false reject する risk が未実測で、裁定のない設計決定になる。起票して裁定へ返す。
